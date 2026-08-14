# V | KERNEL


Propósito del Sistema
VANTAGE resuelve un problema de ingeniería de atención: en una búsqueda laboral sin estructura, las oportunidades de alta señal desaparecen antes de ser procesadas, mientras el tiempo se consume en vacantes de baja calidad.
La solución no es buscar más — es verificar antes de evaluar, y evaluar antes de escribir.
Invariantes del Sistema
1. Una vacante no entra al pipeline sin URL válida — excepción: Bypass activo (ver 09.1).
1. Score no lo calcula el sistema de lenguaje — lo calcula Python con lógica determinista.
1. Gate decision no se sobreescribe manualmente. RT-1 permite corregir inputs Class A para que Python recalcule (ver 09.5).
1. Strategy es responsabilidad humana; processing es responsabilidad del sistema.
Qué significa esto para el Sistema AI
El componente AI es el procesador textual del pipeline:
Filosofía de Fallo
Los fallos del sistema son señales de que el pipeline funciona correctamente. Un gate que nunca bloquea no está filtrando. La presencia de gates BLOCKED, scores en 0 y entradas EXPIRED es evidencia de que el sistema aplica sus criterios.
Qué hace el Sistema cuando falla
- No sugiere workarounds.
- No escala urgencia.
Excepción — Gate BLOCKED Recuperable vía RT-1
El AI informa la opción pero no la ejecuta sin instrucción explícita.
Documentación y Gobernanza (L0)
Canonical Document ID Contract
Bootstrap Protocol
Ante el primer mensaje del operador, el AI Component suspende el procesamiento de datos y ejecuta fetch de SP:BOOTSTRAP-001 y del ID CENSUS. El resultado sobreescribe cualquier instrucción estática previa. Si el Bootstrap falla, reportar "MODO DEGRADADO" y no proceder con triggers operativos.
El Bootstrap corre en cada mensaje inicial de cualquier conversación del proyecto — carga de contexto universal, no registro de sesión formal. El Session Ledger (03.9) es opt-in: solo se escribe cuando el operador invoca vantage-session-open.
Convención de Anuncio de Skills
Todo skill de VANTAGE declara inicio y cierre de su protocolo con un verbo propio en gerundio/participio, nunca con un mensaje genérico compartido ni con el lenguaje de cierre del Bootstrap universal (BOOTLOADED).
Implementación actual
Contrato de health_check.py
Naturaleza: lectura estricta por defecto. Única excepción: auto-sync condicional del Entity Index.
Checks ejecutados (orden fijo)
version → env → git → vgit → notion → docs_sync → vdoc → index_age → pending_tickets.
Entity Index Auto-Sync
Umbral 24h sobre graph_v2.json / entity_index_v2.json. Acción: subprocess a python3 vantage.py sync, timeout 120s. Clasificación: housekeeping de rutina, no remediación de fallo.
Reporte de Tickets
Agrupación por Prioridad (CRÍTICO / ALTO / MEDIO / BAJO) sobre Bug Tracker y Task Tracker. Detalle explícito solo para CRÍTICO y ALTO.
Herramienta de Verificación de Versión
Propósito: ruta de bajo costo para verificar y sincronizar la Versión de los 10 documentos fundacionales sin pagar el costo de un fetch completo por documento.
- --bootstrap (dump read-only de apertura de sesión)
- --scripts (gap report read-only: cruza scripts .py/.sh del árbol activo contra SCRIPT LIBRARY en Notion)
- --skills (gap report read-only: cruza archivos .skill del árbol activo contra SKILL LIBRARY en Notion)
- --length (Sanity check de integridad estructural, read-only, exit code 1 si ATENCIÓN REQUERIDA)
- --update-baseline (Actualiza length_baseline.json, requiere --length + confirmación explícita del operador)
- Alcance: Aplica a los 10 documentos fundacionales (CHANGELOG, KERNEL, MANUAL, CANON, SP, ALIASES, CENSUS, BRIEF, VANTAGE y CHANGELOG_ARCHIVO).
- Métrica: Conteo de bloques con texto extraíble no vacío (paragraph, headings, list_item, toggle, quote, callout, code, table_row), excluyendo bloques estructurales (divider, table_of_contents, column_list, column) y bloques vacíos.
- Salida:
- Veredicto por documento: PASS o ATENCIÓN REQUERIDA.
Archivos asociados:
Flags de ejecución (vversions):
Sincronización Obligatoria del ID Census
El V-ID-CENSUS es el noveno documento fundacional, derivado — su fuente de verdad son los IDs reales de los otros ocho documentos.
Reglas
1. [CENSUS-SYNC-R1]: ningún ticket que implique cambio de estado de un ID se marca Done sin Census regenerado. Si no puede ejecutarse, el ticket queda Blocked-Census.
1. generate_census.py detecta IDs huérfanos y los reporta antes de cerrar el ticket asociado.
1. El Census se regenera antes de que el Changelog registre el batch.
1. Ninguna sesión con cambios cierra sin DRY RUN automático de lo modificado.
1. health_check.py reporta antigüedad del Census (umbral 7 días) como advertencia informativa, no bloqueante.
Session Ledger
Naturaleza: excepción de escritura de housekeeping — no requiere APROBAR_WRITE.
Estructura
Database Notion (data_source_id 8d736032-eef9-4e6e-a05a-df8b8079ebff) con:
- session_id
Escritura autorizada
Solo SKILL-OPEN paso 0 (→ OPEN) y SKILL-CLOSE paso 6 (→ CLOSED + pending_summary).
Documentación Transversal — Contrato de Integridad Documental
Mapeo → DRY RUN → Inyección → Write-Back Verification → Changelog + versión → Binary Gate de salida.
Skills de Gobernanza Documental
Sistema de Cross-Reference Hyperlinks
Propósito: convertir cada mención de un ID canónico (PREFIX:KEY) en los 6 documentos fundamentales en un hipervínculo real al bloque de definición, en vez de texto plano — para que el sistema sea navegable y auditable, no solo nombrado.
Piezas
Regla permanente
El heading de definición nunca se auto-enlaza a sí mismo; toda mención posterior (TOC, prosa, tablas de referencia) sí es clickeable.
Estado de adopción (2026-08-01)
Ver MANUAL:HEALTHCHECK para el procedimiento operativo de cuándo correr cada script.
Notebook Gemini — Auditor Documental Externo
Tipo: Capa de Consulta ReadOnly externa (Google Gemini, ventana de contexto sin límite de tokens equivalente), complementaria al fetch nativo de Claude sobre el corpus fundacional — no es un script ni un alias de Terminal.
Contrato de Cero Inferencia Silenciosa
Consulta puntual de triaje/verificación documental (detección de drifts entre documentos) cuando no se requiere fetch estructural ni escritura en Notion — evita consumir fetch/tokens de Claude en preguntas de bajo riesgo.
Arquitectura de Cuatro Capas
Active Recon
Trigger: humano (ciclo semanal — lunes)
Objetivo: maximizar cobertura y trazabilidad de entrada — no decide prioridad estratégica, solo captura oportunidades de alta señal antes de que se evaporen.
Componentes: Career Sites · LinkedIn · Aggregators — wrappers especializados por fuente, convergiendo a un schema común. Herramienta de soporte: Weekly Prompt Assembler (weekly_prompt_assembler.py, alias vassemble) — materializa en disco los 7 prompts semanales por motor desde la PROMPT LIBRARY, reemplazando el ensamblado anterior vía agente dentro de Perplexity Desktop (ver ALIASES:L1L2-DISCOVERY).
Responsabilidades: buscar vacantes, validar evidencia mínima, extraer campos canónicos, mantener trazabilidad por fuente, emitir resultados estructurados (no recomendaciones).
Campos inmutables: los campos Class A emitidos por cada wrapper (ver KERNEL:SCHEMA-001) no se reinterpretan en L1 — feed_processor.py normaliza formato, no criterio.
Reglas de dedup: L1 no deduplica — la jerarquía L1>L2>L3 y el punto de convergencia único viven en KERNEL:ARCHITECTURE-L4.
Estados de error: fuente sin resultados o evidencia insuficiente → registro no se emite, sin retry automático (ver KERNEL:FAIL-PHILOSOPHY).
Métricas mínimas: resultados por fuente, total de resultados, timestamp de búsqueda.
Strategic Search
Trigger: humano (ciclo semanal — lunes)
Estados de error: JSON malformado o evidencia contradictoria sin resolución determinista → registro se reporta, no se fuerza a Notion.
Métricas mínimas: registros consolidados, duplicados eliminados, conflictos resueltos.
Passive Intake
Trigger: automático (continuo)
Responsabilidades: leer backlog de correo, extraer vacantes, poblar Class A; Class B queda vacío — lo calcula Python en el siguiente run del pipeline.
Campos inmutables: máx. 10 correos por corrida (ver ALIASES:L3-PASSIVE-INTAKE); Class B nunca se estima aquí.
Reglas de dedup: L3 no deduplica — entra directo a feed_processor.py; la jerarquía L1>L2>L3 se resuelve en KERNEL:ARCHITECTURE-L4.
Estados de error: fallo de IMAP o extracción → correo se omite del batch, sin reintento automático (ver KERNEL:FAIL-PHILOSOPHY).
Version Control & Infrastructure
Skills Distribution — Single Source of Truth
/skills/ en la raíz del repo es la fuente canónica de los .skill files de VANTAGE (actualmente 25) + index.json + index.html. GitHub Pages sirve esta ruta desde main en https://mauriciomeyran.github.io/VANTAGE/skills/. git_sync.py (el mismo motor detrás del alias vgit) detecta nuevos .skill en /skills/, regenera index.json y ejecuta commit + push en la misma corrida — no requiere paso manual adicional.
vsum.py (alias vsum) — herramienta de continuidad entre sesiones e IAs, no capa de búsqueda ni de pipeline: resume transcripts de sesiones (Claude, Gemini, ChatGPT, u otro) a Markdown estructurado (contexto, hallazgos, decisiones, pendientes), orientado a que la siguiente sesión o la siguiente IA no pierda continuidad. Escribe vía notion_client.Client directo (no MCP) como página hija del INBOX (ver Cédula Digital, SP:DIGITAL-ID-CARD). Mismo patrón de acceso directo a la API ya usado por vsync_doc.py. No lee ni escribe el Tracker de vacantes; su único contacto con Notion es de salida (push opcional del resumen), nunca de entrada.
Jerarquía de Dedup
L1 > L2 > L3. Perplexity aplica esta jerarquía en Consolidation & Dedup; L3 entra directo a feed_processor.py.
Punto de Convergencia Único
Las tres capas de búsqueda escriben a Notion. vantage-pipeline lee de Notion, no de outputs de capa directamente.
Figma Sync — CV Output Layer
Tipo: Capa de Materialización de CV (WriteOnly sobre lienzo Figma), arquitectura de 3 piezas sobre permisos mínimos (sin capabilities, sin enableProposedApi) — opera exclusivamente sobre el archivo Figma activo, sin llamadas de red.
Ambas piezas activas (ui.html, code.js) se comunican vía postMessage — el mecanismo estándar de Figma entre el iframe de UI y el sandbox del plugin, y el único canal de datos del sistema; no existe transporte de red ni escritura fuera del lienzo abierto.
Invariantes
AI Component
Procesador textual del pipeline:
Restricciones (no negociables)
CV-À SCOPE LOCK: Prohibido en esta fase evaluar fit estratégico o cuestionar la Gate_Decision tomada por Python. La IA informa discrepancias en "observaciones" del HANDOFF sin emitir verbos de decisión ("bloquear", "pasa").
Python Component
Motor de lógica de negocio y escritura autónoma: único componente con permiso de escritura autónoma en Notion.
Excepción — Bypass
Source_Type ∈ {Inbound, Referencia, Networking} → Gate_Decision: CREATE automático (ver 09.1).
Invariante crítico
Python recalcula campos Class B en cada run — ningún valor estimado por el AI Component tiene validez en el pipeline. Este invariante se aplica técnicamente en la vía RT-1/Dashboard mediante el guard documentado en KERNEL:GATE-DECISION-003 (GAP-03 cerrado v9.19.2).
Arquitectura Dashboard/Checklist
Capa de presentación adicional sobre los datos que las capas de búsqueda producen.
1. Backend operativo real — dashboard_server.py + dashboard.db + dashboard_notion.py. Fuente de verdad del pipeline. dashboard.html consume vía fetch('http://127.0.0.1:8000/{path}').
1. Checklist operativo semanal — Checklist.html. Standalone, estado en localStorage['vchecklist_v1']. Sin backend, sin Notion.
1. Capa visual compartida — vantage-tokens.css + vantage-theme.js. Única capa realmente compartida entre (1) y (2).
Regla
Cualquier cambio a color de estado semántico o toggle de tema se hace en vantage-tokens.css / vantage-theme.js, nunca inline.
Class A — Human-Primary
Class B — System-Primary
Python escribe: Score · Gate_Decision · VM_Scope · Role_Class · Next_Action · Fetch · Fuente · Dedup_Flag · Score_Method · Last_Gate_Run.
Restricción del Sistema
Campos Class B en JSON entrante se ignoran sin excepción — Python los calcula en el siguiente run.
Entity Format
PREFIX:H_<hash16> / PREFIX:U_<UUID>.
Prefixes válidos: TRACKER, ARCHIVO, DRYRUN, BUG.
Namespace Ownership Contract: resolver_registry_v2.json es el único punto de verdad para entity_prefix.
Ver 03.3 (KERNEL:DOCUMENTATION-003 — L0 Runtime) para el mecanismo de resolución que consume este contrato.
Contrato de Resolución: 4 Pasos
Lookup → Registry Mapping → Notion Query → Validation.
Ver 03.3 (KERNEL:DOCUMENTATION-003 — L0 Runtime) — este contrato es la contraparte de datos del Runtime Build descrito ahí.
Variantes aceptadas: APROBAR_WRITE · APROBAR · SÍ · sí · YEP · yep.
Acceptance Audit
Resultados: PASS / PASS WITH ARCHITECTURAL FINDING / FAIL.
Mapeo de Vocabulario — Prompts → Tracker
- title → Rol
- holding → Holding (null → "Investigar")
Campo Class B (System-Primary), tipo select (migrado de rich_text en v9.14.2) — escrito por layer_1_run.py y layer_1_run_dash.py con la estructura {"select": {"name": VALUE}}. Auditoría de código realizada 2026-08-06, verificada línea por línea contra el repositorio.
Valores confirmados en código activo (10), rediseño v9.14.6 (KERNEL:GATE-DECISION-010):
Historial de tipo de campo: v9.13.7 introdujo escritura select; v9.13.11 documentó (erróneamente) rich_text tras una auditoría desactualizada; v9.14.2/v9.14.3 (Changelog) confirmaron y ejecutaron la migración real a select — esta sección se corrige en v9.14.5 para alinearse con el Changelog, tras detectarse el drift por fetch directo del schema vivo de Notion.
Alcance
- Proactivo (trabajo/decisión pendiente) → Tasks Tracker
Niveles de Prioridad
Con Class A/B (07) y OWNERSHIP (05) ya definidos, esta sección describe la lógica que decide, para cada vacante, si avanza, se bloquea o se descarta.
Bypass
Lógica Estándar
Orden:
1. Score (0–100)
1. Gate_Decision (≥60 CREATE · 40–59 REVIEW_NEEDED · <40 BLOCKED/Archivar).
### 09.3 KERNEL:GATE-DECISION-003
Resolución de REVIEW_NEEDED
GAP-03 — CERRADO (v9.19.2): escritura directa vía MCP/RT-1 cuenta con guard equivalente al de feed_processor.py. class_b_guard.guard_write_payload() está integrado en dashboard_notion.py::write_patch_to_notion() como guard previo a client.pages.update(), fail-closed (CLASS_B_BLOCKED) ante campos Class B o desconocidos (strict_unknown=True). Verificado línea por línea contra el repositorio, 2026-08-10.
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
Marcado Manual de Archivado
Next_Action='Archivar' Y/O Dedup_Flag='Posible duplicado' (ambos Class B) son señales de candidatos a archivar — no disparan archivado automático. Decisión del operador (2026-08-01): se abandonó el enfoque de mover/copiar automáticamente vía auto_archive.py (deprecado, ver Archive/Legacy_Scripts/) por menor fricción, menor costo de tokens, y por desalineación de esquema con el Archivo Tracker (ver skill vantage-tidy-opportunities-tracker).
El mecanismo vigente es la skill vantage-tidy-opportunities-tracker: identifica candidatos vía Dedup_Flag/Next_Action, marca Archivar = True en el registro original tras DRY RUN + APROBAR_WRITE — no crea copias ni toca el Archivo Tracker ni mueve páginas físicamente. El operador localiza visualmente los registros marcados y decide cuándo archivarlos manualmente.
Consolidación prevista: la skill vantage-housekeeping-archive (propuesta, auditoría 2026-08-13) absorberá este ciclo de detección→marcado→verificación en un solo procedimiento; el reporte read-only status_report.py --archive-queue (aún no implementado) sustituirá el escaneo visual del Tracker sin añadir ninguna vía de escritura nueva.
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
- "Expirada" → protege como EXPIRADA (fix D-001 aplicado v9.19.1 — antes protegida indirectamente solo vía Next_Action=Expirada en TERMINAL_ACTIONS; ambos mecanismos coexisten sin conflicto, evaluados en este orden)
1. Next_Action → TERMINAL_ACTIONS
- "Archivar" · "Expirada"
1. Si ninguno aplica → None (registro elegible para recálculo por gate())
Invariantes
- gate_logic() se invoca antes de gate() en todo pipeline ordinario y backfill (layer_1_run.py Fase 4).
- Todo write que fija Status=Expirada (Fase 2 — URL_GATE; Fase 3.5 — filtro de perfil) debe fijar Next_Action=Archivar en el mismo write — evita drift entre el criterio Status→TERMINAL y Next_Action→TERMINAL_ACTIONS.
- Un registro terminal no puede ser sobreescrito por recálculo de Score/Gate, aunque cambien campos Class A.
- RT-1 (/accept): la escritura de Class A corregido debe limpiar atómicamente Next_Action y Gate_Decision (select: null) en el mismo write, para que el siguiente run no trate la vacante recuperada como terminal fantasma.
- v9.14.5: Status=Rechazado ahora escribe Next_Action=Post-Mortem (antes Ninguna) — protección terminal vía STATUS_TERMINAL_MAP sin cambio, ya cubierta por el criterio 1 de esta sección.
- Protección estrecha: solo los valores listados arriba. Cualquier otro Next_Action (Follow-up, Re-check, etc.) es recalculable — coherente con KERNEL:OWNERSHIP-002.
Referencias
- Implementación: Layer_1/scripts/gate_logic.py, Layer_1/scripts/layer_1_run.py
- Atomicidad RT-1: Dashboard/scripts/dashboard_routes.py (/accept), dashboard_notion.py — la escritura en esta vía pasa por el guard class_b_guard.guard_write_payload() (ver KERNEL:GATE-DECISION-003, GAP-03 cerrado v9.19.2), que bloquea fail-closed cualquier campo Class B o desconocido antes de client.pages.update().
- Contratos relacionados: KERNEL:GATE-DECISION-005, KERNEL:GATE-DECISION-006, KERNEL:GATE-DECISION-008, KERNEL:OWNERSHIP-002
### 09.11 KERNEL:GATE-DECISION-011
Matriz de Transición de Estados (Referencia Técnica)
Vista tabular consolidada de todas las reglas Gate (09.1–09.10).
Referencia canónica para scripts y auditorías — no reemplaza la descripción en prosa de cada sección; la complementa con indexación de estados.
| Estado Origen | Evento / Trigger | Guard / Regla | Estado Destino | Componente | Efecto Class B |
| --- | --- | --- | --- | --- | --- |
| [ENTRY] | feed_processor.py ingesta JSON | URL muerta OR Score < 40 | BLOCKED | Python | Gate_Decision=BLOCKED, Score=0 (si URL muerta) |
| [ENTRY] | feed_processor.py ingesta JSON | URL viva + Score 40–59 + Status=Target | REVIEW_NEEDED | Python | Gate_Decision=REVIEW_NEEDED, Score, VM_Scope, Role_Class, Next_Action |
| [ENTRY] | feed_processor.py ingesta JSON | URL viva + Score ≥ 60 + Status=Target | READY_TO_APPLY | Python | Gate_Decision=CREATE, Score, VM_Scope, Role_Class, Next_Action |
| [ENTRY] | Agregador con HEAD fallido/timeout | AGREGADOR_UNVERIFIED | REVIEW_NEEDED | Python | Fetch=No_Verificado (no Accesible) |
| [ENTRY] | feed_processor.py ingesta JSON | Dedup match (hash/URL/brand+title) contra VANTAGE TRACKER activo, ventana 30d | REVIEW_NEEDED | Python | Status=REVIEW_NEEDED en el registro entrante; Dedup_Flag='Posible duplicado' (select) en el registro existente coincidente |
| BLOCKED | vd — Dashboard RT-1 edita Class A | Patch válido → run_pipeline.py --dry PASS | PATCHED | Humano + Python | Score, Gate_Decision recalculados |
| PATCHED | Operador acepta patch en Dashboard | Aceptar → vantage_pipeline.sh | READY_TO_APPLY OR BLOCKED | Python | Gate_Decision re-evaluado; si falla → regresa BLOCKED |
| PATCHED | Operador rechaza patch en Dashboard | Rechazar | BLOCKED | Humano | Sin cambio en SSOT |
| REVIEW_NEEDED | Operador edita Notion directo + Status→Target | vantage_pipeline.sh evalúa Class B por primera vez | READY_TO_APPLY OR BLOCKED | Humano + Python | Score, Gate_Decision, Next_Action calculados |
| READY_TO_APPLY | Operador inicia postulación | Status→Postulando | APPLYING | Humano | Status (Class A) |
| APPLYING | Confirmación de envío | Status→Postulado | APPLIED | Humano | Status (Class A) |
| APPLIED | Resultado negativo | Status→Rechazado | REJECTED | Humano | Status (Class A) — terminal, protegido por gate_logic(); Next_Action=Post-Mortem (v9.14.5) |
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
### 10.6 KERNEL:CV-GOLDEN-RULES-006
Regla #6 — Invarianza de la Decisión de Gate
Prohibido que el AI Component re-evalúe fit, estime scores o aplique exclusiones sobre vacantes que ya poseen una Gate_Decision calculada por Python o aprobada por el operador.
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
- VL1 backfill — catch-up de campos Class A faltantes en registros existentes: layer, hash y Prioridad. Prioridad se calcula por matriz Urgencia × Importancia (ver tabla). Importancia = bucket de Score: Base (=40) · Media (41–60) · Alta (61–80) · Muy Alta (81–100). Urgencia conserva la lógica original (deadline/antigüedad/Source_Type). Desde Fase 3.6 (layer_1_run.py), Prioridad se escribe primero en el ingreso normal del pipeline — backfill opera solo sobre huecos que quedaron vacíos (migraciones, registros previos a Fase 3.6). Ambos consumen la misma lógica desde priority_logic.py, módulo compartido para evitar import circular entre layer_1_run.py y backfill_class_a.py. Precedente de lectura de objeto Notion: created_time vive en la raíz del objeto página (item["created_time"]), no en item["properties"] — cualquier función que reciba props en vez de item no puede leerlo. Mismo patrón de riesgo que motivó el fix de txt()/rich_text (v9.20.1): asumir la forma del objeto Notion sin verificarla contra el schema real.
| Urgencia \ Importancia | Base | Media | Alta | Muy Alta |
| --- | --- | --- | --- | --- |
| CRÍTICO (deadline/Inbound) | CRÍTICO | CRÍTICO | CRÍTICO | CRÍTICO |
| ALTO (≤3 días) | MEDIO | ALTO | CRÍTICO | CRÍTICO |
| MEDIO (4–14 días) | BAJO | MEDIO | ALTO | CRÍTICO |
| BAJO (>14 días) | BAJO | BAJO | MEDIO | ALTO |
Implementación: priority_logic.py (matriz compartida) — invocado por layer_1_run.py Fase 3.6 (escritura primaria) y por backfill_class_a.py::apply_importancia_matrix() (catch-up).
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
Extrae keywords + gaps + tono de marca. Determina el Positioning Mode aplicable mediante el Algoritmo de Selección N1–N4 (4 pasos, determinista):
1. Keywords — extraer JD_keywords_top6 del JD.
1. Mapeo — alinear cada keyword contra los anclajes canónicos de CANON:POSITIONING.
1. Conteo — contar matches por ancla.
1. Desempate — si dos o más modos empatan, aplicar la Regla de Desempate de CANON:POSITIONING (keywords → seniority → escalamiento humano).
Contrato de Persistencia de la Decisión
El modo seleccionado no es válido sin su justificación: CV-A escribe positioning_rationale (texto libre, 1 línea) en el HANDOFF, documentando el match predominante que determinó el modo (ej. "JD centrado en obra civil → N2"). Sin este campo, el HANDOFF está incompleto y no avanza a CV-B.
Output
HANDOFF (JSON de 7 campos).
Cierre obligatorio
SESIÓN COMPLETADA → nueva sesión.
```json
{
  "empresa": "",
  "rol": "",
  "JD_keywords_top6": ["", "", "", "", "", ""],
  "fit_gaps": ["", ""],
  "tono_marca": "",
  "idioma": "",
  "positioning_rationale": ""
}
```
Un HANDOFF incompleto no avanza a CV-B. El sistema no inventa valores para campos faltantes.
Regla de Orden de Experiencia
Cronológico descendente siempre. Orden canónico obligatorio: C01 → C02 → C03 → C04 → C05. No se modifica por Positioning Mode, relevancia ni ninguna otra variable.
### 12.2 KERNEL:CV-PIPELINE-002
CV-B
Input
HANDOFF completo + Career Canon activo.
Restricción de Lote (Single-Item Processing)
CV-B procesa exactamente UN HANDOFF por invocación. Prohibido procesar múltiples vacantes en la misma pasada/sesión continua, incluso si el operador entrega un batch de HANDOFFs. Ante un batch, CV-B debe: (1) tomar el primer HANDOFF y procesarlo completo como única unidad de trabajo, (2) detenerse y esperar invocación explícita separada para el siguiente. Razón: degradación de densidad y esfuerzo narrativo observada empíricamente en procesamiento secuencial de lote (v9.16.0 post-mortem, 13 CV-B en una sesión) — el contrato formal (IDs, Anti-cloning Guard, secuencia C01–C05) no previene esta degradación porque es un fallo de ejecución del AI Component bajo carga repetitiva, no un gap documental.
Validation
Verificar los 7 campos del HANDOFF.
Canon check
Empresa, rol, bullets y KPIs derivados del Canon — no inventados. Cada bloque de experiencia es una derivación única del Canon frente al HANDOFF activo; se prohíbe reutilizar bullets pre-redactados verbatim entre vacantes distintas, incluso dentro del mismo Positioning Mode.
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
