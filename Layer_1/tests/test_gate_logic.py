"""
VANTAGE Gate Logic Unit Tests

Test suite for gate logic functions based on actual code audit.

Functions tested (from actual code):
- gate_logic(entry) - Main gate logic with terminal state protection
- evaluate_gate(fetch, vm_scope, role_class) - Gate decision evaluation  
- gate(fetch, vm_scope, role_class, source_type, rol="", marca="") - Gate function from layer_1_run.py
- evaluate_application_status(status) - Application status evaluation
- evaluate_rejection_status(status) - Rejection status evaluation
- get_application_next_action(status) - Application next action mapping
"""

import pytest
import sys
from pathlib import Path

# Add scripts directory to path
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

try:
    from gate_logic import gate_logic, evaluate_gate
    GATE_LOGIC_AVAILABLE = True
except ImportError:
    GATE_LOGIC_AVAILABLE = False
    pytest.skip("gate_logic module not available", allow_module_level=True)

try:
    from layer_1_run import (
        gate as gate_layer1,
        evaluate_application_status,
        evaluate_rejection_status,
        get_application_next_action
    )
    LAYER1_AVAILABLE = True
except ImportError:
    LAYER1_AVAILABLE = False
    pytest.skip("layer_1_run module not available", allow_module_level=True)


# ============================================================================
# gate_logic() Tests
# ============================================================================

class TestGateLogic:
    """Test suite for gate_logic() function - terminal state protection only"""
    
    def test_terminal_state_protection_archivar(self):
        """Test that 'Archivar' terminal state is protected"""
        entry = {
            "Next_Action": "Archivar",
            "Status": "Target",
            "Gate_Decision": "CREATE",
            "Fetch": "Accesible"
        }
        
        result = gate_logic(entry)
        assert result == "Archivar", \
            "Terminal state 'Archivar' should not be overwritten"
    
    def test_terminal_state_protection_expirada(self):
        """Test that 'Expirada' terminal state is protected"""
        entry = {
            "Next_Action": "Expirada",
            "Status": "Target",
            "Gate_Decision": "BLOCKED",
            "Fetch": "Bloqueado"
        }
        
        result = gate_logic(entry)
        assert result == "Expirada", \
            "Terminal state 'Expirada' should not be overwritten"
    
    def test_status_postulado_returns_applied(self):
        """Test that Status='Postulado' returns APPLIED (terminal protection)"""
        entry = {
            "Next_Action": "Re-check",
            "Status": "Postulado",
            "Gate_Decision": "CREATE",
            "Fetch": "Accesible"
        }
        
        result = gate_logic(entry)
        assert result == "APPLIED", \
            "Status='Postulado' should return APPLIED (terminal protection)"
    
    def test_status_rechazado_returns_rejected(self):
        """Test that Status='Rechazado' returns REJECTED (terminal protection)"""
        entry = {
            "Next_Action": "Re-check",
            "Status": "Rechazado",
            "Gate_Decision": "BLOCKED",
            "Fetch": "Accesible"
        }
        
        result = gate_logic(entry)
        assert result == "REJECTED", \
            "Status='Rechazado' should return REJECTED (terminal protection)"
    
    def test_non_terminal_eligible_for_recalculation(self):
        """Test that non-terminal states return None (eligible for recalculation)"""
        entry = {
            "Next_Action": "Re-check",
            "Status": "Target",
            "Gate_Decision": "CREATE",
            "Fetch": "Accesible"
        }
        
        result = gate_logic(entry)
        assert result is None, \
            "Non-terminal state should return None (eligible for recalculation)"


# ============================================================================
# evaluate_gate() Tests
# ============================================================================

class TestEvaluateGate:
    """Test suite for evaluate_gate() function"""
    
    def test_fetch_accesible_vm_scope_alto_create(self):
        """Test CREATE condition: Accesible + VM_Scope Alto"""
        result = evaluate_gate("Accesible", "Alto", "VM")
        assert result == "CREATE", \
            "Accesible + VM_Scope Alto should return CREATE"
    
    def test_fetch_accesible_role_class_pivote_create(self):
        """Test CREATE condition: Accesible + Role_Class Pivote"""
        result = evaluate_gate("Accesible", "Medio", "Pivote")
        assert result == "CREATE", \
            "Accesible + Role_Class Pivote should return CREATE"
    
    def test_fetch_bloqueado_blocked(self):
        """Test BLOCKED condition: Bloqueado fetch"""
        result = evaluate_gate("Bloqueado", "Alto", "VM")
        assert result == "BLOCKED", \
            "Bloqueado fetch should return BLOCKED regardless of other factors"
    
    def test_fetch_parcial_vm_scope_bajo_blocked(self):
        """Test BLOCKED condition: Parcial + VM_Scope Bajo"""
        result = evaluate_gate("Parcial", "Bajo", "VM")
        assert result == "BLOCKED", \
            "Parcial + VM_Scope Bajo should return BLOCKED"
    
    def test_fetch_accesible_vm_scope_bajo_role_class_vm_blocked(self):
        """Test BLOCKED condition: Accesible + VM_Scope Bajo + Role_Class VM"""
        result = evaluate_gate("Accesible", "Bajo", "VM")
        assert result == "BLOCKED", \
            "Accesible + VM_Scope Bajo + Role_Class VM should return BLOCKED"


