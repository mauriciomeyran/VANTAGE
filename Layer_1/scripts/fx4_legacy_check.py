#!/usr/bin/env python3
"""
FX-4: Conteo de registros legacy en VANTAGE Tracker
Legacy = registros sin campo 'layer' o sin campo 'hash' (introducidos en v7.5)
"""

import os
import json
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

notion = Client(auth=os.environ["NOTION_TOKEN"])
DATABASE_ID = "596938be-fc42-836b-aea7-814a1491bd47"

results = []
cursor = None

while True:
    kwargs = {"database_id": DATABASE_ID, "page_size": 100}
    if cursor:
        kwargs["start_cursor"] = cursor
    response = notion.databases.query(**kwargs)
    results.extend(response.get("results", []))
    if not response.get("has_more"):
        break
    cursor = response.get("next_cursor")

print(f"Total registros consultados: {len(results)}")

legacy_items = []

for page in results:
    props = page["properties"]

    layer = (props.get("layer") or {}).get("select", {}).get("name")
    hash_list = (props.get("hash") or {}).get("rich_text", [])
    hash_val = hash_list[0].get("plain_text") if hash_list else None

    if not layer or not hash_val:
        role_list = (props.get("Rol") or {}).get("title", [])
        role = role_list[0].get("plain_text", "N/A") if role_list else "N/A"

        legacy_items.append({
            "id": page["id"],
            "role": role,
            "layer": layer,
            "hash": hash_val,
            "missing": [f for f, v in [("layer", layer), ("hash", hash_val)] if not v]
        })

print(f"\n📊 Registros legacy (sin layer y/o sin hash): {len(legacy_items)}")
print(f"   Solo sin layer : {sum(1 for i in legacy_items if 'layer' in i['missing'] and 'hash' not in i['missing'])}")
print(f"   Solo sin hash  : {sum(1 for i in legacy_items if 'hash' in i['missing'] and 'layer' not in i['missing'])}")
print(f"   Sin ambos      : {sum(1 for i in legacy_items if len(i['missing']) == 2)}")

for item in legacy_items:
    print(f"  → {item['id']} | {item['role']} | missing: {item['missing']}")

output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "legacy_items.json")
with open(output_path, "w") as f:
    json.dump(legacy_items, f, indent=2, ensure_ascii=False)

print(f"\n✅ Guardado en: {output_path}")
