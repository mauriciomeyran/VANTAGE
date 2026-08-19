#!/usr/bin/env python3
"""
skill_to_md.py — Extrae el SKILL.md de uno o varios paquetes .skill (zip) a .md standalone.

Uso individual:
    python3 skill_to_md.py archivo.skill
    python3 skill_to_md.py archivo.skill -o salida.md

Uso batch (varios archivos):
    python3 skill_to_md.py a.skill b.skill c.skill
    python3 skill_to_md.py a.skill b.skill -d carpeta_salida/

Uso batch (carpeta completa, recursivo):
    python3 skill_to_md.py /ruta/a/carpeta_con_skills/
    python3 skill_to_md.py /ruta/a/carpeta/ -d carpeta_salida/

Un .skill es un zip con estructura:
    nombre-skill/
        SKILL.md
        references/...
        assets/...
"""

import argparse
import sys
import zipfile
from pathlib import Path


def extract_skill_md(skill_path: Path, output_path: Path) -> bool:
    if not zipfile.is_zipfile(skill_path):
        print(f"  x {skill_path.name}: no es un zip valido (.skill esperado)")
        return False

    with zipfile.ZipFile(skill_path) as zf:
        candidates = [n for n in zf.namelist() if Path(n).name == "SKILL.md"]

        if not candidates:
            print(f"  x {skill_path.name}: no contiene SKILL.md")
            return False
        if len(candidates) > 1:
            print(f"  ! {skill_path.name}: {len(candidates)} SKILL.md encontrados, usando {candidates[0]}")

        content = zf.read(candidates[0]).decode("utf-8")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(f"  ok {skill_path.name} -> {output_path} ({len(content)} bytes)")
    return True


def resolve_inputs(paths: list[Path]) -> list[Path]:
    """Expande carpetas a la lista de .skill que contienen (recursivo); deja archivos tal cual."""
    resolved = []
    for p in paths:
        if p.is_dir():
            found = sorted(p.rglob("*.skill"))
            if not found:
                print(f"Aviso: no se encontraron .skill dentro de {p}")
            resolved.extend(found)
        else:
            resolved.append(p)
    return resolved


def main() -> None:
    parser = argparse.ArgumentParser(description="Extrae SKILL.md de uno o varios paquetes .skill")
    parser.add_argument("inputs", nargs="+", type=Path,
                         help="Uno o mas archivos .skill, y/o carpetas (se buscan .skill recursivamente)")
    parser.add_argument("-o", "--output", type=Path, default=None,
                         help="Ruta de salida .md - solo valido con UN unico archivo de entrada")
    parser.add_argument("-d", "--out-dir", type=Path, default=None,
                         help="Carpeta de salida para modo batch (default: junto a cada .skill)")
    args = parser.parse_args()

    for p in args.inputs:
        if not p.exists():
            sys.exit(f"Error: no existe {p}")

    skill_files = resolve_inputs(args.inputs)

    if not skill_files:
        sys.exit("Error: no se encontro ningun .skill para procesar.")

    if args.output and len(skill_files) > 1:
        sys.exit("Error: -o/--output solo aplica cuando hay un unico .skill de entrada. Usa -d para batch.")

    print(f"Procesando {len(skill_files)} archivo(s)...")
    ok, fail = 0, 0
    for skill_path in skill_files:
        if args.output:
            out_path = args.output
        elif args.out_dir:
            out_path = args.out_dir / skill_path.with_suffix(".md").name
        else:
            out_path = skill_path.with_suffix(".md")

        if extract_skill_md(skill_path, out_path):
            ok += 1
        else:
            fail += 1

    print(f"\nListo: {ok} ok, {fail} con error.")


if __name__ == "__main__":
    main()
