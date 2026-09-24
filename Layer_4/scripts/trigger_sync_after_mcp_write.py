#!/usr/bin/env python3
"""
trigger_sync_after_mcp_write.py — VANTAGE L4
Wrapper para disparar sync Notion→local tras un write exitoso vía MCP a documentos fundacionales.

Este script está diseñado para ser invocado automáticamente por el sistema MCP o manualmente
por el operador después de un write MCP a cualquiera de los 8 documentos fundacionales:
- Kernel
- System Prompt
- Career Canon
- Manual
- Aliases
- Change Log

Uso:
    python3 trigger_sync_after_mcp_write.py <page_id>

Si el page_id corresponde a un documento fundacional, dispara vsync_doc.py --direction notion
para ese documento específicamente.
"""

import sys
import subprocess
from pathlib import Path

# ── Paths L4 → L1 ────────────────────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).resolve()
_PROJECT = _SCRIPT_DIR.parents[2]  # VANTAGE
_VSYNC_DOC = _PROJECT / "Layer_4" / "scripts" / "vsync_doc.py"

# ── Documentos fundacionales (8) ──────────────────────────────────────────────
# Actualizado para incluir todos los documentos en vsync_doc.py DOCS
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

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 trigger_sync_after_mcp_write.py <page_id>")
        print("Dispara vsync_doc.py --direction notion si el page_id es un documento fundacional.")
        sys.exit(1)

    page_id = sys.argv[1].strip()

    if page_id not in FOUNDATIONAL_DOCS:
        # No es un documento fundacional, no hacer nada
        sys.exit(0)

    doc_key = FOUNDATIONAL_DOCS[page_id]
    print(f"[MCP SYNC HOOK] Write detectado a documento fundacional: {doc_key}")
    print(f"[MCP SYNC HOOK] Disparando sync Notion→local (no-bloqueante)...")

    # Ejecutar vsync_doc.py --direction notion --doc <doc_key> en background
    # No-bloqueante: si el sync falla, loguear warning pero no abortar el write original
    try:
        process = subprocess.Popen(
            [sys.executable, str(_VSYNC_DOC), "--direction", "notion", "--doc", doc_key],
            cwd=str(_PROJECT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # No esperar a que termine - dejarlo correr en background
        print(f"[MCP SYNC HOOK] Sync iniciado en background para {doc_key}")
    except Exception as e:
        print(f"[MCP SYNC HOOK] Error iniciando sync para {doc_key}: {e}")
        # No abortar - el write original fue exitoso

if __name__ == "__main__":
    main()
