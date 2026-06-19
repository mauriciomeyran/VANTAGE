#!/usr/bin/env python3
"""
archivar_44.py
Archiva las 44 vacantes "no encontradas" del URL Repair Perplexity 2026-06-19.
Operación: Status=Expirada, Archivar=True, Notas append.

Uso:
  python3 archivar_44.py --dry-run   # muestra qué haría
  python3 archivar_44.py             # ejecuta

Requiere: notion-client, python-dotenv
  pip install notion-client python-dotenv --break-system-packages
"""

import argparse
import os
import sys
import time

# Fix: notion_client.py local tapa el paquete instalado
_venv_site = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".venv", "lib"
)
for _entry in os.listdir(_venv_site):
    _sp = os.path.join(_venv_site, _entry, "site-packages")
    if os.path.isdir(_sp):
        sys.path.insert(0, _sp)
        break

from dotenv import load_dotenv
from notion_client import Client

# ── Config ────────────────────────────────────────────────────────────────────
load_dotenv()
NOTION_TOKEN = os.environ.get("NOTION_TOKEN") or os.environ.get("NOTION_API_KEY")
DB_ID = "596938befc42836baea7814a1491bd47"
NOTA = "Perplexity Deep Research 2026-06-19: No encontrada."
DELAY = 0.35  # segundos entre writes (rate limit safety)

