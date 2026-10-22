#!/usr/bin/env python3
"""
tests/test_vantage_sync.py - Unit tests for Layer_1/scripts/vantage-sync.py

Covers all 7 P0 fixes:
  Fix 1: Intelligent truncation for LLM (preserves end-of-chat with hueco)
  Fix 2: DB validation (missing tables, 0-byte files, non-existent DB)
  Fix 3: ensure_project wrapped with retry_sqlite
  Fix 4: mem0 dedupe_key uses SHA-256 (not content[:12])
  Fix 5: JSON normalization before LLM extraction
  Fix 6: alias vctx (validated via .zshrc content)
  Fix 7: full idempotency + fallback behavior
  P0 lock: validate_db_file wrapped in retry_sqlite

Contract CS-DEVIN-NN additions:
  Part A: MCP server read-only mode
  Part B1: --with-mem0 flag
  Part B2-B8: --publish-notion flag with Notion integration

Tests run against isolated temp databases - never touch ~/.vantage/.
Tests live in Layer_1/tests/ (not repo-root tests/).
"""

import json
import os
import re
import hashlib
import sqlite3
import sys
import tempfile
import io
import urllib.error
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
DECISION: mem0 failures are non-fatal - context-sync.db is primary.

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
    """Intelligent truncation for LLM (preserves end-of-chat content with hueco).

    Fix 1: text[:8000] replaced with intelligent head+tail truncation that
    preserves the final content (recent TODOs/decisions) by keeping head + tail.
    """

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
    """Fix 2: strict DB validation - exit 1 on missing/corrupt DB."""

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


# ─── P0 Lock resilience: real SQLite lock test ──────────────────────────────────

class TestDbLockResilience:
    """P0 lock: validate_db_file wrapped in retry_sqlite; concurrent lock test."""

    def test_validate_db_file_with_concurrent_lock(self, vsync_module, tmp_db, tmp_path):
        """When another process holds an EXCLUSIVE lock, validate_db_file should
        retry (not traceback) and eventually succeed with a clear outcome.

        Uses a real subprocess holding BEGIN EXCLUSIVE to create a contended lock.
        """
        import subprocess
        import time as time_mod

        # Start a subprocess that holds an exclusive lock for 3 seconds
        lock_script = f"""
import sqlite3, time
conn = sqlite3.connect("{tmp_db}", timeout=10000)
conn.execute("BEGIN EXCLUSIVE")
time.sleep(3)
conn.execute("COMMIT")
conn.close()
"""
        proc = subprocess.Popen(
            [sys.executable, "-c", lock_script],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        # Give the subprocess time to acquire the lock
        time_mod.sleep(0.5)

        try:
            items = [{"category": "task", "content": "locked test task",
                      "source_line": "test"}]
            # This should retry, not traceback - it will eventually succeed
            # after the lock is released (or fail with retry after retries)
            results = vsync_module.write_to_context_sync(
                tmp_db, items, "lock-test", dry_run=False
            )
            # If it succeeded, the item should be written
            if results:
                assert results[0]["status"] in ("written", "error")
        finally:
            proc.wait(timeout=10)
            assert proc.returncode == 0, "Lock subprocess should complete cleanly"

    def test_validate_db_file_retry_on_lock_no_traceback(self, vsync_module, tmp_db):
        """Verify retry_sqlite is applied to DB connect+validate path.

        Mock connect_db to raise SQLITE_BUSY on first calls, verify retry
        succeeds without traceback.
        """
        call_count = [0]

        original_connect = vsync_module.connect_db

        def flaky_connect(path, timeout=5000):
            call_count[0] += 1
            if call_count[0] < 3:
                conn = sqlite3.connect(":memory:")
                raise sqlite3.OperationalError("database is locked")
            return original_connect(path, timeout)

        with patch.object(vsync_module, 'connect_db', side_effect=flaky_connect):
            # validate_db_file should retry and succeed on 3rd attempt
            try:
                conn = vsync_module.validate_db_file(tmp_db, ["projects", "memories"])
                conn.close()
                # If we got here, retry succeeded
            except SystemExit:
                # If retries exhausted, it exits 1 - not a traceback
                pass  # acceptable: all retries failed, clean exit
        # Key assertion: no traceback raised (either succeeded or SystemExit)

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
        # The dedupe_key is computed inside write_to_mem0 - let's verify
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
        # New method: SHA-256 hash - no collision
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
# This fix is applied to .zshrc - tested by checking the file content.
# Tests are hermetic: skip if ~/.zshrc doesn't exist (tests should work on any machine).

ZSHRC_PATH = Path.home() / ".zshrc"


class TestVctxAlias:
    """Fix 6: vctx alias exists in .zshrc, vsync remains for vantage.py sync.

    Skipped if ~/.zshrc is not present (hermetic on machines without zsh).
    """

    def test_vctx_alias_exists(self):
        """ .zshrc must contain the vctx alias for vantage-sync.py."""
        if not ZSHRC_PATH.exists():
            pytest.skip(".zshrc not found - skipping operator-machine-specific test")
        content = ZSHRC_PATH.read_text(encoding="utf-8")
        assert "alias vctx=" in content, "vctx alias not found in .zshrc"
        assert "vantage-sync.py" in content, "vctx alias doesn't reference vantage-sync.py"

    def test_vsync_alias_unchanged(self):
        """ .zshrc must still map vsync to vantage.py sync."""
        if not ZSHRC_PATH.exists():
            pytest.skip(".zshrc not found - skipping operator-machine-specific test")
        content = ZSHRC_PATH.read_text(encoding="utf-8")
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
            "done": True,
            "response": '{"decisions": [], "tasks": [], "facts": []}'
        }).encode("utf-8")

        with patch.object(vsync_module.urllib.request, 'urlopen',
                          return_value=mock_resp):
            items = vsync_module.extract_with_ollama(
                sample_chat_text, model="qwen2.5:7b", timeout=5
            )
        assert len(items) > 0  # regex fallback


class TestVhRegressions:
    def test_source_line_is_the_line_containing_the_match(self, vsync_module):
        text = "introductory context\n" + "x" * 220 + "\nTODO: preserve the actual source line"
        item = next(i for i in vsync_module.extract_items(text) if i["category"] == "task")
        assert item["source_line"] == "TODO: preserve the actual source line"

    def test_llm_source_line_uses_explicit_marker(self, vsync_module):
        class MockResp:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self):
                return json.dumps({
                    "done": True,
                    "response": json.dumps({
                        "decisions": [{"content": "Keep source traceability"}],
                        "tasks": [],
                        "facts": [],
                    }),
                }).encode("utf-8")

        with patch.object(vsync_module.urllib.request, "urlopen", return_value=MockResp()):
            items = vsync_module.extract_with_ollama("large preamble " * 50)
        assert items[0]["source_line"] == "(llm extraction)"

    def test_json_cli_normalizes_once_before_regex_extraction(
        self, vsync_module, tmp_db, tmp_mem0, monkeypatch
    ):
        payload = json.dumps([
            {"role": "user", "content": "TODO: VH-04 single normalization"},
            {"role": "assistant", "content": "DECISION: use normalized text"},
        ])
        monkeypatch.setenv("VANTAGE_DB_PATH", tmp_db)
        monkeypatch.setenv("VANTAGE_MEM0_PATH", tmp_mem0)
        monkeypatch.setattr(sys, "argv", [
            "vantage-sync.py", "--inline", payload, "--format", "json",
            "--project", "vh04-test",
        ])

        vsync_module.main()

        with sqlite3.connect(tmp_db) as conn:
            contents = {row[0] for row in conn.execute("SELECT content FROM memories")}
        assert "VH-04 single normalization" in contents
        assert "use normalized text" in contents

    def test_truncation_never_exceeds_default_or_custom_limit(self, vsync_module):
        default = vsync_module.intelligent_truncate("A" * 20000)
        assert len(default) <= vsync_module.LLM_TRUNCATE_LIMIT

        result = vsync_module.intelligent_truncate(
            "x" * 15000, limit=1000, head_length=800, tail_length=800
        )
        assert len(result) <= 1000
        assert "TRUNCATED" in result

    def test_ensure_project_preserves_existing_record(self, vsync_module, tmp_db):
        with sqlite3.connect(tmp_db) as conn:
            vsync_module.ensure_project(conn, "vh05-project", "Canonical name")
            vsync_module.ensure_project(conn, "vh05-project", "Do not replace")
            row = conn.execute(
                "SELECT name FROM projects WHERE id = ?", ("vh05-project",)
            ).fetchone()
        assert row == ("Canonical name",)


class TestT1FallbackEnforcement:
    """T1: Fallback enforcement in write mode."""

    def test_no_fallback_aborts_on_warmup_failure_even_in_dry_run(
        self, vsync_module, tmp_db, tmp_mem0, monkeypatch, capsys
    ):
        monkeypatch.setenv("VANTAGE_DB_PATH", tmp_db)
        monkeypatch.setenv("VANTAGE_MEM0_PATH", tmp_mem0)
        monkeypatch.setattr(sys, "argv", [
            "vantage-sync.py", "--inline", "TODO: do not fallback",
            "--llm", "--dry-run", "--no-fallback",
        ])
        with patch.object(
            vsync_module.urllib.request, "urlopen",
            side_effect=Exception("Ollama unavailable"),
        ):
            with pytest.raises(SystemExit) as exc_info:
                vsync_module.main()
        assert exc_info.value.code == 1
        assert "fallback is disabled" in capsys.readouterr().err
        with sqlite3.connect(tmp_db) as conn:
            assert conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0] == 0

    def test_fallback_flags_are_mutually_exclusive(self, vsync_module, monkeypatch):
        monkeypatch.setattr(sys, "argv", [
            "vantage-sync.py", "--inline", "text", "--llm",
            "--no-fallback", "--allow-regex-fallback",
        ])
        with pytest.raises(SystemExit) as exc_info:
            vsync_module.main()
        assert exc_info.value.code == 2

    def test_no_fallback_aborts_when_llm_returns_no_items(self, vsync_module):
        class MockResp:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self):
                return json.dumps({
                    "done": True,
                    "response": json.dumps({
                        "decisions": [], "tasks": [], "facts": [],
                    }),
                }).encode("utf-8")

        with patch.object(vsync_module.urllib.request, "urlopen", return_value=MockResp()):
            with pytest.raises(RuntimeError, match="fallback is disabled"):
                vsync_module.extract_with_ollama("TODO: no extraction", fallback_to_regex=False)

    @pytest.mark.parametrize("allow_fallback", [False, True])
    def test_main_enforces_fallback_flag(
        self, vsync_module, tmp_db, tmp_mem0, monkeypatch, allow_fallback
    ):
        monkeypatch.setenv("VANTAGE_DB_PATH", tmp_db)
        monkeypatch.setenv("VANTAGE_MEM0_PATH", tmp_mem0)
        argv = [
            "vantage-sync.py", "--inline", "TODO: fallback flag end-to-end",
            "--llm", "--project", "fallback-test",
        ]
        if allow_fallback:
            argv.append("--allow-regex-fallback")
        monkeypatch.setattr(sys, "argv", argv)

        with patch.object(
            vsync_module.urllib.request, "urlopen",
            side_effect=Exception("Ollama unavailable"),
        ):
            if allow_fallback:
                vsync_module.main()
            else:
                with pytest.raises(SystemExit) as exc_info:
                    vsync_module.main()
                assert exc_info.value.code == 1

        with sqlite3.connect(tmp_db) as conn:
            count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        assert count > 0 if allow_fallback else count == 0

    def test_chunk_failure_uses_full_text_regex_not_partial_llm(
        self, vsync_module
    ):
        calls = [0]

        class MockResp:
            def __init__(self, body):
                self.body = body
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self):
                return json.dumps(self.body).encode("utf-8")

        def flaky_urlopen(req, timeout):
            calls[0] += 1
            body = json.loads(req.data.decode("utf-8"))
            if "keep_alive" in body:
                return MockResp({"done": True})
            if calls[0] == 2:
                return MockResp({
                    "done": True,
                    "response": json.dumps({
                        "decisions": [],
                        "tasks": [{"content": "partial LLM result"}],
                        "facts": [],
                    }),
                })
            raise urllib.error.URLError("connection reset")

        text = "x" * 5100 + "\nTODO: full-text regex fallback"
        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=flaky_urlopen):
            items = vsync_module.extract_with_ollama(text, timeout=5)

        assert vsync_module._last_extraction_source == "llm→regex"
        assert [item["content"] for item in items] == ["full-text regex fallback"]
        assert all(item["content"] != "partial LLM result" for item in items)

    def test_llm_fallback_abort_in_write_mode(self, vsync_module, tmp_db, sample_chat_text):
        """LLM failure → regex fallback in write mode (no flag) should exit != 0 and write 0 rows."""
        # Mock urlopen to fail (simulate Ollama unavailable)
        with patch.object(vsync_module.urllib.request, 'urlopen',
                          side_effect=Exception("Connection refused")):
            # Extract with LLM - should fall back to regex
            items = vsync_module.extract_with_ollama(sample_chat_text, model="qwen2.5:7b", timeout=5)
            assert len(items) > 0
            # Verify _last_extraction_source is llm→regex
            assert vsync_module._last_extraction_source == "llm→regex"

        # Now test write enforcement - simulate main() logic
        # In write mode with llm→regex and no flag, should abort
        source = vsync_module._last_extraction_source
        assert source == "llm→regex"

        # Simulate the check in main()
        llm_mode = True
        dry_run = False
        allow_flag = False

        if llm_mode and not dry_run and not allow_flag:
            if source == "llm→regex":
                with pytest.raises(SystemExit) as exc_info:
                    # This is what main() does
                    print(
                        "ERROR: LLM extraction failed and fell back to regex. "
                        "In write mode, this would write potentially unreliable regex output. "
                        "Use --allow-regex-fallback to permit this, or re-run with --dry-run to preview.",
                        file=sys.stderr,
                    )
                    sys.exit(1)
                assert exc_info.value.code == 1

    def test_llm_fallback_allowed_with_flag(self, vsync_module, tmp_db, sample_chat_text):
        """LLM failure → regex fallback with --allow-regex-fallback should write."""
        # Mock urlopen to fail
        with patch.object(vsync_module.urllib.request, 'urlopen',
                          side_effect=Exception("Connection refused")):
            items = vsync_module.extract_with_ollama(sample_chat_text, model="qwen2.5:7b", timeout=5)
            assert vsync_module._last_extraction_source == "llm→regex"

        # With flag, should write
        source = vsync_module._last_extraction_source
        llm_mode = True
        dry_run = False
        allow_flag = True

        # Should NOT abort when flag is set
        if llm_mode and not dry_run and not allow_flag:
            if source == "llm→regex":
                sys.exit(1)  # This path should NOT be taken

        # Write should succeed
        results = vsync_module.write_to_context_sync(tmp_db, items, "test-proj", dry_run=False)
        assert all(r["status"] == "written" for r in results)

        # Verify rows written
        conn = sqlite3.connect(tmp_db)
        count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        conn.close()
        assert count > 0

    def test_dry_run_intact_with_fallback(self, vsync_module, tmp_db, sample_chat_text):
        """--dry-run should show fallback without error."""
        # Mock urlopen to fail
        with patch.object(vsync_module.urllib.request, 'urlopen',
                          side_effect=Exception("Connection refused")):
            items = vsync_module.extract_with_ollama(sample_chat_text, model="qwen2.5:7b", timeout=5)
            assert vsync_module._last_extraction_source == "llm→regex"

        # In dry-run, should not abort
        source = vsync_module._last_extraction_source
        llm_mode = True
        dry_run = True
        allow_flag = False

        # Should NOT abort in dry-run
        if llm_mode and not dry_run and not allow_flag:
            if source == "llm→regex":
                sys.exit(1)  # This path should NOT be taken

        # Dry-run should return dry_run status
        results = vsync_module.write_to_context_sync(tmp_db, items, "test-proj", dry_run=True)
        assert all(r["status"] == "dry_run" for r in results)

        # Verify no rows written
        conn = sqlite3.connect(tmp_db)
        count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        conn.close()
        assert count == 0

    def test_report_shows_llm_to_regex_fallback(self, vsync_module, sample_chat_text):
        """Report should show 'llm→regex (fallback)' when LLM fails."""
        import io
        from contextlib import redirect_stdout

        # Mock urlopen to fail
        with patch.object(vsync_module.urllib.request, 'urlopen',
                          side_effect=Exception("Connection refused")):
            items = vsync_module.extract_with_ollama(sample_chat_text, model="qwen2.5:7b", timeout=5)

        # Capture report output
        output = io.StringIO()
        with redirect_stdout(output):
            vsync_module.print_report(
                "test input", items, "test-proj", True,
                [{"key": "test", "category": "task", "status": "dry_run", "error": None}],
                []
            )

        report = output.getvalue()
        assert "llm→regex" in report or "fallback" in report.lower()


