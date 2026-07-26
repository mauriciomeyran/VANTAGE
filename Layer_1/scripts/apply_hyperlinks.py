#!/usr/bin/env python3
"""
apply_hyperlinks.py (REFACTOR — importa de vantage_id_rules.py)

Convierte referencias cruzadas en prosa plana y filas de TOC a
hipervínculos Markdown accionables, en los documentos fundacionales de
VANTAGE, usando el mapeo ID -> URL de bloque.

CAMBIOS respecto a la versión anterior (ver Changelog, sesión 2026-07-25):
    1. Toda la lógica DEF/REF/heading/boundary ahora vive en
       vantage_id_rules.py — este script ya NO reimplementa su propia
       copia de heading_looks_like_def/line_is_standalone_id.
    2. Soporta el nuevo formato canónico de heading "NN PREFIX:KEY" /
       "NN.N PREFIX:KEY-NNN" (sin símbolo §), además del legacy "§N ID"
       durante la transición.
    3. NUEVO: las filas de tabla-TOC (tabla índice de secciones, ej.
       "| 8 | CANON:OUTPUT-CONTRACT | Contrato de entregable | ESQUEMA |")
       ahora SÍ se convierten a hipervínculo. Antes, el TOC se trataba
       como cualquier otra tabla de cuerpo (ya se enlazaba si el ID
       aparecía en backticks solitarios dentro de una celda) — este
       comportamiento se mantiene y se documenta explícitamente, no
       cambia el resultado pero aclara la intención.
    4. Los headings de definición NUNCA se auto-enlazan (sin cambio,
       confirmado por el operador como regla permanente).
    5. MAPPING actualizado con los 14 IDs afectados por el DRY RUN de
       migración de headings (aprobado por el operador, 2026-07-25):
         - KERNEL:SCOPE + KERNEL:ROUTING -> KERNEL:CONTEXT-INFRASTRUCTURE
           (-001 / -002). IDs viejos conservados como alias legacy.
         - SP:CEDULA-DIGITAL -> SP:DIGITAL-ID-CARD-001 (alias legacy).
         - Stubs SP §4/§5/§7 -> SP:CONTEXT-INFRASTRUCTURE-REF /
           SP:DATA-FLOW-REF / SP:CV-GOLDEN-RULES-REF, apuntando al MISMO
           anchor del Kernel (no crean anchor nuevo).
         - SP:CONSISTENCY duplicado (antiguo §9) -> SP:MCP-ROUTING-NOTES.
           Verificado por grep contra los 6 documentos + Change Log:
           NINGUNA referencia cruzada real apuntaba al §9 — todas las
           citas de "SP:CONSISTENCY" en el sistema resuelven al anchor
           del §11 (el real). Anchor del §9 AÚN PENDIENTE (placeholder
           en el MAPPING) — nadie lo capturó todavía por fetch directo.
         - 6 traducciones ES->EN de IDs de Manual (OBJETIVO->OBJECTIVE,
           FUNCIONAMIENTO->HOW-IT-WORKS, FALLO->FAILURE-PHILOSOPHY,
           FLUJO->WEEKLY-FLOW, GESTION-DATOS->DATA-MANAGEMENT,
           REGLAS-DE-ORO->GOLDEN-RULES). Anchors preservados exactos,
           IDs viejos conservados como alias legacy.
         - MANUAL:COLD-START-001 (Manual §5, sin ID previo) y
           ALIASES:DEDUP (Aliases §8, sin ID previo): anchors PENDIENTES
           — placeholder en el MAPPING hasta escribir el heading nuevo
           en Notion y capturar el anchor real de bloque.

       ANTES de correr --apply sobre Notion: reemplazar los 3 anchors
       marcados "PENDIENTE_ANCHOR..." con los anchors reales, capturados
       DESPUÉS de escribir los headings nuevos correspondientes.

Uso:
    # 1. SIEMPRE primero en modo DRY RUN (default, no escribe nada):
    python3 apply_hyperlinks.py --root "../Documentación/ACTIVE"

    # 2. Revisa el diff impreso y el archivo dry_run_hyperlinks.diff generado.

    # 3. Solo si el diff se ve correcto, aplica de verdad:
    python3 apply_hyperlinks.py --root "../Documentación/ACTIVE" --apply
"""

import argparse
import difflib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vantage_id_rules as rules

