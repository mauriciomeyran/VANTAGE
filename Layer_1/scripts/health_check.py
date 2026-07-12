#!/usr/bin/env python3
"""
VANTAGE — Health Check de Arranque
Corre antes de L1/L2/L3. Lectura estricta, cero escritura.

Uso:
    python3 health_check.py

Exit codes:
    0 = todo OK
    1 = algo falló (ver output)
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────────
REQUIRED_ENV_VARS = [
    "NOTION_TOKEN",
    # agrega aquí las que realmente usa layer_1.env
]

DOCS_FUNDACIONALES = {
    "V-ALIASES": ("37c938be-fc42-80d4-b9ae-f5969830331b", "Aliases.md"),
    "V-CHANGELOG": ("390938be-fc42-80e7-b429-d7d730339353", "Change Log.md"),
    "V-SYSTEM-PROMPT": ("37b938be-fc42-8001-9b9b-fcf81130d274", "System Prompt.md"),
    "V-KERNEL": ("377938be-fc42-805e-a408-c9ae518d4fe7", "Kernel.md"),
    "V-MANUAL": ("372938be-fc42-8050-9a67-e40857d7806e", "Manual.md"),
    "V-CAREER-CANON":  ("377938be-fc42-8089-93f2-f52dbd2dec6c", "Career Canon.md"),
}

ACTIVE_DIR = Path(__file__).resolve().parent.parent.parent / "Documentación" / "ACTIVE"
SCRIPTS_DIR = Path(__file__).resolve().parent
DATA_DIR   = Path(__file__).resolve().parent.parent / "data"
REPO_ROOT   = Path(__file__).resolve().parent.parent.parent

INDEX_FILES = [
    "graph_v2.json",
    "entity_index_v2.json",
]

CHANGELOG_PAGE_ID = "390938be-fc42-80e7-b429-d7d730339353"

# Trackers — Reactivo (Bug) vs Proactivo (Task). Ver KERNEL:SCHEMA en System Prompt.
TRACKERS = {
    "BUG": {
        "data_source_id": "36e938be-fc42-81f8-8c6f-000b6769ba03",  # COL
        "title_prop": "Bug",
        "status_prop": "Status",
        "open_statuses": ["Abierto", "En revisión"],
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
    print(f"{GREEN}✓{RESET} {msg}")


def fail(msg):
    print(f"{RED}✗{RESET} {msg}")


def warn(msg):
    print(f"{YELLOW}!{RESET} {msg}")


# ── Checks ────────────────────────────────────────────────

def check_env():
    """Valida que las vars requeridas existan y no estén vacías."""
    missing = [v for v in REQUIRED_ENV_VARS if not os.environ.get(v)]
    if missing:
        fail(f".env — faltan vars: {', '.join(missing)}")
        return False
    ok(".env cargado correctamente")
    return True


def check_git():
    """Valida que el repo esté limpio (sin cambios sin commitear)."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            fail("git — no se pudo leer status (¿estás en el repo?)")
            return False
        if result.stdout.strip():
            n = len(result.stdout.strip().splitlines())
            warn(f"git — {n} archivo(s) sin commitear")
            return False
        ok("git limpio")
        return True
    except FileNotFoundError:
        fail("git — comando no encontrado")
        return False
    except subprocess.TimeoutExpired:
        fail("git — timeout")
        return False


def check_notion_reachable():
    """
    Valida que Notion API responda. Requiere notion_client instalado
    y NOTION_TOKEN en env. Fetch mínimo a un doc ancla (V-SYSTEM-PROMPT).
    """
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        fail("Notion — NOTION_TOKEN no configurado, skip")
        return False
    try:
        # import tardío para no romper el script si falta la lib
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
        fail("Notion — notion_client no instalado en .venv")
        return False
    except Exception as e:
        fail(f"Notion — error de conexión: {e}")
        return False


