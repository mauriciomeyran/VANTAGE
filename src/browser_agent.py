"""Enhanced browser agent for VANTAGE Scout with Layer_1 integration."""

from __future__ import annotations

import asyncio
import json
import logging
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

logger = logging.getLogger(__name__)

_domain_last_request: defaultdict[str, float] = defaultdict(float)

# Retry is a mitigation for genuinely non-deterministic browser-use watchdog stalls
# (upstream issues #3069, #3196, #2808, #3489). It is NOT a fix for deterministic
# failures — see `summarize_history()` / `preflight_llm()`, which exist to make the
# difference visible instead of retrying the same broken run three times.
MAX_AGENT_RETRIES = 3
RETRY_BACKOFF_SECONDS = 5.0
MIN_VALID_RAW_LENGTH = 150  # below this, treat as a truncated/failed run (see 111-char case)


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


def build_llm(settings: Settings | None = None) -> Any:
    """Instantiate a chat model from LLM_PROVIDER using browser-use native implementations."""
    cfg = settings or get_settings()
    provider = cfg.provider()
    if provider not in SUPPORTED_LLM_PROVIDERS:
        allowed = ", ".join(sorted(SUPPORTED_LLM_PROVIDERS))
        raise ValueError(f"Unsupported LLM_PROVIDER='{cfg.llm_provider}'. Use one of: {allowed}.")

    if provider == "openai":
        if not cfg.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        from browser_use.llm.openai import ChatOpenAI

        model = cfg.openai_model
        if cfg.use_cheap_fallback and cfg.llm_cost_limit < 1.0:
            model = "gpt-4o-mini"
        return ChatOpenAI(
            model=model,
            api_key=cfg.openai_api_key,
            temperature=0,
        )

    if provider == "gemini":
        if not cfg.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
        from browser_use.llm.google import ChatGoogle

        model = cfg.gemini_model
        if cfg.use_cheap_fallback and cfg.llm_cost_limit < 1.0:
            # WARNING: gemini-1.5-flash is discontinued. If this branch ever fires,
            # every agent step will 404 and the run will end with only the initial
            # navigation in history — the exact deterministic failure this module
            # now preflights for. Log loudly rather than swapping models silently.
            model = "gemini-1.5-flash"
            logger.warning(
                "LLM_COST_LIMIT=%s < 1.0 forced a fallback to '%s' instead of the "
                "configured '%s'. That fallback model is discontinued and will fail; "
                "raise LLM_COST_LIMIT or set USE_CHEAP_FALLBACK=false.",
                cfg.llm_cost_limit,
                model,
                cfg.gemini_model,
            )
        return ChatGoogle(
            model=model,
            api_key=cfg.gemini_api_key,
            temperature=0,
        )

    if provider == "anthropic":
        if not cfg.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
        from browser_use.llm.anthropic import ChatAnthropic

        return ChatAnthropic(
            model=cfg.anthropic_model,
            api_key=cfg.anthropic_api_key,
            temperature=0,
        )

    if provider == "ollama":
        from browser_use.llm.ollama import ChatOllama

        return ChatOllama(
            model=cfg.ollama_model,
            base_url=cfg.ollama_base_url,
            temperature=0,
        )

    if provider == "openrouter":
        if not cfg.openrouter_api_key or not cfg.openrouter_api_key.strip():
            raise RuntimeError("OPENROUTER_API_KEY is required when LLM_PROVIDER=openrouter")
        from browser_use.llm.openrouter.chat import ChatOpenRouter

        return ChatOpenRouter(
            model=cfg.openrouter_model,
            api_key=cfg.openrouter_api_key,
            base_url=cfg.openrouter_base_url,
            temperature=0,
        )

    if not cfg.llm_base_url:
        raise RuntimeError("LLM_BASE_URL is required when LLM_PROVIDER=openai_compatible")
    model = cfg.llm_model or cfg.openai_model
    api_key = cfg.llm_api_key or cfg.openai_api_key or "not-needed"
    from browser_use.llm.openai import ChatOpenAI
    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=cfg.llm_base_url,
        temperature=0,
    )


class LLMPreflightError(RuntimeError):
    """The configured LLM rejected a trivial request — no point launching a browser."""


async def preflight_llm(llm: Any) -> None:
    """Send one cheap prompt to prove the model exists and the key works.

    browser-use 0.11.13's `Agent._verify_and_setup_llm()` is a no-op stub, so an
    invalid model name (e.g. a hallucinated `gemini-3.6-flash`) is not caught at
    startup. Instead every reasoning step fails with a 404 and the agent burns
    through max_failures, ending with only the initial navigation in history.
    Failing here converts a silent 5-minute dead end into an instant, clear error.
    """
    from browser_use.llm.messages import UserMessage

    try:
        await llm.ainvoke([UserMessage(content="Reply with the single word: ok")])
    except Exception as exc:  # noqa: BLE001 — re-raised with actionable context
        model = getattr(llm, "model", "<unknown>")
        raise LLMPreflightError(
            f"LLM preflight failed for model '{model}': {exc}. "
            "Verify the model name is currently served by the provider and that the "
            "API key is valid — browser-use does not validate this itself, it just "
            "fails every step until the agent gives up."
        ) from exc


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


