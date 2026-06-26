#!/usr/bin/env python3
"""Consolida duplicados en VANTAGE TRACKER (archiva copias, mantiene la mejor entrada)."""

import argparse
import os
import re
import time
from collections import defaultdict
from difflib import SequenceMatcher
from urllib.parse import urlparse

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

GENERIC_URL_MARKERS = (
    "computrabajo.com.mx/",
    "occ.com.mx/",
    "indeed.com/jobs?",
    "linkedin.com/jobs/search",
)


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
                    f"proceso y vuelve a correr vdedup."
                )

            if not data.get("has_more"):
                break

            cursor = data.get("next_cursor")

    print(f"[query] Total registros: {len(results)}")
    return results


def url_dedup_key(url):
    if not url:
        return None
    u = url.strip().lower()
    for pattern in (
        r"linkedin\.com/jobs/view/(\d+)",
        r"linkedin\.com/comm/jobs/view/(\d+)",
    ):
        match = re.search(pattern, u)
        if match:
            return f"li:{match.group(1)}"
    match = re.search(r"[?&]jk=([a-f0-9]+)", u)
    if match and "indeed" in u:
        return f"indeed:{match.group(1)}"
    if "indeed" in u and ("/pagead/clk" in u or "/rc/clk/" in u):
        return None
    if any(marker in u for marker in GENERIC_URL_MARKERS):
        return None
    parsed = urlparse(u)
    if parsed.path and parsed.path not in ("/", ""):
        return f"{parsed.netloc.lower()}{parsed.path.rstrip('/')}"
    return None


def norm_brand(brand):
    brand = (brand or "").lower().strip()
    for suffix in (" group", " ag", " mx", " s.a.", " sapi de cv", " we are "):
        brand = brand.replace(suffix, "")
    return " ".join(brand.split())


def brands_compatible(job1, job2):
    brand_a = norm_brand(job1["Marca"])
    brand_b = norm_brand(job2["Marca"])
    if not brand_a or not brand_b:
        return False
    if brand_a == brand_b:
        return True
    return SequenceMatcher(None, brand_a, brand_b).ratio() >= 0.9


def url_duplicate(job1, job2):
    if not job1["url_key"] or job1["url_key"] != job2["url_key"]:
        return False
    if norm_brand(job1["Marca"]) == norm_brand(job2["Marca"]):
        return True
    return SequenceMatcher(None, job1["Rol"].lower(), job2["Rol"].lower()).ratio() >= 0.85


def hash_duplicate(job1, job2):
    if not job1["hash"] or job1["hash"] != job2["hash"]:
        return False
    if norm_brand(job1["Marca"]) == norm_brand(job2["Marca"]):
        return True
    return SequenceMatcher(None, job1["Rol"].lower(), job2["Rol"].lower()).ratio() >= 0.9


def fuzzy_duplicate(job1, job2):
    if job1["url_key"] or job2["url_key"]:
        return False
    if norm_brand(job1["Marca"]) != norm_brand(job2["Marca"]):
        return False
    return SequenceMatcher(None, job1["Rol"].lower(), job2["Rol"].lower()).ratio() >= 0.88


def aggressive_duplicate(job1, job2):
    """Marca similar + rol parecido; no fusionar si ambas tienen URL de vacante distinta."""
    if job1["url_key"] and job2["url_key"] and job1["url_key"] != job2["url_key"]:
        return False
    if not brands_compatible(job1, job2):
        return False
    role_similarity = SequenceMatcher(
        None, job1["Rol"].lower(), job2["Rol"].lower()
    ).ratio()
    return role_similarity >= 0.80


class UnionFind:
    def __init__(self, size):
        self.parent = list(range(size))

    def find(self, node):
        while self.parent[node] != node:
            self.parent[node] = self.parent[self.parent[node]]
            node = self.parent[node]
        return node

    def union(self, a, b):
        root_a, root_b = self.find(a), self.find(b)
        if root_a != root_b:
            self.parent[root_b] = root_a


