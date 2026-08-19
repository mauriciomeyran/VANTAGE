#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title VANTAGE Assign Next Action
# @raycast.mode fullOutput
# @raycast.icon ➡️
# @raycast.packageName VANTAGE

cd ~/Documents/03\ Projects/VANTAGE/Layer_1/scripts || exit 1
if [ -f ../.env ]; then
  set -a
  source ../.env
  set +a
fi
source ../.venv/bin/activate
python3 assign_next_action.py
