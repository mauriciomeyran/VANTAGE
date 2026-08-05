#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title VANTAGE Doc Sync (Auto)
# @raycast.mode fullOutput
# @raycast.icon 🔀
# @raycast.packageName VANTAGE
# @raycast.keywords vdoc, auto

notify_success() { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Hero\""; }
notify_error()   { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Basso\""; }

cd ~/Documents/03\ Projects/VANTAGE/Layer_4/scripts || { notify_error "VANTAGE Doc Sync" "Ruta no encontrada"; exit 1; }
export PYTHONUNBUFFERED=1

if python3 vsync_doc.py --direction auto; then
  notify_success "VANTAGE Doc Sync (Auto)" "✅ Documentos sincronizados"
else
  code=$?
  notify_error "VANTAGE Doc Sync (Auto)" "❌ Falló (exit $code)"
  exit $code
fi
