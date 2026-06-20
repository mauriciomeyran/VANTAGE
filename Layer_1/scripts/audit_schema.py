import os
import json
from dotenv import load_dotenv
from notion_utils import Client

load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
notion = Client(auth=os.environ["NOTION_TOKEN"])
db_id = os.environ["NOTION_DB_OPPORTUNITIES"]

print("Obteniendo schema de la base de datos...")
result = notion.databases.retrieve(database_id=db_id)

# Guardar schema completo
with open("out/schema_full.json", "w") as f:
    json.dump(result, f, indent=2)

# Extraer solo las propiedades
properties = result["properties"]
with open("out/schema_properties.json", "w") as f:
    json.dump(properties, f, indent=2)

print(f"✅ Schema guardado en out/")
print(f"Propiedades encontradas: {len(properties)}")
for prop_name, prop_data in properties.items():
    prop_type = prop_data["type"]
    print(f"  - {prop_name} ({prop_type})")