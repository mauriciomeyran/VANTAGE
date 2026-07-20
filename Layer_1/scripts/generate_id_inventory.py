#!/usr/bin/env python3
"""
generate_id_inventory.py

Genera un inventario de referencias cruzadas de IDs del esquema VANTAGE
([PREFIX]:[KEY]) a partir de los .md locales en Layer_1/ACTIVE/ (o la
ruta que se indique).

Distinto del ID Census: el Census dice qué IDs existen y su estado
(Ok/Stub/huérfano). Este script dice DÓNDE vive cada ID (DEF) y DESDE
DÓNDE se le hace referencia (REF), con contexto de línea y sección,
y el conteo total de citas.

Uso:
    python3 generate_id_inventory.py --root /ruta/a/ACTIVE --out ./out

Salidas (en --out):
    inventario_ids_por_id.md   -> un bloque por ID, agrupando DEF + REFs
    inventario_ids.csv         -> tabla plana, una fila por ocurrencia
    inventario_huerfanos.md    -> IDs con REF pero sin DEF detectada
    inventario_historicos.md   -> IDs sin DEF citados solo en Change Log
    inventario_externos.md     -> IDs sin DEF que refieren a entidades
                                   fuera del universo .md (ej. DBs de Notion)

Diseño (ver notas de sesión 2026-07-20):
    - Patrón de ID: [A-Z][A-Z0-9_]*:[A-Z0-9][A-Z0-9-]*
      (mayúsculas/números/guiones/underscore, sin espacios). Evita
      falsos positivos de URLs, timestamps (ej. T00:00 se excluye
      explícitamente vía blocklist) y prosa libre.
    - DEF: la línea es un heading Markdown (empieza con '#') y el ID
      aparece dentro de ese heading (patrones: '## ID: X', '## `X`',
      '# X', 'ID: X' dentro de un heading). Solo la PRIMERA aparición
      de un ID en un heading de ese archivo cuenta como DEF; el resto
      de apariciones del mismo ID en headings subsecuentes del mismo
      archivo se registran como REF (para no inflar el conteo de DEF
      en documentos con secciones repetidas).
    - REF: cualquier otra aparición del ID en el cuerpo de texto,
      fuera de un heading que lo define.
    - Sección: el heading Markdown más reciente (cualquier nivel #-###)
      visto antes de la línea actual, dentro del mismo archivo.
    - No sigue symlinks. No sigue directorios ocultos (.git, etc).
    - No requiere red ni MCP: opera 100% sobre filesystem local.

Categorías de huérfanos (IDs con REF pero sin DEF detectada), ver
write_orphans() para el detalle de por qué existen tres categorías
separadas y no una sola BLOCKLIST:
    - real_orphans : requieren atención genuina (falta DEF o cita mal
                     escrita en un documento vivo).
    - historical   : solo citados en Change Log, bitácora inmutable que
                     documenta a propósito nombres de IDs ya corregidos.
    - external     : IDs reales y correctos que refieren a entidades
                     fuera del universo .md escaneado (ej. una DB de
                     Notion) y por diseño nunca tendrán DEF local.
                     Ver EXTERNAL_REFS. Confirmado sesión 2026-07-20
                     con el caso CANON:ARCHIVO-VANTAGE.
"""

import argparse
import csv
import re
import sys
from pathlib import Path
from collections import defaultdict, OrderedDict

# --- Configuración del patrón de ID -----------------------------------------

ID_PATTERN = re.compile(r'\b([A-Z][A-Z0-9_]*:[A-Z0-9][A-Z0-9-]*)\b')

# IDs que el patrón captura pero que sabemos NO son referencias reales del
# esquema documental (ruido de parseo: timestamps, placeholders genéricos,
# ejemplos de sintaxis dentro de la propia documentación). Ajustar según
# lo que se observe en la corrida real.
#
# IMPORTANTE: BLOCKLIST es SOLO para placeholders de sintaxis / ruido de
# parseo, nunca para IDs reales con contexto legítimo (histórico o externo).
# Para esos casos ver CHANGELOG_FILENAMES (dentro de write_orphans) y
# EXTERNAL_REFS respectivamente.
BLOCKLIST = {
    "T00:00",           # timestamp, no ID
    "PREFIX:NOMBRE-SECCION",   # placeholder de sintaxis, no ID real
    "PREFIX:KEY",              # placeholder de sintaxis
    "PREFIX:CLAVE",            # placeholder de sintaxis
    "PREFIX:H",                # placeholder truncado / ruido
    "PREFIX:U",                # placeholder truncado / ruido
    "ID:UUID",                 # ejemplo de sintaxis, no ID real
    "DOC:CLAVE",               # placeholder de sintaxis (ver KERNEL:DOC-CONTRACT)
    "MANUAL:SETUP",            # ejemplo de sintaxis en Kernel §DOC-CONTRACT
                               # ("ej. MANUAL:SETUP"), no referencia real a
                               # MANUAL:SETUP-001. Confirmado sesión 2026-07-20.
}

