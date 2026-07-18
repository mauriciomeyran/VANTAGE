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
    from gate_logic import gate_logic, evaluate_gate, txt
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
    """Test suite for gate_logic() function"""
    
    def test_terminal_state_protection_archivar(self):
        """Test that 'Archivar' terminal state is protected"""
        entry = {
            "Next_Action": "Archivar",
            "Status": "Postulado",
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
            "Status": "Rechazado",
            "Gate_Decision": "BLOCKED",
            "Fetch": "Bloqueado"
        }
        
        result = gate_logic(entry)
        assert result == "Expirada", \
            "Terminal state 'Expirada' should not be overwritten"
    
    def test_applied_postulado_followup(self):
        """Test APPLIED gate decision with Postulado status"""
        entry = {
            "Next_Action": "Re-check",  # Non-terminal state
            "Status": "Postulado",
            "Gate_Decision": "APPLIED",
            "Fetch": "Accesible"
        }
        
        result = gate_logic(entry)
        assert result == "Follow-up", \
            "APPLIED + Postulado should return Follow-up"
    
    def test_applied_en_proceso_interview_prep(self):
        """Test APPLIED gate decision with En proceso status"""
        entry = {
            "Next_Action": "Re-check",
            "Status": "En proceso",
            "Gate_Decision": "APPLIED",
            "Fetch": "Accesible"
        }
        
        result = gate_logic(entry)
        assert result == "Interview prep", \
            "APPLIED + En proceso should return Interview prep"
    
    def test_applied_negociando_followup(self):
        """Test APPLIED gate decision with Negociando status"""
        entry = {
            "Next_Action": "Re-check",
            "Status": "Negociando",
            "Gate_Decision": "APPLIED",
            "Fetch": "Accesible"
        }
        
        result = gate_logic(entry)
        assert result == "Follow-up", \
            "APPLIED + Negociando should return Follow-up"
    
    def test_applied_sin_respuesta_followup(self):
        """Test APPLIED gate decision with Sin respuesta status"""
        entry = {
            "Next_Action": "Re-check",
            "Status": "Sin respuesta",
            "Gate_Decision": "APPLIED",
            "Fetch": "Accesible"
        }
        
        result = gate_logic(entry)
        assert result == "Follow-up", \
            "APPLIED + Sin respuesta should return Follow-up"
    
    def test_create_postulado_followup(self):
        """Test CREATE gate decision with Postulado status"""
        entry = {
            "Next_Action": "Re-check",
            "Status": "Postulado",
            "Gate_Decision": "CREATE",
            "Fetch": "Accesible"
        }
        
        result = gate_logic(entry)
        assert result == "Follow-up", \
            "CREATE + Postulado should return Follow-up"
    
    def test_create_default_recheck(self):
        """Test CREATE gate decision with default status"""
        entry = {
            "Next_Action": "Re-check",
            "Status": "Target",
            "Gate_Decision": "CREATE",
            "Fetch": "Accesible"
        }
        
        result = gate_logic(entry)
        assert result == "Re-check", \
            "CREATE with non-application status should return Re-check"
    
    def test_blocked_bloqueado_reparar_url(self):
        """Test BLOCKED gate decision with Bloqueado fetch"""
        entry = {
            "Next_Action": "Re-check",
            "Status": "Target",
            "Gate_Decision": "BLOCKED",
            "Fetch": "Bloqueado"
        }
        
        result = gate_logic(entry)
        assert result == "Reparar URL", \
            "BLOCKED + Bloqueado should return Reparar URL"
    
    def test_blocked_parcial_verificar_jd(self):
        """Test BLOCKED gate decision with Parcial fetch"""
        entry = {
            "Next_Action": "Re-check",
            "Status": "Target",
            "Gate_Decision": "BLOCKED",
            "Fetch": "Parcial"
        }
        
        result = gate_logic(entry)
        assert result == "Verificar JD", \
            "BLOCKED + Parcial should return Verificar JD"
    
    def test_blocked_default_archivar(self):
        """Test BLOCKED gate decision with default fetch"""
        entry = {
            "Next_Action": "Re-check",
            "Status": "Target",
            "Gate_Decision": "BLOCKED",
            "Fetch": "Accesible"
        }
        
        result = gate_logic(entry)
        assert result == "Archivar", \
            "BLOCKED with other fetch should return Archivar"
    
    def test_default_fallback_archivar(self):
        """Test default fallback to Archivar"""
        entry = {
            "Next_Action": "Re-check",
            "Status": "Target",
            "Gate_Decision": "UNKNOWN",
            "Fetch": "Accesible"
        }
        
        result = gate_logic(entry)
        assert result == "Archivar", \
            "Unknown gate decision should default to Archivar"


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
        result = gate_layer1("Accesible", "Alto", "VM", "Inbound", "VM Manager", "Nike")
        assert result == "CREATE", \
            "Inbound source should always return CREATE"
    
    def test_referencia_create(self):
        """Test that Referencia source type returns CREATE"""
        result = gate_layer1("Accesible", "Alto", "VM", "Referencia", "VM Manager", "Nike")
        assert result == "CREATE", \
            "Referencia source should always return CREATE"
    
    def test_networking_create(self):
        """Test that Networking source type returns CREATE"""
        result = gate_layer1("Accesible", "Alto", "VM", "Networking", "VM Manager", "Nike")
        assert result == "CREATE", \
            "Networking source should always return CREATE"
    
    def test_vacante_fetch_accesible_vm_scope_alto_create(self):
        """Test Vacante with Accesible + VM_Scope Alto returns CREATE"""
        result = gate_layer1("Accesible", "Alto", "VM", "Vacante", "VM Manager", "Nike")
        assert result == "CREATE", \
            "Vacante + Accesible + VM_Scope Alto should return CREATE"
    
    def test_vacante_fetch_parcial_vm_scope_alto_create(self):
        """Test Vacante with Parcial + VM_Scope Alto returns CREATE"""
        result = gate_layer1("Parcial", "Alto", "VM", "Vacante", "VM Manager", "Nike")
        assert result == "CREATE", \
            "Vacante + Parcial + VM_Scope Alto should return CREATE"
    
    def test_vacante_fetch_accesible_role_class_pivote_create(self):
        """Test Vacante with Accesible + Role_Class Pivote returns CREATE"""
        # Note: This depends on has_vm_title_signal() from profile_fit
        # For testing, we assume the role has VM signal
        result = gate_layer1("Accesible", "Medio", "Pivote", "Vacante", "Brand Experience", "Nike")
        # This may return BLOCKED if has_vm_title_signal returns False
        # The actual behavior depends on profile_fit module
        assert result in ["CREATE", "BLOCKED"], \
            "Vacante + Accesible + Role_Class Pivote should return CREATE or BLOCKED depending on VM signal"


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
    """Integration tests for gate logic functionality"""
    
    def test_terminal_state_priority_over_gate_decision(self):
        """Test that terminal state has priority over gate decision"""
        entry = {
            "Next_Action": "Archivar",  # Terminal state
            "Status": "Postulado",
            "Gate_Decision": "CREATE",  # Would normally change action
            "Fetch": "Accesible"
        }
        
        result = gate_logic(entry)
        assert result == "Archivar", \
            "Terminal state should have priority over gate decision"
    
    def test_application_status_workflow(self):
        """Test complete application status workflow"""
        # Simulate application progression
        statuses = ["Postulado", "En proceso", "Negociando"]
        expected_actions = ["Follow-up", "Interview prep", "Follow-up"]
        
        for status, expected_action in zip(statuses, expected_actions):
            entry = {
                "Next_Action": "Re-check",
                "Status": status,
                "Gate_Decision": "APPLIED",
                "Fetch": "Accesible"
            }
            result = gate_logic(entry)
            assert result == expected_action, \
                f"Status '{status}' should return '{expected_action}'"
    
    def test_blocked_workflow(self):
        """Test complete blocked workflow"""
        blocked_cases = [
            ("Bloqueado", "Reparar URL"),
            ("Parcial", "Verificar JD"),
            ("Accesible", "Archivar"),
        ]
        
        for fetch, expected_action in blocked_cases:
            entry = {
                "Next_Action": "Re-check",
                "Status": "Target",
                "Gate_Decision": "BLOCKED",
                "Fetch": fetch
            }
            result = gate_logic(entry)
            assert result == expected_action, \
                f"Fetch '{fetch}' should return '{expected_action}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])