#!/usr/bin/env python3
"""
Patcher idempotente — inyecta el flag --new-scripts en verify_versions.py

USO:
    python3 patch_new_scripts.py /ruta/a/Layer_1/scripts/verify_versions.py

Qué hace:
1. Crea respaldo verify_versions.py.bak (solo si no existe ya uno).
2. Inserta:
   - Constante GLOSSARY_PATH (ruta al Glosario local, ajustable abajo).
   - Función render_new_scripts_gap_report() — reutiliza scan_committed_assets
     ya existente en el archivo, compara contra el Glosario local (grep de
     nombre de archivo como string), no contra Notion. Cero llamadas MCP.
   - Bloque --new-scripts en argparse + salida temprana en main(), siguiendo
     el mismo patrón que --scripts/--skills.
3. Es idempotente: si ya detecta '--new-scripts' en el archivo, no hace nada
   y avisa.

AJUSTA ANTES DE CORRER si tu Glosario vive en otra ruta:
    GLOSSARY_DEFAULT_REL más abajo (relativo a PROJECT_ROOT del script).
"""
import sys
import shutil
from pathlib import Path

# Ajusta esta ruta si guardas el Glosario en otro lugar dentro del árbol VANTAGE.
# Es relativa a PROJECT_ROOT (VANTAGE/), que verify_versions.py ya calcula como
# SCRIPT_DIR.parent.parent.
GLOSSARY_DEFAULT_REL = "Layer_1/data/script_glossary.md"

CONST_BLOCK = f'''
# Ruta local del Glosario de Scripts (MANUAL:SCRIPT-GLOSSARY, apéndice 22).
# --new-scripts compara contra este archivo, no contra Notion — cero costo MCP.
# Ajustar si el Glosario se mueve de ubicación.
SCRIPT_GLOSSARY_PATH = PROJECT_ROOT / "{GLOSSARY_DEFAULT_REL}"
'''

FUNC_BLOCK = '''
def render_new_scripts_gap_report(extensions: tuple, glossary_path: Path) -> None:
    """Compara assets committeados en disco (árbol activo) contra el Glosario
    de Scripts local (Markdown, MANUAL:SCRIPT-GLOSSARY). 100% local — no llama
    a Notion. Detecta scripts nuevos sin entrada humana documentada, como
    señal de entrada para el skill vantage-sync-script-glossary."""
    disk_scripts = scan_committed_assets(PROJECT_ROOT, extensions)

    if not glossary_path.exists():
        print(f"[-] Error: Glosario no encontrado en {glossary_path}", file=sys.stderr)
        print("    Ajusta SCRIPT_GLOSSARY_PATH en verify_versions.py o coloca el archivo ahí.", file=sys.stderr)
        sys.exit(1)

    glossary_text = glossary_path.read_text(encoding="utf-8")

    missing = []
    documented = []
    for name, rel in disk_scripts:
        # Match simple por nombre de archivo como string literal dentro del
        # Glosario (ej. "`feed_processor.py`"). Suficiente porque el Glosario
        # usa el nombre exacto de archivo como encabezado de cada entrada.
        if name in glossary_text:
            documented.append(name)
        else:
            missing.append((name, rel))

    print("[SCRIPT GLOSSARY — GAP REPORT (local, sin Notion)]")
    print("-" * 60)
    print(f"Assets en árbol activo (disco): {len(disk_scripts)}")
    print(f"Documentados en Glosario: {len(documented)}")
    print("-" * 60)
    print(f"SIN ENTRADA EN GLOSARIO — {len(missing)} encontrados:")
    if not missing:
        print("  (ninguno)")
    for name, rel in sorted(missing):
        print(f"  [-] {name}  ({rel})")
    print("-" * 60)
    print(f"[FIN SCRIPT GLOSSARY — GAP REPORT]")

    # Exit code 1 si hay pendientes — permite usar esto como gate en un skill
    # o automatización (ej. vantage-sync-script-glossary corre solo si esto
    # devuelve distinto de 0).
    if missing:
        sys.exit(1)

'''

