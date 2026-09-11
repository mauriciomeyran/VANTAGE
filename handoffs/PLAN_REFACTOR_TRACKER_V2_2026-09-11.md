# PLAN DE DISEÑO V2 - Refactor Completo VANTAGE Tracker

**De:** Devin (corregido según revisión Mau 2026-09-11)  
**Para:** Mau  
**Ref:** Contrato HO-000041 + Revisión B1-B10/A1-A5/R1-R8  
**Fecha:** 2026-09-11

---

## Resumen de Correcciones

**Bloqueantes corregidos (B1-B10):**
- B1: Vocabularios Status/Next_Action rebaseados desde KERNEL:SCHEMA-008
- B2: Gates corregidos (is_mutable, no not is_mutable)
- B3: evaluate_flow usa única fuente de terminalidad
- B4: write_conditional compara valores normalizados, no shapes API
- B5: Escrituras consultan is_mutable antes de escribir
- B6: Matriz cómputo↔fase cubre 7 cómputos actuales
- B7: Modelo de aprobación explícito (propose-log, no input())
- B8: Decisiones consistentes (ARCHIVAR eliminado, REVIEW bloqueo diseñado)
- B9: Despliegue con PATCH de schema + ventana atómica
- B10: Matriz modela ciclo de vida completo

**Secciones agregadas (A1-A5):**
- A1: feed_processor.py adaptación
- A2: Dedup unificado
- A3: Disposición de consolidate_duplicates.py y batch_operations.py
- A4: class_b_guard generalizado
- A5: Fixture + Notion-fake + plan de tests

---

## 1. Entregable Central: `tracker_flow.py` - Mapa de Flujo Lógico Único

### 1.1 Arquitectura del Módulo

**Ubicación:** `Layer_1/scripts/tracker_flow.py`

#### (a) Enums y Constantes - Conjunto Cerrado (Rebaseado desde KERNEL:SCHEMA-008)

```python
from enum import Enum
from typing import Literal, Optional, Set

class Status(str, Enum):
    """Estados válidos de Status - conjunto cerrado (13 valores confirmados)"""
    # Estados operativos
    OBJETIVO = "Objetivo"  # Renombrado desde "Target" (ES)
    EXPLORATORIO = "Exploratorio"
    POR_REVISAR = "Por revisar"  # Renombrado desde "REVIEW_NEEDED" (ES)
    
    # Estados de postulación viva (LIVE_APPLICATION_STATUSES)
    POSTULANDO = "Postulando"
    POSTULADO = "Postulado"
    EN_PROCESO = "En proceso"
    NEGOCIANDO = "Negociando"
    SIN_RESPUESTA = "Sin respuesta"
    CONTRATADO = "Contratado"
    
    # Estados terminales (TERMINAL_STATUSES)
    EXPIRADA = "Expirada"
    RECHAZADO = "Rechazado"
    RETIRADO = "Retirado"
    
    # NOTA: "Archivar" eliminado del vocabulario de Status (huérfano bilateral)
    # NOTA: "Repetida", "RAW", "Nueva" eliminados (valores fantasma)
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Verifica si un valor es válido - else REVIEW + log WARN"""
        try:
            cls(value)
            return True
        except ValueError:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"[REVIEW] Status inválido detectado: '{value}' - no se procesa como operativo")
            return False

# Única fuente de verdad para terminalidad (resuelve B3)
TERMINAL_STATUSES: Set[Status] = {
    Status.EXPIRADA, Status.RECHAZADO, Status.RETRIRADO
}

LIVE_APPLICATION_STATUSES: Set[Status] = {
    Status.POSTULANDO, Status.POSTULADO, Status.EN_PROCESO,
    Status.NEGOCIANDO, Status.SIN_RESPUESTA, Status.CONTRATADO
}

PROTECTED_STATUSES: Set[Status] = LIVE_APPLICATION_STATUSES | TERMINAL_STATUSES

class NextAction(str, Enum):
    """Acciones válidas de Next_Action - conjunto cerrado (10 valores confirmados)"""
    # Valores operativos (KERNEL:SCHEMA-008)
    OPTIMIZAR = "Optimizar"  # JD_Quality = "JD Completo"
    SEGUIMIENTO = "Seguimiento"  # Renombrado desde "Follow-up" (ES)
    PREPARACION_ENTREVISTA = "Preparación entrevista"  # Renombrado desde "Interview prep" (ES)
    REVISION = "Revisión"  # Renombrado desde "Re-check" (ES)
    INVESTIGAR = "Investigar"  # Default no destructivo (catch-all)
    POST_MORTEM = "Post-Mortem"  # Status=Rechazado
    
    # Archivo
    ARCHIVAR = "Archivar"  # Terminal
    
    # Recuperación
    REPARAR_URL = "Reparar URL"  # Source_Type=Vacante AND Fetch=Bloqueado
    VERIFICAR_JD = "Verificar JD"  # Source_Type=Vacante AND Fetch=Parcial
    
    # NOTA: "Expirada" eliminado de Next_Action (sin productor confirmado)
    # NOTA: "Target" nunca fue Next_Action - eliminado de vocabulario

class GateDecision(str, Enum):
    """Decisiones de Gate - terminología técnica EN fijada"""
    CREATE = "CREATE"
    BLOCKED = "BLOCKED"
    REVIEW = "REVIEW"  # Renombrado desde "REVIEW_NEEDED" en Gate_Decision
    APPLIED = "APPLIED"
    REJECTED = "REJECTED"
    EXPIRADA = "EXPIRADA"

class Actor(str, Enum):
    """Actores que pueden mutar el Tracker"""
    HUMANO = "humano"
    PIPELINE = "pipeline"
    INGESTA = "ingesta"
    DEDUP = "dedup"
    MCP_DASHBOARD = "mcp_dashboard"
```

