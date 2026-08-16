#!/usr/bin/env python3
"""
Script para configurar el archivo .env de Layer 1
Crea un archivo .env con las variables de entorno necesarias para los scripts
"""

import os
import sys
from pathlib import Path

def setup_env():
    """Configura el archivo .env con las variables necesarias."""
    
    layer1_path = Path(__file__).resolve().parent.parent
    env_file = layer1_path / ".env"
    
    print("🔧 Configuración de Layer_1/.env")
    print(f"📁 Ruta: {env_file}")
    print()
    
    # Verificar si ya existe
    if env_file.exists():
        print("⚠️ El archivo .env ya existe.")
        response = input("¿Deseas sobrescribirlo? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Configuración cancelada.")
            return False
    
    # Solicitar valores al usuario
    print("Por favor, proporciona los siguientes valores:")
    print()
    
    notion_token = input("NOTION_TOKEN (o presiona Enter para dejar vacío): ").strip()
    oauth_path = input("GOOGLE_OAUTH_CREDENTIALS_PATH (ruta a client_secret_...json): ").strip()
    
    # Valores por defecto para carpetas de Drive
    drive_skills = input(f"GOOGLE_DRIVE_FOLDER_SKILLS (default: VANTAGE_Skills_Manifest): ").strip()
    if not drive_skills:
        drive_skills = "VANTAGE_Skills_Manifest"
    
    drive_bootloader = input(f"GOOGLE_DRIVE_FOLDER_BOOTLOADER (default: VANTAGE_Bootloader_Exports): ").strip()
    if not drive_bootloader:
        drive_bootloader = "VANTAGE_Bootloader_Exports"
    
    # Crear contenido del archivo .env
    env_content = f"""# VANTAGE Layer 1 Environment Variables
# Generado automáticamente por setup_env.py

# Notion API
NOTION_TOKEN={notion_token if notion_token else "your_notion_token_here"}

# Google Drive OAuth 2.0
GOOGLE_OAUTH_CREDENTIALS_PATH={oauth_path if oauth_path else "/path/to/your/client_secret_...json"}

# Google Drive Configuration
GOOGLE_DRIVE_FOLDER_SKILLS={drive_skills}
GOOGLE_DRIVE_FOLDER_BOOTLOADER={drive_bootloader}
"""
    
    # Escribir archivo
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print()
        print("✅ Archivo .env creado exitosamente.")
        print(f"📁 Ubicación: {env_file}")
        print()
        print("📝 Recuerda:")
        print("   - Reemplaza 'your_notion_token_here' con tu token real")
        print("   - Reemplaza la ruta de OAuth con la ruta correcta a tu client_secret_...json")
        print("   - El archivo .env ya está en .gitignore por seguridad")
        print()
        print("🔐 Para cargar las variables de entorno:")
        print("   source Layer_1/.env  # en bash/zsh")
        print("   o usa python-dotenv en tus scripts")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando archivo .env: {e}")
        return False

if __name__ == "__main__":
    success = setup_env()
    sys.exit(0 if success else 1)