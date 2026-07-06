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
| 8 | CHANGELOG | REFERENCIA | Historial |
## Layer 1 — Active Recon
| Alias | Descripción |
| --- | --- |
| vl1 | Run principal (→ layer_1_pipeline.sh) |
| vl1 status | Estado del pipeline L1 |
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
cd ~/Documents/04-Vantage_CV/Layer_1/scripts && source ../.venv/bin/activate && python lazy_loader.py --page {PAGE_ID} --route {ruta}
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
| vdoc cheat_sheet | Sync quirúrgico Cheat Sheet (auto) |
### Figma Sync — CV Output Layer
04-Vantage_CV/Figma Sync/ — Plugin Figma para inyección de payloads CV-B al lienzo.
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
