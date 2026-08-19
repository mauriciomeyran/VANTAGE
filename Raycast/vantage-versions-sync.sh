#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title VANTAGE Versions (Sync)
# @raycast.mode fullOutput
# @raycast.icon 🔁
# @raycast.packageName VANTAGE
# @raycast.keywords vversions, sync

notify_success() { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Hero\""; }
notify_error()   { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Basso\""; }

cd ~/Documents/03\ Projects/VANTAGE/Layer_1/scripts || { notify_error "VANTAGE Versions" "Ruta no encontrada"; exit 1; }
source ../.venv/bin/activate
export PYTHONUNBUFFERED=1

echo "⚠️  Propaga versión del CHANGELOG a los 9 documentos restantes + verificación por relectura (PASS/FAIL real)."
if python3 verify_versions.py --sync; then
  notify_success "VANTAGE Versions (Sync)" "✅ Sync PASS en todos los documentos"
else
  code=$?
  notify_error "VANTAGE Versions (Sync)" "❌ FAIL en al menos un documento (exit $code)"
  exit $code
fi
