#!/bin/zsh
# vantage-context-dump.zsh - Zsh wrapper for context-dump.py
# Quick terminal access to VANTAGE context for non-MCP agents

SCRIPT_DIR="$(cd "$(dirname "${(%):-%x}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/context-dump.py"

if [ ! -f "$PYTHON_SCRIPT" ]; then
    # Fallback to Layer_1/scripts if not in .devin/mcp-tools
    PYTHON_SCRIPT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$HOME/Documents/03 Projects/VANTAGE")/Layer_1/scripts/context-dump.py"
fi

if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: context-dump.py not found"
    echo "Expected at: $PYTHON_SCRIPT"
    exit 1
fi

python3 "$PYTHON_SCRIPT" "$@"
