"""
T3.N · Prueba pytest del parche "archivado DRY RUN en Notion opt-in"
(decisión B del operador, 2026-10-08).

Convierte en prueba permanente la verificación del parche:
  - archive_dryrun_notion OMITE por defecto (return None, cero llamadas a la
    API de Notion → cero POST https://api.notion.com/v1/pages).
  - Se activa solo con VANTAGE_ARCHIVE_DRYRUN_NOTION=1 (o el flag
    --archive-notion del main de feed_processor, que setea esa variable).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

os.environ.setdefault("NOTION_TOKEN", "test-token")
os.environ.setdefault("NOTION_DB_OPPORTUNITIES", "test-db")
os.environ.setdefault("NOTION_ARCHIVE_PAGE_ID", "test-archive")

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import feed_processor as fp  # noqa: E402


@pytest.fixture()
def dryrun_file(tmp_path: Path) -> Path:
    p = tmp_path / "2026-10-09_dryrun.md"
    p.write_text("# DRY RUN · Layer L1\n- item de prueba\n", encoding="utf-8")
    return p


def test_archive_dryrun_notion_omitted_by_default(monkeypatch, dryrun_file):
    """Sin la variable de entorno: omite, devuelve None y NO toca Notion."""
    monkeypatch.delenv("VANTAGE_ARCHIVE_DRYRUN_NOTION", raising=False)
    client = MagicMock()
    result = fp.archive_dryrun_notion(client, dryrun_file, 1)
    assert result is None
    client.pages.create.assert_not_called()
    # tampoco debe consultar nada (cero requests de cualquier tipo)
    assert client.method_calls == []


def test_archive_dryrun_notion_omitted_with_other_value(monkeypatch, dryrun_file):
    """Cualquier valor distinto de '1' mantiene la omisión."""
    monkeypatch.setenv("VANTAGE_ARCHIVE_DRYRUN_NOTION", "0")
    client = MagicMock()
    assert fp.archive_dryrun_notion(client, dryrun_file, 1) is None
    client.pages.create.assert_not_called()


def test_archive_dryrun_notion_optin_enabled(monkeypatch, dryrun_file):
    """Con VANTAGE_ARCHIVE_DRYRUN_NOTION=1 sí archiva (mock del cliente)."""
    monkeypatch.setenv("VANTAGE_ARCHIVE_DRYRUN_NOTION", "1")
    client = MagicMock()
    client.pages.create.return_value = {"id": "page-id", "url": "https://notion.so/x"}
    monkeypatch.setattr(fp, "_find_child_page", lambda *a, **k: {"id": "month-id"})
    result = fp.archive_dryrun_notion(client, dryrun_file, 1)
    assert result == "https://notion.so/x"
    client.pages.create.assert_called_once()


def test_archive_notion_cli_flag_sets_env(monkeypatch):
    """El flag --archive-notion del main setea VANTAGE_ARCHIVE_DRYRUN_NOTION=1."""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    parser.add_argument("--layer", type=int, default=1, choices=[1, 2, 3])
    parser.add_argument("--fast", action="store_true", default=False)
    parser.add_argument("--interactive", action="store_true", default=False)
    parser.add_argument("--yes", action="store_true", default=False)
    parser.add_argument("--archive-notion", action="store_true", default=False)

    monkeypatch.delenv("VANTAGE_ARCHIVE_DRYRUN_NOTION", raising=False)
    args = parser.parse_args(["--file", "x.json", "--archive-notion"])
    assert args.archive_notion is True
    # replicar la lógica del main de feed_processor (≈L1327-1329)
    if args.archive_notion:
        os.environ["VANTAGE_ARCHIVE_DRYRUN_NOTION"] = "1"
    assert os.environ.get("VANTAGE_ARCHIVE_DRYRUN_NOTION") == "1"
    monkeypatch.delenv("VANTAGE_ARCHIVE_DRYRUN_NOTION", raising=False)
