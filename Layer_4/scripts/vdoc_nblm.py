import os
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

EXCLUDE_DIRS = {'.git', '.venv', '__pycache__', '.idea', '.vscode', 'node_modules', '.obsidian'}
EXCLUDE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.zip', '.tar', '.gz', '.pyc'}

# ==============================================================================
# GENERACIÓN DE DIGEST LOCAL
# ==============================================================================
def generate_local_digest():
    print('→ Generando digest desde el sistema de archivos local...')
    tree_lines = []
    content_blocks = []
    
    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        rel_path = Path(root).relative_to(PROJECT_ROOT)
        depth = len(rel_path.parts) if str(rel_path) != '.' else 0
        indent = '  ' * depth
        
        if depth == 0:
            tree_lines.append(f"Directory structure:\n└── {PROJECT_ROOT.name}/")
        else:
            tree_lines.append(f"{indent}├── {Path(root).name}/")
            
        for file in sorted(files):
            file_path = Path(root) / file
            if file_path.suffix.lower() in EXCLUDE_EXTS or file == 'VANTAGE_digest.txt':
                continue
                
            file_rel = file_path.relative_to(PROJECT_ROOT)
            tree_lines.append(f"{indent}  └── {file}")
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                content_blocks.append(f"========================================\nFile: {file_rel}\n========================================\n{text}\n")
            except Exception as e:
                content_blocks.append(f"========================================\nFile: {file_rel} (Error al leer: {e})\n========================================\n")

    full_digest = "========================================\nVANTAGE CODEBASE DIGEST (LOCAL)\n========================================\n\n"
    full_digest += "\n".join(tree_lines) + "\n\n"
    full_digest += "========================================\nFILES CONTENT\n========================================\n\n"
    full_digest += "\n".join(content_blocks)
    
    with open(DIGEST_PATH, 'w', encoding='utf-8') as f:
        f.write(full_digest)
        
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
    
    # 1. Purga de versiones antiguas
    try:
        sources = client.notebooks.list_sources(notebook_id)
        for src in sources:
            src_title = getattr(src, 'title', getattr(src, 'name', ''))
            if src_title == file_name:
                client.notebooks.delete_source(notebook_id, src.id)
                print(f'✓ Purga preventiva: {file_name} antiguo eliminado (ID: {src.id})')
    except Exception as e:
        print(f'⚠ Warning en purga preventiva para {file_name}: {e}')

    # 2. Carga pasando el objeto Path directo
    try:
        client.notebooks.add_source(notebook_id, file_path)
        print(f'✓ {file_name} sincronizado exitosamente.')
    except Exception as e:
        print(f'❌ Error cargando {file_name}: {e}')

# ==============================================================================
# EJECUCIÓN PRINCIPAL
# ==============================================================================
def main():
    generate_local_digest()
    
    try:
        client = get_notebooklm_client()
        target_notebook = NOTEBOOK_ID
        
        if not target_notebook:
            notebooks = client.notebooks.list()
            if notebooks:
                target_notebook = notebooks[0].id
            else:
                print('❌ No se encontraron cuadernos activos en NotebookLM.')
                return

        print(f'→ Sincronizando espacio de fuentes con NotebookLM (ID: {target_notebook})...')

        # 1. Digest
        if DIGEST_PATH.exists():
            purge_and_upload(client, target_notebook, DIGEST_PATH)

        # 2. Documentos de ACTIVE/
        if ACTIVE_DIR.exists():
            for file_path in sorted(ACTIVE_DIR.glob('*.md')):
                purge_and_upload(client, target_notebook, file_path)
        else:
            print(f'⚠ ACTIVE_DIR no existe: {ACTIVE_DIR}')
            print('  No se subió ningún documento fundacional (revisar la ruta).')

    except Exception as e:
        print(f'❌ Error en la sincronización con NotebookLM: {e}')

if __name__ == '__main__':
    main()