# IDs reales que refieren a entidades fuera del universo .md escaneado
# (típicamente, una DB de Notion sin equivalente en Markdown local).
# Nunca tendrán DEF detectable por este script, y eso es correcto por
# diseño — no son placeholders (no van en BLOCKLIST) ni errores
# históricos (no van en la categoría 'historical' de write_orphans).
EXTERNAL_REFS = {
    "CANON:ARCHIVO-VANTAGE",  # apunta a la DB de Notion "ARCHIVO VANTAGE"
                              # (Page ID 377938be-fc42-8092-9b52-f61e7bab3284
                              # en la Cédula Digital). Confirmado sesión 2026-07-20.
}

STANDALONE_ID_LINE_RE = re.compile(r'^\s*`?([A-Z][A-Z0-9_]*:[A-Z0-9][A-Z0-9-]*)`?\s*$')
HEADING_RE = re.compile(r'^(?:>\s*)*(#{1,6})\s*(.+?)\s*$')


def line_is_standalone_id(line: str):
    """
    Detecta el tercer patrón DEF real de VANTAGE: una línea que consiste
    ÚNICAMENTE en un ID (con o sin backticks), sin más texto. Patrón
    observado en Career Canon.md:

        ### CF01
        CANON:FACT-001
        ALDO Certification Year = 2014

    Aquí el heading Markdown real es el alias corto ('### CF01'), y el
    ID completo del esquema VANTAGE vive como línea suelta inmediatamente
    debajo, actuando como anchor de facto. No es prosa ni un heading —
    es una tercera categoría de DEF que heading_looks_like_def() no
    puede cubrir porque exige que la línea SEA un heading Markdown.

    Devuelve el ID encontrado (str) o None.
    """
    m = STANDALONE_ID_LINE_RE.match(line)
    return m.group(1) if m else None

def heading_looks_like_def(heading_text: str, id_found: str) -> bool:
    """
    Determina si, dentro de un heading, un ID capturado es su DEFINICIÓN.
    Cubre los formatos observados en la documentación real de VANTAGE:
      - '## ID: KERNEL:SCOPE'                              (ID al inicio)
      - '## `CANON:ACHIEVEMENTS-001`'                       (ID al inicio)
      - '## MANUAL:SETUP-001'                               (ID al inicio, a secas)
      - '## CANON:ACHIEVEMENTS-001 — H. ACHIEVEMENT LIBRARY' (ID al inicio + título)
      - '## 5. VANTAGE RUNTIME (...) · ID: MANUAL:VANTAGE-RUNTIME-001'
        (ID al FINAL, precedido de 'ID:', con numeral/título antes)
    Regla: el ID cuenta como DEF si:
      (a) es el primer token significativo del heading (permitiendo antes
          solo numeral de sección, backticks, o 'ID:'), o
      (b) va precedido inmediatamente por 'ID:' en cualquier posición del
          heading (cubre el patrón 'Título · ID: X' al final).
    Nota histórica: una versión anterior de esta función exigía que casi
    no quedara texto tras el ID, lo cual producía falsos huérfanos
    masivos (~70% de los IDs reales) porque no contemplaba el patrón
    'ID — título descriptivo'. Corregido en la corrida de 2026-07-20.
    """
    idx = heading_text.find(id_found)
    if idx == -1:
        return False

    # Caso (b): precedido inmediatamente por "ID:" (con espacios opcionales)
    prefix_immediate = heading_text[:idx]
    if re.search(r'ID:?\s*$', prefix_immediate, flags=re.IGNORECASE):
        return True

    # Caso (a): es el primer token significativo del heading completo
    prefix = re.sub(r'^[\d.\u00a7\s]+', '', prefix_immediate)  # numerales de sección
    prefix = re.sub(r'^(ID:?)\s*', '', prefix, flags=re.IGNORECASE)
    prefix = prefix.strip('`\u2013\u2014-:. \t')
    return prefix == ""


