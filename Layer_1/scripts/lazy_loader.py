"""
lazy_loader.py — VANTAGE Lazy Loader v2
Fetch quirúrgico de secciones del Kernel (y documentos fundacionales) por ruta DOC:CLAVE.

Cambios respecto a v1:
  - Soporte multi-prefijo: KERNEL, MANUAL, CANON, TRACKER (contrato v8.9.0)
  - Strip genérico de prefijo antes de matching (no solo KERNEL:)
  - Matcher de inicio: busca PREFIX:CLAVE O solo CLAVE en texto del heading
  - Stop-signal corregido: cualquier heading de igual/mayor jerarquía sin la clave activa
  - just_started inicializado antes del loop (fix de NameError latente)
  - Retry con backoff simple (3 intentos, 1s / 2s) en ambas funciones fetch
  - Importable como módulo sin side-effects (load_dotenv solo en __main__)
"""

import os
import time
import requests
import argparse
from pathlib import Path

# ---------------------------------------------------------------------------
# Contrato de prefijos autorizados — cargado desde resolver_registry_v2.json
# via runtime_identity (DT-014). No hardcodeado.
# ---------------------------------------------------------------------------
_REGISTRY_DEFAULT_PATH = Path(__file__).resolve().parent / "resolver_registry_v2.json"
_authorized_prefixes_cache: frozenset[str] | None = None


def _get_authorized_prefixes(registry_path: Path | None = None) -> frozenset[str]:
    """
    Devuelve el conjunto de prefijos autorizados.
    Carga desde resolver_registry_v2.json vía runtime_identity si está disponible.
    Fallback a conjunto estático si el módulo o el Registry no son accesibles
    (compatibilidad en entornos sin Runtime Build completo).
    """
    global _authorized_prefixes_cache
    if _authorized_prefixes_cache is not None:
        return _authorized_prefixes_cache

    path = registry_path or _REGISTRY_DEFAULT_PATH
    try:
        from runtime_identity import get_authorized_prefixes
        _authorized_prefixes_cache = get_authorized_prefixes(path)
    except Exception:
        # Fallback estático — prefijos del contrato v8.9.0
        _authorized_prefixes_cache = frozenset({"KERNEL", "MANUAL", "CANON", "TRACKER"})

    return _authorized_prefixes_cache

# ---------------------------------------------------------------------------
# Tipos de bloque con texto extraíble
# ---------------------------------------------------------------------------
TEXT_BLOCK_TYPES = {
    "paragraph",
    "heading_1",
    "heading_2",
    "heading_3",
    "bulleted_list_item",
    "numbered_list_item",
    "code",
    "quote",
    "callout",
    "toggle",
}

HEADING_TYPES = {"heading_1", "heading_2", "heading_3"}

# Jerarquía para comparar nivel de heading (menor número = mayor jerarquía)
HEADING_LEVEL = {"heading_1": 1, "heading_2": 2, "heading_3": 3}

# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _extract_text(block: dict) -> str:
    """Extrae plain_text de un bloque Notion."""
    btype = block.get("type", "")
    if btype not in TEXT_BLOCK_TYPES:
        return ""
    rich_text = block.get(btype, {}).get("rich_text", [])
    return "".join(rt.get("plain_text", "") for rt in rich_text)


def _parse_route(route: str, registry_path: Path | None = None) -> tuple[str, str]:
    """
    Parsea 'PREFIX:CLAVE' → (PREFIX, CLAVE).
    Si no hay prefijo reconocido, retorna ("", route) para compatibilidad legacy.
    Emite warning si el prefijo no está en el Registry.
    Los prefijos autorizados se cargan desde resolver_registry_v2.json vía
    runtime_identity — no hardcodeados (DT-014).
    """
    if ":" in route:
        prefix, clave = route.split(":", 1)
        prefix_upper = prefix.strip().upper()
        authorized = _get_authorized_prefixes(registry_path)
        if prefix_upper in authorized:
            return prefix_upper, clave.strip()
        else:
            print(f"[WARN] Prefijo '{prefix}' no registrado en Registry {authorized}. "
                  f"Continuando como ruta legacy.")
            return "", route.strip()
    return "", route.strip()


def _notion_get(url: str, headers: dict, params: dict, retries: int = 3) -> dict | None:
    """
    GET a la API de Notion con retry y backoff simple.
    Retorna el JSON parseado o None si todos los intentos fallan.
    """
    delays = [0, 1, 2]
    for attempt in range(retries):
        if delays[attempt]:
            time.sleep(delays[attempt])
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=15)
        except requests.RequestException as exc:
            print(f"[WARN] Request exception (intento {attempt + 1}/{retries}): {exc}")
            continue
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code in (429, 500, 502, 503):
            print(f"[WARN] HTTP {resp.status_code} (intento {attempt + 1}/{retries}) — reintentando...")
            continue
        # Error no retriable
        print(f"[ERROR] API Notion: {resp.status_code} — {resp.text[:200]}")
        return None
    print(f"[ERROR] Todos los reintentos agotados para {url}")
    return None


# ---------------------------------------------------------------------------
# Fetch recursivo de hijos
# ---------------------------------------------------------------------------

