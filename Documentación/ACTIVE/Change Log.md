# V | CHANGELOG

Tipo: [DATA] [AUDIT]
Alcance: VANTAGE TRACKER (5 páginas: Oniverse, Milano Operadora, Ikea, Confidencial/placeholder, Dior); alias_map.json (local).
Contexto: Cierre de tareas C-003 a C-006 del plan B.md (Devin/Claude), verificadas contra datos vivos del Tracker (35 registros, CSV export + Notion MCP) en vez de asumir el plan original sin verificar. Se detectaron y corrigieron discrepancias entre B.md y el estado real: (1) C-004 asumía que fila 3 y fila 10 del Tracker compartían hash — falso; el duplicado real de fila 3 ya estaba archivado en ARCHIVO TRACKER (39a938befc428102a26ecbc0fe20917c, Archivar=true), por lo que C-004 no requirió escritura. (2) C-003 asumía 4 alias sin resolver — en Notion vivo, Milano Operadora e Ikea ya tenían Marca canónica, solo faltaba limpiar Notas; solo Oniverse requirió write real de Marca. (3) C-006 asumía 17 registros — el Tracker vivo tiene 35.
Cambios:
- alias_map.json (local) — altas: oniverse→Intimissimi, milano operadora→Milano Operadora, ikano retail→Ikea. "Importante empresa del sector" excluido (placeholder genérico, resolución manual).
- Tracker — página Oniverse (3b6938befc42818e9ba8c68dbd300b0b): Marca→Intimissimi, Notas actualizadas.
- Tracker — página Milano Operadora (3b6938befc4281b3a827d1acbf6b983c): Notas actualizadas (Marca ya canónica).
- Tracker — página Ikea (3b6938befc4281619c75d37456a9f79f): Notas actualizadas (Marca ya canónica).
- Tracker — página Confidencial/placeholder (3b6938befc4281f3b054f5785e989fa9): Notas documentando decisión de no-alta.
- Tracker — página Dior (38d938befc42818f8447f0da5369c40b): Notas documentando decisión de mantener URL de búsqueda (C-005, opcional, no ejecutada re-captura).
- C-006: auditoría de 35 registros vs. KERNEL:GATE-DECISION-011 (bandas de Score × Gate_Decision) — 35/35 coherentes, 0 excepciones estructurales. Sin escritura asociada (solo lectura).
IDs afectados: ninguno nuevo. Census no requiere regeneración.
Write-Back Verification: las 5 páginas de Tracker re-consultadas vía query_data_sources post-escritura — Marca/Notas confirmadas en los 5 casos, sin mismatch.
Pendiente (fuera de esta entrada): 2 posibles duplicados no marcados sin resolver (CONFIDENCIAL/Gerente Nacional vs. Confidencial/Gerente; Ikano-Retail vs. Ikea) — requieren decisión del operador; verificación de precedencia Next_Action=Optimizar vs JD_Quality no confirmada por falta de esa columna en la query de auditoría.
Versión actualizada: 9.19.3 (CHANGELOG). Resto de fundacionales permanece en v9.19.2 hasta vversions --sync.
---
Tipo: [DOC]
Alcance: Kernel (KERNEL:GATE-DECISION-003 09.3, KERNEL:GATE-DECISION-010 09.10 Referencias, KERNEL:OWNERSHIP-002 05.2).
Contexto: Cierre del pendiente D-002 dejado abierto en v9.19.1. Verificación línea por línea contra dashboard_notion.py confirmó que class_b_guard.guard_write_payload() está integrado en write_patch_to_notion() como guard previo a client.pages.update(), fail-closed (CLASS_B_BLOCKED) ante campos Class B o desconocidos (strict_unknown=True). Esto cierra GAP-03, documentado desde antes como mitigación interina (whitelist en DRY RUN) sin guard real equivalente al de feed_processor.py.
Cambios:
- KERNEL:GATE-DECISION-003 (09.3) — GAP-03 marcado CERRADO, reemplaza la mención de mitigación interina por la descripción del guard real confirmado.
- KERNEL:GATE-DECISION-010 (09.10, bloque Referencias) — extendida la referencia a dashboard_notion.py para mencionar el guard D-002.
- KERNEL:OWNERSHIP-002 (05.2) — nota añadida sobre la aplicación técnica del invariante "Python recalcula Class B" en la vía RT-1/Dashboard.
IDs afectados: ninguno nuevo — extensión de contenido bajo IDs existentes. Census no requiere regeneración.
Write-Back Verification: Kernel re-fetched tras escritura — los tres bloques confirmados en posición correcta, sin mismatch.
Pendiente (fuera de esta entrada): vversions --sync para propagar v9.19.2 al resto de los fundacionales.
Versión actualizada: 9.19.2 (CHANGELOG). Resto de fundacionales permanece en v9.19.1 hasta vversions --sync.
---
Tipo: [FIX] [CODE]
Alcance: Layer_1/scripts/gate_logic.py (D-001, D-004); Layer_1/scripts/profile_fit.py (D-003); Kernel (KERNEL:GATE-DECISION-010).
Contexto: Implementación coordinada Devin de tres fixes puntuales sobre gate_logic.py y profile_fit.py, verificados por dry-run del pipeline sin cambios lógicos a datos existentes (solo protección/observabilidad). D-002 (class_b_guard como middleware MCP) queda fuera de esta entrada — estado sin confirmar, pendiente de verificación en sesión futura.
Cambios:
- gate_logic.py — D-001: agregado "Expirada": "EXPIRADA" a STATUS_TERMINAL_MAP, alineando protección de terminalidad por Status con KERNEL:GATE-DECISION-010 (antes solo protegida indirectamente vía Next_Action=Expirada en TERMINAL_ACTIONS).
- gate_logic.py — D-004: agregado logging explícito de protección de terminales para observabilidad.
- profile_fit.py — D-003: agregado "Postulando" a _PROTECTED_STATUSES.
- KERNEL:GATE-DECISION-010 (09.10) — Criterio 1 actualizado documentando el fix D-001.
IDs afectados: ninguno nuevo — extensión/corrección de contenido bajo KERNEL:GATE-DECISION-010 ya existente. Census no requiere regeneración.
Write-Back Verification: gate_logic.py y profile_fit.py verificados línea por línea contra el código fuente subido (comentarios # D-001 FIX, # D-003 FIX, # D-004 FIX confirmados). Kernel re-fetched tras escritura — 09.10 Criterio 1 confirmado, referencias cruzadas (GATE-DECISION-005, -006, -008) intactas.
Pendiente (fuera de esta entrada): confirmar estado de D-002 (class_b_guard middleware MCP); C-002 posible duplicado (ya cubierto v9.14.5); C-003 a C-006 sin verificar con evidencia de código/tracker.
Versión actualizada: 9.19.1 (CHANGELOG). Resto de fundacionales permanece en v9.18.0 hasta vversions --sync.
Observaciones del dry-run:
1. Logging de terminales (D-004) funcionando:
- 10 registros con Status=Expirada muestran logging correcto:
```plain text

[gate_logic] PROTECTED: unknown → EXPIRADA (Status=Expirada, Next_Action=Archivar)
```
1. Cambios de prioridad (Fase 3.6):
- 6 cambios por sin_fecha_creacion (comportamiento esperado)
- Ejemplo: Confidencial/Zara/Bershka cambiando de BAJO→MEDIO/ALTO
1. Gate updates:
- 38 actualizaciones de Last_Gate_Run (timestamp normal de última ejecución)
1. Estado estable:
- "ESTADO ESTABLE: Sin cambios necesarios"
- D-001 a D-004 no introducen cambios lógicos a los datos, solo protección/observabilidad
RESUMEN FINAL v8.0:
URL Gate: 0 links muertos eliminados
JD Bypass: 2 vacantes con JD existente
READY-TO-APPLY (>=60): 11
CREATE (Pipeline Activo): 11
REVIEW_NEEDED (Score 40-59): 24
APPLIED (En proceso): 0
REJECTED: 0
BLOCKED: 0
PROTEGIDAS: 0
Total procesado: 45
ESTADO ESTABLE: Sin cambios necesarios
---
Tipo: [FIX] [INFRA]
Contexto: Auditoría de conformidad/drift de VANTAGE (sesión arena.ia + Claude, 2026-08-10, GitHub Issue #2, H2) detectó que Fase 3 (Scoring) y Fase 3.6 (Prioridad) iteraban sobre TODAS las filas sin filtrar terminales, violando KERNEL:GATE-DECISION-010 ("un registro terminal no puede ser sobreescrito por recálculo de Score/Gate"). Solo Fase 4 estaba protegida vía gate_logic(). Adicionalmente, la transición APPLIED→REJECTED (GATE-DECISION-011 fila 11) era código muerto porque gate_logic() retornaba "REJECTED" y el código hacía continue antes de llegar a evaluate_rejection_status().
Cambios:
- layer_1_run.py:743-770 — Fase 3 (Scoring): agregado filtro gate_logic() para skip registros terminales antes de recalcular Score.
- layer_1_run.py:917-945 — Fase 3.6 (Prioridad): agregado filtro gate_logic() para skip registros terminales antes de recalcular Prioridad.
- layer_1_run.py:999-1012 — Fase 4 (Gate): modificado gate_logic() continue para permitir que Status="Rechazado" continue y active evaluate_rejection_status() → REJECTED+Post-Mortem (transición APPLIED→REJECTED).
- test_gate_logic.py — agregada clase TestTerminalProtectionScoring con 4 tests de protección de terminales contra recálculo de Score/Prioridad.
IDs afectados: Tracker 596938befc42836baea7814a1491bd47 — 0 filas Postulado+CREATE residual (no presentes en dataset actual; fix previene futuros casos).
Write-Back Verification: Tests pasando (45/45), protección de terminales extendida a Fase 3/3.6, transición REJECTED+Post-Mortem ahora ejecutable.
Pendiente: avisar en GitHub Issue #2; actualizar Task Tracker (3b8938be-fc42-8166-81c9-ef9002012fac) con Status→Hecho y solución documentada.
Versión actualizada: 9.19.0 (CHANGELOG). Resto de fundacionales permanece en v9.18.0 hasta vversions --sync.
---
Tipo: [FIX] [INFRA]
Contexto: Auditoría de conformidad/drift de VANTAGE (sesión arena.ia + Claude, 2026-08-10, GitHub Issue #1, H1) detectó que gate() decidía solo por fetch + VM_Scope + Role_Class y nunca leía Score, violando el contrato del Kernel que define bandas: ≥60 CREATE · 40-59 Para Revisar · <40 BLOCKED. Evidencia: 31/36 filas CREATE con Score<60 en snapshot, mientras Manual/Checklist filtraban por Score≥60.
Cambios:
- layer_1_run.py:457-483 — gate() implementado con umbral de Score: score≥60 → CREATE, score≥40 → REVIEW_NEEDED, score<40 → BLOCKED. Score=None → REVIEW_NEEDED (golden rule: no pérdida silenciosa por dato faltante).
- test_gate_logic.py — actualizado para reflejar contrato actual de gate_logic() (solo protección de terminales) + 9 tests nuevos de Score Band (TestGateScoreBand).
- Manual.md — actualizado para incluir banda REVIEW_NEEDED (Score 40-59) y BLOCKED (Score<40).
- Checklist.html — actualizado para mencionar vista REVIEW_NEEDED en flujo de trabajo.
IDs afectados: Tracker 596938befc42836baea7814a1491bd47 — 9 filas cambiadas de CREATE→REVIEW_NEEDED (Score 40-50), 8 filas permanecen CREATE (Score≥60). Ready-to-Apply (≥60): 8 filas, alineado con contrato.
Write-Back Verification: Tests pasando (41/41), dry-run confirmado, aplicación exitosa al Tracker vivo.
Pendiente: avisar en GitHub Issue #1; actualizar Task Tracker (3b8938be-fc42-8130-b47a-f0150c2502cd) con Status→Hecho y solución documentada.
Versión actualizada: 9.18.0 (CHANGELOG). Resto de fundacionales permanece en v9.17.1 hasta vversions --sync.
---
Tipo: [DOC] [FIX]
Alcance: Kernel (KERNEL:GATE-DECISION-011).
Contexto: Auditoria de conformidad/drift de VANTAGE (sesion arena.ia + Claude, 2026-08-10, GitHub Issue #2, H3) detecto que KERNEL:GATE-DECISION-011 fila 4 documentaba un mecanismo de dedup inexistente en codigo ni schema (Gate_Decision=REJECTED_DUPLICATE, Dedup_Flag=True, Next_Action=Descartar). El mecanismo real (feed_processor.py) escribe Status=REVIEW_NEEDED sobre el registro entrante y Dedup_Flag='Posible duplicado' sobre el registro existente. En paralelo se investigo la causa raiz de 7 registros "Visual Merchandising Coordinator" (Score=50) reportados como no colapsados por la ventana de 30 dias: la mayoria resultaron falsos positivos (vacantes reales de empleadores distintos con titulo generico coincidente); el unico caso real de dedup fallido (par YELLO Marketing Group, hash identico 89a50e5e1978ec...) se debio a que NotionSchema.load() (feed_processor.py:319) limita el scope de dedup_cross_layer()/dedup_by_content_fingerprint() al VANTAGE TRACKER activo, sin visibilidad sobre ARCHIVO TRACKER.
Cambios:
- KERNEL:GATE-DECISION-011 (09.11) — fila 4 corregida: elimina referencia a REJECTED_DUPLICATE/Dedup_Flag=True/Next_Action=Descartar; documenta el mecanismo real (Status=REVIEW_NEEDED, Dedup_Flag='Posible duplicado').
IDs afectados: ninguno nuevo — correccion de contenido bajo KERNEL:GATE-DECISION-011 ya existente. Census no requiere regeneracion.
Write-Back Verification: Kernel re-fetched tras escritura — fila 4 confirmada en posicion correcta, sin mismatch.
Pendiente (fuera de esta entrada): Bug Tracker — nuevo ticket 3b8938be-fc42-8100-aa85-cbfe3c3e27f6 (dedup no cubre Archivo Tracker, 3 ALTO, [CENSUS-SYNC-R1]); vversions --sync para propagar v9.17.2 al resto de los fundacionales. GitHub: cerrado issue #2 con comentario de resolucion; corregido cierre erroneo de issue #3 (H1, permanece abierto — no relacionado con H3).
Version actualizada: 9.17.2 (CHANGELOG). Resto de fundacionales permanece en v9.17.1 hasta vversions --sync.
---
Tipo: [DOC] [FIX]
Alcance: Kernel (KERNEL:GATE-DECISION-007).
Contexto: Auditoria de conformidad/drift de VANTAGE (sesion arena.ia + Claude, 2026-08-10, GitHub Issue #4, H4) detecto que KERNEL:GATE-DECISION-007 documentaba archivado automatico via auto_archive.py como regla vigente, mientras el script vive deprecado en Archive/Legacy_Scripts/auto_archive.py desde la decision del operador (2026-08-01, documentada en la skill vantage-tidy-opportunities-tracker) de abandonar ese enfoque por marcado manual. El Bug Tracker tenia un ticket abierto ("Dedup Caso 5 — Next_Action=Archivar no se ejecuta automaticamente") como consecuencia directa de este drift documental. Es drift puramente documental — no requirio cambio de codigo.
Cambios:
- KERNEL:GATE-DECISION-007 (09.7) — retitulado de "Ejecucion Automatica de Archivado" a "Marcado Manual de Archivado". Reemplazada la referencia a auto_archive.py como mecanismo activo por la descripcion del flujo vigente: la skill vantage-tidy-opportunities-tracker marca Archivar = True tras DRY RUN + APROBAR_WRITE, sin mover ni copiar paginas; el operador archiva manualmente. Documentada explicitamente la decision del operador (2026-08-01) y la razon (friccion, costo de tokens, desalineacion de esquema con el Archivo Tracker).
IDs afectados: ninguno nuevo — extension/correccion de contenido bajo KERNEL:GATE-DECISION-007 ya existente. Census no requiere regeneracion.
Write-Back Verification: Kernel re-fetched tras escritura — bloque 09.7 confirmado en posicion correcta, sin mismatch.
Pendiente (fuera de esta entrada): re-etiquetar/cerrar ticket "Dedup Caso 5..." en Bug Tracker; decidir eliminacion o conservacion como referencia de auto_archive.py en el repo; avisar en GitHub Issue #4; vversions --sync para propagar v9.17.1 al resto de los fundacionales.
Version actualizada: 9.17.1 (CHANGELOG). Resto de fundacionales permanece en v9.16.0 hasta vversions --sync.
---
Contexto: post-mortem de batch de 13 CV-B procesados en una sola sesión continua — densidad narrativa (perfil/bullets) muy por debajo del estándar de referencia (Zegna), pese a que el Anti-cloning Guard (v9.16.0) eliminó correctamente la duplicación verbatim entre vacantes. Comparación directa contra 6 CV-B generados individualmente (uno por sesión) en el mismo periodo confirmó densidad consistentemente alta sin regla numérica adicional — la causa raíz es degradación de esfuerzo del AI Component bajo procesamiento secuencial de lote, no un gap de contrato documental.
Cambios:
- KERNEL:12.2 — Restricción de Lote (Single-Item Processing): CV-B procesa exactamente UN HANDOFF por invocación; ante un batch, procesa el primero y se detiene a esperar invocación explícita para el siguiente.
- vantage-cv-b.md — mismo guard insertado como restricción operativa previa al Anti-cloning Guard.
IDs afectados: ninguno nuevo — extensión de contenido bajo KERNEL:CV-PIPELINE-002 ya existente. Census no requiere regeneración.
Write-Back Verification: pendiente de re-fetch en este mismo batch.
Versión actualizada: 9.17.0 (CHANGELOG). Resto de fundacionales permanece en v9.16.0 hasta vversions --sync.
---
Contexto: drift detectado en batch de 16 CV-B (mismo Positioning Mode reutilizando
bullets pre-redactados verbatim entre vacantes distintas) + defecto mecánico de
viñetas dobles ("• •") en serialización Figma.
Cambios:
- KERNEL:12.2 — prohibición explícita de reutilizar bullets pre-redactados
verbatim entre vacantes, incluso dentro del mismo Positioning Mode.
- CANON:12.1 — alta de Regla #5, Distinctiveness Rule (Figma Sync Protocol).
- vantage-cv-b.md — Anti-cloning Guard como paso de verificación previo a entrega.
- vantage-qa.md — Ítem #7 del checklist: Diferenciación de Contenido, FAIL
automático si match verbatim >80% en Experience frente a otro entregable del
mismo batch.
- MANUAL:08.3 — advertencia operativa de riesgo Batch-Cloning en el flujo de
inyección Figma.
- Regeneración operativa: 16 CV-B del batch (17 HANDOFFs − 1 duplicado de
contenido) reconstruidos con bullets diferenciados por HANDOFF activo y sin
viñetas dobles.
---
Tipo: [INFRA] [DOC]
Cambios:
- Kernel: Subsección 007.3 integrada en KERNEL:DOCUMENTATION-007 (mecanismo, umbrales 5%/10 líneas, baseline).
- Manual: Subsección HC-03 en MANUAL:HEALTHCHECK (procedimiento de salud de documentos).
- Aliases: Extensión de ALIASES:L4-VERSION-CONTROL con flags --length y --update-baseline.
- System Prompt: Subsección 11.3 en SP:VERSION-CHECK-TOOL (guardarraíl operativo para la IA).
- Navigation Brief: Dependencia LENGTH-BASELINE añadida en CROSS-DEPENDENCIES-001 y matriz de autoridad actualizada.
Notas: Backward Compatibility — las operaciones existentes (--sync, --bootstrap) no se ven afectadas. Requisitos — length_baseline.json se genera automáticamente en la primera ejecución de --length.
Versión actualizada: 9.15.1 (CHANGELOG) · 2026-08-08.
---
> El histórico completo del CHANGELOG lo podrás encontrar en ARCHIVO CHANGELOG, en esta pagina de consulta continua solo encontrarás las últimas diez entradas para garantizar la operación y referencia del sistema.
