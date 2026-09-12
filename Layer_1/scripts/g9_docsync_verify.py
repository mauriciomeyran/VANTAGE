#!/usr/bin/env python3
"""
g9_docsync_verify.py — G9: verifica que el mirror repo contiene los diffs mandatorios.

Cero Notion. Exit 0 = paquete completo; 1 = falta ancla.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CHECKS = [
    (ROOT / "Documentación/ACTIVE/Kernel.md", [
        "DEROGACIÓN PARCIAL",
        "tracker_flow.is_mutable",
        "layer_1_orchestrator.py",
        "Seguimiento",
        "Preparación Entrevista",
        "PROTECTED_STATUSES",
        "Q-4",
    ]),
    (ROOT / "Documentación/ACTIVE/Manual.md", [
        "layer_1_orchestrator.py",
        "vl1_sync.py",
        "normalize_tracker_values.py",
        "RETIRADO (G6 / Q-10)",
    ]),
    (ROOT / "Documentación/ACTIVE/Aliases.md", [
        "layer_1_orchestrator.py --dry-run",
        "vl1batch",
    ]),
    (ROOT / "Documentación/ACTIVE/Change Log.md", [
        "v9.22.0",
        "GATE-DECISION-010",
        "APROBAR_WRITE",
    ]),
    (ROOT / "skills/- Tidy/vantage-tidy-opportunities-tracker/SKILL.md", [
        "is_mutable",
        "G9 / orquestador v9",
    ]),
    (ROOT / "handoffs/PREGUNTAS_ABIERTAS.md", [
        "CERRADA en G9",
    ]),
    (ROOT / "Layer_1/docs/G9_DOCSYNC_PACKAGE.md", [
        "Q-4",
        "v9.22.0",
    ]),
]


def main() -> int:
    fails = []
    for path, needles in CHECKS:
        if not path.exists():
            fails.append(f"MISSING FILE {path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8")
        for n in needles:
            if n not in text:
                fails.append(f"{path.relative_to(ROOT)} missing {n!r}")
    print("=" * 60)
    print("G9 docsync verify — repo mirror")
    print("=" * 60)
    if fails:
        for f in fails:
            print(f"  ✗ {f}")
        print(f"fail={len(fails)}")
        return 1
    print(f"  ✓ all anchors present ({sum(len(n) for _, n in CHECKS)} checks, {len(CHECKS)} files)")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
