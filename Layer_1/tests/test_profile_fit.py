"""Tests for profile_fit status predicates (no Notion, no env)."""

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from profile_fit import should_annotate_existing, should_auto_cleanup


class TestShouldAnnotateExisting:
    """KERNEL:GATE-DECISION-007 — Dedup_Flag / layer upgrade predicate."""

    def test_operational_statuses_are_annotatable(self):
        for status in ("Target", "Exploratorio", "REVIEW_NEEDED", "", None):
            assert should_annotate_existing(status) is True, status

    def test_protected_live_applications_are_not_annotatable(self):
        for status in (
            "Postulado", "Postulando", "En proceso",
            "Negociando", "Sin respuesta", "Contratado",
        ):
            assert should_annotate_existing(status) is False, status

    def test_terminal_statuses_are_not_annotatable(self):
        for status in ("Expirada", "Rechazado", "Archivar", "Retirado"):
            assert should_annotate_existing(status) is False, status

    def test_strips_whitespace(self):
        assert should_annotate_existing("  Target  ") is True
        assert should_annotate_existing("  Postulado  ") is False

    def test_gate_logic_would_miss_en_proceso(self):
        """Regression: gate_logic() does not protect En proceso; this helper must."""
        assert should_annotate_existing("En proceso") is False
        assert should_auto_cleanup("En proceso", ["exclude:sales"]) is False
