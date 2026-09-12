#!/usr/bin/env python3
"""
VANTAGE Pipeline Orquestador v9.0 — Refactor completo

Este orquestador reemplaza layer_1_run.py v8.0/v8.1 usando tracker_flow.py
como única fuente de verdad para decisiones de transición.

Características:
- CLI compatible con layer_1_run.py (--dry-run default, --apply explícito)
- Un solo re-query inicial + writes con diff (no write-churn)
- Fases lineales usando tracker_flow.py como core de decisión
- Prioridad manual respetada (is_mutable + last_edited_time)
- Dedup unificado con survivor canónico + guard is_mutable
- class_b_guard generalizado a TODAS las vías de escritura

Serial: DEVIN-20260912-01
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Setup path for imports
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

from tracker_flow import (
    Status, NextAction, GateDecision, Actor,
    normalize_record, is_mutable, evaluate_flow, archive_gate,
    LIFECYCLE_MATRIX, TERMINAL_STATUSES, LIVE_APPLICATION_STATUSES,
    PROTECTED_STATUSES, DELETED_VALUE_MAPPINGS,
    sync_status_from_outcome, apply_status_sync_writeback, run_outcome_status_sync,
    choose_survivor, get_layer_rank, diff_records,
)
from gate_logic import gate_logic
from priority_logic import infer_prioridad
from class_b_guard import (
    CLASS_A_FIELDS, CLASS_B_FIELDS, guard_write_payload, GuardResult,
)

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
    if source_type in ("Inbound", "Referencia", "Networking"):
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
    """F4: idéntico a layer_1_run.gate (Gate_Decision crudo)."""
    from profile_fit import has_vm_title_signal, is_role_excluded, resolve_alias_flags

    if is_role_excluded(rol) or resolve_alias_flags(marca)[0]:
        return "BLOCKED"
    if source_type in ["Inbound", "Referencia", "Networking"]:
        return "CREATE"
    if source_type == "Vacante":
        fetch_ok = fetch in ("Accesible", "Parcial")
        scope_ok = fetch_ok and (
            vm_scope == "Alto"
            or (role_class == "Pivote" and has_vm_title_signal(rol))
        )
        if not scope_ok:
            return "BLOCKED"
        if score is None:
            return "REVIEW_NEEDED"
        if score >= 60:
            return "CREATE"
        if score >= 40:
            return "REVIEW_NEEDED"
        return "BLOCKED"
    return "BLOCKED"


def evaluate_application_status(status: str) -> bool:
    """Paridad layer_1_run."""
    return status in ["Postulado", "En proceso", "En Proceso", "Negociando", "Sin respuesta", "Sin Respuesta"]


def evaluate_rejection_status(status: str) -> bool:
    return status == "Rechazado"


def get_application_next_action(status: str) -> str:
    """Legacy EN next-actions del viejo (G7 normaliza; paridad G3 los expone crudos)."""
    if status == "Postulado":
        return "Follow-up"
    if status in ("En proceso", "En Proceso"):
        return "Interview prep"
    if status == "Negociando":
        return "Follow-up"
    if status in ("Sin respuesta", "Sin Respuesta"):
        return "Follow-up"
    return "Re-check"


def apply_gate_decision(record: Dict[str, Any], score: int) -> Dict[str, Any]:
    """
    F4: Gate + Next_Action — paridad con layer_1_run Fase 4.

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

    flow = evaluate_flow(flat, Actor.PIPELINE)
    if flow.get("decision") in ("PROTECTED", "TERMINAL"):
        return {
            "decision": flow["decision"],
            "reason": flow.get("reason", ""),
            "Gate_Decision": None,
            "Next_Action": None,
            "_flow": flow,
        }

    status = flat.get("Status", "") or ""
    current_action = flat.get("Next_Action", "") or ""
    fetch = flat.get("Fetch", "") or ""
    vm_scope = flat.get("VM_Scope", "") or get_vm_scope(flat.get("Rol", "") or "")
    role_class = flat.get("Role_Class", "") or get_role_class(flat.get("Rol", "") or "")
    source_type = flat.get("Source_Type ", "") or flat.get("Source_Type", "") or "Vacante"
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
    if protected is not None and protected != "REJECTED":
        return {
            "decision": "PROTECTED",
            "reason": f"gate_logic:{protected}",
            "Gate_Decision": protected if protected in ("APPLIED", "REJECTED") else flat.get("Gate_Decision"),
            "Next_Action": current_action or None,
            "_protected": protected,
        }

    if evaluate_rejection_status(status):
        decision = "REJECTED"
        next_action = "Post-Mortem"
    elif evaluate_application_status(status):
        decision = "APPLIED"
        next_action = get_application_next_action(status)
    elif jd_quality == "JD Completo":
        decision = gate(fetch, vm_scope, role_class, source_type, score=score, rol=rol, marca=marca)
        if decision == "CREATE":
            next_action = "Optimizar"
        elif decision == "REVIEW_NEEDED":
            next_action = "Investigar"
        else:
            next_action = "Optimizar"
    else:
        decision = gate(fetch, vm_scope, role_class, source_type, score=score, rol=rol, marca=marca)
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

    return {
        "decision": decision,
        "Gate_Decision": decision,
        "Next_Action": next_action,
        "VM_Scope": vm_scope,
        "Role_Class": role_class,
        "Score": score,
    }


