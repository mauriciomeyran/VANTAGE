import json
import os
from pathlib import Path as _Path
import sys as _sys
from dotenv import load_dotenv
from notion_utils import Client
from difflib import SequenceMatcher
from collections import defaultdict
from datetime import datetime

# Fase 3: terminalidad delegada a vantage_status (R-05 ampliado).
# dedup_opportunities.py ya delegaba PROTECTED_STATUSES a tracker_flow;
# ahora delega is_terminal_status() a vantage_status (única fuente).
_L1_SCRIPTS_DIR = _Path(__file__).resolve().parent
if str(_L1_SCRIPTS_DIR) not in _sys.path:
    _sys.path.insert(0, str(_L1_SCRIPTS_DIR))
from vantage_status import is_terminal_status  # noqa: E402
from layer_1_orchestrator import class_b_guard  # noqa: E402
from tracker_flow import Actor  # noqa: E402

# Diccionario global para métricas de filtros anti-falso-positivo
filter_metrics = {}

# Sistema genérico de reglas anti-falso-positivo
ANTI_FALSE_POSITIVE_RULES = [
    {
        "name": "electrónica",
        "check": lambda role: "electrónica" in role.lower() or "electronic" in role.lower(),
        "description": "Evita agrupar roles de retail general con roles especializados en electrónica"
    },
    # Se pueden agregar más reglas fácilmente en el futuro
]


def should_apply_anti_false_positive(job1, job2):
    """
    Verifica si alguna regla anti-falso-positivo aplica al par de jobs.

    Args:
        job1: dict con campos "Rol" y otros
        job2: dict con campos "Rol" y otros

    Returns:
        str or None - Nombre de la regla que aplicó, o None si no aplicó ninguna
    """
    for rule in ANTI_FALSE_POSITIVE_RULES:
        has_keyword_1 = rule["check"](job1["Rol"])
        has_keyword_2 = rule["check"](job2["Rol"])
        if has_keyword_1 != has_keyword_2:
            return rule["name"]

    return None


def get_plain_text(prop):
    """Extrae texto plano o valor de una propiedad de Notion."""
    if not prop:
        return ""
    prop_type = prop.get('type')

    if prop_type == 'url':
        return prop.get('url', "") or ""
    if prop_type == 'rich_text' and prop.get('rich_text'):
        return prop['rich_text'][0]['plain_text'] if prop['rich_text'] else ""
    if prop_type == 'title' and prop.get('title'):
        return prop['title'][0]['plain_text'] if prop['title'] else ""
    if prop_type == 'select' and prop.get('select'):
        return prop['select']['name']
    return ""


def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def is_terminal_state(entry):
    """
    Protección de estados terminales - única fuente de verdad: vantage_status.

    Fase 3: delega a vantage_status.is_terminal_status().
    El check de Next_Action="Expirada" fue eliminado (D1: 0 ocurrencias en 826 filas,
    código muerto confirmado — la protección real existe vía Status="Expirada" en
    vantage_status.TERMINAL_STATUSES_CANONICO + LEGACY_STATUS_MAP).

    Args:
        entry: dict con al menos "Status" y "Next_Action"

    Returns:
        bool - True si el registro NO debe ser modificado
    """
    status = entry.get("Status") or ""
    if is_terminal_status(status):
        return True

    return False


