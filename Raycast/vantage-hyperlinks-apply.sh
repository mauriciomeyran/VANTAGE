#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title VANTAGE Hyperlinks (APPLY - Write)
# @raycast.mode fullOutput
# @raycast.icon ⚠️
# @raycast.packageName VANTAGE
# @raycast.keywords vhyperlinks, apply, write

notify_success() { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Hero\""; }
notify_error()   { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Basso\""; }

cd ~/Documents/03\ Projects/VANTAGE/Layer_4/scripts || { notify_error "VANTAGE Hyperlinks" "Ruta no encontrada"; exit 1; }
if [ -f ../.env ]; then set -a; source ../.env; set +a; fi
source ../.venv/bin/activate
export PYTHONUNBUFFERED=1

echo "⚠️  ESCRITURA REAL sobre bloques de Notion (PATCH puntual). Confirma que ya corriste el dry-run."
if python3 apply_hyperlinks_notion.py --all --apply; then
  notify_success "VANTAGE Hyperlinks (APPLY)" "✅ Escritura completada"
else
  code=$?
  notify_error "VANTAGE Hyperlinks (APPLY)" "❌ Falló (exit $code)"
  exit $code
fi
