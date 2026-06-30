#!/usr/bin/env python3
"""
vantage_kernel_patch.py — Fase 3
Documenta en Kernel §4 el comportamiento real del campo JD por wrapper (D-06).

Estrategia:
  1. Fetch del Kernel page → localiza el bloque heading que contiene §4 / schema / vocabulario
  2. Busca la tabla de vocabulario con el mapeo 'jd → JD'
  3. Genera nota operativa a insertar después de esa tabla
  4. Dry-run: imprime old_str / new_str exactos
  5. Execute: appends nota al bloque padre de la tabla vía Notion API

Uso:
    python vantage_kernel_patch.py --dry-run
    python vantage_kernel_patch.py --execute

Requiere: NOTION_TOKEN en Layer_1/config/layer_1.env o en env
"""

import os
import sys
import json
import argparse
from pathlib import Path

_ENV_PATH = Path.home() / "Documents/04-Vantage_CV/Layer_1/config/layer_1.env"
if _ENV_PATH.exists():
    for line in _ENV_PATH.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
if not NOTION_TOKEN:
    sys.exit("ERROR: NOTION_TOKEN no encontrado.")

NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"

KERNEL_PAGE_ID = "377938be-fc42-805e-a408-c9ae518d4fe7"

# ── Nota a insertar ───────────────────────────────────────────────────────────
#
# Se inserta después de la tabla de vocabulario en §4 que documenta 'jd → JD'.
# Si no se encuentra la tabla exacta, se appends al final del bloque §4.

JD_COVERAGE_NOTE_LINES = [
    "⚠ Cobertura del campo JD por capa (comportamiento esperado):",
    "",
    "• L1 (Aggregators, LinkedIn, Career Sites): NO extrae JD. El campo llega null "
    "salvo que la career page sea accedida directamente por L2.",
    "• L2 (Career Pages wrapper): SÍ extrae JD cuando navega la career page de forma directa. "
    "Es la única fuente confiable del texto completo de la JD.",
    "• L3 (mail_pipeline): NO extrae JD — ingesta de emails sin acceso a la job page.",
    "",
    "Comportamiento cuando jd llega null:",
    "  - CV-A: el AI Component cruza keywords del JD contra el Canon. "
    "Si jd es null y fetch_status ≠ direct_apply, el cruce no se ejecuta.",
    "  - El campo se escribe en Notion como rich_text vacío — no rompe el schema.",
    "",
    "Pendiente operativo: evaluar auto-asignación de Source_Type=Vacante en ingesta L1 "
    "cuando el campo está vacío y existe URL (ver Bug Tracker 38b938be-fc42-8117).",
]

JD_COVERAGE_CALLOUT_TEXT = "\n".join(JD_COVERAGE_NOTE_LINES)

# Texto de búsqueda para localizar el bloque correcto en §4
JD_ANCHOR_TEXTS = [
    "jd",          # nombre de campo en tabla vocabulario
    "JD",          # nombre de propiedad Notion
    "feed_processor",  # contexto de §4
]

# ── HTTP helpers ──────────────────────────────────────────────────────────────

try:
    import httpx
except ImportError:
    sys.exit("ERROR: httpx no instalado. Ejecuta: pip install httpx --break-system-packages")


def _headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def notion_get(path: str) -> dict:
    r = httpx.get(f"{BASE_URL}{path}", headers=_headers(), timeout=30)
    r.raise_for_status()
    return r.json()


