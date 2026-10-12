"""T12 (decisión del operador 2026-10-12) — Consistencia de notas de
Layer_1/config/hard_blocks.json.

La nota de sincronización no debe contradecir la fuente ejecutable única
(nota "Fuente ejecutable única…", decisión del operador 2026-10-07): la
dirección de sincronización es hard_blocks.json → redacción derivada
(Career Canon / Manual §10), nunca al revés. Sin red, sin Notion.
"""

from __future__ import annotations

import json
from pathlib import Path

_CONFIG = Path(__file__).resolve().parent.parent / "config" / "hard_blocks.json"


def _config() -> dict:
    with open(_CONFIG, encoding="utf-8") as f:
        return json.load(f)


# Set v1.1 — T12 no lo toca (decisión del operador). Un cambio de set es
# decisión del operador y debe actualizar este test en el mismo commit.
EXPECTED_EMPLOYERS = [
    "l'oreal",
    "loreal",
    "l'oréal",
    "l'oreal mexico",
    "l'oreal méxico",
    "l'oreal luxury",
    "l'oreal group",
    "levi's",
    "levis",
    "palacio de hierro",
    "el palacio de hierro",
    "levi strauss",
    "levi strauss & co",
]


class TestHardBlocksNotesConsistency:
    """La redacción de notas no contradice la fuente ejecutable única."""

    def test_employer_set_unchanged(self):
        assert _config()["hard_block_employers"] == EXPECTED_EMPLOYERS

    def test_no_external_canonical_source_instruction(self):
        # Regresión T12: la frase anterior ("Mantener sincronizado manualmente
        # con la fuente canónica …") trataba un documento externo como fuente
        # canónica y contradecía la nota de fuente ejecutable única.
        notes = " | ".join(_config()["notes"])
        assert "sincronizado manualmente con la fuente canónica" not in notes
        assert "fuente canónica" not in notes

    def test_single_executable_source_note_present(self):
        assert any("Fuente ejecutable única" in n for n in _config()["notes"])

    def test_sync_direction_points_to_derived_docs(self):
        # La sincronización va de este archivo hacia la redacción derivada.
        assert any("redacción derivada" in n for n in _config()["notes"])
