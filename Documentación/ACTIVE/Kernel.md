# V | KERNEL

# I. FUNDAMENTO
## 01 KERNEL:PURPOSE - Propósito
VANTAGE resuelve un problema de ingeniería de atención: en una búsqueda laboral sin estructura, las oportunidades de alta señal desaparecen antes de ser procesadas, mientras el tiempo se consume en vacantes de baja calidad.
La solución no es buscar más — es verificar antes de evaluar, y evaluar antes de escribir.
Éxito
- El pipeline identifica y captura vacantes relevantes sin ruido ni trabajo manual repetitivo.
- La producción de CV por vacante es rápida, precisa contra el Career Canon y sin alucinación.
- El sistema documental no cuesta más tiempo mantenerlo del que ahorra operarlo.
Qué no es
- No es un proyecto de ingeniería por sí mismo.
- No es archivo histórico de decisiones (eso vive en el Charter).
- No es manual de comandos (eso vive en el MANUAL).
## 02 KERNEL:INVARIANTS - Invariantes
Estas reglas no se negocian. Si una propuesta las viola, se rechaza.
### 02.1 KERNEL:INV-SYSTEM - Invariantes del Sistema
1. Una vacante no entra al pipeline sin URL válida — excepción: Bypass activo (ver 06.1).
1. Score no lo calcula el sistema de lenguaje — lo calcula Python con lógica determinista.
1. Gate_Decision no se sobreescribe manualmente. El Dashboard permite corregir inputs Class A para que Python recalcule (ver 06.3).
1. Strategy es responsabilidad humana; processing es responsabilidad del sistema.
1. El componente AI es el procesador textual del pipeline: deduplica, normaliza, genera DRY RUN, escribe Class A en Notion, produce CVs.
1. Evaluación de calidad estratégica y cálculo de campos Class B no son operaciones de este componente (ver 03.2, 11).
1. Si una tarea no está en la tabla de Triggers (07), no se ejecuta.
### 02.2 KERNEL:INV-FAIL-NATURE - Naturaleza del Fallo
Un fallo del sistema es evidencia de que el pipeline aplica sus criterios, no un defecto a ocultar. La presencia de gates BLOCKED, scores en 0 y entradas EXPIRED confirma que el filtrado opera. Un gate que nunca bloquea no filtra; no constituye un gate.
### 02.3 KERNEL:INV-FAIL-BEHAVIOR - Comportamiento del Sistema Ante Fallo
Ante un fallo detectado, el sistema:
- No repara outputs de forma autónoma.
- No sugiere workarounds.
- No escala urgencia.
- Reporta el estado exacto y espera instrucción humana explícita.
### 02.4 KERNEL:INV-FAIL-DASHBOARD - Comportamiento del Dashboard Ante Opción de Remediación
El AI informa la opción de remediación disponible. No la ejecuta sin instrucción explícita del operador.
## 03 KERNEL:ACTORS - Actores
### 03.1 KERNEL:ACT-ROLES - Roles y Restricciones
| Actor | Responsabilidad | Restricción |
| --- | --- | --- |
| Operador | Decide, aprueba escrituras, transporta handoffs, define strategy | No ejecuta scoring ni escribe Class B |
| AI Component | Deduplica, normaliza, genera DRY RUN, escribe Class A, produce CVs, mantiene documentación bajo contrato | No calcula Score / Gate / VM_Scope / Role_Class / Next_Action ni otro campo Class B |
| Python (Layer 1) | Dueño exclusivo de Class B: scoring, gate decision, mutabilidad, dedup determinista | No interpreta lenguaje natural ni decide strategy |
| Runtime (L0) | Observabilidad, resolución de entidades, lectura documental ReadOnly (vload / Entity Index) | No es capa de autoridad de escritura |
Regla de interacción: si una tarea no está en la tabla de Triggers (07), ningún actor la ejecuta.
### 03.2 KERNEL:ACT-SPLIT - División de Responsabilidades AI/Python
Contrato de frontera: el AI Component procesa texto y escribe Class A bajo contrato de trigger; Python calcula y escribe Class B de forma autónoma y determinista. Ningún campo cruza esta frontera en dirección inversa.
### 03.3 KERNEL:ACT-AI - AI Component — Contrato de Ejecución
Función: procesador textual del pipeline.
Proceso autorizado: validación de triggers, generación de HANDOFF, deduplicación textual, normalización, generación de DRY RUN, escritura de campos Class A, producción de CVs.
Restricciones (no negociables):
- NO modifica campos Class B.
- NO evalúa fit estratégico.
- NO calcula scores ni estima gate decisions.
- NO ejecuta triggers fuera de 07.
- CV-A Scope Lock: prohibido evaluar fit estratégico o cuestionar la Gate_Decision de Python en esta fase. Discrepancias se informan en "observaciones" del HANDOFF sin emitir verbos de decisión ("bloquear", "pasa").
### 03.4 KERNEL:ACT-PY - Python Component — Contrato de Ejecución
Función: motor de lógica de negocio y único componente con permiso de escritura autónoma en Notion.
Proceso: procesa FEED (feed_processor.py, layer_1_run.py, layer_3_mail.py); calcula Score, Gate_Decision, VM_Scope, Role_Class, Next_Action, Fetch, Fuente.
Excepción — Bypass: Source_Type ∈ {Inbound, Referencia, Networking} → Gate_Decision: CREATE automático (ver 06.1).
Invariante crítico: Python recalcula campos Class B en cada run. Ningún valor estimado por el AI Component tiene validez en el pipeline. Aplicado técnicamente en la vía Dashboard mediante guard documentado en 06.3 (GAP-03 cerrado v9.19.2).
---
# II. ARQUITECTURA Y CONTRATOS
## 04 KERNEL:ARCHITECTURE - Arquitectura de Cuatro Capas + Runtime
Reglas de arquitectura: el Runtime no es capa de autoridad de escritura; la precedencia de dedup es L1 > L2 > L3 (código = norma); Graph no se usa para decidir archivado.
### 04.1 KERNEL:ARC-L0 - L0 — VANTAGE Runtime
Tipo: capa de observabilidad, resolución y acceso ReadOnly.
Función: separa la lectura documental de la resolución de entidades mediante dos rutas no intercambiables:
- Documental: PREFIX:CLAVE → vload.py → document_registry → Notion.
- Entidades: entity_id → Entity Index → Resolver → Notion.
- Las rutas no son intercambiables: PREFIX:CLAVE se resuelve mediante vload; TRACKER/ARCHIVO_TRACKER mediante Entity Index + Resolver.
Componentes: vantage.py opera sobre entidades y las capas Query/Context/Agent; expone resolve, context, ask, sync, status. sync reconstruye los artefactos derivados. vload.py es interfaz preferente de lectura documental puntual; lazy_loader.py es su implementación interna. entity_index_v2.json es el snapshot operativo para lookup O(1).
Graph/Backlinks: estado SUSPENDED por diseño. VANTAGE usa movimiento mutuamente excluyente entre TRACKER y ARCHIVO_TRACKER, no relaciones de grafo, para determinar archivado. graph_edges/backlinks_count en 0 no constituye fallo, y Graph no es una capa operativa de resolución.
Fallo: sync persiste last_sync_result.json; status expone antigüedad y resultado. Version Check y Census son herramientas de observabilidad independientes del Runtime de entidades.
### 04.2 KERNEL:ARC-L1 - L1 — Active Recon
Trigger: humano, ciclo semanal (lunes).
Proceso: Human signal → LinkedIn · Aggregators · Career Sites · Gemini (paralelo, ejecutado exclusivamente por Hermes Desktop) → JSON estructurado → FEED → feed_processor.py → Notion (Class A) → vantage-pipeline.
Función: maximizar cobertura y trazabilidad de entrada. No decide prioridad estratégica.
Responsabilidades: buscar vacantes, validar evidencia mínima, extraer campos canónicos, mantener trazabilidad por fuente, emitir resultados estructurados (no recomendaciones).
Ownership de ejecución: exclusivo de Hermes Desktop — ningún otro agente de la matriz de ruteo (04.5) ejecuta esta capa.
Soporte: Weekly Prompt Assembler (weekly_prompt_assembler.py, alias vassemble) materializa prompts desde PROMPT LIBRARY.
Campos inmutables: los campos Class A emitidos por wrapper (05.1) no se reinterpretan — feed_processor.py normaliza formato, no criterio.
Dedup: L1 no deduplica; jerarquía y convergencia en 04.5.
Fallo: fuente sin resultados o evidencia insuficiente → registro no se emite, sin retry automático (02.2).
Métricas mínimas: resultados por fuente, total, timestamp de búsqueda.
### 04.3 KERNEL:ARC-L2 - L2 — Strategic Search
Trigger: humano, sin ciclo fijo.
Proceso: Operador (chat) → Claude → Notion (Class A poblado, Class B vacío) → vantage-pipeline.
Función: captura puntual fuera del ciclo automatizado de L1, sin wrappers ni PROMPT LIBRARY.
Proceso de población: recibe vacante en lenguaje natural o URL, puebla Class A, deja Class B vacío para cálculo de Python en el siguiente run.
Dedup: L2 no deduplica; mismo patrón que L3 (ver KERNEL:ARC-L3).
Fallo: dato insuficiente para Class A mínimo → Claude solicita el dato faltante; no infiere.
Métricas mínimas: registros ingresados, timestamp.
### 04.4 KERNEL:ARC-L3 - L3 — Passive Intake
Trigger: automático, continuo.
Proceso: Gmail (.Jobs label) → layer_3_mail.py (IMAP + backend ollama/groq) → Notion (Class A poblado, Class B vacío) → vantage-pipeline.
Función: captura pasiva continua, sin ciclo humano ni dependencia de búsqueda activa.
Campo inmutable: GEMINI_MAX_EMAILS_PER_RUN limita por corrida (default: 5); Class B nunca se estima aquí.
Dedup: L3 no deduplica — entra directo a feed_processor.py.
Fallo: si falla el parseo JSON, se agotan reintentos, Ollama no está disponible, o error inesperado → el correo se conserva no leído vía _set_seen(..., False) para reintento. Solo se marca leído tras extracción o descarte correctamente clasificado.
Métricas mínimas: correos procesados, vacantes extraídas, Class A poblado / Class B pendiente.
### 04.5 KERNEL:ARC-L4 - L4 — Version Control & Infrastructure
Función: infraestructura documental, no capa de búsqueda.
Repo: github.com/mauriciomeyran/VANTAGE.
Automatización vigente:
- Auto-commit + push (alias vgit) en cambios de repo, 09:00/15:00/21:00.
- Cron adicionales vía ruta directa al Python del venv (source .venv/bin/activate falla con "Operation not permitted" en entorno cron): vantage.py sync, notion_backup.py, vl3 — 00:00/08:00/16:00.
- vsync_doc.py (alias vdoc, flags dry|notion|local|auto): sync bidireccional Notion↔ACTIVE/ para los 8 documentos del diccionario DOCS (6 fundacionales + Navigation Brief + Change Log Archivo); normativamente solo los 6 son "fundacionales", pero el script sincroniza los 8.
- git_sync.py regenera skills/index.json antes de git status en cada sync().
- Política de versionado (H-6, confirmada): commit automático de todo el árbol no ignorado; .db de estado se versiona por trazabilidad histórica.
Riesgo activo: push_local_to_notion() (vsync_doc.py) ejecuta delete-all + create-all de bloques en cada corrida — cualquier anchor #block-id de hyperlinks (14.6) queda huérfano. apply_hyperlinks_notion.py evita este riesgo (PATCH puntual); vdoc local carece de guard equivalente — evitar sobre documentos con hyperlinks recién aplicados.
Estado de scripts: layer_1_run.py reemplazado por layer_1_orchestrator.py (refactor v9.22.0, mismo alcance, cuatro modos de ejecución — 08.2); layer_1_run.py archivado, fuera de riesgo activo. vsync_doc_fast.py deprecado en Archive/Legacy_Scripts/.
Skills Distribution (Single Source of Truth): /skills/ es la fuente canónica de .md; skills/triggers.json es el manifiesto SSOT ({trigger[], path, description, last_modified}), generado por update_triggers_json.py (alias vtriggers), que en cada corrida: escanea altas, valida SKILL.md físico, detecta huérfanos (reporta, no elimina), actualiza last_modified, y ejecuta git add+commit+push automático sobre triggers.json validando cada paso explícitamente. Cada entrada incluye notion_id poblado por fetch_notion_skill_library().
Matriz de ruteo por agente (8 auditados):
- Familia MCP-Notion (Claude, Cursor, Devin, ChatGPT, Littlebird, Grok) → notion_id → notion-fetch.
- Familia GitHub-only (Perplexity, Mistral) → url → fetch raw. Perplexity requiere repo público.
- Gemini → sin ruta de fetch confiable; único canal cero-fricción es Gem con Knowledge precargado, fuera del flujo de triggers.json.
- Hermes → ejecuta L1 exclusivamente (LinkedIn · Aggregators · Career Sites · Gemini, ver KERNEL:ARC-L1); no consume triggers.json.
- Claude (claude.ai/API): fetch del manifiesto vía web_fetch a https://raw.githubusercontent.com/mauriciomeyran/VANTAGE/main/skills/triggers.json (Bootloader, junto con SYSTEM PROMPT e ID CENSUS); contenido de skills vía git clone --depth 1 + lectura local (vía primaria y estable: web_fetch sobre raw.githubusercontent.com está bloqueado para URLs que no hayan aparecido antes en la sesión, restricción estructural de la herramienta); web_fetch es fallback si git clone falla. Carga bajo demanda por match de trigger, nunca masiva.
- Riesgo de caché de fetch intra-sesión verificado empíricamente (2026-08-16): reintentar con cache-busting (?t={timestamp}) antes de asumir fallo del repo.
- Descontinuado sin reemplazo funcional necesario: GitHub Pages, índice MCP estático, devin mcp add vantage-skills.
Continuidad entre sesiones: vsum.py (alias vsum) resume transcripts a Markdown estructurado, escribe vía notion_client.Client directo como página hija del INBOX. No lee ni escribe el Tracker de vacantes; salida únicamente.
Jerarquía de Dedup: L1 > L2 > L3. L1 y L3 entran directo a feed_processor.py; L2 no deduplica (ver KERNEL:ARC-L2).
Mecanismos de Dedup (dos, complementarios, no excluyentes):
1. Tiempo real (ingesta): hash exacto + URL exacta + brand+title, ventana 30d, feed_processor.py. Previene contaminación obvia al ingresar.
1. Auditoría post-ingesta: fuzzy matching (brand≥0.85, rol≥0.7) + fingerprint, ventana 60d, dedup_opportunities.py + Archive Tracker. Detecta duplicados sutiles (rotación de jk, reposts). Automatizado (v9.21.0) vía ENABLE_DEDUP_AUDIT=true al final de layer_1_run.py; hereda --dry-run; exporta dedup_metrics.json; filtro ANTI_FALSE_POSITIVE_RULES extensible.
Punto de Convergencia Único: las tres capas de búsqueda escriben a Notion. vantage-pipeline lee de Notion, nunca de outputs de capa directamente.
Figma Sync — CV Output Layer
Tipo: capa de materialización de CV, WriteOnly sobre lienzo Figma activo. Arquitectura de 3 piezas sobre permisos mínimos (sin capabilities, sin red).
- manifest.json: identidad (vantage-cv-sync), sandbox (code.js), UI (ui.html).
- ui.html: parser de entrada — detecta formato, sanitiza Markdown, extrae boldRanges.
- code.js: Registry V2 (registry_seed.json) + resolución O(1) vía figma.getNodeById + escritura tipográfica.
- Canal único de datos: postMessage entre ui.html y code.js. Sin transporte de red.
Flujo: CV-B (Markdown + figma_text_id) → ui.html (parsing + sanitización + postMessage) → code.js (Registry V2 → figma.getNodeById(rawId)) → node.characters = item.text → Lienzo Figma.
Invariantes: no escribe en Notion ni Tracker; no es capa de búsqueda; registry_seed.json no se edita manualmente sin regenerar desde Figma.
### 04.6 KERNEL:ARC-DASHBOARD - Arquitectura Dashboard/Checklist
Tipo: capa de presentación sobre datos producidos por las capas de búsqueda.
- Backend operativo real: dashboard_server.py + dashboard.db + dashboard_notion.py — fuente de verdad del pipeline; dashboard.html consume vía fetch('http://127.0.0.1:8000/{path}').
- Checklist operativo semanal: Checklist.html, standalone, estado en localStorage['vchecklist_v1'], sin backend ni Notion.
- Capa visual compartida: vantage-tokens.css + vantage-theme.js — única capa realmente compartida entre backend y checklist.
Regla: todo cambio a color de estado semántico o toggle de tema se hace exclusivamente en vantage-tokens.css/vantage-theme.js, nunca inline.
## 05 KERNEL:SCHEMA - Contrato de Datos
Reglas maestras: el AI nunca escribe Class B; la mutabilidad de estados terminales/en-proceso se gobierna solo por tracker_flow.is_mutable(); Dedup_Flag es checkbox, no select; Match no es campo (decisión 2026-10-03); Hard Blocks se leen de hard_blocks.json versionado, con fallback interno solo si el archivo no existe.
"El Tracker" sin calificativo refiere siempre a la base de datos principal donde L1/L2/L3 escriben cada vacante — distinta de Bug Tracker y Tasks Tracker (05.10).
### 05.1 KERNEL:SCH-OWNERSHIP - Class A vs Class B — Ownership de Campo
El schema define ownership: cada campo pertenece a exactamente un componente. El upgrade de layer en dedup respeta el guard de 06.12 — no reescribe procedencia de una postulación viva.
Class A — Human-Primary. AI Component escribe en CV-A · CV-B · QA · FAST · CANON-UPDATE; feed_processor.py escribe en FEED L1/L3: Rol · Marca · Source_Type · URL · Status · Positioning_Mode · Prioridad · Holding · JD · NAD · layer · hash · Fetch · Fuente · JOB_ID (opcional).
Valores operativos de Status: Target · Postulado · Rechazado · Expirada · Archivar · Repetida.
Notas recibe el texto determinista de auditoría de archivado escrito por VL1 (06.13) — es trazabilidad de decisión, no Class B pese a ser escrito por comando Python.
Class B — System-Primary. Python escribe: Score · Gate_Decision · VM_Scope · Role_Class · Next_Action · Dedup_Flag · Score_Method · Last_Gate_Run · Class_B_Last_Run · JD_Quality.
VM_Scope ∈ {Alto, Bajo} — campo binario. No existe valor "Medio" en ningún punto del sistema.
Resolución B-09 (2026-09-17): Notion es la autoridad declarada (SSOT) del esquema; class_b_guard.py es su espejo en código, con divergencia conocida (Prioridad_Auto). Sincronización manual hoy; propuesta de verificación automática pendiente (verify_versions.py o g9_docsync_verify.py).
### 05.2 KERNEL:SCH-INGEST - Restricción de Ingesta
Campos Class B en JSON entrante se ignoran sin excepción. Python los calcula en el siguiente run.
### 05.3 KERNEL:SCH-SOURCE - Fuente como Campo Especial
Fuente es Class A, escrita por feed_processor.py al crear la fila (notion_utils.pages.create). Fuente_Manual no existe en código ni como propiedad del Tracker en Notion.
### 05.4 KERNEL:SCH-ENTITY - Entity Format
PREFIX:H_<hash16> / PREFIX:U_<UUID>. Prefixes válidos: TRACKER, ARCHIVO, DRYRUN, BUG. Namespace Ownership Contract: resolver_registry_v2.json es el único punto de verdad para entity_prefix. Ver 04.1 para el mecanismo de resolución.
### 05.5 KERNEL:SCH-RESOLUTION - Contrato de Resolución: 4 Pasos
Lookup → Registry Mapping → Notion Query → Validation. Contraparte de datos del Runtime descrito en 04.1.
### 05.6 KERNEL:SCH-APPROVE - APROBAR_WRITE: Alcance
Autoriza escritura de campos Class A únicamente. Variantes aceptadas: APROBAR_WRITE · APROBAR · SÍ · sí · YEP · yep. Eliminados (RAI-03): Ok · Go · YES · yes.
### 05.7 KERNEL:SCH-ACCEPTANCE - Acceptance Audit
Resultados: PASS / PASS WITH ARCHITECTURAL FINDING / FAIL.
Mapeo de vocabulario Prompts→Tracker: source_type "career_page" → Career Page Oficial; source_type "job_board" → Agregador; source_name → NO escribir (Class B); apply_url → URL; brand → Marca; title → Rol; holding → Holding (null → "Investigar").
Entry Template — Campos Class A requeridos: Rol · Marca · URL · Source_Type · Status · Prioridad · JD · Holding. JOB_ID es Class A opcional: si falta o es generado, el hash de dedup usa fallback:{composite_key}.
### 05.8 KERNEL:SCH-NEXTACTION-VALUES - Valores Operativos — Next_Action (Tracker de Vacantes)
Campo Class B, tipo select (migrado de rich_text en v9.14.2), escrito por layer_1_run.py/layer_1_run_dash.py con estructura {"select": {"name": VALUE}}.
| Valor | Condición de disparo |
| --- | --- |
| Optimizar | JD_Quality = "JD Completo" |
| Archivar | Terminal — URL Gate bloqueado / Misfits / NAD vencido / Gate BLOCKED default |
| Investigar | Default no destructivo — ningún branch matchea (catch-all, v9.14.5) |
| Post-Mortem | Status=Rechazado → Gate_Decision=REJECTED |
| Expirada | Constante de protección en TERMINAL_ACTIONS (gate_logic.py) |
| Follow-up | Status ∈ {Postulado, Negociando, Sin respuesta} |
| Interview prep | Status=En proceso |
| Re-check | Gate_Decision=CREATE (Vacante), o Source_Type=Inbound |
| Reparar URL | Source_Type=Vacante AND Fetch=Bloqueado, o agregador con HEAD fallido |
| Verificar JD | Source_Type=Vacante AND Fetch=Parcial |
Procedencia: v9.13.7 introdujo escritura select; v9.13.11 documentó erróneamente rich_text; v9.14.2/v9.14.3 confirmaron la migración real; v9.14.5 corrige la documentación.
### 05.9 KERNEL:SCH-WRITERS - Escritores hacia Notion — Matriz de Integridad
Ocho componentes escriben sobre el Tracker o derivados. Todos pasan por class_b_guard.guard_write_payload() salvo donde se indica.
| Escritor | Escribe sobre | Guard |
| --- | --- | --- |
| feed_processor.py | Class A (ingesta L1/L3) | Validación de schema en ingesta |
| layer_1_orchestrator.py | Class A + Class B | class_b_guard |
| dashboard_notion.py::write_patch_to_notion() | Class A (Dashboard) | class_b_guard, fail-closed |
| dedup_opportunities.py | Class B (Dedup_Flag) + Archive Tracker | class_b_guard(payload, Actor.DEDUP) (Fase 2, 2026-09) |
| vsync_doc.py | Documentos fundacionales (no Tracker) | N/A — housekeeping documental |
| apply_hyperlinks_notion.py | Bloques de Notion (PATCH puntual) | N/A — preserva block-ID |
| vsum.py | Página hija de INBOX | N/A — no toca el Tracker |
| allocate_vantage_serial.py | GLOBAL_VANTAGE_COUNTER (SQLite, no Notion) | N/A — fuera de alcance de class_b_guard |
Nota de historial: dedup_opportunities.py no pasaba por guard hasta la remediación de Fase 2 (2026-09).
### 05.10 KERNEL:SCH-TRACKER-ROUTING - Alcance
Reactivo (algo roto) → Bug Tracker. Proactivo (trabajo/decisión pendiente) → Tasks Tracker.
| Tracker | DB ID | COL ID |
| --- | --- | --- |
| Bug Tracker | 36e938be-fc42-81bd-9e1f-dc360b3b45f5 | 36e938be-fc42-81f8-8c6f-000b6769ba03 |
| Tasks Tracker | d2a65ca1-6a35-465d-bcff-b0d82dddd549 | aaaaef55-a1ce-45f7-9c8b-1c1def2c18e8 |
### 05.11 KERNEL:SCH-PRIORITY - Niveles de Prioridad
| Nivel | Criterio |
| --- | --- |
| 4 CRÍTICO | El flujo punta a punta no puede completarse |
| 3 ALTO | El flujo se completa forzando el sistema (workaround requerido) |
| 2 MEDIO | Sin resolución en la semana, el flujo se verá comprometido |
| 1 BAJO | No bloquea operación — nice-to-have |
## 06 KERNEL:GATE - Gate Decision
Python evalúa inputs Class A + reglas deterministas → produce Gate_Decision y campos Class B asociados. Bypass es excepción documentada, no atajo silencioso. Los estados terminales y en-proceso están protegidos: ningún --apply avanza sobre premisas no verificadas.
### 06.1 KERNEL:GATE-BYPASS - Bypass
Source_Type ∈ {Inbound, Referencia, Networking} → Gate_Decision: CREATE automático. Bypasses adicionales: URL_GATE + Score threshold + Visual Signal detection.
### 06.2 KERNEL:GATE-LOGIC - Lógica Estándar
Orden:
1. URL_GATE: link muerto → Score=0, Status=Expirada. Para agregadores (Computrabajo, Indeed, LinkedIn): chequeo HEAD con timeout 6s en vez de bloqueo ciego. Fallo del HEAD check en agregadores NO archiva automáticamente: escribe Fetch=Accesible, Status=Target, Next_Action=Reparar URL (fix v9.21.40) — distinto de sitios directos, donde el fallo mantiene Score=0/Status=Expirada/Next_Action=Archivar.
1. Score (0–100).
1. Gate_Decision: ≥60 CREATE · 40–59 REVIEW_NEEDED · <40 BLOCKED/Archivar.
### 06.3 KERNEL:GATE-REVIEW - Resolución de REVIEW_NEEDED
GAP-03 CERRADO (v9.19.2): escritura directa vía MCP/Dashboard cuenta con guard equivalente al de feed_processor.py. class_b_guard.guard_write_payload() integrado en dashboard_notion.py::write_patch_to_notion(), fail-closed (CLASS_B_BLOCKED) ante campos Class B o desconocidos (strict_unknown=True). Disparador de resolución: Status = "Target".
### 06.4 KERNEL:GATE-DETERMINISM - Determinismo del Gate
Un gate que puede sobreescribirse manualmente no es un gate — es una sugerencia. Ningún Gate_Decision admite override manual directo.
### 06.5 KERNEL:GATE-BLOCKED - Flujo de Recuperación BLOCKED
El Dashboard permite corregir campos Class A y re-validar con Python. El Dashboard no sobreescribe el gate.
### 06.6 KERNEL:GATE-REJECTED - REJECTED (Post-Aplicación)
REJECTED es Class B derivado de Status = "Rechazado" (Class A). Python traduce vía evaluate_rejection_status(). El operador nunca escribe Gate_Decision directamente.
### 06.7 KERNEL:GATE-ARCHIVE-MARK - Marcado Manual de Archivado
Next_Action='Archivar' y/o Dedup_Flag='Posible duplicado' (ambos Class B) son señales de candidato a archivar — no disparan archivado automático. Sujeto al guard de 06.12.
Mecanismo vigente: skill vantage-tidy-opportunities-tracker identifica candidatos vía Dedup_Flag/Next_Action, marca Archivar = True en el registro original tras DRY RUN + APROBAR_WRITE. La razón textual del candidato a archivo la escribe VL1 (06.13); este nodo cubre solo el marcado.
El operador localiza visualmente los registros marcados y decide cuándo archivarlos manualmente.
Fallo: auto_archive.py fue deprecado por decisión del operador (2026-08-01).
### 06.8 KERNEL:GATE-LAYERS - Capas de Evaluación de Gate: Técnica vs. Negocio
gate() — capa técnica, CREATE/BLOCKED puro. gate_logic() — capa de negocio/workflow, protege estados terminales.
### 06.9 KERNEL:GATE-ESCALATION - Escalamiento de Pendientes a Tickets
Nivel 1 — Bajo esfuerzo (referencia orientativa: <5 iteraciones) / sin evidencia de bloqueo: se mantiene en Handoff/pending_summary; no dispara ticket.
Nivel 2 — Alto esfuerzo (referencia orientativa: ≥5 iteraciones) / sin evidencia dura: Claude sugiere ticket y espera APROBAR_WRITE explícito. Sin confirmación → permanece en Nivel 1; la sugerencia no se reintenta en la misma sesión salvo que el operador la reactive.
Nivel 3 — Bloqueo confirmado por fuente dura (Dump de Terminal, Ledger, Changelog, declaración directa del operador): se dispara automáticamente vantage-create-bug-task sin esperar confirmación.
Restricción crítica: el umbral de iteraciones es criterio orientativo para Nivel 1 vs Nivel 2 y nunca criterio único para Nivel 3; el único criterio duro de Nivel 3 es bloqueo/degradación confirmado por fuente dura. Inferencias de Claude nunca califican para Nivel 3 (SP:CONSISTENCY 05). Re-evaluación Nivel 2→3 exige declaración explícita ante el operador.
### 06.10 KERNEL:GATE-TERMINAL - Definición de Estados Terminales Protegidos
Fuente de verdad ejecutable: gate_logic.py.
Orden de evaluación obligatorio:
1. Status → STATUS_TERMINAL_MAP: "Postulado"→APPLIED, "Rechazado"→REJECTED, "Expirada"→EXPIRADA (fix D-001, v9.19.1).
1. Next_Action → TERMINAL_ACTIONS: "Archivar" · "Expirada".
1. Si ninguno aplica → None (elegible para recálculo por gate()).
Invariantes: gate_logic() se invoca antes de gate(); todo write que fije Status=Expirada debe fijar Next_Action=Archivar en el mismo write; un registro terminal no puede sobreescribirse por recálculo; Dashboard (/accept, atomicidad RT-1) limpia atómicamente Next_Action y Gate_Decision en el mismo write; "Por Revisar" nunca formó parte de los conjuntos de protección.
Protección estrecha: solo los valores listados arriba; cualquier otro Next_Action (Follow-up, Re-check, etc.) es recalculable — coherente con KERNEL:ACT-PY.
Contratos relacionados: KERNEL:GATE-BLOCKED, KERNEL:GATE-REJECTED, KERNEL:GATE-LAYERS, KERNEL:ACT-PY.
### 06.11 KERNEL:GATE-TRANSITIONS - Matriz de Transición de Estados (Referencia Técnica)
Vista tabular consolidada de las reglas Gate (06.1–06.13). Matiz (2026-08-17): "Dedup match en existente" se ajusta a Dedup_Flag='Posible duplicado' solo si el Status del existente no está en el guard de 06.12.
| Estado Origen | Evento/Trigger | Estado Destino | Efecto Class B |
| --- | --- | --- | --- |
| [ENTRY] | URL muerta OR Score<40 | BLOCKED | Gate_Decision=BLOCKED, Score=0 |
| [ENTRY] | URL viva + Score 40–59 | REVIEW_NEEDED | Gate_Decision=REVIEW_NEEDED  • campos |
| [ENTRY] | URL viva + Score≥60 | READY_TO_APPLY | Gate_Decision=CREATE  • campos |
| [ENTRY] | agregador HEAD fallido | Target | Fetch=Accesible, Next_Action=Reparar URL |
| [ENTRY] | Dedup match ventana 30d | REVIEW_NEEDED | Dedup_Flag en existente |
| BLOCKED | patch válido dry PASS | PATCHED | Score/Gate recalculados |
| PATCHED | aceptar | READY_TO_APPLY o BLOCKED | Gate re-evaluado |
| REVIEW_NEEDED | Status→Target | READY_TO_APPLY o BLOCKED | Score/Gate/Next_Action calculados |
| READY_TO_APPLY | Status→Postulando | APPLYING | Status |
| APPLIED | Status→Rechazado | REJECTED | Next_Action=Post-Mortem |
| Cualquier no-terminal | Status ∈ {Postulado, Rechazado, Expirada} | estado preservado | sin escritura |
Precedencia: gate_logic() se ejecuta antes que gate() como filtro de mutabilidad.
### 06.12 KERNEL:GATE-MUTABILITY - Guard de Mutación en Existentes
Alcance: gobierna la mutación de registros existentes durante la ingesta (feed_processor.py). Fuente de verdad: profile_fit._PROTECTED_STATUSES ∪ _TERMINAL_STATUSES.
| Status del existente | ¿Dedup_Flag? | ¿Upgrade layer? |
| --- | --- | --- |
| Target/Exploratorio/REVIEW_NEEDED/vacío/otro operativo | Sí | Sí |
| Postulado/Postulando/En proceso/Negociando/Sin respuesta/Contratado | No | No |
| Rechazado/Expirada/Archivar/Retirado | No | No |
El inbound sigue entrando como REVIEW_NEEDED aunque el existente no se mute.
### 06.13 KERNEL:GATE-ARCHIVE-AUDIT - Auditoría de Archivado en Tiempo Real
Función: generate_archive_notes(), invocada desde layer_1_run.py en tres puntos deterministas: URL Gate bloqueado (Fase 2), Misfit de perfil (Fase 3.5), NAD vencido.
Contrato de escritura: el mensaje se escribe en Notas (Class A) — nunca sobrescribe, agrega (append) separado por línea vacía.
Ownership: VL1 documenta la razón en el momento de la decisión. vantage-tidy-opportunities-tracker y vantage-housekeeping-archive no generan esta nota.
---
# III. OPERACIÓN
## 07 KERNEL:TRIGGERS - Triggers
Si una tarea no está en esta tabla, no se ejecuta. Cada trigger define un contrato de input, proceso y output.
### 07.1 KERNEL:TRG-FEED - FEED
Trigger: JSON de vacantes con trigger explícito.
Proceso: validación de longitud → header de lote → mapeo de vocabulario (05.7) → detección de señales de advertencia → filtrado de campos prohibidos → escritura secuencial.
Procesamiento por lotes: >10 vacantes se divide en lotes de 10, secuencial, con header de lote. Sin reintento automático por lote.
Restricciones: NO escribir campos Class B; NO reparar URLs rotas; NO procesar lote N+1 si lote N falló.
### 07.2 KERNEL:TRG-VL1 - VL1
Comandos de mantenimiento del Tracker — comandos Python autónomos, no triggers del AI Component. Ningún comando VL1 escribe campos Class B.
VL1 backfill: catch-up de Class A faltante (layer, hash, Prioridad). Prioridad = matriz Urgencia × Importancia. Importancia = bucket de Score: Base(=40) · Media(41–60) · Alta(61–80) · Muy Alta(81–100).
| Urgencia  Importancia | Base | Media | Alta | Muy Alta |
| --- | --- | --- | --- | --- |
| CRÍTICO (deadline/Inbound) | CRÍTICO | CRÍTICO | CRÍTICO | CRÍTICO |
| ALTO (≤3 días) | MEDIO | ALTO | CRÍTICO | CRÍTICO |
| MEDIO (4–14 días) | BAJO | MEDIO | ALTO | CRÍTICO |
| BAJO (>14 días) | BAJO | BAJO | MEDIO | ALTO |
VL1 batch: modifica Status (Class A) en batch. Guardia: ausencia de execute hace el comando read-only permanentemente; nunca usa input() interactivo.
VL1 archivado: escribe simultáneamente la nota determinista en Notas vía generate_archive_notes() (06.13).
### 07.3 KERNEL:TRG-QA - QA
Función: validación de formato de CV exportado. No evalúa fit, oportunidad, score ni conveniencia de aplicar.
Checklist canónico de 7 ítems (fuente de verdad: skill vantage-qa, v9.16.0+): invarianza estructural, orden cronológico (C01→C05), cobertura JD, Hard Blocks, no-inferencia/Canon, formato y completitud, diferenciación de contenido (anti-cloning).
Output: GO/NO-GO por ítem; cualquier FAIL → NO-GO final.
### 07.4 KERNEL:TRG-DRYRUN - DRY RUN
Función: preview obligatorio de escritura. No hay escritura sin DRY RUN previo.
Campos permitidos (Class A): Op · Empresa · Rol · URL · Source_Type · Prioridad · Status.
Campos prohibidos (Class B): Visual Signal · Innovation DNA · Score Estimado · Gate_Decision · Decisión CREATE/BLOCKED.
Autorización: una variante válida de APROBAR_WRITE (05.6).
### 07.5 KERNEL:TRG-SYNC - SYNC
Función: reporte de estado del Tracker. Datos puros, sin interpretación.
Output (≤12 líneas):
```javascript
SYNC REPORT — [FECHA]
Target: X | Postulado: X | En proceso: X | Rechazado: X | Total: X
NADs OVERDUE: X
LAST WRITE: [timestamp]
```
### 07.6 KERNEL:TRG-TOP3 - TOP 3 BY SCORE
Query de las 3 vacantes con mayor Score. Campos permitidos: Marca, Rol, Score, (opcional) URL. Sin evaluación de "cuál aplicar primero".
### 07.7 KERNEL:TRG-NEXTACTION - NEXT ACTION
Ejecuta ~/vantage_pipeline.sh status y reporta el output exacto, sin interpretación ni resumen.
### 07.8 KERNEL:TRG-FEED-REDIRECT - FEED (migración)
JSON de vacantes sin trigger explícito → respuesta: "El procesamiento de FEED está migrado a feed_processor.py." Excepción FAST: array de longitud 1 + trigger FAST explícito = procesamiento normal, sin lotes.
### 07.9 KERNEL:TRG-STATUS - STATUS
Lectura del estado general del sistema. Solo lectura; no interpreta si el sistema está "sano" o "degradado" — reporta datos.
## 08 KERNEL:FLOW - Flujo de Datos y Escritura
### 08.1 KERNEL:FLOW-CONTRACT - Contrato Kernel → DRY RUN → APROBAR_WRITE → Write
Contrato: Kernel → DRY RUN → APROBAR_WRITE → Notion Write. El AI Component consulta el Kernel para confirmar el contrato del trigger activo, produce DRY RUN (07.4), espera variante válida de APROBAR_WRITE (05.6), y solo entonces escribe. Ningún paso es saltable.
### 08.2 KERNEL:FLOW-WRITE-RISK - Contrato de Niveles de Riesgo de Escritura — Terminal
El contrato 08 gobierna al AI Component. Los scripts de Terminal sobre Notion (layer_1_orchestrator.py, vl1_sync.py y equivalentes) no pasan por confirmación textual de chat — su contrato de riesgo es la contraparte mecánica del mismo invariante:
- Nivel verde (sin red): cliente fake, sin token requerido.
- Nivel amarillo (lectura de producción): requiere NOTION_TOKEN, consulta datos reales, writes=0 por diseño.
- Nivel rojo (escritura de producción): requiere flag explícito (--apply) MÁS condición externa de contexto (freeze de cutover o intención declarada del operador).
Pre-validación: cruzar esquema contra 05 antes de cualquier escritura.
### 08.3 KERNEL:FLOW-CONTEXT-ECONOMY - Economía de Contexto y Rutas de Carga
Acceso a lógica base preferente vía Terminal (lazy_loader.py). MCP autorizado para lectura, DRY RUN y modificación documental cuando exista instrucción explícita. Jerarquía: L1 > L2 > L3. FEED: única vía manual es FAST (07.8). Triaje de ejecución: Requerimientos → Triaje de costos (A: Terminal, B: MCP, C: Upload) → Confirmación. Priorizar Opción A.
### 08.4 KERNEL:FLOW-CONTEXT-ROUTING - Routing
MCP autorizado cuando: el operador lo solicite explícitamente; la operación sea documental; se presente DRY RUN previo; exista autorización posterior vía APROBAR_WRITE.
Ruta recomendada: python lazy_loader.py --page {KERNEL_MASTER} --route {ruta}.
## 09 KERNEL:CVP - Pipeline de CV — Arquitectura de Dos Sesiones Obligatorias
La preparación mecánica previa a CV-A (scaffold, batch opcional) vive en 09.3 — no es una tercera sesión de IA, es tooling de Terminal.
### 09.1 KERNEL:CVP-CVA - CV-A
Input: URL o JD — opcionalmente pre-poblado por HANDOFF scaffold mecánico (09.3).
Proceso: extrae keywords + gaps + tono de marca. Determina Positioning Mode mediante Algoritmo de Selección N1–N4:
1. Keywords — extraer JD_keywords_top6 del JD.
1. Mapeo — alinear cada keyword contra anclajes canónicos de CANON:POSITIONING.
1. Conteo — contar matches por ancla.
1. Desempate — si dos o más modos empatan, aplicar Regla de Desempate (keywords → seniority → escalamiento humano).
Contrato de persistencia: CV-A escribe positioning_rationale (texto libre, 1 línea) en el HANDOFF. Sin este campo, el HANDOFF está incompleto y no avanza a CV-B.
Output: HANDOFF (JSON de 8 campos: 7 canónicos + observaciones, texto libre y opcional):
```json
{
  "empresa": "", "rol": "",
  "JD_keywords_top6": ["", "", "", "", "", ""],
  "fit_gaps": ["", ""],
  "tono_marca": "", "idioma": "",
  "positioning_rationale": "", "observaciones": ""
}
```
Fallo: un HANDOFF incompleto no avanza a CV-B.
Campos de admisión (2026-09-03): cv_b_eligible (booleano) y block_reason (array). cv_b_eligible=false cuando Positioning_Mode=EMPATE, o Status ∈ {Expirada, Archivada, Rechazada}, o Next_Action=Archivar.
Regla de orden de experiencia: cronológico descendente siempre. Orden canónico obligatorio C01→C05.
Cierre obligatorio: SESIÓN COMPLETADA → nueva sesión.
### 09.2 KERNEL:CVP-CVB - CV-B
Input: HANDOFF completo + Career Canon activo.
Restricción de Lote (Single-Item Processing): CV-B procesa exactamente UN HANDOFF por invocación. Ante batch: (1) tomar el primer HANDOFF y procesarlo completo; (2) detenerse y esperar invocación explícita separada. Razón: degradación de densidad y esfuerzo narrativo observada empíricamente en procesamiento secuencial de lote (post-mortem v9.16.0, 13 CV-B en una sesión) — es un fallo de ejecución bajo carga repetitiva, no un gap documental; el contrato formal (IDs, Anti-cloning Guard, secuencia C01–C05) no lo previene.
Validation: verificar los 7 campos del HANDOFF.
Canon check: empresa, rol, bullets y KPIs derivados del Canon — no inventados. Prohibido reutilizar bullets pre-redactados verbatim entre vacantes distintas.
Auditoría de Estructura: COUNT(figma_text_id)_SKELETON = COUNT(figma_text_id)_OUTPUT. Si no coincide, abortar y re-mapear.
Auditoría de Registry Membership: cada figma_text_id del output debe pertenecer literalmente al registry_seed.json vigente y cada ID del registry debe aparecer una sola vez en el output.
Auditoría de Secuencia: los slots deben aparecer en secuencia canónica estricta C01→C05.
Límite del conteo: un conteo coincidente no prueba identidad ni secuencia — un schema heredado puede conservar la cantidad esperada con IDs obsoletos, slots fusionados o desplazados. Si membership, unicidad o correspondencia exacta contra el Skeleton falla, abortar y re-mapear antes de declarar PASS_FOR_FIGMA.
Output: Markdown con Figma tags.
Post-autorización: escribir en Notion bajo # MARKDOWN CANON ALIGNED.
Post-aplicación: Status = Postulado → Python marca APPLIED.
### 09.3 KERNEL:CVP-BATCH - Preparación Mecánica de Batch (Terminal)
Tooling de Terminal, no sesión de IA — extracción de keywords/gaps y selección de Positioning Mode siguen siendo exclusivas de CV-A.
Cadena: adapt_tracker_export.py → cv_a_batch_agent.py → cv_a_prep.py.
Función: genera HANDOFF_scaffold_<ID>.md por vacante Ready-to-Apply en un solo paso de Terminal.
No reemplaza: CV-A — cada scaffold requiere su propia invocación CV-A [scaffold], una vacante a la vez (Restricción de Lote, KERNEL:CVP-CVB).
## 10 KERNEL:CANON-UPDATE - Actualización del Canon
Función: mantiene actualizada la fuente que el pipeline de CV extrae — el Career Canon. No es discovery, scoring, gate decision ni evaluación de fit.
Input: descripción explícita del cambio solicitado por el operador.
Validación previa: identificar sección(es) afectadas, IDs canónicos impactados, si requiere versión ES/EN/ambas, si impacta CV-A/CV-B/QA/Output Contract, si la información es suficiente.
Flujo obligatorio (6 pasos): recibir descripción → identificar secciones afectadas → validar contra Canon activo → producir DRY RUN → esperar autorización → producir outputs (página Notion + archivo .md).
Restricciones: no evalúa fit; no calcula score; no modifica campos Class B; no inventa KPIs/fechas/certificaciones; no altera figma_text_id sin instrucción explícita; preserva orden C01→C05.
Cierre:
```javascript
CANON-UPDATE COMPLETADO
Secciones actualizadas: [lista]
IDs impactados: [lista]
Outputs entregados: Página Notion · Archivo .md
Compatibilidad downstream: CV-A: PASS/FAIL · CV-B: PASS/FAIL · QA: PASS/FAIL
```
Fallo: información insuficiente → el sistema solicita el dato faltante antes de producir el DRY RUN.
## 11 KERNEL:CVR - CV Golden Rules
Toda afirmación de experiencia debe ser verificable contra el Career Canon; no se inventan títulos, fechas, logros ni métricas.
### 11.1 KERNEL:CVR-NOFIT - Regla #1 — No Evaluar Fit Antes de Escribir
Excepción: CV-A extrae keywords/gaps técnicos — no constituye evaluación de fit.
### 11.2 KERNEL:CVR-NOCLASSB - Regla #2 — No Calcular ni Estimar Campos Class B
Campos protegidos: Score · VM_Scope · Role_Class · Gate_Decision · Next_Action · JD_Quality · Dedup_Flag · Score_Method · Last_Gate_Run · Class_B_Last_Run.
### 11.3 KERNEL:CVR-NODATAQUALITY - Regla #3 — No Cuestionar la Calidad de Datos del Usuario
Sin sugerencias, sin recomendaciones de fuentes alternativas.
### 11.4 KERNEL:CVR-NODELEGATE - Regla #4 — No Delegar Escritura al Usuario
Excepciones: export PDF, upload a Google Drive.
### 11.5 KERNEL:CVR-NOSYNC - Regla #5 — No Interpretar en SYNC
Datos puros, sin análisis de tendencias.
Template Universal de Rechazo:
```plain text
OPERACIÓN RECHAZADA — Violación Regla de Oro #[N]
Tu solicitud: [descripción exacta]
Razón: [qué regla viola y por qué existe la restricción]
Alternativa operativa: [pasos concretos dentro del sistema]
¿Proceder? Escribe SÍ o CANCELAR
```
### 11.6 KERNEL:CVR-GATE-INVARIANCE - Regla #6 — Invarianza de la Decisión de Gate
Prohibido que el AI Component re-evalúe fit, estime scores o aplique exclusiones sobre vacantes que ya poseen una Gate_Decision calculada por Python o aprobada por el operador.
## 12 KERNEL:NAMING - Naming y Contrato de IDs
Formato canónico PREFIX:KEY, prefix ownership, SSOT en resolver_registry_v2.json, matriz tipográfica congelada, regla de bloque único, convención de nombres de outputs.
### 12.1 KERNEL:NAM-ID-CONTRACT - Canonical Document ID Contract
Invariantes:
- Formato único: [PREFIX]:[KEY] (ej. MANUAL:SETUP).
- Prefix Ownership: cada prefijo mapea a una única página canónica en Notion.
- SSOT: resolver_registry_v2.json es la autoridad única para resolver prefijos a UUIDs.
- Resolución determinista: Entity Index permite lookup O(1); el Resolver recupera la página puntual vía Notion.
Prefijos autorizados:
| Prefijo | Documento Destino |  |
| --- | --- | --- |
| KERNEL | V \ | KERNEL |
| MANUAL | V \ | MANUAL |
| CANON | V \ | CAREER CANON |
| TRACKER | V \ | TRACKER |
| SP | V \ | SYSTEM PROMPT |
| ALIASES | V \ | ALIASES |
| CHANGELOG | V \ | CHANGE LOG |
| BRIEF | V \ | NAVIGATION BRIEF |
| VANTAGE | V \ | VANTAGE CENTRAL HUB |
Matriz Tipográfica Congelada (Jerarquía de Encabezados): Documento (raíz) = #; Capítulo/Sección canónica = ##; Subsección (NN.N) = ###; Figma Tag (solo derivados, inmutable) = ######. Ningún nodo NN.N comparte nivel con su capítulo padre.
Regla de Bloque Único: todo heading de subsección declara su ID canónico [PREFIX]:[KEY] en la misma línea de heading que su título — nunca en línea separada ni como texto plano bajo el heading.
Reglas de Migración: toda referencia que use UUIDs hardcodeados o anclas planas debe migrar a este esquema. DT-015 CERRADO: normalización documental (26 ocurrencias) vía trigger NORM, 100% canónico.
### 12.2 KERNEL:NAM-ID-MIGRATION - Normalización Documental de IDs Legacy
Esquema: [PREFIX]:[KEY]. Alcance: todos los documentos fundacionales. Excepciones: IDs de Notion (UUIDs) en metadatos o URLs. Gobernanza: cambios requieren APROBAR_WRITE + entrada en Changelog. Estado actual: normalización completada, DT-015 CERRADO.
### 12.3 KERNEL:NAM-DOC-CONTRACT - Contrato de Prefijos Documentales del Lazy Loader
Fuente de verdad de qué prefijos PREFIX:CLAVE están autorizados para resolución vía lazy_loader.py en el flujo documental (distinto del flujo de entidades del Runtime, 04.1). resolver_registry_v2.json → document_registry es el SSOT operativo.
Prefijos autorizados: los 11 listados en 12.1 — ALIASES, ARCHIVEROS, BRIEF, CANON, CHANGELOG, CHANGELOG_ARCHIVO, KERNEL, MANUAL, SP, TRACKER, VANTAGE.
lazy_loader._get_authorized_prefixes() carga este conjunto desde el Registry en tiempo de ejecución; fallback estático: {KERNEL, MANUAL, CANON, TRACKER}.
Fallo: un prefijo no listado aquí ni en el Registry cae a modo legacy con warning.
### 12.4 KERNEL:NAM-OUTPUT - Convención de Nombres de Outputs
Formato del stem: {Año}_{Nombre}_{Apellido}_{Marca_normalizada}_{Vacante_normalizada}.
Reglas de normalización: espacios → guión bajo; sin acentos ni caracteres especiales; sin símbolos de puntuación; guión bajo como único separador (no CamelCase).
Fijación del stem: se fija al generar el primer entregable y se reutiliza sin variación.
Ejemplo: "Gucci — VM Coordinator, LATAM (2026)" → 2026_Mauricio_Meyran_Gucci_VM_Coordinator_LATAM.
Aplica a: CV-B (.md), export QA (.pdf), archivo Figma (.fig) y cualquier output futuro de una vacante específica.
No aplica a: DRY RUN archivado, artefactos de sistema (logs, backups, entity_index).
Relación con CANON:OUTPUT-CONTRACT: contratos distintos y complementarios.
### 12.5 KERNEL:NAM-ID-GRAMMAR - Gramática de IDs Canónicos v10.3
- Capítulo = KERNEL:<DOMINIO> — sustantivo del capítulo, sin números.
- Subsección = KERNEL:<DOM>-<SLUG> — slug semántico en MAYÚSCULAS_CON_GUIONES. Prohibido relleno numérico (-001): el orden lo lleva la numeración NN.M del heading, nunca el ID.
- Vocabulario controlado: dominios (<DOM>, 3–4 letras) se registran en resolver_registry_v2.json; slug nuevo requiere alta en registry.
- Un slug = un contrato. El slug describe QUÉ gobierna el bloque, no de dónde provino.
- Puente de alias: un KEY legacy se declara en V | ALIASES + resolver por un ciclo de release; después se deprecia.
---
# IV. GOBERNANZA DOCUMENTAL
## 13 KERNEL:LINK - Cross-Reference Hyperlinks
El sistema convierte las menciones de IDs canónicos en hipervínculos reales hacia sus bloques de definición. El heading de definición no se autoenlaza; las menciones posteriores sí.
### 13.1 KERNEL:LINK-SYSTEM - Sistema de Cross-Reference Hyperlinks
Propósito: convertir cada mención de un ID canónico (PREFIX:KEY) en los 7 documentos indexados por el Census en hipervínculo real al bloque de definición.
Piezas:
- generate_census.py: resuelve cada ID a su anchor de bloque real vía API, detecta huérfanos.
- apply_hyperlinks_notion.py: PATCH puntual directo sobre bloques Notion (notion.blocks.update), preserva block-ID, no pasa por destroy/rebuild. Vía activa de escritura.
- apply_hyperlinks.py: DEPRECATED — operaba sobre .md locales con MAPPING estático hardcodeado.
- vantage_id_rules.py: módulo destinado a ser fuente única de reglas DEF/REF/heading.
Estado de adopción (2026-08-01): apply_hyperlinks_notion.py reemplaza a apply_hyperlinks.py. Fix de is_definition_block(): exclusión de table_row corrige falso positivo (239 vs 143 bloques parcheados, 0 regresiones).
### 13.2 KERNEL:LINK-RULE - Cross-Reference Hyperlinks — Regla de Aplicación
El sistema convierte las menciones de IDs canónicos en hipervínculos reales hacia sus bloques de definición, preservando el block-ID mediante parches puntuales y evitando operaciones destructivas de reconstrucción.
## 14 KERNEL:OPS - Operaciones Documentales y de Sesión
Bootstrap, Health Check, vversions, Census, Session Ledger, Impact Assessment, External Config, Notebook Gemini, Sandbox, convención de anuncios, gates transversales y Handoff Serial.
### 14.1 KERNEL:OPS-BOOT - L0-Bootstrap — Dynamic Governance Layer
Tipo: capa de sincronización de sesión (fetch-on-start).
Propósito: elimina el drift de versiones entre la UI estática del agente y el repositorio dinámico de Notion.
Protocolo: ante el primer mensaje del operador, el AI Component suspende procesamiento de datos y ejecuta fetch de SP:BOOTLOADER y del ID CENSUS. El resultado sobreescribe cualquier instrucción estática previa.
Fallo: si el Bootstrap falla, reportar "MODO DEGRADADO" y no proceder con triggers operativos.
Convención de estado: BOOTLOADING... → BOOTLOADED.
Distinción de alcance — Bootstrap vs. Session Ledger: el Bootstrap corre en cada mensaje inicial de cualquier conversación. El Session Ledger (14.5) es opt-in: solo se escribe cuando el operador invoca vantage-session-open.
### 14.2 KERNEL:OPS-HEALTH - Health Check
Naturaleza: lectura estricta por defecto. Única excepción: auto-sync condicional del Entity Index.
Checks ejecutados: version → env → git → vgit → notion → docs_sync → vdoc → index_age → pending_tickets.
Entity Index Auto-Sync: umbral 24h sobre graph_v2.json/entity_index_v2.json. Acción: subprocess a python3 vantage.py sync, timeout 120s. Clasificación: housekeeping de rutina, no remediación de fallo.
Reporte de Tickets: agrupación por prioridad sobre Bug Tracker y Task Tracker. Detalle explícito solo para CRÍTICO y ALTO.
Integridad del Runtime: vantage.py status expone el estado del snapshot y el resultado más reciente de sync. Los checks advisory informan el estado, pero no se convierten por sí mismos en gates del pipeline.
### 14.3 KERNEL:OPS-VERSIONS - Verificación de Versión
Función: ruta de bajo costo para verificar y sincronizar la Versión de los documentos fundacionales sin pagar el costo de un fetch completo por documento.
Modos: --sync (único modo de escritura real); --bootstrap (dump read-only); --scripts/--skills (gap report read-only); --length (sanity check estructural, read-only, exit code 1 si ATENCIÓN REQUERIDA); --update-baseline (requiere --length + confirmación explícita).
Verificación de Integridad Estructural (Length Check):
- Alcance: 11 documentos versionados (CHANGELOG, KERNEL, MANUAL, CANON, SP, ALIASES, CENSUS, BRIEF, VANTAGE, CHANGELOG_ARCHIVO y ARCHIVEROS).
- Métrica: conteo de bloques con texto extraíble no vacío.
- Umbrales: ≥5.0% de caída (LENGTH_TRUNCATION_THRESHOLD_PCT) o ≥10 líneas de caída (LENGTH_TRUNCATION_THRESHOLD_ABS) vs. baseline.
- Salida: veredicto por documento + veredicto final + exit code 1 si ATENCIÓN REQUERIDA.
- Baseline: length_baseline.json almacena el conteo por documento y captured_at; si no existe, la primera ejecución de --length lo genera automáticamente.
- --update-baseline: modo write explícito; requiere --length; sobrescribe el baseline solo si el veredicto final es PASS o el operador confirma explícitamente que las diferencias son intencionales.
### 14.4 KERNEL:OPS-CENSUS - ID Census
El V-ID-CENSUS es el noveno documento fundacional, derivado — su fuente de verdad son los IDs reales de los otros ocho documentos.
Reglas:
1. [CENSUS-SYNC-R1]: ningún ticket que implique cambio de estado de un ID se marca Done sin Census regenerado; si no puede ejecutarse, el ticket queda Blocked-Census.
1. generate_census.py detecta IDs huérfanos y los reporta antes de cerrar el ticket asociado.
1. El Census se regenera antes de que el Changelog registre el batch.
1. Ninguna sesión con cambios cierra sin DRY RUN automático de lo modificado.
1. health_check.py reporta antigüedad del Census (umbral 7 días) como advertencia informativa, no bloqueante.
1. generate_census.py resuelve huérfanos vía --auto-fix-orphans y --sync-to-notion [page_id].
### 14.5 KERNEL:OPS-LEDGER - Session Ledger
Naturaleza: excepción de escritura de housekeeping — no requiere APROBAR_WRITE.
Estructura: Database Notion con: session_id, status (OPEN/CLOSED), opened_at, pending_summary, y campos de trazabilidad de Handoff: Opening Handoff Serial, Opening Agent Family/Instance, Last Handoff Serial, Parent Session ID, Trace Status (select: LINKED/ORPHAN/REVIEW_NEEDED).
Escritura autorizada: solo SKILL-OPEN paso 0 (→ OPEN) y SKILL-CLOSE paso 6 (→ CLOSED + pending_summary).
### 14.6 KERNEL:OPS-IMPACT - Impact Assessment Contract
Toda modificación que afecte un documento con dependencias registradas genera una Evaluación de Impacto antes del cierre de la operación. La evaluación responde: qué documentos pueden verse afectados; qué contratos deben verificarse; si es necesaria actualización documental; si debe regenerarse algún artefacto de Runtime; si debe ejecutarse validación adicional; si se requiere sincronización mediante vcensus, vhyperlinks o vversions.
### 14.7 KERNEL:OPS-EXTCONFIG - External Configuration Contract
Los scripts operativos externalizan la configuración mutable cuando esta pueda cambiar sin alterar la lógica del pipeline. Para CV-A, Layer_1/config/hard_blocks.json es la fuente externa de Hard Blocks; si el archivo no existe, el código utiliza fallback interno.
### 14.8 KERNEL:OPS-NOTEBOOK - Notebook Gemini
Tipo: capa de consulta ReadOnly externa, complementaria al fetch nativo de Claude.
Contrato de Cero Inferencia Silenciosa: toda afirmación técnica requiere ancla exacta (PREFIX:KEY). Ante instrucción no documentada, declara "Fuera de Alcance" o "No encontrado" — nunca infiere. No calcula Score, no redacta CVs, no crea reglas de negocio.
Uso preferente: consulta puntual de triaje/verificación documental (detección de drifts entre documentos) cuando no se requiere fetch estructural ni escritura en Notion — evita consumir fetch/tokens de Claude en preguntas de bajo riesgo.
### 14.9 KERNEL:OPS-SANDBOX - Sandbox
Patrón operativo compartido por skills de documentación transversal, vantage-skill-updater y vantage-housekeeping-archive: todo proceso interno corre en sandbox sin renderizar al operador. Output visible limitado a 3 bloques máximo: apertura, resultado, cierre.
Regla de aplicación: toda skill nueva que adopte este patrón declara explícitamente qué pasos corren en sandbox y cuáles son output visible; no se asume por default.
No aplica a: skills cuyo output es inherentemente iterativo o requiere confirmación por ítem (ej. vantage-cv-b, procesamiento single-item) — su economía de tokens se gestiona por otro mecanismo (Restricción de Lote, KERNEL:CVP-CVB).
### 14.10 KERNEL:OPS-ANNOUNCE - Convención de Anuncio de Skills
Todo skill de VANTAGE declara inicio y cierre de su protocolo con un verbo propio en gerundio/participio, nunca con mensaje genérico compartido ni con el lenguaje de cierre del Bootstrap universal.
Implementación activa: vantage-session-open (SESSION-OPENING…/SESSION-OPENED) · vantage-session-close (CLOSING SESSION…/SESSION CLOSED) · vantage-documentacion-transversal-propuesta (BEGINNING DOCUMENTATION MAPPING…/DOCUMENTATION MAPPING COMPLETE) · vantage-documentacion-transversal-implementacion (RESUMING DOCUMENTATION…/DOCUMENTATION FINISHED) · vantage-sync-assets (SYNCING ASSETS…/ASSETS SYNCED) · vantage-skill-updater (BEGINNING SKILL EVALUATION…/SKILL EVALUATION COMPLETE) · prompt-master (PROMPTING…/PROMPT FINISHED) · vantage-create-bug-task (LOGGING TICKET…/TICKET LOGGED) · vantage-present-handoff (HANDING OFF…/HANDOFF DELIVERED) · vantage-tidy-changelog (TIDYING CHANGELOG…/CHANGELOG TIDIED) · vantage-tidy-bug-task-tracker (TIDYING TRACKER…/TRACKER TIDIED) · vantage-tidy-opportunities-tracker (TIDYING OPPORTUNITIES…/OPPORTUNITIES TIDIED) · vantage-housekeeping-tracker (HOUSEKEEPING TRACKERS…/TRACKERS HOUSEKEPT) · vantage-housekeeping-archive (ARCHIVING HOUSEKEEPING…/ARCHIVE HOUSEKEPT).
Nota — Contrato de Handoff: vantage-present-handoff, vantage-session-open y vantage-session-close incorporan cabecera de identidad de agente y serial de handoff (ver SP:BOOTLOADER-002); la convención de anuncio no cambia, solo el cuerpo del output.
### 14.11 KERNEL:OPS-DOCPROTOCOL - Documentación Transversal
Protocolo (seis fases): Mapeo → DRY RUN → Inyección → Write-Back Verification → Changelog + versión → Binary Gate de salida.
| Skill | Propósito | Gate |
| --- | --- | --- |
| vantage-create-bug-task | Crear tickets en Bug Tracker | Obligatorio |
| vantage-present-handoff | Resumen COMPLETADO/PENDIENTE | No aplica |
| vantage-tidy-changelog | Append + edición de Change Log | Obligatorio |
| vantage-tidy-bug-task-tracker | Limpieza de campos/normalización | Obligatorio |
| vantage-tidy-opportunities-tracker | Duplicados/normalización Class A | Obligatorio |
| vantage-documentacion-transversal-propuesta | Mapeo de nodos, sin escritura | Obligatorio |
| vantage-documentacion-transversal-implementacion | DRY RUN + inyección + write-back | Obligatorio |
### 14.12 KERNEL:OPS-SERIAL - Contrato de Serial Global de Handoff
Autoridad de serial: GLOBAL_VANTAGE_COUNTER. Ruta canónica: vserial vía Terminal, que ejecuta allocate_vantage_serial.py next. Es la única vía canónica para obtener un serial nuevo.
Formato: HO-######, monotónico — no se reinicia por sesión, agente, cuenta ni skill; no se reutiliza tras rechazo o corrección.
Corrección: un handoff emitido no se edita silenciosamente — una corrección genera nuevo serial referenciando el anterior vía correction_of.
Identidad del emisor: ver SP:BOOTLOADER-002 para el registro de agentes autorizados a emitir handoffs serializados. Agentes sin Project Instructions (Arena, Cursor, Devin) no emiten serial propio.
Prioridad de resolución:
1. Serial declarado directamente por el operador en el mismo turno — autoridad máxima; se adopta sin verificación adicional.
1. Si no se declaró, obtenerse vía vserial. Si no está disponible, declarar HANDOFF_SERIAL_UNAVAILABLE y detener la emisión — nunca inventar, interpolar ni asumir continuidad secuencial.
Rutas no canónicas y deprecadas: allocator MCP, bridge HTTP, endpoints de asignación, acceso directo a SQLite.
## 15 KERNEL:EVOLUTION - Evolución del Sistema
Toda decisión estructural mayor se registra en el Charter, no en el cuerpo del Kernel. Drift detectado → ticket + verificación 1:1, nunca corrección en silencio.
### 15.1 KERNEL:EVO-POLICY - Política de Evolución
Cambios válidos: cambio estructural de mercado; cambio en targets; ineficiencia probada con datos; violación de boundary entre capas.
Cambios inválidos: "Score se siente muy estricto"; Ready-to-Apply vacío; un dead link apareció; frustración temporal.
Comportamiento ante solicitud de cambio inválido: el AI identifica la condición, informa la razón, redirige al workflow activo. No ejecuta, no negocia.
Estabilidad de Arquitectura Central: los boundaries de capas no colapsan; los contratos de campo Class A/B no se mezclan; la arquitectura de cuatro capas, el URL_GATE como primer filtro y la división AI/Python son invariantes del sistema.
Linaje Histórico — Preservado, No Operacional: GPT Atlas, Grok discovery, SEARCH-EXEC/SEARCH-SIGNAL, fórmulas de scoring pre-v5.0 — contexto histórico, no código activo.
### 15.2 KERNEL:EVO-CHANGELOG - Change Log
Cuando una Evaluación de Impacto (14.6) determine afectación sobre otro documento o artefacto, la afectación se registra en el Change Log.
La entrada incluye obligatoriamente: documento modificado; documentos potencialmente afectados; tipo de impacto (Normativo, Operativo, Runtime o Navegación); acción correctiva ejecutada; estado final de la validación.
Timestamp obligatorio: toda entrada nueva declara fecha y hora local (CDMX) en el título, formato {Mes} {DD}, {AA} {HH.MM}. Si el operador no la incluye, el AI la solicita antes de escribir; no infiere ni aproxima.
---
# V. EXCEPCIONES
## 16 KERNEL:EXCEPTIONS - Excepciones
Registro cerrado de desviaciones documentadas y acotadas al contrato normativo general. Ninguna excepción no listada aquí es válida por analogía.
| Excepción | Condición / Alcance | Referencia |
| --- | --- | --- |
| Bypass de URL | Source_Type ∈ {Inbound, Referencia, Networking} → CREATE automático | 06.1 |
| Housekeeping sin APROBAR_WRITE | Solo Session Ledger y excepciones explícitas de skills de tidy | 14.5 |
| Graph/Backlinks = 0 | Por diseño (SUSPENDED) — no es fallo | 04.1 |
| ARCHIVEROS sin baseline de length | Por decisión del operador; exclusión de --length pendiente de ticket de código | 14.3 |
| Resoluciones B-xx | Divergencias conocidas y su estado actual viven aquí, no en el cuerpo normativo | 05.1 |
