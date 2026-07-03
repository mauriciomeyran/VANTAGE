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
from pathlib import Path

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
}

ACTIVE_DIR = Path("/Users/mauriciomeyran/Documents/04-Vantage_CV/- Documentación/ACTIVE")

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
        venv_root = Path(__file__).parent / ".venv" / "lib"
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

    ok("5 docs fundacionales presentes en ACTIVE/")
    warn("nota: diff de contenido real pendiente (bug vsync_doc.py sin resolver)")
    return True


# ── Runner ────────────────────────────────────────────────

def main():
    print("VANTAGE Health Check\n" + "-" * 30)
    checks = [
        ("env", check_env),
        ("git", check_git),
        ("notion", check_notion_reachable),
        ("docs_sync", check_docs_sync),
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
