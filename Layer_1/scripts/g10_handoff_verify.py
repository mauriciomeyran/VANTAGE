#!/usr/bin/env python3
"""
g10_handoff_verify.py — G10: verifica handoff de cierre + frase obligatoria.

Cero Notion. Exit 0 = completo.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HANDOFF = ROOT / "handoffs" / "HANDOFF_G10_CIERRE_ORQUESTADOR_2026-09-12.md"

REQUIRED = [
    "ARENA-20260912-G10",
    "Ninguna escritura a Notion de producción fue realizada ni intentada en esta sesión.",
    "layer_1_orchestrator.py",
    "tracker_flow.is_mutable",
    "e24b4b1",  # G9 tip in gates table
    "Q-4",
    "Q-10",
    "G8_DEPLOYMENT_PLAN",
    "G9_DOCSYNC_PACKAGE",
    "250 passed",
    "Archive/Legacy_Scripts/layer_1_run.py",
    "442938be-fc42-828f-b72e-076818d65a5b",
]


def main() -> int:
    print("=" * 60)
    print("G10 handoff verify")
    print("=" * 60)
    if not HANDOFF.exists():
        print(f"  ✗ missing {HANDOFF.relative_to(ROOT)}")
        return 1
    text = HANDOFF.read_text(encoding="utf-8")
    fails = [n for n in REQUIRED if n not in text]
    phrase = "Ninguna escritura a Notion de producción fue realizada ni intentada en esta sesión."
    if text.count(phrase) < 2:
        fails.append("phrase must appear ≥2 times")
    # Tip: either 40-hex or explicit rev-parse instruction (E4 live check)
    m = re.search(r"\*\*Tip \(local = origin\):\*\* `([0-9a-f]{40})`", text)
    if m:
        print(f"  · tip sha {m.group(1)[:7]}")
    elif "git rev-parse HEAD" in text:
        print("  · tip via git rev-parse HEAD (E4 live)")
    else:
        fails.append("Tip SHA or rev-parse instruction missing")
    # G10 row has short sha (7 hex) or range
    if not re.search(r"\| \*\*G10\*\* \| `([0-9a-f]{7})(?:…HEAD)?` \|", text):
        # fallback: any G10 row with backtick sha
        if not re.search(r"\*\*G10\*\*.*`[0-9a-f]{7}`", text):
            fails.append("G10 gates table row missing short sha")
    if fails:
        for f in fails:
            print(f"  ✗ missing {f!r}")
        return 1
    if (ROOT / "Layer_1" / "scripts" / "layer_1_run.py").exists():
        print("  ✗ layer_1_run.py still in active tree")
        return 1
    if not (ROOT / "Archive" / "Legacy_Scripts" / "layer_1_run.py").exists():
        print("  ✗ archived layer_1_run missing")
        return 1
    print(f"  ✓ handoff OK ({len(REQUIRED)} anchors + tip/G10 row)")
    print(f"  ✓ phrase ×{text.count(phrase)}")
    print(f"  ✓ layer_1_run absent active / present Archive")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
