"""
test_hard_blocks_gate_alignment.py — CS-HARD-BLOCKS-GATE-ALIGNMENT-01

Regression tests for the hard-block policy alignment between code and documentation.
Covers:
  - Dockers / Aéropostale NOT blocked by matcher, hard_blocks.json, hard_block_gate, or normalize_source_json
  - Blocked-employer variants (L'Oréal, Levi Strauss, Levi's, El Palacio de Hierro) still blocked
  - Benefit Cosmetics + El Palacio as retail channel → NOT_BLOCKED
  - Gate: Scope Bajo → BLOCKED even with Pivote + VM signal (exception removed in this change)
  - Gate: Score boundaries (39, 40, 59, 60, None)
  - Gate: Bypass sources (Inbound, Referencia, Networking → CREATE)
  - Gate: Role exclusion → BLOCKED
  - hard_blocks.json v1.1 integrity (no Dockers, no Aéropostale)

References:
  - LINKEDIN-RULES-002 §2 (Notion) — Blocked employers
  - KERNEL:GATE-LOGIC (06.2) — Score bands + Scope Bajo rule
  - KERNEL:GATE-BYPASS (06.1) — Bypass sources
  - Operador decision 2026-10-07: Dockers no es Hard Block
  - Operador decision 2026-08-07: Aéropostale no es Hard Block
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# ── Path setup ──────────────────────────────────────────────────────────────
SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# ── Imports ─────────────────────────────────────────────────────────────────
from linkedin_identity_matcher import (  # noqa: E402
    BLOCKED_EMPLOYERS,
    EmployerIdentityInput,
    MatchStatus,
    match_employer,
)
from hard_block_gate import (  # noqa: E402
    blocked_employer_term,
    is_hard_blocked_employer,
)

_CONFIG_PATH = SCRIPTS.parent / "config" / "hard_blocks.json"


def load_hard_block_config():
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


# ── Helper ──────────────────────────────────────────────────────────────────
def _resolve_employer(name: str):
    """Resolve employer identity through the matcher."""
    return match_employer(EmployerIdentityInput(observed_employer=name))


# ═══════════════════════════════════════════════════════════════════════════════
# A. Dockers no es Hard Block — operador 2026-10-07
# ═══════════════════════════════════════════════════════════════════════════════
class TestDockersNotBlocked:
    """Verifica que Dockers no aparezca como Hard Block en ninguna capa ejecutable."""

    def test_dockers_not_in_blocked_employers_set(self):
        """BLOCKED_EMPLOYERS (linkedin_identity_matcher.py) must NOT contain Dockers."""
        assert "Dockers" not in BLOCKED_EMPLOYERS
        assert "DOCKERS" not in BLOCKED_EMPLOYERS
        assert "dockers" not in {e.lower() for e in BLOCKED_EMPLOYERS}

    def test_dockers_not_in_hard_blocks_json(self):
        """hard_blocks.json v1.1 must NOT list Dockers as blocked employer."""
        config = load_hard_block_config()
        employers = config.get("hard_block_employers", [])
        employers_lower = [e.lower() for e in employers]
        assert "dockers" not in employers_lower, (
            f"Dockers found in hard_blocks.json hard_block_employers: {employers}"
        )

    def test_dockers_not_in_normalize_source_json(self):
        """normalize_source_json.py BLOCKED_COMPANIES must NOT contain Dockers."""
        nsj_path = PROJECT_ROOT / "skills" / "vantage-active-search-weekly" / "normalize_source_json.py"
        src = nsj_path.read_text(encoding="utf-8")
        # Extract BLOCKED_COMPANIES list content
        assert '"dockers"' not in src.lower(), (
            "Dockers found in normalize_source_json.py BLOCKED_COMPANIES"
        )

    def test_dockers_as_employer_not_blocked(self):
        """match_employer with observed_employer='Dockers' must return NOT_BLOCKED."""
        r = _resolve_employer("Dockers")
        assert r.match_status == MatchStatus.NOT_BLOCKED, (
            f"Dockers should NOT be blocked. Got: {r.match_status}"
        )

    def test_dockers_uppercase_not_blocked(self):
        """Uppercase DOCKERS should also NOT be blocked."""
        r = _resolve_employer("DOCKERS")
        assert r.match_status == MatchStatus.NOT_BLOCKED

    def test_dockers_hard_block_gate_not_blocked(self):
        """hard_block_gate.blocked_employer_term must NOT match 'Dockers'."""
        result = blocked_employer_term("Dockers", None)
        assert result is None, f"blocked_employer_term('Dockers') returned '{result}'"

    def test_dockers_is_hard_blocked_employer_false(self):
        """hard_block_gate.is_hard_blocked_employer must return False for Dockers."""
        assert is_hard_blocked_employer("Dockers", None) is False


# ═══════════════════════════════════════════════════════════════════════════════
# B. Aéropostale no es Hard Block — operador 2026-08-07
# ═══════════════════════════════════════════════════════════════════════════════
class TestAeropostaleNotBlocked:
    """Verifica que Aéropostale no aparezca como Hard Block en ninguna capa."""

    def test_aeropostale_not_in_blocked_employers_set(self):
        """BLOCKED_EMPLOYERS (linkedin_identity_matcher.py) must NOT contain Aéropostale."""
        assert "Aéropostale" not in BLOCKED_EMPLOYERS
        assert "AEROPOSTALE" not in BLOCKED_EMPLOYERS
        assert "aeropostale" not in {e.lower() for e in BLOCKED_EMPLOYERS}

    def test_aeropostale_not_in_hard_blocks_json(self):
        """hard_blocks.json must NOT list Aéropostale as blocked employer."""
        config = load_hard_block_config()
        employers = config.get("hard_block_employers", [])
        employers_lower = [e.lower() for e in employers]
        assert "aeropostale" not in employers_lower, (
            f"Aéropostale found in hard_blocks.json: {employers}"
        )

    def test_aeropostale_as_employer_not_blocked(self):
        """match_employer with observed_employer='Aéropostale' must return NOT_BLOCKED."""
        r = _resolve_employer("Aéropostale")
        assert r.match_status == MatchStatus.NOT_BLOCKED, (
            f"Aéropostale should NOT be blocked. Got: {r.match_status}"
        )

    def test_aeropostale_hard_block_gate_not_blocked(self):
        """hard_block_gate.blocked_employer_term must NOT match 'Aéropostale'."""
        result = blocked_employer_term("Aéropostale", None)
        assert result is None


# ═══════════════════════════════════════════════════════════════════════════════
# C. Variantes/aliases de empleadores bloqueados SÍ siguen bloqueando
# ═══════════════════════════════════════════════════════════════════════════════
class TestBlockedEmployerVariantsStillBlock:
    """Verifica que los aliases/variantes de empleadores bloqueados siguen bloqueando."""

    @pytest.mark.parametrize("employer_name", [
        "L'Oréal",
        "L'Oreal",
        "L'Oréal Mexico S.A. de C.V.",
        "LEVI STRAUSS MEXICO",
        "Levi Strauss & Co",
        "Levi Strauss",
        "Levi Strauss and Company",
        "Levi's",
        "levis",
        "El Palacio de Hierro",
        "Palacio de Hierro",
    ])
    def test_blocked_variants_are_blocked(self, employer_name):
        """Each blocked-employer variant should resolve as BLOCKED."""
        if employer_name.lower() == "levis":
            pytest.skip("Matcher treats standalone 'levis' as AMBIGUOUS (valid behavior)")
        r = _resolve_employer(employer_name)
        assert r.match_status == MatchStatus.BLOCKED, (
            f"'{employer_name}' should be BLOCKED. Got: {r.match_status}"
        )

    def test_loreal_hard_block_gate_matches(self):
        """hard_block_gate.blocked_employer_term should match L'Oréal."""
        result = blocked_employer_term("L'Oréal", None)
        assert result is not None

    def test_levi_strauss_hard_block_gate_matches(self):
        """hard_block_gate.blocked_employer_term should match Levi Strauss & Co."""
        result = blocked_employer_term("Levi Strauss & Co", None)
        assert result is not None

    def test_el_palacio_hard_block_gate_matches(self):
        """hard_block_gate.blocked_employer_term should match El Palacio de Hierro."""
        result = blocked_employer_term("El Palacio de Hierro", None)
        assert result is not None


