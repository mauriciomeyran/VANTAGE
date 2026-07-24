"""
normalize_heading_ids.py
========================

Complemento de generate_census.py — audita los 6 documentos fundacionales
en busca de encabezados (heading_1/2/3) que contienen un ID con prefijo
válido (KERNEL:, MANUAL:, CANON:, CAREER_CANON:, SP:, ALIASES:, CHANGELOG:)
pero que NO respetan ninguna de las dos nomenclaturas canónicas reconocidas
por el sistema:

    (a) Heading = ID puro                    ej. "### KERNEL:ARCHITECTURE-L0"
    (b) Heading = "§N — ID"  (sección top)    ej. "## §22 — KERNEL:DOC-CONTRACT"
    (c) Subsecciones jerárquicas             ej. "### §3.1 — DOCUMENTATION-001 - Contract"

Cualquier otra forma (ID a mitad de frase, "Sección 22: KERNEL:X", ID sin
el separador correcto, doble prefijo, etc.) se reporta como "mal formado".

MODO DEFAULT = solo lectura (dry-run). Genera un reporte en consola y un
CSV en disco. NO escribe nada en Notion salvo que se invoque con --apply
Y el operador confirme explícitamente, en línea con KERNEL:SCHEMA-006
(APROBAR_WRITE) y KERNEL:DATA-FLOW (DRY RUN -> APROBAR_WRITE -> Write).

Uso:
    python normalize_heading_ids.py                 # solo audita, imprime reporte
    python normalize_heading_ids.py --csv out.csv    # además exporta CSV
    python normalize_heading_ids.py --apply          # aplica fixes (pide confirmación)
    python normalize_heading_ids.py --apply --yes    # aplica sin prompt (usar con cuidado)
"""

import argparse
import csv
import os
import re
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

# ─── CONFIGURACIÓN (idéntica a generate_census.py) ────────────────────────────

# NOTA: este script vive en VANTAGE/Layer_1/scripts/ — se sube dos niveles
# (scripts -> Layer_1 -> VANTAGE) para llegar a VANTAGE/config/.
script_dir = Path(__file__).resolve().parent
dotenv_path = script_dir.parent / "config" / "layer_1.env"

if not dotenv_path.exists():
    print(f"[ERROR] No se encontró layer_1.env en {dotenv_path}")
    sys.exit(1)

load_dotenv(dotenv_path=dotenv_path)
NOTION_TOKEN = os.getenv("NOTION_TOKEN") or os.getenv("NOTION_API_KEY")

if not NOTION_TOKEN:
    print("[ERROR] Ni NOTION_TOKEN ni NOTION_API_KEY definidos en layer_1.env")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

VALID_PREFIXES = ("KERNEL:", "MANUAL:", "CANON:", "CAREER_CANON:", "SP:", "ALIASES:", "CHANGELOG:", "CHANGELOG_ARCHIVE:")

DOCUMENTS = {
    "System Prompt": "37b938be-fc42-8001-9b9b-fcf81130d274",
    "Manual":        "372938be-fc42-8050-9a67-e40857d7806e",
    "Kernel":        "377938be-fc42-805e-a408-c9ae518d4fe7",
    "Career Canon":  "377938be-fc42-8089-93f2-f52dbd2dec6c",
    "Aliases":       "37c938be-fc42-80d4-b9ae-f5969830331b",
    "Change Log":    "390938be-fc42-80e7-b429-d7d730339353",
}

# Change Log queda fuera del barrido de headings: sus entradas narran
# historia y mencionan IDs de pasada dentro de una oración ("v9.4.0 ...
# KERNEL:BOOTSTRAP-001 corregido..."). Nunca son la definición canónica
# de una sección — normalizarlas no solo no aporta nada, sino que puede
# corromper el registro histórico si se reescribe automáticamente
# (ver falso positivo confirmado en la corrida 2026-07-16 19:07).
SKIP_DOCS_FOR_HEADING_AUDIT = {"Change Log"}

# Patrón canónico "§N — ID" / "§N.M — ID" (em dash o guión corto, espacios flexibles con soporte estricto a subsecciones decimales)
SECTION_HEADING_PREFIX_RE = re.compile(r"^§[\d.]+\s*[—-]\s*")

# Un ID válido: uno de los prefijos + clave en mayúsculas/números/guiones
ID_TOKEN_RE = re.compile(
    r"(?:" + "|".join(re.escape(p) for p in VALID_PREFIXES) + r")[A-Z0-9][A-Z0-9_-]*"
)

HEADING_TYPES = {"heading_1", "heading_2", "heading_3"}

# ─── NOTION FETCH ──────────────────────────────────────────────────────────────

