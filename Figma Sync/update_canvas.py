import json
import urllib.request
import os
from pathlib import Path

ENV_PATH = Path("/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/config/layer_1.env")
FILE_KEY = "ga1c5atiei7v0wVNmBhtqD"

def load_env_file(filepath):
    env_vars = {}
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                env_vars[key.strip()] = val.strip().strip("'\"")
    return env_vars

env = load_env_file(ENV_PATH)
FIGMA_TOKEN = env.get("FIGMA_ACCESS_TOKEN")

# Cargar el JSON corregido (asegúrate que el archivo local esté guardado)
with open("registry_seed.json", "r", encoding="utf-8") as f:
    nodes_data = json.load(f)

# Si el JSON viene con wrapper (page/nodes), extraemos la lista plana
if isinstance(nodes_data, list) and "nodes" in nodes_data[0]:
    flat_nodes = nodes_data[0]["nodes"]
else:
    flat_nodes = nodes_data

print(f"Iniciando verificación de {len(flat_nodes)} nodos contra la API REST...")

# Mapear los nodos por ID
updates = {item["id"]: item["characters"] for item in flat_nodes if "id" in item and "characters" in item}

# Verificar accesibilidad en la API
url = f"https://api.figma.com/v1/files/{FILE_KEY}/nodes?ids={','.join(list(updates.keys())[:10])}"
req = urllib.request.Request(url, headers={"X-Figma-Token": FIGMA_TOKEN})

try:
    with urllib.request.urlopen(req) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        found_nodes = res_data.get("nodes", {})
        print(f"Nodos validados correctamente en el servidor: {len(found_nodes)} / 10 comprobados.")
except Exception as e:
    print(f"Error comprobando nodos: {e}")
