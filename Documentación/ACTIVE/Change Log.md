# V | CHANGELOG

Título (toggle Notion): v9.21.10 — Ago 16, 26 10.27
Tipo: [DOC]
Alcance:
- Kernel (KERNEL:GATE-DECISION-007, 09.7 — párrafo nuevo: Guard de anotación en ingesta) y (KERNEL:GATE-DECISION-011, 09.11 — fila dedup match de la matriz condicionada al guard)
- Manual (MANUAL:DATA-MANAGEMENT § Dedup — bullet nuevo: Guard de anotación PR #10) y (Glosario §22 — feed_processor.py, profile_fit.py, backfill_class_a.py actualizados)
Contexto: PR #10 (arena/01a00b06-vantage → main, merge dec979ad, 2026-08-16) implementó el batch autorizado en FEEDBACK_DEVIN_MATRIZ_DEDUP (Fase 1 recortada, APROBAR_WRITE previo): fix infer_layer L2→L2 en backfill_class_a.py; _extract_text_prop consolidado como helper único a nivel de módulo en feed_processor.py (cierra NameError en _check_historical_rejected_status y TypeError en el fingerprint path con location_prop seteado, unifica _extract_title_text); guard should_annotate_existing (profile_fit.py, reutiliza _PROTECTED_STATUSES | _TERMINAL_STATUSES) aplicado vía should_mutate_existing_page a Dedup_Flag (Class B, candidato a archivo) y a upgrade de layer (Class A, procedencia — bloqueado para no reescribir origen de postulación viva, no por ser Class B); comentario GAP-03 actualizado (write path Class A por construcción vía NotionSchema, guard no-Python en dashboard_notion.py, FX-1 cerrado). El código llegó a main sin su contraparte documental — esta entrada la cierra. Parches aplicados en sandbox Arena (branch arena/01a00b58-vantage) sobre ACTIVE/ local; escritura a Notion pendiente vía vdoc local (el sandbox no tiene token, correctamente).
Cambios:
- KERNEL:GATE-DECISION-007 (09.7) — párrafo nuevo "Guard de anotación en ingesta (PR #10)": predicado compartido, sets exactos (_PROTECTED_STATUSES: Postulado, Postulando, En proceso, Negociando, Sin respuesta, Contratado; _TERMINAL_STATUSES: Expirada, Rechazado, Archivar, Retirado), lectura de Status desde el page object de Notion, distinción explícita vs gate_logic(), inbound REVIEW_NEEDED intacto.
- KERNEL:GATE-DECISION-011 (09.11) — fila [ENTRY] dedup match: efecto Class B condicionado a should_annotate_existing(Status).
- MANUAL:DATA-MANAGEMENT § Dedup — bullet nuevo "Guard de anotación (PR #10)" entre resolución de flags y ventana, con reporte en consola (⏭️ Dedup_Flag omitido / Layer upgrade omitido).
- Manual Glosario §22 — feed_processor.py (párrafo Hardening PR #10), profile_fit.py (should_annotate_existing + consumidor nuevo), backfill_class_a.py (fix infer_layer L2 documentado).
IDs afectados: Ninguno (todas las ediciones reutilizan IDs existentes — no dispara KERNEL:CENSUS-SYNC Regla 1).
Write-Back Verification: N/A en esta entrada — parches aplicados solo en ACTIVE/ local (sandbox); la verificación post-escritura en Notion corresponde al paso vdoc local del operador.
Referencia: Archive/Documentación/brief_doc_transversal_pr10_dedup_guard.md (nodos N1–N6, matriz aprobada, checklist operador).
Pendiente (fuera de esta entrada):
- vdoc kernel dry + vdoc manual dry → vdoc local kernel + vdoc local manual (operador, con APROBAR_WRITE).
- Alta de esta entrada en el Change Log de Notion (toggle v9.21.10 — Ago 16, 26 10.27).
- vversions --sync para propagar v9.21.10 al resto de los fundacionales.
- Decisión campo a campo class_b_guard / Positioning_Mode (backlog, FEEDBACK_DEVIN_HALLAZGOS_V2 §3).
- Ticket de Manual para pipeline_recovery (vl1 recovery hoy es consistency check, no resume).
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
> El histórico completo del CHANGELOG lo podrás encontrar en ARCHIVO CHANGELOG, en esta pagina de consulta continua solo encontrarás las últimas diez entradas para garantizar la operación y referencia del sistema.
