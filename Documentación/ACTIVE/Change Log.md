# V | CHANGELOG

---
### v9.8.0 — Fix de generate_census.py (2 bugs de matching de clase) + Diagnóstico completo de EXCLUDE_IDS · 2026-07-24
Tipo: [FIX] [DOC]
Alcance: Layer_1/scripts/generate_census.py (local) + diagnóstico de EXCLUDE_IDS en apply_hyperlinks.py (local, sin escritura aún).
Contexto: Continuación de Cross-Reference Hyperlinks Pt 2 (iniciado en v9.7.9). Al preparar apply_hyperlinks.py --dry-run, se detectó que el anchor de CANON:OUTPUT-CONTRACT en V_ID_CENSUS_PRODUCTION.md apuntaba a Kernel en vez de Career Canon — no era un error de carga manual del CENSUS_SPEC (que ni siquiera contiene anchors), sino un bug de clase en la lógica de resolución de generate_census.py.
Cambios:
- Bug 1 (boundary): is_definition_block() usaba startswith/in sin boundary check, permitiendo que un ID más largo (CANON:OUTPUT-CONTRACT-001) contara como definición del ID corto (CANON:OUTPUT-CONTRACT). Fix: nueva función _starts_with_id_boundary() aplicada en las ramas de nomenclatura (a)/(b), línea ~393–394.
- Bug 2 (regex de formato, causa raíz probable): SECTION_HEADING_PREFIX_RE solo reconocía el formato legacy §N — ID (con guion largo), no el formato nuevo §N ID (sin separador) aplicado transversalmente en v9.7.9. Esto significaba que ningún heading normalizado en la operación de v9.7.9 calificaba como definición real bajo el regex viejo. Fix: regex extendido con grupo opcional (?:[—-]\s*)?, más nueva función _contains_id_boundary() para la condición adicional f"ID:{id_str}" in plain (mismo patrón de bug, sin exigir heading).
- Verificado en producción tras ambos fixes: 129/129 IDs resueltos, 0 sin link, sin regresión. CANON:OUTPUT-CONTRACT a -004 ahora resuelven correctamente contra Career Canon (377938be...8089...), no contra Kernel (...805e...) ni Manual (caso adicional de -001 destapado por el mismo bug tras el primer fix).
- Efecto secundario detectado (visibilidad nueva, no bug nuevo): 7 IDs ALIASES:* (de los 8 dados de alta en v9.7.9) no están en CENSUS_SPEC — antes invisibles porque el regex viejo ni siquiera los reconocía como headings. Quedan pendientes de alta (ver Pendiente).
Diagnóstico de EXCLUDE_IDS (apply_hyperlinks.py, local, sin escritura ejecutada aún): de los 29 IDs en la lista de exclusión histórica (documentada desde v9.7.4), confirmado contra el census post-fix:
- 26 IDs (familias EXPERIENCE-C01..C05, KPI-001..008, FACT-001..008, UF-001..003) ya resuelven correctamente a Career Canon tras el fix — la razón original de su exclusión (colisión de anchor) ya no aplica. Candidatos a remoción de EXCLUDE_IDS antes de la próxima corrida.
- CANON:POSITIONING-N1..N4 (4 IDs): sigue roto. Causa raíz confirmada — Manual §19 (MANUAL:POSITIONING-CRITERIA) tiene una tabla-índice con el ID exacto entre backticks solitarios ( CANON:POSITIONING-N1 ), lo cual dispara la condición stripped == id_str en is_definition_block() sin exigir heading. Como Manual (DOC_PRIORITY=3) gana por prioridad sobre Career Canon (DOC_PRIORITY=4) en empate is_def=True, la definición real pierde. Tercer patrón de bug de la misma clase (matching parcial de texto vs. tabla-índice con match exacto) — requiere refactor más profundo (regla de "doc dueño del prefijo gana por default"), no un parche de una línea. Debe permanecer excluido hasta ese fix.
- 3 IDs restantes (KERNEL:BOOTSTRAP-001, KERNEL:PATCH-QUALITY-001, CANON:ARCHIVO-VANTAGE) sin relación con este bug — exclusión por razones propias ya documentadas en el script.
Write-Back Verification: no aplica a Notion — generate_census.py es script local (filesystem), sin escritura en documentos fundacionales. Verificado por corrida repetida de vcensus (Terminal): 129/129 resueltos, 0 sin link, confirmado en ambas iteraciones del fix.
IDs afectados: ninguna alta/baja de ID canónico en Notion — cambio 100% local a la lógica de resolución del script. CENSUS_SPEC en sí no fue editado en esta entrada. Census no requiere regeneración en Notion; sí fue regenerado localmente (V_ID_CENSUS_PRODUCTION.md).
Pendiente (fuera de esta entrada):
- Agregar las 7 filas ALIASES:* faltantes a CENSUS_SPEC — mismo ticket ALTO "Modificar generate_census.py" ya existente en Tasks Tracker, ahora con alcance concreto.
- Ejecutar limpieza de EXCLUDE_IDS en apply_hyperlinks.py: remover los 26 IDs ya sanados, mantener excluidos CANON:POSITIONING-N1..N4 + los 3 sin relación.
- Correr apply_hyperlinks.py --dry-run sobre el estado post-limpieza de EXCLUDE_IDS — no corrido aún.
- Ticket nuevo candidato (no logueado aún en Bug Tracker): refactor de is_definition_block() para resolver el patrón "tabla-índice con ID en backticks solitarios cuenta como definición" — bug de clase #3, afecta cualquier prefijo con doc dueño distinto de donde aparece en tabla de referencia narrativa. Candidato ALTO, ya bloqueó una resolución real (CANON:POSITIONING-N1..N4).
Versión actualizada: 9.8.0 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.7.9 hasta que el operador corra verify_versions.py --sync.
---
### v9.7.9 — Normalización Transversal Heading-ID + Cross-Reference (6 documentos, 63 diffs) + Consolidación Output Contract · 2026-07-23
Tipo: [DOC]
Alcance: SYSTEM PROMPT (9 IDs), NAVIGATION BRIEF (11 IDs), ALIASES (8 IDs nuevos, esquema ALIASES:KEY), CAREER CANON (33 IDs, incluye alta/baja en Output Contract), KERNEL (1 referencia, §14), MANUAL (1 referencia, §20).
Contexto: Operación de normalización transversal para unificar el formato de heading-ID en toda la suite documental a ## §N PREFIX:KEY / ## Título (dos líneas, misma jerarquía tipográfica ##/##), reemplazando formatos mixtos previos (una línea con guión largo, IDs sueltos sin heading propio, o ausencia total de esquema PREFIX:KEY en Aliases). Ejecutada en dos tramos: DRY RUN inicial delegado a Mistral (rechazado en 2 rondas por desviaciones de contrato — tareas no solicitadas en Aliases, omisiones en Career Canon, jerarquía tipográfica inconsistente), tercera ronda aprobada tras corrección manual del mapeo de Output Contract; ejecución final (63 diffs) realizada directamente por Claude vía Notion MCP tras detectarse que el reporte de éxito de Mistral para Career Canon ("8/8 verificado PASS") era un falso positivo no confirmado por re-fetch real.
Cambios:
- SYSTEM PROMPT (9 IDs: §2, §4–§10, §12): unificados a formato de 2 líneas. Corregido en el proceso un error de numeración propio de esta operación — SP:ID-CONNECTORS y SP:VERSION-CHECK-TOOL estaban invertidos entre §10/§12 respecto al documento real; resuelto contra el documento en vivo, no contra el mapeo original.
- NAVIGATION BRIEF (11 IDs, §1–§11): normalizado esquema inconsistente ID:BRIEF:001/ID: BRIEF:002 (con/sin espacio) + numeral arábigo duplicado en título, a §N BRIEF:00N / título limpio.
- ALIASES (8 IDs nuevos): alta de esquema ALIASES:KEY inexistente previamente — documento tenía cero IDs canónicos, solo numeración temática # N — Título. Nuevo esquema: SESSION-CYCLE, RUNTIME, DISCOVERY, PASSIVE-INTAKE, VERSION-CONTROL, DASHBOARD, CV-PIPELINE, DEDUP.
- CAREER CANON (33 IDs, §0–§8.4): normalización completa — secciones principales §0–§7 (antes letras A/B/D/H/I/J/K sin número), subsecciones §3.1–§3.5 (C01–C05), §5.1–§5.8 (KPI01–08), §6.1–§6.11 (CF01–08 + UF01–03), §7.1–§7.4 (N1–N4, sufijo semántico preservado por decisión explícita del operador). Output Contract (§8) consolidado con alta/baja de ID: dados de baja CANON:OUTPUT-CONTRACT-001 (formato viejo, heading corrupto con residuos 

⬇️

 de un intento previo de reformateo), CANON:OUTPUT-CONTRACT-SKELETON-001, CANON:FIGMA-TAG-SCHEMA, CANON:TAG-REGISTRY, CANON:OUTPUT-CONTRACT-TAGREGISTRY-001 (residuo huérfano sin función real, no un ID válido paralelo pese a aparentarlo). Dados de alta: CANON:OUTPUT-CONTRACT (padre) + -001 Golden Skeleton, -002 Figma Tags, -003 Tag Registry, -004 Positioning Modes — sufijo numérico aplicado por ser 4 piezas de granularidad del mismo contrato padre, no conceptos independientes (mismo criterio que C01–C05 y KPI01–08).
