
#!/usr/bin/env python3

import os, sys, time

_venv_site = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".venv", "lib")

for _entry in os.listdir(_venv_site):

    _sp = os.path.join(_venv_site, _entry, "site-packages")

    if os.path.isdir(_sp):

        sys.path.insert(0, _sp)

        break

from dotenv import load_dotenv

from notion_utils import Client

load_dotenv()

NOTION_TOKEN = os.environ.get("NOTION_TOKEN") or os.environ.get("NOTION_API_KEY")

COLLECTION_ID = "442938be-fc42-828f-b72e-076818d65a5b"

NOT_FOUND = [

    ("Escaparatista y Coordinador VM", "Comercializadora E-Akluck"),

    ("Supervisor VM Victoria's Secret Mitikah", "Grupo Axo"),

    ("Coordinador Trade Marketing VM", "MANSI SERVICIOS S.C."),

    ("Coordinador VM y trademarketing", "GILSA"),

    ("Subgerente / Responsable VM", "NIKE Artz Pedregal"),

    ("Retail Instore VM - Antenas", "PUMA Group"),

    ("Subgerente VM NIKE Artz Pedregal CDMX", "Nike"),

    ("Supervisor VM", "Victoria's Secret"),

    ("Retail Instore VM - Antenas", "PUMA"),

    ("VM retail mobiliario y hogar", "GAIA Design"),

    ("Supervisor Jr VM", "IVONNE"),

    ("VM JR/ Gran Sur", "Puma México"),

    ("VM Coordinator", "DOLCE&GABBANA"),

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

    ("Coordinador VM", "Indeed"),

    ("VM Manager", "Indeed"),

]

def get_all_pages(notion):

    pages, cursor = [], None

    while True:

        body = {"page_size": 100}

        if cursor:

            body["start_cursor"] = cursor

        resp = notion.request(path=f"data_sources/{COLLECTION_ID}/query", method="POST", body=body, auth=None)

        pages.extend(resp["results"])

        if not resp.get("has_more"):

            break

        cursor = resp["next_cursor"]

    return pages

def extract_text(prop):

    if not prop: return ""

    kind = prop.get("type")

    if kind == "title": return "".join(t["plain_text"] for t in prop.get("title", []))

    if kind == "rich_text": return "".join(t["plain_text"] for t in prop.get("rich_text", []))

    if kind == "select":

        sel = prop.get("select"); return sel["name"] if sel else ""

    if kind == "checkbox": return "✅" if prop.get("checkbox") else "☐"

    return ""

if not NOTION_TOKEN:

    print("❌ NOTION_TOKEN no encontrado"); sys.exit(1)

notion = Client(auth=NOTION_TOKEN, notion_version="2025-09-03")

print("Cargando TODAS las páginas...")

pages = get_all_pages(notion)

print(f"  {len(pages)} páginas totales\n")

print(f"{'ROL':<45} {'MARCA':<30} {'STATUS':<15} {'ARCHIVAR'}")

print("─" * 110)

still_missing = []

for rol, marca in NOT_FOUND:

    match = next((p for p in pages

        if extract_text(p["properties"].get("Rol", {})).strip().lower() == rol.strip().lower()

        and extract_text(p["properties"].get("Marca", {})).strip().lower() == marca.strip().lower()), None)

    if match:

        status = extract_text(match["properties"].get("Status", {}))

        archivar = extract_text(match["properties"].get("Archivar", {}))

        print(f"{rol:<45} {marca:<30} {status:<15} {archivar}")

    else:

        print(f"{rol:<45} {marca:<30} ⚠️  NO EXISTE")

        still_missing.append((rol, marca))

print(f"\n── Resumen ──")

print(f"  Encontradas: {len(NOT_FOUND) - len(still_missing)}")

print(f"  No existen: {len(still_missing)}")

