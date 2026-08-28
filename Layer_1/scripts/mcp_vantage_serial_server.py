#!/usr/bin/env python3
"""
VANTAGE Serial Allocation MCP Server

Exposes allocate_vantage_serial functionality as an MCP tool for Claude.
Reuses existing logic from Layer_1/scripts/allocate_vantage_serial.py
"""
from __future__ import annotations

import os
import sys
import json
import sqlite3
from pathlib import Path
from typing import Any

# Add current directory to path to import existing logic
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

# Import functions from allocate_vantage_serial.py
# We're in the same directory, so we can import directly
try:
    # Import the specific functions we need
    from allocate_vantage_serial import allocate_serial, initialize, COUNTER_NAME, DB_PATH
except ImportError:
    # If that fails, define them inline (fallback)
    COUNTER_NAME = "GLOBAL_VANTAGE_COUNTER"
    DB_PATH = Path(os.environ.get("VANTAGE_SERIAL_DB", 
               Path(__file__).parent.parent.parent / "state" / "vantage_handoff_counter.sqlite3"))
    
    def initialize(conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS counters (
                name TEXT PRIMARY KEY,
                value INTEGER NOT NULL CHECK(value >= 0)
            )
            """
        )
        conn.execute(
            "INSERT OR IGNORE INTO counters(name, value) VALUES (?, ?)",
            (COUNTER_NAME, 0),
        )
        conn.commit()

    def allocate_serial() -> str:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(DB_PATH, timeout=30) as conn:
            initialize(conn)
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                "UPDATE counters SET value = value + 1 WHERE name = ?",
                (COUNTER_NAME,),
            )
            row = conn.execute(
                "SELECT value FROM counters WHERE name = ?",
                (COUNTER_NAME,),
            ).fetchone()
            if row is None:
                raise RuntimeError("GLOBAL_VANTAGE_COUNTER is unavailable")
            return f"HO-{row[0]:06d}"

try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    FastMCP = None

# Constants from allocate_vantage_serial.py
DB_PATH = Path(os.environ.get("VANTAGE_SERIAL_DB", 
           str(Path(__file__).resolve().parent.parent.parent / "state" / "vantage_handoff_counter.sqlite3")))
COUNTER_NAME = "GLOBAL_VANTAGE_COUNTER"


def initialize(conn: sqlite3.Connection) -> None:
    """Initialize the counters table if it doesn't exist."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS counters (
            name TEXT PRIMARY KEY,
            value INTEGER NOT NULL CHECK(value >= 0)
        )
        """
    )
    conn.execute(
        "INSERT OR IGNORE INTO counters(name, value) VALUES (?, ?)",
        (COUNTER_NAME, 0),
    )
    conn.commit()


def allocate_serial() -> str:
    """Allocate the next serial number from the counter."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH, timeout=30) as conn:
        initialize(conn)
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            "UPDATE counters SET value = value + 1 WHERE name = ?",
            (COUNTER_NAME,),
        )
        row = conn.execute(
            "SELECT value FROM counters WHERE name = ?",
            (COUNTER_NAME,),
        ).fetchone()
        if row is None:
            raise RuntimeError("GLOBAL_VANTAGE_COUNTER is unavailable")
        return f"HO-{row[0]:06d}"


def create_mcp_server() -> Any:
    """Create and configure the MCP server using FastMCP."""
    if not MCP_AVAILABLE:
        raise RuntimeError("MCP SDK not installed. Install with: pip install mcp")

    mcp = FastMCP("vantage-serial")

    @mcp.tool()
    def allocate_vantage_serial() -> str:
        """Allocate the next VANTAGE handoff serial number from GLOBAL_VANTAGE_COUNTER."""
        try:
            serial = allocate_serial()
            return json.dumps({
                "serial": serial,
                "authority": COUNTER_NAME,
                "status": "ALLOCATED"
            })
        except Exception as exc:
            return json.dumps({
                "error": "HANDOFF_SERIAL_UNAVAILABLE",
                "status": "UNAVAILABLE",
                "detail": str(exc)
            })

    return mcp


def main():
    """Main entry point for the MCP server."""
    if not MCP_AVAILABLE:
        print("Error: MCP SDK not installed", file=sys.stderr)
        print("Install with: pip install mcp", file=sys.stderr)
        sys.exit(1)

    mcp = create_mcp_server()
    mcp.run()


if __name__ == "__main__":
    main()
