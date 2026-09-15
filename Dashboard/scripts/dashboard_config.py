import os
from dotenv import load_dotenv

ROOT_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
ENV_PATH = os.path.join(ROOT_DIR, 'config', 'dashboard.env')

load_dotenv(dotenv_path=ENV_PATH, override=True)

NOTION_TOKEN = os.environ['NOTION_TOKEN']
DATABASE_ID = os.environ['NOTION_DB_OPPORTUNITIES']

DB_PATH = os.path.join(ROOT_DIR, 'dashboard_instances.db')

# R-04 fix: 0.0.0.0 exponía el Dashboard (sin auth ni CORS) a toda la red
# local. Default seguro = solo localhost; override explícito vía env si algún
# día se necesita exponerlo (con auth añadida aparte).
HOST = os.environ.get('DASHBOARD_HOST', '127.0.0.1')
PORT = int(os.environ.get('DASHBOARD_PORT', '8000'))
DEBUG = False
