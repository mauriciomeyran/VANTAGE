#!/usr/bin/env python3
"""
VANTAGE L3 Pipeline — Gmail (.Jobs) → Gemini → Notion VANTAGE TRACKER
Extrae vacantes de correos y las ingresa individualmente al tracker.
"""

import hashlib
import imaplib
import email
import json
import re
import os
import random
import sys
import unicodedata
from datetime import datetime, timezone
from email.header import decode_header
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

import time
import requests
from pathlib import Path
from dotenv import load_dotenv

# ──────────────────────────────────────────
# CONFIGURACIÓN (config/layer_3.env)
# ──────────────────────────────────────────
_LAYER_3_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_LAYER_3_ROOT / "config" / "layer_3.env", override=True)

GMAIL_USER     = os.environ["GMAIL_USER"]
GMAIL_APP_PASS = os.environ["GMAIL_APP_PASS"]
GMAIL_LABEL    = os.environ.get("GMAIL_LABEL", ".Jobs")

GROQ_API_KEY   = os.environ["GROQ_API_KEY"]
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b").strip()
GROQ_FALLBACK_MODEL = os.environ.get("GROQ_FALLBACK_MODEL", "openai/gpt-oss-20b").strip()
GEMINI_MIN_DELAY = float(os.environ.get("GEMINI_MIN_DELAY_SEC", "2.0"))
GEMINI_MAX_RETRY = int(os.environ.get("GEMINI_MAX_RETRIES", "3"))
GEMINI_MAX_BACKOFF = float(os.environ.get("GEMINI_MAX_BACKOFF_SEC", "15"))
MAX_BODY_CHARS = int(os.environ.get("MAX_EMAIL_BODY_CHARS", "4000"))
MAX_EMAILS_RUN = int(os.environ.get("GEMINI_MAX_EMAILS_PER_RUN", "5"))

NOTION_TOKEN   = os.environ["NOTION_TOKEN"]
NOTION_DB_ID   = os.environ["NOTION_DB_ID"]

_last_gemini_call = 0.0


class GeminiFatalError(Exception):
    """Error de Gemini que no se arregla reintentando (VPN, credenciales, modelo inválido)."""

class GroqExhaustedError(Exception):
    """Los N reintentos se agotaron (rate limit persistente o error de red).
    Nunca debe tratarse como 'sin vacantes' — el correo debe reintentarse
    en la siguiente corrida, no marcarse como leído/evaluado."""

# Fuentes reconocidas en el TRACKER
RAW_SOURCE_MAP = {
    "indeed":        "Indeed",
    "computrabajo":  "Computrabajo",
    "linkedin":      "LinkedIn",
    "occ":           "OCC",
    "bumeran":       "Bumeran",
    "puma":          "Puma",
    "swarovski":     "Swarovski",
}

EXCLUDED_SENDERS = [
    "loreal", "levi", "levis", "dockers",
    "palaciodehierro", "palacio de hierro"
]

# Asuntos que no merecen llamada a Gemini (ahorra cuota y tiempo)
SKIP_SUBJECT_RE = re.compile(
    r"agradecimiento|gracias por (tu|su)|postulaciones pendientes|"
    r"confirmaci[oó]n de (registro|cuenta)|newsletter|unsubscribe|"
    r"verifica(r)? tu (correo|email)|bienvenid[oa] a|"
    r"nuevas? (ofertas?|oportunidades?)|empleos? recomendados?|"
    r"alerta de empleo|ofertas? que (podr[ií]an|pueden) interesarte|"
    r"tienes \d+ (nuevas?|ofertas?)|postulaci[oó]n recibida",
    re.IGNORECASE,
)

# Indicadores básicos de vacantes para pre-filtrado (ahorra cuota Gemini)
JOB_INDICATORS_RE = re.compile(
    r"vacante|empleo|puesto|posici[oó]n|oportunidad|contrataci[oó]n|"
    r"job vacancy|job opening|hiring|vacancy|career|work|"
    r"aplica|postula|inscribir|register|apply now",
    re.IGNORECASE,
)

# Indicadores de URLs de job boards
JOB_BOARD_URL_RE = re.compile(
    r"https?://(www\.)?(linkedin|indeed|computrabajo|occ|bumeran)\.com|"
    r"https?://(www\.)?jobs\.",
    re.IGNORECASE,
)

# ──────────────────────────────────────────
# GMAIL — leer correos no leídos de .Jobs
# ──────────────────────────────────────────
def _connect_gmail():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(GMAIL_USER, GMAIL_APP_PASS)
    mail.select(f'"{GMAIL_LABEL}"')
    return mail


def _set_seen(mail, eid, seen: bool):
    flag = "+FLAGS" if seen else "-FLAGS"
    mail.store(eid, flag, "\\Seen")


