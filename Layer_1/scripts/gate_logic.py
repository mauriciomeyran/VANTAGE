"""
VANTAGE Gate Logic — Terminal State Protection (KERNEL:GATE-DECISION)

Contrato (Patch 1 / GATE-DECISION-010):
  1. Evalúa Status contra STATUS_TERMINAL_MAP primero.
  2. Luego Next_Action contra TERMINAL_ACTIONS.
  3. Retorna el valor terminal (str) si el registro NO debe ser recalculado;
     retorna None si es elegible para recálculo por gate().

No contiene lógica de scoring ni de Next_Action operativa:
esa responsabilidad vive en layer_1_run.py (Fase 4).
"""

# ── Constantes de módulo (exportables) ──────────────────────────────────────
TERMINAL_ACTIONS = {"Archivar", "Expirada"}

STATUS_TERMINAL_MAP = {
    "Postulado": "APPLIED",
    "Rechazado": "REJECTED",
}


def gate_logic(entry):
    """
    Protección de estados terminales.

    Args:
        entry: dict con al menos "Status" y "Next_Action".

    Returns:
        str  — valor terminal ("APPLIED", "REJECTED", "Archivar", "Expirada")
               si el registro NO debe ser recalculado.
        None — el registro es elegible para recálculo por gate().
    """
    status = entry.get("Status") or ""
    if status in STATUS_TERMINAL_MAP:
        return STATUS_TERMINAL_MAP[status]

    current_action = entry.get("Next_Action") or ""
    if current_action in TERMINAL_ACTIONS:
        return current_action

    return None


def evaluate_gate(fetch, vm_scope, role_class):
    """Evalúa la regla del gate (helper legacy / smoke)."""
    if fetch == "Accesible" and (vm_scope == "Alto" or role_class == "Pivote"):
        return "CREATE"
    return "BLOCKED"
