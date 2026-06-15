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

print("🔍 DEBUG: ANALIZANDO VACANTES")
print("=" * 60)

for item in items:
    props = item["properties"]
    rol = txt(props.get("Rol"))
    marca = txt(props.get("Marca"))
    status = txt(props.get("Status"))
    jd = txt(props.get("Texto JD")) or txt(props.get("JD")) or ""
    url = txt(props.get("URL"))
    
    # Mostrar todas las vacantes con JD
    if len(jd) > 100:
        print(f"\n📄 VACANTE CON JD:")
        print(f"   Rol: {rol}")
        print(f"   Marca: {marca}")
        print(f"   Status: {status}")
        print(f"   JD length: {len(jd)} chars")
        print(f"   URL: {url[:50]}..." if url else "   URL: None")
        
        # Check condiciones
        dior_in_marca = "dior" in marca.lower() if marca else False
        dior_in_rol = "dior" in rol.lower() if rol else False
        dior_in_url = "dior.com" in url.lower() if url else False
        swarovski_in_marca = "swarovski" in marca.lower() if marca else False
        
        print(f"   Condiciones:")
        print(f"     - 'dior' en marca: {dior_in_marca}")
        print(f"     - 'dior' en rol: {dior_in_rol}")
        print(f"     - 'dior.com' en URL: {dior_in_url}")
        print(f"     - 'swarovski' en marca: {swarovski_in_marca}")
        print(f"     - Status == 'Expirada': {status == 'Expirada'}")

print("\n" + "=" * 60)
print("💡 Esto muestra por qué el script anterior no encontró nada.")