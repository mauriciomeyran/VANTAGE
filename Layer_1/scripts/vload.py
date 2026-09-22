#!/usr/bin/env python3
"""
vload.py — VANTAGE vload command with UUID resolution from registry
Resuelve UUIDs desde resolver_registry_v2.json sin que el operador tenga que buscarlos manualmente.

Uso:
    vload --route KERNEL:SCHEMA              # Resuelve UUID automáticamente desde registry
    vload --page <UUID> --route KERNEL:SCHEMA # Comportamiento legacy (UUID explícito)
    vload --list                             # Lista todos los prefijos disponibles en registry

Referencia: §2.4, §1.1 (Handoff HO-000062 P4)
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Importar lazy_loader para reutilizar la lógica de fetch
sys.path.insert(0, str(Path(__file__).parent))
from lazy_loader import fetch_lazy_section, _parse_route

# ---------------------------------------------------------------------------
# Registry paths
# ---------------------------------------------------------------------------
_REGISTRY_DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "resolver_registry_v2.json"


def _load_document_registry(registry_path: Path | None = None) -> dict[str, str]:
    """
    Carga la sección document_registry de resolver_registry_v2.json.
    
    Retorna un dict mapeando PREFIX -> UUID.
    Si no puede cargar el registry, retorna dict vacío.
    """
    path = registry_path or _REGISTRY_DEFAULT_PATH
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
        doc_registry = registry.get("document_registry")
        if not doc_registry:
            print(f"[WARN] 'document_registry' ausente o vacío en {path}")
            return {}
        # Filtrar claves que empiezan con "_" (comentarios)
        return {k: v for k, v in doc_registry.items() if not k.startswith("_")}
    except FileNotFoundError:
        print(f"[WARN] Registry no encontrado en {path}")
        return {}
    except (json.JSONDecodeError, KeyError) as exc:
        print(f"[WARN] Error al leer registry: {exc}")
        return {}


def _resolve_uuid_from_prefix(prefix: str, registry: dict[str, str]) -> str | None:
    """
    Resuelve un UUID desde el prefix usando el document_registry.
    
    Args:
        prefix: Prefijo documental (ej. "KERNEL", "MANUAL")
        registry: Dict de PREFIX -> UUID del document_registry
    
    Returns:
        UUID si se encuentra, None si no
    """
    prefix_upper = prefix.strip().upper()
    return registry.get(prefix_upper)


def list_available_prefixes(registry_path: Path | None = None) -> None:
    """
    Imprime una tabla de prefijos disponibles en el document_registry.
    """
    registry = _load_document_registry(registry_path)
    if not registry:
        print("[ERROR] No se pudo cargar el document_registry")
        return
    
    print("Prefijos documentales disponibles en resolver_registry_v2.json:")
    print("-" * 60)
    for prefix, uuid in sorted(registry.items()):
        print(f"  {prefix:15} -> {uuid}")
    print("-" * 60)
    print(f"Total: {len(registry)} prefijos")


def main():
    parser = argparse.ArgumentParser(
        description="VANTAGE vload — fetch quirúrgico con resolución automática de UUID desde registry",
        epilog="Ejemplos:\n"
               "  vload --route KERNEL:SCHEMA              # Resuelve UUID automáticamente\n"
               "  vload --page <UUID> --route MANUAL:RUNTIME-002  # UUID explícito (legacy)\n"
               "  vload --list                             # Lista prefijos disponibles",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--page",
        help="Page ID de Notion (UUID con o sin dashes). Si se omite, se resuelve desde el registry usando el prefijo de --route."
    )
    parser.add_argument(
        "--route",
        required=False,  # No required cuando se usa --list
        help="Ruta canónica: PREFIX:CLAVE (ej. KERNEL:SCHEMA, MANUAL:RUNTIME-002). "
             "El prefijo se usa para resolver el UUID automáticamente si --page no se proporciona."
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Lista todos los prefijos disponibles en el document_registry y sale."
    )
    parser.add_argument(
        "--registry",
        help="Path alternativo a resolver_registry_v2.json (default: Layer_1/data/resolver_registry_v2.json)"
    )
    
    args = parser.parse_args()
    
    # Modo --list
    if args.list:
        registry_path = Path(args.registry) if args.registry else None
        list_available_prefixes(registry_path)
        return
    
    # Validar que --route esté presente cuando no es --list
    if not args.route:
        parser.error("--route es requerido (excepto en modo --list)")
    
    # Cargar registry para resolución de UUID
    registry_path = Path(args.registry) if args.registry else None
    registry = _load_document_registry(registry_path)
    
    # Determinar page_id
    page_id = args.page
    if not page_id:
        # Resolver desde registry usando el prefijo de la ruta
        prefix, clave = _parse_route(args.route, registry_path)
        if prefix:
            resolved_uuid = _resolve_uuid_from_prefix(prefix, registry)
            if resolved_uuid:
                page_id = resolved_uuid
                print(f"[INFO] UUID resuelto desde registry: {prefix} -> {page_id}")
            else:
                print(f"[ERROR] Prefijo '{prefix}' no encontrado en document_registry")
                print(f"[INFO] Prefijos disponibles: {', '.join(sorted(registry.keys()))}")
                print(f"[INFO] Usa --list para ver todos los prefijos o --page <UUID> para especificar UUID explícitamente")
                sys.exit(1)
        else:
            print(f"[ERROR] No se pudo extraer prefijo de la ruta '{args.route}'")
            print(f"[INFO] La ruta debe tener formato PREFIX:CLAVE (ej. KERNEL:SCHEMA)")
            print(f"[INFO] Usa --page <UUID> para especificar UUID explícitamente")
            sys.exit(1)
    
    # Ejecutar fetch usando lazy_loader
    result = fetch_lazy_section(page_id, args.route)
    print(result)


if __name__ == "__main__":
    main()