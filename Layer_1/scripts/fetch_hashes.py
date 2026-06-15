import os, json, time, urllib.request

TOKEN = open(os.path.expanduser("~/Documents/04-Vantage_CV/Layer_1/config/layer_1.env")).read().split("NOTION_TOKEN=")[1].split()[0]
OUT = os.path.expanduser("~/output")
TMP = os.path.join(OUT, "hash_fetch_tmp")
os.makedirs(TMP, exist_ok=True)

VANTAGE_IDS = [
    "76a938be-fc42-83fd-8bf9-01adbfbf3159",
    "374938be-fc42-812a-8a1d-fe8891e76866",
    "9f0938be-fc42-835d-b8fc-010dc43694fc",
    "86d938be-fc42-838f-b365-01fa30d60d8e",
    "e37938be-fc42-83aa-a43b-816b548b2718",
    "36d938be-fc42-81f5-94ec-c9adb8e8cc63",
    "214938be-fc42-832d-9466-0144b1fa016a",
    "53a938be-fc42-8264-ad1e-01ae92b0c0bf",
    "77e938be-fc42-82a1-9157-8154fe0d1df7",
    "544938be-fc42-82d8-98db-81b1a338b384",
    "a4c938be-fc42-82e9-ac40-8148a5400775",
    "373938be-fc42-81f5-a453-e44d830b5694",
    "a4c938be-fc42-8317-8da2-01c519788376",
    "374938be-fc42-81cf-8de0-ca70a1e173d4",
    "864938be-fc42-82de-ba9c-0144c82e63e3",
    "9e6938be-fc42-8286-9105-818a8f44634a",
    "483938be-fc42-8392-85f7-81d1299bd81d",
    "374938be-fc42-81e4-a5c2-f6964bec55c4",
]

ARCHIVO_IDS = [
    "36e938be-fc42-817f-8e8f-fce50fa22e62",
    "36e938be-fc42-81ac-89a2-f904391b2773",
    "36e938be-fc42-8130-85a1-e9febe13c9aa",
    "36e938be-fc42-8167-ba3f-c80d6f629721",
    "36e938be-fc42-81d5-accd-cb5faf719be9",
    "36e938be-fc42-81bb-bb04-dcc47e8822e4",
    "36e938be-fc42-8167-b74f-fc4f9823b8a6",
    "36e938be-fc42-8175-85b6-e6166c85cef1",
    "36e938be-fc42-8110-88f2-c42e01626ea7",
    "36e938be-fc42-81f8-b2ae-fe5e62778494",
    "36e938be-fc42-81fb-9dfe-e2f872287f5e",
    "36e938be-fc42-81ad-97ea-c1bbcf8210b6",
    "36e938be-fc42-81af-b7f9-f2e38eda8c2e",
    "36e938be-fc42-81c9-b96e-c463a2e17ca2",
    "36e938be-fc42-81de-b2a0-fb42ca1a22ce",
    "36e938be-fc42-8144-be9f-c6e552b20ac1",
]

def get_hash(page_id):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Notion-Version": "2022-06-28",
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read())
        props = d.get("properties", {})
        for k in ["hash", "Hash", "HASH"]:
            if k in props:
                p = props[k]
                t = p.get("type", "")
                if t == "rich_text":
                    arr = p.get("rich_text", [])
                    if arr:
                        return arr[0]["plain_text"]
                elif t == "formula":
                    v = p.get("formula", {})
                    if "string" in v:
                        return v["string"]
        return None
    except Exception as e:
        print(f"  ERROR {page_id}: {e}")
        return None

all_pages = (
    [("VANTAGE_TRACKER", pid) for pid in dict.fromkeys(VANTAGE_IDS)] +
    [("ARCHIVO_TRACKER", pid) for pid in dict.fromkeys(ARCHIVO_IDS)]
)

print(f"Token: {TOKEN[:20]}...")
print(f"Total paginas: {len(all_pages)}")

resolved = {}
for i, (source, pid) in enumerate(all_pages, 1):
    h = get_hash(pid)
    resolved[pid] = {"source": source, "hash": h}
    status = f"{h[:16]}..." if h else "sin hash"
    print(f"  [{i}/{len(all_pages)}] {pid[:8]}... -> {status}")
    time.sleep(0.35)

index_path = os.path.join(OUT, "entity_index_v2.json")
if not os.path.exists(index_path):
    print(f"ERROR: No existe {index_path} — regenera el index primero")
    exit(1)

with open(index_path) as f:
    idx = json.load(f)

lookup = {e["page_id"]: e for e in idx["entities"]}
patched = 0
for pid, v in resolved.items():
    h = v["hash"]
    if h and pid in lookup:
        e = lookup[pid]
        e["entity_id"]    = f"TRACKER:H_{h[:16]}"
        e["canonical_id"] = h
        e["hash"]         = h
        patched += 1

entities = list(lookup.values())
total    = len(entities)
has_hash = sum(1 for e in entities if not e["entity_id"].startswith("TRACKER:U_"))
orphans  = total - has_hash
hash_cov = round(has_hash / total, 4)
idx["entities"] = entities
idx["metrics"]["hash_coverage"]     = hash_cov
idx["metrics"]["orphan_candidates"] = orphans

with open(index_path, "w") as f:
    json.dump(idx, f, indent=2, ensure_ascii=False)

print(f"\nPatched: {patched} | Coverage: {has_hash}/{total} ({hash_cov*100:.1f}%) | Orphans: {orphans}")
print(f"Listo — {index_path} actualizado.")
