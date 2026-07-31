# V | CHANGELOG

### v9.10.4 — Documentación Transversal: SP:SCHEMA Alineado con Schema Vivo de Notion · 2026-07-31
Tipo: [DOC] [FIX]
Alcance: System Prompt (SP:SCHEMA, sección 08).
Contexto: SP:SCHEMA documentaba solo 7 de 13 campos reales del Bug Tracker y 7 de 10 del Tasks Tracker (confirmado vía fetch directo de ambos data sources). Gap detectado al intentar llenar Fecha_Resolución en un ticket recién cerrado — el campo no aparecía en el schema documentado pese a existir en Notion.
Cambios:
- SP:SCHEMA — Bug Tracker: alta de Fecha_Resolución, Solución, Etiquetas, Archivar, Mantener, Creado.
- SP:SCHEMA — Tasks Tracker: alta de Fecha_Cierre, Archivar, Mantener, Creado.
IDs afectados: ninguno — extensión de contenido sobre SP:SCHEMA existente, no alta de ID nuevo. Census no requiere regeneración.
Write-Back Verification: System Prompt re-fetched tras la escritura de contenido — confirmado sin mismatch.
Pendiente (fuera de esta entrada): vversions --sync para propagar versión a los fundacionales restantes.
Versión actualizada: 9.10.4 (CHANGELOG + SYSTEM PROMPT). El resto de los fundacionales permanece en versión previa hasta vversions --sync.
---
### v9.10.3 — TOC del Manual y Tabla 08.6 Convertidas a Bloques de Tabla Reales · 2026-07-30
Tipo: [FIX]
Alcance: Manual (TOC / DECLARACIÓN DE AUDIENCIA Y ALCANCE, MANUAL:CADENCE-MATRIX).
Contexto: El operador identificó, vía captura de pantalla, que la TOC del Manual (tabla de 21 filas con #/ID/Sección/Porción) nunca fue un bloque <table> real de Notion — era texto plano con pipes | y 
 dentro de un bullet, por lo que se renderizaba como texto corrido en vez de tabla. Mismo patrón de fricción ya identificado en la tabla 08.6 (4 filas de nota fragmentadas con celdas vacías), corregida en esta misma sesión previamente.
Cambios:
- Manual — TOC (bajo "DECLARACIÓN DE AUDIENCIA Y ALCANCE"): convertida de texto plano (| # | ID | ... |
) a bloque <table header-row="true"> real, 21 filas + header, preservando todos los links existentes (§18–§21).
IDs afectados: ninguno — cambio puramente estructural de contenedor (texto → tabla), sin alterar contenido ni IDs. Census no requiere regeneración.
Write-Back Verification: Manual re-fetched de forma independiente tras la escritura — tabla confirmada con las 21 filas correctas, links preservados, sin residuo del formato anterior.
Pendiente (fuera de esta entrada): vversions --sync para propagar versión a los fundacionales restantes (heredado, aún no ejecutado). Revisión humana del resto del Manual (01–07, 09–21) en curso por el operador — pendiente aviso de cierre antes de generar plantilla de referencia para KERNEL/Career Canon.
Versión actualizada: 9.10.3 (CHANGELOG). El resto de los fundacionales permanece en v9.10.0/v9.9.x hasta vversions --sync.
---
### v9.10.2 — Corrección de Terminología (Bloque vs. Línea) + Alta de Criterio 6: Concreción de Títulos · 2026-07-30
Tipo: [DOC] [FIX]
Alcance: Manual (MANUAL:PATCH-QUALITY).
Contexto: El operador editó manualmente 08–08.6 con el patrón real vigente — ID y título unidos por 
 dentro de un único bloque de heading, no "dos líneas contiguas" como quedó redactado en v9.10.1. Se identificó que "línea" es un término ambiguo entre la capa visual (donde ambos patrones parecen "dos renglones") y la capa de bloque Markdown/Notion (donde son estructuras distintas: un bloque con 
 interno vs. dos bloques heading consecutivos). El operador también solicitó formalizar que los títulos deben ser concretos/ilustrativos, no descriptivos-compuestos.
Cambios:
- Manual — MANUAL:PATCH-QUALITY (§15), criterio 1: redacción corregida de "líneas contiguas" a "un único bloque de heading... unión por 
 interno", explicitando que el criterio de éxito es la estructura de bloque, no el conteo visual de líneas.
- Manual — MANUAL:PATCH-QUALITY (§15), alta de criterio 6 (Concreción de títulos): títulos deben ser ilustrativos/concretos, no construcciones semánticas compuestas.
- Ajuste de conteo en encabezado y cierre del bloque ("cinco" → "seis" criterios) para reflejar el nuevo total.
IDs afectados: ninguna alta/baja — extensión de contenido sobre MANUAL:PATCH-QUALITY, ID ya existente. Census no requiere regeneración.
Write-Back Verification: Manual re-fetched de forma independiente tras cada escritura — confirmado sin mismatch en las 3 pasadas (corrección criterio 1 + alta criterio 6, ajuste de conteo cierre, ajuste de conteo apertura).
Pendiente (fuera de esta entrada): Reformateo masivo pendiente de KERNEL + Career Canon + resto del Manual (secciones 01–07, 09–21) para alinear con el patrón de bloque único 
 ya vigente en 08–08.6 — mapeo formal aún no ejecutado. vversions --sync para propagar versión a los fundacionales restantes (heredado, aún no ejecutado).
Versión actualizada: 9.10.2 (CHANGELOG). El resto de los fundacionales permanece en v9.10.0/v9.9.x hasta vversions --sync.
---
### v9.10.1 — Documentación Transversal: Continuidad ID+Título en Bloque de Encabezado · 2026-07-30
Tipo: [DOC]
Alcance: Manual (MANUAL:PATCH-QUALITY, criterio 1).
Contexto: El operador detectó (evidencia visual, dos capturas de Notion UI) espacio vertical entre el identificador técnico y el título descriptivo de un heading (ej. "08 MANUAL:WEEKLY-FLOW" y su título). Confirmado como artefacto de rendering de Notion entre dos heading_2 consecutivos — no hay blank line real en el Markdown fuente vía API. El operador solicitó formalizar la regla igualmente, en forma genérica (sin ejemplo de nodo específico), para prevenir que un colaborador futuro (Devin/Mistral) intente "corregir" el rendering insertando contenido de separación real.
Cambios:
- Manual — MANUAL:PATCH-QUALITY (§15), criterio 1: extensión de la misma oración ya existente sobre nivel de heading, agregando la regla de continuidad ID+título en líneas contiguas del mismo bloque, con aclaración explícita de que el espaciado de Notion es artefacto de plataforma, no instrucción de contenido. Redacción genérica, sin referencia a un nodo particular.
IDs afectados: ninguna alta/baja — extensión de contenido sobre MANUAL:PATCH-QUALITY, ID ya existente. Census no requiere regeneración.
Write-Back Verification: Manual re-fetched de forma independiente tras la escritura — texto confirmado sin mismatch.
Pendiente (fuera de esta entrada): vversions --sync para propagar versión a los fundacionales restantes (heredado de v9.10.0, aún no ejecutado).
Versión actualizada: 9.10.1 (CHANGELOG). El resto de los fundacionales permanece en v9.10.0/v9.9.x hasta vversions --sync.
---
### v9.10.0 — Auditoría de Jerarquía Tipográfica + Documentación Transversal: Matriz Congelada · 2026-07-30
Tipo: [AUDIT] [DOC]
Alcance: Kernel (37 headings + KERNEL:DOCUMENTATION-001), Career Canon (24 headings), Manual (MANUAL:PATCH-QUALITY).
Contexto: Auditoría determinística de jerarquía tipográfica sobre los 6 documentos fundacionales, verificada de forma cruzada entre Perplexity/Sonnet 5, Mistral y Claude vía MCP. Hallazgo central: el nivel ## para capítulos/secciones canónicas ya era uniforme en los 6 documentos; la inconsistencia real estaba en subsecciones NN.N, tipografiadas al mismo nivel que su capítulo padre en Kernel y Career Canon (Navigation Brief ya las tenía correctas en ###). Se congeló la matriz: Documento=#, Capítulo/Sección canónica=##, Subsección (NN.N)=###, Figma Tag (derivados)=######.
Cambios:
- Kernel: 37 headings de subsección (§03.1–03.11, §04.1–04.4, §05.1–05.2, §07.1–07.7, §08.1–08.2, §09.1–09.11) migrados de ## a ###. Efecto colateral: línea de título duplicada preexistente en Career Canon §06.11 (CANON:UF-003) quedó resuelta por el mismo write (old_str capturó la línea completa con el defecto).
- Career Canon: 24 headings de subsección (§03.1–03.5, §06.1–06.11, §07.1–07.4, §08.1–08.4) migrados de ## a ###.
- Kernel — KERNEL:DOCUMENTATION-001 (§03.1): nuevo párrafo "Matriz Tipográfica Congelada (Jerarquía de Encabezados)", insertado entre la tabla de Prefijos Autorizados y Reglas de Migración — extensión de ID existente, no alta.
- Manual — MANUAL:PATCH-QUALITY (§15): nota agregada bajo el criterio #1 ("Invisibilidad estructural"), precisando que el nivel de heading Markdown es parte de esa invisibilidad, con referencia cruzada a KERNEL:DOCUMENTATION-001 — extensión de ID existente, no alta.
Verificación de riesgo descartado: SECTION_HEADING_PREFIX_RE en generate_census.py opera sobre el símbolo § legacy en el cuerpo del heading, no sobre el nivel Markdown — confirmado agnóstico al cambio ##→###. Verificación adicional: ningún heading vivo en los 6 documentos inicia con § — el regex es código legacy sin impacto activo (deuda técnica cosmética, no riesgo).
IDs afectados: ninguna alta/baja — 61 cambios de nivel Markdown sobre IDs ya existentes (Kernel + Career Canon) + 2 extensiones de contenido sobre IDs ya existentes (KERNEL:DOCUMENTATION-001, MANUAL:PATCH-QUALITY). Census no requiere regeneración (CENSUS-SYNC-R1 no se dispara).
Write-Back Verification: Kernel y Career Canon re-fetched de forma independiente tras cada lote — 61/61 headings confirmados en ###, contenido de cuerpo intacto. Kernel y Manual confirmados tras Lote B — sin mismatch.
Pendiente (fuera de esta entrada):
- Ticket registrado en Task Tracker: anidamiento de bloques toggle (indentación \t) en Career Canon §C02–C05/KPI/FACT/UF/Positioning N2–N4 — hallazgo estructural independiente de la jerarquía tipográfica, fuera de alcance de esta operación.
- vversions --sync para propagar v9.10.0 a los fundacionales.
Versión actualizada: 9.10.0 (CHANGELOG). El resto de los fundacionales permanece en v9.9.9/v9.9.8 hasta vversions --sync.
---
### v9.9.9 — Documentación Transversal: Matrices de Estado y Cadencia · 2026-07-29
Tipo: [DOC]
Alcance: V | KERNEL (§09.11), V | MANUAL (§08.6).
Contexto:
Auditoría arquitectónica previa identificó ausencia de referencias tabulares consolidadas para (a) la máquina de estados del pipeline y (b) el flujo de triggers semanal. Los documentos tenían la información en prosa distribuida en múltiples secciones, sin vista indexada para scripts/auditorías. Se inyectan dos matrices de referencia puras — adiciones aditivas, sin tocar contenido existente.
Cambios:
- KERNEL §09.11 KERNEL:GATE-DECISION-011: Matriz de Transición de Estados — 13 transiciones, cubre todos los caminos desde [ENTRY] hasta terminales (APPLIED, REJECTED, BLOCKED). Incluye nota de precedencia gate_logic() → gate() (Hallazgo 2 de auditoría). Insertada inmediatamente antes de §10 KERNEL:CV-GOLDEN-RULES.
- MANUAL §08.6 MANUAL:CADENCE-MATRIX: Matriz de Cadencia Operativa — 5 triggers con contexto de invocación, objetivo y resultado en Tracker. Insertada después de §08.5 Viernes, antes de §09 MANUAL:VANTAGE-RUNTIME.
IDs afectados:
- Altas: KERNEL:GATE-DECISION-011, MANUAL:CADENCE-MATRIX — 2 IDs nuevos.
- Bajas: ninguna.
- Census: pendiente regenerar (vcensus) para registrar los 2 nuevos IDs.
Write-Back Verification: Ambas páginas Notion confirmadas OK vía API response.
Pendiente:
- vcensus para incorporar los 2 nuevos IDs al Census.
- vversions --sync para propagar v9.9.9 a los fundacionales.
Versión actualizada: 9.9.9 (CHANGELOG). El resto de fundacionales permanece en v9.9.8 hasta vversions --sync.
---
### v9.9.8 — Normalización de CENSUS_SPEC: Adopción de IDs Huérfanos y Alineación con Documentos Reales · 2026-07-29
Tipo: [DOC] [FIX]
Alcance: Layer_1/scripts/generate_census.py (CENSUS_SPEC), V_ID_CENSUS_PRODUCTION.md (validación implícita).
Contexto:
El CENSUS_SPEC mantenía referencias a IDs legacy con sufijo -001 (ej: MANUAL:OBJECTIVE-001, BRIEF:001, CANON:PROFILE-001, SP:BOOTSTRAP-001) que no existían en los documentos reales, generando 21 IDs sin link + 38 huérfanos. Los documentos ya usaban IDs sin sufijo (ej: MANUAL:OBJECTIVE, BRIEF:PURPOSE-SCOPE) o nombres descriptivos, pero el spec no se había actualizado.
Cambios:
- MANUAL: Reemplazo de 21 IDs con sufijo -001 por versiones canónicas sin sufijo (ej: MANUAL:OBJECTIVE-001 → MANUAL:OBJECTIVE).
- CAREER CANON: IDs padres sin -001 (ej: CANON:PROFILE, CANON:SKILLS) + lookup_ids para retrocompatibilidad con variantes legacy.
- NAVIGATION BRIEF: Reemplazo de BRIEF:001–BRIEF:011 por nombres descriptivos (ej: BRIEF:PURPOSE-SCOPE, BRIEF:AUTHORITY-MATRIX) + lookup_ids para mapear IDs antiguos.
- SYSTEM PROMPT: Alineación de IDs padres (ej: SP:BOOTSTRAP con lookup_ids: ["SP:BOOTSTRAP-001", "SP:BOOTSTRAP"]).
- Subsecciones: Se mantienen con sufijo -001 (ej: KERNEL:DOCUMENTATION-001) según regla de diseño.
IDs afectados:
- Altas: Ninguna (solo renombres).
- Bajas: 21 IDs legacy con -001 (MANUAL, CAREER CANON, BRIEF, SYSTEM PROMPT).
- Modificados: 4 secciones del CENSUS_SPEC (MANUAL, CAREER CANON, NAVIGATION BRIEF, SYSTEM PROMPT).
- Census: 0 huérfanos (antes: 21 sin link + 38 huérfanos).
Write-Back Verification:
- generate_census.py validado con py_compile (sin errores de sintaxis).
- vcensus ejecutado: 162/162 IDs resueltos (confirmado por operador en Terminal).
Pendiente (fuera de esta entrada):
- verify_versions.py --sync para propagar v9.9.8 a los 6 documentos fundacionales.
- Auditar KERNEL:CV-GOLDEN-RULES-001–005 (sección hardcodeada en Census vs. formato canónico en Kernel).
Versión actualizada: 9.9.8 (CHANGELOG + CENSUS_SPEC). El resto de los fundacionales permanece en v9.9.7 hasta verify_versions.py --sync.
---
### v9.9.7 — Patch 1 real: Estados Terminales Protegidos + Atomicidad RT-1 · 2026-07-29
Tipo: [FIX] [DOC]
Alcance: Layer_1/scripts/gate_logic.py, Layer_1/scripts/layer_1_run.py, Dashboard/scripts/dashboard_routes.py, Dashboard/scripts/dashboard_notion.py, KERNEL §09.10, ID CENSUS.
Contexto: El Hallazgo 1 de la auditoría (precedencia gate_logic() inalcanzable por código muerto) había sido reportado como COMPLIANT por Devin sin estarlo. En esta sesión se implementó y verificó el fix real, más el prerrequisito de clear atómico Class B en RT-1 para no romper el feedback loop.
Código:
- gate_logic.py — constantes de módulo TERMINAL_ACTIONS = {"Archivar", "Expirada"} y STATUS_TERMINAL_MAP = {"Postulado": "APPLIED", "Rechazado": "REJECTED"}; retorna valor terminal o None.
- layer_1_run.py — import de constantes; precedencia obligatoria protected = gate_logic(entry); if protected is not None: continue antes de gate().
- dashboard_notion.py — soporte de clear: None en select → {"select": null}.
- dashboard_routes.py — en /accept, merge atómico de next_action=None + gate=None con el patch del operador (evita fantasmas post-RT-1).
Smoke test: python3 scripts/layer_1_run.py --dry-run — sin crash; PROTEGIDAS: 1; CREATE: 39; APPLIED/REJECTED: 0; total 43.
Documentación:
- KERNEL: nuevo KERNEL:GATE-DECISION-010 (§09.10) — Definición de Estados Terminales Protegidos (doble criterio Status + Next_Action, invariantes, refs).
- TOC KERNEL §09 actualizado.
- ID CENSUS: fila KERNEL:GATE-DECISION-010 (ancla pendiente de verificación en vivo vía generate_census.py).
IDs afectados: alta de KERNEL:GATE-DECISION-010. CENSUS-SYNC-R1 disparado — regenerar Census antes de cerrar ticket asociado.
Pendiente (fuera de esta entrada): regenerar Census para resolver ancla real de §09.10; vversions --sync para propagar versión a fundacionales; campo Score_Method en schema Notion; verificar dedup histórico Status=Rechazado en código real.
Versión actualizada: 9.9.7 (esta página — CHANGELOG). KERNEL / Census tocados en contenido; propiedad Versión de fundacionales permanece hasta verify_versions.py --sync.
---
### v9.9.6 — Resolución de Auditoría Arquitectónica y Bump de Versión · 2026-07-29
Tipo: [AUDIT] [FIX]
Alcance: Layer_1/scripts/layer_1_run.py, Layer_1/scripts/dedup_fix_verified.patch, Bug Tracker (3ac938be-fc42-8149-a909-c8a1b426e7e6), Kernel.md, Manual.md, CHANGELOG.md.
- Controversia A (Tiempo/Calendario vs. Flujo de Estados):
- Riesgo: Confusión entre cronología operativa (Lunes/Martes) y transiciones de datos (estados de vacantes).
- Cambio: Separación de diagramas: Ciclo de Vida de la Vacante (grafo de estados puro) vs. Cadencia Operativa (Gantt/checklist de invocación humana).
- Regla: Ninguna transición de estado puede llevar como etiqueta un día de la semana (solo eventos/comandos como feed_processor.py o Status→Target).
- Controversia B (Límites de Ownership: Python vs. IA):
- Riesgo: Superficie de ataque en escritura directa vía MCP sin guard equivalente a feed_processor.py.
- Cambio: Representar ingesta como dos sub-procesos secuenciales:
- Fase 1 (AI): Generación de JSON (Class A único: Rol, Marca, URL, etc.).
- Fase 2 (Python): Cálculo de Class B (Score, Gate_Decision, etc.).
- Regla: Todo flujo desde IA/Feed hacia Notion debe pasar por un nodo de validación explícito ([FILTRO CLASS B]).
- Controversia C (Loopback de Recuperación RT-1/Dashboard):
- Riesgo: Representación lineal del Dashboard oculta su naturaleza de feedback loop determinista.
- Cambio: Dashboard como ciclo cerrado de retroalimentación con 4 puntos de retorno al pipeline principal:
```javascript
BLOCKED → [Dashboard: Patch Class A] → Validar (dry-run) → PATCHED → Aceptar → RETURNED_TO_CREATE → vantage_pipeline.sh
```
- Regla: Toda flecha desde Dashboard hacia Notion debe re-entrar a vantage_pipeline.sh (nunca directa a READY_TO_APPLY).
---
| Hallazgo | Riesgo | Mitigación |
| --- | --- | --- |
| Ventana de Dedup vs. Persistencia de Estados Terminales | Reaplicación a roles rechazados previamente (Status=Rechazado). | Extender clave de dedup con fingerprint histórico para bloquear REJECTED_RECURRING sin confirmación humana. |
| Desincronización gate() vs. gate_logic() | Regresión de estado (ej: APPLIED → BLOCKED). | Documentar orden de precedencia: gate_logic() primero (filtro de mutabilidad), luego gate(). |
| Bypass de Inbound/Referencia/Networking | Contaminación de Class B con Score=null. | Añadir campo Score_Method (DETERMINISTIC/BYPASS) para distinguir visualmente en el Tracker. |
| Ausencia de Idempotencia en ~/vantage_pipeline.sh | Doble procesamiento de instancias RETURNED_TO_CREATE. | Campo last_pipeline_run_id (Class B) para rechazar re-ejecuciones en el mismo ciclo. |
---
1. Diagnóstico de UUIDs Duplicados:
- Resultado: Counter(ids) sobre 43 items → 43 IDs únicos (sin duplicados reales).
- Conclusión: Los patrones repetidos (397938be × 10, 3a5938be × 7) eran artefactos de logging truncado (coincidencia parcial en primeros 8 caracteres).
- Acción:
- Reclasificar dedup_fix_verified.patch como instrumentación defensiva (blindaje contra logging ambiguo).
- Cerrar Bug Tracker (3ac938be-fc42-8149-a909-c8a1b426e7e6) con resolución: "Falso positivo (UUIDs truncados)".
1. Actualización de Documentación:
- Kernel.md: Añadida regla KERNEL:GATE-DECISION-009 para orden de precedencia gate_logic() → gate().
- Manual.md: Sección §12 actualizada con procedimiento para Score_Method y manejo de REJECTED_RECURRING.
1. Matriz de Transición de Estados:
- 21 transiciones documentadas (ver AUDITORÍA ARQUITECTÓNICA).
- Diagrama Mermaid: Ciclo de vida completo de vacantes en VANTAGE (incluye loops RT-1 y estados terminales).
- Layer_1/scripts/layer_1_run.py (parcheado: protección terminal).
- Layer_1/scripts/dedup_fix_verified.patch (reclasificado como blindaje).
- Layer_1/scripts/fix_terminal_protection_layer_1_run.patch (aplicado).
- Bug Tracker (3ac938be-fc42-8149-a909-c8a1b426e7e6) → Status: Cerrado.
---
### v9.9.5 — Documentación Transversal: vsum.py (Continuidad de Sesiones) · 2026-07-27
Tipo: [DOC]
Alcance: Kernel, Manual, Aliases, System Prompt (Notion).
Contexto: vsum.py — script nuevo del operador para resumir transcripts de sesiones (Claude/Gemini/ChatGPT) a Markdown estructurado, con push opcional a un INBOX de Notion — no tenía ancla documental en ningún fundacional. Se ejecutó vantage-documentacion-transversal-propuesta seguido de -implementacion para integrarlo.
Kernel: nuevo párrafo en §4.4 (KERNEL:ARCHITECTURE-L4), junto a vsync_doc.py/vgit — describe vsum.py como herramienta de continuidad entre sesiones e IAs, escritura vía notion_client directo (mismo patrón ya usado por vsync_doc.py, no excepción nueva a SP:MCP-ROUTING-NOTES).
Manual: nueva entrada en §9.2 (MANUAL:VANTAGE-RUNTIME-001), junto a vversions/vcensus — aclara que no es comando del Tracker ni observabilidad de Notion, sino infraestructura de continuidad documental sobre transcripts externos.
Aliases: nueva fila vsum en §5 (ALIASES:L4-VERSION-CONTROL).
System Prompt: nueva entrada en la Cédula Digital (SP:DIGITAL-ID-CARD-001) — INBOX (Session Summaries) con su Page ID, nodo de Notion previamente no documentado.
Write-Back Verification: los 4 documentos re-fetched de forma independiente por Claude tras cada escritura — sin mismatch. Un residuo de placeholder introducido en el primer intento de escritura del Kernel fue detectado en el mismo write-back y corregido en una segunda pasada antes de continuar.
IDs afectados: ninguna alta/baja de KERNEL:ID/MANUAL:ID — integración como filas/párrafos en nodos existentes, no sección nueva. Census no requiere regeneración por ID canónico, pero conviene re-correr para reflejar la fila nueva de Aliases.
Pendiente (fuera de esta entrada):
- Correr apply_hyperlinks.py --dry-run para confirmar si SP:DIGITAL-ID-CARD-001 requiere nuevo hipervínculo hacia la entrada de INBOX (probablemente no, es una línea de UUID plano, no un ID canónico PREFIX:KEY).
- Heredados de v9.9.4: investigar las 5 KERNEL:CV-GOLDEN-RULES-00X con sección hardcodeada en Census; decidir cierre de SESSION-20260724-A; auditar patrón de anidamiento mention-page en otras celdas de Kernel/Career Canon.
Versión actualizada: 9.9.5 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.9.3/v9.9.4 (mixto, ver v9.9.4) hasta que el operador corra verify_versions.py --sync.
---
### v9.9.4 — Recuperación de Manual Post-Incidente de Red + Fix de Anidamiento de Links · 2026-07-26
Tipo: [FIX]
Alcance: Manual (Notion).
Contexto: Durante el push local→Notion de apply_hyperlinks.py (ver v9.9.2/v9.9.3), un corte de energía interrumpió la conexión a mitad de la escritura sobre Manual (httpcore.ConnectError, tras fallar reintentos de borrado de bloque en Kernel). El operador restauró Manual manualmente a un snapshot de v9.9.1 para garantizar integridad estructural, lo que revirtió los 9 hipervínculos de §18 (KERNEL:CV-GOLDEN-RULES-001..005) y §19 (CANON:POSITIONING-N1..N4) aplicados en v9.9.2.
Cambios:
- Fetch independiente de Manual completo (Claude) confirmó la reversión de los 9 links a texto plano en las celdas de tabla de §18/§19 — resto del documento intacto.
- Reaplicados los 9 hipervínculos vía notion-update-page (update_content, una operación por celda), usando los anchors ya verificados en el diff auditado de apply_hyperlinks.py en esta misma sesión.
- Bug adicional descubierto y corregido durante la reaplicación: el primer intento de reemplazo de cada celda generó un anidamiento roto — KERNEL:CV-GOLDEN-RULES-00N(mention-page) — porque cada celda ya tenía una mention-page completa envolviendo el ID (probablemente residuo de una operación previa de notion-create-pages/sync automático de páginas mencionadas). Corregido con una segunda pasada de update_content que remueve el envoltorio mention-page y deja únicamente ID limpio, igual al patrón usado en el resto del documento.
Write-Back Verification: Manual re-fetched de forma independiente por Claude tras cada una de las dos pasadas (reaplicación + fix de anidamiento) — confirmado que las 9 celdas de §18/§19 están correctas y sin anidamiento, y que ninguna otra sección del documento (§1–§17, §20–§21) sufrió alteración.
IDs afectados: ninguno — mismos 9 IDs ya existentes desde v9.7.9/v9.9.0, sin alta/baja/rename. Census no requiere regeneración.
Pendiente (fuera de esta entrada, heredado):
- Investigar por qué las 5 KERNEL:CV-GOLDEN-RULES-00X siguen resolviendo con sección hardcodeada en el Census pese a que Kernel y Manual están confirmados en formato canónico completo.
- Decidir cierre de SESSION-20260724-A, abierta en el Ledger desde hace varios días.
- Investigar si el patrón de anidamiento mention-page descubierto aquí afecta otras celdas de tabla en Kernel o Career Canon — no auditado exhaustivamente en esta sesión, solo confirmado en Manual §18/§19.
Versión actualizada: 9.9.4 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.9.3 hasta que el operador corra verify_versions.py --sync.
---
### v9.9.3 — Documentación Transversal: Sistema de Cross-Reference Hyperlinks · 2026-07-26
Tipo: [DOC]
Alcance: Kernel, Manual, Aliases (Notion) + 2 skills locales (fuera de Notion).
Contexto: El Sistema de Cross-Reference Hyperlinks (generate_census.py + apply_hyperlinks.py + vantage_id_rules.py) llevaba operando desde la migración de headings sin tener representación en la documentación fundacional — nadie más que quien lo escribió sabía que existía, cuándo correrlo, o su estado real de adopción.
Kernel: nueva §3.11 KERNEL:DOCUMENTATION-011 — describe propósito, piezas y estado de adopción honesto (apply_hyperlinks.py ya consolidado sobre vantage_id_rules.py; generate_census.py aún no consolidado; generate_id_inventory.py y normalize_heading_ids.py sin migrar).
Manual: nueva subsección "Aplicación de Hipervínculos Cross-Reference" en §11 (MANUAL:HEALTHCHECK-001) — procedimiento operativo de cuándo y cómo correr apply_hyperlinks.py.
Aliases: nuevo alias vhyperlinks en §5 (ALIASES:L4-VERSION-CONTROL).
Skills locales (fuera de Notion, no requieren APROBAR_WRITE de Notion pero sí mismo gate de aprobación): vantage-documentacion-transversal-propuesta/SKILL.md (nuevo Paso 4.5, señalar hipervínculos derivados) y vantage-documentacion-transversal-implementacion/SKILL.md (nuevo paso de verificación entre Inyección y Write-Back).
Write-Back Verification: Kernel, Manual y Aliases re-fetched de forma independiente por Claude tras cada escritura — sin discrepancias.
IDs afectados: ninguna alta/baja de ID canónico en Notion — KERNEL:DOCUMENTATION-011 es contenido nuevo bajo sección nueva, no reemplaza ni renombra IDs existentes. Census no requiere regeneración por baja, sí conviene re-correr para confirmar que el nuevo ID resuelve.
Pendiente (fuera de esta entrada):
- vversions --sync para propagar esta versión a los 6 documentos restantes (permanecen en v9.9.2).
- Investigar por qué las 5 KERNEL:CV-GOLDEN-RULES-00X siguen resolviendo con sección hardcodeada pese a formato canónico completo (heredado, sin resolver desde v9.9.1).
- Decidir cierre de SESSION-20260724-A, abierta en el Ledger desde hace varios días.
Versión actualizada: 9.9.3 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.9.2 hasta que el operador corra verify_versions.py --sync.
---
### v9.9.2 — Cierre del Dry-Run de apply_hyperlinks.py + Limpieza de Aliases Legacy · 2026-07-26
Tipo: [FIX] [DOC]
Alcance: Layer_1/scripts/apply_hyperlinks.py (local).
Contexto: v9.9.0/v9.9.1 dejaban pendiente correr apply_hyperlinks.py --dry-run sobre los 6 documentos migrados y revisar el diff antes de --apply. Al revisar el MAPPING del script tras la migración, se encontraron 9 entradas legacy (MANUAL:OBJETIVO-001, MANUAL:FUNCIONAMIENTO-001, MANUAL:FALLO-001, MANUAL:FLUJO-001, MANUAL:GESTION-DATOS-001, MANUAL:REGLAS-DE-ORO-001, SP:CEDULA-DIGITAL, KERNEL:SCOPE, KERNEL:ROUTING) coexistiendo junto a sus 14 reemplazos ya vigentes — marcadas en el propio código como # alias legacy — retirar tras migración, nunca retiradas.
Cambios:
- Removidas las 9 entradas legacy de MAPPING (no afectaban resolución de links — esos IDs ya no existen como texto en los documentos migrados — pero mantenían basura de referencia en el script).
- apply_hyperlinks.py --root Documentación/ACTIVE corrido en modo DRY RUN (operador, Terminal) sobre los 6 documentos: 0 hipervínculos propuestos en los 6 (Aliases, Brief, Career Canon, Kernel, Manual, System Prompt) — confirma que la migración de v9.9.0 ya dejó todo enlazado correctamente, sin residuos pendientes de aplicar.
Write-Back Verification: no aplica a Notion — cambio 100% local (filesystem). Verificado por el resumen de salida del script (0/0 en los 6) y por sintaxis (py_compile) tras la limpieza de MAPPING.
IDs afectados: ninguno — sin alta/baja/rename de ID canónico. Census no requiere regeneración.
Pendiente (fuera de esta entrada):
- verify_versions.py --sync para propagar v9.9.2 a los 6 documentos restantes (siguen en v9.8.1).
- Investigar por qué las 5 KERNEL:CV-GOLDEN-RULES-00X siguen resolviendo con sección hardcodeada en el Census pese a que Kernel está confirmado en formato canónico completo.
- Decidir cierre de SESSION-20260724-A, abierta en el Ledger desde hace varios días.
Versión actualizada: 9.9.2 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.8.1 hasta que el operador corra verify_versions.py --sync.
---
### v9.9.1 — Cierre de Verificación Pendiente de v9.9.0: Census 162/162 Confirmado + Manual Verificado Completo · 2026-07-26
Tipo: [DOC]
Alcance: Verificación de cierre, sin cambios de contenido en documentos fundacionales.
Contexto: La entrada v9.9.0 dejó dos verificaciones explícitamente pendientes: (1) re-confirmar vcensus 162/162 tras la corrección final de Manual, y (2) resolver una "discrepancia crítica" reportada por Perplexity en su Reporte de Cierre de Manual, donde indicaba que §4 (MANUAL:SETUP-001) y §5 (MANUAL:COLD-START-001) seguían en formato inline de una línea (## N ID / ## Título) en vez del formato canónico de 2 líneas.
Verificación ejecutada:
- generate_census.py corrido por el operador en Terminal: 162/162 IDs resueltos, 0 sin link, 0 huérfanos. Único hallazgo residual: 6 IDs con "Sección hardcodeada" (KERNEL:AUDIENCE-SCOPE + KERNEL:CV-GOLDEN-RULES-001..005) — esperado para el primero (metadata de audiencia, sin sección numerada por diseño), pendiente de investigar para las 5 Golden Rules (posible patrón de heading distinto al capturado por el regex vigente; no bloqueante, no afecta resolución de link).
- Fetch directo e independiente de Manual completo (Claude, no delegado): confirmó que §4 y §5 ya estaban en formato canónico correcto de 2 líneas — la discrepancia reportada por Perplexity no se replicó; probablemente causada por un fetch con caché stale en su sesión (su propio reporte ya advertía timestamps idénticos pre/post-escritura, síntoma de esa misma causa). Verificado además §7–§21 completo (rango que el fetch de Perplexity no había alcanzado): sin residuos de formato, sin referencias cruzadas en prosa a los 6 IDs traducidos que pudieran quedar rotas.
Conclusión: los 6 documentos fundacionales (Aliases, Navigation Brief, System Prompt, Career Canon, Kernel, Manual) quedan confirmados en formato canónico completo, con verificación independiente propia en los 6 — no por reporte de ejecutor sin re-fetch.
Write-Back Verification: no aplica — esta entrada documenta verificación de lectura, sin escritura sobre los documentos fundacionales.
IDs afectados: ninguno — sin alta/baja/rename. Census no requiere regeneración adicional.
Pendiente (fuera de esta entrada, heredado de v9.9.0):
- Correr apply_hyperlinks.py --dry-run sobre los 6 documentos y revisar el diff antes de --apply.
- verify_versions.py --sync para propagar v9.9.0/v9.9.1 a los 6 documentos restantes (siguen en v9.8.1).
- Investigar por qué las 5 KERNEL:CV-GOLDEN-RULES-00X siguen resolviendo con sección hardcodeada pese a que Kernel está confirmado en formato canónico completo.
- Decidir cierre de SESSION-20260724-A, abierta en el Ledger desde hace varios días.
Versión actualizada: 9.9.1 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.8.1 hasta que el operador corra verify_versions.py --sync.
---
> El histórico completo del CHANGELOG lo podrás encontrar en ARCHIVO CHANGELOG, en esta pagina de consulta continua solo encontrarás las últimas diez entradas para garantizar la operación y referencia del sistema.
