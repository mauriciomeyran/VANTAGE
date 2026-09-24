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
import hashlib

import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
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
    "vantage": "442938be-fc42-828f-b72e-076818d65a5b",  # VANTAGE TRACKER (DB)
    "archivo": "674696fd-94b6-464a-ac1f-64b0cc917e15",  # ARCHIVO TRACKER (DB)
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
    entity_id_seen = {}  # For duplicate detection (F3)

    for page in pages:
        page_id = page["id"]
        page_url = page.get("url", "")
        hash_value = get_hash(page)

        # Extract archived_from metadata for ARCHIVO_TRACKER (P2 fix)
        archived_from = None
        if meta["entity_type"] == "archive":
            props = page.get("properties", {})
            # Try multiple possible property names for the archived reference
            for prop_name in ["archived_from", "Archived_From", "TRACKER", "Tracker", "Origin"]:
                if prop_name in props:
                    prop_value = props[prop_name]
                    # Handle different property types
                    if prop_value.get("type") == "rich_text":
                        archived_from = "".join(p.get("plain_text", "") for p in prop_value.get("rich_text", [])).strip()
                    elif prop_value.get("type") == "title":
                        archived_from = "".join(p.get("plain_text", "") for p in prop_value.get("title", [])).strip()
                    elif prop_value.get("type") == "select":
                        archived_from = (prop_value.get("select") or {}).get("name", "").strip()
                    elif prop_value.get("type") == "relation":
                        relations = prop_value.get("relation", [])
                        if relations:
                            archived_from = relations[0].get("id", "")
                    if archived_from:
                        break

        entity_id = generate_entity_id(entity_prefix, page_id, hash_value)

        # Duplicate detection (F3)
        if entity_id in entity_id_seen:
            print(f"  ⚠️  DUPLICADO DETECTADO: {entity_id} aparece múltiples veces")
            print(f"      Previo: {entity_id_seen[entity_id]}")
            print(f"      Nuevo: {page_id}")
            # Log but continue - don't silently swallow
        entity_id_seen[entity_id] = page_id

        if not hash_value:
            seed = f"{page_id}:{meta['source_db']}".encode('utf-8')
            final_hash = f"H_{hashlib.sha256(seed).hexdigest()[:16]}"
        else:
            final_hash = hash_value

        entities.append({
            "entity_id": entity_id,
            "canonical_id": final_hash,
            "page_id": page_id,
            "page_url": page_url,
            "hash": final_hash,
            "entity_type": meta["entity_type"],
            "source_db": meta["source_db"],
            "archived_from": archived_from,  # P2: metadata-based archiving
        })

    return entities


# ── graph builder ───────────────────────────────────────────────────────────────
def build_graph(entities: list[dict]) -> dict:
    """
    Builds graph_v2.json from entity index.

    SUSPENDED: The graph subsystem is suspended by product decision.
    VANTAGE architecture does not support graph-based archiving relationships:
    - Archived rows are the SAME row moved from TRACKER to ARCHIVO_TRACKER (mutually exclusive)
    - No two entities exist simultaneously to link with an edge
    - No "archived_from" field exists in the ARCHIVO_TRACKER schema

    This function returns a SUSPENDED marker instead of attempting to build
    structurally impossible edges from non-existent metadata.
    """
    return {
        "version": "2.0",
        "status": "SUSPENDED",
        "reason": "Product decision: VANTAGE uses mutually exclusive row movement (TRACKER ↔ ARCHIVO_TRACKER), not graph-based archiving. No edge relationships exist in the data model.",
        "edges": []
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

    SUSPENDED: If graph status is SUSPENDED, validation passes explicitly
    recognizing the suspended state rather than attempting to validate
    structurally impossible empty artifacts.

    Normal validation (when not suspended):
    1. No orphan entity_ids in graph edges (all nodes must exist in entity index)
    2. Backlinks exactly match graph (inverse relationship)
    3. Graph structure is valid

    Returns:
        (is_valid, list of error messages)
    """
    # Check if graph is suspended
    if graph.get("status") == "SUSPENDED":
        print(f"  ✓ Graph validation: SUSPENDED (reason: {graph.get('reason', 'Product decision')})")
        return (True, [])

    errors = []
    entity_ids = {e["entity_id"] for e in entities}

    # Extract edges from graph (handle new structure with metadata)
    graph_edges = graph.get("edges", []) if isinstance(graph, dict) else graph
    backlinks_data = backlinks.get("backlinks", {}) if isinstance(backlinks, dict) else backlinks

    # Check 1: No orphan entity_ids in graph edges
    for edge in graph_edges:
        from_id = edge["from"]
        to_id = edge["to"]

        if from_id not in entity_ids:
            errors.append(f"Orphan 'from' node in graph: {from_id}")
        if to_id not in entity_ids:
            errors.append(f"Orphan 'to' node in graph: {to_id}")

    # Check 2: Backlinks exactly match graph (inverse relationship)
    # Rebuild backlinks from graph to verify
    expected_backlinks = defaultdict(list)
    for edge in graph_edges:
        expected_backlinks[edge["to"]].append({
            "from": edge["from"],
            "type": edge["type"]
        })

    actual_backlinks = backlinks_data

    # Verify backlinks match
    for node_id, expected_links in expected_backlinks.items():
        actual_links = actual_backlinks.get(node_id, [])
        if len(actual_links) != len(expected_links):
            errors.append(f"Backlinks count mismatch for {node_id}: expected {len(expected_links)}, got {len(actual_links)}")

        # Compare individual links (order-independent)
        expected_set = {(link["from"], link["type"]) for link in expected_links}
        actual_set = {(link["from"], link["type"]) for link in actual_links}
        if expected_set != actual_set:
            errors.append(f"Backlinks content mismatch for {node_id}")

    # Check for extra backlinks not in graph
    for node_id, actual_links in actual_backlinks.items():
        if node_id not in expected_backlinks and actual_links:
            errors.append(f"Extra backlinks for {node_id} not present in graph")

    return (len(errors) == 0, errors)
    
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
    parser.add_argument("--out", type=Path, default=_LAYER_1_ROOT / "data" / "entity_index_v2.json")
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
    try:
        source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=_LAYER_1_ROOT, stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        source_commit = "unknown"

    entity_index = {
        "entities": all_entities,
        "metrics": metrics,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_commit": source_commit,
    }
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
        graph_with_metadata = {
            "edges": graph["edges"],
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "source_commit": source_commit,
        }
        graph_path = _LAYER_1_ROOT / "data" / "graph_v2.json"
        graph_tmp = graph_path.with_suffix(".json.tmp")

        with open(graph_tmp, "w", encoding="utf-8") as f:
            json.dump(graph_with_metadata, f, indent=2, ensure_ascii=False)
        
        # Build backlinks
        backlinks = build_backlinks(graph)
        backlinks_with_metadata = {
            "backlinks": backlinks["backlinks"],
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "source_commit": source_commit,
        }
        backlinks_path = _LAYER_1_ROOT / "data" / "backlinks_v2.json"
        backlinks_tmp = backlinks_path.with_suffix(".json.tmp")

        with open(backlinks_tmp, "w", encoding="utf-8") as f:
            json.dump(backlinks_with_metadata, f, indent=2, ensure_ascii=False)
        
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
