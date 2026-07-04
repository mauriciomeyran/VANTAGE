"""
VANTAGE Runtime
================

Sistema operativo documental completo:

  Entity Index  (Phase 1)
  + Resolver     (Phase 3)
  + Query Layer  (Phase 4)
  + Context Layer (Phase 5)
  + Agent API    (Phase 6)
  + notion_utils hardening (Phase 7)

Entrypoint único. Uso:

  CLI:
    python3 vantage.py ask "show active roles"
    python3 vantage.py ask "find candidates"
    python3 vantage.py ask "compare TRACKER:H_x TRACKER:H_y"
    python3 vantage.py ask "country manager"
    python3 vantage.py resolve TRACKER:H_93a9bae7f01e656e
    python3 vantage.py context TRACKER:H_93a9bae7f01e656e
    python3 vantage.py status
    python3 vantage.py sync

  Python:
    from vantage import ask, resolve, context, query, status, sync
"""

from __future__ import annotations

from dotenv import load_dotenv
load_dotenv("../.env")

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict

# --- imports de todas las capas -----------------------------------------------

from query_layer import (
    query as _query,
    find_entity,
    list_entities,
    search_entities,
    lookup_by_hash,
    lookup_by_role,
    resolve_entity as _resolve_entity,
)
from context_layer import assemble_context
from agent_api import ask as _ask
from notion_utils import get_metrics, clear_cache, reset_metrics, ResolverError


# --- API unificada ----------------------------------------------------------------

def ask(prompt: str, **kwargs) -> Dict[str, Any]:
    """Phase 6 - lenguaje natural -> intención -> resultado estructurado."""
    return _ask(prompt, **kwargs)


def resolve(entity_id: str) -> Dict[str, Any]:
    """Phase 3 - entity_id/canonical_id -> page_url resuelto."""
    return _resolve_entity({"entity_id": entity_id})


def context(entity_id: str) -> Dict[str, Any]:
    """Phase 5 - entity_id -> {entity, status, metadata, content}."""
    return assemble_context(entity_id)


def query(value: str) -> Dict[str, Any]:
    """Phase 4 - entity_id / canonical_id / texto libre -> matches."""
    return _query(value)


def status() -> Dict[str, Any]:
    """Healthcheck del runtime: tamaño del index + metrics de Notion."""
    from query_layer import load_index, ENTITY_INDEX_PATH
    index = load_index()
    entities = index.get("entities", [])

    index_mtime = os.path.getmtime(ENTITY_INDEX_PATH)
    index_age_hours = round((time.time() - index_mtime) / 3600, 1)

    result = {
        "runtime": "VANTAGE",
        "phases": "1-8",
        "entity_index": {
            "total_entities": len(entities),
            "metrics": index.get("metrics", {}),
        },
        "notion_utils_metrics": get_metrics(),
        "index_age_hours": index_age_hours,
        "index_path": str(ENTITY_INDEX_PATH),
    }
    if index_age_hours > 24:
        result["warning"] = "entity_index_stale"
    return result



