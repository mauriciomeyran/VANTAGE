#!/usr/bin/env python3
"""
vantage_bug_close.py — Fase 2
Cierra los bugs con Status=Resuelto y Next_Action=Documentar en el Bug Tracker,
cambiando Next_Action a 'Monitorear' (documentados en v8.7.2 — nada más que hacer).

Uso:
    python vantage_bug_close.py --dry-run          # muestra diff
    python vantage_bug_close.py --execute          # aplica
    python vantage_bug_close.py --id PAGE_ID --execute  # cierra uno específico (D-04)

Requiere: NOTION_TOKEN en Layer_1/config/layer_1.env o en env
"""

import os
import sys
import argparse
from pathlib import Path

_ENV_PATH = Path.home() / "Documents/04-Vantage_CV/Layer_1/config/layer_1.env"
if _ENV_PATH.exists():
    for line in _ENV_PATH.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
if not NOTION_TOKEN:
    sys.exit("ERROR: NOTION_TOKEN no encontrado.")

NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"

# ── Bugs a cerrar ─────────────────────────────────────────────────────────────
#
# Criterio: Status=Resuelto, Next_Action=Documentar, fix ya documentado en v8.7.2.
# Acción: Next_Action → Monitorear (nada más que hacer; se monitorea regresión).
#
# El bug D-04 (Next_Action type inconsistency, En revisión) NO está aquí —
# queda pendiente hasta que el operador confirme si Fix F lo cierra.

BUGS_TO_CLOSE = [
    {
        "id": "38b938be-fc42-817f-9ae0-f28dc7e268f9",
        "title": "Source_Type trailing space — source_analytics.py y gate_logic.py",
        "current_status": "Resuelto",
        "current_next_action": "Documentar",
        "new_next_action": "Monitorear",
        "note": "Documentado en v8.7.2",
    },
    {
        "id": "38b938be-fc42-81a7-9593-f6ea8af18da2",
        "title": "Fuente no asigna en Paso 0.5 — Source_Type sin trailing space",
        "current_status": "Resuelto",
        "current_next_action": "Documentar",
        "new_next_action": "Monitorear",
        "note": "Documentado en v8.7.2",
    },
    {
        "id": "38b938be-fc42-8117-9d3f-cb2903f49415",
        "title": "Source_Type vacío en 9 registros — no se asigna en ingesta L1",
        "current_status": "Resuelto",
        "current_next_action": "Documentar",
        "new_next_action": "Monitorear",
        "note": "Documentado en v8.7.2. Pendiente operativo: evaluar auto-asignación en ingesta (ver D-06).",
    },
    {
        "id": "38b938be-fc42-81fa-b1be-e60f909107fc",
        "title": "Next_Action type mismatch — rich_text vs select en layer_1_run.py",
        "current_status": "Resuelto",
        "current_next_action": "Documentar",
        "new_next_action": "Monitorear",
        "note": "Documentado en v8.7.2. Líneas 591/745/892 de layer_1_run.py.",
    },
]

# Bug D-04 — disponible para cierre manual con --id
D04 = {
    "id": "38b938be-fc42-810a-a1c1-d06b80862135",
    "title": "Next_Action type inconsistency — rich_text en URL Gate vs select en Gate Logic",
    "current_status": "En revisión",
    "current_next_action": "Patch",
    "new_next_action": "Monitorear",
    "note": "Cierre manual tras confirmar Fix F. Cambiar Status a Resuelto + Next_Action a Monitorear.",
}

# ── HTTP helpers ──────────────────────────────────────────────────────────────

try:
    import httpx
except ImportError:
    sys.exit("ERROR: httpx no instalado. Ejecuta: pip install httpx --break-system-packages")


def _headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def notion_get(path: str) -> dict:
    r = httpx.get(f"{BASE_URL}{path}", headers=_headers(), timeout=30)
    r.raise_for_status()
    return r.json()