def should_skip_groq(subject: str, body: str) -> tuple[bool, str]:
    """
    Pre-filtrado antes de llamar a Gemini para ahorrar cuota.
    Devuelve (True, motivo) si debe saltarse, (False, "") si procede.
    """
    # Combinar subject y body para análisis
    combined_text = f"{subject} {body}".lower()

    # Si no hay indicadores de vacante ni URLs de job boards, saltar
    if not JOB_INDICATORS_RE.search(combined_text) and not JOB_BOARD_URL_RE.search(combined_text):
        return True, "NO_VACANCY_PREFILTER"

    return False, ""


def _decode_subject(msg):
    raw_subject = decode_header(msg.get("Subject") or "")[0]
    try:
        if isinstance(raw_subject[0], bytes):
            return raw_subject[0].decode(raw_subject[1] or "utf-8")
        return raw_subject[0] or ""
    except (LookupError, UnicodeDecodeError, IndexError):
        if isinstance(raw_subject[0], bytes):
            return raw_subject[0].decode("utf-8", errors="replace")
        return str(raw_subject[0]) if raw_subject else ""


def _decode_part(part):
    """Decodifica un part usando su charset real declarado; fallback a utf-8
    solo si el part no declara charset. errors=\'replace\' preserva la
    estructura del texto (URLs incluidas) en vez de descartar bytes."""
    payload = part.get_payload(decode=True)
    if not payload:
        return ""
    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except (LookupError, UnicodeDecodeError):
        return payload.decode("utf-8", errors="replace")


def _extract_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = _decode_part(part)
                break
            if part.get_content_type() == "text/html" and not body:
                html = _decode_part(part)
                body = re.sub(r"<[^>]+>", " ", html)
                body = re.sub(r"\s+", " ", body).strip()
    else:
        body = _decode_part(msg)
    body = body.replace("\ufffd", "")  # quita bytes corruptos (fix loop Gemini 400 json_validate_failed)
    return body[:MAX_BODY_CHARS]


def sanitize_and_truncate_payload(body_text: str) -> str:
    """Truncate body text to MAX_BODY_CHARS to prevent TPM spikes."""
    if len(body_text) > MAX_BODY_CHARS:
        return body_text[:MAX_BODY_CHARS] + "\n...[truncated for TPM optimization]"
    return body_text


