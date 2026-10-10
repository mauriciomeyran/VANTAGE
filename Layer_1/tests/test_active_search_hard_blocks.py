"""Regression tests for the active weekly-search employer filter."""

import sys
from pathlib import Path

_SKILL_DIR = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "vantage-active-search-weekly"
)
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))

from normalize_source_json import is_blocked_company


def test_dockers_is_not_a_blocked_company():
    assert is_blocked_company("Dockers") is None


def test_confirmed_hard_blocks_remain_blocked():
    assert is_blocked_company("L'Oréal México") is not None
    assert is_blocked_company("Levi Strauss & Co.") is not None
    assert is_blocked_company("El Palacio de Hierro") is not None


def test_distinct_employer_is_not_blocked_by_retail_brand_context():
    assert is_blocked_company("Benefit Cosmetics") is None
