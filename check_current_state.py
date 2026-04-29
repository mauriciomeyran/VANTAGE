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
    if t == 'select' and prop.get('select'): 
        return prop['select']['name']
    if t == 'title' and prop.get('title'): 
        return prop['title'][0]['plain_text']
    return ''

print('🔍 Verificando estado ACTUAL de las entradas protegidas:')
print('=' * 60)

target_companies = ['Gap Inc.', 'Innovasport', 'Pandora']

for item in items:
    props = item['properties']
    marca = txt(props.get('Marca'))
    action = txt(props.get('Next_Action'))
    gate = txt(props.get('Gate_Decision'))
    rol = txt(props.get('Rol'))
    
    if marca in target_companies:
        print(f'📌 {marca} ({rol}):')
        print(f'   Next_Action: {action}')
        print(f'   Gate_Decision: {gate}')
        print(f'   ID: {item["id"][:8]}...')
        print('-' * 40)
