"""
VANTAGE Tracker Flow — Mapa de Flujo Lógico Único (V3 with F1-F15 fixes)

Ubicación: Layer_1/scripts/tracker_flow.py
Serial: DEVIN-20260911-05

Este módulo implementa:
- Enums cerrados (Status, Next_Action, Gate_Decision, Actor)
- Matriz de transición de ciclo de vida
- Predicado único is_mutable()
- Gate de archivo consolidado
- Normalización de records API shapes → plano

V3 Fixes Applied:
- F1: normalize_record() as mandatory boundary
- F2: Single archive path (evaluate → propose/execute → archive_gate)
- F3: Human edit detection (author + time, propose-log idempotency)
- F4: Diff on normalized flat records with type preservation
- F5: Fixed typo RETIRADO (was RETRIRADO)
- F6: Complete lifecycle matrix + manual rule
- F7: REVIEW gate designed (Por revisar → Objetivo resolution)
- F8: Single literal per enum value (Title Case ES)
- F10: Enum enforcement in normalize_record
- F11/G3/H7: Guard record-level only (field-block Class-B deferred)
- F12: Contratado first in survivor ranking
"""

from enum import Enum
from typing import Literal, Optional, Set, Dict, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


# ── Enums y Constantes - Conjunto Cerrado (A3, F5, F8) ────────────────────────

class Status(str, Enum):
    """Estados válidos de Status - conjunto cerrado (12 valores)"""
    # Estados operativos
    OBJETIVO = "Objetivo"
    EXPLORATORIO = "Exploratorio"
    POR_REVISAR = "Por Revisar"  # Title Case ES, single literal
    
    # Estados de postulación viva (LIVE_APPLICATION_STATUSES)
    POSTULANDO = "Postulando"
    POSTULADO = "Postulado"
    EN_PROCESO = "En Proceso"
    NEGOCIANDO = "Negociando"
    SIN_RESPUESTA = "Sin Respuesta"
    CONTRATADO = "Contratado"
    
    # Estados terminales (TERMINAL_STATUSES)
    EXPIRADA = "Expirada"
    RECHAZADO = "Rechazado"
    RETIRADO = "Retirado"  # F5: Fixed typo (was RETRIRADO)
    
    # NOTA: "Archivar" eliminado del vocabulario de Status (huérfano bilateral)
    # NOTA: "Repetida", "RAW", "Nueva" eliminados (valores fantasma)
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        """
        Verifica si un valor es válido - F10: enforce in normalize_record.
        
        R7: Logging moved to caller (normalize_record) to avoid side-effect in enum method.
        """
        try:
            cls(value)
            return True
        except ValueError:
            return False


# Única fuente de verdad para terminalidad (resuelve B3, F5)
TERMINAL_STATUSES: Set[Status] = {
    Status.EXPIRADA, Status.RECHAZADO, Status.RETIRADO
}

LIVE_APPLICATION_STATUSES: Set[Status] = {
    Status.POSTULANDO, Status.POSTULADO, Status.EN_PROCESO,
    Status.NEGOCIANDO, Status.SIN_RESPUESTA, Status.CONTRATADO
}

PROTECTED_STATUSES: Set[Status] = LIVE_APPLICATION_STATUSES | TERMINAL_STATUSES


# ── F13: Outcome → Status Auto-Sync (Paso 2b, cierre de HO-000042) ───────────
# Notion tiene "Outcome" como propiedad separada de "Status" (historial
# post-hoc). tracker_flow.py trata Contratado como valor directo de Status,
# pero ningún writer seteaba Status="Contratado" automáticamente cuando
# Outcome pasaba a Contratado — PROTECTED_STATUSES.CONTRATADO era código
# muerto en la práctica. F13 cierra ese gap sin tocar el schema de Outcome:
# el mapeo vive aquí, en la única fuente de verdad del vocabulario de Status.

OUTCOME_TO_STATUS_SYNC: Dict[str, Status] = {
    "Contratado": Status.CONTRATADO,
    # Deliberadamente NO se mapean "Rechazado", "Entrevista", "Sin respuesta":
    # esos valores de Outcome son historial de una postulación que puede seguir
    # viva bajo otro Status (p.ej. "Entrevista" no implica terminalidad). Solo
    # Contratado es un evento que debe reflejarse siempre en Status.
}


def sync_status_from_outcome(flat_record: Dict[str, Any]) -> bool:
    """
    F13: Corrige Status en el registro plano si Outcome indica un evento que
    debe reflejarse ahí (hoy: solo Contratado).

    Retorna True si mutó flat_record["Status"], False si no había nada que
    corregir. No escribe a Notion — opera sobre el dict en memoria; el
    caller (normalize_record, o cualquier script que lo invoque tras un
    fetch) es responsable de persistir el cambio si corresponde.
    """
    outcome = flat_record.get("Outcome", "")
    target_status = OUTCOME_TO_STATUS_SYNC.get(outcome)
    if target_status is None:
        return False

    current_status = flat_record.get("Status", "")
    if current_status == target_status.value:
        return False

    logger.info(
        f"[F13] Outcome={outcome!r} fuera de sync con Status={current_status!r} "
        f"— corrigiendo a {target_status.value!r}: "
        f"{flat_record.get('id', 'unknown')[:8]}"
    )
    flat_record["Status"] = target_status.value
    flat_record["_status_synced_from_outcome"] = True
    return True