def fetch_blocks_recursive(block_id: str) -> list:
    """Trae todos los bloques (recursivo) de una página, con retry simple."""
    all_blocks = []
    cursor = None
    while True:
        url = f"https://api.notion.com/v1/blocks/{block_id}/children"
        params = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor

        for attempt in range(5):
            try:
                resp = requests.get(url, headers=HEADERS, params=params, timeout=60)
            except requests.exceptions.RequestException as e:
                print(f"[WARN] Intento {attempt + 1}/5 falló para {block_id}: {e}")
                time.sleep(2 + attempt * 2)
                continue
            if resp.status_code == 200:
                break
            time.sleep(2 + attempt * 2)
        else:
            print(f"[WARN] No se pudo leer children de {block_id} tras 5 intentos — se omite este bloque")
            resp = None

        if resp is None or resp.status_code != 200:
            continue

        data = resp.json()
        for block in data.get("results", []):
            all_blocks.append(block)
            if block.get("has_children"):
                all_blocks.extend(fetch_blocks_recursive(block["id"]))

        if data.get("has_more"):
            cursor = data.get("next_cursor")
        else:
            break

    return all_blocks


def get_plain_text(block: dict) -> str | None:
    btype = block["type"]
    if btype not in HEADING_TYPES:
        return None
    rich_text = block[btype].get("rich_text", [])
    return "".join(s.get("plain_text", "") for s in rich_text)


# ─── CLASIFICACIÓN ─────────────────────────────────────────────────────────────

def classify_heading(plain: str, id_str: str) -> str:
    """
    Devuelve 'ok_bare', 'ok_sectioned', 'ok_id_label', o 'malformed' para
    un heading que contiene id_str.

    IMPORTANTE: esta clasificación debe reflejar EXACTAMENTE las mismas
    nomenclaturas que generate_census.py acepta en is_definition_block —
    de lo contrario este script reporta como "mal formado" texto que el
    census ya reconoce perfectamente, generando falsos positivos.
    """
    stripped = plain.strip("` \n")

    # Nomenclatura (c): "... ID: PREFIX:KEY" en cualquier parte del heading
    if f"ID: {id_str}" in plain or stripped == f"ID: {id_str}":
        return "ok_id_label"

    # Nomenclatura (a): heading = ID puro.
    if stripped == id_str:
        return "ok_bare"

    # Nomenclatura (b): "§N — ID" o "§N.M — ID" al inicio del heading.
    heading_body = SECTION_HEADING_PREFIX_RE.sub("", stripped)
    if heading_body == id_str or heading_body.startswith(id_str):
        return "ok_sectioned"

    return "malformed"


def suggest_fix(plain: str, id_str: str) -> str:
    """
    Propone una reescritura canónica mínima: conserva cualquier número de
    sección detectado (incluyendo subsecciones decimales) y cualquier texto descriptivo
    que venga DESPUÉS del ID, pero garantiza el orden "§N — ID — resto".
    Si no se detecta número de sección, propone el heading como ID puro.
    """
    stripped = plain.strip("` \n")

    section_match = re.match(r"^(§[\d.]+)", stripped)
    # Texto restante quitando cualquier ocurrencia del ID y del número de sección
    remainder = stripped
    if section_match:
        remainder = remainder[len(section_match.group(1)):]
    remainder = remainder.replace(id_str, "")
    remainder = re.sub(r"^\s*[—-]\s*", "", remainder).strip(" —-")

    if section_match:
        base = f"{section_match.group(1)} — {id_str}"
    else:
        base = id_str

    return f"{base} — {remainder}".rstrip(" —") if remainder else base


# ─── MAIN AUDIT ────────────────────────────────────────────────────────────────

def audit() -> list[dict]:
    """
    Recorre todos los documentos y devuelve una lista de findings:
    { doc, block_id, current_text, id_str, status, suggested_fix, link }
    Solo se reportan headings clasificados como 'malformed'.
    """
    findings = []

    for doc_name, page_id in DOCUMENTS.items():
        if doc_name in SKIP_DOCS_FOR_HEADING_AUDIT:
            continue
        print(f"Auditando: {doc_name}...")
        blocks = fetch_blocks_recursive(page_id)
        page_id_clean = page_id.replace("-", "")

        for block in blocks:
            plain = get_plain_text(block)
            if plain is None:
                continue

            ids_in_heading = ID_TOKEN_RE.findall(plain)
            if not ids_in_heading:
                continue

            # Un heading normalmente referencia un solo ID propio; si aparece
            # más de uno, se evalúa el primero como "dueño" del heading.
            id_str = ids_in_heading[0]
            status = classify_heading(plain, id_str)

            if status == "malformed":
                block_id_clean = block["id"].replace("-", "")
                findings.append({
                    "doc": doc_name,
                    "block_id": block["id"],
                    "current_text": plain.strip(),
                    "id_str": id_str,
                    "status": status,
                    "suggested_fix": suggest_fix(plain, id_str),
                    "link": f"https://app.notion.com/p/{page_id_clean}#{block_id_clean}",
                })

    return findings


