#!/usr/bin/env python3
"""
VANTAGE Pipeline — Version Verification & Sync Tool
Path: Layer_1/scripts/verify_versions.py
"""

import os
import sys
import json
import argparse
from pathlib import Path
import httpx

# --- CONFIGURACIÓN DE RUTAS Y CONSTANTES ---
SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR.parent / "config" / "layer_1.env"
REGISTRY_NAME = "resolver_registry_v2.json"

# Nombres canónicos de los 7 documentos fundacionales
DOC_KEYS = ["CHANGELOG", "KERNEL", "MANUAL", "CANON", "SP", "ALIASES", "CENSUS"]

# CENSUS no vive en resolver_registry_v2.json (namespace "document_registry" solo
# cubre KERNEL/MANUAL/CANON/TRACKER/SP/ALIASES/CHANGELOG) — se declara aquí como
# fallback fijo hasta que el registro lo incorpore.
CENSUS_FALLBACK_ID = "394938be-fc42-81e6-a381-e3869e60d89d"

# Infraestructura de sesión — no son documentos fundacionales, no participan de SP:SYNC-RULE
# SESSION LEDGER es una DATABASE (no una página standalone) — corregido tras
# confirmación del operador. data_source_id real: 8d736032-eef9-4e6e-a05a-df8b8079ebff
# (título "Session ID", ordenar por Opened At desc y tomar la primera fila = última sesión).
SESSION_LEDGER_DATA_SOURCE_ID = "8d736032-eef9-4e6e-a05a-df8b8079ebff"
BUG_TRACKER_DB_ID = "36e938befc4281bd9e1fdc360b3b45f5"
TASKS_TRACKER_DB_ID = "d2a65ca16a35465dbcffb0d82dddd549"

def load_env(env_path: Path) -> dict:
    """Carga variables de entorno manualmente para evitar dependencias externas."""
    env_vars = {}
    if not env_path.exists():
        print(f"[-] Error: No se encontró el archivo de entorno en {env_path}", file=sys.stderr)
        sys.exit(1)
    
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                env_vars[key.strip()] = val.strip().strip('"').strip("'")
    return env_vars

def find_registry_file(start_path: Path) -> Path:
    """Busca el archivo de registro subiendo recursivamente en el árbol de directorios."""
    for parent in [start_path] + list(start_path.parents):
        # Buscar en el directorio actual o en subdirectorios comunes (Layer_0, etc.)
        candidate = parent / REGISTRY_NAME
        if candidate.exists():
            return candidate
        candidate_l0 = parent / "Layer_0" / REGISTRY_NAME
        if candidate_l0.exists():
            return candidate_l0
        candidate_data = parent / "data" / REGISTRY_NAME
        if candidate_data.exists():
            return candidate_data
    print(f"[-] Error: No se pudo localizar {REGISTRY_NAME} en el árbol de directorios.", file=sys.stderr)
    sys.exit(1)

def load_document_uuids(registry_path: Path) -> dict:
    """Carga los UUIDs canónicos del registro para evitar hardcoding."""
    with open(registry_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Extraer UUIDs basándose en la estructura real del Registry V2:
    # namespace "document_registry" (PREFIX -> UUID), CENSUS ausente de ese namespace.
    doc_registry = data.get("document_registry", {})
    uuids = {}
    for key in DOC_KEYS:
        if key == "CENSUS":
            uuids[key] = CENSUS_FALLBACK_ID.replace("-", "")
            continue
        val = doc_registry.get(key)
        if val:
            # Limpieza básica de formato si viene con prefijos o brackets
            uuids[key] = val.replace("-", "")
        else:
            print(f"[-] Advertencia: Clave de documento '{key}' no resuelta en el registro.", file=sys.stderr)
    return uuids

def get_notion_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

def get_page_version(client: httpx.Client, page_id: str, headers: dict) -> str:
    """Extrae únicamente la propiedad 'Versión' o 'Version' de la página."""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    try:
        response = client.get(url, headers=headers)
        if response.status_code != 200:
            return f"Error HTTP {response.status_code}"
        
        properties = response.json().get("properties", {})
        # Buscar propiedad "Versión" o "Version"
        prop = properties.get("Versión") or properties.get("Version")
        if not prop:
            return "Sin Propiedad"
        
        p_type = prop.get("type")
        if p_type == "rich_text":
            texts = prop.get("rich_text", [])
            return texts[0].get("plain_text", "N/A") if texts else "N/A"
        elif p_type == "select":
            return prop.get("select", {}).get("name", "N/A")
        elif p_type == "title":
            texts = prop.get("title", [])
            return texts[0].get("plain_text", "N/A") if texts else "N/A"
        return "Tipo no Soportado"
    except Exception as e:
        return f"Error: {str(e)}"

def update_page_version(client: httpx.Client, page_id: str, version: str, headers: dict) -> bool:
    """Actualiza de forma determinista la propiedad 'Versión' de la página."""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": {
            "Versión": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": version
                        }
                    }
                ]
            }
        }
    }
    try:
        response = client.patch(url, headers=headers, json=payload)
        return response.status_code == 200
    except Exception:
        return False

