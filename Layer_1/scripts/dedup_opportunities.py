import os
from dotenv import load_dotenv
from notion_utils import Client
from difflib import SequenceMatcher
from collections import defaultdict

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

if __name__ == "__main__":
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
        for i, group in enumerate(duplicate_groups):
            print(f"\n--- Grupo {i+1} ({len(group)} entradas) ---")
            for job in group:
                url_snippet = (job['URL'] or "N/A")[:60]
                print(f"  - [{job['id'][:8]}] {job['Marca']} | {job['Rol']} | Status: {job['Status']} | URL: {url_snippet}...")