def fetch_unread_emails(mail):
    _, data = mail.search(None, "UNSEEN")
    email_ids = data[0].split()
    if not email_ids:
        return [], 0

    total = len(email_ids)
    if total > MAX_EMAILS_RUN:
        print(f"📨 {total} correo(s) nuevos — procesando {MAX_EMAILS_RUN} esta vez (límite GEMINI_MAX_EMAILS_PER_RUN)")
        email_ids = email_ids[:MAX_EMAILS_RUN]
    else:
        print(f"📨 {total} correo(s) nuevos encontrados")

    emails = []
    for eid in email_ids:
        _, msg_data = mail.fetch(eid, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        subject = _decode_subject(msg)
        sender = msg.get("From", "").lower()

        raw_source = "Other"
        for key, val in RAW_SOURCE_MAP.items():
            if key in sender:
                raw_source = val
                break

        if any(ex in sender for ex in EXCLUDED_SENDERS):
            print(f"⛔ Ignorado (hard block): {subject[:60]}")
            _set_seen(mail, eid, True)
            continue

        emails.append({
            "id":         eid,
            "subject":    subject,
            "sender":     sender,
            "raw_source": raw_source,
            "body":       _extract_body(msg),
        })

    return emails, total


# ──────────────────────────────────────────
# GEMINI — extraer vacantes del cuerpo
# ──────────────────────────────────────────
GROQ_PROMPT = """Eres un extractor de vacantes de empleo especializado en Visual Merchandising y retail.
Del siguiente texto de correo electrónico, extrae ÚNICAMENTE vacantes relevantes para un profesional de Visual Merchandising.

Roles RELEVANTES (incluir): Visual Merchandiser, VM Coordinator, VM Manager, Brand Environment, Escaparatista, Retail Design, Store Planner, Display Coordinator, Trade Marketing Visual, y roles similares en retail/moda/lujo con componente visual explícito.
Incluye también equivalentes en español: Exhibición Visual, Líder de Exhibición Visual, Coordinador Visual, Jefe de Visual, Escaparatismo, Diseño de Interiores Commercial, y cualquier rol con "Visual" o "Exhibición" en retail.

Roles IRRELEVANTES (ignorar completamente — NO incluir aunque aparezcan en el mismo correo):
- Ventas, cajero/a, asesor de ventas, ejecutivo de ventas, promotor
- Marketing digital, influencer marketing, social media, growth, performance
- Logística, almacén, distribución, supply chain
- Recursos humanos, reclutamiento, talent acquisition
- Contabilidad, finanzas, administración
- TI, desarrollo de software, soporte técnico
- Event planner, coordinador de eventos, producción de eventos
- Diseño gráfico sin componente retail/VM explícito
- Intern/practicante en áreas no-VM
- Supervisor operativo de sucursal, gerente de tienda sin scope VM
- Cualquier rol cuyo título no contenga palabras como: visual, merchandising, display, brand environment, retail design, store design, escaparate, vitrina, planograma, exhibición, escaparatismo

EXCLUSIÓN POR SENIORITY DEL TÍTULO (hard exclusion — rechazar sin importar si el rol es VM):
Si el TÍTULO COMPLETO contiene cualquiera de estos términos, NO incluir la vacante:
Director, VP, C-Level, Store Manager, Assistant, Asistente, Auxiliar, Jr., Internship, Intern, Entry Level, Pasantía, Sales Advisor, Vendedor, Asesor Comercial.
Ejemplo: "Visual Merchandising Jr. Coordinator" → excluir (contiene "Jr."). "Sr. Visual Merchandiser" → sí incluir (no contiene ningún término excluido).

MARCAS BLOQUEADAS (ignorar todas sus vacantes, sin excepción):
- El Palacio de Hierro (cualquier variante: Palacio de Hierro, palacio, PHierro)
- L'Oréal (todas sus divisiones: Lancôme, Giorgio Armani Beauty, YSL Beauty, Kiehl's, etc.)
- Levi's, Dockers

Para cada vacante relevante devuelve un objeto json con estos campos exactos:
- rol: título ESPECÍFICO del puesto TAL COMO APARECE en el texto del correo
- marca: empresa que publica TAL COMO APARECE en el texto (obligatorio)
- url: URL COMPLETA que aparezca LITERALMENTE en el correo, copiada carácter por carácter (obligatorio)
- holding: grupo corporativo si se menciona ("" si no se sabe)
- ubicacion: ciudad/país TAL COMO APARECE en el correo ("" si no se menciona)

DEFINICIÓN DE URL VÁLIDA:
- Debe aparecer textualmente en el correo, copiada carácter por carácter
- Debe ser una URL completa comenzando con https://
- Si no existe una URL literal para esa vacante: NO incluir la vacante

EJEMPLOS DE URLs INVÁLIDAS (NUNCA generar, inventar ni completar):
- https://mx.computrabajo.com/jobs/123456  ← ID numérico inventado
- https://mx.computrabajo.com/jobs/vm-coordinator-zara  ← slug construido a partir del rol
- https://computrabajo.com/vacante/display-coordinator-2024  ← URL fabricada con año

EJEMPLO CORRECTO:
Texto del correo: "...aplica aquí: https://www.linkedin.com/jobs/view/4414059078"
Output: {"rol":"VM Coordinator - Zara Polanco","marca":"Zara","url":"https://www.linkedin.com/jobs/view/4414059078","holding":"Inditex","ubicacion":"CDMX"}

REGLAS CRÍTICAS — léelas antes de responder:
1. NUNCA inventes vacantes. Solo extrae lo que está explícitamente escrito en el correo.
2. url es la URL COPIADA DEL TEXTO, NO una construida, completada o inferida por ti.
3. Si dudas si la URL es real o está completa → omitir la vacante.
4. Si el correo es un digest sin URLs directas por vacante (solo links genéricos/homepage), devuelve {"vacantes":[]}.
5. NO repitas la misma vacante.
6. Máximo 20 vacantes por correo.
7. Ante la duda sobre si un rol es relevante → NO incluirlo. Es mejor perder una vacante marginal que contaminar el tracker.

Responde ÚNICAMENTE con un objeto json válido (sin markdown):
{"vacantes":[{"rol":"VM Coordinator - Zara Polanco","marca":"Zara","url":"https://www.linkedin.com/jobs/view/4414059078","holding":"Inditex","ubicacion":"CDMX"}]}

Si no hay vacantes con URL real: {"vacantes":[]}
"""

def _gemini_throttle():
    global _last_gemini_call
    elapsed = time.monotonic() - _last_gemini_call
    if elapsed < GEMINI_MIN_DELAY:
        time.sleep(GEMINI_MIN_DELAY - elapsed)


GEMINI_MAX_RETRY_AFTER = float(os.environ.get("GEMINI_MAX_RETRY_AFTER_SEC", "120"))


def _log_rate_limit_headers(resp):
    """Diagnóstico del 429 real de Groq — distingue RPM/TPM/cuota diaria.
    Sin esto, un backoff bien afinado sigue siendo un tiro a ciegas si la
    causa real es una cuota diaria agotada (ningún backoff dentro del script
    la resuelve; hay que esperar al reset o revisar el dashboard de Groq)."""
    keys = [
        "retry-after",
        "x-ratelimit-limit-requests", "x-ratelimit-remaining-requests", "x-ratelimit-reset-requests",
        "x-ratelimit-limit-tokens", "x-ratelimit-remaining-tokens", "x-ratelimit-reset-tokens",
    ]
    found = {k: resp.headers[k] for k in keys if k in resp.headers}
    if found:
        detail = " · ".join(f"{k}={v}" for k, v in found.items())
        print(f"      ↳ {detail}")
    else:
        print(f"      ↳ (Groq no devolvió headers x-ratelimit-* en este 429)")


def _gemini_wait_seconds(resp, attempt):
    retry_after = resp.headers.get("Retry-After")
    if retry_after:
        try:
            # Techo de sanidad separado (120s default) — NO el mismo cap que
            # el backoff exponencial sin header (15s). Un Retry-After real de
            # Groq (ej. 60s por cuota de RPM/TPM agotada) es información del
            # servidor, no una sugerencia; clampearlo al cap del backoff
            # garantiza reintentos prematuros que vuelven a fallar.
            return min(max(float(retry_after), GEMINI_MIN_DELAY), GEMINI_MAX_RETRY_AFTER)
        except ValueError:
            pass
    # Sin header: backoff exponencial 8,16,32… capped at GEMINI_MAX_BACKOFF + jitter
    return min(GEMINI_MAX_BACKOFF, GEMINI_MIN_DELAY * (2 ** attempt)) + random.uniform(0, 3)


def extract_jobs_with_gemini(email_body, retries=3, use_fallback=False):
    # Sanitize and truncate payload to prevent TPM spikes
    sanitized_body = sanitize_and_truncate_payload(email_body)
    
    valid_ascii = set(range(32, 127)) | {10, 13, 9}
    clean_body = ''.join(ch for ch in sanitized_body if ord(ch) in valid_ascii)

    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    model = GROQ_FALLBACK_MODEL if use_fallback else GROQ_MODEL

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": GROQ_PROMPT},
            {"role": "user", "content": clean_body}
        ],
        "temperature": 0.0,
        "response_format": {"type": "json_object"}
    }

    last_was_rate_limit = False
    for attempt in range(retries):
        _gemini_throttle()
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            if resp.status_code == 429:
                last_was_rate_limit = True
                wait = _gemini_wait_seconds(resp, attempt)
                print(f"  ⏳ Groq rate limit 429 ({attempt+1}/{retries}), esperando {wait:.1f}s...")
                _log_rate_limit_headers(resp)
                time.sleep(wait)
                continue

            resp.raise_for_status()
            content_json = resp.json()["choices"][0]["message"]["content"].strip()
            return _parse_groq_jobs(content_json)

        except requests.exceptions.RequestException as err:
            print(f"  ❌ Groq error: {err}")
            if attempt == retries - 1:
                # If primary model failed and we haven't tried fallback yet, try it
                if not use_fallback and GROQ_FALLBACK_MODEL != GROQ_MODEL:
                    print(f"  🔄 Primary model failed, trying fallback: {GROQ_FALLBACK_MODEL}")
                    try:
                        return extract_jobs_with_gemini(email_body, retries=2, use_fallback=True)
                    except Exception as fallback_err:
                        print(f"  ❌ Fallback model also failed: {fallback_err}")
                raise GroqExhaustedError(f"Reintentos agotados (error de red): {err}") from err

    # Si llegamos aquí, se agotaron los `retries` intentos por 429 —
    # nunca retornar [] silenciosamente: eso se confunde con "Groq evaluó
    # el correo y no encontró vacantes" y el correo se marca como leído
    # sin haber sido evaluado realmente.
    if last_was_rate_limit:
        raise GroqExhaustedError(f"Rate limit agotado tras {retries} reintentos")
    raise GroqExhaustedError("Reintentos agotados sin respuesta válida de Groq")


