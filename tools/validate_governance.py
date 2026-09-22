#!/usr/bin/env python3
"""
validate_governance.py — Lint de gobernanza VANTAGE
Valida JSON sin duplicados, paridad triggers↔skills, y referencias SP:*/KERNEL:* 
que de verdad existan en la documentación viva.

Uso:
    python validate_governance.py                    # Valida todo
    python validate_governance.py --check json       # Solo JSON duplicados
    python validate_governance.py --check parity     # Solo paridad triggers↔skills
    python validate_governance.py --check refs       # Solo referencias documentales

Referencia: §3.2, patrón de drift recurrente (Handoff HO-000062 P7)
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
_TRIGGERS_JSON = _REPO_ROOT / "skills" / "triggers.json"
_REGISTRY_JSON = _REPO_ROOT / "Layer_1" / "data" / "resolver_registry_v2.json"
_SKILLS_DIR = _REPO_ROOT / "skills"
_DOCS_DIR = _REPO_ROOT / "Documentación" / "ACTIVE"
_SCRIPTS_DIRS = [
    _REPO_ROOT / "Layer_1" / "scripts",
    _REPO_ROOT / "tools",
    _REPO_ROOT / "Dashboard" / "scripts",
]


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> dict:
    """Carga JSON con manejo de errores."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"[ERROR] Archivo no encontrado: {path}")
        return {}
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON inválido en {path}: {e}")
        return {}


def _find_python_files(directories: List[Path]) -> List[Path]:
    """Encuentra todos los archivos .py en los directorios dados."""
    py_files = []
    for directory in directories:
        if directory.exists():
            py_files.extend(directory.rglob("*.py"))
    return py_files


def _extract_document_references(content: str) -> Set[str]:
    """
    Extrae referencias documentales del formato SP:* y KERNEL:*.
    Patrón: SP:XXXX, KERNEL:XXXX, MANUAL:XXXX, CANON:XXXX, ALIASES:XXXX, etc.
    """
    pattern = r'\b[A-Z]+:[A-Z0-9_-]+\b'
    matches = re.findall(pattern, content)
    # Filtrar solo prefijos documentales comunes
    doc_prefixes = {"SP", "KERNEL", "MANUAL", "ALIASES", "BRIEF", "TRACKER", "CHANGELOG", "VANTAGE"}
    # Excluir CANON porque es un documento, no secciones (sus secciones son internas)
    refs = {m for m in matches if m.split(":")[0] in doc_prefixes}
    # Excluir placeholders XXXX y X (single char)
    return {r for r in refs if "XXXX" not in r and not r.endswith(":X")}


# ---------------------------------------------------------------------------
# Check 1: JSON sin duplicados
# ---------------------------------------------------------------------------

def check_json_duplicates() -> List[Tuple[str, str, List[str]]]:
    """
    Valida que los archivos JSON no tengan claves duplicadas.
    
    Returns:
        Lista de (archivo, tipo_error, lista_claves_duplicadas)
    """
    issues = []
    
    # Check triggers.json
    triggers_data = _load_json(_TRIGGERS_JSON)
    if triggers_data:
        # Parsear manualmente para detectar duplicados (json.loads los sobrescribe silenciosamente)
        try:
            raw_text = _TRIGGERS_JSON.read_text(encoding="utf-8")
            # Contar ocurrencias de cada clave en el texto crudo
            for skill_name in triggers_data.get("skills", {}).keys():
                pattern = f'"{skill_name}"'
                count = raw_text.count(pattern)
                if count > 1:
                    issues.append((str(_TRIGGERS_JSON), "duplicated_key", [skill_name]))
        except Exception as e:
            print(f"[WARN] No se pudo verificar duplicados en triggers.json: {e}")
    
    # Check resolver_registry_v2.json
    registry_data = _load_json(_REGISTRY_JSON)
    if registry_data:
        try:
            raw_text = _REGISTRY_JSON.read_text(encoding="utf-8")
            # Verificar clave duplicada conocida: CHANGELOG_ARCHIVO
            if 'CHANGELOG_ARCHIVO' in raw_text:
                count = raw_text.count('"CHANGELOG_ARCHIVO"')
                if count > 1:
                    issues.append((str(_REGISTRY_JSON), "duplicated_key", ["CHANGELOG_ARCHIVO"]))
        except Exception as e:
            print(f"[WARN] No se pudo verificar duplicados en registry: {e}")
    
    return issues


# ---------------------------------------------------------------------------
# Check 2: Paridad triggers↔skills
# ---------------------------------------------------------------------------

def check_triggers_skills_parity() -> List[Tuple[str, str, List[str]]]:
    """
    Valida paridad entre triggers.json y archivos .md en skills/.
    
    Returns:
        Lista de (archivo, tipo_error, lista_nombres)
    """
    issues = []
    
    # Cargar triggers.json
    triggers_data = _load_json(_TRIGGERS_JSON)
    if not triggers_data:
        return issues
    
    skills_in_json = set(triggers_data.get("skills", {}).keys())
    
    # Obtener archivos .md en skills/
    skills_files = set()
    if _SKILLS_DIR.exists():
        for md_file in _SKILLS_DIR.glob("*.md"):
            # Normalizar nombre: vantage-cv-b.md -> vantage-cv-b
            skill_name = md_file.stem
            skills_files.add(skill_name)
    
    # Skills en JSON pero sin archivo .md
    missing_files = skills_in_json - skills_files
    if missing_files:
        issues.append((str(_TRIGGERS_JSON), "skill_in_json_no_file", sorted(missing_files)))
    
    # Archivos .md pero no en JSON
    orphan_files = skills_files - skills_in_json
    if orphan_files:
        issues.append((str(_SKILLS_DIR), "file_not_in_json", sorted(orphan_files)))
    
    return issues


