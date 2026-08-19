#!/usr/bin/env python3
"""
backfill_next_action_select.py — Backfill para migración Next_Action rich_text → select (v9.14.2)

Script para migrar valores legacy de Next_Action al nuevo formato select.
Detecta registros que quedaron vacíos tras la conversión automática de Notion
y recalcula el valor correcto usando la lógica existente del pipeline.

Uso:
    python3 backfill_next_action_select.py [--execute]

Opciones:
    --execute    Escribe los cambios en Notion (sin este flag, solo reporta dry-run)

Modo dry-run por default: safe por design (KERNEL:TRIGGER-002).
"""

import os
import sys
import argparse
import httpx
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv("../.env")

VANTAGE_DATA_SOURCE_ID = "442938be-fc42-828f-b72e-076818d65a5b"
VANTAGE_NOTION_VERSION = "2025-09-03"
VANTAGE_NOTION_API_BASE = "https://api.notion.com/v1"

# Los 8 valores válidos para Next_Action (deben coincidir EXACTO con Notion)
VALID_NEXT_ACTIONS = {
    "Archivar",
    "Expirada", 
    "Ninguna",
    "Follow-up",
    "Interview prep",
    "Re-check",
    "Reparar URL",
    "Verificar JD"
}


def txt(prop):
    """Helper para extraer texto de propiedades Notion (misma función que layer_1_run.py)"""
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
    if t == "number": 
        return prop.get("number")
    if t == "date" and prop.get("date"):
        return prop["date"]["start"]
    return ""


def query_all_tracker_records():
    """
    Pagina todos los registros del Tracker vía data_sources/{id}/query (API 2025-09-03).
    Retorna lista completa de registros.
    """
    token = os.environ["NOTION_TOKEN"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": VANTAGE_NOTION_VERSION,
        "Content-Type": "application/json",
    }
    url = f"{VANTAGE_NOTION_API_BASE}/data_sources/{VANTAGE_DATA_SOURCE_ID}/query"

    all_results = []
    cursor = None

    print(f"Conectando a Tracker: {VANTAGE_DATA_SOURCE_ID}")

    with httpx.Client(timeout=30) as http_client:
        while True:
            body = {
                "page_size": 100,
                "sorts": [{"timestamp": "created_time", "direction": "ascending"}],
            }
            if cursor:
                body["start_cursor"] = cursor

            response = http_client.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()

            batch = data.get("results", [])
            all_results.extend(batch)
            print(f"  Pagina {len(all_results)} registros...")

            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")

    return all_results


def get_application_next_action(status):
    """
    Lógica de Next_Action para aplicaciones (misma función que layer_1_run.py).
    KERNEL:SCHEMA-008 define estos valores.
    """
    if status == "Postulado":
        return "Follow-up"
    elif status == "En proceso":
        return "Interview prep"
    elif status == "Negociando":
        return "Follow-up"
    elif status == "Sin respuesta":
        return "Follow-up"
    else:
        return "Re-check"


def evaluate_application_status(status):
    """Helper para detectar estados de aplicación (misma función que layer_1_run.py)"""
    application_statuses = ["Postulado", "En proceso", "Negociando", "Sin respuesta"]
    return status in application_statuses


def evaluate_rejection_status(status):
    """Helper para detectar estado de rechazo (misma función que layer_1_run.py)"""
    return status == "Rechazado"


def calculate_correct_next_action(props):
    """
    Recalcula el valor correcto de Next_Action usando la lógica del pipeline
    (gate_logic.py + get_application_next_action).
    
    Args:
        props: dict de propiedades Notion del registro
        
    Returns:
        str: valor correcto de Next_Action (uno de los 8 válidos)
    """
    # Extraer valores usando el helper txt
    rol = txt(props.get("Rol"))
    marca = txt(props.get("Marca"))
    url = txt(props.get("URL"))
    fetch = txt(props.get("Fetch"))
    vm_scope = txt(props.get("VM_Scope"))
    role_class = txt(props.get("Role_Class"))
    source_type = txt(props.get("Source_Type ")) or "Vacante"
    status = txt(props.get("Status"))
    
    # Lógica simplificada de gate (evaluate_gate de layer_1_run.py)
    def gate(fetch, vm_scope, role_class, source_type, rol=None, marca=None):
        if fetch == "Accesible" and (vm_scope == "Alto" or role_class == "Pivote"):
            return "CREATE"
        return "BLOCKED"
    
    # Lógica de Next_Action del pipeline (Fase 4 de layer_1_run.py)
    if evaluate_rejection_status(status):
        return "Ninguna"
    elif evaluate_application_status(status):
        return get_application_next_action(status)
    else:
        decision = gate(fetch, vm_scope, role_class, source_type, rol=rol, marca=marca)
        
        if decision == "CREATE":
            return "Re-check"
        elif source_type == "Vacante" and fetch == "Bloqueado":
            return "Reparar URL"
        else:
            # Default para casos no cubiertos
            return "Ninguna"


