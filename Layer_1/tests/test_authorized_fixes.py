"""
Tests for the authorized P0 batch:
  - infer_layer L2 typo
  - _extract_text_prop module-level helper (3-arg signature)
  - Dedup_Flag / layer upgrade Status guard
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

os.environ.setdefault("NOTION_TOKEN", "test-token")
os.environ.setdefault("NOTION_DB_OPPORTUNITIES", "test-db")
os.environ.setdefault("NOTION_ARCHIVE_PAGE_ID", "test-archive")

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from backfill_class_a import infer_layer
from feed_processor import (
    NotionSchema,
    _extract_text_prop,
    _set_dedup_flag_if_needed,
    _upgrade_layer_if_needed,
    should_mutate_existing_page,
)


def _rt(*chunks: str) -> dict:
    return {"type": "rich_text", "rich_text": [{"plain_text": c} for c in chunks]}


def _title(*chunks: str) -> dict:
    return {"type": "title", "title": [{"plain_text": c} for c in chunks]}


def _sel(name: str | None) -> dict:
    return {"type": "select", "select": {"name": name} if name else None}


def _url(value: str) -> dict:
    return {"type": "url", "url": value}


def _schema() -> NotionSchema:
    return NotionSchema(properties={
        "Rol": {"type": "title"},
        "Marca": {"type": "rich_text"},
        "Status": {"type": "select"},
        "layer": {"type": "select"},
        "hash": {"type": "rich_text"},
        "Dedup_Flag": {"type": "select"},
        "location": {"type": "rich_text"},
        "URL": {"type": "url"},
    })


def _page(status: str, layer: str = "L3", page_id: str = "abcd1234-xxxx") -> dict:
    return {
        "id": page_id,
        "properties": {
            "Status": _sel(status),
            "layer": _sel(layer),
            "Dedup_Flag": _sel(""),
            "Rol": _title("VM Coordinator"),
            "Marca": _rt("Gucci"),
        },
    }


# ---------------------------------------------------------------------------
# infer_layer
# ---------------------------------------------------------------------------

class TestInferLayer:
    def test_already_set_is_preserved(self):
        for layer in ("L1", "L2", "L3"):
            result = infer_layer({"layer": _sel(layer)})
            assert result == (layer, "ya_seteado"), layer

    def test_notes_layer_l2_returns_l2(self):
        props = {"Notas": _rt("ingesta layer: l2 desde feed"), "layer": _sel("")}
        assert infer_layer(props) == ("L2", "notas_layer")

    def test_notes_layer_l3_returns_l3(self):
        props = {"Notas": _rt("layer: l3"), "layer": _sel("")}
        assert infer_layer(props) == ("L3", "notas_layer")

    def test_notes_feed_semanal_defaults_l1(self):
        props = {"Notas": _rt("feed semanal 2026-08-01"), "layer": _sel("")}
        assert infer_layer(props) == ("L1", "notas_feed")

    def test_raw_email_subject_is_l3(self):
        props = {"Raw Email Subject": _rt("Nueva vacante VM"), "layer": _sel("")}
        assert infer_layer(props) == ("L3", "raw_email_subject")

    def test_linkedin_url_is_l3(self):
        props = {"URL": _url("https://www.linkedin.com/jobs/view/123"), "layer": _sel("")}
        assert infer_layer(props) == ("L3", "linkedin_url")

    def test_mail_fuente_is_l2(self):
        props = {"Fuente": _sel("Indeed"), "layer": _sel("")}
        assert infer_layer(props) == ("L2", "fuente_indeed")

    def test_default_is_l1(self):
        assert infer_layer({"layer": _sel("")}) == ("L1", "default")


# ---------------------------------------------------------------------------
# _extract_text_prop
# ---------------------------------------------------------------------------

class TestExtractTextProp:
    def test_concatenates_rich_text_chunks(self):
        row = {"properties": {"JD": _rt("Hola ", "mundo")}}
        assert _extract_text_prop(row, "JD") == "Hola mundo"

    def test_concatenates_title_chunks(self):
        row = {"properties": {"Rol": _title("Visual ", "Merchandiser")}}
        assert _extract_text_prop(row, "Rol") == "Visual Merchandiser"

    def test_select(self):
        row = {"properties": {"Status": _sel("Target")}}
        assert _extract_text_prop(row, "Status") == "Target"

    def test_url(self):
        row = {"properties": {"URL": _url("https://example.com")}}
        assert _extract_text_prop(row, "URL") == "https://example.com"

    def test_missing_prop_returns_default(self):
        assert _extract_text_prop({"properties": {}}, "location", "n/a") == "n/a"

    def test_empty_prop_name_returns_default(self):
        assert _extract_text_prop({"properties": {}}, "", "x") == "x"

    def test_three_arg_call_does_not_typeerror(self):
        row = {"properties": {"location": _rt("CDMX")}}
        assert _extract_text_prop(row, "location", "") == "CDMX"

    def test_three_arg_missing_location_uses_default(self):
        row = {"properties": {}}
        assert _extract_text_prop(row, "location", "") == ""


# ---------------------------------------------------------------------------
# should_mutate_existing_page + write guards
# ---------------------------------------------------------------------------

class TestShouldMutateExistingPage:
    def test_target_is_mutable(self):
        assert should_mutate_existing_page(_page("Target"), _schema()) is True

    def test_en_proceso_is_not_mutable(self):
        assert should_mutate_existing_page(_page("En proceso"), _schema()) is False

    def test_postulado_is_not_mutable(self):
        assert should_mutate_existing_page(_page("Postulado"), _schema()) is False

    def test_rechazado_is_not_mutable(self):
        assert should_mutate_existing_page(_page("Rechazado"), _schema()) is False


class TestDedupFlagGuard:
    def test_skips_write_on_protected_status(self):
        client = MagicMock()
        _set_dedup_flag_if_needed(client, _page("En proceso"), _schema())
        client.pages.update.assert_not_called()

    def test_writes_on_target(self):
        client = MagicMock()
        _set_dedup_flag_if_needed(client, _page("Target"), _schema())
        client.pages.update.assert_called_once()
        payload = client.pages.update.call_args.kwargs
        assert payload["properties"]["Dedup_Flag"]["select"]["name"] == "Posible duplicado"


class TestLayerUpgradeGuard:
    def test_skips_upgrade_on_postulado(self):
        client = MagicMock()
        _upgrade_layer_if_needed(_page("Postulado", layer="L3"), "L1", client, _schema())
        client.pages.update.assert_not_called()

    def test_upgrades_target_from_l3_to_l1(self):
        client = MagicMock()
        _upgrade_layer_if_needed(_page("Target", layer="L3"), "L1", client, _schema())
        client.pages.update.assert_called_once()
        payload = client.pages.update.call_args.kwargs
        assert payload["properties"]["layer"]["select"]["name"] == "L1"
