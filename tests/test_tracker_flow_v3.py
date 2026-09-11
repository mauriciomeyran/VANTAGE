"""
Tests para tracker_flow.py - V3 Fixes (F1-F15)

A5: Mapa de cobertura test↔celda/rama obligatorio.
"""

import pytest
import sys
from pathlib import Path

# Add Layer_1/scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "Layer_1" / "scripts"))

from tracker_flow import (
    Status, NextAction, GateDecision, Actor,
    normalize_record, extract_value,
    is_mutable, _is_human_edit, _was_edited_since_last_run, _was_touched_by_human,
    evaluate_transition, LIFECYCLE_MATRIX,
    evaluate_flow, generate_propose_log, execute_transition, execute_transition_with_propose_log,
    archive_gate, to_notion_properties, generate_archive_notes,
    evaluate_review_gate, diff_records,
    SURVIVOR_PRIORITY, get_survivor_rank, choose_survivor,
    TERMINAL_STATUSES, LIVE_APPLICATION_STATUSES, PROTECTED_STATUSES,
    KNOWN_BOT_IDS, DELETED_VALUE_MAPPINGS
)

from tests.mocks.notion_fake import NotionClientFake
import json


# ── H7/A5: Mapa cobertura test↔hallazgo (auto-verificado por test_h7_coverage_map_complete)
COVERAGE_MAP = {
    "test_f1_normalize_record_api_shape": "F1",
    "test_g1_fail_closed_missing_last_edited": "G1/F1",
    "test_f1_extract_value_both_shapes": "F1/F4",
    "test_f3_is_human_edit_known_bot": "F3",
    "test_f3_was_touched_by_human": "F3",
    "test_f3_propose_log_idempotency": "F3",
    "test_f5_typo_fixed": "F5",
    "test_f6_create_objetivo_transition": "F6",
    "test_f6_missing_lifecycle_legs": "F6",
    "test_f6_en_proceso_to_rechazado": "F6",
    "test_f6_exploratorio_transitions": "F6",
    "test_f6_manual_rule": "F6",
    "test_f7_review_gate_design": "F7",
    "test_f7_review_gate_blocked": "F7/G5/H2",
    "test_f8_single_literal_per_value": "F8",
    "test_f10_enum_enforcement": "F10",
    "test_f11_composite_guard": "F11/G3",
    "test_f12_contratado_first": "F12",
    "test_f12_choose_survivor": "F12",
    "test_g2_execute_transition_payload": "G2/F2",
    "test_g2_execute_transition_with_propose_log": "G2/F2/F3",
    "test_f4_diff_with_type_preservation": "F4",
    "test_f2_single_archive_path": "F2",
    "test_protected_statuses": "B3",
    "test_notion_fake_mirror_api": "F15/G6",
    "test_end_to_end_normalize_to_archive": "E2E(F1/F2)",
    "test_fixture_loading": "A5/F15",
    "test_h3_fake_pages_chain": "H3/G6",
    "test_h7_url_tiebreak_prefers_url": "H7/F12",
    "test_h7_coverage_map_complete": "H7/A5",
}

# ── F1: Normalization Boundary Tests ──────────────────────────────────────────

def test_f1_normalize_record_api_shape():
    """F1+G1: normalize_record convierte shapes API a plano, extrae desde raíz"""
    api_record = {
        "id": "test-001",
        "last_edited_by": {"object": "user", "id": "human-user-123"},
        "last_edited_time": "2026-09-10T12:00:00.000Z",
        "properties": {
            "Status": {"select": {"name": "Objetivo"}},
            "Score": {"number": 85},
            "URL": {"url": "https://example.com"}
        }
    }
    
    flat = normalize_record(api_record)
    
    assert flat["Status"] == "Objetivo"
    assert flat["Score"] == 85
    assert flat["URL"] == "https://example.com"
    assert flat["last_edited_by_id"] == "human-user-123"
    assert flat["last_edited_time"] == "2026-09-10T12:00:00.000Z"
    assert flat["id"] == "test-001"


