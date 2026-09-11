#!/usr/bin/env python3
"""
Rollback Script for Schema Migration (G4d)

Restores original option values after PATCH operation.
Usage: python3 rollback_schema_migration.py --input backup_file.json
"""

import json
import sys
from pathlib import Path


def rollback_from_backup(backup_file: str):
    """
    Restore Tracker from pre-migration backup.
    
    Args:
        backup_file: Path to JSON backup file
    """
    backup_path = Path(backup_file)
    if not backup_path.exists():
        print(f"Error: Backup file not found: {backup_file}")
        sys.exit(1)
    
    with open(backup_path) as f:
        backup_data = json.load(f)
    
    print(f"Loaded backup with {len(backup_data)} records")
    print("To restore to Notion, use restore_tracker.py with this backup")
    print("Note: This script validates backup format only")
    print("Actual restoration requires Notion client integration")
    
    # Validate backup structure
    required_fields = ["id", "properties"]
    for i, record in enumerate(backup_data):
        for field in required_fields:
            if field not in record:
                print(f"Error: Record {i} missing field '{field}'")
                sys.exit(1)
    
    print("✓ Backup validation passed")
    return backup_data


if __name__ == "__main__":
    if len(sys.argv) < 2 or "--input" not in sys.argv:
        print("Usage: python3 rollback_schema_migration.py --input backup_file.json")
        sys.exit(1)
    
    backup_file = sys.argv[sys.argv.index("--input") + 1]
    rollback_from_backup(backup_file)
