import os
import requests
from dotenv import load_dotenv
from notion_client import Client

def txt(prop):
    if not prop: return ""
    t = prop.get("type")
    if t == "url": return prop.get("url") or ""
    if t == "select" and prop.get("select"): 
        return prop["select"]["name"]
    return ""

def check_url(url):
    try:
        r = requests.head(url, allow_redirects=True, timeout=8)
        if r.status_code >= 200 and r.status_code < 400:
            return "Accesible"
        else:
            return "Bloqueado"
    except:
        return "Bloqueado"

if __name__ == "__main__":
    load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
    client = Client(auth=os.environ["NOTION_TOKEN"])
    ds_id = "4e542b37-6e52-4418-89b7-a0eeb3138307"

    print("🔎 Re-checking URLs...\n")

    items = client.data_sources.query(data_source_id=ds_id)["results"]
    
    for item in items:
        props = item["properties"]
        url = txt(props.get("URL"))
        current_fetch = txt(props.get("Fetch"))

        if not url:
            continue

        new_fetch = check_url(url)

        if new_fetch != current_fetch:
            try:
                client.pages.update(
                    page_id=item["id"],
                    properties={
                        "Fetch": {"select": {"name": new_fetch}}
                    }
                )
                print(f"✅ [{item['id'][:8]}] {new_fetch} | {url[:60]}...")
            except Exception as e:
                print(f"❌ Error updating {item['id'][:8]}: {e}")

    print("\n✅ Re-check completado.")