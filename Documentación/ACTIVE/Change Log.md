# V | CHANGELOG

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
Alcance: Notion (VANTAGE TRACKER, propiedad Next_Action); Kernel (KERNEL:SCHEMA-008, KERNEL:GATE-DECISION-010, KERNEL:GATE-DECISION-011, KERNEL:EVOLUTION §17); System Prompt (SP:SCHEMA); Bug Tracker (ticket nuevo).
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
Pendiente (fuera de esta entrada): implementación en código (layer_1_run.py Fase 4 — branches de Source_Type, default, rama Rechazado→Post-Mortem) no ejecutada en este batch, que fue exclusivamente documental (mapeo + Notion schema); vantage-tidy-changelog (duplicados v9.14.2/v9.14.3); resto de pendientes heredados sin tocar.
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
| Componente | Estado | Detalles |
| --- | --- | --- |
| L0 Runtime Index | ✅ PASS | Índices frescos (<2.3h). |
| L0 ID Census | ✅ PASS | 0 IDs huérfanos detectados tras la migración. |
| L1 Pipeline | ✅ PASS | 33 registros en estado estable. |
| Next_Action Migration | ✅ PASS | 33/33 migrados, 0 huérfanos. |
VEREDICTO FINAL: SISTEMA READY para producción. Migración de esquema y código completada con paridad documental.
---
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
| Componente | Estado | Detalles |
| --- | --- | --- |
| L0 Runtime Index | ✅ PASS | Índices frescos (<2.3h). |
| L0 ID Census | ✅ PASS | 0 IDs huérfanos detectados tras la migración. |
| L1 Pipeline | ✅ PASS | 33 registros en estado estable. |
| Next_Action Migration | ✅ PASS | 33/33 migrados, 0 huérfanos. |
VEREDICTO FINAL: SISTEMA READY para producción. Migración de esquema y código completada con paridad documental.
---
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
| Componente | Estado | Detalles |
| --- | --- | --- |
| L0 Runtime Index | ✅ PASS | Índices frescos (<2.3h). |
| L0 ID Census | ✅ PASS | 0 IDs huérfanos detectados tras la migración. |
| L1 Pipeline | ✅ PASS | 33 registros en estado estable. |
| Next_Action Migration | ✅ PASS | 33/33 migrados, 0 huérfanos. |
VEREDICTO FINAL: SISTEMA READY para producción. Migración de esquema y código completada con paridad documental.
---
### v9.14.3 — Auditoría de Integridad L0 + Resolución de Identidad del Librarian · 2026-08-06
Tipo: [AUDIT] [GOVERNANCE] Alcance: Capa L0 (Observabilidad); Kernel (KERNEL:DOCUMENTATION-012); Manual (MANUAL:RUNTIME-005); System Prompt (SP:CONSISTENCY-002). Contexto: Verificación obligatoria de la infraestructura de ahorro de contexto antes de iniciar procesos de CV-A/CV-B. El protocolo detectó y corrigió un error de identificación sobre el componente "Reference Librarian" en el entorno operativo.
1. Resultados de Auditoría L0 (100% PASS):
- Runtime Index Age: ✅ PASS. Índices entity_index_v2.json y graph_v2.json con antigüedad < 1.0h (umbral: 24h) [KERNEL:DOCUMENTATION-006, MANUAL:11].
- Census Check: ✅ PASS. 0 IDs huérfanos detectados; protocolo de transferencia documental desbloqueado [KERNEL:DOCUMENTATION-008].
- Lazy Loader: ✅ PASS. Verificado fetch quirúrgico de ~150 tokens vía vload, optimizando ventana de contexto [ALIASES:02, MANUAL:14].
- Cross-Reference Validation: ✅ PASS. Confirmado uso de método PATCH en apply_hyperlinks_notion.py para preservación de block-IDs [KERNEL:DOCUMENTATION-011, CHANGELOG:v9.13.2].
2. Resolución de Discrepancia: Reference Librarian:
- Hallazgo: El reporte inicial marcó el componente como "no encontrado".
- Corrección: Se validó que el Reference Librarian es la identidad de Notebook Gemini, formalizada en la v9.14.1como una Capa de Consulta ReadOnly externa [CHANGELOG:v9.14.1, KERNEL:03.12].
- Contrato: Se verificó satisfactoriamente el contrato de Cero Inferencia Silenciosa y anclaje obligatorio de IDs [KERNEL:DOCUMENTATION-012].
3. Invariantes de Seguridad Reforzados:
- Se ratifica la Nota de Orden de Precedencia: el pipeline debe invocar gate_logic() antes que gate() para prevenir regresiones en estados terminales ("Postulado", "Rechazado", "Expirada") [KERNEL:09.11].
- Persistente: La propiedad Score_Method permanece como "corrupta/faltante" en el esquema del Archivo Tracker, sin ancla en el Kernel v9.14.1 [CHANGELOG:v9.13.0].
- Veredicto: SISTEMA CERTIFICADO PARA PRODUCCIÓN CV-A/CV-B/QA.
- Acción del Operador: Ejecutar vversions --sync para propagar formalmente la v9.14.1 si existen cambios pendientes en otros documentos [KERNEL:DOCUMENTATION-007].
Certificación del Bibliotecario: Este registro es consistente con los hallazgos de la sesión y respeta la jerarquía de autoridad definida en el BRIEF:02. Puede ser inyectado en el Change Log tras recibir un APROBAR_WRITE[KERNEL:SCHEMA-006].
---
### v9.14.2 — Auditoría de Integridad L0 (Devin)
Componentes verificados:
✅ Runtime Index Status (vstatus)

