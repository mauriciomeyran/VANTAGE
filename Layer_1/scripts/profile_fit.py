"""
Reglas de fit de perfil VM y exclusiones compartidas (pipeline + cleanup).

Terminalidad y mutabilidad: delegadas a vantage_status (Fase 3).
El resto de este módulo (regex de roles, alias_map, VM title signals,
profile_misfit_reasons) no es terminalidad — es fit de perfil.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from vantage_status import is_protected_status

_EXCLUDE_ROLE_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bvendedor", "vendedor"),
    (r"\bvendedora", "vendedora"),
    (r"\bsales\b", "sales"),
    (r"\basesor\b", "asesor_ventas"),
    (r"merchandise\s*planner", "merchandise_planner"),
    (r"\bplanner\b(?!.*visual)", "planner"),
    (r"store\s+manager(?!.*visual)", "store_manager"),
    (r"retail\s+manager(?!.*visual)", "retail_manager"),
    (r"subgerente\s+de\s+tecnolog", "tecnologias"),
    (r"content\s+designer", "content_designer"),
    (r"desarrollo\s+comercial", "desarrollo_comercial"),
    (r"\bderma\b", "derma"),
    (r"ejecutivo\s+de\s+ventas", "ventas"),
    (r"diseñador\s+gráfico", "diseno_grafico"),
    (r"graphic\s+designer", "graphic_designer"),
    (r"realizador", "realizador"),
    (r"jefe\s+de\s+producto", "jefe_producto"),
    (r"subgerente\s+de\s+producto", "subgerente_producto"),
    (r"influencer", "influencer"),
    (r"mystery\s+shopper", "mystery_shopper"),
    (r"promotions\s+coordinator", "promotions"),
    (r"omnichannel\s+coordinator", "omnichannel"),
    (r"marketing\s+coordinator(?!.*visual)", "marketing_coordinator"),
    (r"merchandising\s+coordinator(?!.*visual)", "merchandising_coordinator"),
    (r"coordinador\s+de\s+merchandising(?!.*visual)", "coordinador_merchandising"),
)

_VM_TITLE_SIGNALS = (
    "visual", "merchandis", " vm", "vm ", "brand environment",
    "retail design", "store design", "escaparate", "exhibición",
)


@lru_cache(maxsize=1)
def _alias_data() -> dict:
    path = Path(__file__).resolve().parent.parent / "config" / "alias_map.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def resolve_alias_flags(marca: str) -> tuple[bool, str | None]:
    if not marca:
        return False, None
    key = marca.strip().lower()
    aliases = _alias_data().get("aliases", {})
    entry = aliases.get(key)
    if not entry:
        for alias_key, alias_val in aliases.items():
            if alias_key in key or key in alias_key:
                entry = alias_val
                break
    if not entry:
        return False, None
    return bool(entry.get("hard_block", False)), entry.get("marca")


def is_role_excluded(role_title: str) -> str | None:
    if not role_title:
        return None
    role_lower = role_title.lower()
    vm_title = has_vm_title_signal(role_title)
    for pattern, label in _EXCLUDE_ROLE_PATTERNS:
        if not re.search(pattern, role_lower, re.I):
            continue
        # "Visual Merchandising Coordinator" sí es fit VM
        if vm_title and label in (
            "merchandising_coordinator", "coordinador_merchandising", "planner",
        ):
            continue
        return label
    return None


def has_vm_title_signal(role_title: str) -> bool:
    role_lower = f" {role_title.lower()} "
    return any(signal in role_lower for signal in _VM_TITLE_SIGNALS)


def profile_misfit_reasons(
    *,
    rol: str,
    marca: str,
    vm_scope: str,
    role_class: str,
    source_type: str = "Vacante",
    score: int | None = None,
) -> list[str]:
    reasons: list[str] = []
    excluded = is_role_excluded(rol)
    if excluded:
        reasons.append(f"exclude:{excluded}")

    hard_block, _ = resolve_alias_flags(marca)
    if hard_block:
        reasons.append("hard_block_alias")

    if source_type == "Vacante":
        if vm_scope == "Bajo" and role_class == "Otro":
            reasons.append("no_profile_fit")
        elif role_class == "Pivote" and vm_scope == "Bajo" and not has_vm_title_signal(rol):
            reasons.append("pivot_without_vm")
        elif vm_scope == "Bajo" and score is not None and score < 45:
            reasons.append(f"low_score:{score}")

    return reasons


def should_auto_cleanup(status: str, reasons: list[str]) -> bool:
    """¿Se puede auto-limpiar un registro?

    Fase 3: delega a vantage_status.is_protected_status().
    Los legacy sin mapeo (Repetida, Target) NO son protegidos por defecto
    hasta que el operador confirme su semántica.
    """
    if is_protected_status(status):
        return False
    return bool(reasons)


def should_annotate_existing(status: str) -> bool:
    """KERNEL:GATE-DECISION-007 — ¿se puede anotar un registro existente?

    Fase 3: delega a vantage_status.is_protected_status().

    Dedup_Flag (Class B, candidato a archivo) y upgrade de layer (Class A,
    procedencia) solo aplican si el existente NO es postulación viva ni
    terminal. No es gate_logic(): ese protege recálculo de Score/Gate y
    no cubre En proceso / Negociando / Postulando.

    True  → Target, Exploratorio, REVIEW_NEEDED, vacío, u otro operativo.
    False → estados protegidos por vantage_status.
    """
    return not is_protected_status(status)
