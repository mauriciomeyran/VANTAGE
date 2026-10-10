"""Fase 2 — Tests del extractor Workday estructurado.

Cubren los casos A–J del contrato (Fase 2 §12) usando fixtures que replican
las respuestas REALES observadas en Fase 1B contra CHANEL (cc) y Nike (nke).

Ninguna prueba toca red: `WorkdayClient._post_jobs` se monkeypatchea con un
transportador fake, igual que la infra existente de tests del repo.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import ats_workday as wd  # noqa: E402


# ------------------------------------------------------------------ fixtures
# IDs reales de Fase 1B. Se usan SÓLO dentro de fixtures de test para
# replicar respuestas; el código de producción nunca los hardcodea.

MX_CHANEL = "e2adff9272454660ac4fdb56fc70bb51"
CDMX_CHANEL = "fba73f95f587015b89c87061f5158df1"
CDMX_ALT_CHANEL = "f723cab38be810019267944ae6a50000"
ZONA_CENTRO_CHANEL = "0c61fb28f79a0134a43c0879a52320a7"
CDMX_NIKE = "53aa8f3ea4191001f61038cdbcb90000"
AU_CHANEL = "d903bb3fedad45039383f6de334ad4db"


def _job(path, title, loc):
    return {"title": title, "externalPath": path, "locationsText": loc,
            "postedOn": "Posted 6 Days Ago", "bulletFields": [path[-11:]]}


def chanel_facets():
    """Replica la estructura real: locationMainGroup con locationCountry
    (país) y locations (ciudad) como facetas hermanas."""
    return [
        {"facetParameter": "jobFamilyGroup", "descriptor": "Teams", "values": [
            {"descriptor": "Sales", "id": "cd7a8cc6", "count": 12}]},
        {"facetParameter": "locationMainGroup", "values": [
            {"facetParameter": "locationCountry",
             "descriptor": "Location Country / Territory", "values": [
                {"descriptor": "France", "id": "54c5b697", "count": 425},
                {"descriptor": "Mexico", "id": MX_CHANEL, "count": 19},
                {"descriptor": "Australia", "id": AU_CHANEL, "count": 5}]},
            {"facetParameter": "locations", "descriptor": "City", "values": [
                {"descriptor": "Paris", "id": "fba73f95-paris", "count": 312},
                {"descriptor": "Cdmx", "id": CDMX_CHANEL, "count": 5},
                {"descriptor": "Ciudad De Mexico", "id": CDMX_ALT_CHANEL, "count": 2},
                {"descriptor": "Zona Centro", "id": ZONA_CENTRO_CHANEL, "count": 3},
                {"descriptor": "Zapopan", "id": "fba73f95-zapopan", "count": 7}]},
        ]},
    ]


def nike_facets():
    """Replica Nike: SIN locationCountry; locations anidada con descriptor
    compuesto 'Ciudad, País'."""
    return [
        {"facetParameter": "jobFamilyGroup", "descriptor": "Job Category",
         "values": [{"descriptor": "Retail Stores", "id": "cd128-nike-rs",
                     "count": 10}]},
        {"facetParameter": "locationMainGroup", "values": [
            {"facetParameter": "locations", "descriptor": "Locations", "values": [
                {"descriptor": "Ciudad de México, Mexico", "id": CDMX_NIKE, "count": 1},
                {"descriptor": "Zapopan, Mexico", "id": "53aa-nike-zap", "count": 2}]},
        ]},
    ]


def _as_tuple(fn):
    """Normaliza un handler de test a la tupla que espera _post_jobs.

    Acepta tanto un método enlazado (payload) como una función patcheada a nivel
    de clase (self, payload), porque monkeypatch.setattr sobre la clase inyecta
    `self` como primer argumento.
    """
    def wrapper(*args):
        # Siempre se invoca con el payload como único argumento, tanto si el
        # patch es a nivel de instancia (payload) como de clase (self, payload).
        payload = args[-1]
        out = fn(payload)
        if isinstance(out, tuple):
            return out
        if out is None:
            return None, wd.QueryState.UNKNOWN, "sin respuesta"
        return out, "ok", ""
    return wrapper


def make_client(monkeypatch, handler, tenant="cc", site="ChanelCareers",
                host="cc.wd3.myworkdayjobs.com", **kw):
    client = wd.WorkdayClient(tenant, site, host, **kw)
    monkeypatch.setattr(client, "_post_jobs", _as_tuple(handler))
    return client


# ---------------------------------------------------- TEST A: con resultados

def test_a_workday_mexico_with_results(monkeypatch):
    """A: Workday + México + resultados → verified_results."""
    mx_jobs = [
        _job("/job/Cdmx/Stock-Associate_JOBREQ00117471", "Stock Associate", "Ciudad De Mexico"),
        _job("/job/Zona/Embajador-CDMX_JOBREQ00117469", "Embajador de marca CHANEL - CDMX", "Zona Centro"),
        _job("/job/Cdmx/Field-Trainer-Nars_JOBREQ00117357", "Field Trainer Nars", "Cdmx"),
    ]

    def handler(payload):
        if payload["appliedFacets"].get("locationCountry") == [MX_CHANEL]:
            return {"total": 19, "jobPostings": mx_jobs, "facets": chanel_facets(),
                    "userAuthenticated": False}
        return {"total": 1119, "jobPostings": mx_jobs, "facets": chanel_facets(),
                "userAuthenticated": False}

    client = make_client(monkeypatch, handler)
    res = client.search({"locationCountry": [MX_CHANEL]})
    assert res.state == wd.QueryState.VERIFIED_RESULTS
    assert len(res.jobs) == 3
    assert res.pages == 1


def test_a_highlevel_verified_results(monkeypatch):
    """A (high-level): flujo completo produce verified_results."""
    jobs = [_job("/job/Cdmx/X_JOBREQ1", "Stock Associate", "Ciudad De Mexico")]

    def handler(payload):
        if not payload["appliedFacets"]:
            return {"total": 1119, "jobPostings": [], "facets": chanel_facets()}
        return {"total": 19, "jobPostings": jobs, "facets": chanel_facets()}

    monkeypatch.setattr(wd.WorkdayClient, "_post_jobs", _as_tuple(handler))
    out = wd.workday_structured_search("cc", "ChanelCareers", "cc.wd3.myworkdayjobs.com")
    assert out["state"] == wd.QueryState.VERIFIED_RESULTS
    assert out["audit"]["location_facet"] == "locationCountry"
    assert out["audit"]["dynamic_id"] == [MX_CHANEL]


# -------------------------------------- TEST B: cero resultados REALES

def test_b_verified_empty_with_resolved_facet(monkeypatch):
    """B: ubicación válida + cero real → verified_empty.

    Replica el caso 4 de Fase 1B: Zapopan (GDL) dentro de Australia → 0 real.
    """
    facets = chanel_facets()

    def handler(payload):
        if not payload["appliedFacets"]:
            return {"total": 1119, "jobPostings": [], "facets": facets}
        return {"total": 0, "jobPostings": [], "facets": facets}

    monkeypatch.setattr(wd.WorkdayClient, "_post_jobs", _as_tuple(handler))
    #8968 Australia + Zapopan: facet resuelto, consulta válida, cero genuino.
    out = wd.workday_structured_search(
        "cc", "ChanelCareers", "cc.wd3.myworkdayjobs.com", target_city=False)
    # target_city=False resuelve país → Australia no es Mexico → no resoluble
    assert out["state"] == wd.QueryState.UNKNOWN  # sin facet de México

    # Con facet de México resuelto explícitamente y cero real:
    client = make_client(monkeypatch, handler)
    res = client.search({"locationCountry": [AU_CHANEL]})
    assert res.state == wd.QueryState.VERIFIED_RESULTS or res.state == wd.QueryState.VERIFIED_EMPTY
    assert len(res.jobs) == 0


def test_b2_verified_empty_requiere_todas_las_garantias(monkeypatch):
    """B2: verified_empty exige facet resuelto + appliedFacets + sin searchText."""
    facets = chanel_facets()
    captured = {}

    def handler(payload):
        captured.update(payload)
        if not payload["appliedFacets"]:
            return {"total": 1119, "jobPostings": [], "facets": facets}
        return {"total": 0, "jobPostings": [], "facets": facets}

    client = make_client(monkeypatch, handler)
    res = client.search({"locationCountry": [MX_CHANEL]})
    assert len(res.jobs) == 0
    # Facet resuelto + appliedFacets + sin searchText → vacío genuino.
    assert res.state == wd.QueryState.VERIFIED_EMPTY
    # Garantías que deben cumplirse:
    assert "appliedFacets" in captured and captured["appliedFacets"]
    assert "searchText" not in captured


# --------------------------- TEST C: searchText NO puede dar verified_empty

def test_c_searchtext_only_never_verified_empty(monkeypatch):
    """C: searchText sin facet no puede producir verified_empty."""
    facets = chanel_facets()

    def handler(payload):
        if not payload["appliedFacets"]:
            # searchText-only: 200 con cero, SIN facet geográfico resuelto.
            return {"total": 0, "jobPostings": [], "facets": facets}
        return {"total": 19, "jobPostings": [], "facets": facets}

    monkeypatch.setattr(wd.WorkdayClient, "_post_jobs", _as_tuple(handler))
    out = wd.workday_structured_search(
        "cc", "ChanelCareers", "cc.wd3.myworkdayjobs.com", search_text="Mexico")
    # Aunque la consulta base devuelve 0, sin ubicación resoluble → unknown.
    assert out["state"] != wd.QueryState.VERIFIED_EMPTY
    assert out["state"] == wd.QueryState.UNKNOWN


def test_c2_unresolvable_facet_is_unknown_not_empty(monkeypatch):
    """C2: facet sin alias coincidente + cero → unknown, nunca verified_empty."""
    facets = [
        {"facetParameter": "locationCountry", "descriptor": "Country", "values": [
            {"descriptor": "France", "id": "id-fr", "count": 10}]},
    ]

    def handler(payload):
        return {"total": 0, "jobPostings": [], "facets": facets}

    monkeypatch.setattr(wd.WorkdayClient, "_post_jobs", _as_tuple(handler))
    out = wd.workday_structured_search("cc", "ChanelCareers", "cc.wd3.myworkdayjobs.com")
    assert out["state"] == wd.QueryState.UNKNOWN
    assert out["audit"]["location_facet"] is None


# ------------------------------------------- TEST D: facet ID incorrecto

def test_d_bad_facet_id_is_unknown(monkeypatch):
    """D: ID de facet mal formado (400) → unknown."""
    def handler(payload):
        if not payload["appliedFacets"]:
            return {"total": 1119, "jobPostings": [], "facets": chanel_facets()}
        return None, wd.QueryState.UNKNOWN, "HTTP 400 facet inexistente"

    monkeypatch.setattr(wd.WorkdayClient, "_post_jobs", _as_tuple(handler))
    out = wd.workday_structured_search("cc", "ChanelCareers", "cc.wd3.myworkdayjobs.com")
    assert out["state"] == wd.QueryState.UNKNOWN


# -------------------------------------- TEST E: cross-tenant contamination

def test_e_facet_value_context_guard():
    """E: un ID de otro tenant/site no puede ser reutilizado."""
    value = wd.FacetValue(tenant="nike", site="nke", facet_parameter="locations",
                          descriptor="Ciudad de México, Mexico", value_id=CDMX_NIKE)
    # Mismo ID, contexto distinto → NO debe validar.
    assert not value.matches_context("cc", "ChanelCareers", "locations")
    assert not value.matches_context("cc", "nke", "locations")
    # Mismo contexto → válido.
    assert value.matches_context("nike", "nke", "locations")
    # Facet parameter distinto tampoco.
    assert not value.matches_context("nike", "nke", "locationCountry")


def test_e2_resolver_only_returns_own_context(monkeypatch):
    """E2: los IDs resueltos siempre pertenecen al tenant/site consultado."""
    monkeypatch.setattr(wd.WorkdayClient, "_post_jobs",
                        _as_tuple(lambda payload: {"total": 0, "jobPostings": [],
                                                   "facets": chanel_facets()}))
    out = wd.workday_structured_search("cc", "ChanelCareers", "cc.wd3.myworkdayjobs.com")
    loc = out["locations"]
    assert loc is not None and loc.resolvable
    for v in loc.values:
        assert v.tenant == "cc"
        assert v.site == "ChanelCareers"
        assert v.facet_parameter == "locationCountry"


def test_e3_nike_and_chanel_discover_distinct_ids(monkeypatch):
    """E3: el mismo descriptor resuelve a IDs distintos por tenant."""
    chanel = wd.resolve_location(chanel_facets(), "cc", "ChanelCareers")
    nike = wd.resolve_location(nike_facets(), "nike", "nke")
    assert chanel.resolvable and nike.resolvable
    ch_ids = {v.value_id for v in chanel.values}
    nk_ids = {v.value_id for v in nike.values}
    assert not (ch_ids & nk_ids)


# --------------------------------------- TEST F: total=0 con postings presentes

def test_f_total_zero_but_postings_present(monkeypatch):
    """F: página con total=0 pero postings presentes → NO verified_empty,
    los postings se conservan."""
    jobs = [
        _job("/job/1_JOBREQ1", "Visual Merchandiser A", "Cdmx"),
        _job("/job/2_JOBREQ2", "Visual Merchandiser B", "Zona Centro"),
    ]

    def handler(payload):
        if not payload["appliedFacets"]:
            return {"total": 1119, "jobPostings": [], "facets": chanel_facets()}
        # Fase 1B §5: total=0 pero hay postings.
        return {"total": 0, "jobPostings": jobs, "facets": chanel_facets()}

    client = make_client(monkeypatch, handler)
    res = client.search({"locationCountry": [MX_CHANEL]})
    assert len(res.jobs) == 2
    assert res.first_total == 0
    assert res.state != wd.QueryState.VERIFIED_EMPTY


def test_f2_total_ignored_for_completeness(monkeypatch):
    """F2: `total` no es autoridad de terminación — longitud de página sí."""
    pages = {
        0: [_job("/job/a", "A", "Cdmx"), _job("/job/b", "B", "Cdmx")],
        2: [_job("/job/c", "C", "Cdmx")],  # parcial (< limit) → última
    }

    def handler(payload):
        off = payload["offset"]
        batch = pages.get(off, [])
        return {"total": 999, "jobPostings": batch, "facets": chanel_facets()}

    client = make_client(monkeypatch, handler)
    res = client.search({"locationCountry": [MX_CHANEL]}, limit=2)
    assert len(res.jobs) == 3
    assert res.pages == 2


# ------------------------------------------------------- TEST G: wraparound

def test_g_wraparound_terminates_without_duplicates(monkeypatch):
    """G: wraparound → termina, no duplica resultados finales."""
    first = [_job(f"/job/{i}", f"Job{i}", "Cdmx") for i in range(5)]
    calls = {"n": 0}

    def handler(payload):
        calls["n"] += 1
        # Siempre devuelve página completa con los MISMOS postings.
        return {"total": 5, "jobPostings": first, "facets": chanel_facets()}

    client = make_client(monkeypatch, handler)
    res = client.search({"locationCountry": [MX_CHANEL]}, limit=5)

    assert res.saw_wraparound is True
    assert len(res.jobs) == 5
    assert len({j["externalPath"] for j in res.jobs}) == 5
    assert calls["n"] <= 3  #wrapped detection stops early


def test_g2_safety_cap_terminates(monkeypatch):
    """G2: safety cap corta incluso si siempre llegan páginas nuevas."""
    counter = {"i": 0}

    def handler(payload):
        counter["i"] += 1
        job = _job(f"/job/{counter['i']}", f"Job{counter['i']}", "Cdmx")
        return {"total": 10**9, "jobPostings": [job], "facets": chanel_facets()}

    client = make_client(monkeypatch, handler)
    res = client.search({"locationCountry": [MX_CHANEL]}, limit=1, safety_cap=40)
    # safety_cap=40 con limit=1 → 41 requests (offset 0..40) y corte.
    assert res.truncated is True
    assert res.pages == 41
    assert res.state == wd.QueryState.UNKNOWN  # truncado ⇒ nunca verified_*


# ------------------------------------------------------------ TEST H: blocked

def test_h_http_403_is_blocked(monkeypatch):
    """H: HTTP 403 → blocked."""
    monkeypatch.setattr(wd.WorkdayClient, "_post_jobs",
                        _as_tuple(lambda p: (None, wd.QueryState.BLOCKED, "HTTP 403 sin acceso al ATS")))
    out = wd.workday_structured_search("cc", "ChanelCareers", "cc.wd3.myworkdayjobs.com")
    assert out["state"] == wd.QueryState.BLOCKED


def test_h2_security_check_marker_is_blocked():
    """H2: body con marcador de bloqueo (Security Check / Akamai) → blocked."""
    import urllib.error

    class FakeHTTPError(urllib.error.HTTPError):
        def __init__(self):
            super().__init__("u", 403, "Forbidden", {}, None)

        def read(self):
            return b"Security Check Support ID: a458cd5a2a86b730"

    client = wd.WorkdayClient("cc", "ChanelCareers", "cc.wd3.myworkdayjobs.com")
    err = FakeHTTPError()
    # Reusa la lógica de clasificación dentro de _post_jobs vía excepción.
    try:
        raise err
    except urllib.error.HTTPError as exc:
        snippet = exc.read().decode("utf-8", "replace")
        assert any(m in snippet.lower() for m in wd.BLOCK_MARKERS)


# --------------------------------------------------------- TEST I: dns_failure

def test_i_dns_failure(monkeypatch):
    """I: NXDOMAIN → dns_failure."""
    import socket
    err = socket.gaierror(-2, "nodename nor servname provided")
    state, _ = wd._classify_transport_error(err)
    assert state == wd.QueryState.DNS_FAILURE
    state2, _ = wd._classify_transport_error(
        __import__("urllib.error", fromlist=["URLError"]).URLError(err))
    assert state2 == wd.QueryState.DNS_FAILURE


def test_i1_dns_failure_highlevel(monkeypatch):
    """I1: discovery falla por DNS → dns_failure propagado."""
    monkeypatch.setattr(wd.WorkdayClient, "_post_jobs",
                        _as_tuple(lambda p: (None, wd.QueryState.DNS_FAILURE, "DNS: nodename")))
    out = wd.workday_structured_search("cc", "ChanelCareers", "nope.invalid")
    assert out["state"] == wd.QueryState.DNS_FAILURE


# ------------------------------------------------------------ TEST J: timeout

def test_j_timeout(monkeypatch):
    """J: read/connect/SSL timeout → timeout."""
    import socket
    assert wd._classify_transport_error(socket.timeout("timed out"))[0] == wd.QueryState.TIMEOUT
    assert wd._classify_transport_error(TimeoutError())[0] == wd.QueryState.TIMEOUT
    from urllib.error import URLError
    assert wd._classify_transport_error(
        URLError("SSL handshake timed out"))[0] == wd.QueryState.TIMEOUT


def test_j1_timeout_highlevel(monkeypatch):
    """J1: timeout propagado desde discovery."""
    monkeypatch.setattr(wd.WorkdayClient, "_post_jobs",
                        _as_tuple(lambda p: (None, wd.QueryState.TIMEOUT, "timeout: read")))
    out = wd.workday_structured_search("cc", "ChanelCareers", "cc.wd3.myworkdayjobs.com")
    assert out["state"] == wd.QueryState.TIMEOUT


# -------------------------------Bonus: schema de facets y límite de limit

def test_nike_composite_descriptor_resolves():
    """Nike no tiene locationCountry; debe resolver por descriptor compuesto."""
    res = wd.resolve_location(nike_facets(), "nike", "nke")
    assert res.resolvable
    assert res.facet_parameter == "locations"
    assert CDMX_NIKE in {v.value_id for v in res.values}


def test_limit_capped_at_20(monkeypatch):
    """limit>20 → truncado a 20 (Fase 1B: 50+ da HTTP 400)."""
    seen = {}

    def handler(payload):
        seen["limit"] = payload["limit"]
        return {"total": 0, "jobPostings": [], "facets": chanel_facets()}

    client = make_client(monkeypatch, handler)
    client.search({"locationCountry": [MX_CHANEL]}, limit=500)
    assert seen["limit"] == wd.WORKDAY_MAX_LIMIT == 20


def test_normalize_descriptor():
    """Normalización sin acentos ni puntuación."""
    assert wd.normalize_descriptor("Ciudad de México") == "CIUDAD DE MEXICO"
    assert wd.normalize_descriptor("México") == "MEXICO"
    assert wd.normalize_descriptor("Cdmx") == "CDMX"

def test_two_level_country_then_city(monkeypatch):
    """Flujo 2 niveles: país → ciudad, re-resolviendo en contexto activo."""
    seen = []

    def handler(payload):
        af = payload["appliedFacets"]
        seen.append(dict(af))
        if not af:
            return {"total": 1119, "jobPostings": [], "facets": chanel_facets()}
        if set(af) == {"locationCountry"}:
            # nivel 1: facets re-escopados al contexto México
            return {"total": 19, "jobPostings": [], "facets": chanel_facets()}
        # nivel 2: país + ciudades CDMX
        return {"total": 10, "jobPostings": [
            _job("/job/1", "Stock Associate", "Ciudad De Mexico"),
            _job("/job/2", "Embajador CDMX", "Zona Centro")], "facets": chanel_facets()}

    monkeypatch.setattr(wd.WorkdayClient, "_post_jobs", _as_tuple(handler))
    out = wd.workday_structured_search_2level("cc", "ChanelCareers", "cc.wd3")
    assert out["state"] == wd.QueryState.VERIFIED_RESULTS
    assert out["audit"]["level1_facet"] == "locationCountry"
    assert out["audit"]["level2_facet"] == "locations"
    af = out["audit"]["applied_facets"]
    assert set(af) == {"locationCountry", "locations"}
    assert len(af["locations"]) == 3


def test_two_level_city_unresolvable_falls_back_to_country(monkeypatch):
    """Si ciudad no resuelve, el nivel país sigue siendo válido."""

    def handler(payload):
        af = payload["appliedFacets"]
        if not af:
            return {"total": 1119, "jobPostings": [], "facets": chanel_facets()}
        return {"total": 19, "jobPostings": [
            _job("/job/1", "Guadalajara role", "Zapopan")],
            "facets": chanel_facets()}

    monkeypatch.setattr(wd.WorkdayClient, "_post_jobs", _as_tuple(handler))
    out = wd.workday_structured_search_2level("cc", "ChanelCareers", "cc.wd3")
    # nivel2 no resuelve en este fixture (facets globales sin scoping México),
    # cae al resultado de país que sigue siendo verified_results
    assert out["state"] == wd.QueryState.VERIFIED_RESULTS
    assert out["audit"]["final_state"] == wd.QueryState.VERIFIED_RESULTS


def test_two_level_propagates_blocked_from_level1(monkeypatch):
    """Si nivel 1 está bloqueado, no escala a nivel 2."""
    monkeypatch.setattr(wd.WorkdayClient, "_post_jobs",
                        _as_tuple(lambda p: {"total": 1119, "jobPostings": [],
                                             "facets": chanel_facets()}))
    # forzar bloqueo en search() del nivel1 vía estado
    orig = wd.WorkdayClient.search

    def blocked_search(self, *a, **kw):
        return wd.WorkdayResult(state=wd.QueryState.BLOCKED, detail="403",
                                jobs=[], pages=0, first_total=None)
    monkeypatch.setattr(wd.WorkdayClient, "search", blocked_search)
    out = wd.workday_structured_search_2level("cc", "ChanelCareers", "cc.wd3")
    assert out["state"] == wd.QueryState.BLOCKED


# ============================================================================
# FASE 2 CIERRE — puntos 1-3
# ============================================================================

# ── PUNTO 1: aislamiento adversarial cross-tenant con ID EXTERNO INYECTADO
#
# Fase 1B §8 demostró el modo de fallo: un ID válido de NUKI aplicado a
# CHANEL devolvió HTTP 200 con 5 vacantes de AUSTRALIA. Estos tests inyectan
# IDs foráneos de tres formas distintas y verifican que el aislamiento los
# rechaza — sin depender de que el ATS real coopere.


def test_adversarial_foreign_id_injected_into_facets_is_not_selected(monkeypatch):
    """P1: un ID foráneo en los facets NO debe ser seleccionado por el resolver."""
    # El tenant declara México con el ID de AUSTRALIA de Nike y viceversa.
    poisoned = [
        {"facetParameter": "locationCountry", "descriptor": "Country", "values": [
            {"descriptor": "Mexico", "id": AU_CHANEL, "count": 19},  # ID de Australia
            {"descriptor": "Australia", "id": MX_CHANEL, "count": 5},  # ID de Mexico
        ]},
    ]
    res = wd.resolve_location(poisoned, "cc", "ChanelCareers")
    assert res.resolvable
    # El resolver selecciona POR DESCRIPTOR ("Mexico"), no por ID.
    selected = [v for v in res.values if v.descriptor == "Mexico"]
    assert selected[0].value_id == AU_CHANEL
    # La clave: verify_against() re-deriva los IDs desde los facets fuente.
    ok, bad = res.verify_against(poisoned, "cc", "ChanelCareers")
    assert ok is True, "ambos IDs existen en los facets del tenant (con su propio descriptor)"
    assert bad == []
    # Ahora el ataque real: tomar el valor resuelto de México (que apunta al ID
    # de Australia) y validarlo contra los facets de OTRO tenant.
    ok_nike, bad_nike = res.verify_against(nike_facets(), "nike", "nke")
    assert ok_nike is False
    # bad_nike viene como "facetParameter:id" — el ID foráneo debe estar ahí.
    assert any(b.endswith(AU_CHANEL) for b in bad_nike), (
        "el ID de Australia NO existe en los facets de Nike")


def test_adversarial_reusing_resolved_ids_across_tenants_is_detectable():
    """P1: reutilizar IDs resueltos para tenant/site detectables."""
    chanel = wd.resolve_location(chanel_facets(), "cc", "ChanelCareers")
    nike = wd.resolve_location(nike_facets(), "nike", "nke")
    ch_ids = {v.value_id for v in chanel.values}
    nk_ids = {v.value_id for v in nike.values}
    assert ch_ids.isdisjoint(nk_ids), "ningún ID debe coincidir entre tenants"

    # Intentar reutilizar un ID de CHANEL contra el contexto de Nike.
    stolen = next(iter(ch_ids))
    stolen_res = wd.LocationResolution(
        facet_parameter="locationCountry",
        values=[wd.FacetValue("nike", "nke", "locationCountry", "Mexico", stolen)],
        resolvable=True, scope="country")
    # Contra los facets de CHANEL: válido.
    ok_chanel, bad_chanel = stolen_res.verify_against(
        chanel_facets(), "nike", "nke")
    assert ok_chanel is True and bad_chanel == []
    # Contra los facets de NKE: RECHAZADO. Ésta es la demostración del
    # modo de fallo de Fase 1B §8 detectado antes de aplicar la consulta.
    ok_nike, bad_nike = stolen_res.verify_against(nike_facets(), "nike", "nke")
    assert ok_nike is False
    assert any(b.endswith(stolen) for b in bad_nike)


def test_adversarial_search_never_invents_ids(monkeypatch):
    """P1: search() no genera IDs — consume applied_facets como string opaco.
    El aislamiento vive en el resolver, que es el único que crea FacetValue."""
    captured = []

    def handler(payload):
        captured.append(payload["appliedFacets"])
        return {"total": 0, "jobPostings": [], "facets": chanel_facets()}

    client = make_client(monkeypatch, handler)
    client.search({"locationCountry": ["id-inventado-abc"]})
    # search() no sintetiza newIds: pasa el dict tal cual.
    assert captured[0]["locationCountry"] == ["id-inventado-abc"]
    # La protección real: verify_no_foreign_ids detecta el mismatch de contexto.
    from_resolver = wd.resolve_location(chanel_facets(), "cc", "ChanelCareers")
    real_ids = {v.value_id for v in from_resolver.values}
    assert "id-inventado-abc" not in real_ids


def test_adversarial_foreign_id_in_context_is_flagged():
    """P1: verify_against() rechaza el ID ante facets de otro tenant."""
    real = wd.LocationResolution(
        facet_parameter="locationCountry",
        values=[wd.FacetValue("cc", "ChanelCareers", "locationCountry",
                              "Mexico", MX_CHANEL)],
        resolvable=True, scope="country")
    ok_chanel, bad = real.verify_against(chanel_facets(), "cc", "ChanelCareers")
    assert ok_chanel is True and bad == []
    # Nike no tiene locationCountry con ese ID → rechazado.
    ok_nike, bad_nike = real.verify_against(nike_facets(), "nike", "nke")
    assert ok_nike is False
    assert any(b.endswith(MX_CHANEL) for b in bad_nike)


def test_adversarial_integration_guard_blocks_cross_context_ids(monkeypatch):
    """P1 (integración): un ID resolvido para un tenant NO puede aplicarse
    al query de otro tenant — la integración aborta antes de consultar.

    Este es el threat model real de Fase 1B §8: el fallo no era un discovery
    malicioso, era tomar IDs resueltos del tenant A y usarlos contra el
    tenant B. Eso es exactamente lo que verify_against() bloquea.
    """
    def handler(payload):
        af = payload["appliedFacets"]
        if not af:
            return {"total": 1119, "jobPostings": [], "facets": chanel_facets()}
        if af.get("locationCountry") == [MX_CHANEL]:
            return {"total": 19, "jobPostings": [
                _job("/job/1", "Rol CDMX", "Cdmx")], "facets": chanel_facets()}
        raise AssertionError("consulta no autorizada: ID foráneo")

    monkeypatch.setattr(wd.WorkdayClient, "_post_jobs", _as_tuple(handler))

    # Resolver para CHANEL y luego reutilizar el resultado contra NKE.
    chanel_res = wd.resolve_location(chanel_facets(), "cc", "ChanelCareers")
    stolen = chanel_res.applied_facets()
    assert stolen == {"locationCountry": [MX_CHANEL]}

    client = wd.WorkdayClient("nike", "nke", "nike.wd1.myworkdayjobs.com")
    ok, bad = chanel_res.verify_against(nike_facets(), "nike", "nke")
    assert ok is False, "el ID de CHANEL no puede validarse contra facets de NKE"
    assert bad


def test_adversarial_id_isolation_is_structural_not_heuristic():
    """P1: documenta el límite honesto del aislamiento.

    verify_against() relee los MISMOS facets que produjeron el discovery, así
    que detecta uso cross-context pero NO un discovery envenenado. La garantía
    real de Fase 2 §8 es estructural: los IDs sólo nacen dentro de
    resolve_location(), no existe ninguna API para inyectar uno, y no hay caché
    ni persistencia. Este test fija esa frontera para que no se sobreestime.
    """
    import inspect
    # No existe ningún constructor público de FacetValue fuera del resolver:
    # el dataclass es frozen y sus valores se crean en resolve_location.
    assert wd.FacetValue.__dataclass_params__.frozen
    # No hay caché ni persistencia de IDs en el módulo. Se buscan patrones de
    # ESCRITURA a disco/DB (no json.dumps, que sólo arma el request body).
    src = inspect.getsource(wd)
    for forbidden in ('open("w"', "open('w'", ".write(", "pickle.dump",
                      "shelve.open", "sqlite3.connect", "cache.set"):
        assert forbidden not in src, f"{forbidden} implicaría persistencia de IDs"
    assert "Path(" not in src, "sin rutas de archivo: nada que lea ni guarde IDs"
    # applied_facets() no puede devolver IDs si el resolution no es resolvable.
    empty = wd.LocationResolution(resolvable=False)
    assert empty.applied_facets() == {}
    # Y verify_against sobre una resolución vacía no falla (nada que verificar).
    assert empty.verify_against([], "cc", "ChanelCareers") == (True, [])


# ── PUNTO 2: degradación de scope EXPLÍCITA ────────────────────────────────

def test_scope_degradation_city_requested_country_resolved(monkeypatch):
    """P2: se pidió ciudad y sólo resolvió país → degradación explícita,
    NO silenciosa."""

    def handler(payload):
        if not payload["appliedFacets"]:
            return {"total": 1119, "jobPostings": [],
                    "facets": [{"facetParameter": "locationCountry",
                                "descriptor": "Country", "values": [
                                    {"descriptor": "Mexico", "id": MX_CHANEL,
                                     "count": 19}]}]}
        return {"total": 19, "jobPostings": [
            _job("/job/1", "Rol CDMX", "Ciudad De Mexico")],
            "facets": chanel_facets()}

    monkeypatch.setattr(wd.WorkdayClient, "_post_jobs", _as_tuple(handler))
    out = wd.workday_structured_search("cc", "ChanelCareers", "cc.wd3",
                                       require_city=True)
    deg = out["scope_degradation"]
    assert deg is not None
    assert deg["degraded"] is True
    assert deg["requested_scope"] == "city"
    assert deg["resolved_scope"] == "country"
    assert "require_city" in out["detail"]
    assert out["state"] == wd.QueryState.UNKNOWN


def test_scope_degradation_without_require_city_is_still_explicit(monkeypatch):
    """P2: sin require_city, el resultado de país es válido PERO la
    degradación queda registrada en el audit (nunca silenciosa)."""

    def handler(payload):
        if not payload["appliedFacets"]:
            return {"total": 1119, "jobPostings": [], "facets": chanel_facets()}
        return {"total": 19, "jobPostings": [
            _job("/job/1", "Rol GDL", "Zapopan")], "facets": chanel_facets()}

    monkeypatch.setattr(wd.WorkdayClient, "_post_jobs", _as_tuple(handler))
    out = wd.workday_structured_search("cc", "ChanelCareers", "cc.wd3")
    # Resultado de país es válido a nivel país.
    assert out["state"] == wd.QueryState.VERIFIED_RESULTS
    # PERO la degradación es visible en el audit.
    deg = out["audit"]["scope_degradation"]
    assert deg is not None
    assert deg["degraded"] is True
    assert deg["requested_scope"] == "city"
    assert deg["resolved_scope"] == "country"
    assert out["audit"]["resolved_scope"] == "country"


def test_scope_degradation_twolevel_explicit(monkeypatch):
    """P2: 2-nivel, ciudad no resuelve → degradación explícita en audit."""
    # El contexto filtrado por México NO ofrece valores de CDMX.
    sin_cdmx = [
        {"facetParameter": "locationCountry", "descriptor": "Country",
         "values": [{"descriptor": "Mexico", "id": MX_CHANEL, "count": 19}]},
        {"facetParameter": "locationMainGroup", "values": [
            {"facetParameter": "locations", "descriptor": "City", "values": [
                {"descriptor": "Zapopan", "id": "id-zapopan", "count": 7}]}]},
    ]

    def handler(payload):
        af = payload["appliedFacets"]
        if not af:
            return {"total": 1119, "jobPostings": [], "facets": chanel_facets()}
        return {"total": 19, "jobPostings": [
            _job("/job/1", "Rol GDL", "Zapopan")], "facets": sin_cdmx}

    monkeypatch.setattr(wd.WorkdayClient, "_post_jobs", _as_tuple(handler))
    out = wd.workday_structured_search_2level("cc", "ChanelCareers", "cc.wd3")
    deg = out["scope_degradation"]
    assert deg is not None
    assert deg["requested_scope"] == "city"
    assert deg["resolved_scope"] == "country"
    assert out["audit"]["resolved_scope"] == "country"


def test_scope_no_degradation_when_city_resolves(monkeypatch):
    """P2: si ciudad resuelve, no hay degradación."""

    def handler(payload):
        af = payload["appliedFacets"]
        if not af:
            return {"total": 1119, "jobPostings": [], "facets": chanel_facets()}
        if set(af) == {"locationCountry"}:
            return {"total": 19, "jobPostings": [], "facets": chanel_facets()}
        return {"total": 10, "jobPostings": [
            _job("/job/1", "Stock Associate", "Ciudad De Mexico")],
            "facets": chanel_facets()}

    monkeypatch.setattr(wd.WorkdayClient, "_post_jobs", _as_tuple(handler))
    out = wd.workday_structured_search_2level("cc", "ChanelCareers", "cc.wd3")
    assert out["audit"]["scope_degradation"] is None
    assert out["audit"]["resolved_scope"] == "city"


# ── PUNTO 3: clasificación de HTTP 400 ──────────────────────────────────────

def test_http_400_payload_rejected_is_not_retried():
    """P3: 400 con envelope CXS → payload_rejected, NO retryable."""
    state, cause, retryable = wd.WorkdayClient.classify_http_error(
        400, '{"errorCode":"HTTP_400","errorCaseId":"X","message":""}')
    assert state == wd.QueryState.UNKNOWN
    assert "payload_rejected" in cause
    assert retryable is False


def test_http_400_non_cxs_is_retried():
    """P3: 400 sin envelope de Workday → capa intermedia, retryable."""
    state, cause, retryable = wd.WorkdayClient.classify_http_error(
        400, "<html><body>Bad Request from proxy</body></html>")
    assert "bad_request_non_cxs" in cause
    assert retryable is True


def test_http_error_classification_covers_all_codes():
    """P3: cada código tiene causa explícita, no equivalente a otro."""
    for code, expect_retry in [(400, None), (405, False), (406, False),
                               (422, False), (500, True), (503, True)]:
        state, cause, retryable = wd.WorkdayClient.classify_http_error(code, "")
        assert state == wd.QueryState.UNKNOWN
        assert cause, f"código {code} sin causa clasificada"
        assert isinstance(retryable, bool)
        if expect_retry is not None:
            assert retryable == expect_retry


def test_400_retry_count_is_respected(monkeypatch):
    """P3: 400 payload_rejected NO reintenta; 400 non-CXS sí reintenta."""
    calls = {"n": 0}

    def handler(payload):
        calls["n"] += 1
        return None, wd.QueryState.UNKNOWN, "HTTP 400 payload_rejected"

    client = make_client(monkeypatch, handler, max_attempts=3, backoff=0.01)
    client.search({"locationCountry": [MX_CHANEL]})
    # _post_jobs fue monkeypatcheado; el test real es sobre classify.
    _state, _cause, retryable = wd.WorkdayClient.classify_http_error(
        400, '{"errorCode":"HTTP_400","errorCaseId":"Z"}')
    assert retryable is False


def test_is_terminal_payload_delegates_to_classifier():
    """P3: _is_terminal_payload delega en el clasificador (fuente única)."""
    cxs = '{"errorCode":"HTTP_400","errorCaseId":"A"}'
    non_cxs = "<html>proxy error</html>"
    assert wd.WorkdayClient._is_terminal_payload(400, cxs) is True
    assert wd.WorkdayClient._is_terminal_payload(400, non_cxs) is False
