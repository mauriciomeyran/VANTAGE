"""
G3 paridad — harness viejo (layer_1_run) vs nuevo (layer_1_orchestrator).

Cero Notion: fixtures + fake. Diff vacío salvo allowlist justificada.
≥15 filas, todas las ramas de decisión relevantes.
"""

from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "Layer_1" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import layer_1_run as old  # noqa: E402
import layer_1_orchestrator as new  # noqa: E402
from tracker_flow import (  # noqa: E402
    Actor,
    Status,
    normalize_record,
    is_mutable,
    PROTECTED_STATUSES,
)
from gate_logic import gate_logic  # noqa: E402


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "g3_parity_fixture.json"

# Campos comparables entre viejo y nuevo (decision table)
COMPARE_KEYS = (
    "Score",
    "Gate_Decision",
    "Next_Action",
    "VM_Scope",
    "Role_Class",
    "archive",  # bool: ¿se archiva Status→Expirada?
    "protected",  # bool: ¿se salta mutación?
)

# Allowlist de diffs justificados (entrada×campo o wildcard).
# Cada entrada DEBE tener reason ≥8 chars. No silenciar regresiones nuevas.
#
# DECISION: tracker_flow.is_mutable protege LIVE_APPLICATION_STATUSES +
# TERMINAL + manual-first. layer_1_run solo protege via gate_logic
# (Postulado/Rechazado/Expirada) y recalcula Score/Gate en En Proceso/
# Negociando/Sin Respuesta. El contrato §0/§2 manda is_mutable único —
# el nuevo es la fuente de verdad; el delta vs viejo se documenta aquí.
ALLOWLIST: Dict[tuple, str] = {
    # Live apps no-terminales: nuevo protege (is_mutable); viejo etiqueta APPLIED y recalcula Score
    ("g3-003-en-proceso", "Score"): "new: LIVE protected no recalc; old Fase3 recalcula",
    ("g3-003-en-proceso", "Gate_Decision"): "new: is_mutable LIVE skip; old gate_logic omite En Proceso y etiqueta APPLIED",
    ("g3-003-en-proceso", "Next_Action"): "new: is_mutable LIVE skip; old set Interview prep",
    ("g3-003-en-proceso", "protected"): "new: PROTECTED_STATUSES includes En Proceso; old no",
    ("g3-016-negociando", "Score"): "new: LIVE protected no recalc; old recalcula",
    ("g3-016-negociando", "Gate_Decision"): "new: is_mutable LIVE skip; old etiqueta APPLIED",
    ("g3-016-negociando", "Next_Action"): "new: is_mutable LIVE skip; old set Follow-up",
    ("g3-016-negociando", "protected"): "new: PROTECTED_STATUSES includes Negociando; old no",
    ("g3-017-sin-respuesta", "Score"): "new: LIVE protected no recalc; old recalcula",
    ("g3-017-sin-respuesta", "Gate_Decision"): "new: is_mutable LIVE skip; old etiqueta APPLIED",
    ("g3-017-sin-respuesta", "Next_Action"): "new: is_mutable LIVE skip; old set Follow-up",
    ("g3-017-sin-respuesta", "protected"): "new: PROTECTED_STATUSES includes Sin Respuesta; old no",
    # Rechazado: gate_logic viejo retorna REJECTED y Fase4 SÍ etiqueta (excepción);
    # is_mutable nuevo bloquea actor!=HUMANO en terminales → protected sin label write
    ("g3-004-rechazado", "Score"): "new: terminal protected no recalc; old recalcula antes de label",
    ("g3-004-rechazado", "Gate_Decision"): "new: is_mutable terminal skip write; old set REJECTED label",
    ("g3-004-rechazado", "Next_Action"): "new: is_mutable terminal skip write; old set Post-Mortem",
    ("g3-004-rechazado", "protected"): "new: TERMINAL in PROTECTED_STATUSES; old procesa label REJECTED",
    # Manual-first §0: humano reciente inmune; viejo archivaría por URL tracking + NAD
    ("g3-018-human-recent-immune", "Next_Action"): "new: manual-first immunity; old would Archivar",
    ("g3-018-human-recent-immune", "archive"): "new: manual-first immunity; old archives tracking URL",
    ("g3-018-human-recent-immune", "protected"): "new: _was_touched_by_human; old no manual window",
}


