# V | KERNEL

## KERNEL:AUDIENCE-SCOPE
## DECLARACIÓN DE AUDIENCIA Y ALCANCE
- Audiencia: Sistemas Agente de IA.
- Alcance: Este documento es el KERNEL_RUNTIME, que contiene únicamente los contratos operativos activos para la IA. Para el documento de referencia completo, solicitar acceso al KERNEL 8.0.
</callout>
---
## TABLE OF CONTENTS
```plain text
─── I. FUNDAMENTO
  §1   KERNEL:PURPOSE
  §2   KERNEL:FAIL-PHILOSOPHY
  §3   KERNEL:DOCUMENTATION (L0)
          §3.1   DOCUMENTATION-001 - Contract
          §3.2   DOCUMENTATION-002 - Norm
          §3.3   DOCUMENTATION-003 - Architecture
          §3.4   DOCUMENTATION-004 - Bootstrap
          §3.5   DOCUMENTATION-005 - Skill Announce Convention
          §3.6   DOCUMENTATION-006 - Health-Check Tool
          §3.7   DOCUMENTATION-007 - Version-Check Tool
          §3.8   DOCUMENTATION-008 - Census-Sync Tool
          §3.9   DOCUMENTATION-009 - Session Ledger
          §3.10  DOCUMENTATION-010 - Documentation Transversal

  §4   KERNEL:ARCHITECTURE (L1, L2, L3, L4, Figma Sync)
  §5   KERNEL:OWNERSHIP
  §6   KERNEL:DASHBOARD-CHECKLIST-ARCH

─── II. DATOS, ESQUEMAS Y REGLAS
  §7   KERNEL:SCHEMA
  §8   KERNEL:TRACKER-SCHEMA
  §9   KERNEL:GATE-DECISION
          §9.1  GATE-DECISION-001 — Bypass
          §9.2  GATE-DECISION-002 — Lógica Estándar
          §9.3  GATE-DECISION-003 — REVIEW_NEEDED
          §9.4  GATE-DECISION-004 — Gates Deterministas
          §9.5  GATE-DECISION-005 — Recuperación BLOCKED
          §9.6  GATE-DECISION-006 — REJECTED
          §9.7  GATE-DECISION-007 — Archivado Automático
          §9.8  GATE-DECISION-008 — Capas Técnica vs. Negocio
          §9.9  GATE-DECISION-009 — Escalamiento de Pendientes a Tickets
  §10   KERNEL:CV-GOLDEN-RULES

─── III. EJECUCIÓN
  §11  KERNEL:TRIGGERS
  §12  KERNEL:CV-PIPELINE
  §13  KERNEL:CANON-UPDATE
  §14  KERNEL:NAMING-CONVENTION

─── IV. INFRAESTRUCTURA DE CONTEXTO
  §15  KERNEL:SCOPE / KERNEL:ROUTING
  §16  KERNEL:DATA-FLOW
  §17  KERNEL:EVOLUTION
```
---
# I. FUNDAMENTO
## §1 — KERNEL:PURPOSE
Propósito del Sistema
VANTAGE resuelve un problema de ingeniería de atención: en una búsqueda laboral sin estructura, las oportunidades de alta señal desaparecen antes de ser procesadas, mientras el tiempo se consume en vacantes de baja calidad. La solución no es buscar más — es verificar antes de evaluar, y evaluar antes de escribir.
Invariantes del Sistema
1. Una vacante no entra al pipeline sin URL válida — excepción: Bypass activo (ver §9.1).
1. Score no lo calcula el sistema de lenguaje — lo calcula Python con lógica determinista.
1. Gate decision no se sobreescribe manualmente. RT-1 permite corregir inputs Class A para que Python recalcule (ver §9.5).
1. Strategy es responsabilidad humana; processing es responsabilidad del sistema.
Qué Significa Esto para el Sistema AI: el componente AI es el procesador textual del pipeline — deduplica, normaliza, genera DRY RUN, escribe Class A en Notion, produce CVs. Evaluación de calidad estratégica y cálculo de campos Class B no son operaciones de este componente (ver §5 OWNERSHIP, §10 CV-GOLDEN-RULES). Si una tarea no está en la tabla de triggers (§11), no se ejecuta.
---
## §2 — KERNEL:FAIL-PHILOSOPHY
Filosofía de Fallo
Los fallos del sistema son señales de que el pipeline funciona correctamente. Un gate que nunca bloquea no está filtrando. La presencia de gates BLOCKED, scores en 0 y entradas EXPIRED es evidencia de que el sistema aplica sus criterios.
Qué Hace el Sistema Cuando Falla: no intenta reparar outputs. No sugiere workarounds. No escala urgencia. Reporta el estado y espera instrucción humana.
Excepción — Gate = BLOCKED recuperable vía RT-1: el AI informa la opción pero no la ejecuta sin instrucción explícita.
---
## §3 — KERNEL:DOCUMENTATION (L0)
Acceso y Manejo de Información (ReadOnly)
### §3.1 — KERNEL:DOCUMENTATION-001
### Canonical Document ID Contract
Invariantes del Contrato
- Formato Único: [PREFIX]:[KEY] (ej. MANUAL:SETUP).
- Prefix Ownership: Cada prefijo mapea a una única página canónica en Notion.
- SSOT: resolver_registry_v2.json es la autoridad única para resolver Prefijos a UUIDs.
- Resolución Determinista: El Resolver (v1.py) garantiza resolución O(1) inyectando el ID crudo al componente solicitante.
Prefijos Autorizados
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
Reglas de Migración: toda referencia a páginas del sistema que use UUIDs hardcodeados o anclas planas debe migrar a este esquema. lazy_loader.py aplica este contrato en tiempo de ejecución. DT-015 — CERRADO: normalización documental (26 ocurrencias) vía trigger NORM. 100% canónico.
---
### §3.2 — KERNEL:DOCUMENTATION-002
### Normalización Documental de IDs Legacy
- Esquema: [PREFIX]:[KEY].
- Alcance: todos los documentos fundacionales.
- Excepciones: IDs de Notion (UUIDs) en metadatos o URLs.
- Gobernanza: cambios requieren APROBAR_WRITE + entrada en Changelog.
Estado actual: normalización completada. DT-015 (26 ocurrencias) — CERRADO.
---
### §3.3 — KERNEL:DOCUMENTATION-003
### L0 — VANTAGE Runtime
Tipo: Capa de Observabilidad y Abstracción de Datos (ReadOnly)
Propósito: Provee la verdad técnica sobre Notion. Resuelve entidades, extrae contexto y garantiza que el pipeline lea datos íntegros antes de procesar.
Runtime Build — proceso determinista que genera: entity_index_v2.json, graph_v2.json, backlinks_v2.json. Consume resolver_registry_v2.json como fuente de namespace ownership — si el Registry no define el prefix de un tipo de entidad, el Build falla explícitamente. graph_layer.py construye graph_v2.json; nunca infiere namespaces ni redefine contratos.
```plain text
Notion (Source) → Runtime (Index + Resolver) → API Response → Pipeline (L1/L2/L3/CV)
```
Version Check Tool y Census como parte de L0: verify_versions.py (alias vversions) y generate_census.py (alias vcensus) son observabilidad ReadOnly sobre Notion — mismo tipo de operación que Runtime Build, aplicada a versión documental y salud del Census.
```plain text
Notion (Source) → Version Check (9 docs) / Census (ID audit) → Reporte a operador
```
---
### §3.4 — KERNEL:DOCUMENTATION-004
### L0-Bootstrap — Dynamic Governance Layer
Tipo: Capa de Sincronización de Sesión (Fetch-on-Start)
Propósito: Elimina el drift de versiones entre la UI estática del agente y el repositorio dinámico de Notion.
Bootstrap Protocol: ante el primer mensaje del operador, el AI Component suspende el procesamiento de datos y ejecuta fetch de SP:BOOTSTRAP-001 y del ID CENSUS. El resultado sobreescribe cualquier instrucción estática previa. Si el Bootstrap falla, reportar "MODO DEGRADADO" y no proceder con triggers operativos.
Convención de estado (X-ING → X-ED): el Bootstrap declara inicio con BOOTLOADING... y cierre con BOOTLOADED: DOCUMENTOS CARGADOS.
Distinción de alcance — Bootstrap vs. Session Ledger: el Bootstrap corre en cada mensaje inicial de cualquier conversación del proyecto — carga de contexto universal, no registro de sesión formal. El Session Ledger (§3.9) es opt-in: solo se escribe cuando el operador invoca vantage-session-open.
```plain text
Sesión Iniciada → BOOTLOADING... → AI Fetch (Bootstrap IDs) → Sincronización de Verdad Operativa
→ BOOTLOADED: DOCUMENTOS CARGADOS → Procesamiento Petición
(Ledger: solo si el operador invoca vantage-session-open)
```
---
### §3.5 — KERNEL:DOCUMENTATION-005
### Convención de Anuncio de Skills
Todo skill de VANTAGE declara inicio y cierre de su protocolo con un verbo propio en gerundio/participio, nunca con un mensaje genérico compartido ni con el lenguaje de cierre del Bootstrap universal (BOOTLOADED).
Implementación actual:
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
### §3.6 — KERNEL:DOCUMENTATION-006
### Contrato de health_check.py
Naturaleza: lectura estricta por defecto. Única excepción: auto-sync condicional del Entity Index.
Checks ejecutados (orden fijo): version → env → git → vgit → notion → docs_sync → vdoc → index_age → pending_tickets.
Entity Index Auto-Sync: umbral 24h sobre graph_v2.json/entity_index_v2.json. Acción: subprocess a python3 vantage.py sync, timeout 120s. Clasificación: housekeeping de rutina, no remediación de fallo.
Reporte de Tickets: agrupación por Prioridad (CRÍTICO/ALTO/MEDIO/BAJO) sobre Bug Tracker y Task Tracker. Detalle explícito solo para CRÍTICO y ALTO.
---
### §3.7 — KERNEL:DOCUMENTATION-007
Propósito: ruta de bajo costo para verificar y sincronizar la Versión de los 9 documentos fundacionales sin pagar el costo de un fetch completo por documento.
Modos: --sync (único modo de escritura y verificación real, relee cada documento post-escritura) y --bootstrap (dump read-only de apertura de sesión). Modo Check eliminado en v9.6.2 — la verificación real vive íntegramente en --sync.
Alias: vversions — acepta --bootstrap o --sync, sin modo default.
---
### §3.8 — KERNEL:DOCUMENTATION-008
### Sincronización Obligatoria del ID Census
El V-ID-CENSUS es el noveno documento fundacional, derivado — su fuente de verdad son los IDs reales de los otros ocho documentos.
- Regla 1 [CENSUS-SYNC-R1]: ningún ticket que implique cambio de estado de un ID se marca Done sin Census regenerado. Si no puede ejecutarse, el ticket queda Blocked-Census.
- Regla 2: generate_census.py detecta IDs huérfanos y los reporta antes de cerrar el ticket asociado.
- Regla 3: el Census se regenera antes de que el Changelog registre el batch.
- Regla 4: ninguna sesión con cambios cierra sin DRY RUN automático de lo modificado.
- Regla 5: health_check.py reporta antigüedad del Census (umbral 7 días) como advertencia informativa, no bloqueante.
---
### §3.9 — KERNEL:DOCUMENTATION-009
### Session Ledger
Naturaleza: excepción de escritura de housekeeping — no requiere APROBAR_WRITE.
Estructura: database Notion (data_source_id 8d736032-eef9-4e6e-a05a-df8b8079ebff) con session_id, status (OPEN/CLOSED), opened_at, pending_summary.
Escritura autorizada: solo SKILL-OPEN paso 0 (→ OPEN) y SKILL-CLOSE paso 6 (→ CLOSED + pending_summary).
---
### §3.10 — KERNEL:DOCUMENTATION-010
### Documentación Transversal — Contrato de Integridad Documental
Protocolo (seis fases): Mapeo → DRY RUN → Inyección → Write-Back Verification → Changelog + versión → Binary Gate de salida.
Skills de Gobernanza Documental:
| Skill | Propósito | Gate |
| --- | --- | --- |
| vantage-create-bug-task | Crear tickets en Bug Tracker | ✅ Obligatorio |
| vantage-present-handoff | Resumen COMPLETADO/PENDIENTE | ❌ No aplica |
| vantage-tidy-changelog | Append + edición de Change Log | ✅ Obligatorio |
| vantage-tidy-bug-task-tracker | Limpieza de campos/normalización | ✅ Obligatorio |
| vantage-tidy-opportunities-tracker | Duplicados/normalización Class A | ✅ Obligatorio |
---
---
## §4 — KERNEL:ARCHITECTURE
Arquitectura de Cuatro Capas
### KERNEL:ARCHITECTURE-L1 — Active Recon
Trigger: humano (ciclo semanal — lunes)
```plain text
Human signal → Career Sites · LinkedIn · Aggregators (paralelo) → JSON estructurado
→ FEED → feed_processor.py → Notion (Class A) → vantage-pipeline
```
### KERNEL:ARCHITECTURE-L2 — Strategic Search
Trigger: humano (ciclo semanal — lunes)
```plain text
Human signal → Gemini · You.com · Grok (extracción paralela) → Perplexity (Consolidation & Dedup)
→ FEED → feed_processor.py → Notion (Class A) → vantage-pipeline
```
### KERNEL:ARCHITECTURE-L3 — Passive Intake
Trigger: automático (continuo)
```plain text
Gmail (.Jobs label) → layer_3_mail.py (IMAP + Groq) → Notion (Class A poblado, Class B vacío) → vantage-pipeline
```
### KERNEL:ARCHITECTURE-L4 — Version Control & Infrastructure
No es capa de búsqueda — infraestructura documental. Auto-commit + push cuando hay cambios en el repo. Alias: vgit · 09:00/15:00/21:00. Repo: github.com/mauriciomeyran/jhs-pipeline.
vsync_doc.py — sync bidireccional Notion → ACTIVE/ para los 6 fundacionales editables (Kernel, System Prompt, Career Canon, Manual, Aliases, Change Log). Alias: vdoc · Flags: dry | notion | local | auto.
Jerarquía de Dedup: L1 > L2 > L3. Perplexity aplica esta jerarquía en Consolidation & Dedup; L3 entra directo a feed_processor.py.
Punto de Convergencia Único: las tres capas de búsqueda escriben a Notion. vantage-pipeline lee de Notion, no de outputs de capa directamente.
### Figma Sync — CV Output Layer
Tipo: Capa de Materialización de CV (WriteOnly sobre lienzo Figma)
```plain text
CV-B (Markdown + figma_text_id) → ui.html (payload) → code.js (Registry V2)
→ figma.getNodeById(rawId) → node.characters = item.text → Lienzo Figma
```
Invariantes: Figma Sync no escribe en Notion ni Tracker. No es capa de búsqueda. registry_seed.json no se edita manualmente sin regenerar desde Figma.
---
## §5 — KERNEL:OWNERSHIP
División de Responsabilidades AI/Python
### KERNEL:OWNERSHIP-001 — AI Component
Procesador textual del pipeline: validación de triggers, generación de HANDOFF, deduplicación textual, normalización, generación de DRY RUN, escritura de campos Class A, producción de CVs.
Restricciones (no negociables): NO modifica campos Class B. NO evalúa fit estratégico. NO calcula scores ni estima gate decisions. NO ejecuta triggers fuera de §11.
### KERNEL:OWNERSHIP-002 — Python Component
Motor de lógica de negocio y escritura autónoma: único componente con permiso de escritura autónoma en Notion. Procesa FEED (feed_processor.py, layer_1_run.py, layer_3_mail.py). Calcula Score, Gate_Decision, VM_Scope, Role_Class, Match, Next_Action, Fetch, Fuente.
Excepción — Bypass: Source_Type ∈ {Inbound, Referencia, Networking} → Gate_Decision: CREATE automático (ver §9.1).
Invariante crítico: Python recalcula campos Class B en cada run — ningún valor estimado por el AI Component tiene validez en el pipeline.
---
## §6 — KERNEL:DASHBOARD-CHECKLIST-ARCH
Arquitectura Dashboard/Checklist
Capa de presentación adicional sobre los datos que las capas de búsqueda producen.
1. Backend operativo real — dashboard_server.py + dashboard.db + dashboard_notion.py. Fuente de verdad del pipeline. dashboard.html consume vía fetch('<http://127.0.0.1:8000>{path}').
1. Checklist operativo semanal — Checklist.html. Standalone, estado en localStorage['vchecklist_v1']. Sin backend, sin Notion.
1. Capa visual compartida — vantage-tokens.css + vantage-theme.js. Única capa realmente compartida entre (1) y (2).
Regla: cualquier cambio a color de estado semántico o toggle de tema se hace en vantage-tokens.css/vantage-theme.js, nunca inline.
---
---
# II. DATOS, ESQUEMAS Y REGLAS
## §7 — KERNEL:SCHEMA
Modelo de Datos y Ownership
Aclaración terminológica: "el Tracker" sin calificativo se refiere siempre a la base de datos principal donde L1/L2/L3 escriben cada vacante — distinta del Bug Tracker y Tasks Tracker (§8).
### KERNEL:SCHEMA-001 — Class A vs Class B
El schema define ownership. Cada campo pertenece a exactamente un componente.
Class A — Human-Primary: AI Component escribe en CV-A · CV-B · QA · FAST · CANON-UPDATE; feed_processor.py escribe en FEED L1/L3: Rol · Marca · Source_Type · URL · Status · Prioridad · Holding · JD · NAD · layer · hash.
Valores operativos de Status: Target · Postulado · Rechazado · Expirada · Archivar · Repetida.
Class B — System-Primary: Python escribe: Score · Gate_Decision · VM_Scope · Role_Class · Match · Next_Action · Fetch · Fuente · Dedup_Flag.
### KERNEL:SCHEMA-002 — Restricción del Sistema
Campos Class B en JSON entrante se ignoran sin excepción — Python los calcula en el siguiente run.
### KERNEL:SCHEMA-003 — Fuente como Campo Especial
Python sobrescribe Fuente en cada run. Persistencia manual → Fuente_Manual (Class A).
### KERNEL:SCHEMA-004 — Entity Format
PREFIX:H_<hash16> / PREFIX:U_<UUID>. Prefixes válidos: TRACKER, ARCHIVO, DRYRUN, BUG. Namespace Ownership Contract: resolver_registry_v2.json es el único punto de verdad para entity_prefix.
Ver §3.3 (KERNEL:DOCUMENTATION-003 — L0 Runtime) para el mecanismo de resolución que consume este contrato.
### KERNEL:SCHEMA-005 — Contrato de Resolución: 4 Pasos
Lookup → Registry Mapping → Notion Query → Validation.
Ver §3.3 (KERNEL:DOCUMENTATION-003 — L0 Runtime) — este contrato es la contraparte de datos del Runtime Build descrito ahí.
### KERNEL:SCHEMA-006 — APROBAR_WRITE: Alcance
Autoriza escritura de campos Class A únicamente. Variantes aceptadas: APROBAR_WRITE · APROBAR · SÍ · sí · YEP · yep. Eliminados (RAI-03): Ok · Go · YES · yes.
### KERNEL:SCHEMA-007 — Acceptance Audit
Resultados: PASS / PASS WITH ARCHITECTURAL FINDING / FAIL.
Mapeo de Vocabulario — Prompts → Tracker: source_type "career_page" → Career Page Oficial; source_type "job_board" → Agregador; source_name → NO escribir (Class B); apply_url → URL; brand → Marca; title → Rol; holding → Holding (null → "Investigar").
Entry Template — Campos Class A Requeridos: Rol · Marca · URL · Source_Type · Status · Prioridad · JD · JOB_ID · Holding.
---
## §8 — KERNEL:TRACKER-SCHEMA
Bug Tracker y Tasks Tracker
Distinto del Tracker de vacantes (§7) — bases de datos de trabajo interno del propio VANTAGE.
### KERNEL:TRACKER-SCHEMA-001 — Alcance
- Reactivo (algo roto) → Bug Tracker
- Proactivo (trabajo/decisión pendiente) → Tasks Tracker
| Tracker | DB ID | COL ID |
| --- | --- | --- |
| Bug Tracker | 36e938be-fc42-81bd-9e1f-dc360b3b45f5 | 36e938be-fc42-81f8-8c6f-000b6769ba03 |
| Tasks Tracker | d2a65ca1-6a35-465d-bcff-b0d82dddd549 | — |
> [TAREA 4 aplicada] DB ID y COL ID de Bug Tracker invertidos respecto a la versión anterior del Kernel — corregidos en esta pasada.
### KERNEL:TRACKER-SCHEMA-002 — Niveles de Prioridad
| Nivel | Criterio |
| --- | --- |
| CRÍTICO | El flujo punta a punta no puede completarse |
| ALTO | El flujo se completa forzando el sistema (workaround requerido) |
| MEDIO | Sin resolución en la semana, el flujo se verá comprometido |
| BAJO | No bloquea operación — nice-to-have |
---
## §9 — KERNEL:GATE-DECISION
Con Class A/B (§7) y OWNERSHIP (§5) ya definidos, esta sección describe la lógica que decide, para cada vacante, si avanza, se bloquea o se descarta.
### §9.1 — KERNEL:GATE-DECISION-001 — Bypass
Source_Type ∈ {Inbound, Referencia, Networking} → Gate_Decision: CREATE automático. Bypasses: URL_GATE + Score threshold + Visual Signal detection.
### §9.2 — KERNEL:GATE-DECISION-002 — Lógica Estándar
Orden: URL_GATE (link muerto → Score=0, Status=Expirada) → Score (0–100) → Gate_Decision (≥60 CREATE · 40–59 Para Revisar · <40 BLOCKED/Archivar).
### §9.3 — KERNEL:GATE-DECISION-003 — Resolución de REVIEW_NEEDED
Gap GAP-03 documentado: escritura directa vía MCP no tiene guard equivalente al de feed_processor.py. Mitigación interina: whitelist de campos Class A en DRY RUN. Disparador de resolución: Status = "Target".
### §9.4 — KERNEL:GATE-DECISION-004 — Por Qué los Gates Son Deterministas
Un gate que puede sobreescribirse manualmente no es un gate — es una sugerencia.
### §9.5 — KERNEL:GATE-DECISION-005 — Flujo de Recuperación BLOCKED
RT-1 permite corregir campos Class A y re-validar con Python. RT-1 no sobreescribe el gate.
### §9.6 — KERNEL:GATE-DECISION-006 — REJECTED (Post-Aplicación)
REJECTED es Class B derivado de Status = "Rechazado" (Class A). Python traduce vía evaluate_rejection_status(). El operador nunca escribe Gate_Decision directamente.
> [Corrección aplicada] Este ID ya existía en el cuerpo del Kernel pero faltaba en la TOC — agregado como sub-ítem de §9.
### §9.7 — KERNEL:GATE-DECISION-007 — Ejecución Automática de Archivado
Next_Action='Archivar' Y Dedup_Flag='Posible duplicado' (ambos Class B) → archivado automático vía auto_archive.py. Dry-run obligatorio antes de execute.
### §9.8 — KERNEL:GATE-DECISION-008 — Capas de Evaluación de Gate: Técnica vs. Negocio
gate() (capa técnica, CREATE/BLOCKED puro) vs. gate_logic() (capa de negocio/workflow, protege estados terminales).
---
### §9.9 — KERNEL:GATE-DECISION-009 — Escalamiento de Pendientes a Tickets
Regla de escalamiento (3 niveles):
- Condición: Pendiente con esfuerzo estimado bajo (referencia orientativa: <5 iteraciones) y sin evidencia de bloqueo.
- Acción: Se mantiene registrado en Handoff y/o pending_summary del Ledger. Ver Manual §6 para el detalle operativo de cómo y cuándo se registra este campo dentro del ciclo de sesión.
- Resultado: No dispara ticket.
---
- Condición: Pendiente con esfuerzo estimado alto (referencia orientativa: ≥5 iteraciones) pero sin evidencia confirmada de bloqueo o degradación operativa.
- Acción:
- Claude sugiere la creación de ticket (Bug o Task Tracker, según corresponda).
- Espera APROBAR_WRITE explícito del operador.
- Si el operador no confirma, el pendiente permanece en Nivel 1 (Handoff/Ledger).
- No se re-intenta la sugerencia en la misma sesión salvo que el operador la reactive.
---
- Condición: El carácter bloqueante o degradante está confirmado por una fuente dura:
- Dump de Terminal (--bootstrap/--sync).
- Ledger.
- Changelog.
- Declaración directa del operador en la sesión.
- Acción:
- Se dispara automáticamente la skill vantage-create-bug-task sin esperar confirmación.
- Restricción crítica:
- Inferencias de Claude (ej: "parece bloqueante") nunca califican para Nivel 3.
- Si Claude sospecha bloqueo pero no tiene fuente dura, el caso baja a Nivel 2 (sugerencia + confirmación).
- Prohibido por SP:CONSISTENCY §5: Automatismos basados en inferencias no confirmadas.
---
Resolución de los 3 puntos de fricción identificados:
| Punto | Solución |
| --- | --- |
| Umbral de iteraciones | Criterio orientativo para Nivel 1 vs Nivel 2. Nunca criterio único para Nivel 3. El único criterio duro para Nivel 3 es: "bloqueante/degradante confirmado por fuente dura". |
| Re-evaluación Nivel 2 → Nivel 3 | Si durante la sesión aparece evidencia dura de que un pendiente Nivel 2 es bloqueante/degradante, Claude re-clasifica explícitamente a Nivel 3, lo declara al operador ("Reclasifico X de Nivel 2 a Nivel 3 por [evidencia]" ) y dispara el ticket automático. |
| Choque con SP:CONSISTENCY §5 | Resuelto por diseño: Nivel 3 requiere fuente dura preexistente. Las inferencias on-the-fly de Claude no activan Nivel 3. |
Referencia cruzada Manual: Ver Manual §6 — Ciclo de Sesión para la implementación práctica de este escalamiento dentro del flujo operador (dónde se declara un Nivel 2, qué cuenta como fuente dura para Nivel 3, y cómo se refleja en el cierre de sesión).
---
## §10 — KERNEL:CV-GOLDEN-RULES
Golden Rules — Límites de Ejecución
Restricciones de arquitectura formales, no preferencias. Cada violación genera respuesta estandarizada de rechazo.
- Regla #1 — No Evaluar Fit Antes de Escribir. Excepción: CV-A extrae keywords/gaps técnicos, no es evaluación de fit.
- Regla #2 — No Calcular ni Estimar Campos Class B. Campos protegidos: Score · VM_Scope · Role_Class · Match · Gate_Decision · Next_Action · Fetch · Fuente · JD_Quality · Dedup_Flag.
- Regla #3 — No Cuestionar la Calidad de Datos del Usuario. Sin sugerencias, sin recomendaciones de fuentes alternativas.
- Regla #4 — No Delegar Escritura al Usuario. Excepciones: export PDF, upload a Google Drive.
- Regla #5 — No Interpretar en SYNC. Datos puros, sin análisis de tendencias.
Template Universal de Rechazo:
```plain text
OPERACIÓN RECHAZADA — Violación Regla de Oro #[N]
Tu solicitud: [descripción exacta]
Razón: [qué regla viola y por qué existe la restricción]
Alternativa operativa: [pasos concretos dentro del sistema]
¿Proceder? Escribe SÍ o CANCELAR
```
---
---
# III. EJECUCIÓN
## §11 — KERNEL:TRIGGERS
Contratos de Ejecución del AI Component
Cada trigger define un contrato de input, proceso y output. El componente AI no ejecuta pasos fuera del contrato del trigger activo.
> [TAREA 2 aplicada] Esta sección tenía residuos de exportación (
, backslashes de escape \*\*, \-\-, \[\], <empty-block/> sueltos) en el Kernel anterior — normalizados a Markdown estándar en toda esta sección.
### KERNEL:TRIGGER-001 — FEED
Procesamiento por Lotes. FEED con más de 10 vacantes se divide en lotes de 10, secuencial, con header de lote. Sin reintento automático por lote — ante fallo parcial, reportar y esperar instrucción.
Proceso: validación de longitud → header de lote → mapeo de vocabulario (§7-SCHEMA-007) → detección de señales de advertencia → filtrado de campos prohibidos → escritura secuencial.
Restricciones: NO escribir campos Class B. NO reparar URLs rotas. NO procesar lote N+1 si lote N falló.
### KERNEL:TRIGGER-002 — VL1
Comandos de mantenimiento del Tracker — no son triggers del AI Component, son comandos Python autónomos. Ningún comando VL1 escribe campos Class B.
- VL1 backfill — escribe layer, hash, Prioridad (Class A) en registros vacíos.
- VL1 batch — modifica Status (Class A) en batch. Guardia: ausencia de execute hace el comando permanentemente read-only; nunca usa input() interactivo.
### KERNEL:TRIGGER-003 — QA
Validación de Formato de CV Exportado. No evalúa fit, oportunidad, score ni conveniencia de aplicar.
Checklist Canónico de 6 ítems: identidad y contacto · estructura de secciones · orden de experiencia (C01→C05) · completitud de contenido · integridad visual · consistencia de exportación.
Output: GO/NO-GO por ítem; cualquier FAIL → NO-GO final.
### KERNEL:TRIGGER-004 — DRY RUN
Preview Obligatorio de Escritura. No hay escritura sin DRY RUN previo.
Campos Permitidos (Class A): Op · Empresa · Rol · URL · Source_Type · Prioridad · Status.
Campos Prohibidos (Class B): Visual Signal · Innovation DNA · Score Estimado · Gate_Decision · Decisión CREATE/BLOCKED.
Autorización: una de las variantes válidas de APROBAR_WRITE (§7-SCHEMA-006).
### KERNEL:TRIGGER-005 — SYNC
Reporte de Estado del Tracker. Datos puros, sin interpretación.
Output (≤12 líneas):
```plain text
SYNC REPORT — [FECHA]
Target: X | Postulado: X | En proceso: X | Rechazado: X | Total: X
NADs OVERDUE: X
LAST WRITE: [timestamp]
```
### KERNEL:TRIGGER-006 — TOP 3 BY SCORE
Query de las 3 vacantes con mayor Score. Campos permitidos: Marca, Rol, Score, (opcional) URL. Sin evaluación de "cuál aplicar primero".
### KERNEL:TRIGGER-007 — NEXT ACTION
Ejecuta ~/vantage_pipeline.sh status y reporta el output exacto, sin interpretación ni resumen.
### KERNEL:TRIGGER-008 — FEED (migración)
JSON de vacantes sin trigger explícito → "El procesamiento de FEED está migrado a feed_processor.py." Excepción FAST: array de longitud 1 + trigger FAST explícito = procesamiento normal, sin lotes.
### KERNEL:TRIGGER-009 — STATUS
Lectura del estado general del sistema. Solo lectura, no interpreta si el sistema está "sano" o "degradado" — reporta datos.
---
## §12 — KERNEL:CV-PIPELINE
CV Pipeline — Arquitectura de Dos Sesiones Obligatorias
### CV-A
Input: URL o JD. Process: extrae keywords + gaps + tono de marca. Output: HANDOFF (JSON de 5 campos). Cierre obligatorio: SESIÓN COMPLETADA → nueva sesión.
```json
{
 "empresa": "", "rol": "",
 "JD_keywords_top6": ["", "", "", "", "", ""],
 "fit_gaps": ["", ""],
 "tono_marca": "", "idioma": ""
}
```
Un HANDOFF incompleto no avanza a CV-B. El sistema no inventa valores para campos faltantes.
Regla de Orden de Experiencia: cronológico descendente siempre. Orden canónico obligatorio: C01 → C02 → C03 → C04 → C05. No se modifica por Positioning Mode, relevancia ni ninguna otra variable.
### CV-B
Input: HANDOFF completo + Career Canon activo. Validation: verificar los 5 campos del HANDOFF. Canon check: empresa, rol, bullets y KPIs derivados del Canon — no inventados.
Auditoría de Estructura: COUNT(figma_text_id)_SKELETON == COUNT(figma_text_id)_OUTPUT. Si no coincide, abortar y re-mapear.
Auditoría de Secuencia: los slots de experiencia deben aparecer en secuencia canónica estricta C01→C05. Ninguna variable del HANDOFF autoriza alterarla.
Output: Markdown con Figma tags. Post-autorización: escribir en Notion bajo # MARKDOWN CANON ALIGNED. Post-aplicación: Status = Postulado → Python marca APPLIED.
---
## §13 — KERNEL:CANON-UPDATE
Con el pipeline de CV y su convención de nombres ya definidos, esta sección cubre el trigger que mantiene actualizada la fuente que ese pipeline extrae: el Career Canon. No es discovery, scoring, gate decision ni evaluación de fit.
Input: descripción explícita del cambio solicitado por el operador.
Validación previa: identificar qué sección(es) se afectan, qué IDs canónicos impactan, si requiere versión ES/EN/ambas, si impacta CV-A/CV-B/QA/Output Contract, si la información es suficiente.
Flujo obligatorio (6 pasos): recibir descripción → identificar secciones afectadas → validar contra Canon activo → producir DRY RUN → esperar autorización → producir outputs (página Notion + archivo .md).
Restricciones: CANON-UPDATE no evalúa fit, no calcula score, no modifica campos Class B, no inventa KPIs/fechas/certificaciones, no altera figma_text_id sin instrucción explícita, preserva orden C01→C05.
Cierre:
```plain text
CANON-UPDATE COMPLETADO
Secciones actualizadas: [lista]
IDs impactados: [lista]
Outputs entregados: Página Notion · Archivo .md
Compatibilidad downstream: CV-A: PASS/FAIL · CV-B: PASS/FAIL · QA: PASS/FAIL
```
---
## §14 — KERNEL:NAMING-CONVENTION
Convención de Nombres de Outputs
Ahora que §12 (CV-PIPELINE) y §13 (CANON-UPDATE) ya definieron qué archivos produce el sistema y cómo se mantiene su fuente, esta sección cierra el bloque de Ejecución definiendo cómo se nombran físicamente en disco.
Formato del stem: {Año}_{Nombre}_{Apellido}_{Marca_normalizada}_{Vacante_normalizada}
Reglas de normalización: espacios → guión bajo; sin acentos ni caracteres especiales; sin símbolos de puntuación; guión bajo como único separador (no CamelCase).
Ejemplo: "Gucci — VM Coordinator, LATAM (2026)" → 2026_Mauricio_Meyran_Gucci_VM_Coordinator_LATAM
Aplica a: CV-B (.md), export QA (.pdf), archivo Figma (.fig) y cualquier output futuro de una vacante específica. El stem se fija al generar el primer entregable y se reutiliza sin variación.
No aplica a: DRY RUN archivado, artefactos de sistema (logs, backups, entity_index).
Relación con CANON:OUTPUT-CONTRACT-001: contratos distintos y complementarios — Output Contract gobierna estructura interna del contenido; esta sección gobierna el nombre físico del archivo. Ninguno reemplaza al otro.
---
---
# IV. INFRAESTRUCTURA DE CONTEXTO
## §15 — KERNEL:SCOPE / KERNEL:ROUTING
Economía de Contexto y Rutas de Carga
Fusión narrativa de dos secciones parcialmente redundantes; ambos IDs se conservan como anclas.
### KERNEL:SCOPE — Principio General
Acceso a lógica base preferente vía Terminal (lazy_loader.py). MCP autorizado para lectura, DRY RUN y modificación documental cuando exista instrucción explícita. Jerarquía: L1 > L2 > L3. FEED: única vía manual es FAST (§11-TRIGGER-008). Triaje de ejecución: Requerimientos → Triaje de costos (A: Terminal, B: MCP, C: Upload) → Confirmación. Priorizar Opción A.
### KERNEL:ROUTING — Mecanismo Técnico de las Rutas MCP
MCP autorizado cuando: el operador lo solicite explícitamente, la operación sea documental, se presente DRY RUN previo, exista autorización posterior vía APROBAR_WRITE.
Ruta recomendada: python lazy_loader.py --page {KERNEL_MASTER} --route {ruta}
---
## §16 — KERNEL:DATA-FLOW
Flujo de Datos y Escritura
Kernel → DRY RUN → APROBAR_WRITE → Notion Write. El componente AI consulta el Kernel para confirmar el contrato del trigger activo; produce DRY RUN (§11-TRIGGER-004); espera variante válida de APROBAR_WRITE (§7-SCHEMA-006); solo entonces escribe.
Ningún paso puede saltarse: escribir sin DRY RUN previo, o sin APROBAR_WRITE explícito, viola el contrato aunque el contenido sea correcto.
Pre-validación: cruzar esquema contra §7 SCHEMA antes de cualquier escritura.
> [TAREA 3 aplicada] El Kernel anterior tenía un bloque Tabla de Cross-References Actualizadas (esquema §L0-XXX) pegado al final de esta sección — nota de trabajo interna de una sesión de edición previa, sin ID canónico ni función de contrato. Removido en esta pasada; el Kernel no documenta su propio proceso de edición.
---
## §17 — KERNEL:EVOLUTION
Evolución del Sistema
Cambios válidos: cambio estructural de mercado, cambio en targets, ineficiencia probada con datos, violación de boundary entre capas.
Cambios inválidos: "Score se siente muy estricto", Ready-to-Apply vacío, un dead link apareció, frustración temporal.
Comportamiento ante solicitud de cambio inválido: el AI identifica la condición, informa la razón, redirige al workflow activo. No ejecuta, no negocia.
Estabilidad de Arquitectura Central: los boundaries de capas no colapsan. Los contratos de campo Class A/B no se mezclan. La arquitectura de tres capas, el URL_GATE como primer filtro y la división AI/Python son invariantes del sistema.
Linaje Histórico — Preservado, No Operacional: GPT Atlas, Grok discovery, SEARCH-EXEC/SEARCH-SIGNAL, fórmulas de scoring pre-v5.0 — contexto histórico, no código activo.
---
---
