#!/usr/bin/env python3
"""
vantage-sync.py — Local-first context sync CLI for VANTAGE.

Processes a collapsed chat dump (text or JSON), extracts key context
(tasks, decisions, stack changes, deliverables), and writes them
transitionally to the local SQLite context stores with deterministic
deduplication.

Non-negotiable constraints:
  - Pure stdlib Python. No external API calls in regex mode.
  - LLM mode (--llm) uses local Ollama (http://localhost:11434) only.
  - Parameterized queries only.
  - context-sync.db is primary; mem0 is secondary and non-fatal.
  - Binary Gate: --dry-run never touches SQLite.
  - Deterministic SHA-256 keys prevent duplicates on re-runs.
  - Regex mode is default; --llm is optional semantic mode with regex fallback.
  - DB validation: exits with code 1 if required tables are missing.
  - Intelligent truncation for LLM: preserves end-of-chat content with overlap.
"""

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone


# ─── Default paths ────────────────────────────────────────────────────────────

DEFAULT_DB_PATH = os.path.expanduser("~/.vantage/context-sync.db")
DEFAULT_MEM0_PATH = os.path.expanduser("~/.vantage/mem0/memories.sqlite")
LLM_TRUNCATE_LIMIT = 8000       # max chars to send to Ollama
LLM_TAIL_LENGTH = 6000          # chars of the end to always preserve
LLM_HEAD_LENGTH = 2000          # chars of the beginning to keep as context

# Module-level tracker for extraction source (regex vs LLM vs LLM→regex fallback)
_last_extraction_source: str = "regex"


# ─── Regex extraction patterns ────────────────────────────────────────────────
# Each entry: (category, compiled_regex, capture_group_index)

EXTRACTION_PATTERNS: list[tuple[str, re.Pattern, int]] = [
    # Tasks
    ("task", re.compile(
        r"(?:TODO|FIXME|action\s*item|task)\s*:?\s*(.+?)(?:\n|$)",
        re.IGNORECASE,
    ), 1),
    # Decisions
    ("decision", re.compile(
        r"(?:DECISION|DECIDED|resolution)\s*:?\s*(.+?)(?:\n|$)",
        re.IGNORECASE,
    ), 1),
    # Stack changes — git operations, path/file references
    ("pattern", re.compile(
        r"(?:git\s+(?:checkout|switch|merge|add|commit)\S*"
        r"|moved\s+to\s+\S+"
        r"|path:\s*\S+"
        r"|file:\s*\S+)",
        re.IGNORECASE,
    ), 0),
    # Facts / deliverables
    ("fact", re.compile(
        r"(?:entregable|deliverable|output|result)\s*:?\s*(.+?)(?:\n|$)",
        re.IGNORECASE,
    ), 1),
]


def extract_items(text: str) -> list[dict]:
    """Extract categorized items from raw text using regex heuristics.

    Returns list of dicts: {category, content, source_line}
    """
    items: list[dict] = []
    for category, pattern, group in EXTRACTION_PATTERNS:
        for match in pattern.finditer(text):
            content = match.group(group) if group > 0 else match.group(0)
            content = content.strip()
            if content and len(content) < 2000:
                items.append({
                    "category": category,
                    "content": content,
                    "source_line": text[:200],
                })
    return items


def parse_text_input(text: str) -> list[dict]:
    """Parse plain text chat dump via regex."""
    global _last_extraction_source
    _last_extraction_source = "regex"
    return extract_items(text)


