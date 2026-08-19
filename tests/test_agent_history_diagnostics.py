"""Regression tests for the deterministic "truncated history" failure.

Background: a run where every LLM step failed (invalid model name) surfaced only
as `Truncated agent history (111 chars): ['🔗 Navigated to ...']`, with the real
per-step errors discarded. These tests pin the two behaviours that caused it:

1. `_history_to_text` must not fall back to `extracted_content()` — the
   intermediate action log is not a result.
2. `summarize_history` must expose browser-use's own verdict (errors, steps,
   is_done) so a deterministic failure is distinguishable from a watchdog stall.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.browser_agent import (  # noqa: E402
    _format_history_diagnostics,
    _history_to_text,
    run_browser_agent,
    summarize_history,
)

NAV_URL = "https://www.linkedin.com/jobs/search/?keywords=Visual%20Merchandising&location=Mexico%20City"


class FakeResult:
    def __init__(self, extracted_content: str | None = None, error: str | None = None) -> None:
        self.extracted_content = extracted_content
        self.error = error


class FakeStep:
    def __init__(self, results: list[FakeResult]) -> None:
        self.result = results


class FakeHistory:
    """Mimics browser-use AgentHistoryList semantics closely enough to test ours."""

    def __init__(self, steps: list[FakeStep]) -> None:
        self.history = steps

    def final_result(self) -> str | None:
        if self.history and self.history[-1].result[-1].extracted_content:
            return self.history[-1].result[-1].extracted_content
        return None

    def extracted_content(self) -> list[str]:
        out: list[str] = []
        for step in self.history:
            out.extend([r.extracted_content for r in step.result if r.extracted_content])
        return out

    def errors(self) -> list[str | None]:
        out: list[str | None] = []
        for step in self.history:
            errs = [r.error for r in step.result if r.error]
            out.append(errs[0] if errs else None)
        return out

    def has_errors(self) -> bool:
        return any(e is not None for e in self.errors())

    def is_done(self) -> bool:
        return False

    def is_successful(self) -> bool | None:
        return None

    def number_of_steps(self) -> int:
        return len(self.history)

    def urls(self) -> list[str]:
        return [NAV_URL]


def _failed_run_history() -> FakeHistory:
    """Navigation succeeded, then every reasoning step 404'd on the model name."""
    steps = [FakeStep([FakeResult(extracted_content=f"🔗 Navigated to {NAV_URL}")])]
    for _ in range(6):
        steps.append(
            FakeStep([FakeResult(error="Error 404 models/gemini-3.6-flash is not found")])
        )
    return FakeHistory(steps)


def test_the_exact_111_char_symptom_is_reproduced_by_the_old_fallback() -> None:
    """Documents the original bug: extracted_content() looks like a real result."""
    history = _failed_run_history()
    legacy_output = str(history.extracted_content())
    assert len(legacy_output) == 111
    assert legacy_output.startswith("['🔗 Navigated to")


def test_history_to_text_returns_empty_when_agent_never_finished() -> None:
    """No done() call => no result. Must not report the navigation log as output."""
    raw = _history_to_text(_failed_run_history())
    assert raw == ""
    assert "Navigated to" not in raw


def test_history_to_text_returns_the_real_final_result() -> None:
    payload = '{"items": [], "prompt_version": "PromptA-v1.0+linkedin"}'
    history = FakeHistory(
        [
            FakeStep([FakeResult(extracted_content=f"🔗 Navigated to {NAV_URL}")]),
            FakeStep([FakeResult(extracted_content=payload)]),
        ]
    )
    assert _history_to_text(history) == payload


def test_summarize_history_exposes_the_underlying_step_errors() -> None:
    summary = summarize_history(_failed_run_history())
    assert summary["number_of_steps"] == 7
    assert summary["is_done"] is False
    assert summary["has_errors"] is True
    assert len(summary["errors"]) == 6
    assert "404" in summary["errors"][0]
    assert summary["final_result"] is None


def test_summarize_history_tolerates_none_and_partial_objects() -> None:
    assert summarize_history(None)["errors"] == []

    class Partial:
        def number_of_steps(self) -> int:
            return 3

    summary = summarize_history(Partial())
    assert summary["number_of_steps"] == 3
    assert summary["is_done"] is None


def test_diagnostics_string_surfaces_the_root_cause() -> None:
    text = _format_history_diagnostics(summarize_history(_failed_run_history()))
    assert "steps=7" in text
    assert "is_done=False" in text
    assert "404" in text


