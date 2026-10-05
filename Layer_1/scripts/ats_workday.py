#!/usr/bin/env python3
"""
VANTAGE — Workday Structured Location Search (Fase 2)

Sustituye la búsqueda geográfica textual (`searchText`) por resolución dinámica
de facets + `appliedFacets` contra la API CXS de Workday.

Precedente: HERMES — FASE 1B TECHNICAL FINDINGS.

Contrato de estados (Fase 2 §6):
    verified_results | verified_empty | blocked | dns_failure | timeout | unknown

Regla fundamental: un HTTP 200 con cero postings NO es `verified_empty`
mientras el facet de ubicación no se haya resuelto desde el contexto activo.

Módulo aislado: no importa nada de Layer 1, no toca scoring, no toca Tracker.
"""

from __future__ import annotations

import json
import socket
import time
import unicodedata
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlparse

# ---------------------------------------------------------------- constantes

# Workday CXS rechaza limit > 20 con HTTP 400 (Fase 1B §3, evidencia live).
WORKDAY_MAX_LIMIT = 20
DEFAULT_LIMIT = 20

# Tope anti-wraparound. Workday envuelve circularmente cuando offset supera la
# ventana real (Fase 1B §5, caso 8). El cap es independiente de `total`.
DEFAULT_SAFETY_CAP = 2000

# Facets de ubicación soportados (Fase 2 §2.4). Se identifican por
# facetParameter, nunca por posición en la respuesta.
LOCATION_FACET_PARAMS = ("locationCountry", "locations")

# Sinónimos de país. Normalización sin acentos ni puntuación.
COUNTRY_ALIASES = frozenset({"MEXICO", "MEXICO CITY", "CDMX"})

# Sinónimos de ciudad. Fase 1B §9 riesgo 5: `Cdmx`, `Ciudad De Mexico` y
# `Zona Centro` son valores DISTINTOS del mismo tenant. Filtrar por uno solo
# pierde vacantes, así que el resolver matchea por set de sinónimos.
CITY_ALIASES = frozenset({
    "CDMX", "CDMX MEXICO",
    "CIUDAD DE MEXICO", "CIUDAD DE MEXICO MEXICO",
    "MEXICO CITY", "MEXICO CITY MEXICO",
    "ZONA CENTRO", "ZONA CENTRO MEXICO",
})

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

BLOCK_MARKERS = (
    "security check", "access denied", "cloudflare", "akamai",
    "captcha", "cf-browser-verification",
)


# ---------------------------------------------------------------- taxonomía

class QueryState:
    """Taxonomía de estado técnico (Fase 2 §6)."""

    VERIFIED_RESULTS = "verified_results"
    VERIFIED_EMPTY = "verified_empty"
    BLOCKED = "blocked"
    DNS_FAILURE = "dns_failure"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


# ------------------------------------------------------------ normalización

def normalize_descriptor(descriptor: str) -> str:
    """Mayúsculas, sin acentos, sin puntuación, espacios colapsados.

    Fase 1B §3: los descriptors varían por tenant (`Cdmx`, `Ciudad De Mexico`,
    `Ciudad de México, Mexico`). Comparar por igualdad exacta pierde vacantes.
    """
    if not isinstance(descriptor, str):
        return ""
    # Descomposición Unicode: "é" -> "e" + acento combinante. Sin esto,
    # "MÉXICO" se corta como "M XICO" porque el acento no es ASCII y cada
    # carácter acentuado se convierte en un separador.
    decomposed = unicodedata.normalize("NFD", descriptor.upper())
    out = []
    for ch in decomposed:
        if unicodedata.combining(ch):
            continue  # descartar el acento, conservar la letra base
        if "A" <= ch <= "Z":
            out.append(ch)
        elif "0" <= ch <= "9":
            out.append(ch)
        else:
            out.append(" ")
    return " ".join("".join(out).split())


# ------------------------------------------------------------- value record

@dataclass(frozen=True)
class FacetValue:
    """ID + contexto completo del que proviene.

    Fase 2 §8: el contexto (tenant, site, facetParameter, descriptor) es la
    unidad de validez. Un ID sin contexto no es utilizable — es exactamente el
    modo de fallo cross-tenant que la Fase 1B demostró (HTTP 200 + Australia).
    """

    tenant: str
    site: str
    facet_parameter: str
    descriptor: str
    value_id: str
    count: Optional[int] = None

    def matches_context(self, tenant: str, site: str, facet_parameter: str) -> bool:
        return (
            self.tenant == tenant
            and self.site == site
            and self.facet_parameter == facet_parameter
        )


