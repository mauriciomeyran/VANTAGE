"""
class_b_guard.py — Guard compartido para campos Class B.
Invocable desde feed_processor.py y desde flujos MCP.
FX-1 · GAP-03 · 2026-06-23
"""

CLASS_B_FIELDS = {
    "Score", "Gate_Decision", "VM_Scope", "Role_Class",
    "Match", "Next_Action", "Fetch", "Fuente",
}

def strip_class_b(props: dict) -> dict:
    """Elimina campos Class B de un dict de propiedades antes de escribir en Notion."""
    return {k: v for k, v in props.items() if k not in CLASS_B_FIELDS}

def assert_no_class_b(props: dict) -> None:
    """Lanza ValueError si el dict contiene campos Class B."""
    violations = CLASS_B_FIELDS.intersection(props.keys())
    if violations:
        raise ValueError(f"CLASS_B_GUARD: campos prohibidos detectados: {violations}")