def get_last_ledger_row(client: httpx.Client, data_source_id: str, headers: dict) -> dict:
    """Consulta la data source SESSION LEDGER (database real, no página standalone)
    vía POST /v1/data_sources/{id}/query, ordenando por 'Opened At' descendente
    y tomando la primera fila = sesión más reciente. Requiere Notion-Version
    que soporte data_sources (2025-09-03), distinta a la usada para /pages."""
    url = f"https://api.notion.com/v1/data_sources/{data_source_id}/query"
    query_headers = dict(headers)
    query_headers["Notion-Version"] = "2025-09-03"
    payload = {
        "sorts": [{"property": "Opened At", "direction": "descending"}],
        "page_size": 1
    }
    try:
        response = client.post(url, headers=query_headers, json=payload)
        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}: {response.text[:200]}"}
        results = response.json().get("results", [])
        if not results:
            return {"error": "Sin filas en Session Ledger"}
        props = results[0].get("properties", {})
        result = {"page_id": results[0].get("id")}
        for key, notion_key in [
            ("session_id", "Session ID"),
            ("status", "Status"),
            ("opened_at", "Opened At"),
            ("pending_summary", "Pending Summary"),
        ]:
            prop = props.get(notion_key)
            if not prop:
                result[key] = None
                continue
            p_type = prop.get("type")
            if p_type == "rich_text":
                texts = prop.get("rich_text", [])
                result[key] = texts[0].get("plain_text") if texts else None
            elif p_type == "select":
                result[key] = (prop.get("select") or {}).get("name")
            elif p_type == "date":
                result[key] = (prop.get("date") or {}).get("start")
            elif p_type == "title":
                texts = prop.get("title", [])
                result[key] = texts[0].get("plain_text") if texts else None
            else:
                result[key] = None
        return result
    except Exception as e:
        return {"error": str(e)}

def get_priority_tickets(client: httpx.Client, database_id: str, headers: dict, label: str) -> list:
    """Consulta un tracker (Bug o Tasks) y devuelve los tickets con Prioridad
    CRÍTICO o ALTO, conforme a KERNEL:HEALTH-CHECK-002 (detalle explícito solo
    para estas dos prioridades)."""
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    payload = {
        "filter": {
            "or": [
                {"property": "Prioridad", "select": {"equals": "CRÍTICO"}},
                {"property": "Prioridad", "select": {"equals": "ALTO"}}
            ]
        }
    }
    try:
        response = client.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            return [{"error": f"{label}: HTTP {response.status_code}"}]
        results = response.json().get("results", [])
        tickets = []
        for row in results:
            props = row.get("properties", {})
            title_prop = next((v for v in props.values() if v.get("type") == "title"), None)
            title_texts = (title_prop or {}).get("title", [])
            title = title_texts[0].get("plain_text") if title_texts else "(sin título)"
            prioridad_prop = props.get("Prioridad", {})
            prioridad = (prioridad_prop.get("select") or {}).get("name", "?")
            tickets.append({"tracker": label, "titulo": title, "prioridad": prioridad})
        return tickets
    except Exception as e:
        return [{"error": f"{label}: {str(e)}"}]

