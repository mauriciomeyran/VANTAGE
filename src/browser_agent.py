"""Enhanced browser agent for VANTAGE Scout with Layer_1 integration."""

from __future__ import annotations

import asyncio
import json
import re
import time
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

from src.config import Settings, get_settings
from src.validator import (
    AuditLogEntry,
    DataQualityWarning,
    PromptAPayload,
    empty_payload,
    validate_raw,
)
from src.dedup import ScoutDedup
from src.gate_logic import ScoutGate
from src.profile_filter import ProfileFilter
from src.url_validator import URLValidator
from src.notion_sync import NotionSync
from src.analytics import ScoutAnalytics

JsonDict = dict[str, Any]

_domain_last_request: defaultdict[str, float] = defaultdict(float)


async def rate_limit_domain(domain: str, min_delay: float = 3.0) -> None:
    """Rate limit requests to specific domain."""
    now = time.time()
    elapsed = now - _domain_last_request[domain]
    if elapsed < min_delay:
        await asyncio.sleep(min_delay - elapsed)
    _domain_last_request[domain] = time.time()


SUPPORTED_LLM_PROVIDERS: frozenset[str] = frozenset(
    {
        "gemini",
        "openai",
        "anthropic",
        "ollama",
        "openrouter",
        "openai_compatible",
    }
)


def _chat_openai(
    *,
    model: str,
    api_key: str,
    base_url: str | None = None,
    provider: str = "openai",
) -> Any:
    from langchain_openai import ChatOpenAI

    kwargs: dict[str, Any] = {
        "model": model,
        "api_key": api_key,
        "temperature": 0,
    }
    if base_url:
        kwargs["base_url"] = base_url
    llm = ChatOpenAI(**kwargs)
    # Add provider and model attributes for browser-use compatibility
    object.__setattr__(llm, 'provider', provider)
    object.__setattr__(llm, 'model', model)
    return llm


def build_llm(settings: Settings | None = None) -> Any:
    """Instantiate a LangChain chat model from LLM_PROVIDER."""
    cfg = settings or get_settings()
    provider = cfg.provider()
    if provider not in SUPPORTED_LLM_PROVIDERS:
        allowed = ", ".join(sorted(SUPPORTED_LLM_PROVIDERS))
        raise ValueError(f"Unsupported LLM_PROVIDER='{cfg.llm_provider}'. Use one of: {allowed}.")

    if provider == "openai":
        if not cfg.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        model = cfg.openai_model
        if cfg.use_cheap_fallback and cfg.llm_cost_limit < 1.0:
            model = "gpt-4o-mini"
        return _chat_openai(model=model, api_key=cfg.openai_api_key, provider="openai")

    if provider == "gemini":
        if not cfg.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
        from browser_use.llm import ChatGoogle

        model = cfg.gemini_model
        if cfg.use_cheap_fallback and cfg.llm_cost_limit < 1.0:
            model = "gemini-1.5-flash"
        llm = ChatGoogle(
            model=model,
            api_key=cfg.gemini_api_key,
            temperature=0,
        )
        return llm

    if provider == "anthropic":
        if not cfg.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
        from langchain_anthropic import ChatAnthropic

        llm = ChatAnthropic(
            model=cfg.anthropic_model,
            api_key=cfg.anthropic_api_key,
            temperature=0,
        )
        object.__setattr__(llm, 'provider', "anthropic")
        object.__setattr__(llm, 'model', cfg.anthropic_model)
        return llm

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        llm = ChatOllama(
            model=cfg.ollama_model,
            base_url=cfg.ollama_base_url,
            temperature=0,
        )
        object.__setattr__(llm, 'provider', "ollama")
        object.__setattr__(llm, 'model', cfg.ollama_model)
        return llm

    if provider == "openrouter":
        if not cfg.openrouter_api_key or not cfg.openrouter_api_key.strip():
            raise RuntimeError("OPENROUTER_API_KEY is required when LLM_PROVIDER=openrouter")
        return _chat_openai(
            model=cfg.openrouter_model,
            api_key=cfg.openrouter_api_key,
            base_url=cfg.openrouter_base_url,
            provider="openrouter",
        )

    if not cfg.llm_base_url:
        raise RuntimeError("LLM_BASE_URL is required when LLM_PROVIDER=openai_compatible")
    model = cfg.llm_model or cfg.openai_model
    api_key = cfg.llm_api_key or cfg.openai_api_key or "not-needed"
    return _chat_openai(model=model, api_key=api_key, base_url=cfg.llm_base_url, provider="openai_compatible")


