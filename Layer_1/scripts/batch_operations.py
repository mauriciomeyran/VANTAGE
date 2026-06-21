#!/usr/bin/env python3
"""
JHS Batch Operations - Actualizaciones masivas en Notion
Uso: python3 scripts/batch_operations.py           # solo reporte
     python3 scripts/batch_operations.py --execute  # activa escritura
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from notion_utils import Client

EXECUTE = "--execute" in sys.argv

def txt(prop):
    if not prop: return ""
    t = prop.get("type")
    if t == "select" and prop.get("select"):
        return prop["select"]["name"]
    if t == "title" and prop.get("title"):
        return prop["title"][0]["plain_text"]
    return ""

def main():
    load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
    client = Client(auth=os.environ["NOTION_TOKEN"])
    ds_id = "596938be-fc42-836b-aea7-814a1491bd47"

    print("🔄 JHS BATCH OPERATIONS")
    if not EXECUTE:
        print("⚠️  Modo lectura — pasa --execute para escribir")
    print("=" * 50)

    all_results = []
    payload = {}
    while True:
        response = client.data_sources.query(data_source_id=ds_id, **payload)
        all_results.extend(response.get("results", []))
        if response.get("has_more") and response.get("next_cursor"):
            payload["start_cursor"] = response["next_cursor"]
        else:
            break

    print(f"\n📊 Total entries: {len(all_results)}")

    status_count = {}
    for item in all_results:
        props = item["properties"]
        status = txt(props.get("Status"))
        if status:
            status_count[status] = status_count.get(status, 0) + 1

    print("📈 Entries por Status:")
    for status, count in sorted(status_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  {status}: {count}")

    target_status = "Target"
    new_status = "Exploratorio"
    target_items = [
        item["id"] for item in all_results
        if txt(item["properties"].get("Status")) == target_status
    ]

    if not target_items:
        print(f"\n✅ No hay entradas con Status='{target_status}'")
        return

    print(f"\n🔄 {len(target_items)} entradas con '{target_status}' → '{new_status}'")

    if not EXECUTE:
        print(f"💡 Para aplicar: vl1 batch --execute")
        return

    updated = 0
    for item_id in target_items:
        try:
            client.pages.update(
                page_id=item_id,
                properties={"Status": {"select": {"name": new_status}}}
            )
            updated += 1
            print(f"  ✅ {item_id[:8]}")
        except Exception as e:
            print(f"  ❌ {item_id[:8]} — {e}")

    print(f"\n✅ Actualizado: {updated}/{len(target_items)}")

if __name__ == "__main__":
    main()
