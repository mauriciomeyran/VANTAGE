#!/usr/bin/env python3
"""
git_sync.py — VANTAGE L4 Git Auto-Sync + MCP Server Update (v9.13.1)
===================================================================
Detecta cambios en el repo y hace add+commit+push automáticamente.
Sincroniza automáticamente index.json si hay cambios en /skills/

Características:
- Regenera index.json si hay cambios en las skills (skills/*.md, */SKILL.md, legacy *.skill)
- Detecta cambios en git status con timeout estricto
- Commitea + push a origin/main con timeout de red (30s max)
- Sin cambios: no hace nada, no emite ruido

Capa: L4 — Version Control & Infrastructure
Ruta canónica: ~/Documents/03 Projects/VANTAGE/Layer_4/scripts/git_sync.py

Uso:
    python3 git_sync.py              # corre sync real (commit + push de la rama activa)
    python3 git_sync.py --dry-run   # ver qué commitearía sin escribir ni commitear
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Layer_4/scripts/ -> Layer_4/ -> VANTAGE
REPO_ROOT = Path(__file__).resolve().parents[2]
BRANCH = "main"
SKILLS_DIR = REPO_ROOT / "skills"
INDEX_JSON = SKILLS_DIR / "index.json"
BASE_URL = "https://mauriciomeyran.github.io/VANTAGE/skills"

SKILL_DESCRIPTIONS = {
    "prompt-master": "Genera prompts optimizados para herramientas de IA",
    "tailored-resume-generator": "Genera currículums personalizados según descripciones de trabajo",
    "vantage-create-bug-task": "Crea tickets en Bug Tracker o Task Tracker de VANTAGE",
    "vantage-documentacion-transversal-implementacion": "Implementa documentación transversal",
    "vantage-documentacion-transversal-propuesta": "Genera propuestas de documentación transversal",
    "vantage-documentacion-transversal": "Mantiene documentación transversal en documentos funcionales",
    "vantage-present-handoff": "Genera snapshot de contexto de sesión para continuidad",
    "vantage-session-close": "Protocolo de cierre de sesión VANTAGE",
    "vantage-session-open": "Protocolo de apertura de sesión VANTAGE",
    "vantage-tidy-bug-task-tracker": "Marca tickets para archivo en Bug/Task Tracker",
    "vantage-tidy-changelog": "Mantiene el Change Log con las últimas 10 entradas",
    "vantage-tidy-opportunities-tracker": "Identifica duplicados y vacantes expiradas en VANTAGE Tracker",
}


def run(cmd: list[str], cwd: Path = REPO_ROOT, timeout: int = 15) -> tuple[int, str, str]:
    """Ejecuta comando en subprocess con captura de output y timeout estricto."""
    try:
        result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return 128, "", f"TimeoutExpired: El comando {' '.join(cmd)} superó el límite de {timeout}s."
    except Exception as e:
        return 1, "", f"ExecutionError: {e}"


class GitError(Exception):
    pass


SKILL_PATTERNS = ("*.md", "*/SKILL.md", "*.skill")


def get_skill_files() -> list[str]:
    """Obtiene los nombres de skill en /skills/.

    Layout vigente: un `skills/<nombre>.md` por skill. `*.skill` es el sufijo
    legacy (verify_versions.py lo documenta como formato histórico) y se sigue
    aceptando. Antes solo se buscaba `*.skill` → la lista siempre salía vacía y
    `index.json` nunca se regeneraba.
    """
    if not SKILLS_DIR.exists():
        return []
    names = set()
    for pattern in SKILL_PATTERNS:
        for f in SKILLS_DIR.glob(pattern):
            if f.name.startswith("."):
                continue
            if pattern == "*/SKILL.md":
                names.add(f.parent.name)
            elif f.name.endswith(".skill"):
                names.add(f.name[: -len(".skill")])
            else:
                names.add(f.stem)
    return sorted(names)


def regenerate_index_json(dry_run: bool = False) -> bool:
    """Regenera index.json si hay cambios en las skills. Retorna True si hubo cambios.

    Con dry_run=True calcula el resultado pero NO escribe el archivo (antes el
    --dry-run sí creaba index.json, dejando el working tree modificado).
    """
    skill_files = get_skill_files()
    
    if not skill_files:
        return False
    
    current_index = {}
    if INDEX_JSON.exists():
        try:
            with open(INDEX_JSON, "r", encoding="utf-8") as f:
                current_index = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    
    current_resources = {r["name"]: r for r in current_index.get("resources", [])}
    new_resources = {}
    
    for skill_file in skill_files:
        skill_name = skill_file.replace(".skill", "")
        description = SKILL_DESCRIPTIONS.get(
            skill_name, 
            f"VANTAGE Skill: {skill_name}"
        )
        
        new_resources[skill_name] = {
            "uri": f"{BASE_URL}/{skill_file}",
            "name": skill_name,
            "description": description,
            "mimeType": "application/octet-stream"
        }
    
    # Detecta si algo cambió
    if set(current_resources.keys()) == set(new_resources.keys()):
        if all(current_resources.get(k) == v for k, v in new_resources.items()):
            return False
    
    if dry_run:
        print(f"📝 index.json se actualizaría ({len(new_resources)} skills)")
        return True

    new_index = {
        "resources": sorted(
            new_resources.values(), 
            key=lambda x: x["name"]
        )
    }
    
    with open(INDEX_JSON, "w", encoding="utf-8") as f:
        json.dump(new_index, f, indent=2, ensure_ascii=False)
    
    print(f"✏️  index.json actualizado ({len(new_resources)} skills)")
    return True


def current_branch() -> str:
    """Rama activa del repo.

    Antes sync() commiteaba en la rama activa pero pusheaba el BRANCH fijo
    ("main"): cualquier trabajo en otra rama quedaba commiteado localmente SIN
    publicar y el script reportaba "✅ L4 Sync OK".
    """
    code, out, _ = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], timeout=10)
    if code == 0 and out and out != "HEAD":  # HEAD = detached HEAD → fallback
        return out
    return BRANCH


def has_changes() -> bool:
    code, out, err = run(["git", "status", "--porcelain"], timeout=10)
    if code != 0:
        raise GitError(err or "git status falló (¿repo inexistente o corrupto?)")
    return bool(out)


def get_changed_files() -> list[str]:
    _, out, _ = run(["git", "status", "--porcelain"], timeout=10)
    return [line.strip() for line in out.splitlines() if line.strip()]


def sync(dry_run: bool = False) -> dict:
    try:
        # Paso 1: Regenera index.json si hay cambios en /skills/
        # (en dry-run solo se calcula; no se escribe nada en disco)
        index_updated = regenerate_index_json(dry_run=dry_run)
        
        # Paso 2: Detecta cambios en git
        changed_flag = has_changes()

        # Paso 3: Rama activa — se commitea y se pushea la MISMA rama
        branch = current_branch()
    except GitError as e:
        return {"status": "error", "step": "git status", "error": str(e)}
    
    if not changed_flag and not index_updated:
        return {"status": "clean", "branch": branch, "message": "No hay cambios — nada que commitear."}

    changed = get_changed_files()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    msg = f"auto-sync: {timestamp} ({len(changed)} archivo(s))"

    if dry_run:
        return {
            "status": "dry_run", 
            "would_commit": msg, 
            "files": changed,
            "index_updated": index_updated,
            "branch": branch,
        }

    code, _, err = run(["git", "add", "-A"], timeout=15)
    if code != 0:
        return {"status": "error", "step": "git add", "error": err}

    code, out, err = run(["git", "commit", "-m", msg], timeout=15)
    if code != 0:
        return {"status": "error", "step": "git commit", "error": err or out}

    # Timeout extendido (30s) para llamadas de red (git push).
    # HEAD:refs/heads/<branch> publica la rama activa real (antes: BRANCH fijo).
    code, out, err = run(["git", "push", "origin", f"HEAD:refs/heads/{branch}"], timeout=30)
    if code != 0:
        return {"status": "error", "step": "git push", "error": err or out, "branch": branch}

    return {
        "status": "ok",
        "commit_message": msg,
        "files_committed": len(changed),
        "files": changed,
        "index_updated": index_updated,
        "branch": branch,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VANTAGE L4 Git Auto-Sync + MCP Server Update")
    parser.add_argument("--dry-run", "--dry", action="store_true", help="Ver cambios sin commitear")
    args = parser.parse_args()

    result = sync(dry_run=args.dry_run)

    if result["status"] == "clean":
        print(result["message"])
        sys.exit(0)
    elif result["status"] == "ok":
        msg = (f"✅ L4 Sync OK — {result['files_committed']} archivo(s) "
               f"commiteados en {result.get('branch', BRANCH)}")
        if result.get("index_updated"):
            msg += " (index.json actualizado)"
        print(msg)
        print(f"   {result['commit_message']}")
        sys.exit(0)
    elif result["status"] == "dry_run":
        print(f"DRY RUN — auto-sync: {result['would_commit']} (rama {result.get('branch', BRANCH)})")
        if result.get("index_updated"):
            print("  📝 index.json será actualizado")
        for f in result["files"]:
            print(f"  {f}")
        sys.exit(0)
    else:
        print(f"❌ Error en {result['step']}: {result['error']}", file=sys.stderr)
        sys.exit(1)