def load_fixture() -> List[Dict[str, Any]]:
    with open(FIXTURE_PATH) as f:
        data = json.load(f)
    assert len(data) >= 15, f"G3 requiere ≥15 filas, got {len(data)}"
    return data


def _flat(api_record: Dict[str, Any]) -> Dict[str, Any]:
    return normalize_record(deepcopy(api_record))


# ── Pure function parity ─────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "role",
    [
        "",
        "x",
        "Visual Merchandising Manager",
        "Store Design Lead",
        "Brand Experience Producer",
        "Sales Associate",
        "Intern",
        "Creative Director",
    ],
)
def test_g3_parity_vm_scope(role):
    assert new.get_vm_scope(role) == old.get_vm_scope(role)


@pytest.mark.parametrize(
    "role",
    [
        "",
        "Visual Merchandiser",
        "Brand Experience Producer",
        "Trade Marketing Lead",
        "Software Engineer",
        "VM Coordinator",
    ],
)
def test_g3_parity_role_class(role):
    assert new.get_role_class(role) == old.get_role_class(role)


@pytest.mark.parametrize(
    "entry",
    [
        {},
        {"title": "VM Manager", "company": "Zara", "jd": "visual store", "contact": "a@b.c"},
        {"title": "Intern", "company": "Unknown", "jd": "", "contact": ""},
        {"title": "Creative Lead", "company": "Auditoire", "jd": "brand experience", "contact": "x"},
        {"title": "Store Manager", "company": "Nike", "jd": "retail", "contact": ""},
        {"title": "Designer", "company": "Louis Vuitton", "jd": "luxury visual merchandising", "contact": "r@l.com"},
    ],
)
def test_g3_parity_score_v64(entry):
    # new accepts both shapes
    new_score = new.calculate_score_v6({
        "Rol": entry.get("title", ""),
        "Marca": entry.get("company", ""),
        "JD": entry.get("jd", ""),
        "Contacto": entry.get("contact", ""),
    })
    old_score = old.calculate_score_v6(entry)
    assert new_score == old_score


@pytest.mark.parametrize(
    "kwargs",
    [
        {"fetch": "Accesible", "vm_scope": "Alto", "role_class": "VM", "source_type": "Vacante", "score": 70, "rol": "VM", "marca": "Zara"},
        {"fetch": "Accesible", "vm_scope": "Alto", "role_class": "VM", "source_type": "Vacante", "score": 50, "rol": "VM", "marca": "Zara"},
        {"fetch": "Accesible", "vm_scope": "Alto", "role_class": "VM", "source_type": "Vacante", "score": 30, "rol": "VM", "marca": "Zara"},
        {"fetch": "Accesible", "vm_scope": "Bajo", "role_class": "Otro", "source_type": "Vacante", "score": 80, "rol": "Intern", "marca": "X"},
        {"fetch": "Bloqueado", "vm_scope": "Alto", "role_class": "VM", "source_type": "Vacante", "score": 80, "rol": "VM", "marca": "Zara"},
        {"fetch": "Accesible", "vm_scope": "Bajo", "role_class": "Otro", "source_type": "Inbound", "score": 0, "rol": "Any", "marca": "Y"},
        {"fetch": "Accesible", "vm_scope": "Alto", "role_class": "VM", "source_type": "Vacante", "score": None, "rol": "VM", "marca": "Zara"},
        {"fetch": "Parcial", "vm_scope": "Alto", "role_class": "VM", "source_type": "Vacante", "score": 65, "rol": "VM", "marca": "Nike"},
    ],
)
def test_g3_parity_gate_function(kwargs):
    assert new.gate(**kwargs) == old.gate(**kwargs)


