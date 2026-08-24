#!/usr/bin/env python3
"""
Wrapper para el alias start que inicia el servicio de seriales si no está corriendo.
"""
import subprocess
import sys
import time
from pathlib import Path

SERIAL_SCRIPT = Path(__file__).parent / "allocate_vantage_serial.py"
HEALTH_CHECK_SCRIPT = Path(__file__).parent / "health_check.py"

def check_serial_service_running():
    """Verifica si el servicio de seriales ya está corriendo."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "allocate_vantage_serial.py serve"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False

def start_serial_service():
    """Inicia el servicio de seriales en background."""
    try:
        subprocess.Popen(
            ["python3", str(SERIAL_SCRIPT), "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        print("🚀 Iniciando servicio de seriales en background...")
        time.sleep(2)  # Dar tiempo al servicio para iniciar
        return True
    except Exception as e:
        print(f"⚠️  Error iniciando servicio de seriales: {e}")
        return False

def main():
    # Cambiar al directorio Layer_1
    layer1_dir = Path(__file__).parent
    import os
    os.chdir(layer1_dir)
    
    # Verificar/iniciar servicio de seriales
    if not check_serial_service_running():
        start_serial_service()
    else:
        print("✓ Servicio de seriales ya está corriendo")
    
    # Ejecutar health check (sin argumentos extra para evitar el error)
    result = subprocess.run(
        ["python3", str(HEALTH_CHECK_SCRIPT)]
    )
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
