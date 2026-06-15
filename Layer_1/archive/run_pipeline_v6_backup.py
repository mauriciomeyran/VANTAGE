#!/usr/bin/env python3
"""
JHS Pipeline Runner v6.0 - Optimizado para velocidad de aplicación
Uso: python3 scripts/run_pipeline_v6.py
"""

import os
import sys
import time
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from notion_client import Client
from difflib import SequenceMatcher

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

def validate_url_pre_ingestion(url):
    """
    GATE CRÍTICO v6: Validación estricta pre-scoring
    Si falla → NO procesar, marcar como Expirada inmediatamente
    """
    try:
        # HEAD + follow redirects (más robusto)
        response = requests.head(url, allow_redirects=True, timeout=8, 
                                headers={'User-Agent': 'Mozilla/5.0'})
        
        # 1. Status 200 OK obligatorio
        if response.status_code != 200:
            return False, f"STATUS_{response.status_code}"
        
        final_url = response.url.lower()
        
        # 2. No URLs de tracking
        tracking_params = ["utm_", "gclid", "fbclid", "ref=", "source="]
        if any(param in final_url for param in tracking_params):
            return False, "TRACKING_URL"
        
        # 3. Debe ser página de aplicación directa
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
                html_response = requests.get(url, timeout=8, 
                                           headers={'User-Agent': 'Mozilla/5.0'})
                html_text = html_response.text.lower()
                apply_indicators = [
                    "apply now", "postular", "aplicar",
                    "submit application", "enviar cv", "postulación"
                ]
                if not any(indicator in html_text for indicator in apply_indicators):
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
    """Versión legacy - mantener compatibilidad"""
    try:
        r = requests.head(url, allow_redirects=True, timeout=8)
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
    NUEVO SCORING v6: Velocidad de aplicación > Etiqueta de lujo
    Puntaje: 0-100
    """
    score = 0
    jd_text = (entry.get("jd", "") or "").lower()
    company = (entry.get("company", "") or "").lower()
    title = (entry.get("title", "") or "").lower()
    
    # VISUAL_SIGNAL: +30 (MÁXIMA PRIORIDAD)
    visual_terms = ["portfolio", "visual output", "brand book", 
                   "store design", "visual standards", "merchandising guidelines",
                   "diseño visual", "experiencia visual", "brand environment"]
    if any(term in jd_text for term in visual_terms):
        score += 30
    
    # APPLY_EASE: +25 (asumimos 1 click si pasó URL_GATE)
    score += 25  # Todos los que pasan URL_GATE tienen CTA directo
    
    # RECRUITER_PRESENCE: +15 (si hay contacto)
    if entry.get("contact") or "contacto" in jd_text or "recruiter" in jd_text:
        score += 15
    
    # HIGH_IMPACT_RETAIL: +10
    high_impact = ["nike", "apple", "inditex", "zara", "h&m", "uniqlo", "adidas"]
    if any(brand in company for brand in high_impact):
        score += 10
    
    # INNOVATION_DNA: +10
    innovative = ["gentle monster", "grupo habita", "ben & frank", 
                 "sede cafe", "auditoire", "another", "magnus", "astound"]
    if any(brand in company for brand in innovative):
        score += 10
    
    # SCALE_FACTOR: +10 (asumir escala si es empresa grande)
    scale_companies = ["lvmh", "kering", "inditex", "nike", "apple", "adidas"]
    if any(brand in company for brand in scale_companies):
        score += 10
    
    # PIVOT_OPPORTUNITY: +10
    pivot_roles = ["experience", "creative", "brand", "environment", 
                   "activation", "design", "innovation"]
    if any(role in title for role in pivot_roles):
        score += 10
    
    # LUXURY_TAG: +5 (degradado)
    luxury = ["lvmh", "kering", "richemont", "chanel", "hermès", 
              "dior", "guerlain", "louis vuitton"]
    if any(brand in company for brand in luxury):
        score += 5
    
    return min(score, 100)

def get_match_level_v6(score):
    """Nuevos niveles basados en score 0-100"""
    if score >= 80:
        return "Muy Alto"
    elif score >= 60:
        return "Alto" 
    elif score >= 40:
        return "Medio"
    else:
        return "Bajo"

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
        print(f"⚠️  Error analyzing patterns: {e}")
        return None

def main():
    print("🚀 JHS Pipeline Runner v6.0 - OPTIMIZADO PARA VELOCIDAD")
    print("=" * 60)

    load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
    client = Client(auth=os.environ["NOTION_TOKEN"])
    ds_id = "4e542b37-6e52-4418-89b7-a0eeb3138307"

    # ==================== PASO 0: URL GATE PRE-SCORING ====================
    print("\n🔍 Paso 0: URL Gate (pre-scoring)...")
    items = client.data_sources.query(data_source_id=ds_id)["results"]
    url_gate_updates = 0
    url_gate_rejects = 0
    
    for item in items:
        props = item["properties"]
        url = txt(props.get("URL"))
        source_type = txt(props.get("Source_Type")) or "Vacante"
        status = txt(props.get("Status"))
        current_fetch = txt(props.get("Fetch"))
        
        # Solo aplicar gate a vacantes nuevas/activas
        if source_type != "Vacante" or not url:
            continue
            
        if status in ["Expirada", "Rechazado", "Archivar", "Contratado"]:
            continue
            
        # URL GATE NUEVO - MÁS ESTRICTO
        is_valid, reason = validate_url_pre_ingestion(url)
        
        if not is_valid:
            url_gate_rejects += 1
            empresa = txt(props.get("Marca")) or "Sin empresa"
            rol = txt(props.get("Rol")) or "Sin rol"
            print(f"❌ [{item['id'][:8]}] {empresa} - {rol[:30]}...")
            print(f"   URL Gate falló: {reason}")
            
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
                print(f"⚠️  Error actualizando {item['id'][:8]}: {e}")
        else:
            url_gate_updates += 1
    
    print(f"✅ URL Gate: {url_gate_updates} válidos, {url_gate_rejects} rechazados")
    
    # ==================== PASO 1: SCORING v6 ====================
    print("\n📊 Paso 1: Scoring determinístico v6...")
    items = client.data_sources.query(data_source_id=ds_id)["results"]
    scoring_updates = 0
    scoring_changes = []

    for item in items:
        props = item["properties"]
        rol = txt(props.get("Rol"))
        marca = txt(props.get("Marca"))
        jd = txt(props.get("JD"))
        contacto = txt(props.get("Contacto"))
        
        current_vm_scope = txt(props.get("VM_Scope"))
        current_score = props.get("Score", {}).get("number")
        current_role_class = txt(props.get("Role_Class"))
        current_match = txt(props.get("Match"))

        new_vm_scope = get_vm_scope(rol)
        new_role_class = get_role_class(rol)
        
        # Calcular score v6
        entry_data = {
            "title": rol,
            "company": marca,
            "jd": jd,
            "contact": contacto
        }
        new_score = calculate_score_v6(entry_data)
        new_match = get_match_level_v6(new_score)

        needs_update = False
        update_props = {}
        changes = []

        if current_vm_scope != new_vm_scope:
            update_props["VM_Scope"] = {"select": {"name": new_vm_scope}}
            changes.append(f"VM_Scope: {current_vm_scope}→{new_vm_scope}")
            needs_update = True

        if current_score != new_score:
            update_props["Score"] = {"number": new_score}
            changes.append(f"Score: {current_score}→{new_score}")
            needs_update = True

        if current_role_class != new_role_class:
            update_props["Role_Class"] = {"select": {"name": new_role_class}}
            changes.append(f"Role_Class: {current_role_class}→{new_role_class}")
            needs_update = True

        if current_match != new_match:
            update_props["Match"] = {"select": {"name": new_match}}
            changes.append(f"Match: {current_match}→{new_match}")
            needs_update = True

        if needs_update:
            try:
                client.pages.update(page_id=item["id"], properties=update_props)
                scoring_updates += 1
                if changes:
                    empresa = txt(props.get("Marca")) or "Sin empresa"
                    scoring_changes.append(f"[{item['id'][:8]}] {empresa}: {', '.join(changes)}")
            except Exception as e:
                print(f"❌ Error scoring {item['id'][:8]}: {e}")

    if scoring_changes:
        print(f"✅ Scoring v6: {len(scoring_changes)} cambios")
        for change in scoring_changes[:5]:
            print(f"  ↳ {change}")
        if len(scoring_changes) > 5:
            print(f"  ↳ ... y {len(scoring_changes)-5} cambios más")
    else:
        print(f"✅ Scoring: Sin cambios (todas las entradas ya actualizadas)")

    # ==================== PASO 2: URL RE-CHECK (solo para válidos) ====================
    print("\n🔗 Paso 2: URL re-check (solo válidos)...")
    items = client.data_sources.query(data_source_id=ds_id)["results"]
    url_updates = 0
    url_changes = []
    expired_suggestions = []

    for item in items:
        props = item["properties"]
        url = txt(props.get("URL"))
        current_fetch = txt(props.get("Fetch"))
        source_type = txt(props.get("Source_Type")) or "Vacante"
        last_seen = txt(props.get("Last_Seen_Active"))
        status = txt(props.get("Status"))

        if source_type != "Vacante" or not url:
            continue
            
        # Saltar si ya está marcado como expirado/rechazado
        if status in ["Expirada", "Rechazado", "Archivar"]:
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
                url_changes.append(f"[{item['id'][:8]}] {empresa}: {current_fetch}→{new_fetch}")

                if check_if_expired(url, last_seen, new_fetch) and status not in ["Expirada", "Rechazado"]:
                    expired_suggestions.append(f"[{item['id'][:8]}] {empresa}: Considerar cambiar Status a 'Expirada'")

            except Exception as e:
                print(f"❌ Error updating URL {item['id'][:8]}: {e}")

    if url_changes:
        print(f"✅ URL check: {len(url_changes)} cambios de estado")
        for change in url_changes:
            print(f"  ↳ {change}")
    else:
        print(f"✅ URL check: Sin cambios (todos los URLs mantienen su estado)")

    if expired_suggestions:
        print(f"\n⏰ Sugerencias de expiración:")
        for suggestion in expired_suggestions:
            print(f"  ↳ {suggestion}")

    # ==================== PASO 3: GATE LOGIC (con protección) ====================
    print("\n🚪 Paso 3: Gate logic y Next Actions...")
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
            changes.append(f"Gate: {current_gate}→{decision}")
        if current_action != next_action:
            changes.append(f"Action: {current_action}→{next_action}")

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
            print(f"❌ Error gate {item['id'][:8]}: {e}")

    if gate_changes:
        print(f"✅ Gate: {len(gate_changes)} cambios de decisión")
        for change in gate_changes[:5]:
            print(f"  ↳ {change}")
        if len(gate_changes) > 5:
            print(f"  ↳ ... y {len(gate_changes)-5} cambios más")
    else:
        print(f"✅ Gate: Sin cambios (todas las decisiones ya correctas)")

    print(f"🛡️  Acciones protegidas: {protected_count}")

    # ==================== PASO 4: ANÁLISIS DE PATRONES ====================
    print("\n📈 Paso 4: Análisis de patrones...")
    patterns = analyze_outcome_patterns()
    if patterns:
        rejection_patterns = patterns["rejection_patterns"]
        score_effectiveness = patterns["score_effectiveness"]
        print("✅ Análisis completado")
        if score_effectiveness:
            print("  📊 Efectividad por Score:")
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
            print("  ⚠️  Empresas con alta tasa de rechazo:")
            for company, rate, total in sorted(high_rejection_companies, key=lambda x: x[1], reverse=True)[:3]:
                print(f"    {company}: {rate:.0f}% rechazo ({total} aplicaciones)")

    print("\n" + "=" * 60)
    print("🎯 RESUMEN FINAL v6.0:")
    print(f"  🔍 URL Gate: {url_gate_rejects} links muertos eliminados")
    print(f"  ✅ CREATE (Pipeline Activo): {create_count}")
    print(f"  🚀 APPLIED (En proceso): {applied_count}")
    print(f"  ❌ BLOCKED: {blocked_count}")
    print(f"  🛡️  PROTEGIDAS: {protected_count}")
    print(f"  📊 Total procesado: {len(items)}")

    if scoring_changes or url_changes or gate_changes:
        print(f"\n📈 CAMBIOS REALIZADOS:")
        print(f"  📊 Scoring v6: {len(scoring_changes)} cambios")
        print(f"  🔗 URLs: {len(url_changes)} cambios")
        print(f"  🚪 Gates: {len(gate_changes)} cambios")
    else:
        print(f"\n✅ ESTADO ESTABLE: Sin cambios necesarios")

    print("\n💡 PRÓXIMOS PASOS (v6.0):")
    print("  1. Abre Notion → Filtra por 'Score ≥ 60'")
    print("  2. Prioriza roles con 'Visual Signal' en JD")
    print("  3. Aplica máximo 5/semana (calidad > cantidad)")
    print("  4. Links muertos se marcan automáticamente como 'Expirada'")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Pipeline cancelado por usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error en pipeline: {e}")
        sys.exit(1)