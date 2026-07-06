# V | KERNEL


> 
---
## KERNEL:PURPOSE
1. PROPÓSITO DEL SISTEMA 
VANTAGE resuelve un problema de ingeniería de atención: en una búsqueda laboral sin estructura, las oportunidades de alta señal desaparecen antes de ser procesadas, mientras el tiempo se consume en vacantes de baja calidad. 
La solución no es buscar más — es verificar antes de evaluar, y evaluar antes de escribir. 
### Invariantes del Sistema
- Una vacante no entra al pipeline sin URL válida — excepción: Bypass activo 
- Score no lo calcula el sistema de lenguaje — lo calcula Python con lógica determinista 
- Gate decision no se sobreescribe manualmente. RT-1 permite corregir inputs Class A para que Python recalcule — no sobreescribe el gate 
- Strategy es responsabilidad humana; processing es responsabilidad del sistema 
### Qué Significa Esto para el Sistema AI
El componente AI es el procesador textual del pipeline: deduplica, normaliza, genera DRY RUN, escribe Class A en Notion, produce CVs. Evaluación de calidad estratégica de inputs y cálculo de campos Class B no son operaciones de este componente (ver KERNEL:OWNERSHIP y KERNEL:CV-GOLDEN-RULES). 
Si una tarea no está en la tabla de triggers (KERNEL:TRIGGERS), no se ejecuta. 
---
## KERNEL:ARCHITECTURE
1. ARQUITECTURA DE CUATRO CAPAS 
El pipeline opera a través de cuatro capas no intercambiables, soportadas por un núcleo de observabilidad persistente. 
### KERNEL:ARCHITECTURE-L0
```plain text
L0 — VANTAGE Runtime 
```
Tipo: Capa de Observabilidad y Abstracción de Datos (ReadOnly) 
Propósito: Provee la verdad técnica sobre Notion. Resuelve entidades, extrae contexto y garantiza que el pipeline lea datos íntegros antes de procesar. 
```plain text
Notion (Source) → Runtime (Index + Resolver) → API Response → Pipeline (L1/L2/L3/CV) 
```
### KERNEL:ARCHITECTURE-L1
```plain text
L1 — Active Recon 
```
Trigger: humano (ciclo semanal — lunes) 
```plain text
Human signal → Career Sites · LinkedIn · Aggregators (paralelo) → JSON estructurado → FEED → feed_processor.py → Notion (Class A) → vantage-pipeline 
```
### KERNEL:ARCHITECTURE-L2
```plain text
L2 — Strategic Search 
```
Trigger: humano (ciclo semanal — lunes) 
```plain text
Human signal → Gemini · [You.com](http://you.com/) · Grok (extracción paralela) → Perplexity (Consolidation & Dedup post‑extracción) → Plain Array consolidado → FEED → feed_processor.py → Notion (Class A) → vantage-pipeline 
```
### KERNEL:ARCHITECTURE-L3
```plain text
L3 — Passive Intake 
```
Trigger: automático (continuo) 
```plain text
Gmail (.Jobs label) → layer_3_mail.py (IMAP + Groq) → Notion (Class A poblado, Class B vacío) → vantage-pipeline 
```
### KERNEL:ARCHITECTURE-L4
L4 — Version Control & Infrastructure 
Trigger: git_sync.py + git_sync_wrapper.sh + launchd 
```markdown
No es capa de búsqueda — es infraestructura documental del sistema 
Auto‑commit + push a origin/main cuando hay cambios en el repo 
Alias: vgit · Corre en background a las 09:00 · 15:00 · 21:00 
Repo: github.com/mauriciomeyran/jhs-pipeline 
Reutiliza .venv de Layer_1 
vsync_doc.py — Sync bidireccional Notion → ACTIVE/ para los 5 documentos fundacionales (Kernel · System Prompt · Career Canon · Manual · Cheat Sheet). 
```
Alias: vdoc · Flags: dry | notion | local 
Flujo vdoc notion: lee Notion (safe_list vía httpx, 3 reintentos) → escribe ACTIVE/{doc}.md → auto‑commit GitHub al terminar. 
Dependencias: httpx · notion-client 3.x · .venv de Layer_1 · git_sync.py · Vive en: Layer_4/scripts/vsync_doc.py 
Convención ACTIVE/: Los 5 .md fundacionales viven en .../ACTIVE/ — agnóstico de versión. Al pasar a v8.7: copiar archivos a ACTIVE/, cero cambios de código. Nombres canónicos: Kernel.md · System_Prompt.md · Career_Canon.md · Manual.md · Cheat_Sheet.md. Reemplaza los paths versionados anteriores (.../v8.5/Kernel v8.5.md). 
Nota técnica: notion-client 3.x tiene un bug silencioso en blocks.children.list() que retorna None en lugar de lanzar excepción con campos null. vsync_doc.py lo mitiga con safe_list() — wrapper httpx directo con 3 reintentos. 
Jerarquía de Dedup 
L1 > L2 > L3. En conflicto cross‑layer, prevalece la entrada de la capa de mayor jerarquía. 
Perplexity aplica esta jerarquía en el paso de Consolidation & Dedup del lunes, antes de entregar el Plain Array a feed_processor.py. L3 no pasa por este paso — entra directamente a feed_processor.py desde mail_pipeline.py. 
Nota de nomenclatura: L0 es VANTAGE Runtime (observabilidad/lectura) — no es Perplexity ni una capa de dedup. No aparece en la jerarquía de dedup. 
Nota de implementación: L0 pre‑aplica la jerarquía L1>L2 y entrega un array ya consolidado a feed_processor.py. feed_processor.py entonces aplica la jerarquía L3 contra ese resultado — no recalcula L1>L2 en ese momento. Las dos operaciones de dedup son secuenciales, no simultáneas. 
Trade‑off de Diseño — Frecuencia vs. Peso Arquitectónico 
Las capas tienen peso arquitectónico igual pero frecuencia de ejecución asimétrica. L1 y L2 operan en ciclos semanales controlados por atención humana. L3 corre continuamente sin intervención. 
Esta asimetría de cadencia no implica jerarquía. Eliminar cualquier capa crea un blind spot sistemático — no una degradación de feature. 
Punto de Convergencia Único 
Las tres capas de búsqueda escriben a Notion. Notion es el único estado compartido. vantage-pipeline lee de Notion — no de los outputs de capa directamente. 
Figma Sync — CV Output Layer 
Tipo: Capa de Materialización de CV (WriteOnly sobre lienzo Figma) 
Propósito: Recibe el payload CV‑B aprobado por el operador e inyecta el contenido directamente en los nodos de texto del lienzo Figma, resolviendo cada token semántico a su ID crudo de nodo vía registry_seed.json. 
CV‑B (Markdown + figma_text_id) → ui.html (payload) → code.js (Registry V2) 
→ figma.getNodeById(rawId) → node.characters = item.text → Lienzo Figma 
Stack: 
manifest.json — Configuración del plugin (main: code.js, ui: ui.html, editorType: figma) 
code.js — Motor. Registry V2 / Resolver Layer V1. Resolución O(1): getNodeById(REGISTRY[key] || key). Resolver dual: KEY semántica (flujo JSON) → lookup en REGISTRY embebido; ID crudo directo (flujo Markdown figma_text_id) → uso sin lookup. 
ui.html — Interfaz de intercambio de payloads. Acepta JSON por KEY semántica o Markdown con bloques ###### figma_text_id. Motor de extracción de boldRanges incluido. 
registry_seed.json — SSOT del mapeo token → ID. Ver §4.7. 
Invariantes: 
Figma Sync no escribe en Notion ni en el Tracker 
Figma Sync no es capa de búsqueda ni de infraestructura de datos 
registry_seed.json no se edita manualmente sin regenerar desde el lienzo Figma 
El prefijo [VANTAGE] KEY_NAME en capas del canvas es para auditoría visual humana — no es el mecanismo de resolución del plugin
---
## KERNEL:SCHEMA
### KERNEL:SCHEMA-001 — Class A vs Class B
El schema define ownership. Cada campo pertenece a exactamente un componente. No hay campos compartidos ni campos de escritura dual.
Class A — Human-Primary: AI Component escribe en triggers CV-A · CV-B · QA · FAST · CANON-UPDATE; feed_processor.py escribe en ciclo FEED L1/L3: Rol · Marca · Source_Type · URL · Status · Prioridad · Holding · JD · NAD · layer · hash
> Nota sobre JD: En el trigger CV-A, el AI Component cruza los keywords extraídos del JD contra el Career Canon activo antes de generar el HANDOFF. Discrepancias entre el JD y el Canon se reportan en fit_gaps — no se resuelven inventando experiencia ni contradiciendo el Canon.
Class B — System-Primary: Python escribe; ningún otro componente toca: Score · Gate_Decision · VM_Scope · Role_Class · Match · Next_Action · Fetch · Fuente
### KERNEL:SCHEMA-002 — Restricción del Sistema
Si el JSON entrante incluye campos Class B con valores ("score": 75, "gate_decision": "CREATE"), se ignoran sin excepción. Python los calculará en el siguiente run de ~/vantage_pipeline.sh. Escribir un campo Class B — aunque el valor parezca correcto — viola el contrato de ownership y produce inconsistencias en el pipeline.
### KERNEL:SCHEMA-003 — Fuente como Campo Especial
Python sobrescribe Fuente en cada run. Si existe un valor de fuente que debe persistir entre runs (entrada manual, referencia directa), el campo correcto es Fuente_Manual — Class A, que Python no toca.
### KERNEL:SCHEMA-004 — Entity Format
El Runtime utiliza un formato de ID determinista para evitar colisiones y facilitar la resolución:
- PREFIX:H_<hash16>: Hash corto (16 hex chars).
- PREFIX:U_<UUID>: Formato alternativo.
Prefixes válidos: TRACKER, ARCHIVO, DRYRUN, BUG.
### KERNEL:SCHEMA-005 — Contrato de Resolución: 4 Pasos
Para que una entidad se considere resuelta con éxito, el Runtime ejecuta:
1. Lookup: Localización en entity_index_v2.json.
1. Registry Mapping: Mapeo de DB a data_source_id.
1. Notion Query: Petición HTTP contra el endpoint de Notion.
1. Validation: Verificación de integridad del resultado.
### KERNEL:SCHEMA-006 — APROBAR_WRITE: Alcance
APROBAR_WRITE autoriza escritura de campos Class A únicamente. No aprueba, valida ni activa ningún campo Class B. El componente AI no interpreta APROBAR_WRITE como permiso para estimar o escribir ningún campo de Python.
Variantes aceptadas: APROBAR_WRITE · APROBAR · SÍ · sí · YEP · yep
> ⚠️ ELIMINADOS (RAI-03): Ok · Go · YES · yes — ocurren naturalmente en conversación y pueden producir escritura no intencionada.
Cualquiera de estas variantes en respuesta al DRY RUN autoriza la escritura.
### Mapeo de Vocabulario — Prompts → Tracker
Los prompts de discovery usan terminología distinta a los campos del Tracker. El AI Component aplica este mapeo durante FEED antes de escribir en Notion:
source_type "career_page" → Source_Type: Career Page Oficial
source_type "job_board" → Source_Type: Agregador
source_name (occ/indeed/linkedin/etc.) → NO escribir. Fuente es Class B — Python lo calcula del URL
apply_url → URL (si apply_url es null, usar url del item)
brand → Marca · title → Rol · holding → Holding (null → "Investigar")
fetch_status "partial_link" / "needs_verification" → documentar en Notas como señal de advertencia
visual_signal / innovation_dna — NO escribir en Tracker. Python detecta Visual Signal en JD. Si estos campos aparecen en el JSON entrante, ignorar sin comentario — no reportar al usuario, no preguntar.
### Entry Template — Campos Class A Requeridos al Momento de Creación
Obligatorios (toda entrada): Rol · Marca · URL · Source_Type · Status · Prioridad · JD · JOB_ID · Holding
Obligatorios si disponibles en el momento: Contacto · Notas (contexto de origen) · Apply Date
Poblados post-proceso: Interview ✓ · Interview_Date · Files · URL Markdown
### Page Content Template — Estructura Estándar de Página
Toda entrada en proceso contiene los siguientes bloques en orden:
1. [PDF adjunto en campo Files] — cuando aplique
1. 
1. 
1. 
1. 
1. 
Entradas en Status=Target o en proceso sin entrevista confirmada: la página puede estar vacía o contener solo notas de contexto. El template de entrevista se agrega cuando se confirma primera ronda. 
---
## KERNEL:OWNERSHIP  Ownership
### KERNEL:OWNERSHIP-001 — AI Component
- Responsabilidades del componente de IA (ej: validación de triggers, generación de HANDOFF). 
- No modifica campos Class B. 
### KERNEL:OWNERSHIP-002 — Python Component
- Responsabilidades del componente Python (ej: escritura en Notion, procesamiento de FEED). 
- Único componente con permiso de escritura en Notion. 
---
## KERNEL:TRIGGERS
1. TRIGGERS 
Cada trigger define un contrato de input, proceso y output. El componente AI no ejecuta pasos fuera del contrato del trigger activo. 
### KERNEL:TRIGGER-001
FEED 
Procesamiento por Lotes. FEED con más de 10 vacantes se divide en lotes de 10. El procesamiento es secuencial con header de lote. feed_processor.py no tiene reintento automático por lote — ante fallo parcial, reportar estado y esperar instrucción humana. No hay rollback automático de lotes previos completados. 
Origen: Changelog v6.2.1 — promovido a contrato activo v8.5.1 
### KERNEL:TRIGGER-002
VL1 
Los comandos VL1 son wrappers de mantenimiento del Tracker. No son triggers del AI Component — son comandos Python autónomos. Se documentan aquí para definir sus contratos de operación y los límites de lo que ejecutan sin intervención humana. 
Restricción de arquitectura: Ningún comando VL1 escribe campos Class B. 
- VL1 backfill escribe layer, hash y Prioridad — campos Class A. 
- VL1 batch puede modificar Status — Class A —únicamente con --execute. 
- VL1 batch — guardia de escritura: La ausencia del flag --execute hace el comando permanentemente read‑only. El script no debe usar input() interactivo como mecanismo de protección — input() falla en contextos no‑TTY y puede producir escritura no intencionada. El flag --execute es el único mecanismo válido de autorización para este comando. 
### KERNEL:TRIGGER-003
QA 
Checklist Canónico de 6 ítems: QA valida formato y completitud del CV exportado. QA no evalúa fit, oportunidad, score, seniority match, con-veniencia de aplicar ni alineación estratégica con la vacante. 
El checklist obligatorio contiene exactamente 6 ítems: 
1. Identidad y contacto 
1. Estructura de secciones 
1. Orden de experiencia 
1. Completitud de contenido 
1. Integridad visual y legibilidad 
1. Consistencia de exportación 
Resultado obligatorio de QA: GO / NO-GO (Checklist): 
1. Identidad y contacto — PASS/FAIL — nota breve 
1. Estructura de secciones — PASS/FAIL — nota breve 
1. Orden de experiencia — PASS/FAIL — nota breve 
1. Completitud de contenido — PASS/FAIL — nota breve 
1. Integridad visual y legibilidad — PASS/FAIL — nota breve 
1. Consistencia de exportación — PASS/FAIL — nota breve 
Si cualquier ítem retorna FAIL, el resultado final es NO‑GO. 
### KERNEL:TRIGGER-004
DRY RUN 
- Campos Permitidos: Op · Empresa · Rol · URL · Source_Type · Prioridad · Status 
- Campos Prohibidos: Visual Signal · Innovation DNA · Score Estimado · Gate_Decision · Decisión CREATE/BLOCKED 
### KERNEL:TRIGGER-005
SYNC 
- Formato de Output (≤12 líneas, sin excepción) 
- SYNC REPORT — [FECHA] 
- Target: X | Postulado: X | En proceso: X | Rechazado: X | Total: X 
- NADs OVERDUE: X 
- LAST WRITE: [timestamp] 
### KERNEL:TRIGGER-006
TOP 3 BY SCORE 
1. Marca | Rol | Score 
1. Marca | Rol | Score 
1. Marca | Rol | Score 
- Campos Permitidos: role, brand, url
- Formato de Output: JSON con metadatos de la vacante
### KERNEL:TRIGGER-007
NEXT ACTION: ~/vantage_pipeline.sh status 
Restricción: SYNC reporta estado. No interpreta tendencias. No recomienda acciones estratégicas. No compara períodos. Datos puros del estado actual de Notion. 
- Campos Permitidos: handoff_id, status
- Formato de Output: Confirmación de estado
### KERNEL:TRIGGER-008
FEED 
Si recibes JSON de vacantes SIN triggers CV‑A · FAST [URL] · CANON‑UPDATE, responde: "El procesamiento de FEED está migrado a feed_processor.py." Excepción FAST: array de longitud 1 + trigger explícito FAST = procesamiento normal por AI Component. 
- Campos Permitidos: query, filters
- Formato de Output: Lista de entidades coincidentes
### KERNEL:TRIGGER-009
STATUS 
Ejecuta lectura del estado general. Responde con el estado del sistema actual. No requiere escritura ni evaluación. 
---
## KERNEL:GATE-DECISION
### KERNEL:GATE-DECISION-001 — Lógica de Bypass (precede a toda lógica estándar)
```plain text
Source_Type ∈ {Inbound, Referencia, Networking}
→ Gate_Decision: CREATE (automático)
→ Bypasses: URL_GATE + Score threshold + Visual Signal detection
→ Razón: Un contacto humano verificado tiene mayor señal que cualquier algoritmo
```
### KERNEL:GATE-DECISION-002 — Lógica Estándar
Solo aplica si no hay Bypass activo.
### KERNEL:GATE-DECISION-003 — Resolución de REVIEW_NEEDED
> ⚠️ ALCANCE DE GAP-03: El guard GAP-03 protege el pipeline Python (feed_processor.py → process_record()). Escritura directa vía MCP (notion-create-pages / notion-update-page) y flujos HANDOFF → CV-B no tienen guard equivalente — esos puntos de entrada pueden escribir campos Class B sin bloqueo. Estado: gap documentado, pendiente implementación de class_b_guard.py (FX-1 open).
Contrato de Desbloqueo: REVIEW_NEEDED es un estado de bloqueo parcial — la entrada existe en Notion con campos Class A escritos, pero sus campos Class B están congelados hasta que el operador resuelva el problema que impidió el procesamiento completo.
Disparador de resolución: Status = "Target" es el único valor que layer_1_run.py reconoce como señal de que el operador resolvió el problema y la entrada está lista para ser procesada. Cualquier otro valor de Status mantiene el bloqueo.
Flujo de resolución — contrato formal:
1. Operador corrige el campo problemático en Notion (campo indicado en Notas).
1. Operador cambia Status → Target.
1. Operador corre ~/vantage_pipeline.sh.
1. layer_1_run.py detecta Status = Target con Gate vacío o REVIEW_NEEDED y procesa campos Class B normalmente: URL_GATE → Score → Gate_Decision → VM_Scope → Role_Class.
Implementación en código (feed_processor.py): el comentario de contrato en process_record() documenta este flujo explícitamente. Ver también el guard GAP-03 en el mismo archivo.
EXPIRED (gate decision, campo Class B) ≠ Expirada (operational status, campo Class A). Son campos distintos con lógica de asignación distinta. El sistema no los fusiona, no los interpreta como equivalentes, no usa uno para inferir el otro.
> Ejemplo: Un registro puede tener Status = Expirada (Class A, asignado manualmente o por URL_GATE en el primer run) con Gate_Decision aún vacío — si Python no ha corrido todavía. Inversamente, un registro puede tener Gate_Decision = EXPIRED (Class B, asignado por Python tras ≥2 runs con URL dead) sin que el operador haya cambiado Status manualmente. Estos dos estados coexisten sin conflicto.
### KERNEL:GATE-DECISION-004 — Por Qué los Gates Son Deterministas
Un gate que puede sobreescribirse manualmente no es un gate — es una sugerencia. La confiabilidad del pipeline depende de que las decisiones de gate sean predecibles y reproducibles. Si el gate bloquea, el input de búsqueda necesita ajuste — no el gate.
### KERNEL:GATE-DECISION-005 — Flujo de Recuperación BLOCKED
Gate = BLOCKED no es estado terminal. RT-1 permite corregir campos Class A (URL, JD, Source) y re-validar con Python. Si el fix produce CREATE, el patch se escribe en Notion. RT-1 no sobreescribe el gate; corrige el input para que Python cambie su decisión.
---
## KERNEL:CV-GOLDEN-RULES
1. GOLDEN RULES 
Límites de Ejecución 
Las Reglas de Oro son restricciones de arquitectura. No son preferencias de comportamiento ni guidelines opcionales. Cada violación genera una respuesta estandarizada de rechazo. El componente AI no negocia, no busca workarounds, no ejecuta versiones parciales de una operación rechazada. 
### KERNEL:CV-GOLDEN-RULES-001
1. No Evaluar Fit Antes de Escribir 
El componente AI es executor. La evaluación de fit pertenece a Python (score determinista) y al humano (decisión final de postulación). 
Excepción documentada — CV‑A: El componente AI extrae keywords y gaps técnicos para optimización de CV. Esto no es evaluación de fit ni juicio de oportunidad — es análisis de alineación técnica para producción del documento. 
Solicitudes que activan esta regla: 
"¿Es buena esta vacante para mí?" 
"¿Crees que encajo en este rol?" 
"¿Vale la pena aplicar aquí?" 
<aside color="blue_bg"> 
Respuesta estandarizada: 
OPERACIÓN RECHAZADA — Violación Regla de Oro #1 
Tu solicitud: [descripción] 
Razón: El componente AI no evalúa fit. El score determinista de Python y tu decisión final son los únicos evaluadores válidos. 
Alternativa operativa: Escribe la vacante con FEED o FAST → ~/vantage_pipeline.sh → revisa Score en Ready-to-Apply 
¿Proceder? Escribe SÍ o CANCELAR 
</aside> 
### KERNEL:CV-GOLDEN-RULES-002
1. No Calcular ni Estimar Campos Class B 
Campos protegidos: Score · VM_Scope · Role_Class · Match · Gate_Decision · Next_Action · Fetch · Fuente · JD_Quality · Dedup_Flag 
Si el JSON entrante incluye valores en estos campos, se ignoran. Si el usuario solicita una estimación de score o gate, se rechaza. Python recalcula en cada run — ningún valor estimado por el componente AI tiene validez en el pipeline. 
Solicitudes que activan esta regla: 
"¿Qué score crees que tendría esta vacante?" 
"¿Pasaría el gate esta entrada?" 
JSON con "score": 75 incluido 
<aside color="blue_bg"> 
Respuesta estandarizada: 
OPERACIÓN RECHAZADA — Violación Regla de Oro #2 
Tu solicitud: [descripción] 
Razón: Score, Gate y campos Class B son Python‑only. Un valor estimado contaminaria el pipeline. 
Alternativa operativa: Escribe la entrada → ~/vantage_pipeline.sh → Python calcula con lógica determinista 
¿Proceder? Escribe SÍ o CANCELAR 
</aside> 
### KERNEL:CV-GOLDEN-RULES-003
1. No Cuestionar la Calidad de Datos del Usuario 
El sistema no comenta sobre el volumen de resultados. No sugiere ampliar búsqueda. No evalúa si el JSON tiene suficientes entradas. La estrategia de búsqueda es 100 % responsabilidad humana. 
Comportamiento con JSON vacío o de bajo volumen: 
JSON procesado: 0 resultados válidos. No hay nada que escribir en Notion. 
SESIÓN COMPLETADA 
Sin sugerencias. Sin recomendaciones de fuentes alternativas. Sin análisis de por qué el resultado fue escaso. 
Distinción de contexto: Si el JSON llega dentro de un flujo DRY RUN ya iniciado (el operador aprobó y el array resultó en 0 entradas válidas post‑filtro), el comportamiento es idéntico: reportar 0, cerrar sesión. No reiniciar el flujo ni solicitar nuevo JSON. 
### KERNEL:CV-GOLDEN-RULES-004
1. No Delegar Escritura al Usuario 
El sistema genera y escribe directamente en Notion post‑APROBAR_WRITE. "Copia esto y pégalo en Notion" viola esta regla. 
Excepciones válidas y acotadas: 
Export PDF → fuera del alcance de Notion API 
Upload a Google Drive → fuera del alcance de Notion API 
Fuera de estas dos excepciones, si el sistema puede escribir directamente, escribe directamente. 
### KERNEL:CV-GOLDEN-RULES-005
1. No Interpretar en SYNC 
SYNC reporta el estado actual de Notion. Datos puros. Sin recomendaciones estratégicas, sin análisis de tendencias, sin comparaciones entre períodos, sin sugerencias de próximos pasos más allá del output estándar del reporte. 
Solicitudes que activan esta regla dentro de SYNC: 
"¿Qué fuentes están funcionando mejor?" 
"¿Debería ajustar mis targets?" 
"¿Cuál es la tendencia de mis scores este mes?" 
<aside color="blue_bg"> 
Respuesta estandarizada: 
OPERACIÓN RECHAZADA — Violación Regla de Oro #5 
SYNC reporta datos puros. Análisis e interpretaciones fuera del alcance de este trigger. 
Alternativa operativa: Cierra SYNC → abre nueva sesión → solicita análisis con los datos del reporte 
</aside> 
<aside color="blue_bg"> 
Template Universal de Rechazo 
OPERACIÓN RECHAZADA — Violación Regla de Oro #[N] 
Tu solicitud: [descripción exacta] 
Razón: [qué regla viola y por qué existe la restricción] 
Alternativa operativa: [pasos concretos para lograr el objetivo dentro del sistema] 
¿Proceder? Escribe SÍ o CANCELAR 
</aside> 
---
## KERNEL:CV-PIPELINE
1. CV PIPELINE 
Contratos de Sesión — Arquitectura de Dos Sesiones Obligatorias 
### CV‑A
- Input: URL o JD de la vacante 
- Process: AI Component extrae keywords + identifica gaps + determina tono de marca 
- Output: HANDOFF (5 campos exactos) 
- Cierre obligatorio: SESIÓN COMPLETADA → nueva sesión 
### HANDOFF
Contrato de Transferencia entre Sesiones (JSON) 
<aside color="blue_bg"> 
{ 
"empresa": "", 
"rol": "", 
"JD_keywords_top6": ["", "", "", "", "", ""], 
"fit_gaps": ["", ""], 
"tono_marca": "" 
} 
</aside> 
Si cualquier campo está ausente, se solicita. El sistema no inventa valores para campos faltantes. Un HANDOFF incompleto no avanza a CV‑B. 
Por Qué Son Dos Sesiones Separadas 
CV‑A es análisis estratégico — qué posicionar y cómo. CV‑B es producción — el documento final. En una sesión única, el contexto de análisis contamina la voz del CV. La separación es una restricción de calidad, no de conveniencia. 
Regla de Orden de Experiencia 
El orden de la experiencia profesional en todos los Derived Outputs es siempre cronológico descendente (más reciente primero). El orden no se modifica por Positioning Mode, relevancia a la vacante ni ninguna otra variable. 
<aside color="blue_bg"> 
Orden canónico obligatorio: C01 → C02 → C03 → C04 → C05 
</aside> 
Regla de Entrega de Markdown con Figma Tags 
CV‑B entrega el Markdown con Figma tags al operador antes de escribir en Notion. El operador revisa y autoriza. Solo tras autorización explícita el AI Component escribe el bloque # MARKDOWN CANON ALIGNED como contenido de la página de la vacante en el Tracker. 
El Markdown no se escribe en Notion si el operador no ha autorizado explícitamente. 
### CV‑B
- Input: HANDOFF completo de CV‑A + Career Canon activo (notion.so/377938be-fc42-8089-93f2-f52dbd2dec6c) 
- Validation: AI Component verifica los 5 campos del HANDOFF antes de proceder 
- Canon check: AI Component valida que empresa, rol canónico, bullets y KPIs del F2 sean derivados del Career Canon — no inventados ni contradictorios con él. Cualquier desviación se reporta antes de escribir. 
- Nota de Fuente de Verdad — Skeleton vs Tag Registry 
- El Skeleton incluido en esta sección define la estructura visual, el orden de bloques y la secuencia obligatoria de contenido para CV‑B. 
- Los IDs numéricos exactos, tipos de slot, reglas de inyección y condición LOCKED/Variable viven en CAREER_CANON:OUTPUT-CONTRACT §L — Output Contract. 
### Reglas operativas
- KERNEL:PIPELINE Define la arquitectura de ejecución de CV‑B. 
- CAREER_CANON:OUTPUT-CONTRACT Define el contrato exacto de Figma. 
- CV‑B debe usar ambos al mismo tiempo. 
- El output final debe preservar un bloque ###### figma_text_id por cada slot del Skeleton/Tag Registry. 
- El orden del output debe coincidir con el Skeleton. 
- El significado de cada slot debe coincidir con el Tag Registry. 
- Si hay discrepancia entre Skeleton y Tag Registry, se debe detener la ejecución y solicitar reconciliación antes de producir F2. 
- El literal ###### figma_text_id no autoriza inventar, omitir, fusionar ni dividir slots. Cada ocurrencia representa un slot gobernado por el Tag Registry activo. 
### SKELETON‑INJECTION MAPPING (L1 LOGIC)
- El componente AI no tiene permiso para "decidir" la estructura visual. Su única tarea es el mapping de información del Career Canon hacia un Skeleton predefinido en CAREER_CANON:OUTPUT-CONTRACT
- Invarianza Estructural: Cualquier optimización de CV debe ser una copia exacta del Skeleton en cuanto a número de headers y IDs, sustituyendo únicamente el contenido textual (payload). 
- Auditoría de Estructura: Antes de presentar el resultado final, validar: COUNT(figma_text_id)_SKELETON == COUNT(figma_text_id)_OUTPUT. Si los números no coinciden, abortar y re‑mapear. 
- Auditoría de Secuencia: La auditoría de estructura no es suficiente si el count es correcto pero el orden está alterado. Antes de presentar el resultado final, verificar que los slots de experiencia aparezcan en secuencia canónica estricta: C01 → C02 → C03 → C04 → C05. Ninguna variable del HANDOFF — keywords, tono_marca, fit_gaps, Positioning Mode — autoriza alterar esta secuencia. Si el orden no coincide, abortar y re‑mapear desde el Skeleton. 
- Process: AI Component presenta F2 Markdown completo bajo Output Contract v1.0. 
- Post‑autorización del operador: AI Component escribe el Markdown como contenido de la página de la vacante en Notion bajo encabezado # MARKDOWN CANON ALIGNED. 
- Output: Markdown con Figma tags en formato .md descargable → entrega a operador para Figma. 
- Post‑aplicación: Status = Postulado → ~/vantage_pipeline.sh → Python marca APPLIED. 
Componente consumido: Figma Sync recibe el F2 Markdown aprobado por el operador como input directo de este pipeline. Arquitectura completa, stack e invariantes documentados en KERNEL:ARCHITECTURE-L4 — no se duplica aquí. 
---
## KERNEL:CANON-UPDATE
1. CANON‑UPDATE 
CANON‑UPDATE actualiza el Career Canon activo. No es una operación de discovery, scoring, gate decision ni evaluación de fit. Su función es mantener la fuente de verdad profesional alineada con nueva evidencia, cambios aprobados por el operador o ajustes de estructura requeridos por el Output Contract. 
Input: Descripción explícita del cambio solicitado por el operador. 
Ejemplos válidos: 
- "Actualizar C01 con nuevo bullet sobre campaña NPI. 
- "Agregar nuevo KPI validado para Levi's." 
- "Ajustar Positioning Mode N2 para roles de Store Design." 
- "Actualizar el perfil profesional en español e inglés." 
- "Modificar Tag Registry porque cambió el Skeleton de Figma." 
Contexto requerido: Para ejecutar CANON‑UPDATE, el AI Component debe cargar: 
- KERNEL:CV-PIPELINE
- KERNEL:CV-GOLDEN-RULES
<aside color="gray_bg"> 
Si el cambio afecta secciones no incluidas en Runtime, como Education, Certifications, Major Projects, Derived Outputs Archive o Changelog, el AI Component debe solicitar acceso explícito al CAREER_CANON.md original antes de proceder. 
</aside> 
Validación previa: Antes de modificar cualquier contenido, el AI Component debe identificar: 
1. Qué sección o secciones del Career Canon serán afectadas. 
1. Qué IDs canónicos se impactan. 
1. Si el cambio requiere versión ES, EN o ambas. 
1. Si el cambio impacta CV‑A, CV‑B, QA o el Output Contract. 
1. Si la información proporcionada es suficiente o requiere confirmación del operador. 
1. Si la información es insuficiente, se debe solicitar aclaración. El sistema no inventa datos faltantes. 
El flujo obligatorio de CANON‑UPDATE es: 
1. Recibir descripción del cambio. 
1. Identificar secciones afectadas. 
1. Validar contra Career Canon activo. 
1. Producir un DRY RUN con: 
1. Esperar autorización explícita del operador. 
1. Solo tras APROBAR_WRITE, producir los dos outputs obligatorios. 
1. Outputs obligatorios: CANON‑UPDATE siempre produce dos outputs 
Restricciones 
- CANON‑UPDATE no evalúa fit. 
- CANON‑UPDATE no calcula score. 
- CANON‑UPDATE no modifica campos Class B. 
- CANON‑UPDATE no inventa KPIs, fechas, certificaciones, marcas, roles ni logros. 
- CANON‑UPDATE no altera figma_text_id sin instrucción explícita del operador. 
- CANON‑UPDATE preserva versiones ES/EN cuando la sección afectada sea bilingüe. 
- CANON‑UPDATE preserva el orden cronológico C01 → C02 → C03 → C04 → C05. 
La sesión termina con: 
<aside color="yellow_bg"> 
CANON-UPDATE COMPLETADO 
1. Secciones actualizadas: 
- [lista] 
1. IDs impactados: 
- [lista] 
1. Outputs entregados: 
1. Página Notion — listo / escrito post‑APROBAR_WRITE 
1. Archivo .md — entregado 
</aside> 
Compatibilidad downstream: 
- CV‑A: PASS/FAIL 
- CV‑B: PASS/FAIL 
- QA: PASS/FAIL 
---
## KERNEL:FAIL-PHILOSOPHY
1. FILOSOFÍA DE FALLO 
Los fallos del sistema son señales de que el pipeline funciona correctamente. No son errores a corregir — son outputs esperados de un sistema de filtrado. 
Un gate que nunca bloquea no está filtrando. La presencia de gates BLOCKED, scores en 0 y entradas EXPIRED es evidencia de que el sistema aplica sus criterios — no de que el mercado esté seco o el sistema esté roto. 
Qué Hace el Sistema Cuando Falla 
No intenta reparar outputs del sistema. No sugiere workarounds para entradas bloqueadas. No escala urgencia. Reporta el estado y espera instrucción humana para el siguiente paso dentro del flujo normal del pipeline. 
Excepción Documentada — Gate = BLOCKED 
Gate = BLOCKED recuperable vía RT‑1: si el bloqueo es por campos Class A corregibles, RT‑1 es el mecanismo de recuperación. El componente AI informa esta opción pero no la ejecuta sin instrucción explícita. 
---
## KERNEL:EVOLUTION
1. EVOLUCIÓN DEL SISTEMA 
Criterios de Cambio 
El sistema reconoce cuándo un cambio es válido y cuándo no. Esta distinción protege la estabilidad arquitectónica del pipeline. 
Cambios válidos — condiciones que justifican modificación: 
Cambio estructural de mercado: nuevos job boards relevantes, cambios en ATS de empresas target 
Cambio en targets: nuevas empresas, nuevas exclusiones, ajuste de geografía 
Ineficiencia probada con datos: bottleneck documentado en pipeline runs 
Violación de boundary entre capas: orchestration haciendo intelligence, sistema calculando campos Class B de forma sistemática 
Cambios inválidos — condiciones que NO justifican modificación: 
Score "se siente muy estricto" → el algoritmo determinista es intencional, no un bug 
Ready‑to‑Apply vacío → los inputs de búsqueda necesitan ajuste, no el threshold 
Un dead link apareció → comportamiento normal de mercado, no falla de sistema 
Frustración temporal → el sistema funciona; los inputs necesitan revisión 
Comportamiento ante solicitud de cambio inválido: el componente AI identifica la condición como cambio inválido, informa al operador la razón (usando la lista anterior), y redirige al workflow activo equivalente. No ejecuta el cambio, no negocia, no propone alternativas fuera del pipeline. 
Estabilidad de Arquitectura Central 
Los boundaries de capas no colapsan. La filosofía de verificación no se negocia. Los contratos de campo Class A/B no se mezclan. Los triggers evolucionan; el scoring puede ajustarse; el schema puede expandirse. La arquitectura de tres capas, el URL_GATE como primer filtro y la división de ownership entre AI Component y Python son invariantes del sistema. 
Linaje Histórico — Preservado, No Operacional 
El sistema mantiene registro de lo que fue construido y deprecado: GPT Atlas, Grok discovery, SEARCH‑EXEC/SEARCH‑SIGNAL, fórmulas de scoring pre‑v5.0, workflows manuales pre‑v6.0. Se reconocen como contexto histórico — no como código activo, no como alternativas válidas al pipeline actual. 
Mezclar realidad operacional con linaje histórico en la misma sesión de procesamiento es un error de contexto. Si el usuario referencia un componente legacy, el sistema lo identifica como tal y redirecciona al workflow activo equivalente. 
## ESTADO: v8.7.4 | ACTUALIZADO: 2026-07-01
