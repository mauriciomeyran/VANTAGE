#!/usr/bin/env python3
"""
VANTAGE Pipeline Runner v8.0
Pipeline principal sobre el tracker Notion (territorio Claude: CV, CANON-UPDATE, FAST).

Pasos:
  0   URL Gate pre-scoring (agregadores aceptados; JD >100 chars bypass) + escritura de Fetch
  1   Scoring determinístico v6.4 (Score, VM_Scope, Role_Class)
  1.5 Limpieza por fit de perfil y exclusiones
  1.6 Prioridad (Urgencia x Importancia) — ver priority_logic.py
  3   Gate Logic (Gate_Decision, Next_Action) — única fuente de verdad
  4   Análisis de patrones de rechazo

Cambios v8.0:
  - ELIMINADOS: Match, Prioridad, Fuente (props redundantes)
  - ELIMINADO: PASO 0.5 (asignación de Fuente)
  - ELIMINADO: PASO 2 (URL re-check) — Fetch se consolida en PASO 0
  - Gate_Decision y Next_Action: escritura única en PASO 3
  - Status: escritura única en PASO 0 (expiradas) y PASO 1.5 (misfits)
  - ~40% menos llamadas a API de Notion por run
  - Class A (layer, hash, dedup cross-layer): feed_processor.py

Cambios v8.1 (2026-08-03):
  - REINTEGRADO: Prioridad — Fase 3.6, vía priority_logic.py (módulo compartido
    con backfill_class_a.py, evita import circular). Escritura primaria pasa de
    backfill_class_a.py (manual, catch-up) a este run (automático, semanal).
    Ver KERNEL:TRIGGER-002 — pendiente de actualizar referencia post-patch.

Uso: python3 scripts/layer_1_run.py [--dedup-audit]

Opciones:
  --dedup-audit  Ejecuta dedup_opportunities.py al final del run para marcar
                 duplicados detectados vía fuzzy matching (empresa >=0.85, rol >=0.7)
  --dry-run      Modo diagnóstico: no escribe cambios a Notion
"""

import os
import sys
import time
import requests
import httpx
from datetime import datetime, timedelta, date
from dotenv import load_dotenv
import pathlib

# Try to set up venv path, but allow fallback to system packages
script_dir = pathlib.Path(__file__).resolve().parent
venv_path = script_dir.parent / ".venv" / "lib" / "python3.14" / "site-packages"
if venv_path.exists():
    sys.path.insert(0, str(venv_path))

from notion_client import Client
from difflib import SequenceMatcher
from gate_logic import gate_logic, TERMINAL_ACTIONS, STATUS_TERMINAL_MAP
# TERMINAL_ACTIONS y STATUS_TERMINAL_MAP viven ahora en gate_logic.py
# (módulo-level, exportables). Ver KERNEL:GATE-DECISION-010.

# ── Dry-run mode ─────────────────────────────────────────────────────────────
DRY_RUN = "--dry-run" in sys.argv

if DRY_RUN:
    print("\n" + "="*60)
    print("DRY RUN MODE — No se escribirán cambios a Notion")
    print("="*60 + "\n")

# ---------- Utilidades ----------
def txt(prop):
    if not prop: return ""
    t = prop.get("type")
    if t == "url": return prop.get("url") or ""
    if t == "rich_text" and prop.get("rich_text"):
        return "".join(chunk["plain_text"] for chunk in prop["rich_text"])
    if t == "select" and prop.get("select"):
        return prop["select"]["name"]
    if t == "title" and prop.get("title"):
        return "".join(chunk["plain_text"] for chunk in prop["title"])
    if t == "number": return prop.get("number")
    if t == "date" and prop.get("date"):
        return prop["date"]["start"]
    return ""

VANTAGE_DATA_SOURCE_ID = "442938be-fc42-828f-b72e-076818d65a5b"
VANTAGE_NOTION_VERSION = "2025-09-03"
VANTAGE_NOTION_API_BASE = "https://api.notion.com/v1"
VANTAGE_MAX_EXPECTED_RESULTS = 250


