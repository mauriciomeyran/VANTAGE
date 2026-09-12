#!/usr/bin/env python3
"""
vl1_sync.py — VANTAGE T6 sidecar reactivo (F13b go-live)

Propósito: invocación reactiva (misma UX que `vl1`) del sync F13b
(`run_outcome_status_sync`, tracker_flow.py) — reconciliación Outcome→Status
sobre el Tracker completo. Aditivo: no reemplaza `vl1`/layer_1_run.py.

Modo de uso:
    python3 vl1_sync.py               # dry-run (default) — cero writes, siempre
    python3 vl1_sync.py --dry-run     # explícito, idéntico al default
    python3 vl1_sync.py --apply       # [GATEADO en T6 — ver HANDOFF_T6 §5]

Nota de diseño (T6, importante): `run_outcome_status_sync` (tracker_flow.py)
NO trae su propio flag de dry-run — escribe vía `apply_status_sync_writeback`
en cuanto detecta una discrepancia Outcome=Contratado / Status≠Contratado,
sin importar cómo se la invoque. Que hoy (2026-09-11/12) haya 0 discrepancias
es un hecho de los datos, no una garantía del código. Por eso este runner NO
pasa el cliente real de Notion a `run_outcome_status_sync`: lo envuelve en
`ReadOnlyNotionClient`, que deja pasar las lecturas (`data_sources.query`) al
cliente real pero intercepta y nunca ejecuta `pages.update` en modo dry-run.
Así el "cero writes" es una propiedad estructural del runner, no un efecto
secundario del estado actual del Tracker.

Requiere: notion_client (paquete `notion-client`), y NOTION_TOKEN/NOTION_API_KEY
vía entorno o vía --env-file (o autodetección de config/layer_1.env / .env
subiendo desde cwd — mismo patrón que sync_status_contratado.py).

DATA_SOURCE_ID default = 442938be-fc42-828f-b72e-076818d65a5b (DATA SOURCE ID,
no DATABASE ID — ver nota en tracker_flow.py:run_outcome_status_sync).
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tracker_flow import run_outcome_status_sync  # noqa: E402

logger = logging.getLogger("vl1_sync")
logging.basicConfig(level=logging.INFO, format="%(message)s")

DATA_SOURCE_ID_DEFAULT = "442938be-fc42-828f-b72e-076818d65a5b"


# ── Carga de credencial (mismo patrón que sync_status_contratado.py) ────────

def find_env_file(explicit_path: Optional[str]) -> Optional[Path]:
    """Busca un env file: ruta explícita, o sube desde cwd probando
    config/layer_1.env y .env en cada nivel."""
    if explicit_path:
        p = Path(explicit_path).expanduser()
        return p if p.is_file() else None

    current = Path.cwd()
    for candidate in [current, *current.parents]:
        for name in ("config/layer_1.env", ".env"):
            env_path = candidate / name
            if env_path.is_file():
                return env_path
    return None


def load_env_file(path: Path) -> Dict[str, str]:
    """Parser mínimo de .env — sin dependencia de python-dotenv."""
    values: Dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def get_notion_token(explicit_env_path: Optional[str]) -> str:
    key = os.environ.get("NOTION_TOKEN") or os.environ.get("NOTION_API_KEY")
    if key:
        return key

    env_path = find_env_file(explicit_env_path)
    if env_path:
        values = load_env_file(env_path)
        key = values.get("NOTION_TOKEN") or values.get("NOTION_API_KEY")
        if key:
            print(f"NOTION_TOKEN cargado desde {env_path}")
            return key
        print(
            f"ERROR: {env_path} existe pero no tiene NOTION_TOKEN ni NOTION_API_KEY. "
            "Deteniendo — no se asume ni se interpola.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(
        "ERROR: no se encontró NOTION_TOKEN/NOTION_API_KEY (ni en el entorno, ni en "
        "config/layer_1.env o .env en el directorio actual o sus padres). Usa "
        "--env-file para apuntar explícito. Deteniendo — no se asume ni se interpola.",
        file=sys.stderr,
    )
    sys.exit(1)


# ── Proxy read-only — garantía estructural de cero writes en dry-run ────────

class _NoWritePages:
    """Espeja `client.pages` pero `update()` nunca toca Notion: registra la
    intención y retorna un stub. `retrieve()` no se usa por
    run_outcome_status_sync, pero se incluye por completitud de interfaz."""

    def __init__(self) -> None:
        self.would_update: List[Dict[str, Any]] = []

    def update(self, page_id: Optional[str] = None, properties: Optional[Dict[str, Any]] = None, **_: Any) -> Dict[str, Any]:
        self.would_update.append({"page_id": page_id, "properties": properties or {}})
        logger.info(f"[DRY-RUN] would update {str(page_id)[:8]} -> {properties}")
        return {"id": page_id, "_dry_run": True}


class ReadOnlyNotionClient:
    """Wrapper: `data_sources.query` pasa al cliente real (lectura); `pages`
    se reemplaza por `_NoWritePages` (escritura interceptada, nunca real)."""

    def __init__(self, real_client: Any) -> None:
        self.data_sources = real_client.data_sources
        self.pages = _NoWritePages()


def build_real_client(token: str) -> Any:
    from notion_client import Client  # import diferido: no requerido para --apply bloqueado
    return Client(auth=token)


# ── CLI ──────────────────────────────────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="Lee y reporta, cero writes. Default si no se pasa --apply.")
    parser.add_argument("--apply", action="store_true", help="[GATEADO en T6 — no ejecuta ningún write. Ver HANDOFF_T6 §5.]")
    parser.add_argument("--env-file", default=None, help="Ruta explícita a un env file (config/layer_1.env o .env).")
    parser.add_argument(
        "--data-source-id",
        default=os.environ.get("NOTION_DATA_SOURCE_ID", DATA_SOURCE_ID_DEFAULT),
        help="Notion DATA SOURCE ID (no database ID).",
    )
    args = parser.parse_args(argv)

    if args.apply:
        print(
            "[GATE] --apply no está habilitado en T6 (HANDOFF_T6_VL1S_SIDECAR §5: "
            "gate futuro, requiere autorización explícita de Mau+Arena cuando Outcome "
            "deje de estar vacío en la muestra real). Corre --dry-run. Deteniendo sin "
            "tocar Notion — ningún cliente fue siquiera construido."
        )
        return 2

    token = get_notion_token(args.env_file)
    real_client = build_real_client(token)
    ro_client = ReadOnlyNotionClient(real_client)

    print(f"[vl1_sync] DRY-RUN — data_source_id={args.data_source_id}")
    result = run_outcome_status_sync(ro_client, args.data_source_id)
    print(f"[vl1_sync] checked={result['checked']} synced={result['synced']} skipped={result['skipped']}")

    if ro_client.pages.would_update:
        print(f"[vl1_sync] {len(ro_client.pages.would_update)} fila(s) HABRÍAN sido escritas (dry-run, no ejecutado):")
        for u in ro_client.pages.would_update:
            print(f"  - page_id={u['page_id']} properties={u['properties']}")
    else:
        print("[vl1_sync] 0 filas a sincronizar — sin discrepancias.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
