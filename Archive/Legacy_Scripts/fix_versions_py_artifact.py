import requests, os
from dotenv import load_dotenv

load_dotenv('config/layer_1.env')
token = os.getenv('NOTION_TOKEN') or os.getenv('NOTION_API_KEY')
headers = {
    'Authorization': f'Bearer {token}',
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json',
}

PAGE_ID = '37b938be-fc42-8001-9b9b-fcf81130d274'  # System Prompt
BROKEN_URL_PREFIX = 'http://versions.py'

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

def fix_block(block):
    btype = block['type']
    if btype not in block or 'rich_text' not in block[btype]:
        return False
    rich_text = block[btype]['rich_text']
    changed = False
    new_rich_text = []
    for seg in rich_text:
        link = seg.get('text', {}).get('link')
        if link and link.get('url', '').startswith(BROKEN_URL_PREFIX):
            # Reconstruye el segmento como texto plano "verify_versions.py",
            # sin el campo link roto. Preserva anotaciones de estilo si las hay.
            fixed_content = seg['text']['content'].replace('versions.py', 'verify_versions.py') \
                if 'verify_' not in seg['text']['content'] else seg['text']['content']
            # El texto visible del link normalmente es solo "versions.py"
            # (el "verify_" queda en el segmento anterior como texto plano) —
            # así que el fix real es: texto = "versions.py", sin link.
            new_seg = {
                "type": "text",
                "text": {"content": seg['text']['content']},
                "annotations": seg.get('annotations', {}),
            }
            new_rich_text.append(new_seg)
            changed = True
        else:
            new_rich_text.append(seg)
    if not changed:
        return False

    payload = {btype: {"rich_text": new_rich_text}}
    resp = requests.patch(f'https://api.notion.com/v1/blocks/{block["id"]}',
                           headers=headers, json=payload)
    ok = resp.status_code == 200
    print(f"  [{'OK' if ok else 'FAIL'}] block {block['id']} ({btype})"
          + ("" if ok else f" — {resp.status_code} {resp.text[:150]}"))
    return ok

def main():
    print(f"Buscando spans rotos con link.url que empiece con {BROKEN_URL_PREFIX!r} en System Prompt...\n")
    blocks = fetch_blocks_recursive(PAGE_ID)
    found = 0
    fixed = 0
    for b in blocks:
        btype = b['type']
        if btype in b and 'rich_text' in b[btype]:
            for seg in b[btype]['rich_text']:
                link = seg.get('text', {}).get('link')
                if link and link.get('url', '').startswith(BROKEN_URL_PREFIX):
                    found += 1
                    print(f"Encontrado en bloque {b['id']} ({btype}): {seg['text']['content']!r}")
                    if fix_block(b):
                        fixed += 1
                    break
    print(f"\nTotal encontrados: {found} | Corregidos: {fixed}")

if __name__ == '__main__':
    main()