_QUERY_ALL_ITEMS_CALLS = 0
def query_all_items(client, ds_id=None):
    """
    Pagina todos los registros vía data_sources/{id}/query (API 2025-09-03).
    FIX v8.2 — databases.query queda roto en DBs multi-source: el cursor
    cambia en cada llamada pero regresa el mismo conjunto (loop infinito con
    cursores únicos, no detectable por seen_cursors). Se migra al endpoint
    de data_sources, mismo patrón que consolidate_duplicates.py.
    El parámetro ds_id se ignora (se mantiene por compatibilidad con los
    llamadores existentes); el data source real es VANTAGE_DATA_SOURCE_ID.

    FIX auditoría duplicados-paginación (2026-07-29, Bug Tracker pendiente
    de alta): sort único por created_time no es clave estable de orden
    cuando hay empates exactos (imports batch de feed_processor.py). Bajo
    keyset pagination esto produce solapamiento inestable entre páginas
    DENTRO de una misma llamada (evidencia: dry-run Fase 4, 38 líneas de
    output para 10 IDs únicos). Mitigación: (a) segundo criterio de sort
    por last_edited_time (best-effort, no elimina el empate garantizado);
    (b) deduplicación defensiva por id antes de retornar, con log de
    duplicados detectados para no ocultar el síntoma; (c) guarda contra
    next_cursor vacío con has_more=True (bug latente distinto, blindaje
    barato, no confirmado en la evidencia). NO se descarta que el mismo
    empate cause omisiones además de duplicados — pendiente de chequeo de
    completitud aparte, fuera de este fix.
    """
    token = os.environ["NOTION_TOKEN"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": VANTAGE_NOTION_VERSION,
        "Content-Type": "application/json",
    }
    url = f"{VANTAGE_NOTION_API_BASE}/data_sources/{VANTAGE_DATA_SOURCE_ID}/query"

    global _QUERY_ALL_ITEMS_CALLS
    _QUERY_ALL_ITEMS_CALLS += 1
    print(f"  [DEBUG] query_all_items call #{_QUERY_ALL_ITEMS_CALLS}")
    all_results = []
    cursor = None
    seen_ids = set()
    duplicate_ids_seen = []  # evidencia diagnóstica — no ocultar el síntoma

    with httpx.Client(timeout=30) as http_client:
        while True:
            body = {
                "page_size": 100,
                "sorts": [
                    {"timestamp": "created_time", "direction": "ascending"},
                    # Desempate best-effort — ver docstring. No garantiza
                    # eliminar colisiones exactas de created_time en
                    # imports batch (feed_processor.py).
                    {"timestamp": "last_edited_time", "direction": "ascending"},
                ],
            }
            if cursor:
                body["start_cursor"] = cursor

            response = http_client.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()

            batch = data.get("results", [])

            # Deduplicación defensiva + instrumentación de evidencia.
            # Independiente de la causa raíz: si Notion repite un id entre
            # páginas de la MISMA llamada, no debe inflar all_results ni
            # los conteos/prints aguas abajo (Fases 1-4).
            new_batch = []
            for record in batch:
                rid = record.get("id")
                if rid in seen_ids:
                    duplicate_ids_seen.append(rid)
                    continue
                seen_ids.add(rid)
                new_batch.append(record)
            all_results.extend(new_batch)

            if len(all_results) > VANTAGE_MAX_EXPECTED_RESULTS:
                print(
                    f"  ⚠️  query_all_items: MAX_EXPECTED_RESULTS "
                    f"({VANTAGE_MAX_EXPECTED_RESULTS}) excedido — abortando paginación"
                )
                break

            if not data.get("has_more"):
                break

            next_cursor = data.get("next_cursor")
            if not next_cursor:
                # Guarda defensiva: has_more=True pero next_cursor vacío
                # repetiría el body sin start_cursor (loop en página 1).
                # No observado en la evidencia actual, blindaje barato.
                print(
                    "  ⚠️  query_all_items: has_more=True pero next_cursor "
                    "vacío — abortando paginación para evitar loop"
                )
                break
            cursor = next_cursor

    if duplicate_ids_seen:
        print(
            f"  ⚠️  query_all_items: {len(duplicate_ids_seen)} duplicados "
            f"detectados y descartados dentro de la misma llamada "
            f"(paginación inestable por empate de sort key). "
            f"IDs (primeros 10, truncados): "
            f"{[str(d)[:8] for d in duplicate_ids_seen[:10]]}"
        )

    return all_results

# ---------- Lista de agregadores ----------
AGREGADOR_DOMAINS = [
    "linkedin.com",
    "indeed.com",
    "occ.com.mx",
    "glassdoor.com",
    "bumeran.com",
    "computrabajo.com",     # fix v7.5.1: dominio principal (www/mx subdomain)
    "computrabajo.com.mx"   # variante regional MX
]

def is_agregador(url):
    """Determina si la URL pertenece a un agregador de empleo"""
    import urllib.parse
    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc.lower()
    for pattern in AGREGADOR_DOMAINS:
        if domain.endswith(pattern):
            return True
    return False

def normalize_url(url):
    """
    Normaliza URLs agregando esquema https:// si falta.
    Si la URL ya tiene http:// o https://, se devuelve sin cambios.
    """
    if not url or not isinstance(url, str):
        return url
    url = url.strip()
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return f"https://{url}"



# ---------- Validación de URL ----------
def validate_url_pre_ingestion(url, jd_text=""):
    """
    GATE CRÍTICO v7.5 - Acepta agregadores sin exigir CTA directa
    JD > 100 chars = VÁLIDO sin importar URL
    """
    # Normalizar URL: agregar https:// si falta esquema
    url = normalize_url(url)
    
    # PRIORIDAD 1: JD existente — skip URL validation
    if jd_text and isinstance(jd_text, str):
        jd_clean = jd_text.strip()
        if len(jd_clean) > 100:
            return True, "JD_ALREADY_EXISTS"

    # PRIORIDAD 2: Agregador — verificación ligera, NO bypass ciego (BUG FIX)
    # LinkedIn/Indeed/Computrabajo bloquean scrapers: usamos timeout corto
    # para no colgar, pero ya no asumimos "Accesible" sin intentar nada.
    if is_agregador(url):
        try:
            agg_response = requests.head(url, allow_redirects=True, timeout=6, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            if agg_response.status_code == 200:
                return True, "AGREGADOR_VERIFIED"
            return False, f"AGREGADOR_STATUS_{agg_response.status_code}"
        except requests.exceptions.RequestException:
            return True, "AGREGADOR_UNVERIFIED"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }

        # Whitelist de dominios problemáticos conocidos (career pages)
        problematic_domains = ['jobs.nike.com', 'workable.com', 'greenhouse.io', 'lever.co']
        import urllib.parse
        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc.lower()

        for problematic in problematic_domains:
            if problematic in domain:
                return True, f"WHITELISTED_DOMAIN_{problematic}"

        # HEAD + follow redirects con timeout extendido
        response = requests.head(url, allow_redirects=True, timeout=12, headers=headers)

        # Status 200 OK obligatorio
        if response.status_code != 200:
            # Para Nike/Workable, intentar GET si HEAD falla
            if any(domain in url.lower() for domain in ['nike.com', 'workable.com']):
                try:
                    get_response = requests.get(url, timeout=12, headers=headers)
                    if get_response.status_code == 200:
                        return True, "SPA_SITE_DETECTED"
                except:
                    pass
            return False, f"STATUS_{response.status_code}"

        final_url = response.url.lower()

        # No URLs de tracking
        tracking_params = ["utm_", "gclid", "fbclid", "ref=", "source="]
        if any(param in final_url for param in tracking_params):
            return False, "TRACKING_URL"

        # Si es un agregador, aceptamos sin verificar CTA directa
        if is_agregador(url):
            return True, "AGREGADOR_VALID"

        # Debe ser página de aplicación directa (career pages oficiales)
        apply_patterns = [
            "/apply", "/careers/", "/jobs/",
            "lever.co", "greenhouse.io", "workable.com",
            "/postular", "/vacante", "/trabajo"
        ]

        # Verificar en URL final
        url_has_apply = any(pattern in final_url for pattern in apply_patterns)

        # Si no está en URL, verificar en página
        if not url_has_apply:
            try:
                html_response = requests.get(url, timeout=12, headers=headers)
                html_text = html_response.text.lower()
                apply_indicators = [
                    "apply now", "postular", "aplicar",
                    "submit application", "enviar cv", "postulación",
                    "apply for this", "apply today", "apply online"
                ]
                if not any(indicator in html_text for indicator in apply_indicators):
                    # Para Nike, aceptar si tiene contenido sustancial
                    if 'nike.com' in url.lower() and len(html_text) > 5000:
                        return True, "NIKE_SPA_DETECTED"
                    return False, "NO_APPLY_CTA"
            except:
                return False, "PAGE_FETCH_FAIL"

        return True, "VALID"

    except requests.exceptions.Timeout:
        return False, "TIMEOUT"
    except requests.exceptions.TooManyRedirects:
        return False, "TOO_MANY_REDIRECTS"
    except Exception as e:
        return False, f"ERROR: {str(e)[:30]}"



