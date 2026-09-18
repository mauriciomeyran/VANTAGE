#!/usr/bin/env python3
"""
VANTAGE Pipeline Orquestador v9.1 — Refactor completo + ingesta de feeds

Este orquestador reemplaza layer_1_run.py v8.0/v8.1 usando tracker_flow.py
como única fuente de verdad para decisiones de transición, y ahora también
absorbe la capacidad de ingesta de feed_processor.py.

Características:
- CLI compatible con layer_1_run.py (--dry-run default, --apply explícito)
- Soporte nativo de --file / --layer para ingesta de JSON de discovery
- Un solo re-query inicial + writes con diff (no write-churn)
- Fases lineales usando tracker_flow.py como core de decisión
- Prioridad manual respetada (is_mutable + last_edited_time)
- Dedup unificado con survivor canónico + guard is_mutable
- class_b_guard generalizado a TODAS las vías de escritura
- Flujo completo: feed JSON → pages.create (Class A) → Score/Gate/Prioridad (Class B)

Serial: DEVIN-20260912-01 → GROK-20260914-01 (ingesta integrada)
"""

import os
import sys
import argparse
import logging
import json
from datetime import datetime, date, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv

# Setup path for imports
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

from tracker_flow import (
    Status, NextAction, GateDecision, Actor, FetchResult, DedupFlag,
    normalize_record, is_mutable, evaluate_flow, archive_gate,
    LIFECYCLE_MATRIX, TERMINAL_STATUSES, LIVE_APPLICATION_STATUSES,
    PROTECTED_STATUSES, DELETED_VALUE_MAPPINGS, NORMALIZATION_TABLE,
    normalize_field_value, normalize_flat_record, SOURCE_TYPE_PROP_ALIASES,
    sync_status_from_outcome, apply_status_sync_writeback, run_outcome_status_sync,
    choose_survivor, get_layer_rank, diff_records, to_notion_properties,
    SOURCE_TYPE_VACANTE, SOURCE_TYPE_BYPASS,
)
from gate_logic import gate_logic
from priority_logic import infer_prioridad
from class_b_guard import (
    CLASS_A_FIELDS, CLASS_B_FIELDS, guard_write_payload, GuardResult,
)

# Reutilizar lógica de ingesta de feed_processor (Class A + pages.create)
# Import lazy dentro de run_ingestion para evitar side-effects de Client al importar.