def iter_markdown_files(root: Path):
    """Itera .md bajo root, ignorando dirs ocultos y symlinks."""
    for path in sorted(root.rglob("*.md")):
        if path.is_symlink():
            continue
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        yield path


def extract_ids_from_line(line: str):
    """Devuelve lista de IDs válidos (no en blocklist) encontrados en la línea."""
    found = ID_PATTERN.findall(line)
    return [f for f in found if f not in BLOCKLIST]


def process_file(path: Path, root: Path):
    """
    Procesa un archivo .md y devuelve una lista de dicts:
    {id, kind, file, section, line_no, line_text}
    kind es 'DEF' o 'REF'.
    """
    rel_path = str(path.relative_to(root))
    occurrences = []
    current_section = "(sin sección)"
    seen_defs_in_file = set()
    prev_line_was_heading = False

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"  [WARN] No se pudo leer {rel_path}: {e}", file=sys.stderr)
        return occurrences

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.rstrip("\n")

        heading_match = HEADING_RE.match(line)
        if heading_match:
            current_section = heading_match.group(2)

        ids_in_line = extract_ids_from_line(line)
        if not ids_in_line:
            prev_line_was_heading = heading_match is not None
            continue

        is_heading = heading_match is not None
        # Patrón 3: línea que ES únicamente un ID (nada más), ubicada
        # justo después de un heading (típicamente un alias corto como
        # '### CF01'). Ver line_is_standalone_id() para el caso real.
        standalone_id = line_is_standalone_id(line)
        is_standalone_def_line = (
            standalone_id is not None
            and prev_line_was_heading
            and not is_heading
        )

        for id_found in ids_in_line:
            looks_like_def_heading = is_heading and heading_looks_like_def(
                heading_match.group(2), id_found
            )
            looks_like_def_standalone = (
                is_standalone_def_line and id_found == standalone_id
            )
            if (looks_like_def_heading or looks_like_def_standalone) and \
                    id_found not in seen_defs_in_file:
                kind = "DEF"
                seen_defs_in_file.add(id_found)
            else:
                kind = "REF"

            occurrences.append({
                "id": id_found,
                "kind": kind,
                "file": rel_path,
                "section": current_section,
                "line_no": line_no,
                "line_text": line.strip()[:200],
            })

        prev_line_was_heading = is_heading

    return occurrences


def build_inventory(root: Path):
    all_occurrences = []
    files = list(iter_markdown_files(root))
    if not files:
        print(f"[ERROR] No se encontraron archivos .md bajo {root}", file=sys.stderr)
        sys.exit(1)

    print(f"Escaneando {len(files)} archivos .md bajo {root} ...")
    for path in files:
        occs = process_file(path, root)
        all_occurrences.extend(occs)

    return all_occurrences


def write_csv(occurrences, out_path: Path):
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "kind", "file", "section", "line_no", "line_text"],
        )
        writer.writeheader()
        for occ in occurrences:
            writer.writerow(occ)


def write_markdown_by_id(occurrences, out_path: Path):
    by_id = defaultdict(list)
    for occ in occurrences:
        by_id[occ["id"]].append(occ)

    with out_path.open("w", encoding="utf-8") as f:
        f.write("# Inventario de Referencias Cruzadas de IDs\n\n")
        f.write(f"Total de IDs únicos: {len(by_id)}\n")
        f.write(f"Total de ocurrencias: {len(occurrences)}\n\n")
        f.write("---\n\n")

        for id_name in sorted(by_id.keys()):
            occs = by_id[id_name]
            defs = [o for o in occs if o["kind"] == "DEF"]
            refs = [o for o in occs if o["kind"] == "REF"]

            f.write(f"## `{id_name}`\n\n")
            f.write(f"**Conteo total:** {len(occs)} ({len(defs)} DEF, {len(refs)} REF)\n\n")

            f.write("**DEF (dónde vive)**\n")
            if defs:
                for d in defs:
                    f.write(f"- `{d['file']}` · L{d['line_no']} · sección: {d['section']}\n")
            else:
                f.write("- (ninguna — posible ID huérfano, ver inventario_huerfanos.md)\n")
            f.write("\n")

            f.write("**REF (desde dónde se cita)**\n")
            if refs:
                # Agrupar por archivo para legibilidad, con conteo por archivo
                by_file = defaultdict(list)
                for r in refs:
                    by_file[r["file"]].append(r)
                for file_name in sorted(by_file.keys()):
                    file_refs = by_file[file_name]
                    f.write(f"- `{file_name}` ({len(file_refs)}×): ")
                    lines_str = ", ".join(f"L{r['line_no']}" for r in file_refs)
                    f.write(f"{lines_str}\n")
            else:
                f.write("- (sin referencias — ID declarado pero no citado en ningún otro punto)\n")
            f.write("\n---\n\n")