def notion_patch(path: str, payload: dict) -> dict:
    r = httpx.patch(f"{BASE_URL}{path}", headers=_headers(), json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def notion_post(path: str, payload: dict) -> dict:
    r = httpx.post(f"{BASE_URL}{path}", headers=_headers(), json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


# ── Traversal ─────────────────────────────────────────────────────────────────

def get_children(block_id: str) -> list:
    blocks = []
    cursor = None
    while True:
        url = f"/blocks/{block_id.replace('-', '')}/children"
        if cursor:
            url += f"?start_cursor={cursor}"
        data = notion_get(url)
        blocks.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data["next_cursor"]
    return blocks


def block_text(block: dict) -> str:
    btype = block.get("type", "")
    rich = block.get(btype, {}).get("rich_text", [])
    return "".join(r.get("plain_text", "") for r in rich)


def find_section_4_block(blocks: list) -> dict | None:
    """Encuentra el bloque heading que corresponde a §4 del Kernel."""
    candidates = []
    for b in blocks:
        txt = block_text(b).strip()
        btype = b.get("type", "")
        # §4 puede llamarse: §4, §4 VOCABULARIO, §4 SCHEMA, etc.
        if btype.startswith("heading") and (
            txt.startswith("§4") or
            txt.startswith("[ID:") and "§4" in txt or
            "VOCABULARIO" in txt.upper() or
            "SCHEMA" in txt.upper() and "§4" in txt
        ):
            candidates.append(b)
    if candidates:
        return candidates[0]
    return None


def find_jd_block_in_section(section_id: str) -> dict | None:
    """
    Dentro del bloque §4, busca el bloque tabla o párrafo que menciona 'jd'.
    Retorna el bloque más cercano para hacer el append después de él.
    """
    children = get_children(section_id)
    last_jd_block = None
    for b in children:
        txt = block_text(b).lower()
        if "jd" in txt or "feed_processor" in txt:
            last_jd_block = b
    return last_jd_block, children


def already_patched(children: list) -> bool:
    """Verifica si la nota ya fue insertada (evita duplicados)."""
    for b in children:
        txt = block_text(b)
        if "Cobertura del campo JD" in txt or "L2 (Career Pages wrapper)" in txt:
            return True
    return False


# ── Payload ───────────────────────────────────────────────────────────────────

def build_callout_block(text: str) -> dict:
    """
    Construye un callout block de Notion con ícono ⚠.
    El texto se convierte en rich_text plano.
    """
    return {
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": [{"type": "text", "text": {"content": text}}],
            "icon": {"type": "emoji", "emoji": "⚠️"},
            "color": "yellow_background",
        },
    }


def build_paragraph_blocks(lines: list) -> list:
    """Fallback: convierte líneas a paragraph blocks simples."""
    blocks = []
    for line in lines:
        if not line.strip():
            continue
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": line}}]
            },
        })
    return blocks


# ── Output helpers ────────────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
YELLOW = "\033[93m"
GREEN  = "\033[92m"
RED    = "\033[91m"
CYAN   = "\033[96m"


def print_header(text):
    print(f"\n{BOLD}{CYAN}{'─'*60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'─'*60}{RESET}")


# ── Dry-run ───────────────────────────────────────────────────────────────────

def dry_run():
    print_header("DRY RUN — vantage_kernel_patch.py")

    print(f"\n{BOLD}[1/3] Leyendo Kernel page...{RESET}")
    try:
        top_blocks = get_children(KERNEL_PAGE_ID)
        print(f"  {GREEN}✓ {len(top_blocks)} bloques raíz encontrados{RESET}")
    except Exception as e:
        sys.exit(f"  {RED}ERROR: {e}{RESET}")

    print(f"\n{BOLD}[2/3] Localizando §4...{RESET}")
    sec4 = find_section_4_block(top_blocks)
    if sec4:
        sec4_text = block_text(sec4)
        print(f"  {GREEN}✓ §4 encontrado: {sec4_text[:80]!r}  [{sec4['id']}]{RESET}")

        jd_block, children = find_jd_block_in_section(sec4["id"])
        if jd_block:
            print(f"  {GREEN}✓ Bloque JD anchor: {block_text(jd_block)[:60]!r}  [{jd_block['id']}]{RESET}")
        else:
            print(f"  {YELLOW}⚠ No se encontró bloque con 'jd' en §4. Se hará append al final de §4.{RESET}")

        if already_patched(children):
            print(f"  {YELLOW}⚠ NOTA: La nota de cobertura JD ya parece estar insertada. Revisar antes de ejecutar.{RESET}")

        insert_after = jd_block["id"] if jd_block else sec4["id"]
        print(f"  Insertar después de bloque: {insert_after}")

    else:
        print(f"  {YELLOW}⚠ §4 no encontrado por heading. Se hará append al final de la página.{RESET}")
        print(f"  Bloques raíz disponibles (primeros 10):")
        for b in top_blocks[:10]:
            txt = block_text(b)[:60]
            print(f"    [{b['type']}] {txt!r}")
        insert_after = KERNEL_PAGE_ID

    print(f"\n{BOLD}[3/3] Bloque a insertar:{RESET}\n")
    print("  ┌─ CALLOUT (⚠️ amarillo) ──────────────────────────────")
    for line in JD_COVERAGE_NOTE_LINES:
        print(f"  │ {line}")
    print("  └────────────────────────────────────────────────────")

    print(f"\n{BOLD}Destino:{RESET} append como hijo de bloque {insert_after}")
    print(f"\n{GREEN}{BOLD}✓ Dry-run completo.{RESET}")
    print(f"  Para aplicar: {BOLD}python vantage_kernel_patch.py --execute{RESET}")