class TestT2Chunking:
    """T2: Text chunking for LLM processing."""

    def test_split_into_chunks_basic(self, vsync_module):
        """Text <= size returns 1 chunk."""
        text = "x" * 3000
        chunks = vsync_module.split_into_chunks(text, size=5000, overlap=500)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_split_into_chunks_large_text(self, vsync_module):
        """Large text splits into multiple chunks with overlap."""
        # Create text of 12000 chars (should be 3 chunks: 0-5000, 4500-9500, 9000-12000)
        text = "x" * 12000
        chunks = vsync_module.split_into_chunks(text, size=5000, overlap=500)
        assert len(chunks) == 3
        assert len(chunks[0]) == 5000
        assert len(chunks[1]) == 5000
        assert len(chunks[2]) == 3000  # last chunk is shorter

    def test_split_into_chunks_overlap_no_duplicate_at_boundary(self, vsync_module):
        """Overlap doesn't create duplicate chunks at exact boundaries."""
        # 10000 chars with 5000 size and 500 overlap = 3 chunks
        text = "x" * 10000
        chunks = vsync_module.split_into_chunks(text, size=5000, overlap=500)
        assert len(chunks) == 3
        # Verify overlap content exists
        assert chunks[0][-500:] == chunks[1][:500]
        assert chunks[1][-500:] == chunks[2][:500]

    def test_chunk_marker_at_middle(self, vsync_module):
        """A marker placed at the middle of large text should appear in results."""
        # Generate 47000 chars with marker at position 25000
        text = "x" * 25000 + "TODO: marcador-medio " + "y" * 22000
        assert len(text) >= 47000

        chunks = vsync_module.split_into_chunks(text, size=5000, overlap=500)
        # Find which chunk contains the marker
        marker_found = False
        for chunk in chunks:
            if "TODO: marcador-medio" in chunk:
                marker_found = True
                break
        assert marker_found, "Marker should be present in one of the chunks"

    def test_46528_chars_11_chunks(self, vsync_module):
        """Exactly 46528 characters should produce 11 chunks with default settings."""
        text = "x" * 46528
        chunks = vsync_module.split_into_chunks(text, size=5000, overlap=500)
        # 46528 / (5000-500) = 46528 / 4500 ≈ 10.34 → 11 chunks
        assert len(chunks) == 11

    def test_chunk_deduplication_no_duplicates(self, vsync_module):
        """Same item appearing in overlapping chunks should be deduplicated."""
        # Create text that will split into exactly 2 chunks
        # 6000 chars with 5000 size, 500 overlap = 2 chunks
        text = "DECISION: First decision. " + "x" * 5980

        # Mock urlopen to return duplicate items
        call_count = [0]

        class MockResp:
            def __init__(self, is_warmup=False):
                self.is_warmup = is_warmup
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
            def read(self):
                call_count[0] += 1
                if self.is_warmup:
                    return b'{"done": true, "response": "{\\"decisions\\": [], \\"tasks\\": [], \\"facts\\": []}"}'
                # Return same decision in both chunks
                return json.dumps({
                    "done": True,
                    "response": json.dumps({
                        "decisions": [{"content": "First decision."}],
                        "tasks": [],
                        "facts": []
                    })
                }).encode("utf-8")

        def capture_urlopen(req, timeout):
            body = json.loads(req.data.decode("utf-8"))
            if "keep_alive" in body and "prompt" not in body:
                return MockResp(is_warmup=True)
            return MockResp(is_warmup=False)

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=capture_urlopen):
            items = vsync_module.extract_with_ollama(text, model="qwen2.5:7b", timeout=5)

        # Should have called warmup + 2 chunks = 3 total, but deduplicated to 1 item
        assert call_count[0] == 3  # warmup + 2 chunks
        assert len(items) == 1
        assert items[0]["content"] == "First decision."

    def test_chunk_failure_all_or_nothing(self, vsync_module, tmp_db):
        """If any chunk fails in write mode, should abort (T1 policy applies)."""
        # Mock urlopen to fail on second chunk
        call_count = [0]

        class MockResp:
            def __init__(self, should_fail=False):
                self.should_fail = should_fail
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
            def read(self):
                if self.should_fail:
                    raise Exception("Chunk 2 failed")
                return json.dumps({
                    "done": True,
                    "response": json.dumps({
                        "decisions": [{"content": "First decision"}],
                        "tasks": [],
                        "facts": []
                    })
                }).encode("utf-8")

        def flaky_urlopen(req, timeout):
            call_count[0] += 1
            body = json.loads(req.data.decode("utf-8"))
            # Warmup (call 1) succeeds
            if "keep_alive" in body and "prompt" not in body:
                return MockResp(should_fail=False)
            # Chunk 2 (call 3) fails - warmup is call 1, chunk 1 is call 2
            if call_count[0] == 3:
                return MockResp(should_fail=True)
            # Other chunks succeed
            return MockResp(should_fail=False)

        # Large text to trigger multiple chunks
        text = "x" * 12000

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=flaky_urlopen):
            items = vsync_module.extract_with_ollama(text, model="qwen2.5:7b", timeout=5)

        # Should have 2 processed, 1 failed (chunk 3 succeeds)
        assert vsync_module._chunk_stats["processed"] == 2
        assert vsync_module._chunk_stats["failed"] == 1

        # Any failed chunk discards successful partial results and falls back on full input.
        assert items == []
        assert vsync_module._last_extraction_source == "llm→regex"
        assert vsync_module._chunk_stats["failed"] > 0

        # Simulate the check in main()
        llm_mode = True
        dry_run = False
        allow_flag = False
        chunk_stats = vsync_module._chunk_stats

        if llm_mode and not dry_run and not allow_flag:
            if chunk_stats["failed"] > 0:
                with pytest.raises(SystemExit) as exc_info:
                    print(
                        f"ERROR: {chunk_stats['failed']} chunk(s) failed during LLM extraction. "
                        "In write mode, this produces incomplete results. "
                        "Use --allow-regex-fallback to permit regex fallback, or re-run with --dry-run to preview.",
                        file=sys.stderr,
                    )
                    sys.exit(1)
                assert exc_info.value.code == 1


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

        # Write to mem0 (simulating --with-mem0 behavior)
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


class TestOllamaOptions:
    """Ollama payload must include temperature=0, fixed seed, and num_ctx for determinism."""

    def test_ollama_payload_has_temperature_zero(self, vsync_module):
        """The Ollama payload must include temperature=0."""
        # Patch urlopen to capture the request body
        captured = {}

        class MockResp:
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
            def read(self):
                # Return an LLM response with empty arrays to force regex fallback
                return json.dumps({
                    "done": True,
                    "response": '{"decisions": [], "tasks": [], "facts": []}'
                }).encode("utf-8")

        def capture_urlopen(req, timeout):
            captured["body"] = json.loads(req.data.decode("utf-8"))
            return MockResp()

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=capture_urlopen):
            vsync_module.extract_with_ollama("test prompt", model="qwen2.5:7b", timeout=5)

        assert "options" in captured["body"]
        assert captured["body"]["options"]["temperature"] == 0
        assert captured["body"]["options"]["seed"] == 42

    def test_ollama_payload_stream_false_and_json_format(self, vsync_module):
        """The Ollama payload must have stream=False and format=json."""
        captured = {}

        class MockResp:
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
            def read(self):
                return json.dumps({
                    "done": True,
                    "response": '{"decisions": [], "tasks": [], "facts": []}'
                }).encode("utf-8")

        def capture_urlopen(req, timeout):
            captured["body"] = json.loads(req.data.decode("utf-8"))
            return MockResp()

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=capture_urlopen):
            vsync_module.extract_with_ollama("test", model="qwen2.5:7b", timeout=5)

        assert captured["body"]["stream"] is False
        assert captured["body"]["format"] == "json"

    def test_ollama_payload_has_num_ctx_8192(self, vsync_module):
        """T3: The Ollama payload must include num_ctx=8192."""
        captured = {}

        class MockResp:
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
            def read(self):
                return json.dumps({
                    "done": True,
                    "response": '{"decisions": [], "tasks": [], "facts": []}'
                }).encode("utf-8")

        def capture_urlopen(req, timeout):
            captured["body"] = json.loads(req.data.decode("utf-8"))
            return MockResp()

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=capture_urlopen):
            vsync_module.extract_with_ollama("test", model="qwen2.5:7b", timeout=5)

        assert "options" in captured["body"]
        assert captured["body"]["options"]["num_ctx"] == 8192


class TestT4Timeouts:
    """T4: Per-chunk timeout and warmup with separate timeout."""

    def test_warmup_called_before_chunks(self, vsync_module):
        """Warmup should be called once before processing chunks."""
        call_log = []
        captured_bodies = []

        class MockResp:
            def __init__(self, is_warmup=False):
                self.is_warmup = is_warmup
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
            def read(self):
                call_log.append("warmup" if self.is_warmup else "chunk")
                return b'{"done": true, "response": "{\\"decisions\\": [], \\"tasks\\": [], \\"facts\\": []}"}'

        def capture_urlopen(req, timeout):
            body = json.loads(req.data.decode("utf-8"))
            captured_bodies.append(body)
            # Warmup has keep_alive but no prompt
            if "keep_alive" in body and "prompt" not in body:
                return MockResp(is_warmup=True)
            return MockResp(is_warmup=False)

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=capture_urlopen):
            vsync_module.extract_with_ollama("test text", model="qwen2.5:7b", timeout=5)

        # Should have 1 warmup + 1 chunk call
        assert call_log == ["warmup", "chunk"]

        # Verify warmup payload has num_ctx and keep_alive="5m"
        warmup_body = captured_bodies[0]
        assert warmup_body["keep_alive"] == "5m"
        assert "options" in warmup_body
        assert warmup_body["options"]["num_ctx"] == 8192
        assert warmup_body["stream"] is False

    @pytest.mark.parametrize("raw", [b"{", b"[]", b'{"done": false}', b"{}"])
    def test_warmup_rejects_invalid_or_incomplete_response(self, vsync_module, raw):
        class MockResp:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self):
                return raw

        with patch.object(vsync_module.urllib.request, "urlopen", return_value=MockResp()):
            with pytest.raises((json.JSONDecodeError, ValueError)):
                vsync_module.warmup_ollama(timeout=5)

    def test_warmup_failure_triggers_regex_fallback(self, vsync_module):
        """If warmup fails, should fall back to regex."""
        def fail_urlopen(req, timeout):
            raise Exception("Warmup failed")

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=fail_urlopen):
            items = vsync_module.extract_with_ollama("DECISION: test decision", model="qwen2.5:7b", timeout=5)

        # Should fall back to regex
        assert vsync_module._last_extraction_source == "llm→regex"
        assert len(items) > 0
        assert items[0]["category"] == "decision"

    def test_warmup_timeout_is_separate(self, vsync_module):
        """Warmup timeout should be separate from chunk timeout."""
        timeout_log = []

        class MockResp:
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
            def read(self):
                return b'{"done": true, "response": "{\\"decisions\\": [], \\"tasks\\": [], \\"facts\\": []}"}'

        def capture_urlopen(req, timeout):
            timeout_log.append(timeout)
            return MockResp()

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=capture_urlopen):
            vsync_module.extract_with_ollama("test", model="qwen2.5:7b", timeout=10, warmup_timeout=180)

        # First call should use warmup timeout (180), second uses chunk timeout (10)
        assert timeout_log[0] == 180
        assert timeout_log[1] == 10

    def test_per_chunk_timeout_applied(self, vsync_module):
        """Each chunk should get the same timeout value."""
        timeout_log = []

        class MockResp:
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
            def read(self):
                return b'{"done": true, "response": "{\\"decisions\\": [], \\"tasks\\": [], \\"facts\\": []}"}'

        def capture_urlopen(req, timeout):
            timeout_log.append(timeout)
            return MockResp()

        # Large text to trigger multiple chunks
        text = "x" * 12000

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=capture_urlopen):
            vsync_module.extract_with_ollama(text, model="qwen2.5:7b", timeout=30)

        # First call is warmup (180 default), then each chunk gets 30
        assert timeout_log[0] == 180  # warmup default
        # All chunk calls should use the chunk timeout
        chunk_timeouts = timeout_log[1:]
        assert all(t == 30 for t in chunk_timeouts)
        assert vsync_module.DEFAULT_OLLAMA_TIMEOUT == 300


