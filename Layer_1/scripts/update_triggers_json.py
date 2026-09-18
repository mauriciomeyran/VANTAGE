import os
import json
import subprocess
import logging
import re
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

# --- Configuración de Rutas Absolutas ---
SKILLS_PATH = Path("/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/skills")
TRIGGERS_PATH = Path("/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/skills/triggers.json")

# --- Configuración de Notion API (Skill Library) ---
# Requiere: pip install requests
# Reutiliza el mismo token que ya usa Layer 1 para Notion (Layer_1/.env)
NOTION_API_KEY = os.environ.get("NOTION_TOKEN")  # Internal Integration Token
NOTION_SKILL_LIBRARY_DATA_SOURCE_ID = "2f1938be-fc42-83c8-8972-07300201136d"
NOTION_API_VERSION = "2025-09-03"  # Notion-Version header requerido para data sources
NOTION_API_BASE = "https://api.notion.com/v1"

DEFAULT_TRIGGERS_TEMPLATES = [
    "ejecuta {skill_name_clean}",
    "activa {skill_name_clean}",
    "{skill_name_clean}"
]


def get_github_raw_url(relative_skill_path, branch="main"):
    """Genera la GitHub raw URL para un skill plano dentro de skills/."""
    return (
        f"https://raw.githubusercontent.com/mauriciomeyran/VANTAGE/"
        f"{branch}/skills/{relative_skill_path}"
    )


def discover_skill_files(skills_path: Path):
    """Descubre skills activos en formato plano: skills/*.md."""
    return {
        path.stem: path
        for path in sorted(skills_path.glob("*.md"))
        if path.is_file() and path.name != "triggers.json"
        and path.name != "vantage-active-search-weekly.md"
    }


def get_skill_metadata(skill_path, relative_skill_path):
    """
    Extrae metadatos de un skill plano.
    """
    skill_name = skill_path.stem
    skill_description = f"VANTAGE Skill: {skill_name}"
    last_modified = None

    try:
        mtime = skill_path.stat().st_mtime
        last_modified = datetime.fromtimestamp(mtime).isoformat()

        with open(skill_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        in_front_matter = False
        first_content_line = None

        for line in lines:
            stripped = line.strip()

            if stripped == "---":
                in_front_matter = not in_front_matter
                continue

            if in_front_matter:
                if stripped.startswith("description:"):
                    skill_description = stripped.split(":", 1)[1].strip().strip('"').strip("'")
                    break

            if stripped and not stripped.startswith("#") and first_content_line is None:
                first_content_line = stripped

        if skill_description == f"VANTAGE Skill: {skill_name}" and first_content_line:
            skill_description = first_content_line[:200]

    except Exception as e:
        logger.warning(f"Error leyendo {skill_path.name}: {e}")

    return {
        "last_modified": last_modified,
        "path": f"skills/{relative_skill_path}",
        "url": get_github_raw_url(relative_skill_path),
        "description": skill_description,
    }


def generate_triggers(skill_name):
    """Genera triggers por defecto basados en los templates configurados."""
    skill_name_clean = skill_name.replace("-", " ")
    triggers = [template.format(skill_name_clean=skill_name_clean) for template in DEFAULT_TRIGGERS_TEMPLATES]
    return list(dict.fromkeys(triggers))


# --- Notion Skill Library sync (reemplaza Google Drive) ---

def normalize_skill_name(raw_name: str) -> str:
    """
    Normaliza el nombre de una fila de Notion contra la key del manifest.
    Reglas:
    - Quita sufijo '.skill' (formato legacy, pre-migración a carpeta/SKILL.md)
    - Trim de espacios
    """
    name = raw_name.strip()
    if name.endswith(".skill"):
        name = name[: -len(".skill")]
    return name


def fetch_notion_skill_library():
    """
    Consulta la Skill Library (Notion data source) vía API y regresa un dict:
        { skill_name_normalizado: notion_page_id }

    Reglas de resolución ante conflicto (ver acuerdo con operador 2026-08-17):
    - Filas con Estado == 'Deprecado' se ignoran por completo.
    - Si hay más de una fila activa para el mismo nombre normalizado:
        1. Preferir la fila cuya 'Ruta' contenga 'SKILL.md' (formato nuevo post-migración).
        2. Si ninguna cumple lo anterior, tomar la de creación más reciente y loggear warning.
    - Skills del manifest sin match en Notion quedan con notion_id=None (huérfano),
      mismo tratamiento que huérfanos de carpeta.
    """
    if not NOTION_API_KEY:
        logger.warning("NOTION_API_KEY no configurada. Skipping notion_id sync — se preservan valores previos si existen.")
        return None

    try:
        import requests
    except ImportError:
        logger.warning("Librería 'requests' no instalada. Instala con: pip install requests")
        return None

    url = f"{NOTION_API_BASE}/data_sources/{NOTION_SKILL_LIBRARY_DATA_SOURCE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json",
    }

    rows = []
    payload = {"page_size": 100}
    try:
        while True:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            rows.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            payload["start_cursor"] = data.get("next_cursor")
    except Exception as e:
        logger.error(f"Error consultando Skill Library en Notion: {e}")
        return None

    # candidates[normalized_name] = list of (page_id, ruta, estado, created_time)
    candidates = {}
    for row in rows:
        props = row.get("properties", {})
        page_id = row.get("id", "")

        title_prop = props.get("Skill", {})
        title_parts = title_prop.get("title", [])
        raw_name = "".join(t.get("plain_text", "") for t in title_parts).strip()
        if not raw_name:
            continue

        estado_prop = props.get("Estado", {})
        estado = (estado_prop.get("select") or {}).get("name", "")

        if estado == "Deprecado":
            continue

        ruta_prop = props.get("Ruta", {})
        ruta_parts = ruta_prop.get("rich_text", [])
        ruta = "".join(t.get("plain_text", "") for t in ruta_parts)

        created_time = row.get("created_time", "")

        normalized = normalize_skill_name(raw_name)
        candidates.setdefault(normalized, []).append({
            "page_id": page_id,
            "ruta": ruta,
            "estado": estado,
            "created_time": created_time,
        })

    resolved = {}
    for name, entries in candidates.items():
        if len(entries) == 1:
            resolved[name] = entries[0]["page_id"]
            continue

        # Conflicto: preferir Ruta que apunte a SKILL.md
        new_format = [e for e in entries if "SKILL.md" in e["ruta"]]
        if len(new_format) == 1:
            resolved[name] = new_format[0]["page_id"]
            logger.warning(
                f"Skill Library: '{name}' tenía {len(entries)} filas activas — "
                f"resuelto por formato SKILL.md (page_id={new_format[0]['page_id']})"
            )
        else:
            # fallback: más reciente
            newest = max(entries, key=lambda e: e["created_time"])
            resolved[name] = newest["page_id"]
            logger.warning(
                f"Skill Library: '{name}' tenía {len(entries)} filas activas ambiguas — "
                f"resuelto por fecha de creación más reciente (page_id={newest['page_id']}). "
                f"REVISAR MANUALMENTE (candidato a vantage-sync-skill-library)."
            )

    return resolved


