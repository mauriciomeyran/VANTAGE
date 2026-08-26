#!/usr/bin/env python3
"""
VANTAGE Pipeline — Version Verification & Sync Tool
Path: Layer_1/scripts/verify_versions.py
"""

import os
import sys
import json
import hashlib
import argparse
from pathlib import Path
from datetime import datetime, timezone
import httpx

# --- CONFIGURACIÓN DE RUTAS Y CONSTANTES ---
SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR.parent / "config" / "layer_1.env"
REGISTRY_NAME = "resolver_registry_v2.json"

# Nombres canónicos de los 11 puntos de supervisión (9 fundacionales + VANTAGE hub + ARCHIVEROS).
# VANTAGE (página principal) se integró en modo idéntico a los demás — NO es
# supervisión pasiva: participa en --sync y en el check de lectura con el
# mismo veredicto PASS/FAIL que el resto.
# ARCHIVEROS (página de archiveros) también participa en --sync del mismo modo.
DOC_KEYS = ["CHANGELOG", "KERNEL", "MANUAL", "CANON", "SP", "ALIASES", "CENSUS", "BRIEF", "VANTAGE", "CHANGELOG_ARCHIVO", "ARCHIVEROS"]

# CENSUS no vive en resolver_registry_v2.json: no tiene prefijo propio en
# KERNEL:DOC-CONTRACT (sus IDs internos usan KERNEL:/SP:/MANUAL:/CANON:/BRIEF:),
# por lo que se declara aquí como fallback fijo.
# BRIEF, VANTAGE, CHANGELOG_ARCHIVO y ARCHIVEROS SÍ viven ya en document_registry
# (incorporados vía CENSUS-SYNC-R1 y actualización integración ARCHIVO) —
# los fallbacks de abajo solo se usan como red de seguridad si el registro
# llegara a perder la clave.
CENSUS_FALLBACK_ID = "394938be-fc42-81e6-a381-e3869e60d89d"
BRIEF_FALLBACK_ID = "3a3938be-fc42-8008-9e90-ec435c01f50d"
VANTAGE_FALLBACK_ID = "36e938be-fc42-81d6-bf40-dfe7dee782a5"
CHANGELOG_ARCHIVO_FALLBACK_ID = "3ba938be-fc42-8011-8947-fb4fa5d1f63f"
ARCHIVEROS_FALLBACK_ID = "3bb938befc4280cd8ea3fc8ba78f570c"

# Infraestructura de sesión — no son documentos fundacionales, no participan de SP:SYNC-RULE
# SESSION LEDGER es una DATABASE (no una página standalone) — corregido tras
# confirmación del operador. data_source_id real: 8d736032-eef9-4e6e-a05a-df8b8079ebff
# (título "Session ID", ordenar por Opened At desc y tomar la primera fila = última sesión).
SESSION_LEDGER_DATA_SOURCE_ID = "8d736032-eef9-4e6e-a05a-df8b8079ebff"

# BUG/TASKS TRACKER — data_source_id (COL), NO database_id (DB).
# Corregido: la versión previa usaba el DB ID contra el endpoint legacy
# /v1/databases/{id}/query con Notion-Version 2022-06-28, inconsistente con
# el resto del script (que ya usa /v1/data_sources/{id}/query + 2025-09-03
# para Session Ledger y Script Library). Esa inconsistencia de endpoint/ID
# era la causa real de los HTTP 400 fantasma — no un mensaje oculto.
# IDs confirmados en SP:DIGITAL-ID-CARD:
#   BUG TRACKER (COL)   = 36e938be-fc42-81f8-8c6f-000b6769ba03
#   TASKS TRACKER (COL) = aaaaef55-a1ce-45f7-9c8b-1c1def2c18e8
BUG_TRACKER_DATA_SOURCE_ID = "36e938befc4281f88c6f000b6769ba03"
TASKS_TRACKER_DATA_SOURCE_ID = "aaaaef55a1ce45f79c8b1c1def2c18e8"

