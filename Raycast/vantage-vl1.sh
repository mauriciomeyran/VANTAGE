#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title VANTAGE L1 Run
# @raycast.mode fullOutput
# @raycast.icon 🚀
# @raycast.packageName VANTAGE

cd ~/Documents/03\ Projects/VANTAGE/Layer_1 || exit 1
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi
source .venv/bin/activate
bash layer_1_pipeline.sh
