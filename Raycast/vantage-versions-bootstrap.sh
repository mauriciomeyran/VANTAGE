#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title VANTAGE Versions (Bootstrap)
# @raycast.mode fullOutput
# @raycast.icon 🧭
# @raycast.packageName VANTAGE
# @raycast.keywords vversions, bootstrap

notify_success() { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Hero\""; }
notify_error()   { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Basso\""; }

cd ~/Documents/03\ Projects/VANTAGE/Layer_1/scripts || { notify_error "VANTAGE Versions" "Ruta no encontrada"; exit 1; }
source ../.venv/bin/activate
export PYTHONUNBUFFERED=1

if python3 verify_versions.py --bootstrap; then
  notify_success "VANTAGE Versions (Bootstrap)" "✅ Dump generado"
else
  code=$?
  notify_error "VANTAGE Versions (Bootstrap)" "❌ Falló (exit $code)"
  exit $code
fi
