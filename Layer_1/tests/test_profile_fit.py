"""Tests for profile_fit status predicates (no Notion, no env)."""

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from profile_fit import (
    is_role_excluded,
    profile_misfit_reasons,
    should_annotate_existing,
    should_auto_cleanup,
)


class TestShouldAnnotateExisting:
    """KERNEL:GATE-DECISION-007 — Dedup_Flag / layer upgrade predicate."""

    def test_operational_statuses_are_annotatable(self):
        for status in ("Target", "Exploratorio", "REVIEW_NEEDED", "", None):
            assert should_annotate_existing(status) is True, status

    def test_protected_live_applications_are_not_annotatable(self):
        for status in (
            "Postulado", "Postulando", "En Proceso",
            "Negociando", "Sin Respuesta", "Contratado",
        ):
            assert should_annotate_existing(status) is False, status

    def test_terminal_statuses_are_not_annotatable(self):
        for status in ("Expirada", "Rechazado", "Archivar", "Retirado"):
            assert should_annotate_existing(status) is False, status

    def test_strips_whitespace(self):
        assert should_annotate_existing("  Target  ") is True
        assert should_annotate_existing("  Postulado  ") is False

    def test_gate_logic_would_miss_en_proceso(self):
        """Regression: gate_logic() does not protect En Proceso; this helper must."""
        assert should_annotate_existing("En Proceso") is False
        assert should_auto_cleanup("En Proceso", ["exclude:sales"]) is False


# ============================================================================
# T11 (decisión del operador 2026-10-11) — Roles de tienda sin alcance
# estratégico excluidos en la fase de ingesta con el mecanismo existente
# (profile_fit.is_role_excluded → feed_processor.process_record:1004
#  disposition="BLOCKED", notes="exclude role: <label>").
# Evidencia de origen: dry-run Workday/Chanel 2026-10-11 — Stock Associate,
# Beauty Advisor, Embajador de marca/ventas y Fashion Tailor quedaron CLEAN
# en ingesta. Sin gate nuevo.
# ============================================================================

STORE_ROLE_TITLES: tuple[tuple[str, str], ...] = (
    ("Stock Associate", "stock_associate"),
    ("stock associate", "stock_associate"),
    ("Beauty Advisor", "beauty_advisor"),
    ("Embajador de marca/ventas", "embajador_marca"),
    ("Embajador de Marca", "embajador_marca"),
    ("Brand Ambassador", "embajador_marca"),
    ("Fashion Tailor", "fashion_tailor"),
    ("Sastre", "fashion_tailor"),
)

VM_DIRECTION_TITLES: tuple[str, ...] = (
    "Visual Merchandising Director",
    "Director de Visual Merchandising",
    "Visual Merchandising Manager",
    "Gerente de Visual Merchandising",
    "VM Manager",
    "VM Director",
    "Brand Environment Director",
    "Retail Design Director",
    "Store Design Manager",
    "Visual Merchandising Coordinator",
    "Director de Escaparates",
)


class TestStoreRoleExclusionAtIntake:
    """T11: bloqueo de roles de tienda en ingesta + sin falsos positivos VM."""

    def test_store_roles_are_excluded_at_intake(self):
        for title, label in STORE_ROLE_TITLES:
            assert is_role_excluded(title) == label, title

    def test_vm_direction_roles_are_not_excluded(self):
        # Sin falsos positivos sobre roles VM de dirección (decisión del operador).
        for title in VM_DIRECTION_TITLES:
            assert is_role_excluded(title) is None, title

    def test_misfit_reasons_tag_store_roles(self):
        reasons = profile_misfit_reasons(
            rol="Stock Associate",
            marca="",
            vm_scope="Bajo",
            role_class="Otro",
            score=90,
        )
        assert "exclude:stock_associate" in reasons
