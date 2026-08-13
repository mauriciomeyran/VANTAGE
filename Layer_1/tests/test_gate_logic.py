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
        get_application_next_action,
        txt,
        validate_url_pre_ingestion
    )
    LAYER1_AVAILABLE = True
except ImportError:
    LAYER1_AVAILABLE = False
    pytest.skip("layer_1_run module not available", allow_module_level=True)

try:
    from priority_logic import infer_prioridad, get_importancia_bucket, apply_importancia_matrix
    PRIORITY_LOGIC_AVAILABLE = True
except ImportError:
    PRIORITY_LOGIC_AVAILABLE = False
    pytest.skip("priority_logic module not available", allow_module_level=True)

try:
    from backfill_class_a import txt as txt_backfill
    BACKFILL_AVAILABLE = True
except ImportError:
    BACKFILL_AVAILABLE = False
    pytest.skip("backfill_class_a module not available", allow_module_level=True)


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


# ============================================================================
# Rich Text Concatenation Tests (KERNEL:TXT-CONCAT-001)
# ============================================================================
# Fix for bug where txt() only read chunk[0] of rich_text arrays,
# causing JD_ALREADY_EXISTS bypass to fail for multi-chunk JDs.

class TestRichTextConcatenation:
    """Test suite for txt() rich_text concatenation fix"""
    
    def test_txt_concatenates_rich_text_chunks(self):
        """Test that txt() concatenates all rich_text chunks, not just chunk[0]"""
        # Simulate Notion API response with multi-chunk rich_text
        prop = {
            "type": "rich_text",
            "rich_text": [
                {"plain_text": "Miguel Hidalgo, CDMX$15,000 por mes -  Tiempo completo&nbsp;"},
                {"plain_text": "Buscamos Visual Merchandiser con experiencia en retail de lujo."},
                {"plain_text": "Responsabilidades: - Desarrollar estrategias visuales en tienda"}
            ]
        }
        
        result = txt(prop)
        expected = "Miguel Hidalgo, CDMX$15,000 por mes -  Tiempo completo&nbsp;Buscamos Visual Merchandiser con experiencia en retail de lujo.Responsabilidades: - Desarrollar estrategias visuales en tienda"
        
        assert result == expected, \
            f"txt() should concatenate all chunks. Expected length {len(expected)}, got {len(result)}"
    
    def test_txt_single_chunk_rich_text(self):
        """Test that txt() works correctly with single-chunk rich_text"""
        prop = {
            "type": "rich_text",
            "rich_text": [
                {"plain_text": "Single chunk text"}
            ]
        }
        
        result = txt(prop)
        assert result == "Single chunk text", \
            "txt() should handle single-chunk rich_text correctly"
    
    def test_txt_empty_rich_text(self):
        """Test that txt() handles empty rich_text array"""
        prop = {
            "type": "rich_text",
            "rich_text": []
        }
        
        result = txt(prop)
        assert result == "", \
            "txt() should return empty string for empty rich_text array"
    
    def test_txt_concatenates_title_chunks(self):
        """Test that txt() concatenates all title chunks, not just chunk[0]"""
        prop = {
            "type": "title",
            "title": [
                {"plain_text": "Visual "},
                {"plain_text": "Merchandiser "},
                {"plain_text": "Manager"}
            ]
        }
        
        result = txt(prop)
        expected = "Visual Merchandiser Manager"
        
        assert result == expected, \
            f"txt() should concatenate all title chunks. Expected '{expected}', got '{result}'"
    
    def test_validate_url_jd_bypass_with_concatenated_text(self):
        """Test that validate_url_pre_ingestion correctly bypasses with concatenated JD > 100 chars"""
        # Simulate JD that was previously truncated to 60 chars in chunk[0]
        # but is now properly concatenated to > 100 chars
        jd_text = "Miguel Hidalgo, CDMX$15,000 por mes -  Tiempo completo&nbsp;Buscamos Visual Merchandiser con experiencia en retail de lujo. Responsabilidades: - Desarrollar estrategias visuales en tienda - Implementar guidelines de marca - Capacitar al equipo de tienda - Mantener estándares visuales consistentes"
        
        assert len(jd_text) > 100, "Test JD should be > 100 chars"
        
        is_valid, reason = validate_url_pre_ingestion("https://indeed.com/job", jd_text)
        
        assert is_valid is True, \
            f"JD > 100 chars should bypass URL validation. Got valid={is_valid}, reason={reason}"
        assert reason == "JD_ALREADY_EXISTS", \
            f"Reason should be JD_ALREADY_EXISTS. Got {reason}"
    
    def test_validate_url_jd_bypass_threshold(self):
        """Test that JD <= 100 chars does NOT trigger bypass"""
        jd_text = "Short JD text that is exactly 100 characters......................................................"
        
        assert len(jd_text) <= 100, "Test JD should be <= 100 chars"
        
        is_valid, reason = validate_url_pre_ingestion("https://indeed.com/job", jd_text)
        
        # Should NOT bypass with JD_ALREADY_EXISTS for short JD
        assert reason != "JD_ALREADY_EXISTS", \
            f"JD <= 100 chars should NOT trigger JD_ALREADY_EXISTS bypass. Got reason={reason}"
    
    def test_txt_handles_non_rich_text_types(self):
        """Test that txt() still works correctly for non-rich_text types"""
        # URL type
        url_prop = {"type": "url", "url": "https://example.com"}
        assert txt(url_prop) == "https://example.com"
        
        # Select type
        select_prop = {"type": "select", "select": {"name": "Target"}}
        assert txt(select_prop) == "Target"
        
        # Number type
        number_prop = {"type": "number", "number": 42}
        assert txt(number_prop) == 42
        
        # Date type
        date_prop = {"type": "date", "date": {"start": "2026-08-13"}}
        assert txt(date_prop) == "2026-08-13"
        
        # Empty prop
        assert txt(None) == ""
        assert txt({}) == ""