def analyze_records(records):
    """
    Analiza todos los registros y categoriza según estado de Next_Action.
    
    Returns:
        dict: {
            'total': int,
            'already_migrated': int,  # Tiene valor select válido
            'orphans': list of dict    # Registros sin Next_Action
        }
    """
    total = len(records)
    already_migrated = 0
    orphans = []
    
    for record in records:
        props = record.get("properties", {})
        next_action_prop = props.get("Next_Action")
        current_action = txt(next_action_prop)
        
        # Extraer campos clave para el reporte
        rol = txt(props.get("Rol"))
        marca = txt(props.get("Marca"))
        url = txt(props.get("URL"))
        status = txt(props.get("Status"))
        record_id = record.get("id", "")[:8]
        
        if current_action and current_action in VALID_NEXT_ACTIONS:
            # Ya migrado correctamente
            already_migrated += 1
        else:
            # Huérfano: vacío o valor inválido
            calculated_action = calculate_correct_next_action(props)
            
            orphans.append({
                'id': record_id,
                'full_id': record.get("id"),
                'marca': marca,
                'rol': rol,
                'url': url,
                'status': status,
                'current_value': current_action or "(vacío)",
                'calculated_value': calculated_action
            })
    
    return {
        'total': total,
        'already_migrated': already_migrated,
        'orphans': orphans
    }


def write_next_action_select(record_id, next_action_value):
    """
    Escribe Next_Action en formato select via API Notion.
    
    Args:
        record_id: ID completo del registro Notion
        next_action_value: valor de Next_Action (uno de los 8 válidos)
        
    Returns:
        bool: True si éxito, False si error
    """
    token = os.environ["NOTION_TOKEN"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": VANTAGE_NOTION_VERSION,
        "Content-Type": "application/json",
    }
    url = f"{VANTAGE_NOTION_API_BASE}/pages/{record_id}"
    
    payload = {
        "properties": {
            "Next_Action": {"select": {"name": next_action_value}}
        }
    }
    
    try:
        response = httpx.patch(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"  ERROR escribiendo {record_id[:8]}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Backfill Next_Action rich_text → select (v9.14.2)"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Escribe cambios en Notion (default: dry-run)"
    )
    args = parser.parse_args()
    
    execute_mode = args.execute
    
    if not execute_mode:
        print("\n" + "="*70)
        print("DRY-RUN MODE — No se escribirán cambios en Notion")
        print("Usa --execute para aplicar los cambios")
        print("="*70 + "\n")
    else:
        print("\n" + "="*70)
        print("EXECUTE MODE — Se escribirán cambios en Notion")
        print("="*70 + "\n")
    
    # Paso 1: Obtener todos los registros
    print("Paso 1: Obteniendo todos los registros del Tracker...")
    records = query_all_tracker_records()
    
    # Paso 2: Analizar estado de migración
    print("\nPaso 2: Analizando estado de Next_Action...")
    analysis = analyze_records(records)
    
    print(f"\n  Total registros: {analysis['total']}")
    print(f"  Ya migrados OK: {analysis['already_migrated']}")
    print(f"  Huérfanos (requieren backfill): {len(analysis['orphans'])}")
    
    # Paso 3: Reportar huérfanos
    if analysis['orphans']:
        print(f"\nPaso 3: Reporte de registros huérfanos ({len(analysis['orphans'])})...")
        print("\n" + "-"*70)
        print(f"{'ID':<10} {'Marca':<20} {'Rol':<30} {'Status':<15} {'Valor Actual':<20} {'Valor Propuesto':<20}")
        print("-"*70)
        
        for orphan in analysis['orphans']:
            print(f"{orphan['id']:<10} {orphan['marca'][:20]:<20} {orphan['rol'][:30]:<30} {orphan['status']:<15} {orphan['current_value'][:20]:<20} {orphan['calculated_value']:<20}")
        
        print("-"*70)
        
        # Paso 4: Ejecutar backfill si modo --execute
        if execute_mode:
            print(f"\nPaso 4: Escribiendo {len(analysis['orphans'])} correcciones...")
            success_count = 0
            error_count = 0
            
            for orphan in analysis['orphans']:
                if write_next_action_select(orphan['full_id'], orphan['calculated_value']):
                    success_count += 1
                    print(f"  ✓ {orphan['id']}: {orphan['current_value']} → {orphan['calculated_value']}")
                else:
                    error_count += 1
            
            print(f"\nBackfill completado:")
            print(f"  Éxitos: {success_count}")
            print(f"  Errores: {error_count}")
        else:
            print(f"\nDRY-RUN: {len(analysis['orphans'])} correcciones propuestas (no ejecutadas)")
            print("Ejecuta con --execute para aplicar los cambios")
    else:
        print("\n✅ Todos los registros ya tienen Next_Action válido - no se requiere backfill")
    
    print("\n" + "="*70)
    print("Proceso completado")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()