def manual_first_protection(record: Dict[str, Any], actor: Actor) -> bool:
    """
    §2.3: Ediciones manuales recientes = máxima prioridad.
    
    Ventana manual = last_edited_time > Last_Gate_Run + autor humano.
    Una fila tocada por humano desde el último run queda inmune a mutación destructiva.
    """
    if not is_mutable(record, actor):
        return False
    
    last_edited_time = record.get("last_edited_time", "")
    last_gate_run = record.get("Last_Gate_Run", "")
    
    if not last_edited_time or not last_gate_run:
        return True  # Sin timestamp = asumir mutable
    
    # Si editado por humano después del último run → inmunidad
    last_edited_by_id = record.get("last_edited_by_id", "")
    from tracker_flow import _is_human_edit
    if _is_human_edit(last_edited_by_id):
        if last_edited_time > last_gate_run:
            logger.info(
                f"[MANUAL-FIRST] Fila {record.get('id', 'unknown')[:8]} "
                f"editada por humano después del último run → inmunidad"
            )
            return False
    
    return True


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
        logger.error(f"[class_b_guard] write bloqueado {page_id[:8]}: {exc}")
        return {"wrote": False, "payload": {}, "skipped_reason": f"guard:{exc}"}

    if not clean:
        return {"wrote": False, "payload": {}, "skipped_reason": "empty_after_guard"}

    if dry_run:
        logger.info(f"[DRY] write {page_id[:8]} keys={sorted(clean.keys())}")
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
                    f"[F6] Skip protegido {rid[:8]} (survivor={survivor_id[:8]})"
                )
                continue

            flag_payload = {"Dedup_Flag": "Posible duplicado"}
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
                logger.info(f"[F6] skip anti-rewrite {rid[:8]} (ya flagged)")
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
                    f"[F6] Dedup_Flag → {rid[:8]} (survivor={survivor_id[:8]})"
                )
            else:
                logger.info(
                    f"[F6 DRY] marcaría Dedup_Flag → {rid[:8]} "
                    f"(survivor={survivor_id[:8]})"
                )

    return result


