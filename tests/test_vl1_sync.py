"""
Tests para vl1_sync.py — T6 sidecar reactivo (HANDOFF_T6_VL1S_SIDECAR_2026-09-11).

3 tests: default=dry-run, dry-run no escribe (NotionClientFake + data_sources
mock), apply-gate respeta el flag (bloquea antes de tocar Notion).
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "Layer_1" / "scripts"))
sys.path.insert(0, str(Path(__file__).parent / "mocks"))

from vl1_sync import main, ReadOnlyNotionClient, _NoWritePages  # noqa: E402
from notion_fake import NotionClientFake  # noqa: E402


def _fake_data_source_response(rows):
    return {"results": rows, "has_more": False, "next_cursor": None}


def test_default_is_dry_run(monkeypatch, capsys):
    """Sin --apply ni --dry-run explícito, el runner opera en modo dry-run
    (no intenta construir token/cliente real fuera de este flujo dry-run)."""
    monkeypatch.setenv("NOTION_TOKEN", "fake-token-for-test")

    fake_real_client = MagicMock()
    fake_real_client.data_sources.query.return_value = _fake_data_source_response([])

    monkeypatch.setattr("vl1_sync.build_real_client", lambda token: fake_real_client)

    exit_code = main([])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "DRY-RUN" in out
    assert "0 filas a sincronizar" in out


def test_dry_run_never_writes_even_with_discrepancy(monkeypatch, capsys):
    """Garantía estructural: aunque haya una fila con discrepancia real
    (Outcome=Contratado, Status≠Contratado), --dry-run NO debe ejecutar
    ningún pages.update real — solo el proxy _NoWritePages lo registra."""
    monkeypatch.setenv("NOTION_TOKEN", "fake-token-for-test")

    row_with_discrepancy = {
        "id": "page-abc123",
        "properties": {
            "Outcome": {"select": {"name": "Contratado"}},
            "Status": {"select": {"name": "En Proceso"}},
        },
    }

    fake_real_client = MagicMock()
    fake_real_client.data_sources.query.return_value = _fake_data_source_response(
        [row_with_discrepancy]
    )
    # Centinela: si algo llamara pages.update en el cliente REAL, esto lo delataría.
    fake_real_client.pages.update.side_effect = AssertionError(
        "pages.update real NO debe invocarse en dry-run"
    )

    monkeypatch.setattr("vl1_sync.build_real_client", lambda token: fake_real_client)

    exit_code = main(["--dry-run"])

    assert exit_code == 0
    fake_real_client.pages.update.assert_not_called()
    out = capsys.readouterr().out
    assert "HABRÍAN sido escritas" in out or "habrían sido escritas" in out.lower()


def test_apply_gate_blocks_before_any_notion_call(monkeypatch, capsys):
    """--apply está gateado en T6: debe bloquear con exit!=0 ANTES de
    construir ningún cliente de Notion (ni siquiera leer el token)."""

    def _should_not_be_called(*_a, **_kw):
        raise AssertionError("get_notion_token no debe llamarse cuando --apply está gateado")

    monkeypatch.setattr("vl1_sync.get_notion_token", _should_not_be_called)
    monkeypatch.setattr("vl1_sync.build_real_client", _should_not_be_called)

    exit_code = main(["--apply"])

    assert exit_code != 0
    out = capsys.readouterr().out
    assert "GATE" in out
    assert "no está habilitado" in out
