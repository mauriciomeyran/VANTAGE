"""Regresiones del DRY RUN fail-closed cuando falta NOTION_TOKEN."""

import importlib
import json
import os
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from layer_1_orchestrator import run_ingestion  # noqa: E402

ENV_KEYS = ("NOTION_TOKEN", "NOTION_DB_OPPORTUNITIES", "NOTION_ARCHIVE_PAGE_ID")

FEED = {
    "listings": [
        {
            "title": "Visual Merchandising Manager",
            "brand": "L'Oréal Luxe",
            "apply_url": "https://careers.loreal.com/job/vm-manager",
            "location": "CDMX",
            "jd": "VM manager for luxury retail.",
        },
        {
            "title": "Visual Merchandising Coordinator",
            "brand": "Nike",
            "apply_url": "https://jobs.nike.com/job/vm-coord",
            "location": "CDMX",
            "jd": "Coordinate VM guidelines for stores.",
        },
        {
            "title": "Sales Associate",
            "brand": "Zara",
            "apply_url": "https://jobs.zara.com/job/sales",
            "location": "CDMX",
            "jd": "Store sales associate.",
        },
    ]
}


def _write_feed(tmp_path, payload=FEED):
    path = tmp_path / "feed.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return str(path)


@pytest.fixture
def no_token_env(monkeypatch, tmp_path):
    """Entorno sin credenciales, import fresco y artefactos confinados a tmp_path."""
    import dotenv

    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **k: None)
    sys.modules.pop("feed_processor", None)

    # Preimportamos con las mismas condiciones sin token que usará el orquestador,
    # y confinamos el archivo DRY RUN temporal a tmp_path.
    module = importlib.import_module("feed_processor")
    monkeypatch.setattr(module, "_LAYER_1_ROOT", tmp_path)
    yield module
    sys.modules.pop("feed_processor", None)


def test_no_token_hard_blocks_and_exclusions_are_blocked(tmp_path, no_token_env):
    metrics = run_ingestion(_write_feed(tmp_path), layer=1, dry_run=True)

    assert metrics.get("error") is None
    assert metrics["total_records"] == 3
    assert metrics["clean"] == 0
    assert metrics["blocked"] == 2
    assert metrics["review_needed"] == 1
    assert metrics["warning"] == "no_token_fail_closed_dryrun"


def test_no_token_never_marks_unvalidated_record_clean(tmp_path, no_token_env):
    feed = {"listings": [FEED["listings"][1]]}
    metrics = run_ingestion(_write_feed(tmp_path, feed), layer=1, dry_run=True)

    assert metrics["clean"] == 0
    assert metrics["blocked"] == 0
    assert metrics["review_needed"] == 1
    assert metrics["candidates"] == 1


def test_no_token_creates_no_notion_client(tmp_path, monkeypatch, no_token_env):
    import notion_client

    def forbidden(*args, **kwargs):
        raise AssertionError("No debe construirse Notion Client sin token")

    monkeypatch.setattr(notion_client, "Client", forbidden)
    metrics = run_ingestion(_write_feed(tmp_path), layer=1, dry_run=True)

    assert metrics.get("error") is None
    assert metrics["dry_run"] is True
    assert metrics["written"] == 0


def test_no_token_apply_mode_is_refused(tmp_path, no_token_env):
    metrics = run_ingestion(_write_feed(tmp_path), layer=1, dry_run=False)

    assert metrics["error"] == "missing_token"
    assert metrics["written"] == 0


def test_import_restores_environment_even_if_dotenv_reinjects_token(monkeypatch):
    import dotenv

    before = {key: os.environ.get(key) for key in ENV_KEYS}
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    def reinject(*args, **kwargs):
        os.environ["NOTION_TOKEN"] = "injected-from-dotenv"
        os.environ["NOTION_DB_OPPORTUNITIES"] = "injected-db"
        os.environ["NOTION_ARCHIVE_PAGE_ID"] = "injected-archive"

    monkeypatch.setattr(dotenv, "load_dotenv", reinject)
    sys.modules.pop("feed_processor", None)
    try:
        importlib.import_module("feed_processor")
        assert os.environ.get("NOTION_TOKEN") is None
        assert os.environ.get("NOTION_DB_OPPORTUNITIES") is None
        assert os.environ.get("NOTION_ARCHIVE_PAGE_ID") is None
    finally:
        sys.modules.pop("feed_processor", None)
        for key, value in before.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
