# V | ALIASES

# V | ALIASES
## 01 ALIASES:SESSION-CYCLE
Session Cycle
| Alias | Qué hace | Procedimiento interno |
| --- | --- | --- |
| start | Arranca el sistema al inicio de cada sesión: activa el entorno, carga variables y corre el chequeo de salud. | Activa .venv, exporta config/layer_1.env, y ejecuta health_check.py, que revisa en orden versión, entorno, git, conectividad a Notion, sync documental y antigüedad de índices — auto-sincroniza el Entity Index si pasó más de 24h. |
| vversions –bootstrap | Genera el paquete de contexto de apertura de sesión: última fila del Ledger, última entrada del Changelog, tickets críticos pendientes. | Lee pages.retrieve sobre la página del Session Ledger y el Changelog y arma el bloque [DUMP INICIO SESIÓN VANTAGE] — no escribe nada. |
| vversions –sync | Propaga la versión ya escrita en el Changelog hacia los 6 documentos restantes. | Único flag con escritura: lee la versión target del Changelog y ejecuta 6 pages.patch secuenciales sobre la propiedad Versión — housekeeping, exento de APROBAR_WRITE. |
## 02 ALIASES:L0-RUNTIME
L0 · VANTAGE Runtime
| Alias | Qué hace | Procedimiento interno |
| --- | --- | --- |
| vload | Motor base del Lazy Loader — consulta rutas específicas del Kernel sin fetch completo. | Activa .venv y corre lazy_loader.py –page {ID} –route {ruta}; parsea bloques hijos vía API y devuelve solo el payload pedido (~150 tokens). |
| vtrig / vgolden / vcheat / vscope / vdataflow / vrouting | Atajos directos a secciones específicas del Kernel (Triggers, Golden Rules, Cheat Sheet, Scope, Data Flow, Routing) sin escribir la ruta a mano cada vez. | Cada uno es vload con –page y –route ya fijos al ID de esa sección. |
| vstatus | Muestra el estado del Runtime: cuántas entidades tiene indexadas y qué tan viejo está el índice. | Corre vantage.py status — lectura pura contra entity_index_v2.json. |
| vsync | Regenera el índice de entidades del Runtime desde Notion. | Corre vantage.py sync — reconstruye entity_index_v2.json, graph_v2.json, backlinks_v2.json. |
| vask | Hace una pregunta en lenguaje natural al Runtime sobre el estado del Tracker. | Corre vantage.py ask “…” — resuelve contra el índice ya cargado. |
| vresolve | Resuelve una entidad específica (ID o nombre) a su ficha completa. | Corre vantage.py resolve — 4 pasos: lookup en índice, mapeo a data source, query a Notion, validación. |
| vcontext | Trae contexto extendido de una entidad (relaciones, backlinks). | Corre vantage.py context sobre graph_v2.json y backlinks_v2.json. |
| vquery | Corre una consulta estructurada contra el índice. | Corre vantage.py query — filtra entity_index_v2.json por los parámetros dados. |
| vversions (sin flag) | Punto de entrada al motor de verificación de versión y observabilidad de librerías de activos — requiere flag explícito (–bootstrap/–sync, ver familia 1; –scripts/–skills, ver MANUAL:RUNTIME-002). | — |
| vcensus | Regenera el V-ID-CENSUS y reporta IDs huérfanos. | Corre generate_census.py — resuelve cada ID contra CENSUS_SPEC, detecta huérfanos no listados, y genera deeplink de bloque exacto vía API para cada uno. |
| vlength | Verifica integridad de longitud de los 9 documentos fundacionales contra el baseline. | Corre verify_versions.py --length — genera length_baseline.json si no existe. |
| vupdatebaseline | Sobrescribe el baseline de longitud con las métricas del conteo actual. | Corre verify_versions.py --length --update-baseline (requiere --length previo; veredicto PASS o confirmación del operador). |
| vunlock / vlock | Quita/restaura el permiso de escritura sobre los .md de Documentación/ACTIVE/. | chmod u+w / chmod 444 directo sobre los 9 archivos fundacionales — housekeeping puro, no invoca Python. |
| vdigest | Descarga el digest completo del repo VANTAGE (vía gitingest.com) a un .txt local, para pegar contexto en agentes sin acceso a GitHub/Notion (Perplexity, Mistral). | Corre get_vantage_digest.sh — curl a gitingest.com/raw/mauriciomeyran/VANTAGE, guarda en VANTAGE_digest.txt (o el path dado como argumento). |
| vsource | Recarga la configuración de shell tras editar .zshrc, sin abrir una terminal nueva. | source ~/.zshrc — housekeeping puro, no toca Notion ni el pipeline. |
## 03 ALIASES:L1L2-DISCOVERY
L1/L2 · Discovery (Lunes)
| Alias | Qué hace | Procedimiento interno |
| --- | --- | --- |
| vl1 | Corre el pipeline principal de Active Recon — procesa el JSON consolidado del día y lo escribe en el Tracker. | Invoca layer_1_pipeline.sh, que activa .venv y dispara feed_processor.py: normaliza campos, aplica dedup cross-layer, presenta DRY RUN antes de escribir. El paso de URL Gate dentro de layer_1_run.py (ejecutado por vl1, Fase 2) valida activamente URLs de agregadores vía HEAD con timeout corto, en vez de aceptarlas por dominio. |
| vl1status / vl1analytics / vl1batch / vl1recovery / vl1profile / vl1feed / vl1backfill | Atajos de un solo token a cada subcomando de vl1 (ver Manual 09.2 para el detalle de cada uno). | Cada uno equivale a vl1 — mismo contrato, solo evita el espacio. |
| vl1app | Abre la app empaquetada de Layer 1 desde Finder/Spotlight en vez de Terminal. | open /Applications/Layer 1. |
| vassemble | Genera los 7 prompts semanales (.md) por motor desde la PROMPT LIBRARY, con fecha del día ya sustituida. | Corre weekly_prompt_assembler.py: fetch vía notion_utils.notion_get (cache/throttling/retry ya existentes) de Prompt A + Wrapper por motor + Prompt E, sustitución de [YYYY-MM-DD], concatenación Prompt A + Wrapper por orden fijo, escritura de Prompt_[Motor][Fecha].md y Prompt_E_Consolidation[Fecha].md en Layer_1/data/Prompts/. |
## 04 ALIASES:L3-PASSIVE-INTAKE
L3 · Passive Intake
| Alias | Qué hace | Procedimiento interno |
| --- | --- | --- |
| vl3 | Procesa manualmente el backlog de Gmail (.Jobs) si el ciclo automático no corrió. | Invoca layer_3_mail.sh — lee vía IMAP, extrae vacantes con Groq (máx. 10 correos/run), escribe Class A en el Tracker. |
| vl3app | Abre la app empaquetada de Layer 3. | open /Applications/Layer 2 (nombre de carpeta heredado, corresponde a L3). |
## 05 ALIASES:L4-VERSION-CONTROL
L4 · Version Control & Documentación
| Alias | Qué hace | Procedimiento interno |
| --- | --- | --- |
| vgit | Fuerza un sync inmediato del repo git fuera de su horario automático. | Invoca git_sync_wrapper.sh — commit con timestamp + push a origin/main si hay cambios sin commitear. |
| vsync-doc | Invocación directa del motor de sync documental (uso interno/depuración). | Corre vsync_doc.py sin el wrapper de comandos — requiere pasar flags manualmente. |
| vdoc | Sincroniza los 6 documentos fundacionales desde Notion hacia el disco local (Read Only): Kernel, System Prompt, Career Canon, Manual, Aliases, Change Log. | Corre vdoc.py (wrapper de comandos) → invoca vsync_doc.py con la dirección y documento pedidos (notion/auto (equivalente), dry (previsualización limitada)). |
| vhyperlinks | Aplica hipervínculos cross-reference DIRECTO sobre bloques de Notion (PATCH puntual, preserva block-ID), a partir de cada mención de un ID canónico (PREFIX:KEY). apply_hyperlinks.py (variante anterior, sobre .md locales) queda DEPRECATED. | Corre apply_hyperlinks_notion.py --all. Sin --apply es dry-run (reporta cuántos links propuestos por documento, no escribe). Agregar --apply para escribir de verdad. |
| cleancaches | Limpia cachés regenerables de apps Mac (Chrome/Safari/Firefox/Edge, WhatsApp/WeChat/Telegram, ChatGPT/Ollama/LM Studio, npm, Cursor) sin tocar sesiones activas. | Corre clean_caches.py. Wrapper Raycast equivalente: clean-caches-raycast.sh (🧹 "Limpiar Cachés de Apps"). |
| vprint | Lista vacantes con Gate_Decision = CREATE (conteo + IDs/URLs) vía query directo a Notion. | Corre vprint.py, cargando .env inline (vprint.sh en disco es un wrapper alterno no usado por este alias). |
| vtriggers | Mantiene el manifiesto SSOT de skills (skills/triggers.json) que consume el Bootloader para lazy-load por trigger. | Corre update_triggers_json.py — escanea /skills/, valida SKILL.md por entrada, detecta huérfanos (reporta, no borra), actualiza last_modified, y ejecuta git add+commit+push automático sobre triggers.json. |
|  | vserial | Genera un nuevo serial de handoff VANTAGE (formato HO-######) y lo imprime en terminal. |
| vsum | Resume transcripts de sesiones |  |
---
| Flag / Comando | Modo | Descripción | Efecto Secundario | Requisitos / Condición |
| --- | --- | --- | --- | --- |
| --length | Read-only | Verifica el conteo de líneas de texto extraíble vs. length_baseline.json. | Genera length_baseline.json si no existe. | Ninguno. |
| --update-baseline | Write | Sobrescribe el baseline con las métricas del conteo actual. | Actualiza timestamp captured_at. | Requiere --length. Veredicto PASS o confirmación del operador. |
## 06 ALIASES:DASHBOARD
Dashboard (Martes — Recuperación)
| Alias | Qué hace | Procedimiento interno |
| --- | --- | --- |
| vd | Abre el Dashboard de recuperación de vacantes bloqueadas. | Invoca dashboard_start.sh — arranca Flask en :8000, corre smoke test, abre dashboard.html en el navegador. |
| vdapp | Abre la app empaquetada del Dashboard. | open /Applications/Dashboard. |
## 07 ALIASES:CV-PIPELINE
CV Pipeline (Miércoles)
CV-A, CV-B y QA se disparan directamente en el chat de Claude — sin alias propio (ver Manual 08.3). La preparación mecánica previa (scaffold batch, opcional) sí corre en Terminal:
| Alias | Qué hace | Procedimiento interno |
| --- | --- | --- |
| (sin alias corto asignado) | Normaliza el export de Notion para el batch de CV-A. | python3 adapt_tracker_export.py --in <export.csv> |
| (sin alias corto asignado) | Genera scaffolds HANDOFF en paralelo para vacantes Optimizar. | python3 cv_a_batch_agent.py --csv tracker_adapted.csv |
| (sin alias corto asignado) | Prepara un scaffold individual (cache, Hard Block, idioma). | python3 cv_a_prep.py --url <URL> |
| Ver MANUAL:SCRIPT-GLOSSARY-CV-PREP para el detalle completo de flags. |  |  |
## 08 ALIASES:DEDUP
Dedup & Oportunidades
| Alias | Qué hace | Procedimiento interno |
| --- | --- | --- |
| vdedup | Consolida entradas duplicadas detectadas en el Tracker. | Corre consolidate_duplicates.py sobre la clave compuesta brand+title+location. |
| vopport | Limpia duplicados específicamente en oportunidades ya calificadas. | Corre dedup_opportunities.py. |
| dedup_audit.sh <em>(sin alias corto en .zshrc — se invoca por ruta)</em> | Auditoría manual semanal recomendada de duplicados en Oportunidades — mismo motor que vopport, pensado como recordatorio de cadencia fija. | ./scripts/dedup_audit.sh → dedup_opportunities.py sin flags. Soporta también --clear <page_id> (falsos positivos) y layer_1_run.py --dedup-audit (integración automática Fase 6, +1-2 min al pipeline). |
| Figma Sync (plugin CV, 04-Vantage_CV/Figma Sync/) no tiene alias de Terminal propio — se opera desde Figma Desktop, ver Manual 08.3. |  |  |
