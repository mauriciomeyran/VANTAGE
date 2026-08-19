#!/usr/bin/env python3
"""
VANTAGE — Compilador de Skills
Genera un único archivo markdown con todas las skills del repositorio.

Uso:
  python compile_skills.py [--output <ruta>] [--skills-dir <ruta>]

Por defecto:
  - skills-dir: ./skills (relativo al directorio donde se ejecuta)
  - output: ./VANTAGE_SKILLS_COMPILED.md
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# ──────────────────────────────────────────────────────────────
# CONFIGURABLE
# ──────────────────────────────────────────────────────────────

DEFAULT_SKILLS_DIR = Path("/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/skills")
DEFAULT_OUTPUT = Path("/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/VANTAGE_SKILLS_COMPILED.md")

# ──────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────

def find_skill_files(skills_dir: Path) -> list[Path]:
    """
    Encuentra todos los SKILL.md dentro de skills_dir, incluyendo subcarpetas.
    Orden: alfabé�ıco por ruta completa.
    """
    skill_files = sorted(skills_dir.rglob("SKILL.md"))
    return skill_files

def read_skill_file(path: Path) -> str:
    """Lee el contenido de un archivo SKILL.md."""
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return f"[ERROR leyendo {path}: {e}]"

def generate_header() -> str:
    """Genera el encabezado del archivo compilado."""
    return f"""# VANTAGE — SKILLS LIBRARY (COMPILADO)

**Generado:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")}
**Fuente:** {DEFAULT_SKILLS_DIR}
**VersiÃ³n del script:** 1.0.0

---

## ÃNDICE

"""

def generate_toc(skill_files: list[Path], skills_dir: Path) -> str:
    """Genera una tabla de contenidos con enlaces ancla."""
    toc_lines = []
    for i, skill_path in enumerate(skill_files, start=1):
        # Nombre legible: ruta relativa sin el sufijo SKILL.md
        rel_path = skill_path.relative_to(skills_dir)
        # Convertir a slug para ancla: reemplazar espacios y caracteres especiales
        slug = (
            str(rel_path.parent)
            .lower()
            .replace(" ", "-")
            .replace("/", "-")
            .replace("-", "-")
        )
        skill_name = rel_path.parent.name
        toc_lines.append(f"{i}. [{skill_name}](#{slug})")
    return "\n".join(toc_lines) + "\n\n---\n\n"

def generate_content(skill_files: list[Path], skills_dir: Path) -> str:
    """Genera el contenido compilado de todas las skills."""
    content_parts = []
    for skill_path in skill_files:
        rel_path = skill_path.relative_to(skills_dir)
        slug = (
            str(rel_path.parent)
            .lower()
            .replace(" ", "-")
            .replace("/", "-")
        )
        skill_name = rel_path.parent.name
        content = read_skill_file(skill_path)
        
        # Encabezado de cada skill
        header = f"## {skill_name}\n\n"
        header += f"**Ruta:** `{rel_path}`\n\n"
        header += "---\n\n"
        
        content_parts.append(header + content + "\n\n---\n\n")
    
    return "".join(content_parts)

# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Compila todas las skills de VANTAGE en un solo markdown.")
    parser.add_argument("--skills-dir", type=Path, default=DEFAULT_SKILLS_DIR, help="Directorio de skills")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Archivo de salida")
    args = parser.parse_args()
    
    skills_dir = args.skills_dir
    output_file = args.output
    
    if not skills_dir.exists():
        print(f"ERROR: El directorio de skills no existe: {skills_dir}")
        sys.exit(1)
    
    print(f"Buscando skills en: {skills_dir}")
    skill_files = find_skill_files(skills_dir)
    
    if not skill_files:
        print("No se encontraron archivos SKILL.md")
        sys.exit(1)
    
    print(f"Encontradas {len(skill_files)} skills:")
    for sf in skill_files:
        print(f"  - {sf.relative_to(skills_dir)}")
    
    print(f"\nGenerando archivo compilado: {output_file}")
    
    # Construir contenido
    header = generate_header()
    toc = generate_toc(skill_files, skills_dir)
    content = generate_content(skill_files, skills_dir)
    
    full_content = header + toc + content
    
    # Escribir archivo
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(full_content, encoding="utf-8")
    
    print(f"â¡¡CompilaciÃ³n completada! {len(skill_files)} skills escritas en {output_file}")

if __name__ == "__main__":
    main()