# ── Execute ───────────────────────────────────────────────────────────────────

def execute():
    print_header("EXECUTE — vantage_kernel_patch.py")

    print(f"\n[1/3] Leyendo Kernel...")
    top_blocks = get_children(KERNEL_PAGE_ID)

    print(f"[2/3] Localizando §4 y verificando duplicados...")
    sec4 = find_section_4_block(top_blocks)

    if sec4:
        jd_block, children = find_jd_block_in_section(sec4["id"])

        if already_patched(children):
            print(f"{YELLOW}⚠ La nota ya está insertada. Abortando para evitar duplicado.{RESET}")
            sys.exit(0)

        # Intentamos insertar como hijo del §4 block si tiene children habilitado.
        # Si §4 es heading_2/heading_3, Notion permite children.
        parent_id = sec4["id"]
    else:
        print(f"{YELLOW}⚠ §4 no localizado. Appending a página raíz.{RESET}")
        parent_id = KERNEL_PAGE_ID

    print(f"[3/3] Insertando callout en {parent_id}...")
    callout = build_callout_block(JD_COVERAGE_CALLOUT_TEXT)

    try:
        notion_patch(
            f"/blocks/{parent_id}/children",
            {"children": [callout]},
        )
        print(f"\n{GREEN}{BOLD}✓ Fase 3 completa. Nota JD insertada en Kernel §4.{RESET}")
        print(f"  Verifica en Notion: https://app.notion.com/p/{KERNEL_PAGE_ID.replace('-', '')}")
    except httpx.HTTPStatusError as e:
        # Si el bloque heading no acepta children, fallback a página raíz
        if e.response.status_code == 400:
            print(f"  {YELLOW}Heading no acepta children directos. Appending a página raíz...{RESET}")
            notion_patch(
                f"/blocks/{KERNEL_PAGE_ID}/children",
                {"children": [callout]},
            )
            print(f"\n{GREEN}{BOLD}✓ Fase 3 completa (append raíz).{RESET}")
        else:
            raise

    print(f"\n{BOLD}Plan completo:{RESET}")
    print(f"  Fase 1 ✓  Script Library + Changelog v8.7.2")
    print(f"  Fase 2 ✓  Bug Tracker cerrado")
    print(f"  Fase 3 ✓  Kernel §4 documentado")
    print(f"\n  Pendientes manuales:")
    print(f"  - D-04: confirmar Fix F → cerrar con: python vantage_bug_close.py --id D04 --execute")
    print(f"  - BUG-A: alias vdoc en shell (fix en disco)")
    print(f"  - BUG-B: vantageKey → key en code.js (fix en disco)")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="VANTAGE Kernel Patch — Fase 3")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true")
    group.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        dry_run()
    else:
        confirm = input(
            f"\n{YELLOW}⚠ APROBAR escritura en Kernel §4 de Notion? [yep/sí]: {RESET}"
        ).strip().lower()
        if confirm not in ("yep", "sí", "si"):
            print("Abortado.")
            sys.exit(0)
        execute()


if __name__ == "__main__":
    main()
