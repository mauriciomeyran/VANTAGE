import os
from dotenv import load_dotenv
from notion_client import Client

def txt(prop):
    if not prop: return ""
    t = prop.get("type")
    if t == "rich_text" and prop.get("rich_text"): 
        return prop["rich_text"][0]["plain_text"]
    if t == "select" and prop.get("select"): 
        return prop["select"]["name"]
    if t == "title" and prop.get("title"): 
        return prop["title"][0]["plain_text"]
    return ""

def gate(fetch, vm_scope, role_class):
    if fetch == "Accesible" and (vm_scope == "Alto" or role_class == "Pivote"):
        return "CREATE"
    return "BLOCKED"

load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
client = Client(auth=os.environ["NOTION_TOKEN"])
ds_id = "4e542b37-6e52-4418-89b7-a0eeb3138307"

items = client.data_sources.query(data_source_id=ds_id)["results"]

print("DEBUG - Valores reales en Notion:")
print("=" * 60)

for i, item in enumerate(items[:5]):  # Solo primeras 5
    props = item["properties"]
    
    fetch = txt(props.get("Fetch"))
    vm_scope = txt(props.get("VM_Scope"))
    role_class = txt(props.get("Role_Class"))
    rol = txt(props.get("Rol"))
    
    decision = gate(fetch, vm_scope, role_class)
    
    print(f"{i+1}. {rol[:40]}...")
    print(f"   Fetch: '{fetch}'")
    print(f"   VM_Scope: '{vm_scope}'")
    print(f"   Role_Class: '{role_class}'")
    print(f"   Gate Decision: {decision}")
    print()
