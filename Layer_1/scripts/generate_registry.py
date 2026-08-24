import json
import urllib.request
import os
from pathlib import Path

# Ruta absoluta a tu archivo .env
ENV_PATH = Path("/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/config/layer_1.env")
FILE_KEY = "ga1c5atiei7v0wVNmBhtqD"

def load_env_file(filepath):
    env_vars = {}
    if not filepath.exists():
        raise FileNotFoundError(f"No se encontró el archivo .env en: {filepath}")
    
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                # Limpiar comillas simples o dobles alrededor del valor
                val = val.strip().strip("'\"")
                env_vars[key.strip()] = val
    return env_vars

# Cargar variables del .env
env = load_env_file(ENV_PATH)
FIGMA_TOKEN = env.get("FIGMA_ACCESS_TOKEN")

if not FIGMA_TOKEN:
    raise ValueError(f"ERROR: No se encontró 'FIGMA_ACCESS_TOKEN' dentro de {ENV_PATH}")

url = f"https://api.figma.com/v1/files/{FILE_KEY}"
headers = {"X-Figma-Token": FIGMA_TOKEN}

def extract_text_nodes(node, current_frame="Root"):
    nodes_summary = []
    
    if node.get("type") in ["FRAME", "GROUP", "COMPONENT", "SECTION", "CANVAS"]:
        current_frame = node.get("name", current_frame)
        
    if node.get("type") == "TEXT":
        nodes_summary.append({
            "id": str(node.get("id")),
            "name": str(node.get("name")),
            "parent_frame": str(current_frame),
            "characters": str(node.get("characters", "")).strip()
        })
    
    if "children" in node:
        for child in node["children"]:
            nodes_summary.extend(extract_text_nodes(child, current_frame))
            
    return nodes_summary

try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode("utf-8"))
        
        document = data.get("document", {})
        registry_data = []
        
        for canvas in document.get("children", []):
            page_name = canvas.get("name")
            text_nodes = extract_text_nodes(canvas)
            
            registry_data.append({
                "page": page_name,
                "total_nodes": len(text_nodes),
                "nodes": text_nodes
            })
            
        with open("registry_seed.json", "w", encoding="utf-8") as f:
            json.dump(registry_data, f, ensure_ascii=False, indent=2)
            
    print(f"SUCCESS: 'registry_seed.json' generado correctamente desde {ENV_PATH.name}.")

except Exception as e:
    print(f"ERROR: No se pudo procesar el archivo -> {e}")
