#!/usr/bin/env python3
"""
notion_write_wrapper.py — VANTAGE L4
Wrapper central para escrituras a Notion con trigger automático de sync.

Este wrapper está diseñado para ser usado por scripts internos del repo que
necesiten escribir a documentos fundacionales en Notion. Después de un write
exitoso, dispara automáticamente el sync Notion→local.

Uso:
    from notion_write_wrapper import write_to_notion_page
    
    result = write_to_notion_page(page_id, content)
    # Si el page_id es fundacional, el sync se dispara automáticamente
"""

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

# ── Paths L4 → L1 ────────────────────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).resolve()
_PROJECT = _SCRIPT_DIR.parents[2]  # VANTAGE
_TRIGGER_SCRIPT = _PROJECT / "Layer_4" / "scripts" / "trigger_sync_after_mcp_write.py"

if str(_SCRIPT_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR.parent))

# Fuente única del mapeo (ver foundational_docs.py). Se re-exporta el nombre
# para no romper imports existentes de este módulo.
from foundational_docs import FOUNDATIONAL_DOCS, mcp_sync_log_path  # noqa: E402,F401


def write_to_notion_page(page_id: str, content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wrapper para escritura a Notion con trigger automático de sync.
    
    Este es un wrapper stub - la implementación real debe usar el cliente
    Notion API o MCP según la configuración del proyecto.
    
    Args:
        page_id: ID de la página Notion
        content: Contenido a escribir (formato según API/MCP usado)
    
    Returns:
        Dict con resultado de la escritura
    
    Example:
        # Para scripts internos que usan notion_client directamente:
        from notion_client import Client
        from notion_write_wrapper import write_to_notion_page
        
        notion = Client(auth=token)
        result = write_to_notion_page(page_id, {"properties": {...}, "children": [...]})
    """
    # NO implementado a propósito (fix B10): antes esta función simulaba una
    # escritura exitosa (write_success = True) y devolvía {"success": True} sin
    # tocar Notion — un success falso que además disparaba un sync del contenido
    # viejo si la página era fundacional. Hasta que exista la implementación real,
    # falla rápido.
    # Implementación pendiente (una de estas):
    # - notion_client API calls
    # - MCP tool calls (notion-update-page, etc.)
    # - HTTP directo a Notion API
    raise NotImplementedError(
        "notion_write_wrapper.write_to_notion_page() es un stub: la escritura real "
        "a Notion no está implementada. No reportar éxito sin escritura "
        "(ver MCP_SYNC_HOOK_README.md, sección notion_write_wrapper)."
    )


def _trigger_sync(page_id: str) -> None:
    """
    Dispara el trigger de sync de forma no-bloqueante.
    
    Args:
        page_id: ID de la página que fue modificada
    """
    try:
        # Ejecutar trigger_sync_after_mcp_write.py en background.
        # Fix B1: el hijo escribe a un log, NO a un PIPE que nadie lee (moría con
        # BrokenPipeError en cuanto imprimía su primera línea).
        log_path = mcp_sync_log_path()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as log:
            subprocess.Popen(
                [sys.executable, str(_TRIGGER_SCRIPT), page_id],
                cwd=str(_PROJECT),
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
                start_new_session=True,
            )
        print(f"[NOTION WRITE] Sync trigger iniciado para {page_id} (log: {log_path})")
    except Exception as e:
        print(f"[NOTION WRITE] Error iniciando sync trigger: {e}")
        # No abortar - el write fue exitoso


def is_foundational_doc(page_id: str) -> bool:
    """
    Verifica si un page_id corresponde a un documento fundacional.
    
    Args:
        page_id: ID de la página Notion
    
    Returns:
        True si es fundacional, False otherwise
    """
    return page_id in FOUNDATIONAL_DOCS


if __name__ == "__main__":
    # Test manual del wrapper
    if len(sys.argv) < 2:
        print("Uso: python notion_write_wrapper.py <page_id>")
        print("Test: verifica si el page_id es fundacional y dispara sync trigger.")
        sys.exit(1)
    
    test_page_id = sys.argv[1]
    print(f"[TEST] Verificando page_id: {test_page_id}")
    
    if is_foundational_doc(test_page_id):
        print("[TEST] ✓ Page_id es documento fundacional")
        print("[TEST] Disparando sync trigger...")
        _trigger_sync(test_page_id)
    else:
        print("[TEST] ✗ Page_id NO es documento fundacional")