def get_vm_scope(role_title):
    if not role_title or len(role_title.strip()) < 3:
        return "Bajo"
    role_lower = role_title.lower()
    vm_terms = ["visual merchandising", "visual", "vm", "brand environment",
                "estándares visuales", "store design", "retail design"]
    for term in vm_terms:
        if term in role_lower:
            return "Alto"
    return "Bajo"

def get_role_class(role_title):
    if not role_title or len(role_title.strip()) < 3:
        return "Otro"
    role_lower = role_title.lower()
    vm_terms = ["visual merchandising", "visual", "vm", "brand environment"]
    for term in vm_terms:
        if term in role_lower:
            return "VM"
    pivot_terms = [
        "training", "experience", "producer", "brand experience",
        "retail design", "store design", "trade marketing", "shopper",
        "activation", "environment", "creative director", "creative lead",
    ]
    for term in pivot_terms:
        if term in role_lower:
            return "Pivote"
    return "Otro"

def calculate_score_v6(entry):
    """
    SCORING v6.4 – Marzo 2026
    Incluye High Impact Retail, Innovation DNA y Agencias Experienciales
    """
    score = 0
    jd_text = (entry.get("jd", "") or "").lower()
    company = (entry.get("company", "") or "").lower()
    title = (entry.get("title", "") or "").lower()

    # 1. BASE SCORE: +40 si pasó URL_GATE
    score += 40

    # 2. VISUAL_SIGNAL: +20
    visual_terms = [
        "visual", "diseño", "brand", "experience", "experiencia",
        "merchandising", "store", "tienda", "retail", "ambiente",
        "estándares", "guidelines", "portfolio", "creativo",
        "escenografía", "montaje", "exhibición", "pop", "punto de venta",
        "trade marketing", "shopper", "customer journey"
    ]
    if any(term in jd_text for term in visual_terms):
        score += 20

    # 3. COMPANY IMPACT: +15 (empresas target ampliadas)
    high_impact = [
        "nike", "apple", "inditex", "zara", "adidas",
        "lvmh", "kering", "richemont", "chanel", "hermès",
        "dior", "guerlain", "louis vuitton", "gentle monster",
        "grupo habita", "ben & frank", "auditoire", "another",
        "sephora", "massimo dutti", "ikea", "cartier", "on ",
        "on running", "aesop", "bershka", "stradivarius",
        "oysho", "pull&bear"
    ]
    if any(brand in company for brand in high_impact):
        score += 15

    # 4. ROLE QUALITY: +10
    quality_titles = [
        "manager", "coordinator", "lead", "jefe", "líder",
        "specialist", "expert", "designer", "architect"
    ]
    if any(role in title for role in quality_titles):
        score += 10

    # 5. RECRUITER PRESENCE: +10
    if entry.get("contact") or "contacto" in jd_text or "recruiter" in jd_text:
        score += 10

    # 6. INNOVATION / COOL DNA: +5
    innovative = [
        "gentle monster", "grupo habita", "ben & frank",
        "sede cafe", "auditoire", "another", "magnus",
        "aesop", "on running", "someone somewhere",
        "astound group", "minuto x minuto", "taste mkt",
        "alo yoga", "skims", "pop mart", "cyklar"
    ]
    if any(brand in company for brand in innovative):
        score += 5

    # 7. SCALE BONUS: +5 (empresas con escala + manager)
    scale_companies = ["lvmh", "inditex", "nike", "apple", "adidas", "sephora"]
    if any(brand in company for brand in scale_companies) and "manager" in title:
        score += 5

    # 8. PIVOT BONUS: +5 (roles de transición)
    pivot_roles = ["experience", "creative", "brand", "environment", "activation",
                   "marketing", "trade", "shopper", "retail design", "store design"]
    if any(role in title for role in pivot_roles):
        score += 5

    # 9. AGENCY BONUS: +5 (agencias de marketing vivencial / BTL)
    agency_names = ["auditoire", "another", "astound", "bisonte", "magnus",
                    "minuto x minuto", "taste mkt", "astound group"]
    if any(agency in company for agency in agency_names):
        score += 5

    # 10. LUXURY HERITAGE: +5 (marcas con historia en lujo, para mantener su ventaja frente a retail masivo)
    luxury_pure = ["dior", "guerlain", "louis vuitton", "chanel", "hermès",
                   "cartier", "fendi", "gucci", "bottega veneta"]
    if any(maison in company for maison in luxury_pure):
        score += 5

    return min(score, 100)



def gate(fetch, vm_scope, role_class, source_type, score=None, rol="", marca=""):
    from profile_fit import has_vm_title_signal, is_role_excluded, resolve_alias_flags

    if is_role_excluded(rol) or resolve_alias_flags(marca)[0]:
        return "BLOCKED"
    if source_type in ["Inbound", "Referencia", "Networking"]:
        return "CREATE"
    if source_type == "Vacante":
        fetch_ok = fetch in ("Accesible", "Parcial")
        scope_ok = fetch_ok and (
            vm_scope == "Alto"
            or (role_class == "Pivote" and has_vm_title_signal(rol))
        )
        if not scope_ok:
            return "BLOCKED"
        # H1 FIX (KERNEL:GATE-DECISION-002 / GATE-DECISION-011 fila 2, v9.18.0):
        # Score decide la banda final una vez superado el filtro de scope/fetch.
        # Score ausente (None) -> REVIEW_NEEDED, nunca BLOCKED silencioso --
        # perder una vacante por dato faltante es peor que pedir revisión manual.
        if score is None:
            return "REVIEW_NEEDED"
        if score >= 60:
            return "CREATE"
        if score >= 40:
            return "REVIEW_NEEDED"
        return "BLOCKED"
    return "BLOCKED"