# ── Las 44 vacantes (rol, marca) ─────────────────────────────────────────────
TARGET_VACANTES = [
    ("Especialista en Visual Merchandising", "Liverpool"),
    ("Escaparatista y Coordinador VM", "Comercializadora E-Akluck"),
    ("Supervisor VM Victoria's Secret Mitikah", "Grupo Axo"),
    ("Coordinador Trade Marketing VM", "MANSI SERVICIOS S.C."),
    ("Visual Merchandiser", "IKEA"),
    ("Supervisor de Visual Merchandising", "Multicont"),
    ("Senior Visual Merchandising", "Prada"),
    ("Supervisor Visual Merchandising", "Grupo Encanto"),
    ("Supervisor Visual Merchandising", "Multicont"),
    ("Visual Merchandising", "precio y variedad"),
    ("Visual Merchandiser", "Ikano-Retail"),
    ("UX & Visual Designer", "Cosign"),
    ("Coordinador VM y trademarketing", "GILSA"),
    ("Subgerente / Responsable VM", "NIKE Artz Pedregal"),
    ("Retail Instore VM - Antenas", "PUMA Group"),
    ("Subgerente VM NIKE Artz Pedregal CDMX", "Nike"),
    ("Lead Visual Merchandiser", "Tory Burch"),
    ("VM Coordinator", "GUESS"),
    ("Supervisor VM", "Victoria's Secret"),
    ("Retail Instore VM - Antenas", "PUMA"),
    ("Senior Visual Merchandising", "Prada"),
    ("VM retail mobiliario y hogar", "GAIA Design"),
    ("Supervisor Jr VM", "IVONNE"),
    ("Visual Merchandiser", "H&M"),
    ("Trade Marketing Visual", "Puma"),
    ("VM JR/ Gran Sur", "Puma México"),
    ("VM Coordinator", "DOLCE&GABBANA"),
    ("Lead Visual Specialist", "Wizeline"),
    ("Senior Visual Designer Brand & Comms", "ION"),
    ("Auxiliar Imagen Visual Moda", "EL NUEVO MUNDO S.A"),
    ("VM Supervisor", "Levi Strauss & Co."),
    ("VM Coordinator", "LinkedIn"),
    ("VM Coordinator", "Oppdoor"),
    ("VM Coordinator", "Grupo Julio"),
    ("VM Coordinator", "Sears México"),
    ("VM Coordinator", "Euphoria"),
    ("Subgerente / Responsable VM", "NIKE"),
    ("VM / Montaje Mobiliario (con automóvil)", "GRUPO EUROKOR DE MEXICO"),
    ("Visual Merchandiser", "Confidencial"),
    ("Retail Visual Merchandiser", "Indeed"),
    ("Coordinador VM", "Indeed"),
    ("Visual Merchandising", "TANE México 1942"),
    ("Visual Merchandising", "Larrouse"),
    ("VM Manager", "Indeed"),
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_all_pages(notion: Client) -> list[dict]:
    """Trae todas las páginas del DB (pagina por pagina)."""
    pages = []
    cursor = None
    while True:
        kwargs = {
            "database_id": DB_ID,
            "page_size": 100,
            "filter": {
                "property": "Status",
                "select": {"does_not_equal": "Expirada"}
            }
        }
        if cursor:
            kwargs["start_cursor"] = cursor
        resp = notion.databases.query(**kwargs)
        pages.extend(resp["results"])
        if not resp.get("has_more"):
            break
        cursor = resp["next_cursor"]
    return pages


def extract_text(prop) -> str:
    """Extrae texto de una propiedad title o rich_text."""
    if not prop:
        return ""
    kind = prop.get("type")
    if kind == "title":
        return "".join(t["plain_text"] for t in prop.get("title", []))
    if kind == "rich_text":
        return "".join(t["plain_text"] for t in prop.get("rich_text", []))
    return ""


def match_page(page: dict, rol: str, marca: str) -> bool:
    """True si el page coincide con (rol, marca) — tolerante a mayúsculas."""
    props = page.get("properties", {})
    page_rol = extract_text(props.get("Rol", {})).strip().lower()
    page_marca = extract_text(props.get("Marca", {})).strip().lower()
    return page_rol == rol.strip().lower() and page_marca == marca.strip().lower()


def build_notas(existing_notas: str) -> str:
    """Agrega la nota si no está ya presente."""
    if NOTA in existing_notas:
        return existing_notas
    if existing_notas.strip():
        return existing_notas.strip() + "\n" + NOTA
    return NOTA


def archive_page(notion: Client, page_id: str, existing_notas: str, dry_run: bool) -> bool:
    new_notas = build_notas(existing_notas)
    if dry_run:
        print(f"  [DRY] {page_id} → Status=Expirada, Archivar=✅, Notas OK")
        return True
    notion.pages.update(
        page_id=page_id,
        properties={
            "Status": {"select": {"name": "Expirada"}},
            "Archivar": {"checkbox": True},
            "Notas": {"rich_text": [{"text": {"content": new_notas}}]},
        }
    )
    return True


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not NOTION_TOKEN:
        print("❌ NOTION_TOKEN no encontrado en .env")
        sys.exit(1)

    notion = Client(auth=NOTION_TOKEN)
    dry_run = args.dry_run

    print(f"{'[DRY RUN] ' if dry_run else ''}Cargando páginas del TRACKER...")
    pages = get_all_pages(notion)
    print(f"  {len(pages)} páginas encontradas (Status ≠ Expirada)\n")

    found = []
    not_found = []

    for rol, marca in TARGET_VACANTES:
        match = next((p for p in pages if match_page(p, rol, marca)), None)
        if match:
            found.append((rol, marca, match))
        else:
            not_found.append((rol, marca))

    print(f"✅ Encontradas: {len(found)}")
    print(f"⚠️  No encontradas en DB: {len(not_found)}\n")

    if not_found:
        print("── No encontradas (ya archivadas o no existen) ──")
        for rol, marca in not_found:
            print(f"  · {rol} | {marca}")
        print()

    print(f"── {'[DRY RUN] ' if dry_run else ''}Procesando {len(found)} páginas ──")
    ok = 0
    errors = []
    for rol, marca, page in found:
        page_id = page["id"]
        existing_notas = extract_text(page["properties"].get("Notas", {}))
        try:
            archive_page(notion, page_id, existing_notas, dry_run)
            print(f"  ✅ {rol} | {marca}")
            ok += 1
            if not dry_run:
                time.sleep(DELAY)
        except Exception as e:
            print(f"  ❌ {rol} | {marca} → {e}")
            errors.append((rol, marca, str(e)))

    print(f"\n── Resultado ──")
    print(f"  Procesadas: {ok}/{len(found)}")
    if errors:
        print(f"  Errores: {len(errors)}")
        for r, m, err in errors:
            print(f"    · {r} | {m}: {err}")
    if dry_run:
        print("\n  ℹ️  Dry run completo. Corre sin --dry-run para ejecutar.")
    else:
        print("\n  🎯 Listo.")


if __name__ == "__main__":
    main()
