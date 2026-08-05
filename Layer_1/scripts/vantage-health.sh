#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title VANTAGE Health Check
# @raycast.mode fullOutput
# @raycast.icon 🩺
# @raycast.packageName VANTAGE
# @raycast.keywords vhealth, start

notify_success() { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Hero\""; }
notify_warning() { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Pop\""; }
notify_error()   { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Basso\""; }

cd ~/Documents/03\ Projects/VANTAGE/Layer_1/scripts || { notify_error "VANTAGE Health Check" "Ruta no encontrada"; exit 1; }
if [ -f ../.env ]; then set -a; source ../.env; set +a; fi
source ../.venv/bin/activate
export PYTHONUNBUFFERED=1

python3 health_check.py
code=$?

# health_check.py usa exit 1 para señalar "encontró issues" (git sucio, tickets sin
# prioridad, etc.), no para señalar que el script se cayó. No lo tratamos como error
# fatal de Raycast — solo cambiamos el sonido/mensaje para reflejar la severidad real.
if [ $code -eq 0 ]; then
  notify_success "VANTAGE Health Check" "✅ Sistema saludable"
else
  notify_warning "VANTAGE Health Check" "⚠️ Sistema con issues — revisar output"
fi
exit 0