# SCRIPT LIBRARY — inventario de scripts en Notion (propiedad título: "Script").
# Mismo patrón que SESSION_LEDGER_DATA_SOURCE_ID: query directo vía httpx a
# /v1/data_sources/{id}/query con Notion-Version 2025-09-03. No pasa por MCP,
# por lo que NO aplica la restricción de plan Business/Notion AI que bloquea
# query_data_sources/query_database_view a nivel de conector MCP.
SCRIPT_LIBRARY_DATA_SOURCE_ID = "ea914544-338f-485e-ac1b-7f137a5c9cee"
SKILL_LIBRARY_DATA_SOURCE_ID = "2f1938be-fc42-83c8-8972-07300201136d"

# Proyecto root real: Layer_1/scripts -> Layer_1 -> VANTAGE/
PROJECT_ROOT = SCRIPT_DIR.parent.parent

SCRIPT_GLOSSARY_PATH = PROJECT_ROOT / "Documentación" / "ACTIVE" / "Manual.md"

# Directorios excluidos del escaneo de "scripts committeados" — código retirado,
# de prueba, o de respaldo no cuenta como script en uso activo.
EXCLUDED_DIR_NAMES = {
    "archive", "archived", "tests", "test", "backup",
    "one_offs", "deprecated_scripts", ".venv", "venv", "node_modules", ".git",
}
EXCLUDED_DIR_SUBSTRINGS = ("backup_", "discarded_")

# Archivos con este prefijo se excluyen aunque vivan fuera de un directorio
# excluido (ej. DEPRECATED_vacante_purge_trash_only.py).
EXCLUDED_FILE_PREFIXES = ("DEPRECATED_",)

# Solo estas carpetas de primer nivel se consideran "árbol activo" del sistema.
# Fuera de esta lista (ej. "- Documentación/") no son scripts operativos.
ACTIVE_TOP_LEVEL_DIRS = {"Layer_1", "Layer_3", "Layer_4", "Dashboard", "Raycast", "skills"}

# Umbrales de alerta para detección de truncamiento de contenido en --length
LENGTH_TRUNCATION_THRESHOLD_PCT = 5.0
LENGTH_TRUNCATION_THRESHOLD_ABS = 10

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
        if key == "CHANGELOG_ARCHIVO":
            val = doc_registry.get(key)
            uuids[key] = val.replace("-", "") if val else CHANGELOG_ARCHIVO_FALLBACK_ID.replace("-", "")
            continue
        if key == "ARCHIVEROS":
            val = doc_registry.get(key)
            uuids[key] = val.replace("-", "") if val else ARCHIVEROS_FALLBACK_ID.replace("-", "")
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

def query_data_source(client: httpx.Client, data_source_id: str, headers: dict, payload: dict) -> tuple:
    """Único punto de entrada para POST /v1/data_sources/{id}/query en todo el
    script. Fuerza siempre Notion-Version 2025-09-03 (requerido por data
    sources, distinto del 2022-06-28 usado para /v1/pages) y siempre devuelve
    el body de error real (response.text[:200]) en vez de tragárselo — así no
    puede reaparecer la ambigüedad de "HTTP 400" sin contexto.
    Devuelve (data, None) en éxito, o (None, {"error": "..."}) en fallo."""
    url = f"https://api.notion.com/v1/data_sources/{data_source_id}/query"
    query_headers = dict(headers)
    query_headers["Notion-Version"] = "2025-09-03"
    try:
        response = client.post(url, headers=query_headers, json=payload)
    except Exception as e:
        return None, {"error": str(e)}
    if response.status_code != 200:
        return None, {"error": f"HTTP {response.status_code}: {response.text[:200]}"}
    return response.json(), None

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
    payload = {
        "sorts": [{"property": "Opened At", "direction": "descending"}],
        "page_size": 1
    }
    try:
        data, err = query_data_source(client, data_source_id, headers, payload)
        if err:
            return err
        results = data.get("results", [])
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

def get_priority_tickets(client: httpx.Client, data_source_id: str, headers: dict, label: str) -> list:
    """Consulta un tracker (Bug o Tasks) y devuelve los tickets con Prioridad
    CRÍTICO o ALTO que además NO estén en un estado terminal, conforme a
    KERNEL:HEALTH-CHECK-002 (detalle explícito solo para estas dos prioridades,
    excluyendo tickets ya cerrados).
    data_source_id es el COL (data source), NO el DB — mismo contrato que
    get_last_ledger_row y get_script_library_titles vía query_data_source()."""

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
                        {"property": "Prioridad", "select": {"equals": "4 CRÍTICO"}},
                        {"property": "Prioridad", "select": {"equals": "3 ALTO"}}
                    ]
                },
                *status_filters
            ]
        }
    }
    try:
        data, err = query_data_source(client, data_source_id, headers, payload)
        if err:
            return [{"error": f"{label}: {err['error']}"}]
        results = data.get("results", [])
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

