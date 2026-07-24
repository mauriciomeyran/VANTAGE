#!/usr/bin/env python3
"""
vdoc.py — VANTAGE L4 Document Layer Sync
==========================================
Wrapper que ejecuta vsync_doc.py + git_sync.py en un solo paso.
Flujo documental completo: Notion ↔ ACTIVE/ ↔ GitHub

Los argumentos son independientes de orden y combinables:
    vdoc dry                    # preview auto, sin escribir ni commitear
    vdoc notion                 # Notion → local + commit (FORZADO — pide confirmación)
    vdoc local                  # local → Notion + commit (FORZADO — pide confirmación)
    vdoc auto                   # auto-detecta dirección (gana el más reciente)
    vdoc notion dry             # preview de lo que haría 'vdoc notion', sin escribir
    vdoc local dry              # preview de lo que haría 'vdoc local', sin escribir
    vdoc kernel                 # solo Kernel (auto)
    vdoc brief                 # solo Brief (auto)
    vdoc kernel dry             # preview de solo Kernel (auto)
    vdoc notion kernel          # solo Kernel, forzado notion→local (pide confirmación)
    vdoc system_prompt   |  vdoc career_canon  |  vdoc manual
    vdoc aliases          |  vdoc change_log
    vdoc Navigation_Brief |  vdoc VANTAGE

Nota: ID Census no es un doc soportado aquí — se genera vía generate-census
y se sube directo a Notion, no vive en ACTIVE/ ni se respalda por este flujo.

Nota: 'dry' es un modificador — se puede combinar con cualquier comando de
arriba y SIEMPRE gana: nunca escribe en Notion, local ni GitHub sin importar
qué más se haya pasado en la misma línea.
"""

import subprocess, sys
from pathlib import Path

PROJECT = Path.home() / "Documents/03 Projects/VANTAGE"
VSYNC = PROJECT / "Layer_4/scripts/vsync_doc.py"
VGIT  = PROJECT / "Layer_4/scripts/git_sync.py"

# Nota (CENSUS-SYNC-R1): ID Census queda fuera de este set a propósito — se
# genera vía generate-census y se sube directo a Notion; no tiene contraparte
# en ACTIVE/ ni tiene sentido respaldarlo por este flujo.
DOCS = {"kernel", "system_prompt", "career_canon", "manual", "aliases", "change_log", "Navigation_Brief", "VANTAGE"}
DIRECTIONS = {"notion", "local", "auto"}

def run(cmd, label=""):
    print(f"\n── {label} ──")
    r = subprocess.run([sys.executable] + cmd, cwd=str(PROJECT))
    return r.returncode

def main():
    raw_args = sys.argv[1:]

    if not raw_args or raw_args[0] in ("-h", "--help"):
        print(__doc__)
        return

    # 'dry' es un modificador global — se detecta y se retira de los args,
    # sin importar en qué posición venga.
    dry_flag = "dry" in raw_args
    args = [a for a in raw_args if a != "dry"]

    direction = None
    doc = None
    for a in args:
        if a in DIRECTIONS:
            if direction is not None:
                print(f"Dirección duplicada/ambigua: '{direction}' y '{a}'")
                return
            direction = a
        elif a in DOCS:
            if doc is not None:
                print(f"Doc duplicado/ambiguo: '{doc}' y '{a}'")
                return
            doc = a
        else:
            print(f"Comando no reconocido: '{a}'")
            print(__doc__)
            return

    # 'vdoc kernel' sin dirección explícita → auto (comportamiento histórico)
    # 'vdoc dry' sin nada más → auto dry
    if direction is None:
        direction = "auto"

    vsync_args = [str(VSYNC), "--direction", direction]
    if doc:
        vsync_args += ["--doc", doc]

    # dry SIEMPRE gana — nunca se pasa a escritura real, sin importar
    # qué dirección o doc se haya combinado en la misma línea.
    if dry_flag:
        vsync_args += ["--dry-run"]
        run(vsync_args, "vsync_doc (preview)")
        return

    forced = direction in ("notion", "local")

    # Confirmación obligatoria para dirección forzada (notion/local explícitos)
    # EXCEPCIÓN TEMPORAL: dirección local no requiere confirmación (push de hipervínculos)
    if forced and direction != "local":
        preview_args = vsync_args + ["--dry-run"]
        run(preview_args, "vsync_doc (preview — dirección forzada)")
        print("\n⚠️  Esta operación sobreescribe sin comparar fecha de modificación.")
        print("   Usa 'vdoc auto' si quieres que gane el más reciente.")
        try:
            confirm = input("   Confirmar escritura forzada [s/N]: ").strip().lower()
        except EOFError:
            # Sin TTY interactivo — fallar seguro, nunca asumir confirmación.
            print("\n   Sin entrada interactiva disponible — cancelado por seguridad.")
            print("   No se escribió nada.")
            return
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
