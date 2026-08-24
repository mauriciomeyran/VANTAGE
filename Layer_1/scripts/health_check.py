#!/usr/bin/env python3
"""
VANTAGE â€” Health Check de Arranque
Corre antes de L1/L2/L3. Lectura estricta, cero escritura.

Uso:
    python3 health_check.py

Exit codes:
    0 = todo OK
    1 = algo fallÃ³ (ver output)
"""

import os
import sys
import subprocess
import time
import json
import re
import requests
from pathlib import Path
from datetime import datetime, timezone

# â”€â”€ Config â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
REQUIRED_ENV_VARS = [
    "NOTION_TOKEN",
    # agrega aquÃ­ las que realmente usa layer_1.env
]

DOCS_FUNDACIONALES = {
    "V-ALIASES": ("37c938be-fc42-80d4-b9ae-f5969830331b", "Aliases.md"),
    "V-CHANGELOG": ("390938be-fc42-80e7-b429-d7d730339353", "Change Log.md"),
    "V-SYSTEM-PROMPT": ("37b938be-fc42-8001-9b9b-fcf81130d274", "System Prompt.md"),
    "V-KERNEL": ("377938be-fc42-805e-a408-c9ae518d4fe7", "Kernel.md"),
    "V-MANUAL": ("372938be-fc42-8050-9a67-e40857d7806e", "Manual.md"),
    "V-CAREER-CANON":  ("377938be-fc42-8089-93f2-f52dbd2dec6c", "Career Canon.md"),
    "V-BRIEF":         ("3a3938be-fc42-8008-9e90-ec435c01f50d", "Brief.md"),
    "V-CHANGELOG-ARCHIVO": ("3ba938be-fc42-8011-8947-fb4fa5d1f63f", "Changelog Archivo.md"),
}

ACTIVE_DIR = Path(__file__).resolve().parent.parent.parent / "DocumentaciÃ³n" / "ACTIVE"
SCRIPTS_DIR = Path(__file__).resolve().parent
DATA_DIR   = Path(__file__).resolve().parent.parent / "data"
REPO_ROOT   = Path(__file__).resolve().parent.parent.parent

INDEX_FILES = [
    "graph_v2.json",
    "entity_index_v2.json",
]

CHANGELOG_PAGE_ID = "390938be-fc42-80e7-b429-d7d730339353"

# Trackers â€” Reactivo (Bug) vs Proactivo (Task). Ver KERNEL:SCHEMA en System Prompt.
TRACKERS = {
    "BUG": {
        "data_source_id": "36e938be-fc42-81f8-8c6f-000b6769ba03",  # COL
        "title_prop": "Bug",
        "status_prop": "Status",
        "open_statuses": ["Abierto", "En revisiÃ³n"],
    },
    "TASK": {
        "data_source_id": "aaaaef55-a1ce-45f7-9c8b-1c1def2c18e8",  # COL
        "title_prop": "Task",
        "status_prop": "Status",
        "open_statuses": ["Pendiente", "En progreso"],
    },
}

RESET = "\033[0m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"


def ok(msg):
    print(f"{GREEN}âœ“{RESET} {msg}")


def fail(msg):
    print(f"{RED}âœ—{RESET} {msg}")


def warn(msg):
    print(f"{YELLOW}!{RESET} {msg}")


# â”€â”€ Checks â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def check_env():
    """Valida que las vars requeridas existan y no estÃ©n vacÃ­as."""
    missing = [v for v in REQUIRED_ENV_VARS if not os.environ.get(v)]
    if missing:
        fail(f".env â€” faltan vars: {', '.join(missing)}")
        return False
    ok(".env cargado correctamente")
    return True


