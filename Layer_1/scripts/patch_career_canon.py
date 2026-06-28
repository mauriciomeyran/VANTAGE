#!/usr/bin/env python3
"""
patch_career_canon.py — VANTAGE v8.7 Audit Patches
Hallazgos aplicados: #9 (título duplicado + metadata desactualizada),
                     #10 (<aside> tag HTML crudo),
                     #15 (§B SKILLS CANON vacía),
                     #16 (§H ACHIEVEMENT LIBRARY vacía)

Uso:
    python3 patch_career_canon.py --dry-run
    python3 patch_career_canon.py
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime

TARGET = Path("Career_Canon.md")
DRY_RUN = "--dry-run" in sys.argv


def apply(content: str, old: str, new: str, label: str) -> str:
    count = content.count(old)
    if count == 0:
        print(f"  [SKIP] {label} — patrón no encontrado")
        return content
    result = content.replace(old, new)
    print(f"  [OK]   {label} ({count} ocurrencia/s)")
    return result


if not TARGET.exists():
    sys.exit(f"ERROR: {TARGET} no encontrado.")

original = TARGET.read_text(encoding="utf-8")
content = original

print(f"\n{'DRY RUN — ' if DRY_RUN else ''}Aplicando patches a {TARGET}\n")

# ─── PATCH #9a — eliminar título duplicado ────────────────────────────────────
# El archivo empieza con:
#   # V | CAREER CANON
#   \n
#   # V | CAREER CANON
#   Versión: 8,5
# Dejamos solo la segunda instancia (que tiene la metadata a continuación).

content = apply(content,
    "# V | CAREER CANON\n\n# V | CAREER CANON\n",
    "# V | CAREER CANON\n",
    "PATCH #9a — título duplicado eliminado"
)

# ─── PATCH #9b — versión desactualizada ──────────────────────────────────────

content = apply(content,
    "Versión: 8,5",
    "Versión: 8.7",
    "PATCH #9b — Versión 8,5 → 8.7"
)

# ─── PATCH #9c — fecha de actualización desactualizada ───────────────────────

content = apply(content,
    "Fecha de actualización: 13 de junio de 2026",
    "Fecha de actualización: 2026-06-27",
    "PATCH #9c — fecha normalizada a ISO 8601"
)

# ─── PATCH #10 — <aside> tag HTML crudo ──────────────────────────────────────
# El bloque:
#   <aside>
#   > ID: 377938be-...:audience-scope-001
# Se convierte en blockquote puro (el <aside> se elimina).

content = apply(content,
    "<aside>\n> ID: 377938be-fc42-8089-93f2-f52dbd2dec6c:audience-scope-001",
    "> ID: 377938be-fc42-8089-93f2-f52dbd2dec6c:audience-scope-001",
    "PATCH #10 — <aside> tag eliminado"
)

# ─── PATCH #15 — §B SKILLS CANON vacía ───────────────────────────────────────

content = apply(content,
    "## [ID: 377938be-fc42-8089-93f2-f52dbd2dec6c:canon-skills-001] B. SKILLS CANON\n---",
    (
        "## [ID: 377938be-fc42-8089-93f2-f52dbd2dec6c:canon-skills-001] B. SKILLS CANON\n"
        "> [PENDING DATA] — Skills Canon pendiente de actualización. "
        "Ejecutar CANON-UPDATE para poblar esta sección.\n"
        "---"
    ),
    "PATCH #15 — §B SKILLS CANON marcada como PENDING DATA"
)

# ─── PATCH #16 — §H ACHIEVEMENT LIBRARY vacía ────────────────────────────────

content = apply(content,
    "## [ID: 377938be-fc42-8089-93f2-f52dbd2dec6c:canon-achievements-001] H. ACHIEVEMENT LIBRARY\n---",
    (
        "## [ID: 377938be-fc42-8089-93f2-f52dbd2dec6c:canon-achievements-001] H. ACHIEVEMENT LIBRARY\n"
        "> [PENDING DATA] — Achievement Library pendiente de actualización. "
        "Ejecutar CANON-UPDATE para poblar esta sección.\n"
        "---"
    ),
    "PATCH #16 — §H ACHIEVEMENT LIBRARY marcada como PENDING DATA"
)

# ─── write ────────────────────────────────────────────────────────────────────

if DRY_RUN:
    print(f"\nDRY RUN completado.")
    print(f"Diff de tamaño: {len(original)} → {len(content)} chars "
          f"({'−' if len(content) < len(original) else '+'}{abs(len(content)-len(original))})")
else:
    backup = TARGET.with_suffix(f".bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(TARGET, backup)
    print(f"\nBackup: {backup}")
    TARGET.write_text(content, encoding="utf-8")
    print(f"Escrito: {TARGET}")

print("\nCareer_Canon.md — DONE\n")
