"""
test_prompt_canon.py — PROMPT_CANON verificador (Fase 3C+)

Invariantes I1..I22 del diseño. Tests offline salvo los de git, que usan el
repositorio real (V6' no se puede mockear: su valor ES probar el binding real).

KERNEL:NAM-ID-CONTRACT §12.1 + V | PROMPT CANON
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "Layer_1" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import verify_versions as vv  # noqa: E402

PROMPT_CANON_UUID = "3f0938be-fc42-813a-9215-c6a1a716c3b7"
LINKEDIN_SHA = "f7fa0513d591a1dbf5c2cf30851e82803d9816e5"
LINKEDIN_PATH = "Layer_1/scripts/linkedin_identity_matcher.py"


def _row(pid="PromptA-v2.0+linkedin", status="CANONICAL", **over):
    """Fila con la forma REAL de la API de Notion (properties anidadas)."""
    props = {
        "Prompt ID": {"type": "title", "title": [{"plain_text": pid}]},
        "Status": {"type": "select", "select": {"name": status}},
        "Version": {"type": "rich_text", "rich_text": [{"plain_text": "v2.0"}]},
        "Contract": {"type": "url", "url": "https://app.notion.com/p/3f0938befc4281218028e49b9c36694c"},
        "Rules": {"type": "url", "url": "https://app.notion.com/p/3f0938befc42816290d0df7dee92e78a"},
        "Query Set": {"type": "url", "url": "https://app.notion.com/p/3f0938befc42816c80ddeb156a4f94ce"},
        "Output Schema": {"type": "url", "url": "https://app.notion.com/p/3f0938befc4281569f36ed0842918690"},
        "Tests": {"type": "url", "url": "https://app.notion.com/p/3f0938befc42813a9215c6a1a716c3b7"},
        "Implementation SHA": {"type": "rich_text", "rich_text": [{"plain_text": LINKEDIN_SHA}]},
        "Implementation Path": {"type": "rich_text", "rich_text": [{"plain_text": LINKEDIN_PATH}]},
        "Promoted At": {"type": "date", "date": {"start": "2026-10-05"}},
        "Evidence": {"type": "url", "url": None},
        "Supersedes": {"type": "rich_text", "rich_text": []},
    }
    for k, v in over.items():
        if v is None:
            props.pop(k, None)
        elif isinstance(v, dict) and "type" in v:
            props[k] = v
    return {"properties": props}


def _run(monkeypatch, rows):
    """Ejecuta verify_prompt_canon con data source simulado."""
    monkeypatch.setattr(vv, "query_data_source",
                        lambda c, d, h, p: ({"results": rows}, None))
    monkeypatch.setattr(vv, "safe_http_get",
                        lambda c, u, h, params=None: type(
                            "R", (), {"status_code": 200})())
    return vv.verify_prompt_canon(None, {}, PROMPT_CANON_UUID, REPO)


# ─────────────────────────────── I1, I2, I4, I5  (registry / config)

def test_i1_registry_entry_is_uuid_string():
    """I1 — document_registry[PROMPT_CANON] es string UUID, no objeto."""
    reg = json.loads((REPO / "Layer_1" / "data" / "resolver_registry_v2.json").read_text())
    val = reg["document_registry"]["PROMPT_CANON"]
    assert isinstance(val, str), "debe ser string, no dict"
    assert val == PROMPT_CANON_UUID


def test_i2_key_resolves_without_dashes(tmp_path):
    """I2 — load_document_uuids() resuelve y quita guiones."""
    reg = {"document_registry": {"PROMPT_CANON": PROMPT_CANON_UUID}}
    p = tmp_path / "r.json"
    p.write_text(json.dumps(reg))
    uuids = vv.load_document_uuids(p)
    assert uuids["PROMPT_CANON"] == PROMPT_CANON_UUID.replace("-", "")


def test_i3_absent_authority_fails_hard(tmp_path):
    """I3 — ausencia = FAIL de infraestructura, no warning."""
    reg = {"document_registry": {}}
    p = tmp_path / "r.json"
    p.write_text(json.dumps(reg))
    uuids = vv.load_document_uuids(p)
    assert uuids["PROMPT_CANON"] is None, "no debe inventar un UUID"
    res = vv.verify_prompt_canon(None, {}, uuids["PROMPT_CANON"], REPO)
    assert res["status"] == "FAIL_INFRASTRUCTURE"
    assert res["findings"][0][1] == "V1"
    assert "FAIL_DATA" not in [f[0] for f in res["findings"]]


def test_i4_no_fallback_constant():
    """I4 — no debe existir constante de fallback para PROMPT_CANON."""
    assert not hasattr(vv, "PROMPT_CANON_FALLBACK_ID"), \
        "PROMPT_CANON no puede degradar a fallback fijo"


def test_i5_key_in_doc_keys():
    assert "PROMPT_CANON" in vv.DOC_KEYS


# ─────────────────────────────── I8, I9, I19  (integridad de fila)

def test_i8_canonical_row_complete(monkeypatch):
    res = _run(monkeypatch, [_row()])
    assert res["status"] == "PASS"
    assert not [f for f in res["findings"] if f[1] == "V3"]


def test_i8b_canonical_row_missing_field_fails(monkeypatch):
    """I8 — fila CANONICAL sin campo primario → FAIL_DATA."""
    bad = _row()
    bad["properties"]["Implementation SHA"] = {"type": "rich_text", "rich_text": []}
    res = _run(monkeypatch, [bad])
    assert res["status"] == "FAIL_DATA"
    assert any(f[1] == "V3" for f in res["findings"])


def test_i9_status_enum_closed(monkeypatch):
    """I9 — Status fuera del enum cerrado → FAIL_DATA."""
    res = _run(monkeypatch, [_row(status="DRAFT")])
    assert res["status"] == "FAIL_DATA"
    assert any(f[1] == "V5" for f in res["findings"])


def test_i9b_candidate_status_is_valid(monkeypatch):
    """I9 — CANDIDATE es válido; no dispara V5."""
    res = _run(monkeypatch, [_row(status="CANDIDATE")])
    assert not [f for f in res["findings"] if f[1] == "V5"]


def test_i19_no_placeholder_rows(monkeypatch):
    """I19 — una fila sin paquete contractual no se considera CANONICAL."""
    res = _run(monkeypatch, [])
    assert res["rows"] == 0
    assert res["status"] == "PASS", "registry vacío es válido"


# ─────────────────────────────── I10, I11, I12, I13  (provenance git)

def test_i10_sha_is_40_hex(monkeypatch):
    bad = _row()
    bad["properties"]["Implementation SHA"] = {
        "type": "rich_text", "rich_text": [{"plain_text": "abc123"}]}
    res = _run(monkeypatch, [bad])
    assert res["status"] == "FAIL_DATA"
    assert any(f[1] == "V6" for f in res["findings"])


def test_i11_sha_resolves_in_git():
    """I11 — SHA real resuelve."""
    ok, why = vv.verify_provenance_git(LINKEDIN_SHA, LINKEDIN_PATH, REPO)
    assert ok, why
    bad, _ = vv.verify_provenance_git("0" * 40, LINKEDIN_PATH, REPO)
    assert not bad


def test_i12_sha_binds_to_path():
    """I12 — el SHA debe VINCULAR al path (git show SHA:path)."""
    ok, _ = vv.verify_provenance_git(LINKEDIN_SHA, LINKEDIN_PATH, REPO)
    assert ok, "path debe existir en ese commit"
    # SHA válido de OTRO commit donde ese path no existe.
    other = subprocess.run(["git", "log", "--format=%H", "-1", "--before=2026-10-04"],
                           cwd=str(REPO), capture_output=True, text=True).stdout.strip()
    if other and other != LINKEDIN_SHA:
        bad, why = vv.verify_provenance_git(other, LINKEDIN_PATH, REPO)
        assert not bad, f"binding roto: {other} no contiene {LINKEDIN_PATH} ({why})"


def test_i13_path_exists_on_disk():
    assert (REPO / LINKEDIN_PATH).exists()


# ─────────────────────────────── I14  (contradicciones)

def test_i14_single_canonical_per_prompt(monkeypatch):
    """I14 — dos CANONICAL para el mismo Prompt ID → FAIL_DATA."""
    res = _run(monkeypatch, [_row(), _row()])
    assert res["status"] == "FAIL_DATA"
    assert any(f[1] == "V7" for f in res["findings"])


# ─────────────────────────────── I15, I16  (artefactos)

def test_i15_artifact_without_page_id_fails(monkeypatch):
    """I15 — artefacto sin page_id extraíble → FAIL_DATA."""
    bad = _row()
    bad["properties"]["Contract"] = {"type": "url", "url": "no-es-una-url"}
    res = _run(monkeypatch, [bad])
    assert res["status"] == "FAIL_DATA"
    assert any(f[1] == "V4" for f in res["findings"])


def test_i16_no_md5_required(monkeypatch):
    """I16 — V4' NO exige MD5: fila con URLs válidas y sin hash pasa."""
    res = _run(monkeypatch, [_row()])
    v4 = [f for f in res["findings"] if f[1] == "V4"]
    assert not v4, f"V4 no debe exigir MD5: {v4}"


