#!/usr/bin/env python3
"""
Script para exportar las páginas del bootloader de VANTAGE a Markdown y opcionalmente a Google Drive.

Las páginas del bootloader son:
- SYSTEM PROMPT (id: 37b938be-fc42-8001-9b9b-fcf81130d274)
- ID CENSUS (id: 394938be-fc42-81e6-a381-e3869e60d89d)

Uso:
    python export_bootloader_pages.py                    # Exportar a local
    python export_bootloader_pages.py --drive             # Exportar a Google Drive (requiere configuración)
    python export_bootloader_pages.py --output ./backups  # Directorio personalizado

Requisitos:
    - NOTION_TOKEN: Token de integración de Notion (variable de entorno)
    - Para Google Drive: google-api-python-client y credenciales configuradas
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Añadir el directorio de scripts al path para importar notion_utils
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from notion_utils import Client, ResolverError

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# IDs de las páginas del bootloader
BOOTLOADER_PAGES = {
    "SYSTEM_PROMPT": "37b938be-fc42-8001-9b9b-fcf81130d274",
    "ID_CENSUS": "394938be-fc42-81e6-a381-e3869e60d89d"
}


class NotionToMarkdownConverter:
    """Convierte páginas de Notion a formato Markdown."""

    def __init__(self):
        self.block_types = {
            "paragraph": self._convert_paragraph,
            "heading_1": self._convert_heading,
            "heading_2": self._convert_heading,
            "heading_3": self._convert_heading,
            "bulleted_list_item": self._convert_bulleted_list,
            "numbered_list_item": self._convert_numbered_list,
            "to_do": self._convert_todo,
            "toggle": self._convert_toggle,
            "code": self._convert_code,
            "quote": self._convert_quote,
            "divider": self._convert_divider,
            "callout": self._convert_callout,
        }

    def convert_page(self, page_data: Dict[str, Any]) -> str:
        """Convierte una página completa de Notion a Markdown."""
        lines = []
        
        # Extraer título y propiedades
        title = self._extract_title(page_data)
        lines.append(f"# {title}\n")
        
        # Procesar bloques de contenido
        if "blocks" in page_data:
            for block in page_data["blocks"]:
                block_md = self._convert_block(block)
                if block_md:
                    lines.append(block_md)
        
        return "\n".join(lines)

    def _extract_title(self, page_data: Dict[str, Any]) -> str:
        """Extrae el título de la página."""
        properties = page_data.get("properties", {})
        
        # Buscar propiedad tipo title
        for prop_name, prop_data in properties.items():
            if prop_data.get("type") == "title":
                title_array = prop_data.get("title", [])
                if title_array:
                    return title_array[0].get("plain_text", "Sin título")
        
        return "Sin título"

    def _convert_block(self, block: Dict[str, Any]) -> Optional[str]:
        """Convierte un bloque individual de Notion a Markdown."""
        block_type = block.get("type")
        
        if block_type in self.block_types:
            return self.block_types[block_type](block)
        
        # Si no hay conversor específico, intentar extraer texto plano
        if block_type in block:
            content = block[block_type]
            if isinstance(content, dict) and "rich_text" in content:
                return self._extract_rich_text(content["rich_text"])
        
        return None

    def _convert_paragraph(self, block: Dict[str, Any]) -> str:
        """Convierte un párrafo."""
        content = block.get("paragraph", {})
        text = self._extract_rich_text(content.get("rich_text", []))
        return text if text else ""

    def _convert_heading(self, block: Dict[str, Any]) -> str:
        """Convierte encabezados."""
        block_type = block.get("type")
        level = {"heading_1": 1, "heading_2": 2, "heading_3": 3}.get(block_type, 1)
        
        content = block.get(block_type, {})
        text = self._extract_rich_text(content.get("rich_text", []))
        
        if text:
            return f"{'#' * level} {text}"
        return ""

    def _convert_bulleted_list(self, block: Dict[str, Any]) -> str:
        """Convierte lista con viñetas."""
        content = block.get("bulleted_list_item", {})
        text = self._extract_rich_text(content.get("rich_text", []))
        return f"- {text}" if text else ""

    def _convert_numbered_list(self, block: Dict[str, Any]) -> str:
        """Convierte lista numerada."""
        content = block.get("numbered_list_item", {})
        text = self._extract_rich_text(content.get("rich_text", []))
        return f"1. {text}" if text else ""

    def _convert_todo(self, block: Dict[str, Any]) -> str:
        """Convierte checkbox/to-do."""
        content = block.get("to_do", {})
        text = self._extract_rich_text(content.get("rich_text", []))
        checked = content.get("checked", False)
        checkbox = "[x]" if checked else "[ ]"
        return f"{checkbox} {text}" if text else ""

    def _convert_toggle(self, block: Dict[str, Any]) -> str:
        """Convierte toggle."""
        content = block.get("toggle", {})
        text = self._extract_rich_text(content.get("rich_text", []))
        return f"<details>\n<summary>{text}</summary>\n</details>" if text else ""

    def _convert_code(self, block: Dict[str, Any]) -> str:
        """Convierte bloque de código."""
        content = block.get("code", {})
        text = self._extract_rich_text(content.get("rich_text", []))
        language = content.get("language", "")
        return f"```{language}\n{text}\n```" if text else ""

    def _convert_quote(self, block: Dict[str, Any]) -> str:
        """Convierte cita."""
        content = block.get("quote", {})
        text = self._extract_rich_text(content.get("rich_text", []))
        return f"> {text}" if text else ""

    def _convert_divider(self, block: Dict[str, Any]) -> str:
        """Convierte separador."""
        return "---"

    def _convert_callout(self, block: Dict[str, Any]) -> str:
        """Convierte callout."""
        content = block.get("callout", {})
        text = self._extract_rich_text(content.get("rich_text", []))
        emoji = content.get("icon", {}).get("emoji", "")
        return f"> {emoji} {text}" if text else ""

    def _extract_rich_text(self, rich_text_array: list) -> str:
        """Extrae texto plano de rich_text de Notion."""
        if not rich_text_array:
            return ""
        
        text_parts = []
        for text_obj in rich_text_array:
            if isinstance(text_obj, dict):
                plain_text = text_obj.get("plain_text", "")
                text_parts.append(plain_text)
        
        return "".join(text_parts)


class BootloaderExporter:
    """Exportador de páginas del bootloader."""

    def __init__(self, output_dir: str = "./bootloader_exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.converter = NotionToMarkdownConverter()
        self.client = Client()
        
    def fetch_page_blocks(self, page_id: str) -> Dict[str, Any]:
        """Recupera todos los bloques de una página de Notion."""
        if self.use_mcp:
            return self._fetch_page_blocks_mcp(page_id)
        else:
            return self._fetch_page_blocks_api(page_id)

    def _fetch_page_blocks_mcp(self, page_id: str) -> Dict[str, Any]:
        """Recupera bloques usando MCP."""
        try:
            # Implementación MCP placeholder - requiere configuración MCP real
            logger.warning("MCP mode requiere configuración MCP. Usando fallback...")
            return self._fetch_page_blocks_api(page_id)
        except Exception as e:
            logger.error(f"Error fetching blocks via MCP for page {page_id}: {e}")
            return {"blocks": []}

    def _fetch_page_blocks_api(self, page_id: str) -> Dict[str, Any]:
        """Recupera bloques usando API de Notion directo."""
        blocks = []
        start_cursor = None
        has_more = True
        
        while has_more:
            try:
                if start_cursor:
                    response = self.client.blocks.children.list(
                        block_id=page_id,
                        start_cursor=start_cursor,
                        page_size=100
                    )
                else:
                    response = self.client.blocks.children.list(
                        block_id=page_id,
                        page_size=100
                    )
                
                blocks.extend(response.get("results", []))
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")
                
            except Exception as e:
                logger.error(f"Error fetching blocks for page {page_id}: {e}")
                break
        
        return {"blocks": blocks}

    def export_page(self, page_name: str, page_id: str) -> Optional[Path]:
        """Exporta una página individual a Markdown."""
        try:
            logger.info(f"Exportando {page_name} (ID: {page_id})...")
            
            if self.use_mcp:
                page_data = self._fetch_page_mcp(page_id)
            else:
                # Recuperar datos de la página
                page_data = self.client.pages.retrieve(page_id)
            
            # Recuperar bloques de contenido
            blocks_data = self.fetch_page_blocks(page_id)
            page_data.update(blocks_data)
            
            # Convertir a Markdown
            markdown_content = self.converter.convert_page(page_data)
            
            # Guardar archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{page_name}_{timestamp}.md"
            output_path = self.output_dir / filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            logger.info(f"✓ Exportado: {output_path}")
            return output_path
            
        except ResolverError as e:
            logger.error(f"✗ Error exportando {page_name}: {e.message}")
            return None
        except Exception as e:
            logger.error(f"✗ Error inesperado exportando {page_name}: {e}")
            return None

    def _fetch_page_mcp(self, page_id: str) -> Dict[str, Any]:
        """Recupera página usando MCP."""
        try:
            # Implementación MCP placeholder
            logger.warning("MCP mode requiere configuración MCP. Usando fallback...")
            return self.client.pages.retrieve(page_id)
        except Exception as e:
            logger.error(f"Error fetching page via MCP for {page_id}: {e}")
            return {}

    def export_all_bootloader_pages(self) -> Dict[str, Optional[Path]]:
        """Exporta todas las páginas del bootloader."""
        logger.info("Iniciando exportación de páginas del bootloader...")
        logger.info(f"Directorio de salida: {self.output_dir}")
        
        results = {}
        for page_name, page_id in BOOTLOADER_PAGES.items():
            results[page_name] = self.export_page(page_name, page_id)
        
        # Resumen
        successful = sum(1 for path in results.values() if path is not None)
        logger.info(f"\nResumen: {successful}/{len(results)} páginas exportadas exitosamente")
        
        return results

    def export_to_google_drive(self, results: Dict[str, Optional[Path]]) -> bool:
        """Exporta los archivos a Google Drive (requiere configuración)."""
        try:
            from googleapiclient.discovery import build
            from google.oauth2.service_account import Credentials
            from googleapiclient.http import MediaFileUpload
            
            # Verificar credenciales
            credentials_path = os.environ.get("GOOGLE_CREDENTIALS_PATH")
            if not credentials_path or not Path(credentials_path).exists():
                logger.error("Google Drive no configurado. Set GOOGLE_CREDENTIALS_PATH")
                return False
            
            # Autenticar
            credentials = Credentials.from_service_account_file(credentials_path)
            service = build('drive', 'v3', credentials=credentials)
            
            # Crear carpeta si no existe
            folder_name = "VANTAGE_Bootloader_Exports"
            folder_id = self._get_or_create_folder(service, folder_name)
            
            # Subir archivos
            for page_name, file_path in results.items():
                if file_path and file_path.exists():
                    self._upload_file(service, file_path, folder_id)
            
            logger.info("✓ Archivos subidos a Google Drive")
            return True
            
        except ImportError:
            logger.error("Librerías de Google Drive no instaladas.")
            logger.info("Instala con: pip install google-api-python-client google-auth")
            return False
        except Exception as e:
            logger.error(f"Error exportando a Google Drive: {e}")
            return False

    def _get_or_create_folder(self, service, folder_name: str) -> str:
        """Obtiene o crea carpeta en Google Drive."""
        # Buscar carpeta existente
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query).execute()
        
        if results.get('files'):
            return results['files'][0]['id']
        
        # Crear nueva carpeta
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=folder_metadata, fields='id').execute()
        return folder['id']

    def _upload_file(self, service, file_path: Path, folder_id: str):
        """Sube un archivo a Google Drive."""
        file_metadata = {
            'name': file_path.name,
            'parents': [folder_id]
        }
        media = MediaFileUpload(str(file_path), resumable=True)
        
        service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        logger.info(f"✓ Subido: {file_path.name}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Exporta páginas del bootloader de VANTAGE a Markdown"
    )
    parser.add_argument(
        "--output", "-o",
        default="./bootloader_exports",
        help="Directorio de salida (default: ./bootloader_exports)"
    )
    parser.add_argument(
        "--api", "-a",
        action="store_true",
        help="Usar API de Notion directo (requiere NOTION_TOKEN)"
    )
    parser.add_argument(
        "--drive", "-d",
        action="store_true",
        help="Exportar también a Google Drive (requiere configuración)"
    )
    
    args = parser.parse_args()
    
    # Crear exportador (por defecto usa MCP si está disponible)
    use_mcp = not args.api
    exporter = BootloaderExporter(output_dir=args.output, use_mcp=use_mcp)
    
    # Exportar páginas
    results = exporter.export_all_bootloader_pages()
    
    # Exportar a Google Drive si se solicita
    if args.drive:
        logger.info("\nIniciando exportación a Google Drive...")
        exporter.export_to_google_drive(results)
    
    # Exit code basado en éxito
    successful = sum(1 for path in results.values() if path is not None)
    sys.exit(0 if successful == len(results) else 1)


if __name__ == "__main__":
    main()