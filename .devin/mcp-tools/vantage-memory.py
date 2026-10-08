#!/usr/bin/env python3
"""
VANTAGE Memory CLI - Terminal wrapper for MCP memory servers
Provides CLI access to mem0-mcp and vantage-context-sync for non-MCP agents
"""

import subprocess
import json
import sys
import os
from pathlib import Path

# Configuration
MEM0_SERVER = "/Users/mauriciomeyran/.npm-global/lib/node_modules/mem0-mcp/dist/bin/mem0-mcp.js"
CONTEXT_SYNC_SERVER = "/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/.devin/mcp-context-sync/index.js"


def call_mcp_server(server_path, method, params=None):
    """Send JSON-RPC request to MCP server via stdio"""
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {}
    }

    env = os.environ.copy()
    if "mem0" in server_path.lower():
        env.update({
            "MEM0_STORE_PATH": os.path.expanduser("~/.vantage/mem0"),
            "OLLAMA_BASE_URL": "http://127.0.0.1:11434",
            "MEM0_EMBED_MODEL": "nomic-embed-text:latest",
            "MEM0_OLLAMA_TIMEOUT_MS": "30000"
        })

    try:
        process = subprocess.Popen(
            ["node", server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )

        stdout, stderr = process.communicate(
            input=json.dumps(request) + "\n",
            timeout=30
        )

        if process.returncode != 0:
            print(f"Error: Server exited with code {process.returncode}", file=sys.stderr)
            if stderr:
                print(f"stderr: {stderr}", file=sys.stderr)
            return None

        response = json.loads(stdout.strip())
        return response.get("result")

    except subprocess.TimeoutExpired:
        print("Error: Request timed out", file=sys.stderr)
        process.kill()
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON response - {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None


def cmd_mem0_store(content, user_id="default", metadata=None):
    """Store a memory in mem0"""
    result = call_mcp_server(
        MEM0_SERVER,
        "tools/call",
        {
            "name": "memory_store",
            "arguments": {
                "content": content,
                "user_id": user_id,
                "metadata": metadata or {}
            }
        }
    )
    return result


def cmd_mem0_search(query, user_id="default", limit=5):
    """Search memories in mem0"""
    result = call_mcp_server(
        MEM0_SERVER,
        "tools/call",
        {
            "name": "memory_search",
            "arguments": {
                "query": query,
                "user_id": user_id,
                "limit": limit
            }
        }
    )
    return result


def cmd_context_save(key, content, category=None, project_id=None):
    """Save a memory in context-sync"""
    result = call_mcp_server(
        CONTEXT_SYNC_SERVER,
        "tools/call",
        {
            "name": "memory_save",
            "arguments": {
                "key": key,
                "content": content,
                "category": category,
                "project_id": project_id
            }
        }
    )
    return result


def cmd_context_get(key):
    """Get a memory from context-sync"""
    result = call_mcp_server(
        CONTEXT_SYNC_SERVER,
        "tools/call",
        {
            "name": "memory_get",
            "arguments": {
                "key": key
            }
        }
    )
    return result


def cmd_context_search(query, project_id=None, limit=10):
    """Search memories in context-sync"""
    result = call_mcp_server(
        CONTEXT_SYNC_SERVER,
        "tools/call",
        {
            "name": "memory_search",
            "arguments": {
                "query": query,
                "project_id": project_id,
                "limit": limit
            }
        }
    )
    return result


def cmd_context_list(project_id=None, category=None, limit=10):
    """List memories in context-sync"""
    result = call_mcp_server(
        CONTEXT_SYNC_SERVER,
        "tools/call",
        {
            "name": "memory_list",
            "arguments": {
                "project_id": project_id,
                "category": category,
                "limit": limit
            }
        }
    )
    return result


def main():
    if len(sys.argv) < 2:
        print("VANTAGE Memory CLI")
        print("\nUsage:")
        print("  vantage-memory.py mem0-store <content> [--user-id ID]")
        print("  vantage-memory.py mem0-search <query> [--user-id ID] [--limit N]")
        print("  vantage-memory.py context-save <key> <content> [--category CAT] [--project-id ID]")
        print("  vantage-memory.py context-get <key>")
        print("  vantage-memory.py context-search <query> [--project-id ID] [--limit N]")
        print("  vantage-memory.py context-list [--project-id ID] [--category CAT] [--limit N]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "mem0-store":
        content = sys.argv[2] if len(sys.argv) > 2 else ""
        user_id = sys.argv[sys.argv.index("--user-id") + 1] if "--user-id" in sys.argv else "default"
        result = cmd_mem0_store(content, user_id)
        print(json.dumps(result, indent=2))

    elif command == "mem0-search":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        user_id = sys.argv[sys.argv.index("--user-id") + 1] if "--user-id" in sys.argv else "default"
        limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 5
        result = cmd_mem0_search(query, user_id, limit)
        print(json.dumps(result, indent=2))

    elif command == "context-save":
        key = sys.argv[2] if len(sys.argv) > 2 else ""
        content = sys.argv[3] if len(sys.argv) > 3 else ""
        category = sys.argv[sys.argv.index("--category") + 1] if "--category" in sys.argv else None
        project_id = sys.argv[sys.argv.index("--project-id") + 1] if "--project-id" in sys.argv else None
        result = cmd_context_save(key, content, category, project_id)
        print(json.dumps(result, indent=2))

    elif command == "context-get":
        key = sys.argv[2] if len(sys.argv) > 2 else ""
        result = cmd_context_get(key)
        print(json.dumps(result, indent=2))

    elif command == "context-search":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        project_id = sys.argv[sys.argv.index("--project-id") + 1] if "--project-id" in sys.argv else None
        limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 10
        result = cmd_context_search(query, project_id, limit)
        print(json.dumps(result, indent=2))

    elif command == "context-list":
        project_id = sys.argv[sys.argv.index("--project-id") + 1] if "--project-id" in sys.argv else None
        category = sys.argv[sys.argv.index("--category") + 1] if "--category" in sys.argv else None
        limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 10
        result = cmd_context_list(project_id, category, limit)
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
