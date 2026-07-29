import requests, os, json
from dotenv import load_dotenv

load_dotenv('config/layer_1.env')
token = os.getenv('NOTION_TOKEN') or os.getenv('NOTION_API_KEY')
headers = {'Authorization': f'Bearer {token}', 'Notion-Version': '2022-06-28'}

PAGE_ID = '37b938be-fc42-8001-9b9b-fcf81130d274'  # System Prompt

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

def main():
    blocks = fetch_blocks_recursive(PAGE_ID)
    for b in blocks:
        btype = b['type']
        if btype not in b or 'rich_text' not in b.get(btype, {}):
            continue
        rich_text = b[btype]['rich_text']
        full_plain = ''.join(s.get('plain_text', '') for s in rich_text)
        if 'versions.py' in full_plain:
            print(f"=== Bloque {b['id']} ({btype}) ===")
            print(f"plain_text completo: {full_plain!r}")
            print("Segmentos rich_text:")
            for i, seg in enumerate(rich_text):
                link = seg.get('text', {}).get('link')
                print(f"  [{i}] content={seg['text']['content']!r}  link={link}")
            print()

if __name__ == '__main__':
    main()
