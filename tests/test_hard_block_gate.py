"""Tests for Layer_1/scripts/hard_block_gate.py (Fase 3 standalone)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "Layer_1" / "scripts"))

from hard_block_gate import (  # noqa: E402
    blocked_employer_term,
    is_hard_blocked_employer,
)

BLOCKED_SAMPLES = [
    ("L'Oréal", None),
    ("Loreal", None),
    ("Levi's", None),
    ("Levis", None),
    ("Palacio de Hierro", None),
]

ALLOWED_SAMPLES = [
    ("Nike", None),
    ("Adidas", None),
    ("Zara", None),
    ("", None),
    (None, None),
]

def test_is_hard_blocked_true():
    for brand, holding in BLOCKED_SAMPLES:
        assert is_hard_blocked_employer(brand, holding) is True, brand

def test_is_hard_blocked_false():
    for brand, holding in ALLOWED_SAMPLES:
        assert is_hard_blocked_employer(brand, holding) is False, brand

def test_blocked_employer_term_returns_str_or_none():
    for brand, holding in BLOCKED_SAMPLES:
        term = blocked_employer_term(brand, holding)
        assert isinstance(term, str) and term, f"expected non-empty term for {brand}"

    for brand, holding in ALLOWED_SAMPLES:
        term = blocked_employer_term(brand, holding)
        assert term is None, f"expected None for {brand}"
