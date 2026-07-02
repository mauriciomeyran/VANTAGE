import os
import requests
import argparse
import time
from dotenv import load_dotenv

# Apuntamos exactamente a tu archivo de configuración en Layer_1/config/layer_1.env
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', 'layer_1.env')
load_dotenv(env_path)

def fetch_block_children_recursive(block_id: str, headers: dict, depth: int = 0) -> list:
    """Recursivamente obtiene texto de bloques hijos (sub-bullets, etc)."""
    lines = []
    url = f"https://api.notion.com/v1/blocks/{block_id}/children"
    next_cursor = None
    has_more = True
    while has_more:
        params = {"page_size": 100}
        if next_cursor:
            params["start_cursor"] = next_cursor
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            break
        data = resp.json()
        for child in data.get("results", []):
            ctype = child["type"]
            if ctype in ["paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item", "code", "quote"]:
                rich_text = child[ctype].get("rich_text", [])
                text = "".join([rt.get("plain_text", "") for rt in rich_text])
                prefix = "  " * (depth + 1) + "- "
                lines.append(f"{prefix}{text}")
            if child.get("has_children"):
                lines.extend(fetch_block_children_recursive(child["id"], headers, depth + 1))
        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor")
    return lines


def fetch_lazy_section(page_id: str, route_id: str) -> str:
    """
    Realiza un fetch quirúrgico a Notion. Devuelve SOLO el contenido 
    de una sección específica, ignorando el resto del documento.
    Soporta esquema post-normalización: KERNEL:CLAVE
    """
    api_key = os.getenv("NOTION_API_KEY")
    if not api_key:
        api_key = os.getenv("NOTION_TOKEN")
        
    if not api_key:
        return f"ERROR: Variable de API de Notion no encontrada. Asegúrate de que exista en {env_path}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28"
    }

    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    has_more = True
    next_cursor = None
    
    capturing = False
    captured_blocks = []

    while has_more:
        params = {"page_size": 100}
        if next_cursor:
            params["start_cursor"] = next_cursor
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            return f"ERROR API Notion: {response.status_code} - {response.text}"
            
        data = response.json()
        
        for block in data.get("results", []):
            block_type = block["type"]
            
            text_content = ""
            if block_type in ["paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item", "code", "quote"]:
                rich_text = block[block_type].get("rich_text", [])
                text_content = "".join([rt.get("plain_text", "") for rt in rich_text])
            
            # 1. Detectar el inicio (soporta KERNEL:CLAVE y headers antiguos)
            if (route_id in text_content or f"KERNEL:{route_id}" in text_content.replace("`", "")) and ("heading" in block_type):
                capturing = True
                just_started = True
                captured_blocks.append(f"## {text_content}")
                continue
            
            # 2. Capturar el Payload y detectar el final (mejorado para KERNEL: y headers)
            if capturing:
                if "</payload>" in text_content:
                    capturing = False
                    break
                if "heading" in block_type and route_id not in text_content and "KERNEL:" not in text_content:
                    if just_started:
                        just_started = False
                    else:
                        capturing = False
                        break
                captured_blocks.append(text_content)
                if block.get("has_children"):
                    captured_blocks.extend(fetch_block_children_recursive(block["id"], headers))
                just_started = False

        if not capturing and len(captured_blocks) > 0:
            break

        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor")

    if not captured_blocks:
        return f"ERROR: Ruta '{route_id}' no encontrada en el documento {page_id}."

    clean_text = "\n".join(captured_blocks).replace("<payload>", "").replace("</payload>", "").strip()
    return clean_text

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VANTAGE Lazy Loader (Post-Normalización KERNEL:)")
    parser.add_argument("--page", required=True, help="ID de la página de Notion (ej: KERNEL_MASTER o UUID)")
    parser.add_argument("--route", required=True, help="Ruta KERNEL:CLAVE (ej: KERNEL:TRIGGERS) o ID legacy")
    args = parser.parse_args()

    # Soporte para rutas KERNEL: limpias
    clean_route = args.route.replace("KERNEL:", "").strip()
    result = fetch_lazy_section(args.page, clean_route)
    print(result)