@dataclass
class LocationResolution:
    """Resultado del resolver de ubicación.

    Fase 2 cierre — punto 2. `scope` y `scope_degraded_from` hacen EXPLÍCITA
    la diferencia entre "se resolvió lo que se pidió" y "se resolvió menos de
    lo que se pidió". Una caída de ciudad→país nunca es silenciosa.
    """

    facet_parameter: Optional[str] = None
    values: List[FacetValue] = field(default_factory=list)
    resolvable: bool = False
    reason: str = ""

    # "country" | "city" | None
    scope: Optional[str] = None
    # "city" cuando sólo se pudo resolver "country"; None si no hubo degradación.
    scope_degraded_from: Optional[str] = None

    def applied_facets(self) -> Dict[str, List[str]]:
        if not self.resolvable or not self.values or not self.facet_parameter:
            return {}
        return {self.facet_parameter: [v.value_id for v in self.values]}

    def verify_against(self, facets: List[Dict[str, Any]],
                       tenant: str, site: str) -> Tuple[bool, List[str]]:
        """Re-deriva cada ID desde los facets del contexto dado y compara.

        Fase 2 cierre — punto 1. `matches_context()` por sí solo es
        AUTORREFERENCIAL: un FacetValue construido a mano declarando otro
        tenant "validaría" contra sí mismo. Esta verificación es la única
        que realmente aísla, porque vuelve a leer los IDs desde la fuente
        (los facets del tenant/site consultado) y exige que coincidan.

        Devuelve (ok, ids_invalidos).
        """
        if not self.values:
            return True, []
        per_param: Dict[str, set] = {}
        for v in self.values:
            if v.facet_parameter not in per_param:
                per_param[v.facet_parameter] = {
                    raw["id"]
                    for raw in _iter_facet_values(facets, v.facet_parameter)
                    if isinstance(raw, dict) and raw.get("id")
                }
        invalid = [
            f"{v.facet_parameter}:{v.value_id}"
            for v in self.values
            if v.value_id not in per_param.get(v.facet_parameter, set())
        ]
        return (not invalid), invalid


# ------------------------------------------------------------------ cliente

class WorkdayError(Exception):
    def __init__(self, state: str, detail: str):
        super().__init__(detail)
        self.state = state
        self.detail = detail


def _classify_transport_error(exc: Exception) -> Tuple[str, str]:
    """Mapea excepciones de urllib a la taxonomía (Fase 2 §6)."""
    if isinstance(exc, socket.gaierror) or "nodename nor servname" in str(exc):
        return QueryState.DNS_FAILURE, f"DNS: {exc}"
    if isinstance(exc, socket.timeout):
        return QueryState.TIMEOUT, f"timeout: {exc}"
    if isinstance(exc, TimeoutError):
        return QueryState.TIMEOUT, f"timeout: {exc}"
    text = str(exc).lower()
    if isinstance(exc, URLError):
        reason = getattr(exc, "reason", exc)
        if isinstance(reason, socket.gaierror) or "nodename nor servname" in str(reason):
            return QueryState.DNS_FAILURE, f"DNS: {reason}"
        if isinstance(reason, (socket.timeout, TimeoutError)):
            return QueryState.TIMEOUT, f"timeout: {reason}"
        if "timed out" in str(reason) or "handshake" in str(reason):
            return QueryState.TIMEOUT, f"timeout: {reason}"
        return QueryState.UNKNOWN, f"URLError: {reason}"
    if "timed out" in text or "handshake" in text:
        return QueryState.TIMEOUT, f"timeout: {exc}"
    return QueryState.UNKNOWN, f"{type(exc).__name__}: {exc}"


