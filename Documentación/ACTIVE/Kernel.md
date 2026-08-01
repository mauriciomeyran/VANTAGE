# V | KERNEL

# V | KERNEL
> 
## DECLARACIÓN DE AUDIENCIA Y ALCANCE
- Audiencia: Sistemas Agente de IA.
- Alcance: Este documento es el KERNEL_RUNTIME, que contiene únicamente los contratos operativos activos para la IA. Para el documento de referencia completo, solicitar acceso al KERNEL 8.0.
| # | ID | SECCIÓN | PORCIÓN |
| --- | --- | --- | --- |
| 01 | KERNEL:PURPOSE | FUNDAMENTO | FUNDAMENTO |
| 02 | KERNEL:FAIL-PHILOSOPHY | FILOSOFÍA DE FALLO | FUNDAMENTO |
| 03 | KERNEL:DOCUMENTATION | DOCUMENTACIÓN (L0) | FUNDAMENTO |
| 04 | KERNEL:ARCHITECTURE | ARQUITECTURA | FUNDAMENTO |
| 05 | KERNEL:OWNERSHIP | OWNERSHIP | FUNDAMENTO |
| 06 | KERNEL:DASHBOARD-CHECKLIST-ARCH | DASHBOARD CHECKLIST | FUNDAMENTO |
| 07 | KERNEL:SCHEMA | SCHEMA | DATOS, ESQUEMAS Y REGLAS |
| 08 | KERNEL:TRACKER-SCHEMA | TRACKER SCHEMA | DATOS, ESQUEMAS Y REGLAS |
| 09 | KERNEL:GATE-DECISION | GATE DECISION | DATOS, ESQUEMAS Y REGLAS |
| 10 | KERNEL:CV-GOLDEN-RULES | CV GOLDEN RULES | DATOS, ESQUEMAS Y REGLAS |
| 11 | KERNEL:TRIGGERS | TRIGGERS | EJECUCIÓN |
| 12 | KERNEL:CV-PIPELINE | CV PIPELINE | EJECUCIÓN |
| 13 | KERNEL:CANON-UPDATE | CANON UPDATE | EJECUCIÓN |
| 14 | KERNEL:NAMING-CONVENTION | NAMING CONVENTION | EJECUCIÓN |
| 15 | KERNEL:CONTEXT-INFRASTRUCTURE | CONTEXT INFRASTRUCTURE | INFRAESTRUCTURA DE CONTEXTO |
| 16 | KERNEL:DATA-FLOW | DATA FLOW | INFRAESTRUCTURA DE CONTEXTO |
| 17 | KERNEL:EVOLUTION | EVOLUTION | INFRAESTRUCTURA DE CONTEXTO |
# I. FUNDAMENTO
## 01 KERNEL:PURPOSE
Propósito del Sistema
VANTAGE resuelve un problema de ingeniería de atención: en una búsqueda laboral sin estructura, las oportunidades de alta señal desaparecen antes de ser procesadas, mientras el tiempo se consume en vacantes de baja calidad.
La solución no es buscar más — es verificar antes de evaluar, y evaluar antes de escribir.
### 01.1 KERNEL:PURPOSE-001
Invariantes del Sistema
1. Una vacante no entra al pipeline sin URL válida — excepción: Bypass activo (ver 09.1).
1. Score no lo calcula el sistema de lenguaje — lo calcula Python con lógica determinista.
1. Gate decision no se sobreescribe manualmente. RT-1 permite corregir inputs Class A para que Python recalcule (ver 09.5).
1. Strategy es responsabilidad humana; processing es responsabilidad del sistema.
Qué significa esto para el Sistema AI
El componente AI es el procesador textual del pipeline:
- Deduplica, normaliza, genera DRY RUN, escribe Class A en Notion, produce CVs.
- Evaluación de calidad estratégica y cálculo de campos Class B no son operaciones de este componente (ver 05 OWNERSHIP, 10 CV-GOLDEN-RULES).
- Si una tarea no está en la tabla de triggers (11), no se ejecuta.
---
## 02 KERNEL:FAIL-PHILOSOPHY
Filosofía de Fallo
Los fallos del sistema son señales de que el pipeline funciona correctamente. Un gate que nunca bloquea no está filtrando. La presencia de gates BLOCKED, scores en 0 y entradas EXPIRED es evidencia de que el sistema aplica sus criterios.
### 02.1 KERNEL:FAIL-PHILOSOPHY-001
Qué hace el Sistema cuando falla
- No intenta reparar outputs.
- No sugiere workarounds.
- No escala urgencia.
- Reporta el estado y espera instrucción humana.
### 02.2 KERNEL:FAIL-PHILOSOPHY-002
Excepción — Gate BLOCKED Recuperable vía RT-1
El AI informa la opción pero no la ejecuta sin instrucción explícita.
---
## 03 KERNEL:DOCUMENTATION
Documentación y Gobernanza (L0)
### 03.1 KERNEL:DOCUMENTATION-001
Canonical Document ID Contract
Invariantes del Contrato
- Formato Único: [PREFIX]:[KEY] (ej. MANUAL:SETUP).
- Prefix Ownership: Cada prefijo mapea a una única página canónica en Notion.
- SSOT: resolver_registry_v2.json es la autoridad única para resolver Prefijos a UUIDs.
- Resolución Determinista: El Resolver (v1.py) garantiza resolución O(1) inyectando el ID crudo al componente solicitante.
Prefijos Autorizados
| Prefijo | Documento Destino | Mapeo Registry |
| --- | --- | --- |
| KERNEL | V | KERNEL | KERNEL |
| MANUAL | V | MANUAL | MANUAL |
| CANON | V | CAREER CANON | CAREER CANON |
| TRACKER | V | TRACKER | TRACKER |
| SP | V | SYSTEM PROMPT | SYSTEM PROMPT |
| ALIASES | V | ALIASES | ALIASES |
| CHANGELOG | V | CHANGE LOG | CHANGE LOG |
| BRIEF | V | NAVIGATION BRIEF | NAVIGATION BRIEF |
| VANTAGE | V | VANTAGE CENTRAL HUB | VANTAGE CENTRAL HUB |
Matriz Tipográfica Congelada (Jerarquía de Encabezados)
La resolución de un ID canónico a su nivel de heading Markdown sigue una jerarquía fija:
- Documento (raíz) = #
- Capítulo/Sección canónica = ##
- Subsección (NN.N) = ###
- Figma Tag (solo derivados, inmutable) = ######
Esta matriz es la fuente de verdad para cualquier futura alta de ID bajo este contrato — ningún nodo NN.N comparte nivel con su capítulo padre.
Regla de Bloque Único
Todo heading ### (subsección NN.N) declara su ID canónico [PREFIX]:[KEY] en la misma línea de heading que su título — nunca en línea separada ni como texto plano bajo el heading. No existe excepción decorativa: un heading ### sin ID visible en su propia línea viola este contrato.
Reglas de Migración
Toda referencia a páginas del sistema que use UUIDs hardcodeados o anclas planas debe migrar a este esquema. lazy_loader.py aplica este contrato en tiempo de ejecución. DT-015 — CERRADO: normalización documental (26 ocurrencias) vía trigger NORM. 100% canónico.
---
### 03.2 KERNEL:DOCUMENTATION-002
Normalización Documental de IDs Legacy
- Esquema: [PREFIX]:[KEY].
- Alcance: todos los documentos fundacionales.
- Excepciones: IDs de Notion (UUIDs) en metadatos o URLs.
- Gobernanza: cambios requieren APROBAR_WRITE + entrada en Changelog.
Estado actual: normalización completada. DT-015 (26 ocurrencias) — CERRADO.
---
### 03.3 KERNEL:DOCUMENTATION-003
L0 — VANTAGE Runtime
Tipo: Capa de Observabilidad y Abstracción de Datos (ReadOnly).
Propósito: Provee la verdad técnica sobre Notion. Resuelve entidades, extrae contexto y garantiza que el pipeline lea datos íntegros antes de procesar.
Runtime Build — proceso determinista que genera:
- entity_index_v2.json
- graph_v2.json
- backlinks_v2.json
Consume resolver_registry_v2.json como fuente de namespace ownership — si el Registry no define el prefix de un tipo de entidad, el Build falla explícitamente. graph_layer.py construye graph_v2.json; nunca infiere namespaces ni redefine contratos.
```plain text
Notion (Source) → Runtime (Index + Resolver) → API Response → Pipeline (L1/L2/L3/CV)
```
Version Check Tool y Census como parte de L0: verify_versions.py (alias vversions) y generate_census.py (alias vcensus) son observabilidad ReadOnly sobre Notion — mismo tipo de operación que Runtime Build, aplicada a versión documental y salud del Census.
```plain text
Notion (Source) → Version Check (9 docs) / Census (ID audit) → Reporte a operador
```
---
### 03.4 KERNEL:DOCUMENTATION-004
L0-Bootstrap — Dynamic Governance Layer
Tipo: Capa de Sincronización de Sesión (Fetch-on-Start).
Propósito: Elimina el drift de versiones entre la UI estática del agente y el repositorio dinámico de Notion.
Bootstrap Protocol
Ante el primer mensaje del operador, el AI Component suspende el procesamiento de datos y ejecuta fetch de SP:BOOTSTRAP-001 y del ID CENSUS. El resultado sobreescribe cualquier instrucción estática previa. Si el Bootstrap falla, reportar "MODO DEGRADADO" y no proceder con triggers operativos.
Convención de estado (X-ING → X-ED)
El Bootstrap declara inicio con BOOTLOADING... y cierre con BOOTLOADED: DOCUMENTOS CARGADOS.
Distinción de alcance — Bootstrap vs. Session Ledger
El Bootstrap corre en cada mensaje inicial de cualquier conversación del proyecto — carga de contexto universal, no registro de sesión formal. El Session Ledger (03.9) es opt-in: solo se escribe cuando el operador invoca vantage-session-open.
```plain text
Sesión Iniciada → BOOTLOADING... → AI Fetch (Bootstrap IDs) → Sincronización de Verdad Operativa
→ BOOTLOADED: DOCUMENTOS CARGADOS → Procesamiento Petición
(Ledger: solo si el operador invoca vantage-session-open)
```
---
### 03.5 KERNEL:DOCUMENTATION-005
Convención de Anuncio de Skills
Todo skill de VANTAGE declara inicio y cierre de su protocolo con un verbo propio en gerundio/participio, nunca con un mensaje genérico compartido ni con el lenguaje de cierre del Bootstrap universal (BOOTLOADED).
Implementación actual
- vantage-session-open — SESSION-OPENING… / SESSION-OPENED
- vantage-session-close — CLOSING SESSION… / SESSION CLOSED
- vantage-documentacion-transversal — BEGINNING DOCUMENTATION… / DOCUMENTATION FINISHED
- prompt-master — PROMPTING… / PROMPT FINISHED
- vantage-create-bug-task — LOGGING TICKET… / TICKET LOGGED
- vantage-present-handoff — HANDING OFF… / HANDOFF DELIVERED
- vantage-tidy-changelog — TIDYING CHANGELOG… / CHANGELOG TIDIED
- vantage-tidy-bug-task-tracker — TIDYING TRACKER… / TRACKER TIDIED
- vantage-tidy-opportunities-tracker — TIDYING OPPORTUNITIES… / OPPORTUNITIES TIDIED
---
### 03.6 KERNEL:DOCUMENTATION-006
Contrato de health_check.py
Naturaleza: lectura estricta por defecto. Única excepción: auto-sync condicional del Entity Index.
Checks ejecutados (orden fijo)
version → env → git → vgit → notion → docs_sync → vdoc → index_age → pending_tickets.
Entity Index Auto-Sync
Umbral 24h sobre graph_v2.json / entity_index_v2.json. Acción: subprocess a python3 vantage.py sync, timeout 120s. Clasificación: housekeeping de rutina, no remediación de fallo.
Reporte de Tickets
Agrupación por Prioridad (CRÍTICO / ALTO / MEDIO / BAJO) sobre Bug Tracker y Task Tracker. Detalle explícito solo para CRÍTICO y ALTO.
---
### 03.7 KERNEL:DOCUMENTATION-007
Herramienta de Verificación de Versión
Propósito: ruta de bajo costo para verificar y sincronizar la Versión de los 9 documentos fundacionales sin pagar el costo de un fetch completo por documento.
Modos
- --sync (único modo de escritura y verificación real, relee cada documento post-escritura)
- --bootstrap (dump read-only de apertura de sesión)
Modo Check eliminado en v9.6.2 — la verificación real vive íntegramente en --sync.
Alias: vversions — acepta --bootstrap o --sync, sin modo default.
---
### 03.8 KERNEL:DOCUMENTATION-008
Sincronización Obligatoria del ID Census
El V-ID-CENSUS es el noveno documento fundacional, derivado — su fuente de verdad son los IDs reales de los otros ocho documentos.
Reglas
1. [CENSUS-SYNC-R1]: ningún ticket que implique cambio de estado de un ID se marca Done sin Census regenerado. Si no puede ejecutarse, el ticket queda Blocked-Census.
1. generate_census.py detecta IDs huérfanos y los reporta antes de cerrar el ticket asociado.
1. El Census se regenera antes de que el Changelog registre el batch.
1. Ninguna sesión con cambios cierra sin DRY RUN automático de lo modificado.
1. health_check.py reporta antigüedad del Census (umbral 7 días) como advertencia informativa, no bloqueante.
---
### 03.9 KERNEL:DOCUMENTATION-009
Session Ledger
Naturaleza: excepción de escritura de housekeeping — no requiere APROBAR_WRITE.
Estructura
Database Notion (data_source_id 8d736032-eef9-4e6e-a05a-df8b8079ebff) con:
- session_id
- status (OPEN / CLOSED)
- opened_at
- pending_summary
Escritura autorizada
Solo SKILL-OPEN paso 0 (→ OPEN) y SKILL-CLOSE paso 6 (→ CLOSED + pending_summary).
---
### 03.10 KERNEL:DOCUMENTATION-010
Documentación Transversal — Contrato de Integridad Documental
Protocolo (seis fases)
Mapeo → DRY RUN → Inyección → Write-Back Verification → Changelog + versión → Binary Gate de salida.
Skills de Gobernanza Documental
| Skill | Propósito | Gate |
| --- | --- | --- |
| vantage-create-bug-task | Crear tickets en Bug Tracker | ✅ Obligatorio |
| vantage-present-handoff | Resumen COMPLETADO/PENDIENTE | ❌ No aplica |
| vantage-tidy-changelog | Append + edición de Change Log | ✅ Obligatorio |
| vantage-tidy-bug-task-tracker | Limpieza de campos/normalización | ✅ Obligatorio |
| vantage-tidy-opportunities-tracker | Duplicados/normalización Class A | ✅ Obligatorio |
---
### 03.11 KERNEL:DOCUMENTATION-011
Sistema de Cross-Reference Hyperlinks
Propósito: convertir cada mención de un ID canónico (PREFIX:KEY) en los 6 documentos fundamentales en un hipervínculo real al bloque de definición, en vez de texto plano — para que el sistema sea navegable y auditable, no solo nombrado.
Piezas
- generate_census.py (resuelve cada ID a su anchor de bloque real vía API, detecta huérfanos)
- apply_hyperlinks.py (aplica los hipervínculos sobre los .md locales, --dry-run por defecto)
- vantage_id_rules.py — módulo destinado a ser la fuente única de reglas DEF/REF/heading para ambos.
Regla permanente
El heading de definición nunca se auto-enlaza a sí mismo; toda mención posterior (TOC, prosa, tablas de referencia) sí es clickeable.
Estado de adopción (2026-07-26)
- apply_hyperlinks.py ya importa de vantage_id_rules.py.
- generate_census.py mantiene lógica propia parcheada en paralelo, funcionalmente equivalente pero no consolidada.
- generate_id_inventory.py y normalize_heading_ids.py aún no migrados — este último sigue proponiendo el formato legacy §N — ID como destino y no debe correrse con --apply hasta su propia migración.
Ver MANUAL:HEALTHCHECK para el procedimiento operativo de cuándo correr cada script.
---
## 04 KERNEL:ARCHITECTURE
Arquitectura de Cuatro Capas
### 04.1 KERNEL:ARCHITECTURE-L1
Active Recon
Trigger: humano (ciclo semanal — lunes)
```plain text
Human signal → Career Sites · LinkedIn · Aggregators (paralelo) → JSON estructurado
→ FEED → feed_processor.py → Notion (Class A) → vantage-pipeline
```
### 04.2 KERNEL:ARCHITECTURE-L2
Strategic Search
Trigger: humano (ciclo semanal — lunes)
```plain text
Human signal → Gemini · You.com · Grok (extracción paralela) → Perplexity (Consolidation & Dedup)
→ FEED → feed_processor.py → Notion (Class A) → vantage-pipeline
```
### 04.3 KERNEL:ARCHITECTURE-L3
Passive Intake
Trigger: automático (continuo)
```plain text
Gmail (.Jobs label) → layer_3_mail.py (IMAP + Groq) → Notion (Class A poblado, Class B vacío) → vantage-pipeline
```
### 04.4 KERNEL:ARCHITECTURE-L4
Version Control & Infrastructure
No es capa de búsqueda — infraestructura documental.
- Auto-commit + push cuando hay cambios en el repo. Alias: vgit · 09:00/15:00/21:00.
- Repo: github.com/mauriciomeyran/VANTAGE.
- vsync_doc.py — sync bidireccional Notion → ACTIVE/ para los 6 fundacionales editables (Kernel, System Prompt, Career Canon, Manual, Aliases, Change Log). Alias: vdoc · Flags: dry | notion | local | auto.
Skills Distribution — Single Source of Truth
/skills/ en la raíz del repo es la fuente canónica de los .skill files de VANTAGE (actualmente 12) + index.json + index.html. GitHub Pages sirve esta ruta desde main en https://mauriciomeyran.github.io/VANTAGE/skills/. git_sync.py (el mismo motor detrás del alias vgit) detecta nuevos .skill en /skills/, regenera index.json y ejecuta commit + push en la misma corrida — no requiere paso manual adicional.
Consumidores:
- Claude Desktop vía MCP filesystem local (@modelcontextprotocol/server-filesystem apuntando a /skills/).
- Devin Desktop vía devin mcp add vantage-skills -- npx markdown-mcp-resource@latest <URL> contra el espejo de GitHub Pages.
/skills/ local es la fuente primaria; GitHub Pages es espejo — ambos LLMs leen en última instancia de la misma raíz canónica.
vsum.py (alias vsum) — herramienta de continuidad entre sesiones e IAs, no capa de búsqueda ni de pipeline: resume transcripts de sesiones (Claude, Gemini, ChatGPT, u otro) a Markdown estructurado (contexto, hallazgos, decisiones, pendientes), orientado a que la siguiente sesión o la siguiente IA no pierda continuidad. Escribe vía notion_client.Client directo (no MCP) como página hija del INBOX (ver Cédula Digital, SP:DIGITAL-ID-CARD). Mismo patrón de acceso directo a la API ya usado por vsync_doc.py. No lee ni escribe el Tracker de vacantes; su único contacto con Notion es de salida (push opcional del resumen), nunca de entrada.
Jerarquía de Dedup
L1 > L2 > L3. Perplexity aplica esta jerarquía en Consolidation & Dedup; L3 entra directo a feed_processor.py.
Punto de Convergencia Único
Las tres capas de búsqueda escriben a Notion. vantage-pipeline lee de Notion, no de outputs de capa directamente.
Figma Sync — CV Output Layer
Tipo: Capa de Materialización de CV (WriteOnly sobre lienzo Figma)
```plain text
CV-B (Markdown + figma_text_id) → ui.html (payload) → code.js (Registry V2)
→ figma.getNodeById(rawId) → node.characters = item.text → Lienzo Figma
```
Invariantes
- Figma Sync no escribe en Notion ni Tracker.
- No es capa de búsqueda.
- registry_seed.json no se edita manualmente sin regenerar desde Figma.
---
## 05 KERNEL:OWNERSHIP
División de Responsabilidades AI/Python
### 05.1 KERNEL:OWNERSHIP-001
AI Component
Procesador textual del pipeline:
- Validación de triggers
- Generación de HANDOFF
- Deduplicación textual
- Normalización
- Generación de DRY RUN
- Escritura de campos Class A
- Producción de CVs
Restricciones (no negociables)
- NO modifica campos Class B.
- NO evalúa fit estratégico.
- NO calcula scores ni estima gate decisions.
- NO ejecuta triggers fuera de 11.
### 05.2 KERNEL:OWNERSHIP-002
Python Component
Motor de lógica de negocio y escritura autónoma: único componente con permiso de escritura autónoma en Notion.
- Procesa FEED (feed_processor.py, layer_1_run.py, layer_3_mail.py).
- Calcula Score, Gate_Decision, VM_Scope, Role_Class, Match, Next_Action, Fetch, Fuente.
Excepción — Bypass
Source_Type ∈ {Inbound, Referencia, Networking} → Gate_Decision: CREATE automático (ver 09.1).
Invariante crítico
Python recalcula campos Class B en cada run — ningún valor estimado por el AI Component tiene validez en el pipeline.
---
## 06 KERNEL:DASHBOARD-CHECKLIST-ARCH
Arquitectura Dashboard/Checklist
Capa de presentación adicional sobre los datos que las capas de búsqueda producen.
1. Backend operativo real — dashboard_server.py + dashboard.db + dashboard_notion.py. Fuente de verdad del pipeline. dashboard.html consume vía fetch('http://127.0.0.1:8000/{path}').
1. Checklist operativo semanal — Checklist.html. Standalone, estado en localStorage['vchecklist_v1']. Sin backend, sin Notion.
1. Capa visual compartida — vantage-tokens.css + vantage-theme.js. Única capa realmente compartida entre (1) y (2).
Regla
Cualquier cambio a color de estado semántico o toggle de tema se hace en vantage-tokens.css / vantage-theme.js, nunca inline.
---
# II. DATOS, ESQUEMAS Y REGLAS
## 07 KERNEL:SCHEMA
Modelo de Datos y Ownership
Aclaración terminológica: "el Tracker" sin calificativo se refiere siempre a la base de datos principal donde L1/L2/L3 escriben cada vacante — distinta del Bug Tracker y Tasks Tracker (08).
### 07.1 KERNEL:SCHEMA-001
Class A vs Class B
El schema define ownership. Cada campo pertenece a exactamente un componente.
Class A — Human-Primary
AI Component escribe en CV-A · CV-B · QA · FAST · CANON-UPDATE; feed_processor.py escribe en FEED L1/L3:
- Rol · Marca · Source_Type · URL · Status · Prioridad · Holding · JD · NAD · layer · hash.
Valores operativos de Status: Target · Postulado · Rechazado · Expirada · Archivar · Repetida.
Class B — System-Primary
Python escribe: Score · Gate_Decision · VM_Scope · Role_Class · Match · Next_Action · Fetch · Fuente · Dedup_Flag.
### 07.2 KERNEL:SCHEMA-002
Restricción del Sistema
Campos Class B en JSON entrante se ignoran sin excepción — Python los calcula en el siguiente run.
### 07.3 KERNEL:SCHEMA-003
Fuente como Campo Especial
Python sobrescribe Fuente en cada run. Persistencia manual → Fuente_Manual (Class A).
### 07.4 KERNEL:SCHEMA-004
Entity Format
PREFIX:H_<hash16> / PREFIX:U_<UUID>.
Prefixes válidos: TRACKER, ARCHIVO, DRYRUN, BUG.
Namespace Ownership Contract: resolver_registry_v2.json es el único punto de verdad para entity_prefix.
Ver 03.3 (KERNEL:DOCUMENTATION-003 — L0 Runtime) para el mecanismo de resolución que consume este contrato.
### 07.5 KERNEL:SCHEMA-005
Contrato de Resolución: 4 Pasos
Lookup → Registry Mapping → Notion Query → Validation.
Ver 03.3 (KERNEL:DOCUMENTATION-003 — L0 Runtime) — este contrato es la contraparte de datos del Runtime Build descrito ahí.
### 07.6 KERNEL:SCHEMA-006
APROBAR_WRITE: Alcance
Autoriza escritura de campos Class A únicamente.
Variantes aceptadas: APROBAR_WRITE · APROBAR · SÍ · sí · YEP · yep.
Eliminados (RAI-03): Ok · Go · YES · yes.
### 07.7 KERNEL:SCHEMA-007
Acceptance Audit
Resultados: PASS / PASS WITH ARCHITECTURAL FINDING / FAIL.
Mapeo de Vocabulario — Prompts → Tracker
- source_type "career_page" → Career Page Oficial
- source_type "job_board" → Agregador
- source_name → NO escribir (Class B)
- apply_url → URL
- brand → Marca
- title → Rol
- holding → Holding (null → "Investigar")
Entry Template — Campos Class A Requeridos
Rol · Marca · URL · Source_Type · Status · Prioridad · JD · JOB_ID · Holding.
---
## 08 KERNEL:TRACKER-SCHEMA
Bug Tracker y Tasks Tracker
Distinto del Tracker de vacantes (07) — bases de datos de trabajo interno del propio VANTAGE.
### 08.1 KERNEL:TRACKER-SCHEMA-001
Alcance
- Reactivo (algo roto) → Bug Tracker
- Proactivo (trabajo/decisión pendiente) → Tasks Tracker
| Tracker | DB ID | COL ID |
| --- | --- | --- |
| Bug Tracker | 36e938be-fc42-81bd-9e1f-dc360b3b45f5 | 36e938be-fc42-81f8-8c6f-000b6769ba03 |
| Tasks Tracker | d2a65ca1-6a35-465d-bcff-b0d82dddd549 | — |
> [TAREA 4 aplicada] DB ID y COL ID de Bug Tracker invertidos respecto a la versión anterior del Kernel — corregidos en esta pasada.
### 08.2 KERNEL:TRACKER-SCHEMA-002
Niveles de Prioridad
| Nivel | Criterio |
| --- | --- |
| CRÍTICO | El flujo punta a punta no puede completarse |
| ALTO | El flujo se completa forzando el sistema (workaround requerido) |
| MEDIO | Sin resolución en la semana, el flujo se verá comprometido |
| BAJO | No bloquea operación — nice-to-have |
---
## 09 KERNEL:GATE-DECISION
Lógica de Gate Decision
Con Class A/B (07) y OWNERSHIP (05) ya definidos, esta sección describe la lógica que decide, para cada vacante, si avanza, se bloquea o se descarta.
### 09.1 KERNEL:GATE-DECISION-001
Bypass
Source_Type ∈ {Inbound, Referencia, Networking} → Gate_Decision: CREATE automático.
Bypasses: URL_GATE + Score threshold + Visual Signal detection.
### 09.2 KERNEL:GATE-DECISION-002
Lógica Estándar
Orden:
1. URL_GATE (link muerto → Score=0, Status=Expirada)
1. Score (0–100)
1. Gate_Decision (≥60 CREATE · 40–59 Para Revisar · <40 BLOCKED/Archivar).
### 09.3 KERNEL:GATE-DECISION-003
Resolución de REVIEW_NEEDED
Gap GAP-03 documentado: escritura directa vía MCP no tiene guard equivalente al de feed_processor.py.
Mitigación interina: whitelist de campos Class A en DRY RUN.
Disparador de resolución: Status = "Target".
### 09.4 KERNEL:GATE-DECISION-004
Por Qué los Gates Son Deterministas
Un gate que puede sobreescribirse manualmente no es un gate — es una sugerencia.
### 09.5 KERNEL:GATE-DECISION-005
Flujo de Recuperación BLOCKED
RT-1 permite corregir campos Class A y re-validar con Python.
RT-1 no sobreescribe el gate.
### 09.6 KERNEL:GATE-DECISION-006
REJECTED (Post-Aplicación)
REJECTED es Class B derivado de Status = "Rechazado" (Class A).
Python traduce vía evaluate_rejection_status().
El operador nunca escribe Gate_Decision directamente.
> [Corrección aplicada] Este ID ya existía en el cuerpo del Kernel pero faltaba en la TOC — agregado como sub-ítem de 09.
### 09.7 KERNEL:GATE-DECISION-007
Ejecución Automática de Archivado
Next_Action='Archivar' Y Dedup_Flag='Posible duplicado' (ambos Class B) → archivado automático vía auto_archive.py.
Dry-run obligatorio antes de execute.
### 09.8 KERNEL:GATE-DECISION-008
Capas de Evaluación de Gate: Técnica vs. Negocio
gate() (capa técnica, CREATE/BLOCKED puro) vs. gate_logic() (capa de negocio/workflow, protege estados terminales).
### 09.9 KERNEL:GATE-DECISION-009
Escalamiento de Pendientes a Tickets
Regla de escalamiento (3 niveles):
Nivel 1 — Bajo esfuerzo / sin evidencia de bloqueo
- Condición: Pendiente con esfuerzo estimado bajo (referencia orientativa: <5 iteraciones) y sin evidencia de bloqueo.
- Acción: Se mantiene registrado en Handoff y/o pending_summary del Ledger.
- Resultado: No dispara ticket.
Nivel 2 — Alto esfuerzo / sin evidencia dura
- Condición: Pendiente con esfuerzo estimado alto (referencia orientativa: ≥5 iteraciones) pero sin evidencia confirmada de bloqueo o degradación operativa.
- Acción:
- Claude sugiere la creación de ticket (Bug o Task Tracker, según corresponda).
- Espera APROBAR_WRITE explícito del operador.
- Si el operador no confirma, el pendiente permanece en Nivel 1 (Handoff/Ledger).
- No se re-intenta la sugerencia en la misma sesión salvo que el operador la reactive.
- Resultado: Ticket solo con autorización.
Nivel 3 — Bloqueo o degradación confirmada por fuente dura
- Condición: El carácter bloqueante o degradante está confirmado por una fuente dura:
- Dump de Terminal (--bootstrap/--sync).
- Ledger.
- Changelog.
- Declaración directa del operador en la sesión.
- Acción: Se dispara automáticamente la skill vantage-create-bug-task sin esperar confirmación.
- Restricción crítica:
- Inferencias de Claude (ej: "parece bloqueante") nunca califican para Nivel 3.
- Si Claude sospecha bloqueo pero no tiene fuente dura, el caso baja a Nivel 2 (sugerencia + confirmación).
- Prohibido por SP:CONSISTENCY 05: Automatismos basados en inferencias no confirmadas.
Resolución de los 3 puntos de fricción identificados
| Punto | Solución |
| --- | --- |
| Umbral de iteraciones | Criterio orientativo para Nivel 1 vs Nivel 2. Nunca criterio único para Nivel 3. El único criterio duro para Nivel 3 es: "bloqueante/degradante confirmado por fuente dura". |
| Re-evaluación Nivel 2 → Nivel 3 | Si durante la sesión aparece evidencia dura de que un pendiente Nivel 2 es bloqueante/degradante, Claude re-clasifica explícitamente a Nivel 3, lo declara al operador ("Reclasifico X de Nivel 2 a Nivel 3 por [evidencia]") y dispara el ticket automático. |
| Choque con SP:CONSISTENCY 05 | Resuelto por diseño: Nivel 3 requiere fuente dura preexistente. Las inferencias on-the-fly de Claude no activan Nivel 3. |
Referencia cruzada Manual: Ver MANUAL:SESSION-CYCLE — Ciclo de Sesión para la implementación práctica de este escalamiento dentro del flujo operador.
### 09.10 KERNEL:GATE-DECISION-010
Definición de Estados Terminales Protegidos
Contrato de terminalidad (doble criterio). Fuente de verdad ejecutable: gate_logic.py (constantes de módulo).
Criterios (orden de evaluación obligatorio)
1. Status → STATUS_TERMINAL_MAP (prioridad)
- "Postulado" → protege como APPLIED
- "Rechazado" → protege como REJECTED
1. Next_Action → TERMINAL_ACTIONS
- "Archivar" · "Expirada"
1. Si ninguno aplica → None (registro elegible para recálculo por gate())
Invariantes
- gate_logic() se invoca antes de gate() en todo pipeline ordinario y backfill (layer_1_run.py Fase 4).
- Un registro terminal no puede ser sobreescrito por recálculo de Score/Gate, aunque cambien campos Class A.
- RT-1 (/accept): la escritura de Class A corregido debe limpiar atómicamente Next_Action y Gate_Decision (select: null) en el mismo write, para que el siguiente run no trate la vacante recuperada como terminal fantasma.
- Protección estrecha: solo los valores listados arriba. Cualquier otro Next_Action (Follow-up, Re-check, etc.) es recalculable — coherente con KERNEL:OWNERSHIP-002.
Referencias
- Implementación: Layer_1/scripts/gate_logic.py, Layer_1/scripts/layer_1_run.py
- Atomicidad RT-1: Dashboard/scripts/dashboard_routes.py (/accept), dashboard_notion.py
- Contratos relacionados: KERNEL:GATE-DECISION-005, KERNEL:GATE-DECISION-006, KERNEL:GATE-DECISION-008, KERNEL:OWNERSHIP-002
### 09.11 KERNEL:GATE-DECISION-011
Matriz de Transición de Estados (Referencia Técnica)
Vista tabular consolidada de todas las reglas Gate (09.1–09.10).
Referencia canónica para scripts y auditorías — no reemplaza la descripción en prosa de cada sección; la complementa con indexación de estados.
| Estado Origen | Evento / Trigger | Guard / Regla | Estado Destino | Componente | Efecto Class B |
| --- | --- | --- | --- | --- | --- |
| [ENTRY] | feed_processor.py ingesta JSON | Source_Type ∈ {Inbound, Referencia, Networking} | READY_TO_APPLY | Python | Gate_Decision=CREATE, Score=bypass |
| [ENTRY] | feed_processor.py ingesta JSON | URL viva + Score ≥ 60 + Status=Target | READY_TO_APPLY | Python | Gate_Decision=CREATE, Score, VM_Scope, Role_Class, Next_Action |
| [ENTRY] | feed_processor.py ingesta JSON | URL muerta OR Score < 60 | BLOCKED | Python | Gate_Decision=BLOCKED, Score=0 (si URL muerta) |
| [ENTRY] | feed_processor.py ingesta JSON | Dedup match en ventana 30d | REJECTED_DUPLICATE | Python | Dedup_Flag=True, Next_Action=Descartar |
| BLOCKED | vd — Dashboard RT-1 edita Class A | Patch válido → run_pipeline.py --dry PASS | PATCHED | Humano + Python | Score, Gate_Decision recalculados |
| PATCHED | Operador acepta patch en Dashboard | Aceptar → vantage_pipeline.sh | READY_TO_APPLY OR BLOCKED | Python | Gate_Decision re-evaluado; si falla → regresa BLOCKED |
| PATCHED | Operador rechaza patch en Dashboard | Rechazar | BLOCKED | Humano | Sin cambio en SSOT |
| REVIEW_NEEDED | Operador edita Notion directo + Status→Target | vantage_pipeline.sh evalúa Class B por primera vez | READY_TO_APPLY OR BLOCKED | Humano + Python | Score, Gate_Decision, Next_Action calculados |
| READY_TO_APPLY | Operador inicia postulación | Status→Postulando | APPLYING | Humano | Status (Class A) |
| APPLYING | Confirmación de envío | Status→Postulado | APPLIED | Humano | Status (Class A) |
| APPLIED | Resultado negativo | Status→Rechazado | REJECTED | Humano | Status (Class A) — terminal, protegido por gate_logic() |
| READY_TO_APPLY / BLOCKED | URL_GATE detecta URL muerta en re-run | Score=0 + Gate_Decision=BLOCKED | BLOCKED | Python | Score, Gate_Decision |
| Cualquier no-terminal | gate_logic() evalúa estado terminal existente | Status ∈ {Postulado, Rechazado, Expirada} | Estado preservado | Python | Sin escritura — gate_logic() bloquea re-evaluación |
Nota de orden de precedencia (Hallazgo 2 — auditoría arquitectónica)
gate_logic() debe ejecutarse ANTES que gate() como filtro de mutabilidad.
Si Status ∈ {Postulado, Rechazado, Expirada} → pipeline termina aquí, sin invocar gate(). Previene regresión de estado en terminales.
→ Referencia cruzada: KERNEL:GATE-DECISION-010 (terminalidad), KERNEL:GATE-DECISION-005 (RT-1).
---
## 10 KERNEL:CV-GOLDEN-RULES
Golden Rules — Límites de Ejecución
Restricciones de arquitectura formales, no preferencias. Cada violación genera respuesta estandarizada de rechazo.
### 10.1 KERNEL:CV-GOLDEN-RULES-001
Regla #1 — No Evaluar Fit Antes de Escribir
Excepción: CV-A extrae keywords/gaps técnicos, no es evaluación de fit.
### 10.2 KERNEL:CV-GOLDEN-RULES-002
Regla #2 — No Calcular ni Estimar Campos Class B
Campos protegidos: Score · VM_Scope · Role_Class · Match · Gate_Decision · Next_Action · Fetch · Fuente · JD_Quality · Dedup_Flag.
### 10.3 KERNEL:CV-GOLDEN-RULES-003
Regla #3 — No Cuestionar la Calidad de Datos del Usuario
Sin sugerencias, sin recomendaciones de fuentes alternativas.
### 10.4 KERNEL:CV-GOLDEN-RULES-004
Regla #4 — No Delegar Escritura al Usuario
Excepciones: export PDF, upload a Google Drive.
### 10.5 KERNEL:CV-GOLDEN-RULES-005
Regla #5 — No Interpretar en SYNC
Datos puros, sin análisis de tendencias.
Template Universal de Rechazo
```plain text
OPERACIÓN RECHAZADA — Violación Regla de Oro #[N]
Tu solicitud: [descripción exacta]
Razón: [qué regla viola y por qué existe la restricción]
Alternativa operativa: [pasos concretos dentro del sistema]
¿Proceder? Escribe SÍ o CANCELAR
```
---
# III. EJECUCIÓN
## 11 KERNEL:TRIGGERS
Contratos de Ejecución del AI Component
Cada trigger define un contrato de input, proceso y output. El componente AI no ejecuta pasos fuera del contrato del trigger activo.
> [TAREA 2 aplicada] Esta sección tenía residuos de exportación (
, backslashes de escape, <empty-block/> sueltos) en el Kernel anterior — normalizados a Markdown estándar en toda esta sección.
### 11.1 KERNEL:TRIGGER-001
FEED
Procesamiento por Lotes. FEED con más de 10 vacantes se divide en lotes de 10, secuencial, con header de lote. Sin reintento automático por lote — ante fallo parcial, reportar y esperar instrucción.
Proceso
validación de longitud → header de lote → mapeo de vocabulario (07.7) → detección de señales de advertencia → filtrado de campos prohibidos → escritura secuencial.
Restricciones
- NO escribir campos Class B.
- NO reparar URLs rotas.
- NO procesar lote N+1 si lote N falló.
### 11.2 KERNEL:TRIGGER-002
VL1
Comandos de mantenimiento del Tracker — no son triggers del AI Component, son comandos Python autónomos. Ningún comando VL1 escribe campos Class B.
- VL1 backfill — escribe layer, hash, Prioridad (Class A) en registros vacíos.
- VL1 batch — modifica Status (Class A) en batch. Guardia: ausencia de execute hace el comando permanentemente read-only; nunca usa input() interactivo.
### 11.3 KERNEL:TRIGGER-003
QA
Validación de Formato de CV Exportado. No evalúa fit, oportunidad, score ni conveniencia de aplicar.
Checklist Canónico de 6 ítems
- identidad y contacto
- estructura de secciones
- orden de experiencia (C01→C05)
- completitud de contenido
- integridad visual
- consistencia de exportación
Output: GO/NO-GO por ítem; cualquier FAIL → NO-GO final.
### 11.4 KERNEL:TRIGGER-004
DRY RUN
Preview Obligatorio de Escritura. No hay escritura sin DRY RUN previo.
Campos Permitidos (Class A)
Op · Empresa · Rol · URL · Source_Type · Prioridad · Status.
Campos Prohibidos (Class B)
Visual Signal · Innovation DNA · Score Estimado · Gate_Decision · Decisión CREATE/BLOCKED.
Autorización: una de las variantes válidas de APROBAR_WRITE (07.6).
### 11.5 KERNEL:TRIGGER-005
SYNC
Reporte de Estado del Tracker. Datos puros, sin interpretación.
Output (≤12 líneas)
```plain text
SYNC REPORT — [FECHA]
Target: X | Postulado: X | En proceso: X | Rechazado: X | Total: X
NADs OVERDUE: X
LAST WRITE: [timestamp]
```
### 11.6 KERNEL:TRIGGER-006
TOP 3 BY SCORE
Query de las 3 vacantes con mayor Score.
Campos permitidos: Marca, Rol, Score, (opcional) URL.
Sin evaluación de "cuál aplicar primero".
### 11.7 KERNEL:TRIGGER-007
NEXT ACTION
Ejecuta ~/vantage_pipeline.sh status y reporta el output exacto, sin interpretación ni resumen.
### 11.8 KERNEL:TRIGGER-008
FEED (migración)
JSON de vacantes sin trigger explícito → "El procesamiento de FEED está migrado a feed_processor.py."
Excepción FAST: array de longitud 1 + trigger FAST explícito = procesamiento normal, sin lotes.
### 11.9 KERNEL:TRIGGER-009
STATUS
Lectura del estado general del sistema. Solo lectura, no interpreta si el sistema está "sano" o "degradado" — reporta datos.
---
## 12 KERNEL:CV-PIPELINE
CV Pipeline — Arquitectura de Dos Sesiones Obligatorias
### 12.1 KERNEL:CV-PIPELINE-001
CV-A
Input
URL o JD.
Process
Extrae keywords + gaps + tono de marca.
Output
HANDOFF (JSON de 5 campos).
Cierre obligatorio
SESIÓN COMPLETADA → nueva sesión.
```json
{
  "empresa": "",
  "rol": "",
  "JD_keywords_top6": ["", "", "", "", "", ""],
  "fit_gaps": ["", ""],
  "tono_marca": "",
  "idioma": ""
}
```
Un HANDOFF incompleto no avanza a CV-B. El sistema no inventa valores para campos faltantes.
Regla de Orden de Experiencia
Cronológico descendente siempre. Orden canónico obligatorio: C01 → C02 → C03 → C04 → C05. No se modifica por Positioning Mode, relevancia ni ninguna otra variable.
### 12.2 KERNEL:CV-PIPELINE-002
CV-B
Input
HANDOFF completo + Career Canon activo.
Validation
Verificar los 5 campos del HANDOFF.
Canon check
Empresa, rol, bullets y KPIs derivados del Canon — no inventados.
Auditoría de Estructura
COUNT(figma_text_id)_SKELETON == COUNT(figma_text_id)_OUTPUT. Si no coincide, abortar y re-mapear.
Auditoría de Secuencia
Los slots de experiencia deben aparecer en secuencia canónica estricta C01→C05. Ninguna variable del HANDOFF autoriza alterarla.
Output
Markdown con Figma tags.
Post-autorización
Escribir en Notion bajo # MARKDOWN CANON ALIGNED.
Post-aplicación
Status = Postulado → Python marca APPLIED.
---
## 13 KERNEL:CANON-UPDATE
Trigger de Actualización del Career Canon
Con el pipeline de CV y su convención de nombres ya definidos, esta sección cubre el trigger que mantiene actualizada la fuente que ese pipeline extrae: el Career Canon.
No es discovery, scoring, gate decision ni evaluación de fit.
Input
Descripción explícita del cambio solicitado por el operador.
Validación previa
Identificar qué sección(es) se afectan, qué IDs canónicos impactan, si requiere versión ES/EN/ambas, si impacta CV-A/CV-B/QA/Output Contract, si la información es suficiente.
Flujo obligatorio (6 pasos)
1. Recibir descripción
1. Identificar secciones afectadas
1. Validar contra Canon activo
1. Producir DRY RUN
1. Esperar autorización
1. Producir outputs (página Notion + archivo .md)
Restricciones
- CANON-UPDATE no evalúa fit.
- No calcula score.
- No modifica campos Class B.
- No inventa KPIs/fechas/certificaciones.
- No altera figma_text_id sin instrucción explícita.
- Preserva orden C01→C05.
Cierre
```plain text
CANON-UPDATE COMPLETADO
Secciones actualizadas: [lista]
IDs impactados: [lista]
Outputs entregados: Página Notion · Archivo .md
Compatibilidad downstream: CV-A: PASS/FAIL · CV-B: PASS/FAIL · QA: PASS/FAIL
```
---
## 14 KERNEL:NAMING-CONVENTION
Convención de Nombres de Outputs
Ahora que 12 (CV-PIPELINE) y 13 (CANON-UPDATE) ya definieron qué archivos produce el sistema y cómo se mantiene su fuente, esta sección cierra el bloque de Ejecución definiendo cómo se nombran físicamente en disco.
Formato del stem
{Año}{Nombre}{Apellido}{Marca_normalizada}{Vacante_normalizada}
Reglas de normalización
- Espacios → guión bajo
- Sin acentos ni caracteres especiales
- Sin símbolos de puntuación
- Guión bajo como único separador (no CamelCase)
Ejemplo
"Gucci — VM Coordinator, LATAM (2026)" → 2026_Mauricio_Meyran_Gucci_VM_Coordinator_LATAM
Aplica a
CV-B (.md), export QA (.pdf), archivo Figma (.fig) y cualquier output futuro de una vacante específica.
El stem se fija al generar el primer entregable y se reutiliza sin variación.
No aplica a
DRY RUN archivado, artefactos de sistema (logs, backups, entity_index).
Relación con CANON:OUTPUT-CONTRACT
Contratos distintos y complementarios — Output Contract gobierna estructura interna del contenido; esta sección gobierna el nombre físico del archivo. Ninguno reemplaza al otro.
---
# IV. INFRAESTRUCTURA DE CONTEXTO
## 15 KERNEL:CONTEXT-INFRASTRUCTURE
Economía de Contexto y Rutas de Carga
### 15.1 KERNEL:CONTEXT-INFRASTRUCTURE-001
Scope
Acceso a lógica base preferente vía Terminal (lazy_loader.py).
MCP autorizado para lectura, DRY RUN y modificación documental cuando exista instrucción explícita.
Jerarquía: L1 > L2 > L3.
FEED: única vía manual es FAST (11.8).
Triaje de ejecución: Requerimientos → Triaje de costos (A: Terminal, B: MCP, C: Upload) → Confirmación. Priorizar Opción A.
### 15.2 KERNEL:CONTEXT-INFRASTRUCTURE-002
Routing
MCP autorizado cuando:
- El operador lo solicite explícitamente.
- La operación sea documental.
- Se presente DRY RUN previo.
- Exista autorización posterior vía APROBAR_WRITE.
Ruta recomendada: python lazy_loader.py --page {KERNEL_MASTER} --route {ruta}
---
## 16 KERNEL:DATA-FLOW
Flujo de Datos y Escritura
Kernel → DRY RUN → APROBAR_WRITE → Notion Write.
El componente AI consulta el Kernel para confirmar el contrato del trigger activo; produce DRY RUN (11.4); espera variante válida de APROBAR_WRITE (07.6); solo entonces escribe.
Ningún paso puede saltarse: escribir sin DRY RUN previo, o sin APROBAR_WRITE explícito, viola el contrato aunque el contenido sea correcto.
Pre-validación
Cruzar esquema contra 07 SCHEMA antes de cualquier escritura.
> [TAREA 3 aplicada] El Kernel anterior tenía un bloque Tabla de Cross-References Actualizadas (esquema §L0-XXX) pegado al final de esta sección — nota de trabajo interna de una sesión de edición previa, sin ID canónico ni función de contrato. Removido en esta pasada; el Kernel no documenta su propio proceso de edición.
---
## 17 KERNEL:EVOLUTION
Evolución del Sistema
Cambios válidos
- Cambio estructural de mercado
- Cambio en targets
- Ineficiencia probada con datos
- Violación de boundary entre capas
Cambios inválidos
- "Score se siente muy estricto"
- Ready-to-Apply vacío
- Un dead link apareció
- Frustración temporal
Comportamiento ante solicitud de cambio inválido
El AI identifica la condición, informa la razón, redirige al workflow activo. No ejecuta, no negocia.
Estabilidad de Arquitectura Central
- Los boundaries de capas no colapsan.
- Los contratos de campo Class A/B no se mezclan.
- La arquitectura de tres capas, el URL_GATE como primer filtro y la división AI/Python son invariantes del sistema.
Linaje Histórico — Preservado, No Operacional
GPT Atlas, Grok discovery, SEARCH-EXEC/SEARCH-SIGNAL, fórmulas de scoring pre-v5.0 — contexto histórico, no código activo.
---
