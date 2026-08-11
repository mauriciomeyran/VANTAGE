from notion_client import Client

from dashboard_config import NOTION_TOKEN
from dashboard_config import DATABASE_ID

from layer_1_run import txt


def get_notion_client():
    return Client(auth=NOTION_TOKEN)


def fetch_notion_page(page_id: str) -> dict:
    client = get_notion_client()

    page = client.pages.retrieve(page_id=page_id)

    props = page['properties']

    return {
        'rol':          txt(props.get('Rol')),
        'marca':        txt(props.get('Marca')),
        'url':          txt(props.get('URL')),
        'source_type':  txt(props.get('Source_Type ')) or txt(props.get('Source_Type')) or 'Vacante',
        'status':       txt(props.get('Status')),
        'prioridad':    txt(props.get('Prioridad')),
        'jd':           txt(props.get('JD')),
        'gate':         txt(props.get('Gate_Decision')),
        'score':        props.get('Score', {}).get('number'),
        'vm_scope':     txt(props.get('VM_Scope')),
        'role_class':   txt(props.get('Role_Class')),
        'fetch':        txt(props.get('Fetch')),
        'next_action':  txt(props.get('Next_Action')),
        'fuente':       txt(props.get('Fuente')),
        'contacto':     txt(props.get('Contacto')),
    }


def query_blocked_vacancies():
    client = get_notion_client()

    return client.data_sources.query(
        data_source_id=DATABASE_ID,
        filter={
            'and': [
                {
                    'property': 'Gate_Decision',
                    'select': {'equals': 'BLOCKED'},
                },
                {
                    'property': 'Status',
                    'select': {'does_not_equal': 'Expirada'},
                },
                {
                    'property': 'Status',
                    'select': {'does_not_equal': 'Retirado'},
                },
                {
                    'property': 'Status',
                    'select': {'does_not_equal': 'Rechazado'},
                },
            ]
        },
    )


def write_patch_to_notion(page_id: str, patch: dict):
    client = get_notion_client()

    # Nombres exactos de propiedad según la Notion REST API
    field_map = {
        'rol':          ('Rol',          'title'),
        'marca':        ('Marca',        'rich_text'),
        'url':          ('URL',          'url'),
        'source_type':  ('Source_Type ', 'select'),   # espacio trailing real en Notion
        'prioridad':    ('Prioridad',    'select'),
        'jd':           ('JD',           'rich_text'),
        'status':       ('Status',       'select'),
        'next_action':  ('Next_Action',  'select'),
        'gate':         ('Gate_Decision','select'),
    }

    properties = {}

    for field, value in patch.items():
        if field not in field_map:
            continue

        notion_field, field_type = field_map[field]

        # None = clear explícito (solo select / url / number)
        if value is None:
            if field_type == 'select':
                properties[notion_field] = {'select': None}
            elif field_type == 'url':
                properties[notion_field] = {'url': None}
            elif field_type == 'number':
                properties[notion_field] = {'number': None}
            # title / rich_text no se limpian con None (evita vaciar contenido accidental)
            continue

        if field_type == 'title':
            properties[notion_field] = {
                'title': [{'text': {'content': str(value)}}]
            }

        elif field_type == 'rich_text':
            properties[notion_field] = {
                'rich_text': [{'text': {'content': str(value)[:2000]}}]
            }

        elif field_type == 'url':
            properties[notion_field] = {'url': str(value)}

        elif field_type == 'select':
            properties[notion_field] = {'select': {'name': str(value)}}

        elif field_type == 'number':
            try:
                properties[notion_field] = {'number': float(value)}
            except (TypeError, ValueError):
                continue

    if not properties:
        return {'success': False, 'error': 'PATCH_EMPTY'}

    # D-002 FIX (GAP-003): Integrar class_b_guard como middleware antes de escritura
    # Importar class_b_guard desde Layer_1/scripts
    import sys, os
    sys.path.insert(0, os.path.expanduser("~/Documents/03 Projects/VANTAGE/Layer_1/scripts"))
    from class_b_guard import guard_write_payload

    # Aplicar guard a las properties antes de enviar a Notion
    guard_result = guard_write_payload(properties, strict_unknown=True)
    if not guard_result.is_clean:
        print(f"[CLASS_B_GUARD] {guard_result.report()}")
        # Fallar fuertemente si hay campos Class B en el payload
        return {'success': False, 'error': 'CLASS_B_BLOCKED'}
    
    # Usar payload limpio
    properties = guard_result.clean_payload

    try:
        client.pages.update(page_id=page_id, properties=properties)
        return {'success': True, 'error': None}

    except Exception as e:
        import traceback
        print(f'[NOTION_WRITE_ERROR] {str(e)}')
        print(traceback.format_exc())
        return {'success': False, 'error': str(e)}
