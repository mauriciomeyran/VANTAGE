# V | CHANGELOG

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
Tipo: [DOC]
Alcance:
- Skill Library (Notion) — alta de fila nueva
Contexto: Auditoría completa solicitada por el operador — cruce de las 28 skills de skills/triggers.json contra las filas existentes en Skill Library. 27/28 presentes; único gap: vantage-sync-skill-glossary (sincroniza Manual §23, distinta de vantage-sync-script-glossary que sincroniza §22 y sí existía). Verificadas también las dos filas deprecadas (extract-learnings.skill, vantage-audit-navigation-brief.skill) — ambas correctamente marcadas Estado=Deprecado / Acción=Archivar, no son gaps. Sin duplicados detectados entre las 29 filas resultantes.
Cambios:
- Skill Library — fila nueva: vantage-sync-skill-glossary (Capa L4, Estado Activo, Acción Keep, Ruta /skills/vantage-sync-skill-glossary/SKILL.md).
IDs afectados: Ninguno (fila de tabla existente — no dispara KERNEL:CENSUS-SYNC Regla 1).
Write-Back Verification: página creada y confirmada en respuesta de notion-create-pages (id 3be938be-fc42-81b6-9f5f-d64272bdd6c9).
Pendiente (fuera de esta entrada):
- vversions --sync para propagar v9.21.10 (arrastra v9.21.7–v9.21.9 también pendientes) al resto de los fundacionales.
---
Tipo: [DOC]
Alcance:
- Kernel (KERNEL:DOCUMENTATION-010, 03.10 — nodo nuevo: Timestamp Obligatorio en Changelog)
- System Prompt (SP:CONSISTENCY, 10 — regla 3 nueva)
Contexto: El operador solicitó que, a partir de ahora, cada entrada nueva del Change Log declare fecha y hora local (CDMX) en el título. Como Claude no tiene reloj de sistema fiable dentro de la sesión, se fijó como regla que el operador provea el timestamp explícitamente al autorizar la escritura; si no lo hace, Claude pregunta antes de escribir — nunca infiere ni aproxima. Formato adoptado: {Mes} {DD}, {AA} {HH.MM} (ej. "Ago 16, 26 06.22"), confirmado por el operador en esta misma entrada.
Cambios:
- KERNEL:DOCUMENTATION-010 (03.10) — nodo nuevo "Timestamp Obligatorio en Changelog": formato, fuente del dato (operador, no Claude), protocolo ante ausencia (preguntar, no inferir).
- SP:CONSISTENCY (10) — regla 3 nueva, referencia cruzada al nodo Kernel.
- Esta misma entrada (v9.21.9) es la primera en aplicar el formato de título con timestamp.
IDs afectados: Ninguno (contenido nuevo bajo IDs existentes — no dispara KERNEL:CENSUS-SYNC Regla 1).
Write-Back Verification: Kernel y System Prompt re-fetched post-escritura — 2/2 confirmados en posición correcta, sin mismatch.
Pendiente (fuera de esta entrada):
- vversions --sync para propagar v9.21.9 al resto de los fundacionales.
---
Tipo: [DOC]
Alcance:
- Kernel (KERNEL:ARCHITECTURE-L4, 04.4 — párrafo Consumidor corregido)
- Manual (MANUAL:WEEKLY-FLOW-001, 8.1 — línea final corregida)
- System Prompt (SP:BOOTLOADER, 01) y (SP:CONTEXT-INFRASTRUCTURE, 04) — ya reflejaban el mecanismo correcto al momento de esta entrada (aplicado en paralelo a esta sesión, sin intervención de escritura de Claude en este batch)
Contexto: v9.21.7 documentó el consumo del manifiesto de skills exclusivamente vía web_fetch a raw.githubusercontent.com. El operador reportó una restricción estructural no contemplada: web_fetch de Claude sobre raw.githubusercontent.com está bloqueado salvo que la URL ya haya aparecido en la sesión (vía web_search/web_fetch previo) — condición que no se cumple para los paths individuales de SKILL.md construidos dinámicamente desde el manifiesto. Corrección: git clone --depth 1 (bash_tool, github.com whitelisted) pasa a ser la vía primaria y estable para leer el contenido de cada skill; web_fetch queda como fallback solo si el clone falla, y se mantiene como vía única para el fetch inicial del manifiesto (triggers.json), cuya URL sí proviene de SP:BOOTLOADER ya cargado en la sesión. Al escribir, se detectó que SP:BOOTLOADER y SP:CONTEXT-INFRASTRUCTURE ya reflejaban el mecanismo corregido en Notion — no hubo mismatch de old_str porque el contenido vivo ya coincidía con el texto propuesto por el operador.
Cambios:
- KERNEL:ARCHITECTURE-L4 (04.4) — párrafo Consumidor: el manifiesto se recupera vía web_fetch (fetch inicial, URL ya en sesión); el contenido de cada skill se lee vía git clone --depth 1 + lectura local, vía primaria y estable dado el bloqueo estructural de web_fetch sobre raw.githubusercontent.com para URLs no vistas previamente; web_fetch queda como fallback.
- MANUAL:WEEKLY-FLOW-001 (8.1) — línea de cierre del párrafo "Extensión reciente" corregida para reflejar el doble mecanismo (manifiesto vía web_fetch, contenido de skill vía git clone local).
IDs afectados: Ninguno (todas las ediciones reutilizan IDs existentes — no dispara KERNEL:CENSUS-SYNC Regla 1).
Write-Back Verification: KERNEL y MANUAL re-fetched post-escritura — 2/2 confirmados en posición correcta, sin mismatch. SP:BOOTLOADER y SP:CONTEXT-INFRASTRUCTURE verificados en vivo ya conformes, sin escritura requerida en este batch.
Pendiente (fuera de esta entrada):
- vversions --sync para propagar v9.21.8 al resto de los fundacionales.
---
Tipo: [DOC]
Alcance:
- Kernel (KERNEL:ARCHITECTURE-L4, 04.4 — sección Skills Distribution reescrita)
- System Prompt (SP:BOOTLOADER, 01 — paso 2 ampliado + paso 2.1 nuevo)
- Manual (MANUAL:WEEKLY-FLOW-001, 8.1 — párrafo "Extensión reciente — Skills Distribution" reescrito)
- Aliases (ALIASES:L4-VERSION-CONTROL, 05 — fila nueva: vtriggers)
Contexto: Sesión previa implementó update_triggers_json.py (alias vtriggers) generando skills/triggers.json como manifiesto SSOT de skills, con auto-push a git — reemplazando de facto el mecanismo documentado (GitHub Pages + MCP filesystem local para Claude Desktop + Devin vía devin mcp add), que nunca llegó a operar (GitHub Pages no puede responder el handshake JSON-RPC que requiere MCP). Mapeo de documentación transversal (esta sesión) confirmó 4 nodos con referencia directa al mecanismo obsoleto — 3 no contemplados originalmente en el handoff de la sesión anterior (MANUAL:WEEKLY-FLOW-001 y la fila faltante en ALIASES). Confirmado por el operador: el manifiesto se consume vía web_fetch directo a raw.githubusercontent.com (no MCP), con lazy-load por trigger en cada turno — nunca carga masiva de las 28 skills en boot. Devin no consume el manifiesto — solo Claude y Mistral.
Cambios:
- KERNEL:ARCHITECTURE-L4 (04.4) — párrafo "Skills Distribution — Single Source of Truth" reescrito: describe triggers.json (estructura, generador, validaciones, auto-push), consumidor único (Claude vía web_fetch), y descontinuación explícita de GitHub Pages/index.json/Devin MCP.
- SP:BOOTLOADER (01) — paso 2 ampliado con tercer fetch (SKILLS MANIFEST vía web_fetch, no bloqueante para el Bootstrap); paso 2.1 nuevo: lazy-load por trigger en cada turno.
- MANUAL:WEEKLY-FLOW-001 (8.1, "¿Qué es vgit?") — párrafo "Extensión reciente — Skills Distribution" reescrito: reemplaza referencia a Claude Desktop MCP filesystem + Devin/GitHub Pages por vtriggers + web_fetch.
- ALIASES:L4-VERSION-CONTROL (05) — fila nueva: vtriggers (update_triggers_json.py).
IDs afectados: Ninguno (todas las ediciones reutilizan IDs existentes o son alta de fila dentro de tabla ya censada — no dispara KERNEL:CENSUS-SYNC Regla 1).
Write-Back Verification: los 4 nodos re-fetched post-escritura — 4/4 confirmados en posición correcta, sin mismatch.
Discrepancia detectada (no remediada en esta entrada): la propiedad Versión de esta página permanecía en v9.21.5 pese al toggle v9.21.6 ya presente (marcado [COMPRIMIDO], pendiente de expandir) — drift pre-existente a esta sesión, reportado aquí conforme SP:CONSISTENCY; no bloqueó esta escritura.
Pendiente (fuera de esta entrada):
- Expansión de la entrada v9.21.6 [COMPRIMIDO] (Fase G1 saneamiento v3), aún no resuelta.
- vversions --sync para propagar v9.21.7 al resto de los fundacionales.
---
Tipo: [DOC]
T2 (Manual P2a/b/c: correos 5→10 + hallazgo GROQ + nota §22.1 resueltos) · T3 (Kernel §04.4: vsync_doc_fast.py deprecado + conteo skills a Opción B SSOT vivo, reintento tras fallo silencioso 1er intento) · T4 (Kernel §03.5: anuncio vantage-housekeeping-archive) · T5 (Manual §23.2: fila glosario housekeeping-archive) · T6 (Archivo Changelog: dedupe extendido v9.14.2×2+v9.14.3×1 → 1 canonical + 2 notas [DEDUPE v9.21.x], drift de versión registrado para T20). IDs afectados: Ninguno. Pendiente: G2 (Tareas 7–10) sin iniciar; vversions --sync para propagar; SYNC PENDIENTE.
---
Tipo: [AUDIT]
Alcance: Change Log (esta entrada); Script Library (hallazgo, sin escritura); GitHub issue #4 (comentado); index.html raíz (restaurado en repo).
Contexto: Cierre de los 5 pendientes operativos listados tras v9.21.4.
Cambios:
- T9 pasada 2 (Script Library) — marcada obsoleta. Verificación en vivo confirmó que la fila duplicada de git_sync.py ya fue diagnosticada y marcada correctamente (Estado=Deprecado, Acción=Archivar, Descripción explícita) en el batch M1 — el pendiente en v9.21.3 estaba desactualizado respecto al estado real de Notion. Sin escritura requerida.
- Duplicado git_sync.py — confirmado sin acción pendiente (ver punto anterior). Fila canónica (L4, Estado=Activo) intacta.
- GitHub issue #4 — comentado confirmando que auto_archive.py permanece deprecado en Archive/Legacy_Scripts/ como referencia histórica, sin eliminación (decisión del operador 2026-08-01, KERNEL:GATE-DECISION-007). Referencia: https://github.com/mauriciomeyran/VANTAGE/issues/4#issuecomment-5302203383
- index.html raíz — restaurado desde commit 7e92dcd (contenido: landing page GitHub Pages con documentación de skills MCP), aplicado en commit 2a3c7a1 sobre main. Decisión del operador tras confirmar propósito y ausencia de dependencias en el pipeline.
- vversions --sync (v9.21.4) — ya ejecutado y verificado [VEREDICTO FINAL] PASS en sesión previa.
IDs afectados: Ninguno (sin alta/baja de ID canónico — no dispara CENSUS-SYNC Regla 1).
Write-Back Verification: re-fetch de esta entrada tras la escritura.
Pendiente (fuera de esta entrada): Ninguno — ciclo de saneamiento v9.21.x cerrado en su totalidad.
---
Tipo: [AUDIT]
Alcance: Change Log (esta entrada); GitHub issues #8, #9 (comentados y cerrados).
Contexto: Cierre de los issues #8 y #9 dejados abiertos en v9.21.3. Se intentó remediar el incumplimiento del contrato PR-obligatorio (commits d3ba880 y 160337c fueron directo a main) creando branches retroactivas fix/d2-rework-archive-queue y fix/d5-real-descripcion-detector — descartado tras confirmar limitación estructural de Git: una branch creada desde main no puede mostrar diff contra main (GraphQL: "No commits between main and fix/..."). Se optó por registro de auditoría en vez de reescritura de main vía revert/reapply (evita alterar la secuencia limpia de main).
Cambios:
- Branches fix/d2-rework-archive-queue y fix/d5-real-descripcion-detector — creadas, confirmado sin diff, eliminadas de origin.
- GitHub issue #8 — comentario con referencia a Changelog v9.21.3, cerrado.
- GitHub issue #9 — comentario con referencia a Changelog v9.21.3, cerrado.
IDs afectados: Ninguno (sin alta/baja de ID canónico — no dispara CENSUS-SYNC Regla 1).
Write-Back Verification: re-fetch de esta entrada tras la escritura.
Pendiente (fuera de esta entrada): pasada 2 de T9 (Script Library, tras merge de #9 — issue cerrado, verificar si pasada 2 sigue aplicando o queda obsoleta); patch manual de la fila duplicada git_sync.py; aviso en GitHub Issue #4 (auto_archive.py); vversions --sync para propagar v9.21.4 al resto de los fundacionales (arrastra también v9.21.3 aún no propagada).
---
---
> El histórico completo del CHANGELOG lo podrás encontrar en ARCHIVO CHANGELOG, en esta pagina de consulta continua solo encontrarás las últimas diez entradas para garantizar la operación y referencia del sistema.