def get_status_priority(status):
    priority = {
        "En proceso": 10,
        "Negociando": 9,
        "Postulado": 8,
        "Target": 7,
        "Exploratorio": 6,
        "Nueva": 5,
        "Sin respuesta": 4,
        "Expirada": 2,
        "Rechazado": 1,
        "Archivar": 0,
        "Retirado": 0,
    }
    return priority.get(status, 0)


def choose_primary(jobs):
    def rank(job):
        return (
            get_status_priority(job["Status"]),
            1 if job.get("url_key") else 0,
            1 if job.get("Score") is not None else 0,
            job.get("Score") or 0,
            1 if job.get("JD") else 0,
            len(job.get("URL") or ""),
            1 if job.get("Notas") else 0,
        )

    return max(jobs, key=rank)


def merge_notes(primary_notes, secondary_notes):
    if not secondary_notes or not secondary_notes.strip():
        return primary_notes or ""
    if not primary_notes or not primary_notes.strip():
        return secondary_notes
    separator = "\n\n--- CONSOLIDADO DESDE DUPLICADO ---\n"
    return (primary_notes + separator + secondary_notes).strip()


def is_cross_layer_group(group):
    """Retorna True si el grupo contiene entradas de layers distintos."""
    layers = {job.get("layer") for job in group if job.get("layer")}
    return len(layers) > 1


def layers_in_group(group):
    return sorted({job.get("layer", "?") for job in group})


def find_duplicate_groups(jobs, aggressive=False):
    uf = UnionFind(len(jobs))
    by_url = defaultdict(list)
    by_hash = defaultdict(list)

    for index, job in enumerate(jobs):
        if job["url_key"]:
            by_url[job["url_key"]].append(index)
        if job["hash"]:
            by_hash[job["hash"]].append(index)

    if not aggressive:
        for indices in by_url.values():
            base = indices[0]
            for other in indices[1:]:
                if url_duplicate(jobs[base], jobs[other]):
                    uf.union(base, other)

        for indices in by_hash.values():
            base = indices[0]
            for other in indices[1:]:
                if hash_duplicate(jobs[base], jobs[other]):
                    uf.union(base, other)

    for i in range(len(jobs)):
        for j in range(i + 1, len(jobs)):
            if uf.find(i) == uf.find(j):
                continue
            if aggressive:
                if aggressive_duplicate(jobs[i], jobs[j]):
                    uf.union(i, j)
            elif fuzzy_duplicate(jobs[i], jobs[j]):
                uf.union(i, j)

    grouped = defaultdict(list)
    for index, job in enumerate(jobs):
        grouped[uf.find(index)].append(job)
    return [group for group in grouped.values() if len(group) > 1]


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
    # NOTA: ARCHIVO_TRACKER_DB no tiene la propiedad "Source_Type" — se omite.
    with_retry(
        client.pages.create,
        parent={"database_id": ARCHIVO_TRACKER_DB_ID},
        properties=props,
    )
    with_retry(client.pages.update, job["id"], archived=True)


