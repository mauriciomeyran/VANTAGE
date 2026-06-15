#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from notion_client import Client

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
    return ""

load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
client = Client(auth=os.environ["NOTION_TOKEN"])
ds_id = "4e542b37-6e52-4418-89b7-a0eeb3138307"

items = client.data_sources.query(data_source_id=ds_id)["results"]

print("🔧 REPARANDO VACANTES BLOQUEADAS")
print("=" * 60)

nike_fixed = 0
workable_fixed = 0

for item in items:
    props = item["properties"]
    url = txt(props.get("URL"))
    fetch = txt(props.get("Fetch"))
    status = txt(props.get("Status"))
    rol = txt(props.get("Rol"))
    marca = txt(props.get("Marca"))
    
    if not url:
        continue
    
    # Reparar Nike
    if "nike.com" in url.lower() and (fetch == "Bloqueado" or status == "Expirada"):
        print(f"\n🔧 REPARANDO NIKE: {rol}")
        print(f"   URL: {url}")
        
        try:
            client.pages.update(
                page_id=item["id"],
                properties={
                    "Fetch": {"select": {"name": "Accesible"}},
                    "Status": {"select": {"name": "Nueva"}},
                    "Gate_Decision": {"select": {"name": "CREATE"}},
                    "Next_Action": {"select": {"name": "Re-check"}}
                }
            )
            print("   ✅ ACTUALIZADO: Fetch→Accesible, Status→Nueva")
            nike_fixed += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Reparar Workable
    elif "workable.com" in url.lower() and (fetch == "Bloqueado" or status == "Expirada"):
        print(f"\n🔧 REPARANDO WORKABLE: {rol}")
        print(f"   URL: {url}")
        
        try:
            client.pages.update(
                page_id=item["id"],
                properties={
                    "Fetch": {"select": {"name": "Accesible"}},
                    "Status": {"select": {"name": "Nueva"}},
                    "Gate_Decision": {"select": {"name": "CREATE"}},
                    "Next_Action": {"select": {"name": "Re-check"}}
                }
            )
            print("   ✅ ACTUALIZADO: Fetch→Accesible, Status→Nueva")
            workable_fixed += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print(f"📊 RESULTADOS:")
print(f"   Nike reparadas: {nike_fixed}")
print(f"   Workable reparadas: {workable_fixed}")
print(f"   Total: {nike_fixed + workable_fixed}")
print("\n💡 Ahora ejecuta el pipeline normal:")
print("   python3 ./scripts/run_pipeline.py")