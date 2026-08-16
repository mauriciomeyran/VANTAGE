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
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

TARGET_NEXT_ACTION = "Optimizar"
MAX_WORKERS = 3  # Número máximo de procesos paralelos (rate limiting)
CHECKPOINT_FILE = "cv_a_batch_checkpoint.json"


def load_checkpoint(checkpoint_path: Path) -> set:
    """Carga IDs de vacantes ya procesadas desde un checkpoint."""
    if not checkpoint_path.exists():
        return set()
    
    try:
        with open(checkpoint_path, "r") as f:
            data = json.load(f)
            return set(data.get("processed_ids", []))
    except Exception as e:
        print(f"AVISO: Error leyendo checkpoint ({e}). Iniciando desde cero.", file=sys.stderr)
        return set()


def save_checkpoint(checkpoint_path: Path, processed_id: str):
    """Guarda un ID de vacante procesada en el checkpoint."""
    try:
        if checkpoint_path.exists():
            with open(checkpoint_path, "r") as f:
                data = json.load(f)
        else:
            data = {"processed_ids": []}
        
        if processed_id not in data["processed_ids"]:
            data["processed_ids"].append(processed_id)
        
        with open(checkpoint_path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"AVISO: Error guardando checkpoint ({e}).", file=sys.stderr)


def show_progress(current: int, total: int, start_time: float):
    """Muestra una barra de progreso simple en consola."""
    if total == 0:
        return
    
    percent = (current / total) * 100
    bar_length = 40
    filled = int(bar_length * current / total)
    bar = "█" * filled + "░" * (bar_length - filled)
    
    elapsed = time.time() - start_time
    if current > 0:
        eta = (elapsed / current) * (total - current)
        eta_str = f"{int(eta // 60)}m {int(eta % 60)}s"
    else:
        eta_str = "N/A"
    
    print(f"\r[{bar}] {current}/{total} ({percent:.1f}%) | ETA: {eta_str}", end="", flush=True)
    if current == total:
        print()  # Nueva línea al completar


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


def run_cv_a_prep_with_retry(cv_a_prep_path: str, row: dict, out_dir: Path, max_retries: int = 2) -> dict:
    """Ejecuta cv_a_prep con reintentos para fallas temporales."""
    for attempt in range(max_retries + 1):
        result = run_cv_a_prep(cv_a_prep_path, row, out_dir)
        
        # Si el resultado es exitoso o es un error permanente, no reintentar
        if result["resultado"] in ["SCAFFOLD_OK", "BLOCKED"]:
            return result
        if "Sin URL ni JD_File" in result["detalle"]:
            return result  # Error permanente
        
        # Reintentar solo para errores temporales
        if attempt < max_retries:
            print(f"  ⚠️  Reintento {attempt + 1}/{max_retries} para {row['ID_Vacante']}")
            time.sleep(2)  # Espera antes de reintentar
    
    return result  # Último intento fallido


