# V | ALIASES

## TABLE OF CONTENT
```plain text
1. Session Cycle

2. L0 · VANTAGE Runtime

3. L1/L2 · Discovery (Lunes)

4. L3 · Passive Intake

5. L4 · Version Control & Documentación

6. Dashboard (Martes — Recuperación)

7. CV Pipeline (Miércoles)

8. Dedup & Oportunidades
```
# 1 — Session Cycle
| Alias | Qué hace | Procedimiento interno |
| --- | --- | --- |
| start | Arranca el sistema al inicio de cada sesión: activa el entorno, carga variables y corre el chequeo de salud. | Activa .venv, exporta config/layer_1.env, y ejecuta health_check.py, que revisa en orden versión, entorno, git, conectividad a Notion, sync documental y antigüedad de índices — auto-sincroniza el Entity Index si pasó más de 24h. |
| vversions --bootstrap | Genera el paquete de contexto de apertura de sesión: última fila del Ledger, última entrada del Changelog, tickets críticos pendientes. | Lee pages.retrieve sobre la página del Session Ledger y el Changelog y arma el bloque [DUMP INICIO SESIÓN VANTAGE] — no escribe nada. |
| vversions --check | Confirma que los 7 documentos fundacionales están en la misma versión antes de trabajar. | Itera los 7 page_id fijos y lee solo la propiedad Versión de cada uno vía pages.retrieve — no toca el contenido. |
| vversions --sync | Propaga la versión ya escrita en el Changelog hacia los 6 documentos restantes. | Único flag con escritura: lee la versión target del Changelog y ejecuta 6 pages.patch secuenciales sobre la propiedad Versión — housekeeping, exento de APROBAR_WRITE. |
# 2 — L0 · VANTAGE Runtime
| Alias | Qué hace | Procedimiento interno |
| --- | --- | --- |
| vload | Motor base del Lazy Loader — consulta rutas específicas del Kernel sin fetch completo. | Activa .venv y corre lazy_loader.py --page {ID} --route {ruta}; parsea bloques hijos vía API y devuelve solo el payload pedido (~150 tokens). |
| vtrig / vgolden / vcheat / vscope / vdataflow / vrouting | Atajos directos a secciones específicas del Kernel (Triggers, Golden Rules, Cheat Sheet, Scope, Data Flow, Routing) sin escribir la ruta a mano cada vez. | Cada uno es vload con --page y --route ya fijos al ID de esa sección. |
| vstatus | Muestra el estado del Runtime: cuántas entidades tiene indexadas y qué tan viejo está el índice. | Corre vantage.py status — lectura pura contra entity_index_v2.json. |
| vsync | Regenera el índice de entidades del Runtime desde Notion. | Corre vantage.py sync — reconstruye entity_index_v2.json, graph_v2.json, backlinks_v2.json. |
| vask | Hace una pregunta en lenguaje natural al Runtime sobre el estado del Tracker. | Corre vantage.py ask "..." — resuelve contra el índice ya cargado. |
| vresolve | Resuelve una entidad específica (ID o nombre) a su ficha completa. | Corre vantage.py resolve — 4 pasos: lookup en índice, mapeo a data source, query a Notion, validación. |
| vcontext | Trae contexto extendido de una entidad (relaciones, backlinks). | Corre vantage.py context sobre graph_v2.json y backlinks_v2.json. |
| vquery | Corre una consulta estructurada contra el índice. | Corre vantage.py query — filtra entity_index_v2.json por los parámetros dados. |
| vversions (sin flag) | Punto de entrada al motor de verificación de versión — requiere flag explícito (--bootstrap/--check/--sync, ver familia 1). | — |
| vcensus | Regenera el V-ID-CENSUS y reporta IDs huérfanos. | Corre generate_census.py — resuelve cada ID contra CENSUS_SPEC, detecta huérfanos no listados, y genera deeplink de bloque exacto vía API para cada uno. |
| vsource | Recarga la configuración de shell tras editar .zshrc, sin abrir una terminal nueva. | source ~/.zshrc — housekeeping puro, no toca Notion ni el pipeline. |
# 3 — L1/L2 · Discovery (Lunes)
| Alias | Qué hace | Procedimiento interno |
| --- | --- | --- |
| vl1 | Corre el pipeline principal de Active Recon — procesa el JSON consolidado del día y lo escribe en el Tracker. | Invoca layer_1_pipeline.sh, que activa .venv y dispara feed_processor.py: normaliza campos, aplica dedup cross-layer, presenta DRY RUN antes de escribir. |
| vl1status / vl1analytics / vl1batch / vl1recovery / vl1profile / vl1feed / vl1backfill | Atajos de un solo token a cada subcomando de vl1 (ver Manual §9.2 para el detalle de cada uno). | Cada uno equivale a vl1 <subcomando> — mismo contrato, solo evita el espacio. |
| vl1app | Abre la app empaquetada de Layer 1 desde Finder/Spotlight en vez de Terminal. | open /Applications/Layer 1. |
# 4 — L3 · Passive Intake
| Alias | Qué hace | Procedimiento interno |
| --- | --- | --- |
| vl3 | Procesa manualmente el backlog de Gmail (.Jobs) si el ciclo automático no corrió. | Invoca layer_3_mail.sh — lee vía IMAP, extrae vacantes con Groq (máx. 5 correos/run), escribe Class A en el Tracker. |
| vl3app | Abre la app empaquetada de Layer 3. | open /Applications/Layer 2 (nombre de carpeta heredado, corresponde a L3). |
# 5 — L4 · Version Control & Documentación
| Alias | Qué hace | Procedimiento interno |
| --- | --- | --- |
| vgit | Fuerza un sync inmediato del repo git fuera de su horario automático. | Invoca git_sync_wrapper.sh — commit con timestamp + push a origin/main si hay cambios sin commitear. |
| vsync-doc | Invocación directa del motor de sync documental (uso interno/depuración). | Corre vsync_doc.py sin el wrapper de comandos — requiere pasar flags manualmente. |
| vdoc | Sincroniza los 6 documentos fundacionales entre Notion y disco local. | Corre vdoc.py (wrapper de comandos) → invoca vsync_doc.py con la dirección y documento pedidos (auto/notion/local, dry, o nombre de documento específico — ver Manual §8.1 para la matriz completa). |
# 6 — Dashboard (Martes — Recuperación)
| Alias | Qué hace | Procedimiento interno |
| --- | --- | --- |
| vd | Abre el Dashboard de recuperación de vacantes bloqueadas. | Invoca dashboard_start.sh — arranca Flask en :8000, corre smoke test, abre dashboard.html en el navegador. |
| vdapp | Abre la app empaquetada del Dashboard. | open /Applications/Dashboard. |
# 7 — CV Pipeline (Miércoles)
Sin alias de Terminal — CV-A, CV-B y QA se disparan directamente en el chat de Claude (ver Manual §8.3).
# 8 — Dedup & Oportunidades
| Alias | Qué hace | Procedimiento interno |
| --- | --- | --- |
| vdedup | Consolida entradas duplicadas detectadas en el Tracker. | Corre consolidate_duplicates.py sobre la clave compuesta brand+title+location. |
| vopport | Limpia duplicados específicamente en oportunidades ya calificadas. | Corre dedup_opportunities.py. |
---
Figma Sync (plugin CV, 04-Vantage_CV/Figma Sync/) no tiene alias de Terminal propio — se opera desde Figma Desktop, ver Manual §8.3.