def evaluate_application_status(status):
    application_statuses = ["Postulado", "En proceso", "Negociando", "Sin respuesta"]
    return status in application_statuses

def evaluate_rejection_status(status):
    return status == "Rechazado"

def get_application_next_action(status):
    if status == "Postulado":
        return "Follow-up"
    elif status == "En proceso":
        return "Interview prep"
    elif status == "Negociando":
        return "Follow-up"
    elif status == "Sin respuesta":
        return "Follow-up"
    else:
        return "Re-check"



def analyze_outcome_patterns():
    try:
        load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
        client = Client(auth=os.environ["NOTION_TOKEN"])
        ds_id = "442938be-fc42-828f-b72e-076818d65a5b"
        items = query_all_items(client, ds_id)
        rejection_patterns = {}
        score_effectiveness = {}
        timing_patterns = {}
        for item in items:
            props = item["properties"]
            status = txt(props.get("Status"))
            score = props.get("Score", {}).get("number") or 0
            applied_date = txt(props.get("Applied"))
            rejected_date = txt(props.get("Rej Date"))
            marca = txt(props.get("Marca"))
            vm_scope = txt(props.get("VM_Scope"))
            if status == "Rechazado":
                score_bracket = f"Score {score}"
                if score_bracket not in score_effectiveness:
                    score_effectiveness[score_bracket] = {"applied": 0, "rejected": 0}
                score_effectiveness[score_bracket]["rejected"] += 1
                if marca:
                    if marca not in rejection_patterns:
                        rejection_patterns[marca] = {"applied": 0, "rejected": 0}
                    rejection_patterns[marca]["rejected"] += 1
            elif status in ["Postulado", "En proceso", "Negociando"]:
                score_bracket = f"Score {score}"
                if score_bracket not in score_effectiveness:
                    score_effectiveness[score_bracket] = {"applied": 0, "rejected": 0}
                score_effectiveness[score_bracket]["applied"] += 1
                if marca:
                    if marca not in rejection_patterns:
                        rejection_patterns[marca] = {"applied": 0, "rejected": 0}
                    rejection_patterns[marca]["applied"] += 1
            if applied_date and rejected_date:
                try:
                    applied_dt = datetime.strptime(applied_date, "%Y-%m-%d").date()
                    rejected_dt = datetime.strptime(rejected_date, "%Y-%m-%d").date()
                    days_to_rejection = (rejected_dt - applied_dt).days
                    timing_key = f"{vm_scope}_VM"
                    if timing_key not in timing_patterns:
                        timing_patterns[timing_key] = []
                    timing_patterns[timing_key].append(days_to_rejection)
                except:
                    pass
        return {
            "rejection_patterns": rejection_patterns,
            "score_effectiveness": score_effectiveness,
            "timing_patterns": timing_patterns
        }
    except Exception as e:
        print(f"WARNING: Error analyzing patterns: {e}")
        return None

