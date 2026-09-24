#!/bin/bash
# mcp_sync_wrapper.sh — VANTAGE L4
# Wrapper para orquestar writes MCP + sync automático de documentos fundacionales
#
# Este script está diseñado para ser usado después de un write MCP a Notion.
# Si el write fue a uno de los 6 documentos fundacionales, dispara automáticamente
# el sync Notion→local para mantener los mirrors actualizados.
#
# Uso:
#   ./mcp_sync_wrapper.sh <page_id>
#
# Donde <page_id> es el ID de la página Notion que se acaba de modificar vía MCP.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ -z "$1" ]; then
    echo "Uso: $0 <page_id>"
    echo "Dispara sync Notion→local si el page_id es un documento fundacional."
    exit 1
fi

PAGE_ID="$1"

# Ejecutar el wrapper Python
python3 "$SCRIPT_DIR/trigger_sync_after_mcp_write.py" "$PAGE_ID"
