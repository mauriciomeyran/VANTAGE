"""LLM provider factory: keys and routing only (no live API calls)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vantage_scout.src.browser_agent import (  # noqa: E402
    SUPPORTED_LLM_PROVIDERS,
    build_llm,
)
from vantage_scout.src.config import Settings  # noqa: E402


def test_supported_set() -> None:
    assert SUPPORTED_LLM_PROVIDERS == {
        "gemini",
        "openai",
        "anthropic",
        "ollama",
        "openrouter",
        "openai_compatible",
    }


def test_unknown_provider() -> None:
    with pytest.raises(ValueError, match="Unsupported LLM_PROVIDER"):
        build_llm(Settings(llm_provider="mistral-direct"))


@pytest.mark.parametrize(
    ("provider", "fragment"),
    [
        ("openai", "OPENAI_API_KEY"),
        ("gemini", "GEMINI_API_KEY"),
        ("anthropic", "ANTHROPIC_API_KEY"),
        ("openrouter", "OPENROUTER_API_KEY"),
        ("openai_compatible", "LLM_BASE_URL"),
    ],
)
def test_missing_credentials(provider: str, fragment: str) -> None:
    with pytest.raises(RuntimeError, match=fragment):
        build_llm(Settings(llm_provider=provider))


def test_openrouter_uses_openai_compatible_base(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_chat_openai(**kwargs: Any) -> str:
        captured.update(kwargs)
        return "llm"

    monkeypatch.setattr(
        "vantage_scout.src.browser_agent._chat_openai",
        fake_chat_openai,
    )
    llm = build_llm(
        Settings(
            llm_provider="openrouter",
            openrouter_api_key="sk-or-test",
            openrouter_model="qwen/qwen-2.5-vl-7b-instruct",
        )
    )
    assert llm == "llm"
    assert captured["base_url"] == "https://openrouter.ai/api/v1"
    assert captured["api_key"] == "sk-or-test"
    assert captured["model"] == "qwen/qwen-2.5-vl-7b-instruct"


def test_openai_compatible_generic(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_chat_openai(**kwargs: Any) -> str:
        captured.update(kwargs)
        return "compat"

    monkeypatch.setattr(
        "vantage_scout.src.browser_agent._chat_openai",
        fake_chat_openai,
    )
    llm = build_llm(
        Settings(
            llm_provider="openai_compatible",
            llm_base_url="http://127.0.0.1:1234/v1",
            llm_api_key="lm-studio",
            llm_model="local-vl",
        )
    )
    assert llm == "compat"
    assert captured["base_url"] == "http://127.0.0.1:1234/v1"
    assert captured["model"] == "local-vl"
