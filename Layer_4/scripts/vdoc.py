#!/usr/bin/env python3
"""
vdoc.py — VANTAGE L4 Document Layer Sync
==========================================
Wrapper que ejecuta vsync_doc.py + git_sync.py en un solo paso.
Flujo documental completo: Notion ↔ ACTIVE/ ↔ GitHub

Uso:
    vdoc notion     # Notion → local + commit
    vdoc local      # local → Notion + commit
    vdoc auto       # auto-detecta dirección
    vdoc dry        # preview sin escribir ni commitear
    vdoc kernel     # solo un documento
"""

import subprocess, sys
from pathlib import Path

PROJECT = Path.home() / "Documents/04-Vantage_CV"
VSYNC = PROJECT / "Layer_4/scripts/vsync_doc.py"
VGIT  = PROJECT / "Layer_4/scripts/git_sync.py"

def run(cmd, label=""):
    print(f"\n── {label} ──")
    r = subprocess.run([sys.executable] + cmd, cwd=str(PROJECT))
    return r.returncode

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return

    cmd = sys.argv[1]
    doc = sys.argv[2] if len(sys.argv) > 2 else None

    vsync_args = [str(VSYNC)]
    
    if cmd == "notion":
        vsync_args += ["--direction", "notion"]
    elif cmd == "local":
        vsync_args += ["--direction", "local"]
    elif cmd == "auto":
        vsync_args += ["--direction", "auto"]
    elif cmd == "dry":
        vsync_args += ["--dry-run"]
        run(vsync_args, "vsync_doc (preview)")
        return
    elif cmd in ("kernel","system_prompt","career_canon","manual","cheat_sheet"):
        vsync_args += ["--direction", "notion", "--doc", cmd]
    else:
        print(f"Comando no reconocido: {cmd}")
        return

    # Paso 1: sync
    rc = run(vsync_args, "vsync_doc (Notion ↔ ACTIVE)")
    if rc != 0:
        print("⚠️ vsync_doc tuvo error")
        return

    # Paso 2: commit
    vgit_args = [str(VGIT)]
    if cmd == "dry":
        vgit_args.append("--dry-run")
    run(vgit_args, "git_sync (ACTIVE → GitHub)")

if __name__ == "__main__":
    main()
