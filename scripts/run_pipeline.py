#!/usr/bin/env python3
"""
JHS Pipeline Runner v6.2 - Ampliado a agregadores
- Acepta vacantes de agregadores: LinkedIn Jobs, Indeed, OCC, Glassdoor, Bumeran, CompuTrabajo
- Nuevo campo "Fuente": Career Page Oficial / Agregador
- Mantiene URL_GATE y todas las protecciones existentes
Uso: python3 scripts/run_pipeline.py
"""

import os
import sys
import time
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from notion_client import Client
from difflib import SequenceMatcher

# ---------- Utilidades ----------
def txt(prop):
    if not prop: return ""
    t = prop.get("type")
    if t == "url": return prop.get("url") or ""
    if t == "rich_text" and prop.get("rich_text"):
        return prop["rich_text"][0]["plain_text"]
    if t == "select" and prop.get("select"):
        return prop["select"]["name"]
    if t == "title" and prop.get("title"):
        return prop["title"][0]["plain_text"]
    if t == "number": return prop.get("number")
    if t == "date" and prop.get("date"):
        return prop["date"]["start"]
    return ""

# ---------- Lista de agregadores ----------
AGREGADOR_DOMAINS = [
    "linkedin.com",
    "indeed.com",
    "occ.com.mx",
    "glassdoor.com",
    "bumeran.com",
    "computrabajo.com.mx"
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

def determine_fuente(url):
    """Retorna la categoría de fuente según el dominio"""
    if is_agregador(url):
        return "Agregador"
    return "Career Page Oficial"

# ---------- Validación de URL ----------
def validate_url_pre_ingestion(url, jd_text=""):
    """
    GATE CRÍTICO v6.2 - Acepta agregadores sin exigir CTA directa
    JD > 100 chars = VÁLIDO sin importar URL
    """
    # PRIORIDAD ABSOLUTA: JD > 100 chars = VÁLIDO sin validar URL
    if jd_text and isinstance(jd_text, str):
        jd_clean = jd_text.strip()
        if len(jd_clean) > 100:
            return True, "JD_ALREADY_EXISTS"

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

def check_url(url):
    """Versión mejorada con headers anti-bot y fallback a GET para sitios problemáticos"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }

        # Sitios que bloquean HEAD o devuelven 403/timeout
        problematic = ['dior.com', 'swarovski', 'workable.com', 'nike.com',
                       'richemont.com', 'coppel.com', 'occ.com.mx']
        use_get = any(p in url.lower() for p in problematic)

        if use_get:
            r = requests.get(url, allow_redirects=True, timeout=10, headers=headers)
        else:
            r = requests.head(url, allow_redirects=True, timeout=8, headers=headers)

        if 200 <= r.status_code < 400:
            return "Accesible"
        else:
            return "Bloqueado"
    except:
        return "Bloqueado"

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
    pivot_terms = ["training", "experience", "producer", "account",
                   "project", "commercial", "manager", "design", "creative"]
    for term in pivot_terms:
        if term in role_lower:
            return "Pivote"
    return "Otro"

def calculate_score_v6(entry):
    """
    SCORING v6.1 - Más realista, premia calidad sobre perfección
    Puntaje: 0-100
    UMBRAL READY-TO-APPLY: >=60 puntos
    """
    score = 0
    jd_text = (entry.get("jd", "") or "").lower()
    company = (entry.get("company", "") or "").lower()
    title = (entry.get("title", "") or "").lower()

    # 1. BASE SCORE: +40 si pasó URL_GATE (ya es link válido con CTA)
    score += 40

    # 2. VISUAL_SIGNAL: +20 (términos más amplios)
    visual_terms = [
        "visual", "diseño", "brand", "experience", "experiencia",
        "merchandising", "store", "tienda", "retail", "ambiente",
        "estándares", "guidelines", "portfolio", "creativo"
    ]
    if any(term in jd_text for term in visual_terms):
        score += 20

    # 3. COMPANY IMPACT: +15 (empresas target)
    high_impact = [
        "nike", "apple", "inditex", "zara", "adidas",
        "lvmh", "kering", "richemont", "chanel", "hermès",
        "dior", "guerlain", "louis vuitton", "gentle monster",
        "grupo habita", "ben & frank", "auditoire", "another"
    ]
    if any(brand in company for brand in high_impact):
        score += 15

    # 4. ROLE QUALITY: +10 (títulos relevantes)
    quality_titles = [
        "manager", "coordinator", "lead", "jefe", "líder",
        "specialist", "expert", "designer", "architect"
    ]
    if any(role in title for role in quality_titles):
        score += 10

    # 5. RECRUITER PRESENCE: +10 (contacto disponible)
    if entry.get("contact") or "contacto" in jd_text or "recruiter" in jd_text:
        score += 10

    # 6. INNOVATION BONUS: +5 (empresas innovadoras)
    innovative = [
        "gentle monster", "grupo habita", "ben & frank",
        "sede cafe", "auditoire", "another", "magnus"
    ]
    if any(brand in company for brand in innovative):
        score += 5

    # 7. SCALE BONUS: +5 (empresas con escala)
    scale_companies = ["lvmh", "inditex", "nike", "apple", "adidas"]
    if any(brand in company for brand in scale_companies) and "manager" in title:
        score += 5

    # 8. PIVOT BONUS: +5 (roles de transición)
    pivot_roles = ["experience", "creative", "brand", "environment", "activation"]
    if any(role in title for role in pivot_roles):
        score += 5

    return min(score, 100)

def get_match_level_v6(score):
    """Nuevos niveles basados en score 0-100"""
    if score >= 80:
        return "Excelente"  # Aplicar HOY
    elif score >= 60:
        return "Muy Bueno"  # Ready-to-Apply
    elif score >= 40:
        return "Bueno"      # Considerar
    else:
        return "Bajo"       # Revisar

def gate(fetch, vm_scope, role_class, source_type):
    if source_type in ["Inbound", "Referencia", "Networking"]:
        return "CREATE"
    if source_type == "Vacante":
        if fetch == "Accesible" and (vm_scope == "Alto" or role_class == "Pivote"):
            return "CREATE"
    return "BLOCKED"

def evaluate_application_status(status):
    application_statuses = ["Postulado", "En proceso", "Negociando", "Sin respuesta"]
    return status in application_statuses

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

def check_if_expired(url, last_seen, current_fetch):
    if current_fetch != "Bloqueado":
        return False
    if last_seen:
        try:
            last_seen_dt = datetime.strptime(last_seen, "%Y-%m-%d").date()
            days_since = (datetime.now().date() - last_seen_dt).days
            if days_since > 2:
                return True
        except:
            pass
    return False

def analyze_outcome_patterns():
    try:
        load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
        client = Client(auth=os.environ["NOTION_TOKEN"])
        ds_id = "4e542b37-6e52-4418-89b7-a0eeb3138307"
        items = client.data_sources.query(data_source_id=ds_id)["results"]
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
    print("JHS Pipeline Runner v6.2 - AGREGADORES ACTIVADOS")
    print("=" * 60)

    load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
    client = Client(auth=os.environ["NOTION_TOKEN"])
    ds_id = "4e542b37-6e52-4418-89b7-a0eeb3138307"

    # ==================== PASO 0: URL GATE PRE-SCORING ====================
    print("\nPaso 0: URL Gate (pre-scoring) - PRIORIDAD ABSOLUTA AL JD...")
    items = client.data_sources.query(data_source_id=ds_id)["results"]
    url_gate_updates = 0
    url_gate_rejects = 0
    jd_bypass_count = 0
    whitelist_bypass_count = 0

    for item in items:
        props = item["properties"]
        url = txt(props.get("URL"))
        source_type = txt(props.get("Source_Type")) or "Vacante"
        status = txt(props.get("Status"))
        current_fetch = txt(props.get("Fetch"))
        jd_text = txt(props.get("Texto JD")) or txt(props.get("JD"))

        # Solo aplicar gate a vacantes nuevas/activas
        if source_type != "Vacante" or not url:
            continue

        if status in ["Expirada", "Rechazado", "Archivar", "Contratado"]:
            continue

        # URL GATE - JD TIENE PRIORIDAD ABSOLUTA
        is_valid, reason = validate_url_pre_ingestion(url, jd_text)

        if not is_valid:
            url_gate_rejects += 1
            empresa = txt(props.get("Marca")) or "Sin empresa"
            rol = txt(props.get("Rol")) or "Sin rol"
            print(f"X [{item['id'][:8]}] {empresa} - {rol[:30]}...")
            print(f"   URL Gate fallo: {reason}")

            # Marcar como Expirada inmediatamente
            try:
                client.pages.update(
                    page_id=item["id"],
                    properties={
                        "Fetch": {"select": {"name": "Bloqueado"}},
                        "Status": {"select": {"name": "Expirada"}},
                        "Next_Action": {"select": {"name": "Archivar"}},
                        "Gate_Decision": {"select": {"name": "BLOCKED"}}
                    }
                )
            except Exception as e:
                print(f"WARNING: Error actualizando {item['id'][:8]}: {e}")
        else:
            url_gate_updates += 1
            if reason == "JD_ALREADY_EXISTS":
                jd_bypass_count += 1
            elif "WHITELISTED" in reason or "SPA" in reason:
                whitelist_bypass_count += 1

    print(f"OK URL Gate: {url_gate_updates} validos, {url_gate_rejects} rechazados")
    if jd_bypass_count > 0:
        print(f"   -> {jd_bypass_count} bypass por JD existente")
    if whitelist_bypass_count > 0:
        print(f"   -> {whitelist_bypass_count} bypass por whitelist/SPA")

    # ==================== PASO 0.5: ASIGNACIÓN DE FUENTE ====================
    print("\nPaso 0.5: Asignando campo 'Fuente'...")
    fuente_updates = 0
    for item in items:
        props = item["properties"]
        url = txt(props.get("URL"))
        source_type = txt(props.get("Source_Type")) or ""
        if source_type != "Vacante" or not url:
            continue
        current_fuente = txt(props.get("Fuente"))
        nueva_fuente = determine_fuente(url)
        if current_fuente != nueva_fuente:
            try:
                client.pages.update(
                    page_id=item["id"],
                    properties={"Fuente": {"select": {"name": nueva_fuente}}}
                )
                fuente_updates += 1
            except Exception as e:
                print(f"WARNING: Error actualizando Fuente {item['id'][:8]}: {e}")
    if fuente_updates > 0:
        print(f"OK Fuente asignada/actualizada en {fuente_updates} registros")
    else:
        print("OK Todas las fuentes ya estaban correctas")

    # ==================== PASO 1: SCORING v6.1 ====================
    print("\nPaso 1: Scoring deterministico v6.1...")
    items = client.data_sources.query(data_source_id=ds_id)["results"]
    scoring_updates = 0
    scoring_changes = []
    ready_to_apply = 0

    for item in items:
        props = item["properties"]
        rol = txt(props.get("Rol"))
        marca = txt(props.get("Marca"))
        jd = txt(props.get("Texto JD")) or txt(props.get("JD"))
        contacto = txt(props.get("Contacto"))

        current_vm_scope = txt(props.get("VM_Scope"))
        current_score = props.get("Score", {}).get("number")
        current_role_class = txt(props.get("Role_Class"))
        current_match = txt(props.get("Match"))

        new_vm_scope = get_vm_scope(rol)
        new_role_class = get_role_class(rol)

        # Calcular score v6.1
        entry_data = {
            "title": rol,
            "company": marca,
            "jd": jd,
            "contact": contacto
        }
        new_score = calculate_score_v6(entry_data)
        new_match = get_match_level_v6(new_score)

        # Contar ready-to-apply (>=60)
        if new_score >= 60:
            ready_to_apply += 1

        needs_update = False
        update_props = {}
        changes = []

        if current_vm_scope != new_vm_scope:
            update_props["VM_Scope"] = {"select": {"name": new_vm_scope}}
            changes.append(f"VM_Scope: {current_vm_scope}->{new_vm_scope}")
            needs_update = True

        if current_score != new_score:
            update_props["Score"] = {"number": new_score}
            changes.append(f"Score: {current_score}->{new_score}")
            needs_update = True

        if current_role_class != new_role_class:
            update_props["Role_Class"] = {"select": {"name": new_role_class}}
            changes.append(f"Role_Class: {current_role_class}->{new_role_class}")
            needs_update = True

        if current_match != new_match:
            update_props["Match"] = {"select": {"name": new_match}}
            changes.append(f"Match: {current_match}->{new_match}")
            needs_update = True

        if needs_update:
            try:
                client.pages.update(page_id=item["id"], properties=update_props)
                scoring_updates += 1
                if changes:
                    empresa = txt(props.get("Marca")) or "Sin empresa"
                    scoring_changes.append(f"[{item['id'][:8]}] {empresa}: {', '.join(changes)}")
            except Exception as e:
                print(f"X Error scoring {item['id'][:8]}: {e}")

    if scoring_changes:
        print(f"OK Scoring v6.1: {len(scoring_changes)} cambios")
        for change in scoring_changes[:5]:
            print(f"  -> {change}")
        if len(scoring_changes) > 5:
            print(f"  -> ... y {len(scoring_changes)-5} cambios mas")
    else:
        print("OK Scoring: Sin cambios (todas las entradas ya actualizadas)")

    print(f"Ready-to-Apply (>=60 puntos): {ready_to_apply}")

    # ==================== PASO 2: URL RE-CHECK (solo para válidos) ====================
    print("\nPaso 2: URL re-check (solo validos)...")
    items = client.data_sources.query(data_source_id=ds_id)["results"]
    url_updates = 0
    url_changes = []
    expired_suggestions = []
    skipped_recheck = 0
    jd_protected = 0

    for item in items:
        props = item["properties"]
        url = txt(props.get("URL"))
        current_fetch = txt(props.get("Fetch"))
        source_type = txt(props.get("Source_Type")) or "Vacante"
        last_seen = txt(props.get("Last_Seen_Active"))
        status = txt(props.get("Status"))
        jd_text = txt(props.get("Texto JD")) or txt(props.get("JD")) or ""

        if source_type != "Vacante" or not url:
            continue

        # Saltar si ya está marcado como expirado/rechazado
        if status in ["Expirada", "Rechazado", "Archivar"]:
            continue

        # FIX DEFINITIVO 1: No re-checkear si tiene JD > 100 y ya está Accesible
        if current_fetch == "Accesible" and len(jd_text) > 100:
            jd_protected += 1
            continue

        # FIX DEFINITIVO 2: No re-checkear dominios problemáticos conocidos
        problematic_domains = ['nike.com', 'workable.com', 'dior.com', 'swarovski',
                               'richemont.com', 'coppel.com', 'occ.com.mx']
        if any(domain in url.lower() for domain in problematic_domains) and current_fetch == "Accesible":
            skipped_recheck += 1
            continue

        new_fetch = check_url(url)

        if new_fetch != current_fetch:
            try:
                client.pages.update(
                    page_id=item["id"],
                    properties={"Fetch": {"select": {"name": new_fetch}}}
                )
                url_updates += 1
                empresa = txt(props.get("Marca")) or "Sin empresa"
                url_changes.append(f"[{item['id'][:8]}] {empresa}: {current_fetch}->{new_fetch}")

                if check_if_expired(url, last_seen, new_fetch) and status not in ["Expirada", "Rechazado"]:
                    expired_suggestions.append(f"[{item['id'][:8]}] {empresa}: Considerar cambiar Status a 'Expirada'")

            except Exception as e:
                print(f"X Error updating URL {item['id'][:8]}: {e}")

    if url_changes:
        print(f"OK URL check: {len(url_changes)} cambios de estado")
        for change in url_changes:
            print(f"  -> {change}")
    else:
        print("OK URL check: Sin cambios (todos los URLs mantienen su estado)")

    if skipped_recheck > 0:
        print(f"   -> {skipped_recheck} dominios problematicos protegidos")
    if jd_protected > 0:
        print(f"   -> {jd_protected} vacantes con JD protegidas de re-check")

    if expired_suggestions:
        print("\nSugerencias de expiracion:")
        for suggestion in expired_suggestions:
            print(f"  -> {suggestion}")

    # ==================== PASO 3: GATE LOGIC (con protección) ====================
    print("\nPaso 3: Gate logic y Next Actions...")
    items = client.data_sources.query(data_source_id=ds_id)["results"]
    gate_updates = 0
    gate_changes = []
    create_count = 0
    applied_count = 0
    blocked_count = 0
    protected_count = 0

    for item in items:
        props = item["properties"]
        fetch = txt(props.get("Fetch"))
        vm_scope = txt(props.get("VM_Scope"))
        role_class = txt(props.get("Role_Class"))
        source_type = txt(props.get("Source_Type")) or "Vacante"
        status = txt(props.get("Status"))
        current_gate = txt(props.get("Gate_Decision"))
        current_action = txt(props.get("Next_Action"))

        # PROTECCIÓN TOTAL: Si ya tiene una acción, NO MODIFICAR
        if current_action:
            protected_count += 1
            continue

        # Saltar si está expirada/rechazada
        if status in ["Expirada", "Rechazado", "Archivar"]:
            continue

        if evaluate_application_status(status):
            decision = "APPLIED"
            next_action = get_application_next_action(status)
            applied_count += 1
        else:
            decision = gate(fetch, vm_scope, role_class, source_type)

            if decision == "CREATE":
                next_action = "Re-check"
                create_count += 1
            elif source_type == "Vacante" and fetch == "Bloqueado":
                next_action = "Reparar URL"
                blocked_count += 1
            elif source_type == "Vacante" and fetch == "Parcial":
                next_action = "Verificar JD"
                blocked_count += 1
            elif source_type in ["Inbound", "Referencia", "Networking"]:
                next_action = "Re-check"
                if decision != "CREATE":
                    create_count += 1
            else:
                next_action = "Archivar"
                blocked_count += 1

        changes = []
        if current_gate != decision:
            changes.append(f"Gate: {current_gate}->{decision}")
        if current_action != next_action:
            changes.append(f"Action: {current_action}->{next_action}")

        update = {
            "Gate_Decision": {"select": {"name": decision}},
            "Next_Action": {"select": {"name": next_action}}
        }

        try:
            client.pages.update(page_id=item["id"], properties=update)
            gate_updates += 1
            if changes:
                empresa = txt(props.get("Marca")) or "Sin empresa"
                gate_changes.append(f"[{item['id'][:8]}] {empresa}: {', '.join(changes)}")
        except Exception as e:
            print(f"X Error gate {item['id'][:8]}: {e}")

    if gate_changes:
        print(f"OK Gate: {len(gate_changes)} cambios de decision")
        for change in gate_changes[:5]:
            print(f"  -> {change}")
        if len(gate_changes) > 5:
            print(f"  -> ... y {len(gate_changes)-5} cambios mas")
    else:
        print("OK Gate: Sin cambios (todas las decisiones ya correctas)")

    print(f"Acciones protegidas: {protected_count}")

    # ==================== PASO 4: ANÁLISIS DE PATRONES ====================
    print("\nPaso 4: Analisis de patrones...")
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

    print("\n" + "=" * 60)
    print("RESUMEN FINAL v6.2 - AGREGADORES ACTIVADOS:")
    print(f"  URL Gate: {url_gate_rejects} links muertos eliminados")
    print(f"  JD Bypass: {jd_bypass_count} vacantes con JD existente")
    print(f"  Fuente actualizada: {fuente_updates} registros")
    print(f"  READY-TO-APPLY (>=60): {ready_to_apply}")
    print(f"  CREATE (Pipeline Activo): {create_count}")
    print(f"  APPLIED (En proceso): {applied_count}")
    print(f"  BLOCKED: {blocked_count}")
    print(f"  PROTEGIDAS: {protected_count}")
    print(f"  Total procesado: {len(items)}")

    if scoring_changes or url_changes or gate_changes:
        print("\nCAMBIOS REALIZADOS:")
        print(f"  Scoring v6.1: {len(scoring_changes)} cambios")
        print(f"  URLs: {len(url_changes)} cambios")
        print(f"  Gates: {len(gate_changes)} cambios")
    else:
        print("\nESTADO ESTABLE: Sin cambios necesarios")

    print("\nPROXIMOS PASOS (v6.2):")
    print("  1. Agregadores ahora son aceptados (LinkedIn, Indeed, OCC, etc.)")
    print("  2. Campo 'Fuente' identifica si es Career Page Oficial o Agregador")
    print("  3. URL Gate sigue protegiendo de links muertos (agregadores incluidos)")
    print("  4. Nike, Workable y demas protegidos sin cambios")
    print("  5. Abre Notion -> Filtra por 'Score >= 60' (Ready-to-Apply)")
    print("  6. Prioriza 'Excelente' > 'Muy Bueno'")
    print("  7. Aplica maximo 5/semana (calidad > cantidad)")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nPipeline cancelado por usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\nError en pipeline: {e}")
        sys.exit(1)