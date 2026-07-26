import requests, os, re
from dotenv import load_dotenv

load_dotenv('config/layer_1.env')
token = os.getenv('NOTION_TOKEN') or os.getenv('NOTION_API_KEY')
headers = {
    'Authorization': f'Bearer {token}',
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json',
}

PAGE_ID = '372938be-fc42-8050-9a67-e40857d7806e'  # Manual
MD_LINK_RE = re.compile(r'\[([^\[\]]+)\]\((https?://[^\s()]+)\)')

def fetch_blocks_recursive(block_id):
    all_blocks = []
    cursor = None
    while True:
        params = {'page_size': 100}
        if cursor:
            params['start_cursor'] = cursor
        r = requests.get(f'https://api.notion.com/v1/blocks/{block_id}/children',
                          headers=headers, params=params)
        data = r.json()
        for b in data.get('results', []):
            all_blocks.append(b)
            if b.get('has_children'):
                all_blocks.extend(fetch_blocks_recursive(b['id']))
        if data.get('has_more'):
            cursor = data['next_cursor']
        else:
            break
    return all_blocks

def rebuild_cell(cell_rich_text):
    """
    Recibe una celda (lista de segmentos rich_text) y devuelve una nueva
    lista donde cualquier segmento cuyo texto plano contenga sintaxis
    markdown cruda [texto](url) se reconstruye como un link real.
    Preserva segmentos que no necesitan cambio.
    """
    changed = False
    new_cell = []
    for seg in cell_rich_text:
        content = seg.get('text', {}).get('content', '')
        if not MD_LINK_RE.search(content):
            new_cell.append(seg)
            continue
        changed = True
        pos = 0
        for m in MD_LINK_RE.finditer(content):
            if m.start() > pos:
                new_cell.append({"type": "text", "text": {"content": content[pos:m.start()]}})
            label, url = m.group(1), m.group(2)
            new_cell.append({"type": "text", "text": {"content": label, "link": {"url": url}}})
            pos = m.end()
        if pos < len(content):
            new_cell.append({"type": "text", "text": {"content": content[pos:]}})
    return new_cell, changed

def main():
    print("Buscando tablas con sintaxis markdown cruda en Manual...\n")
    blocks = fetch_blocks_recursive(PAGE_ID)
    found = 0
    fixed = 0
    for b in blocks:
        if b['type'] != 'table_row':
            continue
        cells = b['table_row']['cells']
        new_cells = []
        row_changed = False
        for cell in cells:
            new_cell, changed = rebuild_cell(cell)
            new_cells.append(new_cell)
            row_changed = row_changed or changed
        if not row_changed:
            continue
        found += 1
        plain_preview = ''.join(
            s.get('text', {}).get('content', '') for cell in cells for s in cell
        )[:80]
        print(f"Encontrado en table_row {b['id']}: {plain_preview!r}...")
        resp = requests.patch(
            f"https://api.notion.com/v1/blocks/{b['id']}",
            headers=headers,
            json={"table_row": {"cells": new_cells}},
        )
        ok = resp.status_code == 200
        print(f"  [{'OK' if ok else 'FAIL'}] {b['id']}" + ("" if ok else f" — {resp.status_code} {resp.text[:150]}"))
        fixed += ok

    print(f"\nTotal filas encontradas: {found} | Corregidas: {fixed}")

if __name__ == '__main__':
    main()