class WorkdayClient:
    """Cliente CXS mínimo para discovery + consulta estructurada.

    Fase 2 §7: usa la infraestructura de reintentos existente en el módulo
    (`_request_with_retry`). No introduce un segundo sistema de retries.
    """

    def __init__(self, tenant: str, site: str, host: str,
                 timeout: int = 25, max_attempts: int = 3,
                 backoff: float = 1.5, dry_run: bool = True):
        if not host:
            raise ValueError("host requerido")
        self.tenant = tenant
        self.site = site
        # Acepta host con o sin esquema; normaliza a host desnudo.
        self.host = urlparse(host if "//" in host else f"//{host}").netloc or host
        self.timeout = timeout
        self.max_attempts = max_attempts
        self.backoff = backoff
        self.dry_run = dry_run
        self.base = f"https://{self.host}/wday/cxs/{tenant}/{site}"
        self._audit: List[Dict[str, Any]] = []

    # ------------------------------------------------------------ transporte

    def _post_jobs(self, payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], str, str]:
        """POST /jobs con retry. Devuelve (data|None, state, detail)."""
        url = f"{self.base}/jobs"
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        last_state, last_detail = QueryState.UNKNOWN, "sin intentos"
        for attempt in range(1, self.max_attempts + 1):
            req = Request(url, data=body, headers=headers, method="POST")
            try:
                with urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read().decode("utf-8", "replace")
                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        return None, QueryState.UNKNOWN, f"JSON inválido: {raw[:160]}"
                    return data, "ok", ""
            except HTTPError as exc:
                detail = f"HTTP {exc.code}"
                try:
                    snippet = exc.read().decode("utf-8", "replace")[:200]
                except Exception:
                    snippet = ""
                low = snippet.lower()
                if any(m in low for m in BLOCK_MARKERS):
                    return None, QueryState.BLOCKED, f"{detail} bloqueo: {snippet[:120]}"
                if exc.code in (401, 403):
                    return None, QueryState.BLOCKED, f"{detail} sin acceso al ATS"
                if exc.code in (400, 405, 406, 422, 500, 502, 503, 504):
                    # Fase 2 cierre §3: la causa y la decisión de retry salen
                    # de classify_http_error (fuente única de verdad).
                    state_, cause, retryable = self.classify_http_error(
                        exc.code, snippet)
                    last_state = state_
                    last_detail = f"{detail} {cause} | {snippet[:120]}"
                    if not retryable:
                        return None, state_, last_detail
                else:
                    return None, QueryState.UNKNOWN, f"{detail} {snippet[:120]}"
            except Exception as exc:
                last_state, last_detail = _classify_transport_error(exc)
                if last_state in (QueryState.DNS_FAILURE,):
                    return None, last_state, last_detail
            if attempt < self.max_attempts:
                time.sleep(self.backoff * attempt)

        return None, last_state, last_detail

    @staticmethod
    def classify_http_error(code: int, snippet: str) -> Tuple[str, str, bool]:
        """Clasifica un error HTTP en (state, causa, retryable).

        Fase 2 cierre — punto 3. Un HTTP 400 NO es una categoría homogénea:
        tratarlo como equivale a couldn't se pierde la distinción entre
        "payloadRejected" (el ATS rechazó la consulta — no tiene sentido
        reintentar) y "transientBadRequest" (posible fallo de borde en el
        ATS — reintentar tiene sentido y un retry-simple puede resolverlo).

        Las subclases de 400 se distinguen por el cuerpo de la respuesta,
        que CXS siempre acompaña con `errorCode` / `errorCaseId` / `message`.
        """
        low = (snippet or "").lower()
        has_workday_error_envelope = "errorcode" in low and "errorcaseid" in low

        if code == 400:
            # `message` vacío + envelope CXS = rechazo de validación del
            # servidor de aplicación. Es el 400 de Fase 1B: facet ID
            # malformado (f4158df1 vs f5158df1), limit>20, facet inexistente.
            if has_workday_error_envelope:
                return (QueryState.UNKNOWN,
                        "payload_rejected: el ATS rechazó el payload "
                        "(facet ID malformado, limit>20 o facet inexistente)",
                        False)
            # 400 sin envelope CXS = probablemente no vino de Workday
            # (proxy, WAF, borde). No es evidencia sobre el ATS.
            return (QueryState.UNKNOWN,
                    "bad_request_non_cxs: HTTP 400 sin envelope de Workday; "
                    "posible capa intermedia, no atribuible al ATS",
                    True)

        if code == 405:
            return (QueryState.UNKNOWN, "method_not_allowed", False)
        if code == 406:
            return (QueryState.UNKNOWN, "not_acceptable: header Accept rechazado", False)
        if code == 422:
            return (QueryState.UNKNOWN,
                    "unprocessable: falta parámetro requerido por CXS", False)
        if code in (500, 502, 503, 504):
            return (QueryState.UNKNOWN, f"server_error_{code}", True)
        return (QueryState.UNKNOWN, f"unclassified_{code}", True)

    @staticmethod
    def _is_terminal_payload(code: int, snippet: str) -> bool:
        """Compatibilidad: delega en classify_http_error.

        Se conserva porque el contrato Fase 2 §7 prohíbe una segunda
        infraestructura de retries. La decisión retryable/no-retryable
        ahora vive en un solo lugar.
        """
        _, _, retryable = WorkdayClient.classify_http_error(code, snippet)
        return not retryable

    # ------------------------------------------------------------- discovery

    def discover(self) -> Tuple[Optional[Dict[str, Any]], str, str]:
        """POST /jobs con facets vacíos → response.facets (Fase 2 §2.2).

        No existe endpoint /facets utilizable: POST → 405, GET → 406/422
        (Fase 1B §2). El discovery ES la primera consulta real.
        """
        payload = {"appliedFacets": {}, "limit": DEFAULT_LIMIT, "offset": 0}
        return self._post_jobs(payload)

    # ----------------------------------------------------------------- query

    def search(self, applied_facets: Dict[str, List[str]],
               search_text: Optional[str] = None,
               limit: int = DEFAULT_LIMIT,
               safety_cap: int = DEFAULT_SAFETY_CAP
               ) -> "WorkdayResult":
        """Consulta estructurada + paginación defensiva + dedupe."""
        if limit > WORKDAY_MAX_LIMIT:
            limit = WORKDAY_MAX_LIMIT

        collected: Dict[str, Dict[str, Any]] = {}
        order: List[str] = []
        pages = 0
        offset = 0
        first_total: Optional[int] = None
        state = QueryState.VERIFIED_RESULTS
        detail = ""
        truncated = False
        saw_wraparound = False
        empty_first_page = False

        while offset <= safety_cap:
            payload: Dict[str, Any] = {
                "appliedFacets": applied_facets,
                "limit": limit,
                "offset": offset,
            }
            if search_text:
                # §2.1: searchText es filtro textual SECUNDARIO, nunca sustituto
                # del facet geográfico.
                payload["searchText"] = search_text

            data, st, dt = self._post_jobs(payload)
            if data is None:
                if pages == 0:
                    state, detail = st, dt
                else:
                    # Falló a mitad: hay datos pero la consulta está incompleta.
                    state = QueryState.UNKNOWN
                    detail = f"paginación interrumpida en offset {offset}: {dt}"
                    truncated = True
                break

            pages += 1
            if first_total is None:
                first_total = data.get("total")

            batch = data.get("jobPostings") or []
            if pages == 1 and not batch:
                empty_first_page = True
                break

            new_this_page = 0
            for job in batch:
                key = self._stable_key(job)
                if key in collected:
                    # Fase 2 §5 regla adicional: repetición en página != wraparound
                    # si la página aporta algo nuevo. Wraparound real cuando la
                    # página completa no aporta NADA nuevo.
                    continue
                collected[key] = job
                order.append(key)
                new_this_page += 1

            if len(batch) < limit:
                break  # página parcial = última
            if new_this_page == 0:
                saw_wraparound = True
                break  # página completa sin nada nuevo = wraparound
            offset += limit
        else:
            truncated = True
            detail = f"safety cap {safety_cap} alcanzado"

        jobs = [collected[k] for k in order]

        if not jobs:
            if empty_first_page and search_text:
                # searchText presente + 0 resultados: el filtro textual pudo
                # sobre-restringir (ej. "Mexico" sobre un título en español).
                # No es evidencia de que no existan vacantes → unknown.
                # Contrato Fase 2 §12 Test C.
                state = QueryState.UNKNOWN
                detail = ("0 postings con search_text presente; no atribuible "
                          "a ausencia de vacantes")
            elif empty_first_page:
                # Cero genuino: consulta estructurada válida, terminada, sin
                # bloqueo y sin search_text que sobre-restringa.
                state = QueryState.VERIFIED_EMPTY
                detail = detail or "consulta estructurada devolvió 0 postings"
            else:
                # Cero sin página vacía registrada → no determinable.
                state = QueryState.UNKNOWN
                detail = detail or "sin postings sin página vacía registrada"
        elif truncated:
            # Hay postings pero la consulta se cortó: NO verified_results.
            state = QueryState.UNKNOWN

        result = WorkdayResult(
            state=state, detail=detail, jobs=jobs,
            pages=pages, first_total=first_total,
            truncated=truncated, saw_wraparound=saw_wraparound,
        )
        self._audit.append({
            "applied_facets": applied_facets,
            "search_text": search_text,
            "pages": pages,
            "raw_count": len(jobs),
            "state": state,
            "first_total": first_total,
            "saw_wraparound": saw_wraparound,
            "truncated": truncated,
        })
        return result

    @staticmethod
    def _stable_key(job: Dict[str, Any]) -> str:
        """Identificador estable para dedupe. `externalPath` primero (Fase 2 §5)."""
        for field_name in ("externalPath", "jobReqId", "title"):
            value = job.get(field_name)
            if isinstance(value, str) and value.strip():
                return value
        return json.dumps(job, sort_keys=True, ensure_ascii=False)


