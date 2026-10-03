#!/usr/bin/env python3
"""
reorder_census_spec.py — Reordena CENSUS_SPEC según el orden real en Documentación/ACTIVE/
==========================================================================================
Herramienta determinista offline (sin red ni NOTION_TOKEN) que:
  1. Separa las filas CANON:/CAREER_CANON: alojadas dentro de MANUAL hacia su
     propia sección "CAREER CANON".
  2. Ordena las filas de cada sección por la primera aparición real de su
     definición (heading/bloque DEF, con fallback a primera mención) en el
     documento espejo correspondiente de Documentación/ACTIVE/ — nunca por
     orden manual ni numérico forzado.
  3. Sincroniza el campo `seccion` de cada fila con el número real del heading
     vivo en Documentación/ACTIVE/ (normalizando punto final y padding de 2
     dígitos en capítulos raíz).
  4. Elimina duplicados exactos por `id` preservando la primera aparición.
  5. Con `--md-file`, reescribe el markdown publicado (`V_ID_CENSUS_PRODUCTION.md`)
     preservando los enlaces `[`ID`](url)` ya resueltos y la sección de huérfanos.

Uso:
    python3 Layer_1/scripts/reorder_census_spec.py --dry-run
    python3 Layer_1/scripts/reorder_census_spec.py --md-file Layer_1/data/V_ID_CENSUS_PRODUCTION.md
"""
from __future__ import annotations

import argparse
import ast
import copy
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_CENSUS_FILE = SCRIPT_DIR / "generate_census.py"
DEFAULT_ACTIVE_DIR = REPO_ROOT / "Documentación" / "ACTIVE"

sys.path.insert(0, str(SCRIPT_DIR))
import vantage_id_rules as rules  # noqa: E402

DOC_TO_ACTIVE_FILE: dict[str, str] = {
    "PROJECT CHARTER": "PROJECT_CHARTER.md",
    "KERNEL": "Kernel.md",
    "MANUAL": "Manual.md",
    "CAREER CANON": "Career Canon.md",
    "NAVIGATION BRIEF": "Brief.md",
    "SYSTEM PROMPT": "System Prompt.md",
    "ALIASES": "Aliases.md",
}

CANONICAL_SECTION_ORDER: list[str] = [
    "KERNEL",
    "SYSTEM PROMPT",
    "MANUAL",
    "CAREER CANON",
    "ALIASES",
    "NAVIGATION BRIEF",
    "PROJECT CHARTER",
]

HEADING_SEC_RE = re.compile(r"^([\d.]+[a-z]?)\s*(?:[—-]\s*)?")
MD_ROW_RE = re.compile(
    r"^\|\s*(\[?`([A-Z0-9_]+:[A-Z0-9-]+)`(?:\]\([^)]+\))?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|$"
)


def normalize_heading_section(raw_sec: str | None) -> str | None:
    """Normaliza el token de sección extraído de un heading vivo.

    Quita punto final ('1.' → '01') y aplica padding de 2 dígitos solo a
    capítulos enteros raíz ('1' → '01'), dejando subsecciones ('2.1', '8.1',
    '22.1a') intactas conforme a vantage_id_rules.
    """
    if not raw_sec:
        return None
    cleaned = raw_sec.strip().rstrip(".")
    if not cleaned:
        return None
    if cleaned.isdigit():
        return cleaned.zfill(2)
    return cleaned


def extract_heading_section(heading_plain: str) -> str | None:
    """Extrae y normaliza el número de sección al inicio de un heading."""
    stripped = heading_plain.strip("` \n")
    m = HEADING_SEC_RE.match(stripped)
    if m:
        return normalize_heading_section(m.group(1))
    return None


def _strip_markdown_links(text: str) -> str:
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)


