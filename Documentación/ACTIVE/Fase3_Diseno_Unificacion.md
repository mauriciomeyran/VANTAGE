# DISEÑO — Fase 3: Unificación de Terminalidad y Hard Blocks
# ============================================================
# Versión de entrega: 2026-09-15
# Este documento describe lo que realmente se implementó en el patch
# Fase3_Theme (Layer_1/scripts/). No es un borrador ni una propuesta —
# el código ya fue entregado y este documento lo refleja, no al revés.
#
# Estado de entrega del patch:
#   - 2 archivos creados: vantage_status.py, hard_block_gate.py
#   - 4 archivos modificados: gate_logic.py, profile_fit.py,
#     dedup_opportunities.py, feed_processor.py
#   - El diff Fase3_Final_Patch.patch aplica limpio sobre origin/main.
#
# Fuentes de verdad del vocabulario de Status (ítem 1):
#   - tracker_flow.py (Status enum, TERMINAL_STATUSES, PROTECTED_STATUSES,
#     LIVE_APPLICATION_STATUSES) — fuente canónica delegada por todos los
#     módulos modificados.
#   - hard_blocks.json (Layer_1/config/) — fuente única de empleadores
#     bloqueados (ítem 2), consumida por hard_block_gate.py.
#
# ============================================================
# 2.2 — Hard Block Gate: Opción B (implementada)
# ============================================================
# El diseño original contemplaba dos opciones:
#   Opción A: hard_block_gate.py importara src/validator.py
#             (company_is_blocked()) y delegara la validación.
#   Opción B: hard_block_gate.py nuevo, standalone, leyendo
#             hard_blocks.json directamente, con sus propios regex/matching,
#             sin depender de src/ ni de pydantic.
#
# Lo entregado es la Opción B, confirmada por el operador antes del patch
# por las siguientes razones:
#   1. src/ (VANTAGE Scout) queda fuera de alcance de Fase 3 — código no
#      productivo. No se toca src/validator.py, src/gate_logic.py, ni
#      src/dedup.py. Solo se anota en una línea, sin sección de "alcance
#      pendiente" sobre Scout.
#   2. company_is_blocked() vive en src/validator.py, que es parte del
#      subsistema excluido. No se puede usar como base ni reutilizar.
#   3. hard_block_gate.py (Opción B) lee hard_blocks.json (fuente única
#      declarada) y verifica con sus propios regex los términos base más las
#      variantes confirmadas en datos reales del Archive Tracker:
#        - L'Oréal: l'oréal, l'oreal, loreal + divisiones/holdings + méxico
#        - Levi's: levi's, levis
#        - Dockers: dockers
#        - El Palacio de Hierro: palacio de hierro, el palacio de hierro
#      Los regex fueron verificados contra los patrones de
#      src/validator.py:BLOCKED_COMPANY_PATTERNS (sin reutilizar ese código)
#      para garantizar cobertura mínima de las variantes confirmadas.
#   4. La integración con feed_processor.py cierra el circuito donde el
#      hard block opera: process_record() evalúa blocked_employer_term()
#      antes de emitir Gate_Decision="CREATE", evitando que un empleador
#      bloqueado llegue a CREATE. Esto resuelve el hallazgo de 2 filas
#      de Levi's/Dockers con CREATE en producción (violation documentada,
#      no perseguida en este patch).
#
# D1 — Terminal actions (Next_Action="Expirada"):
#   Eliminado del código. 0 ocurrencias en producción (826 filas). La
#   protección real para Expirada ya existe vía Status="Expirada" en
#   vantage_status.TERMINAL_STATUSES_CANONICO + LEGACY_STATUS_MAP. Este
#   check era defensa sobre el campo equivocado.
#
# D2 — Retirado (89 registros):
#   Aunque tracker_flow.Status.RETIRADO está en TERMINAL_STATUSES y
#   PROTECTED_STATUSES, STATUS_TERMINAL_MAP de gate_logic.py no lo
#   incluía. La versión unificada de vantage_status.gate_protected_value()
#   si lo incluye (delegando a TERMINAL_STATUSES), cerrando el gap.
#
# D3 — Legacy sin mapeo (Repetida, Target):
#   Ambos quedan None en LEGACY_STATUS_MAP y se flaggean explícitamente
#   como "legacy sin mapeo, requiere revisión humana" cuando aparecen.
#   No se inventa semántica. Normalización lazy (en memoria), sin escritura
#   a Notion.
