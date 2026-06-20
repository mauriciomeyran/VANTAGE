#!/usr/bin/env python3
"""
Agregar opción APPLIED a Gate_Decision automáticamente
"""

import os
from dotenv import load_dotenv
from notion_utils import Client

def main():
    load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
    client = Client(auth=os.environ["NOTION_TOKEN"])
    ds_id = "4e542b37-6e52-4418-89b7-a0eeb3138307"

    print("🔧 Agregando opción APPLIED a Gate_Decision...")
    
    # Obtener schema actual
    current_props = client.data_sources.retrieve(data_source_id=ds_id)["properties"]
    gate_opts = current_props["Gate_Decision"]["select"]["options"]
    
    # Verificar si APPLIED ya existe
    if any(opt["name"] == "APPLIED" for opt in gate_opts):
        print("✅ Opción APPLIED ya existe")
        return
    
    # Agregar APPLIED a las opciones
    new_opts = gate_opts + [{"name": "APPLIED", "color": "green"}]
    
    # Actualizar
    client.data_sources.update(
        data_source_id=ds_id,
        properties={
            "Gate_Decision": {
                "select": {
                    "options": new_opts
                }
            }
        }
    )
    
    print("✅ Opción 'APPLIED' agregada a Gate_Decision")

if __name__ == "__main__":
    main()