def check_docs_sync():
    """
    Compara timestamp/hash local (ACTIVE/*.md) vs lo que se tiene
    registrado como última sync. Placeholder: solo valida que existan
    los 5 archivos locales — el diff de contenido real requiere que
    vsync_doc.py esté sano primero (bug de parser pendiente).
    """
    if not ACTIVE_DIR.exists():
        warn(f"docs sync — carpeta {ACTIVE_DIR} no existe, skip")
        return False

    missing = []
    for name, (_, filename) in DOCS_FUNDACIONALES.items():
        expected_file = ACTIVE_DIR / filename
        if not expected_file.exists():
            missing.append(name)

    if missing:
        fail(f"docs sync — faltan localmente: {', '.join(missing)}")
        return False

    ok(f"{len(DOCS_FUNDACIONALES)} docs fundacionales presentes en ACTIVE/")
    return True


PRIORITY_ORDER = ["CRÍTICO", "ALTO", "MEDIO", "BAJO"]
PRIORITY_COLOR = {
    "CRÍTICO": "\033[91m",   # rojo
    "ALTO":    "\033[93m",   # amarillo
    "MEDIO":   "\033[94m",   # azul
    "BAJO":    "\033[37m",   # gris
}


def check_pending_tickets():
    """
    Lista tickets abiertos en BUG TRACKER y TASKS TRACKER,
    agrupados por prioridad (CRÍTICO → ALTO → MEDIO → BAJO → Sin Prioridad).
    Informativo — nunca marca el health check como fallido.
    """
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        warn("Tickets — NOTION_TOKEN no configurado, skip")
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
                    ok(f"{label} — sin tickets abiertos")
                    continue

                # Agrupar por prioridad
                groups = {p: [] for p in PRIORITY_ORDER}
                groups["Sin Prioridad"] = []

                for page in results:
                    props = page.get("properties", {})
                    title_prop = props.get(cfg["title_prop"], {})
                    title_parts = title_prop.get("title", [])
                    title = title_parts[0]["plain_text"] if title_parts else "(sin título)"
                    prioridad = props.get("Prioridad", {}).get("select", {})
                    prioridad_name = prioridad.get("name", "") if prioridad else ""
                    bucket = prioridad_name if prioridad_name in PRIORITY_ORDER else "Sin Prioridad"
                    groups[bucket].append(title)

                # Resumen en una línea
                resumen = []
                for p in PRIORITY_ORDER:
                    if groups[p]:
                        color = PRIORITY_COLOR.get(p, "")
                        resumen.append(f"{color}{p}: {len(groups[p])}{RESET}")
                if groups["Sin Prioridad"]:
                    resumen.append(f"Sin Prioridad: {len(groups['Sin Prioridad'])}")

                warn(f"{label} — {len(results)} abierto(s)  [{' · '.join(resumen)}]")

                # Detalle: solo CRÍTICO y ALTO se listan explícitamente
                for p in ["CRÍTICO", "ALTO"]:
                    for title in groups[p]:
                        color = PRIORITY_COLOR[p]
                        print(f"    {color}▲ [{p}]{RESET} {title}")

                # MEDIO y BAJO: solo conteo
                for p in ["MEDIO", "BAJO"]:
                    if groups[p]:
                        print(f"    · {p}: {len(groups[p])} ticket(s) — ver Notion")

                if groups["Sin Prioridad"]:
                    print(f"    · Sin Prioridad: {len(groups['Sin Prioridad'])} ticket(s) — requieren clasificación")

            except Exception as e:
                fail(f"{label} — error al consultar: {e}")

        if total_open == 0:
            ok("Sin pendientes en trackers")
        return True
    except ImportError:
        fail("Tickets — notion_client no instalado en .venv")
        return True
    except Exception as e:
        fail(f"Tickets — error de conexión: {e}")
        return True


def check_system_version():
    """Fetchea versión del sistema desde la propiedad Versión de V-CHANGELOG."""
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        warn("versión — NOTION_TOKEN no configurado, skip")
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
        # propiedad "Versión" directa
        version_prop = meta.get("properties", {}).get("Versión", {})
        if version_prop.get("type") == "rich_text":
            parts = version_prop.get("rich_text", [])
            version = parts[0].get("plain_text", "") if parts else ""
        if version:
            ok(f"Sistema v{version}")
        else:
            warn("versión — no encontrada en V-CHANGELOG")
        return True
    except Exception as e:
        warn(f"versión — error: {e}")
        return True


