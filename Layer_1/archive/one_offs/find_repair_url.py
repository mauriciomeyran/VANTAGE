import os
from dotenv import load_dotenv
from notion_client import Client

load_dotenv(dotenv_path=os.path.abspath('.env'), override=True)
client = Client(auth=os.environ['NOTION_TOKEN'])
ds_id = '4e542b37-6e52-4418-89b7-a0eeb3138307'

items = client.data_sources.query(data_source_id=ds_id)['results']

def txt(prop):
    if not prop: return ''
    t = prop.get('type')
    if t == 'rich_text' and prop.get('rich_text'): 
        return prop['rich_text'][0]['plain_text']
    if t == 'select' and prop.get('select'): 
        return prop['select']['name']
    if t == 'title' and prop.get('title'): 
        return prop['title'][0]['plain_text']
    return ''

print('🔍 Buscando entradas con Next_Action: Reparar URL')
print('=' * 60)

for item in items:
    props = item['properties']
    action = txt(props.get('Next_Action'))
    status = txt(props.get('Status'))
    fetch = txt(props.get('Fetch'))
    rol = txt(props.get('Rol'))
    marca = txt(props.get('Marca'))
    
    if action == 'Reparar URL':
        print(f'📌 ID: {item["id"][:8]}...')
        print(f'   Rol: {rol}')
        print(f'   Marca: {marca}')
        print(f'   Status: {status}')
        print(f'   Fetch: {fetch}')
        print(f'   Next_Action: {action}')
        print('-' * 40)
