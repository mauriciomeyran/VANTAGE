#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title VANTAGE Dedup (Tracker)
# @raycast.mode fullOutput
# @raycast.icon 🧹
# @raycast.packageName VANTAGE
# @raycast.keywords vdedup

notify_success() { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Hero\""; }
notify_error()   { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Basso\""; }

cd ~/Documents/03\ Projects/VANTAGE/Layer_1/scripts || { notify_error "VANTAGE Dedup" "Ruta no encontrada"; exit 1; }
if [ -f ../.env ]; then set -a; source ../.env; set +a; fi
source ../.venv/bin/activate
export PYTHONUNBUFFERED=1

if python3 consolidate_duplicates.py; then
  notify_success "VANTAGE Dedup (Tracker)" "✅ Duplicados consolidados"
else
  code=$?
  notify_error "VANTAGE Dedup (Tracker)" "❌ Falló (exit $code)"
  exit $code
fi
