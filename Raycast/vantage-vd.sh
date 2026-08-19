#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title VANTAGE Dashboard
# @raycast.mode fullOutput
# @raycast.icon 📊
# @raycast.packageName VANTAGE
# @raycast.keywords vd, dashboard

notify_success() { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Hero\""; }
notify_error()   { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Basso\""; }

export PYTHONUNBUFFERED=1
if bash ~/Documents/03\ Projects/VANTAGE/Dashboard/wrappers/dashboard_start.sh; then
  notify_success "VANTAGE Dashboard" "✅ Dashboard arrancado"
else
  code=$?
  notify_error "VANTAGE Dashboard" "❌ Falló (exit $code)"
  exit $code
fi