def notion_patch(path: str, payload: dict) -> dict:
    r = httpx.patch(f"{BASE_URL}{path}", headers=_headers(), json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


# ── Lectura ───────────────────────────────────────────────────────────────────

def fetch_bug(page_id: str) -> dict:
    data = notion_get(f"/pages/{page_id.replace('-', '')}")
    props = data.get("properties", {})

    def sel(p):
        s = props.get(p, {}).get("select")
        return s["name"] if s else ""

    return {
        "id": page_id,
        "Status": sel("Status"),
        "Next_Action": sel("Next_Action"),
    }


# ── Payloads ──────────────────────────────────────────────────────────────────

def build_close_payload(new_next_action: str, also_resolve: bool = False) -> dict:
    payload: dict = {
        "properties": {
            "Next_Action": {"select": {"name": new_next_action}},
        }
    }
    if also_resolve:
        from datetime import date
        payload["properties"]["Status"] = {"select": {"name": "Resuelto"}}
        payload["properties"]["Fecha_Resolución"] = {
            "date": {"start": date.today().isoformat()}
        }
    return payload


# ── Output helpers ────────────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
YELLOW = "\033[93m"
GREEN  = "\033[92m"
RED    = "\033[91m"
CYAN   = "\033[96m"


def print_header(text):
    print(f"\n{BOLD}{CYAN}{'─'*60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'─'*60}{RESET}")


def print_bug_diff(bug: dict, live: dict):
    status_ok = live["Status"] == bug["current_status"]
    na_ok     = live["Next_Action"] == bug["current_next_action"]

    status_icon = GREEN + "✓" + RESET if status_ok else YELLOW + "⚠" + RESET
    na_icon     = GREEN + "✓" + RESET if na_ok     else YELLOW + "⚠" + RESET

    print(f"\n  {BOLD}{bug['title'][:70]}{RESET}")
    print(f"  ID: {bug['id']}")
    print(f"  Status       {status_icon}  {live['Status']!r}  (esperado: {bug['current_status']!r})")
    print(f"  Next_Action  {na_icon}  {live['Next_Action']!r}  →  {GREEN}{bug['new_next_action']!r}{RESET}")
    if bug.get("note"):
        print(f"  Nota: {YELLOW}{bug['note']}{RESET}")


# ── Dry-run ───────────────────────────────────────────────────────────────────

def dry_run(bugs: list):
    print_header("DRY RUN — vantage_bug_close.py")
    print(f"\n  Bugs a procesar: {len(bugs)}")

    errors = []
    skips  = []

    for bug in bugs:
        try:
            live = fetch_bug(bug["id"])
            print_bug_diff(bug, live)

            # Advertencia si el estado en vivo difiere del esperado
            if live["Status"] != bug["current_status"]:
                skips.append(bug["title"])
                print(f"  {YELLOW}⚠ Status en vivo difiere — se aplicará de todas formas{RESET}")

        except Exception as e:
            errors.append((bug["title"], str(e)))
            print(f"  {RED}ERROR: {e}{RESET}")

    if skips:
        print(f"\n{YELLOW}Advertencias: {len(skips)} bugs con estado inesperado en vivo{RESET}")
    if errors:
        print(f"\n{RED}Errores: {len(errors)}{RESET}")
        for t, e in errors:
            print(f"  - {t}: {e}")
        sys.exit(1)

    print(f"\n{GREEN}{BOLD}✓ Dry-run completo.{RESET}")
    print(f"  Para aplicar: {BOLD}python vantage_bug_close.py --execute{RESET}")


# ── Execute ───────────────────────────────────────────────────────────────────

def execute(bugs: list):
    print_header("EXECUTE — vantage_bug_close.py")
    errors = []

    for bug in bugs:
        try:
            # D-04 necesita also_resolve=True porque aún está "En revisión"
            also_resolve = bug["current_status"] != "Resuelto"
            payload = build_close_payload(bug["new_next_action"], also_resolve=also_resolve)
            notion_patch(f"/pages/{bug['id'].replace('-', '')}", payload)
            resolve_note = " + Status→Resuelto" if also_resolve else ""
            print(f"  {GREEN}✓ {bug['title'][:65]}  [Next_Action→{bug['new_next_action']}{resolve_note}]{RESET}")
        except Exception as e:
            errors.append((bug["title"], str(e)))
            print(f"  {RED}✗ {bug['title'][:65]}: {e}{RESET}")

    if errors:
        print(f"\n{RED}Errores: {len(errors)}{RESET}")
        for t, e in errors:
            print(f"  - {t}: {e}")
        sys.exit(1)

    print(f"\n{GREEN}{BOLD}✓ Fase 2 completa. Bug Tracker actualizado.{RESET}")
    print(f"  Siguiente: {BOLD}python vantage_kernel_patch.py --dry-run{RESET}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="VANTAGE Bug Close — Fase 2")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true")
    group.add_argument("--execute", action="store_true")
    parser.add_argument(
        "--id",
        help="Page ID de un bug específico a cerrar (e.g. D-04). "
             "Si se omite, procesa la lista estándar de 4 bugs.",
    )
    args = parser.parse_args()

    if args.id:
        # Modo single: soporta D-04 o cualquier ID arbitrario
        if args.id == D04["id"] or args.id.upper() == "D04":
            bugs = [D04]
            print(f"{YELLOW}Modo single: D-04 — {D04['title'][:60]}{RESET}")
        else:
            # ID arbitrario: construye entrada mínima
            bugs = [{
                "id": args.id,
                "title": f"Bug ID {args.id}",
                "current_status": "En revisión",
                "current_next_action": "Patch",
                "new_next_action": "Monitorear",
                "note": "Cierre manual solicitado por operador.",
            }]
    else:
        bugs = BUGS_TO_CLOSE

    if args.dry_run:
        dry_run(bugs)
    else:
        confirm = input(
            f"\n{YELLOW}⚠ APROBAR cierre de {len(bugs)} bug(s) en Notion Bug Tracker? [yep/sí]: {RESET}"
        ).strip().lower()
        if confirm not in ("yep", "sí", "si"):
            print("Abortado.")
            sys.exit(0)
        execute(bugs)


if __name__ == "__main__":
    main()
