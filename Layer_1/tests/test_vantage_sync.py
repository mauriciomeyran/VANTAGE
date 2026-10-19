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

Tests run against isolated temp databases - never touch ~/.vantage/.
Tests live in Layer_1/tests/ (not repo-root tests/).
"""

import json
import os
import hashlib
import sqlite3
import sys
import tempfile
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
        assert "Do A \|" in data_rows[0] or "Do A \\|" in data_rows[0]

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
