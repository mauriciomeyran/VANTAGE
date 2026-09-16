"""
VANTAGE Status — Módulo unificado de terminalidad y mutabilidad (Fase 3).

Fuente canónica de vocabulario: tracker_flow (enums y constantes).
Capa legacy: mapeo explícito de valores de Status encontrados en producción
que no están en tracker_flow.Status (98 registros, 12% de la base, verificado
con datos reales del Archive Tracker).

Normalización en lectura (lazy) — no escribe a Notion.
Los legacy sin mapeo (Repetida, Target) se flaggean, no se asumen.
"""

from __future__ import annotations

from tracker_flow import (
    Status,
    PROTECTED_STATUSES,
    TERMINAL_STATUSES,
    LIVE_APPLICATION_STATUSES,
    GateDecision,
    NextAction,
)

# ═══════════════════════════════════════════════════════════════════════════════
# Capas canónica y legacy
# ═══════════════════════════════════════════════════════════════════════════════

PROTECTED_STATUSES_CANONICO = PROTECTED_STATUSES     # set[Status]
TERMINAL_STATUSES_CANONICO = TERMINAL_STATUSES         # set[Status]


# Mapeo explícito de valores de Status encontrados en producción que NO están
# en tracker_flow.Status (verificado: 98 registros, 12% de la base).
#
# None → legacy sin mapeo: el módulo los flaggean, no los asume. El operador
#        confirma la equivalencia semántica antes de llenar el mapeo.
# str  → mapeo a valor canónico de tracker_flow.Status
LEGACY_STATUS_MAP: dict[str, str | None] = {
    "Archivar":       "Expirada",        # huérfano bilateral documentado en tracker_flow
    "Repetida":       None,              # 29 filas — semántica no verificable, sin mapear
    "Target":         None,              # 31 filas — semántica no verificable, sin mapear
    "Blocked":        "Rechazado",       # 2 filas — semántica más próxima
    "REVIEW_NEEDED":  "Por Revisar",     # 24 filas — semántica más próxima
    "Sin respuesta":  "Sin Respuesta",   # 1 fila  — diferencia solo de mayúscula
}


# ═══════════════════════════════════════════════════════════════════════════════
# Funciones exportadas
# ═══════════════════════════════════════════════════════════════════════════════

def normalize_status(status: str | None) -> str:
    """Devuelve el Status canónico para un valor crudo de producción.

    - Si está en tracker_flow.Status: pasa tal cual.
    - Si está en LEGACY_STATUS_MAP con mapeo str: retorna el canónico.
    - Si está en LEGACY_STATUS_MAP con None: retorna el original — el caller
      debe tratárselo como "legacy sin mapeo, requiere revisión humana".
    - Si no está en ninguno: retorna el original — comportamiento compatible
      con F8/F10 de tracker_flow (no invalidar, dejar que el caller decida).
    """
    if not status:
        return status or ""

    try:
        return Status(status).value
    except ValueError:
        pass

    mapped = LEGACY_STATUS_MAP.get(status)
    if mapped is not None:
        return mapped

    return status


def is_terminal_status(status: str) -> bool:
    """Terminalidad por Status — única fuente de verdad.

    Cubre:
    - Los 3 de tracker_flow.TERMINAL_STATUSES (Expirada, Rechazado, Retirado).
    - "Archivar" (legacy mapeado a Expirada, incluido explícitamente).
    No cubre legacy sin mapeo (Repetida, Target) — son operativos por defecto
    hasta que el operador confirme su semántica.
    """
    if not status:
        return False

    try:
        if Status(status) in TERMINAL_STATUSES_CANONICO:
            return True
    except ValueError:
        pass

    mapped = LEGACY_STATUS_MAP.get(status)
    if mapped is not None:
        try:
            if Status(mapped) in TERMINAL_STATUSES_CANONICO:
                return True
        except ValueError:
            pass

    return False


def is_protected_status(status: str) -> bool:
    """Protección general: terminal + postulación viva.

    Delegado a tracker_flow.PROTECTED_STATUSES + manejo de legacy mapeado.
    Los legacy sin mapeo (None) NO se consideran protegidos — son operativos
    hasta confirmación del operador.
    """
    if not status:
        return False

    try:
        if Status(status) in PROTECTED_STATUSES_CANONICO:
            return True
    except ValueError:
        pass

    mapped = LEGACY_STATUS_MAP.get(status)
    if mapped is not None:
        try:
            if Status(mapped) in PROTECTED_STATUSES_CANONICO:
                return True
        except ValueError:
            pass

    return False


def is_mutable_status(status: str) -> bool:
    """Contrario de is_protected_status.

    Resuelve D6: profile_fit delega aquí en vez de mantener su propio conjunto.
    """
    return not is_protected_status(status)


def gate_protected_value(entry: dict) -> str | None:
    """Reemplaza gate_logic.gate_logic().

    Contrato de retorno:
    - str  → registro NO debe recalcularse. Valor es un GateDecision canónico
             (CREATE/APPLIED/REJECTED/EXPIRED/BLOCKED/REVIEW_NEEDED) o un
             valor legacy interno ("EXPIRADA") conservado por compatibilidad.
    - None → registro es elegible para recálculo.

    Cobertura:
    - Status canónico en TERMINAL_STATUSES (incluye Retirado — D2 corregido,
      89 registros reales en Archive Tracker).
    - Status legacy mapeado a terminal vía LEGACY_STATUS_MAP
      ("Archivar" → "Expirada", 11 registros reales).
    - NO se revisa Next_Action="Expirada" (D1: 0 ocurrencias en 826 filas,
      código muerto confirmado; la protección real existe vía Status="Expirada").

    Los legacy sin mapeo (Repetida, Target) entran por la ruta normal
    (no son terminales por defecto).
    """
    status = (entry.get("Status") or "").strip()

    # Mapa interno: Status canónico → valor a retornar (compatible con
    # caller de gate_logic() en layer_1_orchestrator.py).
    _STATUS_TO_GATE: dict[str, str] = {
        Status.POSTULADO.value: "APPLIED",
        Status.RECHAZADO.value: "REJECTED",
        Status.EXPIRADA.value: "EXPIRADA",   # legacy value, conserved for compat
        Status.RETIRADO.value: "EXPIRADA",   # D2: Retirado now protected (89 rows)
    }

    # 1. Status canónico terminal
    if status in _STATUS_TO_GATE:
        entry_id = entry.get("id", "unknown")[:8] if "id" in entry else "unknown"
        current_action = entry.get("Next_Action") or ""
        print(
            f"[gate_logic] PROTECTED: {entry_id} → {_STATUS_TO_GATE[status]} "
            f"(Status={status}, Next_Action={current_action})"
        )
        return _STATUS_TO_GATE[status]

    # 2. Legacy status mapeado a terminal
    mapped = LEGACY_STATUS_MAP.get(status)
    if mapped is not None and mapped in _STATUS_TO_GATE:
        entry_id = entry.get("id", "unknown")[:8] if "id" in entry else "unknown"
        current_action = entry.get("Next_Action") or ""
        print(
            f"[gate_logic] PROTECTED: {entry_id} → {_STATUS_TO_GATE[mapped]} "
            f"(Status={status} [legacy→{mapped}], Next_Action={current_action})"
        )
        return _STATUS_TO_GATE[mapped]

    # D1: NO se revisa Next_Action="Expirada" (código muerto confirmado:
    # 0 ocurrencias en 826 filas). La protección real existe vía
    # Status="Expirada" ↓ arriba.

    return None
