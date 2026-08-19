#!/usr/bin/env python3
"""
VANTAGE — class_b_guard.py
Guard técnico para GAP-03 (KERNEL:GATE-DECISION-003).

Problema que resuelve:
  feed_processor.py ya filtra Class B por construcción (NotionSchema solo
  resuelve propiedades Class A nombradas explícitamente — ver clase
  NotionSchema, ~línea 320 de feed_processor.py). El conector MCP de Claude
  (notion-update-page / notion-create-pages) NO pasa por feed_processor.py:
  escribe directo al Tracker, sin ese guard. GAP-03 es esa asimetría.

Qué hace este módulo:
  Punto único de verdad para "qué campos puede escribir un actor no-Python"
  en el Tracker de vacantes. No ejecuta la escritura — audita un payload
  antes de que cualquier llamador (agente IA, script, notebook) lo mande a
  Notion, y devuelve el payload ya limpiado + un reporte de lo removido.

No reemplaza NotionSchema (feed_processor.py) — ese sigue siendo la fuente
para el pipeline Python. Este módulo es la contraparte para todo lo que NO
es feed_processor.py: MCP, escritura manual, otros scripts.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ──────────────────────────────────────────
# Fuente de verdad de Class A/B — KERNEL:SCHEMA-001
# ──────────────────────────────────────────
# Mantener en sync manual con KERNEL:SCHEMA-001 (Notion, System Prompt vivo).
# Si el Kernel cambia esta lista, este módulo debe actualizarse en el mismo
# batch — no hay sincronización automática Notion → este archivo.

CLASS_A_FIELDS: frozenset[str] = frozenset({
    "Rol", "Marca", "Source_Type ",  # nota: trailing space real en schema Notion
    "URL", "Status", "Prioridad", "Holding", "JD", "NAD", "layer", "hash",
    "Contacto", "Notas", "JOB_ID", "Files", "Interview", "Interview_Date",
    "Apply Date", "Rej Date", "Outcome", "Optimizar", "Postular", "Archivar",
    "URL Notion",
})

CLASS_B_FIELDS: frozenset[str] = frozenset({
    "Score", "Gate_Decision", "VM_Scope", "Role_Class", "Match",
    "Next_Action", "Fetch", "Fuente", "Dedup_Flag", "Score_Method",
    "JD_Quality",
})


@dataclass
class GuardResult:
    clean_payload: dict
    blocked_fields: dict = field(default_factory=dict)
    unknown_fields: dict = field(default_factory=dict)

    @property
    def is_clean(self) -> bool:
        return not self.blocked_fields and not self.unknown_fields

    def report(self) -> str:
        lines = []
        if self.blocked_fields:
            lines.append(
                "🛑 CLASS B BLOQUEADO — removido antes de escribir "
                f"({len(self.blocked_fields)}): "
                + ", ".join(sorted(self.blocked_fields))
            )
        if self.unknown_fields:
            lines.append(
                "⚠️  CAMPOS DESCONOCIDOS — no están en Class A ni Class B, "
                f"removidos por precaución ({len(self.unknown_fields)}): "
                + ", ".join(sorted(self.unknown_fields))
            )
        if not lines:
            lines.append("✅ Payload limpio — todos los campos son Class A.")
        return "\n".join(lines)


def guard_write_payload(payload: dict, *, strict_unknown: bool = True) -> GuardResult:
    """
    Audita un payload de escritura Notion antes de enviarlo.

    strict_unknown=True (default): cualquier campo que no sea Class A ni
    Class B declarado se trata como bloqueado (fail-closed — consistente
    con KERNEL:FAIL-PHILOSOPHY: un guard que deja pasar lo desconocido no
    es un guard).
    """
    clean: dict = {}
    blocked: dict = {}
    unknown: dict = {}

    for key, value in payload.items():
        if key in CLASS_A_FIELDS:
            clean[key] = value
        elif key in CLASS_B_FIELDS:
            blocked[key] = value
        elif strict_unknown:
            unknown[key] = value
        else:
            clean[key] = value

    return GuardResult(clean_payload=clean, blocked_fields=blocked, unknown_fields=unknown)


def assert_class_a_only(payload: dict) -> dict:
    """
    Variante estricta para uso en flujos automatizados (no interactivos):
    lanza ValueError si hay cualquier campo Class B o desconocido, en vez
    de limpiar silenciosamente. Usar cuando el llamador debe fallar fuerte
    en vez de degradar.
    """
    result = guard_write_payload(payload, strict_unknown=True)
    if not result.is_clean:
        raise ValueError(
            "class_b_guard: payload rechazado.\n" + result.report()
        )
    return result.clean_payload


if __name__ == "__main__":
    # Auto-test mínimo — no requiere Notion ni red.
    sample = {
        "Rol": "VM Coordinator",
        "Marca": "Gucci",
        "Score": 87,          # Class B — debe bloquearse
        "Gate_Decision": "CREATE",  # Class B — debe bloquearse
        "campo_inventado": "x",     # desconocido — debe bloquearse
    }
    result = guard_write_payload(sample)
    print(result.report())
    print("Payload limpio:", result.clean_payload)
    assert result.clean_payload == {"Rol": "VM Coordinator", "Marca": "Gucci"}
    assert "Score" in result.blocked_fields
    assert "Gate_Decision" in result.blocked_fields
    assert "campo_inventado" in result.unknown_fields
    print("\n✅ Auto-test PASS")