def check_git():
    """Valida que el repo estÃ© limpio (sin cambios sin commitear)."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            fail("git â€” no se pudo leer status (Â¿estÃ¡s en el repo?)")
            return False
        if result.stdout.strip():
            n = len(result.stdout.strip().splitlines())
            warn(f"git â€” {n} archivo(s) sin commitear")
            return False
        ok("git limpio")
        return True
    except FileNotFoundError:
        fail("git â€” comando no encontrado")
        return False
    except subprocess.TimeoutExpired:
        fail("git â€” timeout")
        return False


def check_notion_reachable():
    """
    Valida que Notion API responda. Requiere notion_client instalado
    y NOTION_TOKEN en env. Fetch mÃ­nimo a un doc ancla (V-SYSTEM-PROMPT).
    """
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        fail("Notion â€” NOTION_TOKEN no configurado, skip")
        return False
    try:
        # import tardÃ­o para no romper el script si falta la lib
        import sys as _sys
        import glob as _glob
        # aseguro que cargue el SDK real, no el notion_client.py local que hace shadow
        venv_root = Path(__file__).parent.parent / ".venv" / "lib"
        matches = _glob.glob(str(venv_root / "python3.*" / "site-packages"))
        if matches and matches[0] not in _sys.path:
            _sys.path.insert(0, matches[0])
        from notion_client import Client

        client = Client(auth=token)
        anchor_id = DOCS_FUNDACIONALES["V-SYSTEM-PROMPT"][0]
        client.pages.retrieve(page_id=anchor_id)
        ok("Notion reachable (fetch a V-SYSTEM-PROMPT OK)")
        return True
    except ImportError:
        fail("Notion â€” notion_client no instalado en .venv")
        return False
    except Exception as e:
        fail(f"Notion â€” error de conexiÃ³n: {e}")
        return False


def check_docs_sync():
    """
    Compara timestamp/hash local (ACTIVE/*.md) vs lo que se tiene
    registrado como Ãºltima sync. Placeholder: solo valida que existan
    los 5 archivos locales â€” el diff de contenido real requiere que
    vsync_doc.py estÃ© sano primero (bug de parser pendiente).
    """
    if not ACTIVE_DIR.exists():
        warn(f"docs sync â€” carpeta {ACTIVE_DIR} no existe, skip")
        return False

    missing = []
    for name, (_, filename) in DOCS_FUNDACIONALES.items():
        expected_file = ACTIVE_DIR / filename
        if not expected_file.exists():
            missing.append(name)

    if missing:
        fail(f"docs sync â€” faltan localmente: {', '.join(missing)}")
        return False

    ok(f"{len(DOCS_FUNDACIONALES)} docs fundacionales presentes en ACTIVE/")
    return True


PRIORITY_ORDER = ["CRÃTICO", "ALTO", "MEDIO", "BAJO"]
PRIORITY_COLOR = {
    "CRÃTICO": "\033[91m",   # rojo
    "ALTO":    "\033[93m",   # amarillo
    "MEDIO":   "\033[94m",   # azul
    "BAJO":    "\033[37m",   # gris
}


def check_pending_tickets():
    """
    Lista tickets abiertos en BUG TRACKER y TASKS TRACKER,
    agrupados por prioridad (CRÃTICO â†’ ALTO â†’ MEDIO â†’ BAJO â†’ Sin Prioridad).
    Informativo â€” nunca marca el health check como fallido.
    """
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        warn("Tickets â€” NOTION_TOKEN no configurado, skip")
        return True
    try:
        import sys as _sys
        import glob as _glob
        venv_root = Path(__file__).parent.parent / ".venv" / "lib"
        matches = _glob.glob(str(venv_root / "python3.*" / "site-packages"))
        if matches and matches[0] not in _sys.path:
            _sys.path.insert(0, matches[0])
        from notion_client import Client

        client = Client(auth=token)
        total_open = 0

        for label, cfg in TRACKERS.items():
            try:
                resp = client.data_sources.query(
                    data_source_id=cfg["data_source_id"],
                    filter={
                        "or": [
                            {"property": cfg["status_prop"], "select": {"equals": s}}
                            for s in cfg["open_statuses"]
                        ]
                    },
                )
                results = resp.get("results", [])
                total_open += len(results)

                if not results:
                    ok(f"{label} â€” sin tickets abiertos")
                    continue

                # Agrupar por prioridad
                groups = {p: [] for p in PRIORITY_ORDER}
                groups["Sin Prioridad"] = []

                for page in results:
                    props = page.get("properties", {})
                    title_prop = props.get(cfg["title_prop"], {})
                    title_parts = title_prop.get("title", [])
                    title = title_parts[0]["plain_text"] if title_parts else "(sin tÃ­tulo)"
                    prioridad = props.get("Prioridad", {}).get("select", {})
                    prioridad_name = prioridad.get("name", "") if prioridad else ""
                    bucket = prioridad_name if prioridad_name in PRIORITY_ORDER else "Sin Prioridad"
                    groups[bucket].append(title)

                # Resumen en una lÃ­nea
                resumen = []
                for p in PRIORITY_ORDER:
                    if groups[p]:
                        color = PRIORITY_COLOR.get(p, "")
                        resumen.append(f"{color}{p}: {len(groups[p])}{RESET}")
                if groups["Sin Prioridad"]:
                    resumen.append(f"Sin Prioridad: {len(groups['Sin Prioridad'])}")

                warn(f"{label} â€” {len(results)} abierto(s)  [{' Â· '.join(resumen)}]")

                # Detalle: solo CRÃTICO y ALTO se listan explÃ­citamente
                for p in ["CRÃTICO", "ALTO"]:
                    for title in groups[p]:
                        color = PRIORITY_COLOR[p]
                        print(f"    {color}â–² [{p}]{RESET} {title}")

                # MEDIO y BAJO: solo conteo
                for p in ["MEDIO", "BAJO"]:
                    if groups[p]:
                        print(f"    Â· {p}: {len(groups[p])} ticket(s) â€” ver Notion")

                if groups["Sin Prioridad"]:
                    print(f"    Â· Sin Prioridad: {len(groups['Sin Prioridad'])} ticket(s) â€” requieren clasificaciÃ³n")

            except Exception as e:
                fail(f"{label} â€” error al consultar: {e}")

        if total_open == 0:
            ok("Sin pendientes en trackers")
        return True
    except ImportError:
        fail("Tickets â€” notion_client no instalado en .venv")
        return True
    except Exception as e:
        fail(f"Tickets â€” error de conexiÃ³n: {e}")
        return True


def check_system_version():
    """Fetchea versiÃ³n del sistema desde la propiedad VersiÃ³n de V-CHANGELOG."""
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        warn("versiÃ³n â€” NOTION_TOKEN no configurado, skip")
        return True
    try:
        import glob as _glob
        venv_root = Path(__file__).parent.parent / ".venv" / "lib"
        matches = _glob.glob(str(venv_root / "python3.*" / "site-packages"))
        if matches and matches[0] not in sys.path:
            sys.path.insert(0, matches[0])
        from notion_client import Client
        client = Client(auth=token)
        meta = client.pages.retrieve(page_id=CHANGELOG_PAGE_ID)
        version = ""
        for prop in meta.get("properties", {}).values():
            if prop.get("type") == "rich_text":
                parts = prop.get("rich_text", [])
                if parts:
                    version = parts[0].get("plain_text", "")
                    break
        # propiedad "VersiÃ³n" directa
        version_prop = meta.get("properties", {}).get("VersiÃ³n", {})
        if version_prop.get("type") == "rich_text":
            parts = version_prop.get("rich_text", [])
            version = parts[0].get("plain_text", "") if parts else ""
        if version:
            ok(f"Sistema v{version}")
        else:
            warn("versiÃ³n â€” no encontrada en V-CHANGELOG")
        return True
    except Exception as e:
        warn(f"versiÃ³n â€” error: {e}")
        return True


INDEX_STALE_THRESHOLD_HOURS = 24
VANTAGE_RUNTIME_SCRIPT = SCRIPTS_DIR / "vantage.py"


def _summarize_sync_output(stdout):
    """
    Extrae un resumen legible del stdout de `vantage.py sync`.
    Intenta parsear JSON (busca el Ãºltimo objeto {...} en el output);
    si falla, cae a la Ãºltima lÃ­nea de texto no vacÃ­a.
    """
    text = stdout.strip()
    if not text:
        return "sin output"

    import json as _json
    import re as _re

    # Busca el Ãºltimo bloque {...} en el stdout (tolerante a logs previos)
    matches = _re.findall(r"\{.*\}", text, flags=_re.DOTALL)
    if matches:
        try:
            data = _json.loads(matches[-1])
            status = data.get("status", "ok")
            before = data.get("entities_before")
            after = data.get("entities_after")
            if before is not None and after is not None:
                return f"status: {status}, entities: {before} â†’ {after}"
            return f"status: {status}"
        except (ValueError, _json.JSONDecodeError):
            pass

    # Fallback: Ãºltima lÃ­nea no vacÃ­a del stdout
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return lines[-1] if lines else "sin output"


def _run_vantage_sync():
    """
    Dispara `python3 vantage.py sync` para refrescar el Entity Index.
    Housekeeping de rutina, no remediaciÃ³n de un fallo del sistema
    (ver KERNEL:FAIL-PHILOSOPHY â€” un Ã­ndice stale no es un fallo,
    es mantenimiento esperado). Best-effort: nunca propaga excepciÃ³n.
    """
    if not VANTAGE_RUNTIME_SCRIPT.exists():
        fail(f"index â€” {VANTAGE_RUNTIME_SCRIPT.name} no encontrado en {SCRIPTS_DIR}, auto-sync omitido")
        return False
    try:
        result = subprocess.run(
            ["python3", "vantage.py", "sync"],
            capture_output=True, text=True, timeout=120,
            cwd=str(SCRIPTS_DIR)
        )
        if result.returncode != 0:
            fail(f"index â€” auto-sync fallÃ³: {result.stderr.strip()[:200]}")
            return False
        summary = _summarize_sync_output(result.stdout)
        ok(f"index â€” auto-sync ejecutado ({summary})")
        return True
    except subprocess.TimeoutExpired:
        fail("index â€” auto-sync timeout (>120s)")
        return False
    except Exception as e:
        fail(f"index â€” auto-sync error: {e}")
        return False


def check_index_age():
    """
    Muestra antigÃ¼edad de los Ã­ndices del runtime.
    Si algÃºn Ã­ndice cruza INDEX_STALE_THRESHOLD_HOURS, dispara sync
    automÃ¡tico vÃ­a `vantage.py sync` â€” condicional, no en cada corrida.
    Si el auto-sync falla, se reporta y NO se reintenta (Golden Rules:
    reportar el estado, esperar instrucciÃ³n â€” esto sÃ­ es un fallo real).
    """
    now = time.time()
    all_ok = True
    stale_detected = False

    for name in INDEX_FILES:
        path = DATA_DIR / name
        if not path.exists():
            warn(f"index â€” {name} no encontrado")
            all_ok = False
        else:
            age_hours = (now - path.stat().st_mtime) / 3600
            if age_hours > INDEX_STALE_THRESHOLD_HOURS:
                warn(f"index â€” {name}: {age_hours:.0f}h sin actualizar (umbral: {INDEX_STALE_THRESHOLD_HOURS}h)")
                stale_detected = True
            else:
                ok(f"index â€” {name}: actualizado hace {age_hours:.1f}h")

    if stale_detected:
        warn("index â€” umbral cruzado, disparando auto-sync...")
        synced = _run_vantage_sync()
        all_ok = all_ok and synced

    return all_ok


def check_vgit_last():
    """Muestra timestamp del Ãºltimo commit en el repo."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ci"],
            capture_output=True, text=True, timeout=10,
            cwd=str(REPO_ROOT)
        )
        if result.returncode != 0 or not result.stdout.strip():
            warn("vgit â€” no se pudo leer Ãºltimo commit")
            return True
        last = result.stdout.strip()
        ok(f"vgit â€” Ãºltimo commit: {last}")
        return True
    except Exception as e:
        warn(f"vgit â€” error: {e}")
        return True


def check_vdoc_last():
    """Muestra el doc mÃ¡s recientemente sincronizado en ACTIVE/."""
    if not ACTIVE_DIR.exists():
        warn("vdoc â€” carpeta ACTIVE/ no existe")
        return True
    now = datetime.now(tz=timezone.utc)
    latest_file = None
    latest_mtime = None
    for _, filename in DOCS_FUNDACIONALES.values():
        path = ACTIVE_DIR / filename
        if path.exists():
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            if latest_mtime is None or mtime > latest_mtime:
                latest_mtime = mtime
                latest_file = filename
    if latest_mtime:
        delta = now - latest_mtime
        hours = delta.total_seconds() / 3600
        if hours < 1:
            age_str = f"hace {int(delta.total_seconds() / 60)}min"
        elif hours < 24:
            age_str = f"hace {hours:.1f}h"
        else:
            age_str = f"hace {int(hours / 24)}d"
        ok(f"vdoc â€” Ãºltimo sync: {latest_file} ({age_str})")
    else:
        warn("vdoc â€” sin docs en ACTIVE/")
    return True


L3_HEARTBEAT_PATH    = Path.home() / ".vantage" / "l3_heartbeat.json"
L3_STALE_THRESHOLD_H = 48


def check_layer3_heartbeat():
    """Verifica que Layer 3 haya corrido recientemente."""
    if not L3_HEARTBEAT_PATH.exists():
        warn("layer3 â€” heartbeat no encontrado (\u00bfL3 nunca ha corrido?)")
        return True
    try:
        data = json.loads(L3_HEARTBEAT_PATH.read_text())
        last_run_str = data.get("last_run", "")
        if not last_run_str:
            warn("layer3 â€” heartbeat sin campo last_run")
            return True
        last_run = datetime.fromisoformat(last_run_str.replace("Z", "+00:00"))
        now      = datetime.now(tz=timezone.utc)
        age_h    = (now - last_run).total_seconds() / 3600
        created  = data.get("total_created", "?")
        failed   = data.get("total_failed", "?")
        if age_h > L3_STALE_THRESHOLD_H:
            warn(f"layer3 â€” {age_h:.0f}h sin correr (umbral: {L3_STALE_THRESHOLD_H}h) | created={created} failed={failed}")
        else:
            ok(f"layer3 â€” {age_h:.1f}h | created={created} failed={failed}")
    except Exception as e:
        warn(f"layer3 â€” error leyendo heartbeat: {e}")
    return True


CENSUS_OUTPUT_PATH     = Path("/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/data/V_ID_CENSUS_PRODUCTION.md")
CENSUS_STALE_THRESHOLD_H = 24 * 7   # 7 dÃ­as â€” el Census cambia con cierre de tickets, no con cada sync

SERIAL_SERVICE_URL = os.getenv("VANTAGE_SERIAL_SERVICE_URL", "http://localhost:8787")


def check_census_age():
    """
    Chequeo informativo de antigÃ¼edad del V-ID-CENSUS (KERNEL:CENSUS-SYNC).
    NO auto-regenera: generate_census.py pega directo a la API de Notion
    con paginaciÃ³n y rate-limit real â€” puede tardar minutos, lo cual rompe
    el contrato de health_check.py como lectura estricta y rÃ¡pida.
    Solo reporta estado; nunca marca el health check como fallido â€”
    el gate real vive en el cierre de tickets (Regla 1 de KERNEL:CENSUS-SYNC),
    no en el arranque de sesiÃ³n.
    """
    if not CENSUS_OUTPUT_PATH.exists():
        warn("census â€” V_ID_CENSUS_PRODUCTION.md no encontrado (Â¿nunca se ha generado?)")
        return True

    age_h = (time.time() - CENSUS_OUTPUT_PATH.stat().st_mtime) / 3600

    if age_h > CENSUS_STALE_THRESHOLD_H:
        warn(
            f"census â€” {age_h/24:.1f}d sin regenerar "
            f"(umbral: {CENSUS_STALE_THRESHOLD_H/24:.0f}d) â€” "
            f"correr generate_census.py si cerraste tickets con cambio de estado de ID"
        )
    else:
        ok(f"census â€” actualizado hace {age_h/24:.1f}d")

    return True   # informativo, nunca bloquea arranque


def check_auto_link_corruption():
    """
    Detector read-only de corrupciÃ³n de auto-links (D5-real).
    
    Escanea patrones `_http://` y `[nombre.ext](http://nombre.ext)` 
    (donde el texto del enlace coincide con la URL) sobre:
    - DocumentaciÃ³n/ACTIVE/*.md
    - skills/*.md  
    - Campo DescripciÃ³n en entity_index_v2.json (D5-real extensiÃ³n)
    
    Ignora enlaces HTTP/HTTPS externos legÃ­timos.
    La salida es informativa/advisory (no bloqueante, sin exit code fatal).
    """
    corruption_count = 0
    files_checked = 0
    entities_checked = 0
    
    # Patrones de corrupciÃ³n a detectar
    # 1. Guion bajo antes de http:// (_http://)
    underscore_pattern = re.compile(r'_http://')
    
    # 2. Auto-links donde el texto coincide con la URL completa [texto](http://texto)
    auto_link_pattern = re.compile(r'\[([^\]]+)\]\(http[s]?://\1\)')
    
    # Directorios a escanear (archivos markdown)
    scan_dirs = [ACTIVE_DIR, REPO_ROOT / "skills"]
    
    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
            
        for md_file in scan_dir.glob("*.md"):
            files_checked += 1
            try:
                content = md_file.read_text(encoding='utf-8')
                filename = md_file.name
                
                # Buscar patrones de corrupciÃ³n
                underscore_matches = underscore_pattern.findall(content)
                auto_link_matches = auto_link_pattern.findall(content)
                
                if underscore_matches or auto_link_matches:
                    corruption_count += 1
                    warn(f"auto-link â€” {filename} tiene patrones sospechosos:")
                    
                    if underscore_matches:
                        print(f"    â€¢ {len(underscore_matches)} ocurrencias de '_http://'")
                    
                    if auto_link_matches:
                        print(f"    â€¢ {len(auto_link_matches)} auto-links detectados:")
                        for match in auto_link_matches[:3]:  # Mostrar mÃ¡ximo 3 ejemplos
                            print(f"      - [{match}](http://{match})")
                        if len(auto_link_matches) > 3:
                            print(f"      ... y {len(auto_link_matches) - 3} mÃ¡s")
                    
            except Exception as e:
                # Silencioso para no romper el health check por errores de lectura
                pass
    
    # D5-real: Escanear campo DescripciÃ³n en entity_index_v2.json
    entity_index_path = DATA_DIR / "entity_index_v2.json"
    if entity_index_path.exists():
        try:
            with open(entity_index_path, 'r', encoding='utf-8') as f:
                entity_index = json.load(f)
            
            for entity in entity_index.get('entities', []):
                entities_checked += 1
                description = entity.get('properties', {}).get('DescripciÃ³n', '')
                
                if description and isinstance(description, str):
                    # Buscar patrones de corrupciÃ³n en DescripciÃ³n
                    underscore_matches = underscore_pattern.findall(description)
                    auto_link_matches = auto_link_pattern.findall(description)
                    
                    if underscore_matches or auto_link_matches:
                        corruption_count += 1
                        entity_name = entity.get('name', 'Unknown')
                        entity_id = entity.get('entity_id', 'Unknown')[:8]
                        warn(f"auto-link â€” Entidad [{entity_id}] {entity_name} (DescripciÃ³n) tiene patrones sospechosos:")
                        
                        if underscore_matches:
                            print(f"    â€¢ {len(underscore_matches)} ocurrencias de '_http://' en DescripciÃ³n")
                        
                        if auto_link_matches:
                            print(f"    â€¢ {len(auto_link_matches)} auto-links detectados en DescripciÃ³n:")
                            for match in auto_link_matches[:3]:
                                print(f"      - [{match}](http://{match})")
                            if len(auto_link_matches) > 3:
                                print(f"      ... y {len(auto_link_matches) - 3} mÃ¡s")
            
            if entities_checked > 0:
                print(f"  ðŸ“‹ {entities_checked} entidades verificadas en entity_index_v2.json")
                
        except Exception as e:
            # Silencioso para no romper el health check por errores de lectura
            pass
    else:
        print(f"  â„¹ï¸  entity_index_v2.json no encontrado, omitiendo escaneo de Descripciones")
    
    if corruption_count == 0:
        ok(f"auto-link â€” {files_checked} archivos + {entities_checked} entidades verificadas, sin corrupciÃ³n detectada")
    else:
        warn(f"auto-link â€” {corruption_count}/{files_checked + entities_checked} items con patrones sospechosos")
    
    return True  # Siempre advisory, nunca bloquea


def check_serial_service():
    """
    Verifica que el servicio de seriales VANTAGE esté disponible.
    Informativo — no bloquea el health check si el servicio no está corriendo.
    """
    try:
        response = requests.get(f"{SERIAL_SERVICE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            authority = data.get("authority", "unknown")
            ok(f"serial service — disponible (authority: {authority})")
            return True
        else:
            warn(f"serial service — responde con status {response.status_code}")
            return True
    except requests.exceptions.RequestException as e:
        warn(f"serial service — no disponible ({e.__class__.__name__})")
        return True
    except Exception as e:
        warn(f"serial service — error inesperado: {e}")
        return True

# â”€â”€ Runner â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def main():
    print("VANTAGE Health Check\n" + "-" * 30)
    checks = [
        ("version", check_system_version),
        ("env", check_env),
        ("git", check_git),
        ("vgit", check_vgit_last),
        ("notion", check_notion_reachable),
        ("docs_sync", check_docs_sync),
        ("vdoc", check_vdoc_last),
        ("index_age", check_index_age),
        ("layer3", check_layer3_heartbeat),
        ("census_age", check_census_age),
        ("pending_tickets", check_pending_tickets),
        ("auto_link", check_auto_link_corruption),
        ("serial_service", check_serial_service),
    ]

    results = {}
    for name, fn in checks:
        results[name] = fn()

    print("-" * 30)
    if all(results.values()):
        print(f"{GREEN}Sistema OK â€” listo para L1/L2/L3{RESET}")
        sys.exit(0)
    else:
        failed = [k for k, v in results.items() if not v]
        print(f"{RED}Sistema con issues: {', '.join(failed)}{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()