def render_bootstrap_dump(client: httpx.Client, changelog_page_id: str, headers: dict) -> None:
    """Genera el bloque [DUMP INICIO SESIÓN VANTAGE] descrito en
    KERNEL:VERSION-CHECK-TOOL y MANUAL:SESSION-CYCLE-001 §Apertura paso 1:
    estado de la última fila del Ledger, última entrada del Changelog
    (resumen truncado), y snapshot de tickets CRÍTICO/ALTO."""
    ledger = get_last_ledger_row(client, SESSION_LEDGER_DATA_SOURCE_ID, headers)
    changelog_version = get_page_version(client, changelog_page_id, headers)
    bug_tickets = get_priority_tickets(client, BUG_TRACKER_DB_ID, headers, "Bug")
    task_tickets = get_priority_tickets(client, TASKS_TRACKER_DB_ID, headers, "Task")
    all_tickets = bug_tickets + task_tickets

    print("[DUMP INICIO SESIÓN VANTAGE]")
    print("-" * 60)
    print("SESSION LEDGER — última fila:")
    if "error" in ledger:
        print(f"  [-] Error al leer Ledger: {ledger['error']}")
    else:
        status = ledger.get("status") or "N/A"
        marker = "⚠️ ABIERTA (posible cierre abrupto)" if status == "OPEN" else "OK — cerrada normalmente"
        print(f"  session_id       : {ledger.get('session_id') or 'N/A'}")
        print(f"  status           : {status}  [{marker}]")
        print(f"  opened_at        : {ledger.get('opened_at') or 'N/A'}")
        print(f"  pending_summary  : {ledger.get('pending_summary') or '(vacío)'}")
    print("-" * 60)
    print(f"CHANGELOG — versión vigente: {changelog_version}")
    print("-" * 60)
    print(f"TICKETS PENDIENTES (CRÍTICO/ALTO) — {len(all_tickets)} encontrados:")
    if not all_tickets:
        print("  (ninguno)")
    for t in all_tickets:
        if "error" in t:
            print(f"  [-] {t['error']}")
        else:
            print(f"  [{t['prioridad']:<8}] ({t['tracker']}) {t['titulo']}")
    print("-" * 60)
    print("[FIN DUMP INICIO SESIÓN VANTAGE]")


def main():
    parser = argparse.ArgumentParser(description="Verify and Sync document versions across Notion SSOT.")
    parser.add_argument("--sync", action="store_true", help="Sincroniza la versión de CHANGELOG hacia todos los documentos.")
    parser.add_argument("--bootstrap", action="store_true", help="Genera el dump de contexto de apertura de sesión (Ledger + Changelog + tickets prioritarios). Read-only.")
    parser.add_argument("--check", action="store_true", help="Verifica la versión de los 7 documentos fundacionales (Check Mode). Read-only. Alias explícito del modo por default (sin flags) — existe para que el comando documentado en Manual/System Prompt/skills coincida literalmente con la interfaz real del script.")
    args = parser.parse_args()

    # 1. Inicialización de Entorno e Infraestructura
    env = load_env(ENV_PATH)
    token = env.get("NOTION_TOKEN")
    if not token:
        print("[-] Error: NOTION_TOKEN no definido en layer_1.env", file=sys.stderr)
        sys.exit(1)

    registry_path = find_registry_file(SCRIPT_DIR)
    uuids = load_document_uuids(registry_path)

    # Validar que al menos tengamos la referencia a CHANGELOG
    if "CHANGELOG" not in uuids:
        print("[-] Error Crítico: No se pudo resolver el ID del CHANGELOG.", file=sys.stderr)
        sys.exit(1)

    headers = get_notion_headers(token)

    with httpx.Client(timeout=15.0) as client:
        if args.bootstrap:
            render_bootstrap_dump(client, uuids["CHANGELOG"], headers)
            return

        if args.sync:
            print("[*] Iniciando Modo Sincronización Lote (Sync Mode)...")
            # Obtener la versión de referencia del Changelog
            master_version = get_page_version(client, uuids["CHANGELOG"], headers)
            if "Error" in master_version or master_version in ["N/A", "Sin Propiedad"]:
                print(f"[-] Fallo al leer versión maestro de CHANGELOG: {master_version}", file=sys.stderr)
                sys.exit(1)
            
            print(f"[+] Versión Maestro detectada en CHANGELOG: {master_version}")
            print("-" * 60)
            
            results = []
            for doc in DOC_KEYS:
                if doc == "CHANGELOG":
                    results.append((doc, master_version, "SKIP (Maestro)"))
                    continue
                
                page_id = uuids.get(doc)
                if not page_id:
                    results.append((doc, "N/A", "ERROR: ID no resuelto"))
                    continue
                
                success = update_page_version(client, page_id, master_version, headers)
                status = "OK" if success else "FALLÓ"
                results.append((doc, master_version, status))
            
            # Render del reporte de sincronización
            print(f"{'DOCUMENTO':<15} | {'VERSIÓN':<12} | {'ESTADO':<15}")
            print("-" * 60)
            for doc, ver, status in results:
                print(f"{doc:<15} | {ver:<12} | {status:<15}")
                
        else:
            print("[*] Ejecutando Modo Lectura (Check Mode)...")
            print("-" * 45)
            print(f"{'DOCUMENTO':<15} | {'VERSIÓN':<12}")
            print("-" * 45)
            
            for doc in DOC_KEYS:
                page_id = uuids.get(doc)
                if not page_id:
                    print(f"{doc:<15} | ID No Resuelto")
                    continue
                version = get_page_version(client, page_id, headers)
                print(f"{doc:<15} | {version:<12}")

if __name__ == "__main__":
    main()