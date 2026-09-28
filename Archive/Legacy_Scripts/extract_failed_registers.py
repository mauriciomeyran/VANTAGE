#!/usr/bin/env python3
"""Extrae del JSON de reingesta los 2 registros que fallaron (Oniverse, Commando Retail)
y genera un JSON de reingreso selectivo. También identifica las 22 páginas que sí se
escribieron hoy para borrado previo."""

import json
from pathlib import Path

WORKSPACE = Path("/Users/mauriciomeyran/Documents/03 Projects/VANTAGE")
SRC = WORKSPACE / "reingest_consolidated_format.json"

with open(SRC) as f:
    data = json.load(f)

records = data["consolidated_results"]

# Los 2 fallidos: Oniverse (index 7) y Commando Retail (index 22)
FAILED_INDICES = {7, 22}  # 0-based

failed = []
ok = []
for i, r in enumerate(records):
    entry = {
        "brand": r["brand"],
        "title": r["title"],
        "location": r.get("location", ""),
        "apply_url": r.get("apply_url", ""),
        "source_type": r.get("source_type", ""),
        "source_name": r.get("source_name", ""),
        "fetch_status": r.get("fetch_status", ""),
        "holding": r.get("holding", ""),
        "posted_date": r.get("posted_date", ""),
        "notes": r.get("notes", ""),
        "jd": r.get("jd", ""),
        "priority": r.get("priority", ""),
        "job_id": r.get("job_id", ""),
        "status": r.get("status", ""),
        "positioning_mode": r.get("positioning_mode", ""),
        "nad": r.get("nadir", "") or r.get("nad", ""),
        "layer": r.get("layer", ""),
        "hash": r.get("hash", ""),
    }
    if i in FAILED_INDICES:
        failed.append(entry)
    else:
        ok.append(entry)

print(f"🔴 Registros fallidos (Oniverse, Commando Retail): {len(failed)}")
for r in failed:
    jd_len = len(r["jd"])
    print(f"  {r['brand']:20s} | {r['title'][:45]:45s} | JD={jd_len} chars | hash={r['hash'][:16]}")

# Guardar JSON de reingreso selectivo
out = {"consolidated_results": failed, "reroute_candidates_history": [], "conflict_log": [], "data_quality_warnings": []}
out_path = WORKSPACE / "reingest_failed_2.json"
out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2))
print(f"\n💾 Guardado: {out_path}")
print(f"   Registros: {len(failed)}")
print(f"   Tamaño: {out_path.stat().st_size} bytes")

# Resumen de los 22 exitosos para borrado
print(f"\n🟢 Registros exitosos (a borrar antes de reingreso): {len(ok)}")
for r in ok:
    print(f"  {r['brand'][:25]:25s} | hash={r['hash'][:16]:16s} | status={r['status']}")