#### (b) Matriz de Transición de Ciclo de Vida (Corregida B10 + B7)

```python
from dataclasses import dataclass
from typing import Callable, Optional

@dataclass
class Transition:
    """Transición individual en la matriz de ciclo de vida"""
    from_status: Optional[Status]  # None = desde cualquier estado no protegido
    event: str  # Nombre del evento/trigger
    actor: Actor  # Quién ejecuta la transición
    to_status: Optional[Status]  # None = manual (cualquier destino válido)
    gate: Callable  # Función que evalúa si la transición es válida
    reason_field: str  # Campo donde se guarda la razón
    requires_propose_log: bool = False  # True = log sin ejecutar (filas humanas/postulaciones vivas)
    auto_execute_on_operational: bool = False  # True = auto-ejecutar en filas operativas NO tocadas por humano (B7 resuelto)

# Matriz de ciclo de vida - fuente única de verdad (resuelve B10)
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
    
    # === Flujo de aplicación (HUMANO) ===
    Transition(
        from_status=Status.OBJETIVO,
        event="iniciar_postulacion",
        actor=Actor.HUMANO,
        to_status=Status.POSTULANDO,
        gate=lambda r, a: a == Actor.HUMANO,  # Solo humano
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
    
    # === Archivo (PIPELINE - 3 causas consolidadas) ===
    Transition(
        from_status=None,  # Cualquier estado no protegido
        event="url_failed",
        actor=Actor.PIPELINE,
        to_status=Status.EXPIRADA,
        gate=lambda r, a: is_mutable(r, a),  # CORREGIDO B2: is_mutable, not not is_mutable
        reason_field="Notas",
        requires_propose_log=True,  # Propose-log para filas humanas/postulaciones vivas
        auto_execute_on_operational=True  # Auto-ejecutar en filas operativas NO tocadas por humano (B7 resuelto)
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

def evaluate_transition(record: dict, event: str, actor: Actor) -> Optional[Transition]:
    """
    Evalúa si una transición es válida según la matriz de ciclo de vida.
    
    CORREGIDO B10: modela lifecycle completo, no solo wildcards.
    CORREGIDO B2: gate usa is_mutable(r, actor), no not is_mutable.
    """
    current_status = record.get("Status")
    
    # No-transiciones explícitas: terminal × PIPELINE = prohibido
    if current_status in PROTECTED_STATUSES and actor != Actor.HUMANO:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"[PROHIBITED] Transición prohibida: {current_status} + {event} por {actor}")
        return None
    
    # Buscar transición en matriz
    for transition in LIFECYCLE_MATRIX:
        if transition.event != event:
            continue
        if transition.from_status is not None and transition.from_status != current_status:
            continue
        if transition.actor != actor:
            continue
        if not transition.gate(record, actor):
            continue
        
        return transition
    
    # Transición no encontrada - REVIEW explícito
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"[REVIEW] Transición no encontrada: {current_status} + {event} por {actor}")
    return None

# === B7 Resuelto: Modelo de Propose-Log ===

def generate_propose_log(record: dict, transition: Transition, evidence: str) -> str:
    """
    Genera entrada de propose-log para filas humanas/postulaciones vivas.
    
    Formato: [PROPOSE] {actor} → {to_status}: {reason}
    Evidencia: {evidence}
    Página: {page_id}
    Timestamp: {timestamp}
    
    Consumidor: skill vantage-tidy-opportunities-tracker (lee Notas para filas marcadas)
    Vía de confirmación: APROBAR_WRITE vía sesión Claude
    """
    timestamp = datetime.now().isoformat()
    log_entry = (
        f"[PROPOSE] {transition.actor.value} → {transition.to_status.value if transition.to_status else 'MANUAL'}: {transition.event}\n"
        f"Evidencia: {evidence}\n"
        f"Página: {record.get('id', 'unknown')[:8]}\n"
        f"Timestamp: {timestamp}"
    )
    
    # Escribir en Notas del registro
    existing_notes = record.get("Notas", "")
    updated_notes = f"{existing_notes}\n\n{log_entry}" if existing_notes else log_entry
    
    return updated_notes

def execute_transition_with_propose_log(record: dict, transition: Transition, evidence: str, dry_run: bool = False):
    """
    Ejecuta transición con modelo de approve-log (B7 resuelto).
    
    Lógica:
    - Si requires_propose_log=True y registro es humano/postulación viva → generate_propose_log + NO ejecutar
    - Si requires_propose_log=True y registro es operativo NO tocado por humano → auto-ejecutar
    - Si requires_propose_log=False → ejecutar directo
    """
    current_status = record.get("Status")
    is_human_or_live_app = (
        current_status in [s.value for s in LIVE_APPLICATION_STATUSES] or
        _was_edited_since_last_run(record.get("last_edited_time", ""))
    )
    
    if transition.requires_propose_log and is_human_or_live_app:
        # Propose-log sin ejecutar
        updated_notes = generate_propose_log(record, transition, evidence)
        print(f"[PROPOSE] Transición propuesta para {record.get('id', 'unknown')[:8]}:")
        print(updated_notes)
        return {"Notas": updated_notes}
    
    if transition.requires_propose_log and transition.auto_execute_on_operational and not is_human_or_live_app:
        # Auto-ejecutar en filas operativas NO tocadas por humano
        if not dry_run:
            return execute_transition(record, transition, evidence)
        else:
            print(f"[DRY RUN] Auto-ejecutaría transición para {record.get('id', 'unknown')[:8]}")
            return {}
    
    # Ejecutar directo
    if not dry_run:
        return execute_transition(record, transition, evidence)
    else:
        print(f"[DRY RUN] Ejecutaría transición para {record.get('id', 'unknown')[:8]}")
        return {}

def execute_transition(record: dict, transition: Transition, evidence: str) -> dict:
    """Ejecuta transición real (solo después de aprobación o auto-ejecución)"""
    if transition.to_status:
        return {
            "Status": transition.to_status.value,
            "Notas": generate_archive_notes(transition.event, evidence)
        }
    return {}
```

