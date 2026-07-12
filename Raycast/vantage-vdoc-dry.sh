#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title VANTAGE Doc Sync (Dry Run)
# @raycast.mode fullOutput
# @raycast.icon 👁️
# @raycast.packageName VANTAGE

cd ~/Documents/03\ Projects/VANTAGE/Layer_4/scripts || exit 1
python3 vsync_doc.py --direction notion --dry-run
