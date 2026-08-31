#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title VANTAGE Serial Generator
# @raycast.mode compact
# @raycast.icon 🔢
# @raycast.packageName VANTAGE
# @raycast.keywords vserial,handoff,serial

notify_success() { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Hero\""; }
notify_error()   { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Basso\""; }

cd ~/Documents/03\ Projects/VANTAGE/Layer_1/scripts || { notify_error "VANTAGE Serial" "Ruta no encontrada"; exit 1; }
source ../.venv/bin/activate
export PYTHONUNBUFFERED=1

SERIAL=$(python3 allocate_vantage_serial.py next 2>&1)
if [ $? -eq 0 ]; then
  echo "$SERIAL" | pbcopy
  notify_success "VANTAGE Serial" "🔢 $SERIAL (copiado)"
  echo "$SERIAL"
else
  notify_error "VANTAGE Serial" "❌ Falló la generación"
  exit 1
fi
