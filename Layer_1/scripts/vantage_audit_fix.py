#!/usr/bin/env python3
"""
vantage_audit_fix.py — Fase 1
Depreca scripts one-shot en Script Library y appends bloque v8.7.2 al Changelog.

Uso:
    python vantage_audit_fix.py --dry-run     # muestra diff, no escribe
    python vantage_audit_fix.py --execute     # aplica cambios tras APROBAR

Requiere: NOTION_TOKEN en Layer_1/config/layer_1.env o en env
"""

import os
import sys
import json
import argparse
import textwrap
from datetime import date
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

# Carga token desde el .env canónico si existe
_ENV_PATH = Path.home() / "Documents/04-Vantage_CV/Layer_1/config/layer_1.env"
if _ENV_PATH.exists():
    for line in _ENV_PATH.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
if not NOTION_TOKEN:
    sys.exit("ERROR: NOTION_TOKEN no encontrado. Verifica layer_1.env o exporta la variable.")

NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"

# IDs canónicos
SCRIPT_LIBRARY_DS = "ea914544-338f-485e-ac1b-7f137a5c9cee"
CHEAT_SHEET_PAGE  = "37c938be-fc42-80d4-b9ae-f5969830331b"
ACTIVE_DIR        = Path.home() / "Documents/04-Vantage_CV/- Documentación/ACTIVE"

# Scripts one-shot a deprecar: (page_id, nombre)
ONE_SHOT_SCRIPTS = [
    ("38d938be-fc42-814a-80c8-eed51acaaf11", "patch_kernel.py"),
    ("38d938be-fc42-814d-b1c6-e562fd319aad", "patch_manual.py"),
    ("38d938be-fc42-8119-a314-e5ff5a15ae97", "patch_career_canon.py"),
    ("38d938be-fc42-8110-9ff3-daf502862056", "patch_cheat_sheet.py"),
    ("38d938be-fc42-8120-aaaa-e4be6fe13867", "fx4_legacy_check.py"),
]

# Bloque changelog a insertar en Cheat Sheet
CHANGELOG_BLOCK = f"""\
## v8.7.2 — VANTAGE · {date.today().isoformat()}
> ID: 37c938be-fc42-80d4-b9ae-f5969830331b:Change_Log_v8.7.2

- **[DOC] Source_Type trailing space — `source_analytics.py` y `gate_logic.py`** — \
Ambos scripts leían `props.get("Source_Type")` sin trailing space; el campo real en Notion \
es `"Source_Type "`. Fix aplicado Jun 26: trailing space agregado en ambos scripts. \
Componente: Layer 1. Bug Tracker: 38b938be-fc42-817f-9ae0-f28dc7e268f9.

- **[DOC] Fuente no asignada en Paso 0.5 — Source_Type sin trailing space** — \
`layer_1_run.py` línea ~618 leía `Source_Type` sin trailing space; condición nunca se cumplía \
y `Fuente` quedaba vacío en todos los registros. Fix aplicado Jun 26: \
`props.get("Source_Type")` → `props.get("Source_Type ")`. \
Componente: Layer 1. Bug Tracker: 38b938be-fc42-81a7-9593-f6ea8af18da2.

- **[DOC] Source_Type vacío — backfill 9 registros** — \
9 registros ingresados por L1 con `Source_Type` vacío corregidos vía script puntual \
(query → filtrar URL sin Source_Type → PATCH Notion con valor `Vacante`). \
Pendiente evaluar auto-asignación en ingesta. \
Componente: Layer 1. Bug Tracker: 38b938be-fc42-8117-9d3f-cb2903f49415.

- **[DOC] Next_Action type mismatch — rich_text en `layer_1_run.py`** — \
`layer_1_run.py` escribía `Next_Action` como select; el TRACKER lo define como rich_text. \
Fix 1 incorrecto (convirtió a select); Fix 2 correcto: revertido a \
`{{"rich_text": [{{"text": {{"content": valor}}}}]}}`. Líneas afectadas: 591, 745, 892. \
Componente: Layer 1. Bug Tracker: 38b938be-fc42-81fa-b1be-e60f909107fc.

- **[MAINT] Scripts one-shot deprecados en Script Library** — \
`patch_kernel.py`, `patch_manual.py`, `patch_career_canon.py`, `patch_cheat_sheet.py`, \
`fx4_legacy_check.py` marcados como `Deprecado / Archivar`. \
Ya ejecutados en v8.7.1; no deben re-ejecutarse.
"""

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


