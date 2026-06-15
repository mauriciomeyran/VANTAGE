from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent
ENTITY_INDEX_PATH = BASE_DIR / "entity_index_v2.json"

# resolver_layer_v1 vive en otra carpeta (Layer_1/scripts) en tu setup real.
# Ajusta este import si query_layer.py no está junto a resolver_layer_v1.py.
try:
    from resolver_layer_v1 import resolve_entity as _resolver_resolve, ResolverError
except ImportError:
    _resolver_resolve = None
    ResolverError = Exception


_INDEX_CACHE: Optional[Dict[str, Any]] = None


def load_index(force_reload: bool = False) -> Dict[str, Any]:
    """Carga y cachea entity_index_v2.json en memoria."""
    global _INDEX_CACHE
    if _INDEX_CACHE is None or force_reload:
        _INDEX_CACHE = json.loads(ENTITY_INDEX_PATH.read_text())
    return _INDEX_CACHE


def _entities() -> List[Dict[str, Any]]:
    return load_index().get("entities", [])


def lookup_by_hash(hash_value: str) -> List[Dict[str, Any]]:
    """Busca por hash exacto. Puede haber múltiples matches (tracker + archive)."""
    return [e for e in _entities() if e.get("hash") == hash_value]


def find_entity(query: str) -> List[Dict[str, Any]]:
    """Busca por entity_id o canonical_id exacto."""
    return [
        e for e in _entities()
        if e.get("entity_id") == query or e.get("canonical_id") == query
    ]


def list_entities(
    source_db: Optional[str] = None,
    entity_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Lista entidades, opcionalmente filtradas por source_db y/o entity_type."""
    results = _entities()
    if source_db:
        results = [e for e in results if e.get("source_db") == source_db]
    if entity_type:
        results = [e for e in results if e.get("entity_type") == entity_type]
    return results


def search_entities(
    text: str,
    source_db: Optional[str] = None,
    entity_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Búsqueda libre de texto. Como entity_index_v2 no tiene campo "nombre"/"rol"
    explícito, el match de texto se hace contra page_url (que incluye el título
    legible, ej. ".../Country-Manager-Mexico-37f9...") y contra entity_id/canonical_id.
    """
    needle = text.lower().replace(" ", "-")
    results = []
    for e in _entities():
        haystack = " ".join([
            e.get("page_url", ""),
            e.get("entity_id", ""),
            e.get("canonical_id", ""),
        ]).lower()
        if needle in haystack:
            results.append(e)

    if source_db:
        results = [e for e in results if e.get("source_db") == source_db]
    if entity_type:
        results = [e for e in results if e.get("entity_type") == entity_type]
    return results


def lookup_by_role(role_text: str) -> List[Dict[str, Any]]:
    """
    NOTA: entity_index_v2 no trae un campo 'rol' independiente; el rol/título
    viene embebido en page_url (slug). Esta función es un alias de
    search_entities() sobre ese slug. Si en el futuro entity_index_v2 agrega
    un campo 'title' o 'rol' explícito, actualizar esta función para usarlo
    directo en lugar de parsear page_url.
    """
    return search_entities(role_text)


def resolve_entity(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wrapper directo sobre resolver_layer_v1.resolve_entity (Phase 3).
    payload: {"entity_id": "..."} o {"canonical_id": "..."}
    """
    if _resolver_resolve is None:
        raise RuntimeError(
            "resolver_layer_v1 no encontrado. Coloca query_layer.py en la misma "
            "carpeta que resolver_layer_v1.py, entity_index_v2.json y "
            "resolver_registry_v2.json, o ajusta el import al inicio de este archivo."
        )
    return _resolver_resolve(payload)


def query(value: str) -> Dict[str, Any]:
    """
    Entry point unificado. Acepta:
      - entity_id (ej. "TRACKER:H_xxxx")
      - canonical_id (hash largo)
      - texto libre (busca en page_url / ids)

    Devuelve un dict con el tipo de match y resultados.
    """
    # 1. match exacto por entity_id / canonical_id
    exact = find_entity(value)
    if exact:
        return {"query": value, "match_type": "exact", "count": len(exact), "results": exact}

    # 2. match exacto por hash
    by_hash = lookup_by_hash(value)
    if by_hash:
        return {"query": value, "match_type": "hash", "count": len(by_hash), "results": by_hash}

    # 3. fallback: texto libre
    text_results = search_entities(value)
    return {"query": value, "match_type": "text", "count": len(text_results), "results": text_results}


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("uso: python3 query_layer.py <texto|entity_id|canonical_id>")
        raise SystemExit(1)
    print(json.dumps(query(sys.argv[1]), indent=2, ensure_ascii=False))