def test_g1_fail_closed_missing_last_edited():
    """G1: Fail-closed - sin last_edited_* tratar como humano/reciente, nunca auto-ejecutar"""
    api_record = {
        "id": "test-001",
        "properties": {
            "Status": {"select": {"name": "Objetivo"}},
            "Score": {"number": 30}
        }
    }
    
    flat = normalize_record(api_record)
    
    # Sin last_edited_by_id → _is_human_edit("") = True (safe default)
    assert _is_human_edit(flat.get("last_edited_by_id", "")) is True
    
    # Sin last_edited_time → _was_edited_since_last_run("") = True (safe default)
    assert _was_edited_since_last_run(flat.get("last_edited_time", "")) is True
    
    # Protección manual activada en silencio
    assert _was_touched_by_human(flat) is True


def test_f1_extract_value_both_shapes():
    """F1+F4: extract_value acepta ambas shapes API y plano"""
    # API shape
    api_shape = {"type": "select", "select": {"name": "Objetivo"}}
    assert extract_value(api_shape) == "Objetivo"
    
    # Flat value
    flat_value = "Objetivo"
    assert extract_value(flat_value) == "Objetivo"
    
    # Number
    assert extract_value(42) == 42
    assert extract_value("42") == "42"


# ── F3: Human Edit Detection Tests ───────────────────────────────────────────

def test_f3_is_human_edit_known_bot():
    """F3: Known bot IDs return False"""
    KNOWN_BOT_IDS.add("test-bot-id")
    assert not _is_human_edit("test-bot-id")
    assert _is_human_edit("human-user-123")


def test_f3_was_touched_by_human():
    """F3/H7: Combined check - human author AND recent edit (deterministic)."""
    
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    assert _was_touched_by_human({
        "last_edited_by_id": "human-user-123",
        "last_edited_time": now,
    }) is True
    assert _was_touched_by_human({
        "last_edited_by_id": "test-bot-id",
        "last_edited_time": "2020-01-01T00:00:00.000Z",
    }) is False


def test_f3_propose_log_idempotency():
    """F3: Skip si ya existe [PROPOSE] idéntica abierta"""
    record = {
        "id": "test-001",
        "Notas": "[PROPOSE] pipeline → Expirada: url_failed\nEvidencia: test",
        "Status": "Objetivo"
    }
    
    # Find the url_failed transition
    transition = None
    for t in LIFECYCLE_MATRIX:
        if t.event == "url_failed":
            transition = t
            break
    
    assert transition is not None, "url_failed transition not found"
    
    updated_notes = generate_propose_log(record, transition, "test evidence")
    
    # Should return existing notes without duplicate
    assert "[PROPOSE] pipeline → Expirada: url_failed" in updated_notes
    # Count occurrences - should be 1, not 2
    assert updated_notes.count("[PROPOSE]") == 1


# ── F5: Typo Fix Tests ───────────────────────────────────────────────────────

def test_f5_typo_fixed():
    """F5: Status.RETIRADO (was RETRIRADO)"""
    assert Status.RETIRADO.value == "Retirado"
    assert hasattr(Status, 'RETIRADO')
    assert not hasattr(Status, 'RETRIRADO')


# ── F6: Complete Lifecycle Matrix Tests ───────────────────────────────────────

def test_f6_create_objetivo_transition():
    """F6: Producer for clean Objetivo exists"""
    transition = evaluate_transition(
        {"Status": None},
        "create_objetivo",
        Actor.HUMANO
    )
    assert transition is not None
    assert transition.to_status == Status.OBJETIVO


def test_f6_missing_lifecycle_legs():
    """F6: Legs to Negociando/Sin Respuesta/Contratado exist"""
    # En Proceso → Negociando
    t1 = evaluate_transition({"Status": "En Proceso"}, "progreso_negociacion", Actor.HUMANO)
    assert t1 is not None and t1.to_status == Status.NEGOCIANDO
    
    # Negociando → Sin Respuesta
    t2 = evaluate_transition({"Status": "Negociando"}, "sin_respuesta", Actor.HUMANO)
    assert t2 is not None and t2.to_status == Status.SIN_RESPUESTA
    
    # Negociando → Contratado
    t3 = evaluate_transition({"Status": "Negociando"}, "oferta_aceptada", Actor.HUMANO)
    assert t3 is not None and t3.to_status == Status.CONTRATADO


