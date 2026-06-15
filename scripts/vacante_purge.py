#!/usr/bin/env python3
"""Purga entradas con Status=Expirada del VANTAGE TRACKER al ARCHIVO TRACKER."""

import argparse
import os
import time

import httpx
from dotenv import load_dotenv
from notion_client import Client

DATABASE_ID = "596938befc42836baea7814a1491bd47"
ARCHIVO_TRACKER_DB_ID = "4ec34e1b-5286-48c9-afbd-d57c6eb76053"
# DB migrada a multi-source: databases/{id}/query repite páginas (cursor roto).
# Hay que paginar contra data_sources/{id}/query con la API 2025-09-03.
DATA_SOURCE_ID = "442938be-fc42-828f-b72e-076818d65a5b"
NOTION_VERSION = "2025-09-03"
NOTION_API_BASE = "https://api.notion.com/v1"
MAX_RETRIES = 3
RETRY_SLEEP = 3
PAGE_SIZE = 100
# Margen real ~216 filas; 500 detecta cualquier desborde anómalo sin
# permitir que algo corra indefinidamente.
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
    """Obtiene todos los registros vía data_sources/{id}/query (API 2025-09-03).

    databases/{id}/query quedó roto para DBs migradas a multi-source: el
    cursor cambia pero regresa la misma página una y otra vez. El endpoint
    de data_sources sí pagina bien.
    """
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
                # Orden fijo: evita que inserciones concurrentes (VL1 corriendo
                # al mismo tiempo) muevan el cursor y generen un loop sin fin.
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
                    f"{MAX_EXPECTED_RESULTS}. Posible escritura concurrente sobre la "
                    f"misma DB (¿VL1 corriendo al mismo tiempo?). Detén cualquier otro "
                    f"proceso y vuelve a correr vacante_purge."
                )

            if not data.get("has_more"):
                break

            cursor = data.get("next_cursor")

    print(f"[query] Total registros: {len(results)}")
    return results


def _move_to_archivo(client, job):
    """Copia la entrada al ARCHIVO TRACKER y luego la manda a Trash en el Tracker activo."""
    props = {}
    if job.get("Rol"):
        props["Rol"] = {"title": [{"text": {"content": job["Rol"][:255]}}]}
    if job.get("Marca"):
        props["Marca"] = {"rich_text": [{"text": {"content": job["Marca"][:255]}}]}
    if job.get("URL"):
        props["URL"] = {"url": job["URL"]}
    if job.get("Status"):
        props["Status"] = {"select": {"name": job["Status"]}}
    if job.get("Notas"):
        props["Notas"] = {"rich_text": [{"text": {"content": job["Notas"][:2000]}}]}
    if job.get("hash"):
        props["hash"] = {"rich_text": [{"text": {"content": job["hash"]}}]}
    if job.get("JD"):
        props["JD"] = {"rich_text": [{"text": {"content": job["JD"][:2000]}}]}
    if job.get("Score") is not None:
        props["Score"] = {"number": job["Score"]}
    if job.get("layer"):
        props["layer"] = {"select": {"name": job["layer"]}}
    if job.get("Gate_Decision"):
        props["Gate_Decision"] = {"select": {"name": job["Gate_Decision"]}}
    if job.get("Role_Class"):
        props["Role_Class"] = {"select": {"name": job["Role_Class"]}}
    # NOTA: ARCHIVO_TRACKER_DB no tiene la propiedad "Source_Type " — se omite.
    with_retry(
        client.pages.create,
        parent={"database_id": ARCHIVO_TRACKER_DB_ID},
        properties=props,
    )
    with_retry(client.pages.update, job["id"], in_trash=True)


def main():
    parser = argparse.ArgumentParser(
        description=f"Purga entradas con Status={TARGET_STATUS} al ARCHIVO TRACKER"
    )
    parser.add_argument("--dry-run", action="store_true", help="Solo listar, sin escribir")
    parser.add_argument("--yes", action="store_true", help="Confirmar purga sin prompt")
    args = parser.parse_args()

    load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
    token = os.environ["NOTION_TOKEN"]
    client = make_client(token)

    print(f"[init] Obteniendo registros vía data_sources/{DATA_SOURCE_ID}")
    all_results = query_all_items(token, DATA_SOURCE_ID)
    print(f"[init] {len(all_results)} entradas obtenidas")

    jobs = []
    for item in all_results:
        props = item["properties"]
        status = get_plain_text(props.get("Status"))
        if status != TARGET_STATUS:
            continue
        jobs.append({
            "id": item["id"],
            "Marca": get_plain_text(props.get("Marca")),
            "Rol": get_plain_text(props.get("Rol")),
            "Status": status,
            "URL": get_plain_text(props.get("URL")),
            "hash": get_plain_text(props.get("hash")),
            "Score": props.get("Score", {}).get("number"),
            "JD": get_plain_text(props.get("JD")),
            "Notas": get_plain_text(props.get("Notas")),
            "layer": get_plain_text(props.get("layer")),
            "Gate_Decision": get_plain_text(props.get("Gate_Decision")),
            "Role_Class": get_plain_text(props.get("Role_Class")),
            "Source_Type": get_plain_text(props.get("Source_Type ")),
        })

    print(f"\n[purge] {len(jobs)} entradas con Status={TARGET_STATUS}")

    if not jobs:
        return

    for index, job in enumerate(jobs, start=1):
        print(
            f"{index:3d}. [{job['id'][:8]}] {job['Marca'][:25]:25s} | "
            f"{job['Rol'][:45]:45s} | layer={job['layer']}"
        )

    if args.dry_run:
        print(f"\n[dry-run] {len(jobs)} entradas se archivarían. Nada escrito.")
        return

    if not args.yes:
        print(f"\nPURGA DESTRUCTIVA: archiva {len(jobs)} entradas en Notion (papelera).")
        confirm = input("Continuar? (y/N): ").lower().strip()
        if confirm != "y":
            print("Operacion cancelada.")
            return

    print("\n[purge] Archivando...")
    archived = 0
    for job in jobs:
        try:
            _move_to_archivo(client, job)
            archived += 1
            print(f"  Archivado: {job['id'][:8]} | {job['Rol'][:50]}")
        except Exception as exc:
            print(f"  ERROR archivando {job['id'][:8]}: {exc}")

    print(f"\n[purge] Completado. Archivados: {archived}/{len(jobs)}")


if __name__ == "__main__":
    main()