def main():
    print("VANTAGE Pipeline Runner v8.0")
    print("=" * 60)

    # Find .env file in project root
    script_dir = pathlib.Path(__file__).resolve().parent
    project_root = script_dir.parent
    env_file = project_root / ".env"
    
    if not env_file.exists():
        # Try alternate location
        env_file = project_root.parent / ".env"
    
    load_dotenv(dotenv_path=env_file, override=True)
    
    if "NOTION_TOKEN" not in os.environ:
        print(f"❌ ERROR: NOTION_TOKEN not found in environment")
        print(f"   Looking for .env at: {env_file}")
        print(f"   .env exists: {env_file.exists()}")
        sys.exit(1)
    
    client = Client(auth=os.environ["NOTION_TOKEN"])
    ds_id = "442938be-fc42-828f-b72e-076818d65a5b"

    # ==================== FASE 1: CLASIFICACIÓN (VM_Scope, Role_Class, Source_Type) ====================
    print("\nFase 1: Clasificacion (VM_Scope, Role_Class, Source_Type)...")
    items = query_all_items(client, ds_id)
    scoring_updates = 0
    scoring_changes = []
    ready_to_apply = 0

    # Auto-asignación Source_Type vacío
    source_updates = 0
    for item in items:
        props = item["properties"]
        url = txt(props.get("URL"))
        if not url:
            continue
        st = (props.get("Source_Type ", {}).get("select") or {}).get("name", "")
        if not st:
            if not DRY_RUN:
                try:
                    client.pages.update(
                        page_id=item["id"],
                        properties={"Source_Type ": {"select": {"name": "Vacante"}}}
                    )
                    source_updates += 1
                except Exception as e:
                    print(f"WARNING: Error asignando Source_Type {item['id'][:8]}: {e}")
            else:
                print(f"[DRY-RUN] {item['id'][:8]}: actualizaría Source_Type -> Vacante")
                source_updates += 1
    if source_updates > 0:
        print(f"OK Source_Type=Vacante asignado en {source_updates} registros")
    else:
        print("OK Source_Type: Sin cambios")

    # Clasificación VM_Scope + Role_Class (sin Score aún — depende de FASE 3)
    clasificacion_updates = 0
    for item in items:
        props = item["properties"]
        rol = txt(props.get("Rol"))
        current_vm_scope = txt(props.get("VM_Scope"))
        current_role_class = txt(props.get("Role_Class"))
        new_vm_scope = get_vm_scope(rol)
        new_role_class = get_role_class(rol)

        update_props = {}
        changes = []
        if current_vm_scope != new_vm_scope:
            update_props["VM_Scope"] = {"select": {"name": new_vm_scope}}
            changes.append(f"VM_Scope: {current_vm_scope}->{new_vm_scope}")
        if current_role_class != new_role_class:
            update_props["Role_Class"] = {"select": {"name": new_role_class}}
            changes.append(f"Role_Class: {current_role_class}->{new_role_class}")

        if update_props:
            if not DRY_RUN:
                try:
                    client.pages.update(page_id=item["id"], properties=update_props)
                    clasificacion_updates += 1
                    empresa = txt(props.get("Marca")) or "Sin empresa"
                    scoring_changes.extend([f"[{item['id'][:8]}] {empresa}: {c}" for c in changes])
                except Exception as e:
                    print(f"X Error clasificacion {item['id'][:8]}: {e}")
            else:
                clasificacion_updates += 1
                empresa = txt(props.get("Marca")) or "Sin empresa"
                scoring_changes.extend([f"[{item['id'][:8]}] {empresa}: {c}" for c in changes])
                print(f"[DRY-RUN] {item['id'][:8]}: actualizaría {list(update_props.keys())}")

    if clasificacion_updates > 0:
        print(f"OK Clasificacion: {clasificacion_updates} registros actualizados")
    else:
        print("OK Clasificacion: Sin cambios")

    # ==================== FASE 2: VALIDACIÓN (URL Gate + Fetch) ====================
    print("\nFase 2: Validacion URL Gate...")
    items = query_all_items(client, ds_id)
    url_gate_updates = 0
    url_gate_rejects = 0
    jd_bypass_count = 0
    whitelist_bypass_count = 0
    BYPASS_TYPES = {"Inbound", "Referencia", "Networking"}
    bypass_count = 0

    for item in items:
        props = item["properties"]
        url = txt(props.get("URL"))
        source_type = txt(props.get("Source_Type ")) or "Vacante"
        status = txt(props.get("Status"))
        current_fetch = txt(props.get("Fetch"))
        jd_text = txt(props.get("JD"))

        # Bypass — Gate_Decision se asigna en FASE 4
        if source_type in BYPASS_TYPES:
            bypass_count += 1
            continue

        # Solo Vacantes activas con URL
        if source_type != "Vacante" or not url:
            continue

        if status in ["Expirada", "Rechazado", "Archivar", "Contratado"]:
            continue

        # KERNEL:GATE-DECISION-010: Proteger Status=Target con JD ya presente
        # Evita que fallos de red/parseo sobrescriban vacantes ya verificadas manualmente
        if status == "Target" and jd_text and len(jd_text.strip()) > 100:
            continue

        # JD tiene prioridad absoluta
        is_valid, reason = validate_url_pre_ingestion(url, jd_text)

        if not is_valid:
            url_gate_rejects += 1
            empresa = txt(props.get("Marca")) or "Sin empresa"
            rol = txt(props.get("Rol")) or "Sin rol"
            print(f"X [{item['id'][:8]}] {empresa} - {rol[:30]}...")
            print(f"   URL Gate fallo: {reason}")
            if not DRY_RUN:
                try:
                    client.pages.update(
                        page_id=item["id"],
                        properties={
                            "Fetch": {"select": {"name": "Bloqueado"}},
                            "Status": {"select": {"name": "Expirada"}},
                            "Next_Action": {"select": {"name": "Archivar"}},
                        }
                    )
                except Exception as e:
                    print(f"WARNING: Error actualizando {item['id'][:8]}: {e}")
            else:
                print(f"[DRY-RUN] {item['id'][:8]}: actualizaría ['Fetch', 'Status', 'Next_Action'] -> Bloqueado / Expirada / Archivar")
        else:
            url_gate_updates += 1
            if reason == "JD_ALREADY_EXISTS":
                jd_bypass_count += 1
            elif "WHITELISTED" in reason or "SPA" in reason:
                whitelist_bypass_count += 1

            # FIX BUG CRÍTICO (Bug Tracker 3aa938be-fc42-818b-a4b9-f66c144ef50d):
            # el camino de éxito nunca escribía Fetch, dejándolo vacío y forzando
            # BLOCKED en gate() por default. Solo escribe si hace falta, para no
            # sumar llamadas innecesarias a la API (current_fetch ya viene de línea 574).
            if current_fetch != "Accesible":
                if not DRY_RUN:
                    try:
                        client.pages.update(
                            page_id=item["id"],
                            properties={
                                "Fetch": {"select": {"name": "Accesible"}},
                            }
                        )
                    except Exception as e:
                        print(f"WARNING: Error actualizando Fetch {item['id'][:8]}: {e}")
                else:
                    print(f"[DRY-RUN] {item['id'][:8]}: actualizaría ['Fetch'] -> Accesible")

    print(f"OK URL Gate: {url_gate_updates} validos, {url_gate_rejects} rechazados")
    if jd_bypass_count > 0:
        print(f"   -> {jd_bypass_count} bypass por JD existente")
    if whitelist_bypass_count > 0:
        print(f"   -> {whitelist_bypass_count} bypass por whitelist/SPA")
    if bypass_count > 0:
        print(f"   -> {bypass_count} entradas BYPASS protegidas (Gate en Fase 4)")

    # ==================== FASE 3: SCORING v6.4 ====================
    print("\nFase 3: Scoring deterministico v6.4...")
    items = query_all_items(client, ds_id)

    for item in items:
        props = item["properties"]
        rol = txt(props.get("Rol"))
        marca = txt(props.get("Marca"))
        jd = txt(props.get("JD"))
        contacto = txt(props.get("Contacto"))
        current_score = props.get("Score", {}).get("number")
        source_type = txt(props.get("Source_Type ")) or "Vacante"
        status = txt(props.get("Status"))
        current_action = txt(props.get("Next_Action"))

        # H2 FIX (KERNEL:GATE-DECISION-010): Proteger registros terminales de recálculo de Score
        # Si gate_logic() retornaría algo no-None, el registro es terminal/protected y no debe mutar
        entry = {"Next_Action": current_action, "Status": status}
        protected = gate_logic(entry)
        if protected is not None:
            continue  # Skip terminal/protected records

        entry_data = {"title": rol, "company": marca, "jd": jd, "contact": contacto}
        
        # Determinar método de scoring (Hallazgo 3 - Arena spec)
        if source_type in ["Inbound", "Referencia", "Networking"]:
            score_method = "BYPASS"
            # Bypass: Score se deja en 0 o valor existente, no se recalcula
            new_score = current_score if current_score is not None else 0
        else:
            score_method = "DETERMINISTIC"
            new_score = calculate_score_v6(entry_data)

        if new_score >= 60:
            ready_to_apply += 1

        if current_score != new_score or current_score is None:
            if not DRY_RUN:
                try:
                    update_props = {"Score": {"number": new_score}}
                    # Solo escribir Score_Method si existe la propiedad en schema
                    # (si no existe, el update fallará silenciosamente para ese campo)
                    try:
                        update_props["Score_Method"] = {"select": {"name": score_method}}
                    except:
                        pass  # Campo no existe en schema aún
                    
                    client.pages.update(
                        page_id=item["id"],
                        properties=update_props
                    )
                    scoring_updates += 1
                    empresa = marca or "Sin empresa"
                    scoring_changes.append(f"[{item['id'][:8]}] {empresa}: Score {current_score}->{new_score} ({score_method})")
                except Exception as e:
                    print(f"X Error scoring {item['id'][:8]}: {e}")
            else:
                scoring_updates += 1
                empresa = marca or "Sin empresa"
                scoring_changes.append(f"[{item['id'][:8]}] {empresa}: Score {current_score}->{new_score} ({score_method})")
                print(f"[DRY-RUN] {item['id'][:8]}: actualizaría ['Score'] -> {new_score}, ['Score_Method'] -> {score_method}")

    if scoring_updates > 0:
        print(f"OK Scoring v6.4: {scoring_updates} cambios")
        for change in scoring_changes[:5]:
            print(f"  -> {change}")
        if len(scoring_changes) > 5:
            print(f"  -> ... y {len(scoring_changes)-5} cambios mas")
    else:
        print("OK Scoring: Sin cambios")
    print(f"Ready-to-Apply (>=60 puntos): {ready_to_apply}")

    # ==================== FASE 3.5: LIMPIEZA POR FIT / EXCLUSIONES ====================
    print("\nFase 3.5: Limpieza por fit de perfil y exclusiones...")
    from profile_fit import profile_misfit_reasons, should_auto_cleanup

    misfit_updates = 0
    for item in items:
        props = item["properties"]
        rol = txt(props.get("Rol"))
        marca = txt(props.get("Marca"))
        status = txt(props.get("Status"))
        source_type = txt(props.get("Source_Type ")) or "Vacante"
        vm_scope = txt(props.get("VM_Scope")) or get_vm_scope(rol)
        role_class = txt(props.get("Role_Class")) or get_role_class(rol)
        score = props.get("Score", {}).get("number")
        reasons = profile_misfit_reasons(
            rol=rol, marca=marca, vm_scope=vm_scope, role_class=role_class,
            source_type=source_type, score=score,
        )
        if not should_auto_cleanup(status, reasons):
            continue
        if not DRY_RUN:
            try:
                client.pages.update(
                    page_id=item["id"],
                    properties={
                        "Status": {"select": {"name": "Expirada"}},
                        "Next_Action": {"select": {"name": "Archivar"}},
                    },
                )
                misfit_updates += 1
                print(f"  X [{item['id'][:8]}] {marca[:20]} | {rol[:35]} -> Expirada ({reasons[0]})")
            except Exception as e:
                print(f"WARNING: Error limpiando {item['id'][:8]}: {e}")
        else:
            misfit_updates += 1
            print(f"  [DRY-RUN] {item['id'][:8]}: actualizaría ['Status', 'Next_Action'] -> Expirada / Archivar ({reasons[0]})")
    if misfit_updates:
        print(f"OK {misfit_updates} vacantes fuera de perfil marcadas Expirada")
    else:
        print("OK Sin vacantes fuera de perfil")

    # ==================== FASE 3.5.1: EXPIRACIÓN POR NAD VENCIDO ====================
    print("\nFase 3.5.1: Expiración por NAD vencido...")
    from datetime import date
    
    nad_expiry_updates = 0
    today = date.today()
    
    for item in items:
        props = item["properties"]
        status = txt(props.get("Status"))
        
        # Solo procesar registros que no estén ya en estado terminal
        if status in ["Expirada", "Archivar", "Postulado", "Rechazado"]:
            continue
        
        # Extraer NAD
        nad_field = props.get("NAD", {})
        nad_value = None
        if nad_field.get("type") == "date" and nad_field.get("date"):
            nad_value = nad_field["date"].get("start")
        
        if not nad_value:
            continue
        
        # Parsear NAD y comparar con fecha actual
        try:
            from datetime import datetime
            nad_date = datetime.strptime(nad_value, "%Y-%m-%d").date()
            if nad_date < today:
                # NAD vencido - marcar como Expirada
                if not DRY_RUN:
                    try:
                        client.pages.update(
                            page_id=item["id"],
                            properties={
                                "Status": {"select": {"name": "Expirada"}},
                                "Next_Action": {"select": {"name": "Archivar"}},
                            },
                        )
                        nad_expiry_updates += 1
                        marca = txt(props.get("Marca"))
                        rol = txt(props.get("Rol"))
                        print(f"  ⏰ [{item['id'][:8]}] {marca[:20]} | {rol[:35]} -> Expirada (NAD vencido: {nad_value})")
                    except Exception as e:
                        print(f"WARNING: Error expirando por NAD {item['id'][:8]}: {e}")
                else:
                    nad_expiry_updates += 1
                    marca = txt(props.get("Marca"))
                    rol = txt(props.get("Rol"))
                    print(f"  [DRY-RUN] {item['id'][:8]}: actualizaría ['Status', 'Next_Action'] -> Expirada / Archivar (NAD vencido: {nad_value})")
        except ValueError:
            # Formato de fecha inválido - skip
            continue
    
    if nad_expiry_updates:
        print(f"OK {nad_expiry_updates} vacantes marcadas Expirada por NAD vencido")
    else:
        print("OK Sin vacantes con NAD vencido")



    # ==================== FASE 3.6: PRIORIDAD (Urgencia x Importancia) ====================
    # Escritura primaria de Prioridad — reemplaza la dependencia de backfill_class_a.py
    # como único escritor. Corre después de Fase 3 porque necesita Score ya calculado.
    # backfill_class_a.py queda como catch-up para huecos legacy, no como vía primaria.
    print("\nFase 3.6: Prioridad (Urgencia x Importancia)...")
    from priority_logic import infer_prioridad

    prioridad_updates = 0
    prioridad_changes = []
    today = date.today()

    for item in items:
        props = item["properties"]
        current_prioridad = txt(props.get("Prioridad"))
        status = txt(props.get("Status"))
        current_action = txt(props.get("Next_Action"))

        # H2 FIX (KERNEL:GATE-DECISION-010): Proteger registros terminales de recálculo de Prioridad
        # Si gate_logic() retornaría algo no-None, el registro es terminal/protected y no debe mutar
        entry = {"Next_Action": current_action, "Status": status}
        protected = gate_logic(entry)
        if protected is not None:
            continue  # Skip terminal/protected records

        nuevo_prioridad, razon = infer_prioridad(item, today)

        if current_prioridad != nuevo_prioridad:
            if not DRY_RUN:
                try:
                    client.pages.update(
                        page_id=item["id"],
                        properties={"Prioridad": {"select": {"name": nuevo_prioridad}}},
                    )
                    prioridad_updates += 1
                    empresa = txt(props.get("Marca")) or "Sin empresa"
                    prioridad_changes.append(f"[{item['id'][:8]}] {empresa}: Prioridad {current_prioridad or '(vacío)'}->{nuevo_prioridad} ({razon})")
                except Exception as e:
                    print(f"X Error prioridad {item['id'][:8]}: {e}")
            else:
                prioridad_updates += 1
                empresa = txt(props.get("Marca")) or "Sin empresa"
                prioridad_changes.append(f"[{item['id'][:8]}] {empresa}: Prioridad {current_prioridad or '(vacío)'}->{nuevo_prioridad} ({razon})")
                print(f"[DRY-RUN] {item['id'][:8]}: actualizaría ['Prioridad'] -> {nuevo_prioridad} ({razon})")

    if prioridad_updates > 0:
        print(f"OK Prioridad: {prioridad_updates} cambios")
        for change in prioridad_changes[:5]:
            print(f"  -> {change}")
        if len(prioridad_changes) > 5:
            print(f"  -> ... y {len(prioridad_changes)-5} cambios mas")
    else:
        print("OK Prioridad: Sin cambios")

    # ==================== FASE 4: GATE LOGIC (Gate_Decision, Next_Action) ====================
    print("\nFase 4: Gate logic y Next Actions...")
    items = query_all_items(client, ds_id)
    gate_updates = 0
    gate_changes = []
    create_count = 0
    applied_count = 0
    blocked_count = 0
    review_count = 0
    protected_count = 0
    rejected_status_count = 0

    for item in items:
        props = item["properties"]
        rol = txt(props.get("Rol"))
        marca = txt(props.get("Marca"))
        fetch = txt(props.get("Fetch"))
        vm_scope = txt(props.get("VM_Scope"))
        role_class = txt(props.get("Role_Class"))
        source_type = txt(props.get("Source_Type ")) or "Vacante"
        status = txt(props.get("Status"))
        current_gate = txt(props.get("Gate_Decision"))
        current_action = txt(props.get("Next_Action"))
        score = props.get("Score", {}).get("number")

        # Saltar si está expirada/archivada
        if status in ["Expirada", "Archivar"]:
            continue

        # PRECEDENCIA OBLIGATORIA (KERNEL:GATE-DECISION-010):
        # 1. Status → STATUS_TERMINAL_MAP  (APPLIED / REJECTED)
        # 2. Next_Action → TERMINAL_ACTIONS (Archivar / Expirada)
        # 3. None → elegible para recálculo por gate()
        entry = {
            "Next_Action": current_action,
            "Status": status,
            "Gate_Decision": current_gate,
            "Fetch": fetch
        }
        protected = gate_logic(entry)
        if protected is not None:
            protected_count += 1
            # H2 FIX (KERNEL:GATE-DECISION-006): Si gate_logic() retorna "REJECTED" (Status="Rechazado"),
            # NO hacer continue para permitir que evaluate_rejection_status() aplique REJECTED+Post-Mortem
            # Esto activa la transición APPLIED→REJECTED documentada en GATE-DECISION-011 fila 11
            if protected != "REJECTED":
                continue

        # v9.14.6: JD_Quality == "JD Completo" → priorizar Optimizar (CV-A ready)
        jd_quality = txt(props.get("JD_Quality"))

        # H9 FIX (Observabilidad Opción A): Detección manual de Status=Postulado sin Gate_Decision=APPLIED
        if status == "Postulado" and current_gate != "APPLIED":
            print(f"  [OBSERVABILIDAD] {item['id'][:8]}: Status=Postulado pero Gate_Decision={current_gate or '(vacío)'} → sugerencia manual: establecer Gate_Decision=APPLIED")

        if evaluate_rejection_status(status):
            decision = "REJECTED"
            next_action = "Post-Mortem"  # v9.14.5: antes "Ninguna" -- senal explicita de analisis pendiente antes de Archivar=True
            rejected_status_count += 1
        elif evaluate_application_status(status):
            decision = "APPLIED"
            next_action = get_application_next_action(status)
            applied_count += 1
        elif jd_quality == "JD Completo":
            decision = gate(fetch, vm_scope, role_class, source_type, score=score, rol=rol, marca=marca)
            if decision == "CREATE":
                next_action = "Optimizar"
                create_count += 1
            elif decision == "REVIEW_NEEDED":
                # H1 FIX: no se optimiza CV sobre un registro que aún no supera
                # el umbral de Score -- fuerza revisión manual primero.
                next_action = "Investigar"
                review_count += 1
            else:
                next_action = "Optimizar"
                blocked_count += 1
        else:
            decision = gate(fetch, vm_scope, role_class, source_type, score=score, rol=rol, marca=marca)

            if decision == "CREATE":
                next_action = "Re-check"
                create_count += 1
            elif decision == "REVIEW_NEEDED":
                next_action = "Investigar"
                review_count += 1
            elif source_type == "Vacante" and fetch == "Bloqueado":
                next_action = "Reparar URL"
                blocked_count += 1
            elif source_type == "Vacante" and fetch == "Parcial":
                next_action = "Verificar JD"
                blocked_count += 1
            # v9.14.5: rama "elif source_type in [Inbound, Referencia, Networking]" removida --
            # era codigo muerto: gate() ya retorna CREATE para los 3 (bypass, ver 09.1),
            # por lo que siempre caian en la rama "decision == CREATE" de arriba.
            # Inbound/Referencia/Networking quedan unificados bajo Re-check via ese mismo camino.
            else:
                next_action = "Investigar"  # v9.14.5: antes "Archivar" (catch-all destructivo por default)
                blocked_count += 1

        changes = []
        if current_gate != decision:
            changes.append(f"Gate: {current_gate}->{decision}")
        if current_action != next_action:
            changes.append(f"Action: {current_action}->{next_action}")

        # H9 FIX (Observabilidad Opción A): Agregar Last_Gate_Run timestamp
        from datetime import datetime
        last_gate_run = datetime.now().isoformat()

        update = {
            "Gate_Decision": {"select": {"name": decision}},
            "Next_Action": {"select": {"name": next_action}},
            "Last_Gate_Run": {"date": {"start": last_gate_run}}
        }

        if not DRY_RUN:
            try:
                client.pages.update(page_id=item["id"], properties=update)
                gate_updates += 1
                if changes:
                    empresa = txt(props.get("Marca")) or "Sin empresa"
                    gate_changes.append(f"[{item['id'][:8]}] {empresa}: {', '.join(changes)}")
            except Exception as e:
                print(f"X Error gate {item['id'][:8]}: {e}")
        else:
            gate_updates += 1
            if changes:
                empresa = txt(props.get("Marca")) or "Sin empresa"
                gate_changes.append(f"[{item['id'][:8]}] {empresa}: {', '.join(changes)}")
            print(f"[DRY-RUN] {item['id'][:8]}: actualizaría {list(update.keys())}")

    if gate_changes:
        print(f"OK Gate: {len(gate_changes)} cambios de decision")
        for change in gate_changes[:5]:
            print(f"  -> {change}")
        if len(gate_changes) > 5:
            print(f"  -> ... y {len(gate_changes)-5} cambios mas")
    else:
        print("OK Gate: Sin cambios (todas las decisiones ya correctas)")

    print(f"Acciones protegidas: {protected_count}")

    # ==================== FASE 5: ANÁLISIS DE PATRONES ====================
    print("\nFase 5: Analisis de patrones...")
    patterns = analyze_outcome_patterns()
    if patterns:
        rejection_patterns = patterns["rejection_patterns"]
        score_effectiveness = patterns["score_effectiveness"]
        print("OK Analisis completado")
        if score_effectiveness:
            print("  Efectividad por Score:")
            for score_bracket, data in sorted(score_effectiveness.items()):
                total = data["applied"] + data["rejected"]
                if total > 0:
                    rejection_rate = (data["rejected"] / total) * 100
                    print(f"    {score_bracket}: {rejection_rate:.0f}% rechazo ({data['rejected']}/{total})")
        high_rejection_companies = []
        for company, data in rejection_patterns.items():
            total = data["applied"] + data["rejected"]
            if total >= 2:
                rejection_rate = (data["rejected"] / total) * 100
                if rejection_rate >= 70:
                    high_rejection_companies.append((company, rejection_rate, total))
        if high_rejection_companies:
            print("  Empresas con alta tasa de rechazo:")
            for company, rate, total in sorted(high_rejection_companies, key=lambda x: x[1], reverse=True)[:3]:
                print(f"    {company}: {rate:.0f}% rechazo ({total} aplicaciones)")

    # ==================== FASE 6: DEDUP AUDIT (opcional) ====================
    if "--dedup-audit" in sys.argv:
        print("\nFase 6: Dedup audit (fuzzy matching)...")
        print("Ejecutando dedup_opportunities.py para detectar duplicados...")
        
        try:
            import subprocess
            dedup_script = script_dir / "dedup_opportunities.py"
            
            # Ejecutar dedup_opportunities.py
            result = subprocess.run(
                [sys.executable, str(dedup_script)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos max
            )
            
            if result.returncode == 0:
                print("OK Dedup audit completado")
                if result.stdout:
                    print(result.stdout)
            else:
                print(f"⚠️  Dedup audit finalizó con código {result.returncode}")
                if result.stderr:
                    print(f"Error: {result.stderr}")
        except subprocess.TimeoutExpired:
            print("⚠️  Dedup audit excedió timeout de 5 minutos")
        except Exception as e:
            print(f"⚠️  Error ejecutando dedup audit: {e}")
    else:
        print("\nFase 6: Dedup audit omitido (use --dedup-audit para activar)")

    print("\n" + "=" * 60)
    print("RESUMEN FINAL v8.0:")
    print(f"  URL Gate: {url_gate_rejects} links muertos eliminados")
    print(f"  JD Bypass: {jd_bypass_count} vacantes con JD existente")
    print(f"  READY-TO-APPLY (>=60): {ready_to_apply}")
    print(f"  CREATE (Pipeline Activo): {create_count}")
    print(f"  REVIEW_NEEDED (Score 40-59): {review_count}")
    print(f"  APPLIED (En proceso): {applied_count}")
    print(f"  REJECTED: {rejected_status_count}")
    print(f"  BLOCKED: {blocked_count}")
    print(f"  PROTEGIDAS: {protected_count}")
    print(f"  Total procesado: {len(items)}")

    if scoring_changes or gate_changes:
        print("\nCAMBIOS REALIZADOS:")
        print(f"  Scoring v6.4: {len(scoring_changes)} cambios")
        print(f"  Gates: {len(gate_changes)} cambios")
    else:
        print("\nESTADO ESTABLE: Sin cambios necesarios")

    print("\nPROXIMOS PASOS (v8.0):")
    print("  1. Score vacío: Fase 3 los rellena automáticamente")
    print("  2. Filtra en Notion por 'Score >= 60' (Ready-to-Apply)")
    print("  3. Ingresos L1/L3 nuevos: feed_processor.py (Class A: layer, hash)")
    print("  4. Aplica maximo 5/semana (calidad > cantidad)")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nPipeline cancelado por usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\nError en pipeline: {e}")
        sys.exit(1)
