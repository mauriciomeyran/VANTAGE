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
    vdoc Navigation_Brief
    vdoc project_charter  |  vdoc charter

Nota: 'VANTAGE' ya no es un doc válido: se anunciaba aquí pero vsync_doc.py
nunca lo aceptó en --doc (exit 2 con "invalid choice"). Usa las keys de arriba.

Nota: ID Census no es un doc soportado aquí — se genera vía generate-census
y se sube directo a Notion, no vive en ACTIVE/ ni se respalda por este flujo.

Nota: 'dry' es un modificador — se puede combinar con cualquier comando de
arriba y SIEMPRE gana: nunca escribe en Notion, local ni GitHub sin importar
qué más se haya pasado en la misma línea.
"""

import os, subprocess, sys
from pathlib import Path

# Derivado del propio archivo (Layer_4/scripts/vdoc.py → VANTAGE), no de
# ~/Documents/... hardcodeado: así el wrapper es portable.
PROJECT = Path(__file__).resolve().parents[2]
VSYNC = PROJECT / "Layer_4/scripts/vsync_doc.py"
VGIT  = PROJECT / "Layer_4/scripts/git_sync.py"

# Nota (CENSUS-SYNC-R1): ID Census queda fuera de este set a propósito — se
# genera vía generate-census y se sube directo a Notion; no tiene contraparte
# en ACTIVE/ ni tiene sentido respaldarlo por este flujo.
DOCS = {"kernel", "system_prompt", "career_canon", "manual", "aliases", "change_log", "Navigation_Brief", "change_log_archivo", "project_charter", "charter"}
# Alias → key canónica en vsync_doc.DOCS
DOC_ALIASES = {
    "charter": "project_charter",
    "Navigation_Brief": "brief",  # histórico: vdoc acepta Navigation_Brief; vsync usa "brief"
}
DIRECTIONS = {"notion", "auto", "local"}

def run(cmd, label=""):
    print(f"\n── {label} ──")
    r = subprocess.run([sys.executable] + cmd, cwd=str(PROJECT),
                       env={**os.environ, "VDOC_WRAPPER": "1"})
    return r.returncode

def main() -> int:
    """Retorna el exit code: 0 OK/cancelado por el usuario, != 0 error real.

    Antes todos los caminos terminaban en un `return` pelado (None → exit 0),
    incluso "comando no reconocido" o un fallo de vsync_doc: cualquier wrapper
    o cron que leyera el exit code veía éxito siempre.
    """
    raw_args = sys.argv[1:]

    if not raw_args or raw_args[0] in ("-h", "--help"):
        print(__doc__)
        return 0

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
                return 1
            direction = a
        elif a in DOCS:
            if doc is not None:
                print(f"Doc duplicado/ambiguo: '{doc}' y '{a}'")
                return 1
            doc = a
        else:
            print(f"Comando no reconocido: '{a}'")
            print(__doc__)
            return 1

    # 'vdoc kernel' sin dirección explícita → auto (comportamiento histórico)
    # 'vdoc dry' sin nada más → auto dry
    if direction is None:
        direction = "auto"

    vsync_args = [str(VSYNC), "--direction", direction]
    if doc:
        # Resolver alias a la key canónica que entiende vsync_doc.DOCS
        doc_key = DOC_ALIASES.get(doc, doc)
        vsync_args += ["--doc", doc_key]

    # dry SIEMPRE gana — nunca se pasa a escritura real, sin importar
    # qué dirección o doc se haya combinado en la misma línea.
    if dry_flag:
        vsync_args += ["--dry-run"]
        return run(vsync_args, "vsync_doc (preview)")

    forced = direction in ("notion", "local")

    # R-02 fix: la excepción temporal dejaba que 'vdoc local' se saltara la
    # confirmación que su propio docstring (l.11: "FORZADO — pide
    # confirmación") promete — justo la dirección que borra bloques en
    # Notion sin comparar fecha de modificación. Confirmación obligatoria
    # para ambas direcciones forzadas, sin excepción.
    if forced:
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
            return 0
        if confirm != "s":
            print("   Cancelado. No se escribió nada.")
            return 0

    # Paso 1: sync
    rc = run(vsync_args, "vsync_doc (Notion ↔ ACTIVE)")
    if rc != 0:
        print("⚠️ vsync_doc tuvo error")
        return rc

    # Paso 2: commit
    vgit_args = [str(VGIT)]
    return run(vgit_args, "git_sync (ACTIVE → GitHub)")

if __name__ == "__main__":
    sys.exit(main())