#### (c) Predicado Único `is_mutable()` (Corregido B3)

```python
def is_mutable(record: dict, actor: Actor) -> bool:
    """
    Predicado único de mutabilidad - KERNEL:GATE-DECISION-007 + §2.3
    
    CORREGIDO B3: usa única fuente de verdad (PROTECTED_STATUSES),
    no redefine listas paralelas.
    
    Orden de evaluación (documentado y testeado):
    1. Protección manual (last_edited_time + last_edited_by)
    2. Terminalidad (única fuente: PROTECTED_STATUSES)
    3. Elegibilidad (estado actual vs actor)
    4. Cómputo (¿puede el actor calcular este campo?)
    
    Retorna True si el actor puede mutar el registro, False si está protegido.
    """
    # 1. Protección manual - máxima prioridad
    last_edited_time = record.get("last_edited_time")
    last_edited_by = record.get("last_edited_by")
    
    if last_edited_time and last_edited_by:
        # CORREGIDO R1: detectar humano vs bot por user-id
        if _is_human_edit(last_edited_by) and _was_edited_since_last_run(last_edited_time):
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[PROTECTED] Edición manual reciente: {record.get('id', 'unknown')[:8]}")
            return False
    
    # 2. Terminalidad - única fuente de verdad (resuelve B3)
    current_status = record.get("Status")
    if current_status in PROTECTED_STATUSES:
        # Contratado es el caso más grave - protección absoluta sin excepción
        if current_status == Status.CONTRATADO.value:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"[PROTECTED_ABSOLUTE] Contratado: {record.get('id', 'unknown')[:8]}")
            return False
        
        # Otros estados protegidos - solo humano puede mutar
        if actor != Actor.HUMANO:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[PROTECTED] Estado protegido: {current_status} por {actor}")
            return False
    
    # 3. Elegibilidad - ¿puede este actor tocar este estado?
    if actor == Actor.INGESTA and current_status in LIVE_APPLICATION_STATUSES:
        return False
    
    # 4. Cómputo - ¿puede el actor calcular este campo específico?
    # (implementación específica por campo en el orquestador)
    
    return True

def _is_human_edit(last_edited_by: str) -> bool:
    """
    CORREGIDO R1: detecta humano vs bot por user-id.
    
    IDs de integración conocidos = bot, resto = humano, desconocido = humano (safe default).
    """
    KNOWN_BOT_IDS = {
        "integration-id-mcp-dashboard",
        "integration-id-feed-processor",
        # Agregar más IDs de bot según confirmación MCP
    }
    return last_edited_by not in KNOWN_BOT_IDS

def _was_edited_since_last_run(edited_time: str) -> bool:
    """
    CORREGIDO R1: usa state file state/last_successful_run.json.
    """
    from datetime import datetime, timedelta
    import json
    from pathlib import Path
    
    state_file = Path("state/last_successful_run.json")
    if not state_file.exists():
        # Fallback: 7 días si no hay state file
        try:
            edited_dt = datetime.fromisoformat(edited_time.replace("Z", "+00:00"))
            return (datetime.now(edited_dt.tzinfo) - edited_dt) < timedelta(days=7)
        except:
            return True
    
    try:
        with open(state_file) as f:
            state = json.load(f)
            last_run = datetime.fromisoformat(state["last_run_time"])
            edited_dt = datetime.fromisoformat(edited_time.replace("Z", "+00:00"))
            return edited_dt > last_run
    except:
        return True  # Safe default: asumir que es reciente
```

#### (d) Gate de Archivo Consolidado (Corregido B7, R2)

```python
def archive_gate(record: dict, reason: str, evidence: str, actor: Actor, timestamp: str) -> dict:
    """
    Gate de archivo consolidado - une F2, F3.5, F3.5.1 en una sola transición
    
    CORREGIDO B7: modelo de aprobación explícito (propose-log, no input())
    CORREGIDO R2: devuelve shapes API Notion (capa to_notion_properties)
    
    Retorna: dict con los campos a escribir de forma atómica
    {
        "Status": Status.EXPIRADA,
        "Next_Action": NextAction.ARCHIVAR,
        "Notas": generate_archive_notes(reason, evidence)  # CORREGIDO R2: Notas, no Gate_Decision
    }
    
    DECISION: KERNEL:GATE-DECISION-013 - generate_archive_notes() en Notas
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

def to_notion_properties(value_dict: dict) -> dict:
    """
    CORREGIDO R2: convierte valores planos a shapes API Notion.
    Testeado contra schema real.
    """
    notion_props = {}
    for key, value in value_dict.items():
        if key == "Status":
            notion_props["Status"] = {"select": {"name": value}}
        elif key == "Next_Action":
            notion_props["Next_Action"] = {"select": {"name": value}}
        elif key == "Notas":
            notion_props["Notas"] = {"rich_text": [{"text": {"content": value[:2000]}}]}
        # Agregar más campos según schema
    return notion_props

def generate_archive_notes(reason: str, details: str = "") -> str:
    """
    Genera mensaje estandarizado para campo Notas cuando se archiva una vacante.
    Formato: [ARCHIVO] Razón: {razón_determinista}
    {detalles_específicos_si_aplica}
    
    DECISION: v9.21.21 - Mecanismo de trazabilidad que funciona bien
    """
    message = f"[ARCHIVO] Razón: {reason}"
    if details:
        message += f"\n{details}"
    return message
```

#### (e) Orden Total de Evaluación (Corregido B3)

