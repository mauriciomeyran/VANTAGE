#!/usr/bin/env python3
"""Diagnóstico rápido: ¿la paginación de la DB repite IDs o son filas reales distintas?
No modifica nada. Corre con: python3 diagnose_db.py
(desde la carpeta LAYER_1, con el venv activado, igual que consolidate_duplicates.py)
"""

import os
from dotenv import load_dotenv
from notion_utils import Client

DATABASE_ID = "596938befc42836baea7814a1491bd47"
MAX_PAGES = 15  # 15 x 100 = 1500, de sobra para detectar el patrón

load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
client = Client(auth=os.environ["NOTION_TOKEN"])

seen_ids = set()
cursor = None

for page in range(1, MAX_PAGES + 1):
    kwargs = {"page_size": 100}
    if cursor:
        kwargs["start_cursor"] = cursor

    response = client.databases.query(DATABASE_ID, **kwargs)
    batch = response.get("results", [])

    new_ids = [item["id"] for item in batch]
    dups_in_batch = len(new_ids) - len(set(new_ids))
    dups_vs_seen = sum(1 for i in new_ids if i in seen_ids)

    print(
        f"[page {page}] count={len(batch)} "
        f"dup_dentro_pagina={dups_in_batch} "
        f"dup_vs_anteriores={dups_vs_seen} "
        f"has_more={response.get('has_more')} "
        f"next_cursor={response.get('next_cursor')}"
    )

    if dups_vs_seen > 0:
        print(">> ENCONTRADOS IDs REPETIDOS DE PÁGINAS ANTERIORES. Ejemplo:")
        repeated = [i for i in new_ids if i in seen_ids][:3]
        for r in repeated:
            print("   ", r)
        break

    seen_ids.update(new_ids)

    if not response.get("has_more"):
        print(">> has_more=False, terminó normalmente.")
        break

    cursor = response.get("next_cursor")

print(f"\nTotal IDs únicos vistos: {len(seen_ids)}")

# Bonus: intenta leer el conteo total via la DB (si la API lo expone)
try:
    db = client.databases.retrieve(DATABASE_ID)
    print("\n[databases.retrieve] keys relevantes:")
    for k in ("id", "title", "in_trash", "archived", "is_inline"):
        if k in db:
            val = db[k]
            if k == "title" and isinstance(val, list):
                val = "".join(t.get("plain_text", "") for t in val)
            print(f"   {k}: {val}")
except Exception as exc:
    print(f"\n[databases.retrieve] error: {exc}")
