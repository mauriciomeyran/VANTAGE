# V | CHANGELOG

---
Tipo: [FIX] [INFRA]
Título: H2 — Protección de terminalidad extendida a Score/Prioridad (KERNEL:GATE-DECISION-010 / GATE-DECISION-006)
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
---
Tipo: [FIX] [INFRA]
Título: H1 — Implementación de umbral de Score en gate() (KERNEL:GATE-DECISION-002 / GATE-DECISION-011)
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
Tipo: [INFRA] [DOC]
Título: Implementación de banderas --length y --update-baseline para detección de truncamiento silencioso.
Resumen de cambios:
- Kernel: Subsección 007.3 integrada en KERNEL:DOCUMENTATION-007 (mecanismo, umbrales 5%/10 líneas, baseline).
- Manual: Subsección HC-03 en MANUAL:HEALTHCHECK (procedimiento de salud de documentos).
- Aliases: Extensión de ALIASES:L4-VERSION-CONTROL con flags --length y --update-baseline.
- System Prompt: Subsección 11.3 en SP:VERSION-CHECK-TOOL (guardarraíl operativo para la IA).
- Navigation Brief: Dependencia LENGTH-BASELINE añadida en CROSS-DEPENDENCIES-001 y matriz de autoridad actualizada.
Notas:
- Backward Compatibility: Las operaciones existentes (--sync, --bootstrap) no se ven afectadas.
- Requisitos: length_baseline.json se genera automáticamente en la primera ejecución de --length.
---
### v9.15.0 — Ecosistema Figma Sync: Arquitectura + Diagnóstico (KERNEL:ARCHITECTURE-L4, MANUAL:FIGMA-SYNC-001..005/DIAGNOSTIC, CANON:OUTPUT-CONTRACT-003) · 2026-08-08
Tipo: [DOC] [ENRICHMENT]
Alcance: Kernel (KERNEL:ARCHITECTURE-L4); Manual (MANUAL:WEEKLY-FLOW-003 §8.3, MANUAL:GOLDEN-SKELETON-REF §20 retitulada + 5 altas 20.1–20.5, MANUAL:TROUBLESHOOTING §12 — bloque reemplazado por MANUAL:FIGMA-SYNC-DIAGNOSTIC); Career Canon (CANON:OUTPUT-CONTRACT-003).
Contexto: El plugin VANTAGE CV Sync (manifest.json/ui.html/code.js) operaba sin documentación de su arquitectura interna ni de sus modos de fallo — KERNEL:ARCHITECTURE-L4 solo tenía invariantes de alto nivel y MANUAL:TROUBLESHOOTING un bloque genérico sin distinguir causas. Insumo técnico: documento externo derivado de auditoría directa de los 3 archivos del plugin. Ejecutado bajo protocolo de documentación transversal completo (propuesta → implementación), con una ronda de rectificación: nivel de heading Markdown de las 5 subsecciones nuevas corregido a ### (subsección NN.N) por observación del operador contra la Matriz Tipográfica Congelada (KERNEL:DOCUMENTATION-001), y título de §20 evolucionado a "Figma Sync & Golden Skeleton" para reflejar el ecosistema ampliado.
Cambios:
- KERNEL:ARCHITECTURE-L4 — expandido el bloque "Figma Sync — CV Output Layer": arquitectura de 3 archivos (manifest.json/ui.html/code.js), comunicación vía postMessage, diagrama de flujo detallado (parsing + sanitización + resolución O(1)). Invariantes preexistentes conservadas, nueva referencia cruzada a MANUAL:FIGMA-SYNC-003.
- MANUAL:WEEKLY-FLOW-003 (8.3, Figma) — prosa técnica sustituida por referencia directa a MANUAL:FIGMA-SYNC-003 (§20) y MANUAL:FIGMA-SYNC-DIAGNOSTIC (§12); pasos operativos de uso semanal conservados.
- MANUAL:GOLDEN-SKELETON-REF (§20) — retitulada "Figma Sync & Golden Skeleton"; contenido original intacto. Alta de 5 IDs como subsecciones 20.1–20.5: MANUAL:FIGMA-SYNC-001 (Arquitectura del Ecosistema), 002 (Contrato de Bloque), 003 (Flujo de Inyección, 4 fases), 004 (Sanitización de Contenido), 005 (Regla de Reemplazo Total).
- MANUAL:TROUBLESHOOTING (§12) — bloque "Figma Plugin No Resuelve IDs" reemplazado por MANUAL:FIGMA-SYNC-DIAGNOSTIC (nuevo, 12.1): Matriz de Errores diferenciando Causa A (Registry desincronizado) de Causa B (nodo ausente en lienzo), checklist de 6 situaciones con diagnóstico y acción.
- CANON:OUTPUT-CONTRACT-003 — reforzada regla de resolución O(1) por ID de nodo (figma.getNodeById), explícito que renombrar capas no afecta la resolución.
IDs afectados: 6 altas (MANUAL:FIGMA-SYNC-001, -002, -003, -004, -005, -DIAGNOSTIC) — Census requiere regeneración (vcensus, pendiente, acción local del operador).
Write-Back Verification: Kernel, Manual y Career Canon re-fetched de forma independiente tras cada escritura — todos los bloques confirmados en posición correcta, sin mismatch. Nivel de heading de 20.1–20.5 confirmado como ### real (no code-fence) en el re-fetch post-inyección.
Pendiente (fuera de esta entrada): vcensus + vversions --sync para propagar v9.15.0 al resto de los fundacionales.
Versión actualizada: 9.15.0 (CHANGELOG). El resto de los fundacionales permanece en v9.14.9 hasta vversions --sync.
---
### v9.14.9 — Asignación de Ownership Class A a Positioning_Mode (KERNEL:SCHEMA-001, MANUAL:SCHEMA-FIELD-REF) · 2026-08-08
Tipo: [SCHEMA] [DOC]
Alcance: Kernel (KERNEL:SCHEMA-001); Manual (MANUAL:SCHEMA-FIELD-REF).
Contexto: Positioning_Mode ya operaba de facto como campo determinado por el AI Component en CV-A (Algoritmo de Selección N1–N4, KERNEL:CV-PIPELINE-001) y ya era referenciado en MANUAL:OBJECTIVE como campo de distribución del Tracker, pero carecía de ownership formal en la lista Class A/B — este batch cierra ese gap. Nota de alcance: la propuesta original incluía un tercer parche sobre SP:SCHEMA (Sección 08) que se detuvo en Fase 2 — esa sección no contiene un encabezado de schema para el Tracker de vacantes bajo el cual insertar la propiedad; queda pendiente de resolución con el operador antes de ejecutarse.
Cambios:
- KERNEL:SCHEMA-001 (07.1) — Positioning_Mode insertado en la lista Class A, entre Status y Prioridad.
- MANUAL:SCHEMA-FIELD-REF (21) — mismo campo insertado en la tabla índice, mismo orden.
IDs afectados: ninguno — extensión de contenido bajo IDs ya existentes. Census no requiere regeneración.
Write-Back Verification: Kernel y Manual re-fetched de forma independiente tras cada escritura.
Pendiente (fuera de esta entrada): resolución del Parche #2 (SP:SCHEMA — nodo "Tracker de vacantes" inexistente); vversions --sync para propagar v9.14.9 al resto de los fundacionales.
Versión actualizada: 9.14.9 (CHANGELOG). El resto de los fundacionales permanece en v9.14.8 hasta vversions --sync.
---
### v9.14.8 — Enriquecimiento Teórico de Positioning Modes N1–N4: Algoritmo, Contrato de Persistencia, Mitigación de Riesgos, Router Mental (KERNEL:CV-PIPELINE-001, CANON:POSITIONING-005, MANUAL:POSITIONING-CRITERIA, CANON:OUTPUT-CONTRACT-005) · 2026-08-08
Tipo: [DOC] [ENRICHMENT]
Alcance: Kernel (KERNEL:CV-PIPELINE-001, KERNEL:CV-PIPELINE-002); Career Canon (CANON:POSITIONING, CANON:POSITIONING-005 nuevo, CANON:OUTPUT-CONTRACT-005); Manual (MANUAL:WEEKLY-FLOW-003, MANUAL:POSITIONING-CRITERIA).
Contexto: El operador solicitó elevar el capítulo de Positioning Modes de "definición funcional" a "base teórica operativa", integrando un corpus de investigación externa (Perplexity) sobre la justificación algorítmica y arquitectónica de N1–N4. Durante Fase 1 se detectó que gran parte del mapeo original propuesto ya estaba cubierto por contenido vivo (matriz de anclas, regla de desempate, router JD-first) — el enriquecimiento real se limitó a gaps genuinos: el algoritmo determinista de selección, un contrato de trazabilidad de la decisión, la sección de mitigación de riesgos, y el volumen procedimental del Manual. Se detectó y corrigió en el mismo batch una discrepancia de conteo de campos del HANDOFF preexistente (Kernel citaba 5, Manual citaba 6 en dos lugares distintos) — unificado a 7 con la incorporación de positioning_rationale.
Cambios:
- KERNEL:CV-PIPELINE-001 (12.1) — inyectado Algoritmo de Selección N1–N4 (Keywords → Mapeo → Conteo → Desempate, con referencia cruzada a CANON:POSITIONING) y Contrato de Persistencia de la Decisión (campo positioning_rationale obligatorio en el HANDOFF). HANDOFF actualizado de 5 a 7 campos (JSON + prosa).
- KERNEL:CV-PIPELINE-002 (12.2) — "Verificar los 7 campos del HANDOFF" (antes 5).
- CANON:POSITIONING (11) — frase de apertura formalizando la sección como Matriz de Respaldo Estratégico.
- CANON:POSITIONING-005 (nuevo, 11.5) — alta de ID: sección Mitigación de Riesgos (Anti-overselling, Anti-fragmentación de identidad).
- CANON:OUTPUT-CONTRACT-005 (12.5) — vínculo explícito entre el Positioning Mode activo y el concepto de "preset narrativo" definido en KERNEL:CV-PIPELINE-001.
- MANUAL:WEEKLY-FLOW-003 (8.3, CV-A y CV-B) — HANDOFF actualizado a 7 campos (JSON + ambas menciones en prosa, incluyendo un mismatch de "6 campos" detectado en Write-Back que no estaba en el mapeo original).
- MANUAL:POSITIONING-CRITERIA (19) — tabla "Vista JD-first" expandida con columna Señales de Alarma (Red Flags) por modo; nuevo bloque Gestión de Ambigüedad — JDs Híbridos, detallando cómo redactar fit_gaps ante escalamiento a decisión humana.
IDs afectados: 1 alta (CANON:POSITIONING-005) — Census requiere regeneración (vcensus, pendiente, acción local del operador).
Write-Back Verification: Kernel, Manual y Career Canon re-fetched de forma independiente tras cada escritura — todos los bloques confirmados en posición correcta. Un mismatch adicional fuera del DRY RUN original (MANUAL:WEEKLY-FLOW-003, "6 campos" en sección CV-B) detectado y corregido en el mismo ciclo de verificación.
Pendiente (fuera de esta entrada): consolidación de referencias informales a "KERNEL:CENSUS-SYNC" (sin ancla propia en el corpus vivo — apuntan de facto a KERNEL:DOCUMENTATION-008) — no ejecutada por falta de fuente verificable; candidata a ticket separado en Task Tracker si el operador lo autoriza. vcensus + vversions --sync para propagar v9.14.8 al resto de los fundacionales.
Versión actualizada: 9.14.8 (CHANGELOG). El resto de los fundacionales permanece en v9.14.6 hasta vversions --sync.
---
---
### v9.14.7 — Weekly Prompt Assembler reemplaza Ensamblado vía Agente en Perplexity Desktop (KERNEL:ARCHITECTURE-L1-002, MANUAL:WEEKLY-FLOW-001, MANUAL:PROMPTS-WRAPPERS, ALIASES:L1L2-DISCOVERY) · 2026-08-08
Tipo: [DOC] [INFRA]
Alcance: Kernel (KERNEL:ARCHITECTURE-L1-002); Manual (MANUAL:WEEKLY-FLOW-001, MANUAL:PROMPTS-WRAPPERS §13); Aliases (ALIASES:L1L2-DISCOVERY).
Contexto: El operador introdujo weekly_prompt_assembler.py (verificado contra el archivo real, no solo el abstract) — reemplaza el mecanismo de ensamblado de prompts vía "Prompt D" (agente ejecutado dentro de Perplexity Desktop, documentado hasta v9.14.6) por materialización local en disco de los 7 prompts semanales. Durante la propuesta se detectó y resolvió una contradicción real: MANUAL:PROMPTS-WRAPPERS describía a Claude como quien hace fetch de cada componente vía MCP — ya no aplica, el script hace el fetch directo vía notion_utils.notion_get. fetch_notion_page() fue verificado por contenido de archivo (no self-report) tras hallarse inicialmente como stub (NotImplementedError) en una primera versión pegada por el operador.
Cambios:
- KERNEL:ARCHITECTURE-L1-002: nueva frase sobre Weekly Prompt Assembler (weekly_prompt_assembler.py, alias vassemble) como herramienta de soporte de L1, con referencia cruzada a ALIASES:L1L2-DISCOVERY.
- MANUAL:WEEKLY-FLOW-001 (8.1 Lunes): bloque completo del "Prompt D" (agente ensamblador) reemplazado por instrucción de ejecutar vassemble; subsecciones "¿Cómo inicio L1?" / "¿Cómo inicio L2?" reemplazadas por "¿Cómo uso los archivos generados?", consistente con la materialización en disco.
- MANUAL:PROMPTS-WRAPPERS (§13): corregido — el script hace el fetch, no Claude vía MCP.
- ALIASES:L1L2-DISCOVERY (Familia 03): alta de fila vassemble, con procedimiento interno confirmado contra el archivo real (notion_utils.notion_get, no NotImplementedError).
IDs afectados: ninguno nuevo — extensión/corrección de contenido bajo IDs ya existentes. Census no requiere regeneración.
Write-Back Verification: pendiente (siguiente paso de esta misma sesión — Fase 4 del protocolo).
Pendiente (fuera de esta entrada): vversions --sync para propagar v9.14.7 al resto de los fundacionales.
Versión actualizada: 9.14.7 (CHANGELOG). El resto de los fundacionales permanece en v9.14.6 hasta vversions --sync.
---
---
### v9.14.6 — Refuerzo de Gobernanza CV-A: CV-À SCOPE LOCK + Alta de Regla #6 (KERNEL:CV-GOLDEN-RULES-006) · 2026-08-08
Tipo: [DOC] [GOVERNANCE]
Alcance: Technical Kernel (KERNEL:OWNERSHIP-001, KERNEL:CV-GOLDEN-RULES-006); System Prompt (SP:CV-GOLDEN-RULES-REF); Manual (MANUAL:CV-GOLDEN-RULES-INDEX).
Contexto: Refuerzo de límites operativos para el AI Component durante la ejecución de Skills CV-A (CV-A, CV-B, QA, FAST). El objetivo es evitar que la IA re-evalúe, estime o modifique decisiones ya tomadas por Python o el operador, garantizando que su rol se limite a informar discrepancias en el campo "observaciones" del HANDOFF sin emitir verbos de decisión (ej. "bloquear", "pasa").
Cambios:
- KERNEL:OWNERSHIP-001: Añadido CV-À SCOPE LOCK como restricción explícita para el AI Component, prohibiendo evaluar fit estratégico o cuestionar Gate_Decision.
- SP:CV-GOLDEN-RULES-REF: Inyectada instrucción operativa CV-À SCOPE LOCK, detallando lo PROHIBIDO (estimar Gate_Decision, VM_Scope o campos Class B; usar verbos de decisión) y lo PERMITIDO (señalar discrepancias en "observaciones" del HANDOFF).
- KERNEL:CV-GOLDEN-RULES-006 (nuevo, 10.6): Alta de Regla #6 — Invarianza de la Decisión de Gate, prohibiendo que el AI Component re-evalúe fit, estime scores o aplique exclusiones sobre vacantes con Gate_Decision ya calculada.
- MANUAL:CV-GOLDEN-RULES-INDEX: Añadida fila para KERNEL:CV-GOLDEN-RULES-006, vinculando a la nueva regla.
IDs afectados: 1 alta (KERNEL:CV-GOLDEN-RULES-006).
Write-Back Verification: Kernel, System Prompt y Manual re-fetched tras escritura — 3 bloques confirmados en posición correcta.
Pendiente: vversions --sync para propagar v9.14.6 al resto de los fundacionales.
Versión actualizada: 9.14.6 (CHANGELOG). El resto de los fundacionales permanece en v9.14.5 hasta vversions --sync.
---
### v9.14.6 — Expansión de Next_Action: Inclusión de "Optimizar" · 2026-08-08
Tipo: [SCHEMA] [DOC]
Alcance: Technical Kernel (KERNEL:SCHEMA-008); Manual (MANUAL:SCHEMA-FIELD-REF); Change Log.
Contexto: Regularización post-ejecución parcial. Valor "Optimizar" (Class B Next_Action) se dispara cuando JD_Quality = "JD Completo", priorizando vacantes listas para CV-A.
Cambios ejecutados y verificados:
- KERNEL:SCHEMA-008: conteo (9)→(10); fila "Optimizar | JD_Quality = "JD Completo" (Prioridad de procesamiento)" insertada como primera fila de la tabla.
- MANUAL:SCHEMA-FIELD-REF: nota añadida bajo Class B — "Next_Action: select (10 valores operativos). Ver KERNEL:SCHEMA-008".
IDs afectados: ninguno nuevo (extensión de contenido bajo IDs existentes).
Write-Back Verification: Kernel y Manual re-fetched post-escritura — ambos bloques confirmados, mismatch=0.
Pendiente (operador / Terminal):
- layer_1_run.py Fase 4: condicional JD_Quality == "JD Completo" → next_action = "Optimizar".
- vcensus + vversions --sync.
- SP:SCHEMA y MANUAL:HOW-IT-WORKS (si se requiere armonización adicional).
Versión actualizada: 9.14.6 (CHANGELOG).
---
### v9.14.4a — Auditoria: Diagnostico Mutacion Post-vl3/vl1 (Rx Tracker) · 2026-08-07
Tipo: [AUDIT]
Alcance: VANTAGE TRACKER (442938be...) — solo lectura, sin escritura.
Contexto: El operador reporto que el Tracker "cambio totalmente" tras correr vl3 y luego vl1, sobre un CSV baseline de la noche anterior (20:58) con 15 registros ya triados para CV-A.
Hallazgos (diff por hash, baseline vs. estado post-vl3/vl1):
- Los 15 registros de la baseline siguen todos presentes (0 desaparecidos).
- vl1 agrego 7 registros nuevos (esperado).
- Optimizar/Postular/Interview/Archivar/Gate_Decision/Status/Next_Action: sin cambios en ninguno de los 15 — el triage manual de CV-A quedo intacto.
- Lo que si cambio: Score y Prioridad de varios registros (recalculo normal del pipeline, no corrupcion de datos).
Veredicto: falso positivo de "todo cambio" — el operador interpreto el recalculo esperado de Score/Prioridad como perdida de triage. Sin fix de codigo ni documentacion requerido; comportamiento del pipeline es el esperado.
IDs afectados: ninguno. Census no requiere regeneracion.
Version actualizada: sin bump (entrada retroactiva de auditoria, sin escritura asociada).
---
### v9.14.5 — Rediseño Matriz Next_Action + Fix Drift SCHEMA-008 (KERNEL:SCHEMA-008, KERNEL:GATE-DECISION-010/011, SP:SCHEMA, Notion Tracker) · 2026-08-08
Tipo: [SCHEMA] [DOC] [FIX]
Alcance: Notion (VANTAGE TRACKER, propiedad Next_Action); Kernel (KERNEL:SCHEMA-008, KERNEL:GATE-DECISION-010, KERNEL:GATE-DECISION-011, KERNEL:EVOLUTION); System Prompt (SP:SCHEMA); Bug Tracker (ticket nuevo).
Contexto: Continuación de una sesión Rx Tracker donde el operador reportó mutación masiva de estado tras correr vl3+vl1; diagnóstico confirmó que el triage previo estaba intacto (cambio real fue en Score/Prioridad, no en Gate/Next_Action). A partir de ahí se abrió un rediseno de la matriz Next_Action con el operador (9 preguntas respondidas directamente) para eliminar dos puntos de riesgo: el catch-all silencioso a Archivar, y Rechazado cayendo a Ninguna sin señal de que falta análisis manual (screenshot → Takeaways → Archivar=True). Durante el mapeo de nodos se detectó un drift documental preexistente por fetch directo del schema real de Notion: KERNEL:SCHEMA-008 documentaba rich_text (auditoría 2026-08-04, v9.13.11) mientras el campo real ya era select desde v9.14.2/v9.14.3 (auditoría 2026-08-06) — el contenido correcto había quedado huérfano y duplicado bajo KERNEL:EVOLUTION §17 en vez de reemplazar 07.8. Se corrigió en el mismo batch.
Cambios:
- Notion — VANTAGE TRACKER (442938be...), propiedad Next_Action (select): altas "Post-Mortem" y "Investigar"; "Ninguna" se conserva como opción legacy (no destructivo sobre registros históricos), ya no usada por código nuevo.
- KERNEL:SCHEMA-008 (07.8) — tipo corregido a select (v9.14.2); tabla reescrita a 9 valores: Rechazado→Post-Mortem (reemplaza Ninguna), default no-match→Investigar (reemplaza Archivar como catch-all), Inbound unifica Referencia/Networking→Re-check. Párrafo de "corrección de tipo" desactualizado reescrito con el historial real (v9.13.7 select → v9.13.11 error rich_text → v9.14.2/3 migración confirmada → v9.14.5 fix de drift).
- KERNEL:GATE-DECISION-010 (09.10) — nuevo bullet de invariante: Status=Rechazado ahora escribe Next_Action=Post-Mortem (antes Ninguna); protección terminal sin cambio (ya cubierta por STATUS_TERMINAL_MAP).
- KERNEL:GATE-DECISION-011 (09.11) — fila APPLIED→REJECTED, columna Efecto Class B actualizada con Next_Action=Post-Mortem.
- KERNEL:EVOLUTION (§17) — eliminado bloque huérfano duplicado (2x) que contradecía 07.8 sin ancla propia.
- SP:SCHEMA (08) — lista Next_Action actualizada a 9 valores (Post-Mortem, Investigar; Ninguna removida de la lista operativa).
- Bug Tracker — ticket nuevo (3b6938be...): drift SCHEMA-008 rich_text/select, Prioridad 3 ALTO, Next_Action=Documentar. Nota adicional: duplicados detectados en Changelog vivo (v9.14.3 x2, v9.14.2 x3) — no corregidos en este batch, refuerzan pendiente de vantage-tidy-changelog.
IDs afectados: ninguno nuevo — extensión/corrección de contenido bajo IDs existentes (KERNEL:SCHEMA-008, KERNEL:GATE-DECISION-010, KERNEL:GATE-DECISION-011, SP:SCHEMA). Census no requiere regeneración.
Write-Back Verification: Kernel re-fetched independientemente tras cada tanda de escritura (2 pasadas) — 07.8, 09.10, 09.11 y limpieza de §17 confirmados en posición correcta. System Prompt re-fetched — SP:SCHEMA confirmado. Notion Tracker re-fetched tras ALTER COLUMN — 10 opciones confirmadas (8 originales + Post-Mortem + Investigar), 0 opciones perdidas.
Pendiente (fuera de esta entrada): implementación en código (layer_1_run.py Fase 4 — branches de Source_Type, default, rama Rechazado→Post-Mortem) no ejecutada en este batch, que fue exclusivamente documental (mapeo + Notion schema); vantage-tidy-changelog (duplicados v9.14.2/v9.14.3, resuelto en esta misma sesión de housekeeping); resto de pendientes heredados sin tocar.
Versión actualizada: 9.14.5 (CHANGELOG). El resto de los fundacionales permanece en v9.14.4 hasta vversions --sync.
---
### v9.14.4 — Refactor ArgumentParser: Separación Semántica Scripts/Skills (verify_versions.py, KERNEL:DOCUMENTATION-007, SP:VERSION-CHECK-TOOL, ALIASES:L0-RUNTIME, MANUAL:RUNTIME-002) · 2026-08-07
Tipo: [CODE] [DOC]
Alcance: Layer_1/scripts/verify_versions.py (código, local); Kernel (KERNEL:DOCUMENTATION-007); System Prompt (SP:VERSION-CHECK-TOOL); Aliases (ALIASES:L0-RUNTIME); Manual (MANUAL:RUNTIME-002).
Contexto: Homologación de gobernanza entre Script Library y la nueva Skill Library (SKILL_LIBRARY_DATA_SOURCE_ID confirmado, base creada 2026-08-07). verify_versions.py generalizó scan_committed_scripts() → scan_committed_assets(project_root, extensions) y render_scripts_gap_report() para aceptar extensions/data_source_id/label/title_property dinámicos, agregando el flag --skills (paralelo a --scripts existente) sin regresión sobre su comportamiento previo. get_script_library_titles() expone title_property (default "Script", "Skill" para la base nueva) porque ambas bases usan nombres de propiedad título distintos.
Cambios:
- verify_versions.py — scan_committed_assets() generaliza el filtro de extensión (antes hardcodeado a .py/.sh); render_scripts_gap_report() acepta extensions/data_source_id/label/title_property; nuevo argparse --skills paralelo a --scripts; SKILL_LIBRARY_DATA_SOURCE_ID fijado a 2f1938be-fc42-83c8-8972-07300201136d.
- KERNEL:DOCUMENTATION-007 (03.7) — Modos ampliado con --scripts y --skills como modos de auditoría read-only de librerías de activos; línea de Alias actualizada.
- SP:VERSION-CHECK-TOOL (11) — nota de alcance extendido a observabilidad de Script/Skill Library.
- ALIASES:L0-RUNTIME (02) — fila vversions (sin flag) actualizada, ya no restringida a --bootstrap/--sync.
- MANUAL:RUNTIME-002 (9.2) — bullet vversions actualizado de dos a cuatro flags documentados.
IDs afectados: ninguno — extensión de contenido bajo IDs ya existentes (KERNEL:DOCUMENTATION-007, SP:VERSION-CHECK-TOOL, ALIASES:L0-RUNTIME, MANUAL:RUNTIME-002). Census no requiere regeneración.
Write-Back Verification: Kernel, System Prompt, Aliases y Manual re-fetched de forma independiente tras cada escritura — 4 bloques confirmados en posición correcta, sin mismatch.
Pendiente (fuera de esta entrada): vversions --sync para propagar v9.14.4 al resto de los fundacionales (acción local del operador).
Versión actualizada: 9.14.4 (CHANGELOG). El resto de los fundacionales permanece en v9.14.3 hasta vversions --sync.
---
Tipo: [SCHEMA] [CODE] [AUDIT]
Alcance: Notion (VANTAGE TRACKER); Scripts (Layer_1, Dashboard); Kernel (KERNEL:SCHEMA-008); Manual (MANUAL:SCHEMA-FIELD-REF); System Prompt (SP:SCHEMA).
Contexto: Formalización y cierre de deuda técnica estructural. La propiedad Next_Action migra de rich_text a select con 8 opciones validadas para eliminar drifts y errores 400 de la API. Esta entrada consolida la ejecución coordinada entre Claude, Devin y la auditoría L0.
ACCIONES POR COMPONENTE
1. Claude (Notion Schema Execution):
- Auditoría de Schema Live: Confirmado que Next_Action operaba como type:text sin opciones, validando la discrepancia reportada.
- Migración de Campo: Ejecutado cambio de tipo a select en el VANTAGE TRACKER.
- Creación de Opciones: Inyectadas las 8 opciones operativas canónicas: Archivar, Expirada, Ninguna, Follow-up, Interview prep, Re-check, Reparar URL, Verificar JD.
- Validación de Integridad: Verificado que Notion migró automáticamente los 33 valores existentes sin pérdida de datos en la conversión.
1. Devin (Code Refactor & Backfill Audit):
- Refactor de Escritura: Modificados los payloads de escritura en layer_1_run.py (4 puntos) y layer_1_run_dash.py (3 puntos) para usar la sintaxis {"select": {"name": VALUE}}.
- Script de Backfill: Creado backfill_next_action_select.py para auditoría de huérfanos post-migración.
- Resultado Dry-Run: Confirmados 33/33 registros migrados correctamente por Notion (0 huérfanos). Se determinó que no se requiere ejecución de backfill manual.
1. Reference Librarian (Documentation Mapping):
- Parches Transversales: Reescritos los contratos en Kernel, Manual y System Prompt para alinearlos con el nuevo tipo de dato y la Regla de Bloque Único.
RESUMEN DE AUDITORÍA (FULL PASS)
Componente | Estado | Detalles
L0 Runtime Index | ✅ PASS | Índices frescos (<2.3h).
L0 ID Census | ✅ PASS | 0 IDs huérfanos detectados tras la migración.
L1 Pipeline | ✅ PASS | 33 registros en estado estable.
Next_Action Migration | ✅ PASS | 33/33 migrados, 0 huérfanos.
VEREDICTO FINAL: SISTEMA READY para producción. Migración de esquema y código completada con paridad documental.
---
> El histórico completo del CHANGELOG lo podrás encontrar en ARCHIVO CHANGELOG, en esta pagina de consulta continua solo encontrarás las últimas diez entradas para garantizar la operación y referencia del sistema.
