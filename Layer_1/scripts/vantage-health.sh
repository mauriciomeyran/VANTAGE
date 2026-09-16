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

# health_check.py (V-07 fix): 0 = OK, 1 = encontró issues (git sucio, tickets
# sin prioridad, etc — no fatal), 2 = se cayó de verdad (excepción no
# capturada en una check). Antes solo existían 0/1 y el wrapper no podía
# distinguir "hay issues" de "el script truena" — ambos caían en el mismo
# aviso de warning.
if [ $code -eq 0 ]; then
  notify_success "VANTAGE Health Check" "✅ Sistema saludable"
elif [ $code -eq 1 ]; then
  notify_warning "VANTAGE Health Check" "⚠️ Sistema con issues — revisar output"
else
  notify_error "VANTAGE Health Check" "❌ health_check.py se cayó (exit $code) — revisar output"
  exit $code
fi
exit 0