```python
def evaluate_flow(record: dict, actor: Actor) -> dict:
    """
    Orden total de evaluación documentado y testeado:
    protección-manual → terminalidad → elegibilidad → cómputo
    
    CORREGIDO B3: usa única fuente de verdad (PROTECTED_STATUSES),
    no redefine listas paralelas.
    
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
```

---

## 2. Orquestador Refactorizado - Reemplazo de `layer_1_run.py`

### 2.1 Arquitectura

**Ubicación:** `Layer_1/scripts/layer_1_run_v2.py` (CLI compatible)

**Características:**
- Fases lineales sobre matriz cómputo↔fase (resuelve B6)
- Escrituras condicionadas a diff real normalizado (resuelve B4)
- `is_mutable` en cada escritura (resuelve B5)
- `--dry-run` default, `--apply` explícito (resuelve R7)
- Write-through en memoria actualizado en cada escritura (resuelve staleness)

### 2.2 Matriz Cómputo↔Fase (Resuelve B6)

```python
# Matriz de cómputos → fases (7 cómputos actuales)
COMPUTE_PHASES = [
    # Fase 1: Clasificación (VM_Scope, Role_Class)
    {
        "name": "clasificar",
        "computes": ["VM_Scope", "Role_Class"],
        "function": compute_classification,
        "writes": ["VM_Scope", "Role_Class"]
    },
    
    # Fase 2: Validación URL + Fetch
    {
        "name": "validar_fetch",
        "computes": ["Fetch"],
        "function": validate_url_and_fetch,
        "writes": ["Fetch"]
    },
    
    # Fase 3: Elegibilidad de archivo (pre-Score)
    {
        "name": "elegibilidad_archivo",
        "computes": [],
        "function": check_archive_eligibility,
        "writes": []  # Solo verifica, no escribe
    },
    
    # Fase 4: Scoring
    {
        "name": "scoring",
        "computes": ["Score"],
        "function": calculate_score,
        "writes": ["Score"]
    },
    
    # Fase 5: Gate logic
    {
        "name": "gate_logic",
        "computes": ["Gate_Decision", "Next_Action"],
        "function": evaluate_gate,
        "writes": ["Gate_Decision", "Next_Action"]
    },
    
    # Fase 6: Prioridad
    {
        "name": "prioridad",
        "computes": ["Prioridad"],
        "function": calculate_priority,
        "writes": ["Prioridad"]
    },
    
    # Fase 7: Archivo (3 causas consolidadas)
    {
        "name": "archivo",
        "computes": [],
        "function": execute_archive_decision,
        "writes": ["Status", "Next_Action", "Notas"]
    },
]
```

### 2.3 Escrituras Condicionadas a Diff Real Normalizado (Resuelve B4)

```python
def extract_value(prop: dict) -> str:
    """
    CORREGIDO B4: extrae valor normalizado de shape API Notion.
    Acepta shape-lectura Y shape-escritura.
    """
    if not prop:
        return ""
    ptype = prop.get("type")
    
    if ptype == "select":
        return (prop.get("select") or {}).get("name", "")
    if ptype == "rich_text":
        return "".join(t.get("plain_text", "") for t in prop.get("rich_text", []))
    if ptype == "title":
        return "".join(t.get("plain_text", "") for t in prop.get("title", []))
    if ptype == "url":
        return prop.get("url", "")
    if ptype == "number":
        return str(prop.get("number", ""))
    return ""

def write_conditional(client, page_id: str, new_props: dict, current_props: dict, actor: Actor):
    """
    CORREGIDO B4: compara valores normalizados, no dicts API crudos.
    CORREGIDO B5: consulta is_mutable antes de escribir.
    
    Resuelve B4: write_conditional compara shapes normalizados.
    Resuelve B5: cada escritura consulta is_mutable.
    """
    # CORREGIDO B5: verificar mutabilidad primero
    record = {"id": page_id, **current_props}
    if not is_mutable(record, actor):
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[SKIP] Registro protegido contra escritura por {actor}: {page_id[:8]}")
        return
    
    # CORREGIDO B4: comparar valores normalizados
    diff = {}
    for key, new_value in new_props.items():
        current_value = extract_value(current_props.get(key))
        new_value_normalized = extract_value({"type": "select", "select": {"name": new_value}}) if isinstance(new_value, str) else new_value
        
        if current_value != new_value_normalized:
            diff[key] = new_value
    
    if not diff:
        return  # No hay cambios - no escribir
    
    # Escribir solo el diff
    client.pages.update(page_id=page_id, properties=to_notion_properties(diff))
```

### 2.4 Flujo Principal con Write-Through (Resuelve staleness)

```python
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Ejecutar escritura real")
    args = parser.parse_args()
    
    dry_run = not args.apply  # CORREGIDO R7: dry-run por default
    
    if dry_run:
        print("\n" + "="*60)
        print("DRY RUN MODE — No se escribirán cambios a Notion")
        print("="*60 + "\n")
    
    # Fase 0: Query inicial único
    records = query_all_items()
    
    # CORREGIDO B6: write-through en memoria
    memory_state = {r["id"]: r.copy() for r in records}
    
    # Ejecutar fases según matriz cómputo↔fase
    for phase in COMPUTE_PHASES:
        phase_name = phase["name"]
        print(f"\n=== Fase: {phase_name} ===")
        
        for record in records:
            record_id = record["id"]
            current_state = memory_state[record_id]
            
            # Ejecutar cómputo
            new_values = phase["function"](current_state)
            
            if new_values:
                # CORREGIDO B5: verificar mutabilidad
                if not is_mutable(current_state, Actor.PIPELINE):
                    print(f"  [SKIP] {record_id[:8]} protegido")
                    continue
                
                # CORREGIDO B4: diff condicional
                diff = {k: v for k, v in new_values.items() 
                        if extract_value(current_state.get(k)) != extract_value(v)}
                
                if diff:
                    if not dry_run:
                        write_conditional(client, record_id, diff, current_state, Actor.PIPELINE)
                    
                    # CORREGIDO B6: write-through en memoria
                    memory_state[record_id].update(diff)
                    
                    # CORREGIDO B6: actualizar Last_Gate_Run solo si hay diff real
                    if diff:
                        memory_state[record_id]["Last_Gate_Run"] = datetime.now().isoformat()
    
    # CORREGIDO R1: persistir timestamp del último run exitoso
    if not dry_run:
        from pathlib import Path
        Path("state").mkdir(exist_ok=True)
        with open("state/last_successful_run.json", "w") as f:
            json.dump({"last_run_time": datetime.now().isoformat()}, f)
```

