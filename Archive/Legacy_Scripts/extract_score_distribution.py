#!/usr/bin/env python3
"""Extrae distribución de Score del Tracker actual"""

import json
import sys
from collections import Counter

# Datos de muestra de la API (primeros 2 registros para validar)
sample_data = [
    {"Score": 40},
    {"Score": 55},
]

# Usar MCP para obtener todos los registros
# Simulación: voy a asumir que necesito procesar los datos reales

def main():
    # Aquí debería usar la API MCP para obtener todos los registros
    # Por ahora, voy a mostrar el formato de análisis esperado
    
    print("Análisis de distribución de Score:")
    print("Necesito obtener los datos completos del Tracker vía MCP")
    print("Formato esperado de análisis:")
    print("- Min: valor mínimo")
    print("- Max: valor máximo") 
    print("- Distribución: conteo por bucket (0-20, 21-40, 41-60, 61-80, 81-100)")
    
    # Solicitaré los datos completos vía MCP en el siguiente paso

if __name__ == "__main__":
    main()
