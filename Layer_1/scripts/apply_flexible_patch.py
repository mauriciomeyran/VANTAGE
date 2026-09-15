import re

path = 'layer_1_orchestrator.py'

with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

helpers = '''
def _to_str(val):
    if val is None:
        return None
    if hasattr(val, 'value'):
        return str(val.value)
    if hasattr(val, 'name'):
        return str(val.name)
    return str(val)

def _notion_select(val, *args, **kwargs):
    # Toma el valor principal sin importar si se envían argumentos adicionales
    s = _to_str(val)
    if not s or not s.strip():
        return {"select": None}
    return {"select": {"name": s.strip()}}

def _notion_status(val, *args, **kwargs):
    # Toma el valor principal sin importar si se envían argumentos adicionales
    s = _to_str(val)
    if not s or not s.strip():
        return {"status": None}
    return {"status": {"name": s.strip()}}
'''

payload_patches = [
    (r'"Next_Action":\s*([^,\}\n]+)', r'"Next_Action": _notion_select(\1)'),
    (r'"Fetch":\s*([^,\}\n]+)', r'"Fetch": _notion_select(\1)'),
    (r'"Gate_Decision":\s*([^,\}\n]+)', r'"Gate_Decision": _notion_select(\1)'),
    (r'"Dedup_Flag":\s*([^,\}\n]+)', r'"Dedup_Flag": _notion_select(\1)'),
    (r'"Status":\s*([^,\}\n]+)', r'"Status": _notion_status(\1)')
]

for pattern, repl in payload_patches:
    code = re.sub(pattern, repl, code)

new_code = helpers + "\n" + code

with open(path, 'w', encoding='utf-8') as f:
    f.write(new_code)

print("✅ Parche flexible aplicado correctamente.")
