"""
VANTAGE Hard Block Gate — Validación de empleadores bloqueados (Fase 3).

Fuente única declarada: Layer_1/config/hard_blocks.json.
Implementación independiente — no reutiliza, ni envuelve, ni depende de
src/validator.py (Scout no productivo; diseño no completado ni a
completarse, decisión operador 2026-09-16 — fuera de alcance total).

Match por substring case-insensitive contra los términos declarados en
hard_blocks.json. Sin regex: cualquier variante nueva (sede, división,
holding) se agrega directamente al JSON, sin tocar este código.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

# ═══════════════════════════════════════════════════════════════════════════════
# Fuente única
# ═══════════════════════════════════════════════════════════════════════════════

_HARD_BLOCKS_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent
    / "config"
    / "hard_blocks.json"
)


def _load_hard_blocked_terms() -> list[str]:
    """Carga los términos base desde hard_blocks.json (fuente única declarada)."""
    if not _HARD_BLOCKS_CONFIG_PATH.exists():
        return []
    with open(_HARD_BLOCKS_CONFIG_PATH, encoding="utf-8") as f:
        config = json.load(f)
    return list(config.get("hard_block_employers", []))


def blocked_employer_term(
    brand: str,
    holding: Optional[str] = None,
) -> Optional[str]:
    """Devuelve el término de hard_blocks.json que hizo match, o None.

    Match por substring (case-insensitive, normaliza apóstrofos curvos)
    contra los términos declarados en hard_blocks.json — única fuente.

    Args:
        brand: Nombre de la marca/empresa a verificar.
        holding: Holding opcional (se concatena para la verificación).

    Returns:
        El término de hard_blocks.json que hizo match, o None si no aplica.
    """
    if not brand:
        return None

    haystack = f"{brand} {holding or ''}"
    haystack_norm = haystack.strip().lower().replace("’", "'").replace("‘", "'")

    for term in _load_hard_blocked_terms():
        term_norm = term.strip().lower()
        if term_norm and term_norm in haystack_norm:
            return term

    return None


def is_hard_blocked_employer(
    brand: str,
    holding: Optional[str] = None,
) -> bool:
    """Devuelve True si la empresa está en hard_blocks.json (bloqueo total)."""
    return blocked_employer_term(brand, holding) is not None