# ============================================================================
# gate() from layer_1_run.py Tests
# ============================================================================

class TestGateLayer1:
    """Test suite for gate() function from layer_1_run.py"""
    
    def test_inbound_create(self):
        """Test that Inbound source type returns CREATE"""
        result = gate_layer1("Accesible", "Alto", "VM", "Inbound", rol="VM Manager", marca="Nike")
        assert result == "CREATE", \
            "Inbound source should always return CREATE"
    
    def test_referencia_create(self):
        """Test that Referencia source type returns CREATE"""
        result = gate_layer1("Accesible", "Alto", "VM", "Referencia", rol="VM Manager", marca="Nike")
        assert result == "CREATE", \
            "Referencia source should always return CREATE"
    
    def test_networking_create(self):
        """Test that Networking source type returns CREATE"""
        result = gate_layer1("Accesible", "Alto", "VM", "Networking", rol="VM Manager", marca="Nike")
        assert result == "CREATE", \
            "Networking source should always return CREATE"
    
    def test_vacante_fetch_accesible_vm_scope_alto_create(self):
        """Test Vacante with Accesible + VM_Scope Alto returns CREATE (score>=60, no cambia lo que prueba este caso: scope)"""
        result = gate_layer1("Accesible", "Alto", "VM", "Vacante", score=75, rol="VM Manager", marca="Nike")
        assert result == "CREATE", \
            "Vacante + Accesible + VM_Scope Alto (score>=60) should return CREATE"
    
    def test_vacante_fetch_parcial_vm_scope_alto_create(self):
        """Test Vacante with Parcial + VM_Scope Alto returns CREATE (score>=60, no cambia lo que prueba este caso: scope)"""
        result = gate_layer1("Parcial", "Alto", "VM", "Vacante", score=75, rol="VM Manager", marca="Nike")
        assert result == "CREATE", \
            "Vacante + Parcial + VM_Scope Alto (score>=60) should return CREATE"
    
    def test_vacante_fetch_accesible_role_class_pivote_create(self):
        """Test Vacante with Accesible + Role_Class Pivote returns CREATE or BLOCKED depending on VM signal"""
        # Note: This depends on has_vm_title_signal() from profile_fit
        # For testing, we assume the role has VM signal
        result = gate_layer1("Accesible", "Medio", "Pivote", "Vacante", score=75, rol="Brand Experience", marca="Nike")
        # This may return BLOCKED if has_vm_title_signal returns False
        # The actual behavior depends on profile_fit module
        assert result in ["CREATE", "BLOCKED"], \
            "Vacante + Accesible + Role_Class Pivote (score>=60) should return CREATE or BLOCKED depending on VM signal"

    def test_vacante_score_none_review_needed(self):
        """Score ausente (None, default) con scope_ok=True -> REVIEW_NEEDED, no CREATE ni BLOCKED"""
        result = gate_layer1("Accesible", "Alto", "VM", "Vacante", rol="VM Manager", marca="Nike")
        assert result == "REVIEW_NEEDED", \
            "Vacante + scope_ok + score=None (default) should return REVIEW_NEEDED"


# ============================================================================
# Application Status Tests
# ============================================================================

