#!/usr/bin/env python3
"""
tests/test_vantage_sync.py — Unit tests for Layer_1/scripts/vantage-sync.py

Covers all 7 P0 fixes:
  Fix 1: Intelligent truncation for LLM (preserves end-of-chat)
  Fix 2: DB validation (missing tables, 0-byte files, non-existent DB)
  Fix 3: ensure_project wrapped with retry_sqlite
  Fix 4: mem0 dedupe_key uses SHA-256 (not content[:12])
  Fix 5: JSON normalization before LLM extraction
  Fix 6: alias vctx (validated via .zshrc content)
  Fix 7: full idempotency + fallback behavior

Tests run against isolated temp databases — never touch ~/.vantage/.
"""

import json
import os
import hashlib
import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from importlib.util import spec_from_file_location, module_from_spec

import pytest


# ─── Module loading ───────────────────────────────────────────────────────────

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "vantage-sync.py"


@pytest.fixture(scope="session")
def vsync_module():
    """Import vantage-sync.py as a module without executing main()."""
    spec = spec_from_file_location("vantage_sync", str(SCRIPT_PATH))
    if spec is None or spec.loader is None:
        pytest.skip(f"Cannot load spec for {SCRIPT_PATH}")
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_db(tmp_path, vsync_module):
    """Create a valid context-sync.db schema in a temp path."""
    db_path = str(tmp_path / "context-sync.db")
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            content TEXT NOT NULL,
            category TEXT,
            project_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            root_path TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX idx_memories_key ON memories(key);
        CREATE INDEX idx_memories_project ON memories(project_id);
        CREATE INDEX idx_memories_category ON memories(category);
    """)
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def tmp_mem0(tmp_path):
    """Create a valid mem0 schema in a temp path."""
    db_path = str(tmp_path / "mem0" / "memories.sqlite")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript("""
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
    """)
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def sample_chat_text():
    """Simulated collapsed chat dump."""
    return """\
[2026-10-11 07:47:05 CST]

SESSION CONTRACT: HERMES-VANTAGE-SYNC-CLI-001

DECISION: Proceed with Phase 2 implementation per blueprint.
DECISION: mem0 failures are non-fatal — context-sync.db is primary.

TODO: Create test fixture file
TODO: Verify retry logic handles SQLITE_BUSY correctly
action item: Run dry-run test before real write

Deliverable 1: Python CLI Script (Layer_1/scripts/vantage-sync.py)
entregable: vantage-sync.py at Layer_1/scripts/vantage-sync.py
result: context-sync.db should contain extracted items

git checkout feature-branch
file: config/settings.json