# Actores Python autorizados a escribir Class B (cómputo del pipeline).
# MCP/humano = exención procedural (APROBAR_WRITE); no pasan por esta vía.
_PIPELINE_CLASS_B_ACTORS = {
    Actor.PIPELINE,
    Actor.DEDUP,
    Actor.INGESTA,
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
VANTAGE_DATA_SOURCE_ID = "442938be-fc42-828f-b72e-076818d65a5b"
VANTAGE_ARCHIVE_DATA_SOURCE_ID = os.environ.get("NOTION_ARCHIVE_DATA_SOURCE_ID", "674696fd-...")
ENABLE_DEDUP_AUDIT = os.environ.get("ENABLE_DEDUP_AUDIT", "true").lower() == "true"
DEDUP_WINDOW_DAYS = int(os.environ.get("DEDUP_WINDOW_DAYS", "60"))


class NotionClientFake:
    """Fake Notion client for dry-run mode (no actual API calls)"""
    def __init__(self):
        self.writes = []
        self.queries = []
        
    def query_data_sources(self, data_source_id: str, **kwargs) -> Dict[str, Any]:
        self.queries.append(("query_data_sources", data_source_id, kwargs))
        return {"results": []}
    
    def pages_update(self, page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        self.writes.append(("pages_update", page_id, properties))
        return {"id": page_id}


def validate_url(url: str, source_type: str, jd_text: str = "") -> tuple[bool, str]:
    """
    F2: URL Gate - paridad con layer_1_run.validate_url_pre_ingestion (offline).

    Returns (is_valid, reason).
    """
    if source_type in SOURCE_TYPE_BYPASS:
        return True, "BYPASS_SOURCE"

    from url_gate import validate_url_offline, is_agregador, normalize_url

    if not url:
        return False, "NO_URL"

    # Esquemas no-http explícitos → inválidos (antes de normalize)
    stripped = url.strip().lower()
    if "://" in stripped and not stripped.startswith(("http://", "https://")):
        return False, "INVALID_SCHEME"

    # JD largo = bypass (paridad viejo)
    if jd_text and isinstance(jd_text, str) and len(jd_text.strip()) > 100:
        return True, "JD_ALREADY_EXISTS"

    ok, reason = validate_url_offline(url, jd_text)
    if ok:
        return ok, reason

    if is_agregador(normalize_url(url) if url else ""):
        return True, "AGREGADOR_VALID"

    return ok, reason


def get_vm_scope(role_title: str) -> str:
    """F1.5: idéntico a layer_1_run.get_vm_scope."""
    if not role_title or len(role_title.strip()) < 3:
        return "Bajo"
    role_lower = role_title.lower()
    vm_terms = [
        "visual merchandising", "visual", "vm", "brand environment",
        "estándares visuales", "store design", "retail design",
    ]
    for term in vm_terms:
        if term in role_lower:
            return "Alto"
    return "Bajo"


def get_role_class(role_title: str) -> str:
    """F1.5: idéntico a layer_1_run.get_role_class."""
    if not role_title or len(role_title.strip()) < 3:
        return "Otro"
    role_lower = role_title.lower()
    vm_terms = ["visual merchandising", "visual", "vm", "brand environment"]
    for term in vm_terms:
        if term in role_lower:
            return "VM"
    pivot_terms = [
        "training", "experience", "producer", "brand experience",
        "retail design", "store design", "trade marketing", "shopper",
        "activation", "environment", "creative director", "creative lead",
    ]
    for term in pivot_terms:
        if term in role_lower:
            return "Pivote"
    return "Otro"


def calculate_score_v6(record: Dict[str, Any]) -> int:
    """
    F3: Scoring v6.4 — fórmula IDÉNTICA a layer_1_run.calculate_score_v6.

    Acepta plano (Rol/Marca/JD/Contacto) o entry legacy (title/company/jd/contact).
    """
    # Normalizar shape
    jd_text = (record.get("JD") or record.get("jd") or "") 
    jd_text = jd_text.lower() if isinstance(jd_text, str) else ""
    company = (record.get("Marca") or record.get("company") or "")
    company = company.lower() if isinstance(company, str) else ""
    title = (record.get("Rol") or record.get("title") or "")
    title = title.lower() if isinstance(title, str) else ""
    contact = record.get("Contacto") or record.get("contact") or ""

    score = 0

    # 1. BASE SCORE: +40 si pasó URL_GATE
    score += 40

    # 2. VISUAL_SIGNAL: +20
    visual_terms = [
        "visual", "diseño", "brand", "experience", "experiencia",
        "merchandising", "store", "tienda", "retail", "ambiente",
        "estándares", "guidelines", "portfolio", "creativo",
        "escenografía", "montaje", "exhibición", "pop", "punto de venta",
        "trade marketing", "shopper", "customer journey",
    ]
    if any(term in jd_text for term in visual_terms):
        score += 20

    # 3. COMPANY IMPACT: +15
    high_impact = [
        "nike", "apple", "inditex", "zara", "adidas",
        "lvmh", "kering", "richemont", "chanel", "hermès",
        "dior", "guerlain", "louis vuitton", "gentle monster",
        "grupo habita", "ben & frank", "auditoire", "another",
        "sephora", "massimo dutti", "ikea", "cartier", "on ",
        "on running", "aesop", "bershka", "stradivarius",
        "oysho", "pull&bear",
    ]
    if any(brand in company for brand in high_impact):
        score += 15

    # 4. ROLE QUALITY: +10
    quality_titles = [
        "manager", "coordinator", "lead", "jefe", "líder",
        "specialist", "expert", "designer", "architect",
    ]
    if any(role in title for role in quality_titles):
        score += 10

    # 5. RECRUITER PRESENCE: +10
    if contact or "contacto" in jd_text or "recruiter" in jd_text:
        score += 10

    # 6. INNOVATION / COOL DNA: +5
    innovative = [
        "gentle monster", "grupo habita", "ben & frank",
        "sede cafe", "auditoire", "another", "magnus",
        "aesop", "on running", "someone somewhere",
        "astound group", "minuto x minuto", "taste mkt",
        "alo yoga", "skims", "pop mart", "cyklar",
    ]
    if any(brand in company for brand in innovative):
        score += 5

    # 7. SCALE BONUS: +5
    scale_companies = ["lvmh", "inditex", "nike", "apple", "adidas", "sephora"]
    if any(brand in company for brand in scale_companies) and "manager" in title:
        score += 5

    # 8. PIVOT BONUS: +5
    pivot_roles = [
        "experience", "creative", "brand", "environment", "activation",
        "marketing", "trade", "shopper", "retail design", "store design",
    ]
    if any(role in title for role in pivot_roles):
        score += 5

    # 9. AGENCY BONUS: +5
    agency_names = [
        "auditoire", "another", "astound", "bisonte", "magnus",
        "minuto x minuto", "taste mkt", "astound group",
    ]
    if any(agency in company for agency in agency_names):
        score += 5

    # 10. LUXURY HERITAGE: +5
    luxury_pure = [
        "dior", "guerlain", "louis vuitton", "chanel", "hermès",
        "cartier", "fendi", "gucci", "bottega veneta",
    ]
    if any(maison in company for maison in luxury_pure):
        score += 5

    return min(score, 100)


def gate(
    fetch: str,
    vm_scope: str,
    role_class: str,
    source_type: str,
    score=None,
    rol: str = "",
    marca: str = "",
) -> str:
    """F4: idéntico a layer_1_run.gate — retorna GateDecision.value (cero strings sueltos)."""
    from profile_fit import has_vm_title_signal, is_role_excluded, resolve_alias_flags

    if is_role_excluded(rol) or resolve_alias_flags(marca)[0]:
        return GateDecision.BLOCKED.value
    if source_type in SOURCE_TYPE_BYPASS:
        return GateDecision.CREATE.value
    if source_type == SOURCE_TYPE_VACANTE:
        fetch_ok = fetch in (FetchResult.ACCESIBLE.value, FetchResult.PARCIAL.value)
        scope_ok = fetch_ok and (
            vm_scope == "Alto"
            or (role_class == "Pivote" and has_vm_title_signal(rol))
        )
        if not scope_ok:
            return GateDecision.BLOCKED.value
        if score is None:
            return GateDecision.REVIEW_NEEDED.value
        if score >= 60:
            return GateDecision.CREATE.value
        if score >= 40:
            return GateDecision.REVIEW_NEEDED.value
        return GateDecision.BLOCKED.value
    return GateDecision.BLOCKED.value


def evaluate_application_status(status: str) -> bool:
    """Paridad layer_1_run — acepta Title Case ES + casing legacy 'En proceso'/'Sin respuesta'."""
    if status in {
        Status.POSTULADO.value,
        Status.EN_PROCESO.value,
        Status.NEGOCIANDO.value,
        Status.SIN_RESPUESTA.value,
    }:
        return True
    # Legacy casing visto en layer_1_run (pre-enum)
    return status in {"En proceso", "Sin respuesta"}


def evaluate_rejection_status(status: str) -> bool:
    return status == Status.RECHAZADO.value


def get_application_next_action(status: str) -> str:
    """
    Next_Action para postulaciones vivas.

    G7: emite canónico ES (SEGUIMIENTO / PREPARACION_ENTREVISTA / REVISION).
    Legacy EN sigue en enum para lectura/migración; writers ya no lo emiten.
    Writers: siempre via enum .value — cero strings sueltos (G4).
    """
    if status == Status.POSTULADO.value:
        return NextAction.SEGUIMIENTO.value
    if status in (Status.EN_PROCESO.value, "En proceso"):
        return NextAction.PREPARACION_ENTREVISTA.value
    if status == Status.NEGOCIANDO.value:
        return NextAction.SEGUIMIENTO.value
    if status in (Status.SIN_RESPUESTA.value, "Sin respuesta"):
        return NextAction.SEGUIMIENTO.value
    return NextAction.REVISION.value


def apply_gate_decision(record: Dict[str, Any], score: int) -> Dict[str, Any]:
    """
    F4: Gate + Next_Action — paridad con layer_1_run Fase 4.

    Writers: GateDecision / NextAction enums only (G4 cero literales sueltos).

    Precedencia:
      1. evaluate_flow PROTECTED/TERMINAL (tracker_flow)
      2. gate_logic terminal map (Status/Next_Action)
      3. rejection / application status
      4. gate() + JD_Quality bandas
    """
    # Asegurar plano
    if "properties" in record:
        flat = normalize_record(record)
    else:
        flat = dict(record)

    status = flat.get("Status", "") or ""

    # Q-11: excepcion de una sola pasada -- SCHEMA-008 exige que Rechazado
    # produzca Gate_Decision=REJECTED + Next_Action=Post-Mortem. Sin esto,
    # is_mutable (TERMINAL incluye Rechazado post-G9) corta el flujo antes
    # de que esta etiqueta se escriba nunca. compute_write_diff garantiza
    # que esto escribe una sola vez: la 2a pasada ya trae Gate_Decision=
    # REJECTED y esta rama no vuelve a dispararse.
    if (
        status == Status.RECHAZADO.value
        and flat.get("Gate_Decision") != GateDecision.REJECTED.value
    ):
        return {
            "decision": "TERMINAL_LABEL",
            "reason": "Q-11: Rechazado label (single-pass, pre is_mutable cut)",
            "Gate_Decision": GateDecision.REJECTED.value,
            "Next_Action": NextAction.POST_MORTEM.value,
        }

    flow = evaluate_flow(flat, Actor.PIPELINE)
    if flow.get("decision") in ("PROTECTED", "TERMINAL"):
        return {
            "decision": flow["decision"],
            "reason": flow.get("reason", ""),
            "Gate_Decision": None,
            "Next_Action": None,
            "_flow": flow,
        }
    current_action = flat.get("Next_Action", "") or ""
    fetch = flat.get("Fetch", "") or ""
    vm_scope = flat.get("VM_Scope", "") or get_vm_scope(flat.get("Rol", "") or "")
    role_class = flat.get("Role_Class", "") or get_role_class(flat.get("Rol", "") or "")
    source_type = (
        flat.get("Source_Type ", "")
        or flat.get("Source_Type", "")
        or SOURCE_TYPE_VACANTE
    )
    rol = flat.get("Rol", "") or ""
    marca = flat.get("Marca", "") or ""
    jd_quality = flat.get("JD_Quality", "") or ""

    # gate_logic terminal protection (paridad KERNEL:GATE-DECISION-010)
    protected = gate_logic({
        "Next_Action": current_action,
        "Status": status,
        "Gate_Decision": flat.get("Gate_Decision", ""),
        "Fetch": fetch,
        "id": flat.get("id", ""),
    })
    if protected is not None and protected != GateDecision.REJECTED.value:
        gate_out = None
        if protected in (GateDecision.APPLIED.value, GateDecision.REJECTED.value):
            gate_out = protected
        else:
            gate_out = flat.get("Gate_Decision")
        return {
            "decision": "PROTECTED",
            "reason": f"gate_logic:{protected}",
            "Gate_Decision": gate_out,
            "Next_Action": current_action or None,
            "_protected": protected,
        }

    if evaluate_rejection_status(status):
        decision = GateDecision.REJECTED.value
        next_action = NextAction.POST_MORTEM.value
    elif evaluate_application_status(status):
        decision = GateDecision.APPLIED.value
        next_action = get_application_next_action(status)
    elif jd_quality == "JD Completo":
        decision = gate(fetch, vm_scope, role_class, source_type, score=score, rol=rol, marca=marca)
        if decision == GateDecision.CREATE.value:
            next_action = NextAction.OPTIMIZAR.value
        elif decision == GateDecision.REVIEW_NEEDED.value:
            next_action = NextAction.INVESTIGAR.value
        else:
            next_action = NextAction.OPTIMIZAR.value
    else:
        decision = gate(fetch, vm_scope, role_class, source_type, score=score, rol=rol, marca=marca)
        if decision == GateDecision.CREATE.value:
            next_action = NextAction.REVISION.value  # G7: was RE_CHECK (legacy EN)
        elif decision == GateDecision.REVIEW_NEEDED.value:
            next_action = NextAction.INVESTIGAR.value
        elif source_type == SOURCE_TYPE_VACANTE and fetch == FetchResult.BLOQUEADO.value:
            next_action = NextAction.REPARAR_URL.value
        elif source_type == SOURCE_TYPE_VACANTE and fetch == FetchResult.PARCIAL.value:
            next_action = NextAction.VERIFICAR_JD.value
        else:
            next_action = NextAction.INVESTIGAR.value

    return {
        "decision": decision,
        "Gate_Decision": decision,
        "Next_Action": next_action,
        "VM_Scope": vm_scope,
        "Role_Class": role_class,
        "Score": score,
    }


# ── H9: Snapshot Class B para field-level guard ──────────────────────────────
# Separado de last_successful_run.json (decisión operador 2026-09-15):
# archivos con propósito y tasa de cambio distintos no comparten storage.

CLASS_B_SNAPSHOT_FILE = "last_class_b_snapshot.json"


def load_class_b_snapshot() -> Dict[str, Dict[str, Any]]:
    """
    H9: Carga el snapshot de campos Class B tal como quedaron al final del
    run anterior. Retorna {} si no existe (primer run tras el fix, o fila
    nunca antes procesada) — caller trata ausencia como "sin baseline",
    nunca como "sin cambios".
    """
    state_file = Path(os.environ.get("VANTAGE_STATE_DIR") or (Path(__file__).resolve().parent / "state")) / CLASS_B_SNAPSHOT_FILE
    if not state_file.exists():
        return {}
    try:
        with open(state_file) as f:
            data = json.load(f)
            return data.get("records", {})
    except Exception as exc:
        logger.warning(f"[H9] Snapshot Class B ilegible ({exc}) — tratado como ausente")
        return {}


def save_class_b_snapshot(snapshot: List[Dict[str, Any]]) -> None:
    """
    H9 / Fase 2: Persiste los valores Class B de filas que REALMENTE
    recibieron evaluación Class B en este run, o que ya tenían baseline
    válido (Class_B_Last_Run presente).

    No registra como "computado" filas que fueron:
      protected / skipped / continue / REVIEW_NEEDED / terminal.
    El snapshot es baseline auxiliar; la fuente de verdad del estado
    Class B es Class_B_Last_Run en Notion.
    """
    # Cargar snapshot previo para preservar baselines de filas no tocadas
    # en este run (protegidas, etc.).
    previous = load_class_b_snapshot()
    records: Dict[str, Dict[str, Any]] = dict(previous)

    for record in snapshot:
        page_id = record.get("id")
        if not page_id:
            continue
        # Solo actualizar entrada si se computó Class B en este run
        # o si ya existe baseline y queremos refrescar valores.
        computed = record.get("_class_b_computed", False)
        has_baseline = bool(record.get("Class_B_Last_Run"))
        if not computed and not has_baseline:
            # Protected/skipped sin baseline previo: no inventar entrada.
            continue
        if not computed and page_id in previous:
            # Ya tenía baseline; mantener (no sobrescribir con valores
            # posiblemente stale de un run que no recalculó).
            continue
        records[page_id] = {k: record.get(k) for k in CLASS_B_FIELDS if k in record}

    state_dir = Path(os.environ.get("VANTAGE_STATE_DIR") or (Path(__file__).resolve().parent / "state"))
    state_dir.mkdir(exist_ok=True)
    state_file = state_dir / CLASS_B_SNAPSHOT_FILE
    state_file.write_text(json.dumps({
        "captured_at": datetime.now().isoformat(),
        "records": records,
    }))
    logger.info(f"[H9] Snapshot Class B actualizado: {state_file} ({len(records)} filas)")


def compute_last_edited_field(
    record: Dict[str, Any],
    previous_class_b: Dict[str, Dict[str, Any]],
) -> Optional[str]:
    """
    H9: Determina, lo mejor que los datos disponibles permiten, si la
    edición humana detectada tocó un campo Class A o Class B.

    Estrategia (conservadora, no inventa certeza que no existe):
    - Sin baseline previo para esta fila → None (fila nueva o snapshot no
      existía aún; is_mutable() trata None como "no confirmado Class A",
      protege Class B por defecto).
    - Si algún campo Class B difiere del snapshot anterior → retorna ese
      campo Class B (edición manual directa sobre Class B — inmuniza).
    - Si ningún campo Class B difiere → retorna un marcador de Class A
      genérico ("_class_a_touched"), suficiente para que is_mutable()
      permita el recálculo (solo necesita saber que NO fue Class B).

    No identifica CUÁL campo Class A cambió — el guard no lo necesita:
    is_mutable() solo pregunta "¿touched_field es Class A?", y para eso
    basta un marcador consistente. Devolver un nombre Class A inventado
    sería peor que un marcador honesto.
    """
    page_id = record.get("id")
    baseline = previous_class_b.get(page_id)

    if baseline is None:
        return None  # Sin baseline — conservador, no asumir Class A.

    for field_name in CLASS_B_FIELDS:
        if field_name not in baseline:
            continue  # Campo no capturado en el snapshot anterior — skip.
        if record.get(field_name) != baseline.get(field_name):
            return field_name  # Class B cambió directamente → ese es el campo tocado.

    return "_class_a_touched"  # Ningún Class B cambió → lo tocado fue Class A.


def needs_first_class_b_compute(record: Dict[str, Any]) -> bool:
    """
    Fase 2 GAP Class-B: True cuando el registro aún no tiene baseline de
    evaluación Class B exitosa (Class_B_Last_Run ausente/vacío).

    Ausencia de Class_B_Last_Run significa "primera evaluación pendiente",
    NO "protección manual". El caller debe combinar esto con elegibilidad
    de lifecycle (terminal, REVIEW_NEEDED, etc.).
    """
    val = record.get("Class_B_Last_Run", "")
    return not val


def manual_first_protection(record: Dict[str, Any], actor: Actor) -> bool:
    """
    §2.3 / G5: Ediciones manuales recientes = máxima prioridad.

    Fase 2: la ventana manual se evalúa contra Class_B_Last_Run (baseline
    de evaluación Class B exitosa), NO contra Last_Gate_Run.

    Semántica separada:
      - Class_B_Last_Run  = última evaluación Class B exitosa
      - Last_Gate_Run     = último cambio de Gate_Decision

    Retorna True si el actor PUEDE mutar; False = inmune (manual-first).

    G5: cuando retorna False, el orquestador emite sugerencia de revisión
    (build_manual_suggestion) y JAMÁS ejecuta la mutación.

    Primera evaluación (sin Class_B_Last_Run):
      - NO se aplica protección manual por last_edited_by humano/ausente.
      - Se permite el primer cómputo Class B si el registro es elegible
        por lifecycle (is_mutable / terminal / REVIEW_NEEDED se evalúan
        por separado en el flujo).
    """
    # Q-11 / SCHEMA-008: excepción de una sola pasada para Rechazado.
    if (
        actor == Actor.PIPELINE
        and record.get("Status", "") == Status.RECHAZADO.value
        and record.get("Gate_Decision") != GateDecision.REJECTED.value
    ):
        return True

    # Fase 2: sin baseline Class B → primera evaluación permitida.
    # No usar last_edited_by / Last_Gate_Run como proxy de protección.
    if needs_first_class_b_compute(record):
        # Aún aplicamos is_mutable para terminalidad / REVIEW_NEEDED /
        # protected statuses. is_mutable sin field_name puede bloquear por
        # _was_touched_by_human; para first-run forçamos el camino de
        # elegibilidad de lifecycle sin la rama de "edición humana reciente"
        # como bloqueo de fila completa.
        # Override temporal: si no hay Class_B_Last_Run, no tratar
        # _was_touched_by_human como bloqueo de fila completa aquí.
        # La protección de campos Class B YA EXISTENTES se aplica solo
        # cuando ya hay baseline (rama de abajo).
        from tracker_flow import PROTECTED_STATUSES, Status as TFStatus
        current_status = record.get("Status")
        if current_status in [s.value for s in PROTECTED_STATUSES]:
            if current_status == TFStatus.CONTRATADO.value:
                return False
            if actor != Actor.HUMANO:
                # Otros terminales: solo humano puede mutar (misma regla)
                return False
        # REVIEW_NEEDED / Por Revisar se gobiernan por is_mutable y el
        # workflow explícito; si is_mutable dice False por status, respetar.
        # Para first-run, saltamos la rama de protección manual por humano.
        return True

    # Baseline existe: ventana manual = last_edited_time > Class_B_Last_Run
    # + autor humano. Protege valores Class B ya calculados.
    last_edited_time = record.get("last_edited_time", "")
    class_b_last_run = record.get("Class_B_Last_Run", "")
    last_edited_by_id = record.get("last_edited_by_id", "")

    if last_edited_time and class_b_last_run:
        from tracker_flow import _is_human_edit

        if (
            _is_human_edit(last_edited_by_id)
            and last_edited_time > class_b_last_run
        ):
            return False

    # Fuera de la ventana manual-first, aplicar el guard general.
    if not is_mutable(record, actor):
        return False

    return True

def manual_edit_touched_class_a_only(
    record: Dict[str, Any],
    actor: Actor,
    previous_class_b: Dict[str, Dict[str, Any]],
) -> bool:
    """
    H9 / Fase 2: Evalúa si la ventana manual-first (edición humana tras
    Class_B_Last_Run) debe inmunizar la fila COMPLETA o si, dado que lo
    tocado fue Class A, Class B sigue recalculable.

    Baseline canónico: Class_B_Last_Run (no Last_Gate_Run).

    Retorna True si hay edición humana reciente pero se confirmó Class A
    únicamente (Class B recalculable, fila NO va a la rama de sugerencia).
    Retorna False si no hay edición humana reciente (no aplica este check),
    o si la edición tocó Class B / no se pudo confirmar (fila SIGUE inmune
    — mismo comportamiento que antes del fix, conservador).
    """
    last_edited_time = record.get("last_edited_time", "")
    class_b_last_run = record.get("Class_B_Last_Run", "")

    if not last_edited_time or not class_b_last_run:
        return False  # Sin baseline Class B o sin timestamp: no aplica.

    last_edited_by_id = record.get("last_edited_by_id", "")
    from tracker_flow import _is_human_edit
    if not _is_human_edit(last_edited_by_id):
        return False  # No es edición humana — no aplica.

    if not (last_edited_time > class_b_last_run):
        return False  # Edición humana, pero anterior al baseline Class B — no aplica.

    # Hay edición humana posterior al baseline Class B: verificar si tocó
    # solo Class A.
    touched_field = compute_last_edited_field(record, previous_class_b)
    record["last_edited_field"] = touched_field  # Consumido por is_mutable(field_name=...)

    if touched_field == "_class_a_touched":
        logger.info(
            f"[MANUAL-FIRST-CLASS-A] Fila {record.get('id', 'unknown')[-8:]} "
            f"editada por humano tras Class_B_Last_Run, pero solo Class A confirmado "
            f"— Class B recalculable, fila continúa a cómputo normal."
        )
        return True

    logger.info(
        f"[MANUAL-FIRST] Fila {record.get('id', 'unknown')[-8:]} editada por "
        f"humano tras Class_B_Last_Run, Class B tocado o no confirmado ({touched_field}) "
        f"→ inmunidad de fila completa (comportamiento previo)."
    )
    return False


def is_manual_first_immune(record: Dict[str, Any], actor: Actor = Actor.PIPELINE) -> bool:
    """G5: True si la fila está inmune a mutación (inverso de manual_first_protection)."""
    return not manual_first_protection(record, actor)


def preview_destructive_actions(record: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    G5: calcula qué haría el pipeline SIN escribir nada.

    Usado para armar sugerencias de revisión en filas manual-first.
    No llama client, no muta record.
    """
    actions: List[Dict[str, Any]] = []
    flat = dict(record)
    status = flat.get("Status", "") or ""
    source_type = (
        flat.get("Source_Type ", "")
        or flat.get("Source_Type", "")
        or SOURCE_TYPE_VACANTE
    )
    url = flat.get("URL", "") or ""
    jd = flat.get("JD", "") or ""
    nad = flat.get("NAD", "") or ""
    rol = flat.get("Rol", "") or ""

    # URL gate
    ok, reason = validate_url(url, source_type, jd_text=jd)
    if (
        status not in [s.value for s in PROTECTED_STATUSES]
        and not ok
        and not reason.startswith("AGREGADOR_RETRY")
    ):
        actions.append({
            "kind": "archive",
            "reason": f"URL Gate: {reason}",
            "would_set": {
                "Status": Status.EXPIRADA.value,
                "Next_Action": NextAction.ARCHIVAR.value,
            },
        })
        return actions  # archive short-circuits like the loop

    # NAD expired
    if nad and status not in [s.value for s in PROTECTED_STATUSES]:
        try:
            nad_date = datetime.strptime(str(nad)[:10], "%Y-%m-%d")
            if nad_date < datetime.now():
                actions.append({
                    "kind": "archive",
                    "reason": f"NAD expirado: {nad}",
                    "would_set": {
                        "Status": Status.EXPIRADA.value,
                        "Next_Action": NextAction.ARCHIVAR.value,
                    },
                })
                return actions
        except ValueError:
            pass

    # Score + gate labels (no Status mutation)
    if source_type in SOURCE_TYPE_BYPASS:
        score = flat.get("Score") if flat.get("Score") is not None else 0
    else:
        score = calculate_score_v6(flat)
    gate_result = apply_gate_decision(flat, score if isinstance(score, int) else 0)
    if gate_result.get("Gate_Decision") or gate_result.get("Next_Action"):
        would = {}
        if gate_result.get("Gate_Decision"):
            would["Gate_Decision"] = gate_result["Gate_Decision"]
        if gate_result.get("Next_Action"):
            would["Next_Action"] = gate_result["Next_Action"]
        if would:
            actions.append({
                "kind": "gate_label",
                "reason": gate_result.get("decision") or gate_result.get("reason") or "gate",
                "would_set": would,
            })

    return actions


def build_manual_suggestion(
    record: Dict[str, Any],
    actions: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    G5: sugerencia = revisión, jamás ejecución.

    Produce un dict de observabilidad. El orquestador lo acumula en
    metrics['suggestions'] y NUNCA lo pasa a guarded_pages_update.
    """
    if actions is None:
        actions = preview_destructive_actions(record)
    return {
        "id": record.get("id", ""),
        "status": record.get("Status", ""),
        "last_edited_time": record.get("last_edited_time", ""),
        "last_edited_by_id": record.get("last_edited_by_id", ""),
        "Last_Gate_Run": record.get("Last_Gate_Run", ""),
        "immune": True,
        "execution": "never",  # contrato G5: jamás ejecución
        "review": "manual",
        "actions": actions,
        "message": (
            f"[SUGERENCIA] Fila {str(record.get('id', ''))[-8:]} tocada por humano "
            f"— revisar manualmente; pipeline no ejecuta."
        ),
    }


def class_b_guard(payload: Dict[str, Any], actor: Actor) -> Dict[str, Any]:
    """
    Q-9 / §2-Clase B: guard fail-closed en TODAS las vías Python de escritura.

    - PIPELINE / DEDUP / INGESTA: Class A + Class B permitidos; unknown → ValueError.
    - Otros actores: solo Class A; Class B + unknown → ValueError.
    - MCP = exención documentada (no usa esta vía; control procedural APROBAR_WRITE).

    Retorna payload limpio listo para pages_update. Nunca silencia violaciones.
    """
    if not payload:
        return {}

    if actor in _PIPELINE_CLASS_B_ACTORS:
        clean: Dict[str, Any] = {}
        unknown: Dict[str, Any] = {}
        for key, value in payload.items():
            if key in CLASS_A_FIELDS or key in CLASS_B_FIELDS:
                clean[key] = value
            else:
                unknown[key] = value
        if unknown:
            raise ValueError(
                f"class_b_guard: campos desconocidos rechazados (fail-closed): "
                f"{sorted(unknown.keys())}"
            )
        return clean

    # Actores no-pipeline: Class A only (usa módulo class_b_guard)
    return assert_class_a_only_safe(payload)


def assert_class_a_only_safe(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Wrapper local sobre class_b_guard.assert_class_a_only (Class A only)."""
    from class_b_guard import assert_class_a_only
    return assert_class_a_only(payload)


def compute_write_diff(
    current: Dict[str, Any],
    proposed: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Conditional write: solo campos con valor realmente distinto.

    Usa diff_records del core (type-preserving). Anti-reescritura: si no hay
    diff, retorna {} y el caller NO debe tocar Notion.
    """
    if not proposed:
        return {}
    # Diff solo sobre las keys propuestas (no re-escribir el record entero)
    old_slice = {k: current.get(k) for k in proposed}
    changes = diff_records(old_slice, proposed)
    return {k: proposed[k] for k in changes}


def guarded_pages_update(
    client: Any,
    page_id: str,
    payload: Dict[str, Any],
    *,
    actor: Actor,
    current: Optional[Dict[str, Any]] = None,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """
    Única vía de escritura del orquestador.

    1. Diff real vs current (anti-rewrite)
    2. class_b_guard fail-closed
    3. pages_update solo si queda payload no vacío y not dry_run

    Returns: {wrote: bool, payload: dict, skipped_reason: str|None}
    """
    proposed = dict(payload or {})
    if current is not None:
        proposed = compute_write_diff(current, proposed)

    if not proposed:
        return {"wrote": False, "payload": {}, "skipped_reason": "no_diff"}

    try:
        clean = class_b_guard(proposed, actor)
    except ValueError as exc:
        logger.error(f"[class_b_guard] write bloqueado {page_id[-8:]}: {exc}")
        return {"wrote": False, "payload": {}, "skipped_reason": f"guard:{exc}"}

    if not clean:
        return {"wrote": False, "payload": {}, "skipped_reason": "empty_after_guard"}

    if dry_run:
        logger.info(f"[DRY] write {page_id[-8:]} keys={sorted(clean.keys())}")
        return {"wrote": False, "payload": clean, "skipped_reason": "dry_run"}

    client.pages_update(page_id, clean)
    return {"wrote": True, "payload": clean, "skipped_reason": None}


def analyze_outcome_patterns(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    F5: Análisis de patrones de rechazo — SOLO LECTURA.

    Opera sobre el snapshot ya normalizado (cero re-query, cero writes).
    Port conductual de layer_1_run.analyze_outcome_patterns sobre plano.
    """
    rejection_patterns: Dict[str, Dict[str, int]] = {}
    score_effectiveness: Dict[str, Dict[str, int]] = {}
    timing_patterns: Dict[str, List[int]] = {}

    live_applied = {
        Status.POSTULADO.value,
        Status.EN_PROCESO.value,
        Status.NEGOCIANDO.value,
        "En proceso",  # legacy casing visto en prod
    }

    for record in records:
        status = record.get("Status", "") or ""
        score = record.get("Score", 0) or 0
        marca = record.get("Marca", "") or ""
        vm_scope = record.get("VM_Scope", "") or ""
        applied_date = record.get("Apply Date", "") or record.get("Applied", "") or ""
        rejected_date = record.get("Rej Date", "") or ""

        score_bracket = f"Score {score}"

        if status == Status.RECHAZADO.value:
            score_effectiveness.setdefault(score_bracket, {"applied": 0, "rejected": 0})
            score_effectiveness[score_bracket]["rejected"] += 1
            if marca:
                rejection_patterns.setdefault(marca, {"applied": 0, "rejected": 0})
                rejection_patterns[marca]["rejected"] += 1
        elif status in live_applied:
            score_effectiveness.setdefault(score_bracket, {"applied": 0, "rejected": 0})
            score_effectiveness[score_bracket]["applied"] += 1
            if marca:
                rejection_patterns.setdefault(marca, {"applied": 0, "rejected": 0})
                rejection_patterns[marca]["applied"] += 1

        if applied_date and rejected_date:
            try:
                applied_dt = datetime.strptime(str(applied_date)[:10], "%Y-%m-%d").date()
                rejected_dt = datetime.strptime(str(rejected_date)[:10], "%Y-%m-%d").date()
                days_to_rejection = (rejected_dt - applied_dt).days
                timing_key = f"{vm_scope or 'N/A'}_VM"
                timing_patterns.setdefault(timing_key, []).append(days_to_rejection)
            except (ValueError, TypeError):
                pass

    return {
        "rejection_patterns": rejection_patterns,
        "score_effectiveness": score_effectiveness,
        "timing_patterns": timing_patterns,
    }


def _normalize_dedup_key(url: str) -> str:
    """Clave canónica de URL para agrupar duplicados (sin query/fragment)."""
    if not url:
        return ""
    raw = url.strip().lower()
    # Quitar esquema y www
    for prefix in ("https://", "http://"):
        if raw.startswith(prefix):
            raw = raw[len(prefix):]
            break
    if raw.startswith("www."):
        raw = raw[4:]
    # Quitar query y fragment
    raw = raw.split("?", 1)[0].split("#", 1)[0]
    return raw.rstrip("/")


def find_duplicate_groups(records: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """
    F6: Agrupa duplicados por URL canónica o hash idéntico.

    Solo produce grupos de tamaño ≥ 2. No escribe nada.
    """
    by_key: Dict[str, List[Dict[str, Any]]] = {}
    for record in records:
        url_key = _normalize_dedup_key(record.get("URL", "") or "")
        hash_key = (record.get("hash") or "").strip().lower()
        key = None
        if url_key:
            key = f"url:{url_key}"
        elif hash_key:
            key = f"hash:{hash_key}"
        if not key:
            continue
        by_key.setdefault(key, []).append(record)

    return [group for group in by_key.values() if len(group) >= 2]


def run_dedup_audit(
    records: List[Dict[str, Any]],
    client: Any,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """
    F6: Dedup unificado con survivor canónico + guard is_mutable.

    - Survivor = choose_survivor (core tracker_flow: Status rank → Score → URL → layer L1>L2>L3>N/A)
    - No-survivors mutables reciben Dedup_Flag = "Posible duplicado"
    - Filas protegidas (is_mutable=False) jamás se marcan ni se archivan
    - Cero trash físico; consolidate_duplicates.py se archiva en G6, no se llama aquí
    """
    result = {
        "groups_found": 0,
        "survivors": 0,
        "flagged": 0,
        "protected_skipped": 0,
        "flags": [],  # list of {survivor_id, flagged_id, reason}
    }

    groups = find_duplicate_groups(records)
    result["groups_found"] = len(groups)

    for group in groups:
        survivor = choose_survivor(group)
        result["survivors"] += 1
        survivor_id = survivor.get("id", "")

        for record in group:
            rid = record.get("id", "")
            if rid == survivor_id:
                continue

            # Guard is_mutable: filas protegidas son inmunes al mark
            if not is_mutable(record, Actor.DEDUP):
                result["protected_skipped"] += 1
                logger.info(
                    f"[F6] Skip protegido {rid[-8:]} (survivor={survivor_id[-8:]})"
                )
                continue

            flag_payload = {"Dedup_Flag": {"checkbox": True}}
            # Anti-rewrite: si ya tiene el flag, no tocar
            write_result = guarded_pages_update(
                client,
                rid,
                flag_payload,
                actor=Actor.DEDUP,
                current=record,
                dry_run=dry_run,
            )
            if write_result["skipped_reason"] == "no_diff":
                logger.info(f"[F6] skip anti-rewrite {rid[-8:]} (ya flagged)")
                continue

            result["flags"].append({
                "survivor_id": survivor_id,
                "flagged_id": rid,
                "survivor_layer": survivor.get("layer", "N/A"),
                "flagged_layer": record.get("layer", "N/A"),
            })
            result["flagged"] += 1

            if write_result["wrote"]:
                logger.info(
                    f"[F6] Dedup_Flag → {rid[-8:]} (survivor={survivor_id[-8:]})"
                )
            else:
                logger.info(
                    f"[F6 DRY] marcaría Dedup_Flag → {rid[-8:]} "
                    f"(survivor={survivor_id[-8:]})"
                )

    return result


def run_ingestion(
    feed_path: str,
    layer: int = 1,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """
    Ejecuta el pipeline de ingesta (ex-feed_processor) y retorna métricas.

    Reutiliza las funciones puras de feed_processor.py para:
      - sanitize + normalize_envelope + coerce_types
      - process_record (alias, hard-block, dedup, URL gate)
      - write_to_notion (pages.create Class A) cuando not dry_run

    Después de una ingesta exitosa el orquestador (F0+) calculará
    Score / Prioridad / Gate_Decision / Next_Action sobre las filas nuevas.
    """
    # Import lazy para evitar side-effects de Client y path hacking de feed_processor
    from feed_processor import (
        sanitize_input,
        normalize_envelope,
        coerce_types,
        process_record,
        write_to_notion,
        NotionSchema,
        load_alias_map,
        print_dryrun_summary,
        write_dryrun_file,
        archive_dryrun_notion,
        ProcessedRecord,
    )
    from notion_client import Client as NotionClient

    metrics: Dict[str, Any] = {
        "total_records": 0,
        "clean": 0,
        "blocked": 0,
        "review_needed": 0,
        "written": 0,
        "failed": 0,
        "dry_run": dry_run,
    }

    path = Path(feed_path)
    if not path.is_absolute():
        # Resolver relativo al Layer_1 root (parent de scripts/)
        layer1_root = script_dir.parent
        path = layer1_root / path
    if not path.exists():
        logger.error(f"Archivo de feed no encontrado: {path}")
        metrics["error"] = f"file_not_found:{path}"
        return metrics

    logger.info(f"INGESTA: Layer L{layer} · archivo={path.name}")

    raw_text = path.read_text(encoding="utf-8")
    try:
        clean_json = sanitize_input(raw_text)
        json_data = json.loads(clean_json)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.error(f"JSON inválido tras sanitize_input: {exc}")
        metrics["error"] = f"json_invalid:{exc}"
        return metrics

    records = normalize_envelope(json_data, layer)
    records = coerce_types(records)
    metrics["total_records"] = len(records)
    logger.info(f"INGESTA: {len(records)} registros en envelope")

    alias_data = load_alias_map()
    notion_token = os.environ.get("NOTION_TOKEN")
    if not notion_token and not dry_run:
        logger.error("NOTION_TOKEN requerido para escritura de ingesta")
        metrics["error"] = "missing_token"
        return metrics

    # Cliente real solo cuando vamos a escribir o a consultar schema/dedup
    notion_utils = NotionClient(auth=notion_token) if notion_token else None
    if notion_utils is None:
        # Dry-run sin token: no podemos cargar schema ni hacer dedup real
        logger.warning("Sin NOTION_TOKEN — dry-run de ingesta limitado (sin schema/dedup live)")
        metrics["warning"] = "no_token_limited_dryrun"
        # Aún así procesamos dispositions locales
        processed = []
        for r in records:
            # process_record requiere client+schema; fallback mínimo
            from feed_processor import normalize_record_fields, compute_dedup_hash
            norm = normalize_record_fields(r)
            processed.append(
                ProcessedRecord(
                    record=norm,
                    hash_key=compute_dedup_hash(norm),
                    disposition="CLEAN",
                    brand=norm.get("brand_raw") or norm.get("brand") or "",
                )
            )
    else:
        schema = NotionSchema.load(notion_utils)
        schema.warn_missing_class_a()
        processed = [
            process_record(r, notion_utils, schema, alias_data) for r in records
        ]

    metrics["clean"] = sum(1 for p in processed if p.disposition == "CLEAN")
    metrics["blocked"] = sum(1 for p in processed if p.disposition == "BLOCKED")
    metrics["review_needed"] = sum(
        1 for p in processed if p.disposition == "REVIEW_NEEDED"
    )

    print_dryrun_summary(processed, layer)
    dryrun_path = write_dryrun_file(processed, layer)
    logger.info(f"DRY RUN de ingesta guardado: {dryrun_path}")

    to_write = [p for p in processed if p.disposition in ("CLEAN", "REVIEW_NEEDED")]
    metrics["candidates"] = len(to_write)

    if dry_run:
        logger.info(
            f"INGESTA DRY-RUN: {len(to_write)} candidatos (CLEAN+REVIEW) "
            f"— no se escribe en Notion"
        )
        # Archivar dry-run aunque sea modo diagnóstico
        if notion_utils is not None:
            try:
                archive_dryrun_notion(notion_utils, dryrun_path, layer)
            except Exception as exc:
                logger.warning(f"No se pudo archivar dry-run de ingesta: {exc}")
        return metrics

    # Modo escritura
    if notion_utils is None:
        logger.error("No se puede escribir sin NOTION_TOKEN")
        metrics["error"] = "missing_token"
        return metrics

    logger.info(f"INGESTA APPLY: escribiendo {len(to_write)} registros...")
    written, failed = write_to_notion(notion_utils, processed, schema)
    metrics["written"] = written
    metrics["failed"] = failed
    logger.info(f"INGESTA: escritos={written} · fallidos={failed}")

    try:
        archive_dryrun_notion(notion_utils, dryrun_path, layer)
    except Exception as exc:
        logger.warning(f"No se pudo archivar dry-run de ingesta: {exc}")

    return metrics


def run_orchestrator(
    client: Any,
    dry_run: bool = True,
    apply: bool = False,
    dedup_audit: bool = False,
    dry_run_live: bool = False
) -> Dict[str, Any]:
    """
    Ejecuta el orquestador completo (Fases 0-6 sobre registros existentes).
    
    Args:
        client: Notion client (real o fake)
        dry_run: Modo diagnóstico (default True)
        apply: Modo escritura (requiere --apply explícito)
        dedup_audit: Ejecutar dedup audit al final
        dry_run_live: Modo diagnóstico con datos reales (lectura sin escritura)
    
    Returns:
        Dict con métricas del run
    """
    if apply and dry_run:
        logger.warning("--apply ignora --dry-run, se usará modo escritura")
        dry_run = False
    
    if not dry_run and not apply:
        logger.warning("Sin --apply, default es dry-run")
        dry_run = True
    
    logger.info(f"{'='*60}")
    if apply:
        mode = "APPLY MODE"
    elif dry_run_live:
        mode = "DRY RUN LIVE (real data, no writes)"
    else:
        mode = "DRY RUN (fake data)"
    logger.info(f"VANTAGE Orquestador v9.0 - {mode}")
    logger.info(f"{'='*60}")
    
    metrics = {
        "total_processed": 0,
        "writes": 0,
        "skips": 0,
        "archives": 0,
        "errors": 0,
        "manual_protected": 0,
        "suggestions": [],  # G5: revisión, jamás ejecución
        "patterns": None,
        "dedup": None,
    }
    
    # F0: Query inicial único + snapshot (un solo re-query)
    logger.info("F0: Query inicial del Tracker...")
    query_result = client.query_data_sources(VANTAGE_DATA_SOURCE_ID)
    items = query_result.get("results", [])
    metrics["total_processed"] = len(items)
    
    logger.info(f"F0: {len(items)} filas recuperadas")

    # Snapshot normalizado del run (fuente única para F5/F6; cero re-query)
    snapshot: List[Dict[str, Any]] = []

    # H9: baseline Class B del run anterior, cargado una vez (no por fila).
    previous_class_b_snapshot = load_class_b_snapshot()
    
    # Fases por cada fila
    for item in items:
        try:
            # Normalizar record
            record = normalize_record(item)
            # P5 FIX HO-000056: snapshot inmutable ANTES de mutaciones F1.5/F3/F3.6.
            # record se muta in-place (VM_Scope, Score, Score_Method, Prioridad) más
            # abajo; si se usa el mismo objeto como 'current' en compute_write_diff,
            # el diff compara el valor recién calculado contra sí mismo y descarta
            # el campo como 'sin cambio' — record_original preserva el estado real
            # de Notion al momento del F0 query.
            record_original = dict(record)
            snapshot.append(record)
            record_id = record.get("id", "unknown")[-8:]
            
            # §2.3 / G5: Manual-first — inmune; sugerencia = revisión, jamás ejecución
            # H9: excepción field-aware — si la única edición humana confirmada
            # fue sobre Class A, Class B sigue recalculable (no hace continue).
            if not manual_first_protection(record, Actor.PIPELINE):
                if manual_edit_touched_class_a_only(record, Actor.PIPELINE, previous_class_b_snapshot):
                    pass  # Class A confirmado — cae al cómputo normal debajo.
                else:
                    metrics["manual_protected"] += 1
                    suggestion = build_manual_suggestion(record)
                    metrics["suggestions"].append(suggestion)
                    logger.info(suggestion["message"])
                    for act in suggestion["actions"]:
                        logger.info(
                            f"[SUGERENCIA] {record_id} would {act['kind']}: "
                            f"{act['reason']} → {act.get('would_set')}"
                        )
                    # G5: CERO writes — no guarded_pages_update, no archive, no gate label
                    continue
            
            # F1.5: Clasificación VM_Scope/Role_Class/Source_Type (paridad layer_1_run)
            source_type = record.get("Source_Type ", "") or record.get("Source_Type", "") or ""
            if not source_type:
                source_type = SOURCE_TYPE_VACANTE
                record["Source_Type "] = SOURCE_TYPE_VACANTE

            rol = record.get("Rol", "") or ""
            if not record.get("VM_Scope"):
                record["VM_Scope"] = get_vm_scope(rol)
            if not record.get("Role_Class"):
                record["Role_Class"] = get_role_class(rol)

            # F2: URL Gate (JD bypass + agregadores; paridad offline)
            url = record.get("URL", "")
            jd_text = record.get("JD", "") or ""
            is_valid, reason = validate_url(url, source_type, jd_text=jd_text)

            # Terminales / protegidos: no archivar por URL
            status_now = record.get("Status", "") or ""
            if status_now in [s.value for s in PROTECTED_STATUSES]:
                # Aún corre F4 para APPLIED/REJECTED labels, sin mutar Status
                pass
            elif not is_valid and not reason.startswith("AGREGADOR_RETRY"):
                archive_result = archive_gate(
                    record,
                    reason=f"URL Gate: {reason}",
                    evidence=f"URL={url}",
                    actor=Actor.PIPELINE,
                    timestamp=datetime.now().isoformat()
                )
                wr = guarded_pages_update(
                    client, record["id"], archive_result,
                    actor=Actor.PIPELINE, current=record_original, dry_run=dry_run,
                )
                if wr["wrote"]:
                    metrics["writes"] += 1
                metrics["archives"] += 1
                continue
            else:
                # Éxito URL → Fetch=Accesible si faltaba (paridad bug-fix layer_1_run)
                if (
                    is_valid
                    and record.get("Fetch") != FetchResult.ACCESIBLE.value
                    and source_type == SOURCE_TYPE_VACANTE
                ):
                    record["_proposed_Fetch"] = FetchResult.ACCESIBLE.value

            # F3: Scoring v6.4 (idéntico)
            source_type = (
                record.get("Source_Type ", "")
                or record.get("Source_Type", "")
                or SOURCE_TYPE_VACANTE
            )
            if source_type in SOURCE_TYPE_BYPASS:
                score = record.get("Score") if record.get("Score") is not None else 0
                record["Score_Method"] = "BYPASS"
            else:
                score = calculate_score_v6(record)
                record["Score_Method"] = "DETERMINISTIC"
            record["Score"] = score

            # F3.5.1: Expiración NAD (unificado; is_mutable ya filtró protegidos)
            nad = record.get("NAD", "")
            if nad and status_now not in [s.value for s in PROTECTED_STATUSES]:
                try:
                    nad_date = datetime.strptime(str(nad)[:10], "%Y-%m-%d")
                    if nad_date < datetime.now():
                        archive_result = archive_gate(
                            record,
                            reason="NAD expirado",
                            evidence=f"NAD={nad}",
                            actor=Actor.PIPELINE,
                            timestamp=datetime.now().isoformat()
                        )
                        wr = guarded_pages_update(
                            client, record["id"], archive_result,
                            actor=Actor.PIPELINE, current=record_original, dry_run=dry_run,
                        )
                        if wr["wrote"]:
                            metrics["writes"] += 1
                        metrics["archives"] += 1
                        continue
                except ValueError:
                    logger.warning(f"NAD malformado: {nad}")

            # F3.6: Prioridad (via priority_logic.py, NO tocar bug día/mes)
            try:
                from priority_logic import infer_prioridad
                # P2 FIX 2026-09-14: item["properties"]["Score"] queda stale tras F3
                # (línea ~1010 actualiza record, no item). infer_prioridad lee de item —
                # se parchea aquí para evitar tocar la firma compartida con
                # backfill_class_a.py (que sí depende del shape crudo de item).
                item.setdefault("properties", {})["Score"] = {"number": score}
                prioridad = infer_prioridad(item, datetime.now())
                # infer_prioridad may return (value, reason) tuple
                if isinstance(prioridad, tuple):
                    record["Prioridad"] = prioridad[0]
                else:
                    record["Prioridad"] = prioridad
            except Exception as e:
                logger.warning(f"Error calculando prioridad: {e}")

            # F4: Gate + Next_Action (paridad layer_1_run Fase 4)
            gate_result = apply_gate_decision(record, score)

            # Ensamblar payload de write (solo campos de negocio mutables)
            write_payload: Dict[str, Any] = {}
            if record.get("_proposed_Fetch"):
                write_payload["Fetch"] = record["_proposed_Fetch"]
            # Score y Score_Method (siempre calculados en F3 → siempre en payload)
            if record.get("Score") is not None:
                write_payload["Score"] = record["Score"]
            if record.get("Score_Method"):
                write_payload["Score_Method"] = record["Score_Method"]
            # VM_Scope y Role_Class: calculados en F1.5 → explícitos, sin guarda elif
            # que filtre por valor vacío. Siempre se assignmentan, con default si faltara.
            write_payload["VM_Scope"] = record.get("VM_Scope") or get_vm_scope(
                record.get("Rol", "") or ""
            )
            write_payload["Role_Class"] = record.get("Role_Class") or get_role_class(
                record.get("Rol", "") or ""
            )
            # Source_Type: normalizado en F1.5 → siempre presente
            source_type_val = (
                record.get("Source_Type ")
                or record.get("Source_Type", "")
                or SOURCE_TYPE_VACANTE
            )
            write_payload["Source_Type"] = source_type_val
            # Prioridad: calculada en F3.6 → write_payload si hay valor
            if record.get("Prioridad"):
                write_payload["Prioridad"] = record["Prioridad"]
            # Gate_Decision y Next_Action: se sobreescriben por gate_result abajo
            # (no los asignamos aquí; el bloque de gate_result los maneja)
            if gate_result.get("Gate_Decision"):
                write_payload["Gate_Decision"] = gate_result["Gate_Decision"]
                # P4 FIX 2026-09-14 (corregido tras dry-run-live real: 22/24
                # filas proponían Last_Gate_Run sin cambio real de gate —
                # "if gate_result.get(...)" no basta, hay que comparar contra
                # el valor ya guardado):
                if gate_result["Gate_Decision"] != record.get("Gate_Decision"):
                    write_payload["Last_Gate_Run"] = datetime.now().isoformat()
            if gate_result.get("Next_Action"):
                write_payload["Next_Action"] = gate_result["Next_Action"]
            # No escribir decision/reason internos
            if gate_result.get("decision") in ("PROTECTED", "TERMINAL"):
                # Solo observabilidad — no mutar Status de protegidos
                write_payload.pop("Status", None)

            # Fase 2: Class_B_Last_Run se actualiza en TODA evaluación Class B
            # exitosa, independientemente de que Gate_Decision haya cambiado.
            # Distinto de Last_Gate_Run (solo cambio de Gate).
            # Solo marcar cuando realmente se evaluó (no PROTECTED/TERMINAL
            # early-exit que no computó Class B).
            if gate_result.get("decision") not in ("PROTECTED", "TERMINAL"):
                now_iso = datetime.now().isoformat()
                write_payload["Class_B_Last_Run"] = now_iso
                # Propagar al record para que el snapshot del run lo capture
                # como baseline real (no artificial).
                record["Class_B_Last_Run"] = now_iso
                record["_class_b_computed"] = True

            wr = guarded_pages_update(
                client, record["id"], write_payload,
                actor=Actor.PIPELINE, current=record_original, dry_run=dry_run,
            )
            if wr["wrote"]:
                metrics["writes"] += 1
            else:
                metrics["skips"] += 1
                
        except Exception as e:
            logger.error(f"Error procesando fila {record.get('id', 'unknown')[-8:]}: {e}")
            metrics["errors"] += 1

    # F5: Patrones (solo lectura, sobre snapshot — cero writes)
    logger.info("F5: Análisis de patrones (read-only)...")
    metrics["patterns"] = analyze_outcome_patterns(snapshot)
    
    # F6: Dedup unificado (survivor canónico + guard is_mutable)
    if dedup_audit or ENABLE_DEDUP_AUDIT:
        logger.info("F6: Dedup audit (survivor L1>L2>L3>N/A + is_mutable)...")
        dedup_result = run_dedup_audit(snapshot, client, dry_run=dry_run)
        metrics["dedup"] = dedup_result
        if not dry_run:
            metrics["writes"] += dedup_result.get("flagged", 0)
    
    # Summary
    logger.info(f"{'='*60}")
    logger.info("SUMMARY")
    logger.info(f"Total procesado: {metrics['total_processed']}")
    logger.info(f"Escrituras: {metrics['writes']}")
    logger.info(f"Skips (sin cambios): {metrics['skips']}")
    logger.info(f"Archivos: {metrics['archives']}")
    logger.info(f"Protegidos manual: {metrics['manual_protected']}")
    logger.info(f"Sugerencias (revisión, no ejecución): {len(metrics['suggestions'])}")
    logger.info(f"Errores: {metrics['errors']}")
    if metrics.get("dedup"):
        logger.info(
            f"Dedup: groups={metrics['dedup']['groups_found']} "
            f"flagged={metrics['dedup']['flagged']} "
            f"protected={metrics['dedup']['protected_skipped']}"
        )
    logger.info(f"{'='*60}")

    # Escribir state file tras run exitoso (no dry-run, sin errores) — el
    # fallback de 7 días en tracker_flow._was_edited_since_last_run() solo
    # se activa si este archivo no existe; sin este write, TODA fila tocada
    # en los últimos 7 días queda protegida como "manual" indefinidamente.
    if not dry_run and metrics.get("errors", 0) == 0:
        import json
        state_dir = Path(os.environ.get("VANTAGE_STATE_DIR") or (Path(__file__).resolve().parent / "state"))
        state_dir.mkdir(exist_ok=True)
        state_file = state_dir / "last_successful_run.json"
        state_file.write_text(json.dumps({
            "last_run_time": datetime.now(timezone.utc).isoformat()
        }))
        logger.info(f"State file actualizado: {state_file}")

        # H9: snapshot Class B para el field-level guard del siguiente run.
        save_class_b_snapshot(snapshot)

    return metrics


def main():
    """CLI entry point — v9.1 (ingesta + cálculo)"""
    parser = argparse.ArgumentParser(
        description="VANTAGE Pipeline Orquestador v9.1 — cálculo + ingesta de feeds"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Modo diagnóstico (default). Con --file también simula la ingesta."
    )
    parser.add_argument(
        "--dry-run-live",
        action="store_true",
        help="Modo diagnóstico con datos reales del Tracker (lectura sin escritura)"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Modo escritura (requiere NOTION_TOKEN). Activa pages.create + pages.update."
    )
    parser.add_argument(
        "--dedup-audit",
        action="store_true",
        help="Ejecutar dedup audit al final del cálculo"
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Ruta al JSON de feed. Activa modo completo: ingesta (Class A) + cálculo (Class B)."
    )
    parser.add_argument(
        "--layer",
        type=int,
        default=1,
        choices=[1, 2, 3],
        help="Layer a asignar a los registros del feed (default: 1). Solo tiene efecto con --file."
    )
    
    args = parser.parse_args()
    
    # Load environment
    load_dotenv()
    
    # Determinar modo de escritura
    if args.apply:
        dry_run = False
    elif args.dry_run_live:
        dry_run = True
    else:
        dry_run = True  # default --dry-run

    # ── Fase de INGESTA (si --file) ──────────────────────────────────────────
    ingestion_metrics = None
    if args.file:
        logger.info("=" * 60)
        logger.info("FASE INGESTA (feed → pages.create Class A)")
        logger.info("=" * 60)
        ingestion_metrics = run_ingestion(
            feed_path=args.file,
            layer=args.layer,
            dry_run=dry_run,
        )
        if ingestion_metrics.get("error"):
            logger.error(f"Ingesta abortada: {ingestion_metrics['error']}")
            sys.exit(1)
        logger.info(
            f"Ingesta terminada · candidatos={ingestion_metrics.get('candidates', 0)} "
            f"· escritos={ingestion_metrics.get('written', 0)} "
            f"· dry_run={dry_run}"
        )
        # Tras una ingesta real, el Tracker ya tiene las nuevas filas.
        # Continuamos con el cálculo normal (F0 re-query las verá).

    # Crear client (fake en dry-run puro, real en apply / dry-run-live / post-ingesta)
    need_real_client = args.apply or args.dry_run_live or (args.file and not dry_run)
    if need_real_client:
        from notion_client import Client as NotionClient
        notion_token = os.environ.get("NOTION_TOKEN")
        if not notion_token:
            logger.error("NOTION_TOKEN requerido en modo --apply, --dry-run-live o ingesta con escritura")
            sys.exit(1)
        # Wrap real client to match fake client interface
        class NotionClientReal:
            def __init__(self, client):
                self.client = client
                self.writes = []
                self.queries = []
            
            def query_data_sources(self, data_source_id: str, **kwargs) -> Dict[str, Any]:
                self.queries.append(("query_data_sources", data_source_id, kwargs))
                return self.client.data_sources.query(data_source_id=data_source_id, **kwargs)
            
            def pages_update(self, page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
                self.writes.append(("pages_update", page_id, properties))
                return self.client.pages.update(
                    page_id=page_id,
                    properties=to_notion_properties(properties),
                )
        
        real_client = NotionClient(auth=notion_token)
        client = NotionClientReal(real_client)
    else:
        client = NotionClientFake()
    
    # Ejecutar orquestador (cálculo Class B sobre el Tracker)
    logger.info("=" * 60)
    logger.info("FASE CÁLCULO (Score / Prioridad / Gate / Next_Action)")
    logger.info("=" * 60)
    metrics = run_orchestrator(
        client=client,
        dry_run=dry_run,
        apply=args.apply,
        dedup_audit=args.dedup_audit,
        dry_run_live=args.dry_run_live
    )
    
    if ingestion_metrics is not None:
        metrics["ingestion"] = ingestion_metrics
    
    # Exit code
    if metrics.get("errors", 0) > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
