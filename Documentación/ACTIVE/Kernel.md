# V | KERNEL

> 
## KERNEL:AUDIENCE-SCOPE
## DECLARACIÓN DE AUDIENCIA Y ALCANCE
- Audiencia: Sistemas Agente de IA.
- Alcance: Este documento es el KERNEL_RUNTIME, que contiene únicamente los contratos operativos activos para la IA. Para el documento de referencia completo, solicitar acceso al KERNEL 8.0.
---
## TABLE OF CONTENT
| # | Sección | Tipo | Propósito |
| --- | --- | --- | --- |
| 1 | PURPOSE | CONTEXTO | Propósito del sistema |
| 2 | ARCHITECTURE | ARQUITECTURA | Diseño de cuatro capas |
| 3 | DASHBOARD-CHECKLIST-ARCH | ARQUITECTURA | Arquitectura Dashboard/Checklist — capas backend, standalone y visual compartida |
| 4 | SCHEMA | ESQUEMA | Class A vs Class B |
| 5 | TRACKER-SCHEMA | ESQUEMA | Alcance y niveles de prioridad — Bug/Tasks Tracker |
| 6 | HEALTH-CHECK | OPERACIÓN | Contrato de health_check.py — checks y auto-sync de índice |
| 7 | OWNERSHIP | ARQUITECTURA | Responsabilidades AI vs Python |
| 8 | TRIGGERS | OPERACIÓN | Contratos detallados |
| 9 | GATE-DECISION | REGLAS | Lógica de gates |
| 10 | NAMING-CONVENTION | REGLAS | Convención de nombres de outputs |
| 11 | CV-GOLDEN-RULES | REGLAS | Reglas de oro CV |
| 12 | CV-PIPELINE | OPERACIÓN | Flujo CV-A → CV-B |
| 13 | CANON-UPDATE | OPERACIÓN | Actualización del Canon |
| 14 | FAIL-PHILOSOPHY | FILOSOFÍA | Filosofía de fallo |
| 15 | SCOPE | OPERACIÓN | Scope y economía de contexto (Terminal vs MCP) |
| 16 | DATA-FLOW | ARQUITECTURA | Flujo de datos y escritura |
| 17 | ROUTING | OPERACIÓN | Rutas de carga MCP / lazy_loader |
| 18 | EVOLUTION | FILOSOFÍA | Evolución del sistema, deuda técnica, criterios de cambio |
| 19 | NORM | OPERACIÓN | Normalización Documental (Legacy IDs) |
| 20 | CENSUS-SYNC | OPERACIÓN | Sincronización obligatoria del ID Census |
| 21 | DOC-CONTRACT | REGLAS | Contrato de IDs de Documento |
## §1 — KERNEL:PURPOSE
Propósito del Sistema
VANTAGE resuelve un problema de ingeniería de atención: en una búsqueda laboral sin estructura, las oportunidades de alta señal desaparecen antes de ser procesadas, mientras el tiempo se consume en vacantes de baja calidad.
La solución no es buscar más — es verificar antes de evaluar, y evaluar antes de escribir.
### Invariantes del Sistema
1. Una vacante no entra al pipeline sin URL válida — excepción: Bypass activo. (El Bypass es la ruta que se activa cuando la vacante llega por contacto humano directo — Inbound, Referencia o Networking — en lugar de por discovery automatizado; su lógica completa se define más adelante en KERNEL:GATE-DECISION-001.)
1. Score no lo calcula el sistema de lenguaje — lo calcula Python con lógica determinista.
1. Gate decision no se sobreescribe manualmente. RT-1 permite corregir inputs Class A para que Python recalcule — no sobreescribe el gate. (RT-1 es el flujo de recuperación operado desde el Dashboard: el operador corrige un campo de entrada incorrecto — URL, JD, Source — y deja que Python vuelva a evaluar. RT-1 nunca escribe el resultado del gate directamente; solo corrige la causa para que el sistema llegue a un resultado distinto por sí mismo. El detalle operativo completo de este flujo de recuperación vive en KERNEL:GATE-DECISION-005.)
1. Strategy es responsabilidad humana; processing es responsabilidad del sistema.
### Qué Significa Esto para el Sistema AI
El componente AI es el procesador textual del pipeline: deduplica, normaliza, genera DRY RUN (el preview de escritura que se presenta al operador antes de cualquier cambio en Notion), escribe Class A en Notion (los campos que describen la vacante tal como fue capturada — Rol, Marca, URL, Status, etc.; el contrato completo de qué es Class A y qué es su contraparte Class B vive en KERNEL:SCHEMA, más adelante en este documento), y produce CVs.
Evaluación de calidad estratégica de inputs y cálculo de campos Class B no son operaciones de este componente. Esa división de trabajo — qué corresponde al componente AI y qué corresponde exclusivamente a Python — se define con precisión en KERNEL:OWNERSHIP. Las restricciones específicas que impiden al AI Component evaluar fit, estimar scores o interpretar resultados fuera de su contrato están codificadas como reglas de arquitectura, no como preferencias, en KERNEL:CV-GOLDEN-RULES.
Si una tarea no está en la tabla de triggers — el catálogo de contratos de input/proceso/output que define qué puede ejecutar el componente AI y bajo qué condiciones, desarrollado en KERNEL:TRIGGERS — no se ejecuta.
---
## §2 — KERNEL:FAIL-PHILOSOPHY
Filosofía de Fallo
Los fallos del sistema son señales de que el pipeline funciona correctamente. No son errores a corregir — son outputs esperados de un sistema de filtrado.
Un gate que nunca bloquea no está filtrando. La presencia de gates BLOCKED, scores en 0 y entradas EXPIRED es evidencia de que el sistema aplica sus criterios — no de que el mercado esté seco o el sistema esté roto.
Esta filosofía se presenta aquí, temprano en el documento, porque es referenciada más adelante por al menos tres secciones distintas — KERNEL:HEALTH-CHECK (para justificar por qué el auto-sync del índice no cuenta como “remediación de un fallo”), KERNEL:GATE-DECISION (para explicar por qué un gate bloqueado no es un error a revertir) y KERNEL:EVOLUTION (para distinguir cambios válidos de cambios reactivos a frustración temporal). Entenderla antes de llegar a esas secciones evita que el lector interprete sus referencias como saltos hacia un concepto no explicado.
### Qué Hace el Sistema Cuando Falla
No intenta reparar outputs del sistema. No sugiere workarounds para entradas bloqueadas. No escala urgencia. Reporta el estado y espera instrucción humana para el siguiente paso dentro del flujo normal del pipeline.
### Excepción Documentada — Gate = BLOCKED
Gate = BLOCKED recuperable vía RT-1: si el bloqueo es por campos Class A corregibles, RT-1 es el mecanismo de recuperación. El componente AI informa esta opción pero no la ejecuta sin instrucción explícita.
---
## §3 — KERNEL:ARCHITECTURE
Arquitectura de Cuatro Capas
Con el propósito del sistema y su filosofía de fallo ya establecidos como marco de referencia, esta sección describe cómo esas intenciones se materializan en infraestructura concreta. El pipeline opera a través de cuatro capas no intercambiables, soportadas por un núcleo de observabilidad persistente.
---
### KERNEL:ARCHITECTURE-L0
L0 — VANTAGE Runtime
Tipo: Capa de Observabilidad y Abstracción de Datos (ReadOnly)
Propósito: Provee la verdad técnica sobre Notion. Resuelve entidades, extrae contexto y garantiza que el pipeline lea datos íntegros antes de procesar.
Proceso determinista que genera los tres artefactos de lectura del sistema:
- entity_index_v2.json — índice de entidades con namespaces canónicos
- graph_v2.json — grafo de relaciones entre entidades
- backlinks_v2.json — índice inverso de referencias
El Build consume resolver_registry_v2.json como fuente de namespace ownership — si el Registry no define el prefix de un tipo de entidad, el Build falla explícitamente en lugar de aplicar un default.
graph_layer.py es el componente responsable de construir graph_v2.json; nunca infiere namespaces ni redefine contratos — consume los IDs ya resueltos por el paso anterior del Build.
```plain text
Notion (Source) → Runtime (Index + Resolver) → API Response → Pipeline (L1/L2/L3/CV)
```
verify_versions.py (alias vversions, ver KERNEL:VERSION-CHECK-TOOL) y generate_census.py (alias vcensus) son observabilidad ReadOnly sobre Notion — mismo tipo de operación que Runtime Build (Entity Index, Grafo, Backlinks), aplicada a un dato distinto: versión documental y salud del Census en vez de entidades del Tracker. Ambos pertenecen a L0 en la misma capa, no a una capa separada ni a infraestructura de sesión aparte.
Diagrama ampliado:
```plain text
Notion (Source) → Version Check (7 docs) / Census (ID audit) → Reporte a operador
```
---
### KERNEL:ARCHITECTURE-L0-BOOTSTRAP
L0-Bootstrap — Dynamic Governance Layer
Tipo: Capa de Sincronización de Sesión (Fetch-on-Start)
Propósito: Elimina el drift de versiones entre la UI estática del agente y el repositorio dinámico de Notion.
Ante el primer mensaje del operador, el componente de IA debe suspender el procesamiento de datos y ejecutar un fetch de SP:BOOTSTRAP-001 (System Prompt) y del ID CENSUS. El resultado de este fetch sobreescribe cualquier instrucción estática previa. Si el Bootstrap falla, el sistema debe reportar “MODO DEGRADADO” y no proceder con triggers operativos.
El Bootstrap declara su inicio con BOOTLOADING… y su cierre con BOOTLOADED: DOCUMENTOS CARGADOS — nunca con lenguaje que sugiera cierre de sesión formal. Esta misma convención rige cualquier skill que cargue contenido ([SKILL] LOADING… → [SKILL] LOADED), para que ningún mensaje de carga de contexto se confunda con el cierre de un protocolo distinto.
El Bootstrap corre en cada mensaje inicial de cualquier conversación del proyecto VANTAGE — es carga de contexto universal, no un registro de sesión formal. El Session Ledger (KERNEL:SESSION-LEDGER, §L0-013) es opt-in: solo se escribe cuando el operador invoca explícitamente el skill vantage-session-open. No toda conversación del proyecto necesita una fila en el Ledger; el Bootstrap por sí solo nunca la crea.
```plain text
Sesión Iniciada
→ BOOTLOADING...
→ AI Fetch (Bootstrap IDs)
→ Sincronización de Verdad Operativa
→ BOOTLOADED: DOCUMENTOS CARGADOS
→ Procesamiento Petición
(Ledger: solo si el operador invoca vantage-session-open)
```
---
### KERNEL:SKILL-ANNOUNCE-CONVENTION
Convención de Anuncio de Skills
Todo skill de VANTAGE (presente o futuro) declara el inicio y cierre de su protocolo con un verbo propio en gerundio/participio (X-ING… al abrir, X-ED/equivalente al cerrar), nunca con un mensaje genérico compartido entre skills ni con el lenguaje de cierre del Bootstrap universal (BOOTLOADED). Esto evita la confusión de alcance que originó el bug de Ledger huérfano (ver Changelog v9.5.0–v9.5.1).
Si esta convención cambia, el mismo Changelog debe listar el Kernel y cada .skill afectado dentro del mismo alcance — un cambio que solo toque uno de los dos queda incompleto y debe reportarse como discrepancia (SP:CONSISTENCY).
- vantage-session-open — SESSION-OPENING…/SESSION-OPENED
- vantage-session-close — CLOSING SESSION…/SESSION CLOSED
- vantage-documentacion-transversal — BEGINNING DOCUMENTATION…/DOCUMENTATION FINISHED
- prompt-master — PROMPTING…/PROMPT FINISHED
- vantage-create-bug-task — LOGGING TICKET…/TICKET LOGGED
- vantage-present-handoff — HANDING OFF…/HANDOFF DELIVERED
- vantage-tidy-changelog — TIDYING CHANGELOG…/CHANGELOG TIDIED
- vantage-tidy-bug-task-tracker — TIDYING TRACKER…/TRACKER TIDIED
- vantage-tidy-opportunities-tracker — TIDYING OPPORTUNITIES…/OPPORTUNITIES TIDIED
---
### KERNEL:ARCHITECTURE-L1
L1 — Active Recon
Trigger: humano (ciclo semanal — lunes)
```plain text
Human signal
→ Career Sites · LinkedIn · Aggregators (paralelo)
→ JSON estructurado
→ FEED
→ feed_processor.py
→ Notion (Class A)
→ vantage-pipeline
```
---
### KERNEL:ARCHITECTURE-L2
L2 — Strategic Search
Trigger: humano (ciclo semanal — lunes)
```plain text
Human signal
→ Gemini · You.com · Grok (extracción paralela)
→ Perplexity (Consolidation & Dedup post-extracción)
→ Plain Array consolidado
→ FEED
→ feed_processor.py
→ Notion (Class A)
→ vantage-pipeline
```
---
### KERNEL:ARCHITECTURE-L3
L3 — Passive Intake
Trigger: automático (continuo)
```plain text
Gmail (.Jobs label)
→ layer_3_mail.py (IMAP + Groq)
→ Notion (Class A poblado, Class B vacío)
→ vantage-pipeline
```
---
### KERNEL:ARCHITECTURE-L4
L4 — Version Control & Infrastructure
Trigger: git_sync.py + git_sync_wrapper.sh + launchd
No es capa de búsqueda — es infraestructura documental del sistema.
- Auto-commit + push a origin/main cuando hay cambios en el repo.
- Alias: vgit · Corre en background a las 09:00 · 15:00 · 21:00.
- Repo: github.com/mauriciomeyran/jhs-pipeline.
- Reutiliza .venv de Layer_1.
Sync bidireccional Notion → ACTIVE/ para los 6 documentos fundacionales editables por el operador (Kernel · System Prompt · Career Canon · Manual · Aliases · Change Log). El ID Census es el séptimo fundacional (ver KERNEL:CENSUS-SYNC) pero, al ser derivado y regenerado por generate_census.py en vez de editado directamente, no pasa por este flujo de sync bidireccional — distinción de mecanismo de actualización, no de estatus fundacional.
- Alias: vdoc
- Flags: dry | notion | local | auto
- Flujo vdoc notion: lee Notion (safe_list vía httpx, 3 reintentos) → escribe ACTIVE/{doc}.md → auto-commit GitHub al terminar
- Dependencias: httpx · notion-client 3.x · .venv de Layer_1 · git_sync.py
- Vive en: Layer_4/scripts/vsync_doc.py
Los 6 .md fundacionales editables viven en …/ACTIVE/ — agnóstico de versión. Al pasar a v8.7: copiar archivos a ACTIVE/, cero cambios de código.
Nombres canónicos: Kernel.md · System Prompt.md · Career Canon.md · Manual.md · Aliases.md · Change Log.md (con espacio, no guión bajo — coincide con BASE_DIR real en vsync_doc.py). Reemplaza los paths versionados anteriores (…/v8.5/Kernel v8.5.md).
Nota técnica: notion-client 3.x tiene un bug silencioso en blocks.children.list() que retorna None en lugar de lanzar excepción con campos null. vsync_doc.py lo mitiga con safe_list() — wrapper httpx directo con 3 reintentos.
L1 > L2 > L3. En conflicto cross-layer, prevalece la entrada de la capa de mayor jerarquía.
Perplexity aplica esta jerarquía en el paso de Consolidation & Dedup del lunes, antes de entregar el Plain Array a feed_processor.py. L3 no pasa por este paso — entra directamente a feed_processor.py desde mail_pipeline.py.
Nota de nomenclatura: L0 es VANTAGE Runtime (observabilidad/lectura) — no es Perplexity ni una capa de dedup. No aparece en la jerarquía de dedup.
Nota de implementación: L0 pre-aplica la jerarquía L1>L2 y entrega un array ya consolidado a feed_processor.py. feed_processor.py entonces aplica la jerarquía L3 contra ese resultado — no recalcula L1>L2 en ese momento. Las dos operaciones de dedup son secuenciales, no simultáneas.
Las capas tienen peso arquitectónico igual pero frecuencia de ejecución asimétrica. L1 y L2 operan en ciclos semanales controlados por atención humana. L3 corre continuamente sin intervención.
Esta asimetría de cadencia no implica jerarquía. Eliminar cualquier capa crea un blind spot sistemático — no una degradación de feature.
Las tres capas de búsqueda escriben a Notion. Notion es el único estado compartido. vantage-pipeline lee de Notion — no de los outputs de capa directamente.
Tipo: Capa de Materialización de CV (WriteOnly sobre lienzo Figma)
Propósito: Recibe el payload CV-B aprobado por el operador e inyecta el contenido directamente en los nodos de texto del lienzo Figma, resolviendo cada token semántico a su ID crudo de nodo vía registry_seed.json.
```plain text
CV-B (Markdown + figma_text_id)
→ ui.html (payload)
→ code.js (Registry V2)
→ figma.getNodeById(rawId)
→ node.characters = item.text
→ Lienzo Figma
```
Stack:
- manifest.json — Configuración del plugin (main: code.js, ui: ui.html, editorType: figma)
- code.js — Motor. Registry V2 / Resolver Layer V1. Resolución O(1): getNodeById(REGISTRY[key] || key). Resolver dual: KEY semántica (flujo JSON) → lookup en REGISTRY embebido; ID crudo directo (flujo Markdown figma_text_id) → uso sin lookup
- ui.html — Interfaz de intercambio de payloads. Acepta JSON por KEY semántica o Markdown con bloques ###### figma_text_id. Motor de extracción de boldRanges incluido
- registry_seed.json — SSOT del mapeo token → ID. (Su ubicación exacta y regla de invariancia frente al Golden Skeleton se cubren en el Manual, §18 — Golden Skeleton; el Kernel no reproduce esos detalles operativos.)
Invariantes:
1. Figma Sync no escribe en Notion ni en el Tracker.
1. Figma Sync no es capa de búsqueda ni de infraestructura de datos.
1. registry_seed.json no se edita manualmente sin regenerar desde el lienzo Figma.
1. El prefijo [VANTAGE] KEY_NAME en capas del canvas es para auditoría visual humana — no es el mecanismo de resolución del plugin.
---
## §4 — KERNEL:SCHEMA
Modelo de Datos y Ownership
### Aclaración terminológica antes de empezar
Antes de definir los campos, vale la pena fijar un término que se usa constantemente a partir de aquí: “el Tracker”, sin calificativo, se refiere siempre a la base de datos principal de Notion donde las capas L1, L2 y L3 (ya descritas en KERNEL:ARCHITECTURE) escriben cada vacante — el mismo destino que en los diagramas de arquitectura aparece como “Notion (Class A)”. Esta es una base de datos distinta del Bug Tracker y del Tasks Tracker, que se documentan más adelante en KERNEL:TRACKER-SCHEMA y sirven para gestionar tickets de trabajo interno del propio sistema, no vacantes. Si en algún punto de este documento aparece la palabra “Tracker” sin ese calificativo, se refiere siempre al Tracker de vacantes descrito aquí.
---
### KERNEL:SCHEMA-001
— Class A vs Class B
El schema define ownership. Cada campo pertenece a exactamente un componente. No hay campos compartidos ni campos de escritura dual.
AI Component escribe en triggers CV-A · CV-B · QA · FAST · CANON-UPDATE; feed_processor.py escribe en ciclo FEED L1/L3: Rol · Marca · Source_Type · URL · Status · Prioridad · Holding · JD · NAD · layer · hash.
(Glosario rápido de los triggers mencionados arriba, cada uno desarrollado en detalle más adelante en este Kernel: CV-A y CV-B son las dos sesiones del pipeline de generación de CV — análisis y producción respectivamente, ver KERNEL:CV-PIPELINE; QA es la validación de formato del CV exportado, ver KERNEL:TRIGGER-003; FAST es la vía de ingesta manual de una sola vacante, ver KERNEL:TRIGGER-008; CANON-UPDATE actualiza el Career Canon, ver KERNEL:CANON-UPDATE.)
Valores operativos del campo Status (asignación manual del operador, no calculados por Python): Target · Postulado · Rechazado · Expirada · Archivar · Repetida (duplicado detectado en revisión manual, distinto de descarte por otras razones).
Nota sobre JD: En el trigger CV-A, el AI Component cruza los keywords extraídos del JD contra el Career Canon activo antes de generar el HANDOFF. Discrepancias entre el JD y el Canon se reportan en fit_gaps — no se resuelven inventando experiencia ni contradiciendo el Canon.
Python escribe; ningún otro componente toca: Score · Gate_Decision · VM_Scope · Role_Class · Match · Next_Action · Fetch · Fuente.
---
### KERNEL:SCHEMA-002
— Restricción del Sistema
Si el JSON entrante incluye campos Class B con valores (“score”: 75, “gate_decision”: “CREATE”), se ignoran sin excepción. Python los calculará en el siguiente run de ~/vantage_pipeline.sh. Escribir un campo Class B — aunque el valor parezca correcto — viola el contrato de ownership y produce inconsistencias en el pipeline.
---
### KERNEL:SCHEMA-003
— Fuente como Campo Especial
Python sobrescribe Fuente en cada run. Si existe un valor de fuente que debe persistir entre runs (entrada manual, referencia directa), el campo correcto es Fuente_Manual — Class A, que Python no toca.
---
### KERNEL:SCHEMA-004
— Entity Format
El Runtime utiliza un formato de ID determinista para evitar colisiones y facilitar la resolución:
- PREFIX:H_ — Hash corto (16 hex chars)
- PREFIX:U_ — Formato alternativo
- Prefixes válidos: TRACKER, ARCHIVO, DRYRUN, BUG
resolver_registry_v2.json es el único punto de verdad para entity_prefix por tipo de entidad. entity_prefix se carga en runtime — nunca hardcodeado en ningún componente. graph_layer.py consume namespaces desde el Registry; nunca los infiere ni los redeclara.
Múltiples page_id pueden resolver al mismo entity_id — esto no es una colisión, es dedup histórico válido. Self-loops en graph_v2.json son síntoma de colisión de namespace, no comportamiento esperado del grafo.
---
### KERNEL:SCHEMA-005
— Contrato de Resolución: 4 Pasos
Para que una entidad se considere resuelta con éxito, el Runtime ejecuta:
1. Lookup: Localización en entity_index_v2.json
1. Registry Mapping: Mapeo de DB a data_source_id
1. Notion Query: Petición HTTP contra el endpoint de Notion
1. Validation: Verificación de integridad del resultado
---
### KERNEL:SCHEMA-006
— APROBAR_WRITE: Alcance
APROBAR_WRITE autoriza escritura de campos Class A únicamente. No aprueba, valida ni activa ningún campo Class B. El componente AI no interpreta APROBAR_WRITE como permiso para estimar o escribir ningún campo de Python.
Variantes aceptadas: APROBAR_WRITE · APROBAR · SÍ · sí · YEP · yep
⚠️ ELIMINADOS (RAI-03): Ok · Go · YES · yes — ocurren naturalmente en conversación y pueden producir escritura no intencionada.
Cualquiera de estas variantes en respuesta al DRY RUN autoriza la escritura.
---
### KERNEL:SCHEMA-007
— Acceptance Audit
El Acceptance Audit es la validación formal que certifica que un release cumple los contratos arquitectónicos antes de ser considerado completo. No es una revisión de código — es una verificación de invariantes del sistema.
Resultados posibles:
- PASS — todos los invariantes cumplidos, sin hallazgos pendientes
- PASS WITH ARCHITECTURAL FINDING — el sistema opera correctamente; existe una condición de calidad de datos o deuda técnica identificada y registrada, no bloqueante
- FAIL — uno o más invariantes violados; el release no procede
Un FINDING no bloquea el release si está clasificado, registrado en el Tracker (de vacantes o en Bug/Tasks Tracker según corresponda) y su impacto está acotado. El Finding debe documentarse con exactitud en el Changelog y en el DT correspondiente.
Los prompts de discovery usan terminología distinta a los campos del Tracker de vacantes. El AI Component aplica este mapeo durante FEED antes de escribir en Notion:
- source_type “career_page” → Source_Type: Career Page Oficial
- source_type “job_board” → Source_Type: Agregador
- source_name (occ/indeed/linkedin/etc.) → NO escribir. Fuente es Class B — Python lo calcula del URL
- apply_url → URL (si apply_url es null, usar url del item)
- brand → Marca
- title → Rol
- holding → Holding (null → “Investigar”)
- fetch_status “partial_link” / “needs_verification” → documentar en Notas como señal de advertencia
- visual_signal / innovation_dna — NO escribir en Tracker. Python detecta Visual Signal en JD. Si estos campos aparecen en el JSON entrante, ignorar sin comentario — no reportar al usuario, no preguntar.
Obligatorios (toda entrada): Rol · Marca · URL · Source_Type · Status · Prioridad · JD · JOB_ID · Holding
Obligatorios si disponibles en el momento: Contacto · Notas (contexto de origen) · Apply Date
Poblados post-proceso: Interview ✓ · Interview_Date · Files · URL Markdown
Toda entrada en proceso contiene los siguientes bloques en orden:
1. [PDF adjunto en campo Files] — cuando aplique
1. ENTREVISTA [N] — por cada ronda
- PREP {toggle}
- NOTAS {toggle}
- ACTION ITEMS {toggle} — Responsable: tarea — Due: fecha
- RIESGOS / OPEN QUESTIONS {toggle}
Entradas en Status=Target o en proceso sin entrevista confirmada: la página puede estar vacía o contener solo notas de contexto. El template de entrevista se agrega cuando se confirma primera ronda.
---
## §5 — KERNEL:DASHBOARD-CHECKLIST-ARCH
Arquitectura Dashboard/Checklist
Con las cuatro capas de búsqueda/infraestructura ya establecidas, esta sección describe una capa de presentación adicional que opera sobre los datos que esas capas producen: el Dashboard operativo y el Checklist semanal.
Dashboard/ contiene dos capas independientes que comparten presentación visual pero no estado:
1. Backend operativo real — Dashboard/scripts/dashboard_server.py + dashboard.db + dashboard_instances.db + dashboard_notion.py. Fuente de verdad del pipeline de vacantes (Gate_Decision, scoring, Notion sync). dashboard.html consume este backend vía fetch(‘http://127.0.0.1:8000{path}’).
1. Checklist operativo semanal — Dashboard/Checklist.html. Standalone, estado en localStorage[‘vchecklist_v1’]. Sin backend, sin Notion, sin relación funcional con (1). Intencional: el checklist es una herramienta de tracking personal del operador, no parte del pipeline de vacantes.
1. Capa visual compartida — Dashboard/vantage-tokens.css (tokens de color/superficie) + Dashboard/vantage-theme.js (toggle de tema con persistencia y sync cross-tab). Ambos archivos HTML la referencian. Es la única capa realmente compartida entre (1) y (2).
Regla:
cualquier cambio a un color de estado semántico o al comportamiento del toggle de tema se hace en vantage-tokens.css/vantage-theme.js, nunca en los
---
---
## §6 — KERNEL:TRACKER-SCHEMA
Bug Tracker y Tasks Tracker
Distinto del Tracker de vacantes descrito en KERNEL:SCHEMA — esta sección define el Bug Tracker y el Tasks Tracker, las dos bases de datos donde el sistema (y el operador) registran trabajo interno del propio VANTAGE: bugs, deuda técnica y tareas pendientes. Ninguno de los dos almacena vacantes ni usa los campos Class A/B recién definidos.
### KERNEL:TRACKER-SCHEMA-001
— Alcance
- Reactivo (algo roto) → Bug Tracker
- Proactivo (trabajo/decisión pendiente) → Tasks Tracker
| Tracker | DB ID | COL ID |
| --- | --- | --- |
| Bug Tracker | 36e938be-fc42-81f8-8c6f-000b6769ba03 | 36e938be-fc42-81bd-9e1f-dc360b3b45f5 |
| Tasks Tracker | d2a65ca1-6a35-465d-bcff-b0d82dddd549 | — |
---
### KERNEL:TRACKER-SCHEMA-002
— Niveles de Prioridad
Aplica a Bug Tracker y Tasks Tracker con la misma escala.
| Nivel | Criterio |
| --- | --- |
| CRÍTICO | El flujo punta a punta no puede completarse |
| ALTO | El flujo se completa forzando el sistema (workaround requerido) |
| MEDIO | Sin resolución en la semana, el flujo punta a punta se verá comprometido |
| BAJO | No bloquea operación — nice-to-have |
---
## §7 — KERNEL:DOC-CONTRACT
Canonical Document ID Contract (DOC:CLAVE)
Este contrato estandariza la referencia cruzada entre componentes del sistema y capas documentales, eliminando la dependencia de UUIDs en prompts y lógica de negocio. Se presenta aquí, antes de KERNEL:NORM y KERNEL:CENSUS-SYNC, porque ambas secciones dependen de este contrato como su fuente de verdad — en el orden original del documento, NORM citaba este contrato antes de que estuviera definido.
### Invariantes del Contrato
- Formato Único: [PREFIX]:[KEY] (ej. MANUAL:SETUP)
- Prefix Ownership: Cada prefijo mapea a una única página canónica en Notion
- SSOT: resolver_registry_v2.json es la autoridad única para resolver Prefijos a UUIDs
- Resolución Determinista: El Resolver (v1.py) garantiza resolución O(1) inyectando el ID crudo al componente solicitante
### Prefijos Autorizados (v8.9.0)
| Prefijo | Documento Destino | Mapeo Registry |
| --- | --- | --- |
| KERNEL | V | KERNEL | registry["KERNEL"] |
| MANUAL | V | MANUAL | registry["MANUAL"] |
| CANON | V | CAREER CANON | registry["CANON"] |
| TRACKER | V | TRACKER | registry["TRACKER"] |
| SP | V | SYSTEM PROMPT | registry["SP"] |
| ALIASES | V | ALIASES | registry["ALIASES"] |
| CHANGELOG | V | CHANGE LOG | registry["CHANGELOG"] |
| BRIEF | V | NAVIGATION BRIEF | registry["BRIEF"] |
| VANTAGE | V | VANTAGE CENTRAL HUB | registry["VANTAGE"] |
### Reglas de Migración
Toda referencia a páginas del sistema que actualmente use UUIDs hardcodeados o anclas planas debe migrar a este esquema. lazy_loader.py es el componente encargado de aplicar este contrato en tiempo de ejecución.
DT-015 — CERRADO: Normalización documental (26 ocurrencias) ejecutada vía trigger NORM [DOC:CLAVE]. 100% canónico.
---
## §8 — KERNEL:NORM
Normalización Documental de IDs Legacy
Con el contrato de IDs ya establecido en KERNEL:DOC-CONTRACT, esta sección documenta el estado de la migración hacia ese esquema.
### Contrato de Normalización de IDs (resumen operativo)
- Esquema: [PREFIX]:[KEY] (ej: KERNEL:TRIGGERS)
- Alcance: Todos los documentos fundacionales (MANUAL, CAREER CANON, KERNEL, SYSTEM PROMPT)
- Excepciones: IDs de Notion (UUIDs) en metadatos o URLs
- Gobernanza: Cambios requieren APROBAR_WRITE + entrada en Changelog. Ejecutable vía AI Component bajo autorización explícita del operador
Estado actual: Normalización documental de IDs legacy hacia el esquema [PREFIX]:[KEY] completada. Ver KERNEL:DOC-CONTRACT para el contrato completo y vigente. DT-015 (26 ocurrencias) — CERRADO.
---
## §9 — KERNEL:CENSUS-SYNC
Sincronización Obligatoria del ID Census
El V-ID-CENSUS es el noveno documento fundacional del sistema, sujeto a la misma Regla de Versión Única que los otros ocho (SP:SYNC-RULE). A diferencia de los demás, su contenido es derivado — su fuente de verdad son los IDs reales escritos en los otros ocho documentos fundacionales (Kernel, Manual, Career Canon, System Prompt, Aliases, Change Log, Navigation Brief, VANTAGE Central Hub), no al revés. El Census no reemplaza esos documentos ni los precede; los audita.
Ser derivado en contenido no lo exime de la regla de versión única — una discrepancia de versión del Census bloquea igual que cualquier otro fundacional.
### Problema que resuelve
Sin un gate explícito, un cambio de estado de un ID (⚠️ Stub → ✅ Ok) o la creación de un ID nuevo puede quedar reflejado en el documento fuente pero no en el Census, generando drift silencioso entre lo que el sistema documenta y lo que el Census reporta.
---
### Regla 1 — Gate de cierre de ticket [CENSUS-SYNC-R1]
Ningún ticket en Bug Tracker o Tasks Tracker (KERNEL:TRACKER-SCHEMA) que implique cambio de estado de un ID (Stub→Ok, creación de ID nuevo, deprecación de ID existente) se marca Done sin que el Census haya sido regenerado y reflejado ese cambio. Si el re-run de generate_census.py no puede ejecutarse en el momento (ej. sin acceso a Terminal), el ticket permanece en estado Blocked-Census — no se da por cerrado en falso.
Tag de referencia cruzada: [CENSUS-SYNC-R1] es el string literal canónico que cualquier skill debe citar textualmente al referenciar esta obligación — evita que cada skill redacte su propia paráfrasis del gate (R-13, auditoría de skills 2026-07-19).
---
### Regla 2 — Alta de IDs nuevos en el spec + deeplink automático
generate_census.py debe operar en dos modos:
(a) resolución de IDs ya conocidos en CENSUS_SPEC, y
(b) detección de IDs presentes en los documentos fuente que NO están en CENSUS_SPEC ("IDs huérfanos").
Todo ID huérfano detectado se reporta explícitamente al operador antes de cerrar el ticket asociado — no se ignora silenciosamente. Para todo ID resuelto (conocido u orfano recién agregado), el script genera vía API el deeplink correspondiente al bloque exacto en Notion — la navegación desde el Census hacia la porción publicada en el TOC del documento fuente debe ser precisa, no aproximada al documento completo.
---
### Regla 3 — Disparo atado a Changelog
Toda entrada nueva en V-CHANGELOG que documente cierre de tickets con cambio de estado de ID debe ir precedida, en la misma sesión, por el re-run de Census. El Census se actualiza antes de que Changelog registre el batch — no después, no como tarea suelta.
---
### Regla 4 — Presentación automática de DRY RUN de cierre
Ninguna sesión que haya involucrado cambios (constructivos, correctivos o destructivos) a la documentación o a bases de datos puede cerrarse sin que el AI Component presente, en automático y sin esperar solicitud del operador, un resumen DRY RUN de todo lo modificado en la sesión — incluyendo estado de Census, Changelog pendiente/escrito, y versión. Esta presentación es un reporte de cierre, no un nuevo write: no reabre aprobaciones ya otorgadas, solo consolida y expone lo que quedó pendiente o completado.
---
### Regla 5 — Chequeo informativo en arranque
health_check.py (KERNEL:HEALTH-CHECK) reporta la antigüedad del V-ID-CENSUS en cada corrida (umbral 7 días), como advertencia amarilla si está desactualizado. Este chequeo es puramente informativo — no bloquea el arranque de sesión ni auto-ejecuta generate_census.py (el script pega a la API de Notion con rate-limit real, incompatible con el contrato de lectura estricta y rápida de health_check.py). El gate real de obligatoriedad sigue viviendo en el cierre de tickets (Regla 1), no en el arranque.
No aplica a: tickets que no modifican estado de ningún ID (ej. fixes de redacción, correcciones de trailing space en propiedades Notion).
---
## §10— KERNEL:VERSION-CHECK-TOOL
Herramienta de Verificación de Versiones
Propósito: Ruta de bajo costo para verificar y sincronizar la propiedad Versión de los 9 documentos fundacionales (Kernel, Manual, Career Canon, System Prompt, Aliases, Changelog, Census, Navigation Brief, VANTAGE Central Hub) sin pagar el costo de token e infraestructura de un notion-fetch completo (body entero) por documento.
### Modos de Operación (verify_versions.py)
1. Sync Mode (--sync): Único modo de escritura y única fuente de verificación de versión. Relee cada documento inmediatamente después de escribirlo para confirmar el valor persistido, no solo el status code del PATCH.
Output: tabla de 9 filas (documento | esperado | releído | veredicto) cerrada con [VEREDICTO FINAL] PASS/FAIL.
1. Bootstrap Mode (--bootstrap): sin cambios respecto a versiones previas — dump de contexto de apertura de sesión (Ledger + Changelog + tickets prioritarios), read-only.
1. Modo Check eliminado (v9.6.2): el antiguo Check Mode (default, tabla de solo lectura sin veredicto) fue retirado. Existía para cubrir un hueco real — el OK/FALLÓ de Sync Mode reflejaba únicamente el status code del PATCH, no una relectura confirmada — pero resolvía ese hueco pidiendo un segundo comando en vez de cerrarlo dentro del primero. La verificación real ahora vive íntegramente dentro de --sync, ya descrita en el punto 1.
Alias de invocación: vversions es el nombre corto canónico de verify_versions.py en Terminal — acepta los dos flags vigentes sin variación (vversions --bootstrap, vversions --sync). El script no tiene modo default sin flag; el flag es obligatorio en cada invocación.
### Reglas Operativas de Sincronización
Límite de Escritura del AI Component: Durante una actualización de versión, el componente de IA tiene estrictamente prohibido actualizar la propiedad Versión de manera individual en los documentos a través de múltiples llamadas de API. El AI Component no realiza escrituras redundantes.
### Flujo Canónico de Sincronización
1. El AI Component redacta el borrador del Changelog y actualiza la versión únicamente en la página de Changelog.
1. El AI Component presenta el DRY RUN de cierre indicando que la versión maestro ha sido asentada en el Changelog.
1. El AI Component solicita explícitamente al operador ejecutar localmente python verify_versions.py --sync desde la terminal para propagar la versión en lote a los 8 documentos fundacionales restantes (Manual, Kernel, Career Canon, System Prompt, Aliases, ID CENSUS, Navigation Brief, VANTAGE Central Hub) en Notion.
1. Una vez propagada en Notion, el operador ejecuta el flujo estándar de vsync_doc.py (vdoc, ya definido en KERNEL:ARCHITECTURE-L4) en L4 para bajar los archivos actualizados al repositorio local.
### Relación de Costos y Rutas
Aplica el principio de triaje de costos (Terminal > MCP) ya establecido en KERNEL:SCOPE/KERNEL:ROUTING (§L0-015). Toda validación y propagación de versión masiva se delega al script local para proteger la economía de contexto y evitar los límites de rate-limiting de la API de Notion.
Convención de nombres de alias (Terminal): v<dominio>[ <subcomando>] — subcomando posicional para scripts con modos mutuamente excluyentes (ej. vl1 tracker, vl1 batch); flags con guión para scripts con variaciones sobre un mismo motor (ej. vversions --sync). Un alias nunca coexiste en paralelo con un nombre casi-idéntico de un script renombrado o corregido — el alias viejo se retira del .zshrc al mismo tiempo que se declara el nuevo.
---
## §11 — KERNEL:HEALTH-CHECK
Contrato de health_check.py
Propósito: contrato operativo de health_check.py — script de arranque del sistema, invocado vía alias start.
Naturaleza: lectura estricta por defecto. Única excepción autorizada a escritura: auto-sync condicional del Entity Index (ver abajo). Ninguna otra sección del script escribe en Notion, git, ni archivos locales.
Checks ejecutados (orden fijo): version → env → git → vgit → notion → docs_sync → vdoc → index_age → pending_tickets.
---
### KERNEL:HEALTH-CHECK-001
— Entity Index Auto-Sync
- Umbral: INDEX_STALE_THRESHOLD_HOURS = 24
- Archivos monitoreados: graph_v2.json, entity_index_v2.json (INDEX_FILES, en SCRIPTS_DIR)
- Condición de disparo: al menos un archivo supera el umbral
- Acción: subprocess a python3 vantage.py sync, cwd = SCRIPTS_DIR, timeout 120s
- Frecuencia: máximo una vez por corrida de health_check.py, solo si se cruzó el umbral — no re-sincroniza índices ya frescos
- Clasificación: housekeeping de rutina, NO remediación de fallo — según la filosofía ya establecida en KERNEL:FAIL-PHILOSOPHY, un índice stale no es un fallo del sistema; es mantenimiento esperado de una estructura de lectura
- Manejo de error: si el sync falla (returncode ≠ 0, timeout, o vantage.py no encontrado), el check reporta fail() y el script NO reintenta ni repara — a partir de ahí aplica el tratamiento estándar de KERNEL:FAIL-PHILOSOPHY (reportar, esperar instrucción)
Justificación de la excepción: las Golden Rules de "no reparar automáticamente" — un conjunto de restricciones de arquitectura para el componente AI que se desarrolla íntegramente más adelante en KERNEL:CV-GOLDEN-RULES, y cuyo principio relevante aquí es que el sistema no debe intentar "arreglar" discrepancias de negocio sin instrucción humana — aplican a discrepancias de negocio en el pipeline (Score, Gate_Decision, URLs, JD). El Entity Index es infraestructura de lectura del Runtime, no un dato de negocio — su staleness no es un "fallo" en ese sentido, es equivalente en naturaleza al sync automático ya existente de L4 (git, vía launchd) y L3 (Gmail, vía launchd): mantenimiento programado, no decisión que requiera al operador.
---
### KERNEL:HEALTH-CHECK-001.1 — Auto-Archive como Housekeeping Automático
Naturaleza: Excepción de escritura de housekeeping — mismo tratamiento arquitectónico que Entity Index Auto-Sync (KERNEL:HEALTH-CHECK-001). No es dato de negocio del pipeline de vacantes; es ejecución de una decisión ya tomada por Python. (Fuente: Changelog v9.5.9, v9.5.6, v9.5.4 — mecanismo citado del Changelog, no re-verificado contra el script en esta sesión.)
Propósito: Ejecutar automáticamente el archivado de registros del Tracker de vacantes cuando Python ya determinó (vía campos Class B) que cumplen las condiciones de archivo.
Registro con ambos campos poblados simultáneamente:
- Next_Action = 'Archivar'
- Dedup_Flag = 'Posible duplicado'
Nota de esquema: Dedup_Flag no aparece en la enumeración de campos Class B de KERNEL:SCHEMA-001 — queda documentado aquí por fuente de Changelog, pendiente de conciliar contra el esquema real en una próxima verificación.
Check obligatorio antes de archivar:
```python
if Gate_Decision == 'APPLIED':
    status = "PROTECTED_ACTIVE_APPLICATION"
    return  # NO archivar bajo ninguna circunstancia
```
Justificación del patch: Previene archivado accidental de registros con aplicaciones activas. Consistente con KERNEL:GATE-DECISION-007.
- dry-run obligatorio antes de execute
- APROBAR_WRITE requerido para ejecutar archivado real
- Archivado físico: archived=True en llamada a notion.pages.update() (endpoint PATCH /v1/pages/{page_id})
Housekeeping automático, NO remediación de fallo. Según KERNEL:FAIL-PHILOSOPHY, un registro duplicado ya marcado por Python no es un "fallo del sistema"; auto_archive.py ejecuta una decisión de archivado ya resuelta por el motor de detección de duplicados.
auto_archive.py lee únicamente Next_Action y Dedup_Flag de Notion — no invoca ni comparte lógica con el motor de detección de cruce Marca+Rol. No mueve nada a Archivo sin que ambas flags ya estén asignadas por Python.
Registros con Next_Action ya poblado quedan protegidos y no reciben acciones retroactivas sin limpieza manual del campo.
Origen: Changelog v9.5.9 — Security Patch + Canonización Documental
Bug cerrado: 39b938befc4281efa1ccdd5d763bfdbf (Tracker)
---
### KERNEL:HEALTH-CHECK-002
— Reporte de Tickets
Agrupación por campo Prioridad (CRÍTICO/ALTO/MEDIO/BAJO/Sin Prioridad) sobre Bug Tracker y Task Tracker. Detalle explícito (título) solo para CRÍTICO y ALTO; MEDIO/BAJO/Sin Prioridad solo cuentan. Clasificación Reactivo→Bug / Proactivo→Task ya definida en KERNEL:TRACKER-SCHEMA.
---
### KERNEL:HEALTH-CHECK-003 — Skills de Mantenimiento del Tracker
Las siguientes 5 skills operan como infraestructura de housekeeping del sistema, ejecutando mantenimiento sobre documentos fundacionales y bases de datos de tickets. No son triggers del AI Component para procesamiento de vacantes — son herramientas de limpieza y registro.
| Skill | Propósito | Gate DRY RUN + APROBAR_WRITE |
| --- | --- | --- |
| vantage-create-bug-task | Crear tickets en Bug Tracker desde descripción estructurada del operador | ✅ Obligatorio |
| vantage-present-handoff | Generar resumen COMPLETADO/PENDIENTE de sesión (invocable independiente o como paso de vantage-session-close) | ❌ No aplica (solo lectura + reporte) |
| vantage-tidy-changelog | Append de entrada nueva en Change Log + edición de última entrada si aplica | ✅ Obligatorio |
| vantage-tidy-bug-task-tracker | Limpieza de campos, normalización de Status, detección de tickets huérfanos | ✅ Obligatorio |
| vantage-tidy-opportunities-tracker | Detección de duplicados, normalización de campos Class A, creación de copias para archivo | ✅ Obligatorio |
Toda skill que modifique estado de un ID canónico (creación, deprecación, Stub→Ok) debe citar textualmente el tag [CENSUS-SYNC-R1] al referenciar la obligación de regenerar el Census antes de cerrar el ticket asociado.
No parafrasear. Cada skill referencia el contrato usando el string literal [CENSUS-SYNC-R1], no una descripción libre de la regla.
Skills que ejecutan operaciones multi-paso (ej. vantage-tidy-changelog: append + edición; vantage-tidy-opportunities-tracker: crear-copia + marcar-original) documentan el estado intermedio como recuperable, sin reintentar el paso ya exitoso.
Todas las skills de mantenimiento declaran inicio/cierre con verbos propios en gerundio/participio, según KERNEL:SKILL-ANNOUNCE-CONVENTION — ya listadas en esa sección.
Origen: Changelog v9.6.0, v9.5.8, v9.5.7 — Documentación Transversal de Skills de Mantenimiento
---
## §12 — KERNEL:SESSION-LEDGER
Registro de Continuidad de Sesión
Propósito: Registrar apertura y cierre de sesión para detectar terminación abrupta (crash, timeout, cierre de ventana) sin paso por Session Close Protocol.
Naturaleza: excepción de escritura de housekeeping — mismo tratamiento arquitectónico que KERNEL:HEALTH-CHECK-001 (Entity Index Auto-Sync). No es dato de negocio del pipeline de vacantes; no requiere APROBAR_WRITE porque no toca campos Class A ni Class B del Tracker.
### Estructura
Página Notion standalone con 4 propiedades:
1. session_id (texto, generado por la IA al inicio de sesión)
1. status (select: OPEN / CLOSED)
1. opened_at (timestamp)
1. pending_summary (texto libre — espejo del bloque COMPLETADO/PENDIENTE del último Session Close)
### Escritura autorizada en dos puntos únicamente
1. SKILL-OPEN, paso 0 — antes de Health Check: status → OPEN
1. SKILL-CLOSE, paso 6 — antes de Close: status → CLOSED + pending_summary poblado
Ningún otro trigger ni componente escribe en este documento. Python no lo toca — es propiedad exclusiva del AI Component como infraestructura de continuidad de sesión.
Fuente de verdad de "pendientes": este documento reemplaza a la memoria conversacional o a Claude Memory como fuente primaria de Pending Items en el bootstrap (ver SKILL-OPEN §4 modificado — flujo operativo completo documentado en el Manual, §6).
---
## §13— KERNEL:DOCUMENTATION-TRANSVERSAL-001
Documentación Transversal — Contrato de Integridad Documental
Con KERNEL:CENSUS-SYNC (§L0-010) y KERNEL:SESSION-LEDGER (§L0-013) ya estableciendo cómo se audita el Census y cómo se registra continuidad de sesión, esta sección cierra el clúster de gobernanza documental con el contrato que cubre el caso restante: un cambio de código, schema o flujo operativo que ocurrió pero no tiene contraparte en los documentos fundacionales.
Propósito: Ningún cambio estructural del sistema — script nuevo, schema modificado, decisión de arquitectura resuelta en chat — queda sin ancla documental. La detección puede ser explícita (el operador solicita "documentación transversal" o "parche orgánico") o de recordatorio no-bloqueante (el AI Component identifica el gap en curso de otra tarea y lo señala sin detener el trabajo activo).
### Principio rector — nodo natural, no adendum
Todo contenido nuevo se integra en el punto del flujo de lectura donde el documento lo necesita, nunca apilado al final por conveniencia. Kernel: el orden de sección es orden de prioridad de lectura. Manual: narrativa progresiva — el parche encaja en la secuencia lógica del operador.
Extiende, no redefine: Los criterios de calidad de todo parche documental viven en MANUAL:PATCH-QUALITY-001 — cinco filtros (invisibilidad estructural, continuidad de voz, progresión narrativa, diff mínimo, coherencia transversal). Este contrato los hereda; no declara un criterio paralelo.
### Protocolo (seis fases)
1. Mapeo — identificar todos los documentos fundacionales que el cambio toca; fetch en vivo obligatorio de cada uno antes de proponer nodo(s) de inserción
1. DRY RUN del parche ya en su nodo autorizado — APROBAR_WRITE independiente del de la Fase 1
1. Inyección respetando jerarquía tipográfica y convención de voz del documento objetivo
1. Write-Back Verification — re-fetch de solo lectura post-escritura; un mismatch detiene la operación, una confirmación en chat de que "ya se escribió" nunca es evidencia suficiente por sí sola
1. Changelog + versión — única fuente de historial; nunca se escribe changelog dentro de un documento individual
1. Binary Gate de salida — Full Data Dump o Step-by-Step, a elección del operador
Disparo de KERNEL:CENSUS-SYNC Regla 1: Si el cambio da de alta, deprecia o cambia de estado un ID canónico, el Census se regenera antes de cerrar el ticket asociado — mismo gate que ya rige cualquier otro alta de ID.
Gestión de pendientes: Un parche no aplicado de inmediato se registra en Tasks Tracker (d2a65ca1-6a35-465d-bcff-b0d82dddd549), no en el Tracker de vacantes.
---
### Navigation Brief — Documento de Descubrimiento y Enrutamiento
ID: 3a3938be-fc42-8008-9e90-ec435c01f50d
Estatus: documento fundacional (parte de los nueve totales, desde v9.6.6)
Versión: Sincronizada con el resto de la suite
El Navigation Brief es la Fuente Única de Verdad (SSOT) para la navegación documental en VANTAGE. Resuelve la necesidad de un contrato claro para enrutar consultas y modificaciones estructurales, eliminando ambigüedades en la recuperación de información.
No reemplaza los documentos fundacionales — los complementa como índice de descubrimiento que mapea dominios críticos (Housekeeping, Core Assets, Discovery, Gate Logic, CV Pipeline) a sus ubicaciones canónicas en el Kernel, Manual y System Prompt.
- SP:SYNC-RULE: El Navigation Brief queda sujeto a la Regla de Versión Única. Discrepancias de versión bloquean igual que cualquier otro fundacional.
- KERNEL:CENSUS-SYNC: Los 11 IDs del Brief (BRIEF:001 a BRIEF:011) están registrados en el V-ID-CENSUS y sujetos a las 5 reglas de sincronización.
- verify_versions.py: Debe incluir el Brief en la verificación de los 9 fundacionales — pendiente de confirmar contra el código real, no asumido en esta sesión.
| ID | Sección | Propósito |
| --- | --- | --- |
| BRIEF:001 a BRIEF:011 | Secciones del Navigation Brief | Mapeo de dominios críticos a rutas canónicas |
Origen: Changelog v9.6.6, v9.6.3 — Integración del Navigation Brief como Fundacional
---
### VANTAGE Central Hub — Documento Fundacional de Entrada
ID: 36e938be-fc42-81d6-bf40-dfe7dee782a5
Estatus: documento fundacional (parte de los nueve totales, desde v9.6.8)
Versión: Sincronizada con el resto de la suite
El VANTAGE Central Hub es el punto de entrada del workspace en Notion — la página raíz desde la que se navega hacia todos los demás fundacionales, archiveros y trackers del sistema. No define contratos operativos propios; su función es de organización y acceso, no de gobernanza de contenido.
- SP:SYNC-RULE: sujeto a la Regla de Versión Única, igual que cualquier otro fundacional — una discrepancia de versión del Hub bloquea igual que las demás.
- KERNEL:DOC-CONTRACT: prefijo VANTAGE registrado en la tabla de Prefijos Autorizados (§7).
- KERNEL:CENSUS-SYNC: incluido en el conteo de nueve fundacionales; no aporta IDs propios de sección (no tiene contratos internos tipo BRIEF:001).
Origen: Changelog v9.6.8 — Integración de VANTAGE Central Hub como noveno fundacional
---
## §14 — KERNEL:SCOPE / KERNEL:ROUTING
Economía de Contexto y Rutas de Carga
Estas dos secciones del Kernel original cubrían, de forma parcialmente redundante, el mismo problema: cómo el componente AI decide cuándo consultar lógica del sistema vía Terminal (barato, determinista) frente a MCP (más caro, pero necesario para ciertas operaciones). Se fusionan aquí en una sola sección narrativa; ambos IDs (KERNEL:SCOPE y KERNEL:ROUTING) se conservan como anclas para no romper referencias existentes en el resto del documento.
### KERNEL:SCOPE
— Principio General
- Acceso a lógica base preferente vía Terminal (lazy_loader.py)
- MCP autorizado para lectura, DRY RUN y modificación documental del Kernel cuando exista instrucción explícita del operador
- Terminal continúa siendo la ruta recomendada para operaciones masivas, auditorías y cambios estructurales
- Runtime: L0 (Lectura estricta). Cero escritura directa.
- Jerarquía: L1 > L2 > L3 (ya establecida en KERNEL:ARCHITECTURE-L4). Claude consolida, NO extrae.
- FEED: única vía manual de Claude es FAST (KERNEL:TRIGGER-008). Toda ingesta de L1, L2 y L3 se realiza metódicamente vía Python (layer_1_run.py, layer_3_mail.py, feed_processor.py). Ante JSON o FEED sin trigger FAST explícito: "El procesamiento de FEED está migrado a Python; usa FAST si requieres entrada manual."
- Triaje de ejecución: Antes de usar herramientas, aplicar: 1. Requerimientos, 2. Triaje de costos (A: Terminal, B: MCP, C: Upload), 3. Confirmación. Priorizar Opción A.
### KERNEL:ROUTING
— Mecanismo Técnico de las Rutas MCP
El principio de arriba se traduce operativamente así: para consultar lógica pesada, prioriza Terminal. Alternativamente, MCP puede utilizarse cuando:
- El operador lo solicite explícitamente
- La operación sea documental
- Se presente DRY RUN previo
- Exista autorización posterior mediante APROBAR_WRITE cuando aplique
Ruta recomendada: python lazy_loader.py --page {KERNEL_MASTER} --route {ruta}
Ruta permitida: MCP
Rutas válidas:
- ruta: KERNEL:SCHEMA
- ruta: KERNEL:OWNERSHIP
- ruta: KERNEL:TRIGGERS
- ruta: KERNEL:CV-PIPELINE
- ruta: KERNEL:GATE-DECISION
- ruta: KERNEL:CV-GOLDEN-RULES
- ruta: KERNEL:FAIL-PHILOSOPHY
---
## §15 — KERNEL:DATA-FLOW
Flujo de Datos y Escritura
Con la economía de contexto ya resuelta (§L0-015), esta sección describe la secuencia obligatoria por la que pasa cualquier escritura del sistema, de principio a fin: Kernel → DRY RUN → APROBAR_WRITE → Notion Write.
Desglosado: el componente AI consulta el Kernel (vía Terminal, según la ruta preferente de KERNEL:SCOPE) para confirmar el contrato del trigger activo; produce un DRY RUN — el preview de campos a escribir, ya definido formalmente en KERNEL:TRIGGER-004 — para que el operador lo revise; espera una de las variantes válidas de APROBAR_WRITE (KERNEL:SCHEMA-006); y solo entonces ejecuta la escritura real en Notion.
Ningún paso de esta cadena puede saltarse: escribir sin DRY RUN previo, o sin APROBAR_WRITE explícito, viola el contrato aunque el contenido a escribir sea correcto.
Pre-validación: Cruzar esquema contra KERNEL:SCHEMA antes de cualquier escritura — es decir, confirmar que cada campo en el payload de escritura es Class A y no Class B, exactamente como exige KERNEL:SCHEMA-002.