# ─── Mapeo ID -> URL de bloque ────────────────────────────────────────────
# (idéntico al script anterior — sin cambios en los anchors, solo en la
# lógica de detección que decide CUÁNDO usar este mapeo)

KERNEL_PAGE = "https://app.notion.com/p/377938befc42805ea408c9ae518d4fe7"
SP_PAGE = "https://app.notion.com/p/37b938befc4280019b9bfcf81130d274"
MANUAL_PAGE = "https://app.notion.com/p/372938befc4280509a67e40857d7806e"
CANON_PAGE = "https://app.notion.com/p/377938befc42808993f2f52dbd2dec6c"

MAPPING = {
    # --- KERNEL ---
    "KERNEL:ARCHITECTURE-L0-BOOTSTRAP": f"{KERNEL_PAGE}#a152eaabc7fd444699fd23a5a0190757",
    "KERNEL:AUDIENCE-SCOPE": f"{KERNEL_PAGE}#390938befc4280b58035d9581a04262f",
    "KERNEL:PURPOSE": f"{KERNEL_PAGE}#39e938befc4281f69905dfc6c82c5503",
    "KERNEL:ARCHITECTURE": f"{KERNEL_PAGE}#39e938befc42818a8a61d5a0d71bcf2b",
    "KERNEL:ARCHITECTURE-L0": f"{KERNEL_PAGE}#39e938befc428187b290da141856b8fe",
    "KERNEL:SKILL-ANNOUNCE-CONVENTION": f"{KERNEL_PAGE}#39e938befc4281db9f8eee98d8f90185",
    "KERNEL:ARCHITECTURE-L1": f"{KERNEL_PAGE}#39e938befc4281239ba0dbbe67a4bc1e",
    "KERNEL:ARCHITECTURE-L2": f"{KERNEL_PAGE}#39e938befc4281f6a4e3cfaad30ff1e5",
    "KERNEL:ARCHITECTURE-L3": f"{KERNEL_PAGE}#39e938befc4281d6b2b4faa312b14210",
    "KERNEL:ARCHITECTURE-L4": f"{KERNEL_PAGE}#39e938befc4281aa859de201c02dc6ae",
    "KERNEL:DASHBOARD-CHECKLIST-ARCH": f"{KERNEL_PAGE}#39e938befc42816ead88efa4b9a4e05f",
    "KERNEL:SCHEMA": f"{KERNEL_PAGE}#39e938befc42812dbc97e075758ba0ee",
    "KERNEL:SCHEMA-001": f"{KERNEL_PAGE}#39e938befc4281faa81ac25589b3c67f",
    "KERNEL:SCHEMA-002": f"{KERNEL_PAGE}#39e938befc4281609ac6eec8e5d03b24",
    "KERNEL:SCHEMA-003": f"{KERNEL_PAGE}#39e938befc42817eb1dad96ac1ccc2b0",
    "KERNEL:SCHEMA-004": f"{KERNEL_PAGE}#39e938befc42814e90c1c0833543a831",
    "KERNEL:SCHEMA-005": f"{KERNEL_PAGE}#39e938befc4281578785ea331b8b6c18",
    "KERNEL:SCHEMA-006": f"{KERNEL_PAGE}#39e938befc428178a99ec6c01fe63720",
    "KERNEL:SCHEMA-007": f"{KERNEL_PAGE}#39e938befc4281199a63f8a55a71eef9",
    "KERNEL:TRACKER-SCHEMA": f"{KERNEL_PAGE}#39e938befc4281c2ba8aca2a41ff358b",
    "KERNEL:TRACKER-SCHEMA-001": f"{KERNEL_PAGE}#39e938befc42817ab848edd42582140c",
    "KERNEL:TRACKER-SCHEMA-002": f"{KERNEL_PAGE}#39e938befc42811b8eeef6e10b03ba2e",
    "KERNEL:HEALTH-CHECK": f"{KERNEL_PAGE}#39e938befc428131bc81cfc9a5d0d1a3",
    "KERNEL:HEALTH-CHECK-001": f"{KERNEL_PAGE}#39e938befc42812d8303fa0cd5118520",
    "KERNEL:HEALTH-CHECK-002": f"{KERNEL_PAGE}#39e938befc428139b00bcbf721337856",
    "KERNEL:OWNERSHIP": f"{KERNEL_PAGE}#39e938befc42814385dbe5005b04496c",
    "KERNEL:OWNERSHIP-001": f"{KERNEL_PAGE}#39e938befc42813f859af1dc3ce6943a",
    "KERNEL:OWNERSHIP-002": f"{KERNEL_PAGE}#39e938befc4281b2af80c4f4f31f42b5",
    "KERNEL:TRIGGERS": f"{KERNEL_PAGE}#39e938befc4281f297c7d591f3c132f4",
    "KERNEL:TRIGGER-001": f"{KERNEL_PAGE}#39e938befc4281b8bd25efe38438bb51",
    "KERNEL:TRIGGER-002": f"{KERNEL_PAGE}#39e938befc4281d7a7dde34a70b36ec8",
    "KERNEL:TRIGGER-003": f"{KERNEL_PAGE}#39e938befc428195a017f76fd50b9f02",
    "KERNEL:TRIGGER-004": f"{KERNEL_PAGE}#39e938befc428171a907cbb18445e36f",
    "KERNEL:TRIGGER-005": f"{KERNEL_PAGE}#39e938befc4281a6a3b1fba186508580",
    "KERNEL:TRIGGER-006": f"{KERNEL_PAGE}#39e938befc4281edb6d8f1537b706106",
    "KERNEL:TRIGGER-007": f"{KERNEL_PAGE}#39e938befc4281b08536e0d347558d5e",
    "KERNEL:TRIGGER-008": f"{KERNEL_PAGE}#39e938befc4281bf95d8dde2c5806acc",
    "KERNEL:TRIGGER-009": f"{KERNEL_PAGE}#39e938befc4281298abadc56877df0c0",
    "KERNEL:GATE-DECISION": f"{KERNEL_PAGE}#39e938befc42810d9f3af9b12751d7e1",
    "KERNEL:GATE-DECISION-001": f"{KERNEL_PAGE}#39e938befc428193bf9fddf256e09973",
    "KERNEL:GATE-DECISION-002": f"{KERNEL_PAGE}#39e938befc42815a9d52ccf7394c183a",
    "KERNEL:GATE-DECISION-003": f"{KERNEL_PAGE}#39e938befc4281588c98d61c66e29099",
    "KERNEL:GATE-DECISION-004": f"{KERNEL_PAGE}#39e938befc428189b370f75da76b8b6a",
    "KERNEL:GATE-DECISION-005": f"{KERNEL_PAGE}#39e938befc428113ac64f877a148e71e",
    "KERNEL:GATE-DECISION-006": f"{KERNEL_PAGE}#39e938befc4281d1a8c9fd8e3acdfd96",
    "KERNEL:GATE-DECISION-007": f"{KERNEL_PAGE}#c63a7e403c1e40b1a544802a50a84bc2",
    "KERNEL:GATE-DECISION-008": f"{KERNEL_PAGE}#006e0b519639447590ad173aebc265c4",
    "KERNEL:NAMING-CONVENTION": f"{KERNEL_PAGE}#39e938befc4281bbbe93d1e053bb8e42",
    "KERNEL:CV-GOLDEN-RULES": f"{KERNEL_PAGE}#39e938befc428148a288d1c640c6f64d",
    "KERNEL:CV-GOLDEN-RULES-001": f"{KERNEL_PAGE}#39e938befc4281c0b026c8bcf4901816",
    "KERNEL:CV-GOLDEN-RULES-002": f"{KERNEL_PAGE}#39e938befc428196851ef48a510e16ca",
    "KERNEL:CV-GOLDEN-RULES-003": f"{KERNEL_PAGE}#39e938befc428140b36ff15f47f0a359",
    "KERNEL:CV-GOLDEN-RULES-004": f"{KERNEL_PAGE}#39e938befc4281a29b7adf00572b5f87",
    "KERNEL:CV-GOLDEN-RULES-005": f"{KERNEL_PAGE}#39e938befc42814ebc31de3ceca9c168",
    "KERNEL:CV-PIPELINE": f"{KERNEL_PAGE}#39e938befc428190b72cf74c14c31a4a",
    "KERNEL:CANON-UPDATE": f"{KERNEL_PAGE}#39e938befc42817db23de75a46a964ac",
    "KERNEL:FAIL-PHILOSOPHY": f"{KERNEL_PAGE}#39e938befc428121bb10efedac1b4b99",
    # KERNEL:SCOPE + KERNEL:ROUTING fusionados (DRY RUN migración headings,
    # aprobado por el operador 2026-07-25) -> KERNEL:CONTEXT-INFRASTRUCTURE
    # padre + -001 (antiguo Scope) / -002 (antiguo Routing) como subsecciones.
    # Los IDs viejos se conservan como alias hasta que la migración de
    # headings se aplique en Notion — evita romper cualquier documento
    # todavía no migrado que cite el ID legacy.
    "KERNEL:CONTEXT-INFRASTRUCTURE": f"{KERNEL_PAGE}#39e938befc42810293b4e55167657d86",
    "KERNEL:CONTEXT-INFRASTRUCTURE-001": f"{KERNEL_PAGE}#39e938befc42810293b4e55167657d86",
    "KERNEL:CONTEXT-INFRASTRUCTURE-002": f"{KERNEL_PAGE}#39e938befc42811aa042c048ec085cbc",
    "KERNEL:SCOPE": f"{KERNEL_PAGE}#39e938befc42810293b4e55167657d86",  # alias legacy — retirar tras migración
    "KERNEL:DATA-FLOW": f"{KERNEL_PAGE}#39e938befc428101ade4f430c4bee781",
    "KERNEL:ROUTING": f"{KERNEL_PAGE}#39e938befc42811aa042c048ec085cbc",  # alias legacy — retirar tras migración
    "KERNEL:EVOLUTION": f"{KERNEL_PAGE}#39e938befc42816d813af068ac1d81be",
    "KERNEL:DOC-CONTRACT": f"{KERNEL_PAGE}#39e938befc42818db48bd305897d390f",
    "KERNEL:NORM": f"{KERNEL_PAGE}#39e938befc428147809de3602d40d326",
    "KERNEL:CENSUS-SYNC": f"{KERNEL_PAGE}#39e938befc4281599aa3f17926239597",
    "KERNEL:SESSION-LEDGER": f"{KERNEL_PAGE}#39e938befc42816aa4e8c4daaebe11b1",
    "KERNEL:DOCUMENTATION-TRANSVERSAL-001": f"{KERNEL_PAGE}#39e938befc428142a984f97acbd800b4",
    "KERNEL:VERSION-CHECK-TOOL": f"{KERNEL_PAGE}#380a32a5525b4d5d8cd44516fb1b74d4",

    # --- SYSTEM PROMPT ---
    # SP:CEDULA-DIGITAL renombrado a SP:DIGITAL-ID-CARD-001 (DRY RUN
    # migración headings, aprobado 2026-07-25). Alias legacy conservado
    # hasta aplicar la migración en Notion.
    "SP:DIGITAL-ID-CARD-001": f"{SP_PAGE}#39a938befc42813ca3fde84a978517c0",
    "SP:CEDULA-DIGITAL": f"{SP_PAGE}#39a938befc42813ca3fde84a978517c0",  # alias legacy — retirar tras migración

    # Stubs de System Prompt (§4/§5/§7) que antes reusaban literalmente el
    # ID del Kernel -> ahora tienen ID propio -REF, apuntando al MISMO
    # anchor del Kernel (no crean anchor nuevo, solo dejan de colisionar
    # con el ID padre real del Kernel). Aprobado por el operador 2026-07-25.
    "SP:CONTEXT-INFRASTRUCTURE-REF": f"{KERNEL_PAGE}#39e938befc42810293b4e55167657d86",
    "SP:DATA-FLOW-REF": f"{KERNEL_PAGE}#39e938befc428101ade4f430c4bee781",
    "SP:CV-GOLDEN-RULES-REF": f"{KERNEL_PAGE}#39e938befc428148a288d1c640c6f64d",

    # SP:CONSISTENCY duplicado (antiguo §9, notas MCP/Terminal) renombrado
    # a SP:MCP-ROUTING-NOTES. Verificado por grep contra los 6 documentos +
    # Change Log: ninguna referencia cruzada real apuntaba al anchor del
    # §9 — todas las citas de "SP:CONSISTENCY" en el sistema ya resolvían
    # al anchor del §11 (el real). Aprobado por el operador 2026-07-25.
    "SP:MCP-ROUTING-NOTES": f"{SP_PAGE}#PENDIENTE_ANCHOR_§9_MCP_TERMINAL",
    "SP:TRIGGERS": f"{SP_PAGE}#39a938befc4281e39643e90b1e5c8613",
    "SP:SCHEMA": f"{SP_PAGE}#39a938befc4281f6a321f71d15c03e5d",
    "SP:ID-CONNECTORS-001": f"{SP_PAGE}#39a938befc42812ab19fe572be4eac94",
    "SP:BOOTSTRAP-001": f"{SP_PAGE}#39a938befc4281c68a05fd98ecfef859",
    "SP:SYNC-RULE": f"{SP_PAGE}#39a938befc4281f1ae66e4e694a74ddd",
    "SP:CONSISTENCY": f"{SP_PAGE}#39a938befc428152b7b1fc33a4e390ca",
    "SP:VERSION-CHECK-TOOL": f"{SP_PAGE}#b84275d1780b498a94cdb554244df034",

    # --- MANUAL ---
    # Traducciones ES->EN de IDs de Manual (DRY RUN migración headings,
    # aprobado 2026-07-25). Anchors preservados exactos. IDs viejos
    # conservados como alias hasta aplicar la migración en Notion.
    "MANUAL:OBJECTIVE-001": f"{MANUAL_PAGE}#39d938befc42803dbcebf1425c969871",
    "MANUAL:OBJETIVO-001": f"{MANUAL_PAGE}#39d938befc42803dbcebf1425c969871",  # alias legacy
    "MANUAL:HOW-IT-WORKS-001": f"{MANUAL_PAGE}#39d938befc4280bbbe44e15673de53f1",
    "MANUAL:FUNCIONAMIENTO-001": f"{MANUAL_PAGE}#39d938befc4280bbbe44e15673de53f1",  # alias legacy
    "MANUAL:SETUP-001": f"{MANUAL_PAGE}#39d938befc428083b0d2eae131ec3854",
    "MANUAL:WEEKLY-FLOW-001": f"{MANUAL_PAGE}#39d938befc428005bc2edb8ec38fcf20",
    "MANUAL:FLUJO-001": f"{MANUAL_PAGE}#39d938befc428005bc2edb8ec38fcf20",  # alias legacy
    # Nuevo ID sin anchor real todavía — Manual §5 (Arranque Frío/Cold
    # Start) no tenía ID antes de esta sesión. Pendiente el anchor de
    # bloque real hasta que se escriba el heading nuevo en Notion.
    "MANUAL:COLD-START-001": f"{MANUAL_PAGE}#PENDIENTE_ANCHOR_HEADING_NUEVO",
    "MANUAL:VCHECKLIST-001": f"{MANUAL_PAGE}#39d938befc4280ff8e9ec87ceb0b3468",
    "MANUAL:DASHBOARD-001": f"{MANUAL_PAGE}#39d938befc428013af17d536c665a3c4",
    "MANUAL:VANTAGE-RUNTIME-001": f"{MANUAL_PAGE}#39d938befc4280ff8c1ed556864bcdd4",
    "MANUAL:DATA-MANAGEMENT-001": f"{MANUAL_PAGE}#39d938befc428094afa0dd90d54e27e5",
    "MANUAL:GESTION-DATOS-001": f"{MANUAL_PAGE}#39d938befc428094afa0dd90d54e27e5",  # alias legacy
    "MANUAL:TROUBLESHOOTING-001": f"{MANUAL_PAGE}#39d938befc4280f1b941ff06a6b8e0c6",
    "MANUAL:PROMPTS-WRAPPERS-001": f"{MANUAL_PAGE}#39d938befc4280d4a43cd7b6ec0ace17",
    "MANUAL:CHEATSHEETS-001": f"{MANUAL_PAGE}#39d938befc4280169578d883abe71b78",
    "MANUAL:HEALTHCHECK-001": f"{MANUAL_PAGE}#39d938befc428049a4b1c89fec3b8225",
    "MANUAL:GOLDEN-RULES-001": f"{MANUAL_PAGE}#39d938befc4280cd876bdfec6f2989b3",
    "MANUAL:REGLAS-DE-ORO-001": f"{MANUAL_PAGE}#39d938befc4280cd876bdfec6f2989b3",  # alias legacy
    "MANUAL:FAILURE-PHILOSOPHY-001": f"{MANUAL_PAGE}#39d938befc4280d29606d557df03c39d",
    "MANUAL:FALLO-001": f"{MANUAL_PAGE}#39d938befc4280d29606d557df03c39d",  # alias legacy
    "MANUAL:SLA-001": f"{MANUAL_PAGE}#39d938befc4280caaea9eb250038df97",
    "MANUAL:SESSION-CYCLE-001": f"{MANUAL_PAGE}#39d938befc428050b634dc6b147e3c16",
    "MANUAL:PATCH-QUALITY-001": f"{MANUAL_PAGE}#39d938befc42807d9133fa1477975b44",
    "MANUAL:CV-GOLDEN-RULES-INDEX": f"{MANUAL_PAGE}#3b50c9994bb6457a8afde3252f4647eb",
    "MANUAL:POSITIONING-CRITERIA": f"{MANUAL_PAGE}#01ffec90def642749ae52ef84da7a56b",
    "MANUAL:GOLDEN-SKELETON-REF": f"{MANUAL_PAGE}#e457e54ec4a84a778a7cfd248e718188",
    "MANUAL:SCHEMA-FIELD-REF": f"{MANUAL_PAGE}#4cafd4cfe04847368733b9ba19faf39c",

    # --- CAREER CANON ---
    "CANON:PROFILE-001": f"{CANON_PAGE}#39a938befc42819eada8c4c10a8513f4",
    "CANON:SKILLS-001": f"{CANON_PAGE}#39a938befc4281e58a53c9554cb3693d",
    "CANON:EXPERIENCE-001": f"{CANON_PAGE}#39a938befc42812fbebcdcf9b4287266",
    "CANON:ACHIEVEMENTS-001": f"{CANON_PAGE}#39a938befc4281fc9f88dc891c180b2a",
    "CANON:KPIS-001": f"{CANON_PAGE}#39a938befc42810ba9a1f0febedc739d",
    "CANON:FACTS-001": f"{CANON_PAGE}#39a938befc4281f49ca3f45975cfe4c7",
    "CANON:POSITIONING-001": f"{CANON_PAGE}#39a938befc42811ba92acf1dc1467702",
    "CANON:OUTPUT-CONTRACT": f"{CANON_PAGE}#53a2d31605f84299a99118add45e2af7",
    "CANON:OUTPUT-CONTRACT-001": f"{CANON_PAGE}#39a938befc428110a5effba7515cd721",
    "CANON:OUTPUT-CONTRACT-002": f"{CANON_PAGE}#39a938befc42817f90ace83dd96245a9",
    "CANON:OUTPUT-CONTRACT-003": f"{CANON_PAGE}#39a938befc4281dbac5ae5ae1adf1e90",
    "CANON:OUTPUT-CONTRACT-004": f"{CANON_PAGE}#39a938befc428128b20dc6192e8b8757",
    "CANON:EXPERIENCE-C01": f"{CANON_PAGE}#39a938befc4281889f7dc00f42b0302e",
    "CANON:EXPERIENCE-C02": f"{CANON_PAGE}#39a938befc42812d9187c6abcaf3a055",
    "CANON:EXPERIENCE-C03": f"{CANON_PAGE}#39a938befc4281fcba33c04d786f23a3",
    "CANON:EXPERIENCE-C04": f"{CANON_PAGE}#39a938befc4281399448deae8e03feb5",
    "CANON:EXPERIENCE-C05": f"{CANON_PAGE}#39a938befc428101b9ddc74fb51e9670",
    "CANON:KPI-001": f"{CANON_PAGE}#39a938befc428165b116c5ab225704d3",
    "CANON:KPI-002": f"{CANON_PAGE}#39a938befc4281cc825bcc7ffc944861",
    "CANON:KPI-003": f"{CANON_PAGE}#39a938befc42813d9182d8fbf4f7ac9c",
    "CANON:KPI-004": f"{CANON_PAGE}#d4df9b4fce484b35851e89379b6cc894",
    "CANON:KPI-005": f"{CANON_PAGE}#39a938befc42813fae1bf4d652b4e383",
    "CANON:KPI-006": f"{CANON_PAGE}#39a938befc4281e6b3d3d54cc2c2d897",
    "CANON:KPI-007": f"{CANON_PAGE}#39a938befc4281c0a644ed06936cfa65",
    "CANON:KPI-008": f"{CANON_PAGE}#39a938befc4281ccbd9fea7f671a13d5",
    "CANON:FACT-001": f"{CANON_PAGE}#39a938befc428176b5b4ffc5eb62a1c2",
    "CANON:FACT-002": f"{CANON_PAGE}#39a938befc4281dfaf84f85ecf2fadcd",
    "CANON:FACT-003": f"{CANON_PAGE}#39a938befc42814b8fe5f13720f74a47",
    "CANON:FACT-004": f"{CANON_PAGE}#39a938befc428154845ae643f7ac5c13",
    "CANON:FACT-005": f"{CANON_PAGE}#39a938befc4281ca90e1d03e6762a5ac",
    "CANON:FACT-006": f"{CANON_PAGE}#39a938befc4281b2b404da20a44a09f0",
    "CANON:FACT-007": f"{CANON_PAGE}#39a938befc4281628a9efef46fa846c7",
    "CANON:FACT-008": f"{CANON_PAGE}#39a938befc4281808eefd25dfebc5329",
    "CANON:UF-001": f"{CANON_PAGE}#39a938befc4281368c51f280d549e751",
    "CANON:UF-002": f"{CANON_PAGE}#39a938befc428105a250f82d9c348a9a",
    "CANON:UF-003": f"{CANON_PAGE}#39a938befc42810cbb59cbecda3daa92",
    "CANON:POSITIONING-N1": f"{CANON_PAGE}#39a938befc4281b39765c122a5d6378d",
    "CANON:POSITIONING-N2": f"{CANON_PAGE}#39a938befc4281049bb9ea0791d90b0e",
    "CANON:POSITIONING-N3": f"{CANON_PAGE}#39a938befc42819d9a64db7ddab1e776",
    "CANON:POSITIONING-N4": f"{CANON_PAGE}#39a938befc428110b8f1cb5aa81bb921",

    # --- ALIASES ---
    # Aliases §8 (Dedup & Oportunidades) no tenía ID previo. Nuevo ID
    # asignado (DRY RUN migración headings, aprobado 2026-07-25).
    # Anchor pendiente hasta escribir el heading nuevo en Notion.
    "ALIASES:DEDUP": f"https://app.notion.com/p/37c938befc4280d4b9aef5969830331b#PENDIENTE_ANCHOR_HEADING_NUEVO",
}

