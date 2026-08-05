#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title VANTAGE Status
# @raycast.mode fullOutput
# @raycast.icon 📟
# @raycast.packageName VANTAGE
# @raycast.keywords vstatus

notify_success() { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Hero\""; }
notify_error()   { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Basso\""; }

cd ~/Documents/03\ Projects/VANTAGE/Layer_1/scripts || { notify_error "VANTAGE Status" "Ruta no encontrada"; exit 1; }
if [ -f ../.env ]; then set -a; source ../.env; set +a; fi
source ../.venv/bin/activate
export PYTHONUNBUFFERED=1

if python3 vantage.py status; then
  notify_success "VANTAGE Status" "✅ Status leído"
else
  code=$?
  notify_error "VANTAGE Status" "❌ Falló (exit $code)"
  exit $code
fi