def write_dedup_flag(client, page_id, properties, clear=False, dry_run=False):
    """
    Escribe o limpia Dedup_Flag en el registro especificado

    Args:
        client: Notion client
        page_id: ID de la página a actualizar
        properties: propiedades actuales de la página
        clear: si True, limpia el campo; si False, asigna "Posible duplicado"
        dry_run: si True, simula la escritura sin ejecutarla
    """
    # Extraer valor actual de Dedup_Flag (checkbox)
    dedup_field = properties.get("Dedup_Flag", {})
    current_dedup_flag = False
    if dedup_field.get("type") == "checkbox":
        current_dedup_flag = bool(dedup_field.get("checkbox"))

    if clear:
        # Limpiar campo - checkbox a False
        if current_dedup_flag:  # Solo si estaba marcado
            if dry_run:
                print(f"  [DRY RUN] Limpiaría Dedup_Flag ({page_id[:8]}...)")
                return True
            try:
                payload = class_b_guard({"Dedup_Flag": {"checkbox": False}}, Actor.DEDUP)
                client.pages.update(
                    page_id=page_id,
                    properties=payload
                )
                print(f"  🧹 Dedup_Flag limpiado ({page_id[:8]}...)")
                return True
            except Exception as exc:
                print(f"  ⚠️  Error limpiando Dedup_Flag para {page_id[:8]}: {exc}")
                return False
    else:
        # Asignar True (posible duplicado)
        if not current_dedup_flag:
            if dry_run:
                print(f"  [DRY RUN] Asignaría Dedup_Flag=True ({page_id[:8]}...)")
                return True  # En DRY RUN asumimos que se asignaría
            try:
                payload = class_b_guard({"Dedup_Flag": {"checkbox": True}}, Actor.DEDUP)
                client.pages.update(
                    page_id=page_id,
                    properties=payload
                )
                print(f"  🏷️  Dedup_Flag asignado: True ({page_id[:8]}...)")
                return True
            except Exception as exc:
                print(f"  ⚠️  Error asignando Dedup_Flag para {page_id[:8]}: {exc}")
                return False
        else:
            # Ya tiene el valor correcto, no se necesita hacer nada
            if dry_run:
                print(f"  [DRY RUN] Ya tiene Dedup_Flag=True ({page_id[:8]}...)")
            return False  # No contar como asignación nueva
    return False


def are_duplicates(job1, job2, company_threshold=0.85, role_threshold=0.7):
    company1 = job1["Marca"].lower().replace(" group", "").replace(" ag", "").strip()
    company2 = job2["Marca"].lower().replace(" group", "").replace(" ag", "").strip()

    if similarity(company1, company2) < company_threshold:
        return False

    role1_kw = {kw for kw in {"visual", "merchandising", "coordinator", "manager"} if kw in job1["Rol"].lower()}
    role2_kw = {kw for kw in {"visual", "merchandising", "coordinator", "manager"} if kw in job2["Rol"].lower()}

    if not role1_kw or not role2_kw:
        return False

    intersection = len(role1_kw.intersection(role2_kw))
    union = len(role1_kw.union(role2_kw))
    role_sim = intersection / union if union > 0 else 0

    # ANTI-FALSO POSITIVO: Aplicar sistema genérico de reglas
    filter_applied = should_apply_anti_false_positive(job1, job2)
    if filter_applied:
        filter_metrics[filter_applied] = filter_metrics.get(filter_applied, 0) + 1
        return False

    return role_sim >= role_threshold


