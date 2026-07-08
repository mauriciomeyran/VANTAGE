#!/usr/bin/env python3
"""
Backfill Class A — layer + hash en entradas existentes del Tracker.

Uso:
  python scripts/backfill_class_a.py           # dry run + confirmación
  python scripts/backfill_class_a.py --dry-run # solo preview, sin escribir
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from notion_utils import Client

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from feed_processor import (  # noqa: E402
    NOTION_DB_ID,
    NotionSchema,
    compute_dedup_hash,
    normalize_record_fields,
    query_notion_db,
)
from layer_1_run import is_agregador  # noqa: E402

_LAYER_1_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_LAYER_1_ROOT / ".env", override=True)

import os  # noqa: E402

NOTION_TOKEN = os.environ["NOTION_TOKEN"]

MAIL_FUENTES = {"Indeed", "OCC", "Computrabajo", "Bumeran", "Puma", "Swarovski", "Other"}


def txt(prop: dict | None) -> str:
    if not prop:
        return ""
    t = prop.get("type")
    if t == "url":
        return prop.get("url") or ""
    if t == "rich_text" and prop.get("rich_text"):
        return prop["rich_text"][0]["plain_text"]
    if t == "select" and prop.get("select"):
        return prop["select"]["name"]
    if t == "title" and prop.get("title"):
        return prop["title"][0]["plain_text"]
    return ""


def infer_fetch_status(props: dict) -> str:
    fuente = txt(props.get("Fuente")).lower()
    if "agregador" in fuente:
        return "aggregator"
    if "career" in fuente or "oficial" in fuente:
        return "career_page"
    url = txt(props.get("URL")) or txt(props.get("apply_url"))
    if url:
        return "aggregator" if is_agregador(url) else "career_page"
    return "career_page"


def page_to_record(props: dict) -> dict:
    return normalize_record_fields({
        "title": txt(props.get("Rol")) or txt(props.get("title")),
        "brand": txt(props.get("Marca")) or txt(props.get("brand")),
        "marca": txt(props.get("Marca")),
        "apply_url": txt(props.get("URL")) or txt(props.get("apply_url")),
        "location": txt(props.get("location")) or txt(props.get("Texto")),
        "job_id": txt(props.get("JOB_ID")),
        "jd": txt(props.get("JD")),
        "fetch_status": infer_fetch_status(props),
    })


def infer_layer(props: dict) -> tuple[str, str]:
    current = txt(props.get("layer"))
    if current in ("L1", "L2", "L3"):
        return current, "ya_seteado"

    raw_email = txt(props.get("Raw Email Subject"))
    if raw_email:
        return "L3", "raw_email_subject"

    notas = txt(props.get("Notas")).lower()
    if "feed semanal" in notas or "search-week" in notas or "layer: l" in notas:
        if "layer: l3" in notas:
            return "L3", "notas_layer"
        if "layer: l2" in notas:
            return "L3", "notas_layer"
        return "L1", "notas_feed"

    url = (txt(props.get("URL")) or txt(props.get("apply_url"))).lower()
    fuente = txt(props.get("Fuente"))

    if "linkedin.com" in url:
        return "L3", "linkedin_url"

    if fuente in MAIL_FUENTES:
        if fuente == "LinkedIn":
            return "L3", "fuente_linkedin"
        return "L2", f"fuente_{fuente.lower()}"

    return "L1", "default"


@dataclass
class BackfillRow:
    page_id: str
    brand: str
    title: str
    layer: str
    layer_reason: str
    hash_key: str
    needs_layer: bool
    needs_hash: bool
    needs_prioridad: bool


def collect_backfill_rows(items: list[dict], schema: NotionSchema) -> list[BackfillRow]:
    rows: list[BackfillRow] = []
    layer_prop = schema.layer_prop
    hash_prop = schema.hash_prop

    if not layer_prop and not hash_prop:
        print("❌ Schema sin propiedades 'layer' ni 'hash'. Abortando.")
        sys.exit(1)

    for item in items:
        props = item["properties"]
        current_layer = txt(props.get(layer_prop)) if layer_prop else ""
        current_hash = txt(props.get(hash_prop)) if hash_prop else ""

        needs_layer = bool(layer_prop) and current_layer not in ("L1", "L2", "L3")
        needs_hash = bool(hash_prop) and not current_hash.strip()

        # Prioridad: backfill si el campo existe en schema y está vacío (None)
        prioridad_prop = "Prioridad"
        current_prioridad = props.get(prioridad_prop, {})
        needs_prioridad = (
            prioridad_prop in schema.properties
            and (current_prioridad is None or current_prioridad.get("number") is None)
        )

        if not needs_layer and not needs_hash and not needs_prioridad:
            continue

        record = page_to_record(props)
        layer, layer_reason = infer_layer(props)
        if not needs_layer:
            layer = current_layer
            layer_reason = "sin_cambio"

        hash_key = compute_dedup_hash(record)

        rows.append(BackfillRow(
            page_id=item["id"],
            brand=record.get("brand") or record.get("brand_raw") or "",
            title=record.get("title") or "",
            layer=layer,
            layer_reason=layer_reason,
            hash_key=hash_key,
            needs_layer=needs_layer,
            needs_hash=needs_hash,
            needs_prioridad=needs_prioridad,
        ))

    return rows


def print_preview(rows: list[BackfillRow]) -> None:
    n_layer = sum(1 for r in rows if r.needs_layer)
    n_hash = sum(1 for r in rows if r.needs_hash)
    n_prioridad = sum(1 for r in rows if r.needs_prioridad)

    print(f"\n{'=' * 80}")
    print("BACKFILL Class A — preview")
    print(f"{'=' * 80}")
    print(f"{len(rows)} entradas a actualizar · layer: {n_layer} · hash: {n_hash} · prioridad: {n_prioridad}\n")
    print("| Brand | Title | Layer | Hash (8) | Motivo layer |")
    print("|---|---|---|---|---|")
    for r in rows[:50]:
        print(
            f"| {r.brand[:18]} | {(r.title or '')[:28]} | {r.layer} | "
            f"{r.hash_key[:8]} | {r.layer_reason} |"
        )
    if len(rows) > 50:
        print(f"| ... | +{len(rows) - 50} más | | | |")
    print(f"\n{'=' * 80}\n")


def apply_backfill(
    client: Client,
    rows: list[BackfillRow],
    schema: NotionSchema,
) -> tuple[int, int]:
    ok = 0
    failed = 0
    layer_prop = schema.layer_prop
    hash_prop = schema.hash_prop

    for row in rows:
        update: dict = {}
        if row.needs_layer and layer_prop:
            update[layer_prop] = schema.select_value(row.layer)
        if row.needs_hash and hash_prop:
            update[hash_prop] = schema.prop_text_value(hash_prop, row.hash_key)

        if row.needs_prioridad:
            update["Prioridad"] = schema.select_value("4")

        if not update:
            continue

        try:
            client.pages.update(page_id=row.page_id, properties=update)
            ok += 1
            flags = []
            if row.needs_layer:
                flags.append(f"layer={row.layer}")
            if row.needs_hash:
                flags.append(f"hash={row.hash_key[:8]}")
            if row.needs_prioridad:
                flags.append("prioridad=4")
            print(f"  ✅ [{row.page_id[:8]}] {row.brand[:20]} — {', '.join(flags)}")
        except Exception as exc:
            failed += 1
            print(f"  ❌ [{row.page_id[:8]}] {row.brand[:20]}: {exc}")

    return ok, failed


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill layer + hash en Tracker")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo mostrar preview, sin confirmación ni escritura",
    )
    args = parser.parse_args()

    print("🔄 VANTAGE Backfill Class A (layer · hash)")
    client = Client(auth=NOTION_TOKEN)
    schema = NotionSchema.load(client)
    schema.warn_missing_class_a()

    items = query_notion_db(client)
    print(f"   Entradas en Tracker: {len(items)}")

    rows = collect_backfill_rows(items, schema)
    if not rows:
        print("✅ Todas las entradas ya tienen layer y hash poblados.")
        return

    print_preview(rows)

    if args.dry_run:
        print("⏹️  Modo --dry-run: sin escritura.")
        return

    confirm = input(f"¿Aprobar backfill de {len(rows)} entradas? [s/N]: ").strip().lower()
    if confirm != "s":
        print("⏹️  Backfill abortado.")
        return

    print(f"\n📝 Actualizando {len(rows)} entradas...")
    ok, failed = apply_backfill(client, rows, schema)
    print(f"\n✅ Actualizadas: {ok}  |  ❌ Fallidas: {failed}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Cancelado")
        sys.exit(1)
