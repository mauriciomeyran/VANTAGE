#!/usr/bin/env python3
"""
sync_status_contratado.py — VANTAGE Tracker

Propósito: cerrar el gap descrito en HO-000042 (S3). tracker_flow.py protege
Status="Contratado" pero ningún writer seteaba ese valor — la contratación
real vivía solo en Outcome="Contratado". Tras el patch de schema (HO-000042,
decisión (b) del operador), Status ya admite "Contratado" como opción; este
script sincroniza filas donde Outcome="Contratado" pero Status todavía no
refleja eso.

Modo de uso:
    python sync_status_contratado.py --dry-run     # reporta filas afectadas, no escribe
    python sync_status_contratado.py --apply        # aplica el cambio (requiere --dry-run previo en la misma sesión)

Fuente de autoridad: Notion API directa (no notion-mcp) — ver KERNEL:CONTEXT-INFRASTRUCTURE,
Terminal es la ruta preferente para operaciones estructurales.

Requiere: NOTION_API_KEY definida en un archivo .env (busca en el directorio
actual y sube hasta encontrar uno, o usar --env-file para apuntar explícito)
con acceso al Tracker DB (data source 442938be-fc42-828f-b72e-076818d65a5b).
"""

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("Falta 'requests'. Instalar con: pip install requests --break-system-packages", file=sys.stderr)
    sys.exit(1)


def find_env_file(explicit_path: str | None) -> Path | None:
    """Busca un .env: ruta explícita, o sube desde cwd hasta encontrar uno."""
    if explicit_path:
        p = Path(explicit_path).expanduser()
        return p if p.is_file() else None

    current = Path.cwd()
    for candidate in [current, *current.parents]:
        env_path = candidate / ".env"
        if env_path.is_file():
            return env_path
    return None


def load_env_file(path: Path) -> dict[str, str]:
    """Parser mínimo de .env — sin dependencia de python-dotenv.
    Soporta KEY=value, comillas simples/dobles, líneas vacías y comentarios (#)."""
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        values[key] = value
    return values

NOTION_VERSION = "2022-06-28"
DATA_SOURCE_ID = "596938be-fc42-836b-aea7-814a1491bd47"
API_BASE = "https://api.notion.com/v1"

TARGET_OUTCOME = "Contratado"
TARGET_STATUS = "Contratado"

PROTECTED_STATUSES_REF = {
    # Espejo informativo de PROTECTED_STATUSES en tracker_flow.py — no se
    # importa directo para no acoplar este script al repo. Si cambia allá,
    # actualizar aquí también (ver Bug Tracker si diverge).
    "Contratado",
}


def get_api_key(explicit_env_path: str | None) -> str:
    # Prioridad 1: variable ya exportada en el entorno (por si el operador la setea manualmente).
    key = os.environ.get("NOTION_API_KEY")
    if key:
        return key

    # Prioridad 2: .env — explícito o autodetectado subiendo desde cwd.
    env_path = find_env_file(explicit_env_path)
    if env_path:
        env_values = load_env_file(env_path)
        key = env_values.get("NOTION_API_KEY") or env_values.get("NOTION_TOKEN")
        if key:
            print(f"NOTION_API_KEY cargada desde {env_path}")
            return key
        print(f"ERROR: {env_path} existe pero no tiene NOTION_API_KEY. Deteniendo — no se asume ni se interpola.", file=sys.stderr)
        sys.exit(1)

    print(
        "ERROR: no se encontró NOTION_API_KEY (ni en el entorno, ni en un .env "
        "en el directorio actual o sus padres). Usa --env-file para apuntar explícito. "
        "Deteniendo — no se asume ni se interpola.",
        file=sys.stderr,
    )
    sys.exit(1)


def query_data_source(api_key: str, start_cursor: str | None = None) -> dict:
    """Query directo del data source vía REST — filtra Outcome=Contratado."""
    url = f"{API_BASE}/databases/{DATA_SOURCE_ID}/query"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    payload = {
        "filter": {
            "property": "Outcome",
            "select": {"equals": TARGET_OUTCOME},
        },
        "page_size": 100,
    }
    if start_cursor:
        payload["start_cursor"] = start_cursor

    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def collect_target_rows(api_key: str) -> list[dict]:
    """Pagina el data source completo, filtrando por Outcome=Contratado."""
    rows = []
    cursor = None
    while True:
        data = query_data_source(api_key, cursor)
        rows.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
        time.sleep(0.35)  # cortesía de rate-limit
    return rows


def extract_status(page: dict) -> str | None:
    status_prop = page.get("properties", {}).get("Status", {})
    select_val = status_prop.get("select")
    return select_val["name"] if select_val else None


def extract_rol(page: dict) -> str:
    title_prop = page.get("properties", {}).get("Rol", {})
    title_arr = title_prop.get("title", [])
    if title_arr:
        return "".join(t.get("plain_text", "") for t in title_arr)
    return "(sin título)"


def update_status(api_key: str, page_id: str) -> None:
    url = f"{API_BASE}/pages/{page_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    payload = {
        "properties": {
            "Status": {"select": {"name": TARGET_STATUS}}
        }
    }
    resp = requests.patch(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Reporta filas afectadas, no escribe.")
    mode.add_argument("--apply", action="store_true", help="Aplica el cambio de Status en Notion.")
    parser.add_argument("--env-file", default="config/layer_1.env", help="Ruta explícita a un .env (opcional; si se omite, se autodetecta).")
    args = parser.parse_args()

    api_key = get_api_key(args.env_file)

    print(f"[{datetime.now().isoformat(timespec='seconds')}] Consultando filas con Outcome='{TARGET_OUTCOME}'...")
    rows = collect_target_rows(api_key)
    print(f"Filas totales con Outcome='{TARGET_OUTCOME}': {len(rows)}")

    to_update = []
    for page in rows:
        current_status = extract_status(page)
        if current_status != TARGET_STATUS:
            to_update.append((page["id"], extract_rol(page), current_status))

    if not to_update:
        print("Sin discrepancias — todas las filas con Outcome='Contratado' ya tienen Status='Contratado'. Nada que hacer.")
        return

    print(f"\nFilas a corregir ({len(to_update)}):")
    for page_id, rol, current_status in to_update:
        print(f"  - {rol!r} | page_id={page_id} | Status actual: {current_status!r} -> {TARGET_STATUS!r}")

    if args.dry_run:
        print("\nDRY RUN — ninguna escritura ejecutada. Correr con --apply para aplicar.")
        return

    print(f"\nAplicando {len(to_update)} actualizaciones...")
    errors = []
    for page_id, rol, _ in to_update:
        try:
            update_status(api_key, page_id)
            print(f"  OK  {rol!r}")
        except Exception as exc:  # noqa: BLE001 — reportar y continuar, no abortar el lote
            print(f"  FAIL {rol!r} — {exc}", file=sys.stderr)
            errors.append((page_id, rol, str(exc)))
        time.sleep(0.35)

    print(f"\nCompletado: {len(to_update) - len(errors)}/{len(to_update)} filas actualizadas.")
    if errors:
        print(f"Fallos ({len(errors)}) — revisar manualmente:", file=sys.stderr)
        for page_id, rol, err in errors:
            print(f"  {rol!r} ({page_id}): {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