def run_orchestrator(
    client: Any,
    dry_run: bool = True,
    apply: bool = False,
    dedup_audit: bool = False
) -> Dict[str, Any]:
    """
    Ejecuta el orquestador completo.
    
    Args:
        client: Notion client (real o fake)
        dry_run: Modo diagnóstico (default True)
        apply: Modo escritura (requiere --apply explícito)
        dedup_audit: Ejecutar dedup audit al final
    
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
    logger.info(f"VANTAGE Orquestador v9.0 - {'DRY RUN' if dry_run else 'APPLY MODE'}")
    logger.info(f"{'='*60}")
    
    metrics = {
        "total_processed": 0,
        "writes": 0,
        "skips": 0,
        "archives": 0,
        "errors": 0,
        "manual_protected": 0,
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
    
    # Fases por cada fila
    for item in items:
        try:
            # Normalizar record
            record = normalize_record(item)
            snapshot.append(record)
            record_id = record.get("id", "unknown")[:8]
            
            # §2.3: Manual-first protection
            if not manual_first_protection(record, Actor.PIPELINE):
                metrics["manual_protected"] += 1
                continue
            
            # F1.5: Clasificación VM_Scope/Role_Class/Source_Type (paridad layer_1_run)
            source_type = record.get("Source_Type ", "") or record.get("Source_Type", "") or ""
            if not source_type:
                source_type = "Vacante"
                record["Source_Type "] = "Vacante"

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
                    actor=Actor.PIPELINE, current=record, dry_run=dry_run,
                )
                if wr["wrote"]:
                    metrics["writes"] += 1
                metrics["archives"] += 1
                continue
            else:
                # Éxito URL → Fetch=Accesible si faltaba (paridad bug-fix layer_1_run)
                if is_valid and record.get("Fetch") != "Accesible" and source_type == "Vacante":
                    record["_proposed_Fetch"] = "Accesible"

            # F3: Scoring v6.4 (idéntico)
            source_type = record.get("Source_Type ", "") or record.get("Source_Type", "") or "Vacante"
            if source_type in ("Inbound", "Referencia", "Networking"):
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
                            actor=Actor.PIPELINE, current=record, dry_run=dry_run,
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
            for key in ("Score", "Score_Method", "VM_Scope", "Role_Class",
                        "Source_Type ", "Prioridad", "Gate_Decision", "Next_Action"):
                if key == "Score" and record.get("Score") is not None:
                    write_payload["Score"] = record["Score"]
                elif key == "Score_Method" and record.get("Score_Method"):
                    write_payload["Score_Method"] = record["Score_Method"]
                elif key in record and record[key] not in (None, ""):
                    # Solo proponer si gate_result no lo sobreescribe
                    if key not in ("Gate_Decision", "Next_Action"):
                        write_payload[key] = record[key]
            if gate_result.get("Gate_Decision"):
                write_payload["Gate_Decision"] = gate_result["Gate_Decision"]
            if gate_result.get("Next_Action"):
                write_payload["Next_Action"] = gate_result["Next_Action"]
            # No escribir decision/reason internos
            if gate_result.get("decision") in ("PROTECTED", "TERMINAL"):
                # Solo observabilidad — no mutar Status de protegidos
                write_payload.pop("Status", None)

            wr = guarded_pages_update(
                client, record["id"], write_payload,
                actor=Actor.PIPELINE, current=record, dry_run=dry_run,
            )
            if wr["wrote"]:
                metrics["writes"] += 1
            else:
                metrics["skips"] += 1
                
        except Exception as e:
            logger.error(f"Error procesando fila {record.get('id', 'unknown')[:8]}: {e}")
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
    logger.info(f"Errores: {metrics['errors']}")
    if metrics.get("dedup"):
        logger.info(
            f"Dedup: groups={metrics['dedup']['groups_found']} "
            f"flagged={metrics['dedup']['flagged']} "
            f"protected={metrics['dedup']['protected_skipped']}"
        )
    logger.info(f"{'='*60}")
    
    return metrics


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="VANTAGE Pipeline Orquestador v9.0"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Modo diagnóstico (default)"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Modo escritura (requiere confirmación)"
    )
    parser.add_argument(
        "--dedup-audit",
        action="store_true",
        help="Ejecutar dedup audit al final"
    )
    
    args = parser.parse_args()
    
    # Load environment
    load_dotenv()
    
    # Crear client (fake en dry-run, real en apply)
    if args.apply:
        from notion_client import Client
        notion_token = os.environ.get("NOTION_TOKEN")
        if not notion_token:
            logger.error("NOTION_TOKEN requerido en modo --apply")
            sys.exit(1)
        client = Client(auth=notion_token)
    else:
        client = NotionClientFake()
    
    # Ejecutar orquestador
    metrics = run_orchestrator(
        client=client,
        dry_run=args.dry_run,
        apply=args.apply,
        dedup_audit=args.dedup_audit
    )
    
    # Exit code
    if metrics["errors"] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
