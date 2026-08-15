#!/usr/bin/env python3
"""
cv_a_batch_agent.py — Fase 1 (agente local): loop mecánico sobre un export
del Opportunities Tracker, corriendo cv_a_prep.py por cada fila elegible.

CERO escritura a Notion. Este script opera exclusivamente sobre un CSV
local (export manual o vía notion-query-data-sources) y produce:
  1. Un scaffold .md por vacante elegible (o reporte BLOCKED_...).
  2. Un reporte CSV de resultados (`cv_a_batch_report_<fecha>.csv`) que
     Claude usa como input para la Fase 2 (DRY RUN -> APROBAR_WRITE ->
     escritura gobernada a Notion). Este script NUNCA decide valores de
     schema ni escribe Next_Action — eso es exclusivo de Fase 2, con
     operador y Claude en el loop.

Requisitos del CSV de entrada (columnas mínimas, nombres exactos):
  ID_Vacante, Empresa, Rol, URL, Next_Action, JD_File (opcional)

Uso:
    python3 cv_a_batch_agent.py --csv tracker_export.csv --cv-a-prep ./cv_a_prep.py

Filtro: procesa únicamente filas con Next_Action == "Optimizar"
(exacto, sensible a mayúsculas — consistente con SP:SCHEMA).
"""

import argparse
import csv
import datetime
import subprocess
import sys
from pathlib import Path

TARGET_NEXT_ACTION = "Optimizar"


def load_rows(csv_path: str) -> list[dict]:
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"ID_Vacante", "Empresa", "Rol", "URL", "Next_Action"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            print(f"ERROR: columnas faltantes en el CSV: {missing}", file=sys.stderr)
            sys.exit(1)
        return list(reader)


def run_cv_a_prep(cv_a_prep_path: str, row: dict, out_dir: Path) -> dict:
    id_vac = row["ID_Vacante"].strip()
    empresa = row["Empresa"].strip()
    rol = row["Rol"].strip()
    url = row.get("URL", "").strip()
    jd_file = row.get("JD_File", "").strip()

    out_path = out_dir / f"HANDOFF_scaffold_{id_vac}.md"

    cmd = [sys.executable, cv_a_prep_path, "--empresa", empresa, "--rol", rol, "--out", str(out_path)]
    if url:
        cmd += ["--url", url]
    if jd_file:
        cmd += ["--jd-file", jd_file]

    if not url and not jd_file:
        return {
            "ID_Vacante": id_vac,
            "Empresa": empresa,
            "Rol": rol,
            "resultado": "ERROR",
            "detalle": "Sin URL ni JD_File — no procesable",
            "scaffold_path": "",
        }

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return {
            "ID_Vacante": id_vac,
            "Empresa": empresa,
            "Rol": rol,
            "resultado": "ERROR",
            "detalle": "Timeout ejecutando cv_a_prep.py",
            "scaffold_path": "",
        }

    stdout = proc.stdout.strip()
    if "HARD BLOCK" in stdout:
        resultado = "BLOCKED"
    elif proc.returncode == 0:
        resultado = "SCAFFOLD_OK"
    else:
        resultado = "ERROR"

    return {
        "ID_Vacante": id_vac,
        "Empresa": empresa,
        "Rol": rol,
        "resultado": resultado,
        "detalle": stdout.replace("\n", " | ") or proc.stderr.strip().replace("\n", " | "),
        "scaffold_path": str(out_path) if resultado != "ERROR" else "",
    }


def main():
    parser = argparse.ArgumentParser(description="Batch runner local para cv_a_prep.py (sin escritura a Notion)")
    parser.add_argument("--csv", required=True, help="CSV export del Opportunities Tracker")
    parser.add_argument("--cv-a-prep", default="./cv_a_prep.py", help="Ruta a cv_a_prep.py")
    parser.add_argument("--out-dir", default=".", help="Directorio de salida para scaffolds")
    args = parser.parse_args()

    if not Path(args.cv_a_prep).exists():
        print(f"ERROR: no se encuentra cv_a_prep.py en {args.cv_a_prep}", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = load_rows(args.csv)
    elegibles = [r for r in rows if r.get("Next_Action", "").strip() == TARGET_NEXT_ACTION]

    print(f"Total filas en CSV: {len(rows)}")
    print(f"Elegibles (Next_Action == '{TARGET_NEXT_ACTION}'): {len(elegibles)}")

    results = []
    for row in elegibles:
        res = run_cv_a_prep(args.cv_a_prep, row, out_dir)
        results.append(res)
        print(f"  [{res['resultado']}] {res['Empresa']} — {res['Rol']} ({res['ID_Vacante']})")

    fecha = datetime.date.today().isoformat()
    report_path = out_dir / f"cv_a_batch_report_{fecha}.csv"
    with open(report_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["ID_Vacante", "Empresa", "Rol", "resultado", "detalle", "scaffold_path"])
        writer.writeheader()
        writer.writerows(results)

    ok = sum(1 for r in results if r["resultado"] == "SCAFFOLD_OK")
    blocked = sum(1 for r in results if r["resultado"] == "BLOCKED")
    errors = sum(1 for r in results if r["resultado"] == "ERROR")

    print("\n--- Resumen ---")
    print(f"Procesados: {len(results)} | Scaffolds OK: {ok} | Bloqueados: {blocked} | Errores: {errors}")
    print(f"Reporte: {report_path}")
    print("\nCERO escritura a Notion realizada por este script.")
    print("Siguiente paso: pasar este reporte a Claude en sesión para Fase 2")
    print("(DRY RUN -> APROBAR_WRITE -> actualización gobernada del Tracker).")


if __name__ == "__main__":
    main()