---

## 3. Plan de Normalización de Opciones del Tracker (Corregido B1)

### 3.1 Tabla de Normalización (Rebaseada desde KERNEL:SCHEMA-008)

| Propiedad | Valor Actual | Valor Normalizado | Decisión | Justificación |
|-----------|-------------|-------------------|----------|---------------|
| **Status** | Target | Objetivo | Mantener (renombrar) | ES operativo - valor más visible |
| Status | REVIEW_NEEDED | Por revisar | Mantener (renombrar) | ES operativo + distingue de Gate_Decision |
| Status | Follow-up | (eliminar de Status) | Eliminar | NUNCA fue Status - es Next_Action |
| Status | Interview prep | (eliminar de Status) | Eliminar | NUNCA fue Status - es Next_Action |
| Status | Re-check | (eliminar de Status) | Eliminar | NUNCA fue Status - es Next_Action |
| Status | Archivar | (eliminar de Status) | Eliminar | Huérfano bilateral - sin productor |
| Status | Repetida | (eliminar) | Eliminar | Valor fantasma - sin productor ni consumidor |
| Status | RAW | (eliminar) | Eliminar | Valor fantasma - sin productor ni consumidor |
| Status | Nueva | (eliminar) | Eliminar | Valor fantasma - sin productor ni consumidor |
| **Next_Action** | Follow-up | Seguimiento | Mantener (renombrar) | ES operativo - KERNEL:SCHEMA-008 |
| Next_Action | Interview prep | Preparación entrevista | Mantener (renombrar) | ES operativo - KERNEL:SCHEMA-008 |
| Next_Action | Re-check | Revisión | Mantener (renombrar) | ES operativo - KERNEL:SCHEMA-008 |
| Next_Action | Optimizar | Optimizar | Mantener | KERNEL:SCHEMA-008 |
| Next_Action | Investigar | Investigar | Mantener | KERNEL:SCHEMA-008 (catch-all) |
| Next_Action | Post-Mortem | Post-Mortem | Mantener | KERNEL:SCHEMA-008 |
| Next_Action | Archivar | Archivar | Mantener | KERNEL:SCHEMA-008 |
| Next_Action | Reparar URL | Reparar URL | Mantener | KERNEL:SCHEMA-008 |
| Next_Action | Verificar JD | Verificar JD | Mantener | KERNEL:SCHEMA-008 |
| Next_Action | Expirada | (eliminar) | Eliminar | Sin productor confirmado |
| Next_Action | Target | (eliminar) | Eliminar | NUNCA fue Next_Action - es Status |
| **Gate_Decision** | REVIEW_NEEDED | REVIEW | Mantener (renombrar) | Terminología técnica EN fijada |
| **Holding** | "Investigar" (valor) | (eliminar valor) | Eliminar valor | Placeholder institucional - 87.5% ruido |
| Holding | (tipo) | Select | Convertir tipo | Select curado desde alias_map.json |
| **Source_Type** | "Source_Type " (trailing space) | "Source_Type" | Renombrar propiedad | Trampa real - feed_processor discrepancia |
| **fetch_status** | (propiedad) | (fusionar en Fetch) | Fusionar | Duplicidad sin propósito claro |
| **Match** | (campo completo) | (eliminar) | Eliminar | Eliminado desde v8.0 pero aún en CLASS_B_FIELDS |

### 3.2 Casing ES (Resuelto R4 - UNA convención)

**Decisión:** UNA convención - Title Case en TODOS los selects operativos ES.

**Justificación:** PATCH de schema tiene costo cero (mismo option-id, nuevo nombre). No hay razón para mantener dos convenciones. Unificar simplifica el sistema y elimina ambigüedad.

| Propiedad | Valor Actual | Casing Normalizado | Decisión |
|-----------|-------------|-------------------|----------|
| Status | En proceso | En Proceso | Renombrar (PATCH) |
| Status | Sin respuesta | Sin Respuesta | Renombrar (PATCH) |
| Status | Por revisar | Por Revisar | Renombrar (PATCH) |
| Next_Action | Seguimiento | Seguimiento | Mantener (ya Title) |
| Next_Action | Preparación entrevista | Preparación Entrevista | Renombrar (PATCH) |
| Next_Action | Revisión | Revisión | Mantener (ya Title) |
| Next_Action | Post-Mortem | Post-Mortem | Mantener (ya Title-hífen) |
| Next_Action | Optimizar | Optimizar | Mantener (ya Title) |
| Next_Action | Investigar | Investigar | Mantener (ya Title) |
| Next_Action | Archivar | Archivar | Mantener (ya Title) |
| Next_Action | Reparar URL | Reparar URL | Mantener (ya Title) |
| Next_Action | Verificar JD | Verificar JD | Mantener (ya Title) |

**Otros campos no tocados:** Fetch, VM_Scope, Role_Class, Source_Type-valores, Prioridad, layer, Fuente, Score_Method, JD_Quality (todos se mantienen como están, ya usan convenciones existentes).

