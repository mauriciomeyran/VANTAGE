#!/usr/bin/env python3
"""Identifica las 24 páginas creadas por el reingest previo (v9.21.59) en el Tracker
y las lista para borrado/reingesta. Cruza los hashes del JSON de reingesta con las
páginas actuales del Tracker vía Notion API."""

import json
import os
import sys
from pathlib import Path

# Setup de entorno como hace feed_processor.py
_L1_ROOT = Path(__file__).resolve().parent.parent  # Layer_1/
os.environ.setdefault("NOTION_TOKEN", "")
os.environ.setdefault("NOTION_DB_OPPORTUNITIES", "")

from dotenv import load_dotenv
load_dotenv(_L1_ROOT / ".env", override=True)

from notion_client import Client

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DB_ID = os.environ["NOTION_DB_OPPORTUNITIES"]

client = Client(auth=NOTION_TOKEN)

# Hash tags para búsqueda
with open(Path(__file__).parent / "reingest_consolidated_format.json") as f:
    data = json.load(f)

records = data["consolidated_results"]
target_hashes = set()
for r in records:
    h = r.get("hash", "").strip()
    if h and h != "N/A":
        target_hashes.add(h)

print(f"🧲 Hashes objetivo (con valor): {len(target_hashes)}")
for h in sorted(target_hashes):
    print(f"   {h}")

print("\n🔍 Consultando Tracker vía Notion API...")

# Query paginado del Tracker
all_pages = []
next_cursor = None
while True:
    kwargs = {
        "database_id": NOTION_DB_ID,
        "page_size": 100,
    }
    if next_cursor:
        kwargs["start_cursor"] = next_cursor
    resp = client.databases.query(**kwargs)
    results = resp.get("results", [])
    all_pages.extend(results)
    next_cursor = resp.get("next_cursor")
    if not next_cursor:
        break

print(f"📊 Páginas totales en Tracker: {len(all_pages)}")

# Cruce: páginas que tienen uno de los hashes objetivo
matching = []
for page in all_pages:
    props = page.get("properties", {})
    hash_prop = props.get("hash", {})
    hash_val = ""
    if hash_prop:
        rich_text = hash_prop.get("rich_text", [])
        if rich_text:
            hash_val = rich_text[0].get("plain_text", "")
    if hash_val in target_hashes:
        matching.append({
            "page_id": page["id"],
            "hash": hash_val,
            "title": "",
            "status": "",
            "brand": "",
        })
        # Extraer título y status
        title_prop = props.get("title", {})
        if title_prop:
            tt = title_prop.get("title", [])
            if tt:
                matching[-1]["title"] = tt[0].get("plain_text", "")
        status_prop = props.get("Status", {})
        if status_prop:
            sel = status_prop.get("select", {})
            matching[-1]["status"] = sel.get("name", "")
        brand_prop = props.get("Marca", {})
        if brand_prop:
            rt = brand_prop.get("rich_text", [])
            if rt:
                matching[-1]["brand"] = rt[0].get("plain_text", "")

print(f"\n✅ Páginas coincidentes (hash en reingesta): {len(matching)}")
print("=" * 100)
for i, m in enumerate(matching, 1):
    print(f"{i:2d}. page_id={m['page_id'][:8]}...  hash={m['hash'][:24]:24s}  "
          f"brand={m['brand'][:25]:25s}  title={m['title'][:40]:40s}  status={m['status']}")

# Páginas en Tracker que NO están en la reingesta
tracker_hashes = set()
for page in all_pages:
    props = page.get("properties", {})
    hash_prop = props.get("hash", {})
    if hash_prop:
        rt = hash_prop.get("rich_text", [])
        if rt:
            tracker_hashes.add(rt[0].get("plain_text", ""))

other_hashes = tracker_hashes - target_hashes
print(f"\n📋 Páginas en Tracker NO en la reingesta: {len(other_hashes)}")
if other_hashes:
    print("(estas NO se deben borrar — son registros anteriores al reingest de hoy)")
    for h in sorted(other_hashes)[:10]:
        print(f"   {h[:24]}...")
    if len(other_hashes) > 10:
        print(f"   ... y {len(other_hashes)-10} más")

# Resumen final
print("\n" + "=" * 100)
print("RESUMEN PARA BORRADO:")
print(f"  Total páginas a borrar/arquivar: {len(matching)}")
print(f"  Total páginas a conservar: {len(other_hashes)}")
print(f"  Archivo JSON: reingest_consolidated_format.json ({len(records)} registros)")
print(f"\n⚠️  Ejecutar borrado requiere confirmación explícita del operador.")
print("    Por ahora solo se hizo el listado (dry-run).")