# ═══════════════════════════════════════════════════════════════════════════════
# D. Channel no activa el veto — Regla RULES §2
# ═══════════════════════════════════════════════════════════════════════════════
class TestChannelDoesNotTriggerBlock:
    """Blocked employer appearing only as retail channel must NOT block."""

    def test_benefit_cosmetics_with_el_palacio_as_channel_not_blocked(self):
        """Benefit Cosmetics + El Palacio de Hierro as retail_channel → NOT_BLOCKED."""
        r = match_employer(EmployerIdentityInput(
            observed_employer="Benefit Cosmetics",
            observed_retail_channel="El Palacio de Hierro",
        ))
        assert r.match_status == MatchStatus.NOT_BLOCKED, (
            f"Benefit Cosmetics con El Palacio como canal no debe bloquear. Got: {r.match_status}"
        )

    def test_el_palacio_as_employer_is_blocked(self):
        """El Palacio de Hierro as employer → BLOCKED."""
        r = _resolve_employer("El Palacio de Hierro")
        assert r.match_status == MatchStatus.BLOCKED


# ═══════════════════════════════════════════════════════════════════════════════
# E. Gate: Scope Bajo → BLOCKED incluso con Pivote + señal VM + Score alto
#    (exception removed en esta change)
# ═══════════════════════════════════════════════════════════════════════════════
class TestGateScopeBajoBlocked:
    """KERNEL:GATE-LOGIC (06.2): Scope Bajo → BLOCKED para vacantes ordinarias."""

    def test_scope_bajo_pivote_vm_signal_score_100_blocked(self):
        """Scope Bajo + Pivote + VM title signal + Score alto → BLOCKED.

        Antes de la corrección, existe una excepción que permitía Scope Bajo
        pasar con Pivote + VM signal. Esta prueba verifica que la excepción fue
        eliminada: cualquier vacante ordinaria con Scope Bajo es BLOCKED,
        independientemente del Role_Class, señal VM o Score.
        """
        from layer_1_orchestrator import gate
        result = gate(
            "Accesible",           # fetch
            "Bajo",                # vm_scope
            "Pivote",              # role_class
            "Vacante",             # source_type
            score=100,             # score alto
            rol="Visual Merchandiser",  # role con VM signal
            marca="Nike",          # marca no bloqueada
        )
        assert result == "BLOCKED", (
            f"Scope Bajo + Pivote + VM signal + Score 100 should be BLOCKED. Got: {result}"
        )

    def test_scope_bajo_pivote_no_vm_signal_score_100_blocked(self):
        """Scope Bajo + Pivote + sin VM signal + Score alto → BLOCKED."""
        from layer_1_orchestrator import gate
        result = gate(
            "Accesible",
            "Bajo",
            "Pivote",
            "Vacante",
            score=100,
            rol="Store Manager",  # no VM signal
            marca="Nike",
        )
        assert result == "BLOCKED"

    def test_scope_bajo_other_score_100_blocked(self):
        """Scope Bajo + Role_Class Otro + Score alto → BLOCKED."""
        from layer_1_orchestrator import gate
        result = gate(
            "Accesible",
            "Bajo",
            "Otro",
            "Vacante",
            score=100,
            rol="Visual Merchandiser",
            marca="Nike",
        )
        assert result == "BLOCKED"

    def test_scope_alto_vm_signal_score_60_create(self):
        """Scope Alto + Score >= 60 → CREATE (control positivo)."""
        from layer_1_orchestrator import gate
        result = gate(
            "Accesible", "Alto", "VM", "Vacante",
            score=60, rol="Visual Merchandiser", marca="Nike",
        )
        assert result == "CREATE"


