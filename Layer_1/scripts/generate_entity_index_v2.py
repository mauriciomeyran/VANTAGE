#!/usr/bin/env python3
"""
VANTAGE Entity Index Generator — v2
Genera entity_index_v2.json a partir de VANTAGE_TRACKER y ARCHIVO_TRACKER
usando EXCLUSIVAMENTE las funciones canónicas de backfill_hash.py v1.3
(make_client, query_data_source) y los Data Source IDs ya validados
por el backfill (292 registros actualizados, 0 fallidos).

No usa databases.query. No usa requests. No usa IDs históricos (DB-level).

Uso:
  python scripts/generate_entity_index_v2.py [--limit N] [--out PATH]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# ── paths ──────────────────────────────────────────────────────────────────────
_SCRIPTS_DIR = Path(__file__).resolve().parent
_LAYER_1_ROOT = _SCRIPTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from notion_utils import Client

load_dotenv(_LAYER_1_ROOT / ".env", override=True)

# ── config ─────────────────────────────────────────────────────────────────────
NOTION_TOKEN = os.environ["NOTION_TOKEN"]

# Data Source IDs (COL) — los mismos que backfill_hash.py v1.3 usó para
# actualizar 292 registros exitosamente. NO son database IDs.
DB_IDS = {
    "vantage": "596938be-fc42-836b-aea7-814a1491bd47",  # VANTAGE TRACKER (DB)
    "archivo": "4ec34e1b-5286-48c9-afbd-d57c6eb76053",  # ARCHIVO TRACKER (DB)
}

# Mapeo de label/entity_type para el índice de salida
DB_META = {
    "vantage": {"source_db": "VANTAGE_TRACKER", "entity_type": "tracker"},
    "archivo": {"source_db": "ARCHIVO_TRACKER", "entity_type": "archive"},
}

DATA_SOURCES_API_VERSION = "2025-09-03"

HASH_FIELD = "hash"
MAX_PAGES_PER_DB = 50  # 50 × 100 = 5000 registros máx


# ── helpers — idénticos a backfill_hash.py v1.3 ─────────────────────────────────
def make_client(token: str) -> Client:
    """
    Instancia el cliente forzando Notion-Version >= 2025-09-03, requerido
    para que existan los endpoints data_sources/*. Si el SDK instalado no
    acepta `notion_version` en el constructor, cae a instanciación normal
    y luego intenta sobreescribir el header directamente.
    """
    try:
        client = Client(auth=token, notion_version=DATA_SOURCES_API_VERSION)
    except Exception:
        client = Client(auth=token)

    try:
        client.client.headers["Notion-Version"] = DATA_SOURCES_API_VERSION
    except Exception:
        pass

    return client


def query_data_source(client: Client, data_source_id: str, **kwargs: Any) -> dict:
    """
    Wrapper sobre data_sources/{id}/query (Notion API 2025-09-03+).
    Reemplaza a client.databases.query(database_id=...), que no resuelve
    IDs de data source en DBs multi-source (404 / object_not_found).
    """
    if hasattr(client, "data_sources"):
        return client.data_sources.query(data_source_id=data_source_id, **kwargs)

    return client.request(
        path=f"data_sources/{data_source_id}/query",
        method="POST",
        body=kwargs,
    )


def _plain_text(prop: dict) -> str:
    ptype = prop.get("type", "")
    if ptype in ("rich_text", "title"):
        parts = prop.get(ptype, [])
        return "".join(p.get("plain_text", "") for p in parts).strip()
    if ptype == "select":
        return (prop.get("select") or {}).get("name", "").strip()
    if ptype == "url":
        return (prop.get("url") or "").strip()
    return ""


def get_hash(page: dict) -> str:
    props = page.get("properties", {})
    if HASH_FIELD not in props:
        return ""
    return _plain_text(props[HASH_FIELD])


def iter_all_pages(client: Client, data_source_id: str) -> list[dict]:
    """Misma lógica de paginación que iter_pages_without_hash, pero sin filtrar por hash."""
    all_pages: list[dict] = []
    kwargs: dict[str, Any] = {"page_size": 100}
    seen_cursors: set[str] = set()
    page_count = 0

    while True:
        page_count += 1
        if page_count > MAX_PAGES_PER_DB:
            print(f"  ⚠️  MAX_PAGES ({MAX_PAGES_PER_DB}) alcanzado — abortando")
            break
        try:
            resp = query_data_source(client, data_source_id, **kwargs)
        except Exception as exc:
            print(f"  ❌ Error consultando {data_source_id[:8]}: {exc}")
            break

        results = resp.get("results", [])
        if not results and page_count == 1:
            print(f"  ⚠️  La API devolvió 0 resultados en página 1 — verifica el data_source ID")
            break

        all_pages.extend(results)

        if not results:
            break

        cursor = resp.get("next_cursor")
        if resp.get("has_more") and cursor:
            if cursor in seen_cursors:
                print(f"  ⚠️  Cursor repetido — loop infinito abortado")
                break
            seen_cursors.add(cursor)
            kwargs["start_cursor"] = cursor
        else:
            break

    return all_pages


# ── entity index ─────────────────────────────────────────────────────────────
def generate_entity_id(page_id: str, hash_value: str) -> str:
    if hash_value:
        return f"TRACKER:H_{hash_value[:16]}"
    return f"TRACKER:U_{page_id.replace('-', '')}"


def build_entities(
    client: Client, label: str, data_source_id: str, limit: int | None
) -> list[dict]:
    meta = DB_META[label]
    print(f"\n{'─' * 60}")
    print(f"  Data Source: {meta['source_db']} ({data_source_id[:8]}…)")

    pages = iter_all_pages(client, data_source_id)
    if limit:
        pages = pages[:limit]

    print(f"  Páginas extraídas: {len(pages)}")

    entities = []
    for page in pages:
        page_id = page["id"]
        page_url = page.get("url", "")
        hash_value = get_hash(page)

        entities.append({
            "entity_id": generate_entity_id(page_id, hash_value),
            "canonical_id": hash_value if hash_value else page_id,
            "page_id": page_id,
            "page_url": page_url,
            "hash": hash_value if hash_value else None,
            "entity_type": meta["entity_type"],
            "source_db": meta["source_db"],
        })

    return entities


def main() -> None:
    parser = argparse.ArgumentParser(description="VANTAGE Entity Index Generator v2")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--out", type=Path, default=_LAYER_1_ROOT / "output" / "entity_index_v2.json")
    args = parser.parse_args()

    print("🔧 VANTAGE Entity Index Generator v2")

    client = make_client(NOTION_TOKEN)
    endpoint = "data_sources.query (SDK)" if hasattr(client, "data_sources") else "request() manual a data_sources/*/query"
    print(f"   Endpoint de consulta: {endpoint}")

    all_entities: list[dict] = []
    for label, data_source_id in DB_IDS.items():
        all_entities.extend(build_entities(client, label, data_source_id, args.limit))

    total = len(all_entities)
    tracker_count = sum(1 for e in all_entities if e["entity_type"] == "tracker")
    archive_count = sum(1 for e in all_entities if e["entity_type"] == "archive")
    orphan_count = sum(1 for e in all_entities if not e["hash"])
    hash_coverage = round(((total - orphan_count) / total) * 100, 2) if total > 0 else 0.0

    metrics = {
        "total_entities": total,
        "tracker_entities": tracker_count,
        "archive_entities": archive_count,
        "hash_coverage": hash_coverage,
        "orphan_candidates": orphan_count,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"entities": all_entities, "metrics": metrics}, f, indent=2, ensure_ascii=False)

    print(f"\n{'═' * 60}")
    print(f"  RESUMEN FINAL")
    print(f"  Total entidades   : {metrics['total_entities']}")
    print(f"  Tracker           : {metrics['tracker_entities']}")
    print(f"  Archivo           : {metrics['archive_entities']}")
    print(f"  Hash coverage     : {metrics['hash_coverage']}%")
    print(f"  Orphan candidates : {metrics['orphan_candidates']}")
    print(f"{'═' * 60}")
    print(f"\n✅ Archivo generado: {args.out}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Cancelado")
        sys.exit(1)
