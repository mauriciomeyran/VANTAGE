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

print("🔧 REPARANDO ESTADOS INCORRECTOS")
print("=" * 60)

repaired = 0

for item in items:
    props = item["properties"]
    url = txt(props.get("URL"))
    fetch = txt(props.get("Fetch"))
    status = txt(props.get("Status"))
    gate_decision = txt(props.get("Gate_Decision"))
    next_action = txt(props.get("Next_Action"))
    rol = txt(props.get("Rol"))
    marca = txt(props.get("Marca"))
    jd = txt(props.get("Texto JD")) or txt(props.get("JD")) or ""
    
    # 1. Vacantes con JD pero Status incorrecto
    if len(jd) > 100 and status == "Expirada":
        print(f"\n🔧 REPARANDO STATUS: {rol} @ {marca}")
        print(f"   Status actual: {status} (tiene JD de {len(jd)} chars)")
        
        try:
            client.pages.update(
                page_id=item["id"],
                properties={
                    "Status": {"select": {"name": "Nueva"}}
                }
            )
            print("   ✅ ACTUALIZADO: Status→Nueva")
            repaired += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # 2. Vacantes APPLIED pero con Gate_Decision incorrecto
    elif status in ["Postulado", "En proceso", "Negociando"] and gate_decision != "APPLIED":
        print(f"\n🔧 REPARANDO GATE: {rol} @ {marca}")
        print(f"   Status: {status}, Gate actual: {gate_decision}")
        
        try:
            client.pages.update(
                page_id=item["id"],
                properties={
                    "Gate_Decision": {"select": {"name": "APPLIED"}}
                }
            )
            print("   ✅ ACTUALIZADO: Gate_Decision→APPLIED")
            repaired += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # 3. Vacantes con URL accesible pero Fetch bloqueado
    elif fetch == "Bloqueado" and url and ("dior.com" in url.lower() or "swarovski" in url.lower()):
        print(f"\n🔧 REPARANDO FETCH: {rol} @ {marca}")
        print(f"   URL: {url}")
        
        try:
            client.pages.update(
                page_id=item["id"],
                properties={
                    "Fetch": {"select": {"name": "Accesible"}}
                }
            )
            print("   ✅ ACTUALIZADO: Fetch→Accesible")
            repaired += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print(f"✅ REPARADAS: {repaired} vacantes")
print("\n💡 Ahora ejecuta el pipeline normal:")
print("   python3 ./scripts/run_pipeline.py")