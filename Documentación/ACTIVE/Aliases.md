# V | ALIASES

# V | ALIASES

# V | ALIASES

| # | Sección | Tipo | Propósito |
| --- | --- | --- | --- |
| 1 | Layer 1 — Active Recon | OPERACIÓN | Pipeline principal |
| 2 | Layer 1 — Dedup | OPERACIÓN | Consolidación |
| 3 | Layer 3 & Dashboard | OPERACIÓN | Mail y UI |
| 4 | Lazy Loader (KERNEL Routes) | OPERACIÓN | Acceso rápido al Kernel |
| 5 | Layer 4 — Version Control | OPERACIÓN | Git y sync |
| 6 | Figma Sync | OPERACIÓN | Plugin CV |
| 7 | Runtime CLI | OPERACIÓN | Comandos vantage.py |
| 8 | Session Lifecycle | OPERACIÓN | Andamiaje de apertura/cierre de sesión |
| 9 | CHANGELOG | REFERENCIA | Historial |
## Layer 1 — Active Recon
| Alias | Descripción |
| --- | --- |
| vl1 | Run principal (→ layer_1_pipeline.sh) |
| vl1 tracker | Estado del pipeline L1 (Tracker en tiempo real) |
| vl1 analytics | Métricas y analítica |
| vl1 batch | Reporte batch (read-only). Pasar --execute para escribir. |
| vl1 recovery | Recovery mode |
| vl1 profile | Ver perfil activo |
| vl1 feed | Ciclo FEED |
| vl1 backfill | Backfill de entradas |
### Layer 1 — Dedup & Oportunidades
| Alias | Descripción |
| --- | --- |
| vdedup | Consolida duplicados (consolidate_duplicates.py) |
| vopport | Dedup de oportunidades (dedup_opportunities.py) |
### Layer 3 & Dashboard
| Alias | Descripción |
| --- | --- |
| vl3 | Mail pipeline (layer_3_mail.py) |
| vd | Dashboard RT-1 (dashboard_start.sh) |
### lazy_loader.py — Ruta Canónica
cd ~/Documents/03 Projects/VANTAGE/Layer_1/scripts && source ../.venv/bin/activate && python lazy_loader.py --page {PAGE_ID} --route {ruta}
### Layer 4 — Version Control & Documental
| Alias | Descripción |
| --- | --- |
| vgit | Git sync (git_sync_wrapper.sh) — runs auto 09/15/21h |
| vdoc dry | Preview sync Notion → ACTIVE/ (sin escritura) — usar siempre primero |
| vdoc notion | Notion → ACTIVE/{doc}.md + auto-commit GitHub — FORZADO, pide confirmación |
| vdoc local | ACTIVE/ → Notion (para edits offline) — FORZADO, pide confirmación |
| vdoc auto | Sync bidireccional — gana el más reciente (mtime local vs Notion) |
| vdoc kernel | Sync quirúrgico Kernel (auto) |
| vdoc system_prompt | Sync quirúrgico System Prompt (auto) |
| vdoc career_canon | Sync quirúrgico Career Canon (auto) |
| vdoc manual | Sync quirúrgico Manual (auto) |
| vdoc aliases | Sync quirúrgico Aliases (auto) |
| vdoc change_log | Sync quirúrgico Change Log (auto) |
### Figma Sync — CV Output Layer
03 Projects/VANTAGE/Figma Sync/ — Plugin Figma para inyección de payloads CV-B al lienzo.
| Archivo | Rol |
| --- | --- |
| manifest.json | Configuración nativa del plugin (entry: code.js, UI: ui.html) |
| code.js | Motor del plugin — Registry V2. Resolución O(1) por ID crudo vía REGISTRY embebido. |
| ui.html | Interfaz — acepta payload JSON (KEY semántica) o Markdown con figma_text_id (ID crudo directo) |
| registry_seed.json | SSOT de IDs de nodos Figma. No editar sin regenerar desde el lienzo. |
### Runtime CLI (vantage.py)
| Comando | Alias | Descripción |
| --- | --- | --- |
| vantage.py status | vstatus | Estado del sistema + index age |
| vantage.py sync | vsync | Regenera entity_index_v2.json desde Notion |
| vantage.py ask | vask | Query al agente |
| vantage.py resolve | vresolve | Resolver entidad |
| vantage.py context | vcontext | Context layer |
| vantage.py query | vquery | Query layer |
| vsync_doc.py | vdoc | Sync Notion → ACTIVE/ — ver tabla Layer 4 para flags |
## Session Lifecycle
Los comandos de esta sección no son parte del pipeline de vacantes — son el andamiaje que envuelve cada sesión de trabajo, sin importar qué vayas a hacer dentro de ella. Ver MANUAL:SESSION-CYCLE-001 para el detalle narrativo completo de qué hace cada uno y por qué.
Desde la optimización de verify_versions.py, Terminal es un requisito obligatorio para este ciclo — no existe fallback a fetch MCP directo. El operador corre los flags correspondientes en Terminal primero y entrega los outputs ya resueltos a Claude como payload de entrada; Claude ya no reconstruye ninguno de esos resultados por su cuenta.
| Alias | Descripción |
| --- | --- |
| /vantage-session-open | Abre la sesión: recibe como payload el dump de --bootstrap y la tabla de --check (ambos corridos antes en Terminal), procesa ambos, y realiza una sola escritura — crea fila OPEN en Session Ledger. Es lo primero que invocas al empezar a trabajar, después de correr Terminal. |
| /vantage-session-close | Cierra la sesión: recibe como payload el PASS de --check y el SYNC COMPLETE de --sync (ambos corridos antes en Terminal, junto con generate_census.py si hubo cambio de ID), valida el gate de sincronización, presenta el resumen hecho/pendiente, y marca la fila del Ledger como CLOSED. Es lo último que invocas antes de cerrar la ventana. |
| verify_versions.py --bootstrap | Read-only. Genera el bloque [DUMP INICIO SESIÓN VANTAGE]: última fila del Session Ledger, última entrada de Changelog, y snapshot de tickets CRÍTICO/ALTO. Se corre en Terminal antes de invocar /vantage-session-open y su output se pega junto con el de --check. |
| verify_versions.py --check | Read-only. Lee solo la propiedad Versión de los 7 documentos fundacionales, no su contenido — mucho más barato que un fetch completo. Se usa tanto en apertura (junto a --bootstrap) como en cierre de sesión. |
| verify_versions.py --sync | Único flag con escritura. Toma la versión target de la entrada de Changelog de la sesión, la lee vía pages.retrieve, y ejecuta seis peticiones pages.patch secuenciales — una por documento fundacional restante — actualizando directamente la propiedad "Versión" de cada página en Notion, sin pasar por Claude. Housekeeping, exento de APROBAR_WRITE. Se corre en Terminal como parte del cierre, antes de invocar /vantage-session-close. |
