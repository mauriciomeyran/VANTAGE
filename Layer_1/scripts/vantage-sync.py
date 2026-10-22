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
SCRIPT_PATH = os.path.abspath(__file__)
LLM_TRUNCATE_LIMIT = 8000       # max chars to send to Ollama
LLM_TAIL_LENGTH = 6000          # chars of the end to always preserve
LLM_HEAD_LENGTH = 2000          # chars of the beginning to keep as context

# Module-level tracker for extraction source (regex vs LLM vs LLM→regex fallback)
_last_extraction_source: str = "regex"

# Rate limiting state for Notion API (≤3 requests/s)
_last_request_time: list[float] = [0.0]


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
                line_start = text.rfind("\n", 0, match.start()) + 1
                line_end = text.find("\n", match.start())
                if line_end < 0:
                    line_end = len(text)
                source_line = text[line_start:line_end].strip()[:200]
                items.append({
                    "category": category,
                    "content": content,
                    "source_line": source_line,
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
DEFAULT_OLLAMA_TIMEOUT = 300  # seconds — T4: per chunk default (~2.3x max measured)
DEFAULT_WARMUP_TIMEOUT = 180  # seconds — T4: warmup timeout (default)
OLLAMA_SEED = 42  # fixed seed for deterministic LLM extraction
DEFAULT_CHUNK_SIZE = 5000  # characters per chunk (base, adaptive chunking adjusts this)
DEFAULT_CHUNK_OVERLAP = 500  # overlap between chunks
OLLAMA_NUM_CTX = 8192  # T3: explicit context window size

# Module-level tracker for chunk status
_chunk_stats: dict[str, int] = {"processed": 0, "failed": 0}
# T4-B: tracker for consecutive timeouts
_consecutive_timeouts: int = 0

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

    marker = "\n\n[... TRUNCATED — middle content omitted for LLM context limit ...]\n\n"
    available = max(0, limit - len(marker))
    tail_len = min(tail_length, available)
    head_len = min(head_length, max(0, available - tail_len))
    head = text[:head_len]
    tail = text[-tail_len:] if tail_len else ""

    print(
        f"[info] Text truncated: {len(text)} chars → {head_len} head + "
        f"{tail_len} tail (overlap gap: {len(text) - head_len - tail_len} chars lost)",
        file=sys.stderr,
    )

    result = head + marker + tail
    return result[:limit]


def split_into_chunks(text: str, size: int = 5000, overlap: int = 500) -> list[str]:
    """Split text into overlapping chunks for LLM processing.

    Args:
        text: Input text to split
        size: Target chunk size in characters (default 5000)
        overlap: Overlap between consecutive chunks (default 500)

    Returns:
        List of text chunks. Text <= size returns 1 chunk.
    """
    if len(text) <= size:
        return [text]

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = start + size
        chunk = text[start:end]
        chunks.append(chunk)

        # Move start with overlap, but stop if we've reached the end
        if end >= len(text):
            break
        start += size - overlap

    return chunks


def get_adaptive_chunk_size(text_len: int) -> int:
    """Calculate adaptive chunk size based on total text length.

    Larger files get larger chunks to reduce total LLM requests.
    - < 20,000 chars: 5,000 chars/chunk
    - ≥ 20,000 chars: 10,000 chars/chunk
    """
    if text_len < 20000:
        return 5000
    else:
        return 10000


def warmup_ollama(model: str = "qwen2.5:7b", timeout: int = DEFAULT_WARMUP_TIMEOUT) -> None:
    """Warmup Ollama by loading the model before actual extraction.

    T4: POST to /api/generate with keep_alive and options (num_ctx).
    This loads the model into memory so first chunk is faster.
    Warmup failure is treated as LLM failure.
    """
    print(f"[info] Warming up Ollama model {model}...", file=sys.stderr)

    payload = json.dumps({
        "model": model,
        "keep_alive": "5m",  # Keep model loaded for 5 minutes after warmup
        "stream": False,
        "options": {
            "num_ctx": OLLAMA_NUM_CTX,  # T4: same num_ctx as chunks
        },
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            OLLAMA_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
        if not isinstance(raw, dict) or raw.get("done") is not True:
            raise ValueError("Ollama warmup response must be a JSON object with done=true")
        print("[info] Warmup complete", file=sys.stderr)
    except Exception as e:
        print(f"[info] Warmup failed ({e}) — treating as LLM failure", file=sys.stderr)
        raise


def extract_with_ollama(text: str, model: str = "qwen2.5:7b",
                        timeout: int = DEFAULT_OLLAMA_TIMEOUT,
                        warmup_timeout: int = DEFAULT_WARMUP_TIMEOUT,
                        fallback_to_regex: bool = True,
                        allow_partial: bool = False) -> list[dict]:
    """Extract items via Ollama LLM with regex fallback on any failure.

    Makes a local-only POST to http://localhost:11434/api/generate.
    Returns items in the same shape as extract_items().
    Sets _last_extraction_source to "llm" or "llm→regex (fallback)".

    T2: Processes text in chunks with overlap, combines and deduplicates results.
    T4: Warmup call before chunks, per-chunk timeout, separate warmup timeout.
    T4-B: Aborts after 2 consecutive timeouts to prevent resource waste.
    All-or-nothing by default (any chunk failure → regex fallback).
    --allow-partial opt-in to keep successful chunk results.
    Adaptive chunking based on text length.
    Set fallback_to_regex=False to raise instead of using regex on LLM failure.
    Tracks chunk status in _chunk_stats for reporting.
    """
    global _last_extraction_source, _chunk_stats, _consecutive_timeouts
    _chunk_stats = {"processed": 0, "failed": 0}
    _consecutive_timeouts = 0

    # T4: Warmup before chunking
    try:
        warmup_ollama(model, timeout=warmup_timeout)
    except Exception as e:
        if not fallback_to_regex:
            raise RuntimeError(f"Ollama warmup failed and fallback is disabled: {e}") from e
        print("[info] Warmup failed — falling back to regex", file=sys.stderr)
        _last_extraction_source = "llm→regex"
        return extract_items(text)

    # Adaptive chunking
    adaptive_chunk_size = get_adaptive_chunk_size(len(text))
    print(f"[info] Adaptive chunk size: {adaptive_chunk_size} chars (text length: {len(text)} chars)", file=sys.stderr)

    # Split into chunks
    chunks = split_into_chunks(text, size=adaptive_chunk_size, overlap=DEFAULT_CHUNK_OVERLAP)
    print(f"[info] Processing {len(text)} chars in {len(chunks)} chunk(s)", file=sys.stderr)

    all_items: list[dict] = []
    seen_keys: set[str] = set()

    for i, chunk in enumerate(chunks):
        chunk_num = i + 1
        print(f"[info] Processing chunk {chunk_num}/{len(chunks)} ({len(chunk)} chars)", file=sys.stderr)

        payload = json.dumps({
            "model": model,
            "prompt": OLLAMA_SYSTEM_PROMPT + "\n\n---CHAT LOG CHUNK---\n" + chunk,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0,
                "seed": OLLAMA_SEED,
                "num_ctx": OLLAMA_NUM_CTX,  # T3: explicit context window
            },
        }).encode("utf-8")

        chunk_start = time.time()
        try:
            req = urllib.request.Request(
                OLLAMA_URL,
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
            llm_output = json.loads(raw["response"])
            if not isinstance(llm_output, dict):
                raise ValueError("Ollama response JSON must be an object")
            for req_key in ("decisions", "tasks", "facts"):
                if req_key in llm_output and not isinstance(llm_output[req_key], list):
                    raise ValueError(f"Ollama response field '{req_key}' must be a list")

            chunk_duration = time.time() - chunk_start
            print(f"[info] Chunk {chunk_num}/{len(chunks)} ok in {chunk_duration:.1f}s", file=sys.stderr)

            _chunk_stats["processed"] += 1
            _consecutive_timeouts = 0  # Reset counter on success

            # Extract items from this chunk
            for cat in ("decision", "task", "fact"):
                key = cat + "s"  # JSON keys: decisions, tasks, facts
                for entry in llm_output.get(key, []):
                    if not isinstance(entry, dict):
                        continue
                    content = entry.get("content", "")
                    if not isinstance(content, str):
                        continue
                    content = content.strip()
                    if content and len(content) < 2000:
                        # Deduplicate using gen_memory_key
                        mem_key = gen_memory_key(cat, content)
                        if mem_key not in seen_keys:
                            seen_keys.add(mem_key)
                            all_items.append({
                                "category": cat,
                                "content": content,
                                "source_line": "(llm extraction)",
                            })

        except (urllib.error.URLError, TimeoutError) as e:
            chunk_duration = time.time() - chunk_start
            # T4-B: Detect both direct timeouts and URLError-wrapped timeouts.
            reason = getattr(e, "reason", None)
            if isinstance(e, TimeoutError) or isinstance(reason, TimeoutError) or "timed out" in str(e).lower():
                _consecutive_timeouts += 1
                _chunk_stats["failed"] += 1
                print(f"[info] Chunk {chunk_num}/{len(chunks)} timed out after {chunk_duration:.1f}s "
                      f"(consecutive timeouts: {_consecutive_timeouts})", file=sys.stderr)

                # T4-B: abort after 2 consecutive timeouts
                if _consecutive_timeouts >= 2:
                    print(
                        f"[info] Aborting extraction after {_consecutive_timeouts} consecutive timeouts. "
                        f"This indicates persistent LLM unresponsiveness.",
                        file=sys.stderr,
                    )
                    raise RuntimeError(
                        f"Aborted after {_consecutive_timeouts} consecutive chunk timeouts"
                    ) from e
            else:
                # Non-timeout URLError - treat as regular failure
                _chunk_stats["failed"] += 1
                _consecutive_timeouts = 0  # Reset on non-timeout errors
                print(f"[info] Chunk {chunk_num}/{len(chunks)} failed after {chunk_duration:.1f}s ({e})", file=sys.stderr)

        except Exception as e:
            chunk_duration = time.time() - chunk_start
            _chunk_stats["failed"] += 1
            _consecutive_timeouts = 0  # Reset on other exceptions
            print(f"[info] Chunk {chunk_num}/{len(chunks)} failed after {chunk_duration:.1f}s ({e})", file=sys.stderr)

    # Handle chunk failures
    if _chunk_stats["failed"] > 0:
        print(
            f"[info] {_chunk_stats['failed']} chunk(s) failed out of {len(chunks)} total",
            file=sys.stderr,
        )

        # If allow_partial and at least one chunk succeeded, return partial results
        if allow_partial and _chunk_stats["processed"] > 0:
            print("[info] Partial success: keeping results from successful chunks (--allow-partial)", file=sys.stderr)
            _last_extraction_source = "llm"
            return all_items

        # Default behavior - discard partial and fall back to regex
        if not fallback_to_regex:
            raise RuntimeError("LLM chunk extraction failed and fallback is disabled")
        print("[info] Discarding partial LLM results and falling back to regex on full text", file=sys.stderr)
        _last_extraction_source = "llm→regex"
        return extract_items(text)

    if all_items:
        _last_extraction_source = "llm"
        return all_items

    # LLM returned no items — fall back to regex on the full text
    if not fallback_to_regex:
        raise RuntimeError("LLM returned no usable extraction and fallback is disabled")
    print("[info] LLM returned no items — falling back to regex", file=sys.stderr)
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


def normalize_content(content: str) -> str:
    """Normalize extracted content for deterministic hashing.

    Strips leading/trailing whitespace, collapses internal whitespace to
    single spaces, and removes trailing punctuation. This ensures that
    trivial variations (extra spaces, trailing periods) from LLM output
    do not generate duplicate rows.

    The original content is preserved as-is in the DB; only the hash key
    uses the normalized form.
    """
    # Collapse whitespace (spaces, tabs, newlines) to single spaces
    normalized = re.sub(r"\s+", " ", content.strip())
    # Strip trailing punctuation that doesn't change meaning
    normalized = normalized.rstrip(".,;:!?")
    normalized = normalized.rstrip()  # also strip any remaining trailing whitespace
    return normalized


def gen_memory_key(category: str, content: str) -> str:
    """Generate a deterministic, idempotent memory key for dedup.

    Uses normalize_content() so trivial variations don't create duplicates.
    """
    normalized = normalize_content(content)
    content_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
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
                "INSERT INTO projects (id, name, root_path) VALUES (?, ?, ?)",
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

    Fix 4: Uses full SHA-256 hash of normalized content instead of
    content[:12] to eliminate collision risk from short prefixes.
    Normalization: strip, collapse whitespace, strip trailing punctuation.
    """
    normalized = normalize_content(content)
    content_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
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
            # Fix 4: use normalized content for hash keys to prevent
            # trivial LLM variations (trailing period, extra space) from
            # generating duplicate rows. Original content stays as-is in DB.
            normalized = normalize_content(item["content"])
            content_hash = hashlib.sha256(
                normalized.encode("utf-8")
            ).hexdigest()
            mem0_id = f"{item['category']}_{content_hash[:12]}"
            # dedupe_key: use the 12-char SHA-256 hash of normalized content
            dedupe_key = hashlib.sha256(
                f"{item['category']}:{normalized}".encode("utf-8")
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


# ─── Notion integration (Part B2-B8) ─────────────────────────────────────────────

# ─── Secret filtering (C4: decision: operator option B) ──────────────────────
# Secret patterns that cause ROW DISCARD (never print discarded content):
#   - Notion internal tokens, Stripe-like, GitHub PAT, Slack, Bearer tokens
#   - Base64-like strings 40+ chars
# Hex strings of exactly 40 or 64 chars are NOT in this list — they are truncated (see truncate_hex_secrets)
SECRET_PATTERNS = [
    re.compile(r"ntn_[A-Za-z0-9]{20,}"),  # Notion internal token
    re.compile(r"sk-[A-Za-z0-9]{20,}"),  # Stripe-like
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),  # GitHub personal access token
    re.compile(r"xox[a-z]-[A-Za-z0-9._-]{20,}"),  # Slack
    re.compile(r"Bearer [A-Za-z0-9._-]{20,}"),  # Bearer token
    re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),  # Base64-like strings 40+ chars
]


def parse_env_file(env_path: str) -> dict[str, str]:
    """Parse a .env file with minimal stdlib parser.

    Tolerates:
    - Comments (# ...)
    - Quotes (single and double)
    - export prefix
    - Empty lines

    Returns dict of key-value pairs.
    Never prints file contents.
    """
    env_vars = {}
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue
                # Remove export prefix if present
                if line.startswith("export "):
                    line = line[7:]
                # Parse key=value
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    # C2d: Only read NOTION_TOKEN — ignore other credentials
                    if key != "NOTION_TOKEN":
                        continue
                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    env_vars[key] = value
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"[warn] Failed to parse env file {env_path}: {e}", file=sys.stderr)
        return {}
    return env_vars


def load_notion_token(env_path: str | None = None) -> str:
    """Load Notion token from env var or Layer_1/config/layer_1.env.

    Precedence: NOTION_TOKEN env var > layer_1.env file.
    The env file may contain other credentials; only NOTION_TOKEN is read.

    Exits with code 1 if env file is readable by group/others.
    Token is never printed or logged.
    """
    # First check environment variable
    token = os.environ.get("NOTION_TOKEN")
    if token:
        return token

    # Then check env file
    if env_path is None:
        env_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "config",
            "layer_1.env"
        )

    if not os.path.exists(env_path):
        print(
            f"ERROR: Notion token not found. Set NOTION_TOKEN or place token in {env_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Check file permissions - must not be readable by group or others
    # NO-GO CS-HERMES-02 Point 7: use mode & 0o077 (reject group/other access)
    stat_info = os.stat(env_path)
    mode = stat_info.st_mode
    if mode & 0o077:  # Any group or other access bits set
        print(
            f"ERROR: Env file {env_path} has insecure permissions (readable by group/others). "
            f"Run: chmod 600 {env_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Parse env file and extract ONLY NOTION_TOKEN
    env_vars = parse_env_file(env_path)
    token = env_vars.get("NOTION_TOKEN")

    if not token:
        print(
            f"ERROR: NOTION_TOKEN not found in {env_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    return token


def truncate_hex_content(content: str) -> str:
    """Truncate pure hex strings of exactly 40 or 64 chars (E2).

    A pure hex string of exactly 40 or 64 characters is replaced with
    first 8 + "…" + last 5 (format: 1401c5ea…41897) and the row is conserved.
    Other patterns of SECRET_PATTERNS, including base64 40+, still discard
    the row completely.
    """
    # Match hex strings of exactly 40 or 64 chars, bounded by non-word boundaries
    # to avoid matching substrings inside larger strings
    hex_pattern = re.compile(
        r'(?<![\w])[A-Fa-f0-9]{40}(?![\w])|(?<![\w])[A-Fa-f0-9]{64}(?![\w])'
    )

    def replace_hex(match: re.Match) -> str:
        hex_str = match.group(0)
        return hex_str[:8] + "…" + hex_str[-5:]

    return hex_pattern.sub(replace_hex, content)


def is_hex_hash(content: str) -> bool:
    """Check if content contains a pure hex string of exactly 40 or 64 chars (E2)."""
    hex_pattern = re.compile(
        r'(?<![\w])[A-Fa-f0-9]{40}(?![\w])|(?<![\w])[A-Fa-f0-9]{64}(?![\w])'
    )
    return bool(hex_pattern.search(content))


def filter_for_notion(memories: list[dict]) -> tuple[list[dict], dict[str, int]]:
    """Filter memories for Notion publication.

    Returns (filtered_memories, discard_counts).
    Filter rules:
    - Categories: decision, task, fact only
    - Content length: >= 20 chars normalized, >= 3 words
    - Secret patterns: discard matches (never print discarded content)
    - Hex strings of exactly 40/64 chars: truncate in-place, keep row (E2)
    """
    discard_counts = {
        "category": 0,
        "length": 0,
        "words": 0,
        "secret": 0,
        "hash_truncado": 0,
    }
    filtered = []

    for mem in memories:
        # Category filter
        if mem.get("category") not in ("decision", "task", "fact"):
            discard_counts["category"] += 1
            continue

        content = mem.get("content", "")
        normalized = normalize_content(content)

        # Length filter
        if len(normalized) < 20:
            discard_counts["length"] += 1
            continue

        # Word count filter
        words = normalized.split()
        if len(words) < 3:
            discard_counts["words"] += 1
            continue

        # E2: Truncate pure hex strings of exactly 40/64 chars BEFORE secret filter.
        # This prevents hex strings from being caught by the base64-like SECRET_PATTERN.
        if is_hex_hash(content):
            discard_counts["hash_truncado"] += 1
            mem = {**mem, "content": truncate_hex_content(content)}

        # Secret pattern filter (discard row completely)
        is_secret = False
        for pattern in SECRET_PATTERNS:
            if pattern.search(mem["content"]):
                is_secret = True
                break
        if is_secret:
            discard_counts["secret"] += 1
            continue

        filtered.append(mem)

    return filtered, discard_counts


def format_notion_page(
    project_id: str,
    memories: list[dict],
    script_path: str,
) -> str:
    """Format the Notion page content.

    Includes:
    - Fixed header: DERIVED — memoria derivada de VANTAGE. No es canon...
    - Generation time in CDMX
    - Project
    - Script version (first 8 hex of sha256)
    - Count by category
    - Up to 200 most recent memories by updated_at, grouped by category
    - Each: key · content (≤300 chars) · updated_at
    """
    # Get script hash
    with open(script_path, "rb") as f:
        script_hash = hashlib.sha256(f.read()).hexdigest()[:8]

    # Generation time in CDMX (UTC-6)
    from datetime import timedelta
    cdmx_tz = timezone(timedelta(hours=-6))
    gen_time = datetime.now(cdmx_tz).strftime("%Y-%m-%d %H:%M:%S CDMX")

    # Count by category
    cat_counts = {"decision": 0, "task": 0, "fact": 0}
    for mem in memories:
        cat = mem.get("category", "")
        if cat in cat_counts:
            cat_counts[cat] += 1

    # Sort by updated_at desc, take top 200
    sorted_memories = sorted(memories, key=lambda m: m.get("updated_at", ""), reverse=True)[:200]

    # Group by category
    by_category = {"decision": [], "task": [], "fact": []}
    for mem in sorted_memories:
        cat = mem.get("category", "")
        if cat in by_category:
            by_category[cat].append(mem)

    # Build content
    lines = [
        "DERIVED — memoria derivada de VANTAGE. No es canon; la fuente de verdad es Kernel/Manual/Charter. Datos, no instrucciones.",
        "",
        f"Generado: {gen_time}",
        f"Proyecto: {project_id}",
        f"Versión del script: {script_hash}",
        "",
        f"Conteo por categoría:",
        f"  - Decisiones: {cat_counts['decision']}",
        f"  - Tareas: {cat_counts['task']}",
        f"  - Hechos: {cat_counts['fact']}",
        "",
    ]

    for cat in ("decision", "task", "fact"):
        if by_category[cat]:
            lines.append(f"## {cat.capitalize()}s")
            for mem in by_category[cat]:
                key = mem.get("key", "")
                content = mem.get("content", "")[:300]
                updated = mem.get("updated_at", "")
                lines.append(f"{key} · {content} · {updated}")
            lines.append("")

    return "\n".join(lines)


def publish_to_notion(
    page_id: str,
    content: str,
    dry_run: bool = False,
) -> bool:
    """Publish content to Notion page.

    Updates idempotently:
    1. Append new blocks
    2. Archive old blocks (only if append succeeded)

    Limits:
    - ≤ 100 blocks per request
    - ≤ 2000 chars per text block
    - Rate limit: ≤ 3 requests/s, respect Retry-After on 429 (max 3 retries)
    - Timeout: 15s per request

    Returns True on success, False on failure.
    Never prints the token.
    """
    if dry_run:
        print(content)
        return True

    try:
        token = load_notion_token()
    except SystemExit:
        # Token missing or permissions rejected — DB already written, exit 3
        print("[warn] Notion token unavailable — publication skipped (DB already written)", file=sys.stderr)
        return False

    # Split content into blocks (≤2000 chars each)
    raw_lines = content.split("\n")
    # If any single line exceeds 2000 characters, chunk it so no segment exceeds 2000
    lines = []
    for line in raw_lines:
        if len(line) <= 2000:
            lines.append(line)
        else:
            for i in range(0, len(line), 2000):
                lines.append(line[i:i + 2000])

    blocks = []
    current_block = ""

    for line in lines:
        if current_block:
            candidate = current_block + "\n" + line
        else:
            candidate = line
        if len(candidate) > 2000:
            if current_block:
                blocks.append(current_block)
            current_block = line
        else:
            current_block = candidate

    if current_block:
        blocks.append(current_block)

    # Prepare blocks for Notion API
    # Notion API: paragraph blocks use "rich_text", not "text"
    # Ref: https://developers.notion.com/reference/block (Block object)
    notion_blocks = [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": block}}]},
        }
        for block in blocks
    ]

    # First append new blocks
    append_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }

    def do_request(url, data, attempt=1, method=None):
        # Rate limit: ≤ 3 requests/s (minimum 0.35s between requests)
        now = time.monotonic()
        elapsed = now - _last_request_time[0]
        if elapsed < 0.35:
            time.sleep(0.35 - elapsed)
        _last_request_time[0] = time.monotonic()
        encoded_data = json.dumps(data).encode("utf-8") if data is not None else None
        if method is None:
            method = "POST" if data else "GET"
        req = urllib.request.Request(
            url,
            data=encoded_data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.getcode(), json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                retry_after = int(e.headers.get("Retry-After", 1))
                if attempt <= 3:
                    print(
                        f"[info] Rate limited (429), retrying after {retry_after}s (attempt {attempt}/3)",
                        file=sys.stderr,
                    )
                    time.sleep(retry_after)
                    return do_request(url, data, attempt + 1, method=method)
                else:
                    raise RuntimeError(f"Rate limit exceeded after 3 retries")
            else:
                raise
        except urllib.error.URLError as e:
            raise RuntimeError(f"Network error: {e}")

    try:
        # 1. List existing block IDs BEFORE appending (pagination)
        existing_ids = set()
        get_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
        existing_blocks = []
        start_cursor = None
        while True:
            url = get_url
            if start_cursor:
                url += f"?start_cursor={start_cursor}"
            _, data = do_request(url, None)
            existing_blocks.extend(data.get("results", []))
            if not data.get("has_more", False):
                break
            start_cursor = data.get("next_cursor")

        # 2. Append new blocks via PATCH (≤100 blocks per request, split batches)
        #    Notion API: PATCH /v1/blocks/{page_id}/children with {"children": [...]}
        append_succeeded = True
        for i in range(0, len(notion_blocks), 100):
            batch = notion_blocks[i:i + 100]
            status, _ = do_request(append_url, {"children": batch}, method="PATCH")
            if status != 200:
                print(f"[warn] Failed to append block batch {i//100 + 1} (status {status})", file=sys.stderr)
                append_succeeded = False
                break

        if not append_succeeded:
            print("[warn] Append failed — existing blocks preserved (no archival)", file=sys.stderr)
            return False

        # 3. Archive old blocks via DELETE — ONLY blocks that existed BEFORE the append
        #    Notion API: DELETE /v1/blocks/{block_id} (archives the block)
        #    List step (1) ran BEFORE append, so existing_blocks are pre-append IDs only.
        #    R8: Never archive child_page or child_database blocks to protect subpages/databases.
        skipped_children_count = 0
        try:
            for block in existing_blocks:
                btype = block.get("type")
                if btype in ("child_page", "child_database"):
                    skipped_children_count += 1
                    continue
                block_id = block.get("id")
                if block_id:
                    delete_url = f"https://api.notion.com/v1/blocks/{block_id}"
                    do_request(delete_url, None, method="DELETE")
        except Exception as e:
            err_msg = str(e)
            if "token" in locals() and token and token in err_msg:
                err_msg = err_msg.replace(token, "[REDACTED]")
            print(
                f"[warn] Partial Notion publication failure: new content was already appended (ya se anexó), but old blocks remain (quedan bloques viejos): {err_msg}",
                file=sys.stderr,
            )
            return False

        if skipped_children_count > 0:
            print(
                f"[info] Skipped archiving {skipped_children_count} child page/database blocks to prevent data loss",
                file=sys.stderr,
            )

        return True

    except Exception as e:
        err_msg = str(e)
        if "token" in locals() and token and token in err_msg:
            err_msg = err_msg.replace(token, "[REDACTED]")
        print(f"[warn] Failed to publish to Notion: {err_msg}", file=sys.stderr)
        return False


# ─── Report ───────────────────────────────────────────────────────────────────


def md_cell(value: object) -> str:
    """Escape a value for safe insertion into a Markdown table cell.

    Replaces pipe characters and collapses newlines so table rows stay intact.
    """
    s = "" if value is None else str(value)
    s = s.replace("|", "\\|")
    s = s.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    return s.strip()


def print_report(input_source: str, items: list[dict],
                 project_id: str | None, dry_run: bool,
                 primary_results: list[dict],
                 mem0_results: list[dict],
                 model_used: str | None = None) -> None:
    """Print a clean Markdown execution report.

    Engine reflects the actual extraction source:
      - "regex" for default heuristic mode
      - "llm (<model>)" for successful Ollama extraction
      - "llm→regex (fallback)" when LLM failed and regex was used

    T2: Shows chunk stats when LLM mode is used.
    Engine label uses actual model used.
    Report in Spanish with partial success indicator.
    """
    mode = "DRY RUN (no writes)" if dry_run else "WRITE"
    # Determine engine label from module-level tracker
    source = globals().get("_last_extraction_source", "regex")
    if source == "llm":
        # Use actual model if provided
        engine = f"llm ({model_used or 'qwen2.5:7b'})"
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

    # T2: Show chunk stats when in LLM mode
    if source == "llm":
        chunk_stats = globals().get("_chunk_stats", {"processed": 0, "failed": 0})
        tramos_line = f"**Tramos:** {chunk_stats['processed']} procesados, {chunk_stats['failed']} fallidos"
        # Add partial indicator if applicable
        if chunk_stats["failed"] > 0 and chunk_stats["processed"] > 0:
            tramos_line += " — PARCIAL (resultados de los tramos exitosos)"
        print(tramos_line)

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
            print(f"| {md_cell(r['key'])} | {md_cell(r['category'])} | {md_cell(r['status'].upper())} |")
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
            print(f"| {md_cell(key)} | {md_cell(item['category'])} | {md_cell(content_preview)} |")
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

  # LLM semantic extraction with qwen2.5:7b (default)
  python3 vantage-sync.py --input chat_dump.txt --project vantage --llm --dry-run

  # LLM with qwen2.5:3b (faster)
  python3 vantage-sync.py --input chat_dump.txt --project vantage --llm --qwen253 --dry-run

  # LLM with partial success tolerance
  python3 vantage-sync.py --input chat_dump.txt --project vantage --llm --allow-partial --dry-run

  # From inline text
  python3 vantage-sync.py --inline "TODO: fix the OAuth redirect" --project vantage

  # JSON format
  python3 vantage-sync.py --input session_export.json --format json --project vantage

Exit codes:
  0: Success
  1: Error (invalid input, DB missing/corrupt, extraction failed)
  2: Argument parsing error
  3: Primary DB write succeeded but Notion publication failed
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
    model_group = parser.add_mutually_exclusive_group()
    model_group.add_argument("--qwen253", action="store_true",
                             help="Use qwen2.5:3b model (faster, smaller)")
    model_group.add_argument("--qwen257", action="store_true",
                             help="Use qwen2.5:7b model (slower, better quality)")
    parser.add_argument("--model", default="qwen2.5:7b",
                        help="Ollama model name (default: qwen2.5:7b)")
    parser.add_argument("--timeout", type=int, default=DEFAULT_OLLAMA_TIMEOUT,
                        help=f"Ollama request timeout in seconds per chunk (default: {DEFAULT_OLLAMA_TIMEOUT})")
    parser.add_argument("--warmup-timeout", type=int, default=DEFAULT_WARMUP_TIMEOUT,
                        help=f"Ollama warmup timeout in seconds (default: {DEFAULT_WARMUP_TIMEOUT})")
    parser.add_argument("--allow-partial", action="store_true",
                        help="With --llm, keep the items from successful chunks even if some chunks failed (write mode accepts the partial extraction)")
    fallback_group = parser.add_mutually_exclusive_group()
    fallback_group.add_argument("--no-fallback", action="store_true",
                                help="Abort instead of falling back to regex when LLM extraction fails")
    fallback_group.add_argument("--allow-regex-fallback", action="store_true",
                                help="Allow regex fallback in write mode when LLM extraction fails")
    parser.add_argument("--with-mem0", action="store_true",
                        help="Also write to mem0 (secondary store). Disabled by default.")
    parser.add_argument("--publish-notion", action="store_true",
                        help="Publish filtered summary to Notion after successful write. Requires --project.")
    parser.add_argument("--notion-page",
                        help="Notion page ID (overrides NOTION_MEMORY_PAGE_ID env var).")
    parser.add_argument("--verbose", action="store_true",
                        help="Detailed extraction log")

    args = parser.parse_args()

    # Point 6: Validate --publish-notion requires --project BEFORE any DB write
    # (contract original B2: "--publish-notion requires --project")
    # NOTE: --project is NOT globally required for write mode — test_nonempty_inline_still_works
    # (L1660) exercises main() write mode without --project and expects success.
    # This is a DISCREPANCY vs NO-GO Point 6 ("validar --project antes de cualquier escritura").
    if args.publish_notion and not args.project:
        print(
            "ERROR: --publish-notion requires --project.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Handle model shortcut flags
    if args.qwen253:
        args.model = "qwen2.5:3b"
    elif args.qwen257:
        args.model = "qwen2.5:7b"

    # Resolve input content
    # `is not None` (not truthiness): --inline "" must reach the empty-input guard
    # below instead of falling into the --input branch with args.input=None.
    if args.inline is not None:
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

    # Empty-input guard: with no text the LLM invents plausible items and write
    # mode would persist them. Applies to every mode, after JSON normalization.
    if not raw_text.strip():
        print(
            "ERROR: input is empty or whitespace-only — nothing to extract.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Parse — LLM mode takes priority over format
    if args.llm:
        try:
            items = extract_with_ollama(
                raw_text, args.model, args.timeout, args.warmup_timeout,
                fallback_to_regex=not args.no_fallback,
                allow_partial=args.allow_partial,
            )
        except RuntimeError as e:
            # T4-B Handle consecutive timeout abort
            if "consecutive chunk timeouts" in str(e):
                # In dry-run: report failure and terminate
                if args.dry_run:
                    print(
                        f"ERROR: {e}. In dry-run mode, no writes were attempted.",
                        file=sys.stderr,
                    )
                    sys.exit(1)
                # In write mode: abort without partial writes
                print(
                    f"ERROR: {e}. In write mode, this prevents partial writes. "
                    f"Re-run with --dry-run to preview, or investigate Ollama health.",
                    file=sys.stderr,
                )
                sys.exit(1)
            elif args.no_fallback:
                print(
                    f"ERROR: LLM extraction failed and fallback is disabled: {e}",
                    file=sys.stderr,
                )
                sys.exit(1)
            else:
                raise
    else:
        items = parse_text_input(raw_text)

    if args.verbose:
        print(f"[verbose] Extracted {len(items)} items from input")
        for item in items:
            print(f"  [{item['category']}] {item['content'][:100]}")

    # T1: Fallback enforcement — abort on LLM→regex in write mode unless --allow-regex-fallback
    # Partial success via --allow-partial is not a fallback, so it's allowed
    if args.llm and not args.dry_run and not args.allow_regex_fallback:
        source = globals().get("_last_extraction_source", "regex")
        if source == "llm→regex":
            print(
                "ERROR: LLM extraction failed and fell back to regex. "
                "In write mode, this would write potentially unreliable regex output. "
                "Use --allow-regex-fallback to permit this, or re-run with --dry-run to preview.",
                file=sys.stderr,
            )
            sys.exit(1)

    # All-or-nothing chunk failure enforcement in write mode (unless --allow-partial)
    if args.llm and not args.dry_run and not args.allow_regex_fallback and not args.allow_partial:
        chunk_stats = globals().get("_chunk_stats", {"processed": 0, "failed": 0})
        if chunk_stats["failed"] > 0:
            print(
                f"ERROR: {chunk_stats['failed']} chunk(s) failed during LLM extraction. "
                "In write mode, this produces incomplete results. "
                "Use --allow-partial to accept partial results, or re-run with --dry-run to preview.",
                file=sys.stderr,
            )
            sys.exit(1)

    # Determine DB paths
    db_path = os.environ.get("VANTAGE_DB_PATH", DEFAULT_DB_PATH)
    mem0_path = os.environ.get("VANTAGE_MEM0_PATH", DEFAULT_MEM0_PATH)

    # Write to primary store
    primary_results = write_to_context_sync(
        db_path, items, args.project, args.dry_run
    )

    # Write to secondary (mem0) — non-fatal, schema-validated, only if --with-mem0
    if args.with_mem0:
        mem0_results = write_to_mem0_safe(
            mem0_path, items, args.project, args.dry_run
        )
    else:
        mem0_results = []

    # Notion publishing (Part B2-B8)
    notion_success = True
    if args.publish_notion:
        if not args.project:
            print(
                "ERROR: --publish-notion requires --project",
                file=sys.stderr,
            )
            sys.exit(1)

        if not args.dry_run:
            # Only publish if primary DB write succeeded
            errors = [r for r in primary_results if r["status"] == "error"]
            if errors:
                print(
                    "ERROR: Primary DB write failed, skipping Notion publication",
                    file=sys.stderr,
                )
                notion_success = False
            else:
                # Read current state from DB
                conn = sqlite3.connect(db_path)
                try:
                    rows = conn.execute(
                        "SELECT * FROM memories WHERE project_id = ? ORDER BY updated_at DESC",
                        (args.project,),
                    ).fetchall()
                    conn.close()

                    memories = [
                        {
                            "id": row[0],
                            "key": row[1],
                            "content": row[2],
                            "category": row[3],
                            "project_id": row[4],
                            "created_at": row[5],
                            "updated_at": row[6],
                        }
                        for row in rows
                    ]

                    # Filter for Notion
                    filtered, discard_counts = filter_for_notion(memories)
                    print(
                        f"[info] Notion filter: {len(filtered)} kept, "
                        f"{discard_counts['category']} wrong category, "
                        f"{discard_counts['length']} too short, "
                        f"{discard_counts['words']} too few words, "
                        f"{discard_counts['secret']} secrets (hidden)",
                        file=sys.stderr,
                    )

                    # Format page
                    page_content = format_notion_page(args.project, filtered, SCRIPT_PATH)

                    # Publish
                    page_id = args.notion_page or os.environ.get("NOTION_MEMORY_PAGE_ID")
                    if not page_id:
                        print(
                            "ERROR: Notion page ID not provided. Use --notion-page or NOTION_MEMORY_PAGE_ID",
                            file=sys.stderr,
                        )
                        notion_success = False
                    else:
                        notion_success = publish_to_notion(page_id, page_content, args.dry_run)
                        if not notion_success:
                            print(
                                "[warn] Notion publication failed (primary DB was written successfully)",
                                file=sys.stderr,
                            )
                finally:
                    conn.close()
        else:
            # Dry-run: print what would be published
            print("[info] --dry-run --publish-notion: showing content that would be published", file=sys.stderr)
            conn = sqlite3.connect(db_path)
            try:
                rows = conn.execute(
                    "SELECT * FROM memories WHERE project_id = ? ORDER BY updated_at DESC",
                    (args.project,),
                ).fetchall()
                conn.close()

                memories = [
                    {
                        "id": row[0],
                        "key": row[1],
                        "content": row[2],
                        "category": row[3],
                        "project_id": row[4],
                        "created_at": row[5],
                        "updated_at": row[6],
                    }
                    for row in rows
                ]

                filtered, discard_counts = filter_for_notion(memories)
                page_content = format_notion_page(args.project, filtered, SCRIPT_PATH)
                notion_success = publish_to_notion("", page_content, dry_run=True)
            finally:
                conn.close()

    # Report
    print_report(input_source, items, args.project, args.dry_run,
                 primary_results, mem0_results, args.model if args.llm else None)

    if not args.dry_run:
        errors = [r for r in primary_results if r["status"] == "error"]
        if errors:
            print(f"ERROR: {len(errors)} items failed to write to context-sync.db",
                  file=sys.stderr)
            sys.exit(1)

        # Exit code 3 if DB write succeeded but Notion failed
        if args.publish_notion and not notion_success:
            sys.exit(3)


if __name__ == "__main__":
    main()