def _browser_config(cfg: Settings) -> dict[str, Any]:
    """Build browser configuration dict for browser-use v0.13+."""
    kwargs: dict[str, Any] = {
        "headless": cfg.browser_headless,
        "viewport": {"width": 1920, "height": 1080},
    }
    user_dir = cfg.chrome_user_data_dir.strip()
    if user_dir:
        # Real profile in use: let the browser present its native fingerprint.
        # A spoofed user_agent + disable_security on top of real session cookies
        # triggers LinkedIn's anti-hijack re-auth (mismatched UA vs. real Chrome).
        kwargs["user_data_dir"] = user_dir
    else:
        kwargs["user_agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        kwargs["disable_security"] = True
    return kwargs


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
    output_dir: Path | None = None,
    enable_layer1_integration: bool = True,
) -> PromptAPayload:
    """Run browser-use Agent with Layer_1 integration."""
    cfg = settings or get_settings()
    browser = None
    history = None

    # Initialize Layer_1 components if enabled
    dedup = None
    profile_filter = None
    url_validator = None
    notion_sync = None
    analytics = None

    if enable_layer1_integration and output_dir:
        dedup = ScoutDedup(output_dir)
        profile_filter = ProfileFilter()
        url_validator = URLValidator()
        notion_sync = NotionSync()
        analytics = ScoutAnalytics(output_dir)

    # Extract domains from task for rate limiting
    domains = set(re.findall(r'https?://([^\s/]+)', task))
    if domains:
        for domain in domains:
            await rate_limit_domain(domain, cfg.domain_min_delay)

    # Initial delay to avoid rate limiting
    await asyncio.sleep(2)

    try:
        if agent_factory is None:
            from browser_use import Agent, Browser

            llm = build_llm(cfg)
            browser = Browser(**_browser_config(cfg))
            agent = Agent(
                task=task,
                llm=llm,
                browser=browser,
                use_vision=True,
            )
        else:
            agent = agent_factory(task=task, use_vision=True)

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
    finally:
        if browser:
            await browser.stop()

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
        payload = validate_raw(
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

    # Apply Layer_1 integrations if enabled
    if enable_layer1_integration:
        if dedup:
            dedup_stats = dedup.get_duplicate_stats(payload.items)
            payload.items = dedup.filter_duplicates(payload.items)
            payload.audit_log.append(
                AuditLogEntry(
                    type="DEDUP",
                    source=wrapper_name,
                    message=f"Dedup stats: {dedup_stats}"
                )
            )

        if profile_filter:
            gate_stats = ScoutGate.get_gate_stats(payload.items)
            payload.items = ScoutGate.filter_terminal_items(payload.items)
            payload.audit_log.append(
                AuditLogEntry(
                    type="GATE",
                    source=wrapper_name,
                    message=f"Gate stats: {gate_stats}"
                )
            )

            filtered_items, filter_stats = profile_filter.filter_items(payload.items)
            payload.items = filtered_items
            payload.audit_log.append(
                AuditLogEntry(
                    type="PROFILE_FILTER",
                    source=wrapper_name,
                    message=f"Profile filter stats: {filter_stats}"
                )
            )

        if notion_sync and notion_sync.is_available():
            sync_stats = notion_sync.sync_to_notion(payload.model_dump())
            payload.audit_log.append(
                AuditLogEntry(
                    type="NOTION_SYNC",
                    source=wrapper_name,
                    message=f"Notion sync stats: {sync_stats}"
                )
            )

        if analytics:
            analytics_report = analytics.generate_comprehensive_report()
            payload.audit_log.append(
                AuditLogEntry(
                    type="ANALYTICS",
                    source=wrapper_name,
                    message=f"Analytics generated: {len(analytics_report.get('source_effectiveness', {}))} sources analyzed"
                )
            )

    return payload


def _history_to_text(history: Any) -> str:
    try:
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
    except Exception as exc:
        return f"<history_extraction_failed: {exc}>"


def _looks_like_failure_only(raw: str) -> bool:
    stripped = raw.strip()
    if stripped.startswith("{"):
        return False
    return True
