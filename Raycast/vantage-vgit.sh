#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title VANTAGE Git Sync
# @raycast.mode fullOutput
# @raycast.icon 🔧
# @raycast.packageName VANTAGE
# @raycast.keywords vgit

notify_success() { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Hero\""; }
notify_error()   { osascript -e "display notification \"$2\" with title \"$1\" sound name \"Basso\""; }

export PYTHONUNBUFFERED=1
if bash ~/Documents/03\ Projects/VANTAGE/Layer_4/wrappers/git_sync_wrapper.sh; then
  notify_success "VANTAGE Git Sync" "✅ Push completado"
else
  code=$?
  notify_error "VANTAGE Git Sync" "❌ Falló (exit $code)"
  exit $code
fi
