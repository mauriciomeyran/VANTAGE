import re

path = 'layer_1_orchestrator.py'

with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# Helper para convertir Enum o valores complejos a string/None
safe_enum_helper = '''
def _clean_val(v):
    if v is None:
        return None
    if hasattr(v, 'value'):
        return str(v.value)
    if hasattr(v, 'name'):
        return str(v.name)
    return str(v)
'''

# Insertar el helper al inicio
code = safe_enum_helper + "\n" + code

# Reemplazar únicamente los valores de Enums pasados dentro de las estructuras de Notion
# asegurando que siempre se entreguen cadenas de texto a {'name': ...}
code = re.sub(r"'name':\s*([a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+)+)", r"'name': _clean_val(\1)", code)
code = re.sub(r'"name":\s*([a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+)+)', r'"name": _clean_val(\1)', code)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("✅ Parche de tipos aplicado sin romper llaves de diccionario.")
