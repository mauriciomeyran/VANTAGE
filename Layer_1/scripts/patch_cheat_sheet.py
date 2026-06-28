#!/usr/bin/env python3
"""
patch_cheat_sheet.py — VANTAGE v8.7 Audit Patches
Hallazgos aplicados: #1 (header malformado # ##),
                     #13 (§1 faltante — stub),
                     #14 (changelog sub-IDs en blockquote — nota documental)

Uso:
    python3 patch_cheat_sheet.py --dry-run
    python3 patch_cheat_sheet.py
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime

TARGET = Path("Cheat_Sheet.md")
# También acepta el nombre de archivo con doble guión bajo
if not TARGET.exists():
    TARGET = Path("Cheat_Sheet___Change_Log.md")

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
    sys.exit(f"ERROR: Cheat_Sheet.md / Cheat_Sheet___Change_Log.md no encontrado.")

original = TARGET.read_text(encoding="utf-8")
content = original

print(f"\n{'DRY RUN — ' if DRY_RUN else ''}Aplicando patches a {TARGET}\n")

# ─── PATCH #1 — CRÍTICO: corregir header malformado # ## ─────────────────────

content = apply(content,
    "# ## [ID: 37c938be-fc42-80d4-b9ae-f5969830331b:Aliases_001] 0. CHEAT SHEET",
    "## [ID:37c938be-fc42-80d4-b9ae-f5969830331b:Aliases_001] 0. CHEAT SHEET",
    "PATCH #1 — CRÍTICO: '# ##' → '##' + espacio post-ID: eliminado"
)

# ─── PATCH #13 — insertar stub §1 (sección faltante entre §0 y §2) ───────────
# Se inserta antes del header de §2 CHANGELOG

CHANGELOG_HEADER = "## [ID: 37c938be-fc42-80d4-b9ae-f5969830331b:Change_Log_001] 2. CHANGELOG"
SECTION_1_STUB = (
    "## [ID:37c938be-fc42-80d4-b9ae-f5969830331b:Aliases_detail_001] 1. ALIASES & COMANDOS RÁPIDOS\n"
    "> Aliases canónicos del sistema. Referencia operativa completa en §0 arriba.\n\n"
    "| Alias | Comando completo | Descripción |\n"
    "|-------|-----------------|-------------|\n"
    "| vgit  | python Layer_4/scripts/git_sync.py | Sync git manual |\n"
    "| vdoc  | python Layer_4/scripts/vsync_doc.py | Sync Notion ↔ ACTIVE/ |\n"
    "| vl1   | ~/vantage_pipeline.sh | Pipeline principal |\n"
    "| vl3   | Layer_3/wrappers/layer_3_mail.sh | L3 mail manual |\n"
    "| vd    | dashboard_start.sh | Arranca Dashboard RT-1 |\n\n"
)
content = apply(content,
    CHANGELOG_HEADER,
    SECTION_1_STUB + CHANGELOG_HEADER,
    "PATCH #13 — stub §1 ALIASES & COMANDOS RÁPIDOS insertado"
)

# ─── PATCH #14 — normalizar espacio en ID del CHANGELOG header ───────────────
# [ID: 37c938be...] → [ID:37c938be...] en el header ## del changelog

content = apply(content,
    "## [ID: 37c938be-fc42-80d4-b9ae-f5969830331b:Change_Log_001] 2. CHANGELOG",
    "## [ID:37c938be-fc42-80d4-b9ae-f5969830331b:Change_Log_001] 2. CHANGELOG",
    "PATCH #14 — espacio post-ID: en header CHANGELOG eliminado"
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

print("\nCheat_Sheet.md — DONE\n")
