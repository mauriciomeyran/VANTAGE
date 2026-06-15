#!/usr/bin/env python3
"""
VANTAGE Backfill Hash — v1.3
Puebla el campo `hash` (SHA-256) en registros existentes de VANTAGE_TRACKER y ARCHIVO_TRACKER
que aún no lo tienen. No crea registros nuevos; solo actualiza vía pages.update().

Uso:
  python scripts/backfill_hash.py [--db vantage|archivo|both] [--dry-run] [--limit N]

Lógica de hash: importada directamente de feed_processor.py (compute_dedup_hash).

Fix v1.3:
  Los IDs en DB_IDS son data_source IDs (COL), no database IDs. Desde
  Notion-Version 2025-09-03 las DBs multi-source ya no resuelven vía
  databases.query(database_id=...) — el endpoint correcto es
  data_sources/{id}/query. Ver query_data_source().
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from notion_client import Client

# ── paths ──────────────────────────────────────────────────────────────────────
_SCRIPTS_DIR = Path(__file__).resolve().parent
_LAYER_1_ROOT = _SCRIPTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

load_dotenv(_LAYER_1_ROOT / ".env", override=True)

from feed_processor import compute_dedup_hash  # noqa: E402

# ── config ─────────────────────────────────────────────────────────────────────
NOTION_TOKEN = os.environ["NOTION_TOKEN"]

# IDs con guiones — son DATA SOURCE IDs (no database IDs). Se consultan vía
# data_sources/{id}/query (Notion-Version 2025-09-03+), no databases.query.
DB_IDS = {
    "vantage": "442938be-fc42-828f-b72e-076818d65a5b",  # VANTAGE TRACKER (data source / COL)
    "archivo": "674696fd-94b6-464a-ac1f-64b0cc917e15",  # ARCHIVO TRACKER (data source / COL)
}

# Notion-Version mínima requerida por el endpoint data_sources/*/query.
DATA_SOURCES_API_VERSION = "2025-09-03"

HASH_FIELD = "hash"
MAX_PAGES_PER_DB = 50  # 50 × 100 = 5000 registros máx — más que suficiente


# ── helpers ────────────────────────────────────────────────────────────────────
def make_client(token: str) -> Client:
    """
    Instancia el cliente forzando Notion-Version >= 2025-09-03, requerido
    para que existan los endpoints data_sources/*. Si el SDK instalado no
    acepta `notion_version` en el constructor (versiones viejas de
    notion-client), cae a instanciación normal y luego intenta sobreescribir
    el header directamente en el cliente HTTP interno.
    """
    try:
        client = Client(auth=token, notion_version=DATA_SOURCES_API_VERSION)
    except Exception:
        client = Client(auth=token)

    try:
        client.client.headers["Notion-Version"] = DATA_SOURCES_API_VERSION
    except Exception:
        pass

    return client


def query_data_source(client: Client, data_source_id: str, **kwargs: Any) -> dict:
    """
    Wrapper sobre data_sources/{id}/query (Notion API 2025-09-03+).

    Reemplaza a client.databases.query(database_id=...), que no resuelve
    IDs de data source en DBs multi-source (404 / object_not_found).

    - Si el SDK instalado expone client.data_sources.query (notion-client
      con soporte para Data Sources API), se usa directamente.
    - Si no, cae a un request manual al endpoint, con el header
      Notion-Version ya forzado por make_client().
    """
    if hasattr(client, "data_sources"):
        return client.data_sources.query(data_source_id=data_source_id, **kwargs)

    return client.request(
        path=f"data_sources/{data_source_id}/query",
        method="POST",
        body=kwargs,
    )


def _plain_text(prop: dict) -> str:
    ptype = prop.get("type", "")
    if ptype in ("rich_text", "title"):
        parts = prop.get(ptype, [])
        return "".join(p.get("plain_text", "") for p in parts).strip()
    if ptype == "select":
        return (prop.get("select") or {}).get("name", "").strip()
    if ptype == "url":
        return (prop.get("url") or "").strip()
    return ""


def page_to_record(page: dict) -> dict:
    props = page.get("properties", {})

    def get(*keys: str) -> str:
        for k in keys:
            if k in props:
                v = _plain_text(props[k])
                if v:
                    return v
        return ""

    title     = get("Rol", "title", "rol", "role")
    brand     = get("Marca", "brand", "marca", "company")
    location  = get("location", "Texto", "ubicacion", "city")
    apply_url = get("URL", "apply_url", "url")
    job_id    = get("JOB_ID", "job_id")
    fetch     = get("fetch_status")

    if not fetch:
        from feed_processor import is_agregador
        fetch = "aggregator" if (apply_url and is_agregador(apply_url)) else (
            "career_page" if apply_url else "fallback"
        )

    return {
        "title": title, "brand": brand, "brand_raw": brand,
        "location": location, "apply_url": apply_url,
        "job_id": job_id, "fetch_status": fetch,
    }


def get_existing_hash(page: dict) -> str:
    props = page.get("properties", {})
    if HASH_FIELD not in props:
        return ""
    return _plain_text(props[HASH_FIELD])


def iter_pages_without_hash(client: Client, db_id: str) -> list[dict]:
    all_pages: list[dict] = []
    kwargs: dict[str, Any] = {"page_size": 100}
    seen_cursors: set[str] = set()
    page_count = 0

    while True:
        page_count += 1
        if page_count > MAX_PAGES_PER_DB:
            print(f"  ⚠️  MAX_PAGES ({MAX_PAGES_PER_DB}) alcanzado — abortando")
            break
        try:
            resp = query_data_source(client, db_id, **kwargs)
        except Exception as exc:
            print(f"  ❌ Error consultando {db_id[:8]}: {exc}")
            break

        results = resp.get("results", [])
        if not results and page_count == 1:
            print(f"  ⚠️  La API devolvió 0 resultados en página 1 — verifica el data_source ID")
            break

        for page in results:
            if not get_existing_hash(page):
                all_pages.append(page)

        if not results:
            print(f"  ⚠️  Página {page_count} vacía — abortando")
            break

        cursor = resp.get("next_cursor")
        if resp.get("has_more") and cursor:
            if cursor in seen_cursors:
                print(f"  ⚠️  Cursor repetido — loop infinito abortado")
                break
            seen_cursors.add(cursor)
            kwargs["start_cursor"] = cursor
        else:
            break

    return all_pages


def backfill_db(
    client: Client, db_id: str, db_label: str,
    dry_run: bool, limit: int | None,
) -> tuple[int, int, int]:
    print(f"\n{'─' * 60}")
    print(f"  DB: {db_label} ({db_id[:8]}…)")
    print(f"  Modo: {'DRY RUN' if dry_run else 'WRITE'}")

    pages = iter_pages_without_hash(client, db_id)
    total_sin_hash = len(pages)
    print(f"  Registros sin hash: {total_sin_hash}")

    if limit:
        pages = pages[:limit]
        print(f"  Limitado a: {limit} registros")

    updated = failed = 0

    for i, page in enumerate(pages, 1):
        page_id = page["id"]
        record = page_to_record(page)
        brand = record.get("brand") or ""
        title = record.get("title") or ""
        url   = record.get("apply_url") or ""

        if not brand and not title and not url:
            print(f"  [{i:03d}] ⚠️  SKIP {page_id[:8]}… — sin brand/title/url")
            failed += 1
            continue

        try:
            hash_val = compute_dedup_hash(record)
        except Exception as exc:
            print(f"  [{i:03d}] ❌ HASH ERROR {page_id[:8]}…: {exc}")
            failed += 1
            continue

        label = f"{(brand or '?')[:25]} | {(title or '?')[:30]}"
        print(f"  [{i:03d}] {label}")
        print(f"         hash: {hash_val[:16]}…  fetch: {record.get('fetch_status')}")

        if dry_run:
            print(f"         [DRY RUN — no se escribe]")
            updated += 1
            continue

        try:
            client.pages.update(
                page_id=page_id,
                properties={HASH_FIELD: {"rich_text": [{"text": {"content": hash_val}}]}},
            )
            print(f"         ✅ Escrito")
            updated += 1
        except Exception as exc:
            print(f"         ❌ pages.update falló: {exc}")
            failed += 1

    return total_sin_hash, updated, failed


def main() -> None:
    parser = argparse.ArgumentParser(description="VANTAGE Backfill Hash v1.3")
    parser.add_argument("--db", choices=["vantage", "archivo", "both"], default="both")
    parser.add_argument("--dry-run", action="store_true", default=False)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    print("🔧 VANTAGE Backfill Hash v1.3")
    print(f"   Target: {args.db}  |  Dry-run: {args.dry_run}  |  Limit: {args.limit or 'none'}")

    client = make_client(NOTION_TOKEN)
    endpoint = "data_sources.query (SDK)" if hasattr(client, "data_sources") else "request() manual a data_sources/*/query"
    print(f"   Endpoint de consulta: {endpoint}")
    targets = []
    if args.db in ("vantage", "both"):
        targets.append(("vantage", DB_IDS["vantage"]))
    if args.db in ("archivo", "both"):
        targets.append(("archivo", DB_IDS["archivo"]))

    grand_total = grand_updated = grand_failed = 0
    for label, db_id in targets:
        total, updated, failed = backfill_db(client, db_id, label, args.dry_run, args.limit)
        grand_total += total
        grand_updated += updated
        grand_failed += failed

    print(f"\n{'═' * 60}")
    print(f"  RESUMEN FINAL")
    print(f"  Sin hash encontrados : {grand_total}")
    mode = "simulados (dry-run)" if args.dry_run else "actualizados en Notion"
    print(f"  Hash {mode}: {grand_updated}")
    print(f"  Fallidos             : {grand_failed}")
    if args.dry_run:
        print(f"\n  Para escribir: python scripts/backfill_hash.py --db {args.db}")
    print(f"{'═' * 60}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Cancelado")
        sys.exit(1)