# ─── APPLY (escritura real vía API) ────────────────────────────────────────────

def apply_fix(finding: dict) -> bool:
    """
    Sobrescribe el rich_text del heading block con el texto sugerido,
    preservando el tipo de heading (heading_1/2/3) y sin tocar anotaciones
    de estilo del primer segmento (bold/color), si existen.
    """
    block_id = finding["block_id"]
    get_resp = requests.get(
        f"https://api.notion.com/v1/blocks/{block_id}", headers=HEADERS, timeout=30
    )
    if get_resp.status_code != 200:
        print(f"  [ERROR] No se pudo leer el bloque {block_id} antes de escribir.")
        return False

    block = get_resp.json()
    btype = block["type"]

    payload = {
        btype: {
            "rich_text": [
                {"type": "text", "text": {"content": finding["suggested_fix"]}}
            ]
        }
    }

    patch_resp = requests.patch(
        f"https://api.notion.com/v1/blocks/{block_id}",
        headers=HEADERS,
        json=payload,
        timeout=30,
    )
    if patch_resp.status_code != 200:
        print(f"  [ERROR] Falló el patch de {block_id}: {patch_resp.status_code} {patch_resp.text[:200]}")
        return False
    return True


# ─── ENTRY POINT ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Audita/normaliza IDs mal formados en headings.")
    parser.add_argument("--csv", type=str, default=None, help="Ruta de export CSV del reporte.")
    parser.add_argument("--apply", action="store_true", help="Aplica los fixes sugeridos vía Notion API.")
    parser.add_argument("--yes", action="store_true", help="Omite el prompt de confirmación con --apply.")
    args = parser.parse_args()

    print("\nNormalize Heading IDs — Auditoría v1.1 (Jerárquica)")
    print(f"Modo: {'APLICAR CAMBIOS' if args.apply else 'SOLO LECTURA (dry-run)'}")
    print("=" * 60)

    findings = audit()

    print("\n" + "=" * 60)
    if not findings:
        print("Ningún heading mal formado detectado. Nomenclatura 100% canónica.")
        return

    print(f"  Headings mal formados encontrados: {len(findings)}")
    print("-" * 60)
    for f in findings:
        print(f"  [{f['doc']}] {f['id_str']}")
        print(f"    Actual:    {f['current_text']!r}")
        print(f"    Sugerido:  {f['suggested_fix']!r}")
        print(f"    Link:      {f['link']}")
        print()

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=["doc", "id_str", "current_text", "suggested_fix", "link", "block_id"])
            writer.writeheader()
            for f in findings:
                writer.writerow({k: f[k] for k in writer.fieldnames})
        print(f"Reporte exportado a: {Path(args.csv).resolve()}")

    if not args.apply:
        print("\nModo dry-run: no se escribió nada en Notion.")
        print("Vuelve a correr con --apply para escribir los fixes sugeridos (pide confirmación).")
        return

    # ── DRY RUN previo a escritura real, en línea con KERNEL:DATA-FLOW ──
    print("\n" + "=" * 60)
    print("DRY RUN DE ESCRITURA — se aplicarán los siguientes cambios:")
    for f in findings:
        print(f"  [{f['doc']}] {f['current_text']!r}  ->  {f['suggested_fix']!r}")

    if not args.yes:
        confirm = input("\n¿Proceder con la escritura? Escribe APROBAR_WRITE para continuar: ").strip()
        if confirm not in {"APROBAR_WRITE", "APROBAR", "SÍ", "sí", "YEP", "yep"}:
            print("Cancelado. No se escribió nada.")
            return

    print("\nAplicando fixes...")
    ok, fail = 0, 0
    for f in findings:
        success = apply_fix(f)
        print(f"  [{'OK' if success else 'FAIL'}] {f['doc']} — {f['id_str']}")
        ok += success
        fail += not success

    print("-" * 60)
    print(f"  Aplicados con éxito: {ok}")
    print(f"  Fallidos:            {fail}")
    print("=" * 60)
    print("\nRecuerda: tras normalizar IDs, vuelve a correr generate_census.py")
    print("para regenerar el Census con la nomenclatura ya corregida (KERNEL:CENSUS-SYNC, Regla 1).")


if __name__ == "__main__":
    main()
