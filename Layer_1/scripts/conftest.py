"""Fase 1 fix: aísla el state file real (state/last_successful_run.json)
de la suite de tests. Sin esto, cualquier test que invoque
run_orchestrator() de verdad escribe en Layer_1/scripts/state/ y
contamina los tests que corren después en la misma sesión pytest
(V-01 secondary effect, Arena verdict).

NOTA: se deja el tmp state dir VACÍO a propósito (no poblado). 4 tests
preexistentes (test_f2_url_manual_protection_objetivo,
test_manual_first_human_edit_after_run_immunity,
test_manual_first_unknown_id_human,
test_transversal_manual_window_last_gate_run) usan fixtures con
last_edited_time de hace años y dependían implícitamente de que el
state file real (commiteado, con timestamp reciente) sacara la
comparación del fallback de 7 días de tracker_flow.py. Ver hallazgo
"fixtures con fecha vieja dependen de state file real" — no se
corrige aquí: requiere decidir si se actualizan las fechas del
fixture o se cambia el fallback, y ambas opciones tocan más código
del que cubre Fase 1."""
import os
import pytest


@pytest.fixture(autouse=True)
def _isolate_vantage_state_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("VANTAGE_STATE_DIR", str(tmp_path / "state"))
