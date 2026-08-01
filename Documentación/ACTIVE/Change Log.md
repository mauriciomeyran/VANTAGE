# V | CHANGELOG

# V | CHANGELOG

### v9.11.5 — Kernel: Regla de Bloque Único Formalizada en KERNEL:DOCUMENTATION-001 · 2026-08-01
Tipo: [DOC]
Alcance: Kernel (sección 03.1 KERNEL:DOCUMENTATION-001).
Contexto: Durante auditoría de sesión sobre H3 sin ID (Career Canon + Navigation Brief, hallazgo heredado de sesión previa), se confirmó que la corrección ya vivía en v9.11.1–v9.11.3 (atomización + registro CENSUS_SPEC), pero el contrato normativo del Kernel solo fijaba el nivel de heading (### para NN.N) sin exigir explícitamente que el ID canónico viva en la misma línea del heading. El operador confirmó como regla permanente: "todo H3 lleva ID NN.N, sin excepción decorativa".
Cambios:
- Kernel — KERNEL:DOCUMENTATION-001 (§03.1): nuevo párrafo "Regla de Bloque Único", insertado entre "Matriz Tipográfica Congelada" y "Reglas de Migración" — formaliza que todo heading ### declara su ID [PREFIX]:[KEY] en la misma línea que su título, sin excepción decorativa.
IDs afectados: ninguno — extensión de contenido sobre KERNEL:DOCUMENTATION-001, ID ya existente. Census no requiere regeneración.
Write-Back Verification: Kernel re-fetched de forma independiente tras la escritura — párrafo confirmado en posición correcta, resto del documento (17 secciones) byte-idéntico.
Pendiente (fuera de esta entrada): vversions --sync para propagar v9.11.5 a los 8 fundacionales restantes.
Versión actualizada: 9.11.5 (CHANGELOG + Kernel). El resto de los fundacionales permanece en v9.11.4 hasta vversions --sync.
---
### v9.11.4 — Patch de Debug (--debug-id / campo plain) Declarado Permanente en generate_census.py · 2026-07-31
Tipo: [DOC]
Alcance: Layer_1/scripts/generate_census.py (local, sin escritura en Notion salvo este Changelog).
Contexto: El flag --debug-id y el campo plain agregado a cada entrada del link_index se introdujeron ad-hoc en esta sesión para diagnosticar CANON:POSITIONING-N2/N3/N4 y KERNEL:CV-GOLDEN-RULES-001..005 — en ambos casos fue la evidencia real (plain crudo del bloque) la que descartó hipótesis iniciales incorrectas (desempate de pick_best_link, regex de sección) y confirmó la causa estructural real (bloques fusionados fuera de lugar; ausencia total de heading). Sin el patch, ambos fixes se hubieran basado en suposición en vez de verificación directa.
Decisión: el patch queda permanente en el script, no se revierte. Es puramente aditivo — agrega el campo plain a las entradas del link_index y una rama de salida opcional (--debug-id); no modifica pick_best_link(), el flujo normal de vcensus, ni el Markdown exportado a V_ID_CENSUS_PRODUCTION.md.
IDs afectados: ninguno — cambio de tooling, no de documentación Notion. Census no requiere regeneración.
Pendiente (fuera de esta entrada):
- Patch de debug en generate_census.py (campo plain en link_index) — CERRADO por esta entrada, ya no es pendiente.
- SESSION-2026-07-19-A — mencionada como anómalamente abierta en el Ledger en handoffs previos, aún sin investigar.
Versión actualizada: 9.11.4 (CHANGELOG). El resto de los fundacionales permanece en v9.11.3 hasta vversions --sync.
---
### v9.11.3 — Fix: KERNEL:CV-GOLDEN-RULES-001..005 Sin Heading Propio (Deuda desde v9.9.1) · 2026-07-31
Tipo: [FIX]
Alcance: Kernel (sección 10 KERNEL:CV-GOLDEN-RULES).
Contexto: Los 5 IDs llevaban desde v9.9.1 resolviendo con "sección hardcodeada" en el Census, diagnosticado entonces como posible problema de regex del script. --debug-id confirmó la causa real: las 5 reglas vivían como lista numerada simple ("1. Regla #1...") sin ningún heading ni marcador textual con el ID — el único candidato is_def=True en todo el link_index era una celda de tabla en Manual (MANUAL:CV-GOLDEN-RULES-INDEX) apuntando por anchor directo a Notion, no un heading real en Kernel. Distinto del patrón de CANON:POSITIONING-N2/N3/N4 (v9.10.6): ahí había contenido fusionado en el lugar equivocado; aquí simplemente nunca existió heading propio.
Cambios:
- Kernel — sección 10: la lista numerada 1–5 convertida a 5 headings propios (### 10.N KERNEL:CV-GOLDEN-RULES-00N / título), cada uno con su contenido original preservado tal cual. Template Universal de Rechazo, inmediatamente después, sin alteración.
IDs afectados: ninguna alta/baja — los 5 IDs ya existían en CENSUS_SPEC desde v9.9.8; se corrigió su representación estructural en Notion. Census no requiere alta de CENSUS_SPEC, sí regeneración para reflejar sección en vivo.
Write-Back Verification: Kernel re-fetched de forma independiente tras la escritura — 5 headings confirmados, resto del documento (TOC, secciones 1–9, 11–17) byte-idéntico.
Pendiente (fuera de esta entrada):
- Confirmar vcensus post-fix: debería reportar 0 IDs con sección hardcodeada (cierre del último residuo heredado desde v9.9.1).
- Patch de debug en generate_census.py (campo plain en link_index) sigue local, sin decisión de si se mantiene permanente.
Versión actualizada: 9.11.3 (CHANGELOG + Kernel). El resto de los fundacionales permanece en v9.11.2 hasta vversions --sync.
---
### v9.11.2 — CENSUS_SPEC: Resolución de 9 TBD + Alta de 14 IDs (Homologación v9.11.0/v9.11.1) · 2026-07-31
Tipo: [FIX] [DOC]
Alcance: Layer_1/scripts/generate_census.py (CENSUS_SPEC, local).
Contexto: Tras la reintegración de Career Canon (v9.11.0) y la homologación arquitectónica de Kernel/Career Canon/Navigation Brief/Aliases (v9.11.1), CENSUS_SPEC en disco no reflejaba ninguna de las altas de esas dos operaciones — pese a que la entrada v9.11.0 del Changelog afirmaba "CENSUS_SPEC actualizado en esta misma entrada". Auditoría vía --debug-id (patch de debug local) confirmó, ID por ID, sección y nombre reales en vivo antes de escribir cada entrada — cero valores inventados.
Cambios:
- CENSUS_SPEC — Career Canon: alta de CANON:PROFILE-001/002 (§01.1/§01.2) y CANON:OUTPUT-CONTRACT-005 (§12.5).
- CENSUS_SPEC — Kernel: alta de KERNEL:PURPOSE-001 (§01.1), KERNEL:FAIL-PHILOSOPHY-001/002 (§02.1/§02.2), KERNEL:CV-PIPELINE-001/002 (§12.1/§12.2).
- CENSUS_SPEC — Navigation Brief: alta de BRIEF:CONSULTATION-002..006, CORE-ASSETS-001, DISCOVERY-001, GATE-LOGIC-001, CV-PIPELINE-001 (9 IDs, huérfanos desde la atomización v9.11.1).
- CENSUS_SPEC — Navigation Brief: resueltos 9 placeholders "TBD"/"TBD" (AUTHORITY-001, CONSULTATION-001, CROSS-DEPENDENCIES-001/002/003, HOUSEKEEPING-001, PURPOSE-SCOPE-001/002/003) con sección y nombre reales.
IDs afectados: 14 altas + 9 resoluciones de TBD, todas contra IDs ya existentes en Notion (ningún ID nuevo creado en Notion — solo registro local). Census SÍ requería regeneración — ejecutada por el operador.
Verificación: python3 -m py_compile OK. vcensus post-patch: 209/209 resueltos, 0 sin link, 0 huérfanos (antes: 8 sin link + 17 sin registrar/TBD).
Pendiente (fuera de esta entrada):
- 5 KERNEL:CV-GOLDEN-RULES-001..005 con sección hardcodeada — heredado desde v9.9.1, bajo investigación en esta misma sesión.
- vversions --sync para propagar v9.11.1 a Manual/SP/ID Census/VANTAGE Hub.
- Patch de debug (campo plain en link_index) sigue local, sin decisión de si se mantiene permanente.
Versión actualizada: 9.11.2 (CHANGELOG). Cambio 100% local — no aplica a los 8 documentos fundacionales restantes.
---
### v9.11.1 — Homologación Arquitectónica y Atomización (Aliases + Navigation Brief + Career Canon) · 2026-07-31
Tipo: \[DOC\] \[ARCHITECTURE\]
Alcance: Aliases, Navigation Brief, Career Canon (completos).
Contexto: Contrato de sesión HOMOLOGACIÓN ARQUITECTÓNICA Y ATOMIZACIÓN VANTAGE.
---
Cambios comunes a los 3 documentos:
- Todos los encabezados (## y ###) migrados a formato Bloque Único (ID en línea de heading + título en línea siguiente).
- Tablas pipe convertidas a bloques <table> nativos.
- Atomización de secciones densas (ej: bloques monolíticos divididos en párrafos cortos + listas).
---
Detalles por documento:
- Aliases:
- Tabla DEDUP convertida a nativa.
- Resto de tablas preservadas.
- IDs afectados: 0 nuevos.
- Navigation Brief:
- Atomización de secciones: PURPOSE-SCOPE, CROSS-DEPENDENCIES, MAINTENANCE-CONTRACT, DECISION-TREE.
- IDs afectados: 0 nuevos.
- Career Canon:
- Atomización de bloques densos (ej: Profile ES/EN, Regla de Desempate en Positioning).
- IDs afectados:
- Altas: KERNEL:PURPOSE-001, KERNEL:FAIL-PHILOSOPHY-001/002, KERNEL:CV-PIPELINE-001/002 (5 IDs nuevos en Kernel, derivados de la atomización).
---
Verificación:
- Los 3 documentos re-fetched de forma independiente tras las escrituras.
- Aliases/Navigation Brief: Confirmados sin mismatch estructural.
- Career Canon: 13 secciones, 33 subsecciones y 4 tablas confirmadas correctas.
- Census: Requiere regeneración (CENSUS-SYNC-R1) por los 5 IDs nuevos en Kernel.
---
Pendientes:
- vversions --sync para propagar v9.11.1 a los 9 documentos fundacionales.
- Regenerar Census (ejecutar vcensus).
- Continuar homologación en System Prompt y Manual (según orden de prioridad).
---
### v9.11.0 — Reintegración de Career Canon (Deprecated → Runtime): KPIs, Timeline, Education, Certifications, Major Projects, Derived Outputs Archive · 2026-07-31
Tipo: [DOC] [FEATURE]
Alcance: Career Canon (reestructuración completa de índice y secciones 04–13).
Contexto: El operador identificó que CANON:KPIS (sección I) nunca tenía contenido real en el Runtime — confirmado no como un defecto de formato sino como contenido nunca migrado desde CAREER CANON (DEPRECATED) (37d938be-fc42-800388cfcff6558901d4) al reestructurar el documento. Auditoría diff completa contra la versión deprecada reveló que 8 referencias activas [KPI01]–[KPI07] en Experience Records (§03) y Achievement Library (§05) apuntaban a una sección inexistente — no era contenido faltante cosmético, era una referencia rota en producción. La misma auditoría encontró 4 secciones completas ausentes (Career Timeline, Education, Certifications, Major Projects) y un archivo histórico de Derived Outputs no reintegrado. Dry Run presentado y aprobado ítem por ítem por el operador antes de esta escritura.
Cambios:
- Career Canon — índice superior: expandido de 8 a 13 filas, documentando el nuevo mapeo completo de secciones.
- Career Canon — nueva sección 04 CANON:CAREER-TIMELINE: tabla de 5 filas (C01–C05) con período y país por compañía, ausente en el Runtime desde su consolidación. Reintegrada desde la versión deprecada.
- Career Canon — CANON:ACHIEVEMENTS renumerada de §04 a §05 (sin cambio de contenido).
- Career Canon — nueva sección 06 CANON:KPIS (06.1–06.8, KPI-001–008): resuelve las 8 referencias [KPI01]–[KPI08] previamente rotas. Reintegrada desde la versión deprecada.
- Career Canon — CANON:FACTS renumerada de §06 a §07 (11 subsecciones renumeradas 06.1–06.11 → 07.1–07.11, sin cambio de contenido).
- Career Canon — nueva sección 08 CANON:EDUCATION (ED01, ED02) y nueva sección 09 CANON:CERTIFICATIONS (CERT01, CERT02) — esta última coincide exactamente con el set cerrado ya exigido por CANON:UF-003. Reintegradas desde la versión deprecada.
- Career Canon — nueva sección 10 CANON:MAJOR-PROJECTS (P01–P03) — formaliza la referencia implícita a P01 (Adidas Brand Center) que ya existía sin registro en CANON:POSITIONING-N2. Reintegrada desde la versión deprecada.
- Career Canon — CANON:POSITIONING renumerada de §07 a §11 y CANON:OUTPUT-CONTRACT de §08 a §12 (sin cambio de contenido — ambas versiones Live conservadas tal cual, superiores a la deprecada: tie-break rule de Positioning y registry_seed.json SSOT de Output Contract no existían en la versión deprecada).
- Career Canon — nueva sección 13 CANON:DERIVED-OUTPUTS-ARCHIVE: tabla histórica de 15 CVs derivados, reintegrada con valor de trazabilidad (no es fuente de verdad).
Decisiones de descarte (documentadas en el Dry Run, sin acción): Skills Canon (Live conserva Figma en Stack Técnico, ausente en deprecada); Positioning Modes (Live conserva Regla de Desempate JDs Híbridos); Output Contract (Live conserva Golden Skeleton con IDs de nodo Figma actuales y SSOT registry_seed.json). En los tres casos la versión Live es superior y se descartó explícitamente la versión deprecada.
IDs afectados: Altas — CANON:CAREER-TIMELINE, CANON:KPIS (+ KPI-001..008), CANON:EDUCATION (+ EDUCATION-001/002), CANON:CERTIFICATIONS (+ CERTIFICATION-001/002), CANON:MAJOR-PROJECTS (+ MAJOR-PROJECT-001/002/003), CANON:DERIVED-OUTPUTS-ARCHIVE — 13 IDs nuevos. Renombres de sección (sin alta/baja de ID): CANON:ACHIEVEMENTS §04→§05, CANON:FACTS §06→§07 (+ 11 subsecciones), CANON:POSITIONING §07→§11 (+4 subsecciones), CANON:OUTPUT-CONTRACT §08→§12 (+4 subsecciones). Census REQUIERE regeneración (CENSUS-SYNC-R1 disparado) — CENSUS_SPEC actualizado en esta misma entrada para reflejar el mapeo final antes de que el operador corra vcensus, evitando IDs sin link u huérfanos en la primera corrida post-reintegración.
Write-Back Verification: Career Canon re-fetched de forma independiente tras la escritura (replace_content) — 13 secciones, 33 subsecciones y 4 tablas confirmadas correctas, sin residuo de la estructura anterior de 8 secciones.
Pendiente (fuera de esta entrada):
- Operador debe correr vversions --sync (9/9 fundacionales ya actualizados a v9.11.0 en esta entrada) y vcensus para regenerar V_ID_CENSUS_PRODUCTION.md con los 13 IDs nuevos.
- 15 IDs con sección hardcodeada heredados de v9.10.6 (Kernel CV-GOLDEN-RULES-001..005, Career Canon PROFILE/SKILLS/EXPERIENCE/EXPERIENCE-C01/OUTPUT-CONTRACT-001..004, Aliases:DEDUP) — sin cambio en esta entrada, pendientes de auditoría individual vía --debug-id.
- Patch de debug en generate_census.py (campo plain en link_index) sigue local, sin decisión de si se mantiene o revierte.
Versión actualizada: 9.11.0 (CHANGELOG + los 9 documentos fundacionales: System Prompt, Manual, Kernel, Career Canon, Aliases, Change Log, ID Census, Navigation Brief, VANTAGE Central Hub) — bump aplicado en esta misma entrada, sin esperar vversions --sync del operador, dado que el único contenido tocado fue Career Canon y el resto solo requería alineación de propiedad de versión.
---
### v9.10.6 — Fix: Reconstrucción de CANON:POSITIONING-N2/N3/N4 (Bloque Roto y Fuera de Lugar) · 2026-07-31
Tipo: [FIX]
Alcance: Career Canon (sección 07 CANON:POSITIONING).
Contexto: generate_census.py (patch local de debug --debug-id, agregando plain al link_index) reveló que CANON:POSITIONING-N2, N3 y N4 no eran headings reales en Notion — vivían como texto plano (### tecleado literalmente) fusionado dentro de un único bloque, colgando del último bullet EN de CANON:EXPERIENCE-C05 (sección 03), en vez de vivir en la sección 07 junto a N1. El mismo bloque también arrastraba la línea "Ancla canónica: C01..." que por contenido pertenece a N1. Confirmado en vivo vía notion-fetch antes de escribir — sin asumir causa de origen del defecto.
Cambios:
- Career Canon — bullet EN de CANON:EXPERIENCE-C05 (03.5): removido el contenido fusionado de N2/N3/N4 + Ancla canónica C01 + intro de Regla de Desempate. El bullet ahora cierra limpio en "...directly managed one Jr. Brand Coordinator."
- Career Canon — sección 07 (CANON:POSITIONING): reconstruida con N1, N2, N3 y N4 como headings propios (### 07.N CANON:POSITIONING-NN / ### NN · Título), cada uno con su línea "Ancla canónica" correspondiente. La "Regla de Desempate – JDs Híbridos" recuperó su intro (antes huérfana) precediendo la lista numerada 1/2/3 ya existente de N1.
Verificación previa (sin escritura): patch de debug en generate_census.py (local, script) confirmó vía --debug-id que is_def=False para N2/N3/N4 en Career Canon antes del fix — la causa raíz no era un problema de desempate del script (hipótesis inicial descartada con evidencia), sino ausencia real de bloques heading en Notion.
IDs afectados: ninguna alta/baja — los 4 IDs (CANON:POSITIONING-N1..N4) ya existían en CENSUS_SPEC; se corrigió su representación estructural en Notion. Census sí requiere regeneración para reflejar sección en vivo.
Write-Back Verification: Career Canon re-fetched de forma independiente tras las 2 escrituras — confirmado bullet de C05 limpio y sección 07 con los 4 modos correctamente formados, resto del documento (Achievements, Facts, Output Contract) byte-idéntico.
Post-fix confirmado por operador vía vcensus: CANON:POSITIONING-N1/N2/N3/N4 fuera de la lista de "Sección hardcodeada" (19 → 15 IDs restantes con el mismo patrón, sin verificar individualmente aún).
Pendiente (fuera de esta entrada):
- 8 CANON:KPI-001..008 sin resolver — contenido nunca creado en Career Canon (confirmado, no es defecto de formato).
- 15 IDs restantes con sección hardcodeada (Kernel CV-GOLDEN-RULES-001..005, Career Canon PROFILE/SKILLS/EXPERIENCE/EXPERIENCE-C01/KPIS/OUTPUT-CONTRACT-001..004, Aliases:DEDUP) — mismo patrón estructural sospechado, sin confirmar individualmente vía --debug-id.
- Patch de debug en generate_census.py (campo plain en link_index) es local, no fue aprobado como cambio permanente del script — decidir si se mantiene o se revierte.
- vversions --sync ejecutado por el operador antes de esta entrada — backlog v9.10.0→v9.10.5 cerrado, 9/9 PASS confirmado.
Versión actualizada: 9.10.6 (CHANGELOG). El resto de los fundacionales permanece en v9.10.5 hasta vversions --sync.
---
> El histórico completo del CHANGELOG lo podrás encontrar en ARCHIVO CHANGELOG, en esta pagina de consulta continua solo encontrarás las últimas diez entradas para garantizar la operación y referencia del sistema.
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
---
> El histórico completo del CHANGELOG lo podrás encontrar en ARCHIVO CHANGELOG, en esta pagina de consulta continua solo encontrarás las últimas diez entradas para garantizar la operación y referencia del sistema.
