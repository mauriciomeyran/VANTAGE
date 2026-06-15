#!/usr/bin/env python3
"""Prueba paginación correcta usando el endpoint de data_sources (multi-source DBs).
No modifica nada. Corre con: python3 scripts/test_datasource_query.py
"""

import os
import httpx
from dotenv import load_dotenv

DATA_SOURCE_ID = "442938be-fc42-828f-b72e-076818d65a5b"  # Tracker collection (Cédula Digital)
NOTION_VERSION = "2025-09-03"
MAX_PAGES = 15

load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
token = os.environ["NOTION_TOKEN"]

headers = {
    "Authorization": f"Bearer {token}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json",
}

url = f"https://api.notion.com/v1/data_sources/{DATA_SOURCE_ID}/query"

seen_ids = set()
cursor = None

with httpx.Client(timeout=30) as client:
    for page in range(1, MAX_PAGES + 1):
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor

        resp = client.post(url, headers=headers, json=body)

        if resp.status_code != 200:
            print(f"[page {page}] ERROR {resp.status_code}: {resp.text[:500]}")
            break

        data = resp.json()
        batch = data.get("results", [])
        new_ids = [item["id"] for item in batch]
        dup_vs_seen = sum(1 for i in new_ids if i in seen_ids)

        print(
            f"[page {page}] count={len(batch)} "
            f"dup_vs_anteriores={dup_vs_seen} "
            f"has_more={data.get('has_more')} "
            f"next_cursor={data.get('next_cursor')}"
        )

        if dup_vs_seen > 0:
            print(">> Repetidos otra vez. Mismo problema en este endpoint también.")
            break

        seen_ids.update(new_ids)

        if not data.get("has_more"):
            print(">> has_more=False, terminó normalmente. Esto SÍ funcionó bien.")
            break

        cursor = data.get("next_cursor")

print(f"\nTotal IDs únicos vistos: {len(seen_ids)}")
