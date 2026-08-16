import os
import json
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# Cargar variables de entorno desde .env si existe
def load_env():
    """Carga variables de entorno desde archivo .env si existe."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- Configuración de Google Drive OAuth 2.0 ---
# Este script usa OAuth 2.0 Desktop con client_secret_...json
# Requiere: pip install google-api-python-client google-auth-oauthlib

# --- Configuración de Rutas Absolutas ---
SKILLS_PATH = Path("/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/skills")
TRIGGERS_PATH = Path("/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/skills/triggers.json")

# --- Configuración de Google Drive ---
GOOGLE_DRIVE_FOLDER = os.environ.get("GOOGLE_DRIVE_FOLDER_SKILLS", "VANTAGE_Skills_Manifest")
TOKEN_FILE = "token_drive.json"  # Para guardar el token de OAuth

DEFAULT_TRIGGERS_TEMPLATES = [
    "ejecuta {skill_name_clean}",
    "activa {skill_name_clean}",
    "{skill_name_clean}"
]

def get_github_raw_url(skill_name, branch="main"):
    """
    Genera la GitHub raw URL para un skill.
    """
    return f"https://raw.githubusercontent.com/mauriciomeyran/VANTAGE/{branch}/skills/{skill_name}/SKILL.md"

def get_skill_metadata(skill_path):
    """
    Extrae metadatos de un skill.
    Intenta leer desde SKILL.md (front-matter o contenido) y usa index.json como fallback.
    """
    skill_name = skill_path.name
    skill_description = f"VANTAGE Skill: {skill_name}"
    last_modified = None
    
    skill_md_path = skill_path / "SKILL.md"
    if skill_md_path.exists():
        try:
            # Get mtime and convert to ISO 8601 format
            mtime = skill_md_path.stat().st_mtime
            last_modified = datetime.fromtimestamp(mtime).isoformat()
            
            with open(skill_md_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                
            in_front_matter = False
            first_content_line = None
            
            for line in lines:
                clean_line = line.strip()
                if clean_line == "---":
                    in_front_matter = not in_front_matter
                    continue
                
                if clean_line.lower().startswith("description:"):
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        skill_description = parts[1].strip().strip('"').strip("'")
                        break
                
                if not in_front_matter and clean_line and first_content_line is None:
                    if not clean_line.startswith("#"):
                        first_content_line = clean_line

            if skill_description == f"VANTAGE Skill: {skill_name}" and first_content_line:
                skill_description = first_content_line
        except Exception as e:
            logger.warning(f"Error leyendo SKILL.md para {skill_name}: {e}")

    if skill_description == f"VANTAGE Skill: {skill_name}":
        index_json_path = skill_path / "index.json"
        if index_json_path.exists():
            try:
                with open(index_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        skill_description = data.get("description", data.get("desc", skill_description))
            except Exception as e:
                logger.warning(f"Error leyendo index.json para {skill_name}: {e}")

    return {
        "name": skill_name,
        "description": skill_description,
        "path": f"skills/{skill_name}/SKILL.md",
        "url": get_github_raw_url(skill_name),
        "last_modified": last_modified
    }

def generate_triggers(skill_name):
    """Genera triggers por defecto basados en los templates configurados."""
    skill_name_clean = skill_name.replace("-", " ")
    triggers = [template.format(skill_name_clean=skill_name_clean) for template in DEFAULT_TRIGGERS_TEMPLATES]
    return list(dict.fromkeys(triggers))

def upload_to_google_drive(file_path: Path) -> bool:
    """Sube el archivo triggers.json a Google Drive usando OAuth 2.0."""
    try:
        from googleapiclient.discovery import build
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.http import MediaFileUpload
        
        # Verificar credenciales OAuth
        credentials_path = os.environ.get("GOOGLE_OAUTH_CREDENTIALS_PATH")
        if not credentials_path or not Path(credentials_path).exists():
            logger.warning("Google Drive OAuth no configurado. Set GOOGLE_OAUTH_CREDENTIALS_PATH para habilitar")
            return False
        
        # Scope necesario para Google Drive
        SCOPES = ['https://www.googleapis.com/auth/drive.file']
        
        # Cargar o refresh token existente
        credentials = None
        token_path = Path(TOKEN_FILE)
        
        if token_path.exists():
            credentials = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        
        # Si no hay credenciales válidas, iniciar flow OAuth
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                credentials = flow.run_local_server(port=0)
            
            # Guardar credenciales para futuro uso
            with open(token_path, 'w') as token:
                token.write(credentials.to_json())
        
        # Crear servicio de Drive
        service = build('drive', 'v3', credentials=credentials)
        
        # Crear carpeta si no existe
        folder_id = _get_or_create_folder(service, GOOGLE_DRIVE_FOLDER)
        
        # Buscar archivo existente con el mismo nombre
        query = f"name='{file_path.name}' and '{folder_id}' in parents and trashed=false"
        results = service.files().list(q=query).execute()
        
        if results.get('files'):
            # Actualizar archivo existente
            file_id = results['files'][0]['id']
            media = MediaFileUpload(str(file_path), resumable=True)
            
            service.files().update(
                fileId=file_id,
                media_body=media,
                fields='id'
            ).execute()
            
            logger.info(f"✅ Actualizado en Google Drive: {file_path.name}")
        else:
            # Crear nuevo archivo
            file_metadata = {
                'name': file_path.name,
                'parents': [folder_id]
            }
            media = MediaFileUpload(str(file_path), resumable=True)
            
            service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            logger.info(f"✅ Subido a Google Drive: {file_path.name}")
        
        return True
        
    except ImportError:
        logger.warning("Librerías de Google Drive no instaladas.")
        logger.info("Instala con: pip install google-api-python-client google-auth-oauthlib")
        return False
    except Exception as e:
        logger.error(f"Error subiendo a Google Drive: {e}")
        return False

def _get_or_create_folder(service, folder_name: str) -> str:
    """Obtiene o crea carpeta en Google Drive."""
    # Buscar carpeta existente
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query).execute()
    
    if results.get('files'):
        return results['files'][0]['id']
    
    # Crear nueva carpeta
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = service.files().create(body=folder_metadata, fields='id').execute()
    return folder['id']

def update_triggers_json():
    """Actualiza el archivo triggers.json con todos los skills válidos en la carpeta."""
    if not SKILLS_PATH.exists():
        logger.error(f"Error: La carpeta de skills no existe en:\n   {SKILLS_PATH}")
        return

    triggers = {"skills": {}}
    if TRIGGERS_PATH.exists():
        try:
            with open(TRIGGERS_PATH, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    loaded_data = json.loads(content)
                    if isinstance(loaded_data, dict) and "skills" in loaded_data:
                        triggers = loaded_data
                    else:
                        print(f"⚠️ Estructura no válida en {TRIGGERS_PATH}. Se reiniciará.")
        except json.JSONDecodeError:
            print(f"⚠️ El archivo {TRIGGERS_PATH} está corrupto. Se sobrescribirá.")
        except Exception as e:
            print(f"⚠️ Error al leer {TRIGGERS_PATH}: {e}")

    added_count = 0
    skipped_count = 0
    orphan_count = 0

    # Detect orphans (entries in JSON without corresponding folders)
    existing_skill_names = {skill_dir.name for skill_dir in SKILLS_PATH.iterdir() if skill_dir.is_dir() and not skill_dir.name.startswith('.')}
    for skill_name in list(triggers["skills"].keys()):
        if skill_name not in existing_skill_names:
            logger.warning(f"Huérfano: {skill_name} — carpeta no encontrada")
            orphan_count += 1

    for skill_dir in SKILLS_PATH.iterdir():
        if skill_dir.is_dir() and not skill_dir.name.startswith('.'):
            skill_name = skill_dir.name
            skill_md_path = skill_dir / "SKILL.md"
            
            # Validate SKILL.md exists
            if not skill_md_path.exists():
                logger.error(f"SKILL.md no encontrado para {skill_name}, omitido")
                continue
            
            if skill_name not in triggers["skills"]:
                metadata = get_skill_metadata(skill_dir)
                triggers["skills"][skill_name] = {
                    "trigger": generate_triggers(skill_name),
                    "path": metadata["path"],
                    "url": metadata["url"],
                    "description": metadata["description"],
                    "last_modified": metadata["last_modified"]
                }
                logger.info(f"Añadido: {skill_name}")
                added_count += 1
            else:
                # Update last_modified, url, and description for existing entries
                metadata = get_skill_metadata(skill_dir)
                triggers["skills"][skill_name]["last_modified"] = metadata["last_modified"]
                triggers["skills"][skill_name]["url"] = metadata["url"]
                triggers["skills"][skill_name]["description"] = metadata["description"]
                logger.info(f"Ya existe: {skill_name}")
                skipped_count += 1

    try:
        with open(TRIGGERS_PATH, "w", encoding="utf-8") as f:
            json.dump(triggers, f, indent=2, ensure_ascii=False)
        logger.info(f"Archivo '{TRIGGERS_PATH}' actualizado con éxito.")
        logger.info(f"Resumen: {added_count} añadidos, {skipped_count} ya existentes, {orphan_count} huérfanos, {len(triggers['skills'])} totales.")
        
        # Subir a Google Drive
        logger.info("Iniciando subida a Google Drive...")
        upload_to_google_drive(TRIGGERS_PATH)
        
        # Auto-push to git
        try:
            # Change to project root for git operations
            project_root = Path("/Users/mauriciomeyran/Documents/03 Projects/VANTAGE")
            
            # Try to add file
            add_result = subprocess.run(
                ["git", "add", "skills/triggers.json"],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=False
            )
            
            # Check if git add failed
            if add_result.returncode != 0:
                logger.error(f"git add falló: {add_result.stderr}")
                return
            
            # Try to commit
            commit_result = subprocess.run(
                ["git", "commit", "-m", "chore: update triggers.json [automated]"],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=False
            )
            
            if commit_result.returncode == 0:
                logger.info("Commit exitoso")
                
                # Push
                push_result = subprocess.run(
                    ["git", "push"],
                    cwd=project_root,
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if push_result.returncode == 0:
                    logger.info("Push exitoso")
                else:
                    logger.warning(f"Push falló: {push_result.stderr}")
            else:
                # Check if it's "nothing to commit" error
                if "nothing to commit" in commit_result.stdout or "nothing to commit" in commit_result.stderr:
                    logger.info("No hay cambios que commitear")
                elif commit_result.stderr:
                    logger.warning(f"Commit falló: {commit_result.stderr}")
                else:
                    logger.info("No hay cambios que commitear")
                    
        except Exception as e:
            logger.warning(f"Error en git operations: {e}")
            
    except Exception as e:
        logger.error(f"Error al escribir en el archivo {TRIGGERS_PATH}: {e}")

if __name__ == "__main__":
    update_triggers_json()