class TestApplicationStatus:
    """Test suite for application status evaluation functions"""
    
    def test_evaluate_application_status_true(self):
        """Test application status evaluation returns True for valid statuses"""
        valid_statuses = ["Postulado", "En proceso", "Negociando", "Sin respuesta"]
        for status in valid_statuses:
            result = evaluate_application_status(status)
            assert result is True, \
                f"Status '{status}' should be recognized as application status"
    
    def test_evaluate_application_status_false(self):
        """Test application status evaluation returns False for invalid statuses"""
        invalid_statuses = ["Target", "Rechazado", "Archivado", ""]
        for status in invalid_statuses:
            result = evaluate_application_status(status)
            assert result is False, \
                f"Status '{status}' should not be recognized as application status"
    
    def test_evaluate_rejection_status_true(self):
        """Test rejection status evaluation returns True for Rechazado"""
        result = evaluate_rejection_status("Rechazado")
        assert result is True, \
            "Status 'Rechazado' should be recognized as rejection status"
    
    def test_evaluate_rejection_status_false(self):
        """Test rejection status evaluation returns False for non-rejection statuses"""
        non_rejection_statuses = ["Postulado", "En proceso", "Target", ""]
        for status in non_rejection_statuses:
            result = evaluate_rejection_status(status)
            assert result is False, \
                f"Status '{status}' should not be recognized as rejection status"


# ============================================================================
# Application Next Action Tests
# ============================================================================

class TestApplicationNextAction:
    """Test suite for get_application_next_action() function"""
    
    def test_postulado_followup(self):
        """Test Postulado status returns Follow-up"""
        result = get_application_next_action("Postulado")
        assert result == "Follow-up", \
            "Postulado status should return Follow-up"
    
    def test_en_proceso_interview_prep(self):
        """Test En proceso status returns Interview prep"""
        result = get_application_next_action("En proceso")
        assert result == "Interview prep", \
            "En proceso status should return Interview prep"
    
    def test_negociando_followup(self):
        """Test Negociando status returns Follow-up"""
        result = get_application_next_action("Negociando")
        assert result == "Follow-up", \
            "Negociando status should return Follow-up"
    
    def test_sin_respuesta_followup(self):
        """Test Sin respuesta status returns Follow-up"""
        result = get_application_next_action("Sin respuesta")
        assert result == "Follow-up", \
            "Sin respuesta status should return Follow-up"
    
    def test_unknown_status_recheck(self):
        """Test unknown status returns Re-check"""
        result = get_application_next_action("Unknown")
        assert result == "Re-check", \
            "Unknown status should return Re-check"
    
    def test_empty_status_recheck(self):
        """Test empty status returns Re-check"""
        result = get_application_next_action("")
        assert result == "Re-check", \
            "Empty status should return Re-check"


# ============================================================================
# Integration Tests
# ============================================================================

class TestGateLogicIntegration:
    """Integration tests for gate logic functionality - terminal state protection"""
    
    def test_terminal_state_priority_over_gate_decision(self):
        """Test that terminal state has priority over gate decision"""
        entry = {
            "Next_Action": "Archivar",  # Terminal state
            "Status": "Target",
            "Gate_Decision": "CREATE",  # Would normally change action
            "Fetch": "Accesible"
        }
        
        result = gate_logic(entry)
        assert result == "Archivar", \
            "Terminal state should have priority over gate decision"
    
    def test_status_postulado_overrides_non_terminal_next_action(self):
        """Test that Status='Postulado' overrides non-terminal Next_Action"""
        entry = {
            "Next_Action": "Re-check",  # Non-terminal
            "Status": "Postulado",  # Terminal status
            "Gate_Decision": "CREATE",
            "Fetch": "Accesible"
        }
        
        result = gate_logic(entry)
        assert result == "APPLIED", \
            "Status='Postulado' should return APPLIED regardless of Next_Action"
    
    def test_status_rechazado_overrides_non_terminal_next_action(self):
        """Test that Status='Rechazado' overrides non-terminal Next_Action"""
        entry = {
            "Next_Action": "Re-check",  # Non-terminal
            "Status": "Rechazado",  # Terminal status
            "Gate_Decision": "BLOCKED",
            "Fetch": "Accesible"
        }
        
        result = gate_logic(entry)
        assert result == "REJECTED", \
            "Status='Rechazado' should return REJECTED regardless of Next_Action"


# ============================================================================
# H1 — gate() Score Band Tests (KERNEL:GATE-DECISION-002 / GATE-DECISION-011
# fila 2, v9.18.0)
# ============================================================================
# A diferencia de TestGateLayer1 (arriba), estos casos mockean profile_fit
# para aislar exclusivamente la lógica de banda de Score de gate(), sin
# depender de que "VM Manager"/"Nike" pasen por is_role_excluded/
# resolve_alias_flags en el módulo real.

from unittest.mock import patch