def scan_document_positions(md_path: Path) -> dict[str, dict]:
    """Escanea un archivo de Documentación/ACTIVE/ y devuelve por cada ID:
    - first_def_line: primera línea (1-based) donde el ID aparece como definición
    - first_any_line: primera línea (1-based) donde el ID aparece en cualquier parte
    - live_seccion: sección normalizada extraída de su heading de definición
    """
    positions: dict[str, dict] = {}
    if not md_path.exists():
        return positions

    lines = md_path.read_text(encoding="utf-8").splitlines()
    in_fence = False

    for lineno, raw_line in enumerate(lines, 1):
        if rules.is_fence_line(raw_line):
            in_fence = not in_fence
            continue

        stripped = raw_line.strip()
        m_heading = rules.HEADING_RE.match(raw_line)
        is_heading = m_heading is not None and not in_fence

        if is_heading:
            hashes, h_body = m_heading.group(1), m_heading.group(2).strip()
            btype = f"heading_{min(len(hashes), 3)}"
            plain_clean = _strip_markdown_links(h_body).strip("` ")
        elif stripped.startswith("|"):
            btype = "table_row"
            plain_clean = _strip_markdown_links(stripped).strip("` ")
        else:
            btype = "paragraph"
            plain_clean = _strip_markdown_links(stripped).strip("` ")

        for match in rules.ID_PATTERN.finditer(raw_line):
            cid = match.group(1)
            entry = positions.setdefault(
                cid,
                {
                    "first_def_line": None,
                    "first_def_col": None,
                    "first_any_line": lineno,
                    "first_any_col": match.start(),
                    "live_seccion": None,
                },
            )
            if in_fence:
                continue

            is_def = False
            if is_heading:
                body_after_sec = HEADING_SEC_RE.sub("", plain_clean)
                if (
                    rules.heading_looks_like_def(plain_clean, cid)
                    or rules.starts_with_id_boundary(plain_clean, cid)
                    or rules.starts_with_id_boundary(body_after_sec, cid)
                ):
                    is_def = True
            elif not is_heading and btype != "table_row" and rules.is_definition_block(plain_clean, cid, btype):
                is_def = True

            if is_def and entry["first_def_line"] is None:
                entry["first_def_line"] = lineno
                entry["first_def_col"] = match.start()
                if is_heading:
                    sec = extract_heading_section(plain_clean)
                    if sec:
                        entry["live_seccion"] = sec

    return positions


def _section_sort_tuple(sec: str) -> tuple | None:
    """Convierte '12.3' o '22.1a' en tupla comparable por capítulo padre."""
    if not sec or "." not in sec:
        return None
    parts = sec.split(".")
    parsed = []
    for p in parts:
        m = re.match(r"^(\d+)([a-z]?)$", p)
        if not m:
            return None
        parsed.append((int(m.group(1)), m.group(2)))
    return tuple(parsed)


def detect_numeric_inversions(spec: list[dict]) -> list[dict]:
    """Detecta subsecciones hermanas donde el orden real del documento tiene
    una inversión numérica (ej. 12.3 antes de 12.1, o 22.2 antes de 22.1).
    """
    inversions: list[dict] = []
    for section in spec:
        prev_parent = None
        prev_tuple = None
        prev_row = None
        for row in section.get("rows", []):
            sec = row.get("seccion", "")
            t = _section_sort_tuple(sec)
            if t is None:
                prev_parent = None
                prev_tuple = None
                prev_row = None
                continue
            parent = t[0][0]
            if prev_parent == parent and prev_tuple is not None and t < prev_tuple:
                inversions.append(
                    {
                        "section": section["name"],
                        "first_id": prev_row["id"],
                        "first_seccion": prev_row.get("seccion", ""),
                        "second_id": row["id"],
                        "second_seccion": sec,
                    }
                )
            prev_parent = parent
            prev_tuple = t
            prev_row = row
    return inversions


