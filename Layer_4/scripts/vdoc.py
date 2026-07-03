#!/usr/bin/env python3
"""
vdoc.py — VANTAGE L4 Document Layer Sync
==========================================
Wrapper que ejecuta vsync_doc.py + git_sync.py en un solo paso.
Flujo documental completo: Notion ↔ ACTIVE/ ↔ GitHub

Uso:
    vdoc notion     # Notion → local + commit (FORZADO — pide confirmación)
    vdoc local      # local → Notion + commit (FORZADO — pide confirmación)
    vdoc auto       # auto-detecta dirección (gana el más reciente)
    vdoc dry        # preview sin escribir ni commitear
    vdoc kernel     # solo Kernel (auto)
    vdoc system_prompt   # solo System Prompt (auto)
    vdoc career_canon    # solo Career Canon (auto)
    vdoc manual          # solo Manual (auto)
    vdoc aliases         # solo Aliases (auto)
    vdoc change_log      # solo Change Log (auto)
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
    forced = False

    if cmd == "notion":
        vsync_args += ["--direction", "notion"]
        forced = True
    elif cmd == "local":
        vsync_args += ["--direction", "local"]
        forced = True
    elif cmd == "auto":
        vsync_args += ["--direction", "auto"]
    elif cmd == "dry":
        vsync_args += ["--dry-run"]
        run(vsync_args, "vsync_doc (preview)")
        return
    elif cmd in (
        "kernel",
        "system_prompt",
        "career_canon",
        "manual",
        "aliases",
        "change_log",
    ):
        vsync_args += ["--direction", "auto", "--doc", cmd]
    else:
        print(f"Comando no reconocido: {cmd}")
        return

    # Confirmación obligatoria para dirección forzada (notion/local explícitos)
    if forced:
        preview_args = vsync_args + ["--dry-run"]
        run(preview_args, "vsync_doc (preview — dirección forzada)")
        print("\n⚠️  Esta operación sobreescribe sin comparar fecha de modificación.")
        print("   Usa 'vdoc auto' si quieres que gane el más reciente.")
        confirm = input("   Confirmar escritura forzada [s/N]: ").strip().lower()
        if confirm != "s":
            print("   Cancelado. No se escribió nada.")
            return

    # Paso 1: sync
    rc = run(vsync_args, "vsync_doc (Notion ↔ ACTIVE)")
    if rc != 0:
        print("⚠️ vsync_doc tuvo error")
        return

    # Paso 2: commit
    vgit_args = [str(VGIT)]
    run(vgit_args, "git_sync (ACTIVE → GitHub)")

if __name__ == "__main__":
    main()
