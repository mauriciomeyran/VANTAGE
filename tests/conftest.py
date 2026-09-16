"""Fase 1 fix: aísla el state file real (state/last_successful_run.json)
de la suite de tests. Sin esto, cualquier test que invoque
run_orchestrator() de verdad escribe en Layer_1/scripts/state/ y
contamina los tests que corren después en la misma sesión pytest
(V-01 secondary effect, Arena verdict)."""
import os
import pytest


@pytest.fixture(autouse=True)
def _isolate_vantage_state_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("VANTAGE_STATE_DIR", str(tmp_path / "state"))