def scan_committed_assets(project_root: Path, extensions: tuple) -> list:
    """Escanea el árbol activo del proyecto (Layer_1/3/4, Dashboard, Raycast) en
    busca de archivos cuyo suffix esté en 'extensions', excluyendo
    archive/tests/backup/one_offs/deprecated y archivos con prefijo
    DEPRECATED_. Devuelve lista de (nombre, ruta_relativa) ordenada por
    nombre. No depende de git — escanea el filesystem local tal como está,
    que es lo que realmente se ejecuta."""
    found = []
    for top in sorted(ACTIVE_TOP_LEVEL_DIRS):
        top_path = project_root / top
        if not top_path.exists():
            continue
        for path in top_path.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in extensions:
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

def scan_skill_folders(project_root: Path) -> list:
    """Escanea el árbol activo buscando carpetas que contienen un SKILL.md
    (convención real de skills en disco: carpeta con SKILL.md adentro, no
    archivos sueltos con extensión .skill -- esa extensión solo existe como
    convención de nombre en el título de Notion, ej. 'vantage-cv-b.skill',
    nunca como archivo físico). Devuelve lista de (nombre_virtual, ruta
    relativa al SKILL.md) ordenada por nombre -- mismo shape de retorno que
    scan_committed_assets, para reuso directo en los consumidores existentes
    (--skills, --new-skills, --skills-drift)."""
    found = []
    for top in sorted(ACTIVE_TOP_LEVEL_DIRS):
        top_path = project_root / top
        if not top_path.exists():
            continue
        for path in top_path.rglob("SKILL.md"):
            if not path.is_file():
                continue
            folder_name = path.parent.name
            if folder_name.startswith(EXCLUDED_FILE_PREFIXES):
                continue
            rel = path.relative_to(project_root)
            parts_lower = {p.lower() for p in rel.parts}
            if parts_lower & EXCLUDED_DIR_NAMES:
                continue
            if any(sub in p.lower() for p in rel.parts for sub in EXCLUDED_DIR_SUBSTRINGS):
                continue
            virtual_name = f"{folder_name}.skill"
            found.append((virtual_name, str(rel)))
    found.sort(key=lambda t: t[0])
    return found

def get_script_library_titles(client: httpx.Client, data_source_id: str, headers: dict, title_property: str = "Script") -> dict:
    """Pagina completo el data source (SCRIPT LIBRARY o SKILL LIBRARY) y
    devuelve {titulo: estado} para cada fila. 'title_property' es el nombre
    de la propiedad title en ese data source (difiere entre bases: "Script"
    vs "Skill"). Un solo query_data_sources no trae más de 100 filas — este
    loop sigue next_cursor hasta agotarlo."""
    titles = {}
    cursor = None
    while True:
        payload = {"page_size": 100}
        if cursor:
            payload["start_cursor"] = cursor
        data, err = query_data_source(client, data_source_id, headers, payload)
        if err:
            print(f"[-] Error consultando SCRIPT LIBRARY: {err['error']}", file=sys.stderr)
            sys.exit(1)
        for row in data.get("results", []):
            props = row.get("properties", {})
            title_prop = props.get(title_property, {})
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

