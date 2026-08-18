"""Orchestrate browser-use + LLM for VANTAGE Scout Layer 1."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from vantage_scout.src.config import Settings, get_settings
from vantage_scout.src.validator import (
    AuditLogEntry,
    DataQualityWarning,
    PromptAPayload,
    empty_payload,
    validate_raw,
)

JsonDict = dict[str, Any]


def build_llm(settings: Settings | None = None) -> Any:
    """Instantiate Gemini or OpenAI chat model from env."""
    cfg = settings or get_settings()
    provider = cfg.provider()
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        if not cfg.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return ChatOpenAI(
            model=cfg.openai_model,
            api_key=cfg.openai_api_key,
            temperature=0,
        )
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        if not cfg.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
        return ChatGoogleGenerativeAI(
            model=cfg.gemini_model,
            google_api_key=cfg.gemini_api_key,
            temperature=0,
        )
    raise ValueError(f"Unsupported LLM_PROVIDER='{cfg.llm_provider}'. Use gemini or openai.")


def _browser_config(cfg: Settings) -> Any:
    from browser_use import BrowserConfig

    kwargs: dict[str, Any] = {"headless": cfg.browser_headless}
    user_dir = cfg.chrome_user_data_dir.strip()
    if user_dir:
        kwargs["user_data_dir"] = user_dir
    return BrowserConfig(**kwargs)


def classify_block(text: str) -> str | None:
    lower = text.lower()
    if "cloudflare" in lower:
        return "Cloudflare"
    if "captcha" in lower or "403" in lower:
        return "HTTP"
    if "timeout" in lower or "timed out" in lower:
        return "Timeout"
    if "dns" in lower:
        return "DNS"
    return None


async def run_browser_agent(
    task: str,
    *,
    settings: Settings | None = None,
    prompt_variant: str,
    prompt_version: str,
    today_date: str,
    wrapper_name: str,
    agent_factory: Callable[..., Any] | None = None,
) -> PromptAPayload:
    """Run browser-use Agent with vision enabled.

    ``agent_factory`` is injectable for dry-run / unit tests.
    """
    cfg = settings or get_settings()
    if agent_factory is None:
        from browser_use import Agent, Browser

        llm = build_llm(cfg)
        browser = Browser(config=_browser_config(cfg))
        agent = Agent(
            task=task,
            llm=llm,
            browser=browser,
            use_vision=True,
        )
    else:
        agent = agent_factory(task=task, use_vision=True)

    try:
        history = await agent.run(max_steps=cfg.browser_max_steps)
    except Exception as exc:  # noqa: BLE001 — surface as audit, never invent jobs
        tag = classify_block(str(exc)) or "HTTP"
        return empty_payload(
            prompt_variant=prompt_variant,
            prompt_version=prompt_version,
            today_date=today_date,
            audit=[
                AuditLogEntry(
                    type=tag,
                    source=wrapper_name,
                    message=str(exc),
                )
            ],
            warnings=[
                DataQualityWarning(
                    code="NAVIGATION_BLOCKED",
                    severity="high",
                    cause=str(exc),
                    impact="Zero items extracted",
                    message="Insurmountable browser block; no invented data.",
                    origin_wrapper=wrapper_name,
                )
            ],
        )

    raw = _history_to_text(history)
    block = classify_block(raw)
    if block and _looks_like_failure_only(raw):
        return empty_payload(
            prompt_variant=prompt_variant,
            prompt_version=prompt_version,
            today_date=today_date,
            audit=[
                AuditLogEntry(
                    type=block,
                    source=wrapper_name,
                    message=raw[:2000],
                )
            ],
        )
    try:
        return validate_raw(
            raw,
            prompt_variant=prompt_variant,
            prompt_version=prompt_version,
            today_date=today_date,
            wrapper_name=wrapper_name,
        )
    except Exception as exc:  # noqa: BLE001
        return empty_payload(
            prompt_variant=prompt_variant,
            prompt_version=prompt_version,
            today_date=today_date,
            audit=[
                AuditLogEntry(
                    type="HTTP",
                    source=wrapper_name,
                    message=f"Unparseable agent output: {exc}",
                )
            ],
            warnings=[
                DataQualityWarning(
                    code="INVALID_AGENT_OUTPUT",
                    severity="high",
                    cause=str(exc),
                    impact="Zero items extracted",
                    message="Agent did not return valid PromptA JSON; no invented data.",
                    origin_wrapper=wrapper_name,
                )
            ],
        )


def _history_to_text(history: Any) -> str:
    if history is None:
        return ""
    if isinstance(history, str):
        return history
    for attr in ("final_result", "extracted_content"):
        getter = getattr(history, attr, None)
        if callable(getter):
            value = getter()
            if value:
                return str(value)
        elif getter:
            return str(getter)
    if hasattr(history, "model_dump"):
        return json.dumps(history.model_dump(), ensure_ascii=False)
    return str(history)


def _looks_like_failure_only(raw: str) -> bool:
    stripped = raw.strip()
    if stripped.startswith("{"):
        return False
    return True
