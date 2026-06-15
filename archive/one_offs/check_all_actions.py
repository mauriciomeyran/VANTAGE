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
    if t == 'rich_text' and prop.get('rich_text'): 
        return prop['rich_text'][0]['plain_text']
    return ''

print('🔍 Todas las entradas con Next_Action:')
print('=' * 60)

for item in items:
    props = item['properties']
    marca = txt(props.get('Marca'))
    action = txt(props.get('Next_Action'))
    gate = txt(props.get('Gate_Decision'))
    rol = txt(props.get('Rol'))
    
    print(f'{marca}: {action} (Gate: {gate})')
