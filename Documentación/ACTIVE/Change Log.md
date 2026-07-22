# V | CHANGELOG

### v9.7.2 — Cierre de Huecos L0: Referencia Cruzada SCHEMA-004/005 → §3.3 + Alta de Dedup_Flag en Class B (SCHEMA-001) · 2026-07-22
Tipo: [DOC]
Alcance: Kernel §7 (KERNEL:SCHEMA-004, KERNEL:SCHEMA-005, KERNEL:SCHEMA-001).
Contexto: Cierre de los dos huecos L0 identificados en la revisión post-v9.7.0: (1) KERNEL:SCHEMA-004/-005 documentaban el contrato de Entity Format y el flujo de resolución sin ninguna referencia hacia KERNEL:DOCUMENTATION-003 (§3.3, L0 Runtime), pese a ser la contraparte de datos del mismo mecanismo; (2) Dedup_Flag figuraba como campo Class B protegido en KERNEL:CV-GOLDEN-RULES (§10) desde v9.5.4, pero nunca se había añadido a la enumeración canónica de Class B en KERNEL:SCHEMA-001 (§7) — inconsistencia señalada por SP:CONSISTENCY y arrastrada sin resolución desde v9.5.4/v9.6.8.
Cambios:
- KERNEL:SCHEMA-004 (§7): agregada línea de referencia cruzada hacia §3.3 (KERNEL:DOCUMENTATION-003 — L0 Runtime). Sin fusión ni reestructuración — decisión explícita del operador de mantener ambos IDs separados.
- KERNEL:SCHEMA-005 (§7): misma referencia cruzada agregada, aclarando que el Contrato de Resolución de 4 Pasos es la contraparte de datos del Runtime Build descrito en §3.3.
- KERNEL:SCHEMA-001 (§7): Dedup_Flag agregado a la enumeración Class B — System-Primary, alineando el schema con lo que KERNEL:CV-GOLDEN-RULES ya declaraba como campo protegido.
Write-Back Verification: no ejecutado en esta entrada — escritura autorizada explícitamente por el operador sin DRY RUN/APROBAR_WRITE previo ni re-fetch de confirmación posterior.
IDs afectados: ninguna alta/baja de ID canónico — ambos parches son adiciones de contenido bajo IDs ya existentes (KERNEL:SCHEMA-001, -004, -005). Census no requiere regeneración (KERNEL:CENSUS-SYNC Regla 1 no se dispara).
Pendiente (fuera de esta entrada): ninguno nuevo — los dos huecos L0 abiertos desde la revisión post-v9.7.0 quedan cerrados con esta entrada. El punto sobre la etiqueta "v8.9.0" en la tabla de Prefijos Autorizados sigue sin confirmarse contra el documento real (no encontrado en fetch en vivo, ver v9.7.1).
Versión actualizada: 9.7.2 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.7.0 hasta que el operador corra verify_versions.py --sync.
---
### v9.7.1 — Fix DB ID/COL ID de Bug Tracker en skill vantage-create-bug-task (drift no propagado desde v9.7.0) · 2026-07-22
Tipo: [FIX]
Alcance: vantage-create-bug-task/SKILL.md (local, fuera de Notion — no fundacional).
Contexto: Al revisar los pendientes derivados de la refactorización del Kernel (v9.7.0), se detectó que la corrección de DB ID/COL ID de Bug Tracker aplicada en KERNEL:TRACKER-SCHEMA-001 no se había propagado al skill que consume esos IDs directamente — el skill seguía con el par heredado (invertido) que el propio Kernel ya señalaba como incorrecto.
Cambios:
- vantage-create-bug-task/SKILL.md: corregido el par Bug Tracker de DB ID 36e938be-fc42-81f8-8c6f-000b6769ba03 / COL ID 36e938be-fc42-81bd-9e1f-dc360b3b45f5 (invertido) a DB ID 36e938be-fc42-81bd-9e1f-dc360b3b45f5 / COL ID 36e938be-fc42-81f8-8c6f-000b6769ba03, alineado con Kernel §8 (KERNEL:TRACKER-SCHEMA-001, v9.7.0). Tasks Tracker no requirió cambio.
- Nota de corrección agregada al propio skill documentando el origen del drift (refactor de Kernel v9.7.0 no propagado en el mismo ciclo).
Write-Back Verification: no aplica a Notion — cambio local, verificado por re-lectura directa del archivo tras la edición.
IDs afectados: ninguno en documentos fundacionales — corrección de referencia a un ID ya existente en el Kernel (KERNEL:TRACKER-SCHEMA-001), sin alta/baja de ID canónico. Census no requiere regeneración.
Pendiente (fuera de esta entrada): de la revisión de pendientes post-v9.7.0 quedan abiertos — fragmentación KERNEL:SCHEMA-004/-005 (sin referencia cruzada hacia §3.3) y ubicación canónica de Dedup_Flag (ausente de la lista Class B en KERNEL:SCHEMA-001 §7, pese a estar listado como campo protegido en KERNEL:CV-GOLDEN-RULES §10). El punto sobre una etiqueta de versión "v8.9.0" en la tabla de Prefijos Autorizados no se pudo confirmar contra el documento real — no encontrado en fetch en vivo.
Versión actualizada: 9.7.1 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.7.0 hasta que el operador corra verify_versions.py --sync.
---
### v9.7.0 — Refactor Estructural Completo del Kernel (Renumeración §1–§17, Limpieza de Residuos, Corrección DB/COL ID) · 2026-07-22
Tipo: [DOC] [FIX]
Alcance: V | KERNEL completo — TOC, headers §1–§17, KERNEL:TRIGGERS (§11), KERNEL:DATA-FLOW (§16), KERNEL:TRACKER-SCHEMA-001 (§8).
Contexto: Auditoría en sesión detectó numeración §N duplicada y desordenada (dos secciones en §8, dos en §9), un bloque de nota de trabajo interna pegado al final de DATA-FLOW, residuos de exportación (
, backslashes de escape, <empty-block/>) concentrados en TRIGGERS, y DB ID/COL ID de Bug Tracker invertidos en TRACKER-SCHEMA-001. Se intentó delegar la ejecución a Devin/Mistral vía Arena; ambos intentos fueron auditados y rechazados por fabricar old_str (formato de TOC inexistente, placeholders descriptivos en vez de valores reales, entrega final = concatenación sin cambios de los .md de trabajo). El operador ejecutó manualmente la versión final producida por Claude directamente en Notion.
Cambios:
- Renumeración completa: TOC y headers unificados en secuencia §1–§17 (incluye KERNEL:DOCUMENTATION como §3 con sub-IDs §3.1–§3.10, y KERNEL:GATE-DECISION como §9 con sub-IDs §9.1–§9.8). Elimina la duplicidad previa (§8/§9 repetidos) y la desalineación TOC↔cuerpo.
- Agrupación en 4 clústeres narrativos (metadato de TOC, no reordena contenido): I. FUNDAMENTO (§1–§6, incluye Dashboard/Checklist), II. DATOS, ESQUEMAS Y REGLAS (§7–§10), III. EJECUCIÓN (§11–§14), IV. INFRAESTRUCTURA DE CONTEXTO (§15–§17).
- Reordenamiento §12/§13: CANON-UPDATE antes de NAMING-CONVENTION (dependencia: Naming define el nombre de outputs que Canon-Update alimenta).
- Limpieza de residuos de exportación en TRIGGERS (§11): 
 → saltos de línea Markdown, backslashes de escape (\*\*, \-\-, \[\]) normalizados, <empty-block/> sueltos eliminados.