# ─────────────────────────────── I17  (coverage)

def test_i17_partial_coverage_still_passes(monkeypatch):
    """I17 — 1/4 cobertura es PASS + reporte, nunca FAIL."""
    res = _run(monkeypatch, [_row()])
    assert res["status"] == "PASS"
    assert res["coverage"]["linkedin"] == 1
    assert res["coverage"]["aggregators"] == 0
    assert res["coverage"]["gemini"] == 0
    assert sum(res["coverage"].values()) == 1


def test_i17b_empty_registry_is_pass(monkeypatch):
    """I17 — cobertura 0/4 con autoridad presente también es PASS."""
    res = _run(monkeypatch, [])
    assert res["status"] == "PASS"
    assert sum(res["coverage"].values()) == 0


# ─────────────────────────────── I18  (no almacena texto)

def test_i18_registry_has_no_prompt_body():
    """I18 — el registro no debe embebir texto de prompts."""
    reg = json.loads((REPO / "Layer_1" / "data" / "resolver_registry_v2.json").read_text())
    val = reg["document_registry"]["PROMPT_CANON"]
    assert len(val) < 100, "el valor debe ser sólo el UUID, no cuerpo del prompt"


# ─────────────────────────────── I20  (end-to-end de la fila real)

def test_i20_linkedin_row_passes(monkeypatch):
    """I20 — la fila real de f7fa051 pasa V3, V5', V6', V7."""
    res = _run(monkeypatch, [_row()])
    assert res["status"] == "PASS", res["findings"]
    checks = {f[1] for f in res["findings"]}
    assert not (checks & {"V3", "V5", "V6", "V7"})


# ─────────────────────────────── I21, I22  (census intacto)

def test_i21_not_in_census():
    """I21 — PROMPT_CANON NO debe estar en generate_census.py."""
    src = (SCRIPTS / "generate_census.py").read_text()
    assert "PROMPT_CANON" not in src, \
        "PROMPT_CANON es registro de estado; census descubre vía DOCUMENTS"
    assert "PROMPT_CANON" not in src.split("VALID_PREFIXES")[1].split(")")[0]


def test_i22_census_untouched():
    """I22 — DOCUMENTS / VALID_PREFIXES / DOC_PRIORITY intactos."""
    src = (SCRIPTS / "generate_census.py").read_text()
    assert '"System Prompt": "37b938be' in src
    assert '"Project Charter": "f87938be' in src
    assert len(src.split("VALID_PREFIXES = (")[1].split(")")[0].split(",")) == 8
