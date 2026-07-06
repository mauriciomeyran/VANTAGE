#!/usr/bin/env python3
"""
VANTAGE ID Collision Resolver
Resuelve colisiones de IDs en bloques Notion según Reglas 1-4.
"""

import os
import sys
import time
import requests
import argparse
from pathlib import Path
from dotenv import load_dotenv

# ── ENTORNO ───────────────────────────────────────────────────────────────────
script_dir = Path(__file__).resolve().parent
dotenv_path = script_dir.parent / "config" / "layer_1.env"

if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)
else:
    print(f"Error crítico: No se encontró {dotenv_path}")
    sys.exit(1)

NOTION_API_KEY = os.getenv("NOTION_TOKEN")
if not NOTION_API_KEY:
    print("Error: NOTION_TOKEN es nulo en layer_1.env")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

# ── MATRIZ DE MUTACIONES (Reglas 1-4 aplicadas) ───────────────────────────────
# Formato: (block_uuid, texto_actual, texto_propuesto, motivo)
MUTATION_MAP = [
    # REGLA 1: System Prompt → prefijo KERNEL: migra a PROMPT:
    ("392938be-fc42-8135-9c2d-e3e320613566", "KERNEL:SCOPE",     "PROMPT:SCOPE",     "Regla1: SP vs Kernel"),
    ("392938be-fc42-817b-8b66-e51baaedf9e6", "KERNEL:DATA-FLOW", "PROMPT:DATA-FLOW", "Regla1: SP vs Kernel"),
    ("392938be-fc42-8149-8bb9-ee253c294af6", "KERNEL:ROUTING",   "PROMPT:ROUTING",   "Regla1: SP vs Kernel"),

    # REGLA 2: Manual → sufijo _REF (Kernel retiene nombre canónico)
    ("e8337416-a57c-478b-a393-6b64b8a4df8e", "KERNEL:FAIL-PHILOSOPHY", "KERNEL:FAIL-PHILOSOPHY_REF", "Regla2: Manual vs Kernel (triple)"),
    ("390938be-fc42-80b2-86a4-f0f25bfe66aa", "KERNEL:FAIL-PHILOSOPHY", "KERNEL:FAIL-PHILOSOPHY_REF", "Regla2: Manual vs Kernel (triple)"),
    ("390938be-fc42-80bc-9e78-e71f867fa283", "KERNEL:CV-GOLDEN-RULES", "KERNEL:CV-GOLDEN-RULES_REF", "Regla2: Manual vs Kernel"),
    ("fe66c3b6-fdae-43a5-9c36-c134c889ad9b", "KERNEL:CV-PIPELINE",     "KERNEL:CV-PIPELINE_REF",     "Regla2: Manual vs Kernel"),

    # REGLA 3: Duplicados internos Kernel/Kernel → 2do bloque _DEPRECATED
    ("6e2802a4-0004-4bb0-91bd-623c799b8d0c", "KERNEL:TRACKER-SCHEMA",  "KERNEL:TRACKER-SCHEMA_DEPRECATED",  "Regla3: Kernel interno (2do bloque)"),
    ("390938be-fc42-8091-8991-e326448a5730", "KERNEL:OWNERSHIP",        "KERNEL:OWNERSHIP_DEPRECATED",        "Regla3: Kernel interno (2do bloque)"),
    ("e0ff8ae5-bd56-45fe-bd58-eea192292c03", "KERNEL:ARCHITECTURE-L4",  "KERNEL:ARCHITECTURE-L4_DEPRECATED",  "Regla3: Kernel interno (2do bloque)"),
    ("a89e86d2-4998-408c-8f0b-48ee330536d4", "KERNEL:DOC-CONTRACT",     "KERNEL:DOC-CONTRACT_DEPRECATED",     "Regla3: Kernel interno (2do bloque)"),

    # REGLA 4: Legacy [DT-015] — segunda instancia
    ("9d24816b-922e-4e88-a99e-16a4e2cb51f6", "[DT-015]_NORMALIZACIÓN...", "[DT-015]_NORMALIZACIÓN_DE_IDS_LEGACY_A_E_V2", "Regla4: Legacy"),
]


# ── HELPERS ───────────────────────────────────────────────────────────────────
def get_block_text(block_id: str) -> str:
    """Fetches current plain_text from a block."""
    url = f"https://api.notion.com/v1/blocks/{block_id}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 429:
        time.sleep(int(r.headers.get("Retry-After", 1)))
        return get_block_text(block_id)
    if r.status_code != 200:
        return f"[ERROR {r.status_code}]"
    data = r.json()
    btype = data.get("type", "")
    rich = data.get(btype, {}).get("rich_text", [])
    return "".join(rt.get("plain_text", "") for rt in rich)


def patch_block_text(block_id: str, new_text: str, btype: str = "paragraph") -> int:
    """Patches the rich_text of a block. Returns HTTP status code."""
    url = f"https://api.notion.com/v1/blocks/{block_id}"
    payload = {
        btype: {
            "rich_text": [{"type": "text", "text": {"content": new_text}}]
        }
    }
    r = requests.patch(url, headers=HEADERS, json=payload)
    if r.status_code == 429:
        time.sleep(int(r.headers.get("Retry-After", 1)))
        return patch_block_text(block_id, new_text, btype)
    return r.status_code


# ── DRY RUN REPORT ────────────────────────────────────────────────────────────
def dry_run():
    print("\n" + "="*60)
    print(" DRY RUN — REPORTE PRE-MUTACIÓN")
    print("="*60)
    for uuid, expected_current, proposed, reason in MUTATION_MAP:
        actual = get_block_text(uuid)
        match = "✓" if expected_current in actual else "⚠ TEXTO DISTINTO AL ESPERADO"
        print(f"\n[{uuid}]")
        print(f"  Regla     : {reason}")
        print(f"  Actual    : {actual!r}")
        print(f"  Propuesto : {proposed!r}")
        print(f"  Match     : {match}")
        time.sleep(0.35)
    print("\n" + "="*60)
    print(" Dry run completo. Ejecuta sin --dry-run para aplicar cambios.")
    print("="*60 + "\n")


# ── EJECUCIÓN REAL ────────────────────────────────────────────────────────────
def execute():
    print("\n" + "="*60)
    print(" EJECUTANDO MUTACIONES EN NOTION")
    print("="*60)
    ok, fail = 0, 0
    for uuid, _, proposed, reason in MUTATION_MAP:
        status = patch_block_text(uuid, proposed)
        tag = "✓ OK" if status == 200 else f"✗ ERROR {status}"
        print(f"[{uuid}] {tag} → {proposed!r} ({reason})")
        if status == 200:
            ok += 1
        else:
            fail += 1
        time.sleep(0.35)
    print(f"\nResultado: {ok} exitosos / {fail} fallidos")
    print("="*60 + "\n")


# ── ENTRYPOINT ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VANTAGE ID Collision Resolver")
    parser.add_argument("--dry-run", action="store_true",
                        help="Imprime el reporte sin escribir en Notion")
    args = parser.parse_args()

    if args.dry_run:
        dry_run()
    else:
        print("⚠️  Estás a punto de mutar 12 bloques en Notion. ¿Continuar? [s/N]: ", end="")
        confirm = input().strip().lower()
        if confirm == "s":
            execute()
        else:
            print("Abortado.")
