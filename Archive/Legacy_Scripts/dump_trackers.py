# ~/Documents/03 Projects/VANTAGE/Layer_1/scripts/dump_trackers.py
import os, json, requests
from dotenv import load_dotenv

load_dotenv("../config/layer_1.env")
TOKEN = os.environ["NOTION_TOKEN"]
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": "2025-09-03",
    "Content-Type": "application/json",
}

SOURCES = {
    "bug_tracker": "36e938be-fc42-81f8-8c6f-000b6769ba03",
    "task_tracker": "aaaaef55-a1ce-45f7-9c8b-1c1def2c18e8",
}

def dump(name, data_source_id):
    url = f"https://api.notion.com/v1/data_sources/{data_source_id}/query"
    rows, cursor = [], None
    while True:
        payload = {"start_cursor": cursor} if cursor else {}
        r = requests.post(url, headers=HEADERS, json=payload)
        r.raise_for_status()
        data = r.json()
        rows.extend(data["results"])
        if not data.get("has_more"):
            break
        cursor = data["next_cursor"]
    with open(f"{name}_full.json", "w") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)
    print(f"{name}: {len(rows)} filas -> {name}_full.json")

dump("bug_tracker", SOURCES["bug_tracker"])
dump("task_tracker", SOURCES["task_tracker"])