def _parse_groq_jobs(content):
    content = re.sub(r"^```json\s*", "", content)
    content = re.sub(r"```$", "", content).strip()

    def _coerce(data):
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("vacantes", "jobs", "vacantes_relevantes", "results"):
                if key in data and isinstance(data[key], list):
                    return data[key]
        raise ValueError("JSON sin lista de vacantes")

    try:
        return _coerce(json.loads(content))
    except (json.JSONDecodeError, ValueError):
        match = re.search(r"\{[\s\S]*\}|\[[\s\S]*\]", content)
        if not match:
            raise
        return _coerce(json.loads(match.group()))


# ──────────────────────────────────────────
# NOTION — crear página por vacante
# ──────────────────────────────────────────
NOTION_HEADERS = {
    "Authorization":  f"Bearer {NOTION_TOKEN}",
    "Content-Type":   "application/json",
    "Notion-Version": "2022-06-28",
}

VALID_HOLDINGS = [
    "Adidas Group","Blue Star Group","Coppel","El Puerto de Liverpool",
    "GAP Inc.","Grupo Alfer","Grupo Axo","Grupo BAL","Grupo Piagui",
    "N/A","Pandora Group","Swarovski Group","Hugo Boss AG","IB Group",
    "Inditex México","Innovasport","Investigar","Kering","La Europea",
    "LVMH","Moda Holding","OTB Group","Richemont","Soho Moda",
    "Sportmex","Tendam","Nike","C&A","PVH",
]

VALID_RAW_SOURCES = [
    "Indeed","OCC","LinkedIn","Computrabajo","Bumeran","Puma","Swarovski","Other"
]

