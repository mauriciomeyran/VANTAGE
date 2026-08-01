#!/usr/bin/env python3
"""
apply_hyperlinks_notion.py — VALIDADO EN PRODUCCIÓN (2026-08-01)
====================================================================
Validación real: --doc career_canon --apply, 2 bloques patcheados,
0 errores, link confirmado clickeable por el operador en Notion tras
la corrida. Block-ID preservado (verificado por el operador contra
Historial de versiones de Notion — edición incremental, no rebuild).

Reemplaza a 'vdoc local' / vsync_doc.py --direction local /
vsync_doc_fast.py para el caso de uso "aplicar hyperlinks a Notion":
esos tres mecanismos hacen delete-all + create-all sobre la página
completa (destroy/rebuild), lo que rompe cualquier anchor #block-id
existente — causa raíz confirmada del bug original de esta sesión
("los links de la TOC no hacen nada al click"). Este script hace
PATCH puntual por bloque, preservando block-ID.

Variante de apply_hyperlinks.py que escribe DIRECTO a los bloques de
Notion (PATCH puntual, preserva block-ID) en vez de escribir al .md
local y depender después de vdoc/vsync_doc.py para subirlo.

NO REIMPLEMENTA LÓGICA YA PROBADA. Reusa:
  - fetch_blocks_recursive, extract_ids_from_block, is_definition_block,
    VALID_PREFIXES, DOCUMENTS  ← de generate_census.py (censo real de
    DEF/REF con block_id real de Notion, ya usado y confiable — 209/209
    IDs resueltos en la última corrida real).
  - vantage_id_rules (rules.HEADING_RE, rules.ID_PATTERN, etc.) ← mismo
    módulo único de reglas que ya usan normalize_heading_ids.py y
    apply_hyperlinks.py. No se reimplementa aquí tampoco.

MAPPING YA NO ES UN DICCIONARIO ESTÁTICO HARDCODEADO. Se construye en
cada corrida a partir del link_index real de generate_census.py — esto
elimina de raíz la clase de bug que tenía el apply_hyperlinks.py viejo
(anchors PENDIENTE_ANCHOR sin resolver, IDs fusionados a mano que se
desactualizan cuando un heading se mueve).

ALCANCE PENDIENTE (pin explícito, decisión del operador 2026-08-01):
los 3 IDs sin DEF resuelto en la spec actual (MANUAL:COLD-START-001,
ALIASES:DEDUP, SP:CONSISTENCY §9 legacy) simplemente no producen link
— igual que hoy en vcensus, que ya los reporta como "IDs SIN link" si
no tienen DEF. No se resuelven en esta corrida; quedan pendientes.

QUÉ CAMBIA VS. EL PATRÓN DESTROY/REBUILD:
  - Nunca se llama notion.blocks.delete() salvo que no exista otra
    opción (no aplica en este flujo — solo tocamos texto, nunca tipo
    ni cantidad de bloques).
  - Cada bloque que gana un link nuevo se actualiza con
    PATCH /v1/blocks/{block_id} sobre ESE bloque — su ID no cambia.
  - El .md local en ACTIVE/ no se toca en este flujo. Sigue siendo
    responsabilidad de 'vdoc notion' (Notion -> local, ya soportado y
    no destructivo del lado de Notion) mantenerlo sincronizado después,
    si se desea reflejar el cambio en el filesystem local.

PENDIENTE (no bloqueante, anotado para sesión futura):
  - EXCLUDE_IDS vacío en este script — copiar aquí la lista real de
    apply_hyperlinks.py (27 IDs en la última corrida) antes de usar
    --all sobre documentos donde esa exclusión importe.
  - Sin probar aún en Kernel/Manual (26 y 40 cambios respectivamente,
    con más volumen de table_row) — recomendado correr --dry-run
    primero en cada uno antes de --apply.

Uso:
    python3 apply_hyperlinks_notion.py --doc career_canon --dry-run
    python3 apply_hyperlinks_notion.py --doc career_canon --apply
    python3 apply_hyperlinks_notion.py --all --dry-run
"""

import argparse
import os
import re
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

# ─── Reusar generate_census.py sin reimplementar ──────────────────────
_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))
import generate_census as census  # noqa: E402

# ─── Reusar vantage_id_rules.py (mismo módulo único que ya usan
#     normalize_heading_ids.py y apply_hyperlinks.py) ──────────────────
import vantage_id_rules as rules  # noqa: E402

HEADERS = census.HEADERS
DOCUMENTS = census.DOCUMENTS

# IDs excluidos de esta corrida — copiar aquí el mismo set que ya vive
# en EXCLUDE_IDS dentro de apply_hyperlinks.py, si aplica. Se deja vacío
# en el prototipo; el operador puede pegar la lista real antes de usar
# en documentos donde importe (ej. IDs que deliberadamente no se
# auto-enlazan por regla de negocio, no por falta de anchor).
EXCLUDE_IDS = set()