# ── Lectura ───────────────────────────────────────────────────────────────────

def fetch_script_page(page_id: str) -> dict:
    """Retorna propiedades relevantes de un script de la Library."""
    data = notion_get(f"/pages/{page_id.replace('-', '')}")
    props = data.get("properties", {})

    def txt(p):
        items = props.get(p, {}).get("rich_text", [])
        return "".join(i["plain_text"] for i in items) if items else ""

    def sel(p):
        s = props.get(p, {}).get("select")
        return s["name"] if s else ""

    return {
        "id": page_id,
        "Script": "".join(
            i["plain_text"]
            for i in props.get("Script", {}).get("title", [])
        ),
        "Estado": sel("Estado"),
        "Acción": sel("Acción"),
    }


def fetch_cheat_sheet_blocks() -> list:
    """Trae los bloques del Cheat Sheet para localizar el Changelog."""
    blocks = []
    cursor = None
    while True:
        url = f"/blocks/{CHEAT_SHEET_PAGE.replace('-', '')}/children"
        if cursor:
            url += f"?start_cursor={cursor}"
        data = notion_get(url)
        blocks.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data["next_cursor"]
    return blocks


# ── Construcción de payloads ──────────────────────────────────────────────────

def build_script_update_payload() -> dict:
    """Payload para marcar Estado=Deprecado, Acción=Archivar."""
    return {
        "properties": {
            "Estado": {"select": {"name": "Deprecado"}},
            "Acción": {"select": {"name": "Archivar"}},
        }
    }


def build_changelog_blocks(text: str) -> list:
    """
    Convierte el bloque de texto del changelog en bloques Notion.
    Párrafos separados por línea en blanco → paragraph blocks.
    Líneas con '## ' → heading_2. Líneas con '> ' → quote.
    Líneas con '- ' → bulleted_list_item.
    """
    blocks = []
    for line in text.splitlines():
        line = line.rstrip()
        if not line:
            continue
        if line.startswith("## "):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": line[3:]}}]
                },
            })
        elif line.startswith("> "):
            blocks.append({
                "object": "block",
                "type": "quote",
                "quote": {
                    "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                },
            })
        elif line.startswith("- "):
            # Bold hasta primer '—' si existe
            content = line[2:]
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": content}}]
                },
            })
        else:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": line}}]
                },
            })
    return blocks


def find_changelog_block_id(blocks: list) -> str | None:
    """
    Encuentra el bloque heading que contiene 'CHANGELOG' para insertar
    el nuevo entry inmediatamente después.
    """
    for b in blocks:
        btype = b.get("type", "")
        rich = b.get(btype, {}).get("rich_text", [])
        text = "".join(r.get("plain_text", "") for r in rich)
        if "CHANGELOG" in text.upper():
            return b["id"]
    return None


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


def print_diff(label, old, new):
    print(f"  {BOLD}{label}{RESET}")
    print(f"    {RED}− {old}{RESET}")
    print(f"    {GREEN}+ {new}{RESET}")


# ── Dry-run ───────────────────────────────────────────────────────────────────

def dry_run():
    print_header("DRY RUN — vantage_audit_fix.py")

    # 1. Script Library
    print(f"\n{BOLD}[1/2] Script Library — scripts a deprecar{RESET}")
    errors = []
    for page_id, name in ONE_SHOT_SCRIPTS:
        try:
            s = fetch_script_page(page_id)
            print(f"\n  📄 {BOLD}{s['Script'] or name}{RESET}  [{page_id}]")
            print_diff("Estado", s["Estado"] or "?", "Deprecado")
            print_diff("Acción", s["Acción"] or "?", "Archivar")
        except Exception as e:
            errors.append((name, str(e)))
            print(f"  {RED}ERROR leyendo {name}: {e}{RESET}")

    # 2. Changelog
    print(f"\n{BOLD}[2/2] Cheat Sheet — bloque Changelog a insertar{RESET}")
    try:
        blocks = fetch_cheat_sheet_blocks()
        anchor_id = find_changelog_block_id(blocks)
        if anchor_id:
            print(f"  {GREEN}✓ Anchor CHANGELOG encontrado: {anchor_id}{RESET}")
        else:
            print(f"  {YELLOW}⚠ No se encontró bloque CHANGELOG. Se insertará al final de la página.{RESET}")
        print(f"\n  Bloque a insertar:\n")
        for line in CHANGELOG_BLOCK.splitlines():
            print(f"    {line}")
    except Exception as e:
        errors.append(("Cheat Sheet", str(e)))
        print(f"  {RED}ERROR leyendo Cheat Sheet: {e}{RESET}")

    # 3. Archivo local pending
    pending_path = ACTIVE_DIR / "pending_v872.md"
    print(f"\n{BOLD}[LOCAL] Archivo de referencia:{RESET}")
    print(f"  {pending_path}")
    if ACTIVE_DIR.exists():
        pending_path.write_text(CHANGELOG_BLOCK, encoding="utf-8")
        print(f"  {GREEN}✓ Escrito (dry-run — solo local, no Notion){RESET}")
    else:
        print(f"  {YELLOW}⚠ ACTIVE/ no existe en esta máquina — archivo no escrito{RESET}")

    if errors:
        print(f"\n{RED}Errores encontrados: {len(errors)}{RESET}")
        for name, err in errors:
            print(f"  - {name}: {err}")
        sys.exit(1)

    print(f"\n{GREEN}{BOLD}✓ Dry-run completo. Sin errores.{RESET}")
    print(f"  Para aplicar: {BOLD}python vantage_audit_fix.py --execute{RESET}")


