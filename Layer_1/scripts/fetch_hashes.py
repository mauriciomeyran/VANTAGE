#!/usr/bin/env python3
"""
fetch_hashes.py — Obtiene hashes de VANTAGE y ARCHIVO TRACKER
y actualiza entity_index_v2.json.

Reemplaza la versión con page IDs hardcodeados (v1).
Pagina el data source completo vía data_sources/{id}/query (API 2025-09-03),
mismo patrón que consolidate_duplicates.py y layer_1_run.py.
"""
import json
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env", override=True)

TOKEN = os.environ["NOTION_TOKEN"]
NOTION_VERSION = "2025-09-03"
API_BASE = "https://api.notion.com/v1"

DATA_SOURCES = {
    "VANTAGE_TRACKER": "442938be-fc42-828f-b72e-076818d65a5b",
    "ARCHIVO_TRACKER": "674696fd-94b6-464a-ac1f-64b0cc917e15",
}

INDEX_PATH = Path(__file__).resolve().parent / "entity_index_v2.json"


def query_all(data_source_id: str) -> list[dict]:
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    url = f"{API_BASE}/data_sources/{data_source_id}/query"
    results, cursor = [], None
    with httpx.Client(timeout=30) as client:
        while True:
            body = {
                "page_size": 100,
                "sorts": [{"timestamp": "created_time", "direction": "ascending"}],
            }
            if cursor:
                body["start_cursor"] = cursor
            r = client.post(url, headers=headers, json=body)
            r.raise_for_status()
            data = r.json()
            results.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
    return results


def extract_hash(props: dict) -> str | None:
    for k in ["hash", "Hash", "HASH"]:
        if k not in props:
            continue
        p = props[k]
        t = p.get("type", "")
        if t == "rich_text":
            arr = p.get("rich_text", [])
            return arr[0]["plain_text"] if arr else None
        if t == "formula":
            return p.get("formula", {}).get("string")
    return None


def main():
    if not INDEX_PATH.exists():
        print(f"ERROR: No existe {INDEX_PATH}")
        print("  Ejecuta generate_entity_index_v2.py primero.")
        return

    with open(INDEX_PATH) as f:
        idx = json.load(f)
    lookup = {e["page_id"]: e for e in idx["entities"]}
    print(f"Index cargado: {len(lookup)} entidades")

    patched = 0
    for source_name, ds_id in DATA_SOURCES.items():
        print(f"\n[{source_name}] Consultando data source {ds_id[:8]}...")
        pages = query_all(ds_id)
        print(f"  {len(pages)} páginas obtenidas")
        for page in pages:
            pid = page["id"]
            h = extract_hash(page.get("properties", {}))
            if h and pid in lookup:
                e = lookup[pid]
                e["entity_id"]    = f"TRACKER:H_{h[:16]}"
                e["canonical_id"] = h
                e["hash"]         = h
                patched += 1

    entities = list(lookup.values())
    total    = len(entities)
    has_hash = sum(1 for e in entities if not e["entity_id"].startswith("TRACKER:U_"))
    orphans  = total - has_hash
    hash_cov = round(has_hash / total, 4) if total else 0

    idx["entities"] = entities
    idx["metrics"]["hash_coverage"]     = hash_cov
    idx["metrics"]["orphan_candidates"] = orphans

    with open(INDEX_PATH, "w") as f:
        json.dump(idx, f, indent=2, ensure_ascii=False)

    print(f"\nPatched : {patched}")
    print(f"Coverage: {has_hash}/{total} ({hash_cov * 100:.1f}%)")
    print(f"Orphans : {orphans}")
    print(f"Listo   — {INDEX_PATH} actualizado.")


if __name__ == "__main__":
    main()