# Doc name (como aparece en DOCUMENTS de generate_census.py) -> clave
# corta usada como --doc en este script, para no repetir UUIDs.
DOC_KEY_TO_NAME = {
    "kernel": "Kernel",
    "system_prompt": "System Prompt",
    "manual": "Manual",
    "career_canon": "Career Canon",
    "aliases": "Aliases",
    "change_log": "Change Log",
    "brief": "Navigation Brief",
}


# ─── PATCH a un bloque puntual (preserva block-ID) ─────────────────────

def patch_block_rich_text(block_id: str, btype: str, new_rich_text: list) -> bool:
    """
    PATCH /v1/blocks/{id} sobre el campo rich_text del tipo correspondiente.
    No cambia el tipo del bloque, no cambia su posición, no cambia su ID.
    """
    payload = {btype: {"rich_text": new_rich_text}}
    for attempt in range(3):
        r = requests.patch(
            f"https://api.notion.com/v1/blocks/{block_id}",
            headers=HEADERS, json=payload, timeout=30,
        )
        if r.status_code == 200:
            return True
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 2))
            time.sleep(wait)
            continue
        print(f"    [ERROR {r.status_code}] PATCH {block_id[:8]}: {r.text[:150]}")
        return False
    return False


def patch_table_row_cell(block_id: str, cells: list) -> bool:
    """PATCH de una table_row completa (todas sus celdas) — mismo bloque, mismo ID."""
    payload = {"table_row": {"cells": cells}}
    for attempt in range(3):
        r = requests.patch(
            f"https://api.notion.com/v1/blocks/{block_id}",
            headers=HEADERS, json=payload, timeout=30,
        )
        if r.status_code == 200:
            return True
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 2))
            time.sleep(wait)
            continue
        print(f"    [ERROR {r.status_code}] PATCH table_row {block_id[:8]}: {r.text[:150]}")
        return False
    return False


# ─── Construcción de MAPPING dinámico desde el censo real ─────────────

def build_dynamic_mapping(link_index: dict) -> dict:
    """
    A partir del link_index que ya arma generate_census.py (DEF + REF de
    TODOS los bloques de los 7 documentos, con block_id real), construye
    un MAPPING id -> url usando exactamente la misma lógica de selección
    que el censo (pick_best_link): prioriza DEF, luego por DOC_PRIORITY.

    Reemplaza al diccionario MAPPING estático de apply_hyperlinks.py.
    """
    mapping = {}
    for id_str, entries in link_index.items():
        def_entries = [e for e in entries if e["is_def"]]
        if not def_entries:
            continue  # sin DEF resuelto — no se genera link (mismo criterio que vcensus)
        best = census.pick_best_link(def_entries)
        if best:
            mapping[id_str] = best["link"]
    return mapping


# ─── Conversión de texto (idéntica intención a convert_line, adaptada
#     para operar sobre segmentos rich_text en vez de líneas de string) ─

def _plain_text_of(rich_text: list) -> str:
    return "".join(s.get("plain_text", "") for s in rich_text)


def _rebuild_rich_text_with_links(plain: str, mapping: dict, def_ids_here: set) -> list:
    """
    Reconstruye una lista rich_text a partir de texto plano, convirtiendo
    cada ocurrencia REF de un ID mapeado en un segmento con link real de
    Notion — sin tocar el resto del texto. Análogo a convert_line() de
    apply_hyperlinks.py pero produce rich_text de Notion directamente en
    vez de markdown "[texto](url)".
    """
    segments = []
    pos = 0
    changed = False
    for m in rules.ID_PATTERN.finditer(plain):
        id_found = m.group(1)
        start, end = m.span(1)
        if id_found in def_ids_here or id_found in EXCLUDE_IDS:
            continue
        url = mapping.get(id_found)
        if not url:
            continue
        if start > pos:
            segments.append({"type": "text", "text": {"content": plain[pos:start]}})
        segments.append({"type": "text", "text": {"content": id_found, "link": {"url": url}}})
        pos = end
        changed = True
    if not changed:
        return None  # sin cambios — no tocar el bloque
    if pos < len(plain):
        segments.append({"type": "text", "text": {"content": plain[pos:]}})
    return segments


def _def_ids_in_plain(plain: str, btype: str) -> set:
    """Determina qué IDs, en este texto, cuentan como su propia DEF (no auto-linkear)."""
    defs = set()
    for m in rules.ID_PATTERN.finditer(plain):
        id_str = m.group(1)
        if census.is_definition_block(plain.strip("` \n"), id_str, btype):
            defs.add(id_str)
    return defs


# ─── Runner por documento ───────────────────────────────────────────────