INDEX_STALE_THRESHOLD_HOURS = 24
VANTAGE_RUNTIME_SCRIPT = SCRIPTS_DIR / "vantage.py"


def _summarize_sync_output(stdout):
    """
    Extrae un resumen legible del stdout de `vantage.py sync`.
    Intenta parsear JSON (busca el último objeto {...} en el output);
    si falla, cae a la última línea de texto no vacía.
    """
    text = stdout.strip()
    if not text:
        return "sin output"

    import json as _json
    import re as _re

    # Busca el último bloque {...} en el stdout (tolerante a logs previos)
    matches = _re.findall(r"\{.*\}", text, flags=_re.DOTALL)
    if matches:
        try:
            data = _json.loads(matches[-1])
            status = data.get("status", "ok")
            before = data.get("entities_before")
            after = data.get("entities_after")
            if before is not None and after is not None:
                return f"status: {status}, entities: {before} → {after}"
            return f"status: {status}"
        except (ValueError, _json.JSONDecodeError):
            pass

    # Fallback: última línea no vacía del stdout
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return lines[-1] if lines else "sin output"


def _run_vantage_sync():
    """
    Dispara `python3 vantage.py sync` para refrescar el Entity Index.
    Housekeeping de rutina, no remediación de un fallo del sistema
    (ver KERNEL:FAIL-PHILOSOPHY — un índice stale no es un fallo,
    es mantenimiento esperado). Best-effort: nunca propaga excepción.
    """
    if not VANTAGE_RUNTIME_SCRIPT.exists():
        fail(f"index — {VANTAGE_RUNTIME_SCRIPT.name} no encontrado en {SCRIPTS_DIR}, auto-sync omitido")
        return False
    try:
        result = subprocess.run(
            ["python3", "vantage.py", "sync"],
            capture_output=True, text=True, timeout=120,
            cwd=str(SCRIPTS_DIR)
        )
        if result.returncode != 0:
            fail(f"index — auto-sync falló: {result.stderr.strip()[:200]}")
            return False
        summary = _summarize_sync_output(result.stdout)
        ok(f"index — auto-sync ejecutado ({summary})")
        return True
    except subprocess.TimeoutExpired:
        fail("index — auto-sync timeout (>120s)")
        return False
    except Exception as e:
        fail(f"index — auto-sync error: {e}")
        return False


def check_index_age():
    """
    Muestra antigüedad de los índices del runtime.
    Si algún índice cruza INDEX_STALE_THRESHOLD_HOURS, dispara sync
    automático vía `vantage.py sync` — condicional, no en cada corrida.
    Si el auto-sync falla, se reporta y NO se reintenta (Golden Rules:
    reportar el estado, esperar instrucción — esto sí es un fallo real).
    """
    now = time.time()
    all_ok = True
    stale_detected = False

    for name in INDEX_FILES:
        path = DATA_DIR / name
        if not path.exists():
            warn(f"index — {name} no encontrado")
            all_ok = False
        else:
            age_hours = (now - path.stat().st_mtime) / 3600
            if age_hours > INDEX_STALE_THRESHOLD_HOURS:
                warn(f"index — {name}: {age_hours:.0f}h sin actualizar (umbral: {INDEX_STALE_THRESHOLD_HOURS}h)")
                stale_detected = True
            else:
                ok(f"index — {name}: actualizado hace {age_hours:.1f}h")

    if stale_detected:
        warn("index — umbral cruzado, disparando auto-sync...")
        synced = _run_vantage_sync()
        all_ok = all_ok and synced

    return all_ok