- KERNEL §14 (KERNEL:NAMING-CONVENTION): referencia CANON:OUTPUT-CONTRACT-001 → CANON:OUTPUT-CONTRACT (ID padre renombrado).
- MANUAL §20 (MANUAL:GOLDEN-SKELETON-REF): referencia CANON:OUTPUT-CONTRACT-SKELETON-001 → CANON:OUTPUT-CONTRACT-001 (Golden Skeleton bajo nuevo esquema numérico). MANUAL §19 (CANON:POSITIONING-N1–N4) verificado intacto, sin cambio — fuera de alcance de esta operación.
Write-Back Verification: re-fetch en vivo de Career Canon, Kernel y Manual tras la ejecución directa por Claude — los 33 diffs de Career Canon confirmados verbatim (incluyendo ausencia total de los 6 IDs viejos dados de baja en el documento), §14 de Kernel y §20 de Manual confirmados sin mismatch. System Prompt, Navigation Brief y Aliases verificados en tramo previo de la misma sesión.
IDs afectados — CENSUS-SYNC-R1 disparado: alta de CANON:OUTPUT-CONTRACT, -001, -002, -003, -004; baja de CANON:OUTPUT-CONTRACT-001 (formato viejo), CANON:OUTPUT-CONTRACT-SKELETON-001, CANON:FIGMA-TAG-SCHEMA, CANON:TAG-REGISTRY, CANON:OUTPUT-CONTRACT-TAGREGISTRY-001. Census regenerado en esta sesión vía parche a generate_census.py (CENSUS_SPEC, bloque Output Contract) — resultado vcensus: 129/129 IDs resueltos, 0 sin link, 0 huérfanos.
Pendiente (fuera de esta entrada): verificar si el resto de CENSUS_SPEC para Career Canon (secciones §1–§7, fuera del bloque Output Contract parcheado) sigue usando el esquema de letras viejo (§A, §B...) en vez de los números §1–§7 aplicados en esta operación — no auditado en esta sesión, riesgo de inconsistencia parcial en el spec. Pendiente heredado: cross-reference hyperlinks (Kernel/Manual) usando generate_id_inventory.py + apply_hyperlinks.py sobre los IDs recién normalizados.
Versión actualizada: 9.7.9 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.7.8 hasta que el operador corra verify_versions.py --sync.
---
### v9.7.8 — Centralización de Skills VANTAGE en MCP Server / Single Source of Truth (/skills/) · 2026-07-23
Tipo: [DOC] [INFRA]
Alcance: KERNEL (KERNEL:ARCHITECTURE-L4, §4) + MANUAL (§8.1, bloque vgit).
Contexto: El operador centralizó el sistema de Skills VANTAGE en /skills/ como single source of truth (12 .skill files + index.json + index.html), migró GitHub Pages de la rama dev/layer-2 a main, y extendió git_sync.py (motor de vgit) para detectar .skill nuevos y regenerar index.json en el mismo commit+push. Se ejecutó vantage-documentacion-transversal-propuesta seguido de -implementacion para reflejar este cambio en Kernel y Manual, ambos con gap total previo (ninguna mención de Skills/MCP filesystem en L4). Se detectó además que Kernel §4 citaba el repo como jhs-pipeline, nombre desactualizado — corregido a VANTAGE.
Cambios:
- KERNEL:ARCHITECTURE-L4 (§4): agregado párrafo "Skills Distribution — Single Source of Truth" documentando /skills/, GitHub Pages en main, extensión de git_sync.py, y los dos consumidores (Claude Desktop vía MCP filesystem local, Devin Desktop vía devin mcp add). Corregido repo jhs-pipeline → VANTAGE.
- MANUAL §8.1 (bloque vgit): agregado párrafo "Extensión reciente — Skills Distribution" aclarando que la detección de /skills/ es el mismo mecanismo de auto-sync ya documentado, no un flujo nuevo.
- Tasks Tracker: creados 2 tickets (MEDIO) — "GitHub Actions para auto-regenerar index.json" (3a6938be-fc42-815e-949d-ca3997d55d90) y "Test end-to-end de nuevas skills (Devin + Claude Desktop)" (3a6938be-fc42-81c9-ac7d-f3146adba8ce").
- Tasks Tracker: creado 1 ticket adicional (MEDIO) de ingeniería inversa — "Adoptar fortalezas del Brief de Skills MCP en skills de documentación transversal" (3a6938be-fc42-810b-ab49-ef8784093f39`), a partir de 4 fortalezas identificadas en el brief recibido esta sesión (resumen ejecutivo Antes/Después, auto-señalamiento de incertidumbre, distinción explícita de fases con gate, nodos candidatos con justificación tentativa).
- [FIX] Layer_1/scripts/layer_1_run.py — mismo patrón de defecto ya visto en VL3 (Fuente), detectado tras correr vl1: VM_Scope y Fetch se escribían como rich_text, pero el VANTAGE TRACKER los tiene como select (VM_Scope: Alto/Bajo; Fetch: Accesible/Bloqueado), causando rechazo de escritura ("VM_Scope is expected to be select", "Fetch is expected to be select") sin detener el pipeline (Fases 1–5 completaron igual, 45 registros procesados). Confirmado contra schema real de Notion antes de tocar código — los valores generados por get_vm_scope() y el literal "Bloqueado" ya coincidían verbatim con las opciones del select, sin requerir clamp adicional (a diferencia de Fuente). Corregidas ambas escrituras a {"select": {"name": ...}}, alineado con Role_Class/Status en las mismas llamadas, que ya usaban el tipo correcto. Barrido de verificación (grep -n "rich_text" sobre el archivo completo) confirmó que no quedan más casos del mismo defecto — las 2 ocurrencias restantes son el helper de lectura txt() (correcto) y Next_Action (correcto, campo de texto libre en el schema real, no select).
- Validado en producción por el operador: corrida de vl1 post-parche — Fase 1 escribió 18 registros de VM_Scope/Source_Type sin ningún error de tipo (vs. ~18 fallos repetidos en la corrida previa al fix), Fase 2 marcó 2 links muertos vs Fetch sin error. Ready-to-Apply se mantuvo consistente en 3. Hallazgo menor no bloqueante: el log de Fase 3 reportó "Scoring: Sin cambios" mientras el resumen final de la misma corrida reportaba "Scoring v6.4: 36 cambios" — aparente discrepancia de conteo entre el log por fase y el acumulado del resumen; no afectó la integridad de datos (Ready-to-Apply consistente), candidato a ticket BAJO de claridad de logging, no registrado aún.

Write-Back Verification: pendiente — re-fetch de Kernel y Manual a ejecutar inmediatamente después de esta entrada de Changelog, en la misma sesión.
IDs afectados: ninguna alta/baja de ID canónico — adiciones de contenido bajo KERNEL:ARCHITECTURE-L4, ID ya existente, y bajo sección §8.1 del Manual sin ID propio nuevo. Census no requiere regeneración (CENSUS-SYNC-R1 no se dispara).
Pendiente (fuera de esta entrada): decidir si git_[sync.py](http://sync.py) extendido a /skills/ amerita mención en KERNEL:DOCUMENTATION-005 (Convención de Anuncio de Skills) — no evaluado en esta sesión por estar fuera del alcance del brief original.
Versión actualizada: 9.7.8 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.7.7 hasta que el operador corra verify_[versions.py](http://versions.py) --sync\.
- [CIERRE] Ticket "Adoptar fortalezas del Brief de Skills MCP en skills de documentación transversal" (3a6938be-fc42-810b-ab49-ef8784093f39) cerrado (Status: Hecho). Las 4 fortalezas identificadas se aplicaron directamente a ambos skills locales (sin DRY RUN, autorizado explícitamente por el operador): en vantage-documentacion-transversal-propuesta/SKILL.md — Paso 3 ahora exige justificación tentativa por nodo candidato ("probablemente X porque Y"); Paso 4 agrega resumen ejecutivo Antes/Después como primer elemento, sección de incertidumbre auto-señalada (no omitible, se declara vacía si no aplica), y gate de fase como texto literal visible en el entregable (FASE 1 COMPLETA — SOLO MAPEO...). En vantage-documentacion-transversal-implementacion/SKILL.md — ajuste de compatibilidad: reconoce el nuevo formato de entrada de Fase 1 y declara explícitamente si falta alguno de los tres elementos nuevos antes de generar el DRY RUN. Cambio 100% local (filesystem), sin alta/baja de ID canónico. Census no requiere regeneración.
- [POST-CIERRE — SESSION-20260723-A] Census post-cierre detectó mismatch de sufijo SP:ID-CONNECTORS-001 (CENSUS_SPEC, línea 141 de generate_census.py) vs. SP:ID-CONNECTORS (ID real en SYSTEM PROMPT) — corregido vía sed local, sin escritura en Notion; vcensus re-confirmó 130/130 resueltos, 0 huérfanos.
- [SESSION-20260723-B — Prompt Library] Consolidación de 6 post-mortems de corridas de búsqueda (Perplexity/Comet L1 ×3 vía documento adjunto; Gemini, Grok, You.com L2 ×3 vía texto en sesión) en un análisis comparativo de patrones repetidos. 4 parches aplicados vía notion-update-page (update_content) sin DRY RUN previo — autorizado explícitamente por el operador ("yep"): (1) Prompt A (368938be-fc42-8162-ae48-d48970a729dc) — Accepted Seniority: Head (IC only) ahora remite a criterio de verificación explícito en INCLUSION RULES (title contiene "Head" AND JD sin lenguaje de gestión de personas; si no verificable, fetch_status: needs_verification); INCLUSION RULES — nuevas definiciones operacionales de Company identified (rechaza placeholders genéricos tipo "Empresa confidencial"/"Importante empresa") y Active posting (HTTP 200 AND CTA visible AND ≤21 días, fecha ausente → needs_verification); fit remains strong reemplazado por fit_strong con criterio verificable (≥2 de: industria en lista, visual_signal en título, seniority exacto); SOURCE BUCKETS — nota de alcance aclarando que la política de agregadores como fuente de descubrimiento vs. resultado final es decisión de cada wrapper, no del Prompt Base. (2–4) L2 - Wrapper Gemini (368938be-fc42-8139-b6a7-ee467f6c4584), L2 - Wrapper Grok (368938be-fc42-8145-944d-d15245b6e65e), L2 - Wrapper you.com (368938be-fc42-81c8-95cd-d8d75ff3abe4) — mismo parche en SEARCH SCOPE en los 3: agregadores (LinkedIn/OCC/Indeed/Computrabajo/Bumeran) pasan de "Never search"/"Forbidden" en bloque a "permitido solo para descubrimiento, prohibido como fuente final de datos", respondiendo al hallazgo de Gemini/Grok/You.com de que la exclusión total dejaba fuera ~80% del inventario real de CDMX (concentrado en agregadores por baja penetración de ATS directo en el mercado local). Ningún wrapper L1 (Career Sites/LinkedIn/Aggregators) fue tocado — sus hallazgos de post-mortem fueron de calidad de extracción (Workday/JS dinámico) y ambigüedad heredada de Prompt A, no de SEARCH SCOPE. El bug de deduplicación cross-portal (Multicont, Indeed↔Computrabajo) no se tocó aquí — permanece como ticket ALTO ya existente en Bug Tracker (fix de código, no de prompt).
Write-Back Verification: re-fetch de Prompt A y L2-Gemini tras la escritura — cambios confirmados verbatim, sin mismatch; L2-Grok y L2-you.com confirmados por retorno exitoso de update_content (mismo parche, no re-fetched individualmente por economía de tokens).
IDs afectados: ninguno — los 4 documentos son Prompt Bases/Wrappers de Prompt Library, fuera del namespace PREFIX:KEY de los 9 fundacionales. Census no requiere regeneración.
Versión: sin cambio — esta entrada se documenta como viñeta adicional bajo v9.7.8 por instrucción explícita del operador ("no version update"). Los 4 documentos parcheados no forman parte de la Regla de Versión Única (SP:SYNC-RULE), por lo que no aplica el requisito de actualizar la propiedad Versión en la misma operación.
---
### v9.7.7 — Corrección de Inconsistencias Archivar/Status en Task Tracker + Fix de IDs en vantage-tidy-bug-task-tracker · 2026-07-22
Tipo: [FIX]
Alcance: Tasks Tracker (2 páginas) + vantage-tidy-bug-task-tracker/SKILL.md (local).
Contexto: Auditoría exhaustiva de Bug/Task Tracker vía Terminal (dump completo, 31/31 filas — 10 Bug + 21 Task) tras intento previo vía notion-search. Confirmó cero candidatos de archivado por Status terminal, pero detectó 2 tickets con Archivar=true inconsistente con su Status real.
Cambios:
- vantage-tidy-bug-task-tracker/SKILL.md: corregido par Bug Tracker DB ID/COL ID invertido (mismo patrón que v9.7.1, drift no propagado a este segundo skill). Cambio local, ya reportado en entrada v9.7.6.
- Task Tracker — "Convertir referencias cruzadas a hyperlinks" (39e938be-fc42-81c0-ac8b-e95eb4a0e835): Archivar true→false. Trabajo sigue activo (51/82 hyperlinks aplicados en v9.7.4, 31 IDs pendientes).
- Task Tracker — "Normalizar fundacionales: NUEVE" (3a3938be-fc42-814f-bcdc-ce1a48cf1916): Status Pendiente→Hecho. Confirmado vía archivos subidos por el operador (verify_versions.py DOC_KEYS=9 líneas, resolver_registry_v2.json document_registry con BRIEF+VANTAGE) que el conteo 7→9 está completo en Notion, registry y script.
Write-Back Verification: re-fetch de ambas páginas de Tasks Tracker tras la escritura — sin mismatch.
IDs afectados: ninguna alta/baja de ID canónico. Census no requiere regeneración.
Pendiente (fuera de esta entrada): discrepancia --check entre MANUAL §6 (lo describe como activo) y vantage-session-open.skill/KERNEL (lo declaran eliminado v9.6.2) — sin resolver, requiere vantage-documentacion-transversal-propuesta en próxima sesión.
Versión actualizada: 9.7.7 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.7.6 hasta que el operador corra verify_versions.py --sync.
---
### v9.7.6 — Normalización de Links y Referencias en Filesystem · 2026-07-22
Tipo: [FIX]
Alcance: Filesystem local (~/Documents/04-Vantage_CV/Pipeline/).
Contexto: Corrección de links rotos y referencias obsoletas identificados en el handoff de sesión SESSION-20260722-H. Los links apuntaban a URLs incorrectas (notion.so en lugar de notion.com) o a IDs renombrados (KERNEL:SCHEMA-008 → KERNEL:DOCUMENTATION-009).
Cambios:
- Reemplazo masivo de notion.so/ → notion.com/ en todos los archivos del Pipeline (incluyendo subdirectorios).
- Actualización de KERNEL:SCHEMA-008 → KERNEL:DOCUMENTATION-009 en todos los archivos.
- Búsqueda exhaustiva de KERNEL:FAIL-PHILOSOPHY (sin coincidencias en archivos locales; pendiente verificación en Notion).
- Resolución parcial de ticket de huérfanos: KERNEL:SCHEMA-008 confirmado como no existente (eliminación de referencias pendiente), BRIEF:001/BRIEF:011/SP:SYNC-RULE verificados como existentes con contenido válido (morfología de IDs de BRIEF pendiente de normalización en siguiente Handoff).
- [FIX] vantage-tidy-bug-task-tracker/SKILL.md: corregido el par Bug Tracker de DB ID 36e938be-fc42-81f8-8c6f-000b6769ba03 / COL ID 36e938be-fc42-81bd-9e1f-dc360b3b45f5 (invertido) a DB ID 36e938be-fc42-81bd-9e1f-dc360b3b45f5 / COL ID 36e938be-fc42-81f8-8c6f-000b6769ba03, alineado con KERNEL:TRACKER-SCHEMA-001 y con la corrección ya aplicada en vantage-create-bug-task/SKILL.md (v9.7.1) — mismo patrón de drift no propagado, confirmado por fetch en vivo de ambos trackers en esta sesión. Cambio 100% local (filesystem), sin escritura en Notion.
Write-Back Verification: Validación post-ejecución con grep -r — sin instancias remanentes de notion.so o KERNEL:SCHEMA-008.
IDs afectados: Ninguno en documentos fundacionales — cambios locales en filesystem.
Pendiente (fuera de esta entrada): Verificar KERNEL:FAIL-PHILOSOPHY en Notion (no encontrado en archivos locales).
Versión actualizada: 9.7.6 (solo esta página — CHANGELOG).
### v9.7.5 — Excepción de Versión para Memoria de Sesión de Claude en SP:SYNC-RULE · 2026-07-22
Tipo: [DOC]
Alcance: SYSTEM PROMPT (SP:SYNC-RULE).
Contexto: El operador señaló un patrón recurrente: al abrir sesión, Claude comparaba la cifra de versión traída en su memoria persistente (entre sesiones) contra la versión live recuperada de Notion, y reportaba cualquier diferencia como discrepancia/red flag — pese a que esto es esperado dado que el operador abre y cierra sesiones asíncronas sobre distintos pendientes. La Regla de Versión Única de SP:SYNC-RULE nunca distinguía este caso del de una discrepancia real entre los nueve documentos fundacionales.
Cambios:
- SP:SYNC-RULE: agregado párrafo de excepción inmediatamente después de la Regla de Versión Única, acotando su alcance exclusivamente a discrepancias entre los nueve fundacionales entre sí. Aclara que una diferencia entre la memoria de Claude y la versión live no constituye discrepancia bajo SP:SYNC-RULE ni SP:CONSISTENCY, y que Claude debe adoptar la versión live silenciosamente sin reportarlo.
- Memoria persistente de Claude (fuera de Notion): agregada regla equivalente para reforzar el comportamiento a nivel de sesión.
- [FIX] Alineación de rutas de V_ID_CENSUS_PRODUCTION.md entre generate_census.py y health_check.py (- [FIX] Alineación de rutas de V_ID_CENSUS_PRODUCTION.md entre generate_census.py y health_check.py (ahora en /Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/data/).
- [FIX] Alineación de rutas de salida de apply_hyperlinks.py (diff-out) y generate_id_inventory.py (out_dir) a /Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/data/. diagnose_kernel_blocks.py no requiere cambios (sin output de archivo).
- [FIX] Layer_3/scripts/layer_3_mail.py — _extract_body() forzaba utf-8/errors="ignore" sin consultar part.get_content_charset(), corrompiendo URLs de LinkedIn (mojibake) y causando descarte silencioso de vacantes válidas (0/150 creadas en corrida previa). Nueva función _decode_part() respeta el charset real declarado por cada part, con errors="replace" en vez de ignore.
- [FIX] Layer_3/scripts/layer_3_mail.py — propiedad Fuente se mandaba como rich_text; el VANTAGE TRACKER la tiene como select (Agregador, Career Page Oficial, Indeed, Other, Computrabajo, LinkedIn), causando rechazo 100% de escrituras ("Fuente is expected to be select"). Agregada constante NOTION_FUENTE_OPTIONS con doble clamp (interno VALID_RAW_SOURCES → real Notion) y cambio de tipo a select.
- [DOC] KERNEL:GATE-DECISION-009 — Nueva sección §9.9 en KERNEL (Escalamiento de Pendientes a Tickets). Define 3 niveles de escalamiento (Nivel 1: Handoff/Ledger; Nivel 2: Sugerencia con confirmación; Nivel 3: Automático) y resuelve puntos de fricción: umbral de iteraciones como criterio orientativo, re-evaluación Nivel 2→3 con evidencia dura, y alineación con SP:CONSISTENCY §5.
- [INFRA] Split del skill local vantage-documentacion-transversal en dos entidades independientes: vantage-documentacion-transversal-propuesta (Fase 1 — mapeo de nodos, solo lectura) y vantage-documentacion-transversal-implementacion (Fase 2 — DRY RUN, inyección, write-back, changelog/versión). Objetivo: eficiencia de tokens al cargar solo la fase requerida. Ambos skills heredan intacto el contrato de MANUAL:PATCH-QUALITY-001 (5 filtros), los tokens válidos de APROBAR_WRITE, y el mecanismo de Write-Back Verification del skill original. El skill único queda deprecado (renombrado .deprecated) por el operador en /Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Skills/. Cambio 100% local (filesystem) — sin alta/baja de ID canónico en Notion.
- [DOC] Referencia cruzada bidireccional entre KERNEL:GATE-DECISION-009 (§9.9) y MANUAL:SESSION-CYCLE-001 (§6). Contexto: handoff de sesión SESSION-20260722-F identificó que un ticket citado ("GATE-DECISION-009 ↔ Manual §6") no existía como tal en Tasks Tracker, y que un DRY RUN previo estaba generado contra un estado obsoleto del Kernel (solo Nivel 1, sin Nivel 2/3 — ambos ya presentes en vivo). Se verificó en vivo que KERNEL §9.9 ya tenía los 3 niveles completos y que Manual §6 ya estaba reescrito; el único gap real era la ausencia de referencia cruzada entre ambos. Cambios: (1) KERNEL §9.9, Nivel 1 — línea "Acción" ahora remite a Manual §6 para el detalle operativo de registro dentro del ciclo de sesión; (2) KERNEL §9.9 — nuevo párrafo de cierre tras la tabla de resolución de fricciones, remitiendo a Manual §6 para la implementación práctica del escalamiento; (3) MANUAL §6, sección "Qué hacer si algo no cuadra" — nuevo ítem remitiendo a KERNEL §9.9 para la lógica de los 3 niveles. Escrito autorizado por el operador sin DRY RUN previo (excepción explícita en sesión). IDs afectados: ninguna alta/baja de ID canónico — adiciones de contenido bajo IDs ya existentes (KERNEL:GATE-DECISION-009, MANUAL:SESSION-CYCLE-001). Census pendiente de regenerar a solicitud del operador antes de cierre de sesión. Pendiente: ticket de Tasks Tracker "(Task) Manual §6 describe flujo --check ya eliminado" sigue marcado Pendiente pese a que §6 ya está reescrito — posible drift Tracker↔Documento, verificar/cerrar en próxima sesión.
Write-Back Verification: re-fetch de SYSTEM PROMPT tras la escritura — párrafo confirmado verbatim, sin mismatch.
IDs afectados: ninguna alta/baja de ID canónico — adición de contenido bajo SP:SYNC-RULE, ID ya existente. Census no requiere regeneración.
Pendiente (fuera de esta entrada): ninguno nuevo identificado en esta entrada.
- [SESSION-20260722-H] Creados 3 tickets vía escalamiento KERNEL:GATE-DECISION-009 a partir del Handoff consolidado (SESSION-D+E): (1) Bug ALTO — sesiones huérfanas recurrentes sin cierre en Session Ledger (Nivel 3, evidencia dura del propio Ledger); (2) Bug ALTO — Dedup Caso 5 (Next_Action=Archivar no se ejecuta automáticamente) (Nivel 3, evidencia dura del Handoff); (3) Task ALTO — Navigation Brief, ejecutar Notion writes ya aprobadas en dry run (Nivel 2, APROBAR_WRITE explícito del operador). Los tres quedan fuera de reporte futuro en Handoff/Ledger, según KERNEL:GATE-DECISION-009. Se inició vantage-tidy-bug-task-tracker, bloqueada por límite de tokens de sesión — query_data_sources/query_database_view siguen bloqueadas en este plan; corrida completa pendiente vía Terminal en próxima sesión.
Versión actualizada: 9.7.5 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.7.4 hasta que el operador corra verify_versions.py --sync.
---
### v9.7.4 — Aplicación de Hipervínculos en ACTIVE (51) + Fix de Permisos Read-Only Bloqueante · 2026-07-22
Tipo: [DOC] [FIX]
Alcance: apply_hyperlinks.py (local) + 4 archivos en Documentación/ACTIVE/ (Kernel.md, Manual.md, System Prompt.md, Career Canon.md).
Contexto: --apply falló con PermissionError: [Errno 13] al intentar escribir sobre archivos en modo 444 (read-only, canonizado intencionalmente desde v9.5.9 para forzar Notion como única fuente de verdad). El script nunca contempló hacer chmod temporal antes de escribir — bloqueante no anticipado en el diseño original de v9.5.9.
Cambios:
- Diagnóstico confirmado vía ls -la, ls -lO, stat: permiso Unix estándar -r--r--r--, sin uchg de Finder ni ACL extendida — descartadas ambas hipótesis antes de aplicar el fix.
- Operador aplicó chmod u+w sobre los 4 .md, corrió apply_hyperlinks.py --apply con éxito: 51 hipervínculos aplicados (Kernel 19, Manual 26, System Prompt 6, Career Canon 0), 31 IDs excluidos de esta corrida (EXCLUDE_IDS del script).
- Diff (dry_run_hyperlinks.diff) auditado verbatim contra el Kernel real fetched en esta sesión — anchors confirmados correctos, sin links fabricados ni destinos incorrectos.
- chmod 444 restaurado por el operador sobre los 4 archivos post-escritura, preservando el patrón read-only canónico.
Write-Back Verification: no aplica a Notion — cambio 100% local (filesystem del operador). Verificado por el resumen de salida del script (51/51 aplicados) y por auditoría directa del diff contra el Kernel en vivo.
IDs afectados: ninguno — cambio de formato (hipervínculos) sobre contenido ya existente, sin alta/baja de ID canónico. Census no requiere regeneración.
Pendiente (fuera de esta entrada): decidir si apply_hyperlinks.py debe automatizar chmod +w/chmod 444 en su propio flujo (candidato a ticket Bug/Task Tracker); reparar los 2 destinos de link rotos preexistentes (KERNEL:FAIL-PHILOSOPHY → texto plano (V | KERNEL); KERNEL:SESSION-LEDGER/SP:SYNC-RULE doble-anidados apuntando a notion.so en vez de notion.com); 4 huérfanos sin resolver de inventario_huerfanos.md (BRIEF:001, BRIEF:011, KERNEL:SCHEMA-008, SP:SYNC-RULE).
Versión actualizada: 9.7.4 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.7.3 hasta que el operador corra verify_versions.py --sync.
---
### v9.7.3 — Corrección de Cierre de Bootstrap Desalineado en SP:BOOTSTRAP-001 (VANTAGE: SISTEMA SINCRONIZADO → BOOTLOADED: DOCUMENTOS CARGADOS) · 2026-07-22
Tipo: [DOC] [FIX]
Alcance: SYSTEM PROMPT (SP:BOOTSTRAP-001).
Contexto: Auditoría en sesión (a solicitud del operador) sobre si el Kernel documenta el Bootloader activo en Project Instructions (UI). Confirmado que KERNEL:DOCUMENTATION-004 (§3.4) sí documenta correctamente el protocolo activo (BOOTLOADING... → BOOTLOADED: DOCUMENTOS CARGADOS), pero la página SYSTEM PROMPT real en Notion (SP:BOOTSTRAP-001) seguía con la frase de cierre anterior (VANTAGE: SISTEMA SINCRONIZADO), retirada por convención desde el Changelog v9.5.0 pero nunca propagada a esta página.
Cambios:
- SP:BOOTSTRAP-001: frase de cierre del paso 5 corregida de VANTAGE: SISTEMA SINCRONIZADO a BOOTLOADED: DOCUMENTOS CARGADOS, alineada con KERNEL:DOCUMENTATION-004 (§3.4) y con el copy real activo en Project Instructions.
Write-Back Verification: re-fetch de SYSTEM PROMPT tras la escritura — frase corregida confirmada verbatim.
IDs afectados: ninguna alta/baja de ID canónico — reescritura de contenido bajo SP:BOOTSTRAP-001, ID ya existente. Census no requiere regeneración.
Pendiente (fuera de esta entrada): el bloque final de SP:BOOTSTRAP-001 sigue citando verify_versions.py --check, flag ya eliminado del Kernel desde v9.6.2 — mismo defecto ya logueado como ticket ALTO (Manual §6 desalineado), no tocado en esta entrada por estar fuera del alcance solicitado.
Versión actualizada: 9.7.3 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.7.0 hasta que el operador corra verify_versions.py --sync.
---
### v9.7.2 — Cierre de Huecos L0: Referencia Cruzada SCHEMA-004/005 → §3.3 + Alta de Dedup_Flag en Class B (SCHEMA-001) · 2026-07-22
Tipo: [DOC]
Alcance: Kernel §7 (KERNEL:SCHEMA-004, KERNEL:SCHEMA-005, KERNEL:SCHEMA-001).
Contexto: Cierre de los dos huecos L0 identificados en la revisión post-v9.7.0: (1) KERNEL:SCHEMA-004/-005 documentaban el contrato de Entity Format y el flujo de resolución sin ninguna referencia hacia KERNEL:DOCUMENTATION-003 (§3.3, L0 Runtime), pese a ser la contraparte de datos del mismo mecanismo; (2) Dedup_Flag figuraba como campo Class B protegido en KERNEL:CV-GOLDEN-RULES (§10) desde v9.5.4, pero nunca se había añadido a la enumeración canónica de Class B en KERNEL:SCHEMA-001 (§7) — inconsistencia señalada por SP:CONSISTENCY y arrastrada sin resolución desde v9.5.4/v9.6.8.
Cambios:
- KERNEL:SCHEMA-004 (§7): agregada línea de referencia cruzada hacia §3.3 (KERNEL:DOCUMENTATION-003 — L0 Runtime). Sin fusión ni reestructuración — decisión explícita del operador de mantener ambos IDs separados.
- KERNEL:SCHEMA-005 (§7): misma referencia cruzada agregada, aclarando que el Contrato de Resolución de 4 Pasos es la contraparte de datos del Runtime Build descrito en §3.3.
- KERNEL:SCHEMA-001 (§7): Dedup_Flag agregado a la enumeración Class B — System-Primary, alineando el schema con lo que KERNEL:CV-GOLDEN-RULES ya declaraba como campo protegido.
Write-Back Verification: no ejecutado en esta entrada — escritura autorizada explícitamente por el operador sin DRY RUN/APROBAR_WRITE previo ni re-fetch de confirmación posterior.
IDs afectados: ninguna alta/baja de ID canónico — ambos parches son adiciones de contenido bajo IDs ya existentes (KERNEL:SCHEMA-001, -004, -005). Census no requiere regeneración (KERNEL:CENSUS-SYNC Regla 1 no se dispara).
Pendiente (fuera de esta entrada): ninguno nuevo — los dos huecos L0 abiertos desde la revisión post-v9.7.0 quedan cerrados con esta entrada. El punto sobre la etiqueta "v8.9.0" en la tabla de Prefijos Autorizados sigue sin confirmarse contra el documento real (no encontrado en fetch en vivo, ver v9.7.1).
Versión actualizada: 9.7.2 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.7.0 hasta que el operador corra verify_versions.py --sync.
---
### v9.7.1 — Fix DB ID/COL ID de Bug Tracker en skill vantage-create-bug-task (drift no propagado desde v9.7.0) · 2026-07-22
Tipo: [FIX]
Alcance: vantage-create-bug-task/SKILL.md (local, fuera de Notion — no fundacional).
Contexto: Al revisar los pendientes derivados de la refactorización del Kernel (v9.7.0), se detectó que la corrección de DB ID/COL ID de Bug Tracker aplicada en KERNEL:TRACKER-SCHEMA-001 no se había propagado al skill que consume esos IDs directamente — el skill seguía con el par heredado (invertido) que el propio Kernel ya señalaba como incorrecto.
Cambios:
- vantage-create-bug-task/SKILL.md: corregido el par Bug Tracker de DB ID 36e938be-fc42-81f8-8c6f-000b6769ba03 / COL ID 36e938be-fc42-81bd-9e1f-dc360b3b45f5 (invertido) a DB ID 36e938be-fc42-81bd-9e1f-dc360b3b45f5 / COL ID 36e938be-fc42-81f8-8c6f-000b6769ba03, alineado con Kernel §8 (KERNEL:TRACKER-SCHEMA-001, v9.7.0). Tasks Tracker no requirió cambio.
- Nota de corrección agregada al propio skill documentando el origen del drift (refactor de Kernel v9.7.0 no propagado en el mismo ciclo).
Write-Back Verification: no aplica a Notion — cambio local, verificado por re-lectura directa del archivo tras la edición.
IDs afectados: ninguno en documentos fundacionales — corrección de referencia a un ID ya existente en el Kernel (KERNEL:TRACKER-SCHEMA-001), sin alta/baja de ID canónico. Census no requiere regeneración.
Pendiente (fuera de esta entrada): de la revisión de pendientes post-v9.7.0 quedan abiertos — fragmentación KERNEL:SCHEMA-004/-005 (sin referencia cruzada hacia §3.3) y ubicación canónica de Dedup_Flag (ausente de la lista Class B en KERNEL:SCHEMA-001 §7, pese a estar listado como campo protegido en KERNEL:CV-GOLDEN-RULES §10). El punto sobre una etiqueta de versión "v8.9.0" en la tabla de Prefijos Autorizados no se pudo confirmar contra el documento real — no encontrado en fetch en vivo.
Versión actualizada: 9.7.1 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.7.0 hasta que el operador corra verify_versions.py --sync.
---
### v9.7.0 — Refactor Estructural Completo del Kernel (Renumeración §1–§17, Limpieza de Residuos, Corrección DB/COL ID) · 2026-07-22
Tipo: [DOC] [FIX]
Alcance: V | KERNEL completo — TOC, headers §1–§17, KERNEL:TRIGGERS (§11), KERNEL:DATA-FLOW (§16), KERNEL:TRACKER-SCHEMA-001 (§8).
Contexto: Auditoría en sesión detectó numeración §N duplicada y desordenada (dos secciones en §8, dos en §9), un bloque de nota de trabajo interna pegado al final de DATA-FLOW, residuos de exportación (
, backslashes de escape, <empty-block/>) concentrados en TRIGGERS, y DB ID/COL ID de Bug Tracker invertidos en TRACKER-SCHEMA-001. Se intentó delegar la ejecución a Devin/Mistral vía Arena; ambos intentos fueron auditados y rechazados por fabricar old_str (formato de TOC inexistente, placeholders descriptivos en vez de valores reales, entrega final = concatenación sin cambios de los .md de trabajo). El operador ejecutó manualmente la versión final producida por Claude directamente en Notion.
Cambios:
- Renumeración completa: TOC y headers unificados en secuencia §1–§17 (incluye KERNEL:DOCUMENTATION como §3 con sub-IDs §3.1–§3.10, y KERNEL:GATE-DECISION como §9 con sub-IDs §9.1–§9.8). Elimina la duplicidad previa (§8/§9 repetidos) y la desalineación TOC↔cuerpo.
- Agrupación en 4 clústeres narrativos (metadato de TOC, no reordena contenido): I. FUNDAMENTO (§1–§6, incluye Dashboard/Checklist), II. DATOS, ESQUEMAS Y REGLAS (§7–§10), III. EJECUCIÓN (§11–§14), IV. INFRAESTRUCTURA DE CONTEXTO (§15–§17).
- Reordenamiento §12/§13: CANON-UPDATE antes de NAMING-CONVENTION (dependencia: Naming define el nombre de outputs que Canon-Update alimenta).
- Limpieza de residuos de exportación en TRIGGERS (§11): 
 → saltos de línea Markdown, backslashes de escape (\*\*, \-\-, \[\]) normalizados, <empty-block/> sueltos eliminados.
- Eliminación de bloque de cross-references huérfano al final de DATA-FLOW (§16) — nota de trabajo interna de una sesión de edición previa, sin ID canónico ni función de contrato; el Kernel no documenta su propio proceso de edición.
- Corrección DB ID/COL ID en KERNEL:TRACKER-SCHEMA-001 (§8): Bug Tracker tenía DB ID y COL ID invertidos. Valor corregido — DB ID: 36e938be-fc42-81bd-9e1f-dc360b3b45f5 · COL ID: 36e938be-fc42-81f8-8c6f-000b6769ba03. Tasks Tracker no requirió cambio.
Write-Back Verification: re-fetch en vivo del Kernel post-escritura (esta sesión) — TOC y cuerpo coinciden §1–§17 sin discrepancia; 
/backslash/<empty-block/> no detectados fuera del patrón Tipo:
Propósito: ya estándar en el resto del documento; bloque de cross-references confirmado ausente; DB ID/COL ID de Bug Tracker confirmados en el orden corregido.
IDs afectados: ninguna alta/baja de KERNEL:ID canónico — renumeración §N es posicional, no cambia namespace ni claves PREFIX:KEY. KERNEL:CENSUS-SYNC Regla 1 no se dispara. KERNEL:GATE-DECISION-006 (§9.6) ya estaba incorporado desde v9.6.5 — confirmado presente y correctamente indexado en esta renumeración.
Nota de honestidad estructural: el clúster I. FUNDAMENTO incluye KERNEL:DASHBOARD-CHECKLIST-ARCH (§6), que en la propuesta de clústeres original de esta sesión se había asignado a III. EJECUCIÓN. La versión final aplicada en Notion la ubica en Fundamento — confirmar con el operador si fue una decisión deliberada de la sesión o si amerita ticket de reconciliación.
Pendiente (fuera de esta entrada): decidir si el hallazgo de honestidad estructural anterior requiere corrección o si se documenta como decisión final.
Versión actualizada: 9.7.0 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.6.6 hasta que el operador corra verify_versions.py --sync.
---
### v9.6.9 — Reconciliación de Conteo 8→9 (VANTAGE Central Hub) + Extracción de TOC vigente · 2026-07-20
Tipo: [DOC]
Alcance: KERNEL (KERNEL:CENSUS-SYNC §9, KERNEL:DOCUMENTATION-TRANSVERSAL-001 §13).
Contexto: Auditoría del Kernel real detectó que la entrada v9.6.8 dejó KERNEL:CENSUS-SYNC a medio actualizar — ordinal "séptimo" sin corregir a "noveno" y lista de fuente de IDs con 7 nombres en vez de 8 (faltaba VANTAGE Central Hub). Además, KERNEL:DOCUMENTATION-TRANSVERSAL-001 tenía subsección narrativa para Navigation Brief pero ninguna equivalente para VANTAGE Central Hub, pese a que ambos son fundacionales desde el mismo lote de cambios.
Cambios:
- KERNEL:CENSUS-SYNC (§9): "séptimo... otros ocho... siete documentos" → "noveno... otros ocho... ocho documentos (agregando VANTAGE Central Hub)".
- KERNEL:DOCUMENTATION-TRANSVERSAL-001 (§13): nueva subsección "VANTAGE Central Hub — Documento Fundacional de Entrada", paralela en estructura a la de Navigation Brief.
- Extracción de TOC vigente del Kernel (§1–§15, con subsecciones) confirmada contra fetch en vivo — sin discrepancia frente a la tabla "TABLE OF CONTENT" embebida en el documento.
- Se descartó reconciliar el documento externo "PARCHES INDIVIDUALES PARA KERNEL" (solo contemplaba 7→8 con Brief únicamente) — superado por este parche directo.
Write-Back Verification: re-fetch de Kernel tras cada escritura — sin mismatch en ninguna de las dos.
IDs afectados: ninguna alta/baja de KERNEL:ID canónico — corrección de conteo y nueva subsección narrativa bajo secciones ya existentes. KERNEL:CENSUS-SYNC Regla 1 no se dispara.
Tickets logueados en esta sesión (Tasks Tracker):
- ALTO — Modificar generate_census.py: 131 IDs en spec, 121 resueltos, 10 sin link (KERNEL:OWNERSHIP-001/002, KERNEL:TRIGGER-001/002/005/006/007/009, KERNEL:GATE-DECISION-004, KERNEL:NAMING-CONVENTION), 2 huérfanos (KERNEL:HEALTH-CHECK-001.1, KERNEL:HEALTH-CHECK-003). [CENSUS-SYNC-R1] anotado.
- MEDIO — Desarrollar generate_id_inventory.py y apply_hyperlinks.py (porciones pendientes).
- MEDIO — Generar script de normalización de formato ID/título de sección-subsección a través de la suite documental.
Pendiente (fuera de esta entrada): los 3 tickets recién logueados; verify_versions.py real (Terminal) pendiente de extender a 9 documentos (heredado de v9.6.8); Manual §6 desalineado con --check eliminado (heredado, ticket ALTO ya logueado en v9.6.8).
Versión actualizada: 9.6.9 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.6.6 hasta que el operador corra verify_versions.py --sync.
---
### v9.6.8 — Normalización de Conteo de Fundacionales: 7→9 (BRIEF + VANTAGE Central Hub) · 2026-07-20
Tipo: [DOC]
Alcance: KERNEL (KERNEL:DOC-CONTRACT §7, KERNEL:CENSUS-SYNC §9, KERNEL:VERSION-CHECK-TOOL §10 ×3, KERNEL:HEALTH-CHECK §11 ×2 nuevas subsecciones, KERNEL:DOCUMENTATION-TRANSVERSAL-001 §13); SYSTEM PROMPT (SP:BOOTSTRAP-001 ×2, SP:SYNC-RULE, SP:CEDULA-DIGITAL, SP:VERSION-CHECK-TOOL).
Contexto: El operador confirmó en sesión que el conteo de documentos fundacionales pasa de 7 a 9, incorporando Navigation Brief (ya formalizado como 8vo en v9.6.5/v9.6.6) y VANTAGE Central Hub (página hub del workspace, versionable, con artáfactos de trabajo puntuales) como 9no. Se detectó y corrigió en la misma sesión un ID incorrecto para Navigation Brief circulando en un borrador externo (3a3938be-fc42-8089-93f2-f52dbd2dec6c, colisión de sufijo con Career Canon) — el ID real usado aquí es 3a3938be-fc42-8008-9e90-ec435c01f50d, confirmado por fetch directo del Census.
Cambios:
- KERNEL:DOC-CONTRACT (§7): tabla "Prefijos Autorizados" — agregadas filas BRIEF y VANTAGE.
- KERNEL:CENSUS-SYNC (§9): "séptimo... otros seis" → "séptimo... otros ocho"; lista de fuente de IDs ampliada con Navigation Brief.
- KERNEL:VERSION-CHECK-TOOL (§10): conteo 7→9 en Propósito, Output de Sync Mode (filas) y Flujo Canónico paso 3 (documentos restantes).
- KERNEL:HEALTH-CHECK (§11): 2 subsecciones nuevas — KERNEL:HEALTH-CHECK-001.1 (Auto-Archive como Housekeeping, citando Changelog v9.5.9/v9.5.6/v9.5.4, mecanismo no re-verificado contra script en esta sesión) y KERNEL:HEALTH-CHECK-003 (Skills de Mantenimiento del Tracker, tabla de 5 skills).
- KERNEL:DOCUMENTATION-TRANSVERSAL-001 (§13): nueva subsección Navigation Brief — Documento de Descubrimiento y Enrutamiento, con ID corregido.
- SYSTEM PROMPT: 6 ediciones de conteo 7→9 en SP:BOOTSTRAP-001 (×2), SP:SYNC-RULE (lista + cierre), SP:CEDULA-DIGITAL (UUIDs de Brief y Vantage agregados) y SP:VERSION-CHECK-TOOL.
Nota de honestidad estructural: un primer intento de escritura en KERNEL:HEALTH-CHECK-003 produjo una fila de tabla rota por un pipe (|) sin escapar en "V|CHANGELOG" — detectado en Write-Back Verification, no en el DRY RUN, y corregido en la misma sesión antes de este Changelog.
Write-Back Verification: re-fetch de KERNEL tras cada tanda de escritura (incluida la corrección de la tabla) — sin mismatch en el estado final. SYSTEM PROMPT verificado en escritura previa de esta misma sesión.
IDs afectados: ninguna alta/baja de KERNEL:ID canónico — son ediciones de conteo y contenido bajo secciones ya existentes; las 2 subsecciones nuevas de HEALTH-CHECK y la de Navigation Brief documentan mecanismos ya operativos (Changelog v9.5.9/v9.6.0/v9.6.6), no dan de alta identificadores nuevos del esquema PREFIX:KEY. KERNEL:CENSUS-SYNC Regla 1 no se dispara.
Pendiente (fuera de esta entrada, tickets logueados en sesión): (1) Dedup_Flag citado en HEALTH-CHECK-001.1 no está en la enumeración Class B de KERNEL:SCHEMA-001 — pendiente conciliar contra esquema real; (2) Manual §6 (MANUAL:SESSION-CYCLE-001) describe verify_versions.py con 3 flags activos incluyendo --check, ya eliminado del Kernel en v9.6.2 — desalineación mayor, ticket ALTO logueado en Tasks Tracker; (3) verify_versions.py real (Terminal) pendiente de extenderse a 9 documentos — no verificado en esta sesión, solo documentado como pendiente.
Versión actualizada: 9.6.8 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.6.6 hasta que el operador corra verify_versions.py --sync.
---
### v9.6.7 — Schema Consolidation: Bug Tracker ↔ Archivo Bug Tracker / Task Tracker ↔ Archivo Task Tracker · 2026-07-20
Tipo: [INFRA] [SCHEMA]
Alcance: Igualación de esquemas en cuatro databases Notion para garantizar integridad de datos en flujos de archivado automático (vantage-tidy-bug-task-tracker).
Cambios Ejecutados:
| Database | Acción | Propiedades |
| BUG TRACKER | Agregar | Creado, Etiquetas, Fecha_Resolución, Solución |
| ARCHIVO BUG TRACKER | Eliminar/Renombrar | ✗ Prioridad (number); Prioridad 1 → Prioridad; Nombre → Bug |
| TASK TRACKER | Agregar | Fecha_Cierre, Creado |
| ARCHIVO TASK TRACKER | Consolidar Status | 3 valores [Pendiente, En progreso, Hecho] |
IDs Afectados: Ninguno en documentos fundacionales — cambios de schema en data sources Notion únicamente
(collection://36e938be..., collection://9ef938be..., collection://aaaaef55..., collection://c470ead7...)
Impacto en Pipeline: vantage-tidy-bug-task-tracker ahora opera sobre esquemas idénticos activo↔archivo, 
eliminando riesgo de truncamiento o pérdida de datos en migración.
Versión Actualizada: v9.6.7 (solo CHANGELOG). Resto de fundacionales en v9.6.6 hasta versions --sync.
---
v9.6.6 — [2026-07-20] — ORQUESTACIÓN ESTRUCTURAL Y NAVEGACIÓN
1. Integración Documental (Navigation Brief)
- Alcance: Formalización del Navigation Brief (ID: 3a3938be-...) como 8vo documento fundacional del ecosistema VANTAGE.
- Gobernanza: Inclusión en SP:SYNC-RULE y KERNEL:CENSUS-SYNC. El documento queda sujeto a la Regla de Versión Única (bloqueante ante discrepancias de versión).
- Versión: Asignada v9.6.5 de forma sincronizada con el resto de la suite.
1. Reingeniería del Master Index
- Sustitución de S.S.O.T.: Eliminación del Bloque 3 (Census Embebido) por redundancia con V:ID-CENSUS.
- Estandarización:
- Bloque 1: Suite de 8 fundacionales, sincronizados contra SP:CEDULA-DIGITAL v9.6.5.
- Bloque 2: Actualización de trackers (Archivo Task, Bug, Changelog, Manifest, Ledger) con IDs de base de datos validados.
- Propósito: El documento queda consolidado exclusivamente como Índice de Descubrimiento de activos y rutas.
1. Normalización del ID Census
- Expansión: Registro de 11 nuevos identificadores (BRIEF:001 al BRIEF:011) para las secciones del Navigation Brief.
- Integridad: Verificación final mediante generate_census.py (v3.0) con resultado: 131/131 IDs resueltos, 0 huérfanos, 0 colisiones.
1. Actualizaciones del Sistema de Supervisión
- Scripting: Modificación profunda en verify_versions.py (DOC_KEYS extendido a 8 documentos + fallback BRIEF_FALLBACK_ID).
- VANTAGE HUB (Página Principal): Implementación de supervisión pasiva (v9.0.1). El sistema ahora reporta el status en -sync y -bootstrap sin disparar bloqueos (veredicto tolerante al formato de propiedad "Versión ").
- Cross-Referencing: Inyección masiva de hipervínculos normalizados en Kernel, Manual y System Prompt (apply_hyperlinks.py).
1. Auditoría de Cierre
- Verificación: verify_versions.py --sync reportó PASS en todos los documentos.
- Pending validation: Se da por resuelta la entrada del Changelog v9.6.3 ("Pending Validation") al completarse la integración aquí descrita.
> El histórico completo del CHANGELOG lo podrás encontrar en ARCHIVO CHANGELOG, en esta pagina de consulta continua solo encontrarás las últimas diez entradas para garantizar la operación y referencia del sistema.

