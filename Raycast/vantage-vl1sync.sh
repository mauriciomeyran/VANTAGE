#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title VANTAGE L1 Sync (F13b, dry-run)
# @raycast.mode fullOutput
# @raycast.icon 🔄
# @raycast.packageName VANTAGE
# @raycast.keywords vl1s

notify_success() { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Hero\""; }
notify_error()   { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Basso\""; }

cd ~/Documents/03\ Projects/VANTAGE/Layer_1 || { notify_error "VANTAGE L1 Sync" "Ruta no encontrada"; exit 1; }
if [ -f .env ]; then set -a; source .env; set +a; fi
source .venv/bin/activate
export PYTHONUNBUFFERED=1

if bash layer_1_pipeline.sh sync; then
  notify_success "VANTAGE L1 Sync" "✅ Sync F13b completado (dry-run)"
else
  code=$?
  notify_error "VANTAGE L1 Sync" "❌ Falló (exit $code)"
  exit $code
fi
