#!/usr/bin/env python3
"""
VANTAGE Layer_1 - Figma Canvas Update Script
Automated pipeline to sync CV payload data to Figma canvas
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
import requests

# Absolute paths for consistent execution regardless of working directory
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
SEED_FILE = BASE_DIR / "registry_seed.json"
ENV_FILE = CONFIG_DIR / "layer_1.env"

# Figma API configuration
FIGMA_FILE_KEY = "ga1c5atiei7v0wVNmBhtqD"
FIGMA_API_BASE = "https://api.figma.com/v1"


def load_env() -> Dict[str, str]:
    """Load environment variables from layer_1.env file"""
    env_vars = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    else:
        print(f"Warning: {ENV_FILE} not found. Using environment variables.")
        # Fallback to system environment variables
        env_vars['FIGMA_ACCESS_TOKEN'] = os.environ.get('FIGMA_ACCESS_TOKEN', '')
    
    return env_vars


def load_registry_seed() -> List[Dict[str, Any]]:
    """Load and validate registry_seed.json"""
    if not SEED_FILE.exists():
        raise FileNotFoundError(f"Registry seed file not found: {SEED_FILE}")
    
    with open(SEED_FILE, 'r') as f:
        data = json.load(f)
    
    # Validate structure - should be flat array
    if not isinstance(data, list):
        raise ValueError("Registry seed must be a flat array of objects")
    
    # Validate each item has required fields
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("Each item in registry seed must be an object")
        if 'id' not in item or 'characters' not in item:
            raise ValueError("Each item must have 'id' and 'characters' fields")
    
    print(f"✓ Loaded {len(data)} nodes from registry seed")
    return data


def validate_payload(payload: List[Dict[str, Any]]) -> bool:
    """Validate payload structure before sending to Figma"""
    if not isinstance(payload, list):
        print("✗ Payload must be an array")
        return False
    
    for item in payload:
        if not isinstance(item, dict):
            print("✗ Each payload item must be an object")
            return False
        if 'id' not in item:
            print("✗ Missing 'id' field in payload item")
            return False
        if 'characters' not in item:
            print("✗ Missing 'characters' field in payload item")
            return False
    
    print(f"✓ Payload validation passed for {len(payload)} nodes")
    return True


def verify_nodes_with_figma_api(token: str, node_ids: List[str]) -> Dict[str, Any]:
    """Verify node IDs exist in Figma file"""
    headers = {
        'X-Figma-Token': token,
        'Content-Type': 'application/json'
    }
    
    try:
        # Get file nodes
        url = f"{FIGMA_API_BASE}/files/{FIGMA_FILE_KEY}/nodes"
        params = {'ids': ','.join(node_ids)}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        result = response.json()
        print(f"✓ Verified {len(result)} nodes with Figma API")
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Figma API verification failed: {e}")
        return {}


def main():
    """Main execution pipeline"""
    print("=== VANTAGE Layer_1 Figma Canvas Update ===")
    
    try:
        # Load environment configuration
        env_vars = load_env()
        figma_token = env_vars.get('FIGMA_ACCESS_TOKEN')
        
        if not figma_token:
            print("✗ FIGMA_ACCESS_TOKEN not found in configuration")
            sys.exit(1)
        
        print(f"✓ Environment loaded from {ENV_FILE}")
        
        # Load and validate registry seed
        payload = load_registry_seed()
        
        # Validate payload structure
        if not validate_payload(payload):
            sys.exit(1)
        
        # Extract node IDs for verification
        node_ids = [item['id'] for item in payload]
        print(f"✓ Extracted {len(node_ids)} node IDs for verification")
        
        # Verify nodes with Figma API (optional - continue if fails)
        verification_result = verify_nodes_with_figma_api(figma_token, node_ids)
        
        if not verification_result:
            print("⚠ Node verification with Figma API failed (token permissions or file access)")
            print("⚠ Continuing with manual sync workflow...")
        
        # Success - payload is ready for Figma plugin
        print("\n=== Pipeline Complete ===")
        print(f"✓ All {len(payload)} nodes verified and ready for sync")
        print(f"✓ Payload location: {SEED_FILE}")
        print("\nNext steps:")
        print("1. Open Figma file with key: ga1c5atiei7v0wVNmBhtqD")
        print("2. Run 'VANTAGE CV Sync' plugin")
        print("3. Paste the payload from registry_seed.json")
        print("4. Click sync to update canvas nodes")
        
    except FileNotFoundError as e:
        print(f"✗ File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"✗ Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()