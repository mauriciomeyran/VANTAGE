#!/usr/bin/env python3
"""
patch_manual.py — VANTAGE v8.7 Audit Patches
Hallazgos aplicados: #6 (prefijos KERNEL- en ÍNDICE),
                     #7 (IDs RUNTIME- sin sección — marcador),
                     #8 (secciones §4 y §6 faltantes — stubs),
                     #12 (SLA sin ID)

Uso:
    python3 patch_manual.py --dry-run
    python3 patch_manual.py
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime

TARGET = Path("Manual.md")
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

# ─── PATCH #6 — corregir prefijos KERNEL- en ÍNDICE del Manual ───────────────

content = apply(content,
    "0.1 [ID:KERNEL-AUDIENCE-001] Guía de Estilo y Protocolo IA",
    "0.1 [ID:MANUAL-AUDIENCE-001] Guía de Estilo y Protocolo IA",
    "PATCH #6a — KERNEL-AUDIENCE-001 → MANUAL-AUDIENCE-001"
)
content = apply(content,
    "0.2 [ID:KERNEL-PURPOSE-001] Filosofía de Interacción y Kernel",
    "0.2 [ID:MANUAL-PURPOSE-001] Filosofía de Interacción y Kernel",
    "PATCH #6b — KERNEL-PURPOSE-001 → MANUAL-PURPOSE-001"
)
content = apply(content,
    "1.1 [ID:KERNEL-ARCHITECTURE-001] Estructura de Capas (L0-L4)",
    "1.1 [ID:MANUAL-ARCHITECTURE-001] Estructura de Capas (L0-L4)",
    "PATCH #6c — KERNEL-ARCHITECTURE-001 → MANUAL-ARCHITECTURE-001"
)
content = apply(content,
    "1.2 [ID:KERNEL-OWNERSHIP-001] Ownership: Class A vs. Class B",
    "1.2 [ID:MANUAL-OWNERSHIP-001] Ownership: Class A vs. Class B",
    "PATCH #6d — KERNEL-OWNERSHIP-001 → MANUAL-OWNERSHIP-001"
)

# ─── PATCH #7 — agregar nota de resolución para IDs RUNTIME-* en ÍNDICE ──────
# Los IDs RUNTIME-COMMANDS-001 y RUNTIME-RESOLVER-001 no tienen secciones
# correspondientes en el cuerpo. Se agrega un comentario de redirección en el
# ÍNDICE para que quede explícito que resuelven a manual-vantage-runtime-001.

content = apply(content,
    "2.1 [ID:RUNTIME-COMMANDS-001] Comandos de Consola y Agent API",
    "2.1 [ID:RUNTIME-COMMANDS-001] Comandos de Consola y Agent API → resuelve a [ID:372938be-fc42-8050-9a67-e40857d7806e:manual-vantage-runtime-001] §5.2",
    "PATCH #7a — RUNTIME-COMMANDS-001 con nota de resolución"
)
content = apply(content,
    "2.2 [ID:RUNTIME-RESOLVER-001] Resolver: Capa de Contexto Técnico",
    "2.2 [ID:RUNTIME-RESOLVER-001] Resolver: Capa de Contexto Técnico → resuelve a [ID:372938be-fc42-8050-9a67-e40857d7806e:manual-vantage-runtime-001] §5.3",
    "PATCH #7b — RUNTIME-RESOLVER-001 con nota de resolución"
)

# ─── PATCH #8 — insertar stubs §4 y §6 para cerrar gaps de numeración ────────
# §4 CICLO SEMANAL: el contenido del V-Checklist (LUNES/MARTES/MIÉRCOLES...)
# ya existe bajo §3 SETUP. Insertamos el header ##4 justo antes de la línea
# ### [ID:MANUAL-VCHECKLIST-001] para crear la sección formalmente.

VCHECKLIST_HEADER = "### [ID:MANUAL-VCHECKLIST-001] CHECKLIST INTERACTIVO"
SECTION_4_STUB = (
    "## [ID:MANUAL-CICLO-001] 4. CICLO SEMANAL\n"
    "> Contenido: V-Checklist y flujos de operación diaria. "
    "Ver §3 Setup para prerrequisitos.\n\n"
)
content = apply(content,
    VCHECKLIST_HEADER,
    SECTION_4_STUB + VCHECKLIST_HEADER,
    "PATCH #8a — stub §4 CICLO SEMANAL insertado"
)

# §6 GESTIÓN DE DATOS: insertar stub antes de §7 TROUBLESHOOTING
TROUBLESHOOTING_HEADER = "## [ID:MANUAL-TROUBLESHOOTING-001] 7. TROUBLESHOOTING"
SECTION_6_STUB = (
    "## [ID:MANUAL-GESTIÓN-DATOS-001] 6. GESTIÓN DE DATOS\n"
    "> Hard Blocks permanentes: L'Oréal (todas las divisiones) · "
    "Levi Strauss & Co. (Levi's, Dockers) · El Palacio de Hierro · "
    "Roles store-level sin gestión estratégica.\n"
    "> Soft Blocks: recuperables vía RT-1 (Dashboard, Martes §4).\n"
    "> Dedup: ventana 30 días, clave brand+title+location, jerarquía L1>L2>L3.\n\n"
)
content = apply(content,
    TROUBLESHOOTING_HEADER,
    SECTION_6_STUB + TROUBLESHOOTING_HEADER,
    "PATCH #8b — stub §6 GESTIÓN DE DATOS insertado"
)

# ─── PATCH #12 — agregar ID a SLA header ─────────────────────────────────────

content = apply(content,
    "## SLA de Latencia Post-Ingesta",
    "## [ID:MANUAL-SLA-001] SLA de Latencia Post-Ingesta",
    "PATCH #12 — SLA header con ID:MANUAL-SLA-001"
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

print("\nManual.md — DONE\n")
