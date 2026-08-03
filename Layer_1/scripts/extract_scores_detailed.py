#!/usr/bin/env python3
"""Extrae histograma detallado de Score del Tracker actual"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import sys as _sys
_scripts_dir = str(Path(__file__).resolve().parent)
_saved_path = _sys.path[:]
_saved_nc = _sys.modules.pop("notion_utils", None)
_sys.path = [p for p in _sys.path if p not in (_scripts_dir, ".", "")]
try:
    from notion_client import Client
finally:
    _sys.path = _saved_path
    if _saved_nc is not None:
        _sys.modules["notion_utils"] = _saved_nc

_LAYER_1_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_LAYER_1_ROOT / ".env", override=True)

import os
import httpx

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_VERSION = "2025-09-03"
NOTION_API_BASE = "https://api.notion.com/v1"
DATA_SOURCE_ID = "442938be-fc42-828f-b72e-076818d65a5b"

def txt(prop):
    if not prop: return ""
    t = prop.get("type")
    if t == "number": return prop.get("number")
    return ""

def query_all_items():
    """Pagina todos los registros vía data_sources/{id}/query"""
    results = []
    cursor = None
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    url = f"{NOTION_API_BASE}/data_sources/{DATA_SOURCE_ID}/query"
    
    with httpx.Client(timeout=30) as http_client:
        while True:
            body = {"page_size": 100}
            if cursor:
                body["start_cursor"] = cursor
            resp = http_client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
            batch = data.get("results", [])
            results.extend(batch)
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
    
    return results

def main():
    items = query_all_items()
    print(f"Total registros: {len(items)}")
    
    scores = []
    for item in items:
        props = item["properties"]
        score = txt(props.get("Score"))
        if score is not None:
            scores.append(score)
    
    if not scores:
        print("No se encontraron scores válidos")
        return
    
    # Histograma con buckets de 5 en 5
    histogram = {}
    for i in range(0, 101, 5):
        histogram[f"{i}-{i+4}"] = 0
    
    for score in scores:
        bucket_start = (score // 5) * 5
        bucket_key = f"{bucket_start}-{bucket_start+4}"
        histogram[bucket_key] = histogram.get(bucket_key, 0) + 1
    
    print(f"\nHistograma de Score (buckets de 5):")
    for bucket in range(0, 101, 5):
        bucket_key = f"{bucket}-{bucket+4}"
        count = histogram.get(bucket_key, 0)
        if count > 0:
            print(f"  {bucket_key}: {count}")
    
    # Análisis específico de Score=40
    score_40_count = scores.count(40)
    print(f"\nAnálisis Score=40:")
    print(f"  Registros con Score=40 exacto: {score_40_count}")
    print(f"  Registros con Score 0-40 pero ≠40: {len([s for s in scores if s < 40])}")
    print(f"  Registros con Score 0-40 total: {len([s for s in scores if s <= 40])}")

if __name__ == "__main__":
    main()
