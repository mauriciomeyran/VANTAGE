#!/usr/bin/env python3
"""
VANTAGE Serial Allocation MCP Bridge for Claude Desktop
"""
from __future__ import annotations

import os
import sys

# Resolver dinámicamente la carpeta site-packages del .venv actual
venv_site_packages = os.path.abspath(
    os.path.join(
        os.path.dirname(sys.executable),
        "..",
        "lib",
        f"python{sys.version_info.major}.{sys.version_info.minor}",
        "site-packages",
    )
)
if venv_site_packages not in sys.path:
    sys.path.insert(0, venv_site_packages)

import json
from typing import Any
import requests

try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    FastMCP = None

# Configuration
HTTP_SERVER_URL = os.environ.get("VANTAGE_SERIAL_HTTP_URL", "http://localhost:8787")
TIMEOUT = int(os.environ.get("VANTAGE_SERIAL_TIMEOUT", "10"))


def create_mcp_server() -> Any:
    """Create and configure the MCP server using FastMCP."""
    if not MCP_AVAILABLE:
        raise RuntimeError("MCP SDK not installed. Install with: pip install mcp")

    mcp = FastMCP("vantage-serial-bridge")

    @mcp.tool()
    def allocate_vantage_serial() -> str:
        """Allocate the next VANTAGE handoff serial number via central HTTP server."""
        try:
            response = requests.post(
                f"{HTTP_SERVER_URL}/allocate", timeout=TIMEOUT
            )
            response.raise_for_status()
            return json.dumps(response.json())
        except requests.exceptions.RequestException as exc:
            return json.dumps(
                {
                    "error": "HANDOFF_SERIAL_UNAVAILABLE",
                    "status": "UNAVAILABLE",
                    "detail": f"HTTP request failed: {str(exc)}",
                }
            )
        except Exception as exc:
            return json.dumps(
                {
                    "error": "HANDOFF_SERIAL_UNAVAILABLE",
                    "status": "UNAVAILABLE",
                    "detail": str(exc),
                }
            )

    @mcp.tool()
    def vantage_serial_status() -> str:
        """Get the status of the VANTAGE serial allocation service."""
        try:
            response = requests.get(f"{HTTP_SERVER_URL}/health", timeout=TIMEOUT)
            response.raise_for_status()
            return json.dumps(response.json())
        except Exception as exc:
            return json.dumps({"error": "STATUS_UNAVAILABLE", "detail": str(exc)})

    return mcp


def main():
    """Main entry point for the MCP bridge server."""
    if not MCP_AVAILABLE:
        print("Error: MCP SDK not installed", file=sys.stderr)
        print("Install with: pip install mcp", file=sys.stderr)
        sys.exit(1)

    # Redirección estricta de telemetría a stderr para proteger el canal stdout de JSON-RPC
    print(f"[vantage-bridge] HTTP Server URL: {HTTP_SERVER_URL}", file=sys.stderr)
    print(f"[vantage-bridge] Timeout: {TIMEOUT}s", file=sys.stderr)

    mcp = create_mcp_server()
    mcp.run()


if __name__ == "__main__":
    main()
