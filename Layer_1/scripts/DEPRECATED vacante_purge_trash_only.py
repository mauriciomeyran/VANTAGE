#!/usr/bin/env python3
"""Manda a la papelera las entradas Status=Expirada en VANTAGE TRACKER.

Las copias en ARCHIVO TRACKER ya existen (de un run previo de vacante_purge.py
que creó las copias pero no logró archivar las originales por usar el campo
"in_trash" en vez de "archived"). Este script SOLO hace el paso de archivar
las originales -- no crea copias nuevas.
"""

import argparse
import os
import time

import httpx
from dotenv import load_dotenv
from notion_utils import Client

DATA_SOURCE_ID = "442938be-fc42-828f-b72e-076818d65a5b"
NOTION_VERSION = "2025-09-03"
NOTION_API_BASE = "https://api.notion.com/v1"
MAX_RETRIES = 3
RETRY_SLEEP = 3
PAGE_SIZE = 100
MAX_EXPECTED_RESULTS = 500

TARGET_STATUS = "Expirada"


def make_client(token: str) -> Client:
    return Client(auth=token)


def with_retry(func, *args, **kwargs):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return func(*args, **kwargs)
        except (httpx.ReadTimeout, httpx.ConnectTimeout):
            if attempt == MAX_RETRIES:
                raise
        except Exception as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if not (status and 500 <= status < 600) or attempt == MAX_RETRIES:
                raise
        time.sleep(RETRY_SLEEP * attempt)


def get_plain_text(prop):
    if not prop:
        return ""
    prop_type = prop.get("type")
    if prop_type == "url":
        return prop.get("url", "") or ""
    if prop_type == "rich_text" and prop.get("rich_text"):
        return prop["rich_text"][0]["plain_text"] if prop["rich_text"] else ""
    if prop_type == "title" and prop.get("title"):
        return prop["title"][0]["plain_text"] if prop["title"] else ""
    if prop_type == "select" and prop.get("select"):
        return prop["select"]["name"]
    if prop_type == "number":
        return prop.get("number")
    return ""


def query_all_items(token: str, data_source_id: str):
    results = []
    cursor = None
    page = 0

    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    url = f"{NOTION_API_BASE}/data_sources/{data_source_id}/query"

    with httpx.Client(timeout=30) as http_client:
        while True:
            page += 1
            body = {
                "page_size": PAGE_SIZE,
                "sorts": [{"timestamp": "created_time", "direction": "ascending"}],
            }
            if cursor:
                body["start_cursor"] = cursor

            def do_request():
                resp = http_client.post(url, headers=headers, json=body)
                resp.raise_for_status()
                return resp

            response = with_retry(do_request)
            data = response.json()

            batch = data.get("results", [])
            results.extend(batch)

            print(
                f"[query] página={page} results={len(batch)} "
                f"has_more={data.get('has_more')} "
                f"acumulados={len(results)}"
            )

            if len(results) > MAX_EXPECTED_RESULTS:
                raise RuntimeError(
                    f"[ABORT] acumulados={len(results)} excede MAX_EXPECTED_RESULTS="
                    f"{MAX_EXPECTED_RESULTS}. Detén otros procesos y reintenta."
                )

            if not data.get("has_more"):
                break

            cursor = data.get("next_cursor")

    print(f"[query] Total registros: {len(results)}")
    return results


def main():
    parser = argparse.ArgumentParser(
        description=f"Archiva (trash) entradas con Status={TARGET_STATUS}"
    )
    parser.add_argument("--dry-run", action="store_true", help="Solo listar, sin escribir")
    parser.add_argument("--yes", action="store_true", help="Confirmar sin prompt")
    args = parser.parse_args()

    load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
    token = os.environ["NOTION_TOKEN"]
    client = make_client(token)

    print(f"[init] Obteniendo registros vía data_sources/{DATA_SOURCE_ID}")
    all_results = query_all_items(token, DATA_SOURCE_ID)
    print(f"[init] {len(all_results)} entradas obtenidas")

    targets = []
    for item in all_results:
        props = item["properties"]
        status = get_plain_text(props.get("Status"))
        if status != TARGET_STATUS:
            continue
        targets.append({
            "id": item["id"],
            "Marca": get_plain_text(props.get("Marca")),
            "Rol": get_plain_text(props.get("Rol")),
        })

    print(f"\n[trash] {len(targets)} entradas con Status={TARGET_STATUS}")

    if not targets:
        return

    for index, t in enumerate(targets, start=1):
        print(f"{index:3d}. [{t['id'][:8]}] {t['Marca'][:25]:25s} | {t['Rol'][:50]}")

    if args.dry_run:
        print(f"\n[dry-run] {len(targets)} entradas se mandarían a la papelera. Nada escrito.")
        return

    if not args.yes:
        print(f"\nArchiva {len(targets)} entradas (papelera) en el Tracker activo.")
        confirm = input("Continuar? (y/N): ").lower().strip()
        if confirm != "y":
            print("Operacion cancelada.")
            return

    print("\n[trash] Archivando...")
    done = 0
    for t in targets:
        try:
            with_retry(client.pages.update, t["id"], archived=True)
            done += 1
            print(f"  OK: {t['id'][:8]} | {t['Rol'][:50]}")
        except Exception as exc:
            print(f"  ERROR {t['id'][:8]}: {exc}")

    print(f"\n[trash] Completado. Archivados: {done}/{len(targets)}")


if __name__ == "__main__":
    main()