# ---------------------------------------------------------------------------
# Check 3: Referencias documentales
# ---------------------------------------------------------------------------

def check_document_references() -> List[Tuple[str, str, List[str]]]:
    """
    Valida que las referencias SP:*/KERNEL:* citadas por código realmente existan
    en la documentación viva (Documentación/ACTIVE/).
    
    Returns:
        Lista de (archivo, tipo_error, lista_referencias)
    """
    issues = []
    
    # 1. Extraer referencias de todos los scripts Python
    py_files = _find_python_files(_SCRIPTS_DIRS)
    all_refs: Set[str] = set()
    
    for py_file in py_files:
        try:
            content = py_file.read_text(encoding="utf-8")
            refs = _extract_document_references(content)
            all_refs.update(refs)
        except Exception as e:
            print(f"[WARN] No se pudo leer {py_file}: {e}")
    
    # 2. Cargar documentación viva (mirrors .md)
    doc_files = {}
    if _DOCS_DIR.exists():
        for md_file in _DOCS_DIR.glob("*.md"):
            doc_name = md_file.stem.upper()
            doc_files[doc_name] = md_file
    
    # 3. Verificar cada referencia
    for ref in all_refs:
        prefix, key = ref.split(":", 1)
        
        # Verificar que el documento base exista
        doc_file = doc_files.get(prefix)
        if not doc_file:
            issues.append(("documentacion", "missing_document", [ref]))
            continue
        
        # Verificar que la sección exista en el documento
        try:
            doc_content = doc_file.read_text(encoding="utf-8")
            # Buscar la sección en varios formatos:
            # 1. ## §XX — KEY (con número de sección)
            # 2. ## KEY (heading simple)
            # 3. # KEY (heading nivel 1)
            # 4. KEY en cualquier heading
            section_patterns = [
                rf'## §\d+[\s—-]+{re.escape(key)}',
                rf'## {re.escape(key)}\b',
                rf'# {re.escape(key)}\b',
                rf'#{1,3} .*{re.escape(key)}\b'
            ]
            
            found = False
            for pattern in section_patterns:
                if re.search(pattern, doc_content, re.IGNORECASE):
                    found = True
                    break
            
            if not found:
                issues.append((str(doc_file), "missing_section", [ref]))
        except Exception as e:
            print(f"[WARN] No se pudo verificar ref {ref} en {doc_file}: {e}")
    
    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="VANTAGE Governance Lint — valida JSON, paridad triggers↔skills, y referencias documentales",
        epilog="Ejemplos:\n"
               "  python validate_governance.py                    # Valida todo\n"
               "  python validate_governance.py --check json       # Solo JSON duplicados\n"
               "  python validate_governance.py --check parity     # Solo paridad triggers↔skills\n"
               "  python validate_governance.py --check refs       # Solo referencias documentales",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--check",
        choices=["json", "parity", "refs", "all"],
        default="all",
        help="Tipo de validación a ejecutar (default: all)"
    )
    
    args = parser.parse_args()
    
    all_issues = []
    
    # Ejecutar checks según selección
    if args.check in ["json", "all"]:
        print("[CHECK] Validando JSON sin duplicados...")
        json_issues = check_json_duplicates()
        all_issues.extend(json_issues)
        if not json_issues:
            print("  ✓ JSON duplicados: OK")
        else:
            print(f"  ✗ JSON duplicados: {len(json_issues)} issues")
    
    if args.check in ["parity", "all"]:
        print("[CHECK] Validando paridad triggers↔skills...")
        parity_issues = check_triggers_skills_parity()
        all_issues.extend(parity_issues)
        if not parity_issues:
            print("  ✓ Paridad triggers↔skills: OK")
        else:
            print(f"  ✗ Paridad triggers↔skills: {len(parity_issues)} issues")
    
    if args.check in ["refs", "all"]:
        print("[CHECK] Validando referencias documentales...")
        ref_issues = check_document_references()
        all_issues.extend(ref_issues)
        if not ref_issues:
            print("  ✓ Referencias documentales: OK")
        else:
            print(f"  ✗ Referencias documentales: {len(ref_issues)} issues")
    
    # Reportar resultados
    print("\n" + "=" * 60)
    if not all_issues:
        print("✓ TODAS LAS VALIDACIONES PASARON")
        return 0
    else:
        print(f"✗ {len(all_issues)} ISSUES ENCONTRADOS:")
        print("=" * 60)
        
        for archivo, error_type, items in all_issues:
            print(f"\n[{error_type.upper()}] {archivo}")
            for item in items:
                print(f"  - {item}")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())