#!/bin/bash

# Cargar variables de entorno desde Layer_1/.env
export $(grep -v '^#' /Users/mauriciomeyran/Documents/03\ Projects/VANTAGE/Layer_1/.env | xargs)

# Ejecutar el script de Python
python3 /Users/mauriciomeyran/Documents/03\ Projects/VANTAGE/vprint.py
