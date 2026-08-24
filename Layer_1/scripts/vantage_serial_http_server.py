#!/usr/bin/env python3
"""
VANTAGE Serial Allocation HTTP Server

Central HTTP server for VANTAGE handoff serial allocation.
Accessible by all agents (Claude, Gemini, ChatGPT, etc.) via HTTP API.
"""
from __future__ import annotations

import os
import json
import sqlite3
from pathlib import Path
from typing import Any
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

# Constants
DB_PATH = Path(os.environ.get("VANTAGE_SERIAL_DB", 
           Path(__file__).parent.parent.parent / "state" / "vantage_handoff_counter.sqlite3"))
COUNTER_NAME = "GLOBAL_VANTAGE_COUNTER"
DEFAULT_PORT = int(os.environ.get("VANTAGE_SERIAL_PORT", "8787"))
DEFAULT_HOST = os.environ.get("VANTAGE_SERIAL_HOST", "localhost")


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


def get_status() -> dict:
    """Get current status of the serial service."""
    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(DB_PATH, timeout=30) as conn:
            initialize(conn)
            row = conn.execute(
                "SELECT value FROM counters WHERE name = ?",
                (COUNTER_NAME,),
            ).fetchone()
            current_value = row[0] if row else 0
            next_serial = f"HO-{current_value + 1:06d}"
            
            return {
                "status": "ok",
                "authority": COUNTER_NAME,
                "current_value": current_value,
                "next_serial": next_serial,
                "database": str(DB_PATH)
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


class VantageSerialHandler(BaseHTTPRequestHandler):
    """HTTP request handler for VANTAGE serial allocation."""
    
    def send_json_response(self, data: dict, status_code: int = 200) -> None:
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_OPTIONS(self) -> None:
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self) -> None:
        """Handle GET requests."""
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == '/health':
            self.send_json_response(get_status())
        elif parsed_path.path == '/':
            self.send_json_response({
                "service": "VANTAGE Serial Allocation HTTP Server",
                "version": "1.0",
                "endpoints": {
                    "/allocate": "POST - Allocate next serial",
                    "/health": "GET - Get service status"
                }
            })
        else:
            self.send_json_response({"error": "Not found"}, 404)
    
    def do_POST(self) -> None:
        """Handle POST requests."""
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == '/allocate':
            try:
                serial = allocate_serial()
                self.send_json_response({
                    "serial": serial,
                    "authority": COUNTER_NAME,
                    "status": "ALLOCATED"
                })
            except Exception as exc:
                self.send_json_response({
                    "error": "HANDOFF_SERIAL_UNAVAILABLE",
                    "status": "UNAVAILABLE",
                    "detail": str(exc)
                }, 503)
        else:
            self.send_json_response({"error": "Not found"}, 404)
    
    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default logging."""
        pass


def main():
    """Main entry point for the HTTP server."""
    print(f"Starting VANTAGE Serial Allocation HTTP Server...")
    print(f"Host: {DEFAULT_HOST}")
    print(f"Port: {DEFAULT_PORT}")
    print(f"Database: {DB_PATH}")
    print(f"Authority: {COUNTER_NAME}")
    print(f"\nEndpoints:")
    print(f"  POST http://{DEFAULT_HOST}:{DEFAULT_PORT}/allocate - Allocate serial")
    print(f"  GET  http://{DEFAULT_HOST}:{DEFAULT_PORT}/health - Get status")
    print(f"\nPress Ctrl+C to stop the server.")
    
    server = HTTPServer((DEFAULT_HOST, DEFAULT_PORT), VantageSerialHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.shutdown()


if __name__ == "__main__":
    main()
