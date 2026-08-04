import os
from dotenv import load_dotenv
from notion_utils import Client
from difflib import SequenceMatcher
from collections import defaultdict
from datetime import datetime

def get_plain_text(prop):
    """Extrae texto plano o valor de una propiedad de Notion."""
    if not prop: return ""
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
    Protección de estados terminales - respeta gate_logic.py
    
    Args:
        entry: dict con al menos "Status" y "Next_Action"
    
    Returns:
        bool - True si el registro NO debe ser modificado
    """
    status = entry.get("Status") or ""
    if status in ["Postulado", "Rechazado"]:
        return True
    
    current_action = entry.get("Next_Action") or ""
    if current_action in ["Archivar", "Expirada"]:
        return True
    
    return False


def write_dedup_flag(client, page_id, properties, clear=False):
    """
    Escribe o limpia Dedup_Flag en el registro especificado
    
    Args:
        client: Notion client
        page_id: ID de la página a actualizar
        properties: propiedades actuales de la página
        clear: si True, limpia el campo; si False, asigna "Posible duplicado"
    """
    # Extraer valor actual de Dedup_Flag
    dedup_field = properties.get("Dedup_Flag", {})
    current_dedup_flag = ""
    if dedup_field.get("type") == "select":
        current_dedup_flag = (dedup_field.get("select") or {}).get("name", "")
    
    if clear:
        # Limpiar campo - enviar null para select
        if current_dedup_flag:  # Solo si tiene valor
            try:
                client.pages.update(
                    page_id=page_id,
                    properties={"Dedup_Flag": {"select": None}}
                )
                print(f"  🧹 Dedup_Flag limpiado ({page_id[:8]}...)")
                return True
            except Exception as exc:
                print(f"  ⚠️  Error limpiando Dedup_Flag para {page_id[:8]}: {exc}")
                return False
    else:
        # Asignar "Posible duplicado"
        if current_dedup_flag != "Posible duplicado":
            try:
                client.pages.update(
                    page_id=page_id,
                    properties={"Dedup_Flag": {"select": {"name": "Posible duplicado"}}}
                )
                print(f"  🏷️  Dedup_Flag asignado: 'Posible duplicado' ({page_id[:8]}...)")
                return True
            except Exception as exc:
                print(f"  ⚠️  Error asignando Dedup_Flag para {page_id[:8]}: {exc}")
                return False
    return False

def are_duplicates(job1, job2, company_threshold=0.85, role_threshold=0.7):
    company1 = job1["Marca"].lower().replace(" group", "").replace(" ag", "").strip()
    company2 = job2["Marca"].lower().replace(" group", "").replace(" ag", "").strip()

    if similarity(company1, company2) < company_threshold:
        return False

    role1_kw = {kw for kw in {"visual", "merchandising", "coordinator", "manager"} if kw in job1["Rol"].lower()}
    role2_kw = {kw for kw in {"visual", "merchandising", "coordinator", "manager"} if kw in job2["Rol"].lower()}

    if not role1_kw or not role2_kw: return False

    intersection = len(role1_kw.intersection(role2_kw))
    union = len(role1_kw.union(role2_kw))
    role_sim = intersection / union if union > 0 else 0

    # ANTI-FALSO POSITIVO: Excluir pares donde uno tiene "electrónica" y el otro no
    # Esto evita agrupar roles de retail general con roles especializados en electrónica
    has_electronics_1 = "electrónica" in job1["Rol"].lower() or "electronic" in job1["Rol"].lower()
    has_electronics_2 = "electrónica" in job2["Rol"].lower() or "electronic" in job2["Rol"].lower()
    if has_electronics_1 != has_electronics_2:
        return False

    return role_sim >= role_threshold

if __name__ == "__main__":
    import sys
    
    # Verificar flag --clear para limpiar Dedup_Flag específico
    clear_mode = "--clear" in sys.argv
    if clear_mode and len(sys.argv) > 2:
        # Modo específico: --clear <page_id>
        target_page_id = sys.argv[2]
        load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
        client = Client(auth=os.environ["NOTION_TOKEN"])
        
        try:
            # Obtener la página para extraer sus propiedades
            page = client.pages.retrieve(page_id=target_page_id)
            props = page.get("properties", {})
            
            if write_dedup_flag(client, target_page_id, props, clear=True):
                print(f"✅ Dedup_Flag limpiado para {target_page_id[:8]}")
            else:
                print(f"ℹ️  No se necesitó limpiar Dedup_Flag para {target_page_id[:8]}")
        except Exception as e:
            print(f"❌ Error limpiando Dedup_Flag: {e}")
        sys.exit(0)
    
    load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
    client = Client(auth=os.environ["NOTION_TOKEN"])
    data_source_id = "442938be-fc42-828f-b72e-076818d65a5b"  # VANTAGE TRACKER (COL)

    print("Obteniendo todas las oportunidades...")
    all_results = client.data_sources.query(data_source_id=data_source_id)["results"]
    print(f"✅ {len(all_results)} entradas obtenidas")

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
        
        # Contador de cambios
        dedup_flags_assigned = 0
        
        for i, group in enumerate(duplicate_groups):
            print(f"\n--- Grupo {i+1} ({len(group)} entradas) ---")
            
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
                    print(f"  ⛔ [{job['id'][:8]}] OMITIDO (estado terminal): {job['Marca']} | {job['Rol']} | Status: {job['Status']} | Next_Action: {job['Next_Action']}")
            
            if not eligible_jobs:
                print(f"  ℹ️  Todos los registros del grupo están en estado terminal - sin cambios")
                continue
            
            # MARCAR TODOS los registros elegibles del grupo (no solo uno)
            print(f"  - REGISTROS A MARCAR: {len(eligible_jobs)} de {len(group)}")
            
            for job in eligible_jobs:
                print(f"  -> [{job['id'][:8]}] {job['Marca']} | {job['Rol']} | Score: {job['Score']}")
                
                # Escribir Dedup_Flag en cada registro elegible
                if write_dedup_flag(client, job["id"], job["properties"]):
                    dedup_flags_assigned += 1
            
            # Mostrar todos los registros del grupo para contexto
            for job in group:
                url_snippet = (job['URL'] or "N/A")[:60]
                is_eligible = job in eligible_jobs
                marker = "🏷️ MARCADO" if is_eligible else ""
                print(f"  - [{job['id'][:8]}] {job['Marca']} | {job['Rol']} | Status: {job['Status']} | Score: {job['Score']} | URL: {url_snippet}... {marker}")
        
        print(f"\n📊 RESUMEN: {dedup_flags_assigned} Dedup_Flag(s) asignados")