#!/bin/bash
# git_sync_wrapper.sh — VANTAGE L4 wrapper para launchd / alias vgit
# Ruta canónica: ~/Documents/04-VANTAGE_CV/Layer_4/wrappers/git_sync_wrapper.sh

notify_success() {
    osascript -e "display notification \"$2\" with title \"$1\" sound name \"Hero\""
}

notify_error() {
    osascript -e "display notification \"$2\" with title \"$1\" sound name \"Basso\""
}

SCRIPT="$HOME/Documents/04-VANTAGE_CV/Layer_4/scripts/git_sync.py"
VENV="$HOME/Documents/04-VANTAGE_CV/Layer_1/.venv/bin/python3"

OUTPUT=$("$VENV" "$SCRIPT" 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    if echo "$OUTPUT" | grep -q "Sync OK"; then
        notify_success "VANTAGE L4" "$OUTPUT"
    fi
else
    notify_error "VANTAGE L4" "❌ Error: $OUTPUT"
fi

exit $EXIT_CODE