EXCLUDE_IDS = {
    "KERNEL:BOOTSTRAP-001",
    "KERNEL:PATCH-QUALITY-001",
    "CANON:ARCHIVO-VANTAGE",
    "CANON:EXPERIENCE-C01", "CANON:EXPERIENCE-C02", "CANON:EXPERIENCE-C03",
    "CANON:EXPERIENCE-C04", "CANON:EXPERIENCE-C05",
    "CANON:KPI-001", "CANON:KPI-002", "CANON:KPI-003", "CANON:KPI-004",
    "CANON:KPI-005", "CANON:KPI-006", "CANON:KPI-007", "CANON:KPI-008",
    "CANON:FACT-001", "CANON:FACT-002", "CANON:FACT-003", "CANON:FACT-004",
    "CANON:FACT-005", "CANON:FACT-006", "CANON:FACT-007", "CANON:FACT-008",
    "CANON:UF-001", "CANON:UF-002", "CANON:UF-003",
}

TARGET_FILES = {"Kernel.md", "Manual.md", "System Prompt.md", "Career Canon.md"}


# ─── Conversión de línea: REF -> hipervínculo ────────────────────────────────

def already_linked(line: str, start: int, end: int) -> bool:
    """True si el ID en line[start:end] ya está dentro de un [texto](url)."""
    after = line[end:end + 2]
    before_bracket = line.rfind('[', 0, start)
    if before_bracket != -1:
        between = line[before_bracket + 1:start]
        import re as _re
        if _re.fullmatch(r'`?', between) and after.startswith(']'):
            close = line.find(')', end)
            open_paren = line.find('(', end)
            if open_paren != -1 and open_paren < close:
                return True
    return False


