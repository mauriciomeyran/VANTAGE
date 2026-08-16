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
import hashlib
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


def validate_url(url: str) -> bool:
    """Valida que una URL tenga un formato básico correcto."""
    if not url:
        return False
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        return False
    # Validación básica de formato
    if "." not in url.split("//")[1]:
        return False
    return True


def generate_url_hash(url: str) -> str:
    """Genera un hash único para una URL para detección de duplicados."""
    return hashlib.md5(url.strip().lower().encode()).hexdigest()


def detect_duplicates(rows: list[dict]) -> tuple[list[dict], list[str]]:
    """Detecta filas duplicadas basadas en URL o hash.
    
    Returns:
        tuple: (filas únicas, lista de IDs duplicados eliminados)
    """
    seen_urls = set()
    seen_hashes = set()
    unique_rows = []
    duplicate_ids = []
    
    for row in rows:
        url = (row.get("URL") or "").strip()
        row_hash = (row.get("hash") or "").strip()
        
        # Generar hash de URL para comparación
        url_hash = generate_url_hash(url) if url else None
        
        # Verificar duplicados
        is_duplicate = False
        duplicate_reason = ""
        
        if url and url_hash in seen_urls:
            is_duplicate = True
            duplicate_reason = f"URL duplicada: {url}"
        elif row_hash and row_hash in seen_hashes:
            is_duplicate = True
            duplicate_reason = f"Hash duplicado: {row_hash[:12]}"
        
        if is_duplicate:
            id_vac = build_id(row, rows.index(row))
            duplicate_ids.append(f"{id_vac} ({duplicate_reason})")
        else:
            unique_rows.append(row)
            if url:
                seen_urls.add(url_hash)
            if row_hash:
                seen_hashes.add(row_hash)
    
    return unique_rows, duplicate_ids


def main():
    parser = argparse.ArgumentParser(description="Adapta export crudo de Notion al formato de cv_a_batch_agent.py")
    parser.add_argument("--in", dest="in_csv", required=True, help="CSV export crudo del Opportunities Tracker")
    parser.add_argument("--out-dir", default="./adapted", help="Directorio de salida (CSV adaptado + JD .txt)")
    parser.add_argument("--skip-dup-check", action="store_true", help="Saltar detección de duplicados")
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

    # Detección de duplicados
    if not args.skip_dup_check:
        original_count = len(rows)
        rows, duplicate_ids = detect_duplicates(rows)
        if duplicate_ids:
            print(f"⚠️  Duplicados detectados y eliminados: {len(duplicate_ids)}")
            for dup_id in duplicate_ids[:5]:  # Mostrar primeros 5
                print(f"   - {dup_id}")
            if len(duplicate_ids) > 5:
                print(f"   ... y {len(duplicate_ids) - 5} más")
            print(f"   Filas originales: {original_count} → Filas únicas: {len(rows)}")

    adapted_rows = []
    invalid_urls = []
    missing_rols = []
    
    for idx, row in enumerate(rows):
        id_vac = build_id(row, idx)
        
        # Validaciones
        rol = (row.get("Rol") or "").strip()
        if not rol:
            missing_rols.append(id_vac)
            
        url_val = (row.get("URL") or "").strip()
        if url_val and not validate_url(url_val):
            invalid_urls.append(f"{id_vac}: {url_val}")
            # Normalizar URLs sin esquema (Notion a veces las guarda sin https://)
            if url_val and not url_val.startswith(("http://", "https://")):
                url_val = "https://" + url_val
        
        jd_text = (row.get("JD") or "").strip()
        jd_file_path = ""
        if jd_text:
            jd_file_path = jd_dir / f"{id_vac}.txt"
            with open(jd_file_path, "w", encoding="utf-8") as jf:
                jf.write(jd_text)

        adapted_rows.append({
            "ID_Vacante": id_vac,
            "Empresa": (row.get("Marca") or "").strip(),
            "Rol": rol,
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

    print(f"✅ OK — {len(adapted_rows)} filas adaptadas.")
    print(f"📄 CSV adaptado: {out_csv}")
    print(f"📁 JD files: {jd_dir} ({len(adapted_rows) - sin_jd} generados, {sin_jd} sin JD)")
    print(f"🎯 Elegibles (Next_Action == 'Optimizar'): {elegibles}")
    
    # Reporte de validaciones
    if invalid_urls:
        print(f"⚠️  URLs inválidas detectadas: {len(invalid_urls)}")
        for inv_url in invalid_urls[:3]:
            print(f"   - {inv_url}")
        if len(invalid_urls) > 3:
            print(f"   ... y {len(invalid_urls) - 3} más")
    
    if missing_rols:
        print(f"⚠️  Filas sin Rol: {len(missing_rols)}")
        if len(missing_rols) <= 3:
            for missing_id in missing_rols:
                print(f"   - {missing_id}")
        else:
            print(f"   - {missing_rols[0]}, {missing_rols[1]}, ... y {len(missing_rols) - 2} más")


if __name__ == "__main__":
    main()
