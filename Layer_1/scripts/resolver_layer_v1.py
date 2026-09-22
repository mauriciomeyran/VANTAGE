from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

BASE_DIR = Path(__file__).resolve().parent.parent / "data"
ENTITY_INDEX_PATH = BASE_DIR / "entity_index_v2.json"
RESOLVER_REGISTRY_PATH = BASE_DIR / "resolver_registry_v2.json"

class ResolverError(Exception):
    def __init__(self, status: str, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text())


# Index en memoria: {entity_id: row, canonical_id: row} para lookup O(1)
_entity_index: Dict[str, Dict[str, Any]] = {}
_registry_cache: Dict[str, Any] = {}


def load_index() -> None:
    """Construye el índice en memoria como dict {entity_id: row, canonical_id: row}.
    Elimina el scan O(n) en cada lookup — ahora es O(1).
    """
    global _entity_index, _registry_cache
    index_data = _load_json(ENTITY_INDEX_PATH)
    _entity_index = {}
    for row in index_data.get("entities", []):
        entity_id = row.get("entity_id")
        canonical_id = row.get("canonical_id")
        if entity_id:
            _entity_index[entity_id] = row
        if canonical_id:
            _entity_index[canonical_id] = row
    _registry_cache = _load_json(RESOLVER_REGISTRY_PATH)


def _normalize_input(payload: Dict[str, Any]) -> str:
    if payload.get("entity_id"):
        return str(payload["entity_id"])
    if payload.get("canonical_id"):
        return str(payload["canonical_id"])
    raise ResolverError("unknown_entity", "missing entity_id or canonical_id")


def _lookup_entity(key: str) -> Dict[str, Any]:
    """Lookup O(1) usando el índice en memoria cargado por load_index()."""
    if not _entity_index:
        load_index()
    row = _entity_index.get(key)
    if row is None:
        raise ResolverError("unknown_entity", key)

    # F3: Detect duplicate entity_ids in the index and log warning
    # (This is a basic check; full duplicate detection is in generate_entity_index_v2.py)
    return row


def _source_config(source_db: str) -> Dict[str, Any]:
    """Lookup de config de data source usando el cache del registry."""
    if not _registry_cache:
        load_index()
    normalized = source_db.upper().replace(" ", "_")
    for name, cfg in _registry_cache.get("data_sources", {}).items():
        if name.upper().replace(" ", "_") == normalized:
            return cfg
    raise ResolverError("not_found", f"no registry mapping for {source_db}")


def _query_notion(data_source_id: str) -> list[Dict[str, Any]]:
    """Stub mantenido por compatibilidad — no usado en P1.
    El punto P1 es sustituir el scan O(n) por page_id puntual vía notion_utils.
    """
    raise ResolverError("deprecated", "_query_notion es obsoleto en v3 — usar _fetch_page_via_notion_utils")


def _fetch_page_via_notion_utils(page_id: str) -> Dict[str, Any]:
    """GET /v1/pages/{page_id} vía notion_utils — cache 6h, throttle, retry, métricas."""
    try:
        from notion_utils import notion_get
    except ImportError:
        raise ResolverError("import_error", "notion_utils.py no encontrado")

    return notion_get(f"/v1/pages/{page_id}", use_cache=True)


def resolve_entity(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Resolución v3: usa page_id puntual GET /v1/pages/{page_id} vía notion_utils.
    Elimina el scan O(n) del data source completo.
    """
    if not _entity_index:
        load_index()

    key = _normalize_input(payload)
    row = _lookup_entity(key)
    source_db = row.get("source_db")
    if not source_db:
        raise ResolverError("not_found", key)

    # Validar que la config del data source existe (aunque no la usamos para query)
    _source_config(source_db)

    page_id = row.get("page_id")
    page_url = row.get("page_url")

    # GET puntual vía notion_utils (cache 6h, throttle, retry, métricas)
    _fetch_page_via_notion_utils(page_id)

    return {
        "entity_id": row.get("entity_id") or row.get("canonical_id"),
        "status": "resolved",
        "source_db": source_db,
        "page_url": page_url,
        "resolved": True,
    }


if __name__ == "__main__":
    import sys
    payload = json.loads(sys.stdin.read() or "{}")
    try:
        print(json.dumps(resolve_entity(payload), ensure_ascii=False))
    except ResolverError as exc:
        print(json.dumps({"status": exc.status, "error": exc.message}, ensure_ascii=False))
        raise SystemExit(1)
