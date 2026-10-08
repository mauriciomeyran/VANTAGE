#!/usr/bin/env python3
"""
context-dump.py — Dump compact context from local MCP memory servers
Returns a compact Markdown block (~150-250 tokens) for injection into non-MCP agents.

Usage:
    python3 context-dump.py --project vantage --limit 5 --format markdown
    python3 context-dump.py --project vantage --limit 10 --format json

This is a standalone script that doesn't require the full VANTAGE runtime dependencies.
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path


def dump_context(project_id: str = "vantage", limit: int = 5, format: str = "markdown") -> str:
    """
    Dump compact context from local MCP memory servers (mem0 + context-sync).

    Args:
        project_id: Project identifier for context-sync filtering
        limit: Maximum number of memories to include from each source
        format: Output format ('markdown' or 'json')

    Returns:
        Compact context string
    """
    mem0_db_path = Path.home() / ".vantage" / "mem0" / "memories.sqlite"
    context_db_path = Path.home() / ".vantage" / "context-sync.db"

    sections = []

    # Query Context Sync (project memory)
    if context_db_path.exists():
        try:
            conn = sqlite3.connect(str(context_db_path))
            cursor = conn.cursor()
            cursor.execute(
                "SELECT key, content, category, updated_at FROM memories "
                "WHERE project_id = ? OR project_id IS NULL OR project_id = 'null' "
                "ORDER BY updated_at DESC LIMIT ?",
                (project_id, limit)
            )
            context_memories = cursor.fetchall()
            conn.close()

            if context_memories:
                sections.append("## Project Memory (Context Sync)")
                for key, content, category, updated_at in context_memories:
                    cat_str = f"[{category}] " if category else ""
                    content_preview = content[:100] + "..." if len(content) > 100 else content
                    sections.append(f"- {cat_str}{key}: {content_preview}")
        except Exception as e:
            sections.append(f"[Context Sync error: {e}]")
    else:
        sections.append("[Context Sync: database not found at ~/.vantage/context-sync.db]")

    # Query mem0 (semantic memory)
    if mem0_db_path.exists():
        try:
            conn = sqlite3.connect(str(mem0_db_path))
            cursor = conn.cursor()

            # Check if memories table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memories'")
            if cursor.fetchone():
                # Query with scope filtering (scope is JSON)
                cursor.execute(
                    "SELECT id, kind, content, scope, created_at FROM memories "
                    "ORDER BY created_at DESC LIMIT ?",
                    (limit,)
                )
                mem0_memories = cursor.fetchall()
                conn.close()

                if mem0_memories:
                    sections.append("## Semantic Memory (mem0)")
                    for mem_id, kind, content, scope, created_at in mem0_memories:
                        # Parse scope JSON to check if it matches project_id
                        try:
                            scope_data = json.loads(scope) if scope else {}
                            scope_project = scope_data.get("project", "")
                            # Include if project matches or if scope is empty
                            if not scope_project or scope_project == project_id:
                                content_preview = content[:100] + "..." if len(content) > 100 else content
                                sections.append(f"- [{kind}] {content_preview}")
                        except:
                            # If scope parsing fails, include anyway
                            content_preview = content[:100] + "..." if len(content) > 100 else content
                            sections.append(f"- [{kind}] {content_preview}")
            else:
                conn.close()
                sections.append("[mem0: no memories stored yet]")
        except Exception as e:
            sections.append(f"[mem0 error: {e}]")
    else:
        sections.append("[mem0: database not found at ~/.vantage/mem0/memories.sqlite]")

    if not sections or all(s.startswith("[") for s in sections):
        return "# VANTAGE Context\n\nNo local memories found for this project."

    if format == "json":
        return json.dumps({
            "project_id": project_id,
            "context_sync": sections if any("Context Sync" in s for s in sections) else [],
            "mem0": sections if any("mem0" in s.lower() for s in sections) else [],
            "full_output": sections
        }, indent=2)

    # Markdown format
    output = "# VANTAGE Context\n\n"
    output += "\n".join(sections)
    return output


def main():
    parser = argparse.ArgumentParser(
        description="Dump compact context from local MCP memory servers for non-MCP agents",
        epilog="Example:\n  python3 context-dump.py --project vantage --limit 5 --format markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--project",
        default="vantage",
        help="Project ID for filtering (default: vantage)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum memories per source (default: 5)"
    )
    parser.add_argument(
        "--format",
        default="markdown",
        choices=["markdown", "json"],
        help="Output format (default: markdown)"
    )

    args = parser.parse_args()

    result = dump_context(project_id=args.project, limit=args.limit, format=args.format)
    print(result)


if __name__ == "__main__":
    main()