def test_f6_en_proceso_to_rechazado():
    """F6: En Proceso → Rechazado leg exists"""
    transition = evaluate_transition({"Status": "En Proceso"}, "rechazo_proceso", Actor.HUMANO)
    assert transition is not None
    assert transition.to_status == Status.RECHAZADO


def test_f6_exploratorio_transitions():
    """F6: Exploratorio transitions exist"""
    t1 = evaluate_transition({"Status": "Exploratorio"}, "promover_objetivo", Actor.HUMANO)
    assert t1 is not None and t1.to_status == Status.OBJETIVO
    
    t2 = evaluate_transition({"Status": "Exploratorio"}, "descartar", Actor.HUMANO)
    assert t2 is not None and t2.to_status == Status.RETIRADO


def test_f6_manual_rule():
    """F6: HUMANO(any→any within enum) = válido"""
    for status in Status:
        transition = evaluate_transition({"Status": status.value}, "manual_edit", Actor.HUMANO)
        assert transition is not None
        assert transition.actor == Actor.HUMANO


# ── F7: REVIEW Gate Design Tests ─────────────────────────────────────────────

def test_f7_review_gate_design():
    """F7: REVIEW gate designed with field parameter"""
    record = {"Status": "Por Revisar"}
    result = evaluate_review_gate(record, field="Status")
    
    assert result["decision"] == GateDecision.REVIEW
    assert result["suggested_resolution"] == Status.OBJETIVO.value
    assert result["action"] == "review_to_objetivo"


def test_f7_review_gate_blocked():
    """F7+G5/H2: REVIEW gate, safe default BLOCKED (wiring deferred)"""
    record = {"Status": "Contratado"}
    result = evaluate_review_gate(record, field="Score")
    
    # H2: Safe default BLOCKED while wiring deferred (G5)
    assert result["decision"] == GateDecision.BLOCKED
    assert result["action"] == "block_review_deferred"
    assert result["suggested_resolution"] == Status.OBJETIVO.value


# ── F8: Enum Literal Unification Tests ───────────────────────────────────────

def test_f8_single_literal_per_value():
    """F8: Single literal per enum value (Title Case ES)"""
    assert Status.POR_REVISAR.value == "Por Revisar"  # Not "Por revisar"
    assert Status.EN_PROCESO.value == "En Proceso"  # Not "En proceso"
    assert Status.SIN_RESPUESTA.value == "Sin Respuesta"  # Not "Sin respuesta"
    assert NextAction.PREPARACION_ENTREVISTA.value == "Preparación Entrevista"  # Not "Preparación entrevista"


# ── F10: Enum Enforcement Tests ─────────────────────────────────────────────

def test_f10_enum_enforcement():
    """F10: Status.is_valid validates, normalize_record converts unknown to REVIEW"""
    # Valid status
    assert Status.is_valid("Objetivo") is True
    
    # Invalid status
    assert Status.is_valid("InvalidStatus") is False
    
    # normalize_record converts invalid to REVIEW
    api_record = {
        "id": "test-001",
        "last_edited_by": {"object": "user", "id": "bot-integration"},
        "last_edited_time": "2026-09-01T12:00:00.000Z",
        "properties": {
            "Status": {"select": {"name": "InvalidStatus"}}
        }
    }
    flat = normalize_record(api_record)
    assert flat["Status"] == Status.POR_REVISAR.value
    assert flat["_original_invalid_status"] == "InvalidStatus"


# ── F11: Guard Regression Fix Tests ─────────────────────────────────────────