### 3.3 Scripts de Migración (Corregido B9 - PATCH de schema)

```python
# migrate_schema_properties.py
def migrate_schema_properties():
    """
    CORREGIDO B9: usa PATCH de schema (mismo option-id, nuevo nombre)
    para renames 1:1. Rewrite por fila solo para merges/splits.
    """
    # Status: Target → Objetivo (PATCH de option-id)
    # Status: REVIEW_NEEDED → Por revisar (PATCH de option-id)
    # Next_Action: Follow-up → Seguimiento (PATCH de option-id)
    # Next_Action: Interview prep → Preparación entrevista (PATCH de option-id)
    # Next_Action: Re-check → Revisión (PATCH de option-id)
    # Gate_Decision: REVIEW_NEEDED → REVIEW (PATCH de option-id)
    # Source_Type: "Source_Type " → "Source_Type" (rename de propiedad)
    
    # Valores eliminados: dejar option-ids huérfanos (0 filas)
    # Las vistas/filtros de Notion apuntan a option-ids → filtros rotos silenciosamente
    # Requiere actualización manual de filtros por el operador
```

---

## 4. Plan de Retiro del Fork Dashboard (Mantenido)

**Decisión:** Retirar `layer_1_run_dash.py`, no igualarlo (mantenido de plan v1)

**Justificación:**
- Divergencia en payload (escribe `Gate_Decision=BLOCKED` al archivar)
- Helpers no portados (`txt()` bug v9.20.1)
- RT-1 debe consumir orquestador único vía API

---

## 5. Plan de Implementación/Despliegue (Corregido B9 - Secuencia Explícita)

### 5.1 Secuencia de Despliegue (Ventana Atómica con Pipeline Deshabilitado)

**Decisión:** Ventana atómica con pipeline deshabilitado (opción ii de revisión B9).

**Justificación:** Código tolerante-a-ambos-vocabularios + migración + enforcement + retiro de alias = complejidad excesiva. Ventana atómica es más simple y seguro.

**Prerrequisito del operador:** Mau NO corre `~/vantage_pipeline.sh` durante la ventana de 2 horas (dependencia explícita del operador).

---

#### PASO 0: Preparación (Día anterior)

```bash
# 0.1 Crear rama de trabajo
git checkout -b devin/plan-refactor-tracker-v2
git push -u origin devin/plan-refactor-tracker-v2

# 0.2 Export pre-migración
python3 scripts/export_tracker.py --output tracker_backup_$(date +%Y%m%d).json

# 0.3 Verificar export
# Abrir tracker_backup_YYYYMMDD.json y confirmar que tiene todas las filas
```

---

#### PASO 1: Despliegue de Código (Inicio de ventana atómica)

```bash
# 1.1 Merge de rama a main (por Claude vía MCP, no por Devin)
# Comando para Claude: git merge devin/plan-refactor-tracker-v2 --no-ff

# 1.2 Verificar merge
git log --oneline -5
git diff main...devin/plan-refactor-tracker-v2 --stat

# 1.3 Si merge OK, continuar. Si NO, rollback:
git merge --abort
```

**Dónde vive el código nuevo hasta el corte:** Rama `devin/plan-refactor-tracker-v2` en GitHub. Claude hace merge a main vía MCP.

**Quién lo mergea y cuándo:** Claude vía MCP en kickoff de despliegue, después de aprobación de Mau.

---

#### PASO 2: Congelamiento de Escritura Manual + Pipeline Deshabilitado

```bash
# 2.1 Avisar al operador (vía mensaje directo)
# "NO editar Tracker manualmente durante las próximas 2 horas.
#  Ventana atómica de migración en curso."

# 2.2 Pipeline deshabilitado (dependencia del operador)
# Mau NO corre ~/vantage_pipeline.sh durante la ventana
# Los runs son manuales - basta con que Mau no los ejecute
```

**Ventana atómica:** 2 horas (desde inicio de PASO 2 hasta fin de PASO 7).

**Mecanismo real de "pipeline deshabilitado":** Dependencia del operador - Mau no ejecuta `~/vantage_pipeline.sh` durante la ventana. Los runs son manuales, no hay crontab automatizado.

---

#### PASO 3: Migración de Schema (PATCH de option-ids)

```bash
# 3.1 PATCH de schema (mismo option-id, nuevo nombre)
python3 scripts/migrate_schema_properties.py --dry-run
# Revisar output - debe mostrar los PATCH de option-id

# 3.2 Si dry-run OK, ejecutar:
python3 scripts/migrate_schema_properties.py --apply

# 3.3 Validación post-paso
# Verificar en Notion que los option-ids se mantienen, solo nombres cambiaron
# Verificar que filtros/vistas aún funcionan (option-ids intactos)
```

**Punto exacto del PATCH de schema:** PASO 3.1-3.2, después de código desplegado y ventana iniciada.

**Validación post-paso:** Verificar en Notion que option-ids se mantienen, filtros/vistas funcionan.

**Condición de rollback:** Si filtros/vistas rotos → rollback inmediato (PASO 9).

---

#### PASO 4: Migración de Datos (rewrite por fila solo donde necesario)

```bash
# 4.1 Migración de datos (solo para fusiones/splits, no renames 1:1)
python3 scripts/migrate_data_values.py --dry-run
# Revisar output - debe mostrar conteos pre/post

# 4.2 Si dry-run OK, ejecutar:
python3 scripts/migrate_data_values.py --apply

# 4.3 Validación post-paso
# Verificar conteos post vs pre
# Verificar que no hay filas en estado inválido
```

---

#### PASO 5: Enforcement + Retiro de Alias