# Opciones REALES del select "Fuente" en el VANTAGE TRACKER (Notion).
# No confundir con VALID_RAW_SOURCES: ese es el vocabulario interno de
# detección por remitente; este es el contrato exacto que Notion acepta.
# Cualquier raw_source detectado que no esté aquí colapsa a "Other".
NOTION_FUENTE_OPTIONS = {
    "Agregador", "Career Page Oficial", "Indeed", "Other", "Computrabajo", "LinkedIn"
}

# ──────────────────────────────────────────
# CANONICALIZACIÓN DE URLs (Fix B)
# ──────────────────────────────────────────
STRIP_PARAMS = {
    "linkedin.com": {"trackingId", "refId", "trk", "src"},
}

SYNTHETIC_CT_PATTERNS = [
    re.compile(r'/jobs/\d{4,8}$'),                    # numeric ID corto
    re.compile(r'/jobs/\d{10,}$'),                    # numeric ID largo inventado
    re.compile(r'\d{4}-\d{4}-\d{4}'),                 # year chain
    re.compile(r'-(12345|67890|23456|34567|89012)'),  # IDs plantilla conocidos
    re.compile(r'/jobs/[^/]+-\d{4}$'),                # rol-marca-2024 (bug fix ticket 3be938be-fc42-8195-a602-d3a8c1bf0adf)
]


def canonicalize_url(url: str) -> tuple[str, str]:
    """
    Devuelve (canonical_url, rejection_reason | "")
    rejection_reason vacío = URL aceptable
    """
    if not url or not url.startswith("http"):
        return url, "NO_URL"

    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    # 1. Detectar URLs sintéticas de Computrabajo (alucinadas por Groq)
    if "computrabajo" in domain:
        # Decodificar URL para manejar acentos/encoding (ej. galer%C3%ADas → galerías)
        # solo para matching del regex - la URL original se retorna intacta
        from urllib.parse import unquote
        decoded_url = unquote(url)
        for pat in SYNTHETIC_CT_PATTERNS:
            if pat.search(parsed.path) or pat.search(url) or pat.search(decoded_url):
                return url, "SYNTHETIC_AGGREGATOR_URL"

    # 2. Resolver redirects de Indeed (son tracking links, no canónicos)
    if "indeed.com/rc/clk" in url or "indeed.com/applystart" in url:
        try:
            r = requests.head(url, allow_redirects=True, timeout=5,
                               headers={"User-Agent": "Mozilla/5.0"})
            resolved = r.url
            if "indeed.com" not in resolved:  # llegó a ATS o career page
                return resolved, ""
        except Exception:
            pass
        # Fallback: extraer jk= como fingerprint, no resolver
        params = parse_qs(parsed.query)
        jk = params.get("jk", [""])[0]
        if jk:
            return f"https://mx.indeed.com/viewjob?jk={jk}", ""
        return url, "UNRESOLVABLE_REDIRECT"

    # 3. Limpiar tracking params de LinkedIn y normalizar comm/jobs → jobs
    if "linkedin.com" in domain:
        path = parsed.path.replace("/comm/jobs/", "/jobs/")
        params = parse_qs(parsed.query)
        clean_params = {k: v for k, v in params.items()
                         if k not in STRIP_PARAMS.get("linkedin.com", set())}
        clean_query = urlencode(clean_params, doseq=True)
        canonical = urlunparse((parsed.scheme, parsed.netloc, path,
                                 parsed.params, clean_query, ""))
        return canonical, ""

    return url, ""



def _compute_l3_hash(rol: str, marca: str, url: str) -> str:
    """Hash compatible con feed_processor.compute_dedup_hash para entradas L3.
    Prioriza URL canónica (career_page branch); fallback a agg:brand|title|."""
    url = (url or "").strip()
    if url.startswith("http"):
        key = f"url:{url}"
    else:
        brand = (marca or "").strip().lower()
        title = (rol or "").strip().lower()
        key = f"agg:{brand}|{title}|"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def normalize_holding(raw):
    if not raw:
        return "Investigar"
    for h in VALID_HOLDINGS:
        if h.lower() in raw.lower() or raw.lower() in h.lower():
            return h
    return "Investigar"


def _normalize_job(job):
    return {
        "rol":       (job.get("rol") or "").strip()[:200],
        "marca":     (job.get("marca") or "").strip()[:200],
        "url":       (job.get("url") or "").strip(),
        "holding":   (job.get("holding") or "").strip()[:200],
        "ubicacion": (job.get("ubicacion") or "").strip()[:200],
    }


def _job_dedupe_key(job):
    url = job["url"].lower().rstrip("/")
    if url.startswith("http"):
        return ("url", url)
    rol = job["rol"].lower()
    marca = job["marca"].lower()
    if marca:
        return ("rol_marca", rol, marca)
    return ("rol_only", rol)


