#!/usr/bin/env python3
"""
vantage-sync.py — Local-first context sync CLI for VANTAGE.

Processes a collapsed chat dump (text or JSON), extracts key context
(items: tasks, decisions, stack changes, deliverables), and writes them
transitionally to the local SQLite context stores with deterministic
deduplication.

Non-negotiable constraints:
  - Pure stdlib Python. No external API calls.
  - Parameterized queries only.
  - context-sync.db is primary; mem0 is secondary and non-fatal.
  - Binary Gate: --dry-run never touches SQLite.
  - Deterministic SHA-256 keys prevent duplicates on re-runs.
"""

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone


# ── Default paths ────────────────────────────────────────────────────────────

DEFAULT_DB_PATH = os.path.expanduser("~/.vantage/context-sync.db")
DEFAULT_MEM0_PATH = os.path.expanduser("~/.vantage/mem0/memories.sqlite")


# ── Extraction patterns ──────────────────────────────────────────────────────
# Each pattern: (category, regex, extract_group)
# extract_group: index of the capture group containing the content text.

EXTRACTION_PATTERNS = [
    # Tasks — TODO, fixme, action items
    ("task", re.compile(
        r"(?:TODO|FIXME|action\s*item|task)\s*:?\s*(.+?)(?:\n|$)",
        re.IGNORECASE
    ), 1),

    # Decisions — DECISION:, DECIDED:, resolution:
    ("decision", re.compile(
        r"(?:DECISION|DECIDED|resolution)\s*:?\s*(.+?)(?:\n|$)",
        re.IGNORECASE
    ), 1),

    # Stack changes — git operations, path/file references
    ("pattern", re.compile(
        r"(?:git\s+(?:checkout|switch|merge|add|commit)\S*|moved\s+to\s+\S+|path:\s*\S+|file:\s*\S+)",
        re.IGNORECASE
    ), 0),

    # Deliverables — entregable, output:, result:
    ("fact", re.compile(
        r"(?:entregable|deliverable|output|result)\s*:?\s*(.+?)(?:\n|$)",
        re.IGNORECASE
    ), 1),
]


def extract_items(text: str) -> list[dict]:
    """Extract categorized items from raw text using heuristic patterns."""
    items = []
    for category, pattern, group in EXTRACTION_PATTERNS:
        for match in pattern.finditer(text):
            content = match.group(group) if group > 0 else match.group(0)
            content = content.strip()
            if content and len(content) < 2000:
                items.append({
                    "category": category,
                    "content": content,
                    "source_line": text[:200],  # first 200 chars for attribution
                })
    return items


def parse_text_input(text: str) -> list[dict]:
    """Parse plain text chat dump."""
    return extract_items(text)