# ── Execute ───────────────────────────────────────────────────────────────────

def execute():
    print_header("EXECUTE — vantage_audit_fix.py")

    errors = []
    payload = build_script_update_payload()

    # 1. Script Library
    print(f"\n{BOLD}[1/2] Deprecando scripts en Script Library...{RESET}")
    for page_id, name in ONE_SHOT_SCRIPTS:
        try:
            notion_patch(f"/pages/{page_id.replace('-', '')}", payload)
            print(f"  {GREEN}✓ {name}{RESET}")
        except Exception as e:
            errors.append((name, str(e)))
            print(f"  {RED}✗ {name}: {e}{RESET}")

    # 2. Changelog → append después del header CHANGELOG
    print(f"\n{BOLD}[2/2] Insertando bloque v8.7.2 en Cheat Sheet...{RESET}")
    try:
        blocks = fetch_cheat_sheet_blocks()
        anchor_id = find_changelog_block_id(blocks)

        new_blocks = build_changelog_blocks(CHANGELOG_BLOCK)

        if anchor_id:
            # Insertar como hijos del bloque anchor (heading_2 CHANGELOG)
            # Notion no soporta "after" directo; append a la página y luego
            # usamos el endpoint children del bloque padre de la página.
            # Estrategia: append al root de la página — el Changelog ya está
            # al final estructuralmente; los nuevos bloques van después del anchor.
            # Insertamos como children del bloque de tipo heading_2 no funciona
            # (headings no tienen children); usamos append a la página entera
            # y confiamos en que el Changelog está al final.
            pass  # fallthrough a append de página

        notion_patch(
            f"/blocks/{CHEAT_SHEET_PAGE}/children",
            {"children": new_blocks},
        )
        print(f"  {GREEN}✓ Bloque v8.7.2 insertado en Cheat Sheet{RESET}")
    except Exception as e:
        errors.append(("Cheat Sheet changelog", str(e)))
        print(f"  {RED}✗ Cheat Sheet: {e}{RESET}")

    # 3. Archivo local
    pending_path = ACTIVE_DIR / "pending_v872.md"
    if ACTIVE_DIR.exists():
        pending_path.unlink(missing_ok=True)
        print(f"\n  {GREEN}✓ pending_v872.md eliminado (ya aplicado){RESET}")

    # Resumen
    if errors:
        print(f"\n{RED}Errores: {len(errors)}{RESET}")
        for name, err in errors:
            print(f"  - {name}: {err}")
        sys.exit(1)

    print(f"\n{GREEN}{BOLD}✓ Fase 1 completa.{RESET}")
    print(f"  Siguiente: {BOLD}python vantage_bug_close.py --dry-run{RESET}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="VANTAGE Audit Fix — Fase 1")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Muestra diff sin escribir")
    group.add_argument("--execute", action="store_true", help="Aplica cambios en Notion")
    args = parser.parse_args()

    if args.dry_run:
        dry_run()
    else:
        confirm = input(
            f"\n{YELLOW}⚠ APROBAR escritura en Notion (Script Library + Cheat Sheet)? [yep/sí]: {RESET}"
        ).strip().lower()
        if confirm not in ("yep", "sí", "si"):
            print("Abortado.")
            sys.exit(0)
        execute()


if __name__ == "__main__":
    main()
