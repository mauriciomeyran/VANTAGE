#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title VANTAGE Doc Sync (Notion)
# @raycast.mode fullOutput
# @raycast.icon 🔀
# @raycast.packageName VANTAGE
# @raycast.keywords vdoc, notion

notify_success() { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Hero\""; }
notify_error()   { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Basso\""; }

cd ~/Documents/03\ Projects/VANTAGE/Layer_4/scripts || { notify_error "VANTAGE Doc Sync" "Ruta no encontrada"; exit 1; }
export PYTHONUNBUFFERED=1

if python3 vsync_doc.py --direction notion; then
  notify_success "VANTAGE Doc Sync (Notion)" "✅ Documentos sincronizados"
else
  code=$?
  notify_error "VANTAGE Doc Sync (Notion)" "❌ Falló (exit $code)"
  exit $code
fi