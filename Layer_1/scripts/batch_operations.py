#!/usr/bin/env python3
"""
JHS Batch Operations - Actualizaciones masivas en Notion
Uso: python3 scripts/batch_operations.py
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from notion_utils import Client

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
    ds_id = "4e542b37-6e52-4418-89b7-a0eeb3138307"

    print("🔄 JHS BATCH OPERATIONS")
    print("=" * 50)
    
    # Get all entries
    items = client.data_sources.query(data_source_id=ds_id)["results"]
    
    print(f"\n📊 Total entries: {len(items)}")
    
    # Count by status
    status_count = {}
    for item in items:
        props = item["properties"]
        status = txt(props.get("Status"))
        if status:
            status_count[status] = status_count.get(status, 0) + 1
    
    print("📈 Entries por Status:")
    for status, count in sorted(status_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  {status}: {count}")
    
    # Batch update example: Change all "Target" to "Exploratorio"
    target_status = "Target"
    new_status = "Exploratorio"
    
    target_items = []
    for item in items:
        props = item["properties"]
        status = txt(props.get("Status"))
        if status == target_status:
            target_items.append(item["id"])
    
    if target_items:
        print(f"\n🔄 Cambiando {len(target_items)} entradas de '{target_status}' a '{new_status}':")
        
        confirm = input("¿Confirmar? (y/N): ").lower().strip()
        if confirm == "y":
            updated = 0
            for item_id in target_items:
                try:
                    client.pages.update(
                        page_id=item_id,
                        properties={
                            "Status": {"select": {"name": new_status}}
                        }
                    )
                    updated += 1
                    print(f"  ✅ Actualizado: {item_id[:8]}")
                except Exception as e:
                    print(f"  ❌ Error: {item_id[:8]} - {e}")
            
            print(f"\n✅ Total actualizado: {updated}/{len(target_items)}")
        else:
            print("❌ Operación cancelada")
    else:
        print(f"\n✅ No hay entradas con Status='{target_status}'")
    
    print("\n" + "=" * 50)
    print("💡 Comandos disponibles:")
    print("  python3 scripts/batch_operations.py")
    print("  (Modifica el script para batch específico)")

if __name__ == "__main__":
    main()