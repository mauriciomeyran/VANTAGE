"""Unit / integration dry-run for prompt injection and PromptA schema."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vantage_scout.main import main  # noqa: E402
from vantage_scout.src.prompt_loader import DATE_PLACEHOLDER, load_prompt  # noqa: E402
from vantage_scout.src.validator import (  # noqa: E402
    company_is_blocked,
    title_is_hard_excluded,
    validate_raw,
)


def test_date_injection() -> None:
    rendered, stem, iso = load_prompt("Prompt_Career_Sites", today=date(2026, 8, 18))
    assert iso == "2026-08-18"
    assert DATE_PLACEHOLDER not in rendered
    assert "2026-08-18" in rendered
    assert stem == "Prompt_Career_Sites"


@pytest.mark.parametrize(
    "wrapper",
    ["Prompt_LinkedIn", "Prompt_Aggregators", "linkedin", "aggregators"],
)
def test_all_wrappers_inject(wrapper: str) -> None:
    rendered, _stem, iso = load_prompt(wrapper, today=date(2026, 8, 18))
    assert iso in rendered
    assert DATE_PLACEHOLDER not in rendered


def test_hard_exclusions() -> None:
    assert title_is_hard_excluded("Store Manager Regional") == "Store Manager"
    assert title_is_hard_excluded("Jr. Visual Merchandiser") == "Jr."
    assert title_is_hard_excluded("Visual Merchandising Coordinator") is None
    assert company_is_blocked("L'Oréal México")
    assert company_is_blocked("Levi's")
    assert company_is_blocked("El Palacio de Hierro")
    assert company_is_blocked("Dockers")
    assert company_is_blocked("Nike") is None


def test_schema_filters_blocked_and_geo() -> None:
    raw = {
        "prompt_variant": "A-weekly-unified-careersites",
        "prompt_version": "PromptA-v1.0+careersites",
        "today_date": "2026-08-18",
        "items": [
            {
                "job_id": "ok-1",
                "title": "Visual Merchandising Coordinator",
                "brand": "Richemont",
                "location": "Mexico City, CDMX",
                "apply_url": "https://careers.richemont.com/job/1",
                "source_type": "career_page",
                "source_name": "Richemont",
                "fetch_status": "direct_apply",
                "prompt_version": "PromptA-v1.0+careersites",
                "visual_signal": True,
            },
            {
                "job_id": "bad-title",
                "title": "Director Visual Merchandising",
                "brand": "Gucci",
                "location": "CDMX",
                "apply_url": "https://example.com/2",
                "source_type": "career_page",
                "source_name": "Gucci",
                "fetch_status": "direct_apply",
                "prompt_version": "PromptA-v1.0+careersites",
            },
            {
                "job_id": "bad-co",
                "title": "Visual Merchandising Manager",
                "brand": "L'Oréal",
                "location": "CDMX",
                "apply_url": "https://example.com/3",
                "source_type": "career_page",
                "source_name": "Loreal",
                "fetch_status": "direct_apply",
                "prompt_version": "PromptA-v1.0+careersites",
            },
            {
                "job_id": "bad-geo",
                "title": "Visual Merchandising Manager",
                "brand": "Nike",
                "location": "Remote, United States",
                "apply_url": "https://example.com/4",
                "source_type": "career_page",
                "source_name": "Nike",
                "fetch_status": "direct_apply",
                "prompt_version": "PromptA-v1.0+careersites",
            },
        ],
        "audit_log": [{"type": "Cloudflare", "message": "challenge on workday", "source": "test"}],
    }
    payload = validate_raw(
        raw,
        prompt_variant="A-weekly-unified-careersites",
        prompt_version="PromptA-v1.0+careersites",
        today_date="2026-08-18",
        wrapper_name="Prompt_Career_Sites",
    )
    assert len(payload.items) == 1
    assert payload.items[0].job_id == "ok-1"
    assert any(r["job_id"] != "ok-1" for r in []) or payload.reroute_candidates
    assert any(w.code == "HARD_BLOCK_EMPLOYER" for w in payload.data_quality_warnings)
    assert any(w.code == "GEO_FILTER" for w in payload.data_quality_warnings)
    assert payload.audit_log[0].type == "Cloudflare"


def test_cli_dry_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    code = main(["--wrapper", "Prompt_Career_Sites", "--dry-run", "--today", "2026-08-18"])
    assert code == 0
    out = ROOT / "vantage_scout" / "output" / "vantage_scout_Prompt_Career_Sites_20260818.json"
    assert out.is_file()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["prompt_version"] == "PromptA-v1.0+careersites"
    assert data["today_date"] == "2026-08-18"
    assert data["items"] == []
    assert "audit_log" in data
