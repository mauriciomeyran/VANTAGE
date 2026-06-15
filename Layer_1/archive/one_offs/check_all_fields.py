#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from notion_client import Client

load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
client = Client(auth=os.environ["NOTION_TOKEN"])
ds_id = "4e542b37-6e52-4418-89b7-a0eeb3138307"

items = client.data_sources.query(data_source_id=ds_id)["results"]

print("🔍 TODOS LOS CAMPOS DE DIOR Y SWAROVSKI")
print("=" * 60)

for item in items:
    props = item["properties"]
    rol = props.get("Rol", {}).get("title", [{}])[0].get("plain_text", "")
    marca = props.get("Marca", {}).get("select", {}).get("name", "")
    
    if "dior" in marca.lower() or "swarovski" in marca.lower():
        print(f"\n🎯 {rol} @ {marca}")
        print("   Campos disponibles:")
        for key, value in props.items():
            if value:  # Solo mostrar campos con contenido
                print(f"   - {key}: {type(value)}")
        
        # Mostrar contenido de campos de texto
        for field in ["Texto JD", "JD", "Description", "Descripción"]:
            if field in props:
                content = props[field]
                if content.get("rich_text"):
                    text = content["rich_text"][0].get("plain_text", "")
                    if text:
                        print(f"   📄 {field}: {len(text)} chars")