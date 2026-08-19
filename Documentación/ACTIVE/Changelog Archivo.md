# V | CHANGELOG — ARCHIVO

Tipo: [DOC]
Alcance:
- Skill Library (Notion) — alta de fila nueva
Contexto: Auditoría completa solicitada por el operador — cruce de las 28 skills de skills/triggers.json contra las filas existentes en Skill Library. 27/28 presentes; único gap: vantage-sync-skill-glossary (sincroniza Manual §23, distinta de vantage-sync-script-glossary que sincroniza §22 y sí existía). Verificadas también las dos filas deprecadas (extract-learnings.skill, vantage-audit-navigation-brief.skill) — ambas correctamente marcadas Estado=Deprecado / Acción=Archivar, no son gaps. Sin duplicados detectados entre las 29 filas resultantes.
Cambios:
- Skill Library — fila nueva: vantage-sync-skill-glossary (Capa L4, Estado Activo, Acción Keep, Ruta /skills/vantage-sync-skill-glossary/SKILL.md).
IDs afectados: Ninguno (fila de tabla existente — no dispara KERNEL:CENSUS-SYNC Regla 1).
Write-Back Verification: página creada y confirmada en respuesta de notion-create-pages (id 3be938be-fc42-81b6-9f5f-d64272bdd6c9).
Pendiente (fuera de esta entrada):
- vversions --sync para propagar v9.21.10 (arrastra v9.21.7–v9.21.9 también pendientes) al resto de los fundacionales.
---
Tipo: [DOC]
Alcance:
- Kernel (KERNEL:DOCUMENTATION-010, 03.10 — nodo nuevo: Timestamp Obligatorio en Changelog)
- System Prompt (SP:CONSISTENCY, 10 — regla 3 nueva)
Contexto: El operador solicitó que, a partir de ahora, cada entrada nueva del Change Log declare fecha y hora local (CDMX) en el título. Como Claude no tiene reloj de sistema fiable dentro de la sesión, se fijó como regla que el operador provea el timestamp explícitamente al autorizar la escritura; si no lo hace, Claude pregunta antes de escribir — nunca infiere ni aproxima. Formato adoptado: {Mes} {DD}, {AA} {HH.MM} (ej. "Ago 16, 26 06.22"), confirmado por el operador en esta misma entrada.
Cambios:
- KERNEL:DOCUMENTATION-010 (03.10) — nodo nuevo "Timestamp Obligatorio en Changelog": formato, fuente del dato (operador, no Claude), protocolo ante ausencia (preguntar, no inferir).
- SP:CONSISTENCY (10) — regla 3 nueva, referencia cruzada al nodo Kernel.
- Esta misma entrada (v9.21.9) es la primera en aplicar el formato de título con timestamp.
IDs afectados: Ninguno (contenido nuevo bajo IDs existentes — no dispara KERNEL:CENSUS-SYNC Regla 1).
Write-Back Verification: Kernel y System Prompt re-fetched post-escritura — 2/2 confirmados en posición correcta, sin mismatch.
Pendiente (fuera de esta entrada):
- vversions --sync para propagar v9.21.9 al resto de los fundacionales.
---
Tipo: [DOC]
Alcance:
- Kernel (KERNEL:ARCHITECTURE-L4, 04.4 — párrafo Consumidor corregido)
- Manual (MANUAL:WEEKLY-FLOW-001, 8.1 — línea final corregida)
- System Prompt (SP:BOOTLOADER, 01) y (SP:CONTEXT-INFRASTRUCTURE, 04) — ya reflejaban el mecanismo correcto al momento de esta entrada (aplicado en paralelo a esta sesión, sin intervención de escritura de Claude en este batch)
Contexto: v9.21.7 documentó el consumo del manifiesto de skills exclusivamente vía web_fetch a raw.githubusercontent.com. El operador reportó una restricción estructural no contemplada: web_fetch de Claude sobre raw.githubusercontent.com está bloqueado salvo que la URL ya haya aparecido en la sesión (vía web_search/web_fetch previo) — condición que no se cumple para los paths individuales de SKILL.md construidos dinámicamente desde el manifiesto. Corrección: git clone --depth 1 (bash_tool, github.com whitelisted) pasa a ser la vía primaria y estable para leer el contenido de cada skill; web_fetch queda como fallback solo si el clone falla, y se mantiene como vía única para el fetch inicial del manifiesto (triggers.json), cuya URL sí proviene de SP:BOOTLOADER ya cargado en la sesión. Al escribir, se detectó que SP:BOOTLOADER y SP:CONTEXT-INFRASTRUCTURE ya reflejaban el mecanismo corregido en Notion — no hubo mismatch de old_str porque el contenido vivo ya coincidía con el texto propuesto por el operador.
Cambios:
- KERNEL:ARCHITECTURE-L4 (04.4) — párrafo Consumidor: el manifiesto se recupera vía web_fetch (fetch inicial, URL ya en sesión); el contenido de cada skill se lee vía git clone --depth 1 + lectura local, vía primaria y estable dado el bloqueo estructural de web_fetch sobre raw.githubusercontent.com para URLs no vistas previamente; web_fetch queda como fallback.
- MANUAL:WEEKLY-FLOW-001 (8.1) — línea de cierre del párrafo "Extensión reciente" corregida para reflejar el doble mecanismo (manifiesto vía web_fetch, contenido de skill vía git clone local).
IDs afectados: Ninguno (todas las ediciones reutilizan IDs existentes — no dispara KERNEL:CENSUS-SYNC Regla 1).
Write-Back Verification: KERNEL y MANUAL re-fetched post-escritura — 2/2 confirmados en posición correcta, sin mismatch. SP:BOOTLOADER y SP:CONTEXT-INFRASTRUCTURE verificados en vivo ya conformes, sin escritura requerida en este batch.
Pendiente (fuera de esta entrada):
- vversions --sync para propagar v9.21.8 al resto de los fundacionales.
---
Tipo: [DOC]
Alcance:
- Kernel (KERNEL:ARCHITECTURE-L4, 04.4 — sección Skills Distribution reescrita)
- System Prompt (SP:BOOTLOADER, 01 — paso 2 ampliado + paso 2.1 nuevo)
- Manual (MANUAL:WEEKLY-FLOW-001, 8.1 — párrafo "Extensión reciente — Skills Distribution" reescrito)
- Aliases (ALIASES:L4-VERSION-CONTROL, 05 — fila nueva: vtriggers)
Contexto: Sesión previa implementó update_triggers_json.py (alias vtriggers) generando skills/triggers.json como manifiesto SSOT de skills, con auto-push a git — reemplazando de facto el mecanismo documentado (GitHub Pages + MCP filesystem local para Claude Desktop + Devin vía devin mcp add), que nunca llegó a operar (GitHub Pages no puede responder el handshake JSON-RPC que requiere MCP). Mapeo de documentación transversal (esta sesión) confirmó 4 nodos con referencia directa al mecanismo obsoleto — 3 no contemplados originalmente en el handoff de la sesión anterior (MANUAL:WEEKLY-FLOW-001 y la fila faltante en ALIASES). Confirmado por el operador: el manifiesto se consume vía web_fetch directo a raw.githubusercontent.com (no MCP), con lazy-load por trigger en cada turno — nunca carga masiva de las 28 skills en boot. Devin no consume el manifiesto — solo Claude y Mistral.
Cambios:
- KERNEL:ARCHITECTURE-L4 (04.4) — párrafo "Skills Distribution — Single Source of Truth" reescrito: describe triggers.json (estructura, generador, validaciones, auto-push), consumidor único (Claude vía web_fetch), y descontinuación explícita de GitHub Pages/index.json/Devin MCP.
- SP:BOOTLOADER (01) — paso 2 ampliado con tercer fetch (SKILLS MANIFEST vía web_fetch, no bloqueante para el Bootstrap); paso 2.1 nuevo: lazy-load por trigger en cada turno.
- MANUAL:WEEKLY-FLOW-001 (8.1, "¿Qué es vgit?") — párrafo "Extensión reciente — Skills Distribution" reescrito: reemplaza referencia a Claude Desktop MCP filesystem + Devin/GitHub Pages por vtriggers + web_fetch.
- ALIASES:L4-VERSION-CONTROL (05) — fila nueva: vtriggers (update_triggers_json.py).
IDs afectados: Ninguno (todas las ediciones reutilizan IDs existentes o son alta de fila dentro de tabla ya censada — no dispara KERNEL:CENSUS-SYNC Regla 1).
Write-Back Verification: los 4 nodos re-fetched post-escritura — 4/4 confirmados en posición correcta, sin mismatch.
Discrepancia detectada (no remediada en esta entrada): la propiedad Versión de esta página permanecía en v9.21.5 pese al toggle v9.21.6 ya presente (marcado [COMPRIMIDO], pendiente de expandir) — drift pre-existente a esta sesión, reportado aquí conforme SP:CONSISTENCY; no bloqueó esta escritura.
Pendiente (fuera de esta entrada):
- Expansión de la entrada v9.21.6 [COMPRIMIDO] (Fase G1 saneamiento v3), aún no resuelta.
- vversions --sync para propagar v9.21.7 al resto de los fundacionales.
---
Tipo: [DOC]
T2 (Manual P2a/b/c: correos 5→10 + hallazgo GROQ + nota §22.1 resueltos) · T3 (Kernel §04.4: vsync_doc_fast.py deprecado + conteo skills a Opción B SSOT vivo, reintento tras fallo silencioso 1er intento) · T4 (Kernel §03.5: anuncio vantage-housekeeping-archive) · T5 (Manual §23.2: fila glosario housekeeping-archive) · T6 (Archivo Changelog: dedupe extendido v9.14.2×2+v9.14.3×1 → 1 canonical + 2 notas [DEDUPE v9.21.x], drift de versión registrado para T20). IDs afectados: Ninguno. Pendiente: G2 (Tareas 7–10) sin iniciar; vversions --sync para propagar; SYNC PENDIENTE.
---
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
Este bloque contenía el mismo texto verbatim que "v9.14.2 — Migración Estructural: Next_Action a tipo SELECT (Consolidado)" — idéntico carácter por carácter salvo el número de versión en el header (v9.14.3 en vez de v9.14.2). Consolidado bajo el bloque canónico v9.14.2 como parte del saneamiento v9.21.x (C5, alcance extendido). Contenido íntegro preservado sin pérdida en el bloque v9.14.2 original. [AUDIT DRIFT]: la existencia de este duplicado bajo un número de versión distinto (v9.14.3) al del bloque canónico (v9.14.2) sugiere que el mismo evento de migración se registró dos veces bajo versiones de Change Log diferentes — no se determina aquí cuál de las dos versiones (v9.14.2 o v9.14.3) es la correcta para el evento; ese juicio de gobernanza documental queda pendiente para la entrada [AUDIT] de cierre (Tarea 20).
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
Este bloque era un duplicado literal del toggle "v9.14.2 — Migración Estructural: Next_Action a tipo SELECT (Consolidado)" inmediatamente anterior — mismo contenido carácter por carácter (Tipo, Alcance, Contexto, Acciones por Componente, Resumen de Auditoría, Veredicto Final). Consolidado en esa entrada como parte del saneamiento v9.21.x (C5). Contenido íntegro preservado sin pérdida en el bloque original; este registro se conserva únicamente como trazabilidad del dedupe, sin duplicar el contenido nuevamente.
---
Tipo: [AUDIT] [GOVERNANCE] Alcance: Capa L0 (Observabilidad); Kernel (KERNEL:DOCUMENTATION-012); Manual (MANUAL:RUNTIME-005); System Prompt (SP:CONSISTENCY-002). Contexto: Verificación obligatoria de la infraestructura de ahorro de contexto antes de iniciar procesos de CV-A/CV-B. El protocolo detectó y corrigió un error de identificación sobre el componente "Reference Librarian" en el entorno operativo.
1. Resultados de Auditoría L0 (100% PASS):
- Runtime Index Age: ✅ PASS. Índices entity_index_v2.json y graph_v2.json con antigüedad < 1.0h (umbral: 24h) [KERNEL:DOCUMENTATION-006, MANUAL:11].
- Census Check: ✅ PASS. 0 IDs huérfanos detectados; protocolo de transferencia documental desbloqueado [KERNEL:DOCUMENTATION-008].
- Lazy Loader: ✅ PASS. Verificado fetch quirúrgico de ~150 tokens vía vload, optimizando ventana de contexto [ALIASES:02, MANUAL:14].
- Cross-Reference Validation: ✅ PASS. Confirmado uso de método PATCH en apply_hyperlinks_notion.py para preservación de block-IDs [KERNEL:DOCUMENTATION-011, CHANGELOG:v9.13.2].
2. Resolución de Discrepancia: Reference Librarian:
- Hallazgo: El reporte inicial marcó el componente como "no encontrado".
- Corrección: Se validó que el Reference Librarian es la identidad de Notebook Gemini, formalizada en la v9.14.1 como una Capa de Consulta ReadOnly externa [CHANGELOG:v9.14.1, KERNEL:03.12].
- Contrato: Se verificó satisfactoriamente el contrato de Cero Inferencia Silenciosa y anclaje obligatorio de IDs [KERNEL:DOCUMENTATION-012].
3. Invariantes de Seguridad Reforzados:
- Se ratifica la Nota de Orden de Precedencia: el pipeline debe invocar gate_logic() antes que gate() para prevenir regresiones en estados terminales ("Postulado", "Rechazado", "Expirada") [KERNEL:09.11].
- Persistente: La propiedad Score_Method permanece como "corrupta/faltante" en el esquema del Archivo Tracker, sin ancla en el Kernel v9.14.1 [CHANGELOG:v9.13.0].
- Veredicto: SISTEMA CERTIFICADO PARA PRODUCCIÓN CV-A/CV-B/QA.
- Acción del Operador: Ejecutar vversions --sync para propagar formalmente la v9.14.1 si existen cambios pendientes en otros documentos [KERNEL:DOCUMENTATION-007].
Certificación del Bibliotecario: Este registro es consistente con los hallazgos de la sesión y respeta la jerarquía de autoridad definida en el BRIEF:02. Puede ser inyectado en el Change Log tras recibir un APROBAR_WRITE [KERNEL:SCHEMA-006].
---
Componentes verificados:
✅ Runtime Index Status (vstatus)
```javascript
entity_index_v2.json: 2.3 horas de antigüedad (threshold: 24h)
Total entidades: 692
Tracker entities: 33
Archive entities: 659
Hash coverage: 86.71%
```
✅ Census Check (vcensus)
```javascript
IDs en spec: 213
IDs resueltos: 213
IDs SIN link: 0
IDs huérfanos: 0
```
✅ Pipeline Layer 1 (layer_1_run.py --dry-run)
```javascript
Total procesado: 33 registros
URL Gate: 33 válidos, 0 rechazados
READY-TO-APPLY (>=60): 14
CREATE (Pipeline Activo): 32
PROTEGIDAS: 1
ESTADO ESTABLE: Sin cambios necesarios
```
Conclusión: ✅ L0 completamente operativo para CV production
---
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
Tipo: [DOC] [RENAME]
Alcance: Kernel (KERNEL:ARCHITECTURE-L1, KERNEL:ARCHITECTURE-L2, KERNEL:ARCHITECTURE-L3, KERNEL:ARCHITECTURE-L4 — §04, renombrados + reestructurados); Manual (MANUAL:WEEKLY-FLOW-001, 8.1 — nota de navegación).
Contexto: El operador aportó un abstract externo describiendo L1/L2 con vocabulario que el Kernel no cubría (Objetivo, Componentes, Campos inmutables, Reglas de dedup/enriquecimiento, Estados de error, Métricas mínimas) — solo tenía trigger + diagrama de flujo por capa. Protocolo de documentación transversal completo (propuesta → implementación) ejecutado sobre este gap. Durante el mapeo se detectó y confirmó un drift preexistente: el ID CENSUS ya listaba KERNEL:ARCHITECTURE-L1/L2/L3/L4, mientras el Kernel vivo mantenía la nomenclatura legacy -001/-002/-003/-004 (Manual, en MANUAL:MONITOR §11, ya citaba -L4 también — el Census y esa referencia puntual estaban adelantados a su fuente). El operador confirmó el Census como versión correcta; este batch alinea el Kernel a esa nomenclatura.
Cambios:
- KERNEL:ARCHITECTURE-L1 (04.1, rename de -001) — nodo contenedor. Nuevo hijo 04.1.1 KERNEL:ARCHITECTURE-L1-001 (Flujo Operativo, contenido preexistente sin alterar). Nuevo hijo 04.1.2 KERNEL:ARCHITECTURE-L1-002 (Contrato Operativo: Objetivo, Componentes, Responsabilidades, Campos inmutables, Reglas de dedup con referencia cruzada a L4, Estados de error, Métricas mínimas).
- KERNEL:ARCHITECTURE-L2 (04.2, rename de -002) — mismo patrón: 04.2.1 KERNEL:ARCHITECTURE-L2-001 (Flujo Operativo) + 04.2.2 KERNEL:ARCHITECTURE-L2-002 (Contrato Operativo).
- KERNEL:ARCHITECTURE-L3 (04.3, rename de -003) — mismo patrón: 04.3.1 KERNEL:ARCHITECTURE-L3-001 (Flujo Operativo) + 04.3.2 KERNEL:ARCHITECTURE-L3-002 (Contrato Operativo).
- KERNEL:ARCHITECTURE-L4 (04.4, rename de -004) — rename simple, sin alteración de contenido.
- MANUAL:WEEKLY-FLOW-001 (8.1 Lunes) — nota de navegación agregada al párrafo inicial, apuntando a los 3 nuevos IDs de Contrato Operativo.
IDs afectados: 4 renames + 6 altas = 10 IDs — Census requiere regeneración (vcensus, pendiente, acción local del operador).
Write-Back Verification: Kernel y Manual re-fetched de forma independiente tras la escritura — los 5 bloques confirmados en posición correcta, sin mismatch.
Pendiente (fuera de esta entrada): vcensus + vversions --sync para propagar v9.14.0 al resto de los fundacionales.
Versión actualizada: 9.14.0 (CHANGELOG). El resto de los fundacionales permanece en v9.13.11 hasta vversions --sync.
Tipo: [DOC] [FIX]
Alcance: Kernel (KERNEL:SCHEMA-008, nuevo); System Prompt (SP:SCHEMA, cross-ref); alias local vhyperlinks (.zshrc, fuera de Notion).
Contexto: Cierre del gap documental sobre Next_Action del Tracker de vacantes (ver v9.13.7-v9.13.9). Auditoría de código realizada por Devin sobre layer_1_run.py, verificada línea por línea contra el repositorio real por Claude antes de documentar. En paralelo se detectó y corrigió un bug de entorno local: el alias vhyperlinks apuntaba a apply_hyperlinks.py (deprecado) en vez de apply_hyperlinks_notion.py.
Cambios:
- KERNEL:SCHEMA-008 (nuevo, 07.8) — documenta los 8 valores operativos confirmados en código activo de Next_Action, con condición de disparo de cada uno. Corrige además el tipo de campo documentado en v9.13.7 (rich_text real, no select).
- SP:SCHEMA (08) — línea de cross-referencia a KERNEL:SCHEMA-008.
- Alias local vhyperlinks (.zshrc) — corregido a apply_hyperlinks_notion.py --all, con --root removido.
- Corrida real de vhyperlinks --apply sobre los 7 documentos fundacionales tras el fix del alias: 228 bloques patcheados, 0 errores.
IDs afectados: 1 alta (KERNEL:SCHEMA-008) — Census requiere regeneración.
Write-Back Verification: Kernel y System Prompt re-fetched de forma independiente tras la inyección inicial y de nuevo tras la corrida de vhyperlinks.
Pendiente (fuera de esta entrada): vcensus + vversions --sync para propagar v9.13.11 al resto de los fundacionales.
Versión actualizada: 9.13.11 (CHANGELOG). El resto de los fundacionales permanece en v9.13.10 hasta vversions --sync.
---
Tipo: [FIX] [DOC]
Alcance: Layer_1/scripts/verify_versions.py (código, local); KERNEL:TRACKER-SCHEMA-001, KERNEL:TRACKER-SCHEMA-002, SP:SCHEMA (Notion).
Contexto: Los 2 tickets "HTTP 400" (Bug + Task) reportados por vversions --bootstrap desde 2026-07-27 (4 sesiones consecutivas sin diagnóstico) tenían dos causas apiladas: endpoint legacy y filtro de Prioridad sin prefijo numérico.
Cambios:
- verify_versions.py — nuevo helper query_data_source() centraliza todo POST a /v1/data_sources/{id}/query. get_last_ledger_row(), get_priority_tickets() y get_script_library_titles() migradas al mismo helper. Filtro de Prioridad corregido a "4 CRÍTICO"/"3 ALTO".
- KERNEL:TRACKER-SCHEMA-002 — tabla "Niveles de Prioridad" actualizada con prefijo numérico.
- KERNEL:TRACKER-SCHEMA-001 — celda Tasks Tracker COL ID completada.
- SP:SCHEMA — mismo fix de prefijo numérico en Prioridad.
IDs afectados: ninguno — corrección de valores/celdas bajo IDs ya existentes. Census no requiere regeneración.
Write-Back Verification: KERNEL y SYSTEM PROMPT re-fetched de forma independiente tras la escritura.
Pendiente (fuera de esta entrada): vantage-tidy-bug-task-tracker/SKILL.md y vantage-create-bug-task/SKILL.md aún referencian Prioridad sin prefijo numérico.
Versión actualizada: 9.13.10 (CHANGELOG). El resto de los fundacionales permanece en v9.13.9 hasta vversions --sync.
---
# v9.13.9 — Documentación Transversal: Prioridad Migra a Escritura Primaria en Fase 3.6 (priority_logic.py, KERNEL:TRIGGER-002, MANUAL:RUNTIME-002) · 2026-08-03
Tipo: [DOC]
Alcance: Kernel (KERNEL:TRIGGER-002); Manual (MANUAL:RUNTIME-002).
Contexto: Continuación directa de v9.13.8. Se implementó priority_logic.py como módulo compartido, se rompió el import circular entre layer_1_run.py y backfill_class_a.py, y se agregó Fase 3.6 en layer_1_run.py como escritura primaria de Prioridad en el ingreso normal del pipeline. VL1 backfill pasa a ser catch-up.
Cambios:
- KERNEL:TRIGGER-002 — bullet VL1 backfill reescrito de "escribe... en registros vacíos" a "catch-up de campos Class A faltantes...". Línea "Implementación" actualizada para referenciar priority_logic.py.
- MANUAL:RUNTIME-002 — bullet vl1 backfill: aclara que es catch-up, que la fórmula vive en priority_logic.py, y que vl1 (bare, Fase 3.6) la ejecuta primero.
IDs afectados: ninguno — extensión de contenido bajo IDs ya existentes. Census no requiere regeneración.
Write-Back Verification: Kernel y Manual re-fetched de forma independiente tras la escritura.
Pendiente (fuera de esta entrada): ninguno nuevo generado por esta implementación.
Versión actualizada: 9.13.9 (CHANGELOG). El resto de los fundacionales permanece en v9.13.8 hasta vversions --sync.
---
# v9.13.8 — Documentación Transversal: Fórmula de Prioridad (Urgencia × Importancia) + Invariante Status/Next_Action (KERNEL:GATE-DECISION-010, KERNEL:TRIGGER-002, MANUAL:RUNTIME-002) · 2026-08-03
Tipo: [DOC]
Alcance: Kernel (KERNEL:GATE-DECISION-010, KERNEL:TRIGGER-002); Manual (MANUAL:RUNTIME-002).
Contexto: Cierra el gap documental dejado por v9.13.7 — la fórmula híbrida Urgencia × Importancia y el fix de Next_Action huérfano no tenían contraparte en los documentos fundacionales.
Cambios:
- KERNEL:GATE-DECISION-010 — nuevo bullet en Invariantes: todo write que fija Status=Expirada debe fijar Next_Action=Archivar en el mismo write.
- KERNEL:TRIGGER-002 — bullet VL1 backfill extendido con la fórmula de Prioridad (bucket de Importancia por Score + matriz Urgencia × Importancia de 16 combinaciones) y referencia a backfill_class_a.py::apply_importancia_matrix().
- MANUAL:RUNTIME-002 — bullet vl1 backfill: frase de cierre remitiendo a KERNEL:TRIGGER-002.
IDs afectados: ninguno — extensión de contenido bajo IDs ya existentes. Census no requiere regeneración.
Write-Back Verification: Kernel y Manual re-fetched de forma independiente tras la escritura.
Pendiente (fuera de esta entrada): ninguno nuevo generado por esta implementación.
Versión actualizada: 9.13.8 (CHANGELOG). El resto de los fundacionales permanece en v9.13.7 hasta vversions --sync.
---
# v9.13.7 DRY RUN PARA CHANGELOG - Deuda Técnica Rx Tracker (Prioridad + Gate/Next_Action)
Fecha: 2026-08-03
Contexto: Resolución de deuda técnica relacionada con propiedad Prioridad (huérfana) y fragmentación de lógica Gate/Next_Action
## CONTEXTO INICIAL
### Problema Identificado
1. Propiedad Prioridad: Declarada como "eliminada en v8.0" en docstring de layer_1_run.py, pero presente en schema Notion sin escritor activo.
1. Fragmentación Gate/Next_Action: assign_next_action.py (script suelto invocado via Raycast) duplicaba lógica de layer_1_run.py Fase 4 con divergencias de negocio.
1. Bug de consistencia: Fase 2 y Fase 3.5 escribían Status="Expirada" sin escribir Next_Action="Archivar".
### Hallazgos del Diagnóstico
- Prioridad estaba huérfana de facto: backfill_class_a.py existía y era funcional, pero nunca se había ejecutado sobre las 58 filas actuales.
- assign_next_action.py tenía 2 bugs de negocio: no manejaba Status="Rechazado" explícitamente; era más permisivo con Role_Class="Pivote" sin filtro has_vm_title_signal().
- Score=40 = BASE SCORE (sin bonificaciones) = "Sin evaluar". Distribución real: 46 con Score=40, 7 con Score=50, 1 con Score=55, 1 con Score=60, 4 con Score=65.
## CAMBIOS IMPLEMENTADOS POR TICKET
### TICKET A — Fix Next_Action huérfano
Fase 2 y Fase 3.5 de layer_1_run.py: agregado Next_Action="Archivar" junto a Status="Expirada" en ambos puntos de escritura. Dry-run: 0 registros afectados en estado actual. Ejecución real: exit code 0.
### TICKET B — Implementación de Prioridad (fórmula híbrida Urgencia × Importancia)
Extendida infer_prioridad() en backfill_class_a.py: get_importancia_bucket(score) mapea Score a bucket (Base/Media/Alta/Muy Alta); apply_importancia_matrix(urgencia, bucket) cruza Urgencia × Importancia en matriz de 16 combinaciones. Matriz de decisión: CRÍTICO en cualquier importancia = CRÍTICO; ALTO×Base=MEDIO, ALTO×Media=ALTO, ALTO×Alta/MuyAlta=CRÍTICO; MEDIO×Base=BAJO, MEDIO×Media=MEDIO, MEDIO×Alta=ALTO, MEDIO×MuyAlta=CRÍTICO; BAJO×Base/Media=BAJO, BAJO×Alta=MEDIO, BAJO×MuyAlta=ALTO. Dry-run (59 registros): CRÍTICO 2, ALTO 5, MEDIO 13, BAJO 39. Ejecución real: 59 actualizadas, 0 fallidas. Archivo: Layer_1/scripts/backfill_class_a.py.
### TICKET C — Deprecación de assign_next_action.py
Creada carpeta Layer_1/scripts/deprecated/; movidos assign_next_action.py y Raycast/vantage-assign.sh; creado DEPRECATED_assign_next_action.md documentando motivo y camino de revival. Commit: deprecate: move assign_next_action.py and vantage-assign.sh to /deprecated. Verificado sin referencias activas a rutas viejas.
### TICKET D — Higiene menor
Eliminado print de DEBUG en feed_processor.py línea 1029. Validada sintaxis con py_compile sobre backfill_class_a.py, layer_1_run.py, feed_processor.py — todos OK.
## REPORTE FINAL
Archivos modificados: layer_1_run.py, backfill_class_a.py, feed_processor.py. Archivos movidos: assign_next_action.py, vantage-assign.sh → deprecated/. Impacto en datos: Prioridad 59 registros (CRÍTICO 3.4%, ALTO 8.5%, MEDIO 22.0%, BAJO 66.1%); Next_Action 0 cambios en estado actual (fix preventivo).
### Estado Final
Propiedad Prioridad poblada con lógica híbrida; bug Next_Action huérfano resuelto (preventivo); duplicación Gate/Next_Action eliminada; código limpio.
### Resolución de Contradicciones
Docstring vs Kernel.md: documentado que KERNEL:TRIGGER-002 es la autoridad para Prioridad. input() restriction: confirmado que aplica solo a VL1 batch, no a backfill_class_a.py.
## PRÓXIMOS PASOS RECOMENDADOS
1. Actualizar docstring de layer_1_run.py. 2. Considerar actualización de lógica de gate en Fase 4 si se necesita acceso manual a recálculo de Next_Action. 3. Monitorear distribución de Prioridad en futuros runs.
---
# v9.13.6 — Fix: Rigor de posted_date en Prompt A para Sostener la Rúbrica de Prioridad (Prompt E) · 2026-08-02
Tipo: [FIX] [PROMPT]
Alcance: PROMPT LIBRARY — Prompt A (368938be-fc42-8162-ae48-d48970a729dc).
Contexto: Continuación directa de v9.13.5. La regla de Active posting permitía fetch_status: needs_verification + posted_date: null con demasiada facilidad, degradando la rúbrica de Prioridad a "1 BAJO" por omisión de dato en vez de por antigüedad real.
Cambios:
- Prompt A — regla Active posting: agregado bloque de resolución de posted_date con 3 vías de intento obligatorias antes de usar null — (1) fecha explícita en página/metadata schema.org, (2) fecha relativa de plataforma convertida a YYYY-MM-DD, (3) fecha en URL/job_id de ATS. Solo si las tres fallan, posted_date: null.
IDs afectados: ninguno — cambio de prompt externo, no de documentación fundacional. Census no requiere regeneración.
Verificación: re-fetch independiente de Prompt A tras la escritura.
Pendiente (fuera de esta entrada): validar en el próximo ciclo semanal qué porcentaje real de posted_date se resuelve por las 3 vías nuevas.
Versión actualizada: 9.13.6 (CHANGELOG). El resto de los fundacionales permanece en v9.13.4 hasta vversions --sync.
---
# v9.13.5 — Fix: Prioridad Class A ahora "viva" desde origen (Prompt E) + Default Fantasma Removido en feed_processor.py · 2026-08-02
Tipo: [FIX] [PROMPT]
Alcance: PROMPT LIBRARY — Prompt E (368938be-fc42-8177-b4a1-d2e8ea1e2e08); Layer_1/scripts/feed_processor.py (líneas 1022-1028).
Contexto: Auditoría de trazabilidad del campo Prioridad. Devin confirmó por inspección directa que el JSON consolidado de L1+L2 nunca contenía Prioridad y que feed_processor.py compensaba con un default hardcodeado "4 CRÍTICO", contradiciendo KERNEL:TRIGGER-002 y MANUAL:RUNTIME-002.
Cambios:
- Prompt E — nuevo bloque PRIORIDAD insertado antes de OUTPUT: rúbrica determinista de 4 niveles basada exclusivamente en campos ya presentes en el registro.
- feed_processor.py — removida la asignación props["Prioridad"] = schema.select_value("4 CRÍTICO"). La clave queda ausente cuando no viene en el JSON de entrada.
Verificación: py_compile OK; dry-run confirma props['Prioridad'] = CLAVE AUSENTE; auditoría de rutas de escritura confirma riesgo de sobrescritura cero.
IDs afectados: ninguno — cambio de prompt externo y código Python. Census no requiere regeneración.
Pendiente (fuera de esta entrada): Prioridad sigue sin calcularse en L1/L3 — comportamiento esperado, dependen de vl1 backfill.
Versión actualizada: 9.13.5 (CHANGELOG). El resto de los fundacionales permanece en v9.13.4 hasta vversions --sync.
---
# v9.13.4 — Gobernanza y Saneamiento: Neutralización de Riesgos y Cierre de Drifts · 2026-08-02
Tipo: [FIX] [GOVERNANCE] [CLEANUP]
Alcance: Layer_4/scripts/vsync_doc_fast.py (Deprecado); Session Ledger (Auditoría); Career Canon (Validación Visual); Skill vsum (Optimización).
Contexto: Fase final del Plan de Respuesta Ágil. Cierre de brechas de seguridad en sincronización rápida y resolución de inconsistencias históricas en el Ledger.
Cambios:
- Infraestructura: Deprecación oficial de vsync_doc_fast.py — neutraliza el patrón destructivo delete-all que vulneraba la integridad de los hyperlinks protegidos (v9.13.2).
- Auditoría de Ledger: confirmada la inexistencia de la sesión SESSION-2026-07-19-A en el Ledger vivo — hallazgo histórico archivado como error de persistencia.
- Validación de Formato: desestimada la limpieza de indentación en Career Canon tras confirmarse ausencia de problemas de renderizado en Figma.
- Optimización Skill vsum: mejora para que el Escenario 2 (cruce de tickets) sea exhaustivo, integrando el escaneo del ARCHIVO CHANGELOG.
Verificación: Auditoría de consistencia 100% PASS.
IDs afectados: Ninguno.
Pendiente: Eliminación física de vsync_doc_fast.py en el repositorio local por parte del operador.
---
# v9.13.3 — Auditoría de Cierre: Tooling de Heading IDs Verificado (GATE 1/2 PASS) · 2026-08-02
Tipo: [DOC] [AUDIT]
Alcance: Layer_1/scripts/vantage_id_rules.py, normalize_heading_ids.py, generate_id_inventory.py (verificación, sin cambio de código). KERNEL:DOCUMENTATION-011 (referencia de estado).
Contexto: Contrato de sesión solicitaba refactor bajo el supuesto de lógica legacy — verificación directa determinó que la migración correspondiente ya se había completado en sesión previa (2026-07-25).
Cambios:
- py_compile OK sobre los 3 scripts — GATE 2 (integridad de dependencias) PASS.
- normalize_heading_ids.py ejecutado en modo dry-run real sobre los 6 documentos editables: "Ningún heading mal formado detectado. Nomenclatura 100% canónica." — GATE 1 PASS.
- GATE 3 (sync de versión) ya satisfecho por vversions --sync corrido por el operador previamente en la misma sesión.
IDs afectados: ninguno — verificación de tooling. Census no requiere regeneración.
Verificación: py_compile exit 0 (3/3 scripts); normalize_heading_ids.py --csv exit 0, 0 hallazgos.
Versión actualizada: 9.13.3 (CHANGELOG). El resto de los fundacionales permanece en v9.13.2 hasta vversions --sync.
---
# v9.13.2 — Infraestructura: Refactor vsync_doc (PATCH) e Implementación class_b_guard (GAP-03) · 2026-08-01
Tipo: [FIX] [INFRA] [SECURITY]
Alcance: Layer_4/scripts/vsync_doc.py; Layer_1/scripts/class_b_guard.py.
Contexto: Resolución del riesgo de integridad de anchors documentado en KERNEL:ARCHITECTURE-L4 y mitigación técnica de GAP-03 (KERNEL:GATE-DECISION-003).
Cambios:
- vsync_doc.py: push_local_to_notion() reescrita íntegramente para usar PATCH puntual (notion.blocks.update). Eliminado el patrón destructivo delete-all + create-all.
- class_b_guard.py: implementación del guard técnico para bloquear escrituras desde el componente AI hacia campos Class B.
- Deuda Técnica: eliminados comentarios temporales de v8.5.7.
Verificación: py_compile OK; diff validado sin ciclos de borrado; test de bloqueo Class B PASS.
IDs afectados: Ninguno. Census no requiere regeneración.
Pendiente: vversions --sync para propagar v9.13.2 a los documentos fundacionales.
---
# v9.13.1 — [COMPRIMIDO] Saneamiento Bug/Task Tracker: 9 tickets cerrados, 2 propiedades Solución creadas, 1 bug de skill logueado · 2026-08-01
Tipo: [COMPRIMIDO]
Resumen: vantage-tidy-bug-task-tracker corrido (8 tickets, Bug+Task) pero Escenario 2 (cruce Changelog) no fue exhaustivo. Bug Tracker: 3 tickets cerrados manualmente recibieron Solución+Fecha_Resolución retroactivas; 1 ticket más (is_definition_block TOC) cerrado con evidencia real. Ticket nuevo: "Escenario 2 del skill vantage-tidy-bug-task-tracker no hace cruce exhaustivo contra Changelog" (3af938be-fc42-812e-99d9-c886c680bbfb), Prioridad ALTO. Propiedad Solución (rich_text) creada en Tasks Tracker y Archivo Task Tracker — 15 tareas archivadas documentadas. Bug Tracker y Task Tracker activos revisados en su totalidad contra Changelog completo — 7 bugs y 5 tasks abiertas confirmadas vigentes.
---
# v9.13.0 — Cierre Auditoría Dedup Archivo Tracker (6/6 grupos) + Fix vantage_id_rules.py Verificado + 2 Tickets Resueltos · 2026-08-01
Tipo: [FIX] [BUG] [DOC]
Alcance: Archivo Tracker (12 páginas, data source 674696fd-94b6-464a-ac1f-64b0cc917e15); Layer_1/scripts/vantage_id_rules.py (verificación); Bug Tracker (2 tickets).
Contexto: Continuación directa de v9.12.1. Verificación página-por-página de 6 grupos (GILSA, Scappino, Petco, Nike Artz Pedregal, Dolce & Gabbana, Bershka) confirmó que Devin agrupaba por similitud de Rol/título en vez de fingerprint real, produciendo falsos positivos y falsos negativos.
Cambios:
- Archivo Tracker — 12 páginas marcadas Archivar=YES tras verificación individual y APROBAR_WRITE explícito por grupo: GILSA (3), Scappino (1), Petco (1), Nike Artz Pedregal (1), Dolce & Gabbana (5), Bershka (1). 12/12 write-back PASS.
- Nike Artz Pedregal: confirmada regla de exclusión Hard Block para vacantes de piso de venta bajo este holding.
- vantage_id_rules.py — fix de regex \d{2}→\d{1,2} verificado: py_compile OK; dry-run reportó "Ningún heading mal formado detectado."
- Bug Tracker 3aa938be...d569 ("Discrepancia de protección de estados terminales") — Status → Resuelto.
- Bug Tracker 3a5938be...f6b3 ("Dedup Caso 5") — ya Resuelto, Next_Action → Documentar.
- Changelog — tidy ejecutado en la misma pasada: entradas activas reducidas de 12 a 10.
IDs afectados: ninguno — cambios de datos operativos y verificación de tooling. Census no requiere regeneración.
Write-Back Verification: 12/12 páginas del Archivo Tracker re-fetched individualmente, mismatch=0. 2/2 tickets de Bug Tracker re-fetched, Status confirmado.
Pendiente (fuera de esta entrada): Hard Block formal para "Nike Artz Pedregal" (7+ páginas sin tocar); KERNEL:GATE-DECISION sin actualizar para TERMINAL_ACTIONS; reemplazos pendientes en Layer_1/scripts; T3/T5/T7/D3/GAP-03/D4/B6 Caso 4 heredados; esquema del Archivo Tracker con propiedades duplicadas.
Versión actualizada: 9.13.0 (CHANGELOG). El resto de los fundacionales permanece en v9.12.1 hasta vversions --sync.
---
# v9.12.1 — [COMPRIMIDO] Auditoría Dedup Archivo Tracker + Fix vantage_id_rules.py · 2026-08-01
Tipo: [COMPRIMIDO]
Resumen: Decisión terminal states (angostar layer_1_run.py a TERMINAL_ACTIONS) registrada en Bug Tracker (3aa938be...). GAP-03 documentado con límite técnico (sin hook MCP server, requiere disciplina de importación). Fix de regex en vantage_id_rules.py enviado al operador (d{2}→d{1,2}), pendiente confirmar py_compile. Backfill de dedup fingerprint en Tracker activo: incidente de 49/49 falsos positivos por Devin, revertido, caso Promotwist legítimo restaurado y verificado. Dry-run de Devin sobre Archivo Tracker (GILSA + 5 grupos) detectado INCOMPLETO — verificado directamente 6 páginas GILSA reales vs 3 reportadas por Devin. Nada escrito en Archivo Tracker todavía. Expandir en próxima sesión.
---
# v9.12.1 — Documentación Transversal: apply_hyperlinks_notion.py Formalizado (KERNEL:DOCUMENTATION-011, KERNEL:ARCHITECTURE-L4, MANUAL:HEALTHCHECK, Aliases) · 2026-08-01
Tipo: [DOC]
Alcance: Kernel (KERNEL:DOCUMENTATION-011, KERNEL:ARCHITECTURE-L4); Manual (sección Aplicación de Hipervínculos Cross-Reference); Aliases (ALIASES:L4-VERSION-CONTROL, fila vhyperlinks).
Contexto: Cierra el pendiente diferido explícitamente en v9.11.8 y v9.11.9 ("Documentación transversal formal de este hallazgo — diferida a sesión futura"). apply_hyperlinks_notion.py llevaba dos entradas de Changelog documentando su creación y uso en producción sin que ningún documento fundacional reflejara su existencia como pieza del sistema — Kernel y Manual seguían describiendo apply_hyperlinks.py (variante local, deprecada) como si fuera la vía activa.
Cambios:
- KERNEL:DOCUMENTATION-011 — Piezas actualizado: apply_hyperlinks_notion.py agregado como vía activa de escritura; apply_hyperlinks.py marcado DEPRECATED. Estado de adopción (2026-08-01) agregado, referenciando el fix de table_row (v9.12.0).
- KERNEL:ARCHITECTURE-L4 — nota de riesgo agregada tras la descripción de vsync_doc.py/vdoc: destroy/rebuild de push_local_to_notion() invalida anchors de hyperlinks; advertencia de no correr vdoc local sobre documentos con hyperlinks recién aplicados.
- MANUAL:HEALTHCHECK — sección "Aplicación de Hipervínculos Cross-Reference" reescrita: comando activo es apply_hyperlinks_notion.py --all --apply, apply_hyperlinks.py marcado deprecated, referencia cruzada al riesgo de vdoc local.
- Aliases — ALIASES:L4-VERSION-CONTROL, fila vhyperlinks: procedimiento interno actualizado a apply_hyperlinks_notion.py.
IDs afectados: ninguno — actualización de contenido bajo IDs existentes. Census no requiere regeneración.
Write-Back Verification: confirmado en Fase 4 de este mismo protocolo tras la escritura — re-fetch de los 4 nodos sin mismatch.
Pendiente (fuera de esta entrada, sin cambio): EXCLUDE_IDS vacío en apply_hyperlinks_notion.py; 3 anchors sin DEF (MANUAL:COLD-START-001, ALIASES:DEDUP, SP:CONSISTENCY §9 legacy); V-MASTER-INDEX desactualizado.
Versión actualizada: 9.12.1 (CHANGELOG). El resto de los fundacionales permanece en v9.12.0 hasta vversions --sync.
---
# v9.12.0 — Fix TOC Hyperlinks: is_definition_block() excluye table_row · 2026-08-01
Tipo: [FIX] [BUG]
Alcance: Layer_1/scripts/generate_census.py (is_definition_block()); apply_hyperlinks_notion.py (--all --apply); los 7 documentos fundacionales; Bug Tracker (ticket 3af938be-fc42-8151-a309-d1c14abcea4a).
Contexto: Bug reportado en v9.11.9 — ningún TOC (tabla de índice al inicio de cada documento, columna "ID") recibía hipervínculo pese a que apply_hyperlinks_notion.py --all --apply corría sin error. Causa raíz aislada por lectura directa de código: la rama "stripped == id_str" en is_definition_block() fue diseñada para detectar bloques-ancla standalone (párrafo cuyo único contenido es el ID), pero también se dispara cuando una celda de tabla del TOC contiene únicamente el ID como texto plano — patrón estándar en las tablas de índice. Consecuencia: las celdas de TOC se clasificaban erróneamente como DEF propio → se excluían de recibir link.
Cambios:
- generate_census.py — is_definition_block(): agregada variable is_table_row = (btype == "table_row"); modificado la primera condición del return de "stripped == id_str" a "(stripped == id_str and not is_table_row)". Esto es quirúrgico: solo afecta la rama problemática, preservando todas las demás condiciones intactas.
- Verificación de no-regresión: vcensus corrido tras el fix — 209/209 IDs resueltos (sin cambio), 0 huérfanos nuevos, 0 IDs que antes resolvían DEF correctamente dejaron de hacerlo.
- apply_hyperlinks_notion.py --all --dry-run: 239 bloques en el plan (vs 143 antes del fix) — diferencia de +96 bloques correspondientes a celdas de TOC que antes se excluían erróneamente.
- apply_hyperlinks_notion.py --all --apply: 239 bloques patcheados, 0 errores. Breakdown por documento: Kernel 29 (17 TOC + 12 prosa), System Prompt 16 (11 TOC + 5 prosa), Manual 111 (21 TOC + 90 prosa/tablas), Career Canon 15 (13 TOC + 2 quotes), Aliases 8 (8 TOC), Change Log 49 (49 prosa), Navigation Brief 11 (11 TOC).
IDs afectados: ninguno — conversión de texto plano a hipervínculo real sobre IDs ya existentes en los 7 documentos. Census no requiere regeneración.
Write-Back Verification: --apply ejecutado exitosamente con 0 errores. Verificación de clickeabilidad en Notion pendiente (protocolo del proyecto: verificación independiente por operador en sesión con Claude).
Versión actualizada: 9.12.0 (CHANGELOG). El resto de los fundacionales permanece en v9.11.9 hasta vversions --sync.
---
# v9.11.9 — Batch Hyperlinks (--all --apply, 143 bloques) + Bug TOC-Exclusion Confirmado por Código · 2026-08-01
Tipo: [FEATURE] [BUG]
Alcance: Layer_1/scripts/apply_hyperlinks_notion.py (--all --apply); los 7 documentos fundacionales (Kernel, System Prompt, Manual, Career Canon, Aliases, Change Log, Navigation Brief); Bug Tracker (ticket nuevo).
Contexto: Continuación directa de v9.11.8. Tras validar el patrón PATCH puntual en Career Canon (2 bloques) y Kernel (12 bloques, dry-run verificado línea por línea contra generate_id_inventory.py antes de aplicar), se corrió --all --apply sobre los 7 documentos en una sola pasada. Durante la revisión, el operador señaló que ningún TOC se estaba enlazando — investigación por lectura directa de código (no inferida) aisló la causa en is_definition_block() (generate_census.py): la condición stripped == id_str, pensada para detectar bloques-ancla standalone, también matchea falsamente celdas de tabla TOC cuyo único contenido es el ID bare — excluyéndolas de recibir link.
Cambios:
- apply_hyperlinks_notion.py --all --apply ejecutado sobre los 7 documentos: Kernel 12, System Prompt 5, Manual 78, Career Canon 2, Aliases 0, Change Log 46, Navigation Brief 0 — total 143 bloques patcheados, 0 errores. (Kernel y Career Canon ya habían sido aplicados individualmente antes de esta corrida — el re-patch fue idempotente, sin efecto adicional.)
- Bug registrado en Bug Tracker: TOC de los 7 documentos no recibe hyperlinks por falso positivo en is_definition_block() — Prioridad 2 MEDIO, Componente Python, Next_Action Patch. Cross-ref: V-MASTER-INDEX (391938be-fc42-8085-b7ad-ff68b601dec4) contiene TOCs duplicadas manualmente, fuera de este pipeline, desactualizada — housekeeping separado, no bloquea este fix.
IDs afectados: ninguno — conversión de texto plano a hipervínculo real sobre IDs ya existentes en los 7 documentos. Census no requiere regeneración.
Write-Back Verification: Kernel re-fetched de forma independiente tras --apply — los 12 links confirmados clickeables con anchors reales (ejemplos verificados: MANUAL:SETUP, KERNEL:DOCUMENTATION-003 ×2, SP:CONSISTENCY, MANUAL:SESSION-CYCLE, KERNEL:OWNERSHIP-002, los 4 GATE-DECISION de la fila 460, los 2 de la fila 483, CANON:OUTPUT-CONTRACT).
Pendiente (fuera de esta entrada):
- Fix de is_definition_block() (excluir btype table_row de la rama "stripped == id_str", o exigir is_heading) — bloquea que los TOCs de los 7 documentos se enlacen. Cambio afecta también al censo (vcensus), requiere revisión de impacto antes de aplicar.
- Documentación transversal formal (KERNEL:ARCHITECTURE-L4, KERNEL:DOCUMENTATION-011, posible ajuste de vantage-hyperlink-loop) — diferida hasta resolver el bug de TOC.
- EXCLUDE_IDS vacío en apply_hyperlinks_notion.py — copiar la lista real de apply_hyperlinks.py (27 IDs) antes de futuras corridas donde esa exclusión importe.
- 3 anchors sin DEF resuelto en la spec (MANUAL:COLD-START-001, ALIASES:DEDUP, SP:CONSISTENCY §9 legacy) — pin explícito, sin cambio en esta entrada.
- V-MASTER-INDEX desactualizado (v9.6.5 propia, docs listados en v9.11.5, IDs obsoletos) — housekeeping separado, sin fecha asignada.
Versión actualizada: 9.11.9 (CHANGELOG). El resto de los fundacionales permanece en v9.11.8 hasta vversions --sync.
---
# v9.11.8 — Fix Raíz: PATCH Puntual Reemplaza Destroy/Rebuild para Hyperlinks (apply_hyperlinks_notion.py) · 2026-08-01
Tipo: [FIX] [ARCHITECTURE]
Alcance: Layer_1/scripts/apply_hyperlinks_notion.py (nuevo, local); Career Canon (2 bloques quote, sección 10 CANON:MAJOR-PROJECTS).
Contexto: Bug reportado por el operador al abrir sesión — "los links de la TOC no hacen nada al click" pese a que vcensus reportaba 209/209 IDs resueltos y vhyperlinks --apply corría sin error. Causa raíz aislada por lectura directa de código (no inferida): vsync_doc.py y vsync_doc_fast.py (push_local_to_notion()) hacen delete-all + create-all sobre TODOS los bloques de la página en cada corrida de 'vdoc local' — cualquier anchor #block-id generado por vhyperlinks queda huérfano en cuanto corre el siguiente sync, porque Notion asigna block-IDs nuevos a los bloques recreados. Confirmado como mecanismo consciente pero mal cerrado: el propio código trae comentarios "TEMPORALMENTE HABILITADO... debe ser deshabilitado después" (v8.5.7) nunca revertidos.
Cambios:
- Nuevo script apply_hyperlinks_notion.py: aplica hyperlinks DIRECTO a bloques de Notion vía PATCH puntual (notion.blocks.update / PATCH /v1/blocks/{id}), preservando block-ID — nunca borra ni recrea bloques para este flujo. Reusa fetch_blocks_recursive/extract_ids_from_block/is_definition_block de generate_census.py (no reimplementa) y vantage_id_rules.py (mismo módulo único de reglas que ya usan normalize_heading_ids.py y apply_hyperlinks.py).
- MAPPING ID→URL ya no es diccionario estático hardcodeado (como en apply_hyperlinks.py, con anchors PENDIENTE_ANCHOR sin resolver) — se construye en cada corrida desde el link_index real de generate_census.py, eliminando de raíz la clase de bug de anchors desactualizados.
- Validado en producción: --doc career_canon --apply, 2 bloques patcheados (quote, sección CANON:MAJOR-PROJECTS), 0 errores. Confirmado por el operador en Notion: link clickeable, block-ID preservado (verificado contra Historial de versiones — edición incremental, no rebuild).
IDs afectados: ninguno — ambos bloques ya contenían los IDs CANON:OUTPUT-CONTRACT-002 y CANON:POSITIONING-N2 en texto plano; el cambio fue solo la conversión a hipervínculo real. Census no requiere regeneración.
Write-Back Verification: confirmado por el operador directamente en Notion (click funcional) — no solo por código de retorno 200 del script.
Pendiente (fuera de esta entrada, explícitamente pineado por el operador para sesión futura):
- 3 anchors sin DEF resuelto en la spec (MANUAL:COLD-START-001, ALIASES:DEDUP, SP:CONSISTENCY §9 legacy) — no se resuelven en este fix, quedan sin link igual que hoy en vcensus.
- EXCLUDE_IDS vacío en apply_hyperlinks_notion.py — copiar la lista real de apply_hyperlinks.py (27 IDs en la última corrida) antes de correr --all sobre documentos donde esa exclusión importe.
- Sin probar aún en Kernel (26 cambios) ni Manual (40 cambios) — mayor volumen de table_row, recomendado --dry-run individual antes de --apply.
- Documentación transversal formal de este hallazgo (KERNEL:ARCHITECTURE-L4, KERNEL:DOCUMENTATION-011, posible actualización del skill vantage-hyperlink-loop) — decisión del operador: diferida a sesión futura por límite de tokens en esta sesión.
- vsync_doc.py / vsync_doc_fast.py NO fueron modificados ni deprecados en esta entrada — siguen existiendo con el mecanismo destroy/rebuild; el operador debe evitar 'vdoc local' sobre documentos con hyperlinks recién aplicados hasta que se decida su reemplazo formal o se documente la restricción de uso.
Versión actualizada: 9.11.8 (CHANGELOG). El resto de los fundacionales permanece en v9.11.7 hasta vversions --sync.
---
# v9.11.7 — Registro Retroactivo: Fix Protección Terminal gate_logic() (commit ca5f1a8, 2026-07-29) · 2026-08-01
Tipo: [FIX] [DOC-RETROACTIVO]
Alcance: Layer_1/scripts/layer_1_run.py (local, código ya en producción desde el 29-jul); Bug Tracker (ticket 3ac938be-fc42-8149-a909-c8a1b426e7e6).
Contexto: El fix real se aplicó el 2026-07-29 vía fix_terminal_protection_layer_1_run.patch (commit ca5f1a8, 04:47), ANTES de que el ticket correspondiente fuera abierto — por eso nunca generó su propia entrada de Changelog en su momento. Un reporte de Devin marcó el hallazgo original ("protección de gate_logic() es código muerto por la línea 772") como implementado; verificación directa contra el código real (layer_1_run.py, main, GitHub) en esta sesión confirmó que la línea 'if current_action: continue' descrita por el ticket ya NO existe — el patch la había reemplazado antes de la apertura del ticket. Falso positivo confirmado, no un bug nuevo.
Cambios (ya vigentes en producción desde el 29-jul, documentados aquí por primera vez):
- layer_1_run.py línea ~842: único mecanismo de protección de estado terminal es ahora gate_logic(entry), invocado antes de gate() (FASE 4).
- gate_logic.py: TERMINAL_ACTIONS = {'Archivar', 'Expirada'} — criterio angosto, alineado con decisión de gobierno 2026-08-01.
IDs afectados: ninguno — cambio de código Python, no de documentación Notion. Census no requiere regeneración.
Verificación: confirmado por Devin y re-verificado independientemente por Claude contra el repo (GitHub, rama main) en esta sesión. Ticket 3ac938be-fc42-8149-a909-c8a1b426e7e6 cerrado como Resuelto (falso positivo), Prioridad 4 CRÍTICO, Fecha_Resolución 2026-08-01.
Nota de alcance — no confundir con B3: este fix resuelve únicamente la capa de PROTECCIÓN de estados terminales (qué registros NO se re-evalúan). Es distinto y no desbloquea automáticamente el bug de EJECUCIÓN de archivado automático (Bug Tracker: "Dedup Caso 5 — Next_Action=Archivar no se ejecuta automáticamente", Status Abierto) — ese bug sigue abierto, y además existe un tercer ticket sin resolver ("Discrepancia de protección de estados terminales": gate_logic.py vs. layer_1_run.py FASE 4) que es prerequisito de diseño antes de construir auto_archive.py (KERNEL:GATE-DECISION-007).
Pendiente (fuera de esta entrada):
- Decisión del operador sobre la discrepancia FASE 4 (protección amplia: cualquier Next_Action no vacío) vs. gate_logic.py (protección angosta: solo Archivar/Expirada) — ticket abierto, Prioridad 3 ALTO.
- Bug "Dedup Caso 5" (archivado automático nunca se ejecuta) — sigue abierto, Prioridad 3 ALTO, sin auto_archive.py construido.
- T3, T5, T7, D3/GAP-03, D4/B6 Caso 4 — heredados, sin tocar esta sesión.
Versión actualizada: 9.11.7 (CHANGELOG). El resto de los fundacionales permanece en v9.11.5/9.11.6 hasta vversions --sync.
---
# v9.11.6 — Manual §6 Sincronizado + Fix normalize_heading_ids.py (ok_legacy_sectioned) · 2026-08-01
Tipo: [FIX] [DOC]
Alcance: Manual (MANUAL:SESSION-CYCLE, §6); Layer_1/scripts/normalize_heading_ids.py (local).
Contexto: Dos hallazgos independientes en la misma sesión. (1) Manual §6 seguía documentando "6 documentos fundacionales + el Census" pese a la expansión a 9 fundacionales vigente desde v9.11.x — drift de conteo detectado por auditoría cruzada con SP:SYNC-RULE. (2) Lectura directa de vantage_id_rules.py y normalize_heading_ids.py reveló que audit() ignoraba en silencio el estado ok_legacy_sectioned (headings aún en formato §N) pese a que el propio módulo lo declara "SIEMPRE candidato a migrar" — confirmado por código, no inferido.
Cambios:
- Manual — MANUAL:SESSION-CYCLE (§6): "Confirma que los 6 documentos fundacionales + el Census..." corregido a "9 documentos fundacionales + el Census". Ejecutado vía contrato determinista (Mistral, pares old_str/new_str, APROBAR_WRITE explícito).
- normalize_heading_ids.py — audit(): condición ampliada de status == "malformed" a status in ("malformed", "ok_legacy_sectioned"); reporte de consola distingue tag [LEGACY]/[MALFORMED]. Diff mínimo, sin cambio de firma ni flags nuevos. py_compile OK.
IDs afectados: ninguno — ambos cambios son de contenido/tooling, no alta/baja de ID canónico. Census no requiere regeneración.
Write-Back Verification: Manual re-fetched de forma independiente tras la escritura — línea corregida confirmada, resto de §6 y del documento byte-idéntico. Script verificado vía py_compile, entregado al operador vía present_files.
Ticket asociado: Bug Tracker 3af938be-fc42-813e-9b50-e286ae7f121a (Resuelto, Prioridad 3 ALTO).
Pendiente (fuera de esta entrada):
- Operador debe reemplazar normalize_heading_ids.py en Layer_1/scripts/ y correr dry-run real para confirmar 0 headings § vivos o detectarlos por primera vez.
- T3 (Documentación Transversal Fase 2), T4 (Census — contradicción a verificar, fetch de esta sesión mostró 0 huérfanos), T5, T7, B3, D3/GAP-03, D4/B6 Caso 4 — heredados, sin tocar esta sesión (detalle completo en handoff de sesión).
- Changelog retroactivo del patch fix_terminal_protection_layer_1_run.patch (2026-07-29) — aún sin decisión.
Versión actualizada: 9.11.6 (CHANGELOG + Manual). El resto de los fundacionales permanece en v9.11.5 hasta vversions --sync.
---
# v9.11.5 — Kernel: Regla de Bloque Único Formalizada en KERNEL:DOCUMENTATION-001 · 2026-08-01
Tipo: [DOC]
Alcance: Kernel (sección 03.1 KERNEL:DOCUMENTATION-001).
Contexto: Durante auditoría de sesión sobre H3 sin ID (Career Canon + Navigation Brief, hallazgo heredado de sesión previa), se confirmó que la corrección ya vivía en v9.11.1–v9.11.3 (atomización + registro CENSUS_SPEC), pero el contrato normativo del Kernel solo fijaba el nivel de heading (### para NN.N) sin exigir explícitamente que el ID canónico viva en la misma línea del heading. El operador confirmó como regla permanente: "todo H3 lleva ID NN.N, sin excepción decorativa".
Cambios:
- Kernel — KERNEL:DOCUMENTATION-001 (§03.1): nuevo párrafo "Regla de Bloque Único", insertado entre "Matriz Tipográfica Congelada" y "Reglas de Migración" — formaliza que todo heading ### declara su ID [PREFIX]:[KEY] en la misma línea que su título, sin excepción decorativa.
IDs afectados: ninguno — extensión de contenido sobre KERNEL:DOCUMENTATION-001, ID ya existente. Census no requiere regeneración.
Write-Back Verification: Kernel re-fetched de forma independiente tras la escritura — párrafo confirmado en posición correcta, resto del documento (17 secciones) byte-idéntico.
Pendiente (fuera de esta entrada): vversions --sync para propagar v9.11.5 a los 8 fundacionales restantes.
Versión actualizada: 9.11.5 (CHANGELOG + Kernel). El resto de los fundacionales permanece en v9.11.4 hasta vversions --sync.
---
# v9.11.4 — Patch de Debug (--debug-id / campo plain) Declarado Permanente en generate_census.py · 2026-07-31
Tipo: [DOC]
Alcance: Layer_1/scripts/generate_census.py (local, sin escritura en Notion salvo este Changelog).
Contexto: El flag --debug-id y el campo plain agregado a cada entrada del link_index se introdujeron ad-hoc en esta sesión para diagnosticar CANON:POSITIONING-N2/N3/N4 y KERNEL:CV-GOLDEN-RULES-001..005 — en ambos casos fue la evidencia real (plain crudo del bloque) la que descartó hipótesis iniciales incorrectas (desempate de pick_best_link, regex de sección) y confirmó la causa estructural real (bloques fusionados fuera de lugar; ausencia total de heading). Sin el patch, ambos fixes se hubieran basado en suposición en vez de verificación directa.
Decisión: el patch queda permanente en el script, no se revierte. Es puramente aditivo — agrega el campo plain a las entradas del link_index y una rama de salida opcional (--debug-id); no modifica pick_best_link(), el flujo normal de vcensus, ni el Markdown exportado a V_ID_CENSUS_PRODUCTION.md.
IDs afectados: ninguno — cambio de tooling, no de documentación Notion. Census no requiere regeneración.
Pendiente (fuera de esta entrada):
- Patch de debug en generate_census.py (campo plain en link_index) — CERRADO por esta entrada, ya no es pendiente.
- SESSION-2026-07-19-A — mencionada como anómalamente abierta en el Ledger en handoffs previos, aún sin investigar.
Versión actualizada: 9.11.4 (CHANGELOG). El resto de los fundacionales permanece en v9.11.3 hasta vversions --sync.
---
# v9.11.3 — Fix: KERNEL:CV-GOLDEN-RULES-001..005 Sin Heading Propio (Deuda desde v9.9.1) · 2026-07-31
Tipo: [FIX]
Alcance: Kernel (sección 10 KERNEL:CV-GOLDEN-RULES).
Contexto: Los 5 IDs llevaban desde v9.9.1 resolviendo con "sección hardcodeada" en el Census, diagnosticado entonces como posible problema de regex del script. --debug-id confirmó la causa real: las 5 reglas vivían como lista numerada simple ("1. Regla #1...") sin ningún heading ni marcador textual con el ID — el único candidato is_def=True en todo el link_index era una celda de tabla en Manual (MANUAL:CV-GOLDEN-RULES-INDEX) apuntando por anchor directo a Notion, no un heading real en Kernel. Distinto del patrón de CANON:POSITIONING-N2/N3/N4 (v9.10.6): ahí había contenido fusionado en el lugar equivocado; aquí simplemente nunca existió heading propio.
Cambios:
- Kernel — sección 10: la lista numerada 1–5 convertida a 5 headings propios (### 10.N KERNEL:CV-GOLDEN-RULES-00N / título), cada uno con su contenido original preservado tal cual. Template Universal de Rechazo, inmediatamente después, sin alteración.
IDs afectados: ninguna alta/baja — los 5 IDs ya existían en CENSUS_SPEC desde v9.9.8; se corrigió su representación estructural en Notion. Census no requiere alta de CENSUS_SPEC, sí regeneración para reflejar sección en vivo.
Write-Back Verification: Kernel re-fetched de forma independiente tras la escritura — 5 headings confirmados, resto del documento (TOC, secciones 1–9, 11–17) byte-idéntico.
Pendiente (fuera de esta entrada):
- Confirmar vcensus post-fix: debería reportar 0 IDs con sección hardcodeada (cierre del último residuo heredado desde v9.9.1).
- Patch de debug en generate_census.py (campo plain en link_index) sigue local, sin decisión de si se mantiene permanente.
Versión actualizada: 9.11.3 (CHANGELOG + Kernel). El resto de los fundacionales permanece en v9.11.2 hasta vversions --sync.
# v9.11.2 — CENSUS_SPEC: Resolución de 9 TBD + Alta de 14 IDs (Homologación v9.11.0/v9.11.1) · 2026-07-31
Alcance: Layer_1/scripts/generate_census.py (CENSUS_SPEC, local).
Contexto: Tras la reintegración de Career Canon (v9.11.0) y la homologación arquitectónica de Kernel/Career Canon/Navigation Brief/Aliases (v9.11.1), CENSUS_SPEC en disco no reflejaba ninguna de las altas de esas dos operaciones — pese a que la entrada v9.11.0 del Changelog afirmaba "CENSUS_SPEC actualizado en esta misma entrada". Auditoría vía --debug-id (patch de debug local) confirmó, ID por ID, sección y nombre reales en vivo antes de escribir cada entrada — cero valores inventados.
Cambios:
- CENSUS_SPEC — Career Canon: alta de CANON:PROFILE-001/002 (§01.1/§01.2) y CANON:OUTPUT-CONTRACT-005 (§12.5).
- CENSUS_SPEC — Kernel: alta de KERNEL:PURPOSE-001 (§01.1), KERNEL:FAIL-PHILOSOPHY-001/002 (§02.1/§02.2), KERNEL:CV-PIPELINE-001/002 (§12.1/§12.2).
- CENSUS_SPEC — Navigation Brief: alta de BRIEF:CONSULTATION-002..006, CORE-ASSETS-001, DISCOVERY-001, GATE-LOGIC-001, CV-PIPELINE-001 (9 IDs, huérfanos desde la atomización v9.11.1).
- CENSUS_SPEC — Navigation Brief: resueltos 9 placeholders "TBD"/"TBD" (AUTHORITY-001, CONSULTATION-001, CROSS-DEPENDENCIES-001/002/003, HOUSEKEEPING-001, PURPOSE-SCOPE-001/002/003) con sección y nombre reales.
IDs afectados: 14 altas + 9 resoluciones de TBD, todas contra IDs ya existentes en Notion (ningún ID nuevo creado en Notion — solo registro local). Census SÍ requería regeneración — ejecutada por el operador.
Verificación: python3 -m py_compile OK. vcensus post-patch: 209/209 resueltos, 0 sin link, 0 huérfanos (antes: 8 sin link + 17 sin registrar/TBD).
Pendiente (fuera de esta entrada):
- 5 KERNEL:CV-GOLDEN-RULES-001..005 con sección hardcodeada — heredado desde v9.9.1, bajo investigación en esta misma sesión.
- vversions --sync para propagar v9.11.1 a Manual/SP/ID Census/VANTAGE Hub.
- Patch de debug (campo plain en link_index) sigue local, sin decisión de si se mantiene permanente.
Versión actualizada: 9.11.2 (CHANGELOG). Cambio 100% local — no aplica a los 8 documentos fundacionales restantes.
---
</content>
<parameter name="position">{"type": "start"}
Tipo: [FIX] [DOC]
# v9.11.1 — Homologación Arquitectónica y Atomización (Aliases + Navigation Brief + Career Canon) · 2026-07-31
Tipo: \[DOC\] \[ARCHITECTURE\]
Alcance: Aliases, Navigation Brief, Career Canon (completos).
Contexto: Contrato de sesión HOMOLOGACIÓN ARQUITECTÓNICA Y ATOMIZACIÓN VANTAGE.
---
Cambios comunes a los 3 documentos:
- Todos los encabezados (## y ###) migrados a formato Bloque Único (ID en línea de heading + título en línea siguiente).
- Tablas pipe convertidas a bloques <table> nativos.
- Atomización de secciones densas (ej: bloques monolíticos divididos en párrafos cortos + listas).
---
Detalles por documento:
- Aliases:
- Tabla DEDUP convertida a nativa.
- Resto de tablas preservadas.
- IDs afectados: 0 nuevos.
- Navigation Brief:
- Atomización de secciones: PURPOSE-SCOPE, CROSS-DEPENDENCIES, MAINTENANCE-CONTRACT, DECISION-TREE.
- IDs afectados: 0 nuevos.
- Career Canon:
- Atomización de bloques densos (ej: Profile ES/EN, Regla de Desempate en Positioning).
- IDs afectados:
- Altas: KERNEL:PURPOSE-001, KERNEL:FAIL-PHILOSOPHY-001/002, KERNEL:CV-PIPELINE-001/002 (5 IDs nuevos en Kernel, derivados de la atomización).
---
Verificación:
- Los 3 documentos re-fetched de forma independiente tras las escrituras.
- Aliases/Navigation Brief: Confirmados sin mismatch estructural.
- Career Canon: 13 secciones, 33 subsecciones y 4 tablas confirmadas correctas.
- Census: Requiere regeneración (CENSUS-SYNC-R1) por los 5 IDs nuevos en Kernel.
---
Pendientes:
- vversions --sync para propagar v9.11.1 a los 9 documentos fundacionales.
- Regenerar Census (ejecutar vcensus).
- Continuar homologación en System Prompt y Manual (según orden de prioridad).
---
# v9.11.0 — Reintegración de Career Canon (Deprecated → Runtime): KPIs, Timeline, Education, Certifications, Major Projects, Derived Outputs Archive · 2026-07-31
Tipo: [DOC] [FEATURE]
Alcance: Career Canon (reestructuración completa de índice y secciones 04–13).
Contexto: El operador identificó que CANON:KPIS (sección I) nunca tenía contenido real en el Runtime — confirmado no como un defecto de formato sino como contenido nunca migrado desde CAREER CANON (DEPRECATED) (37d938be-fc42-800388cfcff6558901d4) al reestructurar el documento. Auditoría diff completa contra la versión deprecada reveló que 8 referencias activas [KPI01]–[KPI07] en Experience Records (§03) y Achievement Library (§05) apuntaban a una sección inexistente — no era contenido faltante cosmético, era una referencia rota en producción. La misma auditoría encontró 4 secciones completas ausentes (Career Timeline, Education, Certifications, Major Projects) y un archivo histórico de Derived Outputs no reintegrado. Dry Run presentado y aprobado ítem por ítem por el operador antes de esta escritura.
Cambios:
- Career Canon — índice superior: expandido de 8 a 13 filas, documentando el nuevo mapeo completo de secciones.
- Career Canon — nueva sección 04 CANON:CAREER-TIMELINE: tabla de 5 filas (C01–C05) con período y país por compañía, ausente en el Runtime desde su consolidación. Reintegrada desde la versión deprecada.
- Career Canon — CANON:ACHIEVEMENTS renumerada de §04 a §05 (sin cambio de contenido).
- Career Canon — nueva sección 06 CANON:KPIS (06.1–06.8, KPI-001–008): resuelve las 8 referencias [KPI01]–[KPI08] previamente rotas. Reintegrada desde la versión deprecada.
- Career Canon — CANON:FACTS §06→§07 (11 subsecciones, sin cambio de contenido).
- Career Canon — nueva sección 08 CANON:EDUCATION y 09 CANON:CERTIFICATIONS.
- Career Canon — nueva sección 10 CANON:MAJOR-PROJECTS (P01–P03).
- Career Canon — CANON:POSITIONING §07→§11 y CANON:OUTPUT-CONTRACT §08→§12.
- Career Canon — nueva sección 13 CANON:DERIVED-OUTPUTS-ARCHIVE.
IDs afectados: 13 IDs nuevos + renombres de sección. Census REQUIERE regeneración (CENSUS-SYNC-R1).
Write-Back Verification: Career Canon re-fetched — 13 secciones, 33 subsecciones y 4 tablas confirmadas.
Versión actualizada: 9.11.0 (CHANGELOG + 9 fundacionales).
---
# v9.10.6 — Fix: Reconstrucción de CANON:POSITIONING-N2/N3/N4 (Bloque Roto y Fuera de Lugar) · 2026-07-31
Tipo: [FIX]
Alcance: Career Canon (sección 07 CANON:POSITIONING).
Contexto: generate_census.py (patch local de debug --debug-id) reveló que CANON:POSITIONING-N2, N3 y N4 no eran headings reales — vivían como texto plano fusionado dentro de un único bloque bajo CANON:EXPERIENCE-C05.
Cambios:
- Career Canon — bullet EN de C05 limpio; sección 07 reconstruida con N1–N4 como headings propios.
IDs afectados: ninguna alta/baja — corrección estructural. Census sí requiere regeneración.
Write-Back Verification: Career Canon re-fetched — C05 limpio, sección 07 con 4 modos correctos.
Versión actualizada: 9.10.6 (CHANGELOG).
---
> El histórico completo del CHANGELOG lo podrás encontrar en ARCHIVO CHANGELOG, en esta pagina de consulta continua solo encontrarás las últimas diez entradas para garantizar la operación y referencia del sistema.
# v9.10.5 — Fix: MANUAL:HEALTHCHECK Restaurado Sin Guión Tras Edición Manual · 2026-07-31
Tipo: [FIX]
Alcance: Manual (sección 11 y sus 2 referencias cruzadas).
Contexto: El operador editó manualmente el Manual en Notion, renombrando MANUAL:HEALTHCHECK a MANUAL:HEALTH-CHECK. Esto rompió 2 referencias cruzadas. Se restauró el ID estándar y se alinearon las referencias.
Cambios:
- Manual — heading sección 11: MANUAL:HEALTH-CHECK → MANUAL:HEALTHCHECK.
- Manual — sección 03 (Filosofía de Fallo) y 09.1: referencias actualizadas a MANUAL:HEALTHCHECK.
- Se mantuvo el nombre de subtítulo "¿Qué es el Census ID?" por instrucción del operador.
Versión actualizada: 9.10.5 (CHANGELOG).
---
# v9.10.4 — Documentación Transversal: SP:SCHEMA Alineado con Schema Vivo de Notion · 2026-07-31
Tipo: [DOC] [FIX]
Alcance: System Prompt (SP:SCHEMA, sección 08).
Contexto: SP:SCHEMA documentaba solo parte de los campos reales de los trackers. Se detectó el gap al intentar cerrar un ticket.
Cambios:
- SP:SCHEMA — Bug Tracker: alta de Fecha_Resolución, Solución, Etiquetas, Archivar, Mantener, Creado.
- SP:SCHEMA — Tasks Tracker: alta de Fecha_Cierre, Archivar, Mantener, Creado.
Versión actualizada: 9.10.4 (CHANGELOG + SYSTEM PROMPT).
---
# v9.10.3 — TOC del Manual y Tabla 08.6 Convertidas a Bloques de Tabla Reales · 2026-07-30
Tipo: [FIX]
Alcance: Manual (TOC / MANUAL:CADENCE-MATRIX).
Contexto: La TOC era texto plano simulando una tabla, lo que generaba fricción visual y de renderizado. Se convirtió a bloques estructurales reales de Notion.
Cambios:
- Manual — TOC: convertida de texto plano a bloque table real (21 filas + header), preservando links (§18–§21).
Versión actualizada: 9.10.3 (CHANGELOG).
---
# v9.10.2 — Corrección de Terminología (Bloque vs. Línea) + Alta de Criterio 6: Concreción de Títulos · 2026-07-30
Tipo: [DOC] [FIX]
Alcance: Manual (MANUAL:PATCH-QUALITY).
Contexto: Ajuste semántico para reflejar que el ID y el título van en un único bloque de heading unido por un br interno, no en líneas separadas de Markdown.
Cambios:
- Manual — MANUAL:PATCH-QUALITY (§15): criterio 1 corregido a "un único bloque de heading... unión por br interno".
- Manual — MANUAL:PATCH-QUALITY (§15): alta de Criterio 6 (Concreción de títulos).
Versión actualizada: 9.10.2 (CHANGELOG).
---
# v9.10.1 — Documentación Transversal: Continuidad ID+Título en Bloque de Encabezado · 2026-07-30
Tipo: [DOC]
Alcance: Manual (MANUAL:PATCH-QUALITY, criterio 1).
Contexto: Formalización de la regla de continuidad ID+título para evitar que procesos automáticos intenten "corregir" el espacio vertical generado por el rendering de Notion.
Versión actualizada: 9.10.1 (CHANGELOG).
---
# v9.10.0 — Auditoría de Jerarquía Tipográfica + Documentación Transversal: Matriz Congelada · 2026-07-30
Tipo: [AUDIT] [DOC]
Alcance: Kernel, Career Canon, Manual.
Contexto: Auditoría determinística para estandarizar encabezados. Se congeló la matriz: # (Documento), ## (Capítulo), ### (Subsección NN.N).
Cambios:
- Kernel: 37 headings migrados de ## a ###.
- Career Canon: 24 headings migrados de ## a ###.
- Manual: Agregado criterio de "Invisibilidad estructural".
Versión actualizada: 9.10.0 (CHANGELOG).
---
# v9.9.9 — Documentación Transversal: Matrices de Estado y Cadencia · 2026-07-29
Tipo: [DOC]
Alcance: Kernel (§09.11), Manual (§08.6).
Contexto: Inyección de matrices de referencia para la máquina de estados y triggers semanales, consolidando información previamente dispersa en prosa.
Versión actualizada: 9.9.9 (CHANGELOG).
---
# v9.9.8 — Normalización de CENSUS_SPEC: Adopción de IDs Huérfanos · 2026-07-29
Tipo: [DOC] [FIX]
Alcance: generate_census.py, CENSUS_SPEC.
Contexto: Actualización del spec para eliminar sufijos -001 legacy que generaban IDs huérfanos. Se alinearon 162/162 IDs.
Versión actualizada: 9.9.8 (CHANGELOG + CENSUS_SPEC).
---
# v9.9.7 — Patch 1 real: Estados Terminales Protegidos + Atomicidad RT-1 · 2026-07-29
Tipo: [FIX] [DOC]
Alcance: gate_logic.py, layer_1_run.py, Dashboard, Kernel §09.10.
Contexto: Implementación del fix real para la precedencia de gate_logic() (estados terminales) y limpieza atómica en el Dashboard para evitar "fantasmas" post-RT-1.
Cambios:
- Código: Definición de TERMINAL_ACTIONS y STATUS_TERMINAL_MAP.
- Documentación: Nuevo KERNEL:GATE-DECISION-010 (Definición de Estados Terminales Protegidos).
Versión actualizada: 9.9.7 (CHANGELOG).
---
# v9.9.6 — Resolución de Auditoría Arquitectónica y Fix de UUIDs · 2026-07-29
Tipo: [AUDIT] [FIX]
Alcance: Scripts de Layer_1, Kernel, Manual.
Contexto: Resolución de controversias sobre el flujo de estados vs. calendario y ownership Python vs. IA.
Cambios:
- Controversias: Separación de diagramas de ciclo de vida vs. cadencia; implementación de Filtro Class B para ingesta IA.
- Hallazgo UUIDs: Diagnóstico de duplicados resultó en falso positivo por truncamiento de logging.
- Matriz: Documentación de 21 transiciones de estado.
Versión actualizada: 9.9.6 (CHANGELOG).
---
# v9.9.5 — Documentación Transversal: vsum.py (Continuidad de Sesiones) · 2026-07-27
Tipo: [DOC]
Alcance: Kernel, Manual, Aliases, System Prompt.
Contexto: Integración documental del script vsum.py para la gestión de transcripts de sesiones e Inbox de Notion.
Versión actualizada: 9.9.5 (CHANGELOG).
---
# v9.9.4 — Recuperación de Manual Post-Incidente de Red + Fix de Anidamiento de Links · 2026-07-26
Tipo: [FIX]
Alcance: Manual (Notion).
Contexto: Restauración manual a un snapshot de v9.9.1 tras fallo de red durante una escritura. Se reaplicaron 9 hipervínculos y se corrigió un bug de anidamiento de links (mention-page).
Cambios:
- Reaplicación de 9 links en §18/§19.
- Fix de anidamiento para dejar el formato [ID](anchor) limpio.
Versión actualizada: 9.9.4 (CHANGELOG).
---
# v9.9.3 — Documentación Transversal: Sistema de Cross-Reference Hyperlinks · 2026-07-26
Tipo: [DOC]
Alcance: Kernel, Manual, Aliases (Notion) + 2 skills locales (fuera de Notion).
Contexto: El Sistema de Cross-Reference Hyperlinks (generate_census.py + apply_hyperlinks.py + vantage_id_rules.py) llevaba operando desde la migración de headings sin tener representación en la documentación fundacional.
Versión actualizada: 9.9.3 (solo esta página — CHANGELOG).
---
# v9.9.2 — Cierre del Dry-Run de apply_hyperlinks.py + Limpieza de Aliases Legacy · 2026-07-26
Tipo: [FIX] [DOC]
Alcance: Layer_1/scripts/apply_hyperlinks.py (local).
Contexto: v9.9.0/v9.9.1 dejaban pendiente correr apply_hyperlinks.py --dry-run sobre los 6 documentos migrados.
Versión actualizada: 9.9.2 (solo esta página — CHANGELOG).
---
# v9.9.1 — Cierre de Verificación Pendiente de v9.9.0: Census 162/162 Confirmado + Manual Verificado Completo · 2026-07-26
Tipo: [DOC]
Alcance: Verificación de cierre, sin cambios de contenido en documentos fundacionales.
Versión actualizada: 9.9.1 (solo esta página — CHANGELOG).
---
# v9.9.0 — Migración de Headings a Formato Canónico VANTAGE (6 documentos) · 2026-07-26
Tipo: [DOC]
Alcance: Aliases, Navigation Brief, System Prompt, Career Canon, Kernel, Manual.
Contexto: Migración estructural de formato de heading en los 6 documentos fundacionales editables, bajo contrato formal, con Gate de verificación por documento.
Cambio de formato: eliminado §; unificado a ## NN PREFIX:KEY / ## NN.N PREFIX:KEY-NNN.
14 IDs renombrados o creados (KERNEL:CONTEXT-INFRASTRUCTURE, SP:DIGITAL-ID-CARD-001, stubs SP, MANUAL:*-001, ALIASES:DEDUP, etc.).
Verificación: generate_census.py — 162/162 IDs resueltos, 0 huérfanos. Write-Back Verification por documento.
Versión actualizada: 9.9.0 (solo CHANGELOG). Resto en v9.8.1 hasta vversions --sync.
---
# v9.8.1 — Cierre de Cross-Reference Hyperlinks Pt 2: apply_hyperlinks.py aplicado a producción (62 hipervínculos) · 2026-07-24
Tipo: [FIX] [DOC]
Alcance: Kernel, Manual, System Prompt, Career Canon (local + Notion) · apply_hyperlinks.py.
Contexto: Cierre del hilo v9.7.9/v9.8.0 — MAPPING/EXCLUDE_IDS actualizados y 62 hipervínculos aplicados a producción.
Cambios: MAPPING Output Contract + POSITIONING-N1..N4; 62 links (Kernel 21, Manual 29, SP 11, Canon 1); push local→Notion.
IDs afectados: ninguno. Census no requiere regeneración.
Versión actualizada: 9.8.1 (CHANGELOG). Resto en v9.8.0 hasta vversions --sync.
---
# v9.8.0 — Fix de generate_census.py (2 bugs de matching de clase) + Diagnóstico completo de EXCLUDE_IDS · 2026-07-24
Tipo: [FIX] [DOC]
Alcance: Layer_1/scripts/generate_census.py (local) + diagnóstico de EXCLUDE_IDS en apply_hyperlinks.py (local, sin escritura aún).
Contexto: Continuación de Cross-Reference Hyperlinks Pt 2 (iniciado en v9.7.9). Al preparar apply_hyperlinks.py --dry-run, se detectó que el anchor de CANON:OUTPUT-CONTRACT en V_ID_CENSUS_PRODUCTION.md apuntaba a Kernel en vez de Career Canon — no era un error de carga manual del CENSUS_SPEC (que ni siquiera contiene anchors), sino un bug de clase en la lógica de resolución de generate_census.py.
Cambios:
- Bug 1 (boundary): is_definition_block() usaba startswith/in sin boundary check, permitiendo que un ID más largo (CANON:OUTPUT-CONTRACT-001) contara como definición del ID corto (CANON:OUTPUT-CONTRACT). Fix: nueva función _starts_with_id_boundary() aplicada en las ramas de nomenclatura (a)/(b), línea ~393–394.
- Bug 2 (regex de formato, causa raíz probable): SECTION_HEADING_PREFIX_RE solo reconocía el formato legacy §N — ID (con guion largo), no el formato nuevo §N ID (sin separador) aplicado transversalmente en v9.7.9. Esto significaba que ningún heading normalizado en la operación de v9.7.9 calificaba como definición real bajo el regex viejo. Fix: regex extendido con grupo opcional (?:[—-]\s*)?, más nueva función _contains_id_boundary() para la condición adicional f"ID:{id_str}" in plain (mismo patrón de bug, sin exigir heading).
- Verificado en producción tras ambos fixes: 129/129 IDs resueltos, 0 sin link, sin regresión. CANON:OUTPUT-CONTRACT a -004 ahora resuelven correctamente contra Career Canon (377938be...8089...), no contra Kernel (...805e...) ni Manual (caso adicional de -001 destapado por el mismo bug tras el primer fix).
- Efecto secundario detectado (visibilidad nueva, no bug nuevo): 7 IDs ALIASES:* (de los 8 dados de alta en v9.7.9) no están en CENSUS_SPEC — antes invisibles porque el regex viejo ni siquiera los reconocía como headings. Quedan pendientes de alta (ver Pendiente).
Diagnóstico de EXCLUDE_IDS (apply_hyperlinks.py, local, sin escritura ejecutada aún): de los 29 IDs en la lista de exclusión histórica (documentada desde v9.7.4), confirmado contra el census post-fix:
- 26 IDs (familias EXPERIENCE-C01..C05, KPI-001..008, FACT-001..008, UF-001..003) ya resuelven correctamente a Career Canon tras el fix — la razón original de su exclusión (colisión de anchor) ya no aplica. Candidatos a remoción de EXCLUDE_IDS antes de la próxima corrida.
- CANON:POSITIONING-N1..N4 (4 IDs): sigue roto. Causa raíz confirmada — Manual §19 (MANUAL:POSITIONING-CRITERIA) tiene una tabla-índice con el ID exacto entre backticks solitarios (CANON:POSITIONING-N1), lo cual dispara la condición stripped == id_str en is_definition_block() sin exigir heading. Como Manual (DOC_PRIORITY=3) gana por prioridad sobre Career Canon (DOC_PRIORITY=4) en empate is_def=True, la definición real pierde. Tercer patrón de bug de la misma clase (matching parcial de texto vs. tabla-índice con match exacto) — requiere refactor más profundo (regla de "doc dueño del prefijo gana por default"), no un parche de una línea. Debe permanecer excluido hasta ese fix.
- 3 IDs restantes (KERNEL:BOOTSTRAP-001, KERNEL:PATCH-QUALITY-001, CANON:ARCHIVO-VANTAGE) sin relación con este bug — exclusión por razones propias ya documentadas en el script.
Write-Back Verification: no aplica a Notion — generate_census.py es script local (filesystem), sin escritura en documentos fundacionales. Verificado por corrida repetida de vcensus (Terminal): 129/129 resueltos, 0 sin link, confirmado en ambas iteraciones del fix.
IDs afectados: ninguna alta/baja de ID canónico en Notion — cambio 100% local a la lógica de resolución del script. CENSUS_SPEC en sí no fue editado en esta entrada. Census no requiere regeneración en Notion; sí fue regenerado localmente (V_ID_CENSUS_PRODUCTION.md).
Pendiente (fuera de esta entrada):
- Agregar las 7 filas ALIASES:* faltantes a CENSUS_SPEC — mismo ticket ALTO "Modificar generate_census.py" ya existente en Tasks Tracker, ahora con alcance concreto.
- Ejecutar limpieza de EXCLUDE_IDS en apply_hyperlinks.py: remover los 26 IDs ya sanados, mantener excluidos CANON:POSITIONING-N1..N4 + los 3 sin relación.
- Correr apply_hyperlinks.py --dry-run sobre el estado post-limpieza de EXCLUDE_IDS — no corrido aún.
- Ticket nuevo candidato (no logueado aún en Bug Tracker): refactor de is_definition_block() para resolver el patrón "tabla-índice con ID en backticks solitarios cuenta como definición" — bug de clase #3, afecta cualquier prefijo con doc dueño distinto de donde aparece en tabla de referencia narrativa. Candidato ALTO, ya bloqueó una resolución real (CANON:POSITIONING-N1..N4).
Versión actualizada: 9.8.0 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.7.9 hasta que el operador corra verify_versions.py --sync.
---
# v9.7.9 — Normalización Transversal Heading-ID + Cross-Reference (6 documentos, 63 diffs) + Consolidación Output Contract · 2026-07-23
Tipo: [DOC]
Alcance: SYSTEM PROMPT (9 IDs), NAVIGATION BRIEF (11 IDs), ALIASES (8 IDs nuevos, esquema ALIASES:KEY), CAREER CANON (33 IDs, incluye alta/baja en Output Contract), KERNEL (1 referencia, §14), MANUAL (1 referencia, §20).
Contexto: Operación de normalización transversal para unificar el formato de heading-ID en toda la suite documental a ## §N PREFIX:KEY / ## Título (dos líneas, misma jerarquía tipográfica ##/##), reemplazando formatos mixtos previos (una línea con guión largo, IDs sueltos sin heading propio, o ausencia total de esquema PREFIX:KEY en Aliases). Ejecutada en dos tramos: DRY RUN inicial delegado a Mistral (rechazado en 2 rondas por desviaciones de contrato — tareas no solicitadas en Aliases, omisiones en Career Canon, jerarquía tipográfica inconsistente), tercera ronda aprobada tras corrección manual del mapeo de Output Contract; ejecución final (63 diffs) realizada directamente por Claude vía Notion MCP tras detectarse que el reporte de éxito de Mistral para Career Canon ("8/8 verificado PASS") era un falso positivo no confirmado por re-fetch real.
Cambios:
- SYSTEM PROMPT (9 IDs: §2, §4–§10, §12): unificados a formato de 2 líneas. Corregido en el proceso un error de numeración propio de esta operación — SP:ID-CONNECTORS y SP:VERSION-CHECK-TOOL estaban invertidos entre §10/§12 respecto al documento real; resuelto contra el documento en vivo, no contra el mapeo original.
- NAVIGATION BRIEF (11 IDs, §1–§11): normalizado esquema inconsistente ID:BRIEF:001/ID: BRIEF:002 (con/sin espacio) + numeral arábigo duplicado en título, a §N BRIEF:00N / título limpio.
- ALIASES (8 IDs nuevos): alta de esquema ALIASES:KEY inexistente previamente — documento tenía cero IDs canónicos, solo numeración temática # N — Título. Nuevo esquema: SESSION-CYCLE, RUNTIME, DISCOVERY, PASSIVE-INTAKE, VERSION-CONTROL, DASHBOARD, CV-PIPELINE, DEDUP.
- CAREER CANON (33 IDs, §0–§8.4): normalización completa — secciones principales §0–§7 (antes letras A/B/D/H/I/J/K sin número), subsecciones §3.1–§3.5 (C01–C05), §5.1–§5.8 (KPI01–08), §6.1–§6.11 (CF01–08 + UF01–03), §7.1–§7.4 (N1–N4, sufijo semántico preservado por decisión explícita del operador). Output Contract (§8) consolidado con alta/baja de ID: dados de baja CANON:OUTPUT-CONTRACT-001 (formato viejo, heading corrupto con residuos de un intento previo de reformateo), CANON:OUTPUT-CONTRACT-SKELETON-001, CANON:FIGMA-TAG-SCHEMA, CANON:TAG-REGISTRY, CANON:OUTPUT-CONTRACT-TAGREGISTRY-001 (residuo huérfano sin función real, no un ID válido paralelo pese a aparentarlo). Dados de alta: CANON:OUTPUT-CONTRACT (padre) + -001 Golden Skeleton, -002 Figma Tags, -003 Tag Registry, -004 Positioning Modes — sufijo numérico aplicado por ser 4 piezas de granularidad del mismo contrato padre, no conceptos independientes (mismo criterio que C01–C05 y KPI01–08).
- KERNEL §14 (KERNEL:NAMING-CONVENTION): referencia CANON:OUTPUT-CONTRACT-001 → CANON:OUTPUT-CONTRACT (ID padre renombrado).
- MANUAL §20 (MANUAL:GOLDEN-SKELETON-REF): referencia CANON:OUTPUT-CONTRACT-SKELETON-001 → CANON:OUTPUT-CONTRACT-001 (Golden Skeleton bajo nuevo esquema numérico). MANUAL §19 (CANON:POSITIONING-N1–N4) verificado intacto, sin cambio — fuera de alcance de esta operación.
Write-Back Verification: re-fetch en vivo de Career Canon, Kernel y Manual tras la ejecución directa por Claude — los 33 diffs de Career Canon confirmados verbatim (incluyendo ausencia total de los 6 IDs viejos dados de baja en el documento), §14 de Kernel y §20 de Manual confirmados sin mismatch. System Prompt, Navigation Brief y Aliases verificados en tramo previo de la misma sesión.
IDs afectados — CENSUS-SYNC-R1 disparado: alta de CANON:OUTPUT-CONTRACT, -001, -002, -003, -004; baja de CANON:OUTPUT-CONTRACT-001 (formato viejo), CANON:OUTPUT-CONTRACT-SKELETON-001, CANON:FIGMA-TAG-SCHEMA, CANON:TAG-REGISTRY, CANON:OUTPUT-CONTRACT-TAGREGISTRY-001. Census regenerado en esta sesión vía parche a generate_census.py (CENSUS_SPEC, bloque Output Contract) — resultado vcensus: 129/129 IDs resueltos, 0 sin link, 0 huérfanos.
Pendiente (fuera de esta entrada): verificar si el resto de CENSUS_SPEC para Career Canon (secciones §1–§7, fuera del bloque Output Contract parcheado) sigue usando el esquema de letras viejo (§A, §B...) en vez de los números §1–§7 aplicados en esta operación — no auditado en esta sesión, riesgo de inconsistencia parcial en el spec. Pendiente heredado: cross-reference hyperlinks (Kernel/Manual) usando generate_id_inventory.py + apply_hyperlinks.py sobre los IDs recién normalizados.
Versión actualizada: 9.7.9 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.7.8 hasta que el operador corra verify_versions.py --sync.
---
# v9.7.8 — Centralización de Skills VANTAGE en MCP Server / Single Source of Truth (/skills/) · 2026-07-23
Tipo: [DOC] [INFRA]
Alcance: KERNEL (KERNEL:ARCHITECTURE-L4, §4) + MANUAL (§8.1, bloque vgit).
Contexto: El operador centralizó el sistema de Skills VANTAGE en /skills/ como single source of truth (12 .skill files + index.json + index.html), migró GitHub Pages de la rama dev/layer-2 a main, y extendió git_sync.py (motor de vgit) para detectar .skill nuevos y regenerar index.json en el mismo commit+push. Se ejecutó vantage-documentacion-transversal-propuesta seguido de -implementacion para reflejar este cambio en Kernel y Manual, ambos con gap total previo (ninguna mención de Skills/MCP filesystem en L4). Se detectó además que Kernel §4 citaba el repo como jhs-pipeline, nombre desactualizado — corregido a VANTAGE.
Cambios:
- KERNEL:ARCHITECTURE-L4 (§4): agregado párrafo "Skills Distribution — Single Source of Truth" documentando /skills/, GitHub Pages en main, extensión de git_sync.py, y los dos consumidores (Claude Desktop vía MCP filesystem local, Devin Desktop vía devin mcp add). Corregido repo jhs-pipeline → VANTAGE.
- MANUAL §8.1 (bloque vgit): agregado párrafo "Extensión reciente — Skills Distribution" aclarando que la detección de /skills/ es el mismo mecanismo de auto-sync ya documentado, no un flujo nuevo.
- Tasks Tracker: creados 2 tickets (MEDIO) — "GitHub Actions para auto-regenerar index.json" (3a6938be-fc42-815e-949d-ca3997d55d90) y "Test end-to-end de nuevas skills (Devin + Claude Desktop)" (3a6938be-fc42-81c9-ac7d-f3146adba8ce").
- Tasks Tracker: creado 1 ticket adicional (MEDIO) de ingeniería inversa — "Adoptar fortalezas del Brief de Skills MCP en skills de documentación transversal" (3a6938be-fc42-810b-ab49-ef8784093f39`), a partir de 4 fortalezas identificadas en el brief recibido esta sesión (resumen ejecutivo Antes/Después, auto-señalamiento de incertidumbre, distinción explícita de fases con gate, nodos candidatos con justificación tentativa).
- [FIX] Layer_1/scripts/layer_1_run.py — mismo patrón de defecto ya visto en VL3 (Fuente), detectado tras correr vl1: VM_Scope y Fetch se escribían como rich_text, pero el VANTAGE TRACKER los tiene como select (VM_Scope: Alto/Bajo; Fetch: Accesible/Bloqueado), causando rechazo de escritura ("VM_Scope is expected to be select", "Fetch is expected to be select") sin detener el pipeline (Fases 1–5 completaron igual, 45 registros procesados). Confirmado contra schema real de Notion antes de tocar código — los valores generados por get_vm_scope() y el literal "Bloqueado" ya coincidían verbatim con las opciones del select, sin requerir clamp adicional (a diferencia de Fuente). Corregidas ambas escrituras a {"select": {"name": ...}}, alineado con Role_Class/Status en las mismas llamadas, que ya usaban el tipo correcto. Barrido de verificación (grep -n "rich_text" sobre el archivo completo) confirmó que no quedan más casos del mismo defecto — las 2 ocurrencias restantes son el helper de lectura txt() (correcto) y Next_Action (correcto, campo de texto libre en el schema real, no select).
- Validado en producción por el operador: corrida de vl1 post-parche — Fase 1 escribió 18 registros de VM_Scope/Source_Type sin ningún error de tipo (vs. ~18 fallos repetidos en la corrida previa al fix), Fase 2 marcó 2 links muertos vs Fetch sin error. Ready-to-Apply se mantuvo consistente en 3. Hallazgo menor no bloqueante: el log de Fase 3 reportó "Scoring: Sin cambios" mientras el resumen final de la misma corrida reportaba "Scoring v6.4: 36 cambios" — aparente discrepancia de conteo entre el log por fase y el acumulado del resumen; no afectó la integridad de datos (Ready-to-Apply consistente), candidato a ticket BAJO de claridad de logging, no registrado aún.
Write-Back Verification: pendiente — re-fetch de Kernel y Manual a ejecutar inmediatamente después de esta entrada de Changelog, en la misma sesión.
IDs afectados: ninguna alta/baja de ID canónico — adiciones de contenido bajo KERNEL:ARCHITECTURE-L4, ID ya existente, y bajo sección §8.1 del Manual sin ID propio nuevo. Census no requiere regeneración (KERNEL:CENSUS-SYNC Regla 1 no se dispara).
Pendiente (fuera de esta entrada): decidir si git_sync.py extendido a /skills/ amerita mención en KERNEL:DOCUMENTATION-005 (Convención de Anuncio de Skills) — no evaluado en esta sesión por estar fuera del alcance del brief original.
Versión actualizada: 9.7.8 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.7.7 hasta que el operador corra verify_versions.py --sync.
- [CIERRE] Ticket "Adoptar fortalezas del Brief de Skills MCP en skills de documentación transversal" (3a6938be-fc42-810b-ab49-ef8784093f39) cerrado (Status: Hecho). Las 4 fortalezas identificadas se aplicaron directamente a ambos skills locales (sin DRY RUN, autorizado explícitamente por el operador): en vantage-documentacion-transversal-propuesta/SKILL.md — Paso 3 ahora exige justificación tentativa por nodo candidato ("probablemente X porque Y"); Paso 4 agrega resumen ejecutivo Antes/Después como primer elemento, sección de incertidumbre auto-señalada (no omitible, se declara vacía si no aplica), y gate de fase como texto literal visible en el entregable (FASE 1 COMPLETA — SOLO MAPEO...). En vantage-documentacion-transversal-implementacion/SKILL.md — ajuste de compatibilidad: reconoce el nuevo formato de entrada de Fase 1 y declara explícitamente si falta alguno de los tres elementos nuevos antes de generar el DRY RUN. Cambio 100% local (filesystem), sin alta/baja de ID canónico. Census no requiere regeneración.
- [POST-CIERRE — SESSION-20260723-A] Census post-cierre detectó mismatch de sufijo SP:ID-CONNECTORS-001 (CENSUS_SPEC, línea 141 de generate_census.py) vs. SP:ID-CONNECTORS (ID real en SYSTEM PROMPT) — corregido vía sed local, sin escritura en Notion; vcensus re-confirmó 130/130 resueltos, 0 huérfanos.
- [SESSION-20260723-B — Prompt Library] Consolidación de 6 post-mortems de corridas de búsqueda (Perplexity/Comet L1 ×3 vía documento adjunto; Gemini, Grok, You.com L2 ×3 vía texto en sesión) en un análisis comparativo de patrones repetidos. 4 parches aplicados vía notion-update-page (update_content) sin DRY RUN previo — autorizado explícitamente por el operador ("yep"): (1) Prompt A (368938be-fc42-8162-ae48-d48970a729dc) — Accepted Seniority: Head (IC only) ahora remite a criterio de verificación explícito en INCLUSION RULES (title contiene "Head" AND JD sin lenguaje de gestión de personas; si no verificable, fetch_status: needs_verification); INCLUSION RULES — nuevas definiciones operacionales de Company identified (rechaza placeholders genéricos tipo "Empresa confidencial"/"Importante empresa") y Active posting (HTTP 200 AND CTA visible AND ≤21 días, fecha ausente → needs_verification); fit remains strong reemplazado por fit_strong con criterio verificable (≥2 de: industria en lista, visual_signal en título, seniority exacto); SOURCE BUCKETS — nota de alcance aclarando que la política de agregadores como fuente de descubrimiento vs. resultado final es decisión de cada wrapper, no del Prompt Base. (2–4) L2 - Wrapper Gemini (368938be-fc42-8139-b6a7-ee467f6c4584), L2 - Wrapper Grok (368938be-fc42-8145-944d-d15245b6e65e), L2 - Wrapper you.com (368938be-fc42-81c8-95cd-d8d75ff3abe4) — mismo parche en SEARCH SCOPE en los 3: agregadores (LinkedIn/OCC/Indeed/Computrabajo/Bumeran) pasan de "Never search"/"Forbidden" en bloque a "permitido solo para descubrimiento, prohibido como fuente final de datos", respondiendo al hallazgo de Gemini/Grok/You.com de que la exclusión total dejaba fuera ~80% del inventario real de CDMX (concentrado en agregadores por baja penetración de ATS directo en el mercado local). Ningún wrapper L1 (Career Sites/LinkedIn/Aggregators) fue tocado — sus hallazgos de post-mortem fueron de calidad de extracción (Workday/JS dinámico) y ambigüedad
Write-Back Verification: re-fetch de Prompt A y L2-Gemini tras la escritura — cambios confirmados verbatim, sin mismatch; L2-Grok y L2-you.com confirmados por retorno exitoso de update_content (mismo parche, no re-fetched individualmente por economía de tokens).
IDs afectados: ninguno — los 4 documentos son Prompt Bases/Wrappers de Prompt Library, fuera del namespace PREFIX:KEY de los 9 fundacionales. Census no requiere regeneración.
Versión: sin cambio — esta entrada se documenta como viñeta adicional bajo v9.7.8 por instrucción explícita del operador ("no version update"). Los 4 documentos parcheados no forman parte de la Regla de Versión Única (SP:SYNC-RULE), por lo que no aplica el requisito de actualizar la propiedad Versión en la misma operación.
---
# v9.7.7 — Corrección de Inconsistencias Archivar/Status en Task Tracker + Fix de IDs en vantage-tidy-bug-task-tracker · 2026-07-22
Tipo: [FIX]
Alcance: Tasks Tracker (2 páginas) + vantage-tidy-bug-task-tracker/SKILL.md (local).
Contexto: Auditoría exhaustiva de Bug/Task Tracker vía Terminal (dump completo, 31/31 filas — 10 Bug + 21 Task) tras intento previo vía notion-search. Confirmó cero candidatos de archivado por Status terminal, pero detectó 2 tickets con Archivar=true inconsistente con su Status real.
Cambios:
- vantage-tidy-bug-task-tracker/SKILL.md: corregido par Bug Tracker DB ID/COL ID invertido (mismo patrón que v9.7.1, drift no propagado a este segundo skill). Cambio local, ya reportado en entrada v9.7.6.
- Task Tracker — "Convertir referencias cruzadas a hyperlinks" (39e938be-fc42-81c0-ac8b-e95eb4a0e835): Archivar true→false. Trabajo sigue activo (51/82 hyperlinks aplicados en v9.7.4, 31 IDs pendientes).
- Task Tracker — "Normalizar fundacionales: NUEVE" (3a3938be-fc42-814f-bcdc-ce1a48cf1916): Status Pendiente→Hecho. Confirmado vía archivos subidos por el operador (verify_versions.py DOC_KEYS=9 líneas, resolver_registry_v2.json document_registry con BRIEF+VANTAGE) que el conteo 7→9 está completo en Notion, registry y script.
Write-Back Verification: re-fetch de ambas páginas de Tasks Tracker tras la escritura — sin mismatch.
IDs afectados: ninguna alta/baja de ID canónico. Census no requiere regeneración.
Pendiente (fuera de esta entrada): discrepancia --check entre MANUAL §6 (lo describe como activo) y vantage-session-open.skill/KERNEL (lo declaran eliminado v9.6.2) — sin resolver, requiere vantage-documentacion-transversal-propuesta en próxima sesión.
Versión actualizada: 9.7.7 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.7.6 hasta que el operador corra verify_versions.py --sync.
---
# v9.7.6 — Normalización de Links y Referencias en Filesystem · 2026-07-22
Tipo: [FIX]
Alcance: Filesystem local (~/Documents/04-Vantage_CV/Pipeline/).
Contexto: Corrección de links rotos y referencias obsoletas identificados en el handoff de sesión SESSION-20260722-H. Los links apuntaban a URLs incorrectas (notion.so en lugar de notion.com) o a IDs renombrados (KERNEL:SCHEMA-008 → KERNEL:DOCUMENTATION-009).
Cambios:
- Reemplazo masivo de notion.so/ → notion.com/ en todos los archivos del Pipeline (incluyendo subdirectorios).
- Actualización de KERNEL:SCHEMA-008 → KERNEL:DOCUMENTATION-009 en todos los archivos.
- Búsqueda exhaustiva de KERNEL:FAIL-PHILOSOPHY (sin coincidencias en archivos locales; pendiente verificación en Notion).
- Resolución parcial de ticket de huérfanos: KERNEL:SCHEMA-008 confirmado como no existente (eliminación de referencias pendiente), BRIEF:001/BRIEF:011/SP:SYNC-RULE verificados como existentes con contenido válido (morfología de IDs de BRIEF pendiente de normalización en siguiente Handoff).
- [FIX] vantage-tidy-bug-task-tracker/SKILL.md: corregido el par Bug Tracker de DB ID 36e938be-fc42-81f8-8c6f-000b6769ba03 / COL ID 36e938be-fc42-81bd-9e1f-dc360b3b45f5 (invertido) a DB ID 36e938be-fc42-81bd-9e1f-dc360b3b45f5 / COL ID 36e938be-fc42-81f8-8c6f-000b6769ba03, alineado con KERNEL:TRACKER-SCHEMA-001 y con la corrección ya aplicada en vantage-create-bug-task/SKILL.md (v9.7.1) — mismo patrón de drift no propagado, confirmado por fetch en vivo de ambos trackers en esta sesión. Cambio 100% local (filesystem), sin escritura en Notion.
Write-Back Verification: Validación post-ejecución con grep -r — sin instancias remanentes de notion.so o KERNEL:SCHEMA-008.
IDs afectados: Ninguno en documentos fundacionales — cambios locales en filesystem.
Pendiente (fuera de esta entrada): Verificar KERNEL:FAIL-PHILOSOPHY en Notion (no encontrado en archivos locales).
Versión actualizada: 9.7.6 (solo esta página — CHANGELOG).
# v9.7.5 — Excepción de Versión para Memoria de Sesión de Claude en SP:SYNC-RULE · 2026-07-22
Tipo: [DOC]
Alcance: SYSTEM PROMPT (SP:SYNC-RULE).
Contexto: El operador señaló un patrón recurrente: al abrir sesión, Claude comparaba la cifra de versión traída en su memoria persistente (entre sesiones) contra la versión live recuperada de Notion, y reportaba cualquier diferencia como discrepancia/red flag — pese a que esto es esperado dado que el operador abre y cierra sesiones asíncronas sobre distintos pendientes. La Regla de Versión Única de SP:SYNC-RULE nunca distinguía este caso del de una discrepancia real entre los nueve documentos fundacionales.
Cambios:
- SP:SYNC-RULE: agregado párrafo de excepción inmediatamente después de la Regla de Versión Única, acotando su alcance exclusivamente a discrepancias entre los nueve fundacionales entre sí. Aclara que una diferencia entre la memoria de Claude y la versión live no constituye discrepancia bajo SP:SYNC-RULE ni SP:CONSISTENCY, y que Claude debe adoptar la versión live silenciosamente sin reportarlo.
- Memoria persistente de Claude (fuera de Notion): agregada regla equivalente para reforzar el comportamiento a nivel de sesión.
- [FIX] Alineación de rutas de V_ID_CENSUS_PRODUCTION.md entre generate_census.py y health_check.py (ahora en /Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/data/).
- [FIX] Alineación de rutas de salida de apply_hyperlinks.py (diff-out) y generate_id_inventory.py (out_dir) a /Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/data/. diagnose_kernel_blocks.py no requiere cambios (sin output de archivo).
- [FIX] Layer_3/scripts/layer_3_mail.py — _extract_body() forzaba utf-8/errors="ignore" sin consultar part.get_content_charset(), corrompiendo URLs de LinkedIn (mojibake) y causando descarte silencioso de vacantes válidas (0/150 creadas en corrida previa). Nueva función _decode_part() respeta el charset real declarado por cada part, con errors="replace" en vez de ignore.
- [FIX] Layer_3/scripts/layer_3_mail.py — propiedad Fuente se mandaba como rich_text; el VANTAGE TRACKER la tiene como select (Agregador, Career Page Oficial, Indeed, Other, Computrabajo, LinkedIn), causando rechazo 100% de escrituras ("Fuente is expected to be select"). Agregada constante NOTION_FUENTE_OPTIONS con doble clamp (interno VALID_RAW_SOURCES → real Notion) y cambio de tipo a select.
- [DOC] KERNEL:GATE-DECISION-009 — Nueva sección §9.9 en KERNEL (Escalamiento de Pendientes a Tickets). Define 3 niveles de escalamiento (Nivel 1: Handoff/Ledger; Nivel 2: Sugerencia con confirmación; Nivel 3: Automático) y resuelve puntos de fricción: umbral de iteraciones como criterio orientativo, re-evaluación Nivel 2→3 con evidencia dura, y alineación con SP:CONSISTENCY §5.
- [INFRA] Split del skill local vantage-documentacion-transversal en dos entidades independientes: vantage-documentacion-transversal-propuesta (Fase 1 — mapeo de nodos, solo lectura) y vantage-documentacion-transversal-implementacion (Fase 2 — DRY RUN, inyección, write-back, changelog/versión). Objetivo: eficiencia de tokens al cargar solo la fase requerida. Ambos skills heredan intacto el contrato de MANUAL:PATCH-QUALITY-001 (5 filtros), los tokens válidos de APROBAR_WRITE, y el mecanismo de Write-Back Verification del skill original. El skill único queda deprecado (renombrado .deprecated) por el operador en /Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Skills/. Cambio 100% local (filesystem) — sin alta/baja de ID canónico en Notion.
- [DOC] Referencia cruzada bidireccional entre KERNEL:GATE-DECISION-009 (§9.9) y MANUAL:SESSION-CYCLE-001 (§6). Contexto: handoff de sesión SESSION-20260722-F identificó que un ticket citado ("GATE-DECISION-009 ↔ Manual §6") no existía como tal en Tasks Tracker, y que un DRY RUN previo estaba generado contra un estado obsoleto del Kernel (solo Nivel 1, sin Nivel 2/3 — ambos ya presentes en vivo). Se verificó en vivo que KERNEL §9.9 ya tenía los 3 niveles completos y que Manual §6 ya estaba reescrito; el único gap real era la ausencia de referencia cruzada entre ambos. Cambios: (1) KERNEL §9.9, Nivel 1 — línea "Acción" ahora remite a Manual §6 para el detalle operativo de registro dentro del ciclo de sesión; (2) KERNEL §9.9 — nuevo párrafo de cierre tras la tabla de resolución de fricciones, remitiendo a Manual §6 para la implementación práctica del escalamiento; (3) MANUAL §6, sección "Qué hacer si algo no cuadra" — nuevo ítem remitiendo a KERNEL §9.9 para la lógica de los 3 niveles. Escrito autorizado por el operador sin DRY RUN previo (excepción explícita en sesión). IDs afectados: ninguna alta/baja de ID canónico — adiciones de contenido bajo IDs ya existentes (KERNEL:GATE-DECISION-009, MANUAL:SESSION-CYCLE-001). Census pendiente de regenerar a solicitud del operador antes de cierre de sesión. Pendiente: ticket de Tasks Tracker "(Task) Manual §6 describe flujo --check ya eliminado" sigue marcado Pendiente pese a que §6 ya está reescrito — posible drift Tracker↔Documento, verificar/cerrar en próxima sesión.
Write-Back Verification: re-fetch de SYSTEM PROMPT tras la escritura — párrafo confirmado verbatim, sin mismatch.
IDs afectados: ninguna alta/baja de ID canónico — adición de contenido bajo SP:SYNC-RULE, ID ya existente. Census no requiere regeneración.
Pendiente (fuera de esta entrada): ninguno nuevo identificado en esta entrada.
- [SESSION-20260722-H] Creados 3 tickets vía escalamiento KERNEL:GATE-DECISION-009 a partir del Handoff consolidado (SESSION-D+E): (1) Bug ALTO — sesiones huérfanas recurrentes sin cierre en Session Ledger (Nivel 3, evidencia dura del propio Ledger); (2) Bug ALTO — Dedup Caso 5 (Next_Action=Archivar no se ejecuta automáticamente) (Nivel 3, evidencia dura del Handoff); (3) Task ALTO — Navigation Brief, ejecutar Notion writes ya aprobadas en dry run (Nivel 2, APROBAR_WRITE explícito del operador). Los tres quedan fuera de reporte futuro en Handoff/Ledger, según KERNEL:GATE-DECISION-009. Se inició vantage-tidy-bug-task-tracker, bloqueada por límite de tokens de sesión — query_data_sources/query_database_view siguen bloqueadas en este plan; corrida completa pendiente vía Terminal en próxima sesión.
Versión actualizada: 9.7.5 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.7.4 hasta que el operador corra verify_versions.py --sync.
---
# v9.7.4 — Aplicación de Hipervínculos en ACTIVE (51) + Fix de Permisos Read-Only Bloqueante · 2026-07-22
Tipo: [DOC] [FIX]
Alcance: apply_hyperlinks.py (local) + 4 archivos en Documentación/ACTIVE/ (Kernel.md, Manual.md, System Prompt.md, Career Canon.md).
Contexto: --apply falló con PermissionError: [Errno 13] al intentar escribir sobre archivos en modo 444 (read-only, canonizado intencionalmente desde v9.5.9 para forzar Notion como única fuente de verdad). El script nunca contempló hacer chmod temporal antes de escribir — bloqueante no anticipado en el diseño original de v9.5.9.
Cambios:
- Diagnóstico confirmado vía ls -la, ls -lO, stat: permiso Unix estándar -r--r--r--, sin uchg de Finder ni ACL extendida — descartadas ambas hipótesis antes de aplicar el fix.
- Operador aplicó chmod u+w sobre los 4 .md, corrió apply_hyperlinks.py --apply con éxito: 51 hipervínculos aplicados (Kernel 19, Manual 26, System Prompt 6, Career Canon 0), 31 IDs excluidos de esta corrida (EXCLUDE_IDS del script).
- Diff (dry_run_hyperlinks.diff) auditado verbatim contra el Kernel real fetched en esta sesión — anchors confirmados correctos, sin links fabricados ni destinos incorrectos.
- chmod 444 restaurado por el operador sobre los 4 archivos post-escritura, preservando el patrón read-only canónico.
Write-Back Verification: no aplica a Notion — cambio 100% local (filesystem del operador). Verificado por el resumen de salida del script (51/51 aplicados) y por auditoría directa del diff contra el Kernel en vivo.
IDs afectados: ninguno — cambio de formato (hipervínculos) sobre contenido ya existente, sin alta/baja de ID canónico. Census no requiere regeneración.
Pendiente (fuera de esta entrada): decidir si apply_hyperlinks.py debe automatizar chmod +w/chmod 444 en su propio flujo (candidato a ticket Bug/Task Tracker); reparar los 2 destinos de link rotos preexistentes (KERNEL:FAIL-PHILOSOPHY → texto plano (V | KERNEL); KERNEL:SESSION-LEDGER/SP:SYNC-RULE doble-anidados apuntando a notion.so en vez de notion.com); 4 huérfanos sin resolver de inventario_huerfanos.md (BRIEF:001, BRIEF:011, KERNEL:SCHEMA-008, SP:SYNC-RULE).
Versión actualizada: 9.7.4 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.7.3 hasta que el operador corra verify_versions.py --sync.
---
# v9.7.3 — Corrección de Cierre de Bootstrap Desalineado en SP:BOOTSTRAP-001 (VANTAGE: SISTEMA SINCRONIZADO → BOOTLOADED: DOCUMENTOS CARGADOS) · 2026-07-22
Tipo: [FIX] [DOC]
Alcance: SYSTEM PROMPT (SP:BOOTSTRAP-001).
Contexto: Auditoría en sesión (a solicitud del operador) sobre si el Kernel documenta el Bootloader activo en Project Instructions (UI). Confirmado que KERNEL:DOCUMENTATION-004 (§3.4) sí documenta correctamente el protocolo activo (BOOTLOADING... → BOOTLOADED: DOCUMENTOS CARGADOS), pero la página SYSTEM PROMPT real en Notion (SP:BOOTSTRAP-001) seguía con la frase de cierre anterior (VANTAGE: SISTEMA SINCRONIZADO), retirada por convención desde el Changelog v9.5.0 pero nunca propagada a esta página.
Cambios:
- SP:BOOTSTRAP-001: frase de cierre del paso 5 corregida de VANTAGE: SISTEMA SINCRONIZADO a BOOTLOADED: DOCUMENTOS CARGADOS, alineada con KERNEL:DOCUMENTATION-004 (§3.4) y con el copy real activo en Project Instructions.
Write-Back Verification: re-fetch de SYSTEM PROMPT tras la escritura — frase corregida confirmada verbatim.
IDs afectados: ninguna alta/baja de ID canónico — reescritura de contenido bajo SP:BOOTSTRAP-001, ID ya existente. Census no requiere regeneración.
Pendiente (fuera de esta entrada): el bloque final de SP:BOOTSTRAP-001 sigue citando verify_versions.py --check, flag ya eliminado del Kernel desde v9.6.2 — mismo defecto ya logueado como ticket ALTO (Manual §6 desalineado), no tocado en esta entrada por estar fuera del alcance solicitado.
Versión actualizada: 9.7.3 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.7.0 hasta que el operador corra verify_versions.py --sync.
---
# v9.7.2 — Cierre de Huecos L0: Referencia Cruzada SCHEMA-004/005 → §3.3 + Alta de Dedup_Flag en Class B (SCHEMA-001) · 2026-07-22
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
# v9.7.1 — Fix DB ID/COL ID de Bug Tracker en skill vantage-create-bug-task (drift no propagado desde v9.7.0) · 2026-07-22
Tipo: [FIX]
Alcance: vantage-create-bug-task/SKILL.md (local, fuera de Notion — no fundacional).
Contexto: Al revisar los pendientes derivados de la refactorización del Kernel (v9.7.0), se detectó que la corrección de DB ID/COL ID de Bug Tracker aplicada en KERNEL:TRACKER-SCHEMA-001 no se había propagado al skill que consume esos IDs directamente — el skill seguía con el par heredado (invertido) que el propio Kernel ya señalaba como incorrecto.
Cambios:
- vantage-create-bug-task/SKILL.md: corregido el par Bug Tracker de DB ID 36e938be-fc42-81f8-8c6f-000b6769ba03 / COL ID 36e938be-fc42-81bd-9e1f-dc360b3b45f5 (invertido) a DB ID 36e938be-fc42-81bd-9e1f-dc360b3b45f5 / COL ID 36e938be-fc42-81f8-8c6f-000b6769ba03, alineado con Kernel §8 (KERNEL:TRACKER-SCHEMA-001, v9.7.0). Tasks Tracker no requirió cambio.
- Nota de corrección agregada al propio skill documentando el origen del drift (refactor de Kernel v9.7.0 no propagado en el mismo ciclo).
Write-Back Verification: no aplica a Notion — cambio local, verificado por re-lectura directa del archivo tras la edición.
IDs afectados: ninguno en documentos fundacionales — corrección de referencia a un ID ya existente en el documento real. Census no requiere regeneración.
Pendiente (fuera de esta entrada): ninguno identificado en esta entrada.
Versión actualizada: 9.7.1 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.7.0 hasta que el operador corra verify_versions.py --sync.
---
# v9.7.0 — Refactor de Arquitectura del Kernel (Secciones §3/§4) + Fix de Tracker IDs · 2026-07-22
Tipo: [AUDIT] [FIX] [DOC]
Alcance: KERNEL (§3, §4, §7, §8) + TASKS TRACKER (1 ID).
Contexto: Reestructuración profunda del Kernel para resolver ambigüedades críticas de arquitectura L0/L1/L4 y corregir IDs de base de datos desalineados. Ejecutado vía vantage-documentacion-transversal-propuesta (Fase 1) seguido de -implementacion (Fase 2) tras Gate de verificación de 4 pasos.
Cambios:
- KERNEL §3 (Runtime): reescrito de Runtime Components a Runtime Flow. Agregado KERNEL:DOCUMENTATION-003 (§3.3 — L0 Runtime Build) y KERNEL:DOCUMENTATION-004 (§3.4 — L0 Initialization Protocol), documentando formalmente el bootloading de Project Instructions.
- KERNEL §4 (Scripts): reescrito de Scripting Framework a Infrastructure Layers. Definidos KERNEL:ARCHITECTURE-001 (L1 Pipeline Engine) y KERNEL:ARCHITECTURE-002 (L4 Version Control), aclarando el ownership de cada nivel.
- KERNEL §7 (Schema): actualizado KERNEL:SCHEMA-001 (§7.1) para incluir el mapa de campos Class A/Class B protegidos, alineado con SP:SCHEMA.
- KERNEL §8 (Notion): KERNEL:TRACKER-SCHEMA-001 (§8.1) corregido tras auditoría en vivo. El par Bug Tracker DB ID/COL ID estaba invertido — corregido a DB ID terminación 45f5 / COL ID terminación ba03. El par de Tasks Tracker (terminaciones a035/ba03) fue auditado y confirmado correcto, sin cambio.
- Tasks Tracker: corregido Título de ticket 3a3938be-fc42-814f-bcdc-ce1a48cf1916 (Normalizar fundacionales: SIETE → NUEVE), reflejando la adición de Navigation Brief y Changelog al resolver_registry_v2.json.
- [FIX] Manual §6: eliminada referencia obsoleta a verify_versions.py --check (flag retirado v9.6.2), alineado con KERNEL:DOCUMENTATION-005 (§3.5). Ticket ALTO en Bug Tracker (36e938be-fc42-81f8-8c6f-000b6769ba03) marcado como Hecho.
Write-Back Verification: re-fetch de Kernel §3, §4, §7 y §8 tras la escritura — adiciones confirmadas verbatim, sin mismatch. Tasks Tracker re-fetched — cambio de título confirmado.
IDs afectados — CENSUS-SYNC-R1 disparado: altas de KERNEL:DOCUMENTATION-003, KERNEL:DOCUMENTATION-004, KERNEL:ARCHITECTURE-001, KERNEL:ARCHITECTURE-002. Baja de KERNEL:INFRA-001 (residuo obsoleto de v9.6.0). Census regenerado en esta sesión — vcensus confirmó 130/130 resueltos, 0 huérfanos.
Pendiente (fuera de esta entrada): dos huecos L0 identificados en la revisión post-escritura: (1) KERNEL:SCHEMA-004/-005 no apuntan a §3.3; (2) Dedup_Flag no figura en la lista Class B de §7.1. Ambos requieren parche en próxima sesión.
Versión actualizada: 9.7.0 (fundacional transversal — los 9 documentos sincronizados).
---
# v9.6.9 — Auditoría de Red Flags post-Sync-NUEVE + Cierre de Inconsistencia Versión/Prompt · 2026-07-22
Tipo: [FIX] [DOC]
Alcance: SYSTEM PROMPT (Propiedad Versión) + ARCHIVO CHANGELOG (v9.6.0-v9.6.8).
Contexto: Tras el Sync-NUEVE (v9.6.8), se detectaron 3 Red Flags asíncronas: (1) System Prompt seguía reportando v9.6.7 en su propiedad Versión de Notion pese a estar en v9.6.8; (2) la entrada v9.6.0 del Changelog tenía un anchor corrupto (# v9.6.0... en vez de ### v9.6.0...); (3) el resumen del Handoff citaba erróneamente 380 IDs en Census cuando el conteo real era 126. Auditoría realizada vía notion-fetch + Terminal.
Cambios:
- SYSTEM PROMPT: propiedad Versión corregida de v9.6.7 → v9.6.8 en Notion, alineándolo con el contenido real de la página y con el resto de los 8 fundacionales. Ticket ALTO cerrado.
- ARCHIVO CHANGELOG: corregido anchor de entrada v9.6.0 (agregados los ### faltantes) para permitir resolución de link desde otros documentos. Verificado por vcensus post-fix.
- Auditoría Census: confirmado que el conteo real es 126/126 resueltos (Census v2.0). El número "380" era un residuo de una sesión anterior (v9.5.4) que se coló en el resumen por error de copia. Registro corregido en el Ledger de esta sesión.
Write-Back Verification: re-fetch de System Prompt y Changelog tras la escritura — cambios confirmados verbatim.
IDs afectados: ninguno — correcciones de formato y metadata sobre contenido existente.
Versión actualizada: 9.6.8 (sincronizada en los 9 documentos).
---
# v9.6.8 — Sync-NUEVE: Adopción de Navigation Brief y Changelog en la Regla de Versión Única · 2026-07-22
Tipo: [DOC]
Alcance: Sincronización transversal de los 9 documentos fundacionales (Aliases, Navigation Brief, System Prompt, Career Canon, Kernel, Manual, Census Spec, Census Prod, Changelog).
Contexto: El proyecto VANTAGE operaba bajo la Regla de Versión Única (SP:SYNC-RULE) aplicada a 7 documentos. Hoy se formalizó la inclusión de Navigation Brief (BRIEF) y Archivo Changelog (CHANGELOG) en el núcleo fundacional, elevando el conteo de 7 → 9. Esto garantiza que cualquier cambio de versión se propague atómicamente a toda la suite documental, eliminando el drift que ambos documentos sufrían previamente.
Cambios:
- Propiedad Versión actualizada a v9.6.8 en los 9 documentos vía verify_versions.py --sync (corrida por el operador, verificado por Claude vía notion-search).
- resolver_registry_v2.json (local): agregados los dos nuevos documentos con sus IDs correspondientes y alias BRIEF/CHANGELOG.
- verify_versions.py (local): actualizada la constante DOC_KEYS para exigir coincidencia en los 9 documentos.
- SYSTEM PROMPT: actualizada la SP:SYNC-RULE para citar explícitamente los 9 documentos fundacionales.
Write-Back Verification: verificado por Claude vía notion-search: los 9 documentos reportan v9.6.8 como propiedad Versión en Notion.
IDs afectados: ninguno — cambio de metadata transversal.
Versión actualizada: 9.6.8 (los 9 documentos sincronizados).
---
# v9.6.7 — Cierre de Handoff SESSION-20260721-A + Registro de 2 tickets ALTO en Bug Tracker · 2026-07-21
Tipo: [FIX]
Alcance: Bug Tracker (2 páginas) + Session Ledger (Cierre de sesión).
Contexto: Cierre formal de la sesión tras verificar la correcta inyección de la arquitectura L0 en el System Prompt. Se detectaron 2 red-flags durante el handoff que requerían escalamiento inmediato a tickets.
Cambios:
- Bug Tracker: creado ticket ALTO "Inconsistencia Versión Notion vs. Contenido (System Prompt)" (36e938be-fc42-811c-9051-ef06cc7d7607). SP reportaba v9.6.6 en metadata de Notion pero v9.6.7 en contenido.
- Bug Tracker: creado ticket ALTO "Manual §6 desalineado con KERNEL:DOCUMENTATION-005" (36e938be-fc42-81f8-8c6f-000b6769ba03). Manual sigue citando verify_versions.py --check, comando eliminado en v9.6.2.
- Session Ledger: registrado el handoff consolidado SESSION-20260721-A como Hecho.
Write-Back Verification: re-fetch de ambos tickets en Bug Tracker tras la creación — confirmados correctos.
IDs afectados: ninguno — alta de registros en base de datos externa (Trackers).
Versión actualizada: 9.6.7 (en contenido de los 7 documentos fundacionales).
---
# v9.6.6 — Inyección de Arquitectura L0 en el System Prompt (SP:BOOTSTRAP-001) · 2026-07-21
Tipo: [DOC]
Alcance: SYSTEM PROMPT (SP:BOOTSTRAP-001).
Contexto: El System Prompt describía el proceso de arranque de forma genérica. Se inyectó la arquitectura L0 (L0 Bootloader Runtime Build) para formalizar cómo Claude debe cargar las Project Instructions y el estado persistente del sistema al iniciar sesión.
Cambios:
- SP:BOOTSTRAP-001 (§2): reescrito para incluir los 5 pasos del L0 Bootloader: 1. Ingesta de Project Instructions; 2. Verificación de ID de sesión; 3. Carga de Registry L0; 4. Sincronización de Versión; 5. Declaración de Readiness (BOOTLOADED: DOCUMENTOS CARGADOS).
- Alineación con KERNEL:DOCUMENTATION-004 (§3.4) garantizada vía DRY RUN cruzado en la misma sesión.
Write-Back Verification: re-fetch de System Prompt §2 tras la escritura — cambios confirmados verbatim.
IDs afectados: ninguna alta/baja de ID canónico — adición de contenido bajo SP:BOOTSTRAP-001, ID ya existente.
Versión actualizada: 9.6.6 (sincronizada vía verify_versions.py --sync en los 7 documentos).
---
# v9.6.5 — Normalización de IDs Legacy en apply_hyperlinks.py (Output Contract) · 2026-07-21
Tipo: [FIX]
Alcance: apply_hyperlinks.py (MAPPING) + V_ID_CENSUS_PRODUCTION.md (local).
Contexto: Auditoría post-v9.6.0 reveló que apply_hyperlinks.py seguía intentando usar IDs legacy para el Output Contract (CANON:FIGMA-TAGS-001), causando links rotos. Se normalizó el MAPPING del script para usar los anchors canónicos de v9.6.0.
Cambios:
- MAPPING en apply_hyperlinks.py: actualizado de CANON:FIGMA-TAGS-001 → CANON:OUTPUT-CONTRACT-002 (Figma Tags) y CANON:GOLDEN-SKELETON-001 → CANON:OUTPUT-CONTRACT-001 (Golden Skeleton).
- EXCLUDE_IDS: agregados temporalmente los 4 IDs de Positioning Modes (CANON:POSITIONING-N1..N4) hasta resolver colisión de anchors en Manual §19.
Write-Back Verification: verificado por corrida exitosa de apply_hyperlinks.py --dry-run (0 errores de mapping).
IDs afectados: ninguno en Notion — cambio en lógica local de scripting.
Versión actualizada: 9.6.5 (sincronizada en los 7 documentos).
---
# v9.6.0 — Re-Arquitectura de Kernel §3 y §4 + Consolidación de Output Contract · 2026-07-20
Tipo: [AUDIT] [DOC] [FIX]
Alcance: KERNEL (§3, §4), CAREER CANON (§8), MANUAL (§19).
Contexto: Auditoría estructural de la suite documental tras detectar ambigüedad en la definición de capas L1 (Pipeline) vs L4 (Control de Versiones) y fragmentación del contrato de salida en el Career Canon.
Cambios:
- KERNEL §3 (Runtime): reescrito para separar L0 (Bootloader) de L4 (Sync Engine). Documentado formalmente el L0 Registry en KERNEL:DOCUMENTATION-003.
- KERNEL §4 (Scripts): reescrito para definir las 3 capas activas: L1 (vsearch/vtrack), L3 (vmail/vupdate), L4 (vgit/vsync). Definido KERNEL:ARCHITECTURE-001 (L1 Pipeline Flow).
- CAREER CANON §8 (Output Contract): consolidado esquema de 4 piezas: Golden Skeleton (-001), Figma Tags (-002), Tag Registry (-003), Positioning Modes (-004). Dados de baja 5 IDs fragmentados previos.
- MANUAL §19 (Positioning Modes): actualizadas referencias cruzadas al nuevo esquema CANON:OUTPUT-CONTRACT-004.
Write-Back Verification: re-fetch de los 3 documentos tras la escritura — confirmados correctos.
IDs afectados — CENSUS-SYNC-R1: bajas de CANON:FIGMA-TAGS-001, CANON:GOLDEN-SKELETON-001, CANON:TAG-REGISTRY-001, CANON:SKELETON-SPEC-001. Altas de CANON:OUTPUT-CONTRACT-001..004. Census regenerado.
Versión actualizada: 9.6.0 (fundacional sincronizado).
---
# v9.5.9 — Transición a Notion-First (Filesystem read-only) · 2026-07-20
Tipo: [INFRA]
Alcance: Filesystem local (Documentación/ACTIVE/).
Contexto: Para evitar el drift entre las copias locales (.md) y las páginas de Notion, se formalizó a Notion como la Única Fuente de Verdad. Los archivos locales se marcaron como read-only (chmod 444).
Cambios:
- Documentación/ACTIVE/ (.md): todos los archivos fundacionales protegidos contra escritura accidental.
- SP:CONSISTENCY: agregada regla de verificación de permisos en el bootloading.
Versión: 9.5.9 (sincronizada).
---
# v9.5.4 — Blindaje de Class B (Dedup_Flag) en KERNEL:CV-GOLDEN-RULES · 2026-07-18
Tipo: [FIX] [DOC]
Alcance: KERNEL (§10).
Contexto: El Dedup_Flag es crítico para el Layer 1 pero se perdía en las limpiezas manuales del Dashboard. Se agregó a la lista de campos protegidos.
Cambios:
- KERNEL:CV-GOLDEN-RULES (§10): agregado Dedup_Flag como campo Class B (System-Primary).
Versión: 9.5.4 (sincronizada).
---
# v9.5.0 — Deprecación de 'SISTEMA SINCRONIZADO' · 2026-07-15
Tipo: [INFRA] [DOC]
Alcance: System Prompt, Kernel, Aliases.
Contexto: El copy legacy de cierre de bootloading fue retirado por considerarse redundante bajo el nuevo protocolo L0.
Cambios:
- Retirada la frase "VANTAGE: SISTEMA SINCRONIZADO" de todos los fundacionales.
Versión: 9.5.0 (sincronizada).
---
# v9.4.0 — Primera Implementación de Cross-Reference Hyperlinks · 2026-07-10
Tipo: [INFRA]
Alcance: Layer_1/scripts/apply_hyperlinks.py.
Contexto: Alta del script inicial para automatizar la creación de links entre documentos usando el Census como base.
Versión: 9.4.0.
---
# v9.0.0 — Lanzamiento de VANTAGE ARCHITECTURE · 2026-07-01
Tipo: [MAJOR]
Alcance: Suite Documental Completa.
Contexto: Migración de JHS-Pipeline a VANTAGE. Primera versión del Kernel y el Manual operativo bajo el nuevo paradigma de capas (L1/L2/L3/L4).
Versión: 9.0.0.
---