if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Auditoría de duplicados en VANTAGE Tracker")
    parser.add_argument("--clear", type=str, metavar="PAGE_ID",
                       help="Limpiar Dedup_Flag de una página específica")
    parser.add_argument("--window-days", type=int, default=60,
                       help="Ventana de días para búsqueda de duplicados (default: 60)")
    parser.add_argument("--dry-run", action="store_true",
                       help="[COMPATIBILIDAD] Simula ejecución sin escribir Dedup_Flag. "
                            "Ya no es necesario: es el comportamiento por defecto.")
    parser.add_argument("--apply", action="store_true",
                       help="R-05 fix: requerido explícitamente para escribir Dedup_Flag en Notion. "
                            "Sin este flag, el script siempre corre en modo simulación.")

    args = parser.parse_args()

    # R-05 fix: invertir el default. Antes --dry-run era opt-in y el script
    # escribía por defecto; ahora se requiere --apply explícito para escribir.
    args.dry_run = not args.apply

    # Verificar flag --clear para limpiar Dedup_Flag específico
    if args.clear:
        target_page_id = args.clear
        load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
        client = Client(auth=os.environ["NOTION_TOKEN"])

        try:
            # Obtener la página para extraer sus propiedades
            page = client.pages.retrieve(page_id=target_page_id)
            props = page.get("properties", {})

            if write_dedup_flag(client, target_page_id, props, clear=True, dry_run=args.dry_run):
                print(f"✅ Dedup_Flag limpiado para {target_page_id[:8]}")
            else:
                print(f"ℹ️  No se necesitó limpiar Dedup_Flag para {target_page_id[:8]}")
        except Exception as e:
            print(f"❌ Error limpiando Dedup_Flag: {e}")
            sys.exit(1)
        sys.exit(0)

    if args.dry_run:
        print("\n" + "="*60)
        print("DRY RUN MODE — No se escribirán cambios a Notion")
        print("Pasa --apply para escribir Dedup_Flag de verdad.")
        print("="*60 + "\n")
    else:
        print("\n" + "="*60)
        print("⚠️  MODO ESCRITURA (--apply) — se escribirá Dedup_Flag en Notion")
        print("="*60 + "\n")

    load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
    client = Client(auth=os.environ["NOTION_TOKEN"])
    data_source_id = "442938be-fc42-828f-b72e-076818d65a5b"  # VANTAGE TRACKER (COL)
    archive_data_source_id = os.environ.get("NOTION_ARCHIVE_DATA_SOURCE_ID", "674696fd-94b6-464a-ac1f-64b0cc917e15")  # ARCHIVO TRACKER (default)
    window_days = args.window_days

    # Configurar etiqueta para logging (el filtro temporal se aplica en memoria por ahora)
    if window_days >= 28:
        time_label = "mes" if window_days < 60 else "2 meses"
    else:
        time_label = "semana"

    print(f"Obteniendo oportunidades (ventana objetivo: {window_days} días, {time_label})...")

    # Obtener resultados del Tracker activo
    active_results = client.data_sources.query(data_source_id=data_source_id)["results"]

    # Fix (operador, 2026-09-17): el Archive Tracker deja de consultarse.
    # Los registros ya archivados no requieren ninguna acción — listarlos
    # como contexto no ayudaba a la toma de decisiones y dominaba el output
    # (40/45 líneas "OMITIDO" en la corrida que motivó este fix).
    archived_results = []
    all_results = active_results
    print(f"✅ Total de entradas: {len(all_results)} (solo Tracker activo)")

    # Aplicar filtro temporal en memoria basado en created_time
    from datetime import datetime, timedelta
    cutoff_date = datetime.now() - timedelta(days=window_days)

    filtered_results = []
    for item in all_results:
        created_time_str = item.get("created_time", "")
        if created_time_str:
            try:
                # Notion devuelve fechas en formato ISO 8601
                created_date = datetime.fromisoformat(created_time_str.replace("Z", "+00:00"))
                if created_date >= cutoff_date:
                    filtered_results.append(item)
            except (ValueError, TypeError):
                # Si no podemos parsear la fecha, incluir el registro por seguridad
                filtered_results.append(item)

    all_results = filtered_results
    print(f"✅ {len(all_results)} entradas obtenidas (ventana aplicada: {time_label})")

    # Reiniciar contadores de métricas para esta ejecución
    filter_metrics.clear()

    # Guardar contadores para métricas
    metrics_context = {
        "active_count": len(active_results),
        "archived_count": len(archived_results)
    }

    jobs = []
    for item in all_results:
        props = item["properties"]
        jobs.append({
            "id": item["id"],
            "Marca": get_plain_text(props.get("Marca")),
            "Rol": get_plain_text(props.get("Rol")),
            "Status": get_plain_text(props.get("Status")),
            "URL": get_plain_text(props.get("URL")),
            "Score": get_plain_text(props.get("Score")),
            "Gate_Decision": get_plain_text(props.get("Gate_Decision")),
            "Next_Action": get_plain_text(props.get("Next_Action")),
            "created_time": item.get("created_time", ""),
            "properties": props,  # Guardar props para escritura
            "is_archived": False,  # ya no aplica: universo es solo Tracker activo
        })

    print("\n🔎 Buscando duplicados (Empresa + Rol similar)...")
    processed_indices = set()
    duplicate_groups = []
    for i in range(len(jobs)):
        if i in processed_indices:
            continue

        current_group = [jobs[i]]
        processed_indices.add(i)

        for j in range(i + 1, len(jobs)):
            if j in processed_indices:
                continue

            if are_duplicates(jobs[i], jobs[j]):
                current_group.append(jobs[j])
                processed_indices.add(j)

        if len(current_group) > 1:
            duplicate_groups.append(current_group)

    if not duplicate_groups:
        print("\nNo se encontraron duplicados.")
    else:
        print(f"\n✅ Grupos de duplicados encontrados: {len(duplicate_groups)}")

        # Contadores de métricas
        dedup_flags_assigned = 0  # Cambios reales escritos
        dedup_flags_skipped = 0    # Registros que ya tenían el valor
        terminal_state_omitted = 0

        for i, group in enumerate(duplicate_groups):
            print(f"\n--- grupo {i+1} ({len(group)} entradas) ---")

            # Filtrar registros que NO están en estado terminal
            eligible_jobs = []
            for job in group:
                entry = {
                    "Status": job["Status"],
                    "Next_Action": job["Next_Action"],
                    "Gate_Decision": job["Gate_Decision"],
                }
                if not is_terminal_state(entry):
                    eligible_jobs.append(job)
                else:
                    terminal_state_omitted += 1
                    print(f"  ⛔ [{job['id'][:8]}] OMITIDO (estado terminal): {job['Marca']} | {job['Rol']} | Status: {job['Status']} | Next_Action: {job['Next_Action']}")

            if not eligible_jobs:
                print(f"  ℹ️  Todos los registros del grupo están en estado terminal - sin cambios")
                continue

            # MARCAR TODOS los registros elegibles del grupo (no solo uno)
            print(f"  - REGISTROS A MARCAR: {len(eligible_jobs)} de {len(group)}")

            for job in eligible_jobs:
                print(f"  -> [{job['id'][:8]}] {job['Marca']} | {job['Rol']} | Score: {job['Score']}")

                # Escribir Dedup_Flag en cada registro elegible
                result = write_dedup_flag(client, job["id"], job["properties"], dry_run=args.dry_run)
                if result:
                    dedup_flags_assigned += 1

            # Mostrar todos los registros del grupo para contexto
            for job in group:
                url_snippet = (job['URL'] or "N/A")[:60]
                is_eligible = job in eligible_jobs
                marker = "🏷️ MARCADO" if is_eligible else ""
                print(f"  - [{job['id'][:8]}] {job['Marca']} | {job['Rol']} | Status: {job['Status']} | Score: {job['Score']} | URL: {url_snippet}... {marker}")
        print(f"\n📊 RESUMEN: {dedup_flags_assigned} Dedup_Flag(s) asignados")
        print(f"📊 MÉTRICAS: {terminal_state_omitted} omitidos por estado terminal")

        # Mostrar resumen de filtros anti-falso-positivo
        if filter_metrics:
            print(f"📊 FILTROS ANTI-FALSO-POSITIVO:")
            for filter_name, count in filter_metrics.items():
                print(f"   - {filter_name}: {count} aplicaciones")

        # Exportar métricas a JSON
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "window_days": window_days,
            "window_label": time_label,
            "total_records_analyzed": len(jobs),
            "active_records": metrics_context["active_count"],
            "archived_records": metrics_context["archived_count"],
            "duplicate_groups_found": len(duplicate_groups),
            "dedup_flags_assigned": dedup_flags_assigned,
            "terminal_state_omitted": terminal_state_omitted,
            "filter_metrics": filter_metrics,
            "dry_run": args.dry_run
        }

        try:
            with open("dedup_metrics.json", "w") as f:
                json.dump(metrics, f, indent=2)
            print(f"📊 Métricas guardadas en dedup_metrics.json")
        except Exception as e:
            print(f"⚠️  Error guardando métricas: {e}")