def update_triggers_json():
    """Actualiza triggers.json con los skills planos de skills/*.md."""
    triggers = {"skills": {}}

    if TRIGGERS_PATH.exists():
        try:
            with open(TRIGGERS_PATH, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
                if isinstance(loaded_data, dict) and "skills" in loaded_data:
                    triggers = loaded_data
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"No se pudo cargar triggers.json: {e}")

    discovered = discover_skill_files(SKILLS_PATH)
    added_count = 0
    skipped_count = 0
    orphan_count = 0

    # Elimina entradas que ya no corresponden a un skill activo.
    discovered_names = set(discovered)
    for skill_name in list(triggers["skills"].keys()):
        if skill_name not in discovered_names:
            del triggers["skills"][skill_name]
            orphan_count += 1
            logger.info(f"Huérfano eliminado: {skill_name}")

    for skill_name, skill_path in discovered.items():
        relative_skill_path = skill_path.relative_to(SKILLS_PATH).as_posix()
        metadata = get_skill_metadata(skill_path, relative_skill_path)

        if skill_name not in triggers["skills"]:
            triggers["skills"][skill_name] = {
                "trigger": generate_triggers(skill_name),
                "path": metadata["path"],
                "url": metadata["url"],
                "notion_id": None,
                "description": metadata["description"],
                "last_modified": metadata["last_modified"]
            }
            logger.info(f"Añadido: {skill_name} ({relative_skill_path})")
            added_count += 1
        else:
            triggers["skills"][skill_name]["last_modified"] = metadata["last_modified"]
            triggers["skills"][skill_name]["path"] = metadata["path"]
            triggers["skills"][skill_name]["url"] = metadata["url"]
            triggers["skills"][skill_name]["description"] = metadata["description"]
            triggers["skills"][skill_name].setdefault("notion_id", None)
            logger.info(f"Ya existe: {skill_name} ({relative_skill_path})")
            skipped_count += 1

    # --- Sync notion_id contra Skill Library ---
    notion_map = fetch_notion_skill_library()
    notion_matched = 0
    notion_orphan = 0
    if notion_map is not None:
        for skill_name, entry in triggers["skills"].items():
            page_id = notion_map.get(skill_name)
            if page_id:
                entry["notion_id"] = page_id
                notion_matched += 1
            else:
                entry["notion_id"] = None
                notion_orphan += 1
                logger.warning(f"Sin match en Skill Library (Notion): {skill_name} — notion_id=None")

    try:
        with open(TRIGGERS_PATH, "w", encoding="utf-8") as f:
            json.dump(triggers, f, indent=2, ensure_ascii=False)
        logger.info(f"Archivo '{TRIGGERS_PATH}' actualizado con éxito.")
        logger.info(f"Resumen: {added_count} añadidos, {skipped_count} ya existentes, {orphan_count} huérfanos (carpeta), {len(triggers['skills'])} totales.")
        if notion_map is not None:
            logger.info(f"Notion sync: {notion_matched} con notion_id, {notion_orphan} sin match en Skill Library.")

        # Auto-push to git
        try:
            project_root = Path("/Users/mauriciomeyran/Documents/03 Projects/VANTAGE")

            add_result = subprocess.run(
                ["git", "add", "skills/triggers.json"],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=False
            )

            if add_result.returncode != 0:
                logger.error(f"git add falló: {add_result.stderr}")
                return

            commit_result = subprocess.run(
                ["git", "commit", "-m", "chore: update triggers.json [automated]"],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=False
            )

            if commit_result.returncode == 0:
                logger.info("Commit exitoso")

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
