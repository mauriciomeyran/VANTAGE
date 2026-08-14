#!/usr/bin/env python3
"""
Convierte cada entrada del ARCHIVO CHANGELOG a encabezado desplegable
formato: # vX.Y.Z — Título {toggle="true"} + cuerpo indentado con tab.

Uso:
  export NOTION_TOKEN="secret_..."
  python toggle_changelog_archive.py --dry-run   # solo muestra plan
  python toggle_changelog_archive.py --apply     # escribe en Notion
"""

import os
import re
import argparse
from notion_client import Client

PAGE_ID = "39d938be-fc42-801c-94f6-f11bfe803633"  # ARCHIVO CHANGELOG

# Patrón de inicio de entrada (### / #### / ## / # seguido de vX.Y.Z)
ENTRY_START = re.compile(
    r"^(#{1,4})\s+(v\d+\.\d+\.\d+[^\n]*)$",
    re.MULTILINE,
)

def fetch_markdown(client: Client, page_id: str) -> str:
    """
    Nota: notion-client no devuelve el markdown enhanced directamente.
    Este script asume que exportas el contenido actual a un .md local
    o que usas el mismo pipeline que vsync/vsync_doc.

    Alternativa práctica en VANTAGE:
    1. Corre vsync o exporta ARCHIVO CHANGELOG a Documentación/ACTIVE/ o /tmp
    2. Pasa la ruta con --file
    """
    raise NotImplementedError(
        "Usa --file con un export markdown del Archivo (vía vsync / Terminal)."
    )


def convert_entries(md: str) -> str:
    lines = md.splitlines(keepends=True)
    out = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        m = re.match(r"^(#{1,4})\s+(v\d+\.\d+\.\d+.*)$", line.rstrip("\n"))
        if not m:
            out.append(line)
            i += 1
            continue

        # Inicio de entrada
        title = m.group(2).rstrip()
        # Si ya tiene {toggle="true"}, no tocar
        if '{toggle="true"}' in title or "{toggle='true'}" in title:
            out.append(line)
            i += 1
            # consumir cuerpo ya indentado hasta próximo heading de versión o fin
            while i < n:
                nxt = lines[i]
                if re.match(r"^#{1,4}\s+v\d+\.\d+\.\d+", nxt):
                    break
                out.append(nxt)
                i += 1
            continue

        # Nuevo heading toggle
        out.append(f'# {title} {{toggle="true"}}\n')
        i += 1

        # Cuerpo: indentar con tab hasta el siguiente entry-start o separador fuerte
        while i < n:
            nxt = lines[i]
            # Siguiente entrada de versión
            if re.match(r"^#{1,4}\s+v\d+\.\d+\.\d+", nxt):
                break
            # Nota final del archivo (blockquote histórico) — dejar fuera del toggle
            if nxt.startswith("> El histórico completo"):
                break
            # Línea vacía o contenido → indentar (excepto si ya viene con tab)
            raw = nxt.rstrip("\n")
            if raw == "":
                out.append("\t\n")
            elif raw.startswith("\t"):
                out.append(nxt)
            else:
                out.append("\t" + nxt if nxt.endswith("\n") else "\t" + nxt + "\n")
            i += 1

    return "".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, help="Ruta al .md exportado del ARCHIVO CHANGELOG")
    ap.add_argument("--out", default="/tmp/archivo_changelog_toggled.md")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true", help="Escribe el .md de salida (no pega a Notion solo)")
    args = ap.parse_args()

    with open(args.file, "r", encoding="utf-8") as f:
        original = f.read()

    converted = convert_entries(original)

    # Stats
    orig_entries = len(re.findall(r"^#{1,4}\s+v\d+\.\d+\.\d+", original, re.M))
    new_toggles = len(re.findall(r'\{toggle="true"\}', converted))
    print(f"Entradas detectadas: {orig_entries}")
    print(f"Toggles resultantes: {new_toggles}")

    if args.dry_run:
        # Muestra primeras 80 líneas del resultado
        print("\n--- preview (primeras 80 líneas) ---")
        print("\n".join(converted.splitlines()[:80]))
        print("...")
        return

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(converted)
    print(f"Escrito: {args.out}")
    print("Siguiente paso: revisa el .md y súbelo a Notion con tu flujo habitual")
    print("  (replace_content vía MCP, o vsync_doc / pipeline local que uses).")


if __name__ == "__main__":
    main()