def dedupe_jobs(jobs):
    """Quita repeticiones dentro del mismo correo; descarta filas sin url ni marca,
    rechaza URLs sintéticas/alucinadas y canonicaliza tracking links."""
    unique = []
    seen = set()
    dropped = 0
    rejected_synthetic = 0
    for raw in jobs:
        job = _normalize_job(raw)
        if not job["rol"]:
            dropped += 1
            continue
        if not job["url"].startswith("http"):
            dropped += 1
            continue

        canonical, reason = canonicalize_url(job["url"])
        if reason:
            rejected_synthetic += 1
            continue
        job["url"] = canonical

        key = _job_dedupe_key(job)
        if key in seen:
            dropped += 1
            continue
        seen.add(key)
        unique.append(job)
    if rejected_synthetic:
        print(f"  🚫 {rejected_synthetic} URL(s) sintética(s)/no resoluble(s) descartada(s)")
    return unique, dropped


# ──────────────────────────────────────────
# FILTRO VM — validación post-Groq por título
# ──────────────────────────────────────────
_VM_KEYWORDS = re.compile(
    r"visual merch|merchandis|display|escaparat|vitrina|planograma|exhibici[oó]n|"
    r"brand environment|store design|retail design|store planner|"
    r"vm coord|vm manager|visual coord|visual manager|"
    r"trade marketing visual|montaje.*mobiliario|mobiliario.*montaje|"
    r"exhibici[oó]n visual|escaparatismo|diseño.*interiores.*commercial|"
    r"coordinador.*visual|líder.*visual|jefe.*visual|visual.*coordinator|"
    r"visual.*leader|visual.*lead",
    re.IGNORECASE,
)

_HARD_BLOCK_BRANDS = re.compile(
    r"palacio de hierro|palaciodehierro|l.?or.?al|loreal|levi.?s|dockers",
    re.IGNORECASE,
)

# Hard exclusions de título — replicadas 1:1 de Prompt A / L1 (HARD EXCLUSIONS).
# Evaluación sobre el TÍTULO COMPLETO, igual que L1 ("Title evaluation MUST use
# the complete title string"). Rechaza sin importar si el rol matchea VM
# keywords — Director/VP/Assistant/Jr./Intern/Sales quedan fuera aunque el
# título contenga "Visual Merchandising".
_TITLE_HARD_EXCLUSIONS = re.compile(
    r"\bstore manager\b|\bdirector\b|\bvp\b|\bc-level\b|\bassistant\b|"
    r"\basistente\b|\bauxiliar\b|\bjr\.?\b|\binternship\b|\bintern\b|"
    r"\bentry level\b|\bpasant[ií]a\b|\bsales advisor\b|\bvendedor(a)?\b|"
    r"\basesor(a)? comercial\b",
    re.IGNORECASE,
)

# Location — replicado de L1 (Location: CDMX; Accepted work modes On-site/Hybrid;
# Exclude remote roles outside Mexico). Solo rechaza cuando el correo declara
# EXPLÍCITAMENTE una ubicación fuera de México o "remoto" sin país México —
# nunca por ausencia de dato (la mayoría de los correos no traen ubicación en
# el digest y L3 no debe perder cobertura por eso; el filtro estricto de
# ubicación ya vive en L1/Score, aquí solo se descarta lo inequívocamente fuera
# de alcance).
_LOCATION_OUTSIDE_MX_RE = re.compile(
    r"\bremote\b(?!.*m[eé]xico)|\bremoto\b(?!.*m[eé]xico)|"
    r"\b(usa|united states|canada|canadá|espa[ñn]a|colombia|argentina|"
    r"per[uú]|chile|brasil|brazil|europe|europa)\b",
    re.IGNORECASE,
)
_LOCATION_MX_RE = re.compile(
    r"cdmx|ciudad de m[eé]xico|m[eé]xico|mexico city|edo\.?\s*m[eé]x|"
    r"estado de m[eé]xico",
    re.IGNORECASE,
)


def is_vm_relevant(job: dict) -> tuple[bool, str]:
    """
    Devuelve (True, "") si la vacante pasa el filtro VM.
    Devuelve (False, motivo) si debe descartarse.
    Segunda línea de defensa post-Groq: Python nunca falla.
    """
    rol = job.get("rol", "")
    marca = job.get("marca", "")

    if _HARD_BLOCK_BRANDS.search(marca):
        return False, f"HARD_BLOCK_BRAND: {marca}"

    # Hard exclusion de título (replicado de L1/Prompt A) — se evalúa ANTES
    # del match VM: un "VM Director" o "Visual Merchandising Jr. Coordinator"
    # se rechaza aunque contenga keywords VM, igual que en L1.
    excl_match = _TITLE_HARD_EXCLUSIONS.search(rol)
    if excl_match:
        return False, f"HARD_EXCLUSION_TITLE ({excl_match.group().strip()}): {rol}"

    if not _VM_KEYWORDS.search(rol):
        return False, f"NO_VM_KEYWORD: {rol}"

    return True, ""


