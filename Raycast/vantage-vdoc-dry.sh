#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title VANTAGE Doc Sync (Dry Run)
# @raycast.mode fullOutput
# @raycast.icon 👁️
# @raycast.packageName VANTAGE
# @raycast.keywords vdoc, dry

notify_success() { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Hero\""; }
notify_error()   { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Basso\""; }

cd ~/Documents/03\ Projects/VANTAGE/Layer_4/scripts || { notify_error "VANTAGE Doc Sync" "Ruta no encontrada"; exit 1; }
export PYTHONUNBUFFERED=1

if python3 vsync_doc.py --direction auto --dry-run; then
  notify_success "VANTAGE Doc Sync (Dry Run)" "✅ Preview generado"
else
  code=$?
  notify_error "VANTAGE Doc Sync (Dry Run)" "❌ Falló (exit $code)"
  exit $code
fi