def write_orphans(occurrences, out_path: Path, historical_path: Path, external_path: Path):
    """
    Escribe tres archivos separados:
      - out_path (inventario_huerfanos.md): IDs sin DEF que aparecen en
        al menos un documento VIVO (cualquiera que no sea Change Log.md)
        y que no están en EXTERNAL_REFS. Estos SÍ requieren atención —
        o falta la definición, o hay una cita incorrecta en un documento
        que se sigue usando activamente.
      - historical_path (inventario_historicos.md): IDs sin DEF cuyas
        ÚNICAS ocurrencias están en Change Log.md. El Change Log es una
        bitácora inmutable: documenta errores ya corregidos citando el
        nombre incorrecto a propósito, como registro de qué pasó y
        dónde se corrigió (ver casos KERNEL:BOOTSTRAP-001 y
        KERNEL:PATCH-QUALITY-001, sesión 2026-07-20). Reclasificar estos
        como 'histórico' evita que cada corrida futura los reporte como
        falso problema, sin ocultarlos vía BLOCKLIST (que es solo para
        placeholders de sintaxis, no para IDs reales con contexto
        histórico legítimo).
      - external_path (inventario_externos.md): IDs sin DEF que refieren
        a entidades reales fuera del universo .md escaneado (ej. una DB
        de Notion sin archivo Markdown equivalente). Estos son
        referencias correctas por diseño y nunca tendrán DEF local — ver
        EXTERNAL_REFS. Reclasificarlos aparte evita que se confundan con
        huérfanos reales o con BLOCKLIST (que es solo ruido de sintaxis).
        Confirmado con el caso CANON:ARCHIVO-VANTAGE, sesión 2026-07-20.

    Un ID se evalúa primero contra EXTERNAL_REFS, luego contra
    CHANGELOG_FILENAMES, y solo si no calza en ninguna de las dos cae en
    real_orphans.
    """
    by_id = defaultdict(list)
    for occ in occurrences:
        by_id[occ["id"]].append(occ)

    orphans_all = {
        id_name: occs for id_name, occs in by_id.items()
        if not any(o["kind"] == "DEF" for o in occs)
    }

    CHANGELOG_FILENAMES = {"Change Log.md", "ARCHIVO CHANGELOG.md"}

    real_orphans = {}
    historical = {}
    external = {}
    for id_name, occs in orphans_all.items():
        files_involved = {o["file"] for o in occs}
        if id_name in EXTERNAL_REFS:
            external[id_name] = occs
        elif files_involved.issubset(CHANGELOG_FILENAMES):
            historical[id_name] = occs
        else:
            real_orphans[id_name] = occs

    with out_path.open("w", encoding="utf-8") as f:
        f.write("# IDs Huérfanos (REF sin DEF detectada, en documentos vivos)\n\n")
        f.write(
            "Estos IDs aparecen citados en al menos un documento que NO es el "
            "Change Log, pero el script no encontró su definición. Requieren "
            "atención: o falta el DEF real, o hay una cita incorrecta en un "
            "documento vivo (Kernel, Manual, Career Canon, System Prompt). "
            "Los IDs cuya única aparición es dentro del Change Log se listan "
            "aparte en inventario_historicos.md, y los que refieren a "
            "entidades fuera del universo .md (ej. DBs de Notion) se listan "
            "en inventario_externos.md — ver esos archivos para más contexto "
            "sobre por qué se excluyen de esta lista.\n\n"
        )
        if not real_orphans:
            f.write("Ninguno detectado en esta corrida.\n")
        else:
            f.write(f"Total: {len(real_orphans)}\n\n---\n\n")
            for id_name in sorted(real_orphans.keys()):
                occs = real_orphans[id_name]
                f.write(f"## `{id_name}`\n\n")
                f.write(f"Citado {len(occs)}× en:\n")
                for o in occs:
                    f.write(f"- `{o['file']}` · L{o['line_no']} · sección: {o['section']}\n")
                f.write("\n---\n\n")

    with historical_path.open("w", encoding="utf-8") as f:
        f.write("# IDs Históricos (solo citados en Change Log — bitácora inmutable)\n\n")
        f.write(
            "El Change Log documenta errores ya corregidos citando el nombre "
            "incorrecto tal como existió en su momento (ej. 'CENSUS_SPEC "
            "declaraba X, un ID que nunca existió — el ID real es Y'). Esto "
            "es correcto por diseño y NO debe editarse retroactivamente. "
            "Estos IDs se excluyen de inventario_huerfanos.md para no generar "
            "falsos positivos en corridas futuras.\n\n"
        )
        if not historical:
            f.write("Ninguno detectado en esta corrida.\n")
        else:
            f.write(f"Total: {len(historical)}\n\n---\n\n")
            for id_name in sorted(historical.keys()):
                occs = historical[id_name]
                f.write(f"## `{id_name}`\n\n")
                f.write(f"Citado {len(occs)}× en:\n")
                for o in occs:
                    f.write(f"- `{o['file']}` · L{o['line_no']} · sección: {o['section']}\n")
                f.write("\n---\n\n")

    with external_path.open("w", encoding="utf-8") as f:
        f.write("# IDs Externos (refieren a entidades fuera del universo .md — DBs de Notion)\n\n")
        f.write(
            "Estos IDs son referencias reales y correctas a entidades que no "
            "viven como archivo Markdown local (típicamente, una DB de "
            "Notion registrada en la Cédula Digital). Nunca tendrán DEF "
            "detectable por este script y se excluyen de "
            "inventario_huerfanos.md por diseño, no por error. Para agregar "
            "un nuevo caso, añadir el ID a la constante EXTERNAL_REFS al "
            "inicio del script, con un comentario que documente a qué "
            "entidad real refiere.\n\n"
        )
        if not external:
            f.write("Ninguno detectado en esta corrida.\n")
        else:
            f.write(f"Total: {len(external)}\n\n---\n\n")
            for id_name in sorted(external.keys()):
                occs = external[id_name]
                f.write(f"## `{id_name}`\n\n")
                f.write(f"Citado {len(occs)}× en:\n")
                for o in occs:
                    f.write(f"- `{o['file']}` · L{o['line_no']} · sección: {o['section']}\n")
                f.write("\n---\n\n")