def split_canon_from_manual(spec: list[dict]) -> tuple[list[dict], int]:
    """Separa las filas CANON:/CAREER_CANON: alojadas en MANUAL hacia CAREER CANON."""
    result: list[dict] = []
    extracted_canon: list[dict] = []
    existing_canon_idx: int | None = None

    for section in spec:
        name = section["name"]
        rows = [copy.deepcopy(r) for r in section["rows"]]
        if name == "MANUAL":
            manual_rows = []
            for r in rows:
                if r["id"].startswith(("CANON:", "CAREER_CANON:")):
                    extracted_canon.append(r)
                else:
                    manual_rows.append(r)
            result.append({"name": "MANUAL", "rows": manual_rows})
            if extracted_canon:
                existing_canon_idx = len(result)
                result.append({"name": "CAREER CANON", "rows": list(extracted_canon)})
        elif name in ("CAREER CANON", "CANON", "CAREER_CANON"):
            if existing_canon_idx is not None:
                seen = {r["id"] for r in result[existing_canon_idx]["rows"]}
                for r in rows:
                    if r["id"] not in seen:
                        result[existing_canon_idx]["rows"].append(r)
                        seen.add(r["id"])
            else:
                existing_canon_idx = len(result)
                result.append({"name": "CAREER CANON", "rows": rows})
        else:
            result.append({"name": name, "rows": rows})

    return result, len(extracted_canon)


def reorder_spec(
    spec: list[dict],
    active_dir: Path = DEFAULT_ACTIVE_DIR,
    section_order: str = "preserve",
    sync_seccion: bool = True,
) -> tuple[list[dict], dict]:
    """Reordena `spec` según la primera aparición real en `active_dir`.

    Retorna `(new_spec, stats)`.
    """
    if section_order not in ("preserve", "canonical"):
        raise ValueError(f"section_order inválido: {section_order!r}")

    split_sections, canon_separated = split_canon_from_manual(spec)

    if section_order == "canonical":
        order_map = {name: i for i, name in enumerate(CANONICAL_SECTION_ORDER)}
        split_sections = sorted(
            split_sections,
            key=lambda s: (order_map.get(s["name"], 999), s["name"]),
        )

    seen_global: set[str] = set()
    duplicates_removed = 0
    relocated_total = 0
    seccion_synced = 0
    seccion_changes: list[tuple[str, str, str, str]] = []
    unlocated: list[str] = []
    per_section_relocated: dict[str, int] = {}

    new_spec: list[dict] = []

    for section in split_sections:
        sec_name = section["name"]
        md_filename = DOC_TO_ACTIVE_FILE.get(sec_name)
        md_path = active_dir / md_filename if md_filename else Path("/nonexistent")
        positions = scan_document_positions(md_path)

        deduped_rows: list[dict] = []
        for row in section["rows"]:
            rid = row["id"]
            if rid in seen_global:
                duplicates_removed += 1
                continue
            seen_global.add(rid)
            deduped_rows.append(copy.deepcopy(row))

        indexed_rows: list[tuple[tuple[int, int, int], int, dict]] = []
        for orig_idx, row in enumerate(deduped_rows):
            lids = [row["id"]] + [x for x in row.get("lookup_ids", []) if x != row["id"]]

            def_candidates = [
                (positions[lid]["first_def_line"], positions[lid]["first_def_col"] or 0)
                for lid in lids
                if lid in positions and positions[lid]["first_def_line"] is not None
            ]
            any_candidates = [
                (positions[lid]["first_any_line"], positions[lid]["first_any_col"] or 0)
                for lid in lids
                if lid in positions and positions[lid]["first_any_line"] is not None
            ]

            if def_candidates:
                best_line, best_col = min(def_candidates)
                sort_key = (0, best_line, best_col)
            elif any_candidates:
                best_line, best_col = min(any_candidates)
                sort_key = (1, best_line, best_col)
            else:
                unlocated.append(row["id"])
                sort_key = (2, 999999, orig_idx)

            if sync_seccion:
                for lid in lids:
                    live_sec = positions.get(lid, {}).get("live_seccion")
                    if live_sec:
                        old_sec = row.get("seccion", "")
                        if live_sec != old_sec:
                            row["seccion"] = live_sec
                            seccion_synced += 1
                            seccion_changes.append((sec_name, row["id"], old_sec, live_sec))
                        break

            indexed_rows.append((sort_key, orig_idx, row))

        sorted_rows = [r for _, _, r in sorted(indexed_rows, key=lambda item: (item[0], item[1]))]
        moved = sum(1 for a, b in zip(deduped_rows, sorted_rows) if a["id"] != b["id"])
        relocated_total += moved
        per_section_relocated[sec_name] = moved
        new_spec.append({"name": sec_name, "rows": sorted_rows})

    inversions = detect_numeric_inversions(new_spec)
    total_rows = sum(len(s["rows"]) for s in new_spec)

    stats = {
        "total_rows": total_rows,
        "relocated": relocated_total,
        "per_section_relocated": per_section_relocated,
        "canon_separated": canon_separated,
        "seccion_synced": seccion_synced,
        "seccion_changes": seccion_changes,
        "duplicates_removed": duplicates_removed,
        "unlocated": unlocated,
        "inversions": inversions,
    }
    return new_spec, stats