def consolidate(client, duplicate_groups, dry_run=False):
    archived = 0
    for index, group in enumerate(duplicate_groups, start=1):
        primary = choose_primary(group)
        secondaries = [job for job in group if job["id"] != primary["id"]]

        print(f"\n--- Grupo {index} ({len(group)} entradas) ---")
        print(
            f"MANTENER: [{primary['id'][:8]}] {primary['Marca']} | "
            f"{primary['Rol'][:50]} | {primary['Status']} | Score={primary.get('Score')}"
        )

        merged_notes = primary["Notas"]
        best_url = primary.get("URL") or ""
        for secondary in secondaries:
            print(
                f"ARCHIVAR:  [{secondary['id'][:8]}] {secondary['Marca']} | "
                f"{secondary['Rol'][:50]} | {secondary['Status']} | Score={secondary.get('Score')}"
            )
            merged_notes = merge_notes(merged_notes, secondary["Notas"])
            if not best_url and secondary.get("URL"):
                best_url = secondary["URL"]

        # DT-03: Dedup_Flag cross-layer
        cross_layer = is_cross_layer_group(group)
        if not dry_run and cross_layer:
            flag_ids = [primary["id"]] + [s["id"] for s in secondaries]
            for fid in flag_ids:
                try:
                    with_retry(
                        client.pages.update,
                        fid,
                        properties={"Dedup_Flag": {"select": {"name": "Posible duplicado"}}}
                    )
                except Exception as exc:
                    print(f"  WARNING: Error escribiendo Dedup_Flag en {fid[:8]}: {exc}")
            print(f"  ⚠️  Dedup_Flag=Posible duplicado → {len(flag_ids)} entradas (cross-layer: {layers_in_group(group)})")

        if dry_run:
            continue

        update_props = {}
        if merged_notes != primary["Notas"]:
            update_props["Notas"] = {
                "rich_text": [{"text": {"content": merged_notes[:2000]}}]
            }
        if best_url and best_url != (primary.get("URL") or ""):
            update_props["URL"] = {"url": best_url}

        if update_props:
            try:
                with_retry(client.pages.update, primary["id"], properties=update_props)
            except Exception as exc:
                print(f"  WARNING: Error actualizando entrada principal: {exc}")

        for secondary in secondaries:
            try:
                _move_to_archivo(client, secondary)
                archived += 1
                print(f"  Archivado: {secondary['id'][:8]}")
            except Exception as exc:
                print(f"  ERROR archivando {secondary['id'][:8]}: {exc}")

    return archived


def main():
    parser = argparse.ArgumentParser(description="Consolida duplicados en VANTAGE TRACKER")
    parser.add_argument("--dry-run", action="store_true", help="Solo mostrar grupos, sin escribir")
    parser.add_argument("--yes", action="store_true", help="Confirmar consolidación sin prompt")
    parser.add_argument(
        "--aggressive",
        action="store_true",
        help="Marca+rol similar aunque la URL difiera (no fusiona dos URLs de vacante distintas)",
    )
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
        url = get_plain_text(props.get("URL"))
        jobs.append({
            "id": item["id"],
            "Marca": get_plain_text(props.get("Marca")),
            "Rol": get_plain_text(props.get("Rol")),
            "Status": get_plain_text(props.get("Status")),
            "URL": url,
            "url_key": url_dedup_key(url),
            "hash": get_plain_text(props.get("hash")),
            "Score": props.get("Score", {}).get("number"),
            "JD": get_plain_text(props.get("JD")),
            "Notas": get_plain_text(props.get("Notas")),
            "layer": get_plain_text(props.get("layer")),
            "Gate_Decision": get_plain_text(props.get("Gate_Decision")),
            "Role_Class": get_plain_text(props.get("Role_Class")),
            "Source_Type": get_plain_text(props.get("Source_Type")),
        })

    mode = "agresivo (marca+rol)" if args.aggressive else "URL/hash + marca+rol sin URL"
    print(f"\n[dedup] Detectando duplicados [{mode}]...")
    duplicate_groups = find_duplicate_groups(jobs, aggressive=args.aggressive)

    if not duplicate_groups:
        print("[dedup] No se encontraron duplicados.")
        return

    to_archive = sum(len(group) - 1 for group in duplicate_groups)
    print(
        f"[dedup] {len(duplicate_groups)} grupos | "
        f"{to_archive} a archivar | "
        f"quedarían {len(jobs) - to_archive}"
    )

    if args.dry_run:
        consolidate(client, duplicate_groups, dry_run=True)
        return

    if not args.yes:
        print("\nCONSOLIDACION DESTRUCTIVA: archiva duplicados en Notion (papelera).")
        confirm = input("Continuar? (y/N): ").lower().strip()
        if confirm != "y":
            print("Operacion cancelada.")
            return

    print("\n[consolidate] Consolidando duplicados...")
    archived = consolidate(client, duplicate_groups, dry_run=False)
    print(f"\n[consolidate] Completado. Archivados: {archived}")


if __name__ == "__main__":
    main()
