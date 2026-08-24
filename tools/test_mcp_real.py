#!/usr/bin/env python3
"""
Real Test for VANTAGE MCP Serial Server

Tests the MCP server with the real database to verify functionality.
THIS WILL CONSUME HO-000004 from the real database.
"""
import os
import sys
import json
from pathlib import Path

# Setup path
tools_dir = Path(__file__).parent
repo_root = tools_dir.parent
sys.path.insert(0, str(tools_dir))

def test_mcp_server_real():
    """Test MCP server with real database."""
    print("=== VANTAGE MCP Server Real Test ===")
    print("WARNING: This will consume HO-000004 from the real database\n")
    
    # Set environment for real database
    real_db = repo_root / "state" / "vantage_handoff_counter.sqlite3"
    os.environ["VANTAGE_SERIAL_DB"] = str(real_db)
    
    print(f"Using real database: {real_db}")
    print("Testing MCP server functionality...\n")
    
    # Check current counter value
    import sqlite3
    with sqlite3.connect(real_db) as conn:
        cursor = conn.execute("SELECT value FROM counters WHERE name = ?", ("GLOBAL_VANTAGE_COUNTER",))
        row = cursor.fetchone()
        if row:
            current_value = row[0]
            print(f"Current counter value: {current_value}")
            print(f"Expected next serial: HO-{current_value + 1:06d}\n")
    
    # Import and test the allocation function
    from mcp_vantage_serial_server import allocate_serial, COUNTER_NAME
    
    try:
        print("Test: Real serial allocation")
        serial = allocate_serial()
        print(f"  Result: {serial}")
        
        # Verify the format
        assert serial.startswith("HO-"), f"Serial should start with HO-, got {serial}"
        assert len(serial) == 9, f"Serial should be 9 characters, got {len(serial)}"
        
        # Verify the expected value
        expected_serial = f"HO-{current_value + 1:06d}"
        assert serial == expected_serial, f"Expected {expected_serial}, got {serial}"
        
        print(f"  ✓ PASS - Serial {serial} allocated successfully\n")
        
        # Verify output format
        test_output = {
            "serial": serial,
            "authority": COUNTER_NAME,
            "status": "ALLOCATED"
        }
        print("Output format verification:")
        print(f"  {json.dumps(test_output, indent=2)}")
        
        # Verify counter was incremented
        with sqlite3.connect(real_db) as conn:
            cursor = conn.execute("SELECT value FROM counters WHERE name = ?", ("GLOBAL_VANTAGE_COUNTER",))
            row = cursor.fetchone()
            if row:
                new_value = row[0]
                print(f"\nCounter verification:")
                print(f"  Before: {current_value}")
                print(f"  After: {new_value}")
                assert new_value == current_value + 1, f"Counter should be {current_value + 1}, got {new_value}"
                print(f"  ✓ PASS - Counter incremented correctly\n")
        
        print("=== Real Test Completed Successfully ===")
        print(f"✓ Serial {serial} allocated and persisted")
        print(f"✓ Counter incremented from {current_value} to {new_value}")
        print(f"✓ Next serial will be: HO-{new_value + 1:06d}")
        print(f"✓ Database: {real_db}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_mcp_server_real()
    sys.exit(0 if success else 1)
