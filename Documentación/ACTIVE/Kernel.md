# V | KERNEL

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
- No intenta reparar equipos.
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
| KERNEL | V | KERNEL |
| MANUAL | V | MANUAL |
| CANON | V | CAREER CANON |
| TRACKER | V | TRACKER |
| SP | V | SYSTEM PROMPT |
| ALIASES | V | ALIASES |
| CHANGELOG | V | CHANGE LOG |
| BRIEF | V | NAVIGATION BRIEF |
| VANTAGE | V | VANTAGE CENTRAL HUB |
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
- apply_hyperlinks_notion.py — PATCH puntual directo sobre bloques Notion (notion.blocks.update), preserva block-ID, no pasa por destroy/rebuild. Reutiliza fetch_blocks_recursive/extract_ids_from_block/is_definition_block de generate_census.py. Es la vía activa de escritura.
- apply_hyperlinks.py — DEPRECATED. Operaba sobre los .md locales con MAPPING estático hardcodeado; reemplazado por apply_hyperlinks_notion.py, que construye el MAPPING en cada corrida desde el link_index real del Census.
- vantage_id_rules.py — módulo destinado a ser la fuente única de reglas DEF/REF/heading para ambos.
Regla permanente
El heading de definición nunca se auto-enlaza a sí mismo; toda mención posterior (TOC, prosa, tablas de referencia) sí es clickeable.
Estado de adopción (2026-08-01)
- apply_hyperlinks_notion.py reemplaza a apply_hyperlinks.py como vía de escritura — ver KERNEL:ARCHITECTURE-L4 para el riesgo de destroy/rebuild que motivó el cambio.
- Fix de is_definition_block() en generate_census.py: exclusión de table_row en la condición stripped == id_str — corrige falso positivo que excluía celdas de TOC de recibir hipervínculo (239 vs 143 bloques patcheados, 0 regresiones). Detalle completo en Changelog v9.12.0.
- generate_id_inventory.py y normalize_heading_ids.py ya fueron migrados 
Ver MANUAL:HEALTHCHECK para el procedimiento operativo de cuándo correr cada script.
---
### 03.12 KERNEL:DOCUMENTATION-012
Notebook Gemini — Auditor Documental Externo
Tipo: Capa de Consulta ReadOnly externa (Google Gemini, ventana de contexto sin límite de tokens equivalente), complementaria al fetch nativo de Claude sobre el corpus fundacional — no es un script ni un alias de Terminal.
Contrato de Cero Inferencia Silenciosa
- Toda afirmación técnica requiere ancla exacta (PREFIX:KEY).
- Ante instrucción o mecanismo no documentado en las fuentes cargadas, declara explícitamente "Fuera de Alcance" o "No encontrado" — nunca infiere.
- No calcula Score, no redacta CVs, no crea reglas de negocio; su alcance es reportar lo ya escrito en el corpus.
Uso preferente
Consulta puntual de triaje/verificación documental (detección de drifts entre documentos) cuando no se requiere fetch estructural ni escritura en Notion — evita consumir fetch/tokens de Claude en preguntas de bajo riesgo.
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
Objetivo: maximizar cobertura y trazabilidad de entrada — no decide prioridad estratégica, solo captura oportunidades de alta señal antes de que se evaporen.
Componentes: Career Sites · LinkedIn · Aggregators — wrappers especializados por fuente, convergiendo a un schema común.
Responsabilidades: buscar vacantes, validar evidencia mínima, extraer campos canónicos, mantener trazabilidad por fuente, emitir resultados estructurados (no recomendaciones).
Campos inmutables: los campos Class A emitidos por cada wrapper (ver KERNEL:SCHEMA-001) no se reinterpretan en L1 — feed_processor.py normaliza formato, no criterio.
Reglas de dedup: L1 no deduplica — la jerarquía L1>L2>L3 y el punto de convergencia único viven en KERNEL:ARCHITECTURE-L4.
Estados de error: fuente sin resultados o evidencia insuficiente → registro no se emite, sin retry automático (ver KERNEL:FAIL-PHILOSOPHY).
Métricas mínimas: resultados por fuente, total de resultados, timestamp de búsqueda.
### 04.2 KERNEL:ARCHITECTURE-L2
Strategic Search
Trigger: humano (ciclo semanal — lunes)
```plain text
Human signal → Gemini · You.com · Grok (extracción paralela) → Perplexity (Consolidation & Dedup)
→ FEED → feed_processor.py → Notion (Class A) → vantage-pipeline
```
Objetivo: resolver fragmentación entre motores de extracción — prioriza reconciliación y reducción de ruido sobre amplitud de cobertura.
Componentes: Gemini · You.com · Grok (extracción paralela) — Perplexity como consolidador determinista.
Responsabilidades: consolidar, deduplicar, resolver conflictos, enriquecer solo cuando no rompe evidencia válida, emitir métricas y estados.
Reglas de consolidación/enriquecimiento: Perplexity aplica reglas deterministas sobre los JSON recibidos — no infiere ni inventa datos; prioriza evidencia y preserva el registro de mayor calidad o canonicalidad cuando hay conflicto.
Estados de error: JSON malformado o evidencia contradictoria sin resolución determinista → registro se reporta, no se fuerza a Notion.
Métricas mínimas: registros consolidados, duplicados eliminados, conflictos resueltos.
### 04.3 KERNEL:ARCHITECTURE-L3
Passive Intake
Trigger: automático (continuo)
```plain text
Gmail (.Jobs label) → layer_3_mail.py (IMAP + Groq) → Notion (Class A poblado, Class B vacío) → vantage-pipeline
```
Objetivo: captura pasiva y continua de vacantes ya remitidas al operador — sin ciclo humano semanal, sin dependencia de búsqueda activa.
Componentes: Gmail (label .Jobs) · layer_3_mail.py (IMAP + extracción Groq).
Responsabilidades: leer backlog de correo, extraer vacantes, poblar Class A; Class B queda vacío — lo calcula Python en el siguiente run del pipeline.
Campos inmutables: máx. 5 correos por corrida (ver ALIASES:L3-PASSIVE-INTAKE); Class B nunca se estima aquí.
Reglas de dedup: L3 no deduplica — entra directo a feed_processor.py; la jerarquía L1>L2>L3 se resuelve en KERNEL:ARCHITECTURE-L4.
Estados de error: fallo de IMAP o extracción → correo se omite del batch, sin reintento automático (ver KERNEL:FAIL-PHILOSOPHY).
Métricas mínimas: correos procesados, vacantes extraídas, Class A poblado / Class B pendiente.
---
## 07 KERNEL:SCHEMA
Esquema del Tracker de Vacantes
### 07.8 KERNEL:SCHEMA-008
Valores Operativos — Next_Action (Tracker de Vacantes)
Campo Class B (System-Primary), tipo select (migrado de rich_text en v9.14.2) — escrito por layer_1_run.py y layer_1_run_dash.py con la estructura {"select": {"name": VALUE}}. Auditoría de código realizada 2026-08-06.