def main():
    parser = argparse.ArgumentParser(
        description="Genera inventario de referencias cruzadas de IDs VANTAGE."
    )
    parser.add_argument(
        "--root",
        required=True,
        type=Path,
        help="Ruta raíz a escanear (ej. Layer_1/ACTIVE o VANTAGE root).",
    )
    parser.add_argument(
        "--out",
        default=Path("./out"),
        type=Path,
        help="Carpeta de salida (default: ./out).",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.exists() or not root.is_dir():
        print(f"[ERROR] Ruta no existe o no es directorio: {root}", file=sys.stderr)
        sys.exit(1)

    out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    occurrences = build_inventory(root)

    unique_ids = {o["id"] for o in occurrences}
    def_count = sum(1 for o in occurrences if o["kind"] == "DEF")
    ref_count = sum(1 for o in occurrences if o["kind"] == "REF")

    csv_path = out_dir / "inventario_ids.csv"
    md_path = out_dir / "inventario_ids_por_id.md"
    orphans_path = out_dir / "inventario_huerfanos.md"
    historical_path = out_dir / "inventario_historicos.md"
    external_path = out_dir / "inventario_externos.md"

    write_csv(occurrences, csv_path)
    write_markdown_by_id(occurrences, md_path)
    write_orphans(occurrences, orphans_path, historical_path, external_path)

    print("\n--- RESUMEN ---")
    print(f"IDs únicos detectados : {len(unique_ids)}")
    print(f"Ocurrencias totales   : {len(occurrences)}  (DEF: {def_count}, REF: {ref_count})")
    print(f"Salida CSV            : {csv_path}")
    print(f"Salida MD (por ID)    : {md_path}")
    print(f"Salida MD (huérfanos) : {orphans_path}")
    print(f"Salida MD (históricos): {historical_path}")
    print(f"Salida MD (externos)  : {external_path}")
    print(
        "\nNOTA: revisar BLOCKLIST al inicio del script si aparecen falsos "
        "positivos nuevos (placeholders de sintaxis, timestamps, etc.), "
        "EXTERNAL_REFS si aparece un nuevo ID que refiere a una entidad "
        "fuera del universo .md (ej. otra DB de Notion), y "
        "heading_looks_like_def() si hay IDs marcados como huérfanos que sí "
        "tienen una definición real con un formato de heading distinto."
    )


if __name__ == "__main__":
    main()