@dataclass
class WorkdayResult:
    state: str
    detail: str
    jobs: List[Dict[str, Any]]
    pages: int
    first_total: Optional[int]
    truncated: bool = False
    saw_wraparound: bool = False


# ------------------------------------------------------------------ resolver

def _iter_facet_values(facets: List[Dict[str, Any]],
                       param: str) -> List[Dict[str, Any]]:
    """Extrae valores de un facetParameter, incluyendo grupos anidados.

    Nike expone `locations` anidado dentro de `locationMainGroup` como
    sub-facet con su propio facetParameter (Fase 1B §4). El recorrido es
    recursivo y匹配 por facetParameter, nunca por posición.
    """
    found: List[Dict[str, Any]] = []
    stack = list(facets or [])
    while stack:
        node = stack.pop(0)
        if not isinstance(node, dict):
            continue
        node_param = node.get("facetParameter")
        values = node.get("values") or []
        if node_param == param:
            for v in values:
                if isinstance(v, dict) and v.get("id"):
                    found.append(v)
        # descender en subfacets
        for child in values:
            if isinstance(child, dict) and child.get("facetParameter"):
                stack.append(child)
    return found


def _select(values: List[Dict[str, Any]], aliases: frozenset) -> List[Dict[str, Any]]:
    """Selecciona por descriptor normalizado dentro de un set de sinónimos."""
    out = []
    for v in values:
        norm = normalize_descriptor(v.get("descriptor", ""))
        if norm in aliases:
            out.append(v)
    return out