def parse_json_input(raw: str) -> list[dict]:
    """Parse JSON-formatted chat dump.

    Expected formats:
      [{"role": "user", "content": "..."}, ...]
      {"conversation": [{"role": "...", "content": "..."}]}
      [{"content": "..."}]
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: --format json but input is not valid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    # Normalize to a list of message dicts
    if isinstance(data, dict) and "conversation" in data:
        messages = data["conversation"]
    elif isinstance(data, list):
        messages = data
    else:
        messages = [data]

    # Concatenate all content fields
    text_parts = []
    for msg in messages:
        if isinstance(msg, dict) and "content" in msg:
            content = msg["content"]
            if isinstance(content, str):
                text_parts.append(content)
            elif isinstance(content, list):
                # Some formats use content as list of blocks
                for block in content:
                    if isinstance(block, dict) and "text" in block:
                        text_parts.append(block["text"])

    full_text = "\n".join(text_parts)
    return extract_items(full_text)


# ── SQLite helpers ───────────────────────────────────────────────────────────

def connect_db(db_path: str, timeout: int = 5000) -> sqlite3.Connection:
    """Open a SQLite connection with busy timeout for lock resilience."""
    conn = sqlite3.connect(db_path)
    conn.execute(f"PRAGMA busy_timeout = {timeout}")
    return conn


def retry_sqlite(fn, max_retries: int = 3, base_delay: float = 0.1):
    """Execute a DB operation with exponential backoff on SQLITE_BUSY."""
    last_error = None
    for attempt in range(max_retries):
        try:
            return fn()
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) or "locked" in str(e).lower():
                last_error = e
                delay = base_delay * (2 ** attempt)
                print(f"  [retry {attempt+1}/{max_retries}] DB locked, waiting {delay:.2f}s...",
                      file=sys.stderr)
                time.sleep(delay)
            else:
                raise
    # Unreachable: the else branch above raises non-locked errors immediately,
    # and locked errors set last_error before retrying. If all retries are
    # exhausted, last_error is guaranteed to be non-None.
    assert last_error is not None
    raise RuntimeError(f"Failed after {max_retries} retries: {last_error}")


def gen_memory_key(category: str, content: str) -> str:
    """Generate a deterministic, idempotent memory key for dedup."""
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
    return f"{category}:{content_hash}"


def ensure_project(conn: sqlite3.Connection, project_id: str | None,
                   project_name: str | None = None) -> None:
    """Register project in context-sync.db if not already present."""
    if not project_id:
        return
    existing = conn.execute(
        "SELECT id FROM projects WHERE id = ?", (project_id,)
    ).fetchone()
    if existing is None:
        conn.execute(
            "INSERT OR REPLACE INTO projects (id, name, root_path) VALUES (?, ?, ?)",
            (project_id, project_name or project_id,
             os.getcwd())
        )
        conn.commit()


def write_to_context_sync(db_path: str, items: list[dict],
                          project_id: str | None, dry_run: bool) -> list[dict]:
    """Write items to the primary context-sync.db store.

    Returns list of {key, category, status, error} dicts for reporting.
    """
    results = []
    if dry_run:
        # Dry-run: skip all DB access, just compute keys + statuses
        for item in items:
            key = gen_memory_key(item["category"], item["content"])
            results.append({
                "key": key,
                "category": item["category"],
                "status": "dry_run",
                "error": None,
            })
        return results

    conn = connect_db(db_path)
    try:
        ensure_project(conn, project_id)

        for item in items:
            key = gen_memory_key(item["category"], item["content"])
            status = "written"
            error = None

            def do_upsert():
                conn.execute(
                    "INSERT INTO memories (key, content, category, project_id) "
                    "VALUES (?, ?, ?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET "
                    "content = excluded.content, "
                    "category = excluded.category, "
                    "project_id = excluded.project_id, "
                    "updated_at = CURRENT_TIMESTAMP",
                    (key, item["content"], item["category"], project_id)
                )
                conn.commit()

            try:
                retry_sqlite(do_upsert)
                status = "written"
            except Exception as e:
                status = "error"
                error = str(e)

            results.append({
                "key": key,
                "category": item["category"],
                "status": status,
                "error": error,
            })

    finally:
        if conn:
            conn.close()

    return results


def write_to_mem0(mem0_path: str, items: list[dict],
                  project_id: str | None, dry_run: bool) -> list[dict]:
    """Write items to the secondary mem0 store.

    Failures here are non-fatal — they surface as warnings in the report.
    """
    results = []
    if dry_run:
        return [{"key": gen_memory_key(i["category"], i["content"]),
                 "status": "dry_run", "error": None} for i in items]

    try:
        conn = connect_db(mem0_path)
    except sqlite3.Error as e:
        # mem0 DB not available — report all as skipped (non-fatal)
        for item in items:
            results.append({
                "key": gen_memory_key(item["category"], item["content"]),
                "status": "skipped",
                "error": f"mem0 unavailable: {e}",
            })
        return results

    try:
        for item in items:
            key = gen_memory_key(item["category"], item["content"])
            content_hash = hashlib.sha256(
                item["content"].encode("utf-8")
            ).hexdigest()[:12]
            mem0_id = f"{item['category']}_{content_hash}"
            now = datetime.now(timezone.utc).isoformat()
            metadata = json.dumps({
                "source_category": item["category"],
                "project_id": project_id or "",
            })

            def do_insert():
                conn.execute(
                    "INSERT OR REPLACE INTO memories "
                    "(id, kind, content, scope, provenance, metadata, embedding, "
                    "dedupe_key, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (mem0_id, item["category"], item["content"],
                     project_id or "default", "vantage-sync.py",
                     metadata, "",  # embedding left empty
                     item["content"][:12],  # dedupe_key
                     now, now)
                )
                conn.commit()

            try:
                retry_sqlite(do_insert)
                results.append({"key": key, "status": "written", "error": None})
            except Exception as e:
                results.append({"key": key, "status": "skipped", "error": str(e)})

    finally:
        conn.close()

    return results


# ── Report ───────────────────────────────────────────────────────────────────

def print_report(input_source: str, items: list[dict],
                 project_id: str | None, dry_run: bool,
                 primary_results: list[dict],
                 mem0_results: list[dict]) -> None:
    """Print a clean Markdown execution report."""
    mode = "DRY RUN (no writes)" if dry_run else "WRITE"
    print()
    print("# vantage-sync.py — Execution Report")
    print()
    print(f"**Input:** {input_source}")
    print(f"**Project:** {project_id or '(none)'}")
    print(f"**Mode:** {mode}")
    print()

    # Extraction summary
    print("## Extraction Summary")
    cat_counts = {}
    for item in items:
        cat_counts[item["category"]] = cat_counts.get(item["category"], 0) + 1
    if cat_counts:
        for cat in sorted(cat_counts):
            print(f"- {cat.capitalize()}s extracted: {cat_counts[cat]}")
    else:
        print("- No items extracted (no matching patterns found)")
    print()

    # Write results — primary store
    if not dry_run:
        print("## context-sync.db (primary)")
        print("| Key | Category | Status |")
        print("|-----|----------|--------|")
        for r in primary_results:
            print(f"| {r['key']} | {r['category']} | {r['status'].upper()} |")
        print()

        # mem0 secondary
        if mem0_results:
            warnings = [r for r in mem0_results if r["status"] != "written"]
            if warnings:
                print("## mem0/memories.sqlite (secondary) — Warnings")
                for r in warnings:
                    print(f"- `{r['key']}` — {r['status'].upper()}: {r.get('error', '')}")
                print("(These are non-fatal — primary store was written successfully.)")
                print()
    else:
        print("## Extraction Preview (--dry-run)")
        print("| Key | Category | Content (truncated) |")
        print("|-----|----------|---------------------|")
        for item in items:
            key = gen_memory_key(item["category"], item["content"])
            content_preview = item["content"][:80]
            print(f"| {key} | {item['category']} | {content_preview} |")
        print()

    print("**Done.**")
    print()


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="VANTAGE context sync CLI — extract context from collapsed chat dumps into local SQLite memory stores.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  # Dry-run preview
  python3 vantage-sync.py --input chat_dump.txt --dry-run

  # Write to primary store
  python3 vantage-sync.py --input chat_dump.txt --project vantage

  # From inline text
  python3 vantage-sync.py --inline "TODO: fix the OAuth redirect" --project vantage

  # JSON format
  python3 vantage-sync.py --input session_export.json --format json --project vantage
"""
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", "-i",
                       help="Path to chat dump file (text or JSON)")
    group.add_argument("--inline",
                       help="Raw text string (mutually exclusive with --input)")

    parser.add_argument("--project", "-p",
                        help="Project ID for context association")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                        help="Input format (default: text)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview only — no SQLite writes")
    parser.add_argument("--verbose", action="store_true",
                        help="Detailed extraction log")

    args = parser.parse_args()

    # Resolve input content
    if args.inline:
        raw_text = args.inline
        input_source = "inline string"
    else:
        if not os.path.exists(args.input):
            print(f"ERROR: input file not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        with open(args.input, "r", encoding="utf-8") as f:
            raw_text = f.read()
        input_source = args.input

    # Parse
    if args.format == "json":
        items = parse_json_input(raw_text)
    else:
        items = parse_text_input(raw_text)

    if args.verbose:
        print(f"[verbose] Extracted {len(items)} items from input")
        for item in items:
            print(f"  [{item['category']}] {item['content'][:100]}")

    # Determine DB paths
    db_path = os.environ.get("VANTAGE_DB_PATH", DEFAULT_DB_PATH)
    mem0_path = os.environ.get("VANTAGE_MEM0_PATH", DEFAULT_MEM0_PATH)

    # Write to primary store
    primary_results = write_to_context_sync(
        db_path, items, args.project, args.dry_run
    )

    # Write to secondary (mem0) — non-fatal
    mem0_results = []
    if items and not args.dry_run:
        mem0_results = write_to_mem0(
            mem0_path, items, args.project, args.dry_run
        )
    elif items and args.dry_run:
        mem0_results = [{"key": gen_memory_key(i["category"], i["content"]),
                         "status": "dry_run", "error": None} for i in items]

    # Report
    print_report(input_source, items, args.project, args.dry_run,
                 primary_results, mem0_results)

    if not args.dry_run:
        errors = [r for r in primary_results if r["status"] == "error"]
        if errors:
            print(f"ERROR: {len(errors)} items failed to write to context-sync.db",
                  file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