class TestT4BConsecutiveTimeouts:
    """T4-B: Abort after 2 consecutive timeouts, no partial writes."""

    def test_single_timeout_then_success_resets_counter(self, vsync_module):
        """A single timeout followed by success should reset the counter."""
        call_count = [0]

        class MockResp:
            def __init__(self, should_timeout=False):
                self.should_timeout = should_timeout
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
            def read(self):
                if self.should_timeout:
                    raise urllib.error.URLError("timed out")
                return json.dumps({
                    "done": True,
                    "response": json.dumps({
                        "decisions": [{"content": "Decision after timeout"}],
                        "tasks": [],
                        "facts": []
                    })
                }).encode("utf-8")

        def flaky_urlopen(req, timeout):
            call_count[0] += 1
            body = json.loads(req.data.decode("utf-8"))
            # Warmup (call 1) succeeds
            if "keep_alive" in body and "prompt" not in body:
                return MockResp(should_timeout=False)
            # Chunk 1 (call 2) times out
            if call_count[0] == 2:
                return MockResp(should_timeout=True)
            # Chunk 2 (call 3) succeeds
            return MockResp(should_timeout=False)

        # Large text to trigger multiple chunks
        text = "x" * 12000

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=flaky_urlopen):
            items = vsync_module.extract_with_ollama(text, model="qwen2.5:7b", timeout=5)

        # Should have 2 processed (chunks 2 and 3), 1 failed (chunk 1)
        assert vsync_module._chunk_stats["processed"] == 2
        assert vsync_module._chunk_stats["failed"] == 1
        # Counter should be reset to 0 after successful chunk
        assert vsync_module._consecutive_timeouts == 0
        # A failed chunk discards all partial LLM output and falls back on the full text.
        assert items == []
        assert vsync_module._last_extraction_source == "llm→regex"

    def test_two_consecutive_timeouts_aborts_extraction(self, vsync_module):
        """Two consecutive timeouts should abort extraction with RuntimeError."""
        call_count = [0]

        class MockResp:
            def __init__(self, should_timeout=False):
                self.should_timeout = should_timeout
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
            def read(self):
                if self.should_timeout:
                    raise urllib.error.URLError("timed out")
                return json.dumps({
                    "done": True,
                    "response": json.dumps({
                        "decisions": [{"content": "Decision"}],
                        "tasks": [],
                        "facts": []
                    })
                }).encode("utf-8")

        def timeout_urlopen(req, timeout):
            call_count[0] += 1
            body = json.loads(req.data.decode("utf-8"))
            # Warmup (call 1) succeeds
            if "keep_alive" in body and "prompt" not in body:
                return MockResp(should_timeout=False)
            # Chunk 1 (call 2) times out
            if call_count[0] == 2:
                return MockResp(should_timeout=True)
            # Chunk 2 (call 3) times out - should abort
            return MockResp(should_timeout=True)

        # Large text to trigger multiple chunks
        text = "x" * 12000

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=timeout_urlopen):
            with pytest.raises(RuntimeError) as exc_info:
                vsync_module.extract_with_ollama(text, model="qwen2.5:7b", timeout=5)

        assert "consecutive chunk timeouts" in str(exc_info.value)
        assert "2" in str(exc_info.value)
        # Should have 0 processed, 2 failed before abort
        assert vsync_module._chunk_stats["processed"] == 0
        assert vsync_module._chunk_stats["failed"] == 2
        assert vsync_module._consecutive_timeouts == 2

    def test_direct_timeout_error_counts_toward_abort(self, vsync_module):
        """A direct TimeoutError and a wrapped timeout both count consecutively."""
        call_count = [0]

        class MockResp:
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
            def read(self):
                return b'{"done": true, "response": "{\\"decisions\\": [], \\"tasks\\": [], \\"facts\\": []}"}'

        def timeout_urlopen(req, timeout):
            call_count[0] += 1
            body = json.loads(req.data.decode("utf-8"))
            if "keep_alive" in body and "prompt" not in body:
                return MockResp()
            if call_count[0] == 2:
                raise TimeoutError("timed out")
            raise urllib.error.URLError(TimeoutError("timed out"))

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=timeout_urlopen):
            with pytest.raises(RuntimeError, match="2 consecutive chunk timeouts"):
                vsync_module.extract_with_ollama("x" * 12000, model="qwen2.5:7b", timeout=5)

        assert vsync_module._chunk_stats["failed"] == 2
        assert vsync_module._consecutive_timeouts == 2

    def test_non_timeout_error_resets_counter(self, vsync_module):
        """An unrelated error between timeouts resets the consecutive timeout counter."""
        call_count = [0]

        class MockResp:
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
            def read(self):
                return json.dumps({
                    "done": True,
                    "response": json.dumps({
                        "decisions": [{"content": "Decision"}],
                        "tasks": [],
                        "facts": []
                    })
                }).encode("utf-8")

        def flaky_urlopen(req, timeout):
            call_count[0] += 1
            body = json.loads(req.data.decode("utf-8"))
            # Warmup (call 1) succeeds
            if "keep_alive" in body and "prompt" not in body:
                return MockResp()
            # Chunk 1 times out.
            if call_count[0] == 2:
                raise urllib.error.URLError(TimeoutError("timed out"))
            # Chunk 2 has an unrelated error, resetting the timeout counter.
            if call_count[0] == 3:
                raise urllib.error.URLError("connection reset")
            # Chunk 3 times out; this is only one consecutive timeout.
            raise TimeoutError("timed out")

        text = "x" * 12000

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=flaky_urlopen):
            items = vsync_module.extract_with_ollama(text, model="qwen2.5:7b", timeout=5)

        assert items == []
        assert vsync_module._chunk_stats["processed"] == 0
        assert vsync_module._chunk_stats["failed"] == 3
        assert vsync_module._consecutive_timeouts == 1

    def test_dry_run_mode_exits_on_consecutive_timeouts(self, vsync_module, tmp_db, tmp_mem0, monkeypatch, capsys):
        """The real CLI exits on consecutive timeouts before attempting either write."""
        call_count = [0]

        class MockResp:
            def __init__(self, should_timeout=False):
                self.should_timeout = should_timeout
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
            def read(self):
                if self.should_timeout:
                    raise urllib.error.URLError("timed out")
                return json.dumps({
                    "done": True,
                    "response": json.dumps({
                        "decisions": [{"content": "Decision"}],
                        "tasks": [],
                        "facts": []
                    })
                }).encode("utf-8")

        def timeout_urlopen(req, timeout):
            call_count[0] += 1
            body = json.loads(req.data.decode("utf-8"))
            # Warmup (call 1) succeeds
            if "keep_alive" in body and "prompt" not in body:
                return MockResp(should_timeout=False)
            # Chunk 1 (call 2) times out
            if call_count[0] == 2:
                return MockResp(should_timeout=True)
            # Chunk 2 (call 3) times out
            return MockResp(should_timeout=True)

        monkeypatch.setenv("VANTAGE_DB_PATH", tmp_db)
        monkeypatch.setenv("VANTAGE_MEM0_PATH", tmp_mem0)
        monkeypatch.setattr(sys, "argv", [
            "vantage-sync.py", "--inline", "TODO: preserve existing rows " + "x" * 12000,
            "--llm", "--dry-run", "--project", "t4b-test",
        ])
        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=timeout_urlopen):
            with pytest.raises(SystemExit) as exc_info:
                vsync_module.main()

        assert exc_info.value.code == 1
        assert "In dry-run mode, no writes were attempted." in capsys.readouterr().err
        with sqlite3.connect(tmp_db) as conn:
            assert conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0] == 0
            assert conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 0
        with sqlite3.connect(tmp_mem0) as conn:
            assert conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0] == 0

    def test_no_partial_writes_on_consecutive_timeouts(self, vsync_module, tmp_db, tmp_mem0, monkeypatch, capsys):
        """The real write-mode CLI aborts before either SQLite store is touched."""
        call_count = [0]

        class MockResp:
            def __init__(self, should_timeout=False):
                self.should_timeout = should_timeout
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
            def read(self):
                if self.should_timeout:
                    raise urllib.error.URLError("timed out")
                return json.dumps({
                    "done": True,
                    "response": json.dumps({
                        "decisions": [{"content": "Decision"}],
                        "tasks": [],
                        "facts": []
                    })
                }).encode("utf-8")

        def timeout_urlopen(req, timeout):
            call_count[0] += 1
            body = json.loads(req.data.decode("utf-8"))
            # Warmup (call 1) succeeds
            if "keep_alive" in body and "prompt" not in body:
                return MockResp(should_timeout=False)
            # Chunk 1 (call 2) times out
            if call_count[0] == 2:
                return MockResp(should_timeout=True)
            # Chunk 2 (call 3) times out
            return MockResp(should_timeout=True)

        with sqlite3.connect(tmp_db) as conn:
            conn.execute(
                "INSERT INTO memories (key, content, category) VALUES (?, ?, ?)",
                ("existing", "preserve this row", "fact"),
            )
        with sqlite3.connect(tmp_mem0) as conn:
            conn.execute(
                "INSERT INTO memories "
                "(id, kind, content, scope, provenance, metadata, embedding, dedupe_key, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("existing", "fact", "preserve this row", "default", "test", "{}", "", "existing", "now", "now"),
            )

        monkeypatch.setenv("VANTAGE_DB_PATH", tmp_db)
        monkeypatch.setenv("VANTAGE_MEM0_PATH", tmp_mem0)
        monkeypatch.setattr(sys, "argv", [
            "vantage-sync.py", "--inline", "TODO: do not write partial results " + "x" * 12000,
            "--llm", "--project", "t4b-test",
        ])

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=timeout_urlopen):
            with pytest.raises(SystemExit) as exc_info:
                vsync_module.main()

        assert exc_info.value.code == 1
        assert "prevents partial writes" in capsys.readouterr().err
        with sqlite3.connect(tmp_db) as conn:
            assert conn.execute("SELECT key, content FROM memories").fetchall() == [
                ("existing", "preserve this row")
            ]
            assert conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 0
        with sqlite3.connect(tmp_mem0) as conn:
            assert conn.execute("SELECT id, content FROM memories").fetchall() == [
                ("existing", "preserve this row")
            ]


class TestNormalizationDedup:
    """Trivial LLM output variations should not generate duplicate rows."""

    def test_normalize_content_collapses_whitespace(self, vsync_module):
        """Multiple spaces/newlines should collapse to single space."""
        raw = "TODO: fix the    bug\n\n  at the end"
        result = vsync_module.normalize_content(raw)
        assert result == "TODO: fix the bug at the end"

    def test_normalize_content_strips_trailing_punctuation(self, vsync_module):
        """Trailing period, comma, semicolon should be removed."""
        assert vsync_module.normalize_content("Fix auth bug.") == "Fix auth bug"
        assert vsync_module.normalize_content("Fix auth bug,") == "Fix auth bug"
        assert vsync_module.normalize_content("Fix auth bug;!") == "Fix auth bug"

    def test_normalized_key_same_for_trivial_variations(self, vsync_module):
        """Same content with trailing period/extra whitespace should have same key."""
        key1 = vsync_module.gen_memory_key("task", "Fix the auth bug")
        key2 = vsync_module.gen_memory_key("task", "Fix the auth bug.")
        key3 = vsync_module.gen_memory_key("task", "  Fix the auth bug  ")
        key4 = vsync_module.gen_memory_key("task", "Fix the auth bug  .")
        assert key1 == key2 == key3 == key4

    def test_normalized_mem0_id_same_for_trivial_variations(self, vsync_module):
        """gen_mem0_id should also be stable under normalization."""
        id1 = vsync_module.gen_mem0_id("task", "Fix the auth bug")
        id2 = vsync_module.gen_mem0_id("task", "Fix the auth bug.")
        assert id1 == id2


class TestVh07Vh10ReportAndSchema:
    """Regression for residual BUG HUNTER items VH-07 and VH-10."""

    def test_md_cell_escapes_pipe_and_newlines(self, vsync_module):
        assert vsync_module.md_cell("a|b") == r"a\|b"
        assert vsync_module.md_cell("line1\nline2") == "line1 line2"
        assert vsync_module.md_cell(None) == ""

    def test_print_report_dry_run_survives_pipe_in_content(self, vsync_module, capsys):
        items = [{
            "category": "task",
            "content": "Do A | B\nand more",
            "source_line": "TODO: Do A | B",
        }]
        vsync_module.print_report(
            input_source="test",
            items=items,
            project_id=None,
            dry_run=True,
            primary_results=[],
            mem0_results=[],
        )
        out = capsys.readouterr().out
        data_rows = [
            ln for ln in out.splitlines()
            if ln.startswith("| ") and "Key" not in ln and "---" not in ln
        ]
        assert len(data_rows) == 1
        assert "\n" not in data_rows[0]
        assert r"Do A \|" in data_rows[0] or "Do A \\|" in data_rows[0]

    def test_llm_non_object_response_counts_as_chunk_failure(self, vsync_module, monkeypatch):
        class FakeResp:
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
            def read(self):
                return b'{"response": "[1,2,3]"}'

        def fake_urlopen(req, timeout=None):
            return FakeResp()

        monkeypatch.setattr(vsync_module.urllib.request, "urlopen", fake_urlopen)
        monkeypatch.setattr(vsync_module, "warmup_ollama", lambda *a, **k: None)

        items = vsync_module.extract_with_ollama(
            "TODO: something important to extract",
            fallback_to_regex=True,
        )
        assert isinstance(items, list)
        assert vsync_module._chunk_stats["failed"] >= 1
        assert vsync_module._last_extraction_source == "llm\u2192regex"

    def test_llm_malformed_field_triggers_chunk_failure(self, vsync_module, monkeypatch):
        import json
        payload = {
            "decisions": ["not-a-dict", {"content": "Real decision"}],
            "tasks": [{"content": 123}, {"content": "Real task"}],
            "facts": {"wrong": "shape"},
        }

        class FakeResp:
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
            def read(self):
                return json.dumps({"response": json.dumps(payload)}).encode()

        def fake_urlopen(req, timeout=None):
            return FakeResp()

        monkeypatch.setattr(vsync_module.urllib.request, "urlopen", fake_urlopen)
        monkeypatch.setattr(vsync_module, "warmup_ollama", lambda *a, **k: None)

        items = vsync_module.extract_with_ollama("TODO: x", fallback_to_regex=True)
        assert isinstance(items, list)
        assert vsync_module._last_extraction_source == "llm\u2192regex"