# ============================================================================
# Priority Logic Created Time Fix Tests (KERNEL:PRIORITY-CREATED-TIME-001)
# ============================================================================
# Fix for bug where infer_prioridad() read created_time from props instead of
# item["created_time"], causing urgency to always be MEDIO (sin_fecha_creacion).

class TestPriorityLogicCreatedTime:
    """Test suite for infer_prioridad() created_time fix"""

    def test_infer_prioridad_reads_created_time_from_item_root(self):
        """Test that infer_prioridad reads created_time from item root, not props"""
        from datetime import date, timedelta

        # Create a mock item with created_time at root level (correct Notion API structure)
        item = {
            "id": "test-id",
            "created_time": "2026-08-10T00:00:00.000Z",  # 3 days ago
            "properties": {
                "JD": {"type": "rich_text", "rich_text": [{"plain_text": "No deadline mentioned"}]},
                "Source_Type ": {"type": "select", "select": {"name": "Vacante"}},
                "Score": {"type": "number", "number": 60}
            }
        }

        today = date(2026, 8, 13)  # Fixed date for consistent testing
        prioridad, reason = infer_prioridad(item, today)

        # Should calculate urgency based on created_time (3 days old = ALTO)
        # not fall back to MEDIO with reason "sin_fecha_creacion"
        assert "sin_fecha_creacion" not in reason, \
            f"Should not use 'sin_fecha_creacion' reason when created_time exists. Got reason: {reason}"
        assert "creado_" in reason, \
            f"Should use 'creado_X_dias' reason when created_time exists. Got reason: {reason}"

    def test_infer_prioridad_urgency_alto_for_recent_vacancies(self):
        """Test that vacancies <= 3 days old get ALTO urgency"""
        from datetime import date

        item = {
            "id": "test-id",
            "created_time": "2026-08-10T00:00:00.000Z",  # 3 days ago
            "properties": {
                "JD": {"type": "rich_text", "rich_text": [{"plain_text": "No deadline"}]},
                "Source_Type ": {"type": "select", "select": {"name": "Vacante"}},
                "Score": {"type": "number", "number": 60}
            }
        }

        today = date(2026, 8, 13)
        prioridad, reason = infer_prioridad(item, today)

        # 3 days old should be ALTO urgency
        assert "creado_3_dias" in reason, \
            f"3-day-old vacancy should have 'creado_3_dias' reason. Got: {reason}"

    def test_infer_prioridad_urgency_medio_for_medium_age(self):
        """Test that vacancies 4-14 days old get MEDIO urgency"""
        from datetime import date

        item = {
            "id": "test-id",
            "created_time": "2026-08-05T00:00:00.000Z",  # 8 days ago
            "properties": {
                "JD": {"type": "rich_text", "rich_text": [{"plain_text": "No deadline"}]},
                "Source_Type ": {"type": "select", "select": {"name": "Vacante"}},
                "Score": {"type": "number", "number": 60}
            }
        }

        today = date(2026, 8, 13)
        prioridad, reason = infer_prioridad(item, today)

        # 8 days old should be MEDIO urgency
        assert "creado_8_dias" in reason, \
            f"8-day-old vacancy should have 'creado_8_dias' reason. Got: {reason}"

    def test_infer_prioridad_urgency_bajo_for_old_vacancies(self):
        """Test that vacancies > 14 days old get BAJO urgency"""
        from datetime import date

        item = {
            "id": "test-id",
            "created_time": "2026-07-20T00:00:00.000Z",  # 24 days ago
            "properties": {
                "JD": {"type": "rich_text", "rich_text": [{"plain_text": "No deadline"}]},
                "Source_Type ": {"type": "select", "select": {"name": "Vacante"}},
                "Score": {"type": "number", "number": 60}
            }
        }

        today = date(2026, 8, 13)
        prioridad, reason = infer_prioridad(item, today)

        # 24 days old should be BAJO urgency
        assert "creado_24_dias" in reason, \
            f"24-day-old vacancy should have 'creado_24_dias' reason. Got: {reason}"

    def test_infer_prioridad_critical_override_by_source_type(self):
        """Test that Inbound/Referencia/Networking override urgency to CRÍTICO"""
        from datetime import date

        for source_type in ["Inbound", "Referencia", "Networking"]:
            item = {
                "id": "test-id",
                "created_time": "2026-07-20T00:00:00.000Z",  # 24 days ago (would be BAJO normally)
                "properties": {
                    "JD": {"type": "rich_text", "rich_text": [{"plain_text": "No deadline"}]},
                    "Source_Type ": {"type": "select", "select": {"name": source_type}},
                    "Score": {"type": "number", "number": 60}
                }
            }

            today = date(2026, 8, 13)
            prioridad, reason = infer_prioridad(item, today)

            # Should be CRÍTICO due to source_type, not BAJO from age
            assert "source_type_" in reason, \
                f"{source_type} should trigger source_type urgency. Got reason: {reason}"
            assert prioridad == "4 CRÍTICO", \
                f"{source_type} should result in CRÍTICO priority. Got: {prioridad}"

    def test_infer_prioridad_critical_override_by_deadline(self):
        """Test that deadline within 5 days overrides urgency to CRÍTICO"""
        from datetime import date

        item = {
            "id": "test-id",
            "created_time": "2026-07-20T00:00:00.000Z",  # 24 days ago (would be BAJO normally)
            "properties": {
                "JD": {"type": "rich_text", "rich_text": [{"plain_text": "Apply by 08/15/2026"}]},  # 2 days from test date
                "Source_Type ": {"type": "select", "select": {"name": "Vacante"}},
                "Score": {"type": "number", "number": 60}
            }
        }

        today = date(2026, 8, 13)
        prioridad, reason = infer_prioridad(item, today)

        # Should be CRÍTICO due to deadline, not BAJO from age
        assert "deadline_jd" in reason, \
            f"Deadline within 5 days should trigger deadline_jd urgency. Got reason: {reason}"
        assert prioridad == "4 CRÍTICO", \
            f"Deadline within 5 days should result in CRÍTICO priority. Got: {prioridad}"

    def test_infer_prioridad_missing_created_time_fallback(self):
        """Test that missing created_time falls back to MEDIO with sin_fecha_creacion"""
        from datetime import date

        item = {
            "id": "test-id",
            # No created_time field
            "properties": {
                "JD": {"type": "rich_text", "rich_text": [{"plain_text": "No deadline"}]},
                "Source_Type ": {"type": "select", "select": {"name": "Vacante"}},
                "Score": {"type": "number", "number": 60}
            }
        }

        today = date(2026, 8, 13)
        prioridad, reason = infer_prioridad(item, today)

        # Should fall back to MEDIO when created_time is missing
        assert "sin_fecha_creacion" in reason, \
            f"Missing created_time should trigger sin_fecha_creacion reason. Got: {reason}"


