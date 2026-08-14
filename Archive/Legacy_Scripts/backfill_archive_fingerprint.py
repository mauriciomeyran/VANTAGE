#!/usr/bin/env python3
"""
Backfill de fingerprint de contenido sobre ARCHIVO TRACKER - caso jk rotativo (GILSA).

Smoke test primero con los 3 registros GILSA para confirmar que generan el mismo
fingerprint SHA-256 antes de proceder con el batch completo.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from collections import defaultdict
from notion_utils import Client

# Importar función real de feed_processor.py
sys.path.insert(0, str(Path(__file__).resolve().parent))
from feed_processor import content_fingerprint

# Configuración
script_dir = Path(__file__).resolve().parent
dotenv_path = script_dir.parent / "config" / "layer_1.env"
load_dotenv(dotenv_path=dotenv_path)

NOTION_TOKEN = os.getenv("NOTION_TOKEN") or os.getenv("NOTION_API_KEY")
ARCHIVO_TRACKER_DATA_SOURCE_ID = "674696fd-94b6-464a-ac1f-64b0cc917e15"  # ARCHIVO TRACKER

if not NOTION_TOKEN:
    print("[ERROR] NOTION_TOKEN no encontrado")
    sys.exit(1)

client = Client(auth=NOTION_TOKEN)

def get_plain_text(prop):
    """Extrae texto plano de una propiedad de Notion."""
    if not prop: return ""
    prop_type = prop.get('type')
    
    if prop_type == 'url':
        return prop.get('url', "") or ""
    if prop_type == 'rich_text' and prop.get('rich_text'):
        return prop['rich_text'][0]['plain_text'] if prop['rich_text'] else ""
    if prop_type == 'title' and prop.get('title'):
        return prop['title'][0]['plain_text'] if prop['title'] else ""
    if prop_type == 'select' and prop.get('select'):
        return prop['select']['name']
    return ""

print("=" * 70)
print("SMOKE TEST - 3 registros GILSA con jk rotativo")
print("=" * 70)

# IDs conocidos de GILSA
gilsa_known_ids = [
    "37e938befc428105bd5fcdb0dc197365",  # jk=9f45d9e2450010ca
    "37e938befc42818e8d9bc01d48fbde6a",  # jk=9f45d9e2450010ca (mismo jk)
]

print(f"\n[INFO] Obteniendo todos los registros GILSA del Archivo Tracker...")
all_results = client.data_sources.query(data_source_id=ARCHIVO_TRACKER_DATA_SOURCE_ID)["results"]
print(f"[INFO] {len(all_results)} entradas en Archivo Tracker")

all_gilsa = []
for item in all_results:
    props = item["properties"]
    marca = get_plain_text(props.get("Marca"))
    rol = get_plain_text(props.get("Rol"))
    job_id = get_plain_text(props.get("JOB_ID"))
    
    if "gilsa" in marca.lower():
        record = {
            "id": item["id"],
            "Marca": marca,
            "Rol": rol,
            "Ubicación": get_plain_text(props.get("Ubicación")),
            "JOB_ID": job_id,
            "created_time": item.get("created_time", ""),
        }
        all_gilsa.append(record)

print(f"[INFO] Total registros GILSA encontrados: {len(all_gilsa)}")
for record in all_gilsa:
    print(f"  - {record['id'][:8]}... | {record['Marca']} | {record['Rol']} | JK: {record['JOB_ID']}")

# Buscar específicamente los registros del caso jk rotativo
print(f"\n[INFO] Buscando registros con jks específicos del caso rotativo...")
target_jks = ["9f45d9e2450010ca", "cf3ca0540af5d305", "cf3ca0540af5e1f7cb5"]
gilsa_jk_records = []

for record in all_gilsa:
    if record["JOB_ID"] in target_jks:
        gilsa_jk_records.append(record)
        print(f"[FOUND] {record['id'][:8]}... | {record['Marca']} | {record['Rol']} | JK: {record['JOB_ID']}")

# Si no se encuentran suficientes por JK, buscar por marca+rol
gilsa_records = []
if len(gilsa_jk_records) >= 3:
    gilsa_records = gilsa_jk_records
    print(f"[INFO] Usando {len(gilsa_records)} registros encontrados por JK")
else:
    print(f"[INFO] Solo {len(gilsa_jk_records)} registros por JK, buscando por marca+rol...")
    
    # Usar los IDs conocidos
    for known_id in gilsa_known_ids:
        for record in all_gilsa:
            if record["id"] == known_id and record not in gilsa_records:
                gilsa_records.append(record)
                print(f"[ADDED] {record['id'][:8]}... (ID conocido)")
    
    # Buscar por marca+rol si faltan
    if len(gilsa_records) < 3:
        for record in all_gilsa:
            if "coordinador de exhibiciones" in record["Rol"].lower() and record not in gilsa_records:
                gilsa_records.append(record)
                print(f"[ADDED] {record['id'][:8]}... (marca+rol match)")
                if len(gilsa_records) >= 3:
                    break

print(f"\n[INFO] Total registros GILSA seleccionados para smoke test: {len(gilsa_records)}")

if len(gilsa_records) < 3:
    print(f"[ERROR] Se esperaban 3 registros GILSA, se encontraron {len(gilsa_records)}")
    print("[INFO] No se puede proceder con el smoke test")
    sys.exit(1)

# Calcular fingerprints SHA-256 para los registros seleccionados
print(f"\n[SMOKE TEST] Calculando fingerprints SHA-256...")
fingerprints = []
for record in gilsa_records:
    # Construir record en el formato que espera content_fingerprint()
    fp_record = {
        "brand": record["Marca"],
        "brand_raw": record["Marca"],
        "title": record["Rol"],
        "location": record["Ubicación"],
    }
    fp = content_fingerprint(fp_record)
    fingerprints.append(fp)
    print(f"  - {record['id'][:8]}... | {record['Marca']} | {record['Rol']} | JK: {record['JOB_ID']}")
    print(f"    Fingerprint: {fp}")

# Verificar si los 3 son idénticos
if len(set(fingerprints)) == 1:
    print(f"\n[SUCCESS] ✅ Los {len(gilsa_records)} registros GILSA tienen el MISMO fingerprint SHA-256")
    print(f"          Fingerprint común: {fingerprints[0]}")
    print(f"\n[INFO] Smoke test PASADO - se puede proceder con el batch completo")
else:
    print(f"\n[ERROR] ❌ Los registros GILSA tienen fingerprints DIFERENTES")
    print(f"[INFO] Algo está mal en la normalización - no se puede proceder")
    for i, (record, fp) in enumerate(zip(gilsa_records, fingerprints)):
        print(f"  - Registro {i+1}: {fp}")
    sys.exit(1)

print("\n" + "=" * 70)
print("DRY-RUN COMPLETO - ARCHIVO TRACKER")
print("=" * 70)

# Revisar schema del Archivo Tracker para confirmar qué campo usar
print(f"\n[INFO] Revisando schema del Archivo Tracker...")
sample_page = all_results[0] if all_results else None
if sample_page:
    props = sample_page["properties"]
    print(f"[INFO] Propiedades disponibles en Archivo Tracker:")
    for prop_name in sorted(props.keys()):
        prop_type = props[prop_name].get("type")
        print(f"  - {prop_name} ({prop_type})")

# Ahora hacer el dry-run completo
print(f"\n[INFO] Procesando todos los registros del Archivo Tracker...")

jobs = []
for item in all_results:
    props = item["properties"]
    job = {
        "id": item["id"],
        "Marca": get_plain_text(props.get("Marca")),
        "Rol": get_plain_text(props.get("Rol")),
        "Ubicación": get_plain_text(props.get("Ubicación")),
        "Status": get_plain_text(props.get("Status")),
        "created_time": item.get("created_time", ""),
        "JOB_ID": get_plain_text(props.get("JOB_ID")),
    }
    jobs.append(job)

print(f"[INFO] {len(jobs)} registros procesados")

# Agrupar por fingerprint (usando la función real)
fingerprint_groups = defaultdict(list)
for job in jobs:
    record = {
        "brand": job["Marca"],
        "brand_raw": job["Marca"],
        "title": job["Rol"],
        "location": job["Ubicación"],
    }
    fp = content_fingerprint(record)
    if fp:
        fingerprint_groups[fp].append(job)

# Encontrar grupos con más de 1 registro
duplicate_groups = {fp: group for fp, group in fingerprint_groups.items() if len(group) > 1}

print(f"\n[DRY-RUN] {len(duplicate_groups)} grupos de duplicados encontrados")

print(f"\n[DRY-RUN] Lista completa de grupos propuestos:")
for fp, group in duplicate_groups.items():
    print(f"\n--- Fingerprint: {fp[:32]}... ({len(group)} registros) ---")
    for job in group:
        print(f"  - ID: {job['id'][:8]}... | {job['Marca']} | {job['Rol']} | {job['Ubicación']} | JK: {job['JOB_ID']} | Creado: {job['created_time'][:10]}")

total_proposed = sum(len(group) - 1 for group in duplicate_groups.values())
print(f"\n[DRY-RUN] Total de registros que se marcarían como duplicados: {total_proposed}")
print(f"[INFO] Esperando APROBAR_WRITE antes de aplicar cambios a Notion")