def convert_line(line: str) -> tuple:
    """
    Convierte todas las ocurrencias REF de IDs mapeados en `line` a
    hipervínculos Markdown. Devuelve (nueva_linea, cambios: list[str]).

    Regla permanente confirmada por el operador: NINGUNA línea de heading
    se toca, ni siquiera cuando menciona de pasada un ID que no es su
    propio DEF. Los headings quedan siempre como texto plano; solo la
    prosa del cuerpo (incluyendo filas de TOC, que son tablas de cuerpo)
    se convierte.
    """
    if rules.HEADING_RE.match(line):
        return line, []

    def_ids_here = _line_ids_that_are_def(line)
    changes = []

    def repl(m):
        id_found = m.group(1)
        start, end = m.span(1)
        if id_found in def_ids_here:
            return m.group(0)
        if id_found in EXCLUDE_IDS:
            return m.group(0)
        url = MAPPING.get(id_found)
        if not url:
            return m.group(0)
        if already_linked(line, start, end):
            return m.group(0)
        changes.append(id_found)
        pre = line[max(0, start - 1):start]
        post = line[end:end + 1]
        if pre == '`' and post == '`':
            return f'[`{id_found}`]({url})'
        return f'[{id_found}]({url})'

    new_line = rules.ID_PATTERN.sub(repl, line)
    return new_line, changes