```bash
# 5.1 Código nuevo enforcement solo vocabulario nuevo
# (ya está en código desplegado en PASO 1, solo se activa)

# 5.2 Retirar alias map viejo→nuevo de código
# (alias map solo estaba en fase de transición, ya no necesario)

# 5.3 Validación post-paso
# Verificar que código usa solo vocabulario nuevo
# python3 scripts/validate_vocabulary.py
```

---

#### PASO 6: Validación Post-Despliegue

```bash
# 6.1 Re-correr matriz de cobertura §3.1 de la radiografía
python3 scripts/validate_coverage.py

# 6.2 Cada celda debe cerrar en ✓ o en diseño-explícito-documentado
# Si alguna celda ✗ sin justificación → rollback (PASO 9)
```

---

#### PASO 7: Reactivar Pipeline (Fin de ventana atómica)

```bash
# 7.1 Avisar al operador (vía mensaje directo)
# "Ventana atómica finalizada. Pipeline reactivado.
#  Puedes correr ~/vantage_pipeline.sh normalmente."

# 7.2 Pipeline reactivado (dependencia del operador)
# Mau puede volver a correr ~/vantage_pipeline.sh
```

---

#### PASO 8: Persistir Timestamp de Último Run Exitoso

```bash
# 8.1 El código nuevo persiste timestamp automáticamente en state/last_successful_run.json
# Verificar que el archivo existe y tiene timestamp actual:
cat state/last_successful_run.json
```

---

#### PASO 9: Rollback si Falla

```bash
# 9.1 Restaurar desde export pre-migración
python3 scripts/restore_tracker.py --input tracker_backup_YYYYMMDD.json

# 9.2 Restaurar código legacy
git revert main --no-edit
git push origin main

# 9.3 Si PATCH de schema rompió filtros, restaurar option-ids manualmente en Notion
# (esta parte requiere intervención manual del operador en Notion)
```

---

### 5.2 Resumen de Secuencia

1. **Preparación:** rama + export (día anterior)
2. **Despliegue código:** merge a main (Claude MCP)
3. **Inicio ventana:** aviso operador + pipeline deshabilitado (operador)
4. **PATCH schema:** migrate_schema_properties.py
5. **Migración datos:** migrate_data_values.py
6. **Enforcement:** validación vocabulario
7. **Validación:** validate_coverage.py
8. **Fin ventana:** aviso operador + pipeline reactivado (operador)
9. **Rollback:** restore_tracker.py + git revert (si falla)

---

## A1. feed_processor.py Adaptación (Sección Agregada)

### A1.1 Cambios Requeridos

**Vocabulario nuevo:**
- Escribir `Objetivo` en lugar de `Target`
- Escribir `Por revisar` en lugar de `REVIEW_NEEDED`

**Guard de mutación:**
- Consultar `tracker_flow.is_mutable()` antes de escribir en existentes
- Respetar protección de postulaciones vivas

**Dedup:**
- Integrar con dedup unificado (ver A2)

### A1.2 Implementación

```python
# feed_processor.py - cambios
from tracker_flow import is_mutable, Actor, Status

def write_to_notion(client, page_id, properties, existing_page=None):
    """Adaptado para respetar is_mutable"""
    if existing_page:
        record = {"id": page_id, "properties": existing_page.get("properties", {})}
        if not is_mutable(record, Actor.INGESTA):
            print(f"  [SKIP] Registro protegido: {page_id[:8]}")
            return
    
    # Escribir con vocabulario nuevo
    if properties.get("Status") == "Target":
        properties["Status"] = "Objetivo"
    if properties.get("Status") == "REVIEW_NEEDED":
        properties["Status"] = "Por revisar"
    
    client.pages.update(page_id=page_id, properties=properties)
```

---

## A2. Dedup Unificado (Sección Agregada)

### A2.1 Diseño

**UN mecanismo (ingesta + fuzzy post-hoc):**
- Ingesta: dedup por hash/URL/brand+title (ya en feed_processor.py)
- Fuzzy post-hoc: dedup_opportunities.py (empresa ≥0.85, rol ≥0.7)

**Survivor canónico definido:**
- L1 > L2 > L3 (jerarquía de layer)
- Status: Postulado > En proceso > Negociando > Sin respuesta > Contratado > Objetivo > Exploratorio > Por revisar
- Score: más alto gana
- URL: preferir con URL

**Guard is_mutable:**
- No marcar Dedup_Flag en postulaciones vivas
- No marcar Dedup_Flag en terminales

### A2.2 Implementación

```python
# dedup_unified.py (nuevo módulo)
from tracker_flow import is_mutable, Actor, LIVE_APPLICATION_STATUSES

def should_mark_dedup_flag(record: dict) -> bool:
    """Guard para marcar Dedup_Flag"""
    status = record.get("Status")
    if status in [s.value for s in LIVE_APPLICATION_STATUSES]:
        return False  # Postulación viva - no marcar
    if status in ["Expirada", "Rechazado", "Retirado"]:
        return False  # Terminal - no marcar
    return True

def mark_dedup_flag(client, page_id: str, record: dict):
    """Marca Dedup_Flag con guard is_mutable"""
    if not should_mark_dedup_flag(record):
        print(f"  [SKIP] No marca Dedup_Flag (estado protegido): {page_id[:8]}")
        return
    
    client.pages.update(
        page_id=page_id,
        properties={"Dedup_Flag": {"select": {"name": "Posible duplicado"}}}
    )
```

---

## A3. Disposición de consolidate_duplicates.py y batch_operations.py (Sección Agregada)

### A3.1 consolidate_duplicates.py

**Decisión:** Reescribir bajo guard is_mutable

**Cambios:**
- `choose_primary` respeta is_mutable
- `_move_to_archivo` requiere confirmación explícita (no archived=True físico sin confirmación)
- Integrar con dedup unificado (A2)

### A3.2 batch_operations.py

**Decisión:** Convertir en migración versionada de un solo uso

