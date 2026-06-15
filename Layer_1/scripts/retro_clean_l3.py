#!/usr/bin/env python3
"""
VANTAGE — Retro Clean L3
Limpieza retroactiva de ruido en VANTAGE TRACKER (Class B legado de L3).

Reutiliza la lógica de canonicalize_url() (Fix B) y normalize_text() (Fix C)
ya aplicada en layer_3_mail.py, pero corriéndola contra TODO el Tracker
existente en lugar de correos nuevos.

Acciones:
  - SYNTHETIC_AGGREGATOR_URL / UNRESOLVABLE_REDIRECT / NO_URL  -> archivar (trash)
  - DUP_CROSS_EMAIL (Rol+Marca normalizados ya existen)        -> archivar (trash)
  - LinkedIn/Indeed con tracking params                        -> canonicalizar URL (no archivar)

Reglas:
  - Solo se archivan filas con layer == "L3".
  - Nunca se archiva una fila L1/L2, aunque sea el "duplicado" detectado.
  - DRY RUN por default. Requiere --yes para escribir en Notion.

Uso:
  python3 retro_clean_l3.py            # dry run -> retro_clean_l3_dryrun.json
  python3 retro_clean_l3.py --yes      # ejecuta archivado + canonicalización
"""

import os
import re
import sys
import json
import time
import unicodedata
from pathlib import Path
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

import requests
from dotenv import load_dotenv

# ──────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────
for _candidate in (
    Path(__file__).resolve().parent / "config" / "layer_3.env",
    Path(__file__).resolve().parent / ".env",
    Path.cwd() / "config" / "layer_3.env",
    Path.cwd() / ".env",
):
    if _candidate.exists():
        load_dotenv(_candidate, override=True)

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
# Confirmado en bugfix vdedup — data_sources/{id}/query, NO databases/{id}/query
DATA_SOURCE_ID = os.environ.get(
    "NOTION_TRACKER_DATA_SOURCE_ID", "442938be-fc42-828f-b72e-076818d65a5b"
)

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2025-09-03",
}

MAX_EXPECTED_RESULTS = 500
DEDUP_PRIORITY = {"L1": 1, "L2": 2, "L3": 3}

DRYRUN_PATH = Path(__file__).resolve().parent / "retro_clean_l3_dryrun.json"


# ──────────────────────────────────────────
# canonicalize_url() — Fix B (idéntico a layer_3_mail.py)
# ──────────────────────────────────────────
STRIP_PARAMS = {
    "linkedin.com": {"trackingId", "refId", "trk", "src"},
}

SYNTHETIC_CT_PATTERNS = [
    re.compile(r'/jobs/\d{4,8}$'),
    re.compile(r'/jobs/\d{10,}$'),
    re.compile(r'\d{4}-\d{4}-\d{4}'),
    re.compile(r'-(12345|67890|23456|34567|89012)'),
]


def canonicalize_url(url: str) -> tuple[str, str]:
    """Devuelve (canonical_url, rejection_reason | "")."""
    if not url or not url.startswith("http"):
        return url, "NO_URL"

    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    if "computrabajo" in domain:
        for pat in SYNTHETIC_CT_PATTERNS:
            if pat.search(parsed.path) or pat.search(url):
                return url, "SYNTHETIC_AGGREGATOR_URL"

    if "indeed.com/rc/clk" in url or "indeed.com/applystart" in url:
        try:
            r = requests.head(url, allow_redirects=True, timeout=5,
                               headers={"User-Agent": "Mozilla/5.0"})
            resolved = r.url
            if "indeed.com" not in resolved:
                return resolved, ""
        except Exception:
            pass
        params = parse_qs(parsed.query)
        jk = params.get("jk", [""])[0]
        if jk:
            return f"https://mx.indeed.com/viewjob?jk={jk}", ""
        return url, "UNRESOLVABLE_REDIRECT"

    if "linkedin.com" in domain:
        path = parsed.path.replace("/comm/jobs/", "/jobs/")
        params = parse_qs(parsed.query)
        clean_params = {k: v for k, v in params.items()
                         if k not in STRIP_PARAMS.get("linkedin.com", set())}
        clean_query = urlencode(clean_params, doseq=True)
        canonical = urlunparse((parsed.scheme, parsed.netloc, path,
                                 parsed.params, clean_query, ""))
        return canonical, ""

    return url, ""