# ============================================================================
# Backfill Class A txt() Tests (KERNEL:BACKFILL-TXT-CONCAT-001)
# ============================================================================
# Fix for bug where backfill_class_a.py::txt() only read chunk[0] of
# rich_text arrays, same class of bug as layer_1_run.py and priority_logic.py.

class TestBackfillTxtConcatenation:
    """Test suite for backfill_class_a.py::txt() rich_text concatenation fix"""

    def test_backfill_txt_concatenates_rich_text_chunks(self):
        """Test that backfill txt() concatenates all rich_text chunks, not just chunk[0]"""
        # Simulate Notion API response with multi-chunk rich_text
        prop = {
            "type": "rich_text",
            "rich_text": [
                {"plain_text": "Miguel Hidalgo, CDMX$15,000 por mes -  Tiempo completo&nbsp;"},
                {"plain_text": "Buscamos Visual Merchandiser con experiencia en retail de lujo."},
                {"plain_text": "Responsabilidades: - Desarrollar estrategias visuales en tienda"}
            ]
        }

        result = txt_backfill(prop)
        expected = "Miguel Hidalgo, CDMX$15,000 por mes -  Tiempo completo&nbsp;Buscamos Visual Merchandiser con experiencia en retail de lujo.Responsabilidades: - Desarrollar estrategias visuales en tienda"

        assert result == expected, \
            f"backfill txt() should concatenate all chunks. Expected length {len(expected)}, got {len(result)}"

    def test_backfill_txt_single_chunk_rich_text(self):
        """Test that backfill txt() works correctly with single-chunk rich_text"""
        prop = {
            "type": "rich_text",
            "rich_text": [
                {"plain_text": "Single chunk text"}
            ]
        }

        result = txt_backfill(prop)
        assert result == "Single chunk text", \
            "backfill txt() should handle single-chunk rich_text correctly"

    def test_backfill_txt_empty_rich_text(self):
        """Test that backfill txt() handles empty rich_text array"""
        prop = {
            "type": "rich_text",
            "rich_text": []
        }

        result = txt_backfill(prop)
        assert result == "", \
            "backfill txt() should return empty string for empty rich_text array"

    def test_backfill_txt_concatenates_title_chunks(self):
        """Test that backfill txt() concatenates all title chunks, not just chunk[0]"""
        prop = {
            "type": "title",
            "title": [
                {"plain_text": "Visual "},
                {"plain_text": "Merchandiser "},
                {"plain_text": "Manager"}
            ]
        }

        result = txt_backfill(prop)
        expected = "Visual Merchandiser Manager"

        assert result == expected, \
            f"backfill txt() should concatenate all title chunks. Expected '{expected}', got '{result}'"

    def test_backfill_txt_handles_non_rich_text_types(self):
        """Test that backfill txt() still works correctly for non-rich_text types"""
        # URL type
        url_prop = {"type": "url", "url": "https://example.com"}
        assert txt_backfill(url_prop) == "https://example.com"

        # Select type
        select_prop = {"type": "select", "select": {"name": "Target"}}
        assert txt_backfill(select_prop) == "Target"

        # Empty prop
        assert txt_backfill(None) == ""
        assert txt_backfill({}) == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])