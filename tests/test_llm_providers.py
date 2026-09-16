"""LLM provider factory: keys and routing only (no live API calls)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.browser_agent import (  # noqa: E402
    SUPPORTED_LLM_PROVIDERS,
    build_llm,
)
from src.config import Settings  # noqa: E402


def test_supported_set() -> None:
    assert SUPPORTED_LLM_PROVIDERS == {
        "gemini",
        "openai",
        "anthropic",
        "ollama",
        "openrouter",
        "openai_compatible",
        "groq",
    }


def test_unknown_provider() -> None:
    with pytest.raises(ValueError, match="Unsupported LLM_PROVIDER"):
        build_llm(Settings(llm_provider="mistral-direct"))


@pytest.mark.parametrize(
    ("provider", "fragment", "field"),
    [
        ("openai", "OPENAI_API_KEY", "openai_api_key"),
        ("gemini", "GEMINI_API_KEY", "gemini_api_key"),
        ("anthropic", "ANTHROPIC_API_KEY", "anthropic_api_key"),
        ("openai_compatible", "LLM_BASE_URL", "llm_base_url"),
    ],
)
def test_missing_credentials(
    provider: str,
    fragment: str,
    field: str,
) -> None:
    settings = Settings(llm_provider=provider)
    setattr(settings, field, "")
    with pytest.raises(RuntimeError, match=fragment):
        build_llm(settings)


def test_openrouter_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    class FakeChatOpenRouter:
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)

    monkeypatch.setattr(
        "browser_use.llm.openrouter.chat.ChatOpenRouter",
        FakeChatOpenRouter,
    )

    llm = build_llm(
        Settings(
            llm_provider="openrouter",
            openrouter_api_key="sk-or-test",
            openrouter_model="qwen/qwen-2.5-vl-7b-instruct",
        )
    )

    assert isinstance(llm, FakeChatOpenRouter)
    assert captured["base_url"] == "https://openrouter.ai/api/v1"
    assert captured["api_key"] == "sk-or-test"
    assert captured["model"] == "qwen/qwen-2.5-vl-7b-instruct"


def test_openai_compatible_generic(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)

    monkeypatch.setattr(
        "browser_use.llm.openai.chat.ChatOpenAI",
        FakeChatOpenAI,
    )

    llm = build_llm(
        Settings(
            llm_provider="openai_compatible",
            llm_base_url="http://127.0.0.1:1234/v1",
            llm_api_key="lm-studio",
            llm_model="local-vl",
        )
    )

    assert isinstance(llm, FakeChatOpenAI)
    assert captured["base_url"] == "http://127.0.0.1:1234/v1"
    assert captured["model"] == "local-vl"


def test_cost_control_fallback_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that cheap models are used when cost limit is low."""
    captured: dict[str, Any] = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)

    monkeypatch.setattr(
        "browser_use.llm.openai.chat.ChatOpenAI",
        FakeChatOpenAI,
    )

    llm = build_llm(
        Settings(
            llm_provider="openai",
            openai_api_key="sk-test",
            openai_model="gpt-4o",
            llm_cost_limit=0.5,
            use_cheap_fallback=True,
        )
    )
    assert isinstance(llm, FakeChatOpenAI)
    assert captured["model"] == "gpt-4o-mini"

    captured.clear()

    llm = build_llm(
        Settings(
            llm_provider="openai",
            openai_api_key="sk-test",
            openai_model="gpt-4o",
            llm_cost_limit=10.0,
            use_cheap_fallback=True,
        )
    )
    assert isinstance(llm, FakeChatOpenAI)
    assert captured["model"] == "gpt-4o"


def test_cost_control_fallback_gemini(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that cheap models are used when cost limit is low for Gemini."""
    captured: dict[str, Any] = {}

    class FakeChatGoogle:
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)

    monkeypatch.setattr(
        "browser_use.llm.google.ChatGoogle",
        FakeChatGoogle,
    )

    llm = build_llm(
        Settings(
            llm_provider="gemini",
            gemini_api_key="test-key",
            gemini_model="gemini-2.0-flash",
            llm_cost_limit=0.5,
            use_cheap_fallback=True,
        )
    )

    assert isinstance(llm, FakeChatGoogle)
    assert captured["model"] == "gemini-1.5-flash"
