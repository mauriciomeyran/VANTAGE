#!/usr/bin/env python3
"""
git_sync.py — VANTAGE L4 Git Auto-Sync
========================================
Detecta cambios en el repo y hace add+commit+push automáticamente.
Sin cambios: no hace nada, no emite ruido.
Con cambios: commit con timestamp + push a origin/main.

Capa: L4 — Version Control & Infrastructure
Ruta canónica: ~/Documents/04-VANTAGE_CV/Layer_4/scripts/git_sync.py

Uso:
    python3 git_sync.py              # corre sync real
    python3 git_sync.py --dry-run   # ver qué commitearía sin ejecutar
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Layer_4/scripts/ -> Layer_4/ -> 04-VANTAGE_CV/
REPO_ROOT = Path(__file__).resolve().parents[2]
BRANCH = "main"


def run(cmd: list[str], cwd: Path = REPO_ROOT) -> tuple[int, str, str]:
    result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def has_changes() -> bool:
    code, out, _ = run(["git", "status", "--porcelain"])
    return code == 0 and bool(out)


def get_changed_files() -> list[str]:
    _, out, _ = run(["git", "status", "--porcelain"])
    return [line.strip() for line in out.splitlines() if line.strip()]


def sync(dry_run: bool = False) -> dict:
    if not has_changes():
        return {"status": "clean", "message": "No hay cambios — nada que commitear."}

    changed = get_changed_files()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    msg = f"auto-sync: {timestamp} ({len(changed)} archivo(s))"

    if dry_run:
        return {"status": "dry_run", "would_commit": msg, "files": changed}

    code, _, err = run(["git", "add", "-A"])
    if code != 0:
        return {"status": "error", "step": "git add", "error": err}

    code, out, err = run(["git", "commit", "-m", msg])
    if code != 0:
        return {"status": "error", "step": "git commit", "error": err or out}

    code, out, err = run(["git", "push", "origin", BRANCH])
    if code != 0:
        return {"status": "error", "step": "git push", "error": err or out}

    return {
        "status": "ok",
        "commit_message": msg,
        "files_committed": len(changed),
        "files": changed,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VANTAGE L4 Git Auto-Sync")
    parser.add_argument("--dry-run", action="store_true", help="Ver cambios sin commitear")
    args = parser.parse_args()

    result = sync(dry_run=args.dry_run)

    if result["status"] == "clean":
        print(result["message"])
        sys.exit(0)
    elif result["status"] == "ok":
        print(f"✅ L4 Sync OK — {result['files_committed']} archivo(s) commiteados")
        print(f"   {result['commit_message']}")
        sys.exit(0)
    elif result["status"] == "dry_run":
        print(f"DRY RUN — se commitearía: {result['would_commit']}")
        for f in result["files"]:
            print(f"  {f}")
        sys.exit(0)
    else:
        print(f"❌ Error en {result['step']}: {result['error']}", file=sys.stderr)
        sys.exit(1)
