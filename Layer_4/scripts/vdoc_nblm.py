import asyncio
import os
import sys
import tempfile
from fnmatch import fnmatch
from pathlib import Path

# ==============================================================================
# CONFIGURACIÓN DE RUTAS Y CONSTANTES
# ==============================================================================
_SCRIPT_DIR = Path(__file__).resolve()
PROJECT_ROOT = _SCRIPT_DIR.parents[2]
ACTIVE_DIR = PROJECT_ROOT / 'Documentación' / 'ACTIVE'
DIGEST_PATH = PROJECT_ROOT / 'VANTAGE_digest.txt'
MAX_WORDS_PER_PART = 500000
NOTEBOOK_ID = os.environ.get('NOTEBOOK_ID', '')

EXCLUDE_DIRS = {
    '.git', '.venv', 'venv', '__pycache__', '.idea', '.vscode', 'node_modules',
    '.obsidian', 'archive', 'backups', '.ssh', '.aws', '.config', '.cache',
    '.pytest_cache', 'dist', 'build',
}

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
        and not name.startswith('vantage_digest_part_')
        and not any(fnmatch(name, pattern) for pattern in SECRET_PATTERNS)
        and path.suffix.lower() in INCLUDE_EXTS
        and path.is_file()
    )

# ==============================================================================
# GENERACIÓN DE DIGEST LOCAL
# ==============================================================================
def count_words(text: str) -> int:
    """Cuenta palabras en un string."""
    return len(text.split())

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

            text = file_path.read_text(encoding='utf-8')
            content_blocks.append(f"========================================\nFile: {file_rel}\n========================================\n{text}\n")

    header = "========================================\nVANTAGE CODEBASE DIGEST (LOCAL)\n========================================\n\n"
    tree_section = "\n".join(tree_lines) + "\n\n"
    files_header = "========================================\nFILES CONTENT\n========================================\n\n"

    # Dividir en partes por palabras
    parts = []
    current_part = header + tree_section + files_header
    current_word_count = count_words(current_part)

    for block in content_blocks:
        block_word_count = count_words(block)

        if current_word_count + block_word_count > MAX_WORDS_PER_PART:
            parts.append(current_part)
            current_part = header + tree_section + files_header + block
            current_word_count = count_words(current_part)
        else:
            current_part += block
            current_word_count += block_word_count

    if current_part:
        parts.append(current_part)

    # Escribir cada parte
    digest_files = []
    for i, part in enumerate(parts, 1):
        if len(parts) == 1:
            output_path = DIGEST_PATH
        else:
            output_path = DIGEST_PATH.parent / f"VANTAGE_digest_part_{i}.txt"

        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                             dir=output_path.parent, delete=False) as f:
                temporary = Path(f.name)
                f.write(part)
            temporary.replace(output_path)
            digest_files.append(output_path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    print(f'✓ Digest local generado en {len(digest_files)} parte(s):')
    for f in digest_files:
        print(f'  - {f.name} ({count_words(f.read_text()):,} palabras)')

    return digest_files

# ==============================================================================
# OPERACIONES DE SINCRONIZACIÓN Y PURGA
# ==============================================================================
async def purge_and_upload(client, notebook_id, file_path: Path):
    file_name = file_path.name
    sources = await client.sources.list(notebook_id)
    await client.sources.add_file(notebook_id, file_path)
    for src in sources:
        src_title = getattr(src, 'title', getattr(src, 'name', ''))
        if src_title == file_name:
            await client.sources.delete(notebook_id, src.id)
            print(f'✓ Fuente anterior eliminada: {file_name} (ID: {src.id})')
    print(f'✓ {file_name} sincronizado exitosamente.')

async def purge_and_upload_all(client, notebook_id, file_paths: list[Path]):
    """Elimina todas las fuentes anteriores con el mismo patrón de nombre y sube las nuevas."""
    sources = await client.sources.list(notebook_id)

    # Si hay múltiples partes, eliminar todas las partes anteriores
    if len(file_paths) > 1:
        for src in sources:
            src_title = getattr(src, 'title', getattr(src, 'name', ''))
            if src_title.startswith('VANTAGE_digest_part_') or src_title == 'VANTAGE_digest.txt':
                await client.sources.delete(notebook_id, src.id)
                print(f'✓ Fuente anterior eliminada: {src_title} (ID: {src.id})')

    # Subir todas las partes nuevas
    for file_path in file_paths:
        await client.sources.add_file(notebook_id, file_path)
        print(f'✓ {file_path.name} sincronizado exitosamente.')

# ==============================================================================
# EJECUCIÓN PRINCIPAL
# ==============================================================================
async def main():
    from notebooklm import NotebookLMClient

    target_notebook = NOTEBOOK_ID.strip()
    if not target_notebook:
        print('❌ NOTEBOOK_ID es obligatorio; no se seleccionará un cuaderno automáticamente.')
        return 1

    try:
        if not ACTIVE_DIR.is_dir() or ACTIVE_DIR.is_symlink():
            print(f'⚠ ACTIVE_DIR no existe o no es un directorio seguro: {ACTIVE_DIR}')
            print('  No se subió ningún documento fundacional (revisar la ruta).')
            return 1

        async with NotebookLMClient.from_storage() as client:
            notebooks = await client.notebooks.list()
            if not any(getattr(nb, 'id', '') == target_notebook for nb in notebooks):
                print('❌ NOTEBOOK_ID no corresponde a un cuaderno accesible.')
                return 1

            digest_files = generate_local_digest()
            print(f'→ Sincronizando espacio de fuentes con NotebookLM (ID: {target_notebook})...')
            await purge_and_upload_all(client, target_notebook, digest_files)
            for file_path in sorted(ACTIVE_DIR.glob('*.md')):
                if is_safe_source(file_path):
                    await purge_and_upload(client, target_notebook, file_path)
        return 0
    except Exception as e:
        print(f'❌ Error en la sincronización con NotebookLM: {e}')
        return 1

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
