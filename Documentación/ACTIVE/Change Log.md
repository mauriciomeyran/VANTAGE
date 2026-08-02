# V | CHANGELOG

### v9.13.3 — Auditoría de Cierre: Tooling de Heading IDs Verificado (GATE 1/2 PASS) · 2026-08-02
Tipo: [DOC] [AUDIT]
Alcance: Layer_1/scripts/vantage_id_rules.py, normalize_heading_ids.py, generate_id_inventory.py (verificación, sin cambio de código). KERNEL:DOCUMENTATION-011 (referencia de estado).
Contexto: Contrato de sesión solicitaba refactor de vantage_id_rules.py y fix de normalize_heading_ids.py bajo el supuesto de que ambos scripts operaban con lógica legacy (búsqueda de símbolo §, falsos positivos de "heading mal formado"). Verificación directa contra código y ejecución real determinó que el supuesto no aplicaba: la migración correspondiente ya se había completado en sesión previa (contrato 2026-07-25, ver contrato_migracion_headings.md) y KERNEL:DOCUMENTATION-011 ya confirma "generate_id_inventory.py y normalize_heading_ids.py ya fueron migrados". No hubo refactor que ejecutar — la tarea real era auditoría de cierre.
Cambios:
- py_compile OK sobre los 3 scripts (vantage_id_rules.py, normalize_heading_ids.py, generate_id_inventory.py) — GATE 2 (integridad de dependencias) PASS. Confirmado que normalize_heading_ids.py importa classify_heading/suggest_canonical_heading de vantage_id_rules.py sin reimplementación local.
- normalize_heading_ids.py ejecutado en modo dry-run real (sin --apply) sobre los 6 documentos editables vía Terminal del operador (venv Layer_1/.venv), no simulado: "Ningún heading mal formado detectado. Nomenclatura 100% canónica." — GATE 1 PASS.
- GATE 3 (sync de versión) ya satisfecho por vversions --sync corrido por el operador en esta misma sesión, previo a esta entrada — confirmó los 9 fundacionales en v9.13.2 antes de este batch.
IDs afectados: ninguno — verificación de tooling, no de documentación fundacional. Census no requiere regeneración.
Verificación: py_compile exit 0 (3/3 scripts); normalize_heading_ids.py --csv corrido en Terminal real del operador, exit 0, 0 hallazgos.
Pendiente (fuera de esta entrada): ninguno nuevo generado por esta auditoría.
Versión actualizada: 9.13.3 (CHANGELOG). El resto de los fundacionales permanece en v9.13.2 hasta vversions --sync.
---
### v9.13.2 — Infraestructura: Refactor vsync_doc (PATCH) e Implementación class_b_guard (GAP-03) · 2026-08-01
Tipo: [FIX] [INFRA] [SECURITY]
Alcance: Layer_4/scripts/vsync_doc.py; Layer_1/scripts/class_b_guard.py.
Contexto: Resolución del riesgo de integridad de anchors documentado en KERNEL:ARCHITECTURE-L4 y mitigación técnica de GAP-03 (KERNEL:GATE-DECISION-003).
Cambios:
- vsync_doc.py: Función push_local_to_notion() reescrita íntegramente para usar el método PATCH puntual (notion.blocks.update). Se elimina el patrón destructivo delete-all + create-all que invalidaba los block_ids necesarios para el Sistema de Cross-Reference Hyperlinks (KERNEL:DOCUMENTATION-011).
- class_b_guard.py: Implementación del guard técnico para bloquear escrituras desde el componente AI hacia campos Class B (Score, Gate_Decision, VM_Scope, etc.). Asegura el cumplimiento del contrato de ownership definido en KERNEL:SCHEMA-001 y KERNEL:OWNERSHIP-001.
- Deuda Técnica: Eliminados comentarios temporales de v8.5.7 en los scripts de sincronización.
Verificación: py_compile OK; diff validado sin ciclos de borrado; test de bloqueo Class B PASS.
IDs afectados: Ninguno (cambios de lógica de sistema). Census no requiere regeneración.
Pendiente: vversions --sync para propagar v9.13.2 a los documentos fundacionales.
---
### v9.13.1 — [COMPRIMIDO] Saneamiento Bug/Task Tracker: 9 tickets cerrados, 2 propiedades Solución creadas, 1 bug de skill logueado · 2026-08-01
Tipo: [COMPRIMIDO]
Resumen: vantage-tidy-bug-task-tracker corrido (8 tickets, Bug+Task) pero Escenario 2 (cruce Changelog) no fue exhaustivo — operador cerró manualmente varios tickets adicionales después, exponiendo el gap. Bug Tracker: 3 tickets cerrados manualmente por el operador recibieron Solución+Fecha_Resolución retroactivas (Dedup no detecta duplicados, Sesiones huérfanas, GAP-03); 1 ticket más (is_definition_block TOC) cerrado con evidencia real hallada en Changelog v9.12.0. Ticket nuevo creado: 'Escenario 2 del skill vantage-tidy-bug-task-tracker no hace cruce exhaustivo contra Changelog' (3af938be-fc42-812e-99d9-c886c680bbfb), Prioridad ALTO. Propiedad Solución (rich_text) creada en Tasks Tracker (aaaaef55...) y Archivo Task Tracker (c470ead7...), antes inexistente en ambas — 15 tareas archivadas documentadas: 1 con evidencia real (v9.11.2), 10 autocontenidas en Notas, 4 marcadas explícitamente sin evidencia/pendientes de confirmar con el operador. Bug Tracker y Task Tracker activos revisados en su totalidad contra Changelog completo (activo+archivo) — 7 bugs y 5 tasks abiertas confirmadas vigentes, sin decisión arquitectónica que las vuelva obsoletas. Expandir en próxima sesión: revisar los 4 tasks sin evidencia con el operador directamente.
---
### v9.13.0 — Cierre Auditoría Dedup Archivo Tracker (6/6 grupos) + Fix vantage_id_rules.py Verificado + 2 Tickets Resueltos · 2026-08-01
Tipo: [FIX] [BUG] [DOC]
Alcance: Archivo Tracker (12 páginas, data source 674696fd-94b6-464a-ac1f-64b0cc917e15); Layer_1/scripts/vantage_id_rules.py (verificación, sin cambio de código en esta entrada); Bug Tracker (2 tickets: 3aa938be-fc42-818e-bd1a-e899bbd6d569, 3a5938be-fc42-81ef-b268-ff186307f6b3).
Contexto: Continuación directa de v9.12.1. El dry-run de Devin sobre el Archivo Tracker (6 grupos: GILSA, Scappino, Petco, Nike Artz Pedregal, Dolce & Gabbana, Bershka) había sido marcado INCOMPLETO al cierre de v9.12.1 — verificado en esa sesión que GILSA tenía 6 páginas reales vs 3 reportadas. Esta sesión completó la verificación independiente página-por-página de los 6 grupos completos, confirmando el mismo patrón de bug en múltiples grupos: Devin agrupaba por similitud de Rol/título en vez de por fingerprint real de posting (URL o hash), produciendo tanto falsos positivos (páginas de Puma, Paco Rabanne, Pull&Bear agrupadas bajo "Bershka" por compartir el título genérico "Escaparatista") como falsos negativos (Dolce & Gabbana: 6 páginas reales del mismo posting vs. 2 reportadas).
Cambios:
- Archivo Tracker — 12 páginas marcadas Archivar=YES tras verificación individual (fetch + comparación de userDefined:URL/hash) y APROBAR_WRITE explícito del operador por cada grupo: GILSA (3), Scappino (1), Petco (1), Nike Artz Pedregal (1), Dolce & Gabbana (5), Bershka (1). Cada escritura verificada por re-fetch inmediato (write-back verification), 12/12 PASS.
- Nike Artz Pedregal: operador confirmó regla de exclusión — vacantes de piso de venta bajo este holding son Hard Block (no se postulan ni se tratan como leads activos); 7+ variantes de título adicionales identificadas pero no tocadas en este ciclo, quedan pendientes de un batch de Hard Block separado si el operador lo autoriza.
- vantage_id_rules.py — fix de regex \d{2}→\d{1,2} (enviado en v9.12.1) verificado en esta sesión: python3 -m py_compile OK; dry-run de normalize_heading_ids.py sobre los 5 documentos (SP, Manual, Kernel, Career Canon, Aliases) reportó "Ningún heading mal formado detectado. Nomenclatura 100% canónica." — confirma que MANUAL:WEEKLY-FLOW-001 (heading de un dígito, antes falso positivo bajo \d{2}) ahora se reconoce correctamente.
- Bug Tracker 3aa938be...d569 ("Discrepancia de protección de estados terminales") — Status Abierto/En revisión → Resuelto. La decisión ya registrada en Solución (angostar layer_1_run.py FASE 4 a TERMINAL_ACTIONS={Archivar, Expirada}, ya vigente en producción según v9.11.7) se reafirma como cerrada; Next_Action → Documentar (pendiente reflejar en KERNEL:GATE-DECISION en sesión futura).
- Bug Tracker 3a5938be...f6b3 ("Dedup Caso 5 — Next_Action=Archivar no se ejecuta automáticamente") — ya Resuelto (solución: flujo manual vía checkbox adoptado en vez de auto_archive.py, decisión operador 2026-08-01); Next_Action → Documentar por consistencia.
- Changelog — tidy ejecutado en la misma pasada: entradas activas reducidas de 12 a 10 (esta entrada incluida), exceso movido a Archivo Changelog.
IDs afectados: ninguno — cambios de datos operativos (Archivo Tracker, Bug Tracker) y verificación de tooling, no de documentación fundacional. Census no requiere regeneración.
Write-Back Verification: 12/12 páginas del Archivo Tracker re-fetched individualmente tras cada escritura, mismatch=0. 2/2 tickets de Bug Tracker re-fetched, Status confirmado.
Pendiente (fuera de esta entrada):
- Hard Block formal para variantes de "Nike Artz Pedregal" (7+ páginas de piso de venta identificadas, sin tocar) — requiere batch separado con APROBAR_WRITE explícito.
- KERNEL:GATE-DECISION sin actualizar aún para reflejar TERMINAL_ACTIONS={Archivar, Expirada} como definición canónica documentada (código ya lo aplica desde v9.11.7).
- Reemplazo pendiente en Layer_1/scripts: normalize_heading_ids.py, apply_hyperlinks.py, vantage-tidy-opportunities-tracker.md (versiones limpiadas, acción local del operador, fuera de alcance de este Changelog).
- T3, T5, T7, D3/GAP-03, D4/B6 Caso 4, 7 IDs ALIASES:* faltantes en CENSUS_SPEC, 3 anchors PENDIENTE_ANCHOR — heredados, sin tocar esta sesión.
- Esquema del Archivo Tracker con propiedades duplicadas/corruptas (Next_Action 1, Score_Method faltante) — cosmético, no bloqueante.
Versión actualizada: 9.13.0 (CHANGELOG). El resto de los fundacionales permanece en v9.12.1 hasta vversions --sync.
---
### v9.12.1 — [COMPRIMIDO] Auditoría Dedup Archivo Tracker + Fix vantage_id_rules.py · 2026-08-01
Tipo: [COMPRIMIDO]
Resumen: Decisión terminal states (angostar layer_1_run.py a TERMINAL_ACTIONS) registrada en Bug Tracker (3aa938be...). GAP-03 documentado con límite técnico (sin hook MCP server, requiere disciplina de importación). Fix de regex en vantage_id_rules.py enviado al operador (d{2}→d{1,2}), pendiente confirmar py_compile. Backfill de dedup fingerprint en Tracker activo: incidente de 49/49 falsos positivos por Devin, revertido, caso Promotwist legítimo restaurado y verificado. Dry-run de Devin sobre Archivo Tracker (GILSA + 5 grupos) detectado INCOMPLETO — verificado directamente 6 páginas GILSA reales vs 3 reportadas por Devin. Nada escrito en Archivo Tracker todavía. Expandir en próxima sesión.
---
### v9.12.1 — Documentación Transversal: apply_hyperlinks_notion.py Formalizado (KERNEL:DOCUMENTATION-011, KERNEL:ARCHITECTURE-L4, MANUAL:HEALTHCHECK, Aliases) · 2026-08-01
Tipo: [DOC]
Alcance: Kernel (KERNEL:DOCUMENTATION-011, KERNEL:ARCHITECTURE-L4); Manual (sección Aplicación de Hipervínculos Cross-Reference); Aliases (ALIASES:L4-VERSION-CONTROL, fila vhyperlinks).
Contexto: Cierra el pendiente diferido explícitamente en v9.11.8 y v9.11.9 ("Documentación transversal formal de este hallazgo — diferida a sesión futura"). apply_hyperlinks_notion.py llevaba dos entradas de Changelog documentando su creación y uso en producción sin que ningún documento fundacional reflejara su existencia como pieza del sistema — Kernel y Manual seguían describiendo apply_hyperlinks.py (variante local, deprecada) como si fuera la vía activa.
Cambios:
- KERNEL:DOCUMENTATION-011 — Piezas actualizado: apply_hyperlinks_notion.py agregado como vía activa de escritura; apply_hyperlinks.py marcado DEPRECATED. Estado de adopción (2026-08-01) agregado, referenciando el fix de table_row (v9.12.0).
- KERNEL:ARCHITECTURE-L4 — nota de riesgo agregada tras la descripción de vsync_doc.py/vdoc: destroy/rebuild de push_local_to_notion() invalida anchors de hyperlinks; advertencia de no correr vdoc local sobre documentos con hyperlinks recién aplicados.
- MANUAL:HEALTHCHECK — sección "Aplicación de Hipervínculos Cross-Reference" reescrita: comando activo es apply_hyperlinks_notion.py --all --apply, apply_hyperlinks.py marcado deprecated, referencia cruzada al riesgo de vdoc local.
- Aliases — ALIASES:L4-VERSION-CONTROL, fila vhyperlinks: procedimiento interno actualizado a apply_hyperlinks_notion.py.
IDs afectados: ninguno — actualización de contenido bajo IDs existentes. Census no requiere regeneración.
Write-Back Verification: confirmado en Fase 4 de este mismo protocolo tras la escritura — re-fetch de los 4 nodos sin mismatch.
Pendiente (fuera de esta entrada, sin cambio): EXCLUDE_IDS vacío en apply_hyperlinks_notion.py; 3 anchors sin DEF (MANUAL:COLD-START-001, ALIASES:DEDUP, SP:CONSISTENCY §9 legacy); V-MASTER-INDEX desactualizado.
Versión actualizada: 9.12.1 (CHANGELOG). El resto de los fundacionales permanece en v9.12.0 hasta vversions --sync.
---
### v9.12.0 — Fix TOC Hyperlinks: is_definition_block() excluye table_row · 2026-08-01
Tipo: [FIX] [BUG]
Alcance: Layer_1/scripts/generate_census.py (is_definition_block()); apply_hyperlinks_notion.py (--all --apply); los 7 documentos fundacionales; Bug Tracker (ticket 3af938be-fc42-8151-a309-d1c14abcea4a).
Contexto: Bug reportado en v9.11.9 — ningún TOC (tabla de índice al inicio de cada documento, columna "ID") recibía hipervínculo pese a que apply_hyperlinks_notion.py --all --apply corría sin error. Causa raíz aislada por lectura directa de código: la rama "stripped == id_str" en is_definition_block() fue diseñada para detectar bloques-ancla standalone (párrafo cuyo único contenido es el ID), pero también se dispara cuando una celda de tabla del TOC contiene únicamente el ID como texto plano — patrón estándar en las tablas de índice. Consecuencia: las celdas de TOC se clasificaban erróneamente como DEF propio → se excluían de recibir link.
Cambios:
- generate_census.py — is_definition_block(): agregada variable is_table_row = (btype == "table_row"); modificado la primera condición del return de "stripped == id_str" a "(stripped == id_str and not is_table_row)". Esto es quirúrgico: solo afecta la rama problemática, preservando todas las demás condiciones intactas.
- Verificación de no-regresión: vcensus corrido tras el fix — 209/209 IDs resueltos (sin cambio), 0 huérfanos nuevos, 0 IDs que antes resolvían DEF correctamente dejaron de hacerlo.
- apply_hyperlinks_notion.py --all --dry-run: 239 bloques en el plan (vs 143 antes del fix) — diferencia de +96 bloques correspondientes a celdas de TOC que antes se excluían erróneamente.
- apply_hyperlinks_notion.py --all --apply: 239 bloques patcheados, 0 errores. Breakdown por documento: Kernel 29 (17 TOC + 12 prosa), System Prompt 16 (11 TOC + 5 prosa), Manual 111 (21 TOC + 90 prosa/tablas), Career Canon 15 (13 TOC + 2 quotes), Aliases 8 (8 TOC), Change Log 49 (49 prosa), Navigation Brief 11 (11 TOC).
IDs afectados: ninguno — conversión de texto plano a hipervínculo real sobre IDs ya existentes en los 7 documentos. Census no requiere regeneración.
Write-Back Verification: --apply ejecutado exitosamente con 0 errores. Verificación de clickeabilidad en Notion pendiente (protocolo del proyecto: verificación independiente por operador en sesión con Claude).
Versión actualizada: 9.12.0 (CHANGELOG). El resto de los fundacionales permanece en v9.11.9 hasta vversions --sync.
---
### v9.11.9 — Batch Hyperlinks (--all --apply, 143 bloques) + Bug TOC-Exclusion Confirmado por Código · 2026-08-01
Tipo: [FEATURE] [BUG]
Alcance: Layer_1/scripts/apply_hyperlinks_notion.py (--all --apply); los 7 documentos fundacionales (Kernel, System Prompt, Manual, Career Canon, Aliases, Change Log, Navigation Brief); Bug Tracker (ticket nuevo).
Contexto: Continuación directa de v9.11.8. Tras validar el patrón PATCH puntual en Career Canon (2 bloques) y Kernel (12 bloques, dry-run verificado línea por línea contra generate_id_inventory.py antes de aplicar), se corrió --all --apply sobre los 7 documentos en una sola pasada. Durante la revisión, el operador señaló que ningún TOC se estaba enlazando — investigación por lectura directa de código (no inferida) aisló la causa en is_definition_block() (generate_census.py): la condición stripped == id_str, pensada para detectar bloques-ancla standalone, también matchea falsamente celdas de tabla TOC cuyo único contenido es el ID bare — excluyéndolas de recibir link.
Cambios:
- apply_hyperlinks_notion.py --all --apply ejecutado sobre los 7 documentos: Kernel 12, System Prompt 5, Manual 78, Career Canon 2, Aliases 0, Change Log 46, Navigation Brief 0 — total 143 bloques patcheados, 0 errores. (Kernel y Career Canon ya habían sido aplicados individualmente antes de esta corrida — el re-patch fue idempotente, sin efecto adicional.)
- Bug registrado en Bug Tracker: TOC de los 7 documentos no recibe hyperlinks por falso positivo en is_definition_block() — Prioridad 2 MEDIO, Componente Python, Next_Action Patch. Cross-ref: V-MASTER-INDEX (391938be-fc42-8085-b7ad-ff68b601dec4) contiene TOCs duplicadas manualmente, fuera de este pipeline, desactualizada — housekeeping separado, no bloquea este fix.
IDs afectados: ninguno — conversión de texto plano a hipervínculo real sobre IDs ya existentes en los 7 documentos. Census no requiere regeneración.
Write-Back Verification: Kernel re-fetched de forma independiente tras --apply — los 12 links confirmados clickeables con anchors reales (ejemplos verificados: MANUAL:SETUP, KERNEL:DOCUMENTATION-003 ×2, SP:CONSISTENCY, MANUAL:SESSION-CYCLE, KERNEL:OWNERSHIP-002, los 4 GATE-DECISION de la fila 460, los 2 de la fila 483, CANON:OUTPUT-CONTRACT).
Pendiente (fuera de esta entrada):
- Fix de is_definition_block() (excluir btype table_row de la rama "stripped == id_str", o exigir is_heading) — bloquea que los TOCs de los 7 documentos se enlacen. Cambio afecta también al censo (vcensus), requiere revisión de impacto antes de aplicar.
- Documentación transversal formal (KERNEL:ARCHITECTURE-L4, KERNEL:DOCUMENTATION-011, posible ajuste de vantage-hyperlink-loop) — diferida hasta resolver el bug de TOC.
- EXCLUDE_IDS vacío en apply_hyperlinks_notion.py — copiar la lista real de apply_hyperlinks.py (27 IDs) antes de futuras corridas donde esa exclusión importe.
- 3 anchors sin DEF resuelto en la spec (MANUAL:COLD-START-001, ALIASES:DEDUP, SP:CONSISTENCY §9 legacy) — pin explícito, sin cambio en esta entrada.
- V-MASTER-INDEX desactualizado (v9.6.5 propia, docs listados en v9.11.5, IDs obsoletos) — housekeeping separado, sin fecha asignada.
Versión actualizada: 9.11.9 (CHANGELOG). El resto de los fundacionales permanece en v9.11.8 hasta vversions --sync.
---
### v9.11.8 — Fix Raíz: PATCH Puntual Reemplaza Destroy/Rebuild para Hyperlinks (apply_hyperlinks_notion.py) · 2026-08-01
Tipo: [FIX] [ARCHITECTURE]
Alcance: Layer_1/scripts/apply_hyperlinks_notion.py (nuevo, local); Career Canon (2 bloques quote, sección 10 CANON:MAJOR-PROJECTS).
Contexto: Bug reportado por el operador al abrir sesión — "los links de la TOC no hacen nada al click" pese a que vcensus reportaba 209/209 IDs resueltos y vhyperlinks --apply corría sin error. Causa raíz aislada por lectura directa de código (no inferida): vsync_doc.py y vsync_doc_fast.py (push_local_to_notion()) hacen delete-all + create-all sobre TODOS los bloques de la página en cada corrida de 'vdoc local' — cualquier anchor #block-id generado por vhyperlinks queda huérfano en cuanto corre el siguiente sync, porque Notion asigna block-IDs nuevos a los bloques recreados. Confirmado como mecanismo consciente pero mal cerrado: el propio código trae comentarios "TEMPORALMENTE HABILITADO... debe ser deshabilitado después" (v8.5.7) nunca revertidos.
Cambios:
- Nuevo script apply_hyperlinks_notion.py: aplica hyperlinks DIRECTO a bloques de Notion vía PATCH puntual (notion.blocks.update / PATCH /v1/blocks/{id}), preservando block-ID — nunca borra ni recrea bloques para este flujo. Reusa fetch_blocks_recursive/extract_ids_from_block/is_definition_block de generate_census.py (no reimplementa) y vantage_id_rules.py (mismo módulo único de reglas que ya usan normalize_heading_ids.py y apply_hyperlinks.py).
- MAPPING ID→URL ya no es diccionario estático hardcodeado (como en apply_hyperlinks.py, con anchors PENDIENTE_ANCHOR sin resolver) — se construye en cada corrida desde el link_index real de generate_census.py, eliminando de raíz la clase de bug de anchors desactualizados.
- Validado en producción: --doc career_canon --apply, 2 bloques patcheados (quote, sección CANON:MAJOR-PROJECTS), 0 errores. Confirmado por el operador en Notion: link clickeable, block-ID preservado (verificado contra Historial de versiones — edición incremental, no rebuild).
IDs afectados: ninguno — ambos bloques ya contenían los IDs CANON:OUTPUT-CONTRACT-002 y CANON:POSITIONING-N2 en texto plano; el cambio fue solo la conversión a hipervínculo real. Census no requiere regeneración.
Write-Back Verification: confirmado por el operador directamente en Notion (click funcional) — no solo por código de retorno 200 del script.
Pendiente (fuera de esta entrada, explícitamente pineado por el operador para sesión futura):
- 3 anchors sin DEF resuelto en la spec (MANUAL:COLD-START-001, ALIASES:DEDUP, SP:CONSISTENCY §9 legacy) — no se resuelven en este fix, quedan sin link igual que hoy en vcensus.
- EXCLUDE_IDS vacío en apply_hyperlinks_notion.py — copiar la lista real de apply_hyperlinks.py (27 IDs en la última corrida) antes de correr --all sobre documentos donde esa exclusión importe.
- Sin probar aún en Kernel (26 cambios) ni Manual (40 cambios) — mayor volumen de table_row, recomendado --dry-run individual antes de --apply.
- Documentación transversal formal de este hallazgo (KERNEL:ARCHITECTURE-L4, KERNEL:DOCUMENTATION-011, posible actualización del skill vantage-hyperlink-loop) — decisión del operador: diferida a sesión futura por límite de tokens en esta sesión.
- vsync_doc.py / vsync_doc_fast.py NO fueron modificados ni deprecados en esta entrada — siguen existiendo con el mecanismo destroy/rebuild; el operador debe evitar 'vdoc local' sobre documentos con hyperlinks recién aplicados hasta que se decida su reemplazo formal o se documente la restricción de uso.
Versión actualizada: 9.11.8 (CHANGELOG). El resto de los fundacionales permanece en v9.11.7 hasta vversions --sync.
---
### v9.11.7 — Registro Retroactivo: Fix Protección Terminal gate_logic() (commit ca5f1a8, 2026-07-29) · 2026-08-01
Tipo: [FIX] [DOC-RETROACTIVO]
Alcance: Layer_1/scripts/layer_1_run.py (local, código ya en producción desde el 29-jul); Bug Tracker (ticket 3ac938be-fc42-8149-a909-c8a1b426e7e6).
Contexto: El fix real se aplicó el 2026-07-29 vía fix_terminal_protection_layer_1_run.patch (commit ca5f1a8, 04:47), ANTES de que el ticket correspondiente fuera abierto — por eso nunca generó su propia entrada de Changelog en su momento. Un reporte de Devin marcó el hallazgo original ("protección de gate_logic() es código muerto por la línea 772") como implementado; verificación directa contra el código real (layer_1_run.py, main, GitHub) en esta sesión confirmó que la línea 'if current_action: continue' descrita por el ticket ya NO existe — el patch la había reemplazado antes de la apertura del ticket. Falso positivo confirmado, no un bug nuevo.
Cambios (ya vigentes en producción desde el 29-jul, documentados aquí por primera vez):
- layer_1_run.py línea ~842: único mecanismo de protección de estado terminal es ahora gate_logic(entry), invocado antes de gate() (FASE 4).
- gate_logic.py: TERMINAL_ACTIONS = {'Archivar', 'Expirada'} — criterio angosto, alineado con decisión de gobierno 2026-08-01.
IDs afectados: ninguno — cambio de código Python, no de documentación Notion. Census no requiere regeneración.
Verificación: confirmado por Devin y re-verificado independientemente por Claude contra el repo (GitHub, rama main) en esta sesión. Ticket 3ac938be-fc42-8149-a909-c8a1b426e7e6 cerrado como Resuelto (falso positivo), Prioridad 4 CRÍTICO, Fecha_Resolución 2026-08-01.
Nota de alcance — no confundir con B3: este fix resuelve únicamente la capa de PROTECCIÓN de estados terminales (qué registros NO se re-evalúan). Es distinto y no desbloquea automáticamente el bug de EJECUCIÓN de archivado automático (Bug Tracker: "Dedup Caso 5 — Next_Action=Archivar no se ejecuta automáticamente", Status Abierto) — ese bug sigue abierto, y además existe un tercer ticket sin resolver ("Discrepancia de protección de estados terminales": gate_logic.py vs. layer_1_run.py FASE 4) que es prerequisito de diseño antes de construir auto_archive.py (KERNEL:GATE-DECISION-007).
Pendiente (fuera de esta entrada):
- Decisión del operador sobre la discrepancia FASE 4 (protección amplia: cualquier Next_Action no vacío) vs. gate_logic.py (protección angosta: solo Archivar/Expirada) — ticket abierto, Prioridad 3 ALTO.
- Bug "Dedup Caso 5" (archivado automático nunca se ejecuta) — sigue abierto, Prioridad 3 ALTO, sin auto_archive.py construido.
- T3, T5, T7, D3/GAP-03, D4/B6 Caso 4 — heredados, sin tocar esta sesión.
Versión actualizada: 9.11.7 (CHANGELOG). El resto de los fundacionales permanece en v9.11.5/9.11.6 hasta vversions --sync.
---
### v9.11.6 — Manual §6 Sincronizado + Fix normalize_heading_ids.py (ok_legacy_sectioned) · 2026-08-01
Tipo: [FIX] [DOC]
Alcance: Manual (MANUAL:SESSION-CYCLE, §6); Layer_1/scripts/normalize_heading_ids.py (local).
Contexto: Dos hallazgos independientes en la misma sesión. (1) Manual §6 seguía documentando "6 documentos fundacionales + el Census" pese a la expansión a 9 fundacionales vigente desde v9.11.x — drift de conteo detectado por auditoría cruzada con SP:SYNC-RULE. (2) Lectura directa de vantage_id_rules.py y normalize_heading_ids.py reveló que audit() ignoraba en silencio el estado ok_legacy_sectioned (headings aún en formato §N) pese a que el propio módulo lo declara "SIEMPRE candidato a migrar" — confirmado por código, no inferido.
Cambios:
- Manual — MANUAL:SESSION-CYCLE (§6): "Confirma que los 6 documentos fundacionales + el Census..." corregido a "9 documentos fundacionales + el Census". Ejecutado vía contrato determinista (Mistral, pares old_str/new_str, APROBAR_WRITE explícito).
- normalize_heading_ids.py — audit(): condición ampliada de status == "malformed" a status in ("malformed", "ok_legacy_sectioned"); reporte de consola distingue tag [LEGACY]/[MALFORMED]. Diff mínimo, sin cambio de firma ni flags nuevos. py_compile OK.
IDs afectados: ninguno — ambos cambios son de contenido/tooling, no alta/baja de ID canónico. Census no requiere regeneración.
Write-Back Verification: Manual re-fetched de forma independiente tras la escritura — línea corregida confirmada, resto de §6 y del documento byte-idéntico. Script verificado vía py_compile, entregado al operador vía present_files.
Ticket asociado: Bug Tracker 3af938be-fc42-813e-9b50-e286ae7f121a (Resuelto, Prioridad 3 ALTO).
Pendiente (fuera de esta entrada):
- Operador debe reemplazar normalize_heading_ids.py en Layer_1/scripts/ y correr dry-run real para confirmar 0 headings § vivos o detectarlos por primera vez.
- T3 (Documentación Transversal Fase 2), T4 (Census — contradicción a verificar, fetch de esta sesión mostró 0 huérfanos), T5, T7, B3, D3/GAP-03, D4/B6 Caso 4 — heredados, sin tocar esta sesión (detalle completo en handoff de sesión).
- Changelog retroactivo del patch fix_terminal_protection_layer_1_run.patch (2026-07-29) — aún sin decisión.
Versión actualizada: 9.11.6 (CHANGELOG + Manual). El resto de los fundacionales permanece en v9.11.5 hasta vversions --sync.
---
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
> El histórico completo del CHANGELOG lo podrás encontrar en ARCHIVO CHANGELOG, en esta pagina de consulta continua solo encontrarás las últimas diez entradas para garantizar la operación y referencia del sistema.
---
