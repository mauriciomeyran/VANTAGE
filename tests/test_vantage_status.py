"""Tests for Layer_1/scripts/vantage_status.py (Fase 3)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "Layer_1" / "scripts"))

from vantage_status import (  # noqa: E402
    LEGACY_STATUS_MAP,
    normalize_status,
    is_terminal_status,
    is_protected_status,
    is_mutable_status,
    gate_protected_value,
)

# ── normalize_status ──────────────────────────────────────────────────────────

def test_normalize_canonical():
    assert normalize_status("Expirada") == "Expirada"
    assert normalize_status("Rechazado") == "Rechazado"
    assert normalize_status("Objetivo") == "Objetivo"

def test_normalize_legacy_mapped():
    assert normalize_status("Archivar") == "Expirada"
    assert normalize_status("Target") == "Objetivo"
    assert normalize_status("Blocked") == "Rechazado"
    assert normalize_status("REVIEW_NEEDED") == "Por Revisar"
    assert normalize_status("Sin respuesta") == "Sin Respuesta"

def test_normalize_legacy_unmapped():
    assert normalize_status("Repetida") == "Repetida"

def test_normalize_unknown_passthrough():
    assert normalize_status("FooBar") == "FooBar"
    assert normalize_status("") == ""
    assert normalize_status(None) == ""

# ── is_terminal_status ────────────────────────────────────────────────────────

def test_terminal_canonical():
    assert is_terminal_status("Expirada") is True
    assert is_terminal_status("Rechazado") is True
    assert is_terminal_status("Retirado") is True
    assert is_terminal_status("Objetivo") is False
    assert is_terminal_status("Por Revisar") is False

def test_terminal_legacy_mapped():
    assert is_terminal_status("Archivar") is True
    assert is_terminal_status("Blocked") is True

def test_terminal_legacy_unmapped():
    assert is_terminal_status("Repetida") is False
    assert is_terminal_status("Target") is False

def test_terminal_empty():
    assert is_terminal_status("") is False
    assert is_terminal_status(None) is False  # type: ignore

# ── is_protected / is_mutable ─────────────────────────────────────────────────

def test_protected_and_mutable_inverse():
    protected_samples = ["Expirada", "Rechazado", "Retirado", "Archivar", "Blocked"]
    for s in protected_samples:
        assert is_protected_status(s) is True
        assert is_mutable_status(s) is False

    mutable_samples = ["Objetivo", "Por Revisar", "Repetida", "Target"]
    for s in mutable_samples:
        assert is_protected_status(s) is False
        assert is_mutable_status(s) is True

def test_protected_empty():
    assert is_protected_status("") is False
    assert is_mutable_status("") is True

# ── gate_protected_value ──────────────────────────────────────────────────────

def test_gate_protected_canonical():
    assert gate_protected_value({"Status": "Postulado", "id": "abc12345"}) == "APPLIED"
    assert gate_protected_value({"Status": "Rechazado", "id": "abc12345"}) == "REJECTED"
    assert gate_protected_value({"Status": "Expirada", "id": "abc12345"}) == "EXPIRADA"
    assert gate_protected_value({"Status": "Retirado", "id": "abc12345"}) == "EXPIRADA"

def test_gate_protected_legacy():
    assert gate_protected_value({"Status": "Archivar", "id": "abc12345"}) == "EXPIRADA"
    assert gate_protected_value({"Status": "Blocked", "id": "abc12345"}) == "REJECTED"

def test_gate_not_protected():
    assert gate_protected_value({"Status": "Objetivo", "id": "abc12345"}) is None
    assert gate_protected_value({"Status": "Repetida", "id": "abc12345"}) is None
    assert gate_protected_value({"Status": "Target", "id": "abc12345"}) is None
    assert gate_protected_value({"Status": "", "id": "abc12345"}) is None
    assert gate_protected_value({}) is None