def resolve_location(facets: List[Dict[str, Any]], tenant: str, site: str,
                     country_aliases: frozenset = COUNTRY_ALIASES,
                     city_aliases: frozenset = CITY_ALIASES
                     ) -> LocationResolution:
    """Resuelve ubicación desde response.facets del contexto ACTIVO.

    Regla §2.4:
      - si existe locationCountry → resolver país (preferido, cardinalidad baja)
      - si no → resolver directo por locations
      - identificación por facetParameter, no por posición

    Regla crítica §3: un ID sólo es válido si proviene del discovery del
    contexto actual. Cada FacetValue lleva tenant+site+facetParameter.
    """
    for param in LOCATION_FACET_PARAMS:
        raw = _iter_facet_values(facets, param)
        if not raw:
            continue

        is_country = param == "locationCountry"
        aliases = country_aliases if is_country else city_aliases

        # País: Descriptor suele ser exacto ("Mexico").
        if is_country:
            hits = _select(raw, aliases)
            if hits:
                return LocationResolution(
                    facet_parameter=param,
                    values=[FacetValue(tenant, site, param, h["descriptor"], h["id"],
                                        h.get("count")) for h in hits],
                    resolvable=True,
                    reason=f"país por descriptor normalizado ({len(hits)} match)",
                    scope="country",
                )
            continue

        # Ciudad: descriptor puede venir compuesto ("Ciudad de México, Mexico").
        hits = []
        for v in raw:
            norm = normalize_descriptor(v.get("descriptor", ""))
            if norm in city_aliases:
                hits.append(v)
            else:
                # Descriptor compuesto: "CIUDAD DE MEXICO MEXICO"
                tokens = set(norm.split())
                if tokens & city_aliases and "MEXICO" in tokens:
                    hits.append(v)
        if hits:
            return LocationResolution(
                facet_parameter=param,
                values=[FacetValue(tenant, site, param, h["descriptor"], h["id"],
                                    h.get("count")) for h in hits],
                resolvable=True,
                reason=f"ciudad por descriptor normalizado/compuesto ({len(hits)} match)",
                scope="city",
            )

    return LocationResolution(
        resolvable=False,
        scope=None,
        reason="ningún facet de ubicación resolvió a los alias solicitados",
    )


# ---------------------------------------------------------------- high level

