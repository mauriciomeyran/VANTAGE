import os
from dotenv import load_dotenv
from notion_client import Client
from difflib import SequenceMatcher

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

def get_status_priority(status):
    """Asigna prioridad a status (mayor = mejor)"""
    priority = {
        "En proceso": 8, "Negociando": 7, "Postulado": 6, "Target": 5,
        "Exploratorio": 4, "Sin respuesta": 3, "Expirada": 2, "Rechazado": 1, "Retirado": 1
    }
    return priority.get(status, 0)

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

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

    return role_sim >= role_threshold

def choose_primary(jobs):
    """Elige cuál entrada mantener basado en prioridad"""
    # Ordenar por: 1) Status priority, 2) URL válida, 3) JD válido
    def score(job):
        status_score = get_status_priority(job["Status"])
        url_score = 1 if job["URL"] and not job["URL"].startswith("N/A") else 0
        jd_score = 1 if job.get("JD") and job["JD"].strip() else 0
        return (status_score, url_score, jd_score)
    
    return max(jobs, key=score)

def merge_notes(primary_notes, secondary_notes):
    """Combina notas de dos entradas"""
    if not secondary_notes or not secondary_notes.strip():
        return primary_notes or ""
    
    if not primary_notes or not primary_notes.strip():
        return secondary_notes
    
    separator = "\n\n--- CONSOLIDADO DESDE DUPLICADO ---\n"
    return (primary_notes + separator + secondary_notes).strip()

if __name__ == "__main__":
    load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
    client = Client(auth=os.environ["NOTION_TOKEN"])
    ds_id = "4e542b37-6e52-4418-89b7-a0eeb3138307"

    print("Obteniendo todas las oportunidades...")
    all_results = client.data_sources.query(data_source_id=ds_id)["results"]
    print(f"✅ {len(all_results)} entradas obtenidas")

    # Convertir a formato procesable
    jobs = []
    for item in all_results:
        props = item["properties"]
        jobs.append({
            "id": item["id"],
            "raw_item": item,
            "Marca": get_plain_text(props.get("Marca")),
            "Rol": get_plain_text(props.get("Rol")),
            "Status": get_plain_text(props.get("Status")),
            "URL": get_plain_text(props.get("URL")),
            "JD": get_plain_text(props.get("JD")),
            "Notas": get_plain_text(props.get("Notas")),
        })

    print("\n🔎 Detectando duplicados...")
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
        print("No se encontraron duplicados.")
        exit()

    print(f"✅ {len(duplicate_groups)} grupos de duplicados encontrados")
    
    # Preguntar confirmación antes de consolidar
    print("\n🚨 CONSOLIDACIÓN DESTRUCTIVA")
    print("Esto eliminará entradas duplicadas y no se puede deshacer.")
    confirm = input("¿Continuar? (y/N): ").lower().strip()
    
    if confirm != 'y':
        print("❌ Operación cancelada.")
        exit()

    print("\n🔄 Consolidando duplicados...")
    
    for i, group in enumerate(duplicate_groups):
        print(f"\n--- Grupo {i+1} ---")
        
        # Elegir entrada principal
        primary = choose_primary(group)
        secondaries = [job for job in group if job["id"] != primary["id"]]
        
        print(f"✅ MANTENER: [{primary['id'][:8]}] {primary['Marca']} | {primary['Rol']} | {primary['Status']}")
        
        # Consolidar información
        merged_notes = primary["Notas"]
        for secondary in secondaries:
            print(f"🗑️  ELIMINAR: [{secondary['id'][:8]}] {secondary['Marca']} | {secondary['Rol']} | {secondary['Status']}")
            merged_notes = merge_notes(merged_notes, secondary["Notas"])
        
        # Actualizar entrada principal con notas consolidadas
        if merged_notes != primary["Notas"]:
            print(f"   📝 Actualizando notas consolidadas...")
            try:
                client.pages.update(
                    page_id=primary["id"],
                    properties={
                        "Notas": {
                            "rich_text": [{"text": {"content": merged_notes}}]
                        }
                    }
                )
            except Exception as e:
                print(f"   ❌ Error actualizando notas: {e}")
        
        # Eliminar entradas secundarias
        for secondary in secondaries:
            try:
                client.pages.update(
                    page_id=secondary["id"],
                    in_trash=True
                )
                print(f"   🗑️  Eliminado: {secondary['id'][:8]}")
            except Exception as e:
                print(f"   ❌ Error eliminando {secondary['id'][:8]}: {e}")

    print(f"\n✅ Consolidación completada.")