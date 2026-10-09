"""
T3.I (propuesta) · Prueba de paridad matcher ↔ Layer_1/config/hard_blocks.json.

hard_blocks.json v1.1 (decisión del operador 2026-10-07) es la fuente
ejecutable única de Hard Blocks. El set BLOCKED_EMPLOYERS del matcher
(linkedin_identity_matcher.py) debe ser consistente con ese conjunto
(identidades canónicas + alias del JSON) y NO debe incluir Dockers.

Nota de gobernanza: cualquier cambio a BLOCKED_EMPLOYERS altera el SHA de
implementación ligado al contrato CANONICAL PromptA-v2.0+linkedin (f7fa0513…)
y exige re-promoción del operador (nueva fila/versión en PROMPT_CANON).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from linkedin_identity_matcher import BLOCKED_EMPLOYERS, normalize_identity

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "hard_blocks.json"

# Decisión del operador 2026-10-07 + notas de hard_blocks.json v1.1:
# alias (minúsculas, tal cual en el JSON) → identidad canónica del matcher.
CANONICAL_BY_ALIAS = {
    "l'oreal": "L'Oréal",
    "loreal": "L'Oréal",
    "l'oréal": "L'Oréal",
    "l'oreal mexico": "L'Oréal",
    "l'oreal méxico": "L'Oréal",
    "l'oreal luxury": "L'Oréal",
    "l'oreal group": "L'Oréal",
    "levi's": "Levi's",
    "levis": "Levi's",
    "levi strauss": "Levi Strauss",
    "levi strauss & co": "Levi Strauss",
    "palacio de hierro": "El Palacio de Hierro",
    "el palacio de hierro": "El Palacio de Hierro",
}


def _load_hard_blocks() -> tuple[dict, set[str]]:
    data = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    aliases = {str(e).strip().lower() for e in data["hard_block_employers"]}
    return data, aliases


def test_dockers_absent_from_both_sources():
    """Decisión 2026-10-07: Dockers NO es Hard Block en ninguna de las dos fuentes."""
    data, aliases = _load_hard_blocks()
    assert "dockers" not in aliases, (
        "hard_blocks.json no debe incluir 'dockers' (decisión del operador 2026-10-07)"
    )
    matcher_norms = {normalize_identity(name) for name in BLOCKED_EMPLOYERS}
    assert "dockers" not in matcher_norms, (
        "BLOCKED_EMPLOYERS del matcher no debe incluir Dockers "
        "(decisión del operador 2026-10-07)"
    )


def test_every_json_alias_is_covered_by_matcher():
    """Cada alias del JSON debe resolver a una identidad del matcher."""
    data, aliases = _load_hard_blocks()
    matcher_norms = {normalize_identity(name) for name in BLOCKED_EMPLOYERS}
    for alias in sorted(aliases):
        canonical = CANONICAL_BY_ALIAS.get(alias)
        assert canonical is not None, (
            f"El alias '{alias}' de hard_blocks.json v{data.get('version')} no tiene "
            "mapeo en CANONICAL_BY_ALIAS; actualiza esta prueba si el set cambió"
        )
        assert normalize_identity(canonical) in matcher_norms, (
            f"hard_blocks.json incluye '{alias}' (canónico: '{canonical}') pero "
            "BLOCKED_EMPLOYERS del matcher no lo cubre"
        )


def test_every_matcher_identity_appears_in_json():
    """Cada identidad del matcher debe aparecer (normalizada) entre los alias del JSON."""
    data, aliases = _load_hard_blocks()
    for name in sorted(BLOCKED_EMPLOYERS):
        norm = normalize_identity(name)
        assert norm in aliases, (
            f"La identidad '{name}' del matcher (normalizada: '{norm}') no aparece "
            f"en hard_blocks.json v{data.get('version')}"
        )


def test_aeropostale_is_not_hard_block():
    """Aéropostale NO es Hard Block (confirmado con el operador; notas del JSON)."""
    data, aliases = _load_hard_blocks()
    assert "aeropostale" not in aliases
    assert "aéropostale" not in aliases
    matcher_norms = {normalize_identity(name) for name in BLOCKED_EMPLOYERS}
    assert "aeropostale" not in matcher_norms