def get_page_line_count(client: httpx.Client, page_id: str, headers: dict, max_depth: int = 10) -> int | dict:
    """Cuenta recursivamente las líneas de texto extraíble en una página Notion.
    Usa GET /v1/blocks/{block_id}/children con paginación via next_cursor.
    Tipos de bloque que cuentan como 1 línea si tienen texto no vacío:
    paragraph, heading_1, heading_2, heading_3, bulleted_list_item,
    numbered_list_item, to_do, toggle, quote, callout, table_row, code.
    Bloques vacíos o solo whitespace NO cuentan.
    divider, table_of_contents, column_list/column (contenedor) NO cuentan.
    Devuelve int en éxito, o {"error": "..."} en fallo."""
    try:
        block_headers = dict(headers)
        block_headers["Notion-Version"] = "2022-06-28"
        url = f"https://api.notion.com/v1/blocks/{page_id}/children"
        count = 0
        cursor = None

        while True:
            params = {"page_size": 100}
            if cursor:
                params["start_cursor"] = cursor
            response = client.get(url, headers=block_headers, params=params)
            if response.status_code != 200:
                return {"error": f"HTTP {response.status_code}: {response.text[:200]}"}

            data = response.json()
            for block in data.get("results", []):
                block_type = block.get("type")
                if not block_type:
                    continue

                # Bloques que NO cuentan como línea (contenedores o estructurales)
                if block_type in ("divider", "table_of_contents", "column_list", "column"):
                    pass

                # Bloques que pueden contar si tienen texto
                elif block_type in (
                    "paragraph", "heading_1", "heading_2", "heading_3",
                    "bulleted_list_item", "numbered_list_item", "to_do",
                    "toggle", "quote", "callout", "code"
                ):
                    block_data = block.get(block_type, {})
                    rich_text = block_data.get("rich_text", [])
                    # Concatenar todo el texto y verificar si no está vacío
                    text = "".join(t.get("plain_text", "") for t in rich_text)
                    if text.strip():
                        count += 1

                # table_row cuenta como 1 línea por fila (no por celda)
                elif block_type == "table_row":
                    block_data = block.get("table_row", {})
                    cells = block_data.get("cells", [])
                    # Una fila cuenta si al menos una celda tiene texto no vacío
                    has_content = False
                    for cell in cells:
                        cell_text = "".join(t.get("plain_text", "") for t in cell)
                        if cell_text.strip():
                            has_content = True
                            break
                    if has_content:
                        count += 1

                # Recursión para bloques con hijos (toggle, column, etc.)
                if block.get("has_children") and max_depth > 0:
                    child_id = block.get("id")
                    if child_id:
                        child_result = get_page_line_count(client, child_id, block_headers, max_depth - 1)
                        if isinstance(child_result, dict):
                            return child_result
                        count += child_result

            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")

        return count
    except Exception as e:
        return {"error": str(e)}

