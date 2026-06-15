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

print("🔧 FIX FINAL - TODOS LOS AJUSTES")
print("=" * 60)

fixed = 0

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
    vm_scope = txt(props.get("VM_Scope"))
    role_class = txt(props.get("Role_Class"))
    
    # 1. Vacantes con JD > 100 chars pero Status Expirada → Nueva
    if len(jd) > 100 and status == "Expirada":
        print(f"\n🔧 1. STATUS: {rol} @ {marca}")
        print(f"   Status: {status} → Nueva (JD: {len(jd)} chars)")
        
        try:
            client.pages.update(
                page_id=item["id"],
                properties={
                    "Status": {"select": {"name": "Nueva"}}
                }
            )
            print("   ✅ ACTUALIZADO")
            fixed += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # 2. Vacantes con Fetch Accesible, JD > 100, pero Gate_Decision BLOCKED → CREATE
    if (fetch == "Accesible" and len(jd) > 100 and 
        gate_decision == "BLOCKED" and status != "Expirada"):
        print(f"\n🔧 2. GATE: {rol} @ {marca}")
        print(f"   Gate: {gate_decision} → CREATE")
        
        try:
            client.pages.update(
                page_id=item["id"],
                properties={
                    "Gate_Decision": {"select": {"name": "CREATE"}},
                    "Next_Action": {"select": {"name": "Re-check"}}
                }
            )
            print("   ✅ ACTUALIZADO")
            fixed += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # 3. Vacantes CREATE con VM_Scope Alto o Role_Class Pivote → Next_Action diferente
    if (gate_decision == "CREATE" and next_action == "Re-check" and
        (vm_scope == "Alto" or role_class == "Pivote")):
        print(f"\n🔧 3. NEXT_ACTION: {rol} @ {marca}")
        print(f"   VM_Scope: {vm_scope}, Role_Class: {role_class}")
        print(f"   Next_Action: {next_action} → Revisar JD")
        
        try:
            client.pages.update(
                page_id=item["id"],
                properties={
                    "Next_Action": {"select": {"name": "Revisar JD"}}
                }
            )
            print("   ✅ ACTUALIZADO")
            fixed += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # 4. Vacantes APPLIED con Gate_Decision incorrecto
    if status in ["Postulado", "En proceso", "Negociando", "Sin respuesta"] and gate_decision != "APPLIED":
        print(f"\n🔧 4. APPLIED: {rol} @ {marca}")
        print(f"   Status: {status}, Gate: {gate_decision} → APPLIED")
        
        try:
            client.pages.update(
                page_id=item["id"],
                properties={
                    "Gate_Decision": {"select": {"name": "APPLIED"}}
                }
            )
            print("   ✅ ACTUALIZADO")
            fixed += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print(f"✅ TOTAL REPARADAS: {fixed} vacantes")
print("\n💡 Ahora ejecuta el pipeline para recalcular scoring:")
print("   python3 ./scripts/run_pipeline.py")