def sync() -> dict:
    """
    Regenera Runtime Build completo:
    1. entity_index_v2.json (consultando Notion via generate_entity_index_v2)
    2. graph_v2.json (relaciones archived_from derivadas de entity index)
    3. backlinks_v2.json (representación inversa de graph)
    
    Atomic write (.tmp -> os.replace). Preserva artefactos anteriores si falla.
    """
    import importlib

    _scripts_dir = Path(__file__).resolve().parent

    # Lazy import con sys.path limpio para evitar que notion_utils.py local
    # tape al SDK notion-client de PyPI que usa generate_entity_index_v2
    _gen_path = Path(__file__).resolve().parent / "generate_entity_index_v2.py"
    try:
        import importlib.util as _ilu
        _scripts_dir_str = str(_scripts_dir)
        _saved_path  = sys.path[:]
        _saved_nc    = sys.modules.pop("notion_utils", None)
        sys.path     = [p for p in sys.path if p not in (_scripts_dir_str, ".", "")]
        try:
            _spec = _ilu.spec_from_file_location("generate_entity_index_v2", _gen_path)
            gen   = _ilu.module_from_spec(_spec)
            _spec.loader.exec_module(gen)
        finally:
            sys.path = _saved_path
            if _saved_nc is not None:
                sys.modules["notion_utils"] = _saved_nc
    except Exception as exc:
        return {"status": "error", "error": f"No se pudo cargar generate_entity_index_v2: {exc}", "artifacts_preserved": True}

    from query_layer import ENTITY_INDEX_PATH, load_index

    index_path = Path(ENTITY_INDEX_PATH)
    graph_path = _scripts_dir / "graph_v2.json"
    backlinks_path = _scripts_dir / "backlinks_v2.json"
    
    index_tmp = index_path.with_suffix(".json.tmp")
    graph_tmp = graph_path.with_suffix(".json.tmp")
    backlinks_tmp = backlinks_path.with_suffix(".json.tmp")

    try:
        entities_before = len(load_index().get("entities", []))
    except Exception:
        entities_before = 0

    t_start = time.monotonic()
    try:
        token  = os.environ["NOTION_TOKEN"]
        client = gen.make_client(token)

        # Step 1: Generate entity index
        all_entities = []
        for label, ds_id in gen.DB_IDS.items():
            all_entities.extend(gen.build_entities(client, label, ds_id, limit=None))

        total         = len(all_entities)
        tracker_count = sum(1 for e in all_entities if e["entity_type"] == "tracker")
        archive_count = sum(1 for e in all_entities if e["entity_type"] == "archive")
        orphan_count  = sum(1 for e in all_entities if not e["hash"])
        hash_coverage = round(((total - orphan_count) / total) * 100, 2) if total > 0 else 0.0

        new_index = {
            "entities": all_entities,
            "metrics": {
                "total_entities":    total,
                "tracker_entities":  tracker_count,
                "archive_entities":  archive_count,
                "hash_coverage":     hash_coverage,
                "orphan_candidates": orphan_count,
            },
        }

        # Step 2: Build graph
        graph = gen.build_graph(all_entities)
        
        # Step 3: Build backlinks
        backlinks = gen.build_backlinks(graph)
        
        # Step 4: Validate artifacts
        is_valid, errors = gen.validate_graph_artifacts(all_entities, graph, backlinks)
        
        if not is_valid:
            return {
                "status": "error",
                "error": f"Graph validation failed: {'; '.join(errors)}",
                "artifacts_preserved": True
            }
        
        # Step 5: Atomic write all artifacts
        index_tmp.write_text(json.dumps(new_index, indent=2, ensure_ascii=False), encoding="utf-8")
        graph_tmp.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
        backlinks_tmp.write_text(json.dumps(backlinks, indent=2, ensure_ascii=False), encoding="utf-8")
        
        os.replace(index_tmp, index_path)
        os.replace(graph_tmp, graph_path)
        os.replace(backlinks_tmp, backlinks_path)

    except Exception as exc:
        # Clean up temp files on failure
        index_tmp.unlink(missing_ok=True)
        graph_tmp.unlink(missing_ok=True)
        backlinks_tmp.unlink(missing_ok=True)
        return {"status": "error", "error": str(exc), "artifacts_preserved": True}

    elapsed = round(time.monotonic() - t_start, 3)
    load_index(force_reload=True)
    
    # Reload graph_layer to pick up new graph artifacts
    try:
        import importlib
        import graph_layer
        importlib.reload(graph_layer)
    except Exception:
        pass
    
    status_result = status()

    return {
        "status":                "ok",
        "entities_before":       entities_before,
        "entities_after":        status_result["entity_index"]["total_entities"],
        "graph_edges":           len(graph["edges"]),
        "backlinks_count":       len(backlinks["backlinks"]),
        "elapsed_seconds":       elapsed,
        "index_path":            str(index_path),
        "graph_path":            str(graph_path),
        "backlinks_path":        str(backlinks_path),
        "entity_index":          status_result["entity_index"],
        "notion_utils_metrics": status_result["notion_utils_metrics"],
    }

__all__ = [
    "ask", "resolve", "context", "query", "status", "sync",
    "find_entity", "list_entities", "search_entities",
    "lookup_by_hash", "lookup_by_role",
    "clear_cache", "reset_metrics", "ResolverError",
]


# --- CLI ----------------------------------------------------------------------------

def _main() -> None:
    import sys

    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(1)

    cmd = sys.argv[1]
    rest = sys.argv[2:]

    try:
        if cmd == "ask":
            if not rest:
                print("uso: python3 vantage.py ask '<prompt>'")
                raise SystemExit(1)
            result = ask(" ".join(rest))
        elif cmd == "resolve":
            if not rest:
                print("uso: python3 vantage.py resolve <entity_id>")
                raise SystemExit(1)
            result = resolve(rest[0])
        elif cmd == "context":
            if not rest:
                print("uso: python3 vantage.py context <entity_id>")
                raise SystemExit(1)
            result = context(rest[0])
        elif cmd == "query":
            if not rest:
                print("uso: python3 vantage.py query '<texto|entity_id>'")
                raise SystemExit(1)
            result = query(" ".join(rest))
        elif cmd == "status":
            result = status()
        elif cmd == "sync":
            result = sync()
        else:
            print(__doc__)
            raise SystemExit(1)

        print(json.dumps(result, indent=2, ensure_ascii=False))

    except ResolverError as exc:
        print(json.dumps({"status": exc.status, "error": exc.message}, ensure_ascii=False))
        raise SystemExit(1)


if __name__ == "__main__":
    _main()
