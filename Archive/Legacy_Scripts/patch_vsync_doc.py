#!/usr/bin/env python3
"""
Patcher para vsync_doc.py
Reemplaza la entrada 'cheat_sheet' en DOCS por dos entradas separadas:
'aliases' y 'change_log'.
Uso: python3 patch_vsync_doc.py
Correr desde Layer_4/scripts/ (mismo directorio que vsync_doc.py)
"""
import ast
import py_compile
from pathlib import Path

TARGET = Path("vsync_doc.py")

OLD = '''    "cheat_sheet":   {"notion_id": "37c938be-fc42-80d4-b9ae-f5969830331b", "local_file": BASE_DIR / "Cheat Sheet & Change Log.md", "label": "CHEAT SHEET"},'''

NEW = '''    "aliases":       {"notion_id": "37c938be-fc42-80d4-b9ae-f5969830331b", "local_file": BASE_DIR / "Aliases.md", "label": "ALIASES"},
    "change_log":    {"notion_id": "390938be-fc42-80e7-b429-d7d730339353", "local_file": BASE_DIR / "Change Log.md", "label": "CHANGE LOG"},'''

def main():
    assert TARGET.exists(), f"No se encontró {TARGET} en el directorio actual"
    src = TARGET.read_text(encoding="utf-8")

    assert OLD in src, "old_str no encontrado — el archivo pudo haber cambiado. Abortando sin escribir."
    assert src.count(OLD) == 1, "old_str aparece más de una vez — ambiguo, abortando."

    patched = src.replace(OLD, NEW)

    # Validar sintaxis antes de escribir
    ast.parse(patched)

    backup = TARGET.with_suffix(".py.bak")
    backup.write_text(src, encoding="utf-8")
    TARGET.write_text(patched, encoding="utf-8")

    py_compile.compile(str(TARGET), doraise=True)

    print(f"✓ Patch aplicado. Backup en {backup}")
    print("✓ Sintaxis validada (ast.parse + py_compile)")
    print("\nVerifica con: grep -A2 'aliases\\|change_log' vsync_doc.py")

if __name__ == "__main__":
    main()
