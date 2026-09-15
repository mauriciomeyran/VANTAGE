import re

path = 'layer_1_orchestrator.py'

with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# Funciones de ayuda para extraer valores y formatear para Notion
helpers = '''
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

if '_notion_select' not in code:
    code = helpers + '\n' + code

# Parchear propiedades para Notion
payload_patches = [
    (r'"Next_Action":\s*([^,\}\n]+)', r'"Next_Action": _notion_select(\1)'),
    (r'"Fetch":\s*([^,\}\n]+)', r'"Fetch": _notion_select(\1)'),
    (r'"Gate_Decision":\s*([^,\}\n]+)', r'"Gate_Decision": _notion_select(\1)'),
    (r'"Dedup_Flag":\s*([^,\}\n]+)', r'"Dedup_Flag": _notion_select(\1)'),
    (r'"Status":\s*([^,\}\n]+)', r'"Status": _notion_status(\1)')
]

for pattern, repl in payload_patches:
    code = re.sub(pattern, repl, code)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("✅ Script parcheado con éxito.")
