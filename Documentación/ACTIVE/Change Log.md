# V | CHANGELOG

Tipo: [AUDIT]
Alcance: Change Log (esta entrada); Script Library (hallazgo, sin escritura); GitHub issue #4 (comentado); index.html raíz (restaurado en repo).
Contexto: Cierre de los 5 pendientes operativos listados tras v9.21.4.
Cambios:
- T9 pasada 2 (Script Library) — marcada obsoleta. Verificación en vivo confirmó que la fila duplicada de git_sync.py ya fue diagnosticada y marcada correctamente (Estado=Deprecado, Acción=Archivar, Descripción explícita) en el batch M1 — el pendiente en v9.21.3 estaba desactualizado respecto al estado real de Notion. Sin escritura requerida.
- Duplicado git_sync.py — confirmado sin acción pendiente (ver punto anterior). Fila canónica (L4, Estado=Activo) intacta.
- GitHub issue #4 — comentado confirmando que auto_archive.py permanece deprecado en Archive/Legacy_Scripts/ como referencia histórica, sin eliminación (decisión del operador 2026-08-01, KERNEL:GATE-DECISION-007). Referencia: https://github.com/mauriciomeyran/VANTAGE/issues/4#issuecomment-5302203383
- index.html raíz — restaurado desde commit 7e92dcd (contenido: landing page GitHub Pages con documentación de skills MCP), aplicado en commit 2a3c7a1 sobre main. Decisión del operador tras confirmar propósito y ausencia de dependencias en el pipeline.
- vversions --sync (v9.21.4) — ya ejecutado y verificado [VEREDICTO FINAL] PASS en sesión previa.
IDs afectados: Ninguno (sin alta/baja de ID canónico — no dispara CENSUS-SYNC Regla 1).
Write-Back Verification: re-fetch de esta entrada tras la escritura.
Pendiente (fuera de esta entrada): Ninguno — ciclo de saneamiento v9.21.x cerrado en su totalidad.
---
Tipo: [AUDIT]
Alcance: Change Log (esta entrada); GitHub issues #8, #9 (comentados y cerrados).
Contexto: Cierre de los issues #8 y #9 dejados abiertos en v9.21.3. Se intentó remediar el incumplimiento del contrato PR-obligatorio (commits d3ba880 y 160337c fueron directo a main) creando branches retroactivas fix/d2-rework-archive-queue y fix/d5-real-descripcion-detector — descartado tras confirmar limitación estructural de Git: una branch creada desde main no puede mostrar diff contra main (GraphQL: "No commits between main and fix/..."). Se optó por registro de auditoría en vez de reescritura de main vía revert/reapply (evita alterar la secuencia limpia de main).
Cambios:
- Branches fix/d2-rework-archive-queue y fix/d5-real-descripcion-detector — creadas, confirmado sin diff, eliminadas de origin.
- GitHub issue #8 — comentario con referencia a Changelog v9.21.3, cerrado.
- GitHub issue #9 — comentario con referencia a Changelog v9.21.3, cerrado.
IDs afectados: Ninguno (sin alta/baja de ID canónico — no dispara CENSUS-SYNC Regla 1).
Write-Back Verification: re-fetch de esta entrada tras la escritura.
Pendiente (fuera de esta entrada): pasada 2 de T9 (Script Library, tras merge de #9 — issue cerrado, verificar si pasada 2 sigue aplicando o queda obsoleta); patch manual de la fila duplicada git_sync.py; aviso en GitHub Issue #4 (auto_archive.py); vversions --sync para propagar v9.21.4 al resto de los fundacionales (arrastra también v9.21.3 aún no propagada).
---
Tipo: [AUDIT]
Alcance: Change Log (entrada de cierre); Ledger (cierre de sesión); registros de trazabilidad ya aplicados en Kernel, Manual, Archivo Changelog, Script Library y Skill Library (G1/G2/T5b, write-back verificado en cada batch).
Contexto: Cierre del saneamiento estructural originado en la auditoría arena.ia 2026-08-13 (AUDIT_SANEAMIENTO_ESTRUCTURAL.md, handoffs/HANDOFF_MAESTRO_V3.md). Batches ejecutados con write-back verificado en cada paso.
Cambios (registro acumulado):
- F1 disco: Tier A 6/6 y B2 2/2 movidos a Archive/Legacy_Scripts/; Tier C retirado (backups .bak*, patches aplicados, dumps, manifest backup, .save); verificación: 80 assets activos, 0 gaps de Glosario. Conteo de assets posterior al cierre: skills/index.json como SSOT (28 skills).
- G1 documental: P1 (Kernel §04.3, máx. 10 correos); T2/P2 (Manual §12 + XREF + tabla env-vars, 3 sub-parches); T3/P4 (§04.4: vsync_doc_fast.py reformulado como variante deprecada en Archive + conteo de skills por referencia viva a index.json); T4 (anuncio vantage-housekeeping-archive en §03.5); T5 (fila en glosario §23.2); T6/C5 (dedupe extendido del Archivo Changelog: 3 copias verbatim de la migración Next_Action→select consolidadas bajo canonical v9.14.2; bloques Auditoría L0 intactos; copias sustituidas por notas [DEDUPE v9.21.x] — mover, nunca borrar).
- T5b/T5c: Glosario §22.1/22.1b anotado con "MOVIDO a Archive/Legacy_Scripts/" para los 6 one-shots; corrupción de auto-link introducida en T5b reparada en T5c (ver P-B).
- G2 datos: Script Library — extract_score_distribution.py y patch_vsync_doc.py → Deprecado/Archivar; 4 one-shots de Tier A confirmados SIN fila en Script Library (solo Glosario — sin deprecación posible); fila duplicada git_sync.py diagnosticada (creada en M1, Estado=Deprecado correcto, fila canónica git_sync.py (L4) intacta); T9 pasada 1: 10/10 filas con anotación corrupta limpiadas con clean_script_library_links.py (PASS verificado). Skill Library: alta vantage-housekeeping-archive (Activo/Keep).
- Cierre de v9.17.1: auto_archive.py se CONSERVA en Archive/Legacy_Scripts/ como referencia histórica (KERNEL:EVOLUTION §17) — pendiente explícito de esa entrada cerrado; queda pendiente avisar en GitHub Issue #4.
- Movimientos de archivo (política cero-borrados del operador): Video→Archive/Video, Outputs→Archive/Outputs (ancla CANON:DERIVED-OUTPUTS-ARCHIVE §13), .devin/skills→Archive/devin-skills. index.html raíz fue eliminado antes de adoptar la política cero-borrados — recuperable desde historial git (f5a0a1b) si se desea restaurar.
- Devin: D1/D3/D4/D6 aceptados con verificación del auditor (suite 141/142; fallo único preexistente en TestPriorityLogicCreatedTime, ticket aparte); D2-rework y D5-real abiertos como GitHub issues #8 y #9 con contrato endurecido (PR obligatorio).
Hallazgos registrados (sin remedio en este ciclo):
- [DRIFT V4] Doble identificador de Archivo Changelog: CHANGELOG_ARCHIVE y CHANGELOG_ARCHIVO coexisten en resolver_registry_v2.json; ID vivo operativo confirmado 3ba938be-fc42-8011-8947-fb4fa5d1f63f. Resolución pendiente de gobernanza de nomenclatura.
- Write silencioso en T3 (update_content reportó éxito sin persistir) — lección operativa: write-back con re-fetch en TODA escritura Notion.
- Auto-linker de Notion corrompe cualquier campo de texto libre que mencione nombre.ext (DB y documentos fundacionales) — mitigación activa: detector D6 en health_check.py + extensión a Descripción en issue #9.
IDs afectados: Ninguno (sin alta/baja de ID canónico — no dispara CENSUS-SYNC Regla 1).
Write-Back Verification: re-fetch de esta entrada en el Change Log tras la escritura (mismatch detiene la operación).
Pendiente (fuera de esta entrada): issues #8 y #9 (Devin) — D2-rework y D5-real remediados post-hoc vía commits directos a main (incumplimiento del contrato PR-obligatorio, branches/PRs retroactivos en curso); pasada 2 de T9 tras merge de #9; patch manual de la fila duplicada git_sync.py; aviso en GitHub Issue #4; vversions --sync para propagar la versión; posible restauración de index.html raíz (decisión del operador).
---
Tipo: [DOC]
Alcance:
- Career Canon (CANON:POSITIONING-001 a -004, 11.1–11.4)
Contexto: Brief del operador (BRIEF_Positioning_Modes_Enrichment.md) solicitaba enriquecer la sección CANON:POSITIONING con profundidad narrativa por modo (Propósito, Qué comunica, Evidencia priorizada, Cómo afecta el CV), sin tocar la arquitectura N1–N4 existente ni las anclas C01–C05. Auditoría previa del dry run del operador identificó 3 correcciones obligatorias antes de escribir: (1) header de N3 corregido a "Regional Brand Execution & Rollout" (nombre canónico exacto); (2) cada bloque N1–N4 ancla explícitamente a CANON:POSITIONING-005 (Anti-overselling/Anti-fragmentación); (3) N1 aclara que Levi's/Dockers, Palacio y Bisonte son evidencia secundaria de apoyo, ancla primaria inalterada en C01. Hallazgo adicional confirmado por el operador: el ancla canónica vigente de N4 es "C04/C05" (no solo C04) — se aplicó Opción B (coanclaje explícito, no silencioso) en vez de dejar la narrativa desmentir la mitad del ancla ya escrita en CANON:POSITIONING-004. Decisión de arquitectura ya resuelta por el operador: expansión directa in situ en 11.1–11.4, sin sub-sección nueva.
Cambios:
- CANON:POSITIONING-001 (11.1) — bloque enriquecido: Propósito, Qué comunica, Evidencia priorizada, Cómo afecta el CV, + anclaje a CANON:POSITIONING-005.
- CANON:POSITIONING-002 (11.2) — idem.
- CANON:POSITIONING-003 (11.3) — idem.
- CANON:POSITIONING-004 (11.4) — idem, con coanclaje explícito C04/C05 (Opción B); Regla de Desempate – JDs Híbridos preservada intacta inmediatamente después.
IDs afectados: Ninguno (extensión de contenido bajo nodos existentes, sin alta/baja de ID canónico — no dispara KERNEL:DOCUMENTATION-008 Regla 1).
Write-Back Verification: Career Canon re-fetched post-escritura — 4/4 bloques confirmados en posición correcta, sin mismatch. Regla de Desempate confirmada intacta tras el bloque de N4.
Pendiente (fuera de esta entrada):
- Tabla comparativa final (N1–N4) del dry run del operador no se insertó — pertenece conceptualmente al nodo padre CANON:POSITIONING (11), fuera del alcance aprobado de 11.1–11.4. Queda como decisión aparte para el operador.
- vversions --sync para propagar v9.21.2 al resto de los fundacionales.
---
Tipo: [DOC] [CODE] [INFRA]
Alcance:
- Local (skill): /skills/vantage-tidy-bug-task-tracker.skill — corrección de anchor
- Código: Layer_1/scripts/verify_versions.py, resolver_registry_v2.json, length_baseline.json (local, ARCHIVEROS)
- Kernel/Manual/System Prompt: SIN CAMBIOS (decisión explícita del operador)
Contexto: Dos cambios ya implementados en filesystem sin contraparte documental cerrada. (1) vantage-tidy-bug-task-tracker se expandió con contexto operativo detallado, manejo de cero candidatos, whitelisting explícito del campo Archivar y validación post-escritura — mapeo confirmó que el contrato operativo ya vigente en Manual §23.2 no requiere modificación. Se detectó una referencia a un ID obsoleto (KERNEL:CENSUS-SYNC) dentro del archivo local de la skill, renombrado a KERNEL:DOCUMENTATION-008 — corregido en este batch. (2) ARCHIVEROS (página-índice de bases de archivo) se integra a verify_versions.py --sync exclusivamente para housekeeping de version-tracking; el operador confirmó que no se eleva a documento fundacional pleno — el conteo oficial permanece en 10, sin cambios en SP:SYNC-RULE, KERNEL:DOCUMENTATION-007 ni MANUAL:SETUP.
Cambios:
- vantage-tidy-bug-task-tracker.skill (local) — anchor corregido: KERNEL:CENSUS-SYNC → KERNEL:DOCUMENTATION-008.
- verify_versions.py (local) — ARCHIVEROS agregado a DOC_KEYS con ARCHIVEROS_FALLBACK_ID = 3bb938befc4280cd8ea3fc8ba78f570c.
- resolver_registry_v2.json (local) — entrada ARCHIVEROS agregada a document_registry.
- length_baseline.json (local) — entrada ARCHIVEROS con baseline inicial.
IDs afectados: Ninguno (sin alta/baja de ID canónico en Kernel/Manual/SP — no dispara KERNEL:DOCUMENTATION-008 Regla 1).
Write-Back Verification: pendiente de confirmación tras escritura.
Pendiente (fuera de esta entrada): Ninguno — drift de versión previamente detectado ya resuelto vía vversions --sync (todos los fundacionales en v9.21.0).
---
Tipo: [CODE] [DOC]
Alcance:
- Código: Layer_1/scripts/layer_1_run.py, Layer_1/scripts/dedup_opportunities.py
- Kernel (KERNEL:ARCHITECTURE-L4)
- Manual (MANUAL:DATA-MANAGEMENT, MANUAL:SCRIPT-GLOSSARY-L1)
Contexto: El sistema ya contaba con dedup en tiempo real (ventana 30d, hash/URL/brand+title) para prevención de contaminación del Tracker al momento de ingesta. Este batch formaliza y automatiza el segundo mecanismo complementario: auditoria fuzzy post-ingesta con ventana configurable, cruce contra el Archivo Tracker y reglas anti-falsos positivos extensibles. Desde esta version corre automaticamente al finalizar layer_1_run.py mediante ENABLE_DEDUP_AUDIT=true (default), hereda --dry-run del pipeline principal y exporta metricas a dedup_metrics.json.
Cambios:
- layer_1_run.py — Fase final: subproceso de dedup_opportunities.py disparado automaticamente si ENABLE_DEDUP_AUDIT=true; timeout extendido a 10 min; herencia de --dry-run.
- dedup_opportunities.py — flags nuevos: --window-days N (default 60), --dry-run; variable NOTION_ARCHIVE_DATA_SOURCE_ID para el cruce contra Archivo Tracker; reglas ANTI_FALSE_POSITIVE_RULES extensibles.
- KERNEL:ARCHITECTURE-L4 — parrafo nuevo: "Mecanismos de Dedup — Distincion de Proposito", documenta coexistencia de dedup ingesta (30d) + auditoria post-ingesta (60d).
- MANUAL:DATA-MANAGEMENT — seccion "Dedup" extendida: dos mecanismos complementarios, automatizacion v9.21.0, resolucion via vantage-tidy-opportunities-tracker.
- MANUAL:SCRIPT-GLOSSARY-L1 — entradas layer_1_run.py y dedup_opportunities.py extendidas con tablas de flags y variables de entorno.
IDs afectados: Ninguno — extensiones de nodos existentes, sin alta/baja de ID canonico (no dispara KERNEL:CENSUS-SYNC Regla 1).
Validacion: DRY RUN sobre 117 registros del Tracker activo: 19 grupos detectados, 40 flags candidatos; metricas exportadas a dedup_metrics.json. Auditoria comparativa: 9.5x mas efectiva frente al baseline de 17 registros, 2 grupos y 1 flag.
Pendiente (fuera de esta entrada):
- vversions --sync para propagar v9.21.0 al resto de los fundacionales.
---
Tipo: [DOC]
Alcance:
- Manual (MANUAL:SKILL-GLOSSARY-HOUSEKEEPING, 23.2 — 2 filas)
- Manual (MANUAL:SKILL-GLOSSARY-AUDIT, 23.3 — 2 filas)
- Manual (MANUAL:SKILL-GLOSSARY-XREF, 23.5 — gap corregido)
- Kernel (KERNEL:DOCUMENTATION-005, 03.5 — lista de implementación)
Contexto: Brief del operador reportaba 4 acciones de optimización del catálogo de skills ya implementadas en filesystem sin contraparte documental formal: expansión de vantage-sync-assets de 4 a 6 dominios sincronizados (altas: Census Spec, Hyperlinks), alta de la meta-skill vantage-housekeeping-tracker (orquesta vantage-tidy-bug-task-tracker → vantage-tidy-opportunities-tracker → vantage-tidy-changelog en orden fijo), y deprecación de vantage-audit-navigation-brief (funcionalidad absorbida por vantage-documentacion-transversal-propuesta desde Fase 1 de mapeo de nodos) y extract-learnings (actividad post-mortem esporádica, no skill operativa recurrente). Se descartó agregar vantage-housekeeping-tracker a la tabla de gobernanza de KERNEL:DOCUMENTATION-010 — mismo criterio ya aplicado a vantage-sync-assets: es orquestador puro sin escritura directa, cada hija conserva su propio gate independiente.
Cambios:
- MANUAL:SKILL-GLOSSARY-HOUSEKEEPING (23.2) — fila vantage-sync-assets actualizada (4→6 dominios); fila nueva vantage-housekeeping-tracker.
- MANUAL:SKILL-GLOSSARY-AUDIT (23.3) — filas vantage-audit-navigation-brief y extract-learnings marcadas [DEPRECATED].
- MANUAL:SKILL-GLOSSARY-XREF (23.5) — gap de anuncio no especificado corregido: 6→5 skills (vantage-audit-navigation-brief removida por deprecación).
- KERNEL:DOCUMENTATION-005 (03.5) — alta de línea: vantage-housekeeping-tracker — HOUSEKEEPING TRACKERS… / TRACKERS HOUSEKEPT.
IDs afectados: Ninguno — todas las ediciones reutilizan IDs existentes (sin alta/baja de ID canónico, no dispara KERNEL:CENSUS-SYNC Regla 1).
Write-Back Verification: pendiente de confirmación en esta misma sesión (Fase 4).
Pendiente (fuera de esta entrada):
- Skill Library (Notion) — alta de fila vantage-housekeeping-tracker, actualización de descripción de vantage-sync-assets (delegar a vantage-sync-skill-library).
- vversions --sync para propagar v9.20.9 al resto de los fundacionales.
---
Tipo: [DOC]
Alcance:
- Kernel (KERNEL:DOCUMENTATION-005, 03.5 — lista de implementación)
- Kernel (KERNEL:DOCUMENTATION-010, 03.10 — tabla Skills de Gobernanza Documental)
- Kernel (KERNEL:DOCUMENTATION-013, 03.13 — nodo nuevo)
- Manual (MANUAL:SKILL-GLOSSARY-AUDIT, 23.3 — fila nueva)
Contexto: Brief del operador reportaba 4 skills modificadas/creadas sin contraparte documental formal (vantage-sync-assets, el split propuesta/implementación de documentación transversal con protocolo sandbox de economía de tokens, y vantage-skill-updater, nueva skill de meta-gobernanza). Mapeo confirmó que MANUAL §23.2 ya reflejaba correctamente vantage-sync-assets y el split propuesta/implementación (v9.20.4/v9.20.5) — el drift real estaba únicamente en KERNEL:DOCUMENTATION-005, que seguía listando una entrada única obsoleta ("vantage-documentacion-transversal") con banners incorrectos. Se descartó agregar vantage-sync-assets a la tabla de gobernanza de KERNEL:DOCUMENTATION-010 (decisión explícita del operador — esa tabla es exclusiva de skills que escriben Class A en trackers/changelog, no de orquestación de Library/Glossary). El patrón de protocolo sandbox (máx. 3 outputs visibles, procesos internos no renderizados) se identificó duplicado idénticamente en 4 skills sin ancla canónica — se formaliza como KERNEL:DOCUMENTATION-013 en vez de crear IDs separados por skill (KERNEL:SANDBOX-PROTOCOL, KERNEL:TOKEN-ECONOMY descartados por redundancia conceptual).
Cambios:
- KERNEL:DOCUMENTATION-005 (03.5) — lista "Implementación actual" corregida: entrada única obsoleta reemplazada por vantage-documentacion-transversal-propuesta y -implementacion (banners reales); altas de vantage-sync-assets y vantage-skill-updater.
- KERNEL:DOCUMENTATION-010 (03.10) — tabla de Skills de Gobernanza Documental: 2 filas nuevas (propuesta/implementacion), que faltaban listarse a sí mismas pese a ser el motor del protocolo que la sección define.
- KERNEL:DOCUMENTATION-013 (03.13) — nodo nuevo: "Protocolo Sandbox — Economía de Tokens Máxima", formaliza el patrón de máx. 3 outputs visibles compartido por 4 skills.
- MANUAL:SKILL-GLOSSARY-AUDIT (23.3) — fila nueva: vantage-skill-updater (Propósito/Trigger/Gate/Anuncio).
IDs afectados: 1 alta — KERNEL:DOCUMENTATION-013 (dispara KERNEL:CENSUS-SYNC Regla 1).
Write-Back Verification: Kernel y Manual re-fetched post-escritura — 4/4 nodos confirmados en posición correcta, sin mismatch.
Pendiente (fuera de esta entrada):
- vcensus para registrar KERNEL:DOCUMENTATION-013 en el Census (alta de ID canónico).
- vversions --sync para propagar v9.20.8 al resto de los fundacionales.
- Skill Library (Notion) — alta de fila vantage-skill-updater pendiente (fuera de alcance de esta entrada, delegar a vantage-sync-skill-library).
---
Tipo: [DOC]
Alcance:
- Kernel (KERNEL:DOCUMENTATION-008, 03.8)
- Manual (MANUAL:RUNTIME-002, 9.2)
- Manual (MANUAL:SCRIPT-GLOSSARY-L1, 22.1 — entrada generate_census.py)
Contexto: Brief v9.21 del operador reportaba corrección de CENSUS_SPEC (40 IDs huérfanos) y dos flags nuevos de generate_census.py. Verificación contra el script subido confirmó que ambos cambios (los 40 IDs y los flags --auto-fix-orphans/--sync-to-notion) ya estaban en producción — el ID CENSUS recuperado en bootload de esta sesión mostró 0 huérfanos, confirmando el estado. La propuesta de mapeo de Notebook Gemini para esta parte (KERNEL:DOCUMENTATION-008, sin alta de ID nuevo) se retomó; su sugerencia de un ID nuevo KERNEL:ASSETS-SYNC y reapertura de KERNEL:DOCUMENTATION-005 correspondía a Cambio 1 (vantage-sync-assets), ya cerrado en v9.20.5 con decisión explícita de no tocar Kernel — se descartó por ser una reapertura de una decisión ya tomada. Gap real detectado en revisión posterior con el operador: la entrada de generate_census.py en el Script Glossary (22.1) tampoco reflejaba los flags nuevos.
Cambios:
- KERNEL:DOCUMENTATION-008 (03.8) — regla 6 nueva: --auto-fix-orphans y --sync-to-notion como mecanismo de resolución de huérfanos del Census.
- MANUAL:RUNTIME-002 (9.2) — entrada vcensus extendida con descripción operativa de ambos flags.
- MANUAL:SCRIPT-GLOSSARY-L1 (22.1) — "Qué hace" de generate_census.py actualizado + 2 filas nuevas en tabla de Flags.
IDs afectados: Ninguno (extensión de nodos existentes, sin alta/baja de ID canónico — no dispara KERNEL:CENSUS-SYNC Regla 1).
Write-Back Verification: Kernel y Manual re-fetched post-escritura — 3/3 nodos confirmados en posición correcta, sin mismatch (re-fetch en vivo requerido en los tres casos por mismatch inicial de old_str contra contenido cacheado del upload local).
Pendiente (fuera de esta entrada):
- vversions --sync para propagar v9.20.7 al resto de los fundacionales.
---
Tipo: [DOC]
- Se restauró la versión de Kernel del 13 de agosto de 2026 (7:27 a.m.) para recuperar bloques críticos borrados en la versión LIVE (incluyendo contratos de ID canónicos, diagramas L1-L4, esquemas de Class A y la tabla de Tracker Schema).⚬	Se integraron los 3 diferenciales detectados del estado LIVE posterior:⚬	Actualización de L3 Passive Intake a un máximo de 10 correos por corrida.⚬	Actualización de Skills Distribution a 25 archivos .skill.⚬	Inserción del párrafo de consolidación prevista en KERNEL:GATE-DECISION-007 (vantage-housekeeping-archive).
- Se completó la integración de la Sección 23 (MANUAL:SKILL-GLOSSARY) con sus 5 subsecciones (23.1 a 23.5) que estaban ausentes en la versión restaurada del Manual. Se restituyó el bullet faltante en MANUAL:SESSION-CYCLE referenciando explícitamente a la Sección 23 para el catálogo de skills.
- Ejecución realizada mediante aprobar_write y actualización con el timestamp local solicitado de las 17:04.
---
Tipo: [DOC]
Alcance:
- Skill Library (Notion DB, alta de fila)
- Manual (MANUAL:SKILL-GLOSSARY-HOUSEKEEPING §23.2 — fila nueva)
- /mnt/skills/user/vantage-sync-script-library/SKILL.md (local, corrección)
- /mnt/skills/user/vantage-sync-assets/SKILL.md (local, instalación)
Contexto: Propuesta de documentación transversal para vantage-sync-assets, meta-skill que orquesta las 4 skills de sincronización existentes (Script Library, Skill Library, Script Glossary §22, Skill Glossary §23) en orden fijo Libraries→Glossaries. Mapeo inicial (Notebook Gemini) proponía altas de ID nuevas en Kernel (KERNEL:ASSETS-SYNC, extensión de KERNEL:DOCUMENTATION-005/-010, trigger en SP:TRIGGERS) — descartadas tras verificación contra BRIEF:CONSULTATION-002 (catálogo de skills es responsabilidad del Manual, no del Kernel) y contra el contrato ya confirmado de vantage-sync-skill-library (que ya cita KERNEL:DOCUMENTATION-005 correctamente). Auditoría cruzada expuso que vantage-sync-script-library citaba un anchor inexistente (KERNEL:SKILL-ANNOUNCE-CONVENTION) para la misma convención — corregido en este batch.
Cambios:
- Skill Library (Notion) — alta de fila vantage-sync-assets (Estado: Activo, Ruta: /mnt/skills/user/vantage-sync-assets/SKILL.md, Dependencias: las 4 skills hijas).
- MANUAL:SKILL-GLOSSARY-HOUSEKEEPING (23.2) — fila nueva insertada tras vantage-sync-skill-library, antes de vantage-sync-census-spec.
- vantage-sync-script-library/SKILL.md (local) — anchor corregido: KERNEL:SKILL-ANNOUNCE-CONVENTION → KERNEL:DOCUMENTATION-005.
- vantage-sync-assets/SKILL.md (local) — instalado, con nota de alcance frente a L4 (vdoc/vsync_doc.py) añadida en Reglas de oro (metadatos de inventario vs. contenido documental — dominios distintos).
IDs afectados: Ninguno (sin alta/baja de KERNEL:ID/MANUAL:ID canónico — fila de tabla existente + archivo local).
Write-Back Verification: Skill Library re-fetched post-escritura (fila confirmada). Manual re-fetched post-escritura — fila vantage-sync-assets confirmada en posición correcta dentro de §23.2. Archivos locales verificados por lectura directa post-escritura.
Pendiente (fuera de esta entrada):
- vversions --sync para propagar v9.20.5 al resto de los fundacionales.
- Gap heredado sin tocar: campo Capa de Skill Library sigue sin opción aplicable para meta-skills de housekeeping (dejado vacío en la fila nueva, consistente con el gap ya documentado en MANUAL:SKILL-GLOSSARY-XREF 23.5).
---
Tipo: [DOC]
Alcance:
- Manual (MANUAL:SKILL-GLOSSARY §23 y subsecciones 23.1–23.5)
- Navigation Brief (BRIEF:AUTHORITY-MATRIX §02, BRIEF:CONSULTATION-002 §04.2)
- Census Spec (Layer_1/scripts/generate_census.py, local)
Contexto: Alta de §23 MANUAL:SKILL-GLOSSARY — catálogo operativo de las 19 skills de Claude (/mnt/skills/user/), contraparte de MANUAL:SCRIPT-GLOSSARY (§22) aplicada a skills en vez de scripts. Contrato validado contra los 6 filtros de MANUAL:PATCH-QUALITY-001. Escritura verificada en vivo vía notion-fetch en esta sesión (Manual y Brief re-fetched, contenido confirmado byte-exacto contra el patch propuesto).
Cambios:
- MANUAL:SKILL-GLOSSARY (23) — nodo nuevo, glosario de skills en 4 categorías (Core, Housekeeping, Audit, Style) + XREF de gaps abiertos.
- MANUAL:SESSION-CYCLE — bullet nuevo referenciando §23.
- BRIEF:AUTHORITY-MATRIX — fila nueva: Gobernanza de Skills IA → Manual §23.
- BRIEF:CONSULTATION-002 — bullet nuevo: catálogo de skills.
- CENSUS_SPEC (local) — alta de 6 IDs: MANUAL:SKILL-GLOSSARY, -CORE, -HOUSEKEEPING, -AUDIT, -STYLE, -XREF.
IDs afectados: 6 altas (ver Census Spec arriba).
Write-Back Verification: Manual y Navigation Brief re-fetched post-escritura — 4 nodos confirmados en posición correcta. vcensus re-ejecutado post-alta en CENSUS_SPEC: 196/196 IDs resueltos, 0 huérfanos. ID CENSUS (Notion) actualizado por el operador con el nuevo export.
Pendiente (fuera de esta entrada):
- vversions --sync para propagar v9.20.4 al resto de los fundacionales.
- Gaps documentados en MANUAL:SKILL-GLOSSARY-XREF (23.5): anuncio no especificado en 6 skills (vantage-cv-a, vantage-cv-b, vantage-qa, vantage-sync-script-glossary, vantage-audit-navigation-brief, cierre de vantage-documentacion-transversal-propuesta); campo Capa null en 24/25 filas de Skill Library.
---
Tipo: [DOC]
Alcance:
- Kernel (KERNEL:TRIGGER-002, 11.2)
- Manual (MANUAL:SCRIPT-GLOSSARY-L1-MODULES — priority_logic.py; MANUAL:SCRIPT-GLOSSARY-L1 — backfill_class_a.py)
Contexto: Cierre documental del fix de código v9.20.2 (created_time leído desde raíz del objeto Notion, no desde properties; duplicación de txt() sin fix de rich_text en backfill_class_a.py). Este batch deja precedente narrativo en Kernel/Manual para que la próxima función que asuma la forma del objeto Notion sin verificar schema tenga ancla de referencia.
Cambios:
- KERNEL:TRIGGER-002 (11.2) — nota de precedente: created_time vive en raíz del objeto página, no en properties; mismo patrón de riesgo que motivó el fix de txt()/rich_text (v9.20.1).
- MANUAL:SCRIPT-GLOSSARY-L1-MODULES (priority_logic.py) — aclaración: txt() existe duplicada en 3 archivos (layer_1_run.py, priority_logic.py, backfill_class_a.py); consolidación evaluada y descartada por riesgo de import circular.
- MANUAL:SCRIPT-GLOSSARY-L1 (backfill_class_a.py) — nota sobre hack de parsing local para propiedades top-level, con referencia cruzada a KERNEL:TRIGGER-002 (nodo aportado por Gemini, validado).
IDs afectados: Ninguno (extensión de nodos existentes).
Write-Back Verification: 3 parches inyectados y confirmados en sesión previa (KERNEL + MANUAL re-fetched byte-exactos contra v9.20.1 vivo).
Pendiente (fuera de esta entrada):
- vversions --sync para propagar v9.20.3 al resto de los fundacionales.
---
Tipo: [FIX] [CODE]
Alcance:
- Código: Layer_1/scripts/priority_logic.py (infer_prioridad()), Layer_1/scripts/layer_1_run.py (caller Fase 3.6), Layer_1/scripts/backfill_class_a.py (txt())
Contexto: Verificación post-v9.20.1 detectó que infer_prioridad() nunca calculaba Urgencia por antigüedad real: leía props.get("created_time"), pero ese campo vive en la raíz del objeto de página de Notion (item["created_time"]), no dentro de properties. Todas las vacantes caían en el fallback urgencia="MEDIO", razon="sin_fecha_creacion" sin importar su antigüedad real. Auditoría de verificación de ese fix reveló además una tercera copia independiente de txt() en backfill_class_a.py sin el fix de concatenación de rich_text aplicado en v9.20.1 (Bug Tracker 3bb938be-fc42-8186-a551-d19cc3691d86).
Cambios:
- priority_logic.py::infer_prioridad() — firma cambiada de (props, today) a (item, today); lee item.get("created_time") en vez de props.get("created_time").
- layer_1_run.py y backfill_class_a.py — callers actualizados para pasar item completo.
- backfill_class_a.py::txt() — concatena todos los chunks de rich_text/title, igual que las otras dos instancias.
- test_gate_logic.py — 7 tests nuevos (TestPriorityLogicCreatedTime) + 5 tests nuevos (TestBackfillTxtConcatenation).
Validación: Corrida real de vl1 post-fix — 9 cambios de Prioridad reflejando antigüedad real (antes: fallback fijo a MEDIO). Fix de backfill_class_a.py::txt() verificado línea por línea contra el archivo real, no solo por resumen del agente.
IDs afectados: Ninguno (fix de código, sin alta/baja de ID canónico).
Write-Back Verification: Bug Tracker 3bb938be-fc42-8186-a551-d19cc3691d86 — Resuelto, verificado.
Pendiente (fuera de esta entrada):
- Evaluar ticket de Task Tracker para consolidar txt() en módulo compartido (notion_helpers.py) — no viable en este ciclo por hack de imports en backfill_class_a.py (ver Bug Tracker para detalle).
- vversions --sync para propagar v9.20.2 al resto de los fundacionales.
---
Tipo: [FIX] [CODE]
Alcance:
- Código: Layer_1/scripts/layer_1_run.py (txt(), FASE 2 URL Gate línea ~693)
- Kernel (KERNEL:GATE-DECISION-010 §09.10 — referencia de protección de terminalidad)
Contexto:
Operador verificó manualmente 17 vacantes activas (JD completo, accesibles, reciben postulaciones) marcándolas Status=Target, Fetch=Accesible, Gate_Decision=CREATE. Re-ejecución de vl1 revirtió las 17 a Bloqueado/Expirada/Archivar. Causa raíz aislada con evidencia directa de la API (no CSV, no hipótesis): txt() leía únicamente rich_text[0]["plain_text"]; la API de Notion fragmenta contenido largo en múltiples chunks (confirmado: 21 chunks para un JD de ENCANTO MÉXICO, chunk[0] de 60 caracteres frente a ~1750+ reales). Esto rompía JD_ALREADY_EXISTS (len(jd_clean) > 100), forzando la rama de HEAD en vivo contra agregadores con anti-scraping activo (403 reproducido en Indeed/OCC/LVMH), sin protección de terminalidad para Status=Target.
Cambios:
- layer_1_run.py::txt() — concatena todos los chunks de rich_text y title en vez de leer solo [0].
- layer_1_run.py línea ~693 — nueva protección: Status=Target con JD concatenado >100 chars se salta el URL Gate (defensa en profundidad, además del fix de raíz).
- test_gate_logic.py — nueva clase TestRichTextConcatenation, 7 tests, 7/7 passed.
Validación: DRY_RUN sobre las 17 filas afectadas — 0/17 rechazos (antes: 17/17 reversiones erróneas).
IDs afectados: Ninguno (fix de código, sin alta/baja de ID canónico).
Write-Back Verification: Bug Tracker (ticket 3bb938be-fc42-813d-a253-ca2097f33957) creado y verificado en esta sesión.
Pendiente (fuera de esta entrada):
- Corrección manual/batch de las 17 filas ya dañadas en Notion (operación de datos separada, requiere DRY RUN + APROBAR_WRITE aparte).
- vversions --sync para propagar v9.20.1 al resto de los fundacionales.
---
Tipo: [FIX] [CODE] [DOC]
Alcance:
- Código: Layer_1/scripts/layer_1_run.py (validate_url_pre_ingestion)
- Kernel (KERNEL:GATE-DECISION-002 §09.2, KERNEL:GATE-DECISION-011 §09.11)
- Manual (MANUAL:HOW-IT-WORKS §02, MANUAL:SCHEMA-FIELD-REF §21)
- Aliases (ALIASES:L1L2-DISCOVERY §03)
Contexto:
Auditoría del Tracker (CSV export, 42 filas) detectó 19 vacantes con JD vacío pese a Fetch=Accesible y Score determinístico. Causa raíz: validate_url_pre_ingestion() tenía un bypass ciego para dominios agregadores (Computrabajo, Indeed, LinkedIn) — retornaba True sin ejecutar ningún request HTTP (AGREGADOR_VALID), y el flujo de FASE 2 escribía Fetch: Accesible sin verificación real. 13 de las 19 filas resultaron URLs sintéticas no indexadas (patrón [rol]-[marca]-2024 en computrabajo.com), consistente con orígen de agente L2 sin verificar, coladas por el bypass.
Cambios:
- layer_1_run.py::validate_url_pre_ingestion() — bypass ciego reemplazado por HEAD con timeout de 6s: 200 → AGREGADOR_VERIFIED; status ≠ 200 → rechazo (AGREGADOR_STATUS_XXX); timeout/excepción → AGREGADOR_UNVERIFIED (no confirma ni descarta, ya no asume Accesible).
- KERNEL:§09.2 — Paso 1 (URL_GATE) re-especificado: HEAD 6s obligatorio para agregadores en vez de excepción sin verificar.
- KERNEL:§09.11 — fila nueva en la matriz: [ENTRY] Agregador con HEAD fallido/timeout → REVIEW_NEEDED (Fetch=No_Verificado, no Accesible).
- MANUAL:§02 — aclaración en "Gate Decisions", paso 1: el chequeo en agregadores ya no omite verificación, registra honestamente si no pudo confirmarse.
- MANUAL:§21 — nota en campo Fetch: refleja verificación técnica real, incluso en agregadores.
- ALIASES:§03 (vl1) — nota sobre validación activa de URLs de agregadores en Fase 2 de layer_1_run.py.
Validación PATCH-QUALITY-001: ✅ Invisibilidad estructural (inline, sin secciones nuevas) · ✅ Continuidad de voz · ✅ Diff mínimo · ✅ Coherencia transversal (sin contradicción con GATE-DECISION-010/011 existentes).
IDs afectados: Ninguno (sin alta/baja de ID canónico — extensiones de nodos existentes).
Write-Back Verification: KERNEL, MANUAL y ALIASES re-fetched post-escritura — 4/4 bloques confirmados en posición correcta, sin mismatch.
Pendiente (fuera de esta entrada):
- Alta del select-option No_Verificado en el campo Fetch del Tracker de vacantes (Notion, Class B — requiere decisión del operador antes de propagar el reason diferenciado a FASE 2 de escritura).
- Ticket Bug Tracker asociado (creación pendiente de APROBAR_WRITE separado).
- vversions --sync para propagar v9.20.0 al resto de los fundacionales.
---
Tipo: [DOC] [GOVERNANCE] [INFRA]Alcance:
- Kernel (KERNEL:DOCUMENTATION-007)
- Manual (MANUAL:RUNTIME-002)
- System Prompt (SP:VERSION-CHECK-TOOL)
Contexto:
El contrato de Length Check (verificación de integridad estructural) estaba definido en un adendum externo (### 007.3) bajo KERNEL:DOCUMENTATION-007, lo que violaba la Matriz Tipográfica Congelada (KERNEL:DOCUMENTATION-001) al introducir un heading ### no autorizado (NN.N.N). Este batch relocaliza el contrato como contenido *inline* bajo el nodo existente ### 03.7, eliminando el adendum y evitando:
- Creación de un nuevo ID canónico (exime de CENSUS-SYNC Regla 1).
- Violación de la jerarquía de headings (NN.N válido).
- Fragmentación de la documentación transversal.
Cambios:
- KERNEL:§03.7:
- Lista de Modos extendida: añadidos -length (Sanity check read-only) y -update-baseline (write explícito).
- Cuerpo del contrato inyectado inline (propósito, mecanismo, umbrales, archivos asociados, flags).
- Adendum ### 007.3 eliminado (evita colisión de headings).
- Alias actualizado: vversions — acepta --bootstrap, --sync, --scripts, --skills, --length o --update-baseline, sin modo default.
- MANUAL:9.2:
- Bullet de vversions expandido con descripción operativa de -length (exit code 1 si ATENCIÓN REQUERIDA) y -update-baseline (requiere confirmación explícita).
- Sección flotante "HC-03" eliminada (consolidación de contenido).
- SP:§11.3:
- Verificado alineado: Directivas vigentes ya reflejan umbrales (≥5.0%, ≥10 líneas) y bloqueo de -update-baseline no verificado. Sin parche requerido.
Validación PATCH-QUALITY-001:
✅ Matriz Tipográfica (001): Respeta niveles autorizados (### NN.N).
✅ Invisibilidad estructural: Contenido vivo dentro de ### 03.7 sin alterar árbol de navegación.
✅ Continuidad de voz: Tono técnico consistente con el estándar del Kernel.
✅ Diff mínimo: Relocalización limpia (inyección + depuración de adendum).
IDs afectados: Ninguno (sin alta/remoción de IDs canónicos).
Write-Back Verification:
- KERNEL, MANUAL y SP re-fetched post-escritura: 3/3 nodos confirmados en posición correcta.
- KERNEL:§03.7: Modos, cuerpo del contrato y alias verificados.
- MANUAL:9.2: Bullet de vversions expandido y "HC-03" eliminado.
- SP:§11.3: Directivas alineadas (sin cambios requeridos).
Pendientes (fuera de esta entrada):
- vversions --sync para propagar v9.19.6 al resto de los fundacionales.
---
Tipo: [DOC] [GOVERNANCE]Alcance:
- Kernel (KERNEL:DOCUMENTATION-001 §03.1, KERNEL:DOCUMENTATION-007 §03.7, KERNEL:SCHEMA-008 §007.3)
- Manual (MANUAL:SESSION-CYCLE §06, MANUAL:SETUP §11)
- System Prompt (SP:SYNC-RULE §02, SP:DIGITAL-ID-CARD §03)
Contexto:
El documento CHANGELOG_ARCHIVO (ID: 3ba938be-fc42-8011-8947-fb4fa5d1f63f) fue migrado de página a base de datos para centralizar el historial de cambios. Este batch actualiza todas las referencias en el corpus fundacional para reflejar su nuevo estatus como 10° documento fundacional, alineando:
- Contrato de Prefijos Autorizados (KERNEL:§03.1).
- Alcance de vversions (KERNEL:§03.7, §007.3).
- Validación de sesión (MANUAL:§06).
- Verificación de archivos locales (MANUAL:§11).
- Lista de documentos en SP:§02 y ID en SP:§03.
Cambios:
- KERNEL:§03.1: Fila CHANGELOG_ARCHIVO V | CHANGE LOG ARCHIVO añadida a la tabla de Prefijos Autorizados.
- KERNEL:§03.7: 9 → 10 documentos fundacionales.
- KERNEL:§007.3: Lista de documentos actualizada para incluir CHANGELOG_ARCHIVO.
- MANUAL:§06: 9 → 10 documentos fundacionales.
- MANUAL:§11: 6 → 7 documentos en ACTIVE/.
- SP:§02: nueve → diez + ARCHIVO CHANGELOG añadido a la lista.
- SP:§03: ID de ARCHIVO CHANGELOG actualizado de 39d938be-fc42-801c-94f6-f11bfe803633 (página) a 3ba938be-fc42-8011-8947-fb4fa5d1f63f (base de datos).
IDs afectados:
- 3ba938be-fc42-8011-8947-fb4fa5d1f63f (nuevo ID de CHANGELOG_ARCHIVO).
Write-Back Verification:
- KERNEL, MANUAL y SP re-fetched post-escritura: 7/7 nodos confirmados en posición correcta.
- SP:§03: ID de ARCHIVO CHANGELOG verificado como 3ba938be-fc42-8011-8947-fb4fa5d1f63f.
Pendientes (fuera de esta entrada):
- vcensus para regenerar el Census con el nuevo ID.
- vversions --sync para propagar v9.19.5 al resto de los fundacionales.
---
Tipo: [INFRA] [DOC]
Alcance: Integración de "Archivo Changelog" (UUID: 3ba938be-fc42-8011-8947-fb4fa5d1f63f) al flujo de sincronización local y de versión.
Contexto: La página de Notion "Archivo Changelog" cuenta con la propiedad "Versión" y cumple con el contrato de página fundacional. Se integra al registry y a los scripts de sincronización para incluirlo en el ciclo de versionado y check de salud.
Cambios:
- resolver_registry_v2.json — Agregada entrada "CHANGELOG_ARCHIVO": "3ba938be-fc42-8011-8947-fb4fa5d1f63f" en document_registry.
- verify_versions.py — Añadido "CHANGELOG_ARCHIVO" a DOC_KEYS (conteo de fundamentales: 9→10). Agregado fallback ID y lógica de resolución.
- vsync_doc.py — Añadida entrada "change_log_archivo" en diccionario DOCS con mapeo a "Changelog Archivo.md".
- vdoc.py — Añadido "change_log_archivo" al set DOCS.
- health_check.py — Añadida entrada "V-CHANGELOG-ARCHIVO" en DOCS_FUNDACIONALES.
IDs afectados: Ninguno nuevo — integración de documento existente al flujo operativo. 
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