def render_length_report(client: httpx.Client, uuids: dict, headers: dict, baseline_path: Path, update_baseline: bool = False) -> None:
    """Compara el conteo de líneas de los 10 documentos fundacionales contra
    el baseline guardado para detectar truncamiento silencioso.
    Si update_baseline=True, sobrescribe el baseline tras el reporte."""
    # Cargar baseline existente o crear dict vacío
    if baseline_path.exists():
        with open(baseline_path, "r", encoding="utf-8") as f:
            baseline = json.load(f)
    else:
        baseline = {}

    results = []
    attention_required = False
    new_baseline_created = not baseline_path.exists()
    new_docs_added = False

    for doc in DOC_KEYS:
        page_id = uuids.get(doc)
        if not page_id:
            results.append((doc, "-", "-", "-", f"[ERROR: ID no resuelto]"))
            continue

        # Contar líneas actuales
        current_count = get_page_line_count(client, page_id, headers)
        if isinstance(current_count, dict):
            results.append((doc, "-", "-", "-", f"[ERROR: {current_count.get('error', 'desconocido')}]"))
            continue

        baseline_entry = baseline.get(doc)
        if baseline_entry is None:
            # Nuevo baseline inicial
            baseline[doc] = {
                "lines": current_count,
                "captured_at": datetime.now(timezone.utc).isoformat()
            }
            new_docs_added = True
            results.append((doc, "-", current_count, "-", "[BASELINE INICIAL]"))
        else:
            baseline_lines = baseline_entry.get("lines", 0)
            delta = current_count - baseline_lines
            delta_str = f"{delta:+d}" if delta != 0 else "0"

            # Calcular porcentaje (evitar división por cero)
            if baseline_lines > 0:
                delta_pct = (delta / baseline_lines) * 100
            else:
                delta_pct = 0.0

            # Determinar veredicto
            if delta < 0 and (abs(delta_pct) >= LENGTH_TRUNCATION_THRESHOLD_PCT or abs(delta) >= LENGTH_TRUNCATION_THRESHOLD_ABS):
                verdict = "⚠️ POSIBLE TRUNCAMIENTO"
                attention_required = True
            else:
                verdict = "OK"

            results.append((doc, baseline_lines, current_count, delta_str, verdict))

            # Si update_baseline, actualizar valor en memoria (se persiste al final)
            if update_baseline:
                baseline[doc] = {
                    "lines": current_count,
                    "captured_at": datetime.now(timezone.utc).isoformat()
                }

    # Renderizar reporte
    print("[VERIFICACIÓN DE LONGITUD — LENGTH CHECK]")
    print("-" * 75)
    print(f"{'DOCUMENTO':<15} | {'BASELINE':<12} | {'ACTUAL':<12} | {'DELTA':<8} | {'VEREDICTO':<25}")
    print("-" * 75)
    for doc, baseline_val, current, delta, verdict in results:
        baseline_str = str(baseline_val) if baseline_val != "-" else "-"
        current_str = str(current) if isinstance(current, int) else current
        print(f"{doc:<15} | {baseline_str:<12} | {current_str:<12} | {delta:<8} | {verdict:<25}")
    print("-" * 75)
    print(f"[VEREDICTO FINAL] {'PASS' if not attention_required else 'ATENCIÓN REQUERIDA'}")
    print("[FIN LENGTH CHECK]")

    # Persistir baseline si se creó inicial, se agregaron docs nuevos o se solicitó actualización
    if new_baseline_created or new_docs_added or update_baseline:
        with open(baseline_path, "w", encoding="utf-8") as f:
            json.dump(baseline, f, indent=2)
        if new_baseline_created:
            print(f"[BASELINE INICIAL CREADO — {len(DOC_KEYS)} documentos]")
        elif new_docs_added:
            print(f"[BASELINE ACTUALIZADO — docs nuevos agregados]")
        elif update_baseline:
            print(f"[BASELINE ACTUALIZADO — {len(DOC_KEYS)} documentos]")

    # Exit code 1 si se requiere atención
    if attention_required:
        sys.exit(1)

def render_skill_drift_report(project_root: Path, baseline_path: Path, update_baseline: bool = False) -> None:
    """Detecta drift de CONTENIDO en archivos .skill ya registrados (nombre
    presente en disco Y en el baseline previo, pero hash distinto). No
    reemplaza a --skills/--new-skills (que detectan altas/bajas por nombre)
    -- cubre el caso complementario: mismo nombre, contenido modificado
    in-place, invisible a una comparación de sets de nombres.
    Mismo patrón que render_length_report: baseline JSON local, sin llamar
    a Notion, exit 1 si hay drift sin reconciliar. Si update_baseline=True,
    sobrescribe el baseline tras el reporte (solo tras confirmar que el
    drift ya fue documentado en Skill Library / Skill Glossary)."""
    if baseline_path.exists():
        with open(baseline_path, "r", encoding="utf-8") as f:
            baseline = json.load(f)
    else:
        baseline = {}

    disk_skills = scan_skill_folders(project_root)
    results = []
    drift_detected = False
    new_baseline_created = not baseline_path.exists()
    new_entries_added = False

    for name, rel_path in disk_skills:
        full_path = project_root / rel_path
        current_hash = hashlib.sha256(full_path.read_bytes()).hexdigest()

        entry = baseline.get(rel_path)
        if entry is None:
            baseline[rel_path] = {
                "hash": current_hash,
                "captured_at": datetime.now(timezone.utc).isoformat()
            }
            new_entries_added = True
            results.append((name, "-", "[BASELINE INICIAL]"))
        else:
            baseline_hash = entry.get("hash")
            if baseline_hash != current_hash:
                drift_detected = True
                results.append((name, rel_path, "⚠️ CONTENIDO MODIFICADO (sin reconciliar)"))
                if update_baseline:
                    baseline[rel_path] = {
                        "hash": current_hash,
                        "captured_at": datetime.now(timezone.utc).isoformat()
                    }
            else:
                results.append((name, rel_path, "OK"))

    # Detectar entradas en baseline sin archivo correspondiente en disco
    # (huérfanos de drift-tracking -- no confundir con huérfanos de --skills,
    # que comparan contra Notion; este caso es baseline vs disco local).
    disk_rel_paths = {rel for _, rel in disk_skills}
    for rel_path in baseline:
        if rel_path not in disk_rel_paths:
            results.append((rel_path, "-", "[BASELINE SIN ARCHIVO EN DISCO]"))

    print("[VERIFICACIÓN DE DRIFT DE CONTENIDO — SKILL DRIFT CHECK]")
    print("-" * 75)
    print(f"{'SKILL':<40} | {'RUTA':<20} | {'VEREDICTO':<30}")
    print("-" * 75)
    for name, rel, verdict in results:
        rel_str = rel if rel != "-" else "-"
        print(f"{name:<40} | {rel_str:<20} | {verdict:<30}")
    print("-" * 75)
    print(f"[VEREDICTO FINAL] {'PASS' if not drift_detected else 'ATENCIÓN REQUERIDA — DRIFT SIN RECONCILIAR'}")
    print("[FIN SKILL DRIFT CHECK]")

    if new_baseline_created or new_entries_added or update_baseline:
        with open(baseline_path, "w", encoding="utf-8") as f:
            json.dump(baseline, f, indent=2)
        if new_baseline_created:
            print(f"[BASELINE INICIAL CREADO — {len(disk_skills)} skills]")
        elif new_entries_added:
            print(f"[BASELINE ACTUALIZADO — skills nuevas agregadas]")
        elif update_baseline:
            print(f"[BASELINE ACTUALIZADO — hashes regrabados tras reconciliación confirmada]")

    if drift_detected and not update_baseline:
        sys.exit(1)

