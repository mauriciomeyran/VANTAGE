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

print("🔧 REPARANDO DIOR Y SWAROVSKI")
print("=" * 60)

fixed = 0

for item in items:
    props = item["properties"]
    rol = txt(props.get("Rol"))
    marca = txt(props.get("Marca"))
    status = txt(props.get("Status"))
    jd = txt(props.get("Texto JD")) or txt(props.get("JD")) or ""
    url = txt(props.get("URL"))
    
    # Condición más amplia
    should_fix = False
    reason = ""
    
    # Dior - por marca o URL
    if ("dior" in marca.lower() or "dior" in rol.lower() or 
        (url and "dior.com" in url.lower())):
        if status == "Expirada" and len(jd) > 100:
            should_fix = True
            reason = "Dior con JD completo"
    
    # Swarovski - por marca
    elif "swarovski" in marca.lower():
        if status == "Expirada" and len(jd) > 100:
            should_fix = True
            reason = "Swarovski con JD completo"
    
    if should_fix:
        print(f"\n🔧 REPARANDO: {rol} @ {marca}")
        print(f"   Razón: {reason}")
        print(f"   Status actual: {status}")
        print(f"   JD length: {len(jd)} chars")
        
        try:
            client.pages.update(
                page_id=item["id"],
                properties={
                    "Status": {"select": {"name": "Nueva"}},
                    "Gate_Decision": {"select": {"name": "CREATE"}},
                    "Next_Action": {"select": {"name": "Revisar JD"}}
                }
            )
            print("   ✅ ACTUALIZADO: Status→Nueva, Gate→CREATE")
            fixed += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print(f"✅ REPARADAS: {fixed} vacantes")
print("\n💡 Ahora ejecuta el pipeline para recalcular scoring:")
print("   python3 ./scripts/run_pipeline.py")