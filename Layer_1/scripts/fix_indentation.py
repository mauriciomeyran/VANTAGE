path = 'layer_1_orchestrator.py'

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Clean out any previously injected broken helpers
clean_lines = [l for l in lines if not any(k in l for k in ['def _to_str', 'def _notion_select', 'def _notion_status', '_notion_select', '_notion_status']) or '_notion_select(' in l]

helpers = """
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
    if not s or not s.strip():
        return {"select": None}
    return {"select": {"name": s.strip()}}

def _notion_status(val):
    s = _to_str(val)
    if not s or not s.strip():
        return {"status": None}
    return {"status": {"name": s.strip()}}
"""

content = "".join(clean_lines)

# Insert clean helpers at top level after imports
import_pos = content.rfind("import ")
if import_pos != -1:
    line_end = content.find("\n", import_pos)
    new_content = content[:line_end+1] + helpers + "\n" + content[line_end+1:]
else:
    new_content = helpers + "\n" + content

with open(path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Indentación corregida y helpers limpios.")
