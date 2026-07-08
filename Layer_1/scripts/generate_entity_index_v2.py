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
from collections import defaultdict
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# ── paths ──────────────────────────────────────────────────────────────────────
_SCRIPTS_DIR = Path(__file__).resolve().parent
_LAYER_1_ROOT = _SCRIPTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from notion_utils import Client
from runtime_identity import load_prefix_map, generate_entity_id

load_dotenv(_LAYER_1_ROOT / ".env", override=True)

# ── config ─────────────────────────────────────────────────────────────────────
NOTION_TOKEN = os.environ["NOTION_TOKEN"]
RESOLVER_REGISTRY_PATH = _SCRIPTS_DIR.parent / "data" / "resolver_registry_v2.json"

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


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


# _load_entity_prefixes() migrada a runtime_identity.load_prefix_map() — DT-014


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
# generate_entity_id() migrada a runtime_identity — DT-014

def build_entities(
    client: Client,
    label: str,
    data_source_id: str,
    limit: int | None,
    entity_prefixes: dict[str, str],
) -> list[dict]:
    meta = DB_META[label]
    source_db = meta["source_db"]
    normalized_source = source_db.upper().replace(" ", "_")
    if normalized_source not in entity_prefixes:
        raise KeyError(f"Missing entity_prefix in resolver_registry_v2.json for {source_db}")
    entity_prefix = entity_prefixes[normalized_source]
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
            "entity_id": generate_entity_id(entity_prefix, page_id, hash_value),
            "canonical_id": hash_value if hash_value else page_id,
            "page_id": page_id,
            "page_url": page_url,
            "hash": hash_value if hash_value else None,
            "entity_type": meta["entity_type"],
            "source_db": meta["source_db"],
        })

    return entities


# ── graph builder ───────────────────────────────────────────────────────────────
def build_graph(entities: list[dict]) -> dict:
    """
    Builds graph_v2.json from entity index.
    
    Only implements archived_from relationships:
    - ARCHIVO:H_<hash> → TRACKER:H_<hash> when both entities share the same hash
    
    Deterministic: edges are generated solely from hash matching in entity metadata.
    No fabricated edges, no inferred relationships.
    """
    # Group entities by hash (first 16 chars, matching entity_id format)
    hash_to_entities = defaultdict(list)
    for entity in entities:
        if entity.get("hash"):
            hash_prefix = entity["hash"][:16]
            hash_to_entities[hash_prefix].append(entity)
    
    # Build edges for archived_from relationships
    edges = []
    for hash_prefix, entity_list in hash_to_entities.items():
        # Need at least one ARCHIVO and one TRACKER with this hash
        archive_entities = [e for e in entity_list if e["entity_type"] == "archive"]
        tracker_entities = [e for e in entity_list if e["entity_type"] == "tracker"]
        
        if not archive_entities or not tracker_entities:
            continue
        
        # Create edges: ARCHIVO → TRACKER for each pair with matching hash
        for archive_ent in archive_entities:
            for tracker_ent in tracker_entities:
                edges.append({
                    "from": archive_ent["entity_id"],
                    "to": tracker_ent["entity_id"],
                    "type": "archived_from"
                })
    
    return {
        "version": "2.0",
        "edges": edges
    }


def build_backlinks(graph: dict) -> dict:
    """
    Builds backlinks_v2.json as inverse representation of graph edges.
    
    For every edge (from → to), creates a backlink entry for 'to' pointing to 'from'.
    No independent logic - purely derived from graph.
    """
    backlinks = defaultdict(list)
    
    for edge in graph.get("edges", []):
        to_entity = edge["to"]
        from_entity = edge["from"]
        edge_type = edge["type"]
        
        backlinks[to_entity].append({
            "from": from_entity,
            "type": edge_type
        })
    
    # Convert defaultdict to regular dict
    return {
        "version": "2.0",
        "backlinks": dict(backlinks)
    }