def main():
    parser = argparse.ArgumentParser(description="Batch runner local para cv_a_prep.py (sin escritura a Notion)")
    parser.add_argument("--csv", required=True, help="CSV export del Opportunities Tracker")
    parser.add_argument("--cv-a-prep", default="./cv_a_prep.py", help="Ruta a cv_a_prep.py")
    parser.add_argument("--out-dir", default=".", help="Directorio de salida para scaffolds")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS, help=f"Número de workers paralelos (default: {MAX_WORKERS})")
    parser.add_argument("--resume", action="store_true", help="Continuar desde checkpoint previo")
    parser.add_argument("--no-progress", action="store_true", help="Desactivar barra de progreso")
    args = parser.parse_args()

    if not Path(args.cv_a_prep).exists():
        print(f"ERROR: no se encuentra cv_a_prep.py en {args.cv_a_prep}", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    checkpoint_path = out_dir / CHECKPOINT_FILE

    rows = load_rows(args.csv)
    elegibles = [r for r in rows if r.get("Next_Action", "").strip() == TARGET_NEXT_ACTION]

    print(f"📊 Total filas en CSV: {len(rows)}")
    print(f"🎯 Elegibles (Next_Action == '{TARGET_NEXT_ACTION}'): {len(elegibles)}")
    
    # Filtrar ya procesados si resume está activo
    processed_ids = set()
    if args.resume:
        processed_ids = load_checkpoint(checkpoint_path)
        if processed_ids:
            elegibles = [r for r in elegibles if r["ID_Vacante"] not in processed_ids]
            print(f"🔄 Resume mode: {len(processed_ids)} ya procesados, {len(elegibles)} pendientes")
        else:
            print("ℹ️  Resume mode activo pero no hay checkpoint previo. Procesando todo.")

    if not elegibles:
        print("✅ No hay vacantes elegibles pendientes de procesar.")
        return

    print(f"🚀 Iniciando procesamiento con {args.workers} workers paralelos...")
    start_time = time.time()
    
    results = []
    completed_count = 0
    
    # Usar ThreadPoolExecutor para procesamiento paralelo
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        # Enviar todas las tareas
        future_to_row = {
            executor.submit(run_cv_a_prep_with_retry, args.cv_a_prep, row, out_dir): row 
            for row in elegibles
        }
        
        # Procesar resultados a medida que completan
        for future in as_completed(future_to_row):
            row = future_to_row[future]
            try:
                result = future.result()
                results.append(result)
                
                # Guardar checkpoint
                save_checkpoint(checkpoint_path, result["ID_Vacante"])
                
                # Mostrar progreso
                completed_count += 1
                if not args.no_progress:
                    show_progress(completed_count, len(elegibles), start_time)
                else:
                    print(f"  [{result['resultado']}] {result['Empresa']} — {result['Rol']} ({result['ID_Vacante']})")
                    
            except Exception as e:
                print(f"\n❌ Error procesando {row['ID_Vacante']}: {e}", file=sys.stderr)
                results.append({
                    "ID_Vacante": row["ID_Vacante"],
                    "Empresa": row["Empresa"],
                    "Rol": row["Rol"],
                    "resultado": "ERROR",
                    "detalle": f"Excepción: {str(e)}",
                    "scaffold_path": "",
                })

    elapsed = time.time() - start_time
    
    fecha = datetime.date.today().isoformat()
    report_path = out_dir / f"cv_a_batch_report_{fecha}.csv"
    with open(report_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["ID_Vacante", "Empresa", "Rol", "resultado", "detalle", "scaffold_path"])
        writer.writeheader()
        writer.writerows(results)

    ok = sum(1 for r in results if r["resultado"] == "SCAFFOLD_OK")
    blocked = sum(1 for r in results if r["resultado"] == "BLOCKED")
    errors = sum(1 for r in results if r["resultado"] == "ERROR")

    print(f"\n{'='*60}")
    print(f"📋 RESUMEN FINAL")
    print(f"{'='*60}")
    print(f"⏱️  Tiempo total: {int(elapsed // 60)}m {int(elapsed % 60)}s")
    print(f"📊 Procesados: {len(results)}")
    print(f"✅ Scaffolds OK: {ok}")
    print(f"🚫 Bloqueados: {blocked}")
    print(f"❌ Errores: {errors}")
    print(f"📄 Reporte: {report_path}")
    print(f"{'='*60}")
    print("\nCERO escritura a Notion realizada por este script.")
    print("Siguiente paso: pasar este reporte a Claude en sesión para Fase 2")
    print("(DRY RUN -> APROBAR_WRITE -> actualización gobernada del Tracker).")
    
    # Limpiar checkpoint si todo fue exitoso
    if errors == 0 and blocked == 0:
        if checkpoint_path.exists():
            checkpoint_path.unlink()
            print("✨ Checkpoint limpiado (procesamiento completo exitoso).")


if __name__ == "__main__":
    main()