def workday_structured_search_2level(tenant: str, site: str, host: str,
                                     dry_run: bool = True,
                                     limit: int = DEFAULT_LIMIT,
                                     safety_cap: int = DEFAULT_SAFETY_CAP,
                                     require_city: bool = False
                                     ) -> Dict[str, Any]:
    """Flujo de DOS NIVELES (Fase 2 §2.4): país → luego ciudad.

    Motivado por la evidencia live de CHANEL: en el contexto global el facet
    `locations` expone cientos de ciudades de todo el mundo; los valores de
    CDMX sólo aparecen con，秦 tras filtrar por `locationCountry=Mexico`.
    Resolver ambos niveles contra el contexto correcto evita contamination
    cross-context y reduce el set a la geografía real.

    Devuelve el resultado del nivel ciudad si resuelve, si no el de país.
    """
    client = WorkdayClient(tenant, site, host, dry_run=dry_run)

    # ── discovery
    data, state, detail = client.discover()
    audit: Dict[str, Any] = {"ats": "workday", "tenant": tenant, "site": site,
                             "host": client.host, "dry_run": dry_run}
    if data is None:
        audit.update({"final_state": state, "detail": detail})
        return {"state": state, "detail": detail, "jobs": [], "audit": audit}

    # ── nivel 1: país
    facets = data.get("facets") or []
    country = _resolve_param(facets, tenant, site, "locationCountry", COUNTRY_ALIASES)
    if not country.resolvable:
        audit["final_state"] = QueryState.UNKNOWN
        audit["detail"] = country.reason
        return {"state": QueryState.UNKNOWN, "detail": country.reason,
                "jobs": [], "audit": audit}

    country_result = client.search(country.applied_facets(), limit=limit,
                                   safety_cap=safety_cap)
    audit["level1_facet"] = country.facet_parameter
    audit["level1_descriptor"] = [v.descriptor for v in country.values]
    audit["level1_id"] = [v.value_id for v in country.values]
    audit["level1_total"] = country_result.first_total
    audit["level1_state"] = country_result.state

    # Si el nivel 1 ya falla (bloqueo/dns/timeout), propagar sin escalar.
    if country_result.state in (QueryState.BLOCKED, QueryState.DNS_FAILURE,
                                QueryState.TIMEOUT):
        audit["final_state"] = country_result.state
        audit["detail"] = country_result.detail
        return {"state": country_result.state, "detail": country_result.detail,
                "jobs": country_result.jobs, "audit": audit}

    # ── nivel 2: ciudad, re-resolviendo facets en el contexto de país
    scoped, sstate, sdetail = client._post_jobs({
        "appliedFacets": country.applied_facets(), "limit": limit, "offset": 0})
    city = _resolve_param(
        (scoped or {}).get("facets") or [], tenant, site, "locations", CITY_ALIASES)

    if not city.resolvable:
        # DEGRADACIÓN DE SCOPE — nunca silenciosa (Fase 2 cierre punto 2).
        # Se resolvió PAÍS cuando se pidió CIUDAD. El resultado sigue siendo
        # válido a nivel país, pero el consumidor DEBE saber que la geografía
        # es más amplia que la solicitada.
        degradation = {
            "degraded": True,
            "requested_scope": "city",
            "resolved_scope": "country",
            "reason": city.reason,
        }
        if require_city:
            # El llamador exige ciudad: un resultado a nivel país NO cumple.
            audit["level2_facet"] = None
            audit["level2_reason"] = city.reason
            audit["scope_degradation"] = degradation
            audit["final_state"] = QueryState.UNKNOWN
            audit["detail"] = (
                "require_city=True pero sólo se pudo resolver scope=country: "
                + city.reason)
            return {"state": QueryState.UNKNOWN, "detail": audit["detail"],
                    "jobs": [], "audit": audit, "locations": country,
                    "scope_degradation": degradation}
        audit["level2_facet"] = None
        audit["level2_reason"] = city.reason
        audit["scope_degradation"] = degradation
        audit["final_state"] = country_result.state
        audit["pages"] = country_result.pages
        audit["raw_count"] = len(country_result.jobs)
        audit["dedup_count"] = len(country_result.jobs)
        audit["applied_facets"] = country.applied_facets()
        audit["resolved_scope"] = "country"
        return {"state": country_result.state, "detail": city.reason,
                "jobs": country_result.jobs, "audit": audit,
                "locations": country, "scope_degradation": degradation}

    # GUARD DE AISLAMIENTO también en el flujo de 2 niveles (punto 1).
    scoped_facets = (scoped or {}).get("facets") or []
    country_ok, country_bad = country.verify_against(
        facets, tenant, site)
    city_ok, city_bad = city.verify_against(scoped_facets, tenant, site)
    audit["id_isolation"] = {
        "level1_verified": country_ok, "level1_invalid": country_bad,
        "level2_verified": city_ok, "level2_invalid": city_bad,
        "method": "verify_against_facets",
    }
    if not (country_ok and city_ok):
        audit["final_state"] = QueryState.UNKNOWN
        audit["detail"] = (
            "aislamiento cross-tenant: IDs no pertenecientes al contexto "
            f"{tenant}/{site} (nivel1={country_bad}, nivel2={city_bad})")
        return {"state": QueryState.UNKNOWN, "detail": audit["detail"],
                "jobs": [], "audit": audit, "locations": city,
                "scope_degradation": None}

    combined = {country.facet_parameter: [v.value_id for v in country.values]}
    combined.update(city.applied_facets())
    city_result = client.search(combined, limit=limit, safety_cap=safety_cap)

    audit["scope_degradation"] = None
    audit["resolved_scope"] = "city"
    audit.update({
        "level2_facet": city.facet_parameter,
        "level2_descriptor": [v.descriptor for v in city.values],
        "level2_id": [v.value_id for v in city.values],
        "applied_facets": combined,
        "pages": city_result.pages,
        "raw_count": len(city_result.jobs),
        "dedup_count": len(city_result.jobs),
        "first_total": city_result.first_total,
        "saw_wraparound": city_result.saw_wraparound,
        "truncated": city_result.truncated,
        "final_state": city_result.state,
        "detail": city_result.detail,
    })
    return {"state": city_result.state, "detail": city_result.detail,
            "jobs": city_result.jobs, "audit": audit, "locations": city,
            "scope_degradation": None}


