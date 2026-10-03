#!/usr/bin/env python3
"""
trigger_sync_after_mcp_write.py — VANTAGE L4
Wrapper para disparar sync Notion→local tras un write exitoso vía MCP a documentos fundacionales.

Este script está diseñado para ser invocado automáticamente por el sistema MCP o manualmente
por el operador después de un write MCP a un documento registrado en
FOUNDATIONAL_DOCS.

Uso:
    python3 trigger_sync_after_mcp_write.py <page_id>

Si el page_id corresponde a un documento fundacional, dispara vsync_doc.py --direction notion
para ese documento específicamente.
"""

import subprocess
import sys
from pathlib import Path

# ── Paths L4 → L1 ────────────────────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).resolve()
_PROJECT = _SCRIPT_DIR.parents[2]  # VANTAGE
_VSYNC_DOC = _PROJECT / "Layer_4" / "scripts" / "vsync_doc.py"

if str(_SCRIPT_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR.parent))

from foundational_docs import FOUNDATIONAL_DOCS, mcp_sync_log_path  # noqa: E402

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
    print("[MCP SYNC HOOK] Disparando sync Notion→local (no-bloqueante)...")

    # Ejecutar vsync_doc.py --direction notion --doc <doc_key> en background.
    # No-bloqueante: si el sync falla, se registra en el log y NO se aborta el write.
    #
    # IMPORTANTE (fix B1): el hijo NO debe heredar PIPE. Antes se lanzaba con
    # stdout=PIPE/stderr=PIPE y el padre terminaba de inmediato sin leer: en cuanto
    # el sync escribía su primer print, moría con BrokenPipeError y el sync
    # post-MCP nunca se completaba. Ahora escribe a un log en disco.
    log_path = mcp_sync_log_path()
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as log:
            subprocess.Popen(
                [sys.executable, str(_VSYNC_DOC), "--direction", "notion", "--doc", doc_key],
                cwd=str(_PROJECT),
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
                start_new_session=True,
            )
        print(f"[MCP SYNC HOOK] Sync iniciado en background para {doc_key} (log: {log_path})")
    except Exception as e:
        print(f"[MCP SYNC HOOK] Error iniciando sync para {doc_key}: {e}")
        # No abortar - el write original fue exitoso

if __name__ == "__main__":
    main()