def render_scripts_gap_report(client: httpx.Client, headers: dict, extensions: tuple, data_source_id: str, label: str, title_property: str = "Script") -> None:
    """Cruza assets committeados en disco (árbol activo) contra la base de
    Notion correspondiente (SCRIPT LIBRARY o SKILL LIBRARY). Read-only en
    ambos lados — no escribe ni crea filas automáticamente, solo reporta
    para que el operador decida el alta."""
    disk_scripts = scan_skill_folders(PROJECT_ROOT) if extensions == (".skill",) else scan_committed_assets(PROJECT_ROOT, extensions)
    library_titles = get_script_library_titles(client, data_source_id, headers, title_property)

    def _norm(n: str) -> str:
        # Normaliza comparación de nombres de skill ignorando el sufijo
        # ".skill" -- esa extensión nunca existió como archivo físico (es
        # convención de título en Notion) y 6/28 filas reales se desviaron
        # de la convención sin sufijo, produciendo falsos gaps/huérfanos.
        # No-op para extensiones reales (.py/.sh), donde el sufijo sí importa.
        return n[:-6] if extensions == (".skill",) and n.endswith(".skill") else n

    disk_names = {name for name, _ in disk_scripts}
    library_names_norm = {_norm(t): t for t in library_titles}
    missing = sorted(name for name in disk_names if _norm(name) not in library_names_norm)
    registered = sorted(name for name in disk_names if _norm(name) in library_names_norm)
    # Filas en Notion marcadas Activo cuyo nombre (normalizado) no aparece en el árbol activo de disco.
    disk_names_norm = {_norm(n) for n in disk_names}
    orphan_notion = sorted(
        title for title, estado in library_titles.items()
        if estado == "Activo" and _norm(title) not in disk_names_norm
    )

    print(f"[{label} — GAP REPORT]")
    print("-" * 60)
    print(f"Assets en árbol activo (disco): {len(disk_names)}")
    print(f"Filas en {label} (Notion): {len(library_titles)}")
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
    print(f"[FIN {label} — GAP REPORT]")


