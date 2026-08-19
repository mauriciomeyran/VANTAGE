#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title VANTAGE Scripts Gap Report
# @raycast.mode fullOutput
# @raycast.icon 🔍
# @raycast.packageName VANTAGE
# @raycast.keywords vversions, scripts, gap

notify_success() { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Hero\""; }
notify_error()   { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Basso\""; }

cd ~/Documents/03\ Projects/VANTAGE/Layer_1/scripts || { notify_error "VANTAGE Scripts Gap" "Ruta no encontrada"; exit 1; }
source ../.venv/bin/activate
export PYTHONUNBUFFERED=1

if python3 verify_versions.py --scripts; then
  notify_success "VANTAGE Scripts Gap Report" "✅ Reporte generado"
else
  code=$?
  notify_error "VANTAGE Scripts Gap Report" "❌ Falló (exit $code)"
  exit $code
fi
