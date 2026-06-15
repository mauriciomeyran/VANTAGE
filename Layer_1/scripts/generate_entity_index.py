import os
import json
import requests
from dotenv import load_dotenv
from pathlib import Path

# --- CONFIGURACIÓN ---
env_path = Path.home() / "Documents/04-Vantage_CV/Layer_1/config/layer_1.env"
load_dotenv(env_path)
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
if not NOTION_TOKEN:
    raise ValueError("❌ NO SE ENCONTRÓ NOTION_TOKEN en el .env.")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# IDs CORREGIDOS (desde tu .env)
DATABASES = {
    "VANTAGE_TRACKER": "596938befc42836baea7814a1491bd47",  # NOTION_DB_OPPORTUNITIES
    "ARCHIVO_TRACKER": "4ec34e1b528648c9afbdd57c6eb76053"   # NOTION_ARCHIVE_DB_ID
}

# --- FUNCIONES (sin cambios) ---
def query_database(database_id, start_cursor=None):
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    payload = {"start_cursor": start_cursor, "page_size": 100} if start_cursor else {"page_size": 100}
    response = requests.post(url, headers=HEADERS, json=payload)
    response.raise_for_status()
    return response.json()

def get_all_pages(database_id):
    all_pages = []
    start_cursor = None
    while True:
        data = query_database(database_id, start_cursor)
        all_pages.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        start_cursor = data.get("next_cursor")
    return all_pages

def extract_hash(page):
    props = page.get("properties", {})
    hash_field = props.get("HASH") or props.get("Hash")
    if hash_field and hash_field.get("rich_text"):
        hash_text = "".join([rt["plain_text"] for rt in hash_field["rich_text"]])
        return hash_text.strip() if hash_text else None
    return None

def generate_entity_id(page_id, hash_value):
    if hash_value:
        return f"TRACKER:H_{hash_value[:16]}"
    return f"TRACKER:U_{page_id.replace('-', '')}"

# --- EJECUCIÓN ---
def main():
    entities = []
    metrics = {
        "total_entities": 0,
        "tracker_entities": 0,
        "archive_entities": 0,
        "hash_coverage": 0.0,
        "orphan_candidates": 0
    }

    for db_name, db_id in DATABASES.items():
        print(f"Procesando {db_name} ({db_id})...")
        pages = get_all_pages(db_id)
        for page in pages:
            page_id = page["id"]
            page_url = page["url"]
            hash_value = extract_hash(page)
            entity_type = "tracker" if db_name == "VANTAGE_TRACKER" else "archive"

            entity = {
                "entity_id": generate_entity_id(page_id, hash_value),
                "canonical_id": hash_value if hash_value else page_id,
                "page_id": page_id,
                "page_url": page_url,
                "entity_type": entity_type,
                "source_db": db_name
            }
            entities.append(entity)

            metrics["total_entities"] += 1
            if entity_type == "tracker":
                metrics["tracker_entities"] += 1
            else:
                metrics["archive_entities"] += 1
            if not hash_value:
                metrics["orphan_candidates"] += 1

        print(f"  - {len(pages)} páginas extraídas de {db_name}.")

    metrics["hash_coverage"] = round(
        ((metrics["total_entities"] - metrics["orphan_candidates"]) / metrics["total_entities"]) * 100,
        2
    ) if metrics["total_entities"] > 0 else 0.0

    output_path = Path.home() / "output" / "entity_index_v2_FULL.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"entities": entities, "metrics": metrics}, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Archivo generado: {output_path}")
    print(f"Métricas: {json.dumps(metrics, indent=2)}")

if __name__ == "__main__":
    main()