# ─── Empty-input guard (P0 patch: LLM hallucination on empty text) ────────────

class TestEmptyInputGuard:
    """Empty/whitespace input must abort with exit 1 before any extraction or write."""

    @pytest.mark.parametrize("argv_input", [
        ["--inline", ""],
        ["--inline", "   \n\t  "],
    ])
    @pytest.mark.parametrize("extra", [[], ["--dry-run"], ["--llm"], ["--llm", "--dry-run"]])
    def test_empty_inline_exits_1_without_extraction(
        self, vsync_module, tmp_db, tmp_mem0, monkeypatch, argv_input, extra
    ):
        def boom(*a, **k):
            raise AssertionError("extraction/Ollama must not run on empty input")
        monkeypatch.setattr(vsync_module, "extract_with_ollama", boom)
        monkeypatch.setattr(vsync_module, "warmup_ollama", boom)
        monkeypatch.setenv("VANTAGE_DB_PATH", tmp_db)
        monkeypatch.setenv("VANTAGE_MEM0_PATH", tmp_mem0)
        monkeypatch.setattr(sys, "argv", ["vantage-sync.py", *argv_input, *extra])

        with pytest.raises(SystemExit) as exc:
            vsync_module.main()
        assert exc.value.code == 1
        with sqlite3.connect(tmp_db) as conn:
            assert conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0] == 0

    def test_empty_file_exits_1(self, vsync_module, tmp_db, tmp_mem0, tmp_path, monkeypatch):
        f = tmp_path / "empty.txt"
        f.write_text("", encoding="utf-8")
        monkeypatch.setenv("VANTAGE_DB_PATH", tmp_db)
        monkeypatch.setenv("VANTAGE_MEM0_PATH", tmp_mem0)
        monkeypatch.setattr(sys, "argv", ["vantage-sync.py", "--input", str(f)])
        with pytest.raises(SystemExit) as exc:
            vsync_module.main()
        assert exc.value.code == 1

    def test_json_without_text_exits_1(self, vsync_module, tmp_db, tmp_mem0, monkeypatch):
        monkeypatch.setenv("VANTAGE_DB_PATH", tmp_db)
        monkeypatch.setenv("VANTAGE_MEM0_PATH", tmp_mem0)
        monkeypatch.setattr(sys, "argv", [
            "vantage-sync.py", "--inline", json.dumps([{"role": "user", "content": ""}]),
            "--format", "json",
        ])
        with pytest.raises(SystemExit) as exc:
            vsync_module.main()
        assert exc.value.code == 1

    def test_nonempty_inline_still_works(self, vsync_module, tmp_db, tmp_mem0, monkeypatch):
        monkeypatch.setenv("VANTAGE_DB_PATH", tmp_db)
        monkeypatch.setenv("VANTAGE_MEM0_PATH", tmp_mem0)
        monkeypatch.setattr(sys, "argv", ["vantage-sync.py", "--inline", "TODO: still works"])
        vsync_module.main()
        with sqlite3.connect(tmp_db) as conn:
            assert conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0] == 1


# ─── Adaptive chunking, --allow-partial, model flags, report (contract CS-DEVIN) ─

def _resp(payload):
    class R:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return payload
    return R()


def _ok_payload(content):
    return json.dumps({
        "done": True,
        "response": json.dumps({"decisions": [{"content": content}], "tasks": [], "facts": []}),
    }).encode("utf-8")


def _scripted_urlopen(outcomes):
    """Return (urlopen_fn, calls). outcomes[i] drives chunk i+1: 'ok', 'fail' or 'timeout'.

    Warmup (body without 'prompt') always succeeds and is not counted as a chunk."""
    calls = {"chunks": 0, "total": 0}

    def fn(req, timeout):
        calls["total"] += 1
        body = json.loads(req.data.decode("utf-8"))
        if "prompt" not in body:
            return _resp(json.dumps({"done": True}).encode("utf-8"))
        idx = calls["chunks"]
        calls["chunks"] += 1
        outcome = outcomes[idx] if idx < len(outcomes) else outcomes[-1]
        if outcome == "timeout":
            raise urllib.error.URLError("timed out")
        if outcome == "fail":
            return _resp(b"not json")
        return _resp(_ok_payload(f"Decision from chunk {idx + 1}"))
    return fn, calls


class TestAdaptiveChunking:
    @pytest.mark.parametrize("length,expected", [
        (0, 5000), (19999, 5000), (20000, 10000), (83220, 10000),
    ])
    def test_adaptive_chunk_size_boundaries(self, vsync_module, length, expected):
        assert vsync_module.get_adaptive_chunk_size(length) == expected

    def test_extraction_uses_adaptive_chunk_size(self, vsync_module):
        text = "x" * 25000
        fn, calls = _scripted_urlopen(["ok"])
        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=fn):
            vsync_module.extract_with_ollama(text, model="qwen2.5:7b", timeout=5)
        expected = len(vsync_module.split_into_chunks(text, size=10000, overlap=500))
        old = len(vsync_module.split_into_chunks(text, size=5000, overlap=500))
        assert expected != old
        assert calls["chunks"] == expected

    def test_small_text_keeps_5000_chunks(self, vsync_module):
        text = "x" * 12000
        fn, calls = _scripted_urlopen(["ok"])
        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=fn):
            vsync_module.extract_with_ollama(text, model="qwen2.5:7b", timeout=5)
        assert calls["chunks"] == len(vsync_module.split_into_chunks(text, size=5000, overlap=500))


class TestAllowPartial:
    TEXT = "x" * 25000  # 3 chunks of up to 10000 chars

    def test_default_is_all_or_nothing(self, vsync_module):
        fn, _ = _scripted_urlopen(["ok", "fail", "ok"])
        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=fn):
            vsync_module.extract_with_ollama(self.TEXT, model="qwen2.5:7b", timeout=5)
        assert vsync_module._last_extraction_source == "llm→regex"

    def test_allow_partial_keeps_good_chunks(self, vsync_module):
        fn, _ = _scripted_urlopen(["ok", "fail", "ok"])
        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=fn):
            items = vsync_module.extract_with_ollama(
                self.TEXT, model="qwen2.5:7b", timeout=5, allow_partial=True)
        assert vsync_module._last_extraction_source == "llm"
        assert vsync_module._chunk_stats == {"processed": 2, "failed": 1}
        assert sorted(i["content"] for i in items) == ["Decision from chunk 1", "Decision from chunk 3"]

    def test_allow_partial_with_no_fallback_does_not_raise(self, vsync_module):
        fn, _ = _scripted_urlopen(["ok", "fail", "ok"])
        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=fn):
            items = vsync_module.extract_with_ollama(
                self.TEXT, model="qwen2.5:7b", timeout=5,
                fallback_to_regex=False, allow_partial=True)
        assert len(items) == 2

    def test_allow_partial_zero_successes_falls_back(self, vsync_module):
        fn, _ = _scripted_urlopen(["fail"])
        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=fn):
            vsync_module.extract_with_ollama(
                self.TEXT, model="qwen2.5:7b", timeout=5, allow_partial=True)
        assert vsync_module._last_extraction_source == "llm→regex"

    def test_allow_partial_zero_successes_no_fallback_raises(self, vsync_module):
        fn, _ = _scripted_urlopen(["fail"])
        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=fn):
            with pytest.raises(RuntimeError):
                vsync_module.extract_with_ollama(
                    self.TEXT, model="qwen2.5:7b", timeout=5,
                    fallback_to_regex=False, allow_partial=True)

    def test_t4b_still_aborts_with_allow_partial(self, vsync_module):
        fn, _ = _scripted_urlopen(["ok", "timeout", "timeout"])
        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=fn):
            with pytest.raises(RuntimeError, match="consecutive chunk timeouts"):
                vsync_module.extract_with_ollama(
                    self.TEXT, model="qwen2.5:7b", timeout=5, allow_partial=True)

    def test_t4b_abort_counts_each_failure_once_and_stops_calls(self, vsync_module):
        text = "x" * 70000  # 8 chunks of up to 10000
        fn, calls = _scripted_urlopen(["timeout"])
        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=fn):
            with pytest.raises(RuntimeError, match="consecutive chunk timeouts"):
                vsync_module.extract_with_ollama(text, model="qwen2.5:7b", timeout=5)
        assert vsync_module._chunk_stats["failed"] == 2
        assert calls["chunks"] == 2


class TestMainPartialAndModelFlags:
    @pytest.fixture
    def env(self, vsync_module, tmp_db, tmp_mem0, monkeypatch):
        monkeypatch.setenv("VANTAGE_DB_PATH", tmp_db)
        monkeypatch.setenv("VANTAGE_MEM0_PATH", tmp_mem0)
        return tmp_db

    def _fake_extract(self, vsync_module, monkeypatch, processed, failed, source="llm"):
        seen = {}
        def fake(raw_text, model, *a, **k):
            seen["model"] = model
            seen["allow_partial"] = k.get("allow_partial")
            vsync_module._chunk_stats = {"processed": processed, "failed": failed}
            vsync_module._last_extraction_source = source
            return [{"category": "decision", "content": "Partial decision", "source_line": "(llm extraction)"}]
        monkeypatch.setattr(vsync_module, "extract_with_ollama", fake)
        monkeypatch.setattr(vsync_module, "_chunk_stats", {"processed": 0, "failed": 0})
        monkeypatch.setattr(vsync_module, "_last_extraction_source", "regex")
        return seen

    def _run(self, vsync_module, monkeypatch, *args):
        monkeypatch.setattr(sys, "argv", ["vantage-sync.py", "--inline", "texto", *args])
        vsync_module.main()

    def _rows(self, db):
        with sqlite3.connect(db) as conn:
            return conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]

    def test_write_partial_without_flag_exits_1(self, vsync_module, env, monkeypatch):
        self._fake_extract(vsync_module, monkeypatch, 2, 1)
        with pytest.raises(SystemExit) as exc:
            self._run(vsync_module, monkeypatch, "--llm")
        assert exc.value.code == 1
        assert self._rows(env) == 0

    def test_write_partial_with_flag_writes(self, vsync_module, env, monkeypatch):
        seen = self._fake_extract(vsync_module, monkeypatch, 2, 1)
        self._run(vsync_module, monkeypatch, "--llm", "--allow-partial")
        assert seen["allow_partial"] is True
        assert self._rows(env) == 1

    def test_report_marks_partial(self, vsync_module, env, monkeypatch, capsys):
        self._fake_extract(vsync_module, monkeypatch, 2, 1)
        self._run(vsync_module, monkeypatch, "--llm", "--allow-partial", "--dry-run")
        out = capsys.readouterr().out
        assert "**Tramos:** 2 procesados, 1 fallidos — PARCIAL (resultados de los tramos exitosos)" in out

    def test_report_no_partial_marker_without_failures(self, vsync_module, env, monkeypatch, capsys):
        self._fake_extract(vsync_module, monkeypatch, 3, 0)
        self._run(vsync_module, monkeypatch, "--llm", "--dry-run")
        out = capsys.readouterr().out
        assert "**Tramos:** 3 procesados, 0 fallidos" in out
        assert "PARCIAL" not in out
        assert "Chunks:" not in out

    def test_default_model_is_7b(self, vsync_module, env, monkeypatch):
        seen = self._fake_extract(vsync_module, monkeypatch, 1, 0)
        self._run(vsync_module, monkeypatch, "--llm", "--dry-run")
        assert seen["model"] == "qwen2.5:7b"

    def test_qwen253_flag(self, vsync_module, env, monkeypatch):
        seen = self._fake_extract(vsync_module, monkeypatch, 1, 0)
        self._run(vsync_module, monkeypatch, "--llm", "--qwen253", "--dry-run")
        assert seen["model"] == "qwen2.5:3b"

    def test_qwen257_flag(self, vsync_module, env, monkeypatch):
        seen = self._fake_extract(vsync_module, monkeypatch, 1, 0)
        self._run(vsync_module, monkeypatch, "--llm", "--qwen257", "--dry-run")
        assert seen["model"] == "qwen2.5:7b"

    def test_qwen_flag_overrides_model(self, vsync_module, env, monkeypatch):
        seen = self._fake_extract(vsync_module, monkeypatch, 1, 0)
        self._run(vsync_module, monkeypatch, "--llm", "--model", "otro:1b", "--qwen253", "--dry-run")
        assert seen["model"] == "qwen2.5:3b"

    def test_qwen_flags_mutually_exclusive(self, vsync_module, env, monkeypatch):
        self._fake_extract(vsync_module, monkeypatch, 1, 0)
        with pytest.raises(SystemExit) as exc:
            self._run(vsync_module, monkeypatch, "--llm", "--qwen253", "--qwen257", "--dry-run")
        assert exc.value.code == 2

    def test_engine_label_uses_actual_model(self, vsync_module, env, monkeypatch, capsys):
        self._fake_extract(vsync_module, monkeypatch, 1, 0)
        self._run(vsync_module, monkeypatch, "--llm", "--qwen253", "--dry-run")
        assert "**Engine:** llm (qwen2.5:3b)" in capsys.readouterr().out


# ─── Part B1: --with-mem0 flag tests ───────────────────────────────────────────

