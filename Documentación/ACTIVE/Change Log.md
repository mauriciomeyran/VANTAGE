# V | CHANGELOG

Tipo: [CODE] [DOC]
Alcance:
- Script nuevo: bulk_upload_skill_bodies.py (Layer_1/scripts)
- Skill Library (Notion) — 28 bodies escritos
- Skill: vantage-sync-skill-library — extensión para escribir body completo en altas futuras
Contexto: Las páginas de Skill Library tenían solo metadata; el body estaba vacío. Se entregó script local (API directa, sin MCP) que descubre skills hasta 2 niveles, matchea contra la data source y escribe el SKILL.md completo como bloques Notion. Dry-run → 28/28 match. Ejecución --write → 28 bodies OK, 0 fallidos. Paralelamente se actualizó la skill de sync para que las altas futuras ya salgan con body desde el primer alta.
Cambios:
- bulk_upload_skill_bodies.py — creado (dry-run default, --write, --only, --force).
- Skill Library — 28 páginas con lógica completa cargada.
- vantage-sync-skill-library — procedimiento + reglas de oro actualizados para body writing; referencia explícita al script para carga histórica.
IDs afectados: Ninguno.
Write-Back Verification: Change Log re-fetched implícito; versión → v9.21.17.
Pendiente:
- vversions --sync para propagar v9.21.17.
- Operador: mover las 2 filas Deprecado al archivo (ya marcadas).
---
Tipo: [AUDIT] [DOC]
Alcance:
- Skill Library (Notion) — 2 filas deprecadas ya marcadas
- generate_census.py / CENSUS_SPEC — drift de 65 secciones hardcodeadas (script ejecutado, vcensus final limpio)
Contexto: Sesión de confirmación post-handoff. Las 2 filas deprecadas (extract-learnings.skill, vantage-audit-navigation-brief.skill) ya tenían Estado=Deprecado + Acción=Archivar; re-fetch confirmó estado. Operador moverá manualmente a archivo. Por separado, el script fix_seccion_drift.sh se ejecutó (pasadas parciales 60/65 + 5/65 por diferencias de estado intermedio); vcensus post-ejecución: 240/240 IDs, 0 huérfanos, 0 sin link, 0 secciones hardcodeadas sin heading detectables en vivo. El drift hardcodeado era fallback silencioso (nunca afectó exports reales).
Cambios:
- Skill Library: confirmación de marcaje (sin escritura adicional requerida).
- CENSUS_SPEC local: higiene de secciones hardcodeadas alineada vía script + verificación vcensus.
IDs afectados: Ninguno.
Write-Back Verification: Change Log re-fetched implícito en esta pasada; versión bumpeada a v9.21.16.
Pendiente (fuera de esta entrada):
- Movimiento manual de las 2 filas deprecadas al archivo (operador).
- vversions --sync para propagar v9.21.16 al resto de fundacionales.
---
Bootloader unificado como fuente única: SP:BOOTLOADER (01) pasa de instrucción única (notion-fetch) a bifurcación explícita por familia de agente — Familia MCP-Notion (Claude, Cursor, Devin, ChatGPT, Littlebird, Grok) vía notion-fetch; Familia GitHub-only (Perplexity, Mistral/Vibe) vía fetch raw sobre raw.githubusercontent.com, apuntando a Documentación/ACTIVE/System Prompt.md e Layer_1/data/V_ID_CENSUS_PRODUCTION.md — ambas URLs verificadas en vivo (200 OK) antes de escribir. Elimina la necesidad de un bootloader separado para Vibe/Mistral; una sola fuente de verdad para ambas familias.nnBug confirmado y parcheado en generate_census.py — auto_fix_orphans(): el regex CENSUS_SPEC = \\[.*?\\] (non-greedy, DOTALL) cortaba en el primer ] encontrado, no en el cierre real de la lista — reproducido en sandbox, causante de la corrupción de KERNEL:ARCHITECTURE-L4 documentada en el handoff previo (campo anidado lookup_ids disparaba el corte prematuro). Reemplazado por find_census_spec_end(), balanceo de profundidad de corchetes en vez de regex de patrón. Verificado en producción: vcensus post-parche → 240/240 IDs resueltos, 0 huérfanos, 0 sin link, KERNEL:ARCHITECTURE-L4 intacto.nnAuditoría completa de CENSUS_SPEC hardcodeado vs. export en vivo verificado: 65/225 entradas (~26%) con seccion desactualizada — no solo las 3 originalmente reportadas (MANUAL:SCRIPT-GLOSSARY-L1 y relacionadas). Concentrado en dos bloques: KERNEL completo desde PURPOSE en adelante (37 entradas, corrimiento de numeración por reestructuración del documento no reflejada en el script) y el bloque MANUAL:SCRIPT-GLOSSARY-* completo (8 entradas, reordenamiento de §22). Incluye bug adicional aislado: KERNEL:CV-GOLDEN-RULES-001 a 005 con seccion="11" sin sub-número (vs. -006 que sí tiene 11.6 correcto). Entregado script de reparación masiva (fix_seccion_drift.sh) para aplicar los 65 fixes de una sola pasada, con verificación exacta por ID+valor-viejo antes de escribir (no aplica si el archivo cambió desde la auditoría). Nota: el drift no afectó ningún export real porque el script prioriza detección de heading en vivo sobre el valor hardcodeado — el hardcoded solo actúa como fallback silencioso, por eso el drift pasó inadvertido hasta esta auditoría.nn---n
---
Tipo: [CODE] [DOC]
Alcance:
- verify_versions.py (local, scripts) — CHANGELOG_ARCHIVO excluido de escritura en --sync, tracking de solo lectura (SKIP)
- generate_census.py (local, scripts) — reparación de corrupción de sintaxis introducida por --auto-fix-orphans; alta correcta de 2 IDs huérfanos
Contexto: CHANGELOG_ARCHIVO fue movido bajo V | ARCHIVEROS (página-hija, no fila de data source) — no tiene ni puede tener propiedad Versión nativa. Se descartó convertirlo en fila de data source (riesgo estructural desproporcionado, sin precedente de diseño) a favor de excluirlo de la escritura de --sync, replicando el criterio ya usado para ARCHIVEROS (housekeeping ligero, sin elevarlo a fundacional pleno). Por separado, generate_census.py --auto-fix-orphans insertó las 2 entradas huérfanas en medio de la definición del diccionario KERNEL:ARCHITECTURE-L4, rompiendo la sintaxis del archivo — bug de la función auto_fix_orphans(), no error de operador.
Cambios:
- verify_versions.py: rama CHANGELOG_ARCHIVO en el loop de --sync ahora hace lectura sin intento de escritura; veredicto SKIP no bloquea all_pass.
- generate_census.py: sintaxis de KERNEL:ARCHITECTURE-L4 restaurada; alta de SP:BOOTLOADER-001 (01.1) y MANUAL:SCRIPT-GLOSSARY-CV-PREP (22.2) con sección/nombre verificados contra Notion en vivo.
IDs afectados: Ninguno nuevo a nivel Kernel/Manual/SP/Canon (los 2 IDs ya existían en Notion; esta entrada documenta su alta correcta en el Census local, no una creación de nodo).
Write-Back Verification: pendiente — se ejecuta tras la escritura, en esta misma sesión.
Pendiente (fuera de esta entrada):
- Drift de numeración local vs. live en MANUAL:SCRIPT-GLOSSARY-L1 (local=22.3, Notion=22.1) — sin tocar, señalado para revisión aparte.
- vversions --sync ya ejecutado y verificado [VEREDICTO FINAL] PASS en esta misma sesión.
---
Tipo: [DOC]
Alcance:
- System Prompt (SP:BOOTLOADER-001, 01.1 — nodo nuevo)
- Kernel (KERNEL:ARCHITECTURE-L4, 04.4 — párrafo Consumidor reescrito con matriz multi-agente)
- Manual (MANUAL:SKILL-GLOSSARY, 23 — nota breve añadida)
Contexto: Handoff de sesión previa (auditoría de 8 agentes/12 cuentas activas) confirmó que skills/triggers.json ahora incluye notion_id por skill junto a url, resuelto por fetch_notion_skill_library() en update_triggers_json.py. Faltaba la especificación formal de qué familia de agente resuelve por cuál campo. Decisión de diseño: fetch_priority vive como lógica fija en el Bootloader (SP:BOOTLOADER-001), no como campo repetido en las 28 filas del manifiesto — la matriz de capacidades es propiedad del agente, no del skill.
Cambios:
- SP:BOOTLOADER-001 (01.1) — nodo nuevo: regla de enrutamiento por familia de agente (MCP-Notion → notion_id; GitHub-only → url; Gemini fuera de flujo).
- KERNEL:ARCHITECTURE-L4 (04.4) — párrafo Consumidor reescrito: matriz de 8 agentes auditados, campo notion_id documentado, consumidor original de Claude preservado como sub-párrafo.
- MANUAL:SKILL-GLOSSARY (23) — nota de una línea señalando el respaldo multi-agente del glosario, con referencia cruzada.
IDs afectados: Ninguno — extensión de nodos existentes (SP:BOOTLOADER, KERNEL:ARCHITECTURE-L4, MANUAL:SKILL-GLOSSARY) más un ID nuevo de subsección (SP:BOOTLOADER-001) bajo el nodo padre ya censado. No dispara KERNEL:DOCUMENTATION-008 Regla 1 (alta de subsección bajo prefijo/nodo existente, no de documento nuevo) — pendiente registrar SP:BOOTLOADER-001 en próxima corrida de vcensus.
Write-Back Verification: los 3 nodos re-fetched post-escritura en esta misma sesión — 3/3 confirmados en posición correcta, sin mismatch.
Pendiente (fuera de esta entrada):
- vcensus para registrar SP:BOOTLOADER-001 como ID nuevo.
- vversions --sync para propagar v9.21.13 al resto de los fundacionales.
- Verificación de ALIASES:L4-VERSION-CONTROL (señalada como susceptible en el mapeo de Fase 1, no confirmada en este batch).
Tipo: [DOC]
Alcance:
- VANTAGE_SKILLS_COMPILED (Notion, pagina 3bf938befc4280ba80adf3d136cffc41) — 28 headings ### inyectados
Contexto: El compilado de Skills Library (generado por script local desde /skills/) carecia de IDs canonicos en su estructura Notion — cada skill viva como ## nombre-skill sin el heading ### SKILL:PREFIX-KEY — nombre-skill requerido por la Matriz Tipografica Congelada (KERNEL:DOCUMENTATION-001). Esta inyeccion no altera el contenido de las skills, solo anade el heading canonico como subseccion inmediata antes de cada ## existente.
Cambios:
- 28 headings ### anadidos en orden de aparicion: 4 CV (TAILLORED-RESUME, VANTAGE-CV-A/B, QA), 3 DOC (TRANSVERSAL-IMP/PROP, HYPERLINK-LOOP), 3 SESSION (HANDOFF, CLOSE, OPEN), 4 STYLE (CORPORATE, CRITICO, RETAIL, SOCIO), 6 SYNC (ASSETS, CENSUS-SPEC, SCRIPT-GLOSSARY/LIBRARY, SKILL-GLOSSARY/LIBRARY), 5 TIDY (HOUSEKEEPING-ARCHIVE/TRACKER, BUG-TASK, CHANGELOG, OPPORTUNITIES), 3 CORE (PROMPT-MASTER, CREATE-BUG-TASK, SKILL-UPDATER).
- Formato: ### SKILL:PREFIX-KEY — nombre-skill seguido de linea en blanco, luego ## nombre-skill original intacto.
IDs afectados: Ninguno (inyeccion de headings bajo IDs existentes — no dispara KERNEL:CENSUS-SYNC Regla 1).
Write-Back Verification: notion-fetch post-escritura — 28/28 headings confirmados en posicion correcta, sin mismatch.
Pendiente (fuera de esta entrada):
- vversions --sync para propagar v9.21.11 al resto de los fundacionales (Kernel, Manual, SP, Aliases, Brief, Census).
---
- Corrección: Typo en infer_layer L2 (backfill_class_a.py).
- Cierre: GAP-03/FX-1 en feed_processor.py (comentario stale).
- Refactor: _extract_text_prop a módulo en feed_processor.py.
- Nuevo guard contractual: KERNEL:GATE-DECISION-012 (Dedup_Flag/layer en existentes).
- Impacto: vantage-tidy-opportunities-tracker ahora excluye postulaciones vivas/terminales como candidatos a archivo.
---
Tipo: [DOC]
Alcance:
- Kernel (KERNEL:ARCHITECTURE-L4, 04.4 — párrafo de riesgo añadido)
- System Prompt (SP:BOOTLOADER, 01, paso 2 — sub-punto de cache-busting añadido)
Contexto: Durante diagnóstico de una discrepancia reportada por el operador (triggers.json actualizado en GitHub con campo url por skill, no reflejado en fetch de Claude), se confirmó empíricamente que web_fetch puede servir contenido cacheado de una URL ya fetcheada en la misma sesión — dos fetches separados por un commit real (5b7c48c) devolvieron contenido idéntico byte-a-byte. Se documenta el riesgo y se instruye reintento con cache-busting (?t={timestamp}) ante reporte de discrepancia del operador, antes de asumir fallo del repo o de su solución.
Cambios:
- KERNEL:ARCHITECTURE-L4 (04.4) — párrafo nuevo "Riesgo conocido — caché de fetch dentro de sesión".
- SP:BOOTLOADER (01, paso 2) — sub-punto nuevo: reintentar con cache-busting ante discrepancia reportada.
IDs afectados: Ninguno (extensión de nodos existentes — no dispara KERNEL:DOCUMENTATION-008 Regla 1).
Write-Back Verification: Kernel y System Prompt re-fetched post-escritura en esta misma sesión — 2/2 confirmados en posición correcta, sin mismatch.
Pendiente (fuera de esta entrada):
- vversions --sync para propagar v9.21.12 al resto de los fundacionales (arrastra también v9.21.8–v9.21.11, ya escritas pero no propagadas según sus propias entradas).
---
Tipo: [DOC]
Alcance:
- Kernel (KERNEL:CV-PIPELINE-003, 12.3 — nodo nuevo)
- Kernel (KERNEL:CV-PIPELINE, 12 — intro extendida)
- Kernel (KERNEL:CV-PIPELINE-001, 12.1 — Input extendido)
- Manual (MANUAL:SCRIPT-GLOSSARY-CV-PREP, 22.2 — nodo nuevo)
- Manual (MANUAL:WEEKLY-FLOW-003, 8.3 — CV-A extendido)
- Aliases (ALIASES:CV-PIPELINE, 07 — correccion de enunciado obsoleto)
Contexto: Brief del operador reportaba 3 scripts de Terminal (adapt_tracker_export.py, cv_a_batch_agent.py, cv_a_prep.py) que generan HANDOFF scaffolds en batch antes de CV-A, sin contraparte documental en ningun fundacional. Fase 1 (mapeo) y Fase 2 (DRY RUN) confirmaron 4 parches: alta de KERNEL:CV-PIPELINE-003 (12.3) con tabla-í¦¬ndice de 7 nodos (N1–N7) como version "dinamica" del diagrama de Devin, alta de MANUAL:SCRIPT-GLOSSARY-CV-PREP (22.2) ocupando hueco numerico reservado, extension de MANUAL:WEEKLY-FLOW-003 (8.3) y correccion de ALIASES:CV-PIPELINE (07) que contenia una contradiccion activa ("Sin alias de Terminal" pese a la existencia de la cadena de 3 scripts). Script Library delegada a vantage-sync-script-library (no escrita en este lote).
Cambios:
- KERNEL:CV-PIPELINE-003 (12.3) — nodo nuevo: "Preparacion Mecanica — Scaffold Batch", describe cadena de 3 scripts, clausula de invarianza (scaffold es metadata mecanica unica, no autoriza batch analisis) y tabla-í¦¬ndice de 7 nodos (N1–N7) con referencias cruzadas a MANUAL:SCRIPT-GLOSSARY-CV-PREP, KERNEL:CV-PIPELINE-001/002, KERNEL:TRIGGER-003 y KERNEL:SCHEMA-008.
- KERNEL:CV-PIPELINE (12) — intro extendida con puente narrativo apuntando a 12.3.
- KERNEL:CV-PIPELINE-001 (12.1) — Input extendido mencionando scaffold mecanico opcional.
- MANUAL:SCRIPT-GLOSSARY-CV-PREP (22.2) — nodo nuevo: 3 entradas con tablas de flags por script (adapt_tracker_export.py, cv_a_batch_agent.py, cv_a_prep.py).
- MANUAL:WEEKLY-FLOW-003 (8.3) — CV-A extendido con parrafo de ruta alterna (batch, opcional).
- ALIASES:CV-PIPELINE (07) — correccion de enunciado obsoleto: ahora documenta la preparacion mecanica opcional en Terminal con tabla de 3 filas (sin alias corto asignado).
IDs afectados: 2 altas — KERNEL:CV-PIPELINE-003 (12.3) y MANUAL:SCRIPT-GLOSSARY-CV-PREP (22.2) — dispara KERNEL:DOCUMENTATION-008 Regla 1 (CENSUS-SYNC).
Write-Back Verification: Kernel, Manual y Aliases re-fetched post-escritura — 3/3 confirmados en posicion correcta, sin mismatch.
Pendiente (fuera de esta entrada):
- vcensus para registrar los 2 IDs nuevos en el Census.
- vversions --sync para propagar v9.21.11 al resto de los fundacionales.
- Script Library (Notion) — alta de 3 filas delegada a vantage-sync-script-library.
---
Tipo: [FIX] [CODE]
Alcance:
- Código: Layer_3/scripts/layer_3_mail.py (SYNTHETIC_CT_PATTERNS, canonicalize_url())
- Bug Tracker (ticket 3be938be-fc42-8195-a602-d3a8c1bf0adf, Resuelto)
Contexto: 21 registros creados por L3 (Gmail→Groq) el 15-ago 17:09–17:16 con Status=Target, layer=L3, Fuente=Computrabajo/Indeed/LinkedIn, sin JD, fueron archivados automáticamente (Next_Action=Archivar) por Fase 2 de vl1 (layer_1_run.py::validate_url_pre_ingestion), sin pasar por Fase 3/4 (Gate_Decision y Score quedaron vacíos en 20/21 filas). Diagnóstico inicial (Claude, sesión previa) descartó reingesta duplicada (hash/URL únicos por fila) e identificó el mecanismo de escritura (Fase 2, rama AGREGADOR_STATUS_XXX vía HEAD 6s) como responsable directo — inicialmente atribuido a bloqueo anti-scraping de agregadores, mismo patrón que el ticket ya resuelto 3bb938be-fc42-813d-a253-ca2097f33957 (truncamiento de rich_text), pero confirmado como insuficiente para cubrir este caso: aquel ticket protegía registros YA verificados con JD poblado; estos 21 nacían sin JD en absoluto.
Sesión de diagnóstico con Devin (contrato de sesión separado) atravesó 3 iteraciones antes de aislar la causa raíz real:
1. Primera hipótesis (Devin) — B1 (validación inline en L3): experimento inicial probó páginas HOME de los agregadores (no las URLs reales del incidente), concluyendo erróneamente que Computrabajo/LinkedIn respondían 200 sin problema y que solo Indeed bloqueaba. Rechazado por el operador — metodológicamente inválido (Devin mismo señaló la limitación sin que le impidiera recomendar código).
1. Verificación cruzada (Claude) — invalidada también: intento de confirmar el hallazgo de Devin vía curl directo devolvió 403 en las URLs reales, pero se determinó post-hoc que ese 403 provenía del propio sandbox de Claude (x-deny-reason: host_not_allowed — computrabajo.com/indeed.com no están en la whitelist de red del entorno), no del servidor real. Corrección reportada explícitamente al operador y a Devin en la misma sesión.
1. Segunda hipótesis (Devin) — causa raíz real confirmada: re-ejecución del experimento contra las 21 URLs reales del incidente (provistas explícitamente por el operador) reveló 404 real (no 403 anti-bot) en las 18 URLs de Computrabajo, con HTML de "página no encontrada" — nunca existieron como recursos reales. El patrón de esas URLs ([rol]-[marca]-2024, ej. visual-merchandiser-hm-2024) coincide exactamente con un patrón de URLs sintéticas ya documentado en un incidente histórico no relacionado (Changelog, bypass ciego de agregadores, ~19 filas con 13 URLs sintéticas del mismo patrón). Causa raíz aislada: Groq (motor de extracción de L3) alucina URLs de Computrabajo con este patrón; el código YA contenía un mecanismo de detección (SYNTHETIC_CT_PATTERNS, 4 regexes, comentario explícito "URLs sintéticas de Computrabajo (alucinadas por Groq)") y el prompt de Groq prohíbe explícitamente "URL fabricada con año" (línea 213), pero ninguno de los 4 patrones existentes cubría la forma [rol]-[marca]-2024.
Verificación independiente de Claude contra el fix propuesto por Devin: primer intento de cierre reportado por Devin ("implementado y verificado") no reflejaba cambios reales en el repo remoto (git pull sin diffs) — Devin no había ejecutado vgit/push, el commit vivía solo en su entorno local. Operador proveyó el archivo layer_3_mail.py directamente vía upload; Claude confirmó el fix presente en el archivo local y lo validó de forma independiente (script Python propio, no reutilizando el reporte de Devin) contra las 21 URLs reales del incidente: 18/18 URLs de Computrabajo correctamente detectadas como SYNTHETIC_AGGREGATOR_URL, 0 falsos positivos en las 2 URLs de Indeed/LinkedIn (fuera del alcance del patrón), incluyendo los 2 casos con acentos/URL-encoding (galer%C3%ADas, auerrer%C3%A1) vía unquote().
Cambios:
- layer_3_mail.py::SYNTHETIC_CT_PATTERNS — 5to patrón añadido: re.compile(r'/jobs/[^/]+-\d{4}$'), cubre el patrón [rol]-[marca]-2024 no capturado por los 4 patrones previos (numeric ID corto/largo, year chain, IDs plantilla).
- layer_3_mail.py::canonicalize_url() — decodificación vía unquote() añadida antes del matching de patrones, para detectar variantes con acentos/URL-encoding; la URL canónica retornada permanece intacta (sin alterar el valor guardado en Notion).
- Bug Tracker 3be938be-fc42-8195-a602-d3a8c1bf0adf — creado, diagnosticado en 3 iteraciones, resuelto con Solución documentada.
Validación: Script de verificación independiente de Claude (no el reporte de Devin) contra las 21 URLs reales del incidente — 18/18 Computrabajo detectadas, 0 falsos positivos, casos de encoding cubiertos.
IDs afectados: Ninguno (fix de código, sin alta/baja de ID canónico — no dispara KERNEL:CENSUS-SYNC Regla 1).
Write-Back Verification: Bug Tracker 3be938be-fc42-8195-a602-d3a8c1bf0adf actualizado (Status=Resuelto) y re-fetched — confirmado. Fix verificado contra archivo local subido por el operador (no contra repo remoto — ver Pendiente).
Lección de proceso (aplicable a futuras sesiones con Devin u otros agentes): nunca aceptar un reporte de "implementado y verificado" al valor nominal sin re-fetch/re-verificación independiente contra la fuente real — en esta sesión ocurrió dos veces en direcciones opuestas: (1) Devin reportó éxito sin push real, detectado por git pull sin diffs; (2) Claude mismo reportó una "contradicción empírica" que resultó ser una falsa alarma de su propio sandbox de red, corregida solo tras inspeccionar los headers de respuesta en vez de confiar en el status code aislado.
Pendiente (fuera de esta entrada):
- Commit con el fix aún no pusheado a GitHub por Devin (vgit no ejecutado) — el fix existe en archivo local confirmado por el operador, pero no está activo en el repo remoto ni en producción hasta que se ejecute el push.
- Corrección manual/batch de las 21 filas ya dañadas en Notion (Status=Expirada, Next_Action=Archivar incorrecto) — operación de datos separada, requiere DRY RUN + APROBAR_WRITE aparte.
- Suite de tests de regresión (Layer_3/tests/test_layer_3_mail.py, reportada por Devin) — no confirmada presente en el archivo local subido; verificar tras el push.
- vversions --sync para propagar v9.21.10 al resto de los fundacionales.
---
> El histórico completo del CHANGELOG lo podrás encontrar en ARCHIVO CHANGELOG, en esta pagina de consulta continua solo encontrarás las últimas diez entradas para garantizar la operación y referencia del sistema.