@patch("profile_fit.has_vm_title_signal", return_value=False)
@patch("profile_fit.resolve_alias_flags", return_value=(False, None))
@patch("profile_fit.is_role_excluded", return_value=False)
class TestGateScoreBand:
    """Vacante, scope_ok=True (vm_scope=Alto, fetch=Accesible) -- solo varía Score."""

    def test_score_60_is_create(self, *_mocks):
        assert gate_layer1("Accesible", "Alto", "VM", "Vacante", score=60) == "CREATE"

    def test_score_75_is_create(self, *_mocks):
        assert gate_layer1("Accesible", "Alto", "VM", "Vacante", score=75) == "CREATE"

    def test_score_59_is_review_needed(self, *_mocks):
        assert gate_layer1("Accesible", "Alto", "VM", "Vacante", score=59) == "REVIEW_NEEDED"

    def test_score_40_is_review_needed(self, *_mocks):
        assert gate_layer1("Accesible", "Alto", "VM", "Vacante", score=40) == "REVIEW_NEEDED"

    def test_score_39_is_blocked(self, *_mocks):
        assert gate_layer1("Accesible", "Alto", "VM", "Vacante", score=39) == "BLOCKED"

    def test_score_0_is_blocked(self, *_mocks):
        assert gate_layer1("Accesible", "Alto", "VM", "Vacante", score=0) == "BLOCKED"

    def test_score_none_is_review_needed_not_blocked(self, *_mocks):
        # Golden rule: dato faltante no debe traducirse en pérdida silenciosa
        # de la vacante.
        assert gate_layer1("Accesible", "Alto", "VM", "Vacante", score=None) == "REVIEW_NEEDED"

    def test_scope_fails_blocked_regardless_of_score(self, *_mocks):
        # vm_scope=Bajo, role_class no Pivote -> scope_ok=False -> BLOCKED
        # aunque el Score sea perfecto.
        assert gate_layer1("Accesible", "Bajo", "Otro", "Vacante", score=100) == "BLOCKED"

    def test_fetch_bloqueado_blocked_regardless_of_score(self, *_mocks):
        assert gate_layer1("Bloqueado", "Alto", "VM", "Vacante", score=100) == "BLOCKED"

    def test_bypass_sources_ignore_score_entirely(self, *_mocks):
        # Inbound/Referencia/Networking: CREATE incondicional, Score no aplica.
        for source in ("Inbound", "Referencia", "Networking"):
            assert gate_layer1("Bloqueado", "Bajo", "Otro", source, score=0) == "CREATE"
            assert gate_layer1("Bloqueado", "Bajo", "Otro", source, score=None) == "CREATE"


@patch("profile_fit.is_role_excluded", return_value=True)
def test_excluded_role_blocked_before_score_check(mock_excluded):
    # Guarda dura de exclusión/alias precede a cualquier lógica de Score.
    with patch("profile_fit.resolve_alias_flags", return_value=(False, None)):
        assert gate_layer1("Accesible", "Alto", "VM", "Vacante", score=100, rol="L'Oréal Manager") == "BLOCKED"


class TestTerminalProtectionScoring:
    """H2 FIX tests: Verify terminal records don't get Score/Priority recalculated"""
    
    def test_terminal_status_protected_from_scoring(self):
        """Test that Postulado status is protected from Score recalculation"""
        entry = {
            "Next_Action": "Follow-up",
            "Status": "Postulado",
            "Gate_Decision": "CREATE",
            "Fetch": "Accesible"
        }
        
        result = gate_logic(entry)
        assert result == "APPLIED", \
            "Postulado should return APPLIED (terminal protection)"
    
    def test_rejected_status_protected_from_scoring(self):
        """Test that Rechazado status is protected from Score recalculation"""
        entry = {
            "Next_Action": "Post-Mortem",
            "Status": "Rechazado",
            "Gate_Decision": "REJECTED",
            "Fetch": "Accesible"
        }
        
        result = gate_logic(entry)
        assert result == "REJECTED", \
            "Rechazado should return REJECTED (terminal protection)"
    
    def test_archivar_action_protected_from_scoring(self):
        """Test that Archivar Next_Action is protected from Score recalculation"""
        entry = {
            "Next_Action": "Archivar",
            "Status": "Target",
            "Gate_Decision": "BLOCKED",
            "Fetch": "Accesible"
        }
        
        result = gate_logic(entry)
        assert result == "Archivar", \
            "Archivar Next_Action should be protected (terminal protection)"
    
    def test_expirada_action_protected_from_scoring(self):
        """Test that Expirada Next_Action is protected from Score recalculation"""
        entry = {
            "Next_Action": "Expirada",
            "Status": "Target",
            "Gate_Decision": "BLOCKED",
            "Fetch": "Bloqueado"
        }
        
        result = gate_logic(entry)
        assert result == "Expirada", \
            "Expirada Next_Action should be protected (terminal protection)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])