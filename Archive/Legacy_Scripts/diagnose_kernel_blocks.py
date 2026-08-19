"""
DIAGNÓSTICO READ-ONLY — no escribe nada en Notion.
Objetivo: confirmar tipo real de bloque (heading_2/3, toggle, has_children)
alrededor de las secciones OWNERSHIP, TRIGGERS, GATE-DECISION, NAMING-CONVENTION
en el Kernel, para diagnosticar por qué generate_census.py no resuelve
esos 10 IDs.

Uso: python3 diagnose_kernel_blocks.py
(correr desde donde generate_census.py encuentra su layer_1.env, o ajustar
dotenv_path abajo)
"""
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

script_dir = Path(__file__).resolve().parent
dotenv_path = script_dir.parent / "config" / "layer_1.env"
if not dotenv_path.exists():
    # fallback: mismo layout que generate_census.py (Layer_1/scripts/)
    dotenv_path = Path("Layer_1/config/layer_1.env")

load_dotenv(dotenv_path=dotenv_path)
NOTION_TOKEN = os.getenv("NOTION_TOKEN") or os.getenv("NOTION_API_KEY")
if not NOTION_TOKEN:
    print("[ERROR] No se encontró NOTION_TOKEN. Ajusta dotenv_path en este script.")
    raise SystemExit(1)

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
}

KERNEL_ID = "377938be-fc42-805e-a408-c9ae518d4fe7"

TARGET_SNIPPETS = [
    "KERNEL:OWNERSHIP-001", "KERNEL:OWNERSHIP-002",
    "KERNEL:TRIGGER-001", "KERNEL:TRIGGER-002", "KERNEL:TRIGGER-005",
    "KERNEL:TRIGGER-006", "KERNEL:TRIGGER-007", "KERNEL:TRIGGER-009",
    "GATE-DECISION-004", "KERNEL:NAMING-CONVENTION",
]


def get_children(block_id):
    """Pagina completo — bug anterior: solo pedía 1 página (100 bloques)."""
    results = []
    cursor = None
    while True:
        params = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor
        r = requests.get(
            f"https://api.notion.com/v1/blocks/{block_id}/children",
            headers=HEADERS, params=params,
        )
        if r.status_code != 200:
            print(f"[ERROR {r.status_code}] {block_id}: {r.text[:200]}")
            break
        data = r.json()
        results.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return results


def block_text(b):
    btype = b["type"]
    payload = b.get(btype, {})
    if isinstance(payload, dict) and "rich_text" in payload:
        return "".join(s.get("plain_text", "") for s in payload["rich_text"])
    return ""


def walk(block_id, depth=0, max_depth=4):
    for b in get_children(block_id):
        btype = b["type"]
        text = block_text(b)
        payload = b.get(btype, {})
        is_toggle = payload.get("is_toggleable") if isinstance(payload, dict) else None
        has_children = b.get("has_children")

        flag = ""
        if any(snip in text for snip in TARGET_SNIPPETS):
            flag = "  <<< TARGET"

        print(
            "  " * depth
            + f"[{btype}] has_children={has_children} toggle={is_toggle} :: {text[:80]}{flag}"
        )

        if has_children and depth < max_depth and btype not in ("child_page", "child_database"):
            walk(b["id"], depth + 1, max_depth)


HEADING_TYPES = {"heading_1", "heading_2", "heading_3"}


def find_and_walk_from(block_id, marker_snippets, stop_snippets=None, max_depth=2):
    """
    Activa impresión solo cuando un HEADING (no cualquier bloque, para
    evitar falsos positivos como el bloque `code` del TOC) contiene uno
    de marker_snippets. Corta al toparse con un heading_1 o heading_2
    real de nivel superior que no sea parte de la sección buscada.
    """
    stop_snippets = stop_snippets or []
    children = get_children(block_id)
    printing = False
    for b in children:
        btype = b["type"]
        text = block_text(b)
        is_target_heading = btype in HEADING_TYPES and any(m in text for m in marker_snippets)
        is_stop_heading = (
            printing
            and btype in ("heading_1", "heading_2")
            and not is_target_heading
            and any(s in text for s in stop_snippets)
        )

        if is_target_heading:
            printing = True

        if is_stop_heading:
            print(f"--- STOP en: [{btype}] {text[:60]} ---")
            break

        if printing:
            payload = b.get(btype, {})
            is_toggle = payload.get("is_toggleable") if isinstance(payload, dict) else None
            has_children = b.get("has_children")
            flag = "  <<< TARGET" if any(snip in text for snip in TARGET_SNIPPETS) else ""
            print(f"[{btype}] has_children={has_children} toggle={is_toggle} :: {text[:90]}{flag}")
            if has_children and btype not in ("child_page", "child_database"):
                walk(b["id"], depth=1, max_depth=max_depth)


if __name__ == "__main__":
    print("=== Volcado COMPLETO de hijos top-level de la página KERNEL (sin filtro) ===\n")
    children = get_children(KERNEL_ID)
    print(f"Total de bloques top-level encontrados: {len(children)}\n")
    for i, b in enumerate(children):
        btype = b["type"]
        text = block_text(b)
        has_children = b.get("has_children")
        print(f"{i:3d}. [{btype}] has_children={has_children} :: {text[:80]}")