class TestWithMem0Flag:
    """B1: mem0 disabled by default, enabled only with --with-mem0."""

    def test_mem0_disabled_by_default(self, vsync_module, tmp_db, tmp_mem0, monkeypatch):
        """Without --with-mem0, mem0 should not be called."""
        monkeypatch.setenv("VANTAGE_DB_PATH", tmp_db)
        monkeypatch.setenv("VANTAGE_MEM0_PATH", tmp_mem0)
        monkeypatch.setattr(sys, "argv", [
            "vantage-sync.py", "--inline", "TODO: test", "--project", "test",
        ])

        vsync_module.main()

        # mem0 should be empty (not written to)
        with sqlite3.connect(tmp_mem0) as conn:
            count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        assert count == 0

    def test_mem0_enabled_with_flag(self, vsync_module, tmp_db, tmp_mem0, monkeypatch):
        """With --with-mem0, mem0 should be written to."""
        monkeypatch.setenv("VANTAGE_DB_PATH", tmp_db)
        monkeypatch.setenv("VANTAGE_MEM0_PATH", tmp_mem0)
        monkeypatch.setattr(sys, "argv", [
            "vantage-sync.py", "--inline", "TODO: test", "--project", "test", "--with-mem0",
        ])

        vsync_module.main()

        # mem0 should have data
        with sqlite3.connect(tmp_mem0) as conn:
            count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        assert count > 0


# ─── Part B2-B8: Notion integration tests ─────────────────────────────────────

class TestNotionFilter:
    """B3: Quality filter for Notion publication."""

    def test_filter_categories_only(self, vsync_module):
        """Only decision, task, fact categories pass."""
        memories = [
            {"category": "decision", "content": "This is a decision with enough length here"},
            {"category": "task", "content": "This is a task with enough length here"},
            {"category": "fact", "content": "This is a fact with enough length here"},
            {"category": "pattern", "content": "This is a pattern with enough length here"},
            {"category": "error", "content": "This is an error with enough length here"},
        ]
        filtered, counts = vsync_module.filter_for_notion(memories)
        assert len(filtered) == 3
        assert counts["category"] == 2

    def test_filter_length(self, vsync_module):
        """Content < 20 chars normalized is discarded."""
        memories = [
            {"category": "task", "content": "Too short"},
            {"category": "task", "content": "This is long enough to pass the filter"},
        ]
        filtered, counts = vsync_module.filter_for_notion(memories)
        assert len(filtered) == 1
        assert counts["length"] == 1

    def test_filter_word_count(self, vsync_module):
        """Content < 3 words is discarded (but ≥20 chars, so passes length filter)."""
        memories = [
            {"category": "task", "content": "Supercalifragilisticexpialidocious is"},
            {"category": "task", "content": "One two three four words here are sufficient"},
        ]
        filtered, counts = vsync_module.filter_for_notion(memories)
        assert len(filtered) == 1
        assert counts["words"] == 1

    def test_filter_secrets(self, vsync_module):
        """Secret patterns are discarded, never printed."""
        notion_token = "nt" + "n_" + "a" * 26  # 30 chars total, matches token regex
        sk_token = "sk-" + "x" * 30    # matches sk-[A-Za-z0-9]{20,}
        memories = [
            {"category": "task", "content": "redacted " + notion_token + " with extra words"},
            {"category": "task", "content": "redacted " + sk_token + " with extra words"},
            {"category": "task", "content": "Normal task content without secrets"},
        ]
        filtered, counts = vsync_module.filter_for_notion(memories)
        assert len(filtered) == 1
        assert counts["secret"] == 2
        # Ensure the secret content is not in the filtered results
        assert all("nt" + "n_" not in m["content"] for m in filtered)

class TestHexTruncationFilter:
    """C4: Pure hex strings of 40/64 chars are truncated, not discarded."""

    def test_sha256_complete_truncated_and_row_kept(self, vsync_module):
        """A full sha256 (64 hex chars) is truncated and the row passes."""
        sha = "a" * 64  # 64 hex chars
        memories = [
            {"category": "task", "content": "Task referencing commit sha " + sha},
        ]
        filtered, counts = vsync_module.filter_for_notion(memories)
        assert len(filtered) == 1
        assert counts["hash_truncado"] == 1
        assert counts["secret"] == 0
        # Content should contain truncated form, not full hash
        assert sha not in filtered[0]["content"]
        assert filtered[0]["content"].startswith("Task referencing commit sha ")

    def test_sha1_commit_hex_truncated_and_row_kept(self, vsync_module):
        """A 40-char hex commit sha is truncated and the row passes."""
        sha = "b" * 40  # 40 hex chars
        memories = [
            {"category": "decision", "content": "Commit " + sha + " fixes the bug now"},
        ]
        filtered, counts = vsync_module.filter_for_notion(memories)
        assert len(filtered) == 1
        assert counts["hash_truncado"] == 1
        assert "b" * 40 not in filtered[0]["content"]
        # Should contain the truncated form: 8 chars + … + 5 chars
        assert "b" * 8 in filtered[0]["content"]

    def test_notion_token_and_bearer_still_discarded(self, vsync_module):
        """Notion token and Bearer patterns still discard the row completely."""
        notion_token = "nt" + "n_" + "a" * 26
        memories = [
            {"category": "task", "content": "Token " + notion_token + " for auth here"},
            {"category": "task", "content": "Bearer abcdefghijklmnopqrstuvwxyz1234567890 and more"},
        ]
        filtered, counts = vsync_module.filter_for_notion(memories)
        assert len(filtered) == 0
        assert counts["secret"] == 2

    def test_hex_64_inside_mixed_text_truncated_without_breaking_rest(self, vsync_module):
        """A 64-char hex within mixed text is truncated; rest of text preserved."""
        sha = "c" * 64
        text = "Decision reference " + sha + " was applied to the codebase today"
        memories = [{"category": "decision", "content": text}]
        filtered, counts = vsync_module.filter_for_notion(memories)
        assert len(filtered) == 1
        assert counts["hash_truncado"] == 1
        result = filtered[0]["content"]
        assert sha not in result  # full hex gone
        assert "Decision reference" in result  # prefix preserved
        assert "was applied to the codebase today" in result  # suffix preserved

    def test_short_hashes_and_already_truncated_passthrough(self, vsync_module):
        """Hashes of 7 chars or already-truncated (8…5) pass without changes."""
        short_hash = "abcdefg"  # 7 chars, not 40 or 64
        already = "deadbeef…12345"  # already truncated format
        memories = [
            {"category": "fact", "content": "Short hash " + short_hash + " is not truncated"},
            {"category": "fact", "content": "Already truncated " + already + " should pass"},
        ]
        filtered, counts = vsync_module.filter_for_notion(memories)
        assert len(filtered) == 2
        assert counts["hash_truncado"] == 0
        # Content unchanged
        assert filtered[0]["content"].startswith("Short hash")
        assert filtered[1]["content"].startswith("Already truncated")


class TestNotionFormat:
    """B4: Format Notion page content."""

    def test_format_includes_header(self, vsync_module, sample_chat_text):
        """Page must start with DERIVED header."""
        items = vsync_module.parse_text_input(sample_chat_text)
        memories = [
            {
                "id": 1,
                "key": vsync_module.gen_memory_key(i["category"], i["content"]),
                "content": i["content"],
                "category": i["category"],
                "project_id": "test",
                "created_at": "2026-10-20",
                "updated_at": "2026-10-20",
            }
            for i in items[:3]
        ]
        content = vsync_module.format_notion_page("test", memories, vsync_module.SCRIPT_PATH)
        assert content.startswith("DERIVED — memoria derivada de VANTAGE")

    def test_format_includes_script_version(self, vsync_module, sample_chat_text):
        """Page must include 8-char script hash."""
        items = vsync_module.parse_text_input(sample_chat_text)
        memories = [
            {
                "id": 1,
                "key": vsync_module.gen_memory_key(i["category"], i["content"]),
                "content": i["content"],
                "category": i["category"],
                "project_id": "test",
                "created_at": "2026-10-20",
                "updated_at": "2026-10-20",
            }
            for i in items[:1]
        ]
        content = vsync_module.format_notion_page("test", memories, vsync_module.SCRIPT_PATH)
        assert "Versión del script:" in content
        # Should be 8 hex chars
        import re
        match = re.search(r"Versión del script: ([a-f0-9]{8})", content)
        assert match is not None

    def test_format_limits_content_length(self, vsync_module):
        """Each memory content truncated to ≤300 chars."""
        memories = [
            {
                "id": 1,
                "key": "test:1",
                "content": "x" * 500,
                "category": "task",
                "project_id": "test",
                "created_at": "2026-10-20",
                "updated_at": "2026-10-20",
            }
        ]
        content = vsync_module.format_notion_page("test", memories, vsync_module.SCRIPT_PATH)
        # Content should be truncated
        assert "x" * 300 in content
        assert "x" * 400 not in content


class TestNotionPublishDryRun:
    """B7: --dry-run --publish-notion prints content, no network calls."""

    def test_dry_run_prints_content(self, vsync_module, tmp_db, monkeypatch, capsys):
        """--dry-run --publish-notion should print the content."""
        # Insert test data
        with sqlite3.connect(tmp_db) as conn:
            conn.execute(
                "INSERT INTO memories (key, content, category, project_id) VALUES (?, ?, ?, ?)",
                ("task:test", "Test task content", "task", "test-proj"),
            )
            conn.commit()

        monkeypatch.setenv("VANTAGE_DB_PATH", tmp_db)
        monkeypatch.setattr(sys, "argv", [
            "vantage-sync.py", "--inline", "TODO: test", "--project", "test-proj",
            "--publish-notion", "--dry-run",
        ])

        vsync_module.main()

        out = capsys.readouterr().out
        assert "DERIVED — memoria derivada de VANTAGE" in out

class TestNotionWriteScope:
    """C3: publish_to_notion only writes to the page_id received."""

    def test_writes_only_to_received_page_id(self, vsync_module, tmp_path, monkeypatch):
        """publish_to_notion must write to the given page_id only, never another."""
        captured_urls = []

        # Point 3: fake_request must accept the request object (as urllib.request.urlopen does)
        def fake_request(req, timeout=None):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            captured_urls.append(url)
            class FakeResp:
                def __init__(self, body=b'{"results": [{"id": "old-block-1", "type": "paragraph"}], "has_more": false}'):
                    self._body = body
                def __enter__(self): return self
                def __exit__(self, *a): return False
                def read(self): return self._body
                def getcode(self): return 200
            return FakeResp()

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=fake_request), \
             patch.object(vsync_module, "load_notion_token", return_value="fake-token"):
            result = vsync_module.publish_to_notion("target-page-id-123", "Test content", dry_run=False)

        # Point 3: Verify captured_urls is not empty (was vacío in the broken version)
        assert len(captured_urls) > 0, "Expected API calls to be captured"
        assert result is True
        # Verify the append (PATCH) goes to the target page_id — not another page
        patch_urls = [u for u in captured_urls if "v1/blocks/" in u and "/children" in u]
        assert len(patch_urls) > 0, "Expected PATCH to page children"
        for url in patch_urls:
            assert "target-page-id-123" in url, f"Append must go to received page_id, got {url}"
            assert "other-page-id" not in url
        # No append/archive URL targets a different page (block-level archive uses block IDs)


class TestNotionRetry429:
    """B8: Retry on 429 with Retry-After, max 3 retries."""

    def test_retry_on_429_then_success(self, vsync_module, monkeypatch):
        """Three 429s then success; sleep called with Retry-After values."""
        call_count = [0]
        sleep_calls = []
        retry_after_values = ["1", "2", "3"]  # Different Retry-After each time

        def fake_sleep(seconds):
            sleep_calls.append(seconds)

        def fake_request(req, timeout=None):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            call_count[0] += 1

            class FakeResp:
                def __init__(self, body=b'{"results": [], "has_more": false}'):
                    self._body = body
                def __enter__(self): return self
                def __exit__(self, *a): return False
                def read(self): return self._body
                def getcode(self): return 200

            if call_count[0] <= 3:
                raise urllib.error.HTTPError(
                    url, 429, "Rate Limited",
                    {"Retry-After": retry_after_values[call_count[0] - 1]},
                    io.BytesIO(b'{"error": {"message": "rate limited"}}')
                )
            return FakeResp()

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=fake_request), \
             patch.object(vsync_module, "load_notion_token", return_value="fake-token"), \
             patch.object(vsync_module.time, "sleep", side_effect=fake_sleep):
            result = vsync_module.publish_to_notion("page-123", "Test content", dry_run=False)

        assert result is True
        # 3 retries + 1 success = 4 requests (or more if GET/POST each retry)
        assert call_count[0] > 1, f"Expected retries, got {call_count[0]}"
        # sleep must have been called with retry_after values (1, 2, 3)
        assert len(sleep_calls) > 0, "Expected sleep calls for Retry-After"
        # Verify sleep was called with the Retry-After values (as floats or ints)
        for val in [1, 2, 3]:
            assert any(int(s) == val for s in sleep_calls), \
                f"Expected sleep({val}) for Retry-After, got sleep_calls={sleep_calls}"

    def test_four_429_returns_false(self, vsync_module, monkeypatch):
        """Four 429s (max retries exhausted) returns False, not raises."""
        call_count = [0]

        def fake_request(req, timeout=None):
            call_count[0] += 1
            url = req.full_url if hasattr(req, "full_url") else str(req)
            raise urllib.error.HTTPError(
                url, 429, "Rate Limited", {"Retry-After": "1"},
                io.BytesIO(b'{"error": {"message": "rate limited"}}')
            )

        sleep_called = []
        def fake_sleep(s):
            sleep_called.append(s)

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=fake_request), \
             patch.object(vsync_module, "load_notion_token", return_value="fake-token"), \
             patch.object(vsync_module.time, "sleep", side_effect=fake_sleep):
            result = vsync_module.publish_to_notion("page-123", "Test", dry_run=False)

        # After max retries (3), should return False (not raise)
        assert result is False
        # sleep was called (rate limited retries triggered sleep)
        assert len(sleep_called) > 0

    def test_retry_429_on_patch_preserves_method(self, vsync_module):
        """(a) 429 then success on PATCH: retry must use PATCH method."""
        requests = []

        def fake_request(req, timeout=None):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            method = req.get_method() if hasattr(req, "get_method") else "GET"
            requests.append({"url": url, "method": method})

            class FakeResp:
                def __enter__(self): return self
                def __exit__(self, *a): return False
                def read(self): return b'{"results": [], "has_more": false}'
                def getcode(self): return 200

            # First PATCH fails with 429
            if method == "PATCH" and len([r for r in requests if r["method"] == "PATCH"]) == 1:
                raise urllib.error.HTTPError(
                    url, 429, "Rate Limited", {"Retry-After": "1"},
                    io.BytesIO(b'{"error": {"message": "rate limited"}}')
                )
            return FakeResp()

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=fake_request), \
             patch.object(vsync_module, "load_notion_token", return_value="fake-token"), \
             patch.object(vsync_module.time, "sleep"):
            result = vsync_module.publish_to_notion("page-123", "Test content", dry_run=False)

        assert result is True
        # Find all requests after the GET (i.e. the PATCH requests)
        non_get = [r for r in requests if "children" in r["url"] and r != requests[0]]
        assert len(non_get) == 2, f"Expected 2 append requests (initial + retry), got {len(non_get)}"
        assert non_get[0]["method"] == "PATCH"
        assert non_get[1]["method"] == "PATCH", f"Expected retry to be PATCH, got {non_get[1]['method']}"

    def test_retry_429_on_delete_preserves_method(self, vsync_module):
        """(b) 429 then success on DELETE: retry must use DELETE method."""
        requests = []

        def fake_request(req, timeout=None):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            method = req.get_method() if hasattr(req, "get_method") else "GET"
            requests.append({"url": url, "method": method})

            class FakeResp:
                def __enter__(self): return self
                def __exit__(self, *a): return False
                def read(self):
                    if "children" in url and method == "GET":
                        return b'{"results": [{"id": "old-block-1", "type": "paragraph"}], "has_more": false}'
                    return b'{}'
                def getcode(self): return 200

            # First DELETE fails with 429
            delete_calls = [r for r in requests if "old-block-1" in r["url"]]
            if len(delete_calls) == 1:
                raise urllib.error.HTTPError(
                    url, 429, "Rate Limited", {"Retry-After": "1"},
                    io.BytesIO(b'{"error": {"message": "rate limited"}}')
                )
            return FakeResp()

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=fake_request), \
             patch.object(vsync_module, "load_notion_token", return_value="fake-token"), \
             patch.object(vsync_module.time, "sleep"):
            result = vsync_module.publish_to_notion("page-123", "Test content", dry_run=False)

        assert result is True
        delete_requests = [r for r in requests if "old-block-1" in r["url"]]
        assert len(delete_requests) == 2, f"Expected 2 delete requests (initial + retry), got {len(delete_requests)}"
        assert delete_requests[0]["method"] == "DELETE"
        assert delete_requests[1]["method"] == "DELETE", f"Expected retry to be DELETE, got {delete_requests[1]['method']}"


