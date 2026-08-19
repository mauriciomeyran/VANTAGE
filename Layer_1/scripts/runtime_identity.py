"""
runtime_identity.py — VANTAGE Runtime Identity Contract
Módulo canónico para resolución de entity_prefix por tipo de entidad.

Cierra DT-014: Extract Runtime Identity Contract.
Antes: _load_entity_prefixes() vivía inline en generate_entity_index_v2.py.
Ahora: un único módulo con contrato explícito, consumible por cualquier
       componente del Runtime sin duplicar lógica.

Consumidores actuales:
  - generate_entity_index_v2.py  (Runtime Build)
  - lazy_loader.py               (resolución documental)

Invariantes (desde KERNEL:SCHEMA-004 / v2.4.0):
  - resolver_registry_v2.json es el único SSOT para entity_prefix.
  - entity_prefix NUNCA se hardcodea en ningún componente.
  - Prefijo ausente en el Registry → fallo explícito, nunca default silencioso.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Tipos
# ---------------------------------------------------------------------------
PrefixMap = dict[str, str]   # source_db_normalized → entity_prefix


# ---------------------------------------------------------------------------
# Carga desde Registry
# ---------------------------------------------------------------------------

def load_prefix_map(registry_path: Path | str) -> PrefixMap:
    """
    Lee resolver_registry_v2.json y devuelve el mapeo completo
    source_db (normalizado) → entity_prefix.

    Args:
        registry_path: Ruta al archivo resolver_registry_v2.json.

    Returns:
        Dict con todas las entradas válidas del Registry.
        Claves normalizadas: upper().replace(" ", "_").

    Raises:
        FileNotFoundError: si el Registry no existe en la ruta indicada.
        KeyError: si la sección 'data_sources' no existe en el JSON.
        ValueError: si el JSON está malformado.
    """
    path = Path(registry_path)
    if not path.exists():
        raise FileNotFoundError(
            f"[runtime_identity] resolver_registry_v2.json no encontrado: {path}"
        )

    try:
        registry: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"[runtime_identity] Registry malformado en {path}: {exc}"
        ) from exc

    data_sources = registry.get("data_sources")
    if data_sources is None:
        raise KeyError(
            f"[runtime_identity] Clave 'data_sources' ausente en {path}"
        )

    prefix_map: PrefixMap = {}
    for source_name, cfg in data_sources.items():
        prefix = str(cfg.get("entity_prefix", "")).strip()
        if not prefix:
            continue
        normalized = source_name.upper().replace(" ", "_")
        prefix_map[normalized] = prefix

    return prefix_map


def get_entity_prefix(source_db: str, registry_path: Path | str) -> str:
    """
    Devuelve el entity_prefix canónico para un tipo de entidad.

    Args:
        source_db:      Nombre del data source (ej. "VANTAGE_TRACKER").
                        Se normaliza internamente — mayúsculas/minúsculas y
                        espacios no importan.
        registry_path:  Ruta al resolver_registry_v2.json.

    Returns:
        String del prefijo canónico (ej. "TRACKER", "ARCHIVO").

    Raises:
        KeyError: si source_db no está registrado en el Registry.
                  Nunca retorna un default — fallo explícito por contrato.
        FileNotFoundError / ValueError: propagados desde load_prefix_map().
    """
    normalized = source_db.upper().replace(" ", "_")
    prefix_map = load_prefix_map(registry_path)

    if normalized not in prefix_map:
        registered = sorted(prefix_map.keys())
        raise KeyError(
            f"[runtime_identity] '{source_db}' no registrado en Registry. "
            f"Registrados: {registered}"
        )

    return prefix_map[normalized]


def get_authorized_prefixes(registry_path: Path | str) -> frozenset[str]:
    """
    Devuelve el conjunto de prefijos autorizados por el Registry.
    Consumible por lazy_loader.py como fuente única — reemplaza
    la constante AUTHORIZED_PREFIXES hardcodeada.

    Returns:
        frozenset de strings (ej. frozenset({"TRACKER", "ARCHIVO", "DRYRUN", "BUG"}))
    """
    prefix_map = load_prefix_map(registry_path)
    return frozenset(prefix_map.values())


def generate_entity_id(entity_prefix: str, page_id: str, hash_value: str) -> str:
    """
    Genera el entity_id canónico en formato PREFIX:H_<hash16> o PREFIX:U_<uuid>.
    Migrado desde generate_entity_index_v2.py para centralizar el contrato
    de formato de ID en un único lugar.

    Args:
        entity_prefix:  Prefijo canónico (obtenido vía get_entity_prefix()).
        page_id:        UUID de la página Notion.
        hash_value:     Hash del registro (puede ser string vacío).

    Returns:
        String en formato canónico (ej. "TRACKER:H_a1b2c3d4e5f60000").
    """
    if hash_value:
        return f"{entity_prefix}:H_{hash_value[:16]}"
    return f"{entity_prefix}:U_{page_id.replace('-', '')}"