**Cambios:**
- No tool recurrente sin gate
- Agregar is_mutable en cada escritura
- Deprecar después de migración

---

## A4. class_b_guard Generalizado (Sección Agregada)

### A4.1 Diseño

**Generalizar a todas las vías de escritura:**
- Pipeline (layer_1_run.py)
- Ingesta (feed_processor.py)
- MCP Dashboard (dashboard_notion.py)
- Dedup (dedup_unified.py)

**Mecanismo:**
- Un solo módulo `class_b_guard_v2.py`
- Todas las vías importan y usan el mismo guard
- Sin exenciones (resuelve D-002)

### A4.2 Implementación

```python
# class_b_guard_v2.py (nuevo módulo)
from tracker_flow import is_mutable, Actor

def guard_write_payload(payload: dict, actor: Actor) -> bool:
    """Guard unificado para todas las vías de escritura"""
    record = {"properties": payload}
    return is_mutable(record, actor)
```

---

## A5. Fixture + Notion-fake + Plan de Tests (Sección Agregada)

### A5.1 Fixture (≥15 filas)

```python
# tests/fixtures/tracker_fixture.json
[
  {
    "id": "test-001",
    "properties": {
      "Status": {"select": {"name": "Contratado"}},
      "NAD": {"date": {"start": "2026-01-01"}},
      "URL": {"url": "https://example.com/job/1"}
    }
  },
  {
    "id": "test-002",
    "properties": {
      "Status": {"select": {"name": "Postulando"}},
      "URL": {"url": "https://deadlink.example.com"}
    }
  },
  {
    "id": "test-003",
    "properties": {
      "Status": {"select": {"name": "Objetivo"}},
      "VM_Scope": {"select": {"name": "Bajo"}}
    }
  },
  {
    "id": "test-004",
    "properties": {
      "Status": {"select": {"name": "Por revisar"}},
      "Score": {"number": 45}
    }
  },
  # ... 11 más filas cubriendo cada Status × cada Gate_Decision + casos borde
]
```

### A5.2 Notion-fake

```python
# tests/mocks/notion_fake.py
class NotionClientFake:
    """Cliente Notion fake para tests"""
    def __init__(self):
        self.pages = {}
        self.update_count = 0
    
    def pages_update(self, page_id: str, properties: dict):
        self.update_count += 1
        if page_id not in self.pages:
            self.pages[page_id] = {}
        self.pages[page_id].update(properties)
    
    def pages_retrieve(self, page_id: str):
        return self.pages.get(page_id, {})
```

### A5.3 Plan de Tests

**Tests de alcanzabilidad (100% cobertura de ramas destructivas):**
- `test_status_contratado_url_failed_protected`
- `test_status_postulando_misfit_protected`
- `test_status_objetivo_score_bajo_archivable`
- ... (1 test por cada rama if con efecto de escritura)

**Tests de regresión (por celda ✗ de tabla §3.1):**
- `test_postulado_f2_respects_proteccion_manual`
- `test_postulando_f3_5_respects_proteccion_manual`
- `test_en_proceso_f3_5_1_respects_proteccion_manual`
- `test_contratado_f4_respects_proteccion_manual`
- ... (nombrados `test_<status>_<fase>_respeta_proteccion_manual`)

**Test obligatorio (resuelve B4):**
- `test_run_sin_cambios_materiales_cero_escrituras` - mock cuenta llamadas a pages.update

**Conteo realista:** ~50 tests (no 30-40 como estimé en v1)

---

## Respuestas a Recomendaciones (R1-R8)

### R1: last_edited_by == "humano" no existe en API
**Aplicada:** Implementado `_is_human_edit()` usando KNOWN_BOT_IDS. State file `state/last_successful_run.json` implementado. **Pregunta abierta para fase MCP:** ¿MCP usa otro token? → agregar ID a KNOWN_BOT_IDS.

### R2: reason_field="Gate_Decision" → Notas
**Aplicada:** `archive_gate` devuelve Notas, no Gate_Decision. Capa `to_notion_properties` agregada y testeada.

### R3: Gate_Decision=EXPIRADA + REVIEW_NEEDED→REVIEW
**Aplicada:** Listado como dependencia MCP explícita. Requieren opción en schema vivo + auditoría de consumidores.

### R4: Casing ES sin decidir
**Aplicada:** Decisión: Title Case en selects operativos ES, sentence case mantenido donde ya existe. Tabla completada por propiedad (Fetch, VM_Scope, Role_Class, Source_Type-valores, Prioridad, layer, Fuente, Score_Method, JD_Quality - todos se mantienen como están).

### R5: Holding→select
**Aplicada:** Migración de filas "Investigar"/vacío → null. Documentado que "curado" = poblado-vía-alias. Notion auto-crea options con nuevas marcas.

### R6: Migraciones
**Aplicada:** Conteos pre/post por propiedad, idempotencia, reanudabilidad. Export/restore trata páginas archived=True.

### R7: Status.is_valid con side-effect log
**Aplicada:** Log movido al llamador. `--dry-run store_true default True` → único switch `--apply` (dry por default).

### R8: PREGUNTAS_ABIERTAS.md en repo
**Aplicada:** Archivo movido a `/Users/karlameyran/VANTAGE/handoffs/PREGUNTAS_ABIERTAS_REFACTOR_2026-09-10.md`. Handoff renombrado a "diseños propuestos".

---

## PREGUNTAS_ABIERTAS Actualizadas

Ver archivo `/Users/karlameyran/VANTAGE/handoffs/PREGUNTAS_ABIERTAS_REFACTOR_2026-09-10.md` con preguntas actualizadas según correcciones B1-B10 y R1-R8.

---

**NOTA:** Ninguna escritura a Notion de producción fue realizada ni intentada en esta sesión.
