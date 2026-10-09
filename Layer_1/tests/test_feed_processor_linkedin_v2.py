"""
T3.M · Tests del normalizador LinkedIn v2.0 en feed_processor.normalize_envelope.

Cubre (contrato CS-ARENA-L1-01 §4 T-A.7):
  - detección del envelope v2.0 (accepted/reroute/rejected/not_evaluated + contract|schema)
  - solo accepted[] produce records
  - mapeo employer_identity→company, location_observed→location, source/source_type
    según convención del baseline v1.0 (feeds/2026-10-04_linkedin.json),
    conservación de evidence_observed y jd ausente → ""
  - ValueError citando job_id ante status inconsistente, campos faltantes o
    employer_identity con forma inesperada (decisión del operador 2026-10-09, opción b)
  - envelope v1.0 (top-level "jobs") sigue rechazado, con el mensaje original como prefijo
  - regresión de las 4 formas existentes (results_by_source, listings,
    consolidated_results, lista simple)

Fixture: Layer_1/tests/fixtures/linkedin_v2_synthetic.json (SINTÉTICO, no va en feeds/).
"""

from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("NOTION_TOKEN", "test-token")
os.environ.setdefault("NOTION_DB_OPPORTUNITIES", "test-db")
os.environ.setdefault("NOTION_ARCHIVE_PAGE_ID", "test-archive")

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import feed_processor as fp  # noqa: E402

_FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "linkedin_v2_synthetic.json"


@pytest.fixture()
def envelope_v2() -> dict:
    return json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))


# ─────────────────────────────────────────────────────────────────────
# Detección v2.0
# ─────────────────────────────────────────────────────────────────────
def test_fixture_is_detected_as_v2(envelope_v2):
    assert fp.is_linkedin_v2_envelope(envelope_v2) is True


def test_detection_requires_four_arrays_as_lists():
    base = {"contract": "PromptA-v2.0+linkedin"}
    # Faltan arrays
    assert fp.is_linkedin_v2_envelope(base) is False
    # Arrays presentes pero uno no es lista
    bad = dict(base, accepted=[], reroute={}, rejected=[], not_evaluated=[])
    assert fp.is_linkedin_v2_envelope(bad) is False
    # Cuatro listas pero sin contract/schema
    no_key = {"accepted": [], "reroute": [], "rejected": [], "not_evaluated": []}
    assert fp.is_linkedin_v2_envelope(no_key) is False
    # Con "schema" en vez de "contract" también detecta
    ok = dict(no_key, schema="LINKEDIN-OUTPUT-SCHEMA-002")
    assert fp.is_linkedin_v2_envelope(ok) is True


def test_detection_rejects_non_dict():
    assert fp.is_linkedin_v2_envelope([1, 2, 3]) is False
    assert fp.is_linkedin_v2_envelope("accepted") is False


# ─────────────────────────────────────────────────────────────────────
# Solo accepted[] produce records
# ─────────────────────────────────────────────────────────────────────
def test_only_accepted_produces_records(envelope_v2):
    records = fp.normalize_envelope(copy.deepcopy(envelope_v2), 1)
    assert len(records) == len(envelope_v2["accepted"]) == 2
    ingested_ids = {r["job_id"] for r in records}
    assert ingested_ids == {"SYN-ACC-0001", "SYN-ACC-0002"}
    # reroute/rejected/not_evaluated NO se ingestan
    for other in ("reroute", "rejected", "not_evaluated"):
        for item in envelope_v2[other]:
            assert item["job_id"] not in ingested_ids


def test_layer_tag_applied_to_v2_records(envelope_v2):
    records = fp.normalize_envelope(copy.deepcopy(envelope_v2), 1)
    assert all(r["layer"] == "L1" for r in records)


# ─────────────────────────────────────────────────────────────────────
# Mapeo
# ─────────────────────────────────────────────────────────────────────
def test_field_mapping(envelope_v2):
    records = fp.normalize_envelope(copy.deepcopy(envelope_v2), 1)
    first_src = envelope_v2["accepted"][0]
    r = next(x for x in records if x["job_id"] == first_src["job_id"])
    # employer_identity → company; location_observed → location
    assert r["company"] == first_src["employer_identity"] == "Benefit Cosmetics"
    assert r["location"] == first_src["location_observed"]
    # convención de provenance del baseline v1.0 (source/source_type = "linkedin")
    assert r["source"] == "linkedin"
    assert r["source_type"] == "linkedin"
    # evidence_observed se conserva
    assert r["evidence_observed"] == first_src["evidence_observed"]
    # url/title/job_id íntegros
    assert r["url"] == first_src["url"]
    assert r["title"] == first_src["title"]
    # jd ausente en v2.0 → ""
    assert r["jd"] == ""


def test_normalize_record_fields_on_v2_record(envelope_v2):
    records = fp.normalize_envelope(copy.deepcopy(envelope_v2), 1)
    norm = fp.normalize_record_fields(records[0])
    src = envelope_v2["accepted"][0]
    assert norm["brand_raw"] == src["employer_identity"]
    assert norm["apply_url"] == src["url"]
    assert norm["title"] == src["title"]
    assert norm["location"] == src["location_observed"]
    assert norm["job_id"] == src["job_id"]
    assert norm["jd"] == ""  # v2.0 no define jd; vacío tolerado (decisión C)
    assert norm["fetch_status"] in ("aggregator", "career_page")


