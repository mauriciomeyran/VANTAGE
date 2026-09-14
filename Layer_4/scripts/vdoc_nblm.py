#!/usr/bin/env python3
"""
vdoc_nblm.py — VANTAGE
Sincroniza docs fundacionales (vdoc notion) + digest de GitHub
y los sube como fuentes al NotebookLM gratuito fijo.

Uso:
  python vdoc_nblm.py                  # reutiliza sesión si es válida
  python vdoc_nblm.py --login          # fuerza abrir browser (login + llave de acceso)
  python vdoc_nblm.py --dry-run
  python vdoc_nblm.py --no-vdoc        # salta sync de Notion
  python vdoc_nblm.py --no-digest      # no descarga el ingest
"""

import argparse
import asyncio
import subprocess
import sys
from pathlib import Path

# ── Rutas VANTAGE ────────────────────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT = _SCRIPT_DIR.parents[1]          # VANTAGE root
ACTIVE_DIR = _PROJECT / "Documentación" / "ACTIVE"
DIGEST_PATH = _PROJECT / "VANTAGE_digest.txt"   # ajusta si tu get_vantage_digest.sh usa otra ruta

NOTEBOOK_ID = "120cc3d6-a2c0-4c2e-ae4c-a794e1fc7f30"

def run_vdoc_notion():
    """Ejecuta el equivalente a `vdoc notion`."""
    print("→ Ejecutando vdoc notion (Notion → ACTIVE)...")
    # Opción A: llamar al wrapper existente
    # subprocess.run([sys.executable, str(_SCRIPT_DIR / "vdoc.py"), "notion"], check=True)
    # Opción B: llamar directamente vsync_doc
    subprocess.run(
        [sys.executable, str(_SCRIPT_DIR / "vsync_doc.py"), "--direction", "notion"],
        check=True,
        cwd=_SCRIPT_DIR,
    )
    print("✓ Documentos fundacionales actualizados en ACTIVE/")

def run_digest():
    """Descarga el ingest de GitHub."""
    print("→ Descargando digest de GitHub (gitingest)...")
    # Ajusta según tu get_vantage_digest.sh real
    script = _SCRIPT_DIR / "get_vantage_digest.sh"
    if script.exists():
        subprocess.run(["bash", str(script), str(DIGEST_PATH)], check=True)
    else:
        # fallback directo
        import urllib.request
        url = "https://gitingest.com/raw/mauriciomeyran/VANTAGE"
        urllib.request.urlretrieve(url, DIGEST_PATH)
    print(f"✓ Digest guardado en {DIGEST_PATH}")

def collect_files(include_digest: bool = True) -> list[Path]:
    files = []
    if ACTIVE_DIR.exists():
        files.extend(sorted(ACTIVE_DIR.glob("*.md")))
    else:
        print(f"  ⚠ Directorio no encontrado: {ACTIVE_DIR}")
    if include_digest and DIGEST_PATH.exists():
        files.append(DIGEST_PATH)
    return files

async def upload_to_notebook(files: list[Path], force_login: bool = False):
    """Sube los archivos al notebook fijo usando notebooklm-py."""
    try:
        from notebooklm import NotebookLMClient
    except ImportError:
        print("ERROR: instala notebooklm-py →  pip install 'notebooklm-py[browser]'")
        sys.exit(1)

    if force_login:
        print("→ Abriendo browser para login (usa tu llave de acceso si es necesario)...")
        subprocess.run(["notebooklm", "login"], check=False)

    print(f"→ Subiendo {len(files)} fuentes al notebook {NOTEBOOK_ID}...")
    async with NotebookLMClient.from_storage() as client:
        for f in files:
            print(f"  • {f.name} ({f.stat().st_size // 1024} KB)")
            # La API exacta puede ser client.sources.add_file(...) o add_local
            # Verifica con: notebooklm source add --help
            await client.sources.add_file(NOTEBOOK_ID, str(f))
    print("✓ Subida completada")

def main():
    parser = argparse.ArgumentParser(description="vdoc + digest → NotebookLM")
    parser.add_argument("--login", action="store_true", help="Fuerza abrir browser para login")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-vdoc", action="store_true", help="Salta sync de Notion")
    parser.add_argument("--no-digest", action="store_true", help="No descarga el digest")
    args = parser.parse_args()

    if not args.no_vdoc:
        run_vdoc_notion()

    if not args.no_digest:
        run_digest()

    files = collect_files(include_digest=not args.no_digest)

    if not files:
        print("No hay archivos para subir.")
        sys.exit(1)

    if args.dry_run:
        print("\n[DRY-RUN] Se subirían estos archivos:")
        for f in files:
            print(f"  - {f}")
        return

    asyncio.run(upload_to_notebook(files, force_login=args.login))

if __name__ == "__main__":
    main()