```plain text

entity_index_v2.json: 2.3 horas de antigüedad (threshold: 24h)
Total entidades: 692
Tracker entities: 33
Archive entities: 659
Hash coverage: 86.71%
```
✅ Census Check (vcensus)
```plain text

IDs en spec: 213
IDs resueltos: 213
IDs SIN link: 0
IDs huérfanos: 0
```
✅ Pipeline Layer 1 (layer_1_run.py --dry-run)
```plain text

Total procesado: 33 registros
URL Gate: 33 válidos, 0 rechazados
READY-TO-APPLY (>=60): 14
CREATE (Pipeline Activo): 32
PROTEGIDAS: 1
ESTADO ESTABLE: Sin cambios necesarios
```
Conclusión: ✅ L0 completamente operativo para CV production
### v9.14.1 — Documentación Transversal: Notebook Gemini — Auditor Documental Externo (KERNEL:DOCUMENTATION-012, MANUAL:RUNTIME-005, SP:CONSISTENCY-002) · 2026-08-05
Tipo: [DOC]
Alcance: Kernel (KERNEL:DOCUMENTATION-012, nuevo, 03.12); Manual (MANUAL:RUNTIME-005, nuevo, 9.5); System Prompt (SP:CONSISTENCY-002, nuevo, 10.1).
Contexto: El operador aportó un abstract externo describiendo a Notebook Gemini (Google Gemini, ventana de contexto sin límite de tokens equivalente) como capa de auditoría documental de solo-lectura ya en uso fuera de este chat, sin ancla en ningún documento fundacional. Protocolo de documentación transversal completo (propuesta → implementación) ejecutado sobre este gap. Durante la propuesta se descartó un alta en ALIASES:L0-RUNTIME (alias vnotebook) al detectarse que rompe la coherencia transversal del documento: cada fila de ALIASES documenta un script real invocado vía Terminal, y Notebook Gemini no invoca ningún script — es una consulta manual fuera del pipeline.
Cambios:
- KERNEL:DOCUMENTATION-012 (nuevo, 03.12, sibling de KERNEL:DOCUMENTATION-011) — define a Notebook Gemini como componente ReadOnly externo, Contrato de Cero Inferencia Silenciosa (ancla obligatoria PREFIX:KEY, declaración explícita de "Fuera de Alcance"/"No encontrado", sin cálculo de Score/CV/reglas de negocio), uso preferente para triaje documental de bajo riesgo.
- MANUAL:RUNTIME-005 (nuevo, 9.5, sibling de 9.1–9.4) — procedimiento de triaje: cuándo delegar verificación documental a Notebook Gemini en vez de fetch estructural de Claude (mismo principio de economía de tokens que vversions/vcensus), qué resuelve y qué no resuelve.
- SP:CONSISTENCY-002 (nuevo, 10.1, sub-nodo de SP:CONSISTENCY) — instruye a Claude a validar su plan contra un reporte de Notebook Gemini ante discrepancias de gobernanza documental, aclarando que el reporte no sustituye APROBAR_WRITE ni DRY RUN.
IDs afectados: 3 altas (KERNEL:DOCUMENTATION-012, MANUAL:RUNTIME-005, SP:CONSISTENCY-002) — Census requiere regeneración (vcensus, pendiente, acción local del operador).
Write-Back Verification: Kernel, Manual y System Prompt re-fetched de forma independiente tras cada escritura — los 3 bloques confirmados en posición correcta, sin mismatch.
Pendiente (fuera de esta entrada): vcensus + vversions --sync para propagar v9.14.1 al resto de los fundacionales.
Versión actualizada: 9.14.1 (CHANGELOG). El resto de los fundacionales permanece en v9.14.0 hasta vversions --sync.
---
### v9.14.0 — Documentación Transversal: Contrato Operativo L1/L2/L3 (KERNEL:ARCHITECTURE-L1/L2/L3, rename -001/-002/-003/-004 → -L1/-L2/-L3/-L4) · 2026-08-05
Tipo: [DOC] [RENAME]
Alcance: Kernel (KERNEL:ARCHITECTURE-L1, KERNEL:ARCHITECTURE-L2, KERNEL:ARCHITECTURE-L3, KERNEL:ARCHITECTURE-L4 — §04, renombrados + reestructurados); Manual (MANUAL:WEEKLY-FLOW-001, 8.1 — nota de navegación).
Contexto: El operador aportó un abstract externo describiendo L1/L2 con vocabulario que el Kernel no cubría (Objetivo, Componentes, Campos inmutables, Reglas de dedup/enriquecimiento, Estados de error, Métricas mínimas) — solo tenía trigger + diagrama de flujo por capa. Protocolo de documentación transversal completo (propuesta → implementación) ejecutado sobre este gap. Durante el mapeo se detectó y confirmó un drift preexistente: el ID CENSUS ya listaba KERNEL:ARCHITECTURE-L1/L2/L3/L4, mientras el Kernel vivo mantenía la nomenclatura legacy -001/-002/-003/-004 (Manual, en MANUAL:MONITOR §11, ya citaba -L4 también — el Census y esa referencia puntual estaban adelantados a su fuente). El operador confirmó el Census como versión correcta; este batch alinea el Kernel a esa nomenclatura.
Cambios:
- KERNEL:ARCHITECTURE-L1 (04.1, rename de -001) — nodo contenedor. Nuevo hijo 04.1.1 KERNEL:ARCHITECTURE-L1-001 (Flujo Operativo, contenido preexistente sin alterar). Nuevo hijo 04.1.2 KERNEL:ARCHITECTURE-L1-002 (Contrato Operativo: Objetivo, Componentes, Responsabilidades, Campos inmutables, Reglas de dedup con referencia cruzada a L4, Estados de error, Métricas mínimas).
- KERNEL:ARCHITECTURE-L2 (04.2, rename de -002) — mismo patrón: 04.2.1 KERNEL:ARCHITECTURE-L2-001 (Flujo Operativo) + 04.2.2 KERNEL:ARCHITECTURE-L2-002 (Contrato Operativo: Objetivo, Componentes, Responsabilidades, Reglas de consolidación/enriquecimiento, Estados de error, Métricas mínimas).
- KERNEL:ARCHITECTURE-L3 (04.3, rename de -003) — mismo patrón: 04.3.1 KERNEL:ARCHITECTURE-L3-001 (Flujo Operativo) + 04.3.2 KERNEL:ARCHITECTURE-L3-002 (Contrato Operativo: Objetivo, Componentes, Responsabilidades, Campos inmutables, Reglas de dedup, Estados de error, Métricas mínimas).
- KERNEL:ARCHITECTURE-L4 (04.4, rename de -004) — rename simple, sin alteración de contenido.
- MANUAL:WEEKLY-FLOW-001 (8.1 Lunes) — nota de navegación agregada al párrafo inicial, apuntando a los 3 nuevos IDs de Contrato Operativo (mismo patrón índice-hacia-Kernel que MANUAL:GOLDEN-RULES §16 y MANUAL:CV-GOLDEN-RULES-INDEX §18).
IDs afectados: 4 renames (KERNEL:ARCHITECTURE-001/002/003/004 → -L1/-L2/-L3/-L4) + 6 altas (KERNEL:ARCHITECTURE-L1-001/L1-002/L2-001/L2-002/L3-001/L3-002) = 10 IDs — Census requiere regeneración (vcensus, pendiente, acción local del operador).
Write-Back Verification: Kernel y Manual re-fetched de forma independiente tras la escritura — los 5 bloques (4 en Kernel + 1 en Manual) confirmados en posición correcta, sin mismatch.
Pendiente (fuera de esta entrada): vcensus + vversions --sync para propagar v9.14.0 al resto de los fundacionales.
Versión actualizada: 9.14.0 (CHANGELOG). El resto de los fundacionales permanece en v9.13.11 hasta vversions --sync.
---
### v9.13.11 — Documentación: Valores Operativos Next_Action (KERNEL:SCHEMA-008) + Fix Alias vhyperlinks Local + Corrida Completa de Hyperlinks · 2026-08-04
Tipo: [DOC] [FIX]
Alcance: Kernel (KERNEL:SCHEMA-008, nuevo); System Prompt (SP:SCHEMA, cross-ref); alias local vhyperlinks (.zshrc, fuera de Notion).
Contexto: Cierre del gap documental sobre Next_Action del Tracker de vacantes (ver v9.13.7-v9.13.9, donde se documentó Prioridad y el invariante de Next_Action huérfano pero nunca los valores operativos en sí). Auditoría de código realizada por Devin sobre layer_1_run.py, verificada línea por línea contra el repositorio real por Claude antes de documentar. En paralelo se detectó y corrigió un bug de entorno local: el alias vhyperlinks apuntaba a apply_hyperlinks.py (deprecado, ya no existe en repo) en vez de apply_hyperlinks_notion.py — bug confirmado por dump de Terminal (KERNEL:GATE-DECISION-009 Nivel 3), ticket no llegó a crearse en Bug Tracker porque el operador resolvió directo en la misma sesión.
Cambios:
- KERNEL:SCHEMA-008 (nuevo, 07.8) — documenta los 8 valores operativos confirmados en código activo de Next_Action (Archivar, Expirada, Ninguna, Follow-up, Interview prep, Re-check, Reparar URL, Verificar JD), con condición de disparo de cada uno. Corrige además el tipo de campo documentado en v9.13.7 (rich_text real, no select).
- SP:SCHEMA (08) — línea de cross-referencia a KERNEL:SCHEMA-008.
- Alias local vhyperlinks (.zshrc) — corregido de apply_hyperlinks.py a apply_hyperlinks_notion.py --all, con --root removido (flag inexistente en el script nuevo, confirmado contra código fuente real).
- Corrida real de vhyperlinks --apply sobre los 7 documentos fundacionales tras el fix del alias: 228 bloques patcheados, 0 errores — incluye la autocorrección del anchor del link a KERNEL:SCHEMA-008 en SP:SCHEMA (Claude había escrito un anchor placeholder incorrecto en la inyección original; el censo dinámico lo resolvió al valor real sin intervención manual).
IDs afectados: 1 alta (KERNEL:SCHEMA-008) — Census requiere regeneración (vcensus, pendiente, acción local del operador).
Write-Back Verification: Kernel y System Prompt re-fetched de forma independiente tras la inyección inicial y de nuevo tras la corrida de vhyperlinks — bloque en posición correcta ambas veces, anchor del link confirmado corregido en la segunda verificación.
Pendiente (fuera de esta entrada): vcensus + vversions --sync para propagar v9.13.11 al resto de los fundacionales.
Versión actualizada: 9.13.11 (CHANGELOG). El resto de los fundacionales permanece en v9.13.10 hasta vversions --sync.
---
### v9.13.10 — Fix: verify_versions.py HTTP 400 Fantasma (Endpoint Legacy + Schema Prioridad Desalineado) · 2026-08-03
Tipo: [FIX] [DOC]
Alcance: Layer_1/scripts/verify_versions.py (código, local); KERNEL:TRACKER-SCHEMA-001, KERNEL:TRACKER-SCHEMA-002, SP:SCHEMA (Notion).
Contexto: Los 2 tickets "HTTP 400" (Bug + Task) reportados por vversions --bootstrap desde 2026-07-27 (4 sesiones consecutivas sin diagnóstico) tenían dos causas apiladas. Primero, get_priority_tickets() era la única función del script pegando contra el endpoint legacy /v1/databases/{id}/query con Notion-Version 2022-06-28 y el DB ID en vez del data source ID (COL), inconsistente con get_last_ledger_row() y get_script_library_titles(), que ya usaban /v1/data_sources/{id}/query + 2025-09-03. Segundo, una vez corregido el endpoint, Notion devolvió el error real: el filtro de Prioridad usaba "CRÍTICO"/"ALTO" sin prefijo, mientras el schema real de Bug/Tasks Tracker usa "4 CRÍTICO"/"3 ALTO"/"2 MEDIO"/"1 BAJO" — desalineación heredada de la migración a fórmula híbrida Urgencia × Importancia (v9.13.7/v9.13.8), nunca propagada a KERNEL:TRACKER-SCHEMA-002 ni SP:SCHEMA.
Cambios:
- verify_versions.py — nuevo helper query_data_source() centraliza todo POST a /v1/data_sources/{id}/query (Notion-Version 2025-09-03, captura response.text[:200] en error). get_last_ledger_row(), get_priority_tickets() y get_script_library_titles() migradas al mismo helper — ya no puede reaparecer un HTTP sin body de error oculto. BUG_TRACKER_DB_ID/TASKS_TRACKER_DB_ID renombradas a BUG_TRACKER_DATA_SOURCE_ID/TASKS_TRACKER_DATA_SOURCE_ID con los COL ID correctos. Filtro de Prioridad corregido a "4 CRÍTICO"/"3 ALTO".
- KERNEL:TRACKER-SCHEMA-002 — tabla "Niveles de Prioridad" actualizada con prefijo numérico (4 CRÍTICO/3 ALTO/2 MEDIO/1 BAJO), reflejando el schema real de Notion.
- KERNEL:TRACKER-SCHEMA-001 — celda Tasks Tracker COL ID completada (antes vacía) con aaaaef55-a1ce-45f7-9c8b-1c1def2c18e8, ya confirmado en SP:DIGITAL-ID-CARD.
- SP:SCHEMA — mismo fix de prefijo numérico en Prioridad, aplicado a los bloques de Bug Tracker y Tasks Tracker.
IDs afectados: ninguno — corrección de valores/celdas bajo IDs ya existentes (KERNEL:TRACKER-SCHEMA-001, KERNEL:TRACKER-SCHEMA-002, SP:SCHEMA). Census no requiere regeneración.
Write-Back Verification: KERNEL y SYSTEM PROMPT re-fetched de forma independiente tras la escritura — ambos bloques confirmados en posición correcta, resto de ambos documentos byte-idéntico. verify_versions.py validado localmente con py_compile antes de entrega al operador.
Pendiente (fuera de esta entrada): vantage-tidy-bug-task-tracker/SKILL.md y vantage-create-bug-task/SKILL.md (fuera de Notion, gobernanza local) aún referencian Prioridad sin prefijo numérico — armonía cosmética, no bloqueante, pendiente de próxima sesión local.
Versión actualizada: 9.13.10 (CHANGELOG). El resto de los fundacionales permanece en v9.13.9 hasta vversions --sync.
---
### v9.13.9 — Documentación Transversal: Prioridad Migra a Escritura Primaria en Fase 3.6 (priority_logic.py, KERNEL:TRIGGER-002, MANUAL:RUNTIME-002) · 2026-08-03
Tipo: [DOC]
Alcance: Kernel (KERNEL:TRIGGER-002); Manual (MANUAL:RUNTIME-002).
Contexto: Continuación directa de v9.13.8. Esa entrada documentó la fórmula de Prioridad (Urgencia × Importancia) asumiendo a VL1 backfill como escritor primario — supuesto correcto en ese momento, pero superado por el trabajo de esta sesión: se implementó priority_logic.py como módulo compartido, se rompió el import circular entre layer_1_run.py y backfill_class_a.py, y se agregó Fase 3.6 en layer_1_run.py como escritura primaria de Prioridad en el ingreso normal del pipeline. VL1 backfill pasa a ser catch-up (huecos de migración o registros pre-Fase 3.6), no la vía principal. Se migraron 59 registros existentes al formato numérico de Prioridad como parte de este trabajo. Siguiendo el patrón de v9.11.7 (registro retroactivo sin editar entradas pasadas), esta entrada es nueva y no modifica v9.13.7 ni v9.13.8 — el Change Log no reescribe su propio historial.
Cambios:
- KERNEL:TRIGGER-002 — bullet VL1 backfill reescrito: de "escribe... en registros vacíos" a "catch-up de campos Class A faltantes... para registros que no pasaron por la escritura primaria de Fase 3.6"; nueva frase explica que Fase 3.6 (layer_1_run.py) escribe Prioridad primero en el ingreso normal, y que ambos caminos comparten lógica desde priority_logic.py (módulo compartido, evita import circular). Línea "Implementación" actualizada para referenciar priority_logic.py como matriz compartida, invocada por Fase 3.6 (primaria) y backfill_class_a.py (catch-up).
- MANUAL:RUNTIME-002 — bullet vl1 backfill: aclara que es catch-up (no la vía primaria), que la fórmula vive en priority_logic.py referenciada desde KERNEL:TRIGGER-002, y que vl1 (bare, Fase 3.6) la ejecuta primero como parte del ingreso normal del pipeline.
IDs afectados: ninguno — extensión de contenido bajo IDs ya existentes (KERNEL:TRIGGER-002, MANUAL:RUNTIME-002). Census no requiere regeneración.
Write-Back Verification: Kernel y Manual re-fetched de forma independiente tras la escritura — ambos bloques confirmados en posición correcta, resto de ambos documentos byte-idéntico.
Pendiente (fuera de esta entrada): ninguno nuevo generado por esta implementación.
Versión actualizada: 9.13.9 (CHANGELOG). El resto de los fundacionales permanece en v9.13.8 hasta vversions --sync.
---
### v9.13.8 — Documentación Transversal: Fórmula de Prioridad (Urgencia × Importancia) + Invariante Status/Next_Action (KERNEL:GATE-DECISION-010, KERNEL:TRIGGER-002, MANUAL:RUNTIME-002) · 2026-08-03
Tipo: [DOC]
Alcance: Kernel (KERNEL:GATE-DECISION-010, KERNEL:TRIGGER-002); Manual (MANUAL:RUNTIME-002).
Contexto: Cierra el gap documental dejado por la entrada v9.13.7 (Deuda Técnica Rx Tracker) — dos cambios de lógica de negocio implementados en Python (backfill_class_a.py, layer_1_run.py) sin contraparte en los documentos fundacionales: (1) la fórmula híbrida Urgencia × Importancia que ahora calcula Prioridad nunca estuvo descrita fuera del código; (2) el fix de Next_Action huérfano (Fase 2/3.5 escribiendo Status=Expirada sin Next_Action=Archivar) no tenía invariante explícito en KERNEL:GATE-DECISION-010 pese a que ese ID ya gobierna la relación Status→Next_Action.
Cambios:
- KERNEL:GATE-DECISION-010 — nuevo bullet en Invariantes: todo write que fija Status=Expirada (Fase 2 URL_GATE, Fase 3.5 filtro de perfil) debe fijar Next_Action=Archivar en el mismo write.
- KERNEL:TRIGGER-002 — bullet VL1 backfill extendido con la fórmula de Prioridad (bucket de Importancia por Score + matriz Urgencia × Importancia de 16 combinaciones) y referencia a backfill_class_a.py::apply_importancia_matrix(). Sin heading nuevo, sin alta de ID — prosa dentro del ID existente.
- MANUAL:RUNTIME-002 — bullet vl1 backfill: frase de cierre remitiendo a KERNEL:TRIGGER-002 para la fórmula completa.
IDs afectados: ninguno — extensión de contenido bajo IDs ya existentes (KERNEL:GATE-DECISION-010, KERNEL:TRIGGER-002, MANUAL:RUNTIME-002). Census no requiere regeneración.
Write-Back Verification: Kernel y Manual re-fetched de forma independiente tras la escritura — los 3 bloques confirmados en posición correcta, resto de ambos documentos byte-idéntico.
Pendiente (fuera de esta entrada): ninguno nuevo generado por esta implementación.
Versión actualizada: 9.13.8 (CHANGELOG). El resto de los fundacionales permanece en v9.13.7 hasta vversions --sync.
---
### v9.13.7 DRY RUN PARA CHANGELOG - Deuda Técnica Rx Tracker (Prioridad + Gate/Next_Action)
Fecha: 2026-08-03
Contexto: Resolución de deuda técnica relacionada con propiedad Prioridad (huérfana) y fragmentación de lógica Gate/Next_Action
## CONTEXTO INICIAL
### Problema Identificado
1. Propiedad Prioridad: Declarada como "eliminada en v8.0" en docstring de layer_1_run.py, pero presente en schema Notion sin escritor activo. Referencia KERNEL:TRIGGER-002 indicaba que backfill_class_a.py sería el escritor designado, pero nunca se había ejecutado.
1. Fragmentación Gate/Next_Action: assign_next_action.py (script suelto invocado via Raycast) duplicaba lógica de layer_1_run.py Fase 4 con divergencias de negocio.
1. Bug de consistencia: Fase 2 y Fase 3.5 escribían Status="Expirada" sin escribir Next_Action="Archivar", dejando inconsistencia de datos.
### Hallazgos del Diagnóstico
- Prioridad estaba huérfana de facto: backfill_class_a.py existía y era funcional, pero nunca se había ejecutado sobre las 58 filas actuales
- assign_next_action.py tenía 2 bugs de negocio:
- No manejaba Status="Rechazado" explícitamente (caía a default BLOCKED → Archivar)
- Era más permisivo con Role_Class="Pivote" sin filtro has_vm_title_signal()
- Score=40 = BASE SCORE (sin bonificaciones) = "Sin evaluar", no un valor calculado orgánico
- Distribución real de Score: 46 registros con Score=40, 7 con Score=50, 1 con Score=55, 1 con Score=60, 4 con Score=65
---
## CAMBIOS IMPLEMENTADOS POR TICKET
### TICKET A — Fix Next_Action huérfano
Objetivo: Resolver inconsistencia entre Status="Expirada" y Next_Action="Archivar"
Cambios en layer_1_run.py:
FASE 2 (líneas 658-664):
```python
# ANTES
client.pages.update(
    page_id=item["id"],
    properties={
        "Fetch": {"select": {"name": "Bloqueado"}},
        "Status": {"select": {"name": "Expirada"}},
    }
)

# DESPUÉS
client.pages.update(
    page_id=item["id"],
    properties={
        "Fetch": {"select": {"name": "Bloqueado"}},
        "Status": {"select": {"name": "Expirada"}},
        "Next_Action": {"select": {"name": "Archivar"}},  # ← AGREGADO
    }
)
```
FASE 3.5 (líneas 788-794):
```python
# ANTES
client.pages.update(
    page_id=item["id"],
    properties={"Status": {"select": {"name": "Expirada"}}},
)

# DESPUÉS
client.pages.update(
    page_id=item["id"],
    properties={
        "Status": {"select": {"name": "Expirada"}},
        "Next_Action": {"select": {"name": "Archivar"}},  # ← AGREGADO
    },
)
```
Dry-run: 0 registros afectados en estado actual (0 rechazados en Fase 2, 0 vacantes fuera de perfil en Fase 3.5)
Ejecución real: Exit code 0, sin cambios en estado actual (fix preventivo para futuros registros)
---
### TICKET B — Implementación de Prioridad (fórmula híbrida Urgencia × Importancia)
Objetivo: Extender infer_prioridad() en backfill_class_a.py para cruzar Urgencia (deadline/antigüedad) con Importancia (Score/VM_Scope)
Lógica implementada:
PASO 1 - Definir eje de Importancia:
```python
def get_importancia_bucket(score: int) -> str:
    if score == 40:
        return "Base"        # Sin datos — BASE SCORE exacto, sin bonificaciones
    elif score <= 60:
        return "Media"       # 41-60
    elif score <= 80:
        return "Alta"        # 61-80
    elif score <= 100:
        return "Muy Alta"    # 81-100
    else:
        return "Base"        # fallback defensivo
```
PASO 2 - Matriz Urgencia × Importancia:
```python
def apply_importancia_matrix(urgencia: str, importancia_bucket: str) -> str:
    matrix = {
        ("CRÍTICO", "Base"):     "CRÍTICO",
        ("CRÍTICO", "Media"):    "CRÍTICO",
        ("CRÍTICO", "Alta"):     "CRÍTICO",
        ("CRÍTICO", "Muy Alta"): "CRÍTICO",
        ("ALTO",    "Base"):     "MEDIO",
        ("ALTO",    "Media"):    "ALTO",
        ("ALTO",    "Alta"):     "CRÍTICO",
        ("ALTO",    "Muy Alta"): "CRÍTICO",
        ("MEDIO",   "Base"):     "BAJO",
        ("MEDIO",   "Media"):    "MEDIO",
        ("MEDIO",   "Alta"):     "ALTO",
        ("MEDIO",   "Muy Alta"): "CRÍTICO",
        ("BAJO",    "Base"):     "BAJO",
        ("BAJO",    "Media"):    "BAJO",
        ("BAJO",    "Alta"):     "MEDIO",
        ("BAJO",    "Muy Alta"): "ALTO",
    }
    return matrix.get((urgencia, importancia_bucket), "BAJO")
```
PASO 3 - Reconexión en infer_prioridad():
- Conservó detector de deadline vía regex intacto
- Calcula Urgencia (lógica original: deadline + antigüedad + Source_Type)
- Calcula Importancia (bucket de Score)
- Aplica matriz Urgencia × Importancia
Matriz de decisión implementada:
| Urgencia \ Importancia | Base (Score=40) | Media (41-60) | Alta (61-80) | Muy Alta (81-100) |
| --- | --- | --- | --- | --- |
| CRÍTICO (deadline/Inbound) | CRÍTICO | CRÍTICO | CRÍTICO | CRÍTICO |
| ALTO (≤3 días) | MEDIO | ALTO | CRÍTICO | CRÍTICO |
| MEDIO (4-14 días) | BAJO | MEDIO | ALTO | CRÍTICO |
| BAJO (>14 días) | BAJO | BAJO | MEDIO | ALTO |
Dry-run (59 registros):
```plain text
Distribución de Prioridad (nueva fórmula):
  CRÍTICO: 2
  ALTO: 5
  MEDIO: 13
  BAJO: 39
```
Ejecución real:
```plain text
✅ Actualizadas: 59  |  ❌ Fallidas: 0
```
Archivos modificados:
- Layer_1/scripts/backfill_class_a.py (reescritura completa de infer_prioridad() + agregado de funciones auxiliares)
---
### TICKET C — Deprecación de assign_next_action.py
Objetivo: Archivar script duplicado con lógica divergente
Acciones ejecutadas:
1. Creó carpeta Layer_1/scripts/deprecated/
1. Movió Layer_1/scripts/assign_next_action.py → Layer_1/scripts/deprecated/assign_next_action.py
1. Movió Raycast/vantage-assign.sh → Layer_1/scripts/deprecated/vantage-assign.sh
1. Creó Layer_1/scripts/deprecated/DEPRECATED_assign_next_action.md con:
- Qué hacía el script
- Por qué se archivó (duplicación + divergencia)
- Bugs conocidos (Rechazado, Pivote sin has_vm_title_signal)
- Camino correcto para revivir (importar funciones canónicas de layer_1_run.py)
Commit:
```plain text
[main c175d22] deprecate: move assign_next_action.py and vantage-assign.sh to /deprecated
```
Verificación post-movimiento:
- No quedan referencias activas a rutas viejas
- Solo referencias en archivos de diagnóstico y documentación de deprecated
---
### TICKET D — Higiene menor
Objetivo: Limpieza de código temporal y validación de sintaxis
Cambios:
1. Eliminó print(f"DEBUG: props['Prioridad'] = ...") de feed_processor.py línea 1029
1. Validó sintaxis con python -m py_compile sobre:
- backfill_class_a.py ✅
- layer_1_run.py ✅
- feed_processor.py ✅
---
## REPORTE FINAL
### Archivos Modificados
1. Layer_1/scripts/layer_1_run.py - Fix Next_Action huérfano (2 puntos de escritura)
1. Layer_1/scripts/backfill_class_a.py - Implementación fórmula híbrida Urgencia × Importancia
1. Layer_1/scripts/feed_processor.py - Eliminación DEBUG print
### Archivos Movidos/Archivados
1. Layer_1/scripts/assign_next_action.py → Layer_1/scripts/deprecated/
1. Raycast/vantage-assign.sh → Layer_1/scripts/deprecated/
1. Layer_1/scripts/deprecated/DEPRECATED_assign_next_action.md (nuevo)
### Archivos de Diagnóstico Creados (para referencia)
- DIAGNOSTICO_RX_TRACKER_PRIORIDAD.md
- DIAGNOSTICO_RX_TRACKER_PRIORIDAD_v2.md
- DIAGNOSTICO_comparacion_gate_logic.md
- DIAGNOSTICO_layer_1_run_gate_functions.py
- DIAGNOSTICO_backfill_class_a.py
- DIAGNOSTICO_VERIFICACION_FASE4.py
- extract_scores.py
- extract_scores_detailed.py
### Impacto en Datos
- Prioridad: 59 registros escritos con nueva fórmula híbrida
- CRÍTICO: 2 (3.4%)
- ALTO: 5 (8.5%)
- MEDIO: 13 (22.0%)
- BAJO: 39 (66.1%)
- Next_Action: 0 cambios en estado actual (fix preventivo)
- layer/hash: 1 hash actualizado, 0 layers actualizados
### Estado Final
- ✅ Propiedad Prioridad ahora poblada con lógica híbrida Urgencia × Importancia
- ✅ Bug de Next_Action huérfano resuelto (preventivo)
- ✅ Duplicación de lógica Gate/Next_Action eliminada (assign_next_action.py archivado)
- ✅ Código limpio (DEBUG prints eliminados, sintaxis validada)
### Resolución de Contradicciones
- Docstring vs Kernel.md: Documentado que KERNEL:TRIGGER-002 es la autoridad para Prioridad, docstring de layer_1_run.py estaba desactualizado
- input() restriction: Confirmado que restricción "nunca usa input() interactivo" aplica solo a VL1 batch, no a backfill_class_a.py
---
## PRÓXIMOS PASOS RECOMENDADOS
1. Actualizar docstring de layer_1_run.py para reflejar que Prioridad sí se escribe (via backfill_class_a.py según KERNEL:TRIGGER-002)
1. Considerar actualización de lógica de gate en layer_1_run.py Fase 4 si se necesita acceso manual a recálculo de Next_Action (path de revival documentado en DEPRECATED_assign_next_action.md)
1. Monitorear distribución de Prioridad en futuros runs para validar calibración de matriz Urgencia × Importancia
---
### v9.13.6 — Fix: Rigor de posted_date en Prompt A para Sostener la Rúbrica de Prioridad (Prompt E) · 2026-08-02
Tipo: [FIX] [PROMPT]
Alcance: PROMPT LIBRARY — Prompt A (368938be-fc42-8162-ae48-d48970a729dc).
Contexto: Continuación directa de v9.13.5. Auditoría de Prompt A confirmó que el ITEM SCHEMA ya expone posted_date, source_type y jd — los tres campos que la rúbrica de Prioridad de Prompt E consume — sin gap estructural. Pero la regla de Active posting permitía fetch_status: needs_verification + posted_date: null con demasiada facilidad (cualquier posting sin fecha visible en el HTML caía directo a null), lo que hubiera degradado la rúbrica de Prioridad a "1 BAJO" por omisión de dato en vez de por antigüedad real — socavando el fix de v9.13.5 antes de que produjera valor.
Cambios:
- Prompt A — regla Active posting: agregado bloque de resolución de posted_date con 3 vías de intento obligatorias antes de usar null — (1) fecha explícita en página/metadata schema.org, (2) fecha relativa de plataforma ("Hace 3 días") convertida a YYYY-MM-DD, (3) fecha en URL/job_id de ATS. Solo si las tres fallan, posted_date: null + fetch_status: needs_verification (comportamiento previo preservado como último recurso, no eliminado).
IDs afectados: ninguno — cambio de prompt externo (wrappers L1/L2 vía Comet/motores de búsqueda), no de documentación fundacional. Census no requiere regeneración.
Verificación: re-fetch independiente de Prompt A tras la escritura — bloque confirmado en posición correcta, resto del prompt (schema, exclusiones, query patterns) byte-idéntico.
Pendiente (fuera de esta entrada): validar en el próximo ciclo semanal (Lunes) qué porcentaje real de posted_date se resuelve por las 3 vías nuevas vs. cuántos siguen cayendo a null — sin datos de producción aún.
Versión actualizada: 9.13.6 (CHANGELOG). El resto de los fundacionales permanece en v9.13.4 hasta vversions --sync.
---
### v9.13.5 — Fix: Prioridad Class A ahora "viva" desde origen (Prompt E) + Default Fantasma Removido en feed_processor.py · 2026-08-02
Tipo: [FIX] [PROMPT]
Alcance: PROMPT LIBRARY — Prompt E (368938be-fc42-8177-b4a1-d2e8ea1e2e08); Layer_1/scripts/feed_processor.py (líneas 1022-1028).
Contexto: Auditoría de trazabilidad del campo Prioridad solicitada por el operador, motivada por KERNEL:SCHEMA-007 (Prioridad es campo Class A requerido del Entry Template) y KERNEL:PURPOSE ("evaluar antes de escribir"). Devin confirmó por inspección directa: (1) el JSON consolidado de L1+L2 nunca contenía Prioridad — no se calculaba en ningún punto de la fase de consolidación; (2) feed_processor.py compensaba esa ausencia con un default hardcodeado "4 CRÍTICO" (líneas 1025-1028), contradiciendo KERNEL:TRIGGER-002 y MANUAL:RUNTIME-002 (9.2), que asignan explícitamente esa responsabilidad a vl1 backfill. El default ensuciaba el pipeline con falsos positivos de urgencia crítica en todo registro sin Prioridad de origen.
Cambios:
- Prompt E — nuevo bloque PRIORIDAD insertado antes de OUTPUT: rúbrica determinista de 4 niveles (CRÍTICO/ALTO/MEDIO/BAJO) basada exclusivamente en campos ya presentes en el registro (posted_date, source_type, detección textual de deadline en jd) — sin evaluación de fit ni juicio de calidad del rol, consistente con el rol de Perplexity como orquestador de consolidación/dedup, no de evaluación.
- feed_processor.py — removida la asignación props["Prioridad"] = schema.select_value("4 CRÍTICO"). La clave Prioridad ahora queda completamente ausente del payload cuando no viene en el JSON de entrada (no None, no string vacío — ausente).
Verificación (evidencia real de ejecución, no inferida):
- py_compile OK sobre feed_processor.py.
- Dry-run con JSON de prueba sin campo Prioridad (test_prioridad_default.json): output confirma props['Prioridad'] = CLAVE AUSENTE — comportamiento verificado, no asumido.
- Auditoría de rutas de escritura: feed_processor.py es CREATE-only para registros Class A (notion.pages.create()); las únicas rutas UPDATE existentes (_upgrade_layer_if_needed, _set_dedup_flag_if_needed) tocan exclusivamente layer y Dedup_Flag — ninguna puede sobrescribir una Prioridad ya poblada en un registro existente. Riesgo de sobrescritura confirmado como cero, no supuesto.
IDs afectados: ninguno — cambio de prompt externo (Perplexity) y código Python, no de documentación fundacional. Census no requiere regeneración.
Pendiente (fuera de esta entrada):
- Prioridad sigue sin calcularse en L1 (Career Sites/LinkedIn/Aggregators, vía Comet) ni en L3 (Gmail/Groq) — comportamiento esperado por diseño: ambos caminos dependen de vl1 backfill para llenar el campo, consistente con KERNEL:TRIGGER-002.
Versión actualizada: 9.13.5 (CHANGELOG). El resto de los fundacionales permanece en v9.13.4 hasta vversions --sync.
---
### v9.13.4 — Gobernanza y Saneamiento: Neutralización de Riesgos y Cierre de Drifts · 2026-08-02
Tipo: [FIX] [GOVERNANCE] [CLEANUP]
Alcance: Layer_4/scripts/vsync_doc_fast.py (Deprecado); Session Ledger (Auditoría); Career Canon (Validación Visual); Skill vsum (Optimización).
Contexto: Fase final del Plan de Respuesta Ágil. Cierre de brechas de seguridad en sincronización rápida y resolución de inconsistencias históricas en el Ledger.
Cambios:
- Infraestructura: Deprecación oficial de vsync_doc_fast.py. El script ha sido marcado como DEPRECADO por el operador para neutralizar el patrón destructivo delete-all que vulneraba la integridad de los hyperlinks protegidos en la v9.13.2 [KERNEL:ARCHITECTURE-L4].
- Auditoría de Ledger: Se confirma la inexistencia de la sesión SESSION-2026-07-19-A en el Ledger vivo. El hallazgo histórico (v9.11.4) queda archivado como registro eliminado o error de persistencia, invalidando el escalamiento Nivel 3.
- Validación de Formato: Se desestima la limpieza de indentación (\t) en el Career Canon [CANON:KPIS/FACTS] tras confirmarse la ausencia de problemas de renderizado en la capa de salida (Figma).
- Optimización Skill vsum: Mejora en la lógica de búsqueda para garantizar que el Escenario 2 (cruce de tickets) sea exhaustivo, integrando el escaneo del ARCHIVO CHANGELOG [ALIASES:L4-VERSION-CONTROL].
Verificación: Auditoría de consistencia 100% PASS; Riesgo de sincronización rápida mitigado por deprecación; Inconsistencias de Ledger resueltas por autoridad del operador.
IDs afectados: Ninguno.
Pendiente: Eliminación física de vsync_doc_fast.py en el repositorio local por parte del operador.
---
### v9.13.3 — Auditoría de Cierre: Tooling de Heading IDs Verificado (GATE 1/2 PASS) · 2026-08-02
Tipo: [DOC] [AUDIT]
Alcance: Layer_1/scripts/vantage_id_rules.py, normalize_heading_ids.py, generate_id_inventory.py (verificación, sin cambio de código). KERNEL:DOCUMENTATION-011 (referencia de estado).
Contexto: Contrato de sesión solicitaba refactor de vantage_id_rules.py y fix de normalize_heading_ids.py bajo el supuesto de que ambos scripts operaban con lógica legacy (búsqueda de símbolo §, falsos positivos de "heading mal formado"). Verificación directa contra código y ejecución real determinó que el supuesto no aplicaba: la migración correspondiente ya se había completado en sesión previa (contrato 2026-07-25, ver contrato_migracion_headings.md) y KERNEL:DOCUMENTATION-011 ya confirma "generate_id_inventory.py y normalize_heading_ids.py ya fueron migrados". No hubo refactor que ejecutar — la tarea real era auditoría de cierre.
Cambios:
- py_compile OK sobre los 3 scripts (vantage_id_rules.py, normalize_heading_ids.py, generate_id_inventory.py) — GATE 2 (integridad de dependencias) PASS. Confirmado que normalize_heading_ids.py importa classify_heading/suggest_canonical_heading de vantage_id_rules.py sin reimplementación local.
- normalize_heading_ids.py ejecutado en modo dry-run real (sin --apply) sobre los 6 documentos editables vía Terminal del operador (venv Layer_1/.venv), no simulado: "Ningún heading mal formado detectado. Nomenclatura 100% canónica." — GATE 1 PASS.
- GATE 3 (sync de versión) ya satisfecho por vversions --sync corrido por el operador en esta misma sesión, previo a esta entrada — confirmó los 9 fundacionales en v9.13.2 antes de este batch.
IDs afectados: ninguno — verificación de tooling, no de documentación fundacional. Census no requiere regeneración.
Verificación: py_compile exit 0 (3/3 scripts); normalize_heading_ids.py --csv corrido en Terminal real del operador, exit 0, 0 hallazgos.
Pendiente (fuera de esta entrada): ninguno nuevo generado por esta auditoría.
Versión actualizada: 9.13.3 (CHANGELOG). El resto de los fundacionales permanece en v9.13.2 hasta vversions --sync.
---
### v9.13.2 — Infraestructura: Refactor vsync_doc (PATCH) e Implementación class_b_guard (GAP-03) · 2026-08-01
Tipo: [FIX] [INFRA] [SECURITY]
Alcance: Layer_4/scripts/vsync_doc.py; Layer_1/scripts/class_b_guard.py.
Contexto: Resolución del riesgo de integridad de anchors documentado en KERNEL:ARCHITECTURE-L4 y mitigación técnica de GAP-03 (KERNEL:GATE-DECISION-003).
Cambios:
- vsync_doc.py: Función push_local_to_notion() reescrita íntegramente para usar el método PATCH puntual (notion.blocks.update). Se elimina el patrón destructivo delete-all + create-all que invalidaba los block_ids necesarios para el Sistema de Cross-Reference Hyperlinks (KERNEL:DOCUMENTATION-011).
- class_b_guard.py: Implementación del guard técnico para bloquear escrituras desde el componente AI hacia campos Class B (Score, Gate_Decision, VM_Scope, etc.). Asegura el cumplimiento del contrato de ownership definido en KERNEL:SCHEMA-001 y KERNEL:OWNERSHIP-001.
- Deuda Técnica: Eliminados comentarios temporales de v8.5.7 en los scripts de sincronización.
Verificación: py_compile OK; diff validado sin ciclos de borrado; test de bloqueo Class B PASS.
IDs afectados: Ninguno (cambios de lógica de sistema). Census no requiere regeneración.
Pendiente: vversions --sync para propagar v9.13.2 a los documentos fundacionales.
---
### v9.13.1 — [COMPRIMIDO] Saneamiento Bug/Task Tracker: 9 tickets cerrados, 2 propiedades Solución creadas, 1 bug de skill logueado · 2026-08-01
Tipo: [COMPRIMIDO]
Resumen: vantage-tidy-bug-task-tracker corrido (8 tickets, Bug+Task) pero Escenario 2 (cruce Changelog) no fue exhaustivo — operador cerró manualmente varios tickets adicionales después, exponiendo el gap. Bug Tracker: 3 tickets cerrados manualmente por el operador recibieron Solución+Fecha_Resolución retroactivas (Dedup no detecta duplicados, Sesiones huérfanas, GAP-03); 1 ticket más (is_definition_block TOC) cerrado con evidencia real hallada en Changelog v9.12.0. Ticket nuevo creado: 'Escenario 2 del skill vantage-tidy-bug-task-tracker no hace cruce exhaustivo contra Changelog' (3af938be-fc42-812e-99d9-c886c680bbfb), Prioridad ALTO. Propiedad Solución (rich_text) creada en Tasks Tracker (aaaaef55...) y Archivo Task Tracker (c470ead7...), antes inexistente en ambas — 15 tareas archivadas documentadas: 1 con evidencia real (v9.11.2), 10 autocontenidas en Notas, 4 marcadas explícitamente sin evidencia/pendientes de confirmar con el operador. Bug Tracker y Task Tracker activos revisados en su totalidad contra Changelog completo (activo+archivo) — 7 bugs y 5 tasks abiertas confirmadas vigentes, sin decisión arquitectónica que las vuelva obsoletas. Expandir en próxima sesión: revisar los 4 tasks sin evidencia con el operador directamente.
---
### v9.13.0 — Cierre Auditoría Dedup Archivo Tracker (6/6 grupos) + Fix vantage_id_rules.py Verificado + 2 Tickets Resueltos · 2026-08-01
Tipo: [FIX] [BUG] [DOC]
Alcance: Archivo Tracker (12 páginas, data source 674696fd-94b6-464a-ac1f-64b0cc917e15); Layer_1/scripts/vantage_id_rules.py (verificación, sin cambio de código en esta entrada); Bug Tracker (2 tickets: 3aa938be-fc42-818e-bd1a-e899bbd6d569, 3a5938be-fc42-81ef-b268-ff186307f6b3).
Contexto: Continuación directa de v9.12.1. El dry-run de Devin sobre el Archivo Tracker (6 grupos: GILSA, Scappino, Petco, Nike Artz Pedregal, Dolce & Gabbana, Bershka) había sido marcado INCOMPLETO al cierre de v9.12.1 — verificado en esa sesión que GILSA tenía 6 páginas reales vs 3 reportadas. Esta sesión completó la verificación independiente página-por-página de los 6 grupos completos, confirmando el mismo patrón de bug en múltiples grupos: Devin agrupaba por similitud de Rol/título en vez de por fingerprint real de posting (URL o hash), produciendo tanto falsos positivos (páginas de Puma, Paco Rabanne, Pull&Bear agrupadas bajo "Bershka" por compartir el título genérico "Escaparatista") como falsos negativos (Dolce & Gabbana: 6 páginas reales del mismo posting vs. 2 reportadas).
Cambios:
- Archivo Tracker — 12 páginas marcadas Archivar=YES tras verificación individual (fetch + comparación de userDefined:URL/hash) y APROBAR_WRITE explícito del operador por cada grupo: GILSA (3), Scappino (1), Petco (1), Nike Artz Pedregal (1), Dolce & Gabbana (5), Bershka (1). Cada escritura verificada por re-fetch inmediato (write-back verification), 12/12 PASS.
- Nike Artz Pedregal: operador confirmó regla de exclusión — vacantes de piso de venta bajo este holding son Hard Block (no se postulan ni se tratan como leads activos); 7+ variantes de título adicionales identificadas pero no tocadas en este ciclo, quedan pendientes de un batch de Hard Block separado si el operador lo autoriza.
- vantage_id_rules.py — fix de regex \d{2}→\d{1,2} (enviado en v9.12.1) verificado en esta sesión: python3 -m py_compile OK; dry-run de normalize_heading_ids.py sobre los 5 documentos (SP, Manual, Kernel, Career Canon, Aliases) reportó "Ningún heading mal formado detectado. Nomenclatura 100% canónica." — confirma que MANUAL:WEEKLY-FLOW-001 (heading de un dígito, antes falso positivo bajo \d{2}) ahora se reconoce correctamente.
- Bug Tracker 3aa938be...d569 ("Discrepancia de protección de estados terminales") — Status Abierto/En revisión → Resuelto. La decisión ya registrada en Solución (angostar layer_1_run.py FASE 4 a TERMINAL_ACTIONS={Archivar, Expirada}, ya vigente en producción según v9.11.7) se reafirma como cerrada; Next_Action → Documentar (pendiente reflejar en KERNEL:GATE-DECISION en sesión futura).
- Bug Tracker 3a5938be...f6b3 ("Dedup Caso 5 — Next_Action=Archivar no se ejecuta automáticamente") — ya Resuelto (solución: flujo manual vía checkbox adoptado en vez de auto_archive.py, decisión operador 2026-08-01); Next_Action → Documentar por consistencia.
- Changelog — tidy ejecutado en la misma pasada: entradas activas reducidas de 12 a 10 (esta entrada incluida), exceso movido a Archivo Changelog.
IDs afectados: ninguno — cambios de datos operativos (Archivo Tracker, Bug Tracker) y verificación de tooling, no de documentación fundacional. Census no requiere regeneración.
Write-Back Verification: 12/12 páginas del Archivo Tracker re-fetched individualmente tras cada escritura, mismatch=0. 2/2 tickets de Bug Tracker re-fetched, Status confirmado.
Pendiente (fuera de esta entrada):
- Hard Block formal para variantes de "Nike Artz Pedregal" (7+ páginas de piso de venta identificadas, sin tocar) — requiere batch separado con APROBAR_WRITE explícito.
- KERNEL:GATE-DECISION sin actualizar aún para reflejar TERMINAL_ACTIONS={Archivar, Expirada} como definición canónica documentada (código ya lo aplica desde v9.11.7).
- Reemplazo pendiente en Layer_1/scripts: normalize_heading_ids.py, apply_hyperlinks.py, vantage-tidy-opportunities-tracker.md (versiones limpiadas, acción local del operador, fuera de alcance de este Changelog).
- T3, T5, T7, D3/GAP-03, D4/B6 Caso 4, 7 IDs ALIASES:* faltantes en CENSUS_SPEC, 3 anchors PENDIENTE_ANCHOR — heredados, sin tocar esta sesión.
- Esquema del Archivo Tracker con propiedades duplicadas/corruptas (Next_Action 1, Score_Method faltante) — cosmético, no bloqueante.
Versión actualizada: 9.13.0 (CHANGELOG). El resto de los fundacionales permanece en v9.12.1 hasta vversions --sync.
---
> El histórico completo del CHANGELOG lo podrás encontrar en ARCHIVO CHANGELOG, en esta pagina de consulta continua solo encontrarás las últimas diez entradas para garantizar la operación y referencia del sistema.
---