def test_f11_composite_guard():
    """F11: Guard = is_mutable (field-block deferred - see G3)"""
    # Protected status (Contratado) - should not be mutable
    record = {
        "Status": "Contratado",
        "last_edited_by_id": "human-user-123",
        "last_edited_time": "2026-09-10T12:00:00.000Z"
    }
    assert not is_mutable(record, Actor.PIPELINE)
    
    # Manual edit - should not be mutable
    record = {
        "Status": "Objetivo",
        "last_edited_by_id": "human-user-123",
        "last_edited_time": "2026-09-10T12:00:00.000Z"
    }
    assert not is_mutable(record, Actor.PIPELINE)
    
    # Operational not touched - should be mutable
    record = {
        "Status": "Objetivo",
        "last_edited_by_id": "bot-integration",
        "last_edited_time": "2026-09-01T12:00:00.000Z"
    }
    assert is_mutable(record, Actor.PIPELINE)


# ── F12: Survivor Ranking Tests ──────────────────────────────────────────────

def test_f12_contratado_first():
    """F12: Contratado first in survivor priority"""
    assert SURVIVOR_PRIORITY[0] == Status.CONTRATADO
    assert get_survivor_rank("Contratado") == 0


def test_f12_choose_survivor():
    """F12: choose_survivor with complete logic"""
    records = [
        {"Status": "Objetivo", "Score": 50, "URL": "https://example.com", "layer": 1},
        {"Status": "Contratado", "Score": 90, "URL": "https://example.com", "layer": 1},
        {"Status": "Postulado", "Score": 80, "URL": None, "layer": 2}
    ]
    
    survivor = choose_survivor(records)
    assert survivor["Status"] == "Contratado"  # First priority


def test_g2_execute_transition_payload():
    """G2: execute_transition includes Next_Action for archive transitions"""
    record = {
        "Status": "Objetivo",
        "Notas": "Existing notes"
    }
    
    # Find url_failed transition
    transition = None
    for t in LIFECYCLE_MATRIX:
        if t.event == "url_failed":
            transition = t
            break
    
    assert transition is not None
    
    payload = execute_transition(record, transition, "test evidence")
    
    # Should include Status, Next_Action, and Notes
    assert "Status" in payload
    assert "Next_Action" in payload
    assert "Notas" in payload
    assert payload["Next_Action"] == NextAction.ARCHIVAR.value
    assert "Existing notes" in payload["Notas"]  # Appended


def test_g2_execute_transition_with_propose_log():
    """G2: Direct test of execute_transition_with_propose_log"""
    record = {
        "Status": "Objetivo",
        "last_edited_by_id": "bot-integration",
        "last_edited_time": "2026-09-01T12:00:00.000Z"
    }
    
    # Find url_failed transition
    transition = None
    for t in LIFECYCLE_MATRIX:
        if t.event == "url_failed":
            transition = t
            break
    
    assert transition is not None
    
    # Test auto-execute on operational (not touched by human)
    result = execute_transition_with_propose_log(record, transition, "test evidence", dry_run=False)
    
    # Should execute and return full payload
    assert "Status" in result
    assert "Next_Action" in result
    assert "Notas" in result


# ── F4: Diff Tests ───────────────────────────────────────────────────────────

def test_f4_diff_with_type_preservation():
    """F4: Diff preserves types (numeric vs string)"""
    old = {"Score": 42, "Status": "Objetivo"}
    new = {"Score": "42", "Status": "Objetivo"}  # String vs number
    
    changes = diff_records(old, new)
    
    # Should detect difference due to type mismatch
    assert "Score" in changes  # 42 (int) vs "42" (str) are different


# ── F2: Single Archive Path Tests ───────────────────────────────────────────

def test_f2_single_archive_path():
    """F2: UN camino evaluate → propose/execute → archive_gate"""
    record = {
        "Status": "Objetivo",
        "last_edited_by_id": "bot-integration",
        "last_edited_time": "2026-09-01T12:00:00.000Z"
    }
    
    # Evaluate flow
    flow_result = evaluate_flow(record, Actor.PIPELINE)
    assert flow_result["decision"] == "COMPUTE"
    
    # Archive gate
    archive_result = archive_gate(record, "url_failed", "test evidence", Actor.PIPELINE, "2026-09-10T12:00:00.000Z")
    assert archive_result["Status"] == Status.EXPIRADA.value
    assert archive_result["Next_Action"] == NextAction.ARCHIVAR.value