async def _run_agent_once(
    task: str,
    cfg: Settings,
    agent_factory: Callable[..., Any] | None,
) -> tuple[Any | None, Exception | None]:
    """Single browser-use Agent run. Returns (history, exception)."""
    browser = None
    try:
        if agent_factory is None:
            from browser_use import Agent, Browser

            llm = build_llm(cfg)
            await preflight_llm(llm)
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
        return history, None
    except Exception as exc:  # noqa: BLE001 — surfaced by caller
        return None, exc
    finally:
        if browser:
            await browser.stop()


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
    """Run browser-use Agent with Layer_1 integration.

    Retries up to MAX_AGENT_RETRIES times on: agent exceptions, truncated/empty
    history (below MIN_VALID_RAW_LENGTH), or unparseable JSON output. This is a
    mitigation for a known browser-use watchdog non-determinism bug (see module
    docstring comment above MAX_AGENT_RETRIES) — not a fix to the underlying issue.
    """
    cfg = settings or get_settings()

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

    payload: PromptAPayload | None = None
    retry_audit: list[AuditLogEntry] = []
    last_failure_audit: AuditLogEntry | None = None
    last_failure_warning: DataQualityWarning | None = None

    for attempt in range(1, MAX_AGENT_RETRIES + 1):
        history, exc = await _run_agent_once(task, cfg, agent_factory)

        if isinstance(exc, LLMPreflightError):
            # Deterministic misconfiguration: retrying cannot help. Fail fast and loudly.
            logger.error("LLM preflight failed; aborting without retries: %s", exc)
            retry_audit.append(
                AuditLogEntry(
                    type="HTTP",
                    source=wrapper_name,
                    message=f"[attempt {attempt}/{MAX_AGENT_RETRIES}] {exc}",
                )
            )
            last_failure_warning = DataQualityWarning(
                code="LLM_PREFLIGHT_FAILED",
                severity="high",
                cause=str(exc),
                impact="Zero items extracted; browser never launched",
                message="LLM rejected a trivial request — check LLM_PROVIDER / model name / API key.",
                origin_wrapper=wrapper_name,
            )
            break

        if exc is not None:
            tag = classify_block(str(exc)) or "HTTP"
            last_failure_audit = AuditLogEntry(
                type=tag,
                source=wrapper_name,
                message=f"[attempt {attempt}/{MAX_AGENT_RETRIES}] {exc}",
            )
            last_failure_warning = DataQualityWarning(
                code="NAVIGATION_BLOCKED",
                severity="high",
                cause=str(exc),
                impact="Zero items extracted",
                message="Insurmountable browser block; no invented data.",
                origin_wrapper=wrapper_name,
            )
            retry_audit.append(last_failure_audit)
            if attempt < MAX_AGENT_RETRIES:
                await asyncio.sleep(RETRY_BACKOFF_SECONDS)
                continue
            break

        raw = _history_to_text(history)
        summary = summarize_history(history)
        diagnostics = _format_history_diagnostics(summary)
        logger.info("Agent attempt %s/%s finished — %s", attempt, MAX_AGENT_RETRIES, diagnostics)

        # No final answer: the agent never called `done`. The step-level errors from
        # browser-use are the actual cause, so record them instead of the old opaque
        # "truncated history" message (which reported the navigation log as if it were output).
        if len(raw.strip()) < MIN_VALID_RAW_LENGTH:
            step_errors = summary.get("errors") or []
            if step_errors:
                cause = f"Agent produced no final result; {len(step_errors)} step error(s). {diagnostics}"
                message = (
                    "Agent never completed the task — every step failed. "
                    "This is a deterministic failure, not a watchdog stall; see errors."
                )
            else:
                cause = f"Agent produced no final result and reported no step errors. {diagnostics}"
                message = (
                    "Agent ended without calling done() and without errors — "
                    "likely a browser-use watchdog stall or exhausted steps."
                )
            last_failure_audit = AuditLogEntry(
                type="Timeout",
                source=wrapper_name,
                message=(
                    f"[attempt {attempt}/{MAX_AGENT_RETRIES}] No final result "
                    f"({len(raw)} chars). {diagnostics}"
                ),
            )
            last_failure_warning = DataQualityWarning(
                code="AGENT_NO_FINAL_RESULT",
                severity="high",
                cause=cause,
                impact="Zero items extracted",
                message=message,
                origin_wrapper=wrapper_name,
            )
            retry_audit.append(last_failure_audit)
            if attempt < MAX_AGENT_RETRIES:
                await asyncio.sleep(RETRY_BACKOFF_SECONDS)
                continue
            break

        block = classify_block(raw)
        if block and _looks_like_failure_only(raw):
            last_failure_audit = AuditLogEntry(
                type=block,
                source=wrapper_name,
                message=f"[attempt {attempt}/{MAX_AGENT_RETRIES}] {raw[:2000]}",
            )
            retry_audit.append(last_failure_audit)
            if attempt < MAX_AGENT_RETRIES:
                await asyncio.sleep(RETRY_BACKOFF_SECONDS)
                continue
            break

        try:
            payload = validate_raw(
                raw,
                prompt_variant=prompt_variant,
                prompt_version=prompt_version,
                today_date=today_date,
                wrapper_name=wrapper_name,
            )
            # Success — stop retrying.
            break
        except Exception as exc:  # noqa: BLE001
            last_failure_audit = AuditLogEntry(
                type="HTTP",
                source=wrapper_name,
                message=f"[attempt {attempt}/{MAX_AGENT_RETRIES}] Unparseable agent output: {exc}",
            )
            last_failure_warning = DataQualityWarning(
                code="INVALID_AGENT_OUTPUT",
                severity="high",
                cause=str(exc),
                impact="Zero items extracted",
                message="Agent did not return valid PromptA JSON; no invented data.",
                origin_wrapper=wrapper_name,
            )
            retry_audit.append(last_failure_audit)
            if attempt < MAX_AGENT_RETRIES:
                await asyncio.sleep(RETRY_BACKOFF_SECONDS)
                continue
            break

    if payload is None:
        # Exhausted all retries without a valid payload.
        return empty_payload(
            prompt_variant=prompt_variant,
            prompt_version=prompt_version,
            today_date=today_date,
            audit=retry_audit or ([last_failure_audit] if last_failure_audit else []),
            warnings=[last_failure_warning] if last_failure_warning else [],
        )

    # Record retry history even on eventual success, for observability.
    if len(retry_audit) > 0:
        payload.audit_log = retry_audit + payload.audit_log

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