def fetch_block_children_recursive(block_id: str, headers: dict, depth: int = 0) -> list[str]:
    """Obtiene recursivamente el texto de bloques hijos (sub-bullets, toggles, etc.)."""
    lines = []
    url = f"https://api.notion.com/v1/blocks/{block_id}/children"
    next_cursor = None
    has_more = True

    while has_more:
        params = {"page_size": 100}
        if next_cursor:
            params["start_cursor"] = next_cursor

        data = _notion_get(url, headers, params)
        if data is None:
            break

        for child in data.get("results", []):
            text = _extract_text(child)
            if text:
                prefix = "  " * (depth + 1) + "- "
                lines.append(f"{prefix}{text}")
            if child.get("has_children"):
                lines.extend(fetch_block_children_recursive(child["id"], headers, depth + 1))

        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor")

    return lines


# ---------------------------------------------------------------------------
# Fetch principal
# ---------------------------------------------------------------------------

def fetch_lazy_section(page_id: str, route: str, api_key: str | None = None) -> str:
    """
    Fetch quirúrgico de una sección de un documento Notion.

    Args:
        page_id:  UUID de la página Notion (sin dashes o con dashes).
        route:    Ruta en formato 'PREFIX:CLAVE' (ej. 'KERNEL:SCHEMA') o legacy.
        api_key:  Token de Notion. Si None, lee de env NOTION_TOKEN / NOTION_API_KEY.

    Returns:
        Texto plano de la sección, o string de error prefijado con 'ERROR:'.
    """
    # --- Resolver API key ---
    if not api_key:
        api_key = os.getenv("NOTION_TOKEN") or os.getenv("NOTION_API_KEY")
    if not api_key:
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', 'layer_1.env')
        return f"ERROR: NOTION_TOKEN no encontrado. Verifica {env_path}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28",
    }

    # --- Parsear ruta ---
    prefix, clave = _parse_route(route)
    # Candidatos de match en orden de prioridad
    # Primero busca la forma canónica completa, luego solo la clave
    canonical_form = f"{prefix}:{clave}" if prefix else clave

    # --- Scan de bloques ---
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    has_more = True
    next_cursor = None

    capturing = False
    anchor_level: int = 3          # nivel del heading que abrió la sección
    just_started = False           # flag para el primer bloque tras el heading
    captured_blocks: list[str] = []

    while has_more:
        params = {"page_size": 100}
        if next_cursor:
            params["start_cursor"] = next_cursor

        data = _notion_get(url, headers, params)
        if data is None:
            return "ERROR: No se pudo conectar a la API de Notion."

        for block in data.get("results", []):
            btype = block.get("type", "")
            text_content = _extract_text(block)
            # Normalizar backticks para match (el Kernel los usa en IDs)
            text_normalized = text_content.replace("`", "").strip()

            is_heading = btype in HEADING_TYPES

            # ----------------------------------------------------------------
            # 1. Detectar inicio de sección
            # ----------------------------------------------------------------
            if is_heading and not capturing:
                # Match canónico (PREFIX:CLAVE) o solo clave
                if canonical_form in text_normalized or (clave and clave in text_normalized):
                    capturing = True
                    just_started = True
                    anchor_level = HEADING_LEVEL.get(btype, 3)
                    captured_blocks.append(f"## {text_content}")
                    continue

            # ----------------------------------------------------------------
            # 2. Dentro de sección: capturar o cerrar
            # ----------------------------------------------------------------
            if capturing:
                # Cierre explícito por payload tag
                if "</payload>" in text_content:
                    capturing = False
                    break

                # Cierre por heading de igual o mayor jerarquía que no sea la sección activa
                if is_heading:
                    current_level = HEADING_LEVEL.get(btype, 3)
                    heading_has_clave = (clave and clave in text_normalized) or \
                                       (canonical_form in text_normalized)
                    if current_level <= anchor_level and not heading_has_clave:
                        if just_started:
                            # Primer bloque tras el heading abridor — no cerrar aún
                            just_started = False
                        else:
                            capturing = False
                            break

                captured_blocks.append(text_content)
                if block.get("has_children"):
                    captured_blocks.extend(fetch_block_children_recursive(block["id"], headers))
                just_started = False

        # Early exit si ya terminamos de capturar
        if not capturing and captured_blocks:
            break

        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor")

    if not captured_blocks:
        return f"ERROR: Ruta '{route}' no encontrada en página {page_id}."

    clean_text = (
        "\n".join(captured_blocks)
        .replace("<payload>", "")
        .replace("</payload>", "")
        .strip()
    )
    return clean_text


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from dotenv import load_dotenv

    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', 'layer_1.env')
    load_dotenv(env_path)

    parser = argparse.ArgumentParser(
        description="VANTAGE Lazy Loader v2 — fetch quirúrgico por ruta DOC:CLAVE"
    )
    parser.add_argument(
        "--page",
        required=True,
        help="Page ID de Notion (UUID con o sin dashes)",
    )
    parser.add_argument(
        "--route",
        required=True,
        help="Ruta canónica: PREFIX:CLAVE (ej. KERNEL:SCHEMA, MANUAL:TRIGGERS). "
             "También acepta rutas legacy sin prefijo.",
    )
    args = parser.parse_args()

    result = fetch_lazy_section(args.page, args.route)
    print(result)