ARGPARSE_LINE = '    parser.add_argument("--new-scripts", action="store_true", help="Cruza los scripts .py/.sh del árbol activo contra el Glosario de Scripts LOCAL (MANUAL:SCRIPT-GLOSSARY), sin llamar a Notion. Exit 1 si hay scripts sin documentar — úsalo como gate para vantage-sync-script-glossary.")\n'

DISPATCH_BLOCK = '''
    if args.new_scripts:
        render_new_scripts_gap_report((".py", ".sh"), SCRIPT_GLOSSARY_PATH)
        return

'''

def main():
    if len(sys.argv) != 2:
        print("Uso: python3 patch_new_scripts.py /ruta/a/verify_versions.py", file=sys.stderr)
        sys.exit(1)

    target = Path(sys.argv[1]).resolve()
    if not target.exists():
        print(f"[-] No existe: {target}", file=sys.stderr)
        sys.exit(1)

    text = target.read_text(encoding="utf-8")

    if "--new-scripts" in text:
        print("[=] El archivo ya contiene --new-scripts. Nada que hacer (idempotente).")
        return

    backup = target.with_suffix(target.suffix + ".bak")
    if not backup.exists():
        shutil.copy2(target, backup)
        print(f"[+] Respaldo creado: {backup}")
    else:
        print(f"[=] Respaldo ya existía, no se sobrescribe: {backup}")

    # 1. Insertar constante justo después de la línea PROJECT_ROOT = ...
    anchor_const = 'PROJECT_ROOT = SCRIPT_DIR.parent.parent\n'
    if anchor_const not in text:
        print("[-] No se encontró el anchor de PROJECT_ROOT. Aborta sin modificar.", file=sys.stderr)
        sys.exit(1)
    text = text.replace(anchor_const, anchor_const + CONST_BLOCK, 1)

    # 2. Insertar la función justo antes de 'def render_bootstrap_dump('
    anchor_func = "def render_bootstrap_dump("
    if anchor_func not in text:
        print("[-] No se encontró el anchor de render_bootstrap_dump. Aborta.", file=sys.stderr)
        sys.exit(1)
    text = text.replace(anchor_func, FUNC_BLOCK + anchor_func, 1)

    # 3. Insertar el argparse.add_argument justo después de la línea de --skills
    anchor_arg = None
    for line in text.splitlines(keepends=True):
        if '"--skills"' in line and "add_argument" in line:
            anchor_arg = line
            break
    if not anchor_arg:
        print("[-] No se encontró la línea add_argument de --skills. Aborta.", file=sys.stderr)
        sys.exit(1)
    text = text.replace(anchor_arg, anchor_arg + ARGPARSE_LINE, 1)

    # 4. Insertar el dispatch temprano justo después del bloque de dispatch de --skills
    anchor_dispatch = '''    if args.skills:
        headers = get_notion_headers(token)
        with httpx.Client(timeout=20.0) as client:
            render_scripts_gap_report(client, headers, (".skill",), SKILL_LIBRARY_DATA_SOURCE_ID, "SKILL LIBRARY", title_property="Skill")
        return
'''
    if anchor_dispatch not in text:
        print("[-] No se encontró el bloque de dispatch de --skills exacto. Aborta.", file=sys.stderr)
        print("    (puede que el archivo tenga formato distinto al esperado — revisa manualmente)", file=sys.stderr)
        sys.exit(1)
    text = text.replace(anchor_dispatch, anchor_dispatch + DISPATCH_BLOCK, 1)

    target.write_text(text, encoding="utf-8")
    print(f"[+] Patch aplicado: {target}")
    print("")
    print("Siguiente paso:")
    print(f"  1. Coloca el Glosario local en: <VANTAGE_ROOT>/{GLOSSARY_DEFAULT_REL}")
    print("  2. Corre: python3 verify_versions.py --new-scripts")
    print("  3. Exit code 1 = hay scripts sin documentar (úsalo como gate).")

if __name__ == "__main__":
    main()