class NextAction(str, Enum):
    """Acciones válidas de Next_Action - conjunto cerrado (9 valores)"""
    # Valores operativos
    OPTIMIZAR = "Optimizar"
    SEGUIMIENTO = "Seguimiento"
    PREPARACION_ENTREVISTA = "Preparación Entrevista"
    REVISION = "Revisión"
    INVESTIGAR = "Investigar"
    POST_MORTEM = "Post-Mortem"
    
    # Archivo
    ARCHIVAR = "Archivar"
    
    # Recuperación
    REPARAR_URL = "Reparar URL"
    VERIFICAR_JD = "Verificar JD"


class GateDecision(str, Enum):
    """Decisiones de Gate - terminología técnica EN fijada"""
    CREATE = "CREATE"
    BLOCKED = "BLOCKED"
    REVIEW_NEEDED = "REVIEW_NEEDED"
    APPLIED = "APPLIED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class Actor(str, Enum):
    """Actores que pueden mutar el Tracker"""
    HUMANO = "humano"
    PIPELINE = "pipeline"
    INGESTA = "ingesta"
    DEDUP = "dedup"
    MCP_DASHBOARD = "mcp_dashboard"


# ── F1: Normalization Boundary ───────────────────────────────────────────────

def normalize_record(api_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    F1: Frontera de normalización obligatoria.
    
    Convierte records con shapes API ({"properties": {"Status": {"select": {...}}}})
    a records planos ({"Status": "Objetivo", ...}).
    
    G1: Extrae last_edited_by_id desde raíz con shape real API
    (last_edited_by.id, no desde properties).
    
    F10: Valida enums y convierte desconocidos a REVIEW + WARN.
    """
    flat_record = {}
    properties = api_record.get("properties", {})
    
    # G1: Extract last_edited_by_id from root with real API shape
    # Real API: {"last_edited_by": {"object": "user", "id": "..."}}
    last_edited_by = api_record.get("last_edited_by", {})
    if isinstance(last_edited_by, dict) and "id" in last_edited_by:
        flat_record["last_edited_by_id"] = last_edited_by["id"]
    elif isinstance(last_edited_by, str):
        flat_record["last_edited_by_id"] = last_edited_by
    
    # G1: Extract last_edited_time from root (real API location)
    flat_record["last_edited_time"] = api_record.get("last_edited_time", "")
    
    # Normalize common fields from properties
    for key, prop in properties.items():
        value = extract_value(prop)
        if value is not None:
            flat_record[key] = value
    
    # F10: Enum enforcement - validate Status
    status = flat_record.get("Status", "")
    if status and not Status.is_valid(status):
        logger.warning(f"[F10] Status inválido normalizado a REVIEW: {status}")
        flat_record["Status"] = Status.POR_REVISAR.value
        flat_record["_original_invalid_status"] = status
    
    # Extract page ID
    flat_record["id"] = api_record.get("id", "")
    
    # F13: Outcome → Status auto-sync. Corre en TODO record que pase por esta
    # frontera (layer_1_run, feed_processor, mcp_dashboard, cualquier futuro
    # consumer) — no requiere que cada script lo invoque por separado.
    sync_status_from_outcome(flat_record)
    
    return flat_record


def extract_value(prop: Any) -> Any:
    """
    F4: Extract value from both API shapes and flat values.
    
    Accepts:
    - API shapes: {"type": "select", "select": {"name": "Objetivo"}}
    - API shapes without type: {"select": {"name": "Objetivo"}}
    - Flat values: "Objetivo"
    - Numbers: 42 (int) or "42" (str)
    """
    if prop is None:
        return None
    
    if isinstance(prop, (str, int, float, bool)):
        return prop
    
    if not isinstance(prop, dict):
        return None
    
    # API shape extraction
    prop_type = prop.get("type")
    
    # Handle both with and without "type" field
    if prop_type == "select" or (prop_type is None and "select" in prop):
        select_data = prop.get("select", {})
        if isinstance(select_data, dict) and "name" in select_data:
            return select_data["name"]
    if prop_type == "url" or (prop_type is None and "url" in prop):
        return prop.get("url")
    if prop_type == "rich_text" or (prop_type is None and "rich_text" in prop):
        rich_text = prop.get("rich_text", [])
        if isinstance(rich_text, list):
            return "".join(chunk["plain_text"] for chunk in rich_text)
    if prop_type == "title" or (prop_type is None and "title" in prop):
        title = prop.get("title", [])
        if isinstance(title, list):
            return "".join(chunk["plain_text"] for chunk in title)
    if prop_type == "number" or (prop_type is None and "number" in prop):
        return prop.get("number")
    if prop_type == "date" or (prop_type is None and "date" in prop):
        date_data = prop.get("date", {})
        if isinstance(date_data, dict) and "start" in date_data:
            return date_data["start"]
    if prop_type == "multi_select" or (prop_type is None and "multi_select" in prop):
        multi_select = prop.get("multi_select", [])
        if isinstance(multi_select, list):
            return [item["name"] for item in multi_select]
    
    # Fallback: try direct name extraction (for already-flat values)
    if "name" in prop:
        return prop["name"]
    
    return None


# ── F3: Human Edit Detection (Fixed) ───────────────────────────────────────────

KNOWN_BOT_IDS = {
    "integration-id-mcp-dashboard",
    "integration-id-feed-processor",
    # Add more bot IDs as discovered via users.me() or config
}


def _is_human_edit(last_edited_by_id: str) -> bool:
    """
    F3: UNA definición de "tocado-por-humano" = autor-humano + tiempo.
    
    Returns True if edited by human, False if edited by known bot.
    Safe default: unknown ID = human (conservative).
    """
    if not last_edited_by_id:
        return True  # No ID = assume human
    return last_edited_by_id not in KNOWN_BOT_IDS


def _was_edited_since_last_run(edited_time: str) -> bool:
    """
    F3+G1: Check if edit was since last successful pipeline run.
    
    G1: Fail-closed - if no edited_time, assume recent (True) to prevent auto-execution.
    Uses state file state/last_successful_run.json.
    Fallback: 7 days if no state file.
    """
    if not edited_time:
        return True  # G1: Fail-closed - no timestamp = assume recent
    
    state_file = Path("state/last_successful_run.json")
    if not state_file.exists():
        # Fallback: 7 days if no state file
        try:
            edited_dt = datetime.fromisoformat(edited_time.replace("Z", "+00:00"))
            return (datetime.now(edited_dt.tzinfo) - edited_dt).days < 7
        except:
            return True
    
    try:
        with open(state_file) as f:
            state = json.load(f)
            last_run = datetime.fromisoformat(state["last_run_time"])
            edited_dt = datetime.fromisoformat(edited_time.replace("Z", "+00:00"))
            return edited_dt > last_run
    except:
        return True  # Safe default: assume recent


def _was_touched_by_human(record: Dict[str, Any]) -> bool:
    """
    F3: Combined check - human author AND recent edit.
    """
    last_edited_by_id = record.get("last_edited_by_id", "")
    last_edited_time = record.get("last_edited_time", "")
    
    return _is_human_edit(last_edited_by_id) and _was_edited_since_last_run(last_edited_time)


# ── F11/G3: Guard record-level (field-block deferred) ───────────────────────────────────

def is_mutable(record: Dict[str, Any], actor: Actor) -> bool:
    """
    Predicado único de mutabilidad.
    
    G3: field-block Class-B deferred - implements record-level guard only.
    Field-level blocking requires Class-B set integration (deferred to future phase).
    
    Orden de evaluación:
    1. Protección manual (last_edited_time + last_edited_by)
    2. Terminalidad (única fuente: PROTECTED_STATUSES)
    3. Elegibilidad (estado actual vs actor)
    4. Cómputo (¿puede el actor calcular este campo?)
    
    Retorna True si el actor puede mutar el registro, False si está protegido.
    """
    # 1. Protección manual - máxima prioridad
    if _was_touched_by_human(record):
        logger.info(f"[PROTECTED] Edición manual reciente: {record.get('id', 'unknown')[:8]}")
        return False
    
    # 2. Terminalidad - única fuente de verdad
    current_status = record.get("Status")
    if current_status in [s.value for s in PROTECTED_STATUSES]:
        # Contratado es el caso más grave - protección absoluta sin excepción
        if current_status == Status.CONTRATADO.value:
            logger.warning(f"[PROTECTED_ABSOLUTE] Contratado: {record.get('id', 'unknown')[:8]}")
            return False
        
        # Otros estados protegidos - solo humano puede mutar
        if actor != Actor.HUMANO:
            logger.info(f"[PROTECTED] Estado protegido: {current_status} por {actor}")
            return False
    
    # 3. Elegibilidad - ¿puede este actor tocar este estado?
    if actor == Actor.INGESTA and current_status in [s.value for s in LIVE_APPLICATION_STATUSES]:
        return False
    
    # 4. Cómputo - ¿puede el actor calcular este campo específico?
    # (implementación específica por campo en el orquestador)
    
    return True


# ── F6: Complete Lifecycle Matrix + Manual Rule ───────────────────────────────

@dataclass
class Transition:
    """Transición individual en la matriz de ciclo de vida"""
    from_status: Optional[Status]  # None = desde cualquier estado no protegido
    event: str  # Nombre del evento/trigger
    actor: Actor  # Quién ejecuta la transición
    to_status: Optional[Status]  # None = manual (cualquier destino válido)
    gate: Callable[[Dict[str, Any], Actor], bool]  # Función que evalúa si la transición es válida
    reason_field: str  # Campo donde se guarda la razón
    requires_propose_log: bool = False  # True = log sin ejecutar (filas humanas/postulaciones vivas)
    auto_execute_on_operational: bool = False  # True = auto-ejecutar en filas operativas NO tocadas por humano


# Matriz de ciclo de vida - fuente única de verdad (F6: complete legs)
LIFECYCLE_MATRIX: list[Transition] = [
    # === Ingesta ===
    Transition(
        from_status=None,  # [ENTRY]
        event="ingesta_json",
        actor=Actor.INGESTA,
        to_status=Status.POR_REVISAR,  # Default
        gate=lambda r, a: True,  # Ingesta siempre crea
        reason_field="Notas",
        requires_propose_log=False
    ),
    
    # === F6: Producer for clean Objetivo ===
    Transition(
        from_status=None,
        event="create_objetivo",
        actor=Actor.HUMANO,
        to_status=Status.OBJETIVO,
        gate=lambda r, a: a == Actor.HUMANO,
        reason_field="Notas",
        requires_propose_log=False
    ),
    
    # === Flujo de aplicación (HUMANO) ===
    Transition(
        from_status=Status.OBJETIVO,
        event="iniciar_postulacion",
        actor=Actor.HUMANO,
        to_status=Status.POSTULANDO,
        gate=lambda r, a: a == Actor.HUMANO,
        reason_field="Notas",
        requires_propose_log=False
    ),
    
    Transition(
        from_status=Status.POSTULANDO,
        event="confirmar_envio",
        actor=Actor.HUMANO,
        to_status=Status.POSTULADO,
        gate=lambda r, a: a == Actor.HUMANO,
        reason_field="Notas",
        requires_propose_log=False
    ),
    
    Transition(
        from_status=Status.POSTULADO,
        event="resultado_negativo",
        actor=Actor.HUMANO,
        to_status=Status.RECHAZADO,
        gate=lambda r, a: a == Actor.HUMANO,
        reason_field="Notas",
        requires_propose_log=False
    ),
    
    Transition(
        from_status=Status.POSTULADO,
        event="resultado_positivo",
        actor=Actor.HUMANO,
        to_status=Status.EN_PROCESO,
        gate=lambda r, a: a == Actor.HUMANO,
        reason_field="Notas",
        requires_propose_log=False
    ),
    
    # === F6: Missing legs to Negociando/Sin Respuesta/Contratado ===
    Transition(
        from_status=Status.EN_PROCESO,
        event="progreso_negociacion",
        actor=Actor.HUMANO,
        to_status=Status.NEGOCIANDO,
        gate=lambda r, a: a == Actor.HUMANO,
        reason_field="Notas",
        requires_propose_log=False
    ),
    
    Transition(
        from_status=Status.NEGOCIANDO,
        event="sin_respuesta",
        actor=Actor.HUMANO,
        to_status=Status.SIN_RESPUESTA,
        gate=lambda r, a: a == Actor.HUMANO,
        reason_field="Notas",
        requires_propose_log=False
    ),
    
    Transition(
        from_status=Status.NEGOCIANDO,
        event="oferta_aceptada",
        actor=Actor.HUMANO,
        to_status=Status.CONTRATADO,
        gate=lambda r, a: a == Actor.HUMANO,
        reason_field="Notas",
        requires_propose_log=False
    ),
    
    Transition(
        from_status=Status.SIN_RESPUESTA,
        event="respuesta_recibida",
        actor=Actor.HUMANO,
        to_status=Status.NEGOCIANDO,
        gate=lambda r, a: a == Actor.HUMANO,
        reason_field="Notas",
        requires_propose_log=False
    ),
    
    # === F6: En Proceso → Rechazado ===
    Transition(
        from_status=Status.EN_PROCESO,
        event="rechazo_proceso",
        actor=Actor.HUMANO,
        to_status=Status.RECHAZADO,
        gate=lambda r, a: a == Actor.HUMANO,
        reason_field="Notas",
        requires_propose_log=False
    ),
    
    # === F6: Exploratorio transitions ===
    Transition(
        from_status=Status.EXPLORATORIO,
        event="promover_objetivo",
        actor=Actor.HUMANO,
        to_status=Status.OBJETIVO,
        gate=lambda r, a: a == Actor.HUMANO,
        reason_field="Notas",
        requires_propose_log=False
    ),
    
    Transition(
        from_status=Status.EXPLORATORIO,
        event="descartar",
        actor=Actor.HUMANO,
        to_status=Status.RETIRADO,
        gate=lambda r, a: a == Actor.HUMANO,
        reason_field="Notas",
        requires_propose_log=False
    ),
    
    # === Archivo (PIPELINE - 3 causas consolidadas) ===
    Transition(
        from_status=None,  # Cualquier estado no protegido
        event="url_failed",
        actor=Actor.PIPELINE,
        to_status=Status.EXPIRADA,
        gate=lambda r, a: is_mutable(r, a),
        reason_field="Notas",
        requires_propose_log=True,
        auto_execute_on_operational=True
    ),
    
    Transition(
        from_status=None,
        event="profile_misfit",
        actor=Actor.PIPELINE,
        to_status=Status.EXPIRADA,
        gate=lambda r, a: is_mutable(r, a),
        reason_field="Notas",
        requires_propose_log=True,
        auto_execute_on_operational=True
    ),
    
    Transition(
        from_status=None,
        event="nad_expired",
        actor=Actor.PIPELINE,
        to_status=Status.EXPIRADA,
        gate=lambda r, a: is_mutable(r, a),
        reason_field="Notas",
        requires_propose_log=True,
        auto_execute_on_operational=True
    ),
    
    # === No-transiciones explícitas (terminal × PIPELINE = prohibido) ===
    # Implementado en evaluate_transition: si from_status en PROTECTED_STATUSES
    # y actor != HUMANO, retorna None (transición prohibida)
]


def evaluate_transition(record: Dict[str, Any], event: str, actor: Actor) -> Optional[Transition]:
    """
    Evalúa si una transición es válida según la matriz de ciclo de vida.
    
    F6: Matriz completa con piernas faltantes.
    """
    current_status = record.get("Status")
    
    # No-transiciones explícitas: terminal × PIPELINE = prohibido
    if current_status in [s.value for s in PROTECTED_STATUSES] and actor != Actor.HUMANO:
        logger.warning(f"[PROHIBITED] Transición prohibida: {current_status} + {event} por {actor}")
        return None
    
    # Buscar transición en matriz primero
    for transition in LIFECYCLE_MATRIX:
        if transition.event != event:
            continue
        if transition.from_status is not None and transition.from_status.value != current_status:
            continue
        if transition.actor != actor:
            continue
        if not transition.gate(record, actor):
            continue
        
        return transition
    
    # F6: Manual rule - HUMANO(any→any within enum) = válido (fallback)
    if actor == Actor.HUMANO:
        current_status_enum = None
        try:
            current_status_enum = Status(current_status) if current_status else None
        except ValueError:
            pass  # Invalid status, but human can still edit
        
        # Human can edit any valid status
        if current_status_enum is None or current_status_enum in Status:
            # Return a synthetic transition for manual edits
            return Transition(
                from_status=current_status_enum,
                event="manual_edit",
                actor=Actor.HUMANO,
                to_status=None,  # Manual - any destination
                gate=lambda r, a: True,
                reason_field="Notas",
                requires_propose_log=False
            )
    
    # Transición no encontrada - REVIEW explícito
    logger.warning(f"[REVIEW] Transición no encontrada: {current_status} + {event} por {actor}")
    return None


# ── F2: Single Archive Path ───────────────────────────────────────────────────

def evaluate_flow(record: Dict[str, Any], actor: Actor) -> Dict[str, Any]:
    """
    F2: UN camino evaluate → propose/execute → archive_gate.
    
    Orden total de evaluación:
    protección-manual → terminalidad → elegibilidad → cómputo
    
    Retorna: dict con la decisión de flujo completa
    """
    # 1. Protección manual
    if not is_mutable(record, actor):
        return {
            "decision": "PROTECTED",
            "reason": "Edición manual reciente o estado terminal protegido"
        }
    
    # 2. Terminalidad - única fuente de verdad
    current_status = record.get("Status")
    if current_status in [s.value for s in TERMINAL_STATUSES]:
        return {
            "decision": "TERMINAL",
            "reason": f"Estado terminal: {current_status}"
        }
    
    # 3. Elegibilidad
    # (evaluar si el actor puede operar sobre este estado)
    
    # 4. Cómputo
    # (calcular Score, Gate_Decision, etc.)
    
    return {
        "decision": "COMPUTE",
        "reason": "Registro elegible para cómputo"
    }


def generate_propose_log(record: Dict[str, Any], transition: Transition, evidence: str) -> str:
    """
    F3: Genera entrada de propose-log con idempotencia.
    
    Formato: [PROPOSE] {actor} → {to_status}: {reason}
    Evidencia: {evidence}
    Página: {page_id}
    Timestamp: {timestamp}
    
    F3: Skip si ya existe [PROPOSE] idéntica abierta.
    """
    timestamp = datetime.now().isoformat()
    log_entry = (
        f"[PROPOSE] {transition.actor.value} → {transition.to_status.value if transition.to_status else 'MANUAL'}: {transition.event}\n"
        f"Evidencia: {evidence}\n"
        f"Página: {record.get('id', 'unknown')[:8]}\n"
        f"Timestamp: {timestamp}"
    )
    
    # F3: Check for duplicate propose log (more specific match)
    existing_notes = record.get("Notas", "")
    expected_prefix = f"[PROPOSE] {transition.actor.value} → {transition.to_status.value if transition.to_status else 'MANUAL'}: {transition.event}"
    if expected_prefix in existing_notes:
        logger.info(f"[F3] PROPOSE log ya existe, skipping: {record.get('id', 'unknown')[:8]}")
        return existing_notes
    
    # Escribir en Notas del registro
    updated_notes = f"{existing_notes}\n\n{log_entry}" if existing_notes else log_entry
    
    return updated_notes


def execute_transition(record: Dict[str, Any], transition: Transition, evidence: str) -> Dict[str, Any]:
    """
    F2+G2: Ejecuta transición real (solo después de aprobación o auto-ejecución).
    
    G2: Unificado con archive_gate - incluye Next_Action cuando es archivo.
    Llamado por execute_transition_with_propose_log después de aprobación.
    """
    if transition.to_status:
        payload = {
            "Status": transition.to_status.value,
            "Notas": generate_archive_notes(transition.event, evidence)
        }
        
        # G2: Include Next_Action for archive transitions
        if transition.to_status in TERMINAL_STATUSES:
            payload["Next_Action"] = NextAction.ARCHIVAR.value
        
        # Append existing notes
        existing_notes = record.get("Notas", "")
        if existing_notes:
            payload["Notas"] = f"{existing_notes}\n\n{payload['Notas']}"
        
        return payload
    return {}


def execute_transition_with_propose_log(
    record: Dict[str, Any], 
    transition: Transition, 
    evidence: str, 
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    F2+F3: Ejecuta transición con modelo de approve-log.
    
    Lógica:
    - Si requires_propose_log=True y registro es humano/postulación viva → generate_propose_log + NO ejecutar
    - Si requires_propose_log=True y registro es operativo NO tocado por humano → auto-ejecutar
    - Si requires_propose_log=False → ejecutar directo
    """
    current_status = record.get("Status")
    is_human_or_live_app = (
        current_status in [s.value for s in LIVE_APPLICATION_STATUSES] or
        _was_touched_by_human(record)
    )
    
    if transition.requires_propose_log and is_human_or_live_app:
        # Propose-log sin ejecutar
        updated_notes = generate_propose_log(record, transition, evidence)
        logger.info(f"[PROPOSE] Transición propuesta para {record.get('id', 'unknown')[:8]}")
        logger.info(updated_notes)
        return {"Notas": updated_notes}
    
    if transition.requires_propose_log and transition.auto_execute_on_operational and not is_human_or_live_app:
        # Auto-ejecutar en filas operativas NO tocadas por humano
        if not dry_run:
            return execute_transition(record, transition, evidence)
        else:
            logger.info(f"[DRY RUN] Auto-ejecutaría transición para {record.get('id', 'unknown')[:8]}")
            return {}
    
    # Ejecutar directo
    if not dry_run:
        return execute_transition(record, transition, evidence)
    else:
        logger.info(f"[DRY RUN] Ejecutaría transición para {record.get('id', 'unknown')[:8]}")
        return {}


def archive_gate(record: Dict[str, Any], reason: str, evidence: str, actor: Actor, timestamp: str) -> Dict[str, Any]:
    """
    F2: Gate de archivo consolidado - une F2, F3.5, F3.5.1 en una sola transición.
    
    Retorna: dict con los campos a escribir de forma atómica
    {
        "Status": Status.EXPIRADA,
        "Next_Action": NextAction.ARCHIVAR,
        "Notas": generate_archive_notes(reason, evidence)
    }
    """
    if not is_mutable(record, actor):
        raise PermissionError(f"Registro protegido contra archivo por {actor}")
    
    # Generar nota única - cierra bug de doble-nota
    notes = generate_archive_notes(reason, evidence)
    
    # Si hay notas existentes, appendear
    existing_notes = record.get("Notas", "")
    if existing_notes:
        notes = f"{existing_notes}\n\n{notes}"
    
    return {
        "Status": Status.EXPIRADA.value,
        "Next_Action": NextAction.ARCHIVAR.value,
        "Notas": notes
    }


# ── F13b: Write-back + Batch Runner ──────────────────────────────────────────
# normalize_record() corrige Status en memoria automáticamente (F13), pero
# alguien tiene que persistirlo en Notion. Estas dos funciones cierran ese
# último tramo sin acoplar tracker_flow.py a notion_client en import time
# (el cliente se pasa como parámetro, con duck-typing sobre .pages.update).

def apply_status_sync_writeback(notion_client: Any, flat_record: Dict[str, Any]) -> bool:
    """
    F13b: Si flat_record trae _status_synced_from_outcome=True (seteado por
    sync_status_from_outcome dentro de normalize_record), escribe el Status
    corregido de vuelta a Notion. No vuelve a llamar a is_mutable() — la
    corrección Outcome→Status es una reconciliación de integridad, no una
    transición de negocio arbitraria, y Contratado es admisible sin importar
    el actor (F12: Contratado siempre gana).

    Retorna True si escribió, False si no había nada pendiente.
    """
    if not flat_record.get("_status_synced_from_outcome"):
        return False

    page_id = flat_record.get("id", "")
    if not page_id:
        logger.warning("[F13b] Sync pendiente sin page id — no se puede escribir")
        return False

    notion_client.pages.update(
        page_id=page_id,
        properties=to_notion_properties({"Status": flat_record["Status"]}),
    )
    logger.info(f"[F13b] Status sincronizado en Notion: {page_id[:8]} → {flat_record['Status']}")
    return True


def run_outcome_status_sync(notion_client: Any, database_id: str) -> Dict[str, int]:
    """
    F13b: Corre la reconciliación Outcome→Status sobre TODO el Tracker en una
    sola invocación — este es el punto de entrada pensado para automatizarse
    vía cron/launchd/Raycast (no hay webhooks nativos de Notion en este stack,
    así que "automático" aquí significa "un comando, programable", no
    "reactivo en tiempo real").

    Uso típico (crontab o launchd, ejecutar cada N minutos/horas):
        python3 -c "
        from notion_client import Client
        from tracker_flow import run_outcome_status_sync
        import os
        client = Client(auth=os.environ['NOTION_TOKEN'])
        run_outcome_status_sync(client, os.environ['NOTION_DATA_SOURCE_ID'])
        "

    NOTA (2026-09-11, verificado en DRY RUN): con notion-client en la versión
    instalada (API version 2025-09-03), NO existe client.databases.query() —
    ese endpoint se movió a client.data_sources.query(). El parámetro
    `database_id` de esta función debe recibir el DATA SOURCE ID
    (442938be-fc42-828f-b72e-076818d65a5b), no el DATABASE ID
    (596938be-fc42-836b-aea7-814a1491bd47) — no son intercambiables.

    Retorna conteos: {"checked": N, "synced": N, "skipped": N}.
    """
    checked = synced = skipped = 0
    cursor: Optional[str] = None

    while True:
        kwargs: Dict[str, Any] = {"data_source_id": database_id, "page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor
        response = notion_client.data_sources.query(**kwargs)

        for api_record in response.get("results", []):
            checked += 1
            flat_record = normalize_record(api_record)  # F13 corre adentro
            if apply_status_sync_writeback(notion_client, flat_record):
                synced += 1
            else:
                skipped += 1

        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")

    logger.info(f"[F13b] Reconciliación completa: {checked} revisados, {synced} sincronizados")
    return {"checked": checked, "synced": synced, "skipped": skipped}


def to_notion_properties(value_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convierte valores planos a shapes API Notion.
    """
    notion_props = {}
    for key, value in value_dict.items():
        if key == "Status":
            notion_props["Status"] = {"select": {"name": value}}
        elif key == "Next_Action":
            notion_props["Next_Action"] = {"select": {"name": value}}
        elif key == "Notas":
            notion_props["Notas"] = {"rich_text": [{"text": {"content": str(value)[:2000]}}]}
        # Agregar más campos según schema
    return notion_props


def generate_archive_notes(reason: str, details: str = "") -> str:
    """
    Genera mensaje estandarizado para campo Notas cuando se archiva una vacante.
    Formato: [ARCHIVO] Razón: {razón_determinista}
    {detalles_específicos_si_aplica}
    """
    message = f"[ARCHIVO] Razón: {reason}"
    if details:
        message += f"\n{details}"
    return message


# ── F7: REVIEW Gate Design ───────────────────────────────────────────────────

def evaluate_review_gate(record: Dict[str, Any], field: Optional[str] = None) -> Dict[str, Any]:
    """
    F7+G5: REVIEW gate designed with field parameter.
    
    G5/H2: Wiring deferred - gate designed but not invoked in current flow.
    Safe default BLOCKED. Exact insertion point: `is_mutable` paso 3
    (elegibilidad) — ver comentario H2 en el return.
    
    When a record would be moved to "Por Revisar", this gate:
    1. Checks if the transition is valid
    2. If not, blocks and suggests resolution to "Objetivo"
    
    Args:
        record: Normalized flat record
        field: Optional field that triggered the REVIEW (e.g., "Status", "Score")
    
    Returns:
        dict with gate decision and suggested resolution
    """
    current_status = record.get("Status", "")
    
    # If already in review, suggest resolution to Objetivo
    if current_status == Status.POR_REVISAR.value:
        return {
            "decision": GateDecision.REVIEW_NEEDED,
            "reason": f"Registro en estado Por Revisar (triggered by field: {field or 'unknown'})",
            "suggested_resolution": Status.OBJETIVO.value,
            "action": "review_to_objetivo"
        }
    
    # H2: Safe default = BLOCKED while wiring deferred (G5). Exact insertion point
    # (implementation phase): `is_mutable` paso 3 (elegibilidad) — el orquestador
    # consulta evaluate_review_gate(record, field) antes de permitir cómputo Class-B
    # en registros Por Revisar; resolución → Objetivo.
    return {
        "decision": GateDecision.BLOCKED,
        "reason": f"Transición a Por Revisar bloqueada (field: {field or 'unknown'}) - wiring deferred per G5/H2, safe default BLOCKED",
        "suggested_resolution": Status.OBJETIVO.value,
        "action": "block_review_deferred"
    }


# ── F4: Diff on Normalized Records ─────────────────────────────────────────────

def diff_records(old_record: Dict[str, Any], new_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    F4: Diff sobre plano normalizado con tipos preservados.
    
    Extract value accepts both shapes, and types are preserved during comparison.
    This prevents numeric vs string comparison bugs (e.g., Score 42 vs "42").
    """
    changes = {}
    
    for key in set(list(old_record.keys()) + list(new_record.keys())):
        old_val = old_record.get(key)
        new_val = new_record.get(key)
        
        # Normalize both values for comparison
        old_normalized = extract_value(old_val) if old_val is not None else None
        new_normalized = extract_value(new_val) if new_val is not None else None
        
        # Type-preserving comparison
        if old_normalized != new_normalized:
            changes[key] = {
                "old": old_normalized,
                "new": new_normalized
            }
    
    return changes


# ── F12: Survivor Ranking (Contratado First) ─────────────────────────────────

SURVIVOR_PRIORITY = [
    Status.CONTRATADO,  # F12: Contratado first always
    Status.POSTULADO,
    Status.EN_PROCESO,
    Status.NEGOCIANDO,
    Status.SIN_RESPUESTA,
    Status.POSTULANDO,
    Status.OBJETIVO,
    Status.EXPLORATORIO,
    Status.POR_REVISAR,
    Status.EXPIRADA,
    Status.RECHAZADO,
    Status.RETIRADO,
]


def get_survivor_rank(status: str) -> int:
    """
    F12: Get survivor rank for dedup.
    
    Lower rank = higher priority (Contratado = 0).
    Unknown status = lowest priority.
    """
    try:
        status_enum = Status(status)
        return SURVIVOR_PRIORITY.index(status_enum)
    except ValueError:
        return len(SURVIVOR_PRIORITY)  # Lowest priority for unknown


LAYER_SURVIVOR_PRIORITY = {
    "L1": 3,
    "L2": 2,
    "L3": 1,
    "N/A": 0,
}


def get_layer_rank(layer: Any) -> int:
    """F12/Q-H7: Traduce el valor string de layer a rank numérico."""
    return LAYER_SURVIVOR_PRIORITY.get(layer, 0)


def choose_survivor(records: list[Dict[str, Any]]) -> Dict[str, Any]:
    """
    F12: Choose survivor from duplicate records.
    
    Priority:
    1. Status rank (Contratado first)
    2. Score (higher is better)
    3. Has URL (preferred)
    4. Layer (higher number first — H7: direction to confirm, see Q-H7)
    """
    if not records:
        raise ValueError("No records to choose from")
    
    # Sort by survivor priority
    sorted_records = sorted(
        records,
        key=lambda r: (
            get_survivor_rank(r.get("Status", "")),
            -(r.get("Score", 0) or 0),  # Higher score first
            0 if r.get("URL") else 1,  # H7: Has URL first (was inverted: 1-if-URL sorted URL-less first)
            -get_layer_rank(r.get("layer"))  # Higher layer first
        )
    )
    
    return sorted_records[0]


# ── F9: Deployment Configuration ──────────────────────────────────────────────

# F9a: Devin opens PR, Mau merges (NOT Claude via MCP)
# F9b: Code branch separate from docs branch
# F9c: Order freeze→merge→patch
# F9d: Rollback script available
# F9e: Row disposition mapping for deleted values

DELETED_VALUE_MAPPINGS = {
    # H1: F9e disposition (value→value). fetch_status describe CANAL (dónde se
    # intentó fetch) mientras Fetch describe RESULTADO (qué pasó): no existe
    # mapping estático canal→resultado. Toda fila migrada entra con default +
    # estrategia "revalidate" (el primer run re-evalúa fetch real).
    # Default "Accesible" (no destructivo, lección v9.14.5: "Bloqueado" podría
    # disparar rutas de archivo masivo). Vocabulario Fetch PARAMÉTRICO — validar
    # contra schema vivo en despliegue (ver Q-H1 en handoff).
    "Status": {
        "Archivar": "Retirado"  # Archived rows → Retirado
    },
    "Fetch": {
        "aggregator": {"fetch": "Accesible", "strategy": "revalidate", "parametric": True},
        "career_page": {"fetch": "Accesible", "strategy": "revalidate", "parametric": True},
        "filled": {"fetch": "Accesible", "strategy": "revalidate", "parametric": True},
    },
    "Fetch_vocab_proposed": ["Accesible", "Bloqueado"],  # H1: PARAMÉTRICO, ver Q-H1
}


# ── State Management ─────────────────────────────────────────────────────────

def persist_last_run_timestamp():
    """
    Persist timestamp of last successful run.
    Used by F3 human edit detection.
    """
    state_dir = Path("state")
    state_dir.mkdir(exist_ok=True)
    
    state_file = state_dir / "last_successful_run.json"
    with open(state_file, "w") as f:
        json.dump({"last_run_time": datetime.now().isoformat()}, f)


# ── A3/A5: Confirmation Mechanism ─────────────────────────────────────────────

# A3: _move_to_archivo requires explicit confirmation
# Mechanism: propose-log + APROBAR_WRITE via Claude session
# Consumer: vantage-tidy-opportunities-tracker skill

# A5: Test coverage map required
# Map: test ↔ cell/branch
# Bodies in implementation
# Fake mirrors client.pages.update or documents adapter


if __name__ == "__main__":
    # Self-test
    print("Testing tracker_flow.py imports...")
    print(f"Status values: {[s.value for s in Status]}")
    print(f"Next_Action values: {[a.value for a in NextAction]}")
    print(f"Gate_Decision values: {[d.value for d in GateDecision]}")
    print(f"Actor values: {[a.value for a in Actor]}")
    print("✓ All imports successful")
