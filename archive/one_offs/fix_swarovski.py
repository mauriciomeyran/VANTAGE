#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from notion_client import Client

load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
client = Client(auth=os.environ["NOTION_TOKEN"])
ds_id = "4e542b37-6e52-4418-89b7-a0eeb3138307"

items = client.data_sources.query(data_source_id=ds_id)["results"]

print("🔧 FORZANDO SWAROVSKI")
print("=" * 60)

fixed = 0

for item in items:
    props = item["properties"]
    
    rol_prop = props.get("Rol", {})
    rol = ""
    if rol_prop.get("title"):
        rol = rol_prop["title"][0].get("plain_text", "")
    
    # Buscar por "Visual Merchandising Expert"
    if "visual merchandising expert" in rol.lower():
        print(f"\n🎯 ENCONTRADO: {rol}")
        
        try:
            client.pages.update(
                page_id=item["id"],
                properties={
                    "Status": {"select": {"name": "Nueva"}},
                    "Gate_Decision": {"select": {"name": "CREATE"}},
                    "Next_Action": {"select": {"name": "Revisar JD"}},
                    "Fetch": {"select": {"name": "Accesible"}}
                }
            )
            print("   ✅ ACTUALIZADO")
            fixed += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")

print(f"\n✅ FORZADAS: {fixed} vacantes")