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

print("🔧 CORRIGIENDO FETCH DE ACTIVATE TALENT")
print("=" * 60)

fixed = 0

for item in items:
    props = item["properties"]
    url = txt(props.get("URL"))
    fetch = txt(props.get("Fetch"))
    rol = txt(props.get("Rol"))
    
    if not url:
        continue
    
    # Solo Activate Talent con Fetch Bloqueado
    if "workable.com" in url.lower() and fetch == "Bloqueado":
        print(f"\n🔧 CORRIGIENDO: {rol}")
        print(f"   URL: {url}")
        print(f"   Fetch actual: {fetch}")
        
        try:
            client.pages.update(
                page_id=item["id"],
                properties={
                    "Fetch": {"select": {"name": "Accesible"}}
                }
            )
            print("   ✅ ACTUALIZADO: Fetch→Accesible")
            fixed += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print(f"✅ CORREGIDAS: {fixed} vacantes")
print("\n💡 Ahora ejecuta el pipeline para recalcular gate:")
print("   python3 ./scripts/run_pipeline.py")
