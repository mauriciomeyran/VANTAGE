"""
VANTAGE Gate Logic — Terminal State Protection (KERNEL:GATE-DECISION)

Contrato (Patch 1 / GATE-DECISION-010):
  1. Evalúa Status contra TERMINAL_STATUSES (tracker_flow) y su mapeo legacy.
  2. Retorna el valor terminal (str) si el registro NO debe ser recalculado;
     retorna None si es elegible para recálculo por gate().

Desde Fase 3 (este patch):
  - TERMINAL_ACTIONS eliminado: Next_Action="Expirada" nunca ocurre en producción
    (0 ocurrencias en 826 filas). El check era defensa sobre el campo equivocado.
    La protección real para "Expirada" ya existe vía Status="Expirada" en
    TERMINAL_STATUSES.
  - STATUS_TERMINAL_MAP eliminado: su lógica ahora vive en
    vantage_status.gate_protected_value(), que usa tracker_flow.TERMINAL_STATUSES
    + LEGACY_STATUS_MAP.
  - gate_logic() delega a vantage_status.gate_protected_value() para mantener
    el contrato de retorno compatible (str | None).

No contiene lógica de scoring ni de Next_Action operativa:
esa responsabilidad vive en layer_1_run.py (Fase 4).
"""

from __future__ import annotations

from vantage_status import gate_protected_value


def gate_logic(entry: dict) -> str | None:
    """Protección de estados terminales.

    Args:
        entry: dict con al menos "Status" y "Next_Action".

    Returns:
        str  — valor terminal ("APPLIED", "REJECTED", "EXPIRADA")
               si el registro NO debe ser recalculado.
        None — el registro es elegible para recálculo por gate().

    Cambios Fase 3:
      - El check de Next_Action="Expirada" fue eliminado (D1: 0 ocurrencias
        en 826 filas; código muerto confirmado).
      - Retirado ahora protegido (D2: 89 registros reales).
      - "Archivar" como Status legacy ahora protegido vía LEGACY_STATUS_MAP.
      - El logging de protección se conserva del módulo delegado.
    """
    return gate_protected_value(entry)


def evaluate_gate(fetch: str, vm_scope: str, role_class: str) -> str:
    """Evalúa la regla del gate (helper legacy / smoke)."""
    if fetch == "Accesible" and (vm_scope == "Alto" or role_class == "Pivote"):
        return "CREATE"
    return "BLOCKED"
