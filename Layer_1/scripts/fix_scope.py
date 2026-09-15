import re

path = 'layer_1_orchestrator.py'

with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Definición clara de las funciones helper
helpers_code = '''
def _to_str(val):
    if val is None:
        return None
    if hasattr(val, 'value'):
        return str(val.value)
    if hasattr(val, 'name'):
        return str(val.name)
    return str(val)

def _notion_select(val):
    s = _to_str(val)
    return {"select": {"name": s}} if s and s.strip() else {"select": None}

def _notion_status(val):
    s = _to_str(val)
    return {"status": {"name": s}} if s and s.strip() else {"status": None}
'''

# 2. Limpiar duplicados previos si existían
code = code.replace("def _notion_select", "# def _notion_select")
code = code.replace("def _notion_status", "# def _notion_status")

# 3. Insertar las funciones justo después de las importaciones principales
import_index = code.rfind("import ")
if import_index != -1:
    end_of_imports = code.find("\n", import_index)
    code = code[:end_of_imports] + "\n" + helpers_code + "\n" + code[end_of_imports:]
else:
    code = helpers_code + "\n" + code

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("✅ Funciones de ayuda reubicadas correctamente.")
