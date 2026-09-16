"""
VANTAGE Hard Block Gate — Validación de empleadores bloqueados (Fase 3).

Fuente única declarada: Layer_1/config/hard_blocks.json.
Implementación independiente — no reutiliza, ni envuelve, ni depende de
src/validator.py (Scout no productivo; Fuera de alcance Fase 3 por
decisión del operador).

Cobertura como mínimo de las variantes confirmadas en datos reales:
  - L'Oréal: l'oréal, l'oreal, loreal + divisiones/holdings + méxico
  - Levi's: levi's, levis
  - Dockers: dockers
  - El Palacio de Hierro: palacio de hierro, el palacio de hierro
"""

from __future__ import annotations

import json
import re
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

# Regex patterns independientes para variantes de empleadores bloqueados.
# Cubren como mínimo las variantes confirmadas en datos reales
# (src/validator.py:BLOCKED_COMPANY_PATTERNS, sin reutilizar ese código).
_HARD_BLOCK_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    # L'Oréal — todas las divisiones y variantes de escritura
    ("L'Oréal", re.compile(
        r"l['’]?or[eé]al"
        r"(?:\s+(?:cosmetics|luxury|division|group|holding|m[eé]xico))?",
        re.IGNORECASE,
    )),
    # L'Oréal variante sin apóstrofo + sede méxico (cobertura alternativa)
    ("L'Oréal", re.compile(
        r"loreal\s+(?:mexico|m[eé]xico)?",
        re.IGNORECASE,
    )),
    # Levi's
    ("Levi's / Dockers", re.compile(
        r"levi['’]?s",
        re.IGNORECASE,
    )),
    # Dockers
    ("Dockers", re.compile(
        r"\bdockers\b",
        re.IGNORECASE,
    )),
    # El Palacio de Hierro — con "el" opcional
    ("El Palacio de Hierro", re.compile(
        r"(?:el\s+)?palacio\s+de\s+hierro",
        re.IGNORECASE,
    )),
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

    Verifica primero por substring contra los términos base de
    hard_blocks.json, luego por regex para variantes no cubiertas
    por los términos base.

    Args:
        brand: Nombre de la marca/empresa a verificar.
        holding: Holding opcional (se concatena para la verificación).

    Returns:
        El término base de hard_blocks.json que hizo match, o el label
        del patrón regex que coincidió, o None si no aplica.
    """
    if not brand:
        return None

    haystack = f"{brand} {holding or ''}"
    haystack_norm = haystack.strip().lower().replace("’", "'").replace("‘", "'")

    # 1. Match por substring contra términos base de hard_blocks.json
    for term in _load_hard_blocked_terms():
        term_norm = term.strip().lower()
        if term_norm and term_norm in haystack_norm:
            return term

    # 2. Match por regex para variantes no cubiertas por términos base
    for label, pattern in _HARD_BLOCK_PATTERNS:
        if pattern.search(haystack):
            return label

    return None


def is_hard_blocked_employer(
    brand: str,
    holding: Optional[str] = None,
) -> bool:
    """Devuelve True si la empresa está en hard_blocks.json (bloqueo total)."""
    return blocked_employer_term(brand, holding) is not None