def render_new_scripts_gap_report(extensions: tuple, glossary_path: Path, label: str = "SCRIPT GLOSSARY") -> None:
    """Compara assets committeados en disco (árbol activo) contra el Glosario
    de Scripts local (Markdown, MANUAL:SCRIPT-GLOSSARY). 100% local — no llama
    a Notion. Detecta scripts nuevos sin entrada humana documentada, como
    señal de entrada para el skill vantage-sync-script-glossary."""
    disk_scripts = scan_skill_folders(PROJECT_ROOT) if extensions == (".skill",) else scan_committed_assets(PROJECT_ROOT, extensions)

    if not glossary_path.exists():
        print(f"[-] Error: Glosario no encontrado en {glossary_path}", file=sys.stderr)
        print("    Ajusta SCRIPT_GLOSSARY_PATH en verify_versions.py o coloca el archivo ahí.", file=sys.stderr)
        sys.exit(1)

    glossary_text = glossary_path.read_text(encoding="utf-8")

    missing = []
    documented = []
    for name, rel in disk_scripts:
        # Match simple por nombre como string literal dentro del Glosario.
        # Para scripts (.py/.sh), el Glosario usa el nombre exacto de archivo
        # como encabezado -- match directo. Para skills (.skill), el apéndice
        # 23 documenta por TABLA (columnas Skill|Propósito|Trigger|Gate|
        # Anuncio) con el nombre SIN el sufijo ".skill" -- ese sufijo nunca
        # existió como archivo físico, es convención de título en Notion.
        # Buscar "nombre.skill" ahí nunca matchea aunque la skill sí esté
        # documentada -- se normaliza quitando el sufijo antes de buscar.
        match_key = name[:-6] if extensions == (".skill",) and name.endswith(".skill") else name
        if match_key in glossary_text:
            documented.append(name)
        else:
            missing.append((name, rel))

    print(f"[{label} — GAP REPORT (local, sin Notion)]")
    print("-" * 60)
    print(f"Assets en árbol activo (disco): {len(disk_scripts)}")
    print(f"Documentados en Glosario: {len(documented)}")
    print("-" * 60)
    print(f"SIN ENTRADA EN GLOSARIO — {len(missing)} encontrados:")
    if not missing:
        print("  (ninguno)")
    for name, rel in sorted(missing):
        print(f"  [-] {name}  ({rel})")
    print("-" * 60)
    print(f"[FIN {label} — GAP REPORT]")

    # Exit code 1 si hay pendientes — permite usar esto como gate en un skill
    # o automatización (ej. vantage-sync-script-glossary corre solo si esto
    # devuelve distinto de 0).
    if missing:
        sys.exit(1)

