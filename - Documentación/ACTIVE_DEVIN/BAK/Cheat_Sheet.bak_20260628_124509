# V | CHEAT SHEET & CHANGE LOG

# ## [ID: 37c938be-fc42-80d4-b9ae-f5969830331b:Aliases_001] 0. CHEAT SHEET
### Layer 1 — Active Recon
### Layer 1 — Dedup & Oportunidades
### Layer 3 & Dashboard
### lazy_loader.py — Ruta Canónica
cd ~/Documents/04-Vantage_CV/Layer_1/scripts && source ../.venv/bin/activate && python lazy_loader.py --page {PAGE_ID} --route {ruta}
### Layer 4 — Version Control & Documental
### Figma Sync — CV Output Layer
04-Vantage_CV/Figma Sync/ — Plugin Figma para inyección de payloads CV-B al lienzo.
### Runtime CLI (vantage.py)
## [ID: 37c938be-fc42-80d4-b9ae-f5969830331b:Change_Log_001] 2. CHANGELOG
## v8.7 — VANTAGE · 2026-06-27
> ID: 37c938be-fc42-80d4-b9ae-f5969830331b:Change_Log_v8.7
- [ARCH] Figma Sync integrado como CV Output Layer — Carpeta Figma Sync/ establecida al mismo nivel jerárquico que L1–L4 dentro de 04-Vantage_CV/. Contiene los 4 componentes del plugin Figma: manifest.json · code.js · ui.html · registry_seed.json. No es capa de búsqueda ni de infraestructura de datos — es la capa de materialización del CV en Figma.
- [NEW] registry_seed.json — SSOT de nodos Figma — JSON canónico que mapea tokens semánticos (ej. HEADER_NAME, EXP_L_OR_AL_LUXE_M_XICO_BULLET_1) a IDs crudos de nodo Figma (ej. "2:4"). 52 tokens mapeados cubriendo header, perfil, habilidades, experiencia C01–C05, formación y certificaciones. Fuente única de verdad para toda operación de inyección sobre el lienzo.
- [REFACTOR] code.js — Registry V2 / Resolver Layer V1 — Motor del plugin refactorizado. Deprecado: findAll() con búsqueda O(n) por nombre de capa [VANTAGE] KEY_NAME. Activo: getNodeById(rawId) con resolución O(1). Resolver dual: KEY semántica → REGISTRY → ID crudo; ID crudo directo (flujo Markdown figma_text_id) → uso directo sin lookup. Notify actualizado para confirmar modo Registry V2 y reportar keys sin resolver.
## v8.5.4 — VANTAGE · 2026-06-23
> ID: 37c938be-fc42-80d4-b9ae-f5969830331b:Change_Log_v8.5.4
- [FIX] Campo jd agregado al pipeline L1/L2 — bug resuelto en consolidación — jd estaba ausente del ITEM SCHEMA de Prompt A y de la capa de escritura de feed_processor.py, impidiendo que el texto del JD llegara al Tracker. Tres patches quirúrgicos aplicados: (1) Prompt A — "jd": "string or null" agregado al ITEM SCHEMA como último campo, con instrucción de poblar cuando fetch_status = direct_apply; (2) feed_processor.py — jd_prop agregado a NotionSchema; JD escrito en build_notion_properties() via rich_text_value(rec["jd"][:2000]); (3) Kernel §4 — mapeo jd → JD documentado en tabla de vocabulario; nota operativa sobre comportamiento cuando el campo llega null (fetch_status ≠ direct_apply). Wrappers L1/L2 heredan el contrato de Prompt A sin cambios individuales.
## v8.6 — VANTAGE · 2026-06-23
> ID: 37c938be-fc42-80d4-b9ae-f5969830331b:Change_Log_v8.6
- [ARCH] Normalización de capa documental — cierre formal de auditoría externa (3 agentes independientes). Todos los pendientes resueltos en sesión 2026-06-22.
- [ARCH] Convención ACTIVE/ establecida — paths versionados (.../v8.5/) reemplazados por directorio agnóstico de versión. Al pasar a v8.7: copiar archivos a ACTIVE/, cero cambios de código.
- [NEW] vsync_doc.py migrado a Layer_4/scripts/ — alias vdoc [dry|notion|local]. Sync bidireccional Notion ↔ ACTIVE/ para los 5 docs fundacionales + auto-commit GitHub al terminar vdoc notion.
- [FIX] Bugs resueltos en vsync_doc.py: layer_1.env token con \n embebido · _rich_text() con None · _block_to_md() en callout con icon: null · safe_list() reemplaza blocks.children.list() (bug silencioso de notion-client 3.x).
- [ARCH] Sistema normalizado a v8.6 en todos los documentos fundacionales.
## v8.5.3 — VANTAGE · 2026-06-23
> ID: 37c938be-fc42-80d4-b9ae-f5969830331b:Change_Log_v8.5.3
- [NEW] vsync_doc.py — Sync bidireccional Notion ↔ .md (BUG-005 cerrado) — Script independiente en Layer_1/scripts/. Sincroniza 5 páginas fundacionales (KERNEL · SYSTEM PROMPT · CAREER CANON · MANUAL · CHEAT SHEET) contra sus .md locales en - Documentación/v8.5/. Flags: --direction {notion|local|auto} (auto: gana timestamp más reciente; notion: default pre-sesión; local: para edits offline) · --dry-run (inspección sin escritura) · --doc {key} (sync quirúrgico por documento). Output --json disponible para integración futura con vstatus. Alias: vsync-doc. Bug Tracker: 388938be-fc42-8198-a954-db353d22a1cc.
## v8.5.2 — VANTAGE · 2026-06-21
> ID: 37c938be-fc42-80d4-b9ae-f5969830331b:Change_Log_v8.5.2
- [FIX] notion_utils.py — rewrite completo de Client — notion_utils.py no exportaba clase Client. Reescrito con namespaces client.data_sources.query(data_source_id=...), client.pages.update(page_id=..., properties=...), client.pages.retrieve(), client.pages.create(), client.databases.retrieve(), client.databases.query(). Drop-in compatible con notion-client 3.x. Throttle, retry, cache y metrics del módulo original preservados. Afectaba: status_report.py, source_analytics.py, batch_operations.py, pipeline_recovery.py, backfill_class_a.py.
- [FIX] NOTION_VERSION corregida — Versión 2025-09-03 (futura, inválida) reemplazada por 2022-06-28 (estable). Causaba invalid_request_url en todas las llamadas a la API.
- [FIX] DB IDs corregidos en scripts — status_report.py usaba COL ID (442938be) en lugar del DB ID (596938be). source_analytics.py, batch_operations.py y pipeline_recovery.py usaban ID desconocido (4e542b37). Todos corregidos a 596938be-fc42-836b-aea7-814a1491bd47 (VANTAGE TRACKER DB).
- [FIX] pyyaml instalado — profile_evolution.py fallaba con ModuleNotFoundError: yaml. Instalado en .venv.
- [FIX] layer_1_pipeline.sh — argumento backfill — $@ pasaba backfill como argumento posicional a backfill_class_a.py. Corregido a ${@:2} para pasar solo flags (--dry-run).
- [FIX] batch_operations.py — escritura destructiva sin guardia — El script ejecutaba batch Target → Exploratorio sin flag de protección. Reescrito con flag --execute obligatorio. Sin el flag: solo reporte. Con --execute: escritura. Eliminado input() interactivo. Alias vl1 batch ahora es read-only por defecto.
## v8.5.1 — VANTAGE · 2026-06-21
> ID: 37c938be-fc42-80d4-b9ae-f5969830331b:Change_Log_v8.5.1
- v8.5.1 (Patch OA-01): Migración de MCP Client-Side Lazy Load a Server-Side Lazy Load vía Terminal (lazy_loader.py). Reducción drástica de Input Tokens al aislar payloads de IDs embebidos desde Python antes de inyectarlos al contexto del LLM.
## v8.5 — VANTAGE · 2026-06-20
> ID: 37c938be-fc42-80d4-b9ae-f5969830331b:Change_Log_v8.5
- [ARCH] Patrón "Thin Client, Thick Server" & MCP Lazy Loading — Cobertura completa (SP + KERNEL + CAREER CANON + MANUAL) — Refactorización arquitectónica mayor en dos capas. Capa 1 — Cirugía de bloques en V | KERNEL: fusión estructural de identificadores de anclaje. Antes: párrafo con ID + bloque heading_2 separado (API retornaba 2 objetos; bloques huérfanos). Después: ## [ID: {KERNEL_MASTER}:{ruta}] TÍTULO — ID y encabezado como un solo objeto. Un read_block extrae el encabezado + todos sus hijos en una sola llamada limpia. Gap de resolución en Notion API eliminado. Capa 2 — Compresión del System Prompt (Enrutador MCP): SP despojado de texto descriptivo y convertido en modelo imperativo estructurado. Directiva Economía de Contexto implementada (respuestas ultra-concisas, solo carga útil). Patrón Lazy Loading centralizado: SP ya no almacena flujos completos; posee un índice de enrutamiento que construye cadenas de búsqueda exactas ([ID: {KERNEL_MASTER}:{ruta}]) para cargar módulos específicos (schema-001, cv-pipeline-001) únicamente cuando el trigger activo lo requiere. Impacto operativo: ~50% reducción del footprint del SP (token-efficiency). Zero hallucination por carga quirúrgica de solo la regla necesaria. KERNEL en Notion escala infinitamente sin añadir tokens al prompt base. Career Canon (377938be-fc42-8089-93f2-f52dbd2dec6c): misma cirugía de bloques aplicada. Todos los IDs de anclaje de secciones (:canon-profile-001, :canon-skills-001, :canon-experience-001, :canon-achievements-001, :canon-kpis-001, :canon-facts-001, :canon-positioning-001, :canon-output-contract-001, :canon-coverage-gate-001, y los IDs de experiencias C01–C05, KPI01–KPI08, CF01–UF03, positioning N1–N4) fusionados con sus encabezados. Un read_block sobre cualquier sección del Canon ahora retorna el bloque completo con su payload en una sola llamada, habilitando la carga diferida del perfil completo del operador sin cargar el documento entero al contexto. Manual de Usuario (372938be-fc42-8050-9a67-e40857d7806e): misma cirugía aplicada a todas las secciones operativas (audience-scope-001, manual-objetivo-001, manual-funcionamiento-001, manual-setup-001, manual-flujo-001, manual-vchecklist-001, manual-vantage-runtime-001, manual-tracker-001, manual-troubleshooting-001, manual-prompts-wrappers-001, manual-cheatsheets-001, manual-healthcheck-001, manual-changelog-001, manual-reglas-de-oro-001, manual-fallo-001). El Manual puede ahora servirse por sección quirúrgica bajo demanda del agente sin cargar el documento completo. Componentes afectados (cobertura total): System Prompt (SP) · V | KERNEL · V | CAREER CANON · V | MANUAL · Notion MCP.
- L4 — Version Control & Infrastructure — Nueva capa documental. git_sync.py + git_sync_wrapper.sh + com.vantage.gitsync.plist instalados en Layer_4/scripts/ y Layer_4/wrappers/. Detecta cambios en el repo, hace add -A + commit con timestamp + push a origin/main. Atomic: sin cambios → silencio total. Con cambios → notificación Hero. Error → notificación Basso. launchd corre a las 09:00, 15:00, 21:00. Alias: vgit. Reutiliza .venv de Layer_1. Repo: github.com/mauriciomeyran/jhs-pipeline.
- Nomenclatura de capas actualizada — L1 Active Recon · L2 Strategic Search · L3 Passive Intake · L4 Version Control & Infrastructure. L4 no es una capa de búsqueda — es infraestructura documental del sistema. — _write_heartbeat(total_created, total_failed) agregada en layer_3_mail.py. Escribe ~/.vantage/l3_heartbeat.json al final de cada run con campos last_run (ISO-8601 UTC), total_created, total_failed. Directorio ~/.vantage/ se crea automáticamente. Imports con alias privados (_json, _pl, _dt) para evitar colisiones. Bug Tracker: 382938be-fc42-81b3-98c1-e513eab798fc.
- M-06 cerrado — find_candidates pre-filter — _handle_find_candidates() en agent_api.py (~l.150) ahora incluye score >= 60 como condición de filtro. Elimina el riesgo de que el endpoint devuelva entidades por debajo del umbral Gate=CREATE. Umbral alineado con Kernel §5. Bug Tracker: 382938be-fc42-810c-9e94-eaa6f416a68f.
- M-01 confirmado operativo — vantage.py status produce index_age_hours: 36.5 + "warning": "entity_index_stale" correctamente. No requirió cambios.
- Nomenclatura mail_pipeline.py corregida — Nombre conceptual desactualizado en Kernel §2 (arquitectura L3) y §3 (ownership table) alineado con nombre real en disco: layer_3_mail.py (Layer_3/scripts/). Origen del alias: renaming pre-v8.0 (layer_2_mail.py → layer_3_mail.py) no propagado a la documentación del Kernel. Manual §4 corregido: LAYER 2.app → LAYER 3.app. Manual §5.4 Arranque Frío actualizado con nombre real + verificación de heartbeat (cat ~/.vantage/l3_heartbeat.json).
## v8.4 — VANTAGE · 2026-06-16
> ID: 37c938be-fc42-80d4-b9ae-f5969830331b:Change_Log_v8.4
- vantage.py sync implementado — Nuevo comando CLI + módulo. Regenera entity_index_v2.json desde Notion en vivo (atomic write: .tmp → os.replace), invalida cache de query_layer con force_reload=True, ejecuta status() al terminar. Resultado en producción: 465 entidades, 100% hash coverage, 0 orphans, 4.3s. Conflicto notion_client local vs SDK PyPI resuelto vía pop(sys.modules) + filtro sys.path + restauración en finally. Implementado con Perplexity Pro + Claude Sonnet 4.6 Thinking + FileSystem MCP.
- resolver_registry_v2.json corregido — Campos status y resolution_contract.live_resolution actualizados de DESIGN_ONLY / NO IMPLEMENTADO a estado operativo real. Resolver Layer verificado en vivo desde 2026-06-15. Pendiente documentado en Runtime Doc §5.7 cerrado.
- vacante_purge_trash_only.py depreciado — Workaround de emergencia para un run puntual. Script canónico: vacante_purge.py (copia + trash, atómico). Renombrado a _DEPRECATED_vacante_purge_trash_only.py. Pendiente de eliminación tras auditoría.
- Archivos .bak generados — vantage.py.bak, vantage.py.bak_20260616_035426 creados por Perplexity durante implementación de sync. Pendiente: mover a Layer_1/backups/ o eliminar.
- VANTAGE Runtime V1 documentado — Documentación formal en V | RUNTIME DOCUMENTATION y V | RUNTIME ROADMAP. Patches de Runtime en Kernel y Manual pendientes de inserción (bloqueados hasta resolver los 4 pendientes del Roadmap §7.2).
- SP actualizado a v8.4 — vantage.py sync agregado al scope y tabla de triggers (§7). Tokens de aprobación ampliados: Ok, Go, YEP.
## v8.3 — VANTAGE · 2026-06-15
> ID: 37c938be-fc42-80d4-b9ae-f5969830331b:Change_Log_v8.3
- Sistema de IDs duales desplegado — Structural ID (<!-- ID: [page_id:node_id] -->) + Visible ID (ID: [page_id:node_id]) implementados en los tres documentos fundacionales: Kernel, Manual de Usuario y System Prompt. Los IDs son los nodos de conexión para el cableado de Runtime.
- VANTAGE Runtime V1 construido — Stack completo operativo: entity_index_v2.py → resolver_layer_v1.py → query_layer.py → context_layer.py → agent_api.py → notion_client.py (hardened: cache, retry, throttle, metrics). 465 entidades indexadas, 100% hash coverage, 0 orphans. Verificado en vivo el 2026-06-15.
- vantage.py entrypoint único — CLI + módulo Python. Comandos: status, ask, resolve, context, query.
- Registry V2 — entity_index_v2.json, graph_v2.json, backlinks_v2.json, resolver_registry_v2.json generados. Graph Layer con 13 edges archived_from (no ejercitado en vivo al 2026-06-15).
- backfill_hash.py v1.2 completado — 100% hash coverage en VANTAGE_TRACKER y ARCHIVO_TRACKER. Prerequisito para generación del Entity Index.
## v8.2 — VANTAGE · 2026-06-14
> ID: 37c938be-fc42-80d4-b9ae-f5969830331b:Change_Log_v8.2
- Kernel optimizado para token efficiency — Refactor completo del Technical Kernel: schemas, workflows y checklists consolidados. Arquitectura token-efficient: SP contiene únicamente contratos operativos activos; lógica completa vive en el Kernel.
- Career Canon integrado — Career Canon v8.2 con métricas verificadas, node markers Figma (###### [figma_text_id](XXXX:XX)), bold metrics con escaped parentheses. Output Contract v1.0 operativo.
- SP v8.2 — Contratos operativos únicamente. Referencias cruzadas al Kernel para schemas y lógica completa. Ownership Matrix Class A/B consolidada.
## v8.0 — VANTAGE · 2026-06-09
- Renaming de capas — Arquitectura renaming completo: Layer 3 (Active Market Reconnaissance) → L1 — Active Recon (Career Sites · LinkedIn · Aggregators) | Layer 1 (Strategic Search) → L2 — Strategic Search (Gemini · You.com · Grok) | Layer 2 (Passive Intake) → L3 — Passive Intake (layer_3_mail.py). Jerarquía dedup: L1 > L2 > L3.
- Perplexity — nuevo rol canónico — Removido de motores de extracción (no opera en Extraction Mode en job boards/career sites). Rol: Consolidation & Dedup — paso post-extracción del ciclo del lunes. Sigue siendo motor de ensamblaje de prompts (sin cambio).
- Ciclo semanal actualizado (Manual §4) — Lunes: ①L1 Active Recon ②L2 Strategic Search ③Consolidation&Dedup (Perplexity) ④feed_processor.py. Martes: Dashboard & Solve Conflicts. Miércoles: CV Optimization.
- Kernel §3/§4/§5/§6/§13 actualizados — Naming canónico L1/L2/L3 propagado en tabla de arquitectura, contratos de capa, flujos de datos y Search Matrix.
- Manual §8 actualizado — Referencias Layer 1/3 → L1/L2 en callouts de prompts y wrappers. Perplexity: rol correcto documentado.
- 
- Canonización L0 — Perplexity renombrado a L0 - Consolidation & Dedup. No es una capa independiente — es el paso del pipeline del lunes entre extracción y FEED. Recibe 6 JSONs: L1 (Career Sites · LinkedIn · Aggregators) + L2 (Gemini · You.com · Grok). Jerarquía de dedup L1 > L2 aplicada en este paso. L3 no pasa por L0.
- Naming wrappers L1 — Wrappers Career Sites · LinkedIn · Aggregators corregidos: Layer 3 → L1, referencias a Perplexity/Comet eliminadas. Responsabilidades canónicas: Career Sites = career pages oficiales + ATS únicamente; LinkedIn = LinkedIn Jobs únicamente; Aggregators = job boards LATAM (OCC · Indeed · Computrabajo · Bumeran).
- Naming L2 - Prompt A — Renombrado de “LAYER 1 - Prompt A” a “L2 - Prompt A”. Categoría LAYER 2 confirmada.
- Kernel §3/§4/§5/§13 actualizados — L0 propagado en arquitectura, flujos de datos, pipeline de fases y search matrix.
- Manual §4/§8 actualizados — PASO ③ LUNES y callout Perplexity reflejan rol L0 canónico.
- Revisión editorial completa — pasada única sobre Kernel y Manual. Sin cambios de arquitectura ni contratos.
- Kernel — §1: prohibiciones reformuladas en voz de IA operadora. §2: redundancia de “no evalúa” eliminada (referencia cruzada a §7/§15). §3: nota de implementación de jerarquía dedup agregada. §4: “Cierre obligatorio” removido (pertenece al Manual). §5: “Rol de Perplexity” consolidado como referencia cruzada. §7: columna AI Component clarificada (calidad estratégica vs. errores de formato). §8: visual_signal/innovation_dna con instrucción de ignorar sin comentar. §10: mini-ejemplo EXPIRED vs. Expirada agregado. §11: scripts/archivos reemplazados por referencia cruzada al Manual §10. §13: segunda instancia de BOUNDARY consolidada. §14: input de FEED clarificado como N/A. §15: comportamiento con JSON vacío post-DRY RUN documentado. §19: comportamiento ante solicitud de cambio inválido especificado.
- Manual — §1: plain text → prosa Notion. Hard Blocks movidos a §6. §2: plain text → tablas Notion; celda Python dividida en Scoring/Gates y FEED. §3: plain text narrativo → prosa Notion. §4: callout ⚠️ movido antes de PASO ①; pasos bold → H3; L3 reescrito como subsec. colapsable. §5: [Sistema] = feed_processor.py aclarado. §6: nota de timing Bypass agregada. §7: diagnósticos reformulados en voz del operador. §8: Prompts B y C URL directa → mention-page. §9: NAD y RT-1 agregados al glosario. §11: referencia a §8 en Red Flags.
## v7.5 — VANTAGE · 2026-06-06
- Migración FEED a Python — feed_processor.py asume ownership completo del ciclo FEED (Layer 1 y Layer 3). Claude queda excluido de esta operación.
- BOUNDARY v7.5 — Kernel recibe bloque de boundary al inicio del Technical Kernel. JSON de vacantes sin trigger CV-A · FAST [URL] · CANON-UPDATE → responde: “El procesamiento de FEED está migrado a feed_processor.py.”
- Confirmación interactiva — feed_processor.py presenta DRY RUN en terminal + _dryrun.md; escritura requiere s del operador.
- REVIEW_NEEDED — nuevo status de vacantes. Python lo asigna cuando alias no resuelve, URL falla parcialmente o hay semi-duplicado. Vacantes con este status se escriben en Notion y se revisan en Dashboard antes del siguiente ciclo.
- Campos layer y hash agregados a Class A — layer (L1/L3) y hash (dedup cross-layer) escritos por feed_processor.py en cada entrada.
- Dedup cross-layer — feed_processor.py computa hash diferenciado por tipo de URL y consulta Notion con ventana de 30 días antes de escribir.
- Archivo DRY RUN archivado mensualmente — estructura: ARCHIVO → YYYY-MM MONTH → DRY RUN · YYYY-MM-DD · Layer L{1|3}.
- Manual §4 (LUNES) y §4 (MARTES Layer 3) actualizados — PASOS 3 y 4 apuntan a layer_1_pipeline.sh feed + confirmación s.
- Callout v7.5 — warning amarillo en Manual §4: Claude no participa en ciclo FEED.
## v7.4 — VANTAGE · 2026-06-06
- Migración de ensamblaje de prompts — responsabilidad transferida de Claude a Perplexity Desktop (vía MCP Notion). Claude queda excluido de esta operación.
- Layer 1 — Perplexity lee Prompt A + Wrapper del motor, concatena y completa TODAY'S DATE. Trigger: "entrégame el prompt de [motor]".
- Layer 3 — Perplexity lee Prompt D + Wrapper del canal, concatena y completa TODAY'S DATE. Trigger: "entrégame el prompt de [Career Sites | LinkedIn]".
- Contrato de ejecución documentado — Wrapper ausente en PROMPT LIBRARY = reportar y detener, no inferir. Prompt A y D no se ejecutan sin Wrapper.
- Manual §8 actualizado — responsable, triggers Layer 1 y Layer 3, regla de no reutilizar sesiones anteriores.
- Manual §4 (LUNES) actualizado — instrucciones operativas apuntan a Perplexity Desktop.
- Kernel §13 actualizado — contrato de ensamblaje, alcance por capa, trigger unificado.
## v7.2 — VANTAGE · 2026-06-01
- Layer 2 — layer_3_mail.py operacional (antes llamado mail_pipeline.py) — Reemplaza arquitectura Make → Notion raw por pipeline autónomo Gmail → Groq → Notion con Class A poblado
- Parsing con LLM — Groq (llama-3.3-70b) extrae rol, marca, url, holding directamente del cuerpo del email; solo roles VM/retail pasan
- Dedup nativo en Layer 2 — query Notion por Rol + Marca antes de cada write; duplicados descartados sin write
- Hard blocks en sender check — L’Oréal · Levi’s/Dockers · El Palacio de Hierro filtrados antes de Groq
- Cadencia automática — launchd · 3 runs diarios 08:00 · 14:00 · 21:00 · alias mail para run manual
- §18 Arquitectura Diferida actualizada — Email parsing (Layer 2) pasa de Deferred a Operacional
## v7.1 — VANTAGE · 2026-05-31
- Career Canon integrado en el pipeline — 3 patches quirúrgicos sin alterar arquitectura de capas ni ownership Class A/B
- § 11 CV-B — Input ampliado: HANDOFF + Career Canon activo. Canon check obligatorio antes de generar F2. Desviaciones se reportan, no se silencian.
- § 7 Class A · Campo JD — En CV-A, el AI Component cruza keywords del JD contra el Canon antes de generar el HANDOFF. Discrepancias van a fit_gaps.
- § 5 CANON-UPDATE — Contrato completo: output = Canon en Notion + .md con Figma tags (Output Contract v1.0). Dos outputs obligatorios.
- Output Contract v1.0 operativo — tag schema Figma + regla de dos outputs documentada en Career Canon § L
- Career Canon — UF01/02/03 resueltos · KPI06 cerrado (red nacional México) · P02-EN redactado · C03 normalizado a Levi Strauss & Co. (Dockers)
## v7 — VANTAGE · Mayo 2026
- Renombrado de JHS → VANTAGE
- Arquitectura de tres capas (Layer 1 / Layer 2 / Layer 3) documentada formalmente
- Layer 1 — Strategic Search: cuatro motores en paralelo (Gemini, Perplexity, You.com, Grok); ninguno es primary ni fallback
- Layer 2 — Passive Intake: Gmail → Make → Notion (raw, Class B vacío); Make como orchestration puro, sin parsing
- Layer 3 — Active Market Reconnaissance: verificación activa obligatoria antes de salir de capa
- RT-1 Dashboard certificado como operacional: recuperación de vacantes BLOCKED, FSM de 5 estados, event log append-only
- Sección Dashboard añadida al Manual de Usuario con flujo paso a paso y tabla de estados
- Source_Type expandido: Inbound, Referencia, Networking activan Bypass automático
- Separación arquitectónica documentada: EXPIRED (Class B) ≠ Expirada (Class A)
- Comando CANON-UPDATE: genera dos outputs obligatorios (página Notion + archivo .md con Figma tags) bajo Output Contract v1.0
- Indicador de salud Career page URL success rate ajustado a > 80% (Manual) / > 90% (Kernel)
- Triggers: SYNC restringido a datos puros ≤12 líneas; QA evalúa formato y completitud, no fit
- Scripts renombrados: ~/jhs_pipeline.sh → ~/vantage_pipeline.sh; ~/jhs_notion_audit/ → ~/vantage_notion_audit/
- Manual de Usuario reestructurado a 12 secciones; Sección 4 expandida con ciclo semanal de cuatro motores
- Sección ARCHIVADAS separada del documento principal
## v6.2.1 — JHS · Abril 2026
- HANDOFF estructurado con 5 campos obligatorios (empresa, rol, JD_keywords_top6, fit_gaps, tono_marca)
- Trigger SYNC añadido: lee Notion via MCP, reporte máximo 12 líneas, sin WRITE
- Trigger CANON-UPDATE añadido: diff del usuario → bloque Markdown afectado; sin WRITE automático
- Alias map extendido para dedup (LVMH, Kering, Inditex, Nike, Adidas, Luxottica)
- BATCH RULE: FEED con más de 10 vacantes se divide en lotes de 10; procesamiento secuencial con header de lote
- Prioridad 5 y 6 diferenciadas: 5 = exploratorio activo con timing incierto; 6 = radar pasivo/especulativo
## v6.2 — JHS · Abril 2026
- Link muerto = Score 0 sin excepciones (regla endurecida)
- Protección total: si Next_Action ya tiene valor, Python no lo sobreescribe
- Gate decision: Source_Type Inbound/Referencia/Networking activa CREATE automático (Bypass)
## v6.1 — JHS
- Scoring realista: Score ≥ 60 = Ready-to-Apply (umbral consolidado)
- Vista Ready-to-Apply como espacio de trabajo diario principal
## v6.0 — JHS
- URL_GATE pre-scoring: verificación de accesibilidad antes de cualquier cálculo de fit
- Limpieza masiva de entradas legacy
- Score 0 automático para links muertos
## v5.0 — JHS
- Arquitectura híbrida Python + Claude introducida
- Python asume ownership de campos Class B (Score, Gate, VM_Scope, Role_Class)
- Separación formal entre AI Component (texto) y Python (cálculo determinista)
## v4.x — JHS
- Sistema manual Claude-only
- Sin pipeline Python; procesamiento y evaluación en sesión de chat
---
ESTADO: v8.7 | ACTUALIZADO: 2026-06-27
