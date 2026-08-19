#!/usr/bin/env python3
"""Isolate a SINGLE browser-use agent run and print its real verdict.

Runs one attempt (no retry loop) so failures are attributable, and prints
browser-use's own history accessors instead of the derived text blob.

Usage (from repo root, with the Scout venv active):

    python3 tools/diagnose_agent_run.py --wrapper Prompt_LinkedIn

    # config only, no browser launched:
    python3 tools/diagnose_agent_run.py --wrapper Prompt_LinkedIn --config-only

Unlike `main.py`, this writes everything to stdout and keeps browser-use logging
enabled, so watchdog stalls and per-step LLM errors are visible.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Enable browser-use's own logging BEFORE it is imported anywhere.
os.environ.setdefault("BROWSER_USE_LOGGING_LEVEL", "debug")
logging.basicConfig(
    level=logging.DEBUG,
    stream=sys.stdout,
    format="%(levelname)-8s [%(name)s] %(message)s",
    force=True,
)

from src.browser_agent import (  # noqa: E402
    _history_to_text,
    _run_agent_once,
    build_llm,
    preflight_llm,
    summarize_history,
)
from src.config import get_settings  # noqa: E402
from src.prompt_loader import load_prompt  # noqa: E402


def _rule(title: str) -> None:
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


async def _main(wrapper: str, config_only: bool) -> int:
    rendered, stem, iso = load_prompt(wrapper, today=date.today())
    cfg = get_settings()

    _rule("EFFECTIVE CONFIGURATION")
    print(f"wrapper            : {stem}")
    print(f"today              : {iso}")
    print(f"llm_provider       : {cfg.provider()}")
    print(f"gemini_model       : {cfg.gemini_model}")
    print(f"ollama_model       : {cfg.ollama_model}")
    print(f"browser_max_steps  : {cfg.browser_max_steps}")
    print(f"browser_headless   : {cfg.browser_headless}")
    print(f"use_cheap_fallback : {cfg.use_cheap_fallback}")
    print(f"llm_cost_limit     : {cfg.llm_cost_limit}")
    print(f"chrome_user_data_dir set: {bool(cfg.chrome_user_data_dir.strip())}")
    print(f"prompt length      : {len(rendered)} chars")

    if cfg.browser_max_steps < 5:
        print(f"\n  WARNING: browser_max_steps={cfg.browser_max_steps} is too low to do anything.")

    _rule("LLM PREFLIGHT (does the model actually exist?)")
    try:
        llm = build_llm(cfg)
        print(f"instantiated: {type(llm).__name__} model={getattr(llm, 'model', '?')}")
        await preflight_llm(llm)
        print("preflight    : OK — model responded")
    except Exception as exc:  # noqa: BLE001
        print(f"preflight    : FAILED — {exc}")
        print("\nThis is the root cause. No browser run needed; fix the model/key first.")
        return 1

    if config_only:
        print("\n--config-only set; stopping before browser launch.")
        return 0

    _rule("SINGLE AGENT RUN")
    history, exc = await _run_agent_once(rendered, cfg, None)
    print(f"exception: {exc!r}")

    _rule("HISTORY VERDICT")
    summary = summarize_history(history)
    for key in (
        "is_done",
        "is_successful",
        "has_errors",
        "number_of_steps",
        "final_result",
    ):
        print(f"{key:18}: {summary[key]}")
    print(f"{'urls':18}: {summary['urls']}")

    errors = summary["errors"]
    print(f"\nstep errors ({len(errors)}):")
    for i, err in enumerate(errors, 1):
        print(f"  [{i}] {err}")
    if not errors:
        print("  (none)")

    raw = _history_to_text(history)
    _rule("EXTRACTED FINAL RESULT")
    print(f"length: {len(raw)} chars")
    print(raw[:3000] if raw else "(empty — agent never called done())")

    _rule("INTERPRETATION")
    if summary["is_done"]:
        print("Agent completed. If JSON is malformed, the prompt/schema is the issue.")
    elif errors:
        print("DETERMINISTIC failure: every step errored. Read the step errors above —")
        print("retrying will not help. Common cause: invalid model name (404).")
    else:
        print("Agent stopped without done() and without errors: watchdog stall or")
        print("max_steps exhausted. Compare number_of_steps against browser_max_steps.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wrapper", default="Prompt_LinkedIn")
    parser.add_argument(
        "--config-only",
        action="store_true",
        help="Print config and run LLM preflight, but never launch the browser",
    )
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_main(args.wrapper, args.config_only)))