def format_row_literal(row: dict, indent: str = " " * 12) -> str:
    """Formatea una fila de CENSUS_SPEC con el orden de claves canónico."""
    parts = [f'"id": {json.dumps(row["id"], ensure_ascii=False)}']
    if "lookup_ids" in row:
        lids = ", ".join(json.dumps(x, ensure_ascii=False) for x in row["lookup_ids"])
        parts.append(f'"lookup_ids": [{lids}]')
    parts.append(f'"seccion": {json.dumps(row.get("seccion", ""), ensure_ascii=False)}')
    parts.append(f'"nombre": {json.dumps(row.get("nombre", ""), ensure_ascii=False)}')
    for extra_key in row:
        if extra_key not in {"id", "lookup_ids", "seccion", "nombre"}:
            parts.append(f"{json.dumps(extra_key, ensure_ascii=False)}: {json.dumps(row[extra_key], ensure_ascii=False)}")
    return f"{indent}{{" + ", ".join(parts) + "},"


def format_census_spec_block(spec: list[dict]) -> str:
    """Serializa `CENSUS_SPEC = [...]` con el estilo exacto de generate_census.py."""
    lines = ["CENSUS_SPEC = ["]
    for section in spec:
        lines.append("    {")
        lines.append(f'        "name": {json.dumps(section["name"], ensure_ascii=False)},')
        lines.append('        "rows": [')
        for row in section["rows"]:
            lines.append(format_row_literal(row))
        lines.append("        ],")
        lines.append("    },")
    lines.append("]")
    return "\n".join(lines)


def load_spec_from_source(source: str) -> tuple[list[dict], int, int]:
    """Extrae `(spec, start_lineno, end_lineno)` de `CENSUS_SPEC` por AST."""
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "CENSUS_SPEC" for t in node.targets):
            spec = ast.literal_eval(node.value)
            return spec, node.lineno, node.end_lineno
    raise ValueError("No se encontró CENSUS_SPEC en el archivo fuente.")


def replace_spec_in_source(source: str, new_spec: list[dict]) -> str:
    """Reemplaza el bloque `CENSUS_SPEC = [...]` en `source` y valida el AST resultante."""
    _, start_lineno, end_lineno = load_spec_from_source(source)
    lines = source.splitlines()
    new_block_lines = format_census_spec_block(new_spec).splitlines()
    updated_lines = lines[: start_lineno - 1] + new_block_lines + lines[end_lineno:]
    updated_source = "\n".join(updated_lines) + ("\n" if source.endswith("\n") else "")

    # Validación AST antes de devolver
    parsed_spec, _, _ = load_spec_from_source(updated_source)
    expected_ids = [r["id"] for s in new_spec for r in s["rows"]]
    actual_ids = [r["id"] for s in parsed_spec for r in s["rows"]]
    if expected_ids != actual_ids:
        raise RuntimeError("Validación AST falló: los IDs serializados no coinciden.")
    return updated_source


