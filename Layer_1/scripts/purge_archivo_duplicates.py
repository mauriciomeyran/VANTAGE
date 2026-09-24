import os
import sys
from collections import defaultdict
from pathlib import Path
from dotenv import load_dotenv

_SCRIPTS_DIR = Path(__file__).resolve().parent
_LAYER_1_ROOT = _SCRIPTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from generate_entity_index_v2 import make_client, query_data_source, get_hash, iter_all_pages
from notion_utils import _notion_patch

env_path = _LAYER_1_ROOT / ".env"
load_dotenv(env_path, override=True)

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATA_SOURCE_ID = "674696fd-94b6-464a-ac1f-64b0cc917e15"

def archive_page(client, page_id):
    try:
        _notion_patch(f"/v1/pages/{page_id}", {"archived": True})
        return True
    except Exception as e:
        print(f" Error archivando {page_id}: {e}")
        return False

def run_deduplication(dry_run=True):
    print(f"🔍 Consultando ARCHIVO_TRACKER via data_sources API...")
    client = make_client(NOTION_TOKEN)
    pages = iter_all_pages(client, DATA_SOURCE_ID)
    print(f" Total registros procesados: {len(pages)}")

    hash_groups = defaultdict(list)
    for page in pages:
        h = get_hash(page)
        if h:
            hash_groups[h].append(page)

    to_archive = []
    for entity_hash, records in hash_groups.items():
        if len(records) > 1:
            records.sort(key=lambda x: x.get("last_edited_time", ""), reverse=True)
            duplicates = records[1:]
            for dup in duplicates:
                to_archive.append((dup["id"], entity_hash, dup.get("last_edited_time", "")))

    print(f"\n--- Resumen de Deduplicación ---")
    print(f"Hashes únicos: {len(hash_groups)}")
    print(f"Registros duplicados a archivar: {len(to_archive)}")

    if dry_run:
        print("\n⚠️ [DRY RUN ACTIVE] Sin cambios en Notion.")
        for page_id, h, last_edited in to_archive[:10]:
            print(f"  A archivar: ID={page_id} | Hash={h} | LastEdited={last_edited}")
        if len(to_archive) > 10:
            print(f"  ... y {len(to_archive) - 10} registros más.")
    else:
        print("\n🚀 Ejecutando archivado en Notion...")
        success_count = 0
        for page_id, h, _ in to_archive:
            if archive_page(client, page_id):
                success_count += 1
        print(f"✅ Completado. {success_count}/{len(to_archive)} duplicados archivados.")

if __name__ == "__main__":
    is_dry = "--apply" not in sys.argv
    run_deduplication(dry_run=is_dry)