def validate_graph_artifacts(
    entities: list[dict], 
    graph: dict, 
    backlinks: dict
) -> tuple[bool, list[str]]:
    """
    Validates graph artifacts against entity index.
    
    Checks:
    1. No orphan entity_ids in graph edges (all nodes must exist in entity index)
    2. Backlinks exactly match graph (inverse relationship)
    3. Graph structure is valid
    
    Returns:
        (is_valid, list of error messages)
    """
    errors = []
    entity_ids = {e["entity_id"] for e in entities}
    
    # Check 1: No orphan entity_ids in graph edges
    for edge in graph.get("edges", []):
        from_id = edge["from"]
        to_id = edge["to"]
        
        if from_id not in entity_ids:
            errors.append(f"Orphan 'from' node in graph: {from_id}")
        if to_id not in entity_ids:
            errors.append(f"Orphan 'to' node in graph: {to_id}")
    
    # Check 2: Backlinks exactly match graph (inverse relationship)
    # Rebuild backlinks from graph to verify
    expected_backlinks = defaultdict(list)
    for edge in graph.get("edges", []):
        expected_backlinks[edge["to"]].append({
            "from": edge["from"],
            "type": edge["type"]
        })
    
    actual_backlinks = backlinks.get("backlinks", {})
    
    # Compare
    for entity_id in set(list(expected_backlinks.keys()) + list(actual_backlinks.keys())):
        expected = sorted(expected_backlinks.get(entity_id, []), key=lambda x: x["from"])
        actual = sorted(actual_backlinks.get(entity_id, []), key=lambda x: x["from"])
        
        if expected != actual:
            errors.append(f"Backlinks mismatch for {entity_id}: expected {len(expected)}, got {len(actual)}")
    
    # Check 3: No orphan entity_ids in backlinks
    for entity_id in actual_backlinks.keys():
        if entity_id not in entity_ids:
            errors.append(f"Orphan entity_id in backlinks: {entity_id}")
    
    return (len(errors) == 0, errors)


def main() -> None:
    parser = argparse.ArgumentParser(description="VANTAGE Entity Index Generator v2")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--out", type=Path, default=_SCRIPTS_DIR / "entity_index_v2.json")
    parser.add_argument("--skip-graph", action="store_true", help="Skip graph generation (entity index only)")
    args = parser.parse_args()

    print("🔧 VANTAGE Entity Index Generator v2")

    client = make_client(NOTION_TOKEN)
    endpoint = "data_sources.query (SDK)" if hasattr(client, "data_sources") else "request() manual a data_sources/*/query"
    print(f"   Endpoint de consulta: {endpoint}")

    entity_prefixes = load_prefix_map(RESOLVER_REGISTRY_PATH)

    all_entities: list[dict] = []
    for label, data_source_id in DB_IDS.items():
        all_entities.extend(build_entities(client, label, data_source_id, args.limit, entity_prefixes))

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

    # Write entity index with atomic pattern
    entity_index = {"entities": all_entities, "metrics": metrics}
    entity_index_path = args.out
    entity_index_tmp = entity_index_path.with_suffix(".json.tmp")
    
    entity_index_tmp.parent.mkdir(parents=True, exist_ok=True)
    with open(entity_index_tmp, "w", encoding="utf-8") as f:
        json.dump(entity_index, f, indent=2, ensure_ascii=False)
    os.replace(entity_index_tmp, entity_index_path)

    print(f"\n{'═' * 60}")
    print(f"  ENTITY INDEX")
    print(f"  Total entidades   : {metrics['total_entities']}")
    print(f"  Tracker           : {metrics['tracker_entities']}")
    print(f"  Archivo           : {metrics['archive_entities']}")
    print(f"  Hash coverage     : {metrics['hash_coverage']}%")
    print(f"  Orphan candidates : {metrics['orphan_candidates']}")
    print(f"  Archivo generado  : {entity_index_path}")

    # Build graph artifacts unless explicitly skipped
    if not args.skip_graph:
        print(f"\n{'═' * 60}")
        print(f"  GRAPH BUILDER")
        
        # Build graph
        graph = build_graph(all_entities)
        graph_path = _SCRIPTS_DIR / "graph_v2.json"
        graph_tmp = graph_path.with_suffix(".json.tmp")
        
        with open(graph_tmp, "w", encoding="utf-8") as f:
            json.dump(graph, f, indent=2, ensure_ascii=False)
        
        # Build backlinks
        backlinks = build_backlinks(graph)
        backlinks_path = _SCRIPTS_DIR / "backlinks_v2.json"
        backlinks_tmp = backlinks_path.with_suffix(".json.tmp")
        
        with open(backlinks_tmp, "w", encoding="utf-8") as f:
            json.dump(backlinks, f, indent=2, ensure_ascii=False)
        
        # Validate before replacing
        is_valid, errors = validate_graph_artifacts(all_entities, graph, backlinks)
        
        if not is_valid:
            # Clean up temp files on validation failure
            graph_tmp.unlink(missing_ok=True)
            backlinks_tmp.unlink(missing_ok=True)
            print(f"\n❌ VALIDATION FAILED:")
            for error in errors:
                print(f"   - {error}")
            raise RuntimeError("Graph validation failed - artifacts not updated")
        
        # Atomic replace
        os.replace(graph_tmp, graph_path)
        os.replace(backlinks_tmp, backlinks_path)
        
        print(f"  Edges generadas  : {len(graph['edges'])}")
        print(f"  Backlinks generadas: {len(backlinks['backlinks'])}")
        print(f"  Archivo graph    : {graph_path}")
        print(f"  Archivo backlinks : {backlinks_path}")
        print(f"  Validación       : ✅ PASSED")
    
    print(f"{'═' * 60}")
    print(f"\n✅ Runtime Build completado")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Cancelado")
        sys.exit(1)
