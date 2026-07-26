import requests, os
from dotenv import load_dotenv

load_dotenv('config/layer_1.env')
token = os.getenv('NOTION_TOKEN') or os.getenv('NOTION_API_KEY')
headers = {'Authorization': f'Bearer {token}', 'Notion-Version': '2022-06-28'}

page_id = '377938be-fc42-8089-93f2-f52dbd2dec6c'  # Career Canon
url = f'https://api.notion.com/v1/blocks/{page_id}/children'
cursor = None

while True:
    params = {'page_size': 100}
    if cursor:
        params['start_cursor'] = cursor
    r = requests.get(url, headers=headers, params=params)
    data = r.json()
    for b in data.get('results', []):
        if b['type'] == 'heading_2':
            text = ''.join(s['plain_text'] for s in b['heading_2']['rich_text'])
            if 'CANON:' in text:
                print(f"{text}  ->  {b['id']}")
    if data.get('has_more'):
        cursor = data.get('next_cursor')
    else:
        break
