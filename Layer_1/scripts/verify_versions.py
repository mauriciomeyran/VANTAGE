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

# Nombres canónicos de los 9 puntos de supervisión (8 fundacionales + VANTAGE hub).
# VANTAGE (página principal) se integró en modo idéntico a los demás — NO es
# supervisión pasiva: participa en --sync y en el check de lectura con el
# mismo veredicto PASS/FAIL que el resto.
DOC_KEYS = ["CHANGELOG", "KERNEL", "MANUAL", "CANON", "SP", "ALIASES", "CENSUS", "BRIEF", "VANTAGE"]

# CENSUS no vive en resolver_registry_v2.json: no tiene prefijo propio en
# KERNEL:DOC-CONTRACT (sus IDs internos usan KERNEL:/SP:/MANUAL:/CANON:/BRIEF:),
# por lo que se declara aquí como fallback fijo.
# BRIEF y VANTAGE SÍ viven ya en document_registry (incorporados vía
# CENSUS-SYNC-R1, conteo de fundamentales 7→9) — los fallbacks de abajo solo
# se usan como red de seguridad si el registro llegara a perder la clave.
CENSUS_FALLBACK_ID = "394938be-fc42-81e6-a381-e3869e60d89d"
BRIEF_FALLBACK_ID = "3a3938be-fc42-8008-9e90-ec435c01f50d"
VANTAGE_FALLBACK_ID = "36e938be-fc42-81d6-bf40-dfe7dee782a5"

# Infraestructura de sesión — no son documentos fundacionales, no participan de SP:SYNC-RULE
# SESSION LEDGER es una DATABASE (no una página standalone) — corregido tras
# confirmación del operador. data_source_id real: 8d736032-eef9-4e6e-a05a-df8b8079ebff
# (título "Session ID", ordenar por Opened At desc y tomar la primera fila = última sesión).
SESSION_LEDGER_DATA_SOURCE_ID = "8d736032-eef9-4e6e-a05a-df8b8079ebff"
BUG_TRACKER_DB_ID = "36e938befc4281bd9e1fdc360b3b45f5"
TASKS_TRACKER_DB_ID = "d2a65ca16a35465dbcffb0d82dddd549"

# SCRIPT LIBRARY — inventario de scripts en Notion (propiedad título: "Script").
# Mismo patrón que SESSION_LEDGER_DATA_SOURCE_ID: query directo vía httpx a
# /v1/data_sources/{id}/query con Notion-Version 2025-09-03. No pasa por MCP,
# por lo que NO aplica la restricción de plan Business/Notion AI que bloquea
# query_data_sources/query_database_view a nivel de conector MCP.
SCRIPT_LIBRARY_DATA_SOURCE_ID = "ea914544-338f-485e-ac1b-7f137a5c9cee"

# Proyecto root real: Layer_1/scripts -> Layer_1 -> VANTAGE/
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Directorios excluidos del escaneo de "scripts committeados" — código retirado,
# de prueba, o de respaldo no cuenta como script en uso activo.
EXCLUDED_DIR_NAMES = {
    "archive", "archived", "tests", "test", "backup",
    "one_offs", "deprecated_scripts", ".venv", "node_modules", ".git",
}
EXCLUDED_DIR_SUBSTRINGS = ("backup_", "discarded_")

# Archivos con este prefijo se excluyen aunque vivan fuera de un directorio
# excluido (ej. DEPRECATED_vacante_purge_trash_only.py).
EXCLUDED_FILE_PREFIXES = ("DEPRECATED_",)

# Solo estas carpetas de primer nivel se consideran "árbol activo" del sistema.
# Fuera de esta lista (ej. "- Documentación/") no son scripts operativos.
ACTIVE_TOP_LEVEL_DIRS = {"Layer_1", "Layer_3", "Layer_4", "Dashboard", "Raycast"}

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
        if key == "BRIEF":
            val = doc_registry.get(key)
            uuids[key] = val.replace("-", "") if val else BRIEF_FALLBACK_ID.replace("-", "")
            continue
        if key == "VANTAGE":
            val = doc_registry.get(key)
            uuids[key] = val.replace("-", "") if val else VANTAGE_FALLBACK_ID.replace("-", "")
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
        # Buscar propiedad "Versión", "Version", o "Versión " (con espacio final —
        # variante real detectada en VANTAGE página principal, schema inconsistente
        # respecto a los 8 fundacionales).
        prop = properties.get("Versión") or properties.get("Version") or properties.get("Versión ")
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

