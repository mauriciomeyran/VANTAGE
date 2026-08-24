"""Load Scout wrappers and inject today's date."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from src.config import PROMPTS_DIR, resolve_wrapper_filename

DATE_PLACEHOLDER = "{injected_by_wrapper}"


def iso_today(today: date | None = None) -> str:
    """Return ISO date YYYY-MM-DD."""
    return (today or date.today()).isoformat()


def load_prompt(
    wrapper: str,
    *,
    today: date | None = None,
    prompts_dir: Path | None = None,
) -> tuple[str, str, str]:
    """Read a wrapper markdown file and inject the current date.

    Returns:
        (rendered_prompt, wrapper_stem, iso_date)
    """
    as_path = Path(wrapper)
    if as_path.is_file():
        text = as_path.read_text(encoding="utf-8")
        injected = iso_today(today)
        return text.replace(DATE_PLACEHOLDER, injected), as_path.stem, injected

    filename = resolve_wrapper_filename(wrapper)
    directory = prompts_dir or PROMPTS_DIR
    path = directory / filename
    if not path.is_file():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    text = path.read_text(encoding="utf-8")
    injected = iso_today(today)
    if DATE_PLACEHOLDER not in text:
        raise ValueError(
            f"Prompt {path.name} is missing required placeholder {DATE_PLACEHOLDER}"
        )
    rendered = text.replace(DATE_PLACEHOLDER, injected)
    return rendered, path.stem, injected
