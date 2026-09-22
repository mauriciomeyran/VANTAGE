#!/usr/bin/env python3
import os
from pathlib import Path
from notion_client import Client

# ── 1. Carga de Variables de Entorno (.env) ──────────────────────────────────
ENV_PATH = Path(
    "/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/config/layer_1.env"
)


def load_env_file(path: Path) -> dict[str, str]:
    """Carga variables desde el archivo .env manualmente (Opción 1)."""
    env_vars = {}
    if not path.exists():
        raise FileNotFoundError(f"[-] No se encontró el archivo .env en: {path}")

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            env_vars[key.strip()] = val.strip().strip('"').strip("'")
    return env_vars


# Extraer el NOTION_TOKEN del entorno local de VANTAGE
env_vars = load_env_file(ENV_PATH)
NOTION_TOKEN = env_vars.get("NOTION_TOKEN")

if not NOTION_TOKEN:
    raise ValueError(f"[-] NOTION_TOKEN no fue encontrado en {ENV_PATH}")

# Inicializar cliente de Notion
notion = Client(auth=NOTION_TOKEN)

# ── 2. Configuración del Reemplazo ───────────────────────────────────────────
OLD_TEXT = "ALDO GROUP"
NEW_TEXT = "ALDO"


# ── 3. Lógica de Reemplazo y Recorrido de Notion ─────────────────────────────
def replace_in_rich_text(rich_text_list: list) -> tuple[list, bool]:
    """Reemplaza OLD_TEXT por NEW_TEXT dentro de estructuras rich_text."""
    has_changed = False
    new_rich_text = []

    for item in rich_text_list:
        item_copy = dict(item)
        if item_copy.get("type") == "text":
            content = item_copy["text"]["content"]
            if OLD_TEXT in content:
                item_copy["text"]["content"] = content.replace(
                    OLD_TEXT, NEW_TEXT
                )
                if "plain_text" in item_copy:
                    item_copy["plain_text"] = item_copy["plain_text"].replace(
                        OLD_TEXT, NEW_TEXT
                    )
                has_changed = True
        new_rich_text.append(item_copy)

    return new_rich_text, has_changed


def process_block(block: dict):
    """Procesa un bloque de Notion y actualiza su texto si contiene la cadena objetivo."""
    block_id = block["id"]
    block_type = block["type"]

    if block_type not in block or "rich_text" not in block[block_type]:
        return

    rich_text = block[block_type]["rich_text"]
    updated_rich_text, changed = replace_in_rich_text(rich_text)

    if changed:
        print(f"  [+] Reemplazando en bloque {block_id} ({block_type})...")
        try:
            notion.blocks.update(
                block_id=block_id,
                **{block_type: {"rich_text": updated_rich_text}},
            )
            print(f"  [✓] Bloque {block_id} actualizado exitosamente.")
        except Exception as e:
            print(f"  [✕] Error al actualizar el bloque {block_id}: {e}")


def process_page_properties(page: dict):
    """Procesa y actualiza las propiedades de nivel de página (Título y Rich Text)."""
    page_id = page["id"]
    properties = page.get("properties", {})
    updated_props = {}

    for prop_name, prop_data in properties.items():
        p_type = prop_data.get("type")

        # Propiedades tipo Título
        if p_type == "title" and prop_data.get("title"):
            new_rt, changed = replace_in_rich_text(prop_data["title"])
            if changed:
                updated_props[prop_name] = {"title": new_rt}

        # Propiedades tipo Texto Enriquecido
        elif p_type == "rich_text" and prop_data.get("rich_text"):
            new_rt, changed = replace_in_rich_text(prop_data["rich_text"])
            if changed:
                updated_props[prop_name] = {"rich_text": new_rt}

    if updated_props:
        print(f"  [+] Reemplazando en propiedades de página {page_id}...")
        try:
            notion.pages.update(page_id=page_id, properties=updated_props)
            print(f"  [✓] Propiedades de la página {page_id} actualizadas.")
        except Exception as e:
            print(
                f"  [✕] Error actualizando propiedades de la página {page_id}: {e}"
            )


def scan_and_replace_recursive(parent_id: str):
    """Escanea y reemplaza iterando recursivamente en los bloques hijos."""
    try:
        children = notion.blocks.children.list(block_id=parent_id).get(
            "results", []
        )
    except Exception:
        return

    for block in children:
        # Reemplazo en el bloque actual
        process_block(block)

        # Si el bloque contiene más elementos anidados (toggles, subpáginas, listas)
        if block.get("has_children"):
            scan_and_replace_recursive(block["id"])


def run_mass_replace(root_page_id: str):
    """Punto de entrada principal para ejecutar el reemplazo masivo."""
    print(f"[*] NOTION_TOKEN cargado exitosamente desde {ENV_PATH}")
    print(
        f"[*] Iniciando escaneo e intercambio de '{OLD_TEXT}' -> '{NEW_TEXT}'..."
    )

    # Procesar propiedades de la página raíz si aplica
    try:
        page = notion.pages.retrieve(page_id=root_page_id)
        process_page_properties(page)
    except Exception:
        pass

    # Iniciar recorrido de bloques
    scan_and_replace_recursive(root_page_id)
    print("\n[✓] Proceso de reemplazo finalizado.")


# ── 4. Ejecución ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Sustituye esta cadena con el Page ID raíz de tu documentación en Notion
    ROOT_PAGE_ID = "36e938befc4281d6bf40dfe7dee782a5"

    run_mass_replace(ROOT_PAGE_ID)