def rewrite_census_markdown(md_path: Path, spec: list[dict], dry_run: bool = False) -> str:
    """Reescribe `V_ID_CENSUS_PRODUCTION.md` preservando los links existentes."""
    existing_text = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
    id_to_cell: dict[str, str] = {}

    for line in existing_text.splitlines():
        m = MD_ROW_RE.match(line.strip())
        if m:
            cell, rid = m.group(1), m.group(2)
            id_to_cell[rid] = cell

    # Preservar bloque de huérfanos existente si está presente
    orphan_header = "## IDs Huérfanos (fuera de CENSUS_SPEC)"
    if orphan_header in existing_text:
        orphan_tail = existing_text[existing_text.index(orphan_header) :].rstrip()
    else:
        orphan_tail = f"{orphan_header}\n\n_Ninguno detectado en esta corrida._"

    out_lines: list[str] = []
    for idx, section in enumerate(spec):
        if idx > 0:
            out_lines.append("---")
            out_lines.append("")
        out_lines += [
            f"## {section['name']}",
            "",
            "| ID | Sección | Nombre |",
            "|---|---|---|",
        ]
        for row in section["rows"]:
            rid = row["id"]
            cell = id_to_cell.get(rid)
            if not cell:
                for lid in row.get("lookup_ids", []):
                    if lid in id_to_cell:
                        cell = id_to_cell[lid]
                        break
            if not cell:
                cell = f"`{rid}`"
            seccion = row.get("seccion", "")
            nombre = row.get("nombre", "")
            out_lines.append(f"| {cell} | {seccion} | {nombre} |")
        out_lines.append("")

    out_lines.append("---")
    out_lines.append("")
    out_lines.append(orphan_tail)
    rendered = "\n".join(out_lines).rstrip() + "\n"

    if not dry_run:
        md_path.write_text(rendered, encoding="utf-8")
    return rendered


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Reordena CENSUS_SPEC por la primera aparición real de cada ID en Documentación/ACTIVE/."
    )
    parser.add_argument(
        "--census-file",
        type=Path,
        default=DEFAULT_CENSUS_FILE,
        help="Ruta a generate_census.py (default: Layer_1/scripts/generate_census.py).",
    )
    parser.add_argument(
        "--active-dir",
        type=Path,
        default=DEFAULT_ACTIVE_DIR,
        help="Directorio Documentación/ACTIVE/ (default: Documentación/ACTIVE).",
    )
    parser.add_argument(
        "--md-file",
        type=Path,
        default=None,
        help="Si se indica, reescribe también el markdown publicado (ej. Layer_1/data/V_ID_CENSUS_PRODUCTION.md).",
    )
    parser.add_argument(
        "--section-order",
        choices=["preserve", "canonical"],
        default="preserve",
        help="Orden de secciones raíz: 'preserve' (default) o 'canonical' (según DOC_PRIORITY).",
    )
    parser.add_argument(
        "--no-sync-seccion",
        action="store_true",
        help="No actualizar el campo 'seccion' con el número del heading vivo.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Calcula y reporta cambios sin escribir archivos.",
    )
    args = parser.parse_args(argv)

    source = args.census_file.read_text(encoding="utf-8")
    spec, _, _ = load_spec_from_source(source)

    new_spec, stats = reorder_spec(
        spec,
        active_dir=args.active_dir,
        section_order=args.section_order,
        sync_seccion=not args.no_sync_seccion,
    )

    print("reorder_census_spec — Resumen")
    print("=" * 56)
    print(f"  Secciones:            {len(new_spec)} ({', '.join(s['name'] for s in new_spec)})")
    print(f"  Filas totales:        {stats['total_rows']}")
    print(f"  Filas CANON separadas:{stats['canon_separated']}")
    print(f"  Filas reubicadas:     {stats['relocated']}")
    for sname, moved in stats["per_section_relocated"].items():
        print(f"    - {sname:<18} {moved} reubicada(s)")
    print(f"  Secciones sincronizadas con heading vivo: {stats['seccion_synced']}")
    print(f"  Duplicados eliminados:{stats['duplicates_removed']}")
    if stats["inversions"]:
        print("  ⚠ Inversiones numéricas en documento fuente (respetadas por orden real):")
        for inv in stats["inversions"]:
            print(
                f"    - [{inv['section']}] {inv['first_id']} ({inv['first_seccion']}) "
                f"aparece antes de {inv['second_id']} ({inv['second_seccion']})"
            )
    print("=" * 56)

    if not args.dry_run:
        updated_source = replace_spec_in_source(source, new_spec)
        args.census_file.write_text(updated_source, encoding="utf-8")
        print(f"✓ CENSUS_SPEC actualizado en {args.census_file}")

    if args.md_file is not None:
        rewrite_census_markdown(args.md_file, new_spec, dry_run=args.dry_run)
        if not args.dry_run:
            print(f"✓ Markdown actualizado en {args.md_file}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