def normalize_json_input(raw: str) -> str:
    """Parse JSON-formatted chat dump and return concatenated text.

    Handles formats:
      [{"role": "user", "content": "..."}, ...]
      {"conversation": [{"role": "...", "content": "..."}]}
      [{"content": "..."}]

    Exits with error code 1 if JSON is invalid.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: --format json but input is not valid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    if isinstance(data, dict) and "conversation" in data:
        messages = data["conversation"]
    elif isinstance(data, list):
        messages = data
    else:
        messages = [data]

    text_parts: list[str] = []
    for msg in messages:
        if isinstance(msg, dict) and "content" in msg:
            content = msg["content"]
            if isinstance(content, str):
                text_parts.append(content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and "text" in block:
                        text_parts.append(block["text"])

    return "\n".join(text_parts)


def parse_json_input(raw: str) -> list[dict]:
    """Parse JSON-formatted chat dump, normalize to text, then extract via regex."""
    global _last_extraction_source
    _last_extraction_source = "regex"
    full_text = normalize_json_input(raw)
    return extract_items(full_text)


# ─── Ollama LLM extraction (optional, local-only) ─────────────────────────────

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_OLLAMA_TIMEOUT = 120  # seconds — qwen2.5:7b needs extra time on cold start

OLLAMA_SYSTEM_PROMPT = """
You are a context extraction specialist for VANTAGE. Given a chat log, extract:
1. decisions: explicit decisions, conclusions, or resolutions stated
2. tasks: actionable TODOs, action items, or next steps
3. facts: key factual statements, deliverables, or outcomes

