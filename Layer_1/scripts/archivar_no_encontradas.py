#!/usr/bin/env python3
import argparse, os, sys, time

# Detección de venv
venv_site = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".venv", "lib")
for entry in os.listdir(venv_site):
    sp = os.path.join(venv_site, entry, "site-packages")
    if os.path.isdir(sp):
        sys.path.insert(0, sp)
        break

from dotenv import load_dotenv
from notion_utils import Client

load_dotenv()
NOTION_TOKEN = os.environ.get("NOTION_TOKEN") or os.environ.get("NOTION_API_KEY")
COLLECTION_ID = "442938be-fc42-828f-b72e-076818d65a5b"
NOTA = "Perplexity Deep Research 2026-06-19: No encontrada."
DELAY = 0.35

TO_ARCHIVE = [
    ("Retail Design Manager", "Adidas"), ("Brand Environment Manager", "Nike"),
    ("Jefe de Visual Merchandising", "Louis Vuitton"), ("VM Coordinator", "Zara"),
    ("Retail Design", "Bershka"), ("Retail Design", "Nike"),
    ("Retail Design", "Massimo Dutti"), ("Brand Environment", "Nike"),
    ("Retail Design Manager", "Uniqlo"), ("Subgerente de Visual Merchandising NIKE Artz Pedregal CDMX", "Nike"),
    ("Visual Merchandiser", "Zara"), ("Visual Merchandiser", "Bershka"),
    ("Visual Merchandising Manager", "Indeed"), ("VM Coordinator", "H&M"),
    ("Brand Environment", "Gucci"), ("Brand Environment", "Calvin Klein"),
    ("Coordinador de Visual merchandising y trademarketing", "GILSA"),
    ("Retail Design", "Burberry"), ("Visual Merchandising JR/ Gran Sur", "Puma México"),
    ("Visual Merchandising / Montaje de Mobiliario (con automóvil)", "GRUPO EUROKOR DE MEXICO"),
    ("Coordinador Visual Merchandising", "Indeed"), ("AUXILIAR DE IMAGEN VISUAL - MODA", "EL NUEVO MUNDO S.A"),
    ("Visual Merchandiser", "M.T. DE MEXICO"), ("Visual Merchandiser", "Viena 360"),
    ("Visual Merchandiser", "Adecco"), ("Visual Merchandiser", "Multicont"),
    ("Visual Merchandiser", "Grupo Axo"), ("Visual Merchandiser", "Mercalogic"),
]

def get_all_pages(notion):
    pages, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor: body["start_cursor"] = cursor
        resp = notion.request(path=f"data_sources/{COLLECTION_ID}/query", method="POST", body=body, auth=None)
        pages.extend(resp["results"])
        if not resp.get("has_more"): break
        cursor = resp["next_cursor"]
    return pages

def extract_text(prop):
    if not prop: return ""
    kind = prop.get("type")
    if kind == "title": return "".join(t["plain_text"] for t in prop.get("title", []))
    if kind == "rich_text": return "".join(t["plain_text"] for t in prop.get("rich_text", []))
    if kind == "select": sel = prop.get("select"); return sel["name"] if sel else ""
    return ""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    if not NOTION_TOKEN:
        print("❌ NOTION_TOKEN no encontrado"); sys.exit(1)
    
    notion = Client(auth=NOTION_TOKEN, notion_version="2025-09-03")
    pages = get_all_pages(notion)
    
    for rol, marca in TO_ARCHIVE:
        match = next((p for p in pages if extract_text(p["properties"].get("Rol", {})).strip().lower() == rol.strip().lower() and extract_text(p["properties"].get("Marca", {})).strip().lower() == marca.strip().lower()), None)
        if match:
            if not args.dry_run:
                notion.pages.update(page_id=match["id"], properties={
                    "Status": {"select": {"name": "Expirada"}},
                    "Archivar": {"checkbox": True}
                })
                print(f"✅ {rol} | {marca}")
            else:
                print(f"[DRY RUN] {rol} | {marca}")
            time.sleep(DELAY)

if __name__ == "__main__":
    main()