@pytest.mark.parametrize(
    "status",
    ["Postulado", "En proceso", "En Proceso", "Negociando", "Sin respuesta", "Sin Respuesta", "Objetivo", "Rechazado"],
)
def test_g3_parity_application_status(status):
    # old uses "En proceso" / "Sin respuesta" (legacy casing)
    old_app = old.evaluate_application_status(status)
    new_app = new.evaluate_application_status(status)
    # New accepts both casings; old only lowercase-proceso variants
    if status in ("En Proceso", "Sin Respuesta"):
        # Documented delta: new accepts Title Case ES enum values
        assert new_app is True
        ALLOWLIST.setdefault(("*", f"app_status:{status}"), "new accepts Title Case ES Status enum")
    else:
        assert new_app == old_app


@pytest.mark.parametrize(
    "status",
    ["Postulado", "En proceso", "Negociando", "Sin respuesta", "Objetivo"],
)
def test_g3_parity_application_next_action(status):
    assert new.get_application_next_action(status) == old.get_application_next_action(status)


# ── Decision table: old pure sim vs new apply_gate_decision ──────────────────

def _old_decide(flat: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simula decisiones puras de layer_1_run Fases 2–4 SIN red ni writes.
    Espejo fiel de la lógica de main() sobre un record plano.
    """
    status = flat.get("Status", "") or ""
    source_type = flat.get("Source_Type ", "") or flat.get("Source_Type", "") or "Vacante"
    url = flat.get("URL", "") or ""
    jd = flat.get("JD", "") or ""
    fetch = flat.get("Fetch", "") or ""
    rol = flat.get("Rol", "") or ""
    marca = flat.get("Marca", "") or ""
    current_action = flat.get("Next_Action", "") or ""
    current_gate = flat.get("Gate_Decision", "") or ""
    jd_quality = flat.get("JD_Quality", "") or ""
    nad = flat.get("NAD", "") or ""

    out: Dict[str, Any] = {
        "id": flat.get("id"),
        "Score": flat.get("Score"),
        "Gate_Decision": current_gate or None,
        "Next_Action": current_action or None,
        "VM_Scope": flat.get("VM_Scope") or old.get_vm_scope(rol),
        "Role_Class": flat.get("Role_Class") or old.get_role_class(rol),
        "archive": False,
        "protected": False,
    }

    # Terminal / protected by status list (Fase 2 skip + Fase 4 skip)
    if status in ("Expirada", "Archivar", "Contratado", "Retirado"):
        out["protected"] = True
        return out

    # gate_logic terminal (Fase 3/4)
    gl = gate_logic({
        "Status": status,
        "Next_Action": current_action,
        "Gate_Decision": current_gate,
        "Fetch": fetch,
        "id": flat.get("id", ""),
    })
    if gl is not None and gl != "REJECTED":
        out["protected"] = True
        out["Gate_Decision"] = gl if gl in ("APPLIED", "REJECTED") else current_gate or None
        return out

    # URL gate (Fase 2) — offline
    from url_gate import validate_url_offline
    if source_type == "Vacante" and url:
        if status not in ("Expirada", "Rechazado", "Archivar", "Contratado", "Postulado"):
            # Target+JD bypass removed (Target=0); JD bypass still applies
            ok, reason = validate_url_offline(url, jd)
            if not ok and status not in ("Postulando",):
                # direct fail → archive (agregador always ok offline)
                out["archive"] = True
                out["Gate_Decision"] = None
                out["Next_Action"] = "Archivar"
                return out

    # NAD expired (Fase 3.5.1)
    if nad and status not in ("Expirada", "Archivar", "Postulado", "Rechazado", "Contratado", "Postulando", "En Proceso", "Negociando", "Sin Respuesta"):
        try:
            from datetime import datetime
            if datetime.strptime(str(nad)[:10], "%Y-%m-%d") < datetime.now():
                out["archive"] = True
                out["Next_Action"] = "Archivar"
                return out
        except ValueError:
            pass

    # Score (Fase 3)
    if source_type in ("Inbound", "Referencia", "Networking"):
        score = flat.get("Score") if flat.get("Score") is not None else 0
    else:
        score = old.calculate_score_v6({
            "title": rol, "company": marca, "jd": jd, "contact": flat.get("Contacto") or "",
        })
    out["Score"] = score

    # Fase 4 gate
    if old.evaluate_rejection_status(status):
        decision, next_action = "REJECTED", "Post-Mortem"
    elif old.evaluate_application_status(status) or status in ("En Proceso", "Sin Respuesta"):
        # Title Case variants: map to old casing for next_action
        status_for_na = status
        if status == "En Proceso":
            status_for_na = "En proceso"
        if status == "Sin Respuesta":
            status_for_na = "Sin respuesta"
        if old.evaluate_application_status(status_for_na) or status in ("En Proceso", "Sin Respuesta"):
            decision = "APPLIED"
            next_action = old.get_application_next_action(status_for_na)
        else:
            decision = old.gate(fetch, out["VM_Scope"], out["Role_Class"], source_type, score=score, rol=rol, marca=marca)
            next_action = "Investigar"
    elif jd_quality == "JD Completo":
        decision = old.gate(fetch, out["VM_Scope"], out["Role_Class"], source_type, score=score, rol=rol, marca=marca)
        if decision == "CREATE":
            next_action = "Optimizar"
        elif decision == "REVIEW_NEEDED":
            next_action = "Investigar"
        else:
            next_action = "Optimizar"
    else:
        decision = old.gate(fetch, out["VM_Scope"], out["Role_Class"], source_type, score=score, rol=rol, marca=marca)
        if decision == "CREATE":
            next_action = "Re-check"
        elif decision == "REVIEW_NEEDED":
            next_action = "Investigar"
        elif source_type == "Vacante" and fetch == "Bloqueado":
            next_action = "Reparar URL"
        elif source_type == "Vacante" and fetch == "Parcial":
            next_action = "Verificar JD"
        else:
            next_action = "Investigar"

    out["Gate_Decision"] = decision
    out["Next_Action"] = next_action
    return out


def _new_decide(flat: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decisiones del orquestador nuevo sobre record plano (sin client).

    Espejo de run_orchestrator: is_mutable/manual-first cortan mutación
    destructiva; no se recalcula Score ni se archiva en protegidos.
    """
    status = flat.get("Status", "") or ""
    source_type = flat.get("Source_Type ", "") or flat.get("Source_Type", "") or "Vacante"
    url = flat.get("URL", "") or ""
    jd = flat.get("JD", "") or ""
    rol = flat.get("Rol", "") or ""
    nad = flat.get("NAD", "") or ""

    out: Dict[str, Any] = {
        "id": flat.get("id"),
        "Score": flat.get("Score"),
        "Gate_Decision": flat.get("Gate_Decision") or None,
        "Next_Action": flat.get("Next_Action") or None,
        "VM_Scope": flat.get("VM_Scope") or new.get_vm_scope(rol),
        "Role_Class": flat.get("Role_Class") or new.get_role_class(rol),
        "archive": False,
        "protected": False,
    }

    # Manual / is_mutable — corte destructivo (contrato §0/§2)
    if not is_mutable(flat, Actor.PIPELINE) or not new.manual_first_protection(flat, Actor.PIPELINE):
        out["protected"] = True
        # Score se preserva (no recalc)
        return out

    # URL
    ok, reason = new.validate_url(url, source_type, jd_text=jd)
    if not ok and not reason.startswith("AGREGADOR_RETRY"):
        out["archive"] = True
        out["Next_Action"] = "Archivar"
        return out

    # NAD
    if nad:
        try:
            from datetime import datetime
            if datetime.strptime(str(nad)[:10], "%Y-%m-%d") < datetime.now():
                out["archive"] = True
                out["Next_Action"] = "Archivar"
                return out
        except ValueError:
            pass

    # Score
    if source_type in ("Inbound", "Referencia", "Networking"):
        score = flat.get("Score") if flat.get("Score") is not None else 0
    else:
        score = new.calculate_score_v6(flat)
    out["Score"] = score

    gate_result = new.apply_gate_decision(
        {**flat, "VM_Scope": out["VM_Scope"], "Role_Class": out["Role_Class"]},
        score,
    )
    if gate_result.get("decision") in ("PROTECTED", "TERMINAL"):
        out["protected"] = True
        return out
    out["Gate_Decision"] = gate_result.get("Gate_Decision")
    out["Next_Action"] = gate_result.get("Next_Action")
    return out


def test_g3_fixture_size():
    rows = load_fixture()
    assert len(rows) >= 15


def test_g3_parity_decision_table_all_rows():
    """
    G3 core: por cada fila del fixture, old_decide == new_decide
    en COMPARE_KEYS, salvo ALLOWLIST justificada entrada×campo.
    """
    rows = load_fixture()
    diffs = []

    for api in rows:
        flat = _flat(api)
        # Inject Last_Gate_Run from props if present as date string already in flat
        old_d = _old_decide(flat)
        new_d = _new_decide(flat)

        for key in COMPARE_KEYS:
            ov, nv = old_d.get(key), new_d.get(key)
            if ov == nv:
                continue
            allow = ALLOWLIST.get((flat.get("id"), key)) or ALLOWLIST.get(("*", key))
            if allow:
                continue
            diffs.append({
                "id": flat.get("id"),
                "field": key,
                "old": ov,
                "new": nv,
                "status": flat.get("Status"),
            })

    assert diffs == [], f"G3 parity diffs (no allowlist):\n" + "\n".join(
        f"  {d['id']} {d['field']}: old={d['old']!r} new={d['new']!r} (Status={d['status']})"
        for d in diffs
    )


def test_g3_parity_orchestrator_run_fake_no_notion():
    """G3: run_orchestrator sobre fixture ≥15 con fake — cero Notion, sin crash."""
    rows = load_fixture()
    client = new.NotionClientFake()
    client.query_data_sources = Mock(return_value={"results": rows})

    metrics = new.run_orchestrator(
        client=client, dry_run=False, apply=True, dedup_audit=True
    )

    assert metrics["total_processed"] == len(rows)
    assert metrics["errors"] == 0
    assert metrics["patterns"] is not None
    # Fake only — no real Notion
    assert all(w[0] == "pages_update" for w in client.writes)
    # Human-recent immune row should not be archived despite bad URL/NAD
    human_writes = [w for w in client.writes if w[1] == "g3-018-human-recent-immune"]
    # May be zero writes (protected) or none destructive
    for w in human_writes:
        props = w[2]
        assert props.get("Status") != Status.EXPIRADA.value


def test_g3_parity_protected_statuses_never_archived_by_new():
    """G3: Contratado/Postulado/etc. jamás Status=Expirada en writes del nuevo."""
    rows = load_fixture()
    client = new.NotionClientFake()
    client.query_data_sources = Mock(return_value={"results": rows})
    new.run_orchestrator(client=client, dry_run=False, apply=True, dedup_audit=False)

    protected_ids = {
        r["id"] for r in rows
        if (r.get("properties", {}).get("Status", {}).get("select") or {}).get("name")
        in {s.value for s in PROTECTED_STATUSES}
    }
    for op, pid, props in client.writes:
        if pid in protected_ids and "Status" in props:
            assert props["Status"] != Status.EXPIRADA.value, f"archived protected {pid}"


def test_g3_parity_score_band_create_review_block():
    """G3: bandas Score CREATE≥60 / REVIEW 40-59 / BLOCKED <40 idénticas."""
    for score, expected in [(70, "CREATE"), (60, "CREATE"), (50, "REVIEW_NEEDED"), (40, "REVIEW_NEEDED"), (39, "BLOCKED")]:
        kwargs = dict(
            fetch="Accesible", vm_scope="Alto", role_class="VM",
            source_type="Vacante", score=score, rol="Visual Merchandiser", marca="Zara",
        )
        assert old.gate(**kwargs) == expected
        assert new.gate(**kwargs) == expected


def test_g3_allowlist_is_documented():
    """G3: toda entrada ALLOWLIST tiene reason no vacío."""
    for key, reason in ALLOWLIST.items():
        assert isinstance(reason, str) and len(reason) >= 8, f"allowlist {key} sin justificación"