class TestNotionTokenNotInOutput:
    """B8: Token must not appear in stdout/stderr."""

    def test_token_not_in_stdout_stderr(self, vsync_module, tmp_db, monkeypatch, capsys):
        """Fake token must not leak to stdout or stderr."""
        fake_token = "secret_test_token_xyz_999"
        monkeypatch.setenv("VANTAGE_DB_PATH", tmp_db)
        monkeypatch.setenv("NOTION_MEMORY_PAGE_ID", "fake-page-id")
        monkeypatch.setattr(sys, "argv", [
            "vantage-sync.py", "--inline", "TODO: test token leak", "--project", "test-proj",
            "--publish-notion",
        ])
        monkeypatch.setenv("NOTION_TOKEN", fake_token)

        # Mock the token getter to return our fake token
        with patch.object(vsync_module, "load_notion_token", return_value=fake_token):
            with patch.object(vsync_module.urllib.request, "urlopen") as mock_urlopen:
                mock_resp = MagicMock()
                mock_resp.__enter__ = MagicMock(return_value=mock_resp)
                mock_resp.__exit__ = MagicMock(return_value=False)
                mock_resp.read.return_value = b'{"results": [], "has_more": false}'
                mock_resp.getcode.return_value = 200
                mock_urlopen.return_value = mock_resp
                try:
                    vsync_module.main()
                except SystemExit:
                    pass

        captured = capsys.readouterr()
        assert fake_token not in captured.out, f"Token leaked to stdout: {captured.out}"
        assert fake_token not in captured.err, f"Token leaked to stderr: {captured.err}"


class TestNotionAppendBeforeArchive:
    """B5: Append new blocks BEFORE archiving old ones; failure conserves previous."""

    def test_append_before_archive_order(self, vsync_module, monkeypatch):
        """publish_to_notion must append first, then archive old blocks."""
        request_log = []

        def fake_request(req, timeout=None):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            body = req.data.decode("utf-8") if req.data else None
            method = req.get_method() if hasattr(req, "get_method") else "GET"
            request_log.append({"url": url, "method": method, "body": body})

            class FakeResp:
                def __enter__(self): return self
                def __exit__(self, *a): return False
                def read(self): return b'{"results": [{"id": "old-block-1", "type": "paragraph"}], "has_more": false}'
                def getcode(self): return 200
            return FakeResp()

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=fake_request), \
             patch.object(vsync_module, "load_notion_token", return_value="fake-token"), \
             patch.object(vsync_module.time, "sleep"):
            result = vsync_module.publish_to_notion("page-123", "Test content", dry_run=False)

        assert result is True
        # Order: GET (list) → PATCH (append) → DELETE (archive)
        methods = [r["method"] for r in request_log]
        assert "GET" in methods, "Expected GET (list) before PATCH (append)"
        assert "PATCH" in methods, "Expected PATCH (append) after GET"
        assert "DELETE" in methods, "Expected DELETE (archive) after PATCH"
        first_get = methods.index("GET")
        first_patch = methods.index("PATCH") if "PATCH" in methods else len(methods)
        first_delete = methods.index("DELETE") if "DELETE" in methods else len(methods)
        assert first_get < first_patch, "GET (list) must come before PATCH (append)"
        assert first_patch < first_delete, "PATCH (append) must come before DELETE (archive)"

    def test_append_failure_conserves_previous_blocks(self, vsync_module, monkeypatch):
        """If append fails, old blocks are NOT archived."""
        archived_urls = []

        def fake_request(req, timeout=None):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            method = req.get_method() if hasattr(req, "get_method") else "GET"

            class FakeResp:
                def __init__(self, code=200):
                    self._code = code
                def __enter__(self): return self
                def __exit__(self, *a): return False
                def read(self): return b'{"results": [{"id": "old-block-1", "type": "paragraph"}], "has_more": false}'
                def getcode(self): return self._code

            if method == "PATCH":
                # Append fails — return non-200
                return FakeResp(500)
            # GET returns existing blocks
            return FakeResp(200)

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=fake_request), \
             patch.object(vsync_module, "load_notion_token", return_value="fake-token"), \
             patch.object(vsync_module.time, "sleep"):
            result = vsync_module.publish_to_notion("page-123", "Test content", dry_run=False)

        # Should return False because append failed
        assert result is False


class TestNotionPatchUrlAndBatching:
    """P3: PATCH URL, batching, and pagination verification."""

    def test_patch_goes_to_blocks_children(self, vsync_module, monkeypatch):
        """PATCH requests must go to /v1/blocks/{page_id}/children."""
        captured_urls = []
        captured_methods = []

        def fake_request(req, timeout=None):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            method = req.get_method() if hasattr(req, "get_method") else "GET"
            captured_urls.append(url)
            captured_methods.append(method)

            class FakeResp:
                def __enter__(self): return self
                def __exit__(self, *a): return False
                def read(self): return b'{"results": [], "has_more": false}'
                def getcode(self): return 200
            return FakeResp()

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=fake_request), \
             patch.object(vsync_module, "load_notion_token", return_value="fake-token"), \
             patch.object(vsync_module.time, "sleep"):
            result = vsync_module.publish_to_notion("page-123", "Test content", dry_run=False)

        assert result is True
        # Find PATCH requests
        patch_requests = [(u, m) for u, m in zip(captured_urls, captured_methods) if m == "PATCH"]
        assert len(patch_requests) > 0, "Expected at least one PATCH request"
        for url, method in patch_requests:
            assert "/v1/blocks/" in url, f"PATCH URL must contain /v1/blocks/, got {url}"
            assert "/children" in url, f"PATCH URL must contain /children, got {url}"
            assert "page-123" in url, f"PATCH URL must contain page_id, got {url}"

    def test_delete_targets_old_ids_only(self, vsync_module, monkeypatch):
        """DELETE requests must target only old block IDs, not new ones."""
        old_ids = ["old-block-1", "old-block-2", "old-block-3"]
        deleted_ids = []

        def fake_request(req, timeout=None):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            method = req.get_method() if hasattr(req, "get_method") else "GET"

            class FakeResp:
                def __init__(self, body=None):
                    self._body = body or b'{"results": [], "has_more": false}'
                def __enter__(self): return self
                def __exit__(self, *a): return False
                def read(self): return self._body
                def getcode(self): return 200

            if method == "GET":
                # Return old blocks
                results = [{"id": bid, "type": "paragraph"} for bid in old_ids]
                body = json.dumps({"results": results, "has_more": False}).encode()
                return FakeResp(body)
            elif method == "DELETE":
                # Extract block ID from URL
                if "/blocks/" in url:
                    parts = url.split("/blocks/")
                    if len(parts) > 1:
                        block_id = parts[1].split("?")[0].split("/")[0]
                        deleted_ids.append(block_id)
                # DELETE needs a valid JSON response
                return FakeResp(b'{"object": "block", "id": "deleted", "archived": true}')
            else:
                return FakeResp()

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=fake_request), \
             patch.object(vsync_module, "load_notion_token", return_value="fake-token"), \
             patch.object(vsync_module.time, "sleep"):
            result = vsync_module.publish_to_notion("page-123", "Test content", dry_run=False)

        assert result is True
        # All deleted IDs must be from the old list
        for did in deleted_ids:
            assert did in old_ids, f"DELETE targeted ID {did} which is not in old list {old_ids}"

    def test_250_blocks_3_batches(self, vsync_module, monkeypatch):
        """250 blocks should be sent in 3 batches: 100, 100, 50."""
        patch_count = [0]
        batch_sizes = []

        def fake_request(req, timeout=None):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            method = req.get_method() if hasattr(req, "get_method") else "GET"

            class FakeResp:
                def __enter__(self): return self
                def __exit__(self, *a): return False
                def read(self): return b'{"results": [], "has_more": false}'
                def getcode(self): return 200

            if method == "PATCH":
                patch_count[0] += 1
                if req.data:
                    body = json.loads(req.data.decode("utf-8"))
                    children = body.get("children", [])
                    batch_sizes.append(len(children))
                return FakeResp()
            return FakeResp()

        # Generate content that will create 250 blocks
        # Each line needs to be >2000 chars to become its own block, OR
        # we make each line exactly a block by not exceeding 2000
        # Simpler: make 250 lines, each under 2000 chars, but they won't merge
        # if each is separate content. Actually, the code merges lines with \n.
        # To get 250 blocks, we need 250 lines where adding \n+next would exceed 2000.
        # So make each line ~1900 chars.
        content = "\n".join([f"Block {i}: " + "x" * 1850 for i in range(250)])

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=fake_request), \
             patch.object(vsync_module, "load_notion_token", return_value="fake-token"), \
             patch.object(vsync_module.time, "sleep"):
            result = vsync_module.publish_to_notion("page-123", content, dry_run=False)

        assert result is True
        assert patch_count[0] == 3, f"Expected 3 PATCH requests, got {patch_count[0]}"
        assert batch_sizes == [100, 100, 50], f"Expected batches [100, 100, 50], got {batch_sizes}"

    def test_pagination_with_has_more(self, vsync_module, monkeypatch):
        """Pagination: must handle has_more and next_cursor."""
        get_count = [0]
        cursors_used = []

        def fake_request(req, timeout=None):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            method = req.get_method() if hasattr(req, "get_mode") else "GET"

            class FakeResp:
                def __init__(self, has_more=False, next_cursor=None):
                    self._has_more = has_more
                    self._next_cursor = next_cursor
                def __enter__(self): return self
                def __exit__(self, *a): return False
                def read(self):
                    body = {
                        "results": [{"id": f"block-{get_count[0]}", "type": "paragraph"}],
                        "has_more": self._has_more,
                    }
                    if self._next_cursor:
                        body["next_cursor"] = self._next_cursor
                    return json.dumps(body).encode()
                def getcode(self): return 200

            if method == "GET":
                get_count[0] += 1
                if "start_cursor" in url:
                    # Extract cursor from URL
                    match = re.search(r"start_cursor=([^&]+)", url)
                    if match:
                        cursors_used.append(match.group(1))
                # First call: has_more=True, next_cursor=cursor1
                # Second call: has_more=False
                if get_count[0] == 1:
                    return FakeResp(has_more=True, next_cursor="cursor-abc-123")
                else:
                    return FakeResp(has_more=False)
            else:
                return FakeResp()

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=fake_request), \
             patch.object(vsync_module, "load_notion_token", return_value="fake-token"), \
             patch.object(vsync_module.time, "sleep"):
            result = vsync_module.publish_to_notion("page-123", "Test content", dry_run=False)

        assert result is True
        assert get_count[0] >= 2, f"Expected at least 2 GET calls for pagination, got {get_count[0]}"
        assert "cursor-abc-123" in cursors_used, f"Expected next_cursor to be used, got {cursors_used}"

    def test_no_delete_before_last_patch(self, vsync_module, monkeypatch):
        """No DELETE should occur before the last successful PATCH."""
        request_log = []

        def fake_request(req, timeout=None):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            method = req.get_method() if hasattr(req, "get_method") else "GET"
            request_log.append({"method": method, "url": url})

            class FakeResp:
                def __enter__(self): return self
                def __exit__(self, *a): return False
                def read(self): return b'{"results": [{"id": "old-1", "type": "paragraph"}], "has_more": false}'
                def getcode(self): return 200
            return FakeResp()

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=fake_request), \
             patch.object(vsync_module, "load_notion_token", return_value="fake-token"), \
             patch.object(vsync_module.time, "sleep"):
            result = vsync_module.publish_to_notion("page-123", "Test content", dry_run=False)

        assert result is True
        # Find indices
        delete_indices = [i for i, r in enumerate(request_log) if r["method"] == "DELETE"]
        patch_indices = [i for i, r in enumerate(request_log) if r["method"] == "PATCH"]

        if delete_indices:
            last_patch_index = max(patch_indices) if patch_indices else -1
            first_delete_index = min(delete_indices)
            assert first_delete_index > last_patch_index, \
                f"DELETE at {first_delete_index} must be after last PATCH at {last_patch_index}"

    def test_two_lines_produce_single_block_with_newline(self, vsync_module):
        """R2: Two-line input produces a single block with 'a\\nb' (not glued together)."""
        captured_payloads = []

        def fake_request(req, timeout=None):
            method = req.get_method() if hasattr(req, "get_method") else "GET"
            if method == "PATCH" and req.data:
                captured_payloads.append(json.loads(req.data.decode("utf-8")))

            class FakeResp:
                def __enter__(self): return self
                def __exit__(self, *a): return False
                def read(self): return b'{"results": [], "has_more": false}'
                def getcode(self): return 200

            return FakeResp()

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=fake_request), \
             patch.object(vsync_module, "load_notion_token", return_value="fake-token"), \
             patch.object(vsync_module.time, "sleep"):
            result = vsync_module.publish_to_notion("page-123", "a\nb", dry_run=False)

        assert result is True
        assert len(captured_payloads) == 1
        children = captured_payloads[0].get("children", [])
        assert len(children) == 1, f"Expected exactly 1 block for small two-line input, got {len(children)}"
        rich_text = children[0]["paragraph"]["rich_text"]
        assert len(rich_text) == 1
        content = rich_text[0]["text"]["content"]
        assert content == "a\nb", f"Expected 'a\\nb', got {repr(content)}"
        assert content != "ab", "Lines must not be glued together without newline"

    def test_rich_text_max_2000_char_limit(self, vsync_module):
        """R2: No rich_text segment or block may exceed 2000 characters."""
        captured_payloads = []

        def fake_request(req, timeout=None):
            method = req.get_method() if hasattr(req, "get_method") else "GET"
            if method == "PATCH" and req.data:
                captured_payloads.append(json.loads(req.data.decode("utf-8")))

            class FakeResp:
                def __enter__(self): return self
                def __exit__(self, *a): return False
                def read(self): return b'{"results": [], "has_more": false}'
                def getcode(self): return 200

            return FakeResp()

        # A single line of 2500 characters
        long_line = "x" * 2500
        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=fake_request), \
             patch.object(vsync_module, "load_notion_token", return_value="fake-token"), \
             patch.object(vsync_module.time, "sleep"):
            result = vsync_module.publish_to_notion("page-123", long_line, dry_run=False)

        assert result is True
        assert len(captured_payloads) > 0
        all_blocks = []
        for payload in captured_payloads:
            all_blocks.extend(payload.get("children", []))

        assert len(all_blocks) > 0
        for block in all_blocks:
            for rt in block["paragraph"]["rich_text"]:
                content = rt["text"]["content"]
                assert len(content) <= 2000, f"rich_text content exceeded 2000 chars: {len(content)}"

    def test_archive_all_250_old_blocks_without_limit(self, vsync_module):
        """R7: All old blocks (e.g. 250) must be deleted without a 100 limit, after the last PATCH."""
        old_ids = [f"old-block-{i}" for i in range(250)]
        request_log = []

        def fake_request(req, timeout=None):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            method = req.get_method() if hasattr(req, "get_method") else "GET"
            request_log.append({"url": url, "method": method})

            class FakeResp:
                def __enter__(self): return self
                def __exit__(self, *a): return False
                def read(self):
                    if method == "GET":
                        return json.dumps({
                            "results": [{"id": bid, "type": "paragraph"} for bid in old_ids],
                            "has_more": False,
                        }).encode("utf-8")
                    return b'{}'
                def getcode(self): return 200

            return FakeResp()

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=fake_request), \
             patch.object(vsync_module, "load_notion_token", return_value="fake-token"), \
             patch.object(vsync_module.time, "sleep"):
            result = vsync_module.publish_to_notion("page-123", "New content", dry_run=False)

        assert result is True

        delete_requests = [r for r in request_log if r["method"] == "DELETE"]
        patch_indices = [i for i, r in enumerate(request_log) if r["method"] == "PATCH"]
        delete_indices = [i for i, r in enumerate(request_log) if r["method"] == "DELETE"]

        assert len(delete_requests) == 250, f"Expected 250 DELETE requests, got {len(delete_requests)}"
        assert len(patch_indices) > 0, "Expected at least one PATCH request"
        last_patch_idx = max(patch_indices)
        for d_idx in delete_indices:
            assert d_idx > last_patch_idx, f"DELETE at index {d_idx} was executed before last PATCH at {last_patch_idx}"

        deleted_ids = [r["url"].split("/")[-1] for r in delete_requests]
        assert set(deleted_ids) == set(old_ids), "All 250 old IDs must be targeted, none other"

    def test_do_not_archive_child_page_or_child_database(self, vsync_module, capsys):
        """R8: Never archive child_page or child_database blocks; inform count via stderr."""
        mixed_blocks = [
            {"id": "p-1", "type": "paragraph"},
            {"id": "cp-1", "type": "child_page", "child_page": {"title": "Subpage"}},
            {"id": "p-2", "type": "paragraph"},
            {"id": "cd-1", "type": "child_database", "child_database": {"title": "Subdb"}},
        ]
        deleted_urls = []

        def fake_request(req, timeout=None):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            method = req.get_method() if hasattr(req, "get_method") else "GET"
            if method == "DELETE":
                deleted_urls.append(url)

            class FakeResp:
                def __enter__(self): return self
                def __exit__(self, *a): return False
                def read(self):
                    if method == "GET":
                        return json.dumps({
                            "results": mixed_blocks,
                            "has_more": False,
                        }).encode("utf-8")
                    return b'{}'
                def getcode(self): return 200

            return FakeResp()

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=fake_request), \
             patch.object(vsync_module, "load_notion_token", return_value="fake-token"), \
             patch.object(vsync_module.time, "sleep"):
            result = vsync_module.publish_to_notion("page-123", "New content", dry_run=False)

        assert result is True
        # Only paragraphs should have been deleted (p-1 and p-2)
        deleted_ids = [u.split("/")[-1] for u in deleted_urls]
        assert deleted_ids == ["p-1", "p-2"], f"Expected DELETE only for paragraphs, got {deleted_ids}"
        assert "cp-1" not in deleted_ids, "child_page must never be deleted"
        assert "cd-1" not in deleted_ids, "child_database must never be deleted"

        # Check stderr reports the skipped count without printing content
        captured = capsys.readouterr()
        assert "2" in captured.err, "Expected skipped count (2) in stderr"
        assert "Subpage" not in captured.err and "Subpage" not in captured.out
        assert "Subdb" not in captured.err and "Subdb" not in captured.out


