#!/usr/bin/env python3
"""
VANTAGE Serial Allocation MCP Server

Exposes allocate_vantage_serial functionality as an MCP tool.
Reuses existing logic from Layer_1/scripts/allocate_vantage_serial.py
"""
from __future__ import annotations

import os
import sys
import json
import sqlite3
from pathlib import Path
from typing import Any

# Add Layer_1/scripts to path to import existing logic
layer1_scripts = Path(__file__).parent.parent / "Layer_1" / "scripts"
sys.path.insert(0, str(layer1_scripts))

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    Server = None
    stdio_server = None
    Tool = None
    TextContent = None

# Constants from allocate_vantage_serial.py
DB_PATH = Path(os.environ.get("VANTAGE_SERIAL_DB", 
           Path(__file__).parent.parent / "state" / "vantage_handoff_counter.sqlite3"))
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
    """Create and configure the MCP server."""
    if not MCP_AVAILABLE:
        raise RuntimeError("MCP SDK not installed. Install with: pip install mcp")

    server = Server("vantage-serial")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available tools."""
        return [
            Tool(
                name="allocate_vantage_serial",
                description="Allocate the next VANTAGE handoff serial number from GLOBAL_VANTAGE_COUNTER",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: Any) -> list[TextContent]:
        """Handle tool calls."""
        if name == "allocate_vantage_serial":
            try:
                serial = allocate_serial()
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "serial": serial,
                            "authority": COUNTER_NAME,
                            "status": "ALLOCATED"
                        })
                    )
                ]
            except Exception as exc:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "HANDOFF_SERIAL_UNAVAILABLE",
                            "status": "UNAVAILABLE",
                            "detail": str(exc)
                        })
                    )
                ]
        else:
            raise ValueError(f"Unknown tool: {name}")

    return server


def main():
    """Main entry point for the MCP server."""
    if not MCP_AVAILABLE:
        print("Error: MCP SDK not installed", file=sys.stderr)
        print("Install with: pip install mcp", file=sys.stderr)
        sys.exit(1)

    server = create_mcp_server()
    
    # Run using stdio transport
    import asyncio
    asyncio.run(stdio_server(server))


if __name__ == "__main__":
    main()
