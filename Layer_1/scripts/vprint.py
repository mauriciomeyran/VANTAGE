import os
from notion_client import Client

notion = Client(auth=os.environ.get("NOTION_TOKEN"))
database_id = os.environ.get("NOTION_DB_OPPORTUNITIES")

# Obtener data_source_id desde database_id (API v2025-09-03)
database_info = notion.databases.retrieve(database_id)
data_source_id = database_info['data_sources'][0]['id']

response = notion.data_sources.query(
    data_source_id=data_source_id,
    filter={
        "property": "Gate_Decision",
        "select": {
            "equals": "CREATE"
        }
    }
)

print(f"Total vacantes encontradas: {len(response['results'])}")
for page in response["results"]:
    print(f"ID: {page['id']} | URL: {page['url']}")