# ── Protected Status Tests ─────────────────────────────────────────────────

def test_protected_statuses():
    """Test protected status constants"""
    assert Status.CONTRATADO in PROTECTED_STATUSES
    assert Status.POSTULADO in PROTECTED_STATUSES
    assert Status.EXPIRADA in TERMINAL_STATUSES
    assert Status.RECHAZADO in TERMINAL_STATUSES


# ── Notion Fake Tests ───────────────────────────────────────────────────────

def test_notion_fake_mirror_api():
    """A5: Notion fake mirrors client.pages.update"""
    fake = NotionClientFake()
    
    # Test pages.update
    result = fake.pages_update("test-001", {"Status": {"select": {"name": "Objetivo"}}})
    assert result["id"] == "test-001"
    assert fake.get_update_count() == 1
    
    # Test pages.retrieve
    retrieved = fake.pages_retrieve("test-001")
    assert retrieved is not None
    assert retrieved["id"] == "test-001"


# ── Integration Tests ────────────────────────────────────────────────────────

def test_end_to_end_normalize_to_archive():
    """Integration: normalize → evaluate → archive"""
    # API record
    api_record = {
        "id": "test-001",
        "last_edited_by": {"object": "user", "id": "bot-integration"},
        "last_edited_time": "2026-09-01T12:00:00.000Z",
        "properties": {
            "Status": {"select": {"name": "Objetivo"}},
            "Score": {"number": 30},
            "URL": {"url": "https://deadlink.example.com"}
        }
    }
    
    # Normalize
    flat = normalize_record(api_record)
    assert flat["Status"] == "Objetivo"
    
    # Evaluate
    flow = evaluate_flow(flat, Actor.PIPELINE)
    assert flow["decision"] == "COMPUTE"
    
    # Archive
    archive = archive_gate(flat, "url_failed", "dead link", Actor.PIPELINE, "2026-09-10T12:00:00.000Z")
    assert archive["Status"] == Status.EXPIRADA.value


def test_fixture_loading():
    """Test fixture file can be loaded"""
    fixture_path = Path(__file__).parent / "fixtures" / "tracker_fixture.json"
    with open(fixture_path) as f:
        fixtures = json.load(f)
    
    assert len(fixtures) == 15  # A5: ≥15 filas
    
    # Test first fixture
    first = fixtures[0]
    assert first["id"] == "test-001"
    assert first["properties"]["Status"]["select"]["name"] == "Contratado"


# ── H3/H7: Arena Micro-Fix Tests (V3.1.1) ─────────────────────────────────────

def test_h3_fake_pages_chain():
    """H3: fake.pages.update/retrieve mirror client.pages.* chain."""
    fake = NotionClientFake()
    result = fake.pages.update(page_id="chain-001", properties={"Status": {"select": {"name": "Objetivo"}}})
    assert result["id"] == "chain-001"
    assert result["properties"]["Status"] == {"select": {"name": "Objetivo"}}
    assert fake.get_update_count() == 1
    retrieved = fake.pages.retrieve(page_id="chain-001")
    assert retrieved is not None
    assert retrieved["id"] == "chain-001"
    assert retrieved["last_edited_by"] == {"object": "user", "id": "fake-bot-id"}


def test_h7_url_tiebreak_prefers_url():
    """H7: survivor tiebreak prefers record WITH url (was inverted)."""
    records = [
        {"Status": "Objetivo", "Score": 50, "URL": None, "layer": 1},
        {"Status": "Objetivo", "Score": 50, "URL": "https://example.com", "layer": 1},
    ]
    survivor = choose_survivor(records)
    assert survivor["URL"] == "https://example.com"


def test_h7_coverage_map_complete():
    """H7/A5: every test in this module is mapped test↔finding-ID (no drift)."""
    names = sorted(n for n, v in globals().items() if n.startswith("test_") and callable(v))
    unmapped = [n for n in names if n not in COVERAGE_MAP]
    assert not unmapped, f"tests sin mapa: {unmapped}"
    stale = [k for k in COVERAGE_MAP if k not in names]
    assert not stale, f"mapa con entradas obsoletas: {stale}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