# ──────────────────────────────────────────
# normalize_text() — Fix C (idéntico a layer_3_mail.py)
# ──────────────────────────────────────────
def normalize_text(s: str) -> str:
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]", " ", s).strip()


# ──────────────────────────────────────────
# Notion — fetch completo via data_sources/{id}/query
# ──────────────────────────────────────────
def _prop_title(props, name):
    try:
        arr = props.get(name, {}).get("title", [])
        return arr[0]["plain_text"] if arr else ""
    except (IndexError, KeyError, TypeError):
        return ""


def _prop_rich_text(props, name):
    try:
        arr = props.get(name, {}).get("rich_text", [])
        return arr[0]["plain_text"] if arr else ""
    except (IndexError, KeyError, TypeError):
        return ""


def _prop_url(props, name):
    return props.get(name, {}).get("url") or ""


def _prop_select(props, name):
    sel = props.get(name, {}).get("select")
    return sel["name"] if sel else ""


def fetch_all_rows():
    rows = []
    payload = {
        "page_size": 100,
        "sorts": [{"timestamp": "created_time", "direction": "ascending"}],
    }
    url = f"https://api.notion.com/v1/data_sources/{DATA_SOURCE_ID}/query"

    while True:
        resp = requests.post(url, headers=HEADERS, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        for page in data.get("results", []):
            if page.get("in_trash") or page.get("archived"):
                continue
            rows.append(page)

        if len(rows) > MAX_EXPECTED_RESULTS:
            print(f"  ⚠️  MAX_EXPECTED_RESULTS ({MAX_EXPECTED_RESULTS}) superado — abortando")
            break

        if data.get("has_more") and data.get("next_cursor"):
            payload["start_cursor"] = data["next_cursor"]
        else:
            break

    return rows


# ──────────────────────────────────────────
# Análisis
# ──────────────────────────────────────────
def analyze(rows):
    """
    Devuelve:
      to_archive: list de {page_id, rol, marca, url, layer, reason}
      to_canonicalize: list de {page_id, rol, marca, old_url, new_url}
    """
    parsed = []
    for page in rows:
        props = page.get("properties", {})
        parsed.append({
            "id":      page["id"],
            "created": page.get("created_time", ""),
            "rol":     _prop_title(props, "Rol"),
            "marca":   _prop_rich_text(props, "Marca"),
            "url":     _prop_url(props, "URL"),
            "layer":   _prop_select(props, "layer"),
        })

    to_archive = []
    to_canonicalize = []
    archived_ids = set()

    # ── Paso 1: canonicalización / detección de URLs sintéticas (solo L3) ──
    for row in parsed:
        if row["layer"] != "L3":
            continue
        canonical, reason = canonicalize_url(row["url"])
        if reason:
            to_archive.append({
                "page_id": row["id"],
                "rol": row["rol"],
                "marca": row["marca"],
                "url": row["url"],
                "layer": row["layer"],
                "reason": reason,
            })
            archived_ids.add(row["id"])
        elif canonical != row["url"]:
            to_canonicalize.append({
                "page_id": row["id"],
                "rol": row["rol"],
                "marca": row["marca"],
                "old_url": row["url"],
                "new_url": canonical,
            })

    # ── Paso 2: duplicados cross-email por Rol+Marca normalizados ──
    groups: dict[tuple[str, str], list[dict]] = {}
    for row in parsed:
        if not row["marca"]:
            continue
        key = (normalize_text(row["rol"]), normalize_text(row["marca"]))
        groups.setdefault(key, []).append(row)

    for key, members in groups.items():
        if len(members) < 2:
            continue
        # keeper = mayor prioridad de layer (L1>L2>L3), empate -> más antiguo
        keeper = min(
            members,
            key=lambda r: (DEDUP_PRIORITY.get(r["layer"], 99), r["created"]),
        )
        for r in members:
            if r["id"] == keeper["id"]:
                continue
            if r["id"] in archived_ids:
                continue  # ya se archiva por otra razón
            if r["layer"] != "L3":
                continue  # nunca archivar L1/L2
            to_archive.append({
                "page_id": r["id"],
                "rol": r["rol"],
                "marca": r["marca"],
                "url": r["url"],
                "layer": r["layer"],
                "reason": "DUP_CROSS_EMAIL",
            })
            archived_ids.add(r["id"])

    return to_archive, to_canonicalize, len(parsed)


# ──────────────────────────────────────────
# Escritura
# ──────────────────────────────────────────
def archive_page(page_id):
    resp = requests.patch(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers=HEADERS,
        json={"in_trash": True},
        timeout=15,
    )
    return resp.status_code == 200, resp.text


def canonicalize_page_url(page_id, new_url):
    resp = requests.patch(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers=HEADERS,
        json={"properties": {"URL": {"url": new_url}}},
        timeout=15,
    )
    return resp.status_code == 200, resp.text


# ──────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────
def main():
    execute = "--yes" in sys.argv

    print("📥 Descargando Tracker completo (data_sources/{id}/query)...")
    rows = fetch_all_rows()
    print(f"   Total filas: {len(rows)}")

    to_archive, to_canonicalize, total = analyze(rows)

    by_reason = {}
    for item in to_archive:
        by_reason[item["reason"]] = by_reason.get(item["reason"], 0) + 1

    print(f"\n{'─'*40}")
    print(f"📊 RESUMEN — {total} filas analizadas")
    print(f"{'─'*40}")
    for reason, count in by_reason.items():
        print(f"  {reason:<26} {count}")
    print(f"  {'CANONICALIZE_URL':<26} {len(to_canonicalize)}")
    print(f"  {'─'*30}")
    print(f"  Total a archivar:          {len(to_archive)}")
    print(f"  Total a canonicalizar URL: {len(to_canonicalize)}")
    print(f"  Quedan activas:            {total - len(to_archive)}")
    print(f"{'─'*40}\n")

    DRYRUN_PATH.write_text(
        json.dumps({"to_archive": to_archive, "to_canonicalize": to_canonicalize},
                    indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"📄 Detalle guardado en: {DRYRUN_PATH}")

    if not execute:
        print("\n⏹️  DRY RUN — nada escrito. Revisa el JSON y corre con --yes para ejecutar.")
        return

    print("\n📝 Ejecutando...")
    archived_ok = archived_fail = 0
    for item in to_archive:
        ok, err = archive_page(item["page_id"])
        if ok:
            archived_ok += 1
        else:
            archived_fail += 1
            print(f"  ❌ Error archivando {item['page_id']}: {err[:120]}")
        time.sleep(0.34)  # ~3 req/s, margen bajo rate limit de Notion

    canon_ok = canon_fail = 0
    for item in to_canonicalize:
        ok, err = canonicalize_page_url(item["page_id"], item["new_url"])
        if ok:
            canon_ok += 1
        else:
            canon_fail += 1
            print(f"  ❌ Error canonicalizando {item['page_id']}: {err[:120]}")
        time.sleep(0.34)

    print(f"\n✅ Archivadas: {archived_ok}  |  ❌ Fallidas: {archived_fail}")
    print(f"✅ URLs canonicalizadas: {canon_ok}  |  ❌ Fallidas: {canon_fail}")


if __name__ == "__main__":
    main()