# ─────────────────────────────────────────────────────────────────────
# Validación: fallos claros citando job_id, sin ingesta parcial
# ─────────────────────────────────────────────────────────────────────
def test_status_inconsistent_raises_citing_job_id(envelope_v2):
    env = copy.deepcopy(envelope_v2)
    env["accepted"][1]["status"] = "REROUTE"
    with pytest.raises(ValueError) as exc:
        fp.normalize_envelope(env, 1)
    assert "SYN-ACC-0002" in str(exc.value)
    assert "ACCEPTED" in str(exc.value)


def test_missing_required_fields_raise_citing_job_id(envelope_v2):
    for field in ("url", "title", "employer_identity"):
        env = copy.deepcopy(envelope_v2)
        env["accepted"][0].pop(field)
        with pytest.raises(ValueError) as exc:
            fp.normalize_envelope(env, 1)
        assert "SYN-ACC-0001" in str(exc.value), field
        assert field in str(exc.value)


def test_empty_required_string_raises(envelope_v2):
    env = copy.deepcopy(envelope_v2)
    env["accepted"][0]["employer_identity"] = "   "
    with pytest.raises(ValueError) as exc:
        fp.normalize_envelope(env, 1)
    assert "SYN-ACC-0001" in str(exc.value)


def test_employer_identity_unexpected_shape_raises(envelope_v2):
    # Decisión del operador 2026-10-09 (opción b): employer_identity es string;
    # cualquier otra forma → ValueError citando job_id, nunca marca vacía.
    env = copy.deepcopy(envelope_v2)
    env["accepted"][0]["employer_identity"] = {"name": "Benefit Cosmetics"}
    with pytest.raises(ValueError) as exc:
        fp.normalize_envelope(env, 1)
    assert "SYN-ACC-0001" in str(exc.value)
    assert "inesperada" in str(exc.value)


def test_location_observed_unexpected_shape_raises(envelope_v2):
    env = copy.deepcopy(envelope_v2)
    env["accepted"][0]["location_observed"] = {"city": "CDMX"}
    with pytest.raises(ValueError) as exc:
        fp.normalize_envelope(env, 1)
    assert "SYN-ACC-0001" in str(exc.value)


def test_non_dict_accepted_item_raises(envelope_v2):
    env = copy.deepcopy(envelope_v2)
    env["accepted"].append("no-soy-un-record")
    with pytest.raises(ValueError) as exc:
        fp.normalize_envelope(env, 1)
    assert "dict" in str(exc.value)


def test_no_partial_ingestion_on_error(envelope_v2):
    # El primer accepted es válido; el segundo tiene status inconsistente.
    # La función debe lanzar antes de devolver nada (no ingesta parcial).
    env = copy.deepcopy(envelope_v2)
    env["accepted"][1]["status"] = "REJECTED"
    with pytest.raises(ValueError):
        fp.normalize_envelope(env, 1)


# ─────────────────────────────────────────────────────────────────────
# v1.0 rechazado (mensaje original como prefijo)
# ─────────────────────────────────────────────────────────────────────
def test_v1_envelope_still_rejected_with_original_prefix():
    v1 = {
        "jobs": [{"title": "x", "company": "y", "apply_url": "https://e.com/1"}],
        "rejected_jobs": [],
        "not_evaluated": [],
        "audit_log": [],
        "search_summary": {},
    }
    with pytest.raises(ValueError) as exc:
        fp.normalize_envelope(v1, 1)
    msg = str(exc.value)
    assert msg.startswith(
        'Envelope no reconocido: se esperaba "results_by_source", '
        '"listings", "consolidated_results" o una lista.'
    )
    # ampliación permitida: referencia a LinkedIn v1.0/v2.0
    assert "jobs" in msg or "v2.0" in msg


# ─────────────────────────────────────────────────────────────────────
# Regresión: las 4 formas existentes de normalize_envelope
# ─────────────────────────────────────────────────────────────────────
def test_regression_results_by_source():
    env = {
        "results_by_source": {
            "workday": [{"title": "A", "company": "X"}],
            "otro": {"nested": [{"title": "B", "company": "Y"}]},
        }
    }
    records = fp.normalize_envelope(copy.deepcopy(env), 1)
    assert len(records) == 2
    assert all(r["layer"] == "L1" for r in records)


def test_regression_listings():
    env = {"listings": [{"title": "A"}, {"title": "B"}, {"title": "C"}]}
    records = fp.normalize_envelope(copy.deepcopy(env), 2)
    assert [r["title"] for r in records] == ["A", "B", "C"]
    assert all(r["layer"] == "L2" for r in records)


def test_regression_consolidated_results():
    env = {"consolidated_results": [{"title": "A"}]}
    records = fp.normalize_envelope(copy.deepcopy(env), 3)
    assert len(records) == 1 and records[0]["layer"] == "L3"


def test_regression_plain_list():
    records = fp.normalize_envelope([{"title": "A"}, {"title": "B"}], 1)
    assert len(records) == 2
    assert all(r["layer"] == "L1" for r in records)


def test_regression_existing_shapes_take_precedence_over_v2_keys():
    # Si un envelope trajera además "listings", la rama existente manda
    # (no se altera el comportamiento previo).
    env = {
        "listings": [{"title": "A"}],
        "accepted": [], "reroute": [], "rejected": [], "not_evaluated": [],
        "contract": "PromptA-v2.0+linkedin",
    }
    records = fp.normalize_envelope(copy.deepcopy(env), 1)
    assert [r["title"] for r in records] == ["A"]
