import os
import sys
import tempfile
from fnmatch import fnmatch
from pathlib import Path

# ==============================================================================
# CONFIGURACIÓN DE RUTAS Y CONSTANTES
# ==============================================================================
# Derivado del propio archivo (Layer_4/scripts/vdoc_nblm.py → VANTAGE), no de
# una ruta /Users/... hardcodeada.
_SCRIPT_DIR = Path(__file__).resolve()
PROJECT_ROOT = _SCRIPT_DIR.parents[2]
# Fix B8: la ruta real de los mirrors es Documentación/ACTIVE (la que usa
# vsync_doc y la que se respalda en git). Antes apuntaba a PROJECT_ROOT/'ACTIVE',
# que no existe: el digest se subía pero NINGÚN documento fundacional llegaba a
# NotebookLM, sin ningún aviso.
ACTIVE_DIR = PROJECT_ROOT / 'Documentación' / 'ACTIVE'
DIGEST_PATH = PROJECT_ROOT / 'VANTAGE_digest.txt'
NOTEBOOK_ID = os.environ.get('NOTEBOOK_ID', '')

# Filtrar ANTES de abrir archivos. No seguir enlaces, ni siquiera dentro del repo.
EXCLUDE_DIRS = {
    '.git', '.venv', 'venv', '__pycache__', '.idea', '.vscode', 'node_modules',
    '.obsidian', 'archive', 'backups', '.ssh', '.aws', '.config', '.cache',
    '.pytest_cache', 'dist', 'build',
}
# Lista positiva: los formatos desconocidos/binarios no son fuentes del digest.
INCLUDE_EXTS = {'.py', '.sh', '.md', '.txt', '.json', '.yaml', '.yml', '.toml',
                '.ini', '.cfg', '.csv', '.js', '.ts', '.tsx', '.jsx', '.html', '.css'}
SECRET_PATTERNS = (
    '*.env', '*.env.*', '*.key', '*.key.*', '*.pem', '*.pem.*',
    '*.secret', '*.secret.*', '*.p12', '*.pfx',
    '*token*.json*', '*secret*.json*', '*credential*.json*',
    'id_rsa*', 'id_ed25519*', '.netrc', '.git-credentials',
)


def is_safe_source(path: Path) -> bool:
    """Política por ruta; no detecta secretos incrustados en código/documentación."""
    try:
        relative = path.relative_to(PROJECT_ROOT)
    except ValueError:
        return False
    if any(part.lower() in EXCLUDE_DIRS for part in relative.parts[:-1]):
        return False
    if any(PROJECT_ROOT.joinpath(*relative.parts[:i]).is_symlink()
           for i in range(1, len(relative.parts) + 1)):
        return False
    name = path.name.lower()
    return (
        path != DIGEST_PATH
        and name != 'vantage_digest.txt'
        and not any(fnmatch(name, pattern) for pattern in SECRET_PATTERNS)
        and path.suffix.lower() in INCLUDE_EXTS
        and path.is_file()
    )

# ==============================================================================
# GENERACIÓN DE DIGEST LOCAL
# ==============================================================================
def generate_local_digest():
    print('→ Generando digest desde el sistema de archivos local...')
    tree_lines = []
    content_blocks = []
    
    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = sorted(d for d in dirs if d.lower() not in EXCLUDE_DIRS
                         and not (Path(root) / d).is_symlink())
        rel_path = Path(root).relative_to(PROJECT_ROOT)
        depth = len(rel_path.parts) if str(rel_path) != '.' else 0
        indent = '  ' * depth
        
        if depth == 0:
            tree_lines.append(f"Directory structure:\n└── {PROJECT_ROOT.name}/")
        else:
            tree_lines.append(f"{indent}├── {Path(root).name}/")
            
        for file in sorted(files):
            file_path = Path(root) / file
            if not is_safe_source(file_path):
                continue
                
            file_rel = file_path.relative_to(PROJECT_ROOT)
            tree_lines.append(f"{indent}  └── {file}")
            
            # Un error de lectura debe abortar, no producir un digest parcial exitoso.
            text = file_path.read_text(encoding='utf-8')
            content_blocks.append(f"========================================\nFile: {file_rel}\n========================================\n{text}\n")

    full_digest = "========================================\nVANTAGE CODEBASE DIGEST (LOCAL)\n========================================\n\n"
    full_digest += "\n".join(tree_lines) + "\n\n"
    full_digest += "========================================\nFILES CONTENT\n========================================\n\n"
    full_digest += "\n".join(content_blocks)
    
    # Reemplazo atómico y permisos privados; no escribir a través de un symlink.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                         dir=DIGEST_PATH.parent, delete=False) as f:
            temporary = Path(f.name)
            f.write(full_digest)
        temporary.replace(DIGEST_PATH)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

    print(f'✓ Digest local guardado en {DIGEST_PATH}')

# ==============================================================================
# INICIALIZACIÓN DE CLIENTE Y AUTENTICACIÓN
# ==============================================================================
def get_notebooklm_client():
    from notebooklm import NotebookLM
    from notebooklm.auth import Auth

    # Cargar credenciales guardadas en perfil local o entorno
    try:
        auth = Auth.from_storage()
    except Exception:
        auth = Auth.from_env()

    return NotebookLM(auth=auth)

# ==============================================================================
# OPERACIONES DE SINCRONIZACIÓN Y PURGA
# ==============================================================================
def purge_and_upload(client, notebook_id, file_path: Path):
    file_name = file_path.name
    # Listar antes de modificar; subir antes de borrar para conservar la fuente
    # anterior si la carga falla. Cualquier fallo se propaga hasta el CLI.
    sources = list(client.notebooks.list_sources(notebook_id))
    client.notebooks.add_source(notebook_id, file_path)
    for src in sources:
        src_title = getattr(src, 'title', getattr(src, 'name', ''))
        if src_title == file_name:
            client.notebooks.delete_source(notebook_id, src.id)
            print(f'✓ Fuente anterior eliminada: {file_name} (ID: {src.id})')
    print(f'✓ {file_name} sincronizado exitosamente.')

# ==============================================================================
# EJECUCIÓN PRINCIPAL
# ==============================================================================
def main():
    target_notebook = NOTEBOOK_ID.strip()
    if not target_notebook:
        print('❌ NOTEBOOK_ID es obligatorio; no se seleccionará un cuaderno automáticamente.')
        return 1

    try:
        if not ACTIVE_DIR.is_dir() or ACTIVE_DIR.is_symlink():
            print(f'⚠ ACTIVE_DIR no existe o no es un directorio seguro: {ACTIVE_DIR}')
            print('  No se subió ningún documento fundacional (revisar la ruta).')
            return 1
        client = get_notebooklm_client()
        if not any(nb.id == target_notebook for nb in client.notebooks.list()):
            print('❌ NOTEBOOK_ID no corresponde a un cuaderno accesible.')
            return 1

        generate_local_digest()
        print(f'→ Sincronizando espacio de fuentes con NotebookLM (ID: {target_notebook})...')
        purge_and_upload(client, target_notebook, DIGEST_PATH)
        for file_path in sorted(ACTIVE_DIR.glob('*.md')):
            if is_safe_source(file_path):
                purge_and_upload(client, target_notebook, file_path)
        return 0
    except Exception as e:
        print(f'❌ Error en la sincronización con NotebookLM: {e}')
        return 1

if __name__ == '__main__':
    sys.exit(main())