def is_location_relevant(job: dict) -> tuple[bool, str]:
    """
    Devuelve (True, "") si la ubicación es aceptable (CDMX/México, on-site u
    híbrido, o simplemente no se menciona en el correo).
    Devuelve (False, motivo) SOLO cuando el correo declara explícitamente una
    ubicación fuera de México o remoto sin México — replicado de L1
    (Location: CDMX; Accepted work modes On-site/Hybrid; Exclude remote roles
    outside Mexico). Nunca rechaza por ausencia de dato — eso corresponde a
    una capa de filtrado más estricta (L1/Score), no a L3.
    """
    ubicacion = job.get("ubicacion", "")
    if not ubicacion:
        return True, ""
    if _LOCATION_MX_RE.search(ubicacion):
        return True, ""
    if _LOCATION_OUTSIDE_MX_RE.search(ubicacion):
        return False, f"LOCATION_OUTSIDE_MX: {ubicacion}"
    return True, ""


def normalize_text(s: str) -> str:
    """Lowercase, quita acentos y caracteres no-alfanuméricos."""
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]", " ", s).strip()


def _notion_query(filt):
    resp = requests.post(
        f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query",
        headers=NOTION_HEADERS,
        json={"filter": filt},
        timeout=15,
    )
    if resp.status_code == 200:
        return resp.json().get("results", [])
    return []


def _prop_text(page, prop_name, kind):
    try:
        arr = page["properties"][prop_name][kind]
        return arr[0]["text"]["content"] if arr else ""
    except (KeyError, IndexError, TypeError):
        return ""


def already_exists(rol, marca, url=""):
    """True si la vacante ya está en Notion (por URL exacta, Rol+Marca exactos,
    o Rol+Marca normalizados — atrapa typos/variantes cross-email)."""
    url = (url or "").strip()
    marca = (marca or "").strip()
    rol = (rol or "").strip()

    # Check 1: URL exacta
    if url.startswith("http"):
        if _notion_query({"property": "URL", "url": {"equals": url}}):
            return True

    # Check 2: Rol+Marca exactos
    if marca:
        filt = {"and": [
            {"property": "Rol",   "title":     {"equals": rol}},
            {"property": "Marca", "rich_text": {"equals": marca}},
        ]}
        if _notion_query(filt):
            return True

    # Check 3: Rol normalizado + Marca normalizada (typos / variantes cross-email)
    if marca:
        rol_norm = normalize_text(rol)
        marca_norm = normalize_text(marca)
        filt = {"property": "Marca", "rich_text": {"contains": marca[:15]}}
        for page in _notion_query(filt):
            existing_rol = normalize_text(_prop_text(page, "Rol", "title"))
            existing_marca = normalize_text(_prop_text(page, "Marca", "rich_text"))
            if existing_marca == marca_norm and existing_rol == rol_norm:
                return True

    return False


def create_notion_page(job, email_meta):
    holding = normalize_holding(job.get("holding", ""))
    raw_source = email_meta["raw_source"] if email_meta["raw_source"] in VALID_RAW_SOURCES else "Other"
    # Segundo clamp: raw_source puede ser válido internamente (VALID_RAW_SOURCES)
    # pero no existir como opción real del select en Notion (ej. OCC, Bumeran,
    # Puma, Swarovski no están dados de alta ahí). Sin este paso, Notion
    # rechaza la escritura con "option does not exist".
    fuente = raw_source if raw_source in NOTION_FUENTE_OPTIONS else "Other"

    properties = {
        "Rol": {
            "title": [{"text": {"content": job.get("rol", "Sin título")[:200]}}]
        },
        "Marca": {
            "rich_text": [{"text": {"content": job.get("marca", "")[:200]}}]
        },
        "Status": {
            "select": {"name": "Target"}
        },
        "layer": {
            "select": {"name": "L3"}
        },
        "Source_Type": {
            "select": {"name": "Vacante"}
        },
        "Holding": {
            "rich_text": [{"text": {"content": holding[:200]}}]
        },
        "Fuente": {
            "select": {"name": fuente}
        },
        "hash": {
            "rich_text": [{"text": {"content": _compute_l3_hash(
                job.get("rol", ""), job.get("marca", ""), job.get("url", "")
            )}}]
        },
    }

    url = job.get("url", "").strip()
    if url and url.startswith("http"):
        properties["URL"] = {"url": url}

    payload = {
        "parent": {"database_id": NOTION_DB_ID},
        "properties": properties,
    }

    resp = requests.post(
        "https://api.notion.com/v1/pages",
        headers=NOTION_HEADERS,
        json=payload,
        timeout=15,
    )

    if resp.status_code == 200:
        return True, resp.json().get("url", "")
    else:
        return False, resp.text


# ──────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────
import json as _json, pathlib as _pl, datetime as _dt

def _write_heartbeat(total_created: int, total_failed: int):
    path = _pl.Path.home() / ".vantage" / "l3_heartbeat.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "last_run": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "total_created": total_created,
        "total_failed": total_failed
    }
    path.write_text(_json.dumps(payload, indent=2))