TEXT_TYPES = {
    "paragraph", "bulleted_list_item", "numbered_list_item",
    "callout", "quote", "toggle",
}
# Headings NUNCA se auto-enlazan — regla permanente confirmada por el
# operador (ver apply_hyperlinks.py, docstring). Se excluyen a propósito.


def process_document(doc_key: str, mapping: dict, dry_run: bool) -> dict:
    doc_name = DOC_KEY_TO_NAME[doc_key]
    page_id = DOCUMENTS[doc_name]

    print(f"\n{'DRY RUN' if dry_run else 'APLICANDO'} — {doc_name}")
    blocks = census.fetch_blocks_recursive(page_id)

    summary = {"patched": 0, "unchanged": 0, "errors": 0}
    plan = []

    for block in blocks:
        btype = block["type"]
        block_id = block["id"]

        if btype in TEXT_TYPES:
            rich_text = block[btype].get("rich_text", [])
            plain = _plain_text_of(rich_text)
            def_ids = _def_ids_in_plain(plain, btype)
            new_rt = _rebuild_rich_text_with_links(plain, mapping, def_ids)
            if new_rt is None:
                summary["unchanged"] += 1
                continue
            plan.append(f"  PATCH [{btype}] {block_id}  {plain[:70]!r}")
            summary["patched"] += 1
            if not dry_run:
                ok = patch_block_rich_text(block_id, btype, new_rt)
                if not ok:
                    summary["errors"] += 1

        elif btype == "table_row":
            cells = block["table_row"].get("cells", [])
            new_cells = []
            any_change = False
            for cell in cells:
                plain = _plain_text_of(cell)
                def_ids = _def_ids_in_plain(plain, btype)
                new_rt = _rebuild_rich_text_with_links(plain, mapping, def_ids)
                if new_rt is None:
                    new_cells.append(cell)
                else:
                    new_cells.append(new_rt)
                    any_change = True
            if not any_change:
                summary["unchanged"] += 1
                continue
            row_preview = " | ".join(_plain_text_of(c) for c in cells)[:70]
            plan.append(f"  PATCH [table_row] {block_id}  {row_preview!r}")
            summary["patched"] += 1
            if not dry_run:
                ok = patch_table_row_cell(block_id, new_cells)
                if not ok:
                    summary["errors"] += 1

        else:
            continue  # code, table (contenedor), divider, etc. — sin texto a convertir

    for line in plan:
        print(line)

    print(f"  Patched: {summary['patched']}  Sin cambios: {summary['unchanged']}  Errores: {summary['errors']}")
    return summary


def main():
    p = argparse.ArgumentParser(description="Aplica hyperlinks directo a Notion (PATCH, preserva block-ID).")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--doc", choices=list(DOC_KEY_TO_NAME.keys()))
    group.add_argument("--all", action="store_true")
    p.add_argument("--apply", action="store_true", help="Escribe de verdad. Sin esta flag (o con --dry-run): dry-run.")
    p.add_argument("--dry-run", action="store_true", help="Explícito, no-op — el default ya es dry-run sin --apply.")
    args = p.parse_args()

    dry_run = not args.apply

    print("apply_hyperlinks_notion (PROTOTIPO) — PATCH directo, sin destroy/rebuild")
    print("=" * 60)
    print("Construyendo MAPPING dinámico desde censo real (fuente de verdad única)...")
    link_index, incomplete = census.build_link_index()
    if incomplete:
        print("\n⚠️  ADVERTENCIA: censo incompleto para estos documentos —")
        for entry in incomplete:
            print(f"    - {entry['doc']}: {entry['error']}")
        print("  Continuar puede generar MAPPING parcial. Considera reintentar antes de --apply.\n")

    mapping = build_dynamic_mapping(link_index)
    print(f"MAPPING dinámico construido: {len(mapping)} IDs con DEF resuelto.\n")

    targets = list(DOC_KEY_TO_NAME.keys()) if args.all else [args.doc]

    totals = {"patched": 0, "unchanged": 0, "errors": 0}
    for doc_key in targets:
        summary = process_document(doc_key, mapping, dry_run)
        for k in totals:
            totals[k] += summary[k]

    print("\n" + "=" * 60)
    print("RESUMEN TOTAL")
    print(f"  Modo: {'DRY RUN (nada escrito)' if dry_run else 'APLICADO (escritura real vía PATCH)'}")
    print(f"  Bloques patched:    {totals['patched']}")
    print(f"  Bloques sin cambio: {totals['unchanged']}")
    print(f"  Errores:            {totals['errors']}")
    print("=" * 60)
    if dry_run:
        print("\nDry-run: nada escrito. Revisa el plan arriba y vuelve a correr con --apply.")
    else:
        print("\nRecuerda: correr 'vdoc notion' después si quieres reflejar estos cambios")
        print("en el .md local de ACTIVE/ (esa dirección SÍ es segura — Notion es la fuente).")


if __name__ == "__main__":
    main()
