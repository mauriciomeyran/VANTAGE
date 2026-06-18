from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

BASE_DIR = Path(__file__).resolve().parent
ENTITY_INDEX_PATH = BASE_DIR / "entity_index_v2.json"
RESOLVER_REGISTRY_PATH = BASE_DIR / "resolver_registry_v2.json"

class ResolverError(Exception):
    def __init__(self, status: str, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text())


def _normalize_input(payload: Dict[str, Any]) -> str:
    if payload.get("entity_id"):
        return str(payload["entity_id"])
    if payload.get("canonical_id"):
        return str(payload["canonical_id"])
    raise ResolverError("unknown_entity", "missing entity_id or canonical_id")


def _lookup_entity(index: Dict[str, Any], key: str) -> Dict[str, Any]:
    for row in index.get("entities", []):
        if row.get("entity_id") == key or row.get("canonical_id") == key:
            return row
    raise ResolverError("unknown_entity", key)


def _source_config(registry: Dict[str, Any], source_db: str) -> Dict[str, Any]:
    normalized = source_db.upper().replace(" ", "_")
    for name, cfg in registry.get("data_sources", {}).items():
        if name.upper().replace(" ", "_") == normalized:
            return cfg
    raise ResolverError("not_found", f"no registry mapping for {source_db}")


def _query_notion(data_source_id: str) -> list[Dict[str, Any]]:
    """Pagina data_sources/{id}/query completo — fix RID-02.

    Antes solo se tomaba el primer batch; con 384+ entidades en
    ARCHIVO_TRACKER, entidades fuera de la primera página devolvian
    not_found silenciosamente. Ahora se acumulan todos los resultados,
    respetando el throttle global de notion_client en cada request.
    """
    token = os.environ.get("NOTION_API_KEY") or os.environ.get("NOTION_TOKEN")
    if not token:
        raise ResolverError("notion_error", "missing notion api token")
    try:
        import requests
    except Exception as exc:
        raise ResolverError("notion_error", f"requests unavailable: {exc}")

    from notion_client import _throttle

    url = f"https://api.notion.com/v1/data_sources/{data_source_id}/query"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": os.environ.get("NOTION_VERSION", "2025-09-03"),
        "Content-Type": "application/json",
    }

    all_results: list[Dict[str, Any]] = []
    payload: Dict[str, Any] = {}
    while True:
        _throttle()
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code >= 400:
            raise ResolverError("notion_error", resp.text)
        data = resp.json()
        all_results.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        payload = {**payload, "start_cursor": data["next_cursor"]}
    return all_results


def resolve_entity(payload: Dict[str, Any]) -> Dict[str, Any]:
    index = _load_json(ENTITY_INDEX_PATH)
    registry = _load_json(RESOLVER_REGISTRY_PATH)
    key = _normalize_input(payload)
    row = _lookup_entity(index, key)
    source_db = row.get("source_db")
    if not source_db:
        raise ResolverError("not_found", key)
    cfg = _source_config(registry, source_db)
    data_source_id = cfg["data_source_id"]
    page_id = row.get("page_id")
    page_url = row.get("page_url")
    results = _query_notion(data_source_id)
    match = next((item for item in results if item.get("id") == page_id), None)
    if match is None:
        raise ResolverError("not_found", key)
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