def render_bootstrap_dump(client: httpx.Client, changelog_page_id: str, headers: dict) -> None:
    """Genera el bloque [DUMP INICIO SESIÓN VANTAGE] descrito en
    KERNEL:VERSION-CHECK-TOOL y MANUAL:SESSION-CYCLE-001 §Apertura paso 1:
    estado de la última fila del Ledger, última entrada del Changelog
    (resumen truncado), y snapshot de tickets CRÍTICO/ALTO."""
    ledger = get_last_ledger_row(client, SESSION_LEDGER_DATA_SOURCE_ID, headers)
    changelog_version = get_page_version(client, changelog_page_id, headers)
    bug_tickets = get_priority_tickets(client, BUG_TRACKER_DATA_SOURCE_ID, headers, "Bug")
    task_tickets = get_priority_tickets(client, TASKS_TRACKER_DATA_SOURCE_ID, headers, "Task")
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
    parser.add_argument("--scripts", action="store_true", help="Cruza los scripts .py/.sh (únicamente) del árbol activo (Layer_1/3/4, Dashboard, Raycast) contra la base SCRIPT LIBRARY en Notion. Read-only, no requiere resolver_registry_v2.json.")
    parser.add_argument("--skills", action="store_true", help="Cruza los archivos .skill del árbol activo (Layer_1/3/4, Dashboard, Raycast) contra la base SKILL LIBRARY en Notion. Read-only, no requiere resolver_registry_v2.json.")
    parser.add_argument("--new-scripts", action="store_true", help="Cruza los scripts .py/.sh del árbol activo contra el Glosario de Scripts LOCAL (MANUAL:SCRIPT-GLOSSARY), sin llamar a Notion. Exit 1 si hay scripts sin documentar — úsalo como gate para vantage-sync-script-glossary.")
    parser.add_argument("--new-skills", action="store_true", help="Cruza los archivos .skill del árbol activo contra el Glosario de Skills LOCAL (MANUAL:SKILL-GLOSSARY), sin llamar a Notion. Exit 1 si hay skills sin documentar — úsalo como gate para vantage-sync-skill-glossary.")
    parser.add_argument("--length", action="store_true", help="Compara el conteo de líneas de contenido de los 10 documentos fundacionales contra el último baseline guardado, para detectar truncamiento silencioso. Read-only salvo --update-baseline.")
    parser.add_argument("--update-baseline", action="store_true", help="Usar junto a --length. Sobrescribe el baseline de longitud con el conteo actual tras confirmar que no hubo truncamiento (edición legítima).")
    parser.add_argument("--skills-drift", action="store_true", help="Detecta drift de CONTENIDO en archivos .skill ya registrados (mismo nombre, hash distinto respecto al último baseline) -- complementario a --skills/--new-skills, que solo detectan altas/bajas por nombre. Read-only salvo --update-skill-baseline. Exit 1 si hay drift sin reconciliar.")
    parser.add_argument("--update-skill-baseline", action="store_true", help="Usar junto a --skills-drift. Sobrescribe el baseline de hashes tras confirmar que el drift ya fue reconciliado en Skill Library (Notion) y Skill Glossary (Manual apéndice 23).")
    args = parser.parse_args()

    # 1. Inicialización de Entorno e Infraestructura
    env = load_env(ENV_PATH)
    token = env.get("NOTION_TOKEN")
    if not token:
        print("[-] Error: NOTION_TOKEN no definido en layer_1.env", file=sys.stderr)
        sys.exit(1)

    # --scripts/--skills no dependen del registro de documentos fundacionales
    # (resolver_registry_v2.json) — se resuelven y salen temprano para no exigir
    # ese archivo si el operador solo quiere el gap report correspondiente.
    if args.scripts:
        headers = get_notion_headers(token)
        with httpx.Client(timeout=20.0) as client:
            render_scripts_gap_report(client, headers, (".py", ".sh"), SCRIPT_LIBRARY_DATA_SOURCE_ID, "SCRIPT LIBRARY")
        return

    if args.skills:
        headers = get_notion_headers(token)
        with httpx.Client(timeout=20.0) as client:
            render_scripts_gap_report(client, headers, (".skill",), SKILL_LIBRARY_DATA_SOURCE_ID, "SKILL LIBRARY", title_property="Skill")
        return

    if args.new_scripts:
        render_new_scripts_gap_report((".py", ".sh"), SCRIPT_GLOSSARY_PATH)
        return

    if args.new_skills:
        render_new_scripts_gap_report((".skill",), SCRIPT_GLOSSARY_PATH, label="SKILL GLOSSARY")
        return

    # --update-skill-baseline requiere --skills-drift (mismo guard que
    # --update-baseline/--length más abajo, pero validado aquí porque
    # --skills-drift retorna temprano sin pasar por resolución de registry).
    if args.update_skill_baseline and not args.skills_drift:
        print("[-] Error: --update-skill-baseline requiere --skills-drift", file=sys.stderr)
        sys.exit(1)

    if args.skills_drift:
        baseline_path = SCRIPT_DIR / "skill_hash_baseline.json"
        render_skill_drift_report(PROJECT_ROOT, baseline_path, update_baseline=args.update_skill_baseline)
        return

    registry_path = find_registry_file(SCRIPT_DIR)
    uuids = load_document_uuids(registry_path)

    # Validar que al menos tengamos la referencia a CHANGELOG
    if "CHANGELOG" not in uuids:
        print("[-] Error Crítico: No se pudo resolver el ID del CHANGELOG.", file=sys.stderr)
        sys.exit(1)

    headers = get_notion_headers(token)

    # --update-baseline requiere --length
    if args.update_baseline and not args.length:
        print("[-] Error: --update-baseline requiere --length", file=sys.stderr)
        sys.exit(1)

    with httpx.Client(timeout=15.0) as client:
        if args.length:
            baseline_path = registry_path.parent / "length_baseline.json"
            render_length_report(client, uuids, headers, baseline_path, update_baseline=args.update_baseline)
            return

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

                if doc == "CHANGELOG_ARCHIVO":
                    # Pagina-hija sin schema de propiedad Version (no es fila de data source).
                    # Tracking de solo lectura -- no participa en la escritura de --sync.
                    read_version = get_page_version(client, page_id, headers)
                    results.append((doc, master_version, read_version, "SKIP (solo lectura, sin propiedad Version)"))
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
                if not status.startswith("PASS") and not status.startswith("SKIP"):
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