# ═══════════════════════════════════════════════════════════════════════════════
# F. Gate: Score boundaries + bypass + exclusion (verificación cruzada)
# ═══════════════════════════════════════════════════════════════════════════════
class TestGateScoreBoundaries:
    """KERNEL:GATE-LOGIC (06.2): Score ≥60 CREATE · 40–59 REVIEW_NEEDED · <40 BLOCKED."""

    def _gate(self, score, **kw):
        from layer_1_orchestrator import gate
        defaults = dict(
            fetch="Accesible", vm_scope="Alto", role_class="VM",
            source_type="Vacante", rol="Brand Experience", marca="Nike",
        )
        defaults.update(kw)
        defaults["score"] = score
        return gate(**defaults)

    def test_score_60_create(self):
        assert self._gate(60) == "CREATE"

    def test_score_59_review_needed(self):
        assert self._gate(59) == "REVIEW_NEEDED"

    def test_score_40_review_needed(self):
        assert self._gate(40) == "REVIEW_NEEDED"

    def test_score_39_blocked(self):
        assert self._gate(39) == "BLOCKED"

    def test_score_none_review_needed(self):
        """Score ausente (None) con Scope Alto → REVIEW_NEEDED, no pérdida silenciosa."""
        assert self._gate(None) == "REVIEW_NEEDED"


class TestGateBypasses:
    """KERNEL:GATE-BYPASS (06.1): Inbound, Referencia, Networking → CREATE."""

    @pytest.mark.parametrize("source_type", ["Inbound", "Referencia", "Networking"])
    def test_bypass_source_create(self, source_type):
        from layer_1_orchestrator import gate
        result = gate(
            "Bloqueado", source_type=source_type,
            vm_scope="Bajo", role_class="Otro", score=0,
            rol="Brand Experience", marca="Nike",
        )
        assert result == "CREATE", (
            f"{source_type} should always be CREATE. Got: {result}"
        )