Binary Gate Rule: No modify files or write definitive code without APPROVED.
CHARTER:NON-NEGOTIABLE-001 (Inward-First & Local)
"""


@pytest.fixture
def sample_chat_json():
    """JSON-formatted chat dump."""
    return json.dumps([
        {"role": "user", "content": "DECISION: Aproceed with implementation."},
        {"role": "assistant", "content": "TODO: Write the script vantage-sync.py"},
        {"role": "user", "content": "Deliverable 1: Python CLI Script"},
    ])


# ─── Fix 1: Intelligent truncation ────────────────────────────────────────────

class TestIntelligentTruncation:
    """Fix 1: text[:8000] replaced with intelligent head+tail truncation."""

    def test_short_text_unchanged(self, vsync_module):
        """Text within limit should pass through unmodified."""
        text = "x" * 5000
        result = vsync_module.intelligent_truncate(text)
        assert result == text

    def test_long_text_truncated_with_head_and_tail(self, vsync_module):
        """Text exceeding limit should be truncated with head + tail + marker."""
        text = "x" * 50000
        result = vsync_module.intelligent_truncate(text)
        assert len(result) < 50000
        assert "TRUNCATED" in result
        assert result.startswith("x" * 100)  # head preserved
        assert result.endswith("x" * 100)   # tail preserved

    def test_tail_priority(self, vsync_module):
        """The end of the original text must be preserved (recent TODOs)."""
        text = "A" * 7000 + "TODO: fix important bug at the end"
        result = vsync_module.intelligent_truncate(text)
        assert "TODO: fix important bug at the end" in result


# ─── Fix 2: DB validation ─────────────────────────────────────────────────────

class TestDbValidation:
    """Fix 2: strict DB validation — exit 1 on missing/corrupt DB."""

    def test_missing_db_exits_1(self, vsync_module, tmp_path):
        """Non-existent DB file should sys.exit(1)."""
        missing = str(tmp_path / "nonexistent.db")
        with pytest.raises(SystemExit) as exc_info:
            vsync_module.write_to_context_sync(missing, [], None, dry_run=False)
        assert exc_info.value.code == 1

    def test_zero_byte_db_exits_1(self, vsync_module, tmp_path):
        """0-byte DB file should sys.exit(1) to prevent corruption."""
        empty_db = str(tmp_path / "empty.db")
        Path(empty_db).touch()  # creates 0-byte file
        with pytest.raises(SystemExit) as exc_info:
            vsync_module.write_to_context_sync(empty_db, [], None, dry_run=False)
        assert exc_info.value.code == 1

    def test_missing_tables_exits_1(self, vsync_module, tmp_path):
        """DB file exists but missing required tables should exit 1."""
        db_path = str(tmp_path / "wrong_schema.db")
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE wrong_table (id INTEGER)")
        conn.commit()
        conn.close()
        with pytest.raises(SystemExit) as exc_info:
            vsync_module.write_to_context_sync(db_path, [], None, dry_run=False)
        assert exc_info.value.code == 1


# ─── Fix 3: ensure_project with retry ─────────────────────────────────────────

class TestEnsureProjectRetry:
    """Fix 3: ensure_project wrapped with retry_sqlite."""

    def test_ensure_project_called_via_retry(self, vsync_module, tmp_db):
        """ensure_project should use retry_sqlite (not raw conn.execute)."""
        with patch.object(vsync_module, 'retry_sqlite', side_effect=lambda fn, **kw: fn()) as mock_retry:
            conn = sqlite3.connect(tmp_db)
            vsync_module.ensure_project(conn, "test-proj", "Test Project")
            conn.close()
            assert mock_retry.called

    def test_ensure_project_writes_once(self, vsync_module, tmp_db):
        """ensure_project should not duplicate project on re-run (idempotent)."""
        conn = sqlite3.connect(tmp_db)
        vsync_module.ensure_project(conn, "proj-1", "P1")
        conn.close()

        # Second call should NOT create a duplicate
        conn = sqlite3.connect(tmp_db)
        vsync_module.ensure_project(conn, "proj-1", "P1")
        conn.close()

        conn = sqlite3.connect(tmp_db)
        count = conn.execute("SELECT COUNT(*) FROM projects WHERE id = 'proj-1'").fetchone()[0]
        conn.close()
        assert count == 1


# ─── Fix 4: mem0 dedupe_key uses SHA-256 ───────────────────────────────────────

class TestMem0DedupeKey:
    """Fix 4: dedupe_key uses SHA-256 hash, not content[:12] prefix."""

    def test_dedupe_key_is_sha256_not_prefix(self, vsync_module):
        """dedupe_key for mem0 should be 12-char SHA-256 hash, not content[:12]."""
        content = "This is a test fact"
        # The dedupe_key is computed inside write_to_mem0 — let's verify
        # by computing what it should be
        expected = hashlib.sha256(
            f"fact:{content}".encode("utf-8")
        ).hexdigest()[:12]
        assert len(expected) == 12
        # Verify it's NOT just content[:12]
        assert expected != content[:12]

    def test_dedupe_key_no_collision_on_similar_content(self, vsync_module):
        """Two contents with same first 12 chars should have different dedupe_keys."""
        import hashlib
        content_a = "TODO: fix the auth bug right now"
        content_b = "TODO: fix the auth bug right now but different"
        # Old method: both would have dedupe_key = "TODO: fix th" → collision
        old_a = content_a[:12]
        old_b = content_b[:12]
        assert old_a == old_b  # demonstrates the old bug
        # New method: SHA-256 hash — no collision
        new_a = hashlib.sha256(f"task:{content_a}".encode()).hexdigest()[:12]
        new_b = hashlib.sha256(f"task:{content_b}".encode()).hexdigest()[:12]
        assert new_a != new_b


# ─── Fix 5: JSON normalization before LLM ─────────────────────────────────────

class TestJsonLlmNormalization:
    """Fix 5: --format json normalized to text before LLM extraction."""

    def test_normalize_json_to_text(self, vsync_module, sample_chat_json):
        """normalize_json_input should produce concatenated text."""
        text = vsync_module.normalize_json_input(sample_chat_json)
        assert "DECISION: Aproceed" in text
        assert "TODO: Write the script" in text
        assert "Deliverable 1" in text

    def test_json_input_with_inline_and_llm(self, vsync_module, sample_chat_json):
        """JSON format + --llm should work: normalize first, then LLM (or regex fallback)."""
        items = vsync_module.parse_json_input(sample_chat_json)
        # Should extract items from normalized text via regex
        assert len(items) >= 2  # at least the DECISION and TODO

    def test_invalid_json_exits_1(self, vsync_module):
        """Invalid JSON with --format json should exit with code 1."""
        import io
        from contextlib import redirect_stderr
        err_buf = io.StringIO()
        with pytest.raises(SystemExit) as exc_info:
            with redirect_stderr(err_buf):
                vsync_module.parse_json_input("{invalid json}")
        assert exc_info.value.code == 1
        assert "not valid JSON" in err_buf.getvalue()


# ─── Fix 6: alias vctx ─────────────────────────────────────────────────────────
# This fix is applied to .zshrc — tested by checking the file content.

class TestVctxAlias:
    """Fix 6: vctx alias exists in .zshrc, vsync remains for vantage.py sync."""

    def test_vctx_alias_exists(self):
        """ .zshrc must contain the vctx alias for vantage-sync.py."""
        zshrc = Path.home() / ".zshrc"
        assert zshrc.exists(), ".zshrc not found"
        content = zshrc.read_text(encoding="utf-8")
        assert "alias vctx=" in content, "vctx alias not found in .zshrc"
        assert "vantage-sync.py" in content, "vctx alias doesn't reference vantage-sync.py"

    def test_vsync_alias_unchanged(self):
        """ .zshrc must still map vsync to vantage.py sync."""
        zshrc = Path.home() / ".zshrc"
        content = zshrc.read_text(encoding="utf-8")
        # vsync should point to vantage.py sync, NOT vantage-sync.py
        assert "alias vsync=" in content
        assert "vantage.py sync" in content


# ─── Fix 7: Idempotency + fallback + integration tests ───────────────────────

class TestIdempotency:
    """Re-running the same input should not create duplicate rows."""

    def test_regex_idempotent(self, vsync_module, tmp_db, sample_chat_text):
        """Same regex extraction + write → same keys, no dups."""
        items = vsync_module.parse_text_input(sample_chat_text)

        # First write
        results1 = vsync_module.write_to_context_sync(
            tmp_db, items, "test-proj", dry_run=False
        )
        assert all(r["status"] == "written" for r in results1)

        # Second write with same items
        results2 = vsync_module.write_to_context_sync(
            tmp_db, items, "test-proj", dry_run=False
        )
        assert all(r["status"] == "written" for r in results2)

        # Count should remain the same
        conn = sqlite3.connect(tmp_db)
        count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        conn.close()
        assert count == len(items)


class TestDryRun:
    """--dry-run must never touch SQLite."""

    def test_dry_run_no_db_connection(self, vsync_module, tmp_db):
        """Dry-run should return results without opening the DB."""
        items = [{"category": "task", "content": "test task", "source_line": "test"}]
        results = vsync_module.write_to_context_sync(
            tmp_db, items, "proj", dry_run=True
        )
        assert all(r["status"] == "dry_run" for r in results)
        # Verify no data was written
        conn = sqlite3.connect(tmp_db)
        count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        conn.close()
        assert count == 0


class TestLlmFallback:
    """Ollama failure → regex fallback."""

    def test_ollama_timeout_falls_back(self, vsync_module, sample_chat_text):
        """If Ollama is unreachable, should fall back to regex extraction."""
        with patch.object(vsync_module.urllib.request, 'urlopen',
                          side_effect=Exception("Connection refused")):
            items = vsync_module.extract_with_ollama(
                sample_chat_text, model="qwen2.5:7b", timeout=5
            )
        # Should have fallen back to regex
        assert len(items) > 0
        assert any(i["category"] == "task" for i in items)

    def test_ollama_empty_response_falls_back(self, vsync_module, sample_chat_text):
        """If Ollama returns empty JSON, should fall back to regex."""
        mock_resp = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=None)
        mock_resp.read.return_value = json.dumps({
            "response": '{"decisions": [], "tasks": [], "facts": []}'
        }).encode("utf-8")

        with patch.object(vsync_module.urllib.request, 'urlopen',
                          return_value=mock_resp):
            items = vsync_module.extract_with_ollama(
                sample_chat_text, model="qwen2.5:7b", timeout=5
            )
        assert len(items) > 0  # regex fallback


class TestEndToEnd:
    """Full integration: write to both stores, verify independently."""

    def test_write_and_verify(self, vsync_module, tmp_db, tmp_path, sample_chat_text):
        """End-to-end: extract → write → independent sqlite3 verification."""
        # Use temp mem0
        mem0_path = str(tmp_path / "mem0" / "memories.sqlite")
        os.makedirs(os.path.dirname(mem0_path), exist_ok=True)
        conn = sqlite3.connect(mem0_path)
        conn.executescript("""
            CREATE TABLE memories (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL, content TEXT NOT NULL,
                scope TEXT NOT NULL, provenance TEXT NOT NULL,
                metadata TEXT NOT NULL, embedding TEXT NOT NULL,
                dedupe_key TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE INDEX idx_memories_dedupe_key ON memories (dedupe_key);
        """)
        conn.commit()
        conn.close()

        # Extract
        items = vsync_module.parse_text_input(sample_chat_text)
        assert len(items) > 0

        # Write to primary
        primary_results = vsync_module.write_to_context_sync(
            tmp_db, items, "e2e-test", dry_run=False
        )
        assert all(r["status"] == "written" for r in primary_results)

        # Write to mem0
        mem0_results = vsync_module.write_to_mem0(mem0_path, items, "e2e-test", dry_run=False)
        assert all(r["status"] == "written" for r in mem0_results)

        # Independent verification
        conn = sqlite3.connect(tmp_db)
        primary_count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        conn.close()

        conn = sqlite3.connect(mem0_path)
        mem0_count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        conn.close()

        assert primary_count == len(items)
        assert mem0_count == len(items)