def update_page_version(client: httpx.Client, page_id: str, version: str, headers: dict, prop_name: str = "Versión") -> bool:
    """Actualiza de forma determinista la propiedad de versión de la página.
    prop_name permite variantes de schema (ej. 'Versión ' con espacio final en VANTAGE)."""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": {
            prop_name: {
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
    CRÍTICO o ALTO que además NO estén en un estado terminal, conforme a
    KERNEL:HEALTH-CHECK-002 (detalle explícito solo para estas dos prioridades,
    excluyendo tickets ya cerrados)."""
    url = f"https://api.notion.com/v1/databases/{database_id}/query"

    # Status terminales por tracker (SP:SCHEMA — Bug Tracker vs Tasks Tracker
    # no comparten las mismas opciones de select). Labels reales confirmados
    # en main(): "Bug" y "Task" (singular).
    closed_statuses_by_label = {
        "Bug": ["Resuelto"],
        "Task": ["Hecho", "Completado"],
    }
    closed_statuses = closed_statuses_by_label.get(label, [])

    status_filters = [
        {"property": "Status", "select": {"does_not_equal": s}}
        for s in closed_statuses
    ]

    payload = {
        "filter": {
            "and": [
                {
                    "or": [
                        {"property": "Prioridad", "select": {"equals": "CRÍTICO"}},
                        {"property": "Prioridad", "select": {"equals": "ALTO"}}
                    ]
                },
                *status_filters
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

def scan_committed_scripts(project_root: Path) -> list:
    """Escanea el árbol activo del proyecto (Layer_1/3/4, Dashboard, Raycast) en
    busca de .py/.sh, excluyendo archive/tests/backup/one_offs/deprecated y
    archivos con prefijo DEPRECATED_. Devuelve lista de (nombre, ruta_relativa)
    ordenada por nombre. No depende de git — escanea el filesystem local tal
    como está, que es lo que realmente se ejecuta."""
    found = []
    for top in sorted(ACTIVE_TOP_LEVEL_DIRS):
        top_path = project_root / top
        if not top_path.exists():
            continue
        for path in top_path.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in (".py", ".sh"):
                continue
            if path.name.startswith(EXCLUDED_FILE_PREFIXES):
                continue
            rel = path.relative_to(project_root)
            parts_lower = {p.lower() for p in rel.parts}
            if parts_lower & EXCLUDED_DIR_NAMES:
                continue
            if any(sub in p.lower() for p in rel.parts for sub in EXCLUDED_DIR_SUBSTRINGS):
                continue
            found.append((path.name, str(rel)))
    found.sort(key=lambda t: t[0])
    return found

def get_script_library_titles(client: httpx.Client, data_source_id: str, headers: dict) -> dict:
    """Pagina completo el data source SCRIPT LIBRARY y devuelve
    {titulo_script: estado} para cada fila. Un solo query_data_sources no
    trae más de 100 filas — este loop sigue next_cursor hasta agotarlo."""
    url = f"https://api.notion.com/v1/data_sources/{data_source_id}/query"
    query_headers = dict(headers)
    query_headers["Notion-Version"] = "2025-09-03"
    titles = {}
    cursor = None
    while True:
        payload = {"page_size": 100}
        if cursor:
            payload["start_cursor"] = cursor
        response = client.post(url, headers=query_headers, json=payload)
        if response.status_code != 200:
            print(f"[-] Error consultando SCRIPT LIBRARY: HTTP {response.status_code}: {response.text[:200]}", file=sys.stderr)
            sys.exit(1)
        data = response.json()
        for row in data.get("results", []):
            props = row.get("properties", {})
            title_prop = props.get("Script", {})
            texts = title_prop.get("title", [])
            # BUGFIX: Notion parte el título en múltiples rich-text runs cuando
            # detecta un link automático dentro del nombre (ej. "patch_cheat_sheet.py"
            # -> runs ["patch_cheat_", "sheet.py"] porque autolinkea "sheet.py").
            # Leer solo texts[0] truncaba el nombre en el primer run. Concatenar
            # todos los runs reconstruye el filename completo.
            name = "".join(t.get("plain_text", "") for t in texts) if texts else None
            estado_prop = props.get("Estado", {})
            estado = (estado_prop.get("select") or {}).get("name") if estado_prop else None
            if name:
                titles[name] = estado
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return titles

def render_scripts_gap_report(client: httpx.Client, headers: dict) -> None:
    """Cruza scripts committeados en disco (árbol activo) contra SCRIPT LIBRARY
    en Notion. Read-only en ambos lados — no escribe ni crea filas
    automáticamente, solo reporta para que el operador decida el alta."""
    disk_scripts = scan_committed_scripts(PROJECT_ROOT)
    library_titles = get_script_library_titles(client, SCRIPT_LIBRARY_DATA_SOURCE_ID, headers)

    disk_names = {name for name, _ in disk_scripts}
    missing = sorted(name for name in disk_names if name not in library_titles)
    registered = sorted(name for name in disk_names if name in library_titles)
    # Filas en Notion marcadas Activo cuyo nombre no aparece en el árbol activo de disco.
    orphan_notion = sorted(
        title for title, estado in library_titles.items()
        if estado == "Activo" and title not in disk_names
    )

    print("[SCRIPT LIBRARY — GAP REPORT]")
    print("-" * 60)
    print(f"Scripts en árbol activo (disco): {len(disk_names)}")
    print(f"Filas en SCRIPT LIBRARY (Notion): {len(library_titles)}")
    print("-" * 60)
    print(f"SIN REGISTRAR EN NOTION — {len(missing)} encontrados:")
    if not missing:
        print("  (ninguno)")
    for name in missing:
        rel = next(r for n, r in disk_scripts if n == name)
        print(f"  [-] {name}  ({rel})")
    print("-" * 60)
    print(f"REGISTRADOS Y VIGENTES — {len(registered)} coinciden")
    print("-" * 60)
    print(f"EN NOTION COMO 'Activo' PERO NO EN DISCO (árbol activo) — {len(orphan_notion)} encontrados:")
    print("  (revisar manualmente — puede ser mismatch de nombre, no ausencia real,")
    print("   ej. título con sufijo aclaratorio distinto al filename real)")
    if not orphan_notion:
        print("  (ninguno)")
    for name in orphan_notion:
        print(f"  [?] {name}")
    print("-" * 60)
    print("[FIN SCRIPT LIBRARY — GAP REPORT]")

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
    parser.add_argument("--sync", action="store_true", help="Sincroniza la versión de CHANGELOG hacia todos los documentos y verifica por relectura (veredicto PASS/FAIL real). Reemplaza al antiguo par --sync + --check.")
    parser.add_argument("--bootstrap", action="store_true", help="Genera el dump de contexto de apertura de sesión (Ledger + Changelog + tickets prioritarios). Read-only.")
    parser.add_argument("--scripts", action="store_true", help="Cruza los scripts .py/.sh del árbol activo (Layer_1/3/4, Dashboard, Raycast) contra la base SCRIPT LIBRARY en Notion. Read-only, no requiere resolver_registry_v2.json.")
    args = parser.parse_args()

    # 1. Inicialización de Entorno e Infraestructura
    env = load_env(ENV_PATH)
    token = env.get("NOTION_TOKEN")
    if not token:
        print("[-] Error: NOTION_TOKEN no definido en layer_1.env", file=sys.stderr)
        sys.exit(1)

    # --scripts no depende del registro de documentos fundacionales (resolver_registry_v2.json)
    # — se resuelve y sale temprano para no exigir ese archivo si el operador solo quiere
    # el gap report de scripts.
    if args.scripts:
        headers = get_notion_headers(token)
        with httpx.Client(timeout=20.0) as client:
            render_scripts_gap_report(client, headers)
        return

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
                    results.append((doc, master_version, master_version, "PASS (Maestro)"))
                    continue

                page_id = uuids.get(doc)
                if not page_id:
                    results.append((doc, "N/A", "N/A", "FAIL: ID no resuelto"))
                    continue

                prop_name = "Versión " if doc == "VANTAGE" else "Versión"
                write_ok = update_page_version(client, page_id, master_version, headers, prop_name=prop_name)
                if not write_ok:
                    results.append((doc, master_version, "N/A", "FAIL: escritura rechazada"))
                    continue

                # Relectura post-escritura: el status code del PATCH no es evidencia
                # suficiente de que el valor quedó persistido. Esta es la verificación
                # real que antes vivía (sin lógica de veredicto) en --check.
                confirmed_version = get_page_version(client, page_id, headers)
                if confirmed_version == master_version:
                    results.append((doc, master_version, confirmed_version, "PASS"))
                else:
                    results.append((doc, master_version, confirmed_version, f"FAIL: releído '{confirmed_version}'"))

            # Render del reporte de sincronización con verificación
            print(f"{'DOCUMENTO':<15} | {'ESPERADO':<12} | {'RELEÍDO':<12} | {'VEREDICTO':<25}")
            print("-" * 75)
            all_pass = True
            for doc, expected, confirmed, status in results:
                if not status.startswith("PASS"):
                    all_pass = False
                print(f"{doc:<15} | {expected:<12} | {confirmed:<12} | {status:<25}")
            print("-" * 75)
            print(f"[VEREDICTO FINAL] {'PASS' if all_pass else 'FAIL'}")
            if not all_pass:
                sys.exit(1)
                
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