def check_vgit_last():
    """Muestra timestamp del último commit en el repo."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ci"],
            capture_output=True, text=True, timeout=10,
            cwd=str(REPO_ROOT)
        )
        if result.returncode != 0 or not result.stdout.strip():
            warn("vgit — no se pudo leer último commit")
            return True
        last = result.stdout.strip()
        ok(f"vgit — último commit: {last}")
        return True
    except Exception as e:
        warn(f"vgit — error: {e}")
        return True


def check_vdoc_last():
    """Muestra el doc más recientemente sincronizado en ACTIVE/."""
    if not ACTIVE_DIR.exists():
        warn("vdoc — carpeta ACTIVE/ no existe")
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
        ok(f"vdoc — último sync: {latest_file} ({age_str})")
    else:
        warn("vdoc — sin docs en ACTIVE/")
    return True


L3_HEARTBEAT_PATH    = Path.home() / ".vantage" / "l3_heartbeat.json"
L3_STALE_THRESHOLD_H = 48


def check_layer3_heartbeat():
    """Verifica que Layer 3 haya corrido recientemente."""
    if not L3_HEARTBEAT_PATH.exists():
        warn("layer3 — heartbeat no encontrado (\u00bfL3 nunca ha corrido?)")
        return True
    try:
        data = json.loads(L3_HEARTBEAT_PATH.read_text())
        last_run_str = data.get("last_run", "")
        if not last_run_str:
            warn("layer3 — heartbeat sin campo last_run")
            return True
        last_run = datetime.fromisoformat(last_run_str.replace("Z", "+00:00"))
        now      = datetime.now(tz=timezone.utc)
        age_h    = (now - last_run).total_seconds() / 3600
        created  = data.get("total_created", "?")
        failed   = data.get("total_failed", "?")
        if age_h > L3_STALE_THRESHOLD_H:
            warn(f"layer3 — {age_h:.0f}h sin correr (umbral: {L3_STALE_THRESHOLD_H}h) | created={created} failed={failed}")
        else:
            ok(f"layer3 — {age_h:.1f}h | created={created} failed={failed}")
    except Exception as e:
        warn(f"layer3 — error leyendo heartbeat: {e}")
    return True


CENSUS_OUTPUT_PATH     = Path(__file__).resolve().parent / "V_ID_CENSUS_PRODUCTION.md"
CENSUS_STALE_THRESHOLD_H = 24 * 7   # 7 días — el Census cambia con cierre de tickets, no con cada sync


def check_census_age():
    """
    Chequeo informativo de antigüedad del V-ID-CENSUS (KERNEL:CENSUS-SYNC).
    NO auto-regenera: generate_census.py pega directo a la API de Notion
    con paginación y rate-limit real — puede tardar minutos, lo cual rompe
    el contrato de health_check.py como lectura estricta y rápida.
    Solo reporta estado; nunca marca el health check como fallido —
    el gate real vive en el cierre de tickets (Regla 1 de KERNEL:CENSUS-SYNC),
    no en el arranque de sesión.
    """
    if not CENSUS_OUTPUT_PATH.exists():
        warn("census — V_ID_CENSUS_PRODUCTION.md no encontrado (¿nunca se ha generado?)")
        return True

    age_h = (time.time() - CENSUS_OUTPUT_PATH.stat().st_mtime) / 3600

    if age_h > CENSUS_STALE_THRESHOLD_H:
        warn(
            f"census — {age_h/24:.1f}d sin regenerar "
            f"(umbral: {CENSUS_STALE_THRESHOLD_H/24:.0f}d) — "
            f"correr generate_census.py si cerraste tickets con cambio de estado de ID"
        )
    else:
        ok(f"census — actualizado hace {age_h/24:.1f}d")

    return True   # informativo, nunca bloquea arranque

# ── Runner ────────────────────────────────────────────────

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
    ]

    results = {}
    for name, fn in checks:
        results[name] = fn()

    print("-" * 30)
    if all(results.values()):
        print(f"{GREEN}Sistema OK — listo para L1/L2/L3{RESET}")
        sys.exit(0)
    else:
        failed = [k for k, v in results.items() if not v]
        print(f"{RED}Sistema con issues: {', '.join(failed)}{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
