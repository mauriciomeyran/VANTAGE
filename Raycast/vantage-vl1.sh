#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title VANTAGE L1 Run (orchestrator v9)
# @raycast.mode fullOutput
# @raycast.icon 🚀
# @raycast.packageName VANTAGE
# @raycast.keywords vl1

notify_success() { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Hero\""; }
notify_error()   { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Basso\""; }

cd ~/Documents/03\ Projects/VANTAGE/Layer_1 || { notify_error "VANTAGE L1 Run" "Ruta no encontrada"; exit 1; }
if [ -f .env ]; then set -a; source .env; set +a; fi
source .venv/bin/activate
export PYTHONUNBUFFERED=1

# G6: layer_1_pipeline.sh → layer_1_orchestrator.py (dry-run default)
if bash layer_1_pipeline.sh; then
  notify_success "VANTAGE L1 Run" "✅ Pipeline L1 completado"
else
  code=$?
  notify_error "VANTAGE L1 Run" "❌ Falló (exit $code)"
  exit $code
fi