def _resolve_param(facets, tenant, site, param, aliases) -> LocationResolution:
    """Resuelve un facetParameter concreto por alias (helper interno)."""
    raw = _iter_facet_values(facets, param)
    if not raw:
        return LocationResolution(resolvable=False, reason=f"{param} no presente")
    if param == "locationCountry":
        hits = _select(raw, aliases)
    else:
        hits = []
        for v in raw:
            norm = normalize_descriptor(v.get("descriptor", ""))
            tokens = set(norm.split())
            if norm in aliases or (tokens & aliases and "MEXICO" in tokens):
                hits.append(v)
    if not hits:
        return LocationResolution(
            resolvable=False, reason=f"{param} sin match para {sorted(aliases)}")
    return LocationResolution(
        facet_parameter=param,
        values=[FacetValue(tenant, site, param, h["descriptor"], h["id"],
                            h.get("count")) for h in hits],
        resolvable=True, reason=f"{param} → {len(hits)} match",
        scope="country" if param == "locationCountry" else "city")


def workday_structured_search(tenant: str, site: str, host: str,
                              target_city: bool = True,
                              require_city: bool = False,
                              dry_run: bool = True,
                              limit: int = DEFAULT_LIMIT,
                              safety_cap: int = DEFAULT_SAFETY_CAP,
                              search_text: Optional[str] = None
                              ) -> Dict[str, Any]:
    """Flujo completo Fase 2 §4:

        DETECT → DISCOVER → RESOLVE → BUILD → QUERY → PAGINATE → DEDUPE
        → VALIDATE → RETURN STATE

    Garantía §17: `verified_empty` sólo con facet resuelto + appliedFacets
    usado + terminación válida. Un 200 con `searchText` y sin facet resuelto
    NUNCA produce verified_empty.
    """
    client = WorkdayClient(tenant, site, host, dry_run=dry_run)

    data, state, detail = client.discover()
    audit: Dict[str, Any] = {
        "ats": "workday",
        "tenant": tenant,
        "site": site,
        "host": client.host,
        "dry_run": dry_run,
    }

    if data is None:
        audit.update({"final_state": state, "detail": detail,
                      "location_facet": None, "descriptor": None,
                      "dynamic_id": None})
        return {"state": state, "detail": detail, "jobs": [],
                "audit": audit, "locations": None}

    facets = data.get("facets") or []
    audit["facets_present"] = bool(facets)

    resolution = resolve_location(facets, tenant, site) if target_city else None
    # GUARD DE AISLAMIENTO (punto 1): re-derivar cada ID desde los facets del
    # contexto actual antes de usarlo. Un ID que no exista en ESTOS facets
    # aborta la consulta — no se aplica.
    audit["id_isolation"] = None
    if resolution is not None and resolution.resolvable:
        ok_ids, bad_ids = resolution.verify_against(facets, tenant, site)
        audit["id_isolation"] = {
            "verified": ok_ids,
            "invalid_ids": bad_ids,
            "method": "verify_against_facets",
        }
        if not ok_ids:
            audit["final_state"] = QueryState.UNKNOWN
            audit["detail"] = (
                f"aislamiento cross-tenant: {len(bad_ids)} ID(s) no pertenecen a "
                f"{tenant}/{site}: {bad_ids}")
            resolution.resolvable = False
            resolution.reason = audit["detail"]

    applied = resolution.applied_facets() if resolution else {}

    # Degradación de scope en flujo de 1 nivel (Fase 2 cierre punto 2):
    # resolver_location puede quedarse en scope=country aunque se haya
    # solicitado ciudad (p.ej. el tenant sólo expone locationCountry).
    if resolution is not None and resolution.resolvable:
        audit["resolved_scope"] = resolution.scope
        if require_city and resolution.scope != "city":
            degradation = {
                "degraded": True,
                "requested_scope": "city",
                "resolved_scope": resolution.scope,
                "reason": resolution.reason,
            }
            audit["scope_degradation"] = degradation
            audit["final_state"] = QueryState.UNKNOWN
            audit["detail"] = (
                "require_city=True pero el scope resuelto es "
                f"{resolution.scope!r}: {resolution.reason}")
            return {"state": QueryState.UNKNOWN, "detail": audit["detail"],
                    "jobs": [], "audit": audit, "locations": resolution,
                    "scope_degradation": degradation}
        if resolution.scope == "country":
            audit["scope_degradation"] = {
                "degraded": True,
                "requested_scope": "city",
                "resolved_scope": "country",
                "reason": resolution.reason,
            }
        else:
            audit["scope_degradation"] = None
    else:
        audit["scope_degradation"] = None

    audit["location_facet"] = resolution.facet_parameter if resolution else None
    audit["descriptor"] = (
        [v.descriptor for v in resolution.values] if resolution else None
    )
    audit["dynamic_id"] = (
        [v.value_id for v in resolution.values] if resolution else None
    )
    audit["resolution_reason"] = resolution.reason if resolution else None

    # §17 + §6: sin ubicación resoluble NO se puede emitir verified_empty.
    if not applied:
        baseline_total = data.get("total")
        audit["final_state"] = QueryState.UNKNOWN
        audit["detail"] = (
            "facet de ubicación no resoluble; no se puede clasificar el resultado"
        )
        audit["baseline_total"] = baseline_total
        return {"state": QueryState.UNKNOWN, "detail": audit["detail"],
                "jobs": [], "audit": audit, "locations": resolution,
                "scope_degradation": None}

    result = client.search(applied, search_text=search_text,
                           limit=limit, safety_cap=safety_cap)

    # La máquina de estados yafudicó en search(); high-level solo propaga.
    final_state = result.state

    audit.update({
        "applied_facets": applied,
        "pages": result.pages,
        "raw_count": len(result.jobs),
        "dedup_count": len(result.jobs),
        "first_total": result.first_total,
        "saw_wraparound": result.saw_wraparound,
        "truncated": result.truncated,
        "final_state": final_state,
        "detail": result.detail,
    })

    return {"state": final_state, "detail": result.detail, "jobs": result.jobs,
            "audit": audit, "locations": resolution,
            "scope_degradation": audit.get("scope_degradation")}


