#!/usr/bin/env python3
"""
Demo del exportador de páginas del bootloader con datos simulados.
Este script muestra la funcionalidad sin requerir token de Notion real.
"""

import json
from pathlib import Path
from datetime import datetime
from export_bootloader_pages import NotionToMarkdownConverter

# Datos simulados que representan las páginas del bootloader
MOCK_PAGES = {
    "SYSTEM_PROMPT": {
        "properties": {
            "title": {
                "type": "title",
                "title": [{"plain_text": "SYSTEM PROMPT"}]
            }
        },
        "blocks": [
            {
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"plain_text": "01 SP:BOOTLOADER"}]
                }
            },
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"plain_text": "Especificación del Bootloader"}]
                }
            },
            {
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"plain_text": "Alcance: El Bootloader se limita exclusivamente a la carga de contexto inicial"}]
                }
            },
            {
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"plain_text": "Validación: La verificación de versión corresponde a un proceso posterior"}]
                }
            },
            {
                "type": "divider",
                "divider": {}
            },
            {
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"plain_text": "Proceso de inicio"}]
                }
            },
            {
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [{"plain_text": "Responde únicamente: BOOTLOADING..."}]
                }
            },
            {
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [{"plain_text": "Recupera vía notion-fetch: SYSTEM PROMPT, ID CENSUS y SKILLS MANIFEST"}]
                }
            },
            {
                "type": "to_do",
                "to_do": {
                    "rich_text": [{"plain_text": "Verificar integridad de documentos"}],
                    "checked": True
                }
            },
            {
                "type": "to_do",
                "to_do": {
                    "rich_text": [{"plain_text": "Inicializar sesión formal"}],
                    "checked": False
                }
            }
        ]
    },
    "ID_CENSUS": {
        "properties": {
            "title": {
                "type": "title",
                "title": [{"plain_text": "ID CENSUS"}]
            }
        },
        "blocks": [
            {
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"plain_text": "CÉDULA DIGITAL"}]
                }
            },
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"plain_text": "Inventario de componentes y recursos del sistema VANTAGE"}]
                }
            },
            {
                "type": "divider",
                "divider": {}
            },
            {
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"plain_text": "Documentos Fundacionales"}]
                }
            },
            {
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"plain_text": "VANTAGE CENTRAL HUB | 36e938be-fc42-81d6-bf40-dfe7dee782a5"}]
                }
            },
            {
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"plain_text": "SYSTEM PROMPT | 37b938be-fc42-8001-9b9b-fcf81130d274"}]
                }
            },
            {
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"plain_text": "TECHNICAL KERNEL | 377938be-fc42-805e-a408-c9ae518d4fe7"}]
                }
            },
            {
                "type": "callout",
                "callout": {
                    "rich_text": [{"plain_text": "Este documento es la fuente de verdad para identificadores de recursos"}],
                    "icon": {"emoji": "📋"}
                }
            }
        ]
    }
}

# Datos simulados del SKILLS MANIFEST (JSON)
MOCK_SKILLS_MANIFEST = {
    "triggers": [
        {
            "trigger": "QA",
            "description": "Análisis de preguntas sobre documentación",
            "skill_path": "skills/qa_skill.md"
        },
        {
            "trigger": "CV-A",
            "description": "Análisis de CV - Primer nivel",
            "skill_path": "skills/cv_a_skill.md"
        },
        {
            "trigger": "SYNC",
            "description": "Sincronización de documentación",
            "skill_path": "skills/sync_skill.md"
        }
    ],
    "version": "1.0.0",
    "last_updated": "2026-08-15"
}

def main():
    """Ejecuta demo del exportador con datos simulados."""
    print("🚀 Demo: Exportador de páginas del bootloader\n")
    print("ℹ️  Nota: El SKILLS MANIFEST se maneja en update_triggers_json.py con Google Drive\n")
    
    # Crear directorio de salida
    output_dir = Path("./demo_exports")
    output_dir.mkdir(exist_ok=True)
    
    # Crear conversor
    converter = NotionToMarkdownConverter()
    
    # Procesar cada página simulada de Notion
    for page_name, page_data in MOCK_PAGES.items():
        print(f"📄 Procesando {page_name}...")
        
        # Convertir a Markdown
        markdown_content = converter.convert_page(page_data)
        
        # Guardar archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{page_name}_{timestamp}.md"
        output_path = output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✅ Exportado: {output_path}")
        print(f"📝 Contenido generado:\n")
        print(markdown_content[:200] + "..." if len(markdown_content) > 200 else markdown_content)
        print("\n" + "="*50 + "\n")
    
    print(f"🎉 Demo completada. Archivos guardados en: {output_dir}")
    print(f"� Total de páginas exportadas: {len(MOCK_PAGES)} (páginas Notion del bootloader)")
    print(f"� SKILLS MANIFEST: ver update_triggers_json.py para Google Drive sync")

if __name__ == "__main__":
    main()