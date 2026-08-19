#!/usr/bin/env python3
"""
feedback_loop.py — VANTAGE Feedback Loop v1.0
Calcula conversión por Score_band, Source_Type y criterios de fit.
Requiere campo Outcome en VANTAGE TRACKER (select):
  Opciones: Sin respuesta | Entrevista | Rechazado | Contratado

Uso:
  python3 feedback_loop.py           # reporte en consola
  python3 feedback_loop.py --json    # output JSON para integraciones
"""

import os
import sys
import json
from collections import defaultdict
from datetime import datetime
from dotenv import load_dotenv
import httpx

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DS_ID            = "442938be-fc42-828f-b72e-076818d65a5b"
NOTION_VERSION   = "2025-09-03"
NOTION_API_BASE  = "https://api.notion.com/v1"
MAX_RESULTS      = 250

SCORE_BANDS = [
    ("0–39",   0,  39),
    ("40–69", 40,  69),
    ("70–100", 70, 100),
]

FIT_FIELDS = [
    "VM_Scope",
    "Role_Class",
    "Source_Type ",   # trailing space intencional — schema de Notion
]

SUCCESS_OUTCOMES = {"Entrevista", "Contratado"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def txt(prop):
    if not prop:
        return ""
    t = prop.get("type")
    if t == "select" and prop.get("select"):
        return prop["select"]["name"]
    if t == "rich_text" and prop.get("rich_text"):
        return prop["rich_text"][0]["plain_text"]
    if t == "title" and prop.get("title"):
        return prop["title"][0]["plain_text"]
    if t == "number":
        return prop.get("number")
    if t == "url":
        return prop.get("url") or ""
    if t == "date" and prop.get("date"):
        return prop["date"]["start"]
    return ""


def get_score_band(score):
    if score is None:
        return "Sin score"
    for label, low, high in SCORE_BANDS:
        if low <= score <= high:
            return label
    return "Sin score"


def pct(num, den):
    if den == 0:
        return 0.0
    return round(num / den * 100, 1)


# ---------------------------------------------------------------------------
# Query — mismo patrón que layer_1_run.py (httpx directo, API 2025-09-03)
# ---------------------------------------------------------------------------

def query_all(token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    url = f"{NOTION_API_BASE}/data_sources/{DS_ID}/query"
    all_results = []
    cursor = None

    with httpx.Client(timeout=30) as http:
        while True:
            body = {
                "page_size": 100,
                "sorts": [{"timestamp": "created_time", "direction": "ascending"}],
            }
            if cursor:
                body["start_cursor"] = cursor

            response = http.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()

            all_results.extend(data.get("results", []))

            if len(all_results) > MAX_RESULTS:
                print(f"  ⚠️  MAX_RESULTS ({MAX_RESULTS}) excedido — abortando paginación")
                break

            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")

    return all_results


# ---------------------------------------------------------------------------
# Análisis
# ---------------------------------------------------------------------------

def analyze(items):
    band_total    = defaultdict(int)
    band_success  = defaultdict(int)
    source_total  = defaultdict(int)
    source_success = defaultdict(int)
    fit_stats = {f: defaultdict(lambda: {"total": 0, "success": 0}) for f in FIT_FIELDS}

    with_outcome = 0
    without_outcome = 0

    for item in items:
        props = item["properties"]
        outcome = txt(props.get("Outcome"))

        if not outcome:
            without_outcome += 1
            continue
        with_outcome += 1

        score = props.get("Score", {}).get("number")
        band  = get_score_band(score)
        is_success = outcome in SUCCESS_OUTCOMES

        band_total[band] += 1
        if is_success:
            band_success[band] += 1

        source = txt(props.get("Source_Type ")) or "Sin fuente"
        source_total[source] += 1
        if is_success:
            source_success[source] += 1

        for field in FIT_FIELDS:
            val = txt(props.get(field)) or "Sin valor"
            fit_stats[field][val]["total"] += 1
            if is_success:
                fit_stats[field][val]["success"] += 1

    return {
        "meta": {
            "total_items": len(items),
            "with_outcome": with_outcome,
            "without_outcome": without_outcome,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        },
        "by_score_band": {
            band: {
                "total": band_total[band],
                "success": band_success[band],
                "conversion_pct": pct(band_success[band], band_total[band]),
            }
            for band in ["0–39", "40–69", "70–100", "Sin score"]
            if band_total[band] > 0
        },
        "by_source": {
            src: {
                "total": source_total[src],
                "success": source_success[src],
                "conversion_pct": pct(source_success[src], source_total[src]),
            }
            for src in sorted(source_total, key=lambda x: source_total[x], reverse=True)
        },
        "by_fit_field": {
            field: {
                val: {
                    "total": stats["total"],
                    "success": stats["success"],
                    "conversion_pct": pct(stats["success"], stats["total"]),
                }
                for val, stats in sorted(
                    fit_stats[field].items(),
                    key=lambda x: x[1]["total"],
                    reverse=True,
                )
            }
            for field in FIT_FIELDS
            if fit_stats[field]
        },
    }


# ---------------------------------------------------------------------------
# Reporte en consola
# ---------------------------------------------------------------------------

def print_report(data):
    meta = data["meta"]
    print("\n" + "=" * 55)
    print("  VANTAGE — FEEDBACK LOOP REPORT")
    print(f"  {meta['generated_at']}")
    print("=" * 55)
    print(f"  Total entradas : {meta['total_items']}")
    print(f"  Con Outcome    : {meta['with_outcome']}")
    print(f"  Sin Outcome    : {meta['without_outcome']}  ← actualizar en Notion")

    if meta["with_outcome"] == 0:
        print("\n  ⚠️  Sin datos de Outcome — agrega el campo en Notion y registra resultados.")
        print("=" * 55 + "\n")
        return

    print("\n── CONVERSIÓN POR SCORE BAND ─────────────────────────")
    print(f"  {'Banda':<12} {'Total':>6} {'Éxitos':>7} {'Conv%':>7}")
    print(f"  {'-'*12} {'-'*6} {'-'*7} {'-'*7}")
    for band, stats in data["by_score_band"].items():
        bar = "█" * int(stats["conversion_pct"] / 5)
        print(f"  {band:<12} {stats['total']:>6} {stats['success']:>7} {stats['conversion_pct']:>6.1f}%  {bar}")

    print("\n── CONVERSIÓN POR FUENTE ────────────────────────────")
    print(f"  {'Fuente':<20} {'Total':>6} {'Éxitos':>7} {'Conv%':>7}")
    print(f"  {'-'*20} {'-'*6} {'-'*7} {'-'*7}")
    for src, stats in data["by_source"].items():
        bar = "█" * int(stats["conversion_pct"] / 5)
        print(f"  {src:<20} {stats['total']:>6} {stats['success']:>7} {stats['conversion_pct']:>6.1f}%  {bar}")

    for field, values in data["by_fit_field"].items():
        label = field.strip()
        print(f"\n── CONVERSIÓN POR {label.upper()} {'─' * max(1, 36 - len(label))}")
        print(f"  {'Valor':<22} {'Total':>6} {'Éxitos':>7} {'Conv%':>7}")
        print(f"  {'-'*22} {'-'*6} {'-'*7} {'-'*7}")
        for val, stats in values.items():
            bar = "█" * int(stats["conversion_pct"] / 5)
            print(f"  {val:<22} {stats['total']:>6} {stats['success']:>7} {stats['conversion_pct']:>6.1f}%  {bar}")

    print("\n── SEÑALES PARA AJUSTE DE SCORING ──────────────────")
    bands = data["by_score_band"]
    band_order = ["0–39", "40–69", "70–100"]
    prev_conv = None
    for band in band_order:
        if band not in bands:
            continue
        conv = bands[band]["conversion_pct"]
        if prev_conv is not None and conv > prev_conv:
            print(f"  ⚠️  Banda {band} convierte más que banda anterior — revisar pesos de scoring")
        prev_conv = conv

    best_source = max(data["by_source"], key=lambda x: data["by_source"][x]["conversion_pct"], default=None)
    if best_source:
        best_conv = data["by_source"][best_source]["conversion_pct"]
        if best_conv > 0:
            print(f"  ✅ Mejor fuente: {best_source} ({best_conv}%) — priorizar en búsqueda")

    print("=" * 55 + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Cargar env desde config/layer_1.env (ruta relativa a este script)
    env_path = os.path.join(os.path.dirname(__file__), "..", "config", "layer_1.env")
    load_dotenv(dotenv_path=os.path.abspath(env_path), override=True)

    if not os.environ.get("NOTION_TOKEN"):
        load_dotenv(override=True)

    token = os.environ.get("NOTION_TOKEN")
    if not token:
        sys.exit("ERROR: NOTION_TOKEN no encontrado.")

    print("Consultando VANTAGE TRACKER...", end=" ", flush=True)
    items = query_all(token)
    print(f"{len(items)} entradas.")

    data = analyze(items)

    if "--json" in sys.argv:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print_report(data)


if __name__ == "__main__":
    main()
