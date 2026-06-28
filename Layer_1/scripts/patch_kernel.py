#!/usr/bin/env python3
"""
patch_kernel.py — VANTAGE v8.7 Audit Patches
Hallazgos aplicados: #2 (GAP-03 dup), #3 (§4.7/§4.6 order),
                     #4/#5 (UUIDs bare + space post-ID: en headers),
                     #11 (ordered list)

Uso:
    python3 patch_kernel.py --dry-run   # preview sin escribir
    python3 patch_kernel.py             # aplica cambios
"""

import sys
import re
import shutil
from pathlib import Path
from datetime import datetime

TARGET = Path("Kernel.md")   # ajusta el path si el archivo no está en CWD
DRY_RUN = "--dry-run" in sys.argv

# ─── helpers ────────────────────────────────────────────────────────────────

def apply(content: str, old: str, new: str, label: str) -> str:
    count = content.count(old)
    if count == 0:
        print(f"  [SKIP] {label} — patrón no encontrado")
        return content
    if count > 1:
        print(f"  [WARN] {label} — patrón aparece {count} veces, se reemplazará TODAS")
    result = content.replace(old, new)
    print(f"  [OK]   {label} ({count} ocurrencia/s)")
    return result


# ─── read ────────────────────────────────────────────────────────────────────

if not TARGET.exists():
    sys.exit(f"ERROR: {TARGET} no encontrado. Ejecuta desde el directorio que contiene Kernel.md")

original = TARGET.read_text(encoding="utf-8")
content = original

print(f"\n{'DRY RUN — ' if DRY_RUN else ''}Aplicando patches a {TARGET}\n")

# ─── PATCH #2 — eliminar bloque GAP-03 duplicado ────────────────────────────
# El bloque aparece 2 veces consecutivas; eliminamos la segunda instancia
# dejando exactamente una.

GAP_BLOCK = (
    "> ⚠️ ALCANCE DE GAP-03: El guard GAP-03 protege el pipeline Python "
    "(feed_processor.py → process_record()).\n"
    "> Escritura directa vía MCP (notion-create-pages / notion-update-page) y flujos\n"
    "> HANDOFF → CV-B no tienen guard equivalente — esos puntos de entrada pueden escribir\n"
    "> campos Class B sin bloqueo. Estado: gap documentado, pendiente implementación de\n"
    "> class_b_guard.py (FX-1 open)."
)
# El duplicado tiene una línea en blanco entre las dos instancias
DOUBLE_GAP = GAP_BLOCK + "\n" + GAP_BLOCK
content = apply(content, DOUBLE_GAP, GAP_BLOCK, "PATCH #2 — GAP-03 duplicado eliminado")

# ─── PATCH #3 — reordenar §4.7 antes de §4.6 ────────────────────────────────

BLOCK_47 = (
    "### 4.7 registry_seed.json — SSOT de Nodos Figma\n"
    "registry_seed.json no es un campo Class A ni Class B del Tracker. "
    "Es el esquema de IDs de nodos del lienzo Figma, propiedad de la Figma Sync Layer.\n"
    "Ownership: Figma Sync — ni AI Component ni Python lo leen ni escriben durante el "
    "pipeline de vacantes.\n"
    "Contrato de modificación: Solo se actualiza cuando cambia la estructura del lienzo "
    "Figma (nuevos nodos, reordenamiento de frames). El proceso correcto es: exportar IDs "
    "actualizados desde Figma → reemplazar registry_seed.json → verificar cobertura de "
    "tokens → vgit.\n"
    "Ruta canónica: 04-Vantage_CV/Figma Sync/registry_seed.json\n"
)

# Encontrar el bloque §4.6 hasta el separador ---
idx46 = content.find("### 4.6 APROBAR_WRITE")
idx47 = content.find("### 4.7 registry_seed.json")

if idx47 < idx46:
    # Extraer §4.7 (desde su header hasta inicio de §4.6)
    block47 = content[idx47:idx46]
    # Extraer §4.6 (desde su header hasta el próximo ## header o ---)
    rest = content[idx46:]
    m = re.search(r'\n## \[ID:', rest)
    end46 = m.start() if m else len(rest)
    block46 = rest[:end46]

    wrong_order = block47 + block46
    right_order = block46 + block47
    content = apply(content, wrong_order, right_order, "PATCH #3 — §4.7/§4.6 reordenados (4.6→4.7)")
else:
    print("  [SKIP] PATCH #3 — §4.6 ya aparece antes de §4.7, no requiere cambio")

# ─── PATCH #4+#5 — UUIDs bare + espacio en headers de sección ───────────────
# Solo aplicamos en headers ## y ### (donde lazy_loader los usa como anclas).
# Regla: [ID: UUID:ruta] → [ID:UUID:ruta]   (quita espacio post-colon)
# Los UUIDs en prosa los dejamos para un pase manual — demasiado riesgo de
# falsos positivos en referencias cruzadas complejas.

# Sub-patch 5a: espacio después de "ID: " en headers
content = apply(
    content,
    "## [ID: 377938be-fc42-805e-a408-c9ae518d4fe7:",
    "## [ID:377938be-fc42-805e-a408-c9ae518d4fe7:",
    "PATCH #5 — espacio post-ID: en headers ## (KERNEL master UUID)"
)
content = apply(
    content,
    "### [ID: 377938be-fc42-805e-a408-c9ae518d4fe7:",
    "### [ID:377938be-fc42-805e-a408-c9ae518d4fe7:",
    "PATCH #5 — espacio post-ID: en headers ### (KERNEL master UUID)"
)

# ─── PATCH #11 — lista ordenada con numeración incorrecta en §4.5 ────────────

BAD_LIST = (
    "1. Lookup: Localización en entity_index_v2.json.\n"
    "1. Registry Mapping: Mapeo de DB a data_source_id.\n"
    "1. Notion Query: Petición HTTP contra el endpoint de Notion.\n"
    "1. Validation: Verificación de integridad del resultado."
)
GOOD_LIST = (
    "1. Lookup: Localización en entity_index_v2.json.\n"
    "2. Registry Mapping: Mapeo de DB a data_source_id.\n"
    "3. Notion Query: Petición HTTP contra el endpoint de Notion.\n"
    "4. Validation: Verificación de integridad del resultado."
)
content = apply(content, BAD_LIST, GOOD_LIST, "PATCH #11 — lista §4.5 numeración 1/2/3/4")

# ─── write ───────────────────────────────────────────────────────────────────

if DRY_RUN:
    print(f"\nDRY RUN completado. Sin cambios escritos.")
    print(f"Diff de tamaño: {len(original)} → {len(content)} chars "
          f"({'−' if len(content) < len(original) else '+'}{abs(len(content)-len(original))})")
else:
    backup = TARGET.with_suffix(f".bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(TARGET, backup)
    print(f"\nBackup: {backup}")
    TARGET.write_text(content, encoding="utf-8")
    print(f"Escrito: {TARGET}")

print("\nKernel.md — DONE\n")
