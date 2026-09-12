#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title VANTAGE Dedup (Tracker)
# @raycast.mode fullOutput
# @raycast.icon 🧹
# @raycast.packageName VANTAGE
# @raycast.keywords vdedup

notify_success() { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Hero\""; }
notify_error()   { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Basso\""; }

# G6: consolidate_duplicates.py → Archive/ (dedup unificado vive en orquestador F6)
cd ~/Documents/03\ Projects/VANTAGE || { notify_error "VANTAGE Dedup" "Ruta no encontrada"; exit 1; }
if [ -f Layer_1/.env ]; then set -a; source Layer_1/.env; set +a; fi
if [ -f Layer_1/.venv/bin/activate ]; then source Layer_1/.venv/bin/activate; fi
export PYTHONUNBUFFERED=1

ARCHIVED="Archive/Legacy_Scripts/consolidate_duplicates.py"
if [ ! -f "$ARCHIVED" ]; then
  notify_error "VANTAGE Dedup" "Script archivado no encontrado"
  exit 1
fi
echo "ℹ️  G6: consolidate_duplicates está en Archive/."
echo "   Dedup unificado del pipeline: layer_1_orchestrator.py --dedup-audit"
echo "   Este Raycast invoca el script archivado SOLO bajo confirmación operativa."
echo ""
# Preferir orquestador F6 dry-run (cero trash físico)
cd Layer_1 || exit 1
if python3 scripts/layer_1_orchestrator.py --dry-run --dedup-audit; then
  notify_success "VANTAGE Dedup (Tracker)" "✅ Dedup audit (orquestador, dry-run)"
else
  code=$?
  notify_error "VANTAGE Dedup (Tracker)" "❌ Falló (exit $code)"
  exit $code
fi