def test_failed_run_payload_reports_step_errors_not_a_truncation_message() -> None:
    """End-to-end: the audit log must name the real cause, not 'truncated history'."""

    class FakeAgent:
        def __init__(self, **_: Any) -> None:
            pass

        async def run(self, max_steps: int = 0) -> FakeHistory:
            return _failed_run_history()

    payload = asyncio.run(
        run_browser_agent(
            "task " + NAV_URL,
            prompt_variant="A-weekly-unified-linkedin",
            prompt_version="PromptA-v1.0+linkedin",
            today_date="2026-08-19",
            wrapper_name="Prompt_LinkedIn",
            agent_factory=lambda **kw: FakeAgent(**kw),
            enable_layer1_integration=False,
        )
    )

    assert payload.items == []
    combined = " ".join(entry.message for entry in payload.audit_log)
    assert "404" in combined, "root-cause step error must reach the audit log"
    assert "is_done=False" in combined

    codes = {w.code for w in payload.data_quality_warnings}
    assert "AGENT_NO_FINAL_RESULT" in codes
    warning = next(w for w in payload.data_quality_warnings if w.code == "AGENT_NO_FINAL_RESULT")
    assert "deterministic" in warning.message.lower()


def test_preflight_failure_aborts_immediately_without_retrying() -> None:
    """A bad model name is deterministic — burning 3 browser runs on it is waste."""
    from src.browser_agent import LLMPreflightError

    attempts = {"n": 0}

    class ExplodingAgent:
        def __init__(self, **_: Any) -> None:
            attempts["n"] += 1
            raise LLMPreflightError("LLM preflight failed for model 'gemini-3.6-flash': 404")

    payload = asyncio.run(
        run_browser_agent(
            "task " + NAV_URL,
            prompt_variant="A-weekly-unified-linkedin",
            prompt_version="PromptA-v1.0+linkedin",
            today_date="2026-08-19",
            wrapper_name="Prompt_LinkedIn",
            agent_factory=lambda **kw: ExplodingAgent(**kw),
            enable_layer1_integration=False,
        )
    )

    assert attempts["n"] == 1, "preflight failure must not be retried"
    assert {w.code for w in payload.data_quality_warnings} == {"LLM_PREFLIGHT_FAILED"}


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-v"]))


# ---------------------------------------------------------------------------
# Ollama (local) provider wiring
# ---------------------------------------------------------------------------


def test_default_provider_is_local_ollama() -> None:
    """Scout must default to local Ollama, not a paid cloud endpoint."""
    from src.config import Settings

    cfg = Settings(_env_file=None)  # type: ignore[call-arg]
    assert cfg.provider() == "ollama"
    assert cfg.ollama_base_url == "http://127.0.0.1:11434"


def test_build_llm_ollama_uses_real_chatollama_signature() -> None:
    """Regression: ChatOllama takes `host`, not `base_url`, and has no `temperature`.

    The previous call passed base_url= and temperature=, which raises TypeError
    before the browser ever launches.
    """
    pytest.importorskip("browser_use.llm.ollama.chat")
    import dataclasses

    from browser_use.llm.ollama.chat import ChatOllama

    from src.browser_agent import build_llm
    from src.config import Settings

    field_names = {f.name for f in dataclasses.fields(ChatOllama)}
    assert "base_url" not in field_names
    assert "temperature" not in field_names

    llm = build_llm(
        Settings(_env_file=None, llm_provider="ollama", ollama_model="qwen2.5vl:7b")  # type: ignore[call-arg]
    )
    assert isinstance(llm, ChatOllama)
    assert llm.model == "qwen2.5vl:7b"
    assert llm.host == "http://127.0.0.1:11434"
    assert llm.provider == "ollama"


def test_ollama_needs_no_api_key() -> None:
    """Local provider must build with no credentials configured at all."""
    pytest.importorskip("browser_use.llm.ollama.chat")
    from src.browser_agent import build_llm
    from src.config import Settings

    llm = build_llm(
        Settings(  # type: ignore[call-arg]
            _env_file=None,
            llm_provider="ollama",
            gemini_api_key="",
            openai_api_key="",
            anthropic_api_key="",
        )
    )
    assert llm.model


def test_ollama_preflight_error_mentions_server_and_pull() -> None:
    """A local failure should point at `ollama serve` / `ollama pull`, not an API key."""
    from src.browser_agent import LLMPreflightError, preflight_llm

    class DeadOllama:
        model = "qwen2.5vl:7b"
        provider = "ollama"
        host = "http://127.0.0.1:11434"

        async def ainvoke(self, messages: Any) -> Any:
            raise ConnectionError("connection refused")

    with pytest.raises(LLMPreflightError) as excinfo:
        asyncio.run(preflight_llm(DeadOllama()))

    msg = str(excinfo.value)
    assert "ollama serve" in msg
    assert "ollama pull qwen2.5vl:7b" in msg
    assert "API key" not in msg