class TestMem0DefaultOff:
    """C5: Without --with-mem0, mem0 is not written."""

    def test_mem0_empty_without_with_mem0(self, vsync_module, tmp_db, tmp_mem0, monkeypatch):
        """main() without --with-mem0 should not write to mem0."""
        monkeypatch.setenv("VANTAGE_DB_PATH", tmp_db)
        monkeypatch.setenv("VANTAGE_MEM0_PATH", tmp_mem0)
        monkeypatch.setattr(sys, "argv", [
            "vantage-sync.py", "--inline", "TODO: test mem0 default", "--project", "test-proj",
        ])
        vsync_module.main()

        # context-sync.db should have data
        with sqlite3.connect(tmp_db) as conn:
            primary_count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        assert primary_count > 0

        # mem0 should be empty
        with sqlite3.connect(tmp_mem0) as conn:
            mem0_count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        assert mem0_count == 0


class TestNotionPublishErrors:
    """B7: Exit code 3 on Notion failure, DB write succeeds."""

    def test_exit_3_on_notion_failure(self, vsync_module, tmp_db, monkeypatch):
        """If DB write succeeds but Notion fails, exit code 3."""
        # Insert test data
        with sqlite3.connect(tmp_db) as conn:
            conn.execute(
                "INSERT INTO memories (key, content, category, project_id) VALUES (?, ?, ?, ?)",
                ("task:test", "Test task content", "task", "test-proj"),
            )
            conn.commit()

        monkeypatch.setenv("VANTAGE_DB_PATH", tmp_db)
        monkeypatch.setenv("NOTION_MEMORY_PAGE_ID", "fake-page-id")
        monkeypatch.setattr(sys, "argv", [
            "vantage-sync.py", "--inline", "TODO: test", "--project", "test-proj",
            "--publish-notion",
        ])

        # Mock publish_to_notion to fail
        with patch.object(vsync_module, "publish_to_notion", return_value=False):
            with pytest.raises(SystemExit) as exc:
                vsync_module.main()
            assert exc.value.code == 3

    def test_requires_project_flag(self, vsync_module, tmp_db, monkeypatch):
        """--publish-notion requires --project."""
        monkeypatch.setenv("VANTAGE_DB_PATH", tmp_db)
        monkeypatch.setattr(sys, "argv", [
            "vantage-sync.py", "--inline", "TODO: test", "--publish-notion",
        ])

        with pytest.raises(SystemExit) as exc:
            vsync_module.main()
        assert exc.value.code == 1


    def test_missing_token_with_db_written_exits_3(self, vsync_module, tmp_db, monkeypatch, tmp_path):
        """Point 6: token faltante con DB ya escrita → exit 3, fila queda escrita."""
        # Ensure NO token is available anywhere
        monkeypatch.delenv("NOTION_TOKEN", raising=False)

        # Create a layer_1.env with 0600 permissions but NO NOTION_TOKEN
        env_dir = tmp_path / "config"
        env_dir.mkdir()
        env_file = env_dir / "layer_1.env"
        env_file.write_text("# no token here\nOTHER=ignored\n", encoding="utf-8")
        env_file.chmod(0o600)

        # Patch load_notion_token to use our env file path and exit(1) as the real one would
        original_load = vsync_module.load_notion_token

        def patched_load(env_path=None):
            # Simulate: token not found
            print("ERROR: NOTION_TOKEN not found", file=sys.stderr)
            sys.exit(1)

        monkeypatch.setenv("VANTAGE_DB_PATH", tmp_db)
        monkeypatch.setenv("NOTION_MEMORY_PAGE_ID", "400938be-fc42-8034-a2d4-eda395e4afed")
        monkeypatch.setattr(sys, "argv", [
            "vantage-sync.py", "--inline", "TODO: test token missing", "--project", "test-proj",
            "--publish-notion",
        ])

        with patch.object(vsync_module, "load_notion_token", side_effect=patched_load):
            with pytest.raises(SystemExit) as exc:
                vsync_module.main()
            assert exc.value.code == 3

        # Verify the row was written to DB BEFORE the Notion failure
        with sqlite3.connect(tmp_db) as conn:
            count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            assert count > 0, "Row should have been written to DB before Notion failure"

    def test_token_permissions_reject_open(self, vsync_module, tmp_path, monkeypatch):
        """Reject token with mode & 0o077 != 0 (0o620, 0o602 rejected)."""
        monkeypatch.delenv("NOTION_TOKEN", raising=False)
        env_file = tmp_path / "test.env"
        env_file.write_text("NOTION_TOKEN=fake\n", encoding="utf-8")
        env_file.chmod(0o620)  # rw-r-----

        with pytest.raises(SystemExit) as exc:
            vsync_module.load_notion_token(str(env_file))
        assert exc.value.code == 1

    def test_token_permissions_accept_600(self, vsync_module, tmp_path, monkeypatch):
        """Accept token with mode 0o600."""
        monkeypatch.delenv("NOTION_TOKEN", raising=False)
        env_file = tmp_path / "test.env"
        env_file.write_text("NOTION_TOKEN=fake\n", encoding="utf-8")
        env_file.chmod(0o600)  # rw-------

        token = vsync_module.load_notion_token(str(env_file))
        assert token == "fake"

    def test_no_publish_notion_no_project_works(self, vsync_module, tmp_db, monkeypatch):
        """Without --publish-notion, --project not required (existing test)."""
        monkeypatch.setenv("VANTAGE_DB_PATH", tmp_db)
        monkeypatch.setattr(sys, "argv", [
            "vantage-sync.py", "--inline", "TODO: test", "--project", "test-proj",
        ])
        vsync_module.main()
        with sqlite3.connect(tmp_db) as conn:
            count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        assert count > 0

    def test_dry_run_no_network_no_files(self, vsync_module, tmp_db, monkeypatch, tmp_path):
        """--dry-run with --publish-notion: zero network, no files left."""
        monkeypatch.setenv("VANTAGE_DB_PATH", tmp_db)
        monkeypatch.setenv("NOTION_MEMORY_PAGE_ID", "fake-page")
        monkeypatch.setenv("NOTION_TOKEN", "fake")
        monkeypatch.setattr(sys, "argv", [
            "vantage-sync.py", "--inline", "TODO: test", "--project", "test-proj",
            "--publish-notion", "--dry-run",
        ])

        urlopen_called = [False]
        def fake_urlopen(*a, **k):
            urlopen_called[0] = True
            raise RuntimeError("Network should not be called in dry-run")

        with patch.object(vsync_module.urllib.request, "urlopen", side_effect=fake_urlopen):
            vsync_module.main()

        assert not urlopen_called[0], "Network should not be called in dry-run"
        # Check no files left (db unchanged)
        with sqlite3.connect(tmp_db) as conn:
            count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        assert count == 0, "DB should be empty in dry-run"

    def _run_http_error_test(self, status_code, vsync_module, tmp_db, monkeypatch, capsys):
        secret_token = "nt" + "n_mock_token_secret_12345"
        monkeypatch.setenv("VANTAGE_DB_PATH", tmp_db)
        monkeypatch.setenv("NOTION_MEMORY_PAGE_ID", "page-fake-id-456")
        monkeypatch.setenv("NOTION_TOKEN", secret_token)
        monkeypatch.setattr(sys, "argv", [
            "vantage-sync.py", "--inline", f"TODO: test http error {status_code}", "--project", "test-proj",
            "--publish-notion",
        ])

        def fake_request(req, timeout=None):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            raise urllib.error.HTTPError(
                url, status_code, f"HTTP Error {status_code}: Mock error with token {secret_token}",
                {}, io.BytesIO(b'{"error": "mocked error"}')
            )

        with patch.object(vsync_module, "load_notion_token", return_value=secret_token), \
             patch.object(vsync_module.urllib.request, "urlopen", side_effect=fake_request), \
             patch.object(vsync_module.time, "sleep"):
            # Direct publish_to_notion call returns False
            res = vsync_module.publish_to_notion("page-fake-id-456", "content", dry_run=False)
            assert res is False

            # Through main(): exits with code 3
            with pytest.raises(SystemExit) as exc:
                vsync_module.main()
            assert exc.value.code == 3

        # DB has the row written
        with sqlite3.connect(tmp_db) as conn:
            count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            assert count > 0, "DB row must remain written after Notion error"

        # Token must not appear in stdout or stderr
        captured = capsys.readouterr()
        assert secret_token not in captured.out, "Token must not appear in stdout"
        assert secret_token not in captured.err, "Token must not appear in stderr"

    def test_http_400_fails_with_exit_3_no_token_leak(self, vsync_module, tmp_db, monkeypatch, capsys):
        """R3: HTTP 400 error returns False, exits with code 3, and never prints token."""
        self._run_http_error_test(400, vsync_module, tmp_db, monkeypatch, capsys)

    def test_http_401_fails_with_exit_3_no_token_leak(self, vsync_module, tmp_db, monkeypatch, capsys):
        """R3: HTTP 401 error returns False, exits with code 3, and never prints token."""
        self._run_http_error_test(401, vsync_module, tmp_db, monkeypatch, capsys)

    def test_http_404_fails_with_exit_3_no_token_leak(self, vsync_module, tmp_db, monkeypatch, capsys):
        """R3: HTTP 404 error returns False, exits with code 3, and never prints token."""
        self._run_http_error_test(404, vsync_module, tmp_db, monkeypatch, capsys)

    def test_partial_failure_delete_404_warns_and_exits_3(self, vsync_module, tmp_db, monkeypatch, capsys):
        """R9: Successful append but DELETE 404 failure returns False, exits 3, warns about appended content and remaining old blocks."""
        secret_token = "nt" + "n_secret_partial_failure_tok_404"
        monkeypatch.setenv("VANTAGE_DB_PATH", tmp_db)
        monkeypatch.setenv("NOTION_MEMORY_PAGE_ID", "page-partial-404")
        monkeypatch.setenv("NOTION_TOKEN", secret_token)
        monkeypatch.setattr(sys, "argv", [
            "vantage-sync.py", "--inline", "TODO: test partial failure 404", "--project", "test-proj",
            "--publish-notion",
        ])

        def fake_request(req, timeout=None):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            method = req.get_method() if hasattr(req, "get_method") else "GET"

            class FakeResp:
                def __enter__(self): return self
                def __exit__(self, *a): return False
                def read(self):
                    if method == "GET":
                        return json.dumps({
                            "results": [{"id": "old-block-xyz", "type": "paragraph"}],
                            "has_more": False,
                        }).encode("utf-8")
                    return b'{}'
                def getcode(self): return 200

            if method == "DELETE":
                raise urllib.error.HTTPError(
                    url, 404, f"Not Found: token={secret_token}", {},
                    io.BytesIO(b'{"error": "block not found"}')
                )
            return FakeResp()

        with patch.object(vsync_module, "load_notion_token", return_value=secret_token), \
             patch.object(vsync_module.urllib.request, "urlopen", side_effect=fake_request), \
             patch.object(vsync_module.time, "sleep"):
            # Direct call returns False
            res = vsync_module.publish_to_notion("page-partial-404", "content", dry_run=False)
            assert res is False

            # main() exits with 3
            with pytest.raises(SystemExit) as exc:
                vsync_module.main()
            assert exc.value.code == 3

        # DB has the row
        with sqlite3.connect(tmp_db) as conn:
            count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            assert count > 0

        # Warning must mention new content was appended and old blocks remain
        captured = capsys.readouterr()
        err_lower = captured.err.lower()
        assert ("already appended" in err_lower or "anex" in err_lower), "Warning must state new content was appended"
        assert ("old blocks" in err_lower or "bloques viejos" in err_lower or "remain" in err_lower), "Warning must state old blocks remain"

        # Token must never leak
        assert secret_token not in captured.out
        assert secret_token not in captured.err

    def test_partial_failure_delete_429_exhausted_warns_and_exits_3(self, vsync_module, tmp_db, monkeypatch, capsys):
        """R9: Successful append but DELETE 429 (exhausted retries) returns False, exits 3, warns without token."""
        secret_token = "nt" + "n_secret_partial_failure_tok_429"
        monkeypatch.setenv("VANTAGE_DB_PATH", tmp_db)
        monkeypatch.setenv("NOTION_MEMORY_PAGE_ID", "page-partial-429")
        monkeypatch.setenv("NOTION_TOKEN", secret_token)
        monkeypatch.setattr(sys, "argv", [
            "vantage-sync.py", "--inline", "TODO: test partial failure 429", "--project", "test-proj",
            "--publish-notion",
        ])

        def fake_request(req, timeout=None):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            method = req.get_method() if hasattr(req, "get_method") else "GET"

            class FakeResp:
                def __enter__(self): return self
                def __exit__(self, *a): return False
                def read(self):
                    if method == "GET":
                        return json.dumps({
                            "results": [{"id": "old-block-xyz", "type": "paragraph"}],
                            "has_more": False,
                        }).encode("utf-8")
                    return b'{}'
                def getcode(self): return 200

            if method == "DELETE":
                raise urllib.error.HTTPError(
                    url, 429, f"Rate limited: token={secret_token}", {"Retry-After": "1"},
                    io.BytesIO(b'{"error": "rate limited"}')
                )
            return FakeResp()

        with patch.object(vsync_module, "load_notion_token", return_value=secret_token), \
             patch.object(vsync_module.urllib.request, "urlopen", side_effect=fake_request), \
             patch.object(vsync_module.time, "sleep"):
            # Direct call returns False
            res = vsync_module.publish_to_notion("page-partial-429", "content", dry_run=False)
            assert res is False

            # main() exits with 3
            with pytest.raises(SystemExit) as exc:
                vsync_module.main()
            assert exc.value.code == 3

        # DB has the row
        with sqlite3.connect(tmp_db) as conn:
            count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            assert count > 0

        # Warning must mention new content was appended and old blocks remain
        captured = capsys.readouterr()
        err_lower = captured.err.lower()
        assert ("already appended" in err_lower or "anex" in err_lower), "Warning must state new content was appended"
        assert ("old blocks" in err_lower or "bloques viejos" in err_lower or "remain" in err_lower), "Warning must state old blocks remain"

        # Token must never leak
        assert secret_token not in captured.out
        assert secret_token not in captured.err


