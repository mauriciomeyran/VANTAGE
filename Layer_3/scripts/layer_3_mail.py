#!/usr/bin/env python3
"""
VANTAGE L3 Pipeline — Gmail (.Jobs) → Groq → Notion VANTAGE TRACKER
Extrae vacantes de correos y las ingresa individualmente al tracker.
"""

import imaplib
import email
import json
import re
import os
import random
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
# 8b-instant: más RPM/TPM en tier gratuito; 70b agota cuota rápido con varios correos
GROQ_MODEL     = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_MIN_DELAY = float(os.environ.get("GROQ_MIN_DELAY_SEC", "12"))
GROQ_MAX_RETRY = int(os.environ.get("GROQ_MAX_RETRIES", "8"))
GROQ_BODY_MAX  = int(os.environ.get("GROQ_BODY_MAX_CHARS", "3500"))
MAX_EMAILS_RUN = int(os.environ.get("GROQ_MAX_EMAILS_PER_RUN", "5"))

NOTION_TOKEN   = os.environ["NOTION_TOKEN"]
NOTION_DB_ID   = os.environ["NOTION_DB_ID"]

_last_groq_call = 0.0

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

# Asuntos que no merecen llamada a Groq (ahorra cuota y tiempo)
SKIP_SUBJECT_RE = re.compile(
    r"agradecimiento|gracias por (tu|su)|postulaciones pendientes|"
    r"confirmaci[oó]n de (registro|cuenta)|newsletter|unsubscribe|"
    r"verifica(r)? tu (correo|email)|bienvenid[oa] a",
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


def _extract_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                break
            if part.get_content_type() == "text/html" and not body:
                html = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                body = re.sub(r"<[^>]+>", " ", html)
                body = re.sub(r"\s+", " ", body).strip()
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            body = payload.decode("utf-8", errors="ignore")
    return body[:GROQ_BODY_MAX]


def fetch_unread_emails(mail):
    _, data = mail.search(None, "UNSEEN")
    email_ids = data[0].split()
    if not email_ids:
        return [], 0

    total = len(email_ids)
    if total > MAX_EMAILS_RUN:
        print(f"📨 {total} correo(s) nuevos — procesando {MAX_EMAILS_RUN} esta vez (límite GROQ_MAX_EMAILS_PER_RUN)")
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
# GROQ — extraer vacantes del cuerpo
# ──────────────────────────────────────────
GROQ_PROMPT = """Eres un extractor de vacantes de empleo especializado en Visual Merchandising y retail.
Del siguiente texto de correo electrónico, extrae ÚNICAMENTE vacantes relevantes para un profesional de Visual Merchandising.

Roles RELEVANTES (incluir): Visual Merchandiser, VM Coordinator, VM Manager, VM Director, Brand Environment, Escaparatista, Retail Design, Store Planner, Display Coordinator, Trade Marketing Visual, y roles similares en retail/moda/lujo.
Roles IRRELEVANTES (ignorar completamente): contadores, asistentes virtuales, logística, ventas, marketing digital, TI, recursos humanos, y cualquier rol sin componente visual/retail.

Para cada vacante relevante devuelve un objeto JSON con estos campos exactos:
- rol: título ESPECÍFICO del puesto TAL COMO APARECE en el texto del correo
- marca: empresa que publica TAL COMO APARECE en el texto (obligatorio)
- url: URL COMPLETA que aparezca LITERALMENTE en el correo, copiada carácter por carácter (obligatorio)
- holding: grupo corporativo si se menciona ("" si no se sabe)

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
Output: {"rol":"VM Coordinator - Zara Polanco","marca":"Zara","url":"https://www.linkedin.com/jobs/view/4414059078","holding":"Inditex"}

REGLAS CRÍTICAS — léelas antes de responder:
1. NUNCA inventes vacantes. Solo extrae lo que está explícitamente escrito en el correo.
2. url es la URL COPIADA DEL TEXTO, NO una construida, completada o inferida por ti.
3. Si dudas si la URL es real o está completa → omitir la vacante.
4. Si el correo es un digest sin URLs directas por vacante (solo links genéricos/homepage), devuelve {"vacantes":[]}.
5. NO repitas la misma vacante.
6. Máximo 20 vacantes por correo.

Responde ÚNICAMENTE con un objeto JSON válido (sin markdown):
{"vacantes":[{"rol":"VM Coordinator - Zara Polanco","marca":"Zara","url":"https://www.linkedin.com/jobs/view/4414059078","holding":"Inditex"}]}

Si no hay vacantes con URL real: {"vacantes":[]}
"""

def _groq_throttle():
    global _last_groq_call
    elapsed = time.monotonic() - _last_groq_call
    if elapsed < GROQ_MIN_DELAY:
        time.sleep(GROQ_MIN_DELAY - elapsed)


def _groq_wait_seconds(resp, attempt):
    retry_after = resp.headers.get("Retry-After")
    if retry_after:
        try:
            return max(float(retry_after), GROQ_MIN_DELAY)
        except ValueError:
            pass
    # backoff: 12, 24, 48… hasta 90s + jitter
    return min(90, GROQ_MIN_DELAY * (2 ** attempt)) + random.uniform(0, 3)


def extract_jobs_with_groq(email_body, retries=None):
    if retries is None:
        retries = GROQ_MAX_RETRY

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": GROQ_PROMPT},
            {"role": "user",   "content": email_body},
        ],
        "temperature": 0.0,
        "max_tokens": 2500,
        "response_format": {"type": "json_object"},
    }

    resp = None
    for attempt in range(retries):
        _groq_throttle()
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        )
        _last_groq_call = time.monotonic()

        if resp.status_code == 429:
            wait = _groq_wait_seconds(resp, attempt)
            print(f"  ⏳ Groq rate limit ({attempt + 1}/{retries}), esperando {wait:.0f}s...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        break
    else:
        raise Exception(f"Groq rate limit persistente después de {retries} intentos")

    content = resp.json()["choices"][0]["message"]["content"].strip()
    return _parse_groq_jobs(content)


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
        for pat in SYNTHETIC_CT_PATTERNS:
            if pat.search(parsed.path) or pat.search(url):
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



def normalize_holding(raw):
    if not raw:
        return "Investigar"
    for h in VALID_HOLDINGS:
        if h.lower() in raw.lower() or raw.lower() in h.lower():
            return h
    return "Investigar"


def _normalize_job(job):
    return {
        "rol":     (job.get("rol") or "").strip()[:200],
        "marca":   (job.get("marca") or "").strip()[:200],
        "url":     (job.get("url") or "").strip(),
        "holding": (job.get("holding") or "").strip()[:200],
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
    fuente = email_meta["raw_source"] if email_meta["raw_source"] in VALID_RAW_SOURCES else "Other"

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
        "Source_Type ": {
            "select": {"name": "Vacante"}
        },
        "Holding": {
            "rich_text": [{"text": {"content": holding[:200]}}]
        },
        "Fuente": {
            "rich_text": [{"text": {"content": fuente[:200]}}]
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
def main():
    print("\n🚀 VANTAGE L3 Pipeline arrancando...")
    print(f"   Groq: {GROQ_MODEL} · pausa mín {GROQ_MIN_DELAY}s · máx {MAX_EMAILS_RUN} correos/ejecución\n")

    print("📬 Conectando a Gmail...")
    mail = _connect_gmail()
    emails, total_inbox = fetch_unread_emails(mail)
    if not emails:
        print("✅ No hay correos nuevos en .Jobs")
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

        try:
            jobs = extract_jobs_with_groq(em["body"])
        except (json.JSONDecodeError, ValueError) as e:
            print(f"  ❌ Groq JSON inválido: {e}")
            _set_seen(mail, em["id"], False)
            groq_failed += 1
            continue
        except Exception as e:
            print(f"  ❌ Groq error: {e}")
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
        for job in jobs:
            rol, marca, url = job["rol"], job["marca"], job["url"]
            label = f"{rol}" + (f" @ {marca}" if marca else f" · {url[:40]}")
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

        if skipped_notion:
            print(f"  ⏭️  {skipped_notion} ya existían en Notion")

    mail.logout()

    remaining = max(0, total_inbox - len(emails))
    print(f"\n{'─'*40}")
    print(f"✅ Creadas: {total_created}  |  ❌ Notion: {total_failed}  |  ⏸️ Groq pendientes: {groq_failed}")
    if remaining:
        print(f"📬 Quedan ~{remaining} correo(s) sin leer — ejecuta de nuevo cuando termine esta tanda")
    print("─"*40 + "\n")


if __name__ == "__main__":
    main()