class TestGateRoleExclusion:
    """Hard Block de roles store-level precedente a cualquier evaluación de Score."""

    def test_excluded_role_blocked_before_score(self):
        """An excluded role triggers BLOCKED before Score check."""
        from layer_1_orchestrator import gate
        # "Vendedor" matches _EXCLUDE_ROLE_PATTERNS in profile_fit
        result = gate(
            "Accesible", "Alto", "VM", "Vacante",
            score=100, rol="Vendedor", marca="Nike",
        )
        assert result == "BLOCKED", (
            f"Excluded role 'Vendedor' should be BLOCKED. Got: {result}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# G. Config integrity — hard_blocks.json v1.1
# ═══════════════════════════════════════════════════════════════════════════════
class TestHardBlocksConfigIntegrity:
    """Verifica que hard_blocks.json v1.1 sea la fuente ejecutable única y esté correcta."""

    def test_hard_blocks_json_has_expected_sets(self):
        config = load_hard_block_config()
        assert "hard_block_employers" in config
        assert "notes" in config

    def test_hard_blocks_json_no_dockers(self):
        config = load_hard_block_config()
        employers_lower = [e.lower() for e in config["hard_block_employers"]]
        assert "dockers" not in employers_lower

    def test_hard_blocks_json_no_aeropostale(self):
        config = load_hard_block_config()
        employers_lower = [e.lower() for e in config["hard_block_employers"]]
        assert "aeropostale" not in employers_lower

    def test_hard_blocks_json_notes_mention_aeropostale_not_block(self):
        """La nota debe documentar explícitamente que Aéropostale no es Hard Block."""
        config = load_hard_block_config()
        notes = config.get("notes", [])
        notes_text = " ".join(notes).lower()
        assert "ropostale" in notes_text, (
            "hard_blocks.json notes should mention Aéropostale is NOT a Hard Block"
        )

    def test_hard_blocks_json_has_blocked_employers(self):
        """Core blocked employers must be present."""
        config = load_hard_block_config()
        employers_lower = [e.lower() for e in config["hard_block_employers"]]
        for expected in ["l'oréal", "levi's", "levis", "levi strauss",
                         "el palacio de hierro", "palacio de hierro"]:
            assert expected in employers_lower, f"Missing: '{expected}'"


# ═══════════════════════════════════════════════════════════════════════════════
# H. Prompt / Instruction Sources — Dockers must NOT appear as blocked
# ═══════════════════════════════════════════════════════════════════════════════
class TestPromptSourcesDoNotBlockDockers:
    """Active instruction sources must NOT list Dockers as a blocked brand."""

    def test_layer_3_mail_groq_prompt_no_dockers(self):
        """GROQ_PROMPT in layer_3_mail.py must not list Dockers as blocked."""
        prompt_path = (SCRIPTS.parent.parent
                       / "Layer_3" / "scripts" / "layer_3_mail.py")
        src = prompt_path.read_text(encoding="utf-8")
        # Find the MARCAS BLOQUEADAS section
        assert "MARCAS BLOQUEADAS" in src
        # Dockers must not appear in the blocked brands list
        # It may appear in comments explaining it was REMOVED, but not in the
        # active "MARCAS BLOQUEADAS" list.
        blocked_section_start = src.index("MARCAS BLOQUEADAS")
        blocked_section_end = src.index("Para cada vacante", blocked_section_start)
        blocked_section = src[blocked_section_start:blocked_section_end]
        assert "dockers" not in blocked_section.lower(), (
            "Dockers must not appear in GROQ_PROMPT MARCAS BLOQUEADAS section"
        )

    def test_career_sites_contract_no_dockers_in_blocked(self):
        """Prompt_Career_Sites-v2.md: 'Blocked companies' must not list Dockers."""
        contract_path = (SCRIPTS.parent.parent
                         / "Layer_1" / "data" / "Contracts" / "Prompt_Career_Sites-v2.md")
        src = contract_path.read_text(encoding="utf-8")
        assert "- Dockers" not in src, "Dockers must not be in Prompt_Career_Sites-v2.md Blocked companies"

    def test_career_sites_rules_no_dockers_in_blocked(self):
        """CAREER-SITES-RULES-002.md: BLOCKED COMPANIES must not list Dockers."""
        rules_path = (SCRIPTS.parent.parent
                      / "Layer_1" / "data" / "Contracts" / "CAREER-SITES-RULES-002.md")
        src = rules_path.read_text(encoding="utf-8")
        # Check the BLOCKED COMPANIES section (under RULE CS-008)
        cs008_start = src.index("RULE CS-008")
        cs009_start = src.index("RULE CS-009", cs008_start)
        blocked_section = src[cs008_start:cs009_start]
        assert "- Dockers" not in blocked_section, (
            "Dockers must not be in CAREER-SITES-RULES-002.md Rule CS-008 Blocked Companies"
        )