def summarize_history(history: Any) -> dict[str, Any]:
    """Extract browser-use's own verdict on the run.

    `final_result()` returns None unless the agent called `done`, so a run where
    every LLM step errored still yields a plausible-looking string once
    `_history_to_text` falls through to `extracted_content()`. That fallback is
    what turned "the model name is invalid, all 7 steps failed" into the opaque
    111-char `['🔗 Navigated to ...']`. This surfaces the real verdict instead.
    """
    summary: dict[str, Any] = {
        "is_done": None,
        "is_successful": None,
        "has_errors": None,
        "errors": [],
        "number_of_steps": None,
        "urls": [],
        "final_result": None,
    }
    if history is None:
        return summary

    def _call(name: str) -> Any:
        getter = getattr(history, name, None)
        if callable(getter):
            try:
                return getter()
            except Exception:  # noqa: BLE001 — diagnostics must never mask the real failure
                return None
        return getter

    summary["is_done"] = _call("is_done")
    summary["is_successful"] = _call("is_successful")
    summary["has_errors"] = _call("has_errors")
    summary["number_of_steps"] = _call("number_of_steps")
    summary["final_result"] = _call("final_result")
    errors = _call("errors")
    if isinstance(errors, list):
        summary["errors"] = [str(e) for e in errors if e]
    urls = _call("urls")
    if isinstance(urls, list):
        summary["urls"] = [str(u) for u in urls if u]
    return summary


def _format_history_diagnostics(summary: dict[str, Any]) -> str:
    """Render a history summary into a compact, log-friendly one-liner."""
    errors = summary.get("errors") or []
    unique_errors: list[str] = []
    for err in errors:
        if err not in unique_errors:
            unique_errors.append(err)
    parts = [
        f"steps={summary.get('number_of_steps')}",
        f"is_done={summary.get('is_done')}",
        f"is_successful={summary.get('is_successful')}",
        f"has_errors={summary.get('has_errors')}",
    ]
    if unique_errors:
        shown = "; ".join(e[:300] for e in unique_errors[:3])
        parts.append(f"errors[{len(errors)}]={shown}")
    else:
        parts.append("errors=none")
    return " | ".join(parts)


def _history_to_text(history: Any) -> str:
    """Return the agent's *final* answer only.

    Deliberately does NOT fall back to `extracted_content()`: that returns the
    running log of every intermediate action (navigations, scrolls), which is not
    a result and cannot be parsed as PromptA JSON. Falling back to it silently
    converts a hard failure into a confusing "truncated history" symptom.
    """
    try:
        if history is None:
            return ""
        if isinstance(history, str):
            return history
        getter = getattr(history, "final_result", None)
        if callable(getter):
            value = getter()
            return str(value) if value else ""
        if isinstance(getter, str):
            return getter
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
