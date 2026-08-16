import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

# --- Configuración de Rutas Absolutas ---
SKILLS_PATH = Path("/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/skills")
TRIGGERS_PATH = Path("/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/skills/triggers.json")

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
            print(f"⚠️ Error leyendo SKILL.md para {skill_name}: {e}")

    if skill_description == f"VANTAGE Skill: {skill_name}":
        index_json_path = skill_path / "index.json"
        if index_json_path.exists():
            try:
                with open(index_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        skill_description = data.get("description", data.get("desc", skill_description))
            except Exception as e:
                print(f"⚠️ Error leyendo index.json para {skill_name}: {e}")

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

def update_triggers_json():
    """Actualiza el archivo triggers.json con todos los skills válidos en la carpeta."""
    if not SKILLS_PATH.exists():
        print(f"❌ Error: La carpeta de skills no existe en:\n   {SKILLS_PATH}")
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
            print(f"⚠️ Huérfano: {skill_name} — carpeta no encontrada")
            orphan_count += 1

    for skill_dir in SKILLS_PATH.iterdir():
        if skill_dir.is_dir() and not skill_dir.name.startswith('.'):
            skill_name = skill_dir.name
            skill_md_path = skill_dir / "SKILL.md"
            
            # Validate SKILL.md exists
            if not skill_md_path.exists():
                print(f"❌ SKILL.md no encontrado para {skill_name}, omitido")
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
                print(f"✅ Añadido: {skill_name}")
                added_count += 1
            else:
                # Update last_modified, url, and description for existing entries
                metadata = get_skill_metadata(skill_dir)
                triggers["skills"][skill_name]["last_modified"] = metadata["last_modified"]
                triggers["skills"][skill_name]["url"] = metadata["url"]
                triggers["skills"][skill_name]["description"] = metadata["description"]
                print(f"⏭️  Ya existe: {skill_name}")
                skipped_count += 1

    try:
        with open(TRIGGERS_PATH, "w", encoding="utf-8") as f:
            json.dump(triggers, f, indent=2, ensure_ascii=False)
        print(f"\n📝 Archivo '{TRIGGERS_PATH}' actualizado con éxito.")
        print(f"   📊 Resumen: {added_count} añadidos, {skipped_count} ya existentes, {orphan_count} huérfanos, {len(triggers['skills'])} totales.")
        
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
                print(f"❌ git add falló: {add_result.stderr}")
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
                print("✅ Commit exitoso")
                
                # Push
                push_result = subprocess.run(
                    ["git", "push"],
                    cwd=project_root,
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if push_result.returncode == 0:
                    print("✅ Push exitoso")
                else:
                    print(f"⚠️ Push falló: {push_result.stderr}")
            else:
                # Check if it's "nothing to commit" error
                if "nothing to commit" in commit_result.stdout or "nothing to commit" in commit_result.stderr:
                    print("ℹ️ No hay cambios que commitear")
                elif commit_result.stderr:
                    print(f"⚠️ Commit falló: {commit_result.stderr}")
                else:
                    print("ℹ️ No hay cambios que commitear")
                    
        except Exception as e:
            print(f"⚠️ Error en git operations: {e}")
            
    except Exception as e:
        print(f"❌ Error al escribir en el archivo {TRIGGERS_PATH}: {e}")

if __name__ == "__main__":
    update_triggers_json()