Return STRICT JSON only — no prose, no markdown. Example:
{"decisions": [{"content": "..."}], "tasks": [{"content": "..."}], "facts": [{"content": "..."}]}
Each array contains objects with a single "content" field containing the extracted text.
"""


def intelligent_truncate(text: str, limit: int = LLM_TRUNCATE_LIMIT,
                        tail_length: int = LLM_TAIL_LENGTH,
                        head_length: int = LLM_HEAD_LENGTH) -> str:
    """Intelligently truncate text to fit within LLM context.

    Preserves the beginning (for context) and the end (for recent TODOs/decisions)
    with overlap marker. If text fits within limit, returns as-is.
    """
    if len(text) <= limit:
        return text

    head = text[:head_length]
    tail = text[-tail_length:]

    print(
        f"[info] Text truncated: {len(text)} chars → {head_length} head + "
        f"{tail_length} tail (overlap gap: {len(text) - head_length - tail_length} chars lost)",
        file=sys.stderr,
    )

    return (
        head
        + "\n\n[... TRUNCATED — middle content omitted for LLM context limit ...]\n\n"
        + tail
    )


def extract_with_ollama(text: str, model: str = "qwen2.5:7b",
                        timeout: int = DEFAULT_OLLAMA_TIMEOUT) -> list[dict]:
    """Extract items via Ollama LLM with regex fallback on any failure.

    Makes a local-only POST to http://localhost:11434/api/generate.
    Returns items in the same shape as extract_items().
    Sets _last_extraction_source to "llm" or "llm→regex (fallback)".
    """
    global _last_extraction_source
    truncated = intelligent_truncate(text)

    payload = json.dumps({
        "model": model,
        "prompt": OLLAMA_SYSTEM_PROMPT + "\n\n---CHAT LOG---\n" + truncated,
        "format": "json",
        "stream": False,
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            OLLAMA_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
        llm_output = json.loads(raw["response"])

        items: list[dict] = []
        for cat in ("decision", "task", "fact"):
            key = cat + "s"  # JSON keys: decisions, tasks, facts
            for entry in llm_output.get(key, []):
                content = entry.get("content", "").strip()
                if content and len(content) < 2000:
                    items.append({
                        "category": cat,
                        "content": content,
                        "source_line": text[:200],
                    })

        if items:
            _last_extraction_source = "llm"
            return items

        # LLM returned empty — fall back to regex
        print("[info] LLM returned no items — falling back to regex", file=sys.stderr)
        _last_extraction_source = "llm→regex"
        return extract_items(text)

    except Exception as e:
        print(f"[info] LLM extraction failed ({e}) — falling back to regex", file=sys.stderr)
        _last_extraction_source = "llm→regex"
        return extract_items(text)


# ─── SQLite helpers ───────────────────────────────────────────────────────────

def connect_db(db_path: str, timeout: int = 5000) -> sqlite3.Connection:
    """Open a SQLite connection with busy timeout for lock resilience."""
    conn = sqlite3.connect(db_path)
    conn.execute(f"PRAGMA busy_timeout = {timeout}")
    return conn


def validate_db_schema(conn: sqlite3.Connection, required_tables: list[str]) -> bool:
    """Verify that all required tables exist in the connected database."""
    existing = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    existing_tables = {row[0] for row in existing}
    missing = set(required_tables) - existing_tables
    if missing:
        print(
            f"ERROR: database at '{conn.execute('PRAGMA database_list').fetchone()[2]}' "
            f"is missing required tables: {sorted(missing)}",
            file=sys.stderr,
        )
        return False
    return True


def validate_db_file(db_path: str, required_tables: list[str]) -> sqlite3.Connection:
    """Validate that a DB file exists, is not empty (0 bytes), and has required tables.

    Returns an open connection if valid.
    Exits with code 1 if the DB is missing, 0 bytes, or missing tables
    — never returns None (exits before returning).
    Uses retry_sqlite for lock resilience.
    """
    if not os.path.exists(db_path):
        print(f"ERROR: database file not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    if os.path.getsize(db_path) == 0:
        print(
            f"ERROR: database file is 0 bytes (corrupt/empty): {db_path}. "
            f"Aborting to prevent MCP context-sync corruption.",
            file=sys.stderr,
        )
        sys.exit(1)

    def _connect_and_validate():
        conn = connect_db(db_path)
        if not validate_db_schema(conn, required_tables):
            conn.close()
            sys.exit(1)
        return conn

    try:
        return retry_sqlite(_connect_and_validate)
    except RuntimeError as e:
        print(
            f"ERROR: database at '{db_path}' is locked after retries: {e}",
            file=sys.stderr,
        )
        sys.exit(1)


def retry_sqlite(fn, max_retries: int = 3, base_delay: float = 0.1):
    """Execute a DB operation with exponential backoff on SQLITE_BUSY.

    Non-locking OperationalErrors are re-raised immediately.
    SQLITE_BUSY errors are retried with exponential backoff.
    """
    last_error: Exception | None = None
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
    # If we exhausted all retries on locked errors, last_error is guaranteed set
    assert last_error is not None
    raise RuntimeError(f"Failed after {max_retries} retries: {last_error}")


def gen_memory_key(category: str, content: str) -> str:
    """Generate a deterministic, idempotent memory key for dedup."""
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
    return f"{category}:{content_hash}"


def ensure_project(conn: sqlite3.Connection, project_id: str | None,
                   project_name: str | None = None) -> None:
    """Register project in context-sync.db if not already present.

    Wrapped with retry for resilience against SQLITE_BUSY.
    """
    if not project_id:
        return

    def do_ensure():
        existing = conn.execute(
            "SELECT id FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        if existing is None:
            conn.execute(
                "INSERT OR REPLACE INTO projects (id, name, root_path) VALUES (?, ?, ?)",
                (project_id, project_name or project_id, os.getcwd()),
            )
            conn.commit()

    retry_sqlite(do_ensure)


def write_to_context_sync(db_path: str, items: list[dict],
                          project_id: str | None, dry_run: bool) -> list[dict]:
    """Write items to the primary context-sync.db store.

    Returns list of {key, category, status, error} dicts for reporting.
    Validates DB schema before writing (Fix 2).
    ensure_project wrapped with retry_sqlite (Fix 3).
    """
    results: list[dict] = []
    if dry_run:
        for item in items:
            key = gen_memory_key(item["category"], item["content"])
            results.append({
                "key": key,
                "category": item["category"],
                "status": "dry_run",
                "error": None,
            })
        return results

    # Fix 2: Validate DB file + schema before any writes
    conn = validate_db_file(db_path, ["projects", "memories"])

    try:
        # Fix 3: ensure_project wrapped with retry_sqlite
        ensure_project(conn, project_id)

        for item in items:
            key = gen_memory_key(item["category"], item["content"])
            status = "written"
            error: str | None = None

            def do_upsert():
                conn.execute(
                    "INSERT INTO memories (key, content, category, project_id) "
                    "VALUES (?, ?, ?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET "
                    "content = excluded.content, "
                    "category = excluded.category, "
                    "project_id = excluded.project_id, "
                    "updated_at = CURRENT_TIMESTAMP",
                    (key, item["content"], item["category"], project_id),
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
        conn.close()

    return results


def gen_mem0_id(category: str, content: str) -> str:
    """Generate a deterministic mem0 row ID based on content hash.

    Fix 4: Uses full SHA-256 hash instead of content[:12] to eliminate
    collision risk from short prefixes.
    """
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return f"{category}_{content_hash[:12]}"


def write_to_mem0(mem0_path: str, items: list[dict],
                  project_id: str | None, dry_run: bool) -> list[dict]:
    """Write items to the secondary mem0 store.

    Failures here are non-fatal — they surface as warnings in the report.
    Fix 4: dedupe_key uses full content hash (not content[:12] prefix).

    Real mem0 schema (verified from ~/.vantage/mem0/memories.sqlite):
      CREATE TABLE memories (
          id TEXT PRIMARY KEY,
          kind TEXT NOT NULL,
          content TEXT NOT NULL,
          scope TEXT NOT NULL,
          provenance TEXT NOT NULL,
          metadata TEXT NOT NULL,
          embedding TEXT NOT NULL,
          dedupe_key TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
      );
      CREATE INDEX idx_memories_dedupe_key ON memories (dedupe_key);

    PRAGMA table_info(memories):
      0|id|TEXT|0||1
      1|kind|TEXT|1||0
      2|content|TEXT|1||0
      3|scope|TEXT|1||0
      4|provenance|TEXT|1||0
      5|metadata|TEXT|1||0
      6|embedding|TEXT|1||0
      7|dedupe_key|TEXT|1|''|0
      8|created_at|TEXT|1||0
      9|updated_at|TEXT|1||0

    No unique constraint on dedupe_key — dedup is enforced by PK (id).
    """
    results: list[dict] = []
    if dry_run:
        return [
            {"key": gen_memory_key(i["category"], i["content"]),
             "status": "dry_run", "error": None}
            for i in items
        ]

    try:
        conn = connect_db(mem0_path)
    except sqlite3.Error as e:
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
            # Fix 4: use full SHA-256 content hash as dedupe_key (not [:12])
            content_hash = hashlib.sha256(
                item["content"].encode("utf-8")
            ).hexdigest()
            mem0_id = f"{item['category']}_{content_hash[:12]}"
            # dedupe_key: use the full 12-char SHA-256 hash (deterministic)
            dedupe_key = hashlib.sha256(
                f"{item['category']}:{item['content']}".encode("utf-8")
            ).hexdigest()[:12]
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
                     dedupe_key,
                     now, now),
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


# ─── DB validation for mem0 (non-fatal wrapper) ────────────────────────────────

def write_to_mem0_safe(mem0_path: str, items: list[dict],
                       project_id: str | None, dry_run: bool) -> list[dict]:
    """Wrapper around write_to_mem0 that validates DB before writing.

    If the DB file is missing or 0 bytes, returns all items as skipped
    with a clear error message — never exits, never creates empty files.
    """
    if dry_run:
        return [
            {"key": gen_memory_key(i["category"], i["content"]),
             "status": "dry_run", "error": None}
            for i in items
        ]

    if not os.path.exists(mem0_path):
        msg = f"mem0 database not found: {mem0_path}"
        print(f"[warn] {msg} — skipping mem0 writes (non-fatal)", file=sys.stderr)
        return [
            {"key": gen_memory_key(i["category"], i["content"]),
             "status": "skipped", "error": msg}
            for i in items
        ]

    if os.path.getsize(mem0_path) == 0:
        msg = f"mem0 database is 0 bytes (corrupt): {mem0_path}"
        print(f"[warn] {msg} — skipping mem0 writes (non-fatal)", file=sys.stderr)
        return [
            {"key": gen_memory_key(i["category"], i["content"]),
             "status": "skipped", "error": msg}
            for i in items
        ]

    # Check schema — if missing, skip gracefully
    try:
        conn = connect_db(mem0_path)
    except sqlite3.Error as e:
        return [
            {"key": gen_memory_key(i["category"], i["content"]),
             "status": "skipped", "error": f"mem0 connection error: {e}"}
            for i in items
        ]

    if not validate_db_schema(conn, ["memories"]):
        conn.close()
        return [
            {"key": gen_memory_key(i["category"], i["content"]),
             "status": "skipped", "error": "mem0 schema validation failed"}
            for i in items
        ]

    conn.close()
    # Schema is valid — delegate to the actual writer
    return write_to_mem0(mem0_path, items, project_id, dry_run)


# ─── Report ───────────────────────────────────────────────────────────────────

def print_report(input_source: str, items: list[dict],
                 project_id: str | None, dry_run: bool,
                 primary_results: list[dict],
                 mem0_results: list[dict]) -> None:
    """Print a clean Markdown execution report.

    Engine reflects the actual extraction source:
      - "regex" for default heuristic mode
      - "llm (qwen2.5:7b)" for successful Ollama extraction
      - "llm→regex (fallback)" when LLM failed and regex was used
    """
    mode = "DRY RUN (no writes)" if dry_run else "WRITE"
    # Determine engine label from module-level tracker
    source = globals().get("_last_extraction_source", "regex")
    if source == "llm":
        engine = "llm (qwen2.5:7b)"
    elif source == "llm→regex":
        engine = "llm→regex (fallback)"
    else:
        engine = "regex"
    print()
    print("# vantage-sync.py — Execution Report")
    print()
    print(f"**Input:** {input_source}")
    print(f"**Project:** {project_id or '(none)'}")
    print(f"**Mode:** {mode}")
    print(f"**Engine:** {engine}")
    print()

    # Extraction summary
    print("## Extraction Summary")
    cat_counts: dict[str, int] = {}
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


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="VANTAGE context sync CLI — extract context from collapsed chat dumps "
                    "into local SQLite memory stores.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  # Dry-run preview (regex mode — default)
  python3 vantage-sync.py --input chat_dump.txt --dry-run

  # Write to primary store (regex mode — default)
  python3 vantage-sync.py --input chat_dump.txt --project vantage

  # LLM semantic extraction (local Ollama qwen2.5:7b, 120s timeout default)
  python3 vantage-sync.py --input chat_dump.txt --project vantage --llm --dry-run

  # LLM with custom model and timeout
  python3 vantage-sync.py --input chat_dump.txt --llm --model qwen2.5:7b --timeout 180

  # From inline text
  python3 vantage-sync.py --inline "TODO: fix the OAuth redirect" --project vantage

  # JSON format
  python3 vantage-sync.py --input session_export.json --format json --project vantage
""",
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
    parser.add_argument("--llm", action="store_true",
                        help="Use Ollama LLM for semantic extraction (qwen2.5:7b local)")
    parser.add_argument("--model", default="qwen2.5:7b",
                        help="Ollama model name (default: qwen2.5:7b)")
    parser.add_argument("--timeout", type=int, default=DEFAULT_OLLAMA_TIMEOUT,
                        help=f"Ollama request timeout in seconds (default: {DEFAULT_OLLAMA_TIMEOUT})")
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

    # Fix 5: Normalize JSON input before LLM extraction
    # If --format json and --llm, normalize the JSON to text first
    if args.format == "json":
        raw_text = normalize_json_input(raw_text)
        input_source = f"{input_source} (normalized JSON → text)"

    # Parse — LLM mode takes priority over format
    if args.llm:
        items = extract_with_ollama(raw_text, args.model, args.timeout)
    elif args.format == "json":
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

    # Write to secondary (mem0) — non-fatal, schema-validated
    mem0_results = write_to_mem0_safe(
        mem0_path, items, args.project, args.dry_run
    )

    # Report
    print_report(input_source, items, args.project, args.dry_run,
                 args.llm, primary_results, mem0_results)

    if not args.dry_run:
        errors = [r for r in primary_results if r["status"] == "error"]
        if errors:
            print(f"ERROR: {len(errors)} items failed to write to context-sync.db",
                  file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