def _line_ids_that_are_def(line: str) -> set:
    """Devuelve el set de IDs que, EN ESTA LÍNEA, cuentan como DEF (heading
    o standalone-id-line) y por tanto NO deben auto-enlazarse."""
    defs = set()
    standalone = rules.line_is_standalone_id(line)
    if standalone:
        defs.add(standalone)
        return defs
    heading_match = rules.HEADING_RE.match(line)
    if heading_match:
        heading_text = heading_match.group(2)
        for m in rules.ID_PATTERN.finditer(heading_text):
            if rules.heading_looks_like_def(heading_text, m.group(1)):
                defs.add(m.group(1))
    return defs


# ─── Runner ──────────────────────────────────────────────────────────────────

def process_file(path: Path):
    original = path.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)
    new_lines = []
    total_changes = []
    in_fence = False
    for line in lines:
        if rules.is_fence_line(line):
            new_lines.append(line)
            in_fence = not in_fence
            continue
        if in_fence:
            new_lines.append(line)
            continue
        new_line, changes = convert_line(line)
        new_lines.append(new_line)
        total_changes.extend(changes)
    new_content = "".join(new_lines)
    return original, new_content, total_changes


def main():
    parser = argparse.ArgumentParser(
        description="Convierte referencias cruzadas de IDs VANTAGE a hipervínculos."
    )
    parser.add_argument("--root", required=True, type=Path,
                         help="Ruta raíz con los .md (ej. Documentación/ACTIVE).")
    parser.add_argument("--apply", action="store_true",
                         help="Escribe los cambios. Sin esta flag: solo DRY RUN.")
    parser.add_argument("--diff-out", default=Path("/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/data/dry_run_hyperlinks.diff"), type=Path,
                         help="Archivo donde guardar el diff del DRY RUN.")
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.exists():
        print(f"[ERROR] Ruta no existe: {root}", file=sys.stderr)
        sys.exit(1)

    diff_chunks = []
    grand_total = 0
    per_file_counts = {}

    for fname in sorted(TARGET_FILES):
        path = root / fname
        if not path.exists():
            print(f"[AVISO] No encontrado, se omite: {path}")
            continue
        original, new_content, changes = process_file(path)
        per_file_counts[fname] = len(changes)
        grand_total += len(changes)

        if original != new_content:
            diff = difflib.unified_diff(
                original.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{fname}", tofile=f"b/{fname}",
            )
            diff_chunks.append("".join(diff))

        if args.apply and original != new_content:
            path.write_text(new_content, encoding="utf-8")

    diff_text = "\n".join(diff_chunks)
    args.diff_out.write_text(diff_text, encoding="utf-8")

    print("\n--- RESUMEN ---")
    mode = "APLICADO (escritura real)" if args.apply else "DRY RUN (nada escrito)"
    print(f"Modo: {mode}")
    for fname, count in sorted(per_file_counts.items()):
        print(f"  {fname:20s} : {count} hipervínculos {'aplicados' if args.apply else 'propuestos'}")
    print(f"Total: {grand_total}")
    print(f"IDs excluidos de esta corrida: {len(EXCLUDE_IDS)} (ver EXCLUDE_IDS en el script)")
    print(f"Diff guardado en: {args.diff_out.resolve()}")
    if not args.apply:
        print("\nRevisa el diff. Si se ve correcto, vuelve a correr con --apply.")


if __name__ == "__main__":
    main()
