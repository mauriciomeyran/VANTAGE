# V | KERNEL

Propósito del Sistema
1. Score no lo calcula el sistema de lenguaje — lo calcula Python con lógica determinista.
1. Gate decision no se sobreescribe manualmente. RT-1 permite corregir inputs Class A para que Python recalcule (ver 09.5).
Documentación y Gobernanza (L0)
Canonical Document ID Contract
Invariantes del Contrato
- Formato Único: [PREFIX]:[KEY] (ej. MANUAL:SETUP).
- Prefix Ownership: Cada prefijo mapea a una única página canónica en Notion.
- SSOT: resolver_registry_v2.json es la autoridad única para resolver Prefijos a UUIDs.
- Resolución Determinista: El Resolver (v1.py) garantiza resolución O(1) inyectando el ID crudo al componente solicitante.
Prefijos Autorizados
Matriz Tipográfica Congelada (Jerarquía de Encabezados)
La resolución de un ID canónico a su nivel de heading Markdown sigue una jerarquía fija:
- Figma Tag (solo derivados, inmutable) = ######
Reglas de Migración
Normalización Documental de IDs Legacy
- Alcance: todos los documentos fundacionales.
- Excepciones: IDs de Notion (UUIDs) en metadatos o URLs.
- Gobernanza: cambios requieren APROBAR_WRITE + entrada en Changelog.
Estado actual: normalización completada. DT-015 (26 ocurrencias) — CERRADO.
Runtime Build — proceso determinista que genera:
Consume resolver_registry_v2.json como fuente de namespace ownership — si el Registry no define el prefix de un tipo de entidad, el Build falla explícitamente. graph_layer.py construye graph_v2.json; nunca infiere namespaces ni redefine contratos.
Version Check Tool y Census como parte de L0: verify_versions.py (alias vversions) y generate_census.py (alias vcensus) son observabilidad ReadOnly sobre Notion — mismo tipo de operación que Runtime Build, aplicada a versión documental y salud del Census.
Tipo: Capa de Sincronización de Sesión (Fetch-on-Start).
Propósito: Elimina el drift de versiones entre la UI estática del agente y el repositorio dinámico de Notion.
- vantage-session-open — SESSION-OPENING… / SESSION-OPENED
- vantage-session-close — CLOSING SESSION… / SESSION CLOSED
Reporte de Tickets
Agrupación por Prioridad (CRÍTICO / ALTO / MEDIO / BAJO) sobre Bug Tracker y Task Tracker. Detalle explícito solo para CRÍTICO y ALTO.
- --bootstrap (dump read-only de apertura de sesión)
- --skills (gap report read-only: cruza archivos .skill del árbol activo contra SKILL LIBRARY en Notion)
- --length (Sanity check de integridad estructural, read-only, exit code 1 si ATENCIÓN REQUERIDA)
Verificación de Integridad Estructural (Length Check)
Propósito: Detectar truncamiento silencioso en los documentos fundacionales mediante comparación del conteo de líneas de texto extraíble contra un baseline predefinido.
Archivos asociados:
- length_baseline.json: Almacena el conteo de líneas por documento y timestamp captured_at. Si no existe, la primera ejecución de --length lo genera automáticamente.
- --length: Modo read-only. Ejecuta la verificación de longitud y genera el reporte.
- --update-baseline: Modo write explícito. Requiere invocarse junto a --length. Sobrescribe length_baseline.json con los conteos actuales únicamente si el veredicto final es PASS o el operador confirma explícitamente que las diferencias son intencionales.
Reglas
1. [CENSUS-SYNC-R1]: ningún ticket que implique cambio de estado de un ID se marca Done sin Census regenerado. Si no puede ejecutarse, el ticket queda Blocked-Census.
1. generate_census.py detecta IDs huérfanos y los reporta antes de cerrar el ticket asociado.
1. Ninguna sesión con cambios cierra sin DRY RUN automático de lo modificado.
1. health_check.py reporta antigüedad del Census (umbral 7 días) como advertencia informativa, no bloqueante.
Session Ledger
- session_id
Mapeo → DRY RUN → Inyección → Write-Back Verification → Changelog + versión → Binary Gate de salida.
Skills de Gobernanza Documental
Piezas
Notebook Gemini — Auditor Documental Externo
Tipo: Capa de Consulta ReadOnly externa (Google Gemini, ventana de contexto sin límite de tokens equivalente), complementaria al fetch nativo de Claude sobre el corpus fundacional — no es un script ni un alias de Terminal.
Contrato de Cero Inferencia Silenciosa
Consulta puntual de triaje/verificación documental (detección de drifts entre documentos) cuando no se requiere fetch estructural ni escritura en Notion — evita consumir fetch/tokens de Claude en preguntas de bajo riesgo.
Protocolo Sandbox — Economía de Tokens Máxima
Patrón operativo compartido por las skills de documentación transversal (propuesta/implementación), vantage-skill-updater y vantage-housekeeping-archive: todo proceso interno de análisis, validación y generación corre en sandbox sin renderizar al operador. El output visible se limita a un máximo de 3 bloques por invocación: apertura (declaración de inicio conforme KERNEL:DOCUMENTATION-005), resultado (propuesta/reporte/DRY RUN estructurado), cierre (declaración de fin).
Regla de aplicación
Cualquier skill nueva que adopte este patrón declara explícitamente qué pasos corren en sandbox interno y cuáles son output visible — no se asume por default; se declara en el cuerpo de la skill.
No aplica a
Skills cuyo output es inherentemente iterativo o requiere confirmación por ítem (ej. vantage-cv-b, procesamiento single-item) — ahí la economía de tokens se gestiona por otro mecanismo (Restricción de Lote, ver KERNEL:CV-PIPELINE-002).
Arquitectura de Cuatro Capas
Trigger: humano (ciclo semanal — lunes)
Objetivo: maximizar cobertura y trazabilidad de entrada — no decide prioridad estratégica, solo captura oportunidades de alta señal antes de que se evaporen.
Componentes: Career Sites · LinkedIn · Aggregators — wrappers especializados por fuente, convergiendo a un schema común. Herramienta de soporte: Weekly Prompt Assembler (weekly_prompt_assembler.py, alias vassemble) — materializa en disco los 7 prompts semanales por motor desde la PROMPT LIBRARY, reemplazando el ensamblado anterior vía agente dentro de Perplexity Desktop (ver ALIASES:L1L2-DISCOVERY).
Responsabilidades: buscar vacantes, validar evidencia mínima, extraer campos canónicos, mantener trazabilidad por fuente, emitir resultados estructurados (no recomendaciones).
Campos inmutables: los campos Class A emitidos por cada wrapper (ver KERNEL:SCHEMA-001) no se reinterpretan en L1 — feed_processor.py normaliza formato, no criterio.
Reglas de dedup: L1 no deduplica — la jerarquía L1>L2>L3 y el punto de convergencia único viven en KERNEL:ARCHITECTURE-L4.
Métricas mínimas: resultados por fuente, total de resultados, timestamp de búsqueda.
Objetivo: resolver fragmentación entre motores de extracción — prioriza reconciliación y reducción de ruido sobre amplitud de cobertura.
Componentes: Gemini · You.com · Grok (extracción paralela) — Perplexity como consolidador determinista.
Responsabilidades: consolidar, deduplicar, resolver conflictos, enriquecer solo cuando no rompe evidencia válida, emitir métricas y estados.
Trigger: automático (continuo)
Objetivo: captura pasiva y continua de vacantes ya remitidas al operador — sin ciclo humano semanal, sin dependencia de búsqueda activa.
Componentes: Gmail (label .Jobs) · layer_3_mail.py (IMAP + extracción Groq).
Responsabilidades: leer backlog de correo, extraer vacantes, poblar Class A; Class B queda vacío — lo calcula Python en el siguiente run del pipeline.
Estados de error: fallo de IMAP o extracción → correo se omite del batch, sin reintento automático (ver KERNEL:FAIL-PHILOSOPHY).
Métricas mínimas: correos procesados, vacantes extraídas, Class A poblado / Class B pendiente.
- Al finalizar, ejecuta git add + git commit + git push automático sobre skills/triggers.json — auto-push sin gate manual, decisión consciente del operador; valida el resultado de cada paso de git explícitamente antes de continuar al siguiente.
Mecanismos de Dedup — Distinción de Propósito
Punto de Convergencia Único
Figma Sync — CV Output Layer
- manifest.json — declara identidad (vantage-cv-sync), sandbox (code.js) y UI (ui.html).
Ambas piezas activas (ui.html, code.js) se comunican vía postMessage — el mecanismo estándar de Figma entre el iframe de UI y el sandbox del plugin, y el único canal de datos del sistema; no existe transporte de red ni escritura fuera del lienzo abierto.
División de Responsabilidades AI/Python
- Escritura de campos Class A
Restricciones (no negociables)
CV-À SCOPE LOCK: Prohibido en esta fase evaluar fit estratégico o cuestionar la Gate_Decision tomada por Python. La IA informa discrepancias en "observaciones" del HANDOFF sin emitir verbos de decisión ("bloquear", "pasa").
### 05.2 KERNEL:OWNERSHIP-002
Python Component
Motor de lógica de negocio y escritura autónoma: único componente con permiso de escritura autónoma en Notion.
Source_Type ∈ {Inbound, Referencia, Networking} → Gate_Decision: CREATE automático (ver 09.1).
Invariante crítico
Arquitectura Dashboard/Checklist
1. Backend operativo real — dashboard_server.py + dashboard.db + dashboard_notion.py. Fuente de verdad del pipeline. dashboard.html consume vía fetch('http://127.0.0.1:8000/{path}').
1. Checklist operativo semanal — Checklist.html. Standalone, estado en localStorage['vchecklist_v1']. Sin backend, sin Notion.
Aclaración terminológica: "el Tracker" sin calificativo se refiere siempre a la base de datos principal donde L1/L2/L3 escriben cada vacante — distinta del Bug Tracker y Tasks Tracker (08).
Class A — Human-Primary
AI Component escribe en CV-A · CV-B · QA · FAST · CANON-UPDATE; feed_processor.py escribe en FEED L1/L3:
Valores operativos de Status: Target · Postulado · Rechazado · Expirada · Archivar · Repetida.
### 07.4 KERNEL:SCHEMA-004
Namespace Ownership Contract: resolver_registry_v2.json es el único punto de verdad para entity_prefix.
Contrato de Resolución: 4 Pasos
Ver 03.3 (KERNEL:DOCUMENTATION-003 — L0 Runtime) — este contrato es la contraparte de datos del Runtime Build descrito ahí.
Eliminados (RAI-03): Ok · Go · YES · yes.
Acceptance Audit
Mapeo de Vocabulario — Prompts → Tracker
Entry Template — Campos Class A Requeridos
Rol · Marca · URL · Source_Type · Status · Prioridad · JD · JOB_ID · Holding.
Campo Class B (System-Primary), tipo select (migrado de rich_text en v9.14.2) — escrito por layer_1_run.py y layer_1_run_dash.py con la estructura {"select": {"name": VALUE}}. Auditoría de código realizada 2026-08-06, verificada línea por línea contra el repositorio.
Valores confirmados en código activo (10), rediseño v9.14.6 (KERNEL:GATE-DECISION-010):
Historial de tipo de campo: v9.13.7 introdujo escritura select; v9.13.11 documentó (erróneamente) rich_text tras una auditoría desactualizada; v9.14.2/v9.14.3 (Changelog) confirmaron y ejecutaron la migración real a select — esta sección se corrige en v9.14.5 para alinearse con el Changelog, tras detectarse el drift por fetch directo del schema vivo de Notion.
Bug Tracker y Tasks Tracker
Alcance
- Proactivo (trabajo/decisión pendiente) → Tasks Tracker
Bypass
GAP-03 — CERRADO (v9.19.2): escritura directa vía MCP/RT-1 cuenta con guard equivalente al de feed_processor.py. class_b_guard.guard_write_payload() está integrado en dashboard_notion.py::write_patch_to_notion() como guard previo a client.pages.update(), fail-closed (CLASS_B_BLOCKED) ante campos Class B o desconocidos (strict_unknown=True). Verificado línea por línea contra el repositorio, 2026-08-10.
Un gate que puede sobreescribirse manualmente no es un gate — es una sugerencia.
Flujo de Recuperación BLOCKED
Regla de escalamiento (3 niveles):
Nivel 1 — Bajo esfuerzo / sin evidencia de bloqueo
Nivel 2 — Alto esfuerzo / sin evidencia dura
Nivel 3 — Bloqueo o degradación confirmada por fuente dura
Referencia cruzada Manual: Ver MANUAL:SESSION-CYCLE — Ciclo de Sesión para la implementación práctica de este escalamiento dentro del flujo operador.
Criterios (orden de evaluación obligatorio)
1. Next_Action → TERMINAL_ACTIONS
1. Si ninguno aplica → None (registro elegible para recálculo por gate())
- Protección estrecha: solo los valores listados arriba. Cualquier otro Next_Action (Follow-up, Re-check, etc.) es recalculable — coherente con KERNEL:OWNERSHIP-002.
- Implementación: Layer_1/scripts/gate_logic.py, Layer_1/scripts/layer_1_run.py
Referencia canónica para scripts y auditorías — no reemplaza la descripción en prosa de cada sección; la complementa con indexación de estados.
gate_logic() debe ejecutarse ANTES que gate() como filtro de mutabilidad.
Si Status ∈ {Postulado, Rechazado, Expirada} → pipeline termina aquí, sin invocar gate(). Previene regresión de estado en terminales.
→ Referencia cruzada: KERNEL:GATE-DECISION-010 (terminalidad), KERNEL:GATE-DECISION-005 (RT-1).
Excepción: CV-A extrae keywords/gaps técnicos, no es evaluación de fit.
### 10.2 KERNEL:CV-GOLDEN-RULES-002
Regla #2 — No Calcular ni Estimar Campos Class B
Campos protegidos: Score · VM_Scope · Role_Class · Match · Gate_Decision · Next_Action · Fetch · Fuente · JD_Quality · Dedup_Flag.
Regla #3 — No Cuestionar la Calidad de Datos del Usuario
Sin sugerencias, sin recomendaciones de fuentes alternativas.
Regla #4 — No Delegar Escritura al Usuario
Regla #5 — No Interpretar en SYNC
Datos puros, sin análisis de tendencias.
Regla #6 — Invarianza de la Decisión de Gate
Prohibido que el AI Component re-evalúe fit, estime scores o aplique exclusiones sobre vacantes que ya poseen una Gate_Decision calculada por Python o aprobada por el operador.
Contratos de Ejecución del AI Component
, backslashes de escape, <empty-block/> sueltos) en el Kernel anterior — normalizados a Markdown estándar en toda esta sección.
Procesamiento por Lotes. FEED con más de 10 vacantes se divide en lotes de 10, secuencial, con header de lote. Sin reintento automático por lote — ante fallo parcial, reportar y esperar instrucción.
Proceso
VL1
Comandos de mantenimiento del Tracker — no son triggers del AI Component, son comandos Python autónomos. Ningún comando VL1 escribe campos Class B.
Validación de Formato de CV Exportado. No evalúa fit, oportunidad, score ni conveniencia de aplicar.
Checklist Canónico de 6 ítems
Output: GO/NO-GO por ítem; cualquier FAIL → NO-GO final.
Preview Obligatorio de Escritura. No hay escritura sin DRY RUN previo.
Campos Permitidos (Class A)
Op · Empresa · Rol · URL · Source_Type · Prioridad · Status.
Campos Prohibidos (Class B)
Visual Signal · Innovation DNA · Score Estimado · Gate_Decision · Decisión CREATE/BLOCKED.
Autorización: una de las variantes válidas de APROBAR_WRITE (07.6).
SYNC
Reporte de Estado del Tracker. Datos puros, sin interpretación.
Output (≤12 líneas)
TOP 3 BY SCORE
Query de las 3 vacantes con mayor Score.
Campos permitidos: Marca, Rol, Score, (opcional) URL.
Sin evaluación de "cuál aplicar primero".
NEXT ACTION
Ejecuta ~/vantage_pipeline.sh status y reporta el output exacto, sin interpretación ni resumen.
JSON de vacantes sin trigger explícito → "El procesamiento de FEED está migrado a feed_processor.py."
Excepción FAST: array de longitud 1 + trigger FAST explícito = procesamiento normal, sin lotes.
STATUS
Lectura del estado general del sistema. Solo lectura, no interpreta si el sistema está "sano" o "degradado" — reporta datos.
CV Pipeline — Arquitectura de Dos Sesiones Obligatorias
1. Keywords — extraer JD_keywords_top6 del JD.
HANDOFF (JSON de 7 campos).
Un HANDOFF incompleto no avanza a CV-B. El sistema no inventa valores para campos faltantes.
Regla de Orden de Experiencia
Cronológico descendente siempre. Orden canónico obligatorio: C01 → C02 → C03 → C04 → C05. No se modifica por Positioning Mode, relevancia ni ninguna otra variable.
CV-B
Validation
Verificar los 7 campos del HANDOFF.
Canon check
Empresa, rol, bullets y KPIs derivados del Canon — no inventados. Cada bloque de experiencia es una derivación única del Canon frente al HANDOFF activo; se prohíbe reutilizar bullets pre-redactados verbatim entre vacantes distintas, incluso dentro del mismo Positioning Mode.
Auditoría de Estructura
COUNT(figma_text_id)_SKELETON == COUNT(figma_text_id)_OUTPUT. Si no coincide, abortar y re-mapear.
Auditoría de Secuencia
Los slots de experiencia deben aparecer en secuencia canónica estricta C01→C05. Ninguna variable del HANDOFF autoriza alterarla.
Output
Post-aplicación
Trigger de Actualización del Career Canon
Con el pipeline de CV y su convención de nombres ya definidos, esta sección cubre el trigger que mantiene actualizada la fuente que ese pipeline extrae: el Career Canon.
No es discovery, scoring, gate decision ni evaluación de fit.
Input
Validación previa
Identificar qué sección(es) se afectan, qué IDs canónicos impactan, si requiere versión ES/EN/ambas, si impacta CV-A/CV-B/QA/Output Contract, si la información es suficiente.
1. Producir DRY RUN
Restricciones
{Año}{Nombre}{Apellido}{Marca_normalizada}{Vacante_normalizada}
- Espacios → guión bajo
- Sin acentos ni caracteres especiales
- Sin símbolos de puntuación
Ejemplo
"Gucci — VM Coordinator, LATAM (2026)" → 2026_Mauricio_Meyran_Gucci_VM_Coordinator_LATAM
No aplica a
DRY RUN archivado, artefactos de sistema (logs, backups, entity_index).
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
