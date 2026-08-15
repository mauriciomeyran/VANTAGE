#!/usr/bin/env python3
"""
adapt_tracker_export.py — Adapta un export crudo de Notion (Opportunities
Tracker) al formato que consume cv_a_batch_agent.py.

Mapeo de columnas (Notion nativo -> cv_a_batch_agent.py):
  Marca            -> Empresa
  Rol              -> Rol
  URL              -> URL
  Next_Action      -> Next_Action
  JD               -> se escribe a un .txt por fila -> JD_File
  ID_Vacante       -> JOB_ID si existe; si no, hash[:12]; si no, índice de fila

No modifica ni interpreta Next_Action ni ningún campo Class B — solo
renombra/reestructura columnas y externaliza el JD ya presente en el
export a archivos de texto. Cero llamadas de red, cero escritura a Notion.

Uso:
    python3 adapt_tracker_export.py --in TRACKER_export.csv --out-dir ./adapted
"""

import argparse
import csv
import sys
from pathlib import Path


def build_id(row: dict, idx: int) -> str:
    job_id = (row.get("JOB_ID") or "").strip()
    if job_id:
        return job_id
    h = (row.get("hash") or "").strip()
    if h:
        return h[:12]
    return f"row{idx:03d}"


def main():
    parser = argparse.ArgumentParser(description="Adapta export crudo de Notion al formato de cv_a_batch_agent.py")
    parser.add_argument("--in", dest="in_csv", required=True, help="CSV export crudo del Opportunities Tracker")
    parser.add_argument("--out-dir", default="./adapted", help="Directorio de salida (CSV adaptado + JD .txt)")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    jd_dir = out_dir / "jd_files"
    jd_dir.mkdir(parents=True, exist_ok=True)

    with open(args.in_csv, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"Rol", "Marca", "URL", "Next_Action", "JD"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            print(f"ERROR: columnas faltantes en el export: {missing}", file=sys.stderr)
            sys.exit(1)
        rows = list(reader)

    adapted_rows = []
    for idx, row in enumerate(rows):
        id_vac = build_id(row, idx)
        jd_text = (row.get("JD") or "").strip()
        jd_file_path = ""
        if jd_text:
            jd_file_path = jd_dir / f"{id_vac}.txt"
            with open(jd_file_path, "w", encoding="utf-8") as jf:
                jf.write(jd_text)

        url_val = (row.get("URL") or "").strip()
        # Normaliza URLs sin esquema (Notion a veces las guarda sin https://)
        if url_val and not url_val.startswith(("http://", "https://")):
            url_val = "https://" + url_val

        adapted_rows.append({
            "ID_Vacante": id_vac,
            "Empresa": (row.get("Marca") or "").strip(),
            "Rol": (row.get("Rol") or "").strip(),
            "URL": url_val,
            "Next_Action": (row.get("Next_Action") or "").strip(),
            "JD_File": str(jd_file_path) if jd_file_path else "",
        })

    out_csv = out_dir / "tracker_adapted.csv"
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["ID_Vacante", "Empresa", "Rol", "URL", "Next_Action", "JD_File"])
        writer.writeheader()
        writer.writerows(adapted_rows)

    elegibles = sum(1 for r in adapted_rows if r["Next_Action"] == "Optimizar")
    sin_jd = sum(1 for r in adapted_rows if not r["JD_File"])

    print(f"OK — {len(adapted_rows)} filas adaptadas.")
    print(f"CSV adaptado: {out_csv}")
    print(f"JD files: {jd_dir} ({len(adapted_rows) - sin_jd} generados, {sin_jd} sin JD)")
    print(f"Elegibles (Next_Action == 'Optimizar'): {elegibles}")


if __name__ == "__main__":
    main()