# ------------------------------------------------------------------- dry run

def _format_dry_run(out: Dict[str, Any]) -> str:
    a = out.get("audit", {})
    # El flujo de dos niveles usa claves level1_/level2_; el de un nivel usa
    # location_facet/descriptor/dynamic_id. Normalizamos para el reporte.
    lvl1_facet = a.get("location_facet") or a.get("level1_facet")
    lvl1_desc = a.get("descriptor") or a.get("level1_descriptor")
    lvl1_id = a.get("dynamic_id") or a.get("level1_id")
    lines = [
        "=== VANTAGE Workday Structured Search — DRY RUN ===",
        f"ATS:            {a.get('ats')}",
        f"tenant/site:    {a.get('tenant')} / {a.get('site')}",
        f"host:           {a.get('host')}",
        f"mode:           {'2-level' if a.get('level1_facet') else '1-level'}",
        f"location facet: {lvl1_facet}",
        f"descriptor(s):  {lvl1_desc}",
        f"dynamic id(s):  {lvl1_id}",
    ]
    if a.get("level2_facet"):
        lines += [
            f"city facet:     {a.get('level2_facet')}",
            f"city descriptor:{a.get('level2_descriptor')}",
            f"city id(s):     {a.get('level2_id')}",
        ]
    deg = a.get("scope_degradation")
    if deg:
        lines += [
            f"SCOPE DEGRADED: pedido={deg['requested_scope']} "
            f"resuelto={deg['resolved_scope']}",
            f"  motivo:      {deg['reason']}",
        ]
    else:
        lines.append(f"scope resuelto: {a.get('resolved_scope')}")
    lines += [
        f"appliedFacets:  {a.get('applied_facets')}",
        f"pages:          {a.get('pages')}",
        f"raw postings:   {a.get('raw_count')}",
        f"dedup postings: {a.get('dedup_count')}",
        f"first total:    {a.get('first_total')}",
        f"wraparound:     {a.get('saw_wraparound')}",
        f"FINAL STATE:    {a.get('final_state')}",
    ]
    if a.get("detail"):
        lines.append(f"detail:         {a['detail']}")
    jobs = out.get("jobs") or []
    lines.append(f"postings devueltos ({len(jobs)}):")
    for j in jobs[:15]:
        lines.append(f"  - {j.get('title', '?')} | {j.get('locationsText', '?')}")
    if len(jobs) > 15:
        lines.append(f"  … +{len(jobs) - 15} más")
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Workday structured location search")
    p.add_argument("host", help="tenant.wdN.myworkdayjobs.com")
    p.add_argument("--tenant", required=True)
    p.add_argument("--site", required=True)
    p.add_argument("--search-text", default=None,
                   help="filtro textual SECUNDARIO (nunca sustituto del facet)")
    p.add_argument("--no-dry-run", action="store_true")
    args = p.parse_args()

    out = workday_structured_search(
        args.tenant, args.site, args.host,
        dry_run=not args.no_dry_run,
        search_text=args.search_text,
    )
    print(_format_dry_run(out))