- Eliminación de bloque de cross-references huérfano al final de DATA-FLOW (§16) — nota de trabajo interna de una sesión de edición previa, sin ID canónico ni función de contrato; el Kernel no documenta su propio proceso de edición.
- Corrección DB ID/COL ID en KERNEL:TRACKER-SCHEMA-001 (§8): Bug Tracker tenía DB ID y COL ID invertidos. Valor corregido — DB ID: 36e938be-fc42-81bd-9e1f-dc360b3b45f5 · COL ID: 36e938be-fc42-81f8-8c6f-000b6769ba03. Tasks Tracker no requirió cambio.
Write-Back Verification: re-fetch en vivo del Kernel post-escritura (esta sesión) — TOC y cuerpo coinciden §1–§17 sin discrepancia; 
/backslash/<empty-block/> no detectados fuera del patrón Tipo:
Propósito: ya estándar en el resto del documento; bloque de cross-references confirmado ausente; DB ID/COL ID de Bug Tracker confirmados en el orden corregido.
IDs afectados: ninguna alta/baja de KERNEL:ID canónico — renumeración §N es posicional, no cambia namespace ni claves PREFIX:KEY. KERNEL:CENSUS-SYNC Regla 1 no se dispara. KERNEL:GATE-DECISION-006 (§9.6) ya estaba incorporado desde v9.6.5 — confirmado presente y correctamente indexado en esta renumeración.
Nota de honestidad estructural: el clúster I. FUNDAMENTO incluye KERNEL:DASHBOARD-CHECKLIST-ARCH (§6), que en la propuesta de clústeres original de esta sesión se había asignado a III. EJECUCIÓN. La versión final aplicada en Notion la ubica en Fundamento — confirmar con el operador si fue una decisión deliberada de la sesión o si amerita ticket de reconciliación.
Pendiente (fuera de esta entrada): decidir si el hallazgo de honestidad estructural anterior requiere corrección o si se documenta como decisión final.
Versión actualizada: 9.7.0 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.6.6 hasta que el operador corra verify_versions.py --sync.
---
### v9.6.9 — Reconciliación de Conteo 8→9 (VANTAGE Central Hub) + Extracción de TOC vigente · 2026-07-20
Tipo: [DOC]
Alcance: KERNEL (KERNEL:CENSUS-SYNC §9, KERNEL:DOCUMENTATION-TRANSVERSAL-001 §13).
Contexto: Auditoría del Kernel real detectó que la entrada v9.6.8 dejó KERNEL:CENSUS-SYNC a medio actualizar — ordinal "séptimo" sin corregir a "noveno" y lista de fuente de IDs con 7 nombres en vez de 8 (faltaba VANTAGE Central Hub). Además, KERNEL:DOCUMENTATION-TRANSVERSAL-001 tenía subsección narrativa para Navigation Brief pero ninguna equivalente para VANTAGE Central Hub, pese a que ambos son fundacionales desde el mismo lote de cambios.
Cambios:
- KERNEL:CENSUS-SYNC (§9): "séptimo... otros ocho... siete documentos" → "noveno... otros ocho... ocho documentos (agregando VANTAGE Central Hub)".
- KERNEL:DOCUMENTATION-TRANSVERSAL-001 (§13): nueva subsección "VANTAGE Central Hub — Documento Fundacional de Entrada", paralela en estructura a la de Navigation Brief.
- Extracción de TOC vigente del Kernel (§1–§15, con subsecciones) confirmada contra fetch en vivo — sin discrepancia frente a la tabla "TABLE OF CONTENT" embebida en el documento.
- Se descartó reconciliar el documento externo "PARCHES INDIVIDUALES PARA KERNEL" (solo contemplaba 7→8 con Brief únicamente) — superado por este parche directo.
Write-Back Verification: re-fetch de Kernel tras cada escritura — sin mismatch en ninguna de las dos.
IDs afectados: ninguna alta/baja de KERNEL:ID canónico — corrección de conteo y nueva subsección narrativa bajo secciones ya existentes. KERNEL:CENSUS-SYNC Regla 1 no se dispara.
Tickets logueados en esta sesión (Tasks Tracker):
- ALTO — Modificar generate_census.py: 131 IDs en spec, 121 resueltos, 10 sin link (KERNEL:OWNERSHIP-001/002, KERNEL:TRIGGER-001/002/005/006/007/009, KERNEL:GATE-DECISION-004, KERNEL:NAMING-CONVENTION), 2 huérfanos (KERNEL:HEALTH-CHECK-001.1, KERNEL:HEALTH-CHECK-003). [CENSUS-SYNC-R1] anotado.
- MEDIO — Desarrollar generate_id_inventory.py y apply_hyperlinks.py (porciones pendientes).
- MEDIO — Generar script de normalización de formato ID/título de sección-subsección a través de la suite documental.
Pendiente (fuera de esta entrada): los 3 tickets recién logueados; verify_versions.py real (Terminal) pendiente de extender a 9 documentos (heredado de v9.6.8); Manual §6 desalineado con --check eliminado (heredado, ticket ALTO ya logueado en v9.6.8).
Versión actualizada: 9.6.9 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.6.6 hasta que el operador corra verify_versions.py --sync.
---
### v9.6.8 — Normalización de Conteo de Fundacionales: 7→9 (BRIEF + VANTAGE Central Hub) · 2026-07-20
Tipo: [DOC]
Alcance: KERNEL (KERNEL:DOC-CONTRACT §7, KERNEL:CENSUS-SYNC §9, KERNEL:VERSION-CHECK-TOOL §10 ×3, KERNEL:HEALTH-CHECK §11 ×2 nuevas subsecciones, KERNEL:DOCUMENTATION-TRANSVERSAL-001 §13); SYSTEM PROMPT (SP:BOOTSTRAP-001 ×2, SP:SYNC-RULE, SP:CEDULA-DIGITAL, SP:VERSION-CHECK-TOOL).
Contexto: El operador confirmó en sesión que el conteo de documentos fundacionales pasa de 7 a 9, incorporando Navigation Brief (ya formalizado como 8vo en v9.6.5/v9.6.6) y VANTAGE Central Hub (página hub del workspace, versionable, con artáfactos de trabajo puntuales) como 9no. Se detectó y corrigió en la misma sesión un ID incorrecto para Navigation Brief circulando en un borrador externo (3a3938be-fc42-8089-93f2-f52dbd2dec6c, colisión de sufijo con Career Canon) — el ID real usado aquí es 3a3938be-fc42-8008-9e90-ec435c01f50d, confirmado por fetch directo del Census.
Cambios:
- KERNEL:DOC-CONTRACT (§7): tabla "Prefijos Autorizados" — agregadas filas BRIEF y VANTAGE.
- KERNEL:CENSUS-SYNC (§9): "séptimo... otros seis" → "séptimo... otros ocho"; lista de fuente de IDs ampliada con Navigation Brief.
- KERNEL:VERSION-CHECK-TOOL (§10): conteo 7→9 en Propósito, Output de Sync Mode (filas) y Flujo Canónico paso 3 (documentos restantes).
- KERNEL:HEALTH-CHECK (§11): 2 subsecciones nuevas — KERNEL:HEALTH-CHECK-001.1 (Auto-Archive como Housekeeping, citando Changelog v9.5.9/v9.5.6/v9.5.4, mecanismo no re-verificado contra script en esta sesión) y KERNEL:HEALTH-CHECK-003 (Skills de Mantenimiento del Tracker, tabla de 5 skills).
- KERNEL:DOCUMENTATION-TRANSVERSAL-001 (§13): nueva subsección Navigation Brief — Documento de Descubrimiento y Enrutamiento, con ID corregido.
- SYSTEM PROMPT: 6 ediciones de conteo 7→9 en SP:BOOTSTRAP-001 (×2), SP:SYNC-RULE (lista + cierre), SP:CEDULA-DIGITAL (UUIDs de Brief y Vantage agregados) y SP:VERSION-CHECK-TOOL.
Nota de honestidad estructural: un primer intento de escritura en KERNEL:HEALTH-CHECK-003 produjo una fila de tabla rota por un pipe (|) sin escapar en "V|CHANGELOG" — detectado en Write-Back Verification, no en el DRY RUN, y corregido en la misma sesión antes de este Changelog.
Write-Back Verification: re-fetch de KERNEL tras cada tanda de escritura (incluida la corrección de la tabla) — sin mismatch en el estado final. SYSTEM PROMPT verificado en escritura previa de esta misma sesión.
IDs afectados: ninguna alta/baja de KERNEL:ID canónico — son ediciones de conteo y contenido bajo secciones ya existentes; las 2 subsecciones nuevas de HEALTH-CHECK y la de Navigation Brief documentan mecanismos ya operativos (Changelog v9.5.9/v9.6.0/v9.6.6), no dan de alta identificadores nuevos del esquema PREFIX:KEY. KERNEL:CENSUS-SYNC Regla 1 no se dispara.
Pendiente (fuera de esta entrada, tickets logueados en sesión): (1) Dedup_Flag citado en HEALTH-CHECK-001.1 no está en la enumeración Class B de KERNEL:SCHEMA-001 — pendiente conciliar contra esquema real; (2) Manual §6 (MANUAL:SESSION-CYCLE-001) describe verify_versions.py con 3 flags activos incluyendo --check, ya eliminado del Kernel en v9.6.2 — desalineación mayor, ticket ALTO logueado en Tasks Tracker; (3) verify_versions.py real (Terminal) pendiente de extenderse a 9 documentos — no verificado en esta sesión, solo documentado como pendiente.
Versión actualizada: 9.6.8 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.6.6 hasta que el operador corra verify_versions.py --sync.
---
### v9.6.7 — Schema Consolidation: Bug Tracker ↔ Archivo Bug Tracker / Task Tracker ↔ Archivo Task Tracker · 2026-07-20
Tipo: [INFRA] [SCHEMA]
Alcance: Igualación de esquemas en cuatro databases Notion para garantizar integridad de datos en flujos de archivado automático (vantage-tidy-bug-task-tracker).
Cambios Ejecutados:
| Database | Acción | Propiedades |
| BUG TRACKER | Agregar | Creado, Etiquetas, Fecha_Resolución, Solución |
| ARCHIVO BUG TRACKER | Eliminar/Renombrar | ✗ Prioridad (number); Prioridad 1 → Prioridad; Nombre → Bug |
| TASK TRACKER | Agregar | Fecha_Cierre, Creado |
| ARCHIVO TASK TRACKER | Consolidar Status | 3 valores [Pendiente, En progreso, Hecho] |
IDs Afectados: Ninguno en documentos fundacionales — cambios de schema en data sources Notion únicamente
(collection://36e938be..., collection://9ef938be..., collection://aaaaef55..., collection://c470ead7...)
Impacto en Pipeline: vantage-tidy-bug-task-tracker ahora opera sobre esquemas idénticos activo↔archivo, 
eliminando riesgo de truncamiento o pérdida de datos en migración.
Versión Actualizada: v9.6.7 (solo CHANGELOG). Resto de fundacionales en v9.6.6 hasta versions --sync.
---
v9.6.6 — [2026-07-20] — ORQUESTACIÓN ESTRUCTURAL Y NAVEGACIÓN
1. Integración Documental (Navigation Brief)
- Alcance: Formalización del Navigation Brief (ID: 3a3938be-...) como 8vo documento fundacional del ecosistema VANTAGE.
- Gobernanza: Inclusión en SP:SYNC-RULE y KERNEL:CENSUS-SYNC. El documento queda sujeto a la Regla de Versión Única (bloqueante ante discrepancias de versión).
- Versión: Asignada v9.6.5 de forma sincronizada con el resto de la suite.
1. Reingeniería del Master Index
- Sustitución de S.S.O.T.: Eliminación del Bloque 3 (Census Embebido) por redundancia con V:ID-CENSUS.
- Estandarización:
- Bloque 1: Suite de 8 fundacionales, sincronizados contra SP:CEDULA-DIGITAL v9.6.5.
- Bloque 2: Actualización de trackers (Archivo Task, Bug, Changelog, Manifest, Ledger) con IDs de base de datos validados.
- Propósito: El documento queda consolidado exclusivamente como Índice de Descubrimiento de activos y rutas.
1. Normalización del ID Census
- Expansión: Registro de 11 nuevos identificadores (BRIEF:001 al BRIEF:011) para las secciones del Navigation Brief.
- Integridad: Verificación final mediante generate_census.py (v3.0) con resultado: 131/131 IDs resueltos, 0 huérfanos, 0 colisiones.
1. Actualizaciones del Sistema de Supervisión
- Scripting: Modificación profunda en verify_versions.py (DOC_KEYS extendido a 8 documentos + fallback BRIEF_FALLBACK_ID).
- VANTAGE HUB (Página Principal): Implementación de supervisión pasiva (v9.0.1). El sistema ahora reporta el status en -sync y -bootstrap sin disparar bloqueos (veredicto tolerante al formato de propiedad "Versión ").
- Cross-Referencing: Inyección masiva de hipervínculos normalizados en Kernel, Manual y System Prompt (apply_hyperlinks.py).
1. Auditoría de Cierre
- Verificación: verify_versions.py --sync reportó PASS en todos los documentos.
- Pending validation: Se da por resuelta la entrada del Changelog v9.6.3 ("Pending Validation") al completarse la integración aquí descrita.
### v9.6.5 — Marcado manual de duplicado (Multicont, jk rotativo Indeed) · 2026-07-20
Tipo: [NOTA]
Alcance: VANTAGE Tracker — 1 registro (39a938befc428135ba15eb001d21125e, "Supervisor Visual Merchandising", Multicont).
Contexto: vopport (dedup_opportunities.py) reportó 3 grupos de posibles duplicados. Verificación manual (fetch directo de URLs completas, no solo el prefijo visible en terminal) confirmó 1 caso real (Multicont, mismo Marca/Score/Fuente/Layer, creados con 2s de diferencia — patrón de rotación de jk de Indeed) y descartó los otros 2 (Link-Worldwide: roles/URLs distintas; Confidencial: los dos links pagead divergen en el payload de tracking tras el prefijo compartido, son anuncios distintos).
Decisión operativa: por instrucción explícita del operador, Dedup_Flag="Posible duplicado" se escribió directamente sobre el registro duplicado (39a938be...d21125e) fuera del flujo Python estándar — normalmente este campo es Class B, Python-only (KERNEL:CV-GOLDEN-RULES-002), y vantage-tidy-opportunities-tracker tiene prohibido escribirlo. Se documenta aquí como excepción puntual, no como cambio de regla: la restricción Python-only sigue vigente para el flujo automático.
Pendiente: el registro queda con Dedup_Flag + Next_Action=Archivar ya poblados — calza la condición compuesta de auto_archive.py, así que debería resolverse en el próximo ciclo de archivado automático o en la próxima corrida de vantage-tidy-opportunities-tracker.
IDs afectados: ninguno en documentos fundacionales — cambio de datos en el Tracker únicamente. Census no requiere regeneración.
Versión actualizada: 9.6.5 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.6.4 hasta que el operador corra verify_versions.py --sync.
---
### v9.6.4 — Sincronización Masiva de Hipervínculos y Corrección de ID Fantasma · 2026-07-20
Tipo: [DOC] [FIX]
Alcance: KERNEL, MANUAL, SYSTEM PROMPT.
Contexto: Aplicación quirúrgica de 116 hipervínculos (mapeo ID -> URL#anchor) para resolver el drift de navegación entre documentos fundacionales. Corrección del ID fantasma CAREER_CANON:OUTPUT-CONTRACT por el ID real CANON:OUTPUT-CONTRACT-001 en el Kernel.
Cambios:
- KERNEL: Reemplazo de ID fantasma en todas las apariciones. Hipervínculos aplicados en §1, §2, §3 y §9.
- MANUAL: Hipervínculos vinculados en §1, §2, §3 y §6.
- SYSTEM PROMPT: Hipervínculos vinculados en SP:BOOTSTRAP-001, SP:SYNC-RULE y KERNEL:CV-GOLDEN-RULES.
- Verificación: Post-write fetch confirma integridad de bloques y persistencia de links.
IDs afectados: CANON:OUTPUT-CONTRACT-001 (normalizado), CAREER_CANON:OUTPUT-CONTRACT (deprecado/eliminado).
Versión actualizada: v9.6.4 (Propagación iniciada).
### v9.6.3 — Brief de Navegación Documental
### 1. Datos del Registro
- Fecha: 2026-07-20
- Componente Modificado: Gobernanza documental y arquitectura de navegación (VANTAGE)
- Artefacto Creado / Actualizado: Navigation & Retrieval Contract (Versión v2.0)
- Tipo de Impacto: Normativo, Navegación y Runtime.
### 2. Evaluación de Impacto (Impact Assessment)
- ¿Qué documentos pueden verse afectados?
- Kernel (en términos de alineación de contratos de integridad).
- Manual (actualización de rutas de recuperación).
- System Prompt (incorporación de la obligatoriedad de navegación previa).
- ¿Qué contratos deben verificarse?
- Contrato de profundidad mínima de verificación (L0–L4).
- Matriz de dependencias cruzadas y obligatoriedad de Impact Assessment.
- ¿Es necesaria una actualización documental? Sí, formalización del Navigation Brief v2.0 como fuente única para enrutar consultas y modificaciones estructurales.
- ¿Debe regenerarse algún artefacto de Runtime? No aplica directamente a este cambio documental, salvo la validación posterior en el inventario de IDs si se cruzan referencias nuevas.
- ¿Debe ejecutarse una validación adicional? Sí, verificación cruzada de que los dominios críticos (Housekeeping, Core Assets, Discovery, Gate Logic, CV Pipeline) respondan inequívocamente al árbol de decisión documentado.
- ¿Se requiere sincronización (vsync_doc, vversions, vcensus)?vsync_docvversionsvcensus Pendiente de validación final en el siguiente ciclo de mantenimiento de infraestructura documental.
### 3. Acción Correctiva Ejecutada
1. Consolidación de los tres componentes estructurales faltantes (Mapa de dependencias por dominio, Contrato de profundidad de verificación y Matriz de referencias/dependencias).
1. Establecimiento del Navigation Decision Tree para eliminar ambigüedades en la recuperación de información.
1. Incorporación del Closure Gate (ninguna modificación estructural se marca como cerrada sin su respectiva evaluación de impacto).
### 4. Estado Final de la Validación
- Estado: Pending Validation (sujeto a la ejecución de la sincronización de versiones del sistema).
- Acción siguiente: Integración del identificador canónico en el ID Census y actualización del Master Index en la siguiente sesión de mantenimiento operativo.
### v9.6.2 — Fusión Check+Sync en verify_versions.py: verificación real post-escritura · 2026-07-19
Tipo: [DOC] [INFRA]
Alcance: Layer_1/scripts/verify_versions.py (local) + KERNEL:VERSION-CHECK-TOOL §23.
Contexto: El operador señaló que pedir --check después de --sync en cada cierre de sesión era gasto de tokens redundante si lo único que importa es que el sync haya quedado bien. Auditoría del código real confirmó la causa raíz: --check nunca emitió un string PASS (grep vacío en el script real) pese a que la skill de cierre lo exigía — mismatch documentación↔implementación preexistente. Además, --sync reportaba OK/FALLÓ basado solo en el status code del PATCH, sin releer el valor escrito — verificación aparente, no real.
Cambios:
- verify_versions.py: --sync ahora relee cada documento tras escribirlo y compara contra la versión maestro del Changelog. Reporta veredicto PASS/FAIL por documento y un veredicto final único ([VEREDICTO FINAL] PASS/FAIL), con sys.exit(1) si algún documento falla.
- verify_versions.py: flag --check eliminado del parser.
- KERNEL §23: sección "Modos de Operación" reescrita para reflejar el modo único de verificación-en-escritura; "Alias de invocación" actualizado a los dos flags vigentes.
- vantage-session-close/SKILL.md (local, fuera de Notion): Pasos 4 (--check) y 4.5 (--sync) fusionados en un único Paso 4, que exige el output de --sync y valida [VEREDICTO FINAL] PASS.
- vantage-session-open/SKILL.md (local, fuera de Notion): eliminado el Paso 3 (VERSION), que invocaba el flag --check ya retirado del parser. Pasos LOG/PENDING/SNAPSHOT/READY renumerados de 3–6 a 3–6 consecutivos. Agregada nota explícita: la verificación de versión de los 7 fundacionales queda reservada exclusivamente al cierre de sesión (--sync, vantage-session-close Paso 4) — la apertura de sesión ya no verifica ni escribe versión.
Validado en producción: el operador corrió vversions --sync tras el fix — 7/7 documentos PASS, veredicto final PASS (VANTAGE Tracker, 2026-07-19).
Write-Back Verification: re-fetch de Kernel §23 tras la escritura — sin mismatch.
IDs afectados: ninguna alta/baja de ID canónico — reescritura de contenido bajo KERNEL:VERSION-CHECK-TOOL, ID ya existente. Census no requiere regeneración.
Pendiente (fuera de esta entrada): ninguno nuevo identificado en esta sesión.
Versión actualizada: 9.6.2 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.6.1 hasta que el operador corra verify_versions.py --sync.
---
### v9.6.1 — Cierre Fase D: KERNEL:SKILL-ANNOUNCE-CONVENTION (ya resuelto) + Patch GATE-DECISION-003 punto 6 · 2026-07-20nTipo: [DOC]nAlcance: KERNEL:GATE-DECISION-003 punto 6 (reescritura de contenido bajo ID ya existente). KERNEL:SKILL-ANNOUNCE-CONVENTION — verificado sin cambios, ya estaba correcto desde v9.5.8.nContexto: Cierre de la Fase D, pendiente heredado desde Changelog v9.5.4/v9.5.7 ("patch a KERNEL:GATE-DECISION-003 punto 6, DRY RUN debe reconstruirse"), agrupado con R-12b bajo un solo ciclo de vantage-documentacion-transversal por tocar ambos el mismo documento fundacional.nR-12b (verificado, sin acción requerida): Al fetchear KERNEL:SKILL-ANNOUNCE-CONVENTION en vivo se confirmó que la tabla "Implementación actual" ya lista los 9 skills (incluyendo los 5 de housekeeping) desde v9.5.8. El reporte que motivó reabrir este ítem (vía Arena IA) describía un estado anterior a v9.5.8, ya superado. Se descarta de pendientes sin escritura.nPatch GATE-DECISION-003 punto 6 (ejecutado): La afirmación previa ("Gate_Decision=EXPIRED asignado por Python tras ≥2 runs con URL dead") se contrastó contra datos vivos y código real: 0/27 registros con Status=Expirada tienen Gate_Decision=EXPIRED poblado (VANTAGE Tracker CSV, 76 filas, 2026-07-19); no se encontró lógica de asignación en feed_processor.py, gate_logic.py, assign_next_action.py, auto_archive.py, profile_fit.py, ni en la porción inspeccionada de layer_1_run.py. El texto se corrigió: Status=Expirada (Class A) queda documentado como la señal operativa suficiente, asignada por operador, URL_GATE en 1er run, o el motor de misfit de perfil (profile_fit.py Fase 3.5). La regla "≥2 runs" se retira como afirmación de comportamiento actual y queda registrada como diseño no implementado, condicionado a rediseñar la protección terminal de Expirada.nWrite-Back Verification: pendiente — se ejecuta re-fetch de Kernel inmediatamente después de esta entrada, en la misma sesión.nIDs afectados: ninguno — reescritura de contenido bajo KERNEL:GATE-DECISION-003, ID ya existente. Census no requiere regeneración (KERNEL:CENSUS-SYNC Regla 1 no se dispara).nPendiente (fuera de esta entrada): ninguno nuevo — Fase D queda cerrada en su totalidad con esta entrada. Diagnóstico de causa raíz del drift de versión SP/Census (v9.5.7) sigue sin diagnosticar, no tocado aquí.nVersión actualizada: 9.6.1 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.6.0 hasta que el operador corra verify_versions.py --sync.nn---n
### v9.6.0 — Documentación Transversal: Skills de Mantenimiento en Manual (Kernel ya cubierto) · 2026-07-19
Tipo: [DOC]
Alcance: Manual §11 (MANUAL:HEALTHCHECK-001) — nuevo sub-nodo "Skills de Mantenimiento del Tracker (VANTAGE)"; Manual §6 (MANUAL:SESSION-CYCLE-001, Cierre) — atribución de la skill vantage-present-handoff en el paso 4 del cierre.
Contexto: Ejecutado vía vantage-documentacion-transversal tras detectar que las 5 skills instaladas en esta sesión (vantage-create-bug-task, vantage-present-handoff, vantage-tidy-bug-task-tracker, vantage-tidy-changelog, vantage-tidy-opportunities-tracker) ya estaban ancladas en KERNEL:SKILL-ANNOUNCE-CONVENTION (§3, desde v9.5.8) pero no tenían ninguna contraparte en el Manual — un operador leyendo el Manual de principio a fin no se enteraba de que existían ni cuándo usarlas.
Cambios:
- Manual §11: nuevo sub-nodo insertado justo después de "El V-ID-Census" y antes de §12 (Troubleshooting) — catálogo operativo de las 5 skills con su propósito y gate de Dry Run + APROBAR_WRITE cuando aplica.
- Manual §6, Cierre — /vantage-session-close, paso 4: frase insertada atribuyendo el resumen automático de hecho/pendiente a la skill vantage-present-handoff, aclarando que es invocable de forma independiente fuera de un cierre formal.
Write-Back Verification: re-fetch de Manual tras la escritura — ambos parches confirmados verbatim, sin mismatch.
Validación contra MANUAL:PATCH-QUALITY-001: los 5 filtros pasan — invisibilidad estructural (sin H2 nuevo, solo H3 bajo sección existente), continuidad de voz, progresión narrativa, diff mínimo (Parche 2 es una sola inserción de frase), coherencia transversal (sin contradicción con Kernel/SP).
IDs afectados: ninguna alta/baja de ID canónico — ambos parches son sub-contenido de secciones ya existentes (MANUAL:HEALTHCHECK-001, MANUAL:SESSION-CYCLE-001). Census no requiere regeneración (KERNEL:CENSUS-SYNC Regla 1 no se dispara).
Pendiente (fuera de esta entrada): ninguno nuevo identificado en esta sesión — pendientes heredados de v9.5.9 (Fase D del patch a KERNEL:GATE-DECISION-003; diagnóstico de causa raíz del drift de versión SP/Census señalado en v9.5.7) siguen abiertos, no tocados aquí.
Versión actualizada: 9.6.0 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.5.9 hasta que el operador corra verify_versions.py --sync.
---
---
### v9.5.9 — Auto-Archive Security Patch + Canonización Documental (Bug Crítico, CERRADO) · 2026-07-19
Tipo: [BUG] [SEC] [INFRA]
Descripción:
Implementación de parche de seguridad crítico en auto_archive.py para prevenir archivado accidental de registros con aplicaciones activas (Gate_Decision='APPLIED'). Adicionalmente, canonización de la documentación ACTIVE LOCAL como read-only para prevenir drift documental, estableciendo Notion como única fuente de verdad.
Cambios:
- auto_archive.py (Parche de Seguridad): Agregado check obligatorio Gate_Decision != 'APPLIED' en query_archive_candidates(). Si Gate_Decision == 'APPLIED', el registro se reporta como "PROTECTED_ACTIVE_APPLICATION" y NO se archiva bajo ninguna circunstancia. El dataclass ArchiveCandidate fue extendido para incluir el campo gate_decision.
- feed_processor.py (Normalización Dedup_Flag): Implementada función _set_dedup_flag_if_needed() que asigna siempre el valor literal "Posible duplicado" al campo Dedup_Flag cuando se detecta duplicado por hash, URL o fingerprint. Esta función se integra en dedup_cross_layer() y dedup_by_content_fingerprint(), asegurando que los 34 registros zombis detectados en la auditoría v9.5.6 puedan ser procesados por el flujo automático.
- auto_archive.py (Archivado Físico): Verificado y corregido para usar archived=True en la llamada a notion.pages.update(), garantizando archivado físico vía API de Notion (endpoint PATCH /v1/pages/{page_id}) en lugar de solo mover parent.
- vsync_doc.py v8.5.5 (Canonización Documental): Eliminada opción --direction local para prevenir drift documental. Documentación ACTIVE LOCAL ahora es read-only, Notion es única fuente de verdad. Auto mode solo permite notion→local, local→notion deshabilitado. Agregado warning inicial sobre política read-only.
- Documentación/ACTIVE/*.md (Bloqueo Físico): Aplicado chmod 444 a todos los archivos de documentación ACTIVE para prevenir edición directa local. Cambios deben hacerse en Notion, luego sincronizar hacia local.
Contexto:
- Consistencia con KERNEL:GATE-DECISION-007: El parche de seguridad mantiene consistencia con el mecanismo documentado, añadiendo protección cruzada contra APPLIED que no estaba explícita en el documento original.
- Canonización Documental: Respuesta a problema de drift documental entre local y Notion. Ahora existe una única fuente de verdad (Notion) y la documentación local es solo una caché read-only.
- Protección Total: Next_Action no se sobreescribe si ya está poblado (restricción mantenida).
- Validación: DRY RUN ejecutado exitosamente — 2 candidatos identificados (Promotwist SC y Zegna), ambos con Gate_Decision='BLOCKED' (aprobados para archivado). 0 registros con Gate_Decision='APPLIED' en riesgo de archivado accidental.
Criterios de aceptación:
| # | Criterio | Estado |
| --- | --- | --- |
| 1 | Check Gate_Decision != 'APPLIED' implementado en query_archive_candidates() | ✅ |
| 2 | Función _set_dedup_flag_if_needed() asigna "Posible duplicado" correctamente | ✅ |
| 3 | Archivado físico usa archived=True en API de Notion | ✅ |
| 4 | DRY RUN ejecutado sin errores, tabla de afectados generada | ✅ |
| 5 | 0 registros con Gate_Decision='APPLIED' en riesgo de archivado | ✅ |
| 6 | vsync_doc.py eliminó --direction local correctamente | ✅ |
| 7 | Archivos Documentación/ACTIVE/*.md bloqueados con chmod 444 | ✅ |
Archivos afectados:
- Layer_1/scripts/auto_archive.py (parche de seguridad + archivado físico)
- Layer_1/scripts/feed_processor.py (normalización Dedup_Flag)
- Layer_4/scripts/vsync_doc.py (canonización documental v8.5.5)
- Documentación/ACTIVE/*.md (bloqueo físico read-only)
IDs afectados: ninguna alta/baja de ID canónico — parche de seguridad bajo código existente, sin cambios en schema de Notion.
### v9.5.8 — KERNEL:SKILL-ANNOUNCE-CONVENTION (R-12b) · 2026-07-19
Tipo: [DOC]
Descripción:
Actualización de la tabla "Implementación actual" en KERNEL:SKILL-ANNOUNCE-CONVENTION para incluir los 5 skills de housekeeping (R-12b, pendiente heredado de v9.5.7). Los verbos se tomaron por lectura directa de los 5 archivos .skill reales subidos por el operador en esta sesión — no de una sesión anterior que había escrito una primera versión de esta misma entrada con verbos incorrectos (no verificados contra los archivos reales, ver Incidente abajo):
- vantage-create-bug-task (LOGGING TICKET.../TICKET LOGGED)
- vantage-present-handoff (HANDING OFF.../HANDOFF DELIVERED)
- vantage-tidy-changelog (TIDYING CHANGELOG.../CHANGELOG TIDIED)
- vantage-tidy-bug-task-tracker (TIDYING TRACKER.../TRACKER TIDIED)
- vantage-tidy-opportunities-tracker (TIDYING OPPORTUNITIES.../OPPORTUNITIES TIDIED)
Incidente de proceso (honestidad estructural): una sesión anterior ya había escrito esta tabla con verbos distintos a los reales (TICKETING/TICKET CREADO, LOGGING CHANGES/CHANGELOG ACTUALIZADO, SWEEPING TICKETS/TICKETS AL DÍA, DEDUPING TRACKER/TRACKER SINCRONIZADO), afirmando haberlos tomado "verbatim de las últimas versiones aprobadas" sin haber hecho grep/lectura directa de los .skill.md antes de proponerlos. El error persistió sin detectarse porque la sesión nunca recibió confirmación explícita de APROBAR_WRITE en el hilo compartido revisado, y por separado circuló un DRY RUN incompleto (bloques BEFORE/AFTER vacíos) hacia un revisor externo (Mistral). Detectado y corregido en esta sesión mediante fetch en vivo del Kernel + lectura directa de los 5 .skill reales adjuntos al chat.
Contexto:
- Regla de mantenimiento: Según KERNEL:SKILL-ANNOUNCE-CONVENTION, cualquier cambio en la convención debe listar el Kernel y cada .skill afectado en el mismo alcance.
- Consistencia: Todos los skills siguen el formato X-ING.../X-ED (o equivalente), alineado con la filosofía de evitar ambigüedad de alcance (ver Changelog v9.5.0–v9.5.1).
Write-Back Verification: re-fetch de Kernel tras la escritura de corrección — sin mismatch, los 5 verbos confirmados verbatim contra los .skill reales.
Criterios de aceptación:
| # | Criterio | Estado |
| --- | --- | --- |
| 1 | Texto en KERNEL:SKILL-ANNOUNCE-CONVENTION actualizado con los 9 skills. | ✅ |
| 2 | Mensajes de inicio/cierre de los nuevos skills coinciden con lo declarado en sus archivos .skill. | ✅ Verificado por lectura directa de los 5 .skill reales |
| 3 | Entrada en Changelog registrada con formato canónico. | ✅ |
Archivos afectados:
- V | KERNEL (sección KERNEL:SKILL-ANNOUNCE-CONVENTION)
- [V | CHANGELOG](https://app.notion.com/p/390938befc4280e7b429d7d730339353) (esta entrada, corregida)
IDs afectados: ninguna alta/baja de ID canónico — corrección de contenido bajo KERNEL:SKILL-ANNOUNCE-CONVENTION, ya existente. Census no requiere regeneración.
Pendiente (fuera de esta entrada): Fase D — patch a KERNEL:GATE-DECISION-003 punto 6 (DRY RUN debe reconstruirse); diagnóstico de la causa raíz del drift de versión SP/Census vs. Changelog señalado en v9.5.7 (sigue sin diagnosticar).
### v9.5.7 — 2026-07-19
Alcance: Cierre de Fase C de la auditoría de skills VANTAGE (R-06b, R-13, R-15, R-08b) + formalización de tag canónico en Kernel.
Kernel: KERNEL:CENSUS-SYNC §20, Regla 1 — formalizado el tag literal [CENSUS-SYNC-R1] como referencia canónica que cualquier skill debe citar textualmente al referenciar esta obligación, en vez de paráfrasis libres por skill (cierra R-13).
Infraestructura (Layer_1/, local): resolver_registry_v2.json — nueva entrada CHANGELOG_ARCHIVE en document_registry, resolviendo al UUID del Archivo Changelog. generate_census.py y normalize_heading_ids.py — VALID_PREFIXES extendida con CHANGELOG_ARCHIVE: en ambos scripts, cerrando el gap donde el Registry reconocía el alias pero el resto del pipeline lo hubiera rechazado como prefijo inválido (cierra R-06b).
Skills (vantage-tidy-changelog, vantage-tidy-bug-task-tracker, vantage-tidy-opportunities-tracker, vantage-create-bug-task): migración de los 2 UUIDs hardcodeados del Changelog a notación CHANGELOG:/CHANGELOG_ARCHIVE: en vantage-tidy-changelog (R-06b); tag [CENSUS-SYNC-R1] citado en vez de string libre en vantage-create-bug-task y vantage-tidy-bug-task-tracker (R-13); referencias posicionales ("Skill N") reemplazadas por nombres reales de archivo en los 5 skills — incluye una corrección de contenido real: la obligación de Regla 1 de CENSUS-SYNC se atribuía incorrectamente a vantage-tidy-changelog en vez de vantage-create-bug-task (R-15); manejo explícito de fallo parcial en operaciones multi-paso (append+edición en vantage-tidy-changelog, crear-copia+marcar-original en vantage-tidy-opportunities-tracker) — estado intermedio documentado como recuperable, sin reintentar el paso ya exitoso (R-08b).
Write-Back Verification: re-fetch de Kernel tras la escritura de §20 — sin mismatch, tag y línea de referencia cruzada confirmados verbatim.
Census: regenerado en Terminal por el operador — 120/120 IDs resueltos, 0 huérfanos, 0 sin link.
IDs afectados: ninguna alta de ID canónico nuevo — [CENSUS-SYNC-R1] es un tag de referencia cruzada dentro de Regla 1 existente, no un ID PREFIX:CLAVE nuevo del DOC-CONTRACT; el Census no lo indexa como entidad, comportamiento confirmado correcto en la regeneración de esta entrada.
Discrepancia detectada (SP:CONSISTENCY): al inicio de esta sesión, SYSTEM PROMPT e ID CENSUS reportaban v9.5.5 vía notion-fetch, un paso atrás de la versión real del Changelog (v9.5.6, ya escrita en la entrada anterior a esta). Causa no diagnosticada en esta sesión — posible verify_versions.py --sync no corrido tras v9.5.6, o drift de caché de fetch. Pendiente investigar antes de asumir que el próximo --sync corrige automáticamente el origen del drift, no solo el síntoma.
Pendiente (fuera de esta entrada): R-12b — actualizar KERNEL:SKILL-ANNOUNCE-CONVENTION §3 para incluir los 5 skills de housekeeping en la tabla "Implementación actual"; Fase D — patch a KERNEL:GATE-DECISION-003 punto 6 (DRY RUN debe reconstruirse, ya no vive en contexto activo); diagnóstico de la causa raíz del drift de versión SP/Census vs. Changelog señalado arriba.
Versión actualizada: 9.5.7 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.5.5/v9.5.6 (discrepancia ya señalada arriba) hasta que el operador corra verify_versions.py --sync.
---
### v9.5.6 — 2026-07-18
Alcance: Segunda vuelta de fixes técnicos ejecutados por Devin: Auto-Archivado (Bug Crítico, CERRADO), JD Null Audit (Bug Medio, causa raíz identificada, requiere task nuevo), Normalize URL (verificación de regresión, sin cambios).
Contexto: Continuidad de v9.5.5. El operador dio el prompt final a Devin con 3 objetivos, corrigiéndolo previamente para usar la condición real de Gate (KERNEL:GATE-DECISION-007) en vez de una condición inventada, separar dry-run de execute con gate de aprobación explícita, y evitar reimplementar el fix de Normalize URL ya resuelto en v9.5.3.
Cambios:
- Auto-Archivado (Bug Tracker, CERRADO): Devin confirmó uso correcto de NOTION_TOKEN desde el entorno (auto_archive.py línea 39). Dry-run confirmó los mismos 2 candidatos ya validados en v9.5.4 (Promotwist SC y Zegna, mismos Page IDs), sin candidatos nuevos ni inesperados. Aprobación explícita del operador (APROBAR_WRITE) antes de execute. Ejecución real: página mensual 2026-07 JULY creada, ambos registros archivados sin errores.
- JD Null Audit (Bug Medio, hallazgo estructural — NO cerrado): Devin descartó la ruta asumida en el prompt (Layer_2/wrappers/) y confirmó vía find que no existe un directorio de código Layer_2 separado — aclaración del operador: Layer 2 es una capa metodológica, no de código (búsquedas vía Perplexity+Comet en LinkedIn/Aggregators/Career Sites), y comparte el mismo núcleo operativo que Layer 1 (los scripts en Layer_1/scripts/). Esto es consistente con el schema real de Notion — tanto Bug Tracker como Tasks Tracker ya tenían "Layer 2" como opción de select en Componente antes de esta sesión, y el Tracker de vacantes tiene un campo layer con opciones L1/L2/L3. Causa raíz real: layer_1_run.py (validate_url_pre_ingestion()) y feed_processor.py (_first_nonempty()) solo consumen el campo JD ya vacío — el problema está en los prompts/flujos de discovery (A-Gemini, A-Grok, A-You.com para L1; Perplexity+Comet para L2), que no extraen el JD del HTML/resultado.
- Normalize URL (verificación de regresión, sin cambios de código): confirmado que el fix de v9.5.3 sigue vigente en feed_processor.py línea 238 — implementación real es path = parsed.path.rstrip("/").lower() or "/" (más completa que la descripción original de v9.5.3, que solo mencionaba .lower(); se deja constancia aquí para que el registro histórico sea exacto). 7/7 tests de regresión pasan, verificado contra datos reales de Notion (Electrónica Confidencial, hashes idénticos), sin duplicados fantasma detectados.
Task nuevo (Tasks Tracker): "Auditar scripts de discovery upstream (you.com/Grok/LinkedIn) — job_description llega NULL en algunos registros" (3a1938be-fc42-8172-bcbc-cd8e8cf2ec81), Componente: Layer 1, Next_Action: Definir, Prioridad: MEDIO, Status: Pendiente.
Write-Back Verification: Task nuevo confirmado por respuesta de la API de creación, sin mismatch. No se tocó ningún documento fundacional en esta entrada más allá de este Changelog.
IDs afectados: ninguno nuevo en los fundacionales — el hallazgo de Layer 2 como capa metodológica (no de código) queda documentado aquí pero no dispara alta en Kernel; queda como candidato a documentación transversal si el operador decide formalizarlo en KERNEL:ARCHITECTURE. Census no requiere regeneración.
Pendiente (fuera de esta entrada): ejecutar el task nuevo de auditoría de discovery upstream; decisión del operador sobre si formalizar la distinción L1/L2 (metodología, mismo núcleo de código) en el Kernel vía vantage-documentacion-transversal; pendientes heredados de v9.5.4 (cross_tracker_match.py Caso 3, decisión sobre Dedup_Flag en SCHEMA-001).
Versión actualizada: 9.5.6 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.5.5 hasta que el operador corra verify_versions.py --sync.
---
### v9.5.5 — 2026-07-18
Alcance: Fix de generate_census.py (Layer_1/scripts/, no fundacional) — alta en spec de 2 IDs huérfanos detectados en Kernel §9 y corrección de 1 ID mal declarado en spec (Bootstrap).
Contexto: Continuidad de v9.5.4. El re-run de vcensus tras el alta de KERNEL:GATE-DECISION-007/-008 (documentada en v9.5.4) reportó ambos IDs como huérfanos — existían en el Kernel real pero no en CENSUS_SPEC del script, confirmando que la Regla 2 de KERNEL:CENSUS-SYNC seguía pendiente de cierre. En el mismo diagnóstico se detectó un segundo defecto no relacionado: CENSUS_SPEC declaraba KERNEL:BOOTSTRAP-001, un ID que nunca existió con ese nombre exacto en el Kernel — el ID real es KERNEL:ARCHITECTURE-L0-BOOTSTRAP (§3), verificado por fetch en vivo antes de tocar el script.
Cambios:
- generate_census.py: agregadas al CENSUS_SPEC las filas KERNEL:GATE-DECISION-007 (§9.7 — Ejecución Automática de Archivado) y KERNEL:GATE-DECISION-008 (§9.8 — Capas de Evaluación de Gate: Técnica vs. Negocio), con nombres tomados verbatim del Kernel.
- generate_census.py: corregida la fila KERNEL:BOOTSTRAP-001 → KERNEL:ARCHITECTURE-L0-BOOTSTRAP (§3 L0-B), alineando el spec al ID real ya escrito en el Kernel — consistente con KERNEL:CENSUS-SYNC ("el Census audita a los documentos fuente, no al revés").
- Re-run de vcensus confirmado por el operador en Terminal: 120/120 IDs resueltos, 0 huérfanos, 0 sin link.
Write-Back Verification: no aplica a escritura en Notion — el fix es local (Layer_1/scripts/generate_census.py, fuera del alcance de sync bidireccional de vdoc). Verificación fue el propio output de vcensus en Terminal, confirmado por el operador en corridas sucesivas (detección de huérfanos → alta en spec → 0 huérfanos → detección de mismatch Bootstrap → corrección → 120/120 limpio).
IDs afectados: ninguno nuevo en Notion — los 2 IDs (KERNEL:GATE-DECISION-007/-008) ya habían sido dados de alta en el Kernel real en v9.5.4; esta entrada cierra su reflejo pendiente en el Census (KERNEL:CENSUS-SYNC Regla 2). KERNEL:ARCHITECTURE-L0-BOOTSTRAP tampoco es alta — ya existía en el Kernel desde v9.5.0.
Pendiente (fuera de esta entrada): los pendientes heredados de v9.5.4 (execute de auto_archive.py para Promotwist/Zegna; cross_tracker_match.py Caso 3; decisión sobre Dedup_Flag en SCHEMA-001) siguen abiertos, no tocados en esta sesión.
Versión actualizada: 9.5.5 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.5.3 hasta que el operador corra verify_versions.py --sync.
---
### v9.5.4 — 2026-07-18
Alcance: Cierre del ticket de Dedup (Bug Tracker 39b938befc4281efa1ccdd5d763bfdbf, pendiente solo execute), cierre del ticket de Suite de Tests Unitarios (Tasks Tracker 3a1938befc4281ca8ebcddf246425981 → Hecho), alta de 2 IDs nuevos en Kernel §9 (KERNEL:GATE-DECISION-007, KERNEL:GATE-DECISION-008).
Contexto: Continuidad de la sesión v9.5.3. Devin ejecutó los 2 prompts pendientes (Dedup completo + Suite de tests). Ambas respuestas fueron auditadas cruzando el ticket original y el código real antes de aceptarlas — no se dieron por buenas de palabra.
Cambios:
- Dedup (Bug Tracker, sigue Abierto — pendiente solo execute): Devin implementó y verificó los 4 frentes del prompt final: (1) auto_archive.py — dry-run confirmó 2 candidatos legítimos: Promotwist (control positivo) y Zegna (397938be-fc42-8124-8b10-def44d530da8, Next_Action='Archivar' y Dedup_Flag='Posible duplicado' verificados en vivo en Notion — corresponde al registro CSV público REVIEW_NEEDED, no al Inbound real ya cerrado). Confirmado sin cruce de lógica con cross_tracker_match.py (grep). (2) content_fingerprint()/dedup_by_content_fingerprint() resuelve Caso 4b (GILSA) — 3/3 tests pasando. (3) cross_tracker_match.py diseñado para Caso 3 (Zegna, cruce Inbound↔público) — pendiente implementación completa. (4) verify_dedup_fix.py confirmó contra Notion real que Casos 1 y 2 ya funcionaban sin cambios adicionales.
- Suite de Tests Unitarios (Tasks Tracker, CERRADO): 77 tests (16 dedup + 36 gate logic + 25 scoring), auditoría de código real confirmó nombres de función no inferidos (gate_logic(), evaluate_gate(), gate() en layer_1_run.py, calculate_score_v6(), get_score_band()). GILSA confirmado validando content_fingerprint() (línea 214 de test_dedup.py), no normalize_url() — README corregido tras señalamiento explícito.
- Kernel §9 (KERNEL:GATE-DECISION) — 2 altas: KERNEL:GATE-DECISION-007 (mecanismo de ejecución automática de archivado vía auto_archive.py, condición Next_Action='Archivar' + Dedup_Flag='Posible duplicado') y KERNEL:GATE-DECISION-008 (distinción arquitectónica confirmada: gate() capa técnica vs. gate_logic() capa de negocio/workflow — no son duplicación). Ambos anclan conocimiento que hasta esta sesión solo existía en chat/Censo.
Hallazgo pendiente de decisión del operador (no ejecutado en esta entrada): Dedup_Flag aparece en la lista de campos Class B protegidos de KERNEL:CV-GOLDEN-RULES-002, pero no en la lista canónica Class B de KERNEL:SCHEMA-001 — inconsistencia pre-existente, no causada por esta sesión, señalada por SP:CONSISTENCY.
Write-Back Verification: re-fetch de Kernel tras la escritura de §9 — sin mismatch, ambas secciones confirmadas verbatim.
IDs afectados: alta de KERNEL:GATE-DECISION-007 y KERNEL:GATE-DECISION-008 — dispara KERNEL:CENSUS-SYNC Regla 1, Census requiere regeneración antes de dar por cerrados los tickets asociados a estos IDs.
Pendiente (fuera de esta entrada): aprobar execute de auto_archive.py para los 2 candidatos confirmados (Promotwist, Zegna); dar de alta implementación completa de cross_tracker_match.py (Caso 3) como task separado; decisión del operador sobre el hallazgo de Dedup_Flag en SCHEMA-001; re-run de generate_census.py para reflejar los 2 IDs nuevos.
Versión actualizada: 9.5.4 (Kernel y Changelog). El resto de los fundacionales (Manual, Career Canon, System Prompt, Aliases, Census) permanece en v9.5.3 hasta que el operador corra verify_versions.py --sync.
---
### v9.5.3 — 2026-07-18
Alcance: 3 quick wins del handoff SESSION-2026-07-17-B: fix --bootstrap (SP:SYNC-RULE/KERNEL:CENSUS-SYNC, Census como 7º fundacional) y 2 fixes de dedup en feed_processor.py.
Contexto: SESSION-2026-07-18-A (Ledger). Auditoría de 3 quick wins (<5 iteraciones) propuestos en el handoff de la sesión anterior, verificados contra el código real (verify_versions.py, feed_processor.py, subidos por el operador) antes de tocar nada.
Cambios:
- Quick win #1 — Bug Tracker (registrado y Resuelto): get_priority_tickets() en verify_versions.py (Layer_1/scripts/, local) filtraba tickets ALTO/CRÍTICO solo por Prioridad, sin excluir Status terminal — causaba falsos positivos en el dump de --bootstrap (caso confirmado: ticket ya Resuelto seguía apareciendo). Fix: agregado filtro and con does_not_equal por Status, diferenciado por tracker vía dict closed_statuses_by_label (Bug: Resuelto · Task: Hecho/Completado — labels reales confirmados en main()). Verificado en producción: dump bajó de 10 a 8 tickets tras el patch, coincidiendo con el handoff.
- Quick win #2 — SP:SYNC-RULE + KERNEL:CENSUS-SYNC (Task, resuelto sin ticket formal — aclaración documental): discrepancia de conteo de documentos fundacionales (5/6/7) entre SP:SYNC-RULE (6), SP:VERSION-CHECK-TOOL (7) y el propio canon del operador ("Census NO es fundacional"). Resuelto por decisión explícita del operador: ID CENSUS pasa a ser el séptimo documento fundacional, sujeto a la misma Regla de Versión Única que los otros seis. Patch en SP:SYNC-RULE (bootstrap universal sigue recuperando solo SP+Census; la verificación de versión de los 7 fundacionales es un paso distinto, vinculado a vantage-session-open) y en KERNEL (KERNEL:CENSUS-SYNC §20, KERNEL:ARCHITECTURE-L4, KERNEL:VERSION-CHECK-TOOL §23 — este último corregido para reflejar el comportamiento real del código: DOC_KEYS en verify_versions.py ya incluía CENSUS y --sync ya ejecutaba 7 patches, no 6; la discrepancia era puramente documental, no de código).
- Quick win #3 — Bug Tracker (ticket original actualizado, NO cerrado): ticket 39b938be-fc42-81ef-a1cc-dd5d763bfdbf ("Dedup no detecta registros duplicados del Tracker", 5 casos documentados) recibía atención parcial — se mantiene Abierto. Dos de cinco causas resueltas en feed_processor.py: (a) normalize_url() no aplicaba .lower() al path (solo a netloc), rompiendo dedup entre URLs idénticas con distinta capitalización de path (Caso 1, Electrónica Confidencial) — fix de una línea, verificado en producción (MATCH: True); (b) dedup_cross_layer() filtraba title vía equals case-sensitive de la API de Notion, fallando en republicación cross-portal con distinta capitalización de título (Caso 2, Vinos La Naval) — fix: el filtro de Notion ya solo usa brand (ya canonizado por resolve_alias()) + ventana temporal; title se compara en Python normalizado post-fetch, con extracción robusta a runs multi-rich_text. Verificado en aislamiento con datos sintéticos (4 casos: match case-insensitive, espacios extra, no-falso-positivo, extracción multi-run) — no verificado aún contra Notion real, pendiente confirmación con caso vivo. Sin tocar: Caso 3 (falta cruce Inbound↔público, Zegna), Caso 4b (jk rotativo de Indeed, requiere fingerprint de contenido), y el bug transversal de Caso 5 (Next_Action=Archivar nunca se ejecuta automáticamente — probablemente el de mayor impacto acumulado, sigue enteramente abierto).
Write-Back Verification: re-fetch de SP, Kernel y del ticket de dedup tras cada escritura — sin mismatch en ninguno.
IDs afectados: ninguno nuevo — los tres cambios son reescritura de contenido bajo IDs ya existentes (SP:SYNC-RULE, KERNEL:CENSUS-SYNC, KERNEL:ARCHITECTURE-L4, KERNEL:VERSION-CHECK-TOOL) y patches de código local (no fundacional). Census no requiere regeneración.
Pendiente (fuera de esta entrada): verificar en producción real el fix de dedup cross-portal (Caso 2) con un caso vivo de republicación; los 7 tickets ALTO restantes del handoff (System Prompt inferencias, Git Infrastructure, hyperlinks cruzados en Kernel/Manual, inventario de referencias cruzadas, RT-1/STATIC BOOTLOADER, tests unitarios) permanecen abiertos, no tocados en esta sesión; Caso 3/4b/5 del ticket de dedup.
Versión actualizada: 9.5.3 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.5.2 hasta que el operador corra verify_versions.py --sync.
---
### v9.5.2 — 2026-07-18
Alcance: KERNEL §3 (alta de KERNEL:SKILL-ANNOUNCE-CONVENTION), Tasks Tracker + ARCHIVO TASK TRACKER (cierre de ticket Ledger huérfano), Bug Tracker (registro de bug nuevo: --bootstrap sin filtro de Status).
Cambios:
- KERNEL: nuevo nodo KERNEL:SKILL-ANNOUNCE-CONVENTION en §3, verificado por re-fetch sin mismatch (sesión 2026-07-17-B).
- Tasks Tracker: ticket "Revisar skill vantage-session-open — Ledger huérfano" cerrado (Status: Hecho), copia migrada a ARCHIVO TASK TRACKER (3a1938be-fc42-810d-ae99-f2666a61e565).
- Archivado real (API archived:true) del ticket original (3a0938be-fc42-813c-92de-cb9e9c86e1da) sigue PENDIENTE — falló por token inválido (401), resolver NOTION_TOKEN contra Layer_1/config/layer_1.env antes de reintentar.
- Bug Tracker (pendiente, no ejecutado en esta sesión): registrar bug "verify_versions.py --bootstrap no filtra Status resuelto/hecho" — detectado, no escrito aún.
Write-Back Verification: pendiente de confirmar en esta misma sesión tras el write.
IDs afectados: alta de KERNEL:SKILL-ANNOUNCE-CONVENTION.
Pendiente (fuera de esta entrada): cerrar Ledger de SESSION-2026-07-17-B (en curso); resolver NOTION_TOKEN antes de reintentar archivado; registrar bug de --bootstrap sin filtro Status.
Versión actualizada: 9.5.2 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.5.1 hasta que el operador corra verify_versions.py --sync.
---
### v9.5.1 — 2026-07-18
Alcance: Skills locales (fuera de Notion, no fundacionales — no dispara KERNEL:CENSUS-SYNC): vantage-session-open, vantage-session-close, vantage-documentacion-transversal, prompt-master, tailored-resume-generator.
Contexto: continuidad del trabajo de v9.5.0. Se detectó que el fix de convención de anuncio (X-ING → X-ED) diseñado y validado en la sesión de Notion previa (2026-07-18) nunca había persistido en el filesystem real del operador — los archivos montados seguían con artefactos de mojibake ([span_x]) y, en el caso de vantage-session-open/vantage-session-close, con un UUID de Session Ledger divergente (8d736032-eef9-4e6e-a05a-df8b8079ebff) del canónico (38324240-c686-47d0-8082-cee5e4409f88) — causa probable de que las filas del Ledger quedaran huérfanas sin cerrar.
Cambios:
- vantage-session-open: agregado paso 0 SESSION-OPENING... / cierre SESSION-OPENED: VANTAGE READY; UUID de Session Ledger corregido al canónico; artefactos de mojibake eliminados.
- vantage-session-close: agregado paso 0 CLOSING SESSION... / cierre SESSION CLOSED -> nuevo chat.; mismo fix de UUID y mojibake.
- vantage-documentacion-transversal: agregado anuncio BEGINNING DOCUMENTATION... / DOCUMENTATION FINISHED.
- prompt-master: agregado anuncio PROMPTING... / PROMPT FINISHED, con nota explícita de que va fuera del bloque de prompt copiable.
- tailored-resume-generator: sin cambios — ya traía el anuncio correcto.
Incidente de proceso (honestidad estructural): en esta misma sesión, antes de leer el handoff completo de la sesión de Notion, Claude entregó una primera versión de estos skills con un fix incompleto (solo limpieza de mojibake) presentado como definitivo. Se generó un Contrato de Sesión documentando la falla y reglas de refuerzo (R1–R5) para prevenir recurrencia — no se escribe a Notion, vive como artefacto de sesión entregado al operador.
Write-Back Verification: no aplica — cambios son locales, fuera de Notion.
IDs afectados: ninguno. Census no requiere regeneración.
Pendiente (fuera de esta entrada): dar de alta KERNEL:SKILL-ANNOUNCE-CONVENTION en el Kernel (nodo junto a KERNEL:ARCHITECTURE-L0-BOOTSTRAP) para formalizar la convención de anuncio como regla transversal — no ejecutado, pendiente de decisión del operador sobre alcance. Confirmar en sesión real que el operador subió los 5 .skill corregidos y que el ciclo open→close cierra la fila del Ledger sin quedar huérfana.
Versión actualizada: 9.5.1 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.5.0 hasta que el operador corra verify_versions.py --sync.
---
### v9.5.0 — 2026-07-17
Alcance: KERNEL:ARCHITECTURE-L0-BOOTSTRAP (§3) — convención de estado del Bootstrap y distinción de alcance frente al Session Ledger.
Contexto: el operador identificó un patrón de riesgo de 5 sesiones consecutivas sin fila nueva en Session Ledger al invocar /vantage-session-open. Diagnosticado en esta sesión: el Bootstrap universal (Project Instructions, copy fuente en SP:BOOTSTRAP-001) cierra con "VANTAGE: SISTEMA SINCRONIZADO" — casi idéntico al cierre real del skill vantage-session-open ("VANTAGE READY") — lo que hacía que el bootstrap universal (que corre en cada mensaje inicial de cualquier conversación del proyecto) se autodeclarara "sesión sincronizada" sin que el operador ni el modelo distinguieran ese cierre de la apertura formal del skill, que es la única que escribe al Ledger.
Cambios:
- KERNEL:ARCHITECTURE-L0-BOOTSTRAP (§3): agregada convención de estado X-ING → X-ED — el Bootstrap declara BOOTLOADING... al inicio y BOOTLOADED: DOCUMENTOS CARGADOS al cierre, nunca lenguaje de cierre de sesión formal. Agregado párrafo explícito de distinción de alcance: el Bootstrap es carga de contexto universal (cada mensaje inicial), el Session Ledger (KERNEL:SESSION-LEDGER, §21) es opt-in exclusivo del skill vantage-session-open. Diagrama de flujo actualizado con ambos estados y nota de Ledger condicional.
- SP:BOOTSTRAP-001 (System Prompt): copy operativo real corregido por el operador directamente en Project Instructions (fuera del alcance de escritura de este componente) — mismo cambio de convención de estado, mas la línea explícita de que el Bootstrap no escribe en Session Ledger.
Write-Back Verification: re-fetch de Kernel tras la escritura — sin mismatch.
IDs afectados: ninguno — ambos patches documentan contenido bajo IDs ya existentes (KERNEL:ARCHITECTURE-L0-BOOTSTRAP, SP:BOOTSTRAP-001). Census no requiere regeneración.
Pendiente (fuera de esta entrada): Task Tracker — "Revisar skill vantage-session-open — no ha abierto fila en Session Ledger en 5 sesiones continuas" permanece abierto hasta que el operador confirme, en una sesión real con el nuevo copy activo, que la distinción BOOTLOADED vs SESSION-OPENED resuelve el patrón de confusión. No cerrar el ticket solo con este Changelog.
Versión actualizada: 9.5.0 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en su versión previa hasta que el operador corra verify_versions.py --sync.
---
### v9.4.9 — 2026-07-17
Alcance: Esquema base de Bug/Tasks Tracker en SP (SP:SCHEMA) + regla de no-inferencia sobre mecanismos del sistema (SP:CONSISTENCY) + narrativa L0 ampliada en Kernel (KERNEL:ARCHITECTURE-L0) y Manual (§9.1, MANUAL:VANTAGE-RUNTIME-001) para incluir Version Check Tool/Census como parte de la capa L0.
Cambios:
- SP:SCHEMA (§7): agregado bloque "Esquema base" para Bug Tracker y Tasks Tracker (campos, tipos, opciones de select) como referencia estática para creación directa de páginas vía notion-create-pages sin fetch previo del data source. Nota explícita: Notion es la fuente de verdad, este bloque es caché de lectura que debe actualizarse en la misma sesión si el schema real cambia.
- SP:CONSISTENCY (§10): nuevo punto 5 — antes de escribir en un documento fundacional una afirmación sobre CÓMO funciona un mecanismo del sistema (skill, script, proceso), confirmar con el operador o la fuente real, nunca inferir por nombre o intención aparente. Originado por una corrección del operador en esta misma sesión: una primera redacción de SP:SCHEMA atribuyó erróneamente a vantage-documentacion-transversal un rol de monitoreo activo que el skill no tiene (es un skill de creación de contenido bajo demanda, no un proceso de vigilancia). Corregido en la misma sesión antes de este Changelog — no se registró como bug porque se resolvió de inmediato.
- KERNEL:ARCHITECTURE-L0: agregado párrafo + línea de diagrama declarando que Version Check Tool (vversions) y Census (vcensus) pertenecen a L0 (observabilidad ReadOnly), ya confirmado por el operador en sesión previa pero nunca escrito en el Kernel.
- MANUAL §9.1 (MANUAL:VANTAGE-RUNTIME-001): extendida la definición de Runtime con la misma pertenencia de vversions/vcensus a L0, sin duplicar el detalle operativo ya documentado en §9.2 y §6.
- V | ALIASES: reescritura completa a las 8 familias (Session Cycle → L0 Runtime → L1/L2 → Pipeline → L3 → L4 → Dashboard → CV → Dedup), aprobada en sesión previa (chat 71ea0fc5) pero nunca escrita — confirmado por fetch al inicio de esta sesión que el documento seguía en su estructura anterior de 9 secciones. Ejecutada ahora junto con alta de alias nuevo vsource (source ~/.zshrc, familia L0 Runtime) solicitado por el operador.
Write-Back Verification: re-fetch de SP y Kernel tras cada escritura — sin mismatch. Manual no re-verificado por fetch en esta entrada (patch aplicado vía update_content sin error reportado). ALIASES re-fetcheado post-escritura — 8 familias confirmadas, sin mismatch.
IDs afectados: ninguno — los cuatro patches documentan contenido bajo IDs ya existentes (SP:SCHEMA, SP:CONSISTENCY, KERNEL:ARCHITECTURE-L0, MANUAL:VANTAGE-RUNTIME-001). Census no requiere regeneración.
Pendiente (fuera de esta entrada): ninguno identificado — handoff de sesión anterior (chat 71ea0fc5) cerrado con esta entrada.
Versión actualizada: 9.4.9 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en su versión previa hasta que el operador corra verify_versions.py --sync.
---
### v9.4.8 — 2026-07-17
Alcance: Convención de nombres de alias de Terminal (Kernel §23, Manual §9.2, Aliases). Corrige drift entre alias reales en .zshrc (vversion, vcensus) y el contrato ya documentado en Kernel/Manual, y cierra el hueco de gramática que mezclaba subcomando posicional (vl1 tracker) con flags de guión (vversions --sync) sin regla explícita.
Cambios:
- Diagnosticado en Terminal (log del operador): vversion/vcensus existían como alias en .zshrc pero con comillas dobladas mal formadas (=''...'' en vez de '...'), causando ejecución silenciosa sin error ni output. Causa raíz identificada, fix entregado al operador para aplicar localmente (no fundacional — vive en .zshrc, fuera de Notion).
- KERNEL §23 (KERNEL:VERSION-CHECK-TOOL): agregado párrafo "Alias de invocación" declarando vversions (plural) como nombre corto canónico de verify_versions.py, con los tres flags sin modo default. Agregada subsección "Convención de nombres de alias (Terminal)" al cierre de la sección: v<dominio>[ <subcomando>] — subcomando posicional para modos mutuamente excluyentes, flags con guión para variaciones sobre un mismo motor; un alias nunca coexiste con un nombre casi-idéntico de un script renombrado.
- MANUAL §9.2 (MANUAL:VANTAGE-RUNTIME-001): catalogadas vversions y vcensus junto a los vl1 * ya documentados, con referencia cruzada a §6 (Ciclo de Sesión) y §11 (V-ID-Census) para no duplicar su contrato operativo completo.
- ALIASES (V | ALIASES, sesión previa a este Changelog): agregadas filas vversions y vcensus a la tabla Session Lifecycle (antes ausentes pese a que verify_versions.py --bootstrap/--check/--sync ya estaba documentado ahí sin alias corto asociado); nota de convención de nombres al pie de la sección.
Write-Back Verification: re-fetch de Kernel y Manual tras cada escritura — sin mismatch en ninguno de los dos.
IDs afectados: ninguno — los tres patches documentan un alias y una convención de nombres ya vigentes en el contrato, no dan de alta, retiran ni cambian de estado ningún ID canónico. Census no requiere regeneración (KERNEL:CENSUS-SYNC Regla 1 no se dispara).
Pendiente (fuera de esta entrada): aplicar el fix de comillas en .zshrc (local, operador) y retirar los alias huérfanos vpipeline/vpipeline-status propuestos en sesión previa y descartados por ser redundantes con vl1.
Versión actualizada: 9.4.8 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en su versión previa hasta que el operador corra verify_versions.py --sync.
---
### v9.4.7 — 2026-07-16
Alcance: Corrección de bugs en tooling local (generate_census.py, normalize_heading_ids.py — ambos en Layer_1/scripts/, no fundacionales) + cierre del pendiente de deeplink dejado abierto por v9.4.6.
Cambios:
- generate_census.py: corregido is_definition_block() — la condición de heading solo reconocía la nomenclatura "ID puro" (### PREFIX:KEY), no la nomenclatura real usada en TODOS los headings de sección top-level del Kernel (§N — PREFIX:KEY). Esto hacía que ninguna sección nueva pudiera detectarse como huérfana, sin importar cuántas veces se regenerara el Census. Agregado reconocimiento de ambas nomenclaturas vía regex §[\w.]+\s*[—-]\s*.
- Re-run de generate_census.py en Terminal: 117/117 IDs resueltos, 0 huérfanos, 0 sin link — confirma que KERNEL:DOCUMENTATION-TRANSVERSAL-001 (alta documentada en v9.4.6) ya se detecta correctamente, con deeplink de bloque real, reemplazando el placeholder de página usado como honesto en la entrada anterior.
- Census (394938be) regenerado y subido manualmente a Notion por el operador con el output fresco.
- Ambos scripts: corregida ruta de resolución de layer_1.env tras el traslado de ambos archivos de Layer_1/ a Layer_1/scripts/. La fórmula inicial (script_dir.parent.parent) sobre-corrigió, apuntando a VANTAGE/config/ en vez de Layer_1/config/ (ubicación real, confirmada vía find). Corregida a script_dir.parent.
- normalize_heading_ids.py (script nuevo, complemento de auditoría de generate_census.py): la primera versión usaba una heurística de clasificación de headings distinta e inconsistente con is_definition_block(), generando falsos positivos masivos (47 hallazgos, la mayoría patrones "ID: PREFIX:KEY" ya válidos y reconocidos por el Census). Corregido para usar exactamente la misma lógica de reconocimiento. Excluido explícitamente Change Log del barrido — sus headings narran historia y mencionan IDs de pasada, nunca los definen; normalizarlos arriesgaba corromper texto histórico (confirmado con un caso real de sugerencia de fix que mutilaba una entrada de v9.4.0).
- normalize_heading_ids.py: agregado retry con backoff (5 intentos, 2–10s) y timeout ampliado (30s → 60s) en fetch_blocks_recursive() — la primera corrida contra el Kernel completo (documento más grande) truncaba con ReadTimeoutError sin reintentar.
- Re-run de normalize_heading_ids.py (modo dry-run, sin escritura): 8 hallazgos reales, todos en Career Canon — mismo patrón en los 8 ("TÍTULO PREFIX:KEY", ID pegado al final sin separador): CANON:PROFILE-001, CANON:SKILLS-001, CANON:EXPERIENCE-001, CANON:ACHIEVEMENTS-001, CANON:KPIS-001, CANON:FACTS-001, CANON:POSITIONING-001, CANON:OUTPUT-CONTRACT-001. No aplicados aún.
Pendiente (no ejecutado en esta sesión):
- Aplicar (o corregir a mano) los 8 headings mal formados de Career Canon detectados por normalize_heading_ids.py. Impacto es cosmético/consistencia — estos 8 IDs ya resuelven bien vía fallback en el Census; además --apply reescribe rich_text plano y perdería cualquier anotación de estilo del heading original.
- Cerrar el ticket de Tasks Tracker sobre el timeout de normalize_heading_ids.py (ya resuelto por esta entrada) — pendiente de marcarlo Hecho.
IDs afectados: ninguno nuevo — KERNEL:DOCUMENTATION-TRANSVERSAL-001 ya fue dado de alta en v9.4.6; esta entrada resuelve su deeplink pendiente, no crea ni retira IDs.
Versión actualizada: 9.4.7 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en su versión previa hasta que el operador corra verify_versions.py --sync.
---
### v9.4.6 — 2026-07-16
Alcance: Alta de KERNEL:DOCUMENTATION-TRANSVERSAL-001 (Kernel §22) + cross-referencia en Manual §6 + fila nueva en Census. Cierra el pendiente dejado abierto por v9.4.5.
Cambios:
- KERNEL: nueva sección §22 — KERNEL:DOCUMENTATION-TRANSVERSAL-001, insertada entre KERNEL:SESSION-LEDGER (§21) y KERNEL:VERSION-CHECK-TOOL (renumerado de §22 a §23). Contrato de seis fases (Mapeo → DRY RUN → Inyección → Write-Back → Changelog/versión → Binary Gate), hereda los 5 filtros de MANUAL:PATCH-QUALITY-001 sin redefinirlos.
- MANUAL §6 ("Qué hacer si algo no cuadra"): nuevo bullet cruzando al ID nuevo, distinguiendo el caso "cambio sin reflejo documental" del drift de versión ya cubierto en esa misma lista.
- CENSUS: fila nueva bajo KERNEL para KERNEL:DOCUMENTATION-TRANSVERSAL-001 (§22); renumerada la fila de KERNEL:VERSION-CHECK-TOOL de "(anexo, post-§21)" a §23 para reflejar la inserción. Deeplink de bloque del ID nuevo queda pendiente de resolución exacta vía generate_census.py (Regla 2) — se registró con link a nivel de página como placeholder honesto, no aproximado como si fuera el anchor exacto.
Write-Back Verification: re-fetch de Kernel, Manual y Census tras cada escritura — sin mismatch en ninguno de los tres.
Disparo KERNEL:CENSUS-SYNC Regla 1: aplicado — alta de ID nuevo reflejada en Census en la misma sesión, antes de este Changelog.
Pendiente (no ejecutado en esta sesión):
- Re-run de generate_census.py en Terminal para resolver el deeplink de bloque exacto del ID nuevo (placeholder de página en uso mientras tanto).
- Instalación del SKILL.md corregido en la ruta local real (pendiente heredado de v9.4.5).
- Verificación de discrepancia entre esta sesión y el último Session Ledger cerrado (pendiente heredado de v9.4.5).
IDs afectados: alta de KERNEL:DOCUMENTATION-TRANSVERSAL-001.
### v9.4.5 — 2026-07-16
Alcance: Revisión y refinamiento del skill vantage-documentacion-transversal (trabajo local, sin escritura a Notion en esta sesión).
Cambios:
- Corrección de cita KERNEL:PATCH-QUALITY-001 → MANUAL:PATCH-QUALITY-001 en el skill.
- Reescritura del protocolo del skill: principio "nodo natural, no adendum"; gate de dos etapas (propuesta de nodo/IDs → autorización → DRY RUN de parches → APROBAR_WRITE → inyección → Write-Back → Changelog/versión → Binary Gate).
- Evaluación y descarte de propuesta externa de "sistema dual de IDs" (no existe en SP:ID-CONNECTORS-001; confundía UUID de Census con el de Changelog).
- Adopción parcial de checklist de validación pre-cierre y de gestión de parches pendientes vía Tasks Tracker (d2a65ca1-6a35-465d-bcff-b0d82dddd549).
- Agregado ejemplo práctico único (auto-referencial): la propia creación de este skill como caso guía.
Pendiente (no ejecutado en esta sesión):
- Alta de KERNEL:DOCUMENTATION-TRANSVERSAL-001 en el Technical Kernel real (nodo junto a KERNEL:CENSUS-SYNC/KERNEL:SESSION-LEDGER).
- Instalación del SKILL.md corregido en la ruta local real (/mnt/skills/user/).
- Verificación de discrepancia entre esta sesión y el último Session Ledger cerrado.
IDs afectados: ninguno en Notion todavía (pendiente KERNEL:DOCUMENTATION-TRANSVERSAL-001).
---
> El histórico completo del CHANGELOG lo podrás encontrar en ARCHIVO CHANGELOG, en esta pagina de consulta continua solo encontrarás las últimas diez entradas para garantizar la operación y referencia del sistema.

---
### v9.6.5 — Integración del Navigation Brief como Fundacional #8 y Actualización del Master Index
Tipo: [DOC] [INFRA]
Alcance: Integración completa del Navigation Brief como el 8vo documento fundacional en el ecosistema VANTAGE, actualización del Master Index y sincronización del ID Census.
Contexto:
El Navigation Brief (v2.0) fue formalizado como la Fuente Única de Verdad (SSOT) para la navegación documental en VANTAGE, resolviendo la necesidad de un contrato claro para enrutar consultas y modificaciones estructurales. Este cambio eleva el Brief a la categoría de documento fundacional, alineado con el Kernel, Manual, Career Canon, System Prompt, Aliases, Change Log y ID Census.
Cambios Ejecutados:
1. Navigation Brief:
- Inyección de 14 IDs de sección (BRIEF:001 a BRIEF:011) para alinear con el contrato de navegación y facilitar referencias cruzadas.
- Versión actualizada a v9.6.5 y marcada como Fundacional #8.
1. V-ID-CENSUS:
- Registro de las nuevas entradas del Navigation Brief en el census de IDs.
- Adición de la referencia al Brief en la tabla de IDs Frecuentes por Namespace (11 IDs, BRIEF:001 a BRIEF:011).
1. Kernel/Manual/System Prompt:
- Actualización de cross-refs para reflejar el nuevo estatus del Brief como 8vo fundacional (previamente 7).
- Adición de KERNEL:GATE-DECISION-006 (§9.6) en el Kernel, completando la lógica de gates.
1. Master Index:
- Sustitución completa de los Bloques 1, 2 y 3 para incluir el Navigation Brief como documento fundacional.
- Eliminación del Bloque 3 redundante (Census Embebido) y reestructuración para evitar duplicación con el V-ID-CENSUS.
- Actualización de métricas: 109 IDs normalizados, 0 stubs, 0 colisiones.
Validación:
- verify_versions.py --sync ejecutado: 7/7 documentos PASS, veredicto final PASS.
- vcensus regenerado: 109/109 IDs resueltos, 0 huérfanos.
- Re-fetch de Kernel, Manual, System Prompt y Master Index: sin mismatches, contenido actualizado verbatim.
IDs Afectados:
- Nuevos: BRIEF:001 a BRIEF:011 (Navigation Brief), KERNEL:GATE-DECISION-006 (Kernel §9.6).
- Modificados: KERNEL:DOC-CONTRACT (actualización de cross-refs a 8 fundacionales).
Pendientes Cerrados:
- Integración del Navigation Brief como fundacional.
- Sincronización del Master Index con el nuevo esquema (8 documentos).
- Adición de KERNEL:GATE-DECISION-006 en el Kernel.
Versión Actualizada: v9.6.5 (todos los documentos fundacionales sincronizados).
Estado: Completado/Validado.
