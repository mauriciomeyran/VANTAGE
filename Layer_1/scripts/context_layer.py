from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent

try:
    from query_layer import resolve_entity, find_entity
except ImportError:
    resolve_entity = None
    find_entity = None

try:
    from notion_utils import notion_get, ResolverError
except ImportError:
    raise RuntimeError("notion_utils.py no encontrado en la misma carpeta.")


# --- normalización de propiedades de Notion -> valores planos ---------------

def _flatten_rich_text(rich_text: List[Dict[str, Any]]) -> str:
    return "".join(t.get("plain_text", "") for t in rich_text)


def _flatten_property(prop: Dict[str, Any]) -> Any:
    ptype = prop.get("type")
    if ptype == "title":
        return _flatten_rich_text(prop.get("title", []))
    if ptype == "rich_text":
        return _flatten_rich_text(prop.get("rich_text", []))
    if ptype == "select":
        sel = prop.get("select")
        return sel.get("name") if sel else None
    if ptype == "multi_select":
        return [s.get("name") for s in prop.get("multi_select", [])]
    if ptype == "checkbox":
        return prop.get("checkbox")
    if ptype == "number":
        return prop.get("number")
    if ptype == "url":
        return prop.get("url")
    if ptype == "date":
        d = prop.get("date")
        return d.get("start") if d else None
    if ptype == "files":
        return [f.get("name") for f in prop.get("files", [])]
    if ptype == "created_time":
        return prop.get("created_time")
    if ptype == "people":
        return [p.get("name") for p in prop.get("people", [])]
    # fallback: devuelve el bloque crudo si no reconocemos el tipo
    return prop.get(ptype)


def _flatten_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
    return {name: _flatten_property(prop) for name, prop in properties.items()}


# --- llamadas a Notion --------------------------------------------------------

def _fetch_page(page_id: str) -> Dict[str, Any]:
    return notion_get(f"/v1/pages/{page_id}")


def _fetch_blocks(page_id: str, page_size: int = 100) -> List[Dict[str, Any]]:
    """Trae todos los bloques hijos de la página, paginando si hace falta."""
    blocks: List[Dict[str, Any]] = []
    cursor: Optional[str] = None
    while True:
        path = f"/v1/blocks/{page_id}/children?page_size={page_size}"
        if cursor:
            path += f"&start_cursor={cursor}"
        data = notion_get(path)
        blocks.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return blocks


def _flatten_block(block: Dict[str, Any]) -> Dict[str, Any]:
    btype = block.get("type")
    content = block.get(btype, {})
    text = ""
    if isinstance(content, dict) and "rich_text" in content:
        text = _flatten_rich_text(content.get("rich_text", []))
    return {"type": btype, "text": text}


# --- assembly principal --------------------------------------------------------

# Propiedad que se usa como "status" -- ajustar si el schema cambia.
STATUS_PROPERTY = "Status"
# Propiedades que se excluyen de "metadata" porque ya van en otros bloques.
_EXCLUDED_FROM_METADATA = {STATUS_PROPERTY, "Rol"}


def assemble_context(entity_id_or_payload) -> Dict[str, Any]:
    """
    entity_id
      -> resolver (Phase 3, vía query_layer.resolve_entity)
      -> notion page (properties + blocks)
      -> context package

    Acepta un string (entity_id/canonical_id) o un payload dict
    {"entity_id": ...} / {"canonical_id": ...}.

    Devuelve:
    {
      "entity": {...},   # entrada de entity_index_v2
      "status": ...,     # valor de la propiedad Status
      "metadata": {...}, # resto de propiedades normalizadas
      "content": [...]   # bloques de la página, normalizados
    }
    """
    if resolve_entity is None or find_entity is None:
        raise RuntimeError(
            "query_layer no encontrado. Coloca context_layer.py en la misma "
            "carpeta que query_layer.py, resolver_layer_v1.py, "
            "entity_index_v2.json y resolver_registry_v2.json."
        )

    payload = (
        entity_id_or_payload
        if isinstance(entity_id_or_payload, dict)
        else {"entity_id": entity_id_or_payload}
    )

    # 1. resolver -> confirma que la entidad existe y obtiene page_url
    resolved = resolve_entity(payload)

    # 2. obtener entity entry completa del index (para page_id)
    lookup_value = payload.get("entity_id") or payload.get("canonical_id")
    matches = find_entity(lookup_value)
    if not matches:
        raise ResolverError("unknown_entity", lookup_value)
    entity_entry = matches[0]
    page_id = entity_entry["page_id"]

    # 3. notion page -> properties
    page = _fetch_page(page_id)
    properties = page.get("properties", {})
    flat_props = _flatten_properties(properties)

    status_value = flat_props.get(STATUS_PROPERTY)
    metadata = {k: v for k, v in flat_props.items() if k not in _EXCLUDED_FROM_METADATA}
    metadata["resolved_page_url"] = resolved.get("page_url")
    metadata["source_db"] = resolved.get("source_db")

    # 4. content -> bloques de la página
    blocks = _fetch_blocks(page_id)
    content = [_flatten_block(b) for b in blocks]

    return {
        "entity": entity_entry,
        "status": status_value,
        "metadata": metadata,
        "content": content,
    }


if __name__ == "__main__":
    import sys
    import json as _json
    if len(sys.argv) < 2:
        print("uso: python3 context_layer.py <entity_id>")
        raise SystemExit(1)
    try:
        result = assemble_context(sys.argv[1])
        print(_json.dumps(result, indent=2, ensure_ascii=False))
    except ResolverError as exc:
        print(_json.dumps({"status": exc.status, "error": exc.message}, ensure_ascii=False))
        raise SystemExit(1)
