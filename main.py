#!/usr/bin/env python3
"""VANTAGE Scout Layer 1 CLI.

Stdout is exclusively PromptA-v1.0 JSON (no preamble).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import date
from pathlib import Path

# Allow `python vantage_scout/main.py` from repo root.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.config import (  # noqa: E402
    OUTPUT_DIR,
    PROMPT_VARIANT_BY_WRAPPER,
    PROMPT_VERSION_BY_WRAPPER,
    get_settings,
)
from src.prompt_loader import load_prompt  # noqa: E402
from src.validator import PromptAPayload, empty_payload  # noqa: E402

# Suppress all logging to stdout (critical for JSON-only contract)
logging.basicConfig(level=logging.CRITICAL, force=True)


def _meta_for(wrapper_stem: str) -> tuple[str, str]:
    version = PROMPT_VERSION_BY_WRAPPER.get(wrapper_stem, "PromptA-v1.0")
    variant = PROMPT_VARIANT_BY_WRAPPER.get(wrapper_stem, "A-weekly-unified")
    return variant, version


def write_output(payload: PromptAPayload, wrapper_stem: str, today: date) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = today.strftime("%Y%m%d")
    path = OUTPUT_DIR / f"vantage_scout_{wrapper_stem}_{stamp}.json"
    path.write_text(
        json.dumps(payload.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def emit(payload: PromptAPayload) -> None:
    sys.stdout.write(json.dumps(payload.model_dump(mode="json"), ensure_ascii=False, indent=2))
    sys.stdout.write("\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "--wrapper",
        required=True,
        help="Prompt_Career_Sites | Prompt_LinkedIn | Prompt_Aggregators (or aliases)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Inject date, validate empty PromptA envelope, do not launch the browser",
    )
    parser.add_argument(
        "--today",
        default=None,
        help="Override ISO date YYYY-MM-DD (tests)",
    )
    return parser.parse_args(argv)


async def _async_main(args: argparse.Namespace) -> int:
    today = date.fromisoformat(args.today) if args.today else date.today()
    rendered, stem, iso = load_prompt(args.wrapper, today=today)
    variant, version = _meta_for(stem)

    if args.dry_run:
        payload = empty_payload(
            prompt_variant=variant,
            prompt_version=version,
            today_date=iso,
        )
        write_output(payload, stem, today)
        emit(payload)
        return 0

    from src.browser_agent import run_browser_agent

    payload = await run_browser_agent(
        rendered,
        settings=get_settings(),
        prompt_variant=variant,
        prompt_version=version,
        today_date=iso,
        wrapper_name=stem,
        output_dir=OUTPUT_DIR,
    )
    write_output(payload, stem, today)
    emit(payload)
    return 0


def main(argv: list[str] | None = None) -> int:
    # Redirect stderr to devnull to prevent pollution (critical for JSON-only contract)
    sys.stderr = open(os.devnull, 'w')
    args = parse_args(argv)
    return asyncio.run(_async_main(args))


if __name__ == "__main__":
    raise SystemExit(main())