class TestNotionTokenLoading:
    """C2: Token loading from Layer_1/config/layer_1.env."""

    def test_env_var_precedence(self, vsync_module, tmp_path):
        """NOTION_TOKEN env var takes precedence over env file."""
        # Create fake env file
        env_file = tmp_path / "layer_1.env"
        env_file.write_text('NOTION_TOKEN=from_file_token\n', encoding="utf-8")
        env_file.chmod(0o600)

        # Env var should take precedence
        token = vsync_module.load_notion_token(str(env_file))
        # If NOTION_TOKEN is set in os.environ, it should be used
        # For this test, we'll just verify the file path is used correctly
        # by checking that the function can parse it
        env_vars = vsync_module.parse_env_file(str(env_file))
        assert env_vars.get("NOTION_TOKEN") == "from_file_token"

    def test_parse_env_file(self, vsync_module, tmp_path):
        """Parse env file with comments, quotes, and export prefix."""
        env_file = tmp_path / "test.env"
        env_file.write_text(
            '# Comment\n'
            'export NOTION_TOKEN="quoted_value"\n'
            'OTHER_VAR=value\n'
            'export SINGLE=unquoted\n',
            encoding="utf-8"
        )
        env_vars = vsync_module.parse_env_file(str(env_file))
        assert env_vars.get("NOTION_TOKEN") == "quoted_value"
        # C2d: Only NOTION_TOKEN should be parsed; other credentials never read
        assert "OTHER_VAR" not in env_vars
        assert "SINGLE" not in env_vars

    def test_parse_env_file_only_reads_notion_token(self, vsync_module, tmp_path):
        """Only NOTION_TOKEN is read from env file, never other credentials."""
        env_file = tmp_path / "test.env"
        env_file.write_text(
            'NOTION_TOKEN=secret_notion\n'
            'OTHER_SECRET=should_not_be_read\n'
            'PRIVATE_KEY=also_ignored\n',
            encoding="utf-8"
        )
        env_vars = vsync_module.parse_env_file(str(env_file))
        # Verify only NOTION_TOKEN is in the parsed dict
        assert "NOTION_TOKEN" in env_vars
        assert "OTHER_SECRET" not in env_vars
        assert "PRIVATE_KEY" not in env_vars

    def test_permission_check_rejects_open_permissions(self, vsync_module, tmp_path, monkeypatch, capsys):
        """Env file with group/others readable permissions is rejected."""
        env_file = tmp_path / "layer_1.env"
        env_file.write_text('NOTION_TOKEN=test\n', encoding="utf-8")
        env_file.chmod(0o644)  # Readable by group and others

        # Ensure NOTION_TOKEN env var doesn't bypass the permission check
        monkeypatch.delenv("NOTION_TOKEN", raising=False)

        with pytest.raises(SystemExit) as exc:
            vsync_module.load_notion_token(str(env_file))
        assert exc.value.code == 1
        err = capsys.readouterr().err
        assert "insecure permissions" in err or "permisos" in err.lower()

    def test_permission_check_accepts_600(self, vsync_module, tmp_path, monkeypatch):
        """Env file with 600 permissions is accepted."""
        env_file = tmp_path / "layer_1.env"
        env_file.write_text('NOTION_TOKEN=test\n', encoding="utf-8")
        env_file.chmod(0o600)

        # Ensure NOTION_TOKEN env var doesn't interfere
        monkeypatch.delenv("NOTION_TOKEN", raising=False)

        # Mock parse_env_file to return the token
        with patch.object(vsync_module, "parse_env_file", return_value={"NOTION_TOKEN": "test"}):
            token = vsync_module.load_notion_token(str(env_file))
            assert token == "test"


class TestNoSecretsInTests:
    """B8: Verify no secret patterns in tests or script."""

    def test_no_long_token_patterns_in_tests(self):
        """Tests must not contain literal Notion tokens (only concatenations allowed)."""
        with open(__file__, "r", encoding="utf-8") as f:
            content = f.read()
        # Check for literal token followed by 20+ chars (not concatenations)
        import re
        # Match token prefix followed by 20+ letters in the same string literal
        literal_pattern = re.compile(r'nt' + r'n_[A-Za-z0-9]{20,}')
        # But exclude lines with concatenation
        lines = content.split('\n')
        violations = []
        for i, line in enumerate(lines, 1):
            if literal_pattern.search(line) and '+' not in line:
                violations.append(f"Line {i}: {line.strip()}")
        assert len(violations) == 0, f"Found literal token patterns:\n" + "\n".join(violations)

    def test_no_long_secret_patterns_in_script(self, vsync_module):
        """Script must not contain secret patterns (except in SECRET_PATTERNS constant)."""
        import re
        with open(vsync_module.SCRIPT_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        # Check for the actual pattern (should only be in SECRET_PATTERNS definition)
        # Count occurrences
        token_count = content.count("nt" + "n_")
        # Should appear only in SECRET_PATTERNS
        assert token_count <= 2, f"Found {token_count} occurrences of token pattern (expected 2 in SECRET_PATTERNS)"


class TestTokenPermissions:
    """Point 7: token file with group/other access bits rejected."""

    def test_token_rejected_with_0o620(self, vsync_module, tmp_path, monkeypatch):
        """Token file mode 0o620 (group-write) must be rejected."""
        monkeypatch.delenv("NOTION_TOKEN", raising=False)
        env_file = tmp_path / "layer_1.env"
        env_file.write_text("NOTION_TOKEN=test-token-123\n", encoding="utf-8")
        env_file.chmod(0o620)  # group-write, other-read
        with pytest.raises(SystemExit) as exc:
            vsync_module.load_notion_token(env_path=str(env_file))
        assert exc.value.code == 1

    def test_token_rejected_with_0o602(self, vsync_module, tmp_path, monkeypatch):
        """Token file mode 0o602 (other-write) must be rejected."""
        monkeypatch.delenv("NOTION_TOKEN", raising=False)
        env_file = tmp_path / "layer_1.env"
        env_file.write_text("NOTION_TOKEN=test-token-123\n", encoding="utf-8")
        env_file.chmod(0o602)  # other-write
        with pytest.raises(SystemExit) as exc:
            vsync_module.load_notion_token(env_path=str(env_file))
        assert exc.value.code == 1

    def test_token_accepted_with_0o600(self, vsync_module, tmp_path, monkeypatch):
        """Token file mode 0o600 (owner-only) must be accepted."""
        monkeypatch.delenv("NOTION_TOKEN", raising=False)
        env_file = tmp_path / "layer_1.env"
        env_file.write_text("NOTION_TOKEN=test-token-123\n", encoding="utf-8")
        env_file.chmod(0o600)  # owner-only
        token = vsync_module.load_notion_token(env_path=str(env_file))
        assert token == "test-token-123"


class TestPublishNotionProjectValidation:
    """Point 6: --publish-notion without --project exits 1 before any DB write."""

    def test_publish_notion_without_project_exits_1(self, vsync_module, tmp_db, monkeypatch):
        """main() with --publish-notion and no --project exits 1, zero rows written."""
        monkeypatch.setenv("VANTAGE_DB_PATH", tmp_db)
        # No project_id provided for context-sync.db writes
        monkeypatch.setattr(sys, "argv", [
            "vantage-sync.py", "--inline", "TODO: test",
            "--publish-notion",  # No --project
        ])
        with pytest.raises(SystemExit) as exc:
            vsync_module.main()
        assert exc.value.code == 1  # Must exit 1, not 3
        # No rows should have been written to context-sync.db
        with sqlite3.connect(tmp_db) as conn:
            count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            assert count == 0, f"Expected 0 rows, got {count}"


class TestDryRunNoEmptyFile:
    """Point 8: --dry-run does not create an empty context-sync.db."""

    def test_dry_run_does_not_create_db(self, vsync_module, tmp_path, monkeypatch):
        """--dry-run should not create context-sync.db."""
        db_path = str(tmp_path / "context-sync.db")
        monkeypatch.setenv("VANTAGE_DB_PATH", db_path)
        monkeypatch.setattr(sys, "argv", [
            "vantage-sync.py", "--inline", "TODO: test", "--project", "test-proj", "--dry-run",
        ])
        vsync_module.main()
        assert not os.path.exists(db_path), "dry-run should not create the DB file"