def main():
    print("\n🚀 VANTAGE L3 Pipeline arrancando...")
    print(f"   Gemini: {GROQ_MODEL} · pausa mín {GEMINI_MIN_DELAY}s · máx {MAX_EMAILS_RUN} correos/ejecución\n")

    print("📬 Conectando a Gmail...")
    mail = _connect_gmail()
    emails, total_inbox = fetch_unread_emails(mail)
    if not emails:
        print("✅ No hay correos nuevos en .Jobs")
        _write_heartbeat(0, 0)
        print("💾 Heartbeat → ~/.vantage/l3_heartbeat.json")
        mail.logout()
        return

    total_created = 0
    total_failed  = 0
    groq_failed   = 0

    for idx, em in enumerate(emails, 1):
        print(f"\n📧 [{idx}/{len(emails)}] {em['subject'][:60]}")

        if SKIP_SUBJECT_RE.search(em["subject"]):
            print("  ⏭️  Asunto ignorado (sin vacantes)")
            _set_seen(mail, em["id"], True)
            continue

        # Pre-filtrado para ahorrar cuota Groq
        skip_groq, skip_reason = should_skip_groq(em["subject"], em["body"])
        if skip_groq:
            print(f"  ⏭️  Pre-filtrado ({skip_reason}) - sin indicadores de vacante")
            _set_seen(mail, em["id"], True)
            continue

        try:
            jobs = extract_jobs_with_gemini(em["body"])
        except (json.JSONDecodeError, ValueError) as e:
            print(f"  ❌ Gemini JSON inválido: {e}")
            _set_seen(mail, em["id"], False)
            groq_failed += 1
            continue
        except GroqExhaustedError as e:
            print(f"  ⏸️  {e} — correo dejado como no leído para reintentar")
            _set_seen(mail, em["id"], False)
            groq_failed += 1
            continue
        except GeminiFatalError as e:
            print(f"  ❌ {e}")
            print("  ↩️  Correos dejados como no leídos")
            _set_seen(mail, em["id"], False)
            groq_failed += len(emails) - idx + 1
            mail.logout()
            print(f"\n{'─'*40}")
            print(f"🛑 ABORT: Gemini no disponible — corrige configuración antes de reintentar")
            print(f"✅ Creadas: {total_created}  |  ❌ Notion: {total_failed}  |  ⏸️ Gemini pendientes: {groq_failed}")
            print("─"*40 + "\n")
            sys.exit(1)
        except Exception as e:
            print(f"  ❌ Gemini error: {e}")
            print("  ↩️  Dejado como no leído para reintentar en la próxima ejecución")
            _set_seen(mail, em["id"], False)
            groq_failed += 1
            continue

        _set_seen(mail, em["id"], True)

        if not jobs:
            print("  ⚪ Sin vacantes detectadas")
            continue

        raw_count = len(jobs)
        jobs, dropped = dedupe_jobs(jobs)
        if dropped:
            print(f"  🔍 {raw_count} detectada(s) → {len(jobs)} única(s) ({dropped} repetidas/genéricas omitidas)")
        else:
            print(f"  🔍 {len(jobs)} vacante(s) a importar")

        skipped_notion = 0
        skipped_vm = 0
        skipped_location = 0
        for job in jobs:
            rol, marca, url = job["rol"], job["marca"], job["url"]
            label = f"{rol}" + (f" @ {marca}" if marca else f" · {url[:40]}")

            relevant, reason = is_vm_relevant(job)
            if not relevant:
                print(f"  🚧 Filtrado post-Groq ({reason}): {label}")
                skipped_vm += 1
                continue

            loc_ok, loc_reason = is_location_relevant(job)
            if not loc_ok:
                print(f"  🌍 Filtrado por ubicación ({loc_reason}): {label}")
                skipped_location += 1
                continue

            if already_exists(rol, marca, url):
                skipped_notion += 1
                continue
            ok, result = create_notion_page(job, em)
            if ok:
                print(f"  ✅ Creada: {label}")
                total_created += 1
            else:
                print(f"  ❌ Error en Notion para '{label}': {result[:100]}")
                total_failed += 1

        if skipped_vm:
            print(f"  🚧 {skipped_vm} filtrada(s) por no ser VM (post-Groq)")
        if skipped_location:
            print(f"  🌍 {skipped_location} filtrada(s) por ubicación fuera de México")
        if skipped_notion:
            print(f"  ⏭️  {skipped_notion} ya existían en Notion")

    mail.logout()

    _write_heartbeat(total_created, total_failed)
    print("💾 Heartbeat → ~/.vantage/l3_heartbeat.json")

    remaining = max(0, total_inbox - len(emails))
    print(f"\n{'─'*40}")
    print(f"✅ Creadas: {total_created}  |  ❌ Notion: {total_failed}  |  ⏸️ Groq pendientes: {groq_failed}")
    if remaining:
        print(f"📬 Quedan ~{remaining} correo(s) sin leer — ejecuta de nuevo cuando termine esta tanda")
    print("─"*40 + "\n")


if __name__ == "__main__":
    main()
