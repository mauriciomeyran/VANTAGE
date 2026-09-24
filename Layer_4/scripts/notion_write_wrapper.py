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
from typing import Optional, Dict, Any

# ── Paths L4 → L1 ────────────────────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).resolve()
_PROJECT = _SCRIPT_DIR.parents[2]  # VANTAGE
_TRIGGER_SCRIPT = _PROJECT / "Layer_4" / "scripts" / "trigger_sync_after_mcp_write.py"

# ── Documentos fundacionales (8) ──────────────────────────────────────────────
FOUNDATIONAL_DOCS = {
    "377938be-fc42-805e-a408-c9ae518d4fe7": "kernel",
    "37b938be-fc42-8001-9b9b-fcf81130d274": "system_prompt",
    "377938be-fc42-8089-93f2-f52dbd2dec6c": "career_canon",
    "372938be-fc42-8050-9a67-e40857d7806e": "manual",
    "37c938be-fc42-80d4-b9ae-f5969830331b": "aliases",
    "390938be-fc42-80e7-b429-d7d730339353": "change_log",
    "3a3938be-fc42-8008-9e90-ec435c01f50d": "brief",
    "3ba938be-fc42-8011-8947-fb4fa5d1f63f": "change_log_archivo",
}


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
    # TODO: Implementar la lógica real de escritura según el stack del proyecto
    # Esto podría ser:
    # - notion_client API calls
    # - MCP tool calls (notion-update-page, etc.)
    # - HTTP directo a Notion API
    
    # Por ahora, este es un stub que demuestra el patrón
    print(f"[NOTION WRITE] Escribiendo a página {page_id}")
    
    # Simular escritura exitosa
    write_success = True
    
    if write_success:
        # Disparar trigger de sync si es documento fundacional
        if page_id in FOUNDATIONAL_DOCS:
            print(f"[NOTION WRITE] Página fundacional detectada, disparando sync...")
            _trigger_sync(page_id)
        
        return {"success": True, "page_id": page_id}
    else:
        return {"success": False, "error": "Write failed"}


def _trigger_sync(page_id: str) -> None:
    """
    Dispara el trigger de sync de forma no-bloqueante.
    
    Args:
        page_id: ID de la página que fue modificada
    """
    try:
        # Ejecutar trigger_sync_after_mcp_write.py en background
        subprocess.Popen(
            [sys.executable, str(_TRIGGER_SCRIPT), page_id],
            cwd=str(_PROJECT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"[NOTION WRITE] Sync trigger iniciado para {page_id}")
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
        print(f"[TEST] ✓ Page_id es documento fundacional")
        print(f"[TEST] Disparando sync trigger...")
        _trigger_sync(test_page_id)
    else:
        print(f"[TEST] ✗ Page_id NO es documento fundacional")
