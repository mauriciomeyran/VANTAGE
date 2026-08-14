# AUDIT DEEP SCAN — VANTAGE: PROPUESTA DE SANEAMIENTO ESTRUCTURAL

**Fecha:** 2026-08-13
**Rol:** Auditor de Confiabilidad (SRE) — revisión read-only del árbol activo y de la documentación canónica
**Alcance:** `Layer_1/scripts`, `Layer_3/scripts`, `Layer_4/scripts`, `Dashboard/scripts`, `Archive/Legacy_Scripts/`, `skills/`, `Raycast/`, documentos fundacionales (`Kernel.md`, `Manual.md`, `Change Log.md`, `Changelog Archivo.md`)
**Naturaleza del entregable:** propuesta — **no se ejecutó ninguna escritura, movimiento ni PATCH**. Toda ejecución posterior queda sujeta a DRY RUN + `APROBAR_WRITE` (KERNEL:CONTEXT-INFRASTRUCTURE-002) o a contrato PATCH puntual con Write-Back Verification.

---

## Resumen ejecutivo

VANTAGE tiene un núcleo de pipeline sano y un **anillo exterior de deuda estructural** producido por scripts de migración y parches de un solo uso que permanecieron en el árbol activo tras cumplir su función. El Deep Audit confirma:

1. **El grafo real de llamadas es más limpio que la documentación sugiere**: el pipeline depende de un núcleo de 7 módulos (Layer_1), las capas L3/L4 son autocontenidas, y el único acoplamiento cruzado de código es Dashboard→Layer_1 (3 archivos, vía hack de `sys.path` con ruta absoluta hardcodeada). **`Archive/Legacy_Scripts/` tiene cero aristas de entrada** — mover archivos allí no rompe nada en runtime.
2. **El mecanismo `verify_versions.py --scripts` es la base correcta** para medir el drift disco↔Script Library, pero su cobertura tiene 3 puntos ciegos verificados: (a) los artefactos `.bak2/.bak_prioridad/.bak_census010` esquivan el `.gitignore` y quedan trackeados; (b) los stubs `graph_v2.json`/`backlinks_v2.json` dentro de `scripts/` están vacíos mientras los datos reales viven en `Layer_1/data/`; (c) la Script Library (Notion) arrastra 70 filas con corrupción de auto-link `http://` documentada y sin remediar.
3. **Seis scripts activos son zombies verificados** (migraciones cerradas en Change Log o borradores muertos), encabezados por `backfill_next_action_select.py` (migración v9.14.2 cerrada con PASS 33/33) y `extract_score_distribution.py` (borrador con datos de muestra hardcodeados).
4. **`auto_archive.py` no debe rehabilitarse bajo PATCH puntual**: además de estar deprecado por decisión del operador (KERNEL:GATE-DECISION-007, v9.17.1), tiene 3 fallas técnicas independientes verificadas en código (root de `.env` incorrecto, filtro `rich_text` contra un campo migrado a `select` en v9.14.2, y destino — Archivo Tracker — con esquema corrupto). Su lugar correcto es `Archive/Legacy_Scripts/` como referencia histórica.
5. **La fricción del archivado manual no se resuelve con más automatización de escritura** — se resuelve con una skill de housekeeping que consolide el ciclo (detección → marcado → verificación) y un reporte Python read-only que elimine el escaneo visual del Tracker, sin tocar el Archivo Tracker hasta que su esquema se repare por decisión explícita.

Los Entregables 1 y 2 (abajo) concretan ambas propuestas con cita de ID canónico por recomendación.

---

## Metodología y límite de evidencia

### Lo que se verificó directamente (disco + documentación local)

- **Grafo de llamadas**: escaneo estático de los 58 archivos `.py` activos — `import`/`from` a nivel de módulo y perezosos, construcción de comandos `subprocess` (listas con `sys.executable`), y referencias de ejecución en wrappers `.sh` (Layer_1/wrappers, Layer_3/wrappers, Layer_4/wrappers, Dashboard/wrappers, Raycast). Se excluyó stdlib y terceros para aislar aristas intra-VANTAGE.
- **Inventario de disco**: simulación local fiel de `scan_committed_assets()` de `verify_versions.py` (mismos `ACTIVE_TOP_LEVEL_DIRS`, `EXCLUDED_DIR_NAMES`, `EXCLUDED_FILE_PREFIXES`, `EXCLUDED_DIR_SUBSTRINGS`) → **86 assets** `.py`/`.sh` visibles para `--scripts` (ver §Discrepancias Script Library).
- **Cierre de migraciones**: `Change Log.md`, `Changelog Archivo.md`, `MIGRATION_NEXT_ACTION_SELECT_V9.14.2.md`, y skills que registran decisiones del operador (`vantage-tidy-opportunities-tracker`, `vantage-sync-script-library`, `vantage-sync-script-glossary`, `vantage-tidy-changelog`).
- **Estado de GitHub**: issues #1–#4 del repo `mauriciomeyran/VANTAGE` (issue #1 "Drift KERNEL:GATE-DECISION-007 vs auto_archive.py" — CLOSED; #2 CLOSED; #3/#4 OPEN, fuera del alcance de esta auditoría).

### Límite declarado

Este sandbox no dispone de `NOTION_TOKEN` ni acceso a la API de Notion. Por tanto:

- La **mitad Notion** del gap report (`--scripts` contra SCRIPT LIBRARY, data source `ea914544-338f-485e-ac1b-7f137a5c9cee`) no pudo ejecutarse en vivo. Las discrepancias del lado Notion se basan en los snapshots documentados: CSV export 2026-08-05 (70 filas, 100% con corrupción de auto-link) y los hallazgos registrados en `vantage-sync-script-library`.
- Antes y después de aplicar la Propuesta de Deprecación, el operador debe correr `python3 Layer_1/scripts/verify_versions.py --scripts` (o el atajo Raycast `vantage-versions-scripts-gap.sh`) para obtener el gap report vivo. Este documento marca explícitamente cada afirmación como **verificado en disco** o **documentado en Notion** para que ninguna predicción se confunda con evidencia.

**Resolución del límite (añadido 2026-08-13, misma sesión):**

1. **Mitad local — CERRADA EN VIVO desde el sandbox.** `verify_versions.py --new-scripts` se ejecutó con env placeholder local (archivo gitignored, sin token real, sin llamadas de red): **86/86 assets documentados en el Glosario §22, 0 gaps**. Verificación análoga skills: **25/25 `.skill` en sync con `index.json`** al momento de la auditoría (posteriormente +1: `vantage-housekeeping-archive` creada en disco — ver Entregable 1).
2. **Mitad Notion — handoff único consolidado entregado en `handoffs/HANDOFF_MAESTRO_SANEAMIENTO.md`** (reemplaza a los dos handoffs anteriores, eliminados por solicitud del operador): tabla maestra secuencial de 23 tareas con responsable/script/atajo/gate/dependencia, contratos de sesión por agente (Operador, Claude, Devin, Grok, Mistral), IDs y anclas exactas.
3. **Estado de verdad actualizado (verificación de Claude en vivo, misma fecha):** `vantage-housekeeping-archive` estaba PENDING (no existía en disco ni Notion) — **creada en disco en este batch** (`skills/` + `index.json` 26), alta en SKILL LIBRARY pendiente de APROBAR_WRITE; duplicados v9.14.2 en Archivo Changelog **ACTIVOS (3 bloques)** — dedupe asignado a `vantage-tidy-changelog`; patch "máx. 5→10 correos" con ancla localizada en KERNEL:ARCHITECTURE-L3 §04.3 + segunda ancla en Manual; drift nuevo detectado: `resolver_registry_v2.json` tiene dos entradas para el Archivo Changelog (`CHANGELOG_ARCHIVE` vs `CHANGELOG_ARCHIVO`) — reportar, no corregir silenciosamente.
4. **Lo que no se hizo (y no debe hacerse):** el `NOTION_TOKEN` nunca se pidió ni se expuso en chat — el camino handoff cubre el 100% del cierre sin exponer el secreto.

**Estado de ejecución — verificación del cierre reportado por el operador (2026-08-14):** la **mitad disco quedó ejecutada y fue verificada contra `origin/main`** desde el sandbox: merge `3eeb3b8` integra arena en main; Tier A 6/6, B2 2/2 (prefijo `DEPRECATED_` verificado) y Tier C C1–C3/C6/B5 retirados (~10,000 líneas); conteo de assets activos **80/80 según la simulación fiel de `scan_committed_assets`** (el "79" reportado no corresponde al estado final verificado). **Corrección crítica al dictamen "100% concluido":** el huérfano de Notion `git_sync.py` no es un script retirado (nunca estuvo en ningún Tier y sigue intacto en `Layer_4/scripts/` — es el motor de `vgit`/`vdoc`); su fila en Script Library debe investigarse (mismatch de título o corrupción `http://`), **prohibido marcarla Deprecado**. Los otros dos huérfanos (`extract_score_distribution.py`, `patch_vsync_doc.py`) sí son los esperados post-movimiento → remediación `Deprecado`/`Archivar`. **Pendiente íntegro:** F2 Notion (tareas 10–15, 21–23 del `HANDOFF_MAESTRO_SANEAMIENTO.md`), F3 código (Devin), C4 (stubs gateados tras fix de `graph_layer.py`), C5 y Tier D (decisiones).

---

## Directiva 1 — Grafo de dependencias reales

### Núcleo de pipeline (Layer_1)

```
layer_1_pipeline.sh (entrada pública, v7.5)
├── (sin arg)          → layer_1_run.py          [importa: gate_logic (top), profile_fit (lazy),
│                                                   priority_logic (lazy); ejecuta por subprocess:
│                                                   dedup_opportunities.py (Fase 6 --dedup-audit)]
├── feed <json>        → feed_processor.py       [importa: layer_1_run (is_agregador,
│                                                   validate_url_pre_ingestion), profile_fit]
├── tracker            → status_report.py        [→ notion_utils]
├── analytics          → source_analytics.py     [→ notion_utils]
├── batch              → batch_operations.py     [→ notion_utils]
├── recovery           → pipeline_recovery.py    [→ notion_utils]
├── profile            → profile_evolution.py    [standalone, interactivo]
└── backfill           → backfill_class_a.py     [→ feed_processor, layer_1_run, priority_logic
                                                   (con hack de sys.path anti-colisión)]
```

- `backfill_class_a.py` queda como **catch-up de huecos legacy**, no como vía primaria — comentario explícito en `layer_1_run.py` (líneas 25–26, 932–934) y `MANUAL:SCRIPT-GLOSSARY-L1-MODULES` (`priority_logic.py`). **NO es candidato a archivo.**
- Arista bidireccional detectada: `feed_processor.py → layer_1_run` (import de nivel superior) y `layer_1_run.py → feed_processor` (solo vía comentarios/referencias de texto, no import). Es un acoplamiento estructural real: correr `feed_processor.py` suelto arrastra la cadena de `layer_1_run` → `gate_logic`. Mismo patrón de riesgo que la triplicación de `txt()` ya documentada (Change Log v9.20.2): **documentar, no refactorizar sin instrucción** (KERNEL:EVOLUTION — cambios válidos solo con ineficiencia probada con datos).

### Cluster de agente / índice de entidades (Layer_1, segundo grafo independiente)

```
vantage.py (CLI)
├── → agent_api.py        [lazy: query_layer, context_layer, notion_utils, graph_layer]
├── → context_layer.py    [lazy: query_layer, notion_utils]
├── → query_layer.py      [lazy: resolver_layer_v1]
└── → notion_utils.py
health_check.py ──subprocess──▶ vantage.py
Raycast/vantage-sync.sh ──────▶ vantage.py sync
```

- `graph_layer.py` carga `scripts/graph_v2.json` y `scripts/backlinks_v2.json` — **ambos son stubs vacíos de 37 y 41 bytes** (`{"edges": []}` / `{"backlinks": {}}`). Los datos reales viven en `Layer_1/data/graph_v2.json` (2.8 KB) y `Layer_1/data/backlinks_v2.json` (2.7 KB). **Hallazgo F2 (funcional, no solo cosmético):** `vantage.py ask` responde con relaciones vacías (`get_archived_from`, `get_backlinks`, `graph_stats`) pese a que `vantage.py sync` regenera los JSON correctos en `data/`. El glosario lo asume sano: "si `vantage.py ask` devuelve relaciones incorrectas... corre `vantage.py sync`" (MANUAL:SCRIPT-GLOSSARY-L1-MODULES) — el consejo no repara el desfase de ruta.
- `lazy_loader.py` y `runtime_identity.py` son contratos vivos por KERNEL:CONTEXT-INFRASTRUCTURE-001 y por consumo de `generate_entity_index_v2.py` — no tocar.

### Cluster documental (Layer_1)

```
generate_census.py · generate_id_inventory.py · apply_hyperlinks_notion.py → vantage_id_rules
normalize_heading_ids.py → vantage_id_rules
verify_versions.py (standalone, httpx; alias vversions — KERNEL:DOCUMENTATION-007)
clean_script_library_links.py (standalone, herramienta de remediación Notion)
```

### Layer_3 — autocontenida

`layer_3_mail.py` (IMAP + Groq, sin imports de hermanos). Wrapper: `Layer_3/wrappers/layer_3_mail.sh`; Raycast: `vantage-vl3.sh`. **Cero deuda de acoplamiento.**

### Layer_4 — autocontenida, cadena por subprocess

```
vdoc.py ──subprocess──▶ vsync_doc.py ──subprocess──▶ git_sync.py
vsum.py (standalone, Groq/Gemini — flag --notion vestigial, documentado en 22.3)
patch_vsync_doc.py (one-shot, PATCH APPLIED 2026-07-05 — zombie, ver Directiva 3)
```

### Dashboard — único acoplamiento cruzado de código del sistema

```
dashboard_routes.py → dashboard_notion.py · dashboard_validation.py · dashboard_db.py
dashboard_notion.py → dashboard_config + layer_1_run (txt) + class_b_guard (lazy)
dashboard_validation.py → layer_1_run (validate_url_pre_ingestion, calculate_score_v6,
                          get_vm_scope, get_role_class, gate)
layer_1_run_dash.py → gate_logic (Layer_1)  [sys.path hack en 3 sitios: L40, L397, L704]
```

- **Hallazgo F1 (riesgo, no violación):** el puente Dashboard→Layer_1 se monta con `sys.path.insert(0, os.path.expanduser("~/Documents/03 Projects/VANTAGE/Layer_1/scripts"))` — ruta absoluta hardcodeada en 4 puntos. La arquitectura está documentada como decisión (MANUAL:SCRIPT-GLOSSARY-DASHBOARD-MODULES: "garantiza que el Dashboard aplique exactamente la misma lógica... no una copia paralela"), así que **no se propone revertirla**; sí se propone sustituir el literal por la variable `LAYER_1_DIR` (ya usada por `layer_1_pipeline.sh` y `layer_1_wrapper.sh`) como hardening de portabilidad, en un fix separado con su propio ticket.
- `class_b_guard.py` es el guard de la vía RT-1 (KERNEL:GATE-DECISION-003, GAP-03 cerrado v9.19.2) — intocable.

### Archive/Legacy_Scripts — cero aristas de entrada

Verificado por escaneo completo de referencias: **ningún** archivo del árbol activo importa o ejecuta nada dentro de `Archive/Legacy_Scripts/`. Cualquier movimiento propuesto en la Directiva 3/Entregable 2 es seguro en runtime. El único vínculo restante es documental: KERNEL:ARCHITECTURE-L4 aún cita `vsync_doc_fast.py` (deprecado en disco) dentro del "riesgo conocido" de delete-all/create-all — **referencia canónica colgante** que debe corregirse por PATCH inline (sin ID nuevo).

---

## Directiva 2 — Script Library (Notion) vs. disco

### Mecanismo base (verificado en código)

`verify_versions.py --scripts` (KERNEL:DOCUMENTATION-007 §03.7) ejecuta:

1. `scan_committed_assets(PROJECT_ROOT, (".py", ".sh"))` sobre `ACTIVE_TOP_LEVEL_DIRS = {Layer_1, Layer_3, Layer_4, Dashboard, Raycast, skills}`, excluyendo directorios `{archive, archived, tests, test, backup, one_offs, deprecated_scripts, .venv, venv, node_modules, .git}`, substrings `("backup_", "discarded_")` y el prefijo de archivo `DEPRECATED_`.
2. Cruzado contra SCRIPT LIBRARY (`ea914544-338f-485e-ac1b-7f137a5c9cee`), schema confirmado: `Script` (título), `Ruta`, `Capa`, `Descripción`, `Dependencias`, `Estado ∈ {Activo, En desarrollo, Deprecado}`, `Acción ∈ {Keep, Archivar}`, `Fecha de creación`.
3. Emite tres listas: **SIN REGISTRAR EN NOTION**, **REGISTRADOS Y VIGENTES**, **EN NOTION COMO 'Activo' PERO NO EN DISCO** (huérfanos).

### Inventario de disco (simulación fiel, 86 assets)

| Árbol | .py | .sh | Subtotal |
| --- | --- | --- | --- |
| Layer_1 (scripts 43+5 · `tools/` 1 · `layer_1_pipeline.sh` · `wrappers/` 1) | 44 | 7 | 51 |
| Layer_3 (incluye `wrappers/`) | 1 | 1 | 2 |
| Layer_4 (incluye `wrappers/`) | 5 | 1 | 6 |
| Dashboard (incluye `wrappers/`) | 8 | 1 | 9 |
| Raycast | — | 18 | 18 |
| **Total** | **58** | **28** | **86** |

### Discrepancias documentadas del lado Notion (no verificables en vivo desde este sandbox)

1. **Corrupción masiva de auto-link** (fuente: `vantage-sync-script-library`, CSV export 2026-08-05): las 70 filas existentes tienen `Script`/`Ruta` corrompidos por Notion (`health_http://check.py`). La skill declara la limpieza retroactiva **fuera de su alcance** — sigue pendiente como batch de 70 updates con su propio DRY RUN. **Esta deuda degrada el matching del gap report**: títulos con `http://` incrustado no coinciden con nombres de disco → falsos "SIN REGISTRAR".
2. **Mismatch de nombre conocido**: Notion `apply_hyperlinks.py` vs disco `apply_hyperlinks_notion.py` (renombrado) — patrón de remediación documentado en la misma skill (preguntar al operador, proponer `update` de título, no crear fila nueva).
3. **Filas de scripts ya deprecados en disco** que, si siguen en `Estado=Activo`, aparecen hoy en el gap report como huérfanos de Notion. Candidatos predecibles: `auto_archive.py`, `vsync_doc_fast.py`, `apply_hyperlinks.py` (legacy), `vantage-assign.sh`. **Predicción, no evidencia** — confirmar con el reporte vivo.
4. **Drift de conteo de skills**: KERNEL:ARCHITECTURE-L4 declara "(actualmente 12)" .skill files; el disco tenía **25** al momento de la auditoría y **26** tras la creación de `vantage-housekeeping-archive` (este batch). Mismo nodo documenta la SSOT (`/skills/` + GitHub Pages) — el número en prosa quedó obsoleto sin mecanismo que lo detecte.
5. **ID canónico colgante — `KERNEL:SKILL-ANNOUNCE-CONVENTION`** (hallazgo nuevo de esta auditoría): citado por `MANUAL.md` (§ skills) y por las 25 skills como convención de anuncio, pero **no existe bloque de definición en ningún fundacional** ni entrada en `resolver_registry_v2.json` (verificado). Remedio propuesto (sin violar la Matriz Tipográfica): Opción A — reanclar la referencia a un nodo existente (descripción de convención ya vive en Manual §skills); Opción B — alta formal del nodo `### NN.N KERNEL:SKILL-ANNOUNCE-CONVENTION` bajo §03 vía `vantage-documentacion-transversal-propuesta`, lo que **sí** dispara CENSUS-SYNC Regla 1 (KERNEL:DOCUMENTATION-008). Recomendación: Opción A en este ciclo.

### Regla de acoplamiento (derivada de la matriz de ciclo de vida)

MANUAL:SCRIPT-GLOSSARY-XREF define: mover un script a carpeta excluida produce estado **HUÉRFANO_GLOSARIO / HUÉRFANO_NOTION** "sin flag de alerta hasta auditoría manual". Por lo tanto, **toda ejecución del Entregable 2 debe ir acoplada** a su remediación documental en el mismo batch: fila Script Library (`Estado→Deprecado`, `Acción→Archivar`) + anotación en el Glosario §22. De lo contrario, el saneamiento solo traslada el drift del disco a Notion.

---

## Directiva 3 — Scripts huérfanos y "zombies" (evidencia verificada)

### Zombies de migración cerrada (núcleo del Entregable 2)

| # | Archivo | Ubicación | Estado verificado | Evidencia de cierre |
| --- | --- | --- | --- | --- |
| Z1 | `backfill_next_action_select.py` | `Layer_1/scripts/` | Migración v9.14.2 **COMPLETADA** — dry-run arrojó 0 huérfanos; nunca requirió ejecución | `MIGRATION_NEXT_ACTION_SELECT_V9.14.2.md` (root) "ESTADO: COMPLETADO - PENDIENTE AUDITORÍA"; `Changelog Archivo.md` entrada v9.14.2 "Next_Action Migration ✅ PASS 33/33"; KERNEL:SCHEMA-008 §07.8 confirma select vigente |
| Z2 | `toggle_changelog_archive.py` | `Layer_1/scripts/` | Un solo uso (formateo toggle del Archivo Changelog). **Cero callers** — solo referenciado en Manual | `MANUAL:SCRIPT-GLOSSARY-L1`; búsqueda global: sin invocador en `.py`/`.sh`/skills |
| Z3 | `backfill_archive_fingerprint.py` | `Layer_1/scripts/` | Un solo uso (fingerprints GILSA sobre Archivo Tracker). **Cero callers** | Auditoría dedup Archivo Tracker cerrada v9.13.0 (12/12 write-back PASS, `Changelog Archivo.md`); solo referenciado en Manual |
| Z4 | `patch_vsync_doc.py` + `patch_vsync_doc.STATUS.md` | `Layer_4/scripts/` | **PATCH APPLIED ✅** (2026-07-05). `vsync_doc.py` ya contiene `aliases` + `change_log` (verificado en disco) | `patch_vsync_doc.STATUS.md`; el propio Manual 22.1b: "no debería necesitar correrse de nuevo. Considera moverlo..." |
| Z5 | `patch_new_scripts.py` | `Layer_1/tools/` | Un solo uso. El flag `--new-scripts` ya existe en `verify_versions.py` (verificado); el patcher es idempotente y hoy no-op | Header del propio script + `render_new_scripts_gap_report()` presente en `verify_versions.py` |
| Z6 | `extract_score_distribution.py` | `Layer_1/scripts/` | **Código muerto**: borrador con `sample_data` hardcodeado y comentarios "Simulación: voy a asumir...", "Por ahora..." — nunca consulta Notion | Hallazgo ya documentado en `MANUAL:SCRIPT-GLOSSARY-L1-TOOLS` ("decide tú si vale la pena eliminarlo del árbol para que deje de aparecer en cada gap report"); superado por `extract_scores.py` funcional |

### Borradores funcionales sin conexión al pipeline (categoría "watch" — no archivar sin decisión)

- `feedback_loop.py` — documentado en Glosario, sin caller, sin wrapper, sin atajo Raycast. Herramienta de métricas de efectividad; no es zombie de migración. **Recomendación: pregunta directa al operador** (mantener como herramienta manual o archivar).
- `cross_tracker_match.py` — documentado como **incompleto**: `query_archive_tracker()` es placeholder sin implementar (declarado en `vantage-tidy-opportunities-tracker` como gap abierto). **No proponer archivo**: es la pieza que un día habilitaría el cruce Inbound↔Público; sí proponer registrar el gap en Bug Tracker (KERNEL:GATE-DECISION-009, Nivel 2 — sugerencia + confirmación).
- `consolidate_duplicates.py` — activo vía Raycast `vantage-dedup.sh`; conservar.

### Artefactos de proceso trackeados en git (sin valor de archivo ni de runtime)

Verificado con `git ls-files` — todos están dentro del árbol versionado:

- Backups que **esquivan el `.gitignore`** (solo cubre `*.bak`): `feed_processor.py.bak2`, `feed_processor.py.bak_prioridad`, `generate_census.py.bak_census010`.
- Parches ya aplicados: `dedup_fix_verified.patch`, `fix_terminal_protection_layer_1_run.patch`.
- Dumps de depuración: `bug_tracker_full.json`, `task_tracker_full.json`, `out/schema_full.json`, `out/schema_properties.json`.
- Documentación duplicada dentro de `scripts/`: `contrato_migracion_headings.md` (duplica contratos del Manual), `generate_census.md` (duplica el Glosario §22), `DEDUP_AUDIT_GUIDE.md`.
- Stubs vacíos `graph_v2.json` (37 B) + `backlinks_v2.json` (41 B) en `scripts/` — causa raíz del **Hallazgo F2**.
- `Archive/Legacy_Scripts/dump_trackers.py.save` — copia accidental duplicada de `dump_trackers.py`.
- `Documentación/ACTIVE/.vsync_manifest.json.backup` — byte-idéntico al manifest activo.

### Ruido fuera del pipeline (decisión de operador, no de auditor)

- `facial_analyzer.py` (raíz) — código extranjero (clasificador de rostros MediaPipe/scipy), sin relación con las 4 capas (KERNEL:ARCHITECTURE). Recomendar salida del repo.
- `index.html` (raíz) — duplicado de la página de documentación de skills que ya vive en `skills/index.html`.
- `Video/` (113 MB, 15 archivos) y `Outputs/` (211 archivos, 127 MB) trackeados en git — `.git` pesa 210 MB. Política de retención externa (los outputs son entregables del CV-PIPELINE, KERNEL:NAMING-CONVENTION; los videos son material de presentación).
- `inventario_output/` — duplicado de `Layer_1/data/inventario_*.md/csv`.
- `.devin/skills/vantage-hyperlink-loop/SKILL.md` — difiere del canónico `skills/vantage-hyperlink-loop.md` (verificado con `diff`): espejo desincronizado contra la SSOT declarada en KERNEL:ARCHITECTURE-L4.
- `Dashboard/archive/legacy_express_node/` (Express v7, 5 HTML + package-lock) y `Layer_4/archive/bak_cleanup_20260705/` + `Layer_4/archive/unidentified/` (READMEs de tareas muertas, una documenta un "FILE NOT FOUND"). Los dirs `archive/` ya están excluidos del scan — su mantenimiento es decisión de retención, no de pipeline.

### Changelog Archivo — duplicados verificados

La entrada de migración v9.14.2 aparece **3 veces consecutivas sin encabezado propio** en `Changelog Archivo.md` (bloque `[SCHEMA] [CODE] [AUDIT]` repetido x3) — exactamente el pendiente que v9.14.5 ya había señalado ("duplicados v9.14.3 x2, v9.14.2 x3... refuerzan pendiente de vantage-tidy-changelog") y que sigue abierto. Remedio: disparar `vantage-tidy-changelog` (regla de oro: **mover, nunca borrar**).

---

## Directiva 4 — Sistema de archivado: estado real y contradicciones

### Cronología del contrato (verificada)

1. **2026-08-01** — Decisión del operador: se abandona mover/copiar automáticamente vía `auto_archive.py` (menor fricción, menos tokens, desalineación de esquema con el Archivo Tracker). Registrada en `vantage-tidy-opportunities-tracker` y luego en KERNEL:GATE-DECISION-007.
2. **2026-08-10** — GitHub issue #1 (drift: Kernel documentaba `auto_archive.py` como activo) → **CLOSED**; KERNEL:GATE-DECISION-007 §09.7 reescrito a "Marcado Manual de Archivado" (Change Log v9.17.1). Pendiente explícito en esa entrada: *"decidir eliminacion o conservacion como referencia de auto_archive.py en el repo"* — **esta auditoría lo resuelve: conservar** (ver Entregable 1).
3. **Vigente hoy** — KERNEL:GATE-DECISION-007: señales `Next_Action='Archivar'` y/o `Dedup_Flag='Posible duplicado'` (Class B) **no disparan archivado automático**; el mecanismo vigente es la skill `vantage-tidy-opportunities-tracker` (marca `Archivar = True` en el registro original tras DRY RUN + APROBAR_WRITE); el archivado físico es manual del operador.

### `auto_archive.py` — decadencia triple verificada (más allá de la deprecación)

| # | Falla | Evidencia en código | Contrato violado |
| --- | --- | --- | --- |
| A | **Root de `.env` incorrecto**: `_LAYER_1_ROOT = Path(__file__).resolve().parent.parent` resuelve a `Archive/`, no a la raíz VANTAGE ni a `Layer_1/` | `auto_archive.py` L36–37; no existe `.env` en `Archive/` (verificado en disco) → `KeyError: NOTION_TOKEN` en import | Patrón de carga correcto documentado en `feed_processor.py`/`extract_scores.py` (`parent.parent` = `Layer_1/`) |
| B | **Filtro de query obsoleto**: `"Next_Action": {"rich_text": {"equals": "Archivar"}}` contra un campo que migró a `select` | `query_archive_candidates()`, filter_body L164–185; KERNEL:SCHEMA-008 §07.8 (select desde v9.14.2) → 400 de API o 0 resultados | KERNEL:SCHEMA-008 |
| C | **Destino con esquema corrupto**: el Archivo Tracker tiene `Next_Action 1` (con opciones de Bug/Task Tracker), `Fetch`/`Fuente`/`VM_Scope`/`Status` duplicadas con tipos inconsistentes y `Score_Method` faltante — sin resolver | Skill `vantage-tidy-opportunities-tracker` (hallazgo 2026-08-01); "Persistente" en `Changelog Archivo.md` v9.13.0 | — |

Aun si se repararan A y B, el flujo escribiría páginas mensuales dentro de un tracker cuyo esquema no está alineado con el Tracker activo — la misma desalineación que motivó la decisión de 2026-08-01.

### Datos de estado del Tracker (snapshot documentado 2026-07-19, no inferido)

- 76 registros totales; 36 con `Next_Action='Archivar'`; solo 2 con `Dedup_Flag='Posible duplicado'` → **34 "zombis" de marcado sin ejecución**.
- 27 registros `Status=Expirada` con `Gate_Decision` vacío — `Gate_Decision=EXPIRED` existe en schema pero **nunca se puebla**; la señal real y suficiente es `Status=Expirada` (Class A).
- `cross_tracker_match.py` (cruce Inbound↔Público) — placeholder sin implementar.

---

## Entregable 1 — Propuesta de refactorización del sistema de archivado

### Decisión central: ¿rehabilitar `auto_archive.py` bajo PATCH puntual o absorber el flujo en housekeeping?

**Respuesta: ninguna rehabilitación de `auto_archive.py` en su forma actual; el flujo se absorbe en una skill de housekeeping nueva, con la skill de marcado vigente como vía de escritura única.** Razones encadenadas:

1. Rehabilitar exige un PATCH de 3 frentes simultáneos (env-root, filtro select, reparación previa del esquema del Archivo Tracker) para restaurar un flujo que el operador deprecó por fricción — inversión desproporcionada, y la reparación del esquema del Archivo Tracker es una decisión de datos independiente que no debe quedar como prerequisito oculto de un script.
2. KERNEL:EVOLUTION: revertir una decisión documentada requiere "ineficiencia probada con datos"; no existe evidencia nueva de ineficiencia — la fricción actual es de **localización visual**, no de escritura.
3. SP:CONSISTENCY 05 (invocado por KERNEL:GATE-DECISION-009): automatismos basados en inferencias no confirmadas están prohibidos. Cualquier automatización de archivado debe derivar de señales Class A/Class B ya calculadas por Python y pasar por gate explícito — el contrato correcto ya existe: es el de `vantage-tidy-opportunities-tracker`.

### Diseño propuesto — skill `vantage-housekeeping-archive` (nueva, 4 fases)

> **Estado (2026-08-13):** creada en disco en este batch — `skills/vantage-housekeeping-archive.md` + `.skill` + entrada en `skills/index.json` (26 recursos). Pendiente: alta en SKILL LIBRARY (Notion) con DRY RUN + `APROBAR_WRITE` — asignada en `handoffs/HANDOFF_MAESTRO_SANEAMIENTO.md` (tarea 11).

La skill **no escribe nada que hoy no se escriba**. Elimina la fricción consolidando el ciclo completo en un solo procedimiento con anuncio (`ARCHIVING HOUSEKEEPING...` / `ARCHIVE HOUSEKEPT`, según KERNEL:SKILL-ANNOUNCE-CONVENTION) y añade un reporte Python read-only que sustituye el escaneo visual del Tracker.

### Fase 0 — Detección (lectura, sin escritura)

- Candidatos: `Dedup_Flag='Posible duplicado'` (señal primaria), `Status=Expirada` (señal real y suficiente — no asumir `Gate_Decision=EXPIRED`, verificado vacío en la práctica), `Next_Action ∈ {Archivar, Post-Mortem}` (KERNEL:SCHEMA-008, KERNEL:GATE-DECISION-006).
- Guards heredados textualmente de KERNEL:GATE-DECISION-010 y `gate_logic.py`: exclusión absoluta de `Gate_Decision=APPLIED` (reporte aparte, "aplicación activa"); protección de terminalidad (`STATUS_TERMINAL_MAP` → `TERMINAL_ACTIONS`, en ese orden); nunca sobreescribir `Next_Action` ni ningún Class B (KERNEL:CV-GOLDEN-RULES-002).

### Fase 1 — Marcado (única vía de escritura vigente, sin cambios)

Reutiliza el procedimiento de `vantage-tidy-opportunities-tracker` (payload mínimo `{"Archivar": {"checkbox": true}}`, DRY RUN con tabla de evidencia → variante válida de `APROBAR_WRITE` → write-back verification). La skill de housekeeping **no duplica** este procedimiento: lo referencia como sub-skill, igual que KERNEL:GATE-DECISION-009 escala a `vantage-create-bug-task`.

### Fase 2 — Reporte de "listos para archivar" (desfricción real, read-only)

Extender `status_report.py` (ya invocado por `layer_1_pipeline.sh tracker` y Raycast `vantage-status.sh`) con una vista `--archive-queue`: tabla de registros con `Archivar=True` agrupados por criterio, con IDs de página listos para localizar en Notion. Cero escritura nueva, cero dependencia del esquema del Archivo Tracker — elimina la parte manual del escaneo visual sin violar KERNEL:OWNERSHIP-002 (Python calcula y reporta; el operador decide). Requiere fix puntual de código + tests (patrón v9.20.x), con su propio DRY RUN.

### Fase 3 — Reparación del esquema del Archivo Tracker (opcional, gateada por operador)

Batch **separado** y explícito, solo si el operador quiere volver a usar el Archivo Tracker como destino: one-shot bajo contrato de PATCH puntual al estilo v9.14.2 (dry-run por default, backup de esquema, write-back verification, APROBAR_WRITE por grupo de propiedades). Objetivo documentado: eliminar `Next_Action 1` corrupta, deduplicar `Fetch`/`Fuente`/`VM_Scope`/`Status` y crear `Score_Method`. **No bloquear las Fases 0–2 por esta reparación** — es exactamente el anti-patrón que ya se evitó el 2026-08-01.

### Fase 4 — Rehabilitación de movimiento automático (NO recomendada en este ciclo)

Solo tras Fase 3 PASS y con evidencia nueva de fricción. Si algún día se aprueba, el artefacto debe ser un `auto_archive_v2.py` **nuevo** bajo el contrato v9.14.2 (filtro `select`, root de `.env` correcto, guards de Fase 0, dry-run default) — nunca un PATCH sobre el archivo deprecado. Registrar como decisión futura, no como tarea.

### Disposición de `auto_archive.py` — resuelve el pendiente de v9.17.1

**Conservar en `Archive/Legacy_Scripts/` como referencia histórica** ("Mantenimiento histórico"), en coherencia con KERNEL:EVOLUTION §17 "Linaje Histórico — Preservado, No Operacional". Acciones acopladas:

1. Script Library: si la fila `auto_archive.py` sigue en `Estado=Activo`, actualizar a `Deprecado` + `Acción=Archivar` (via `vantage-sync-script-library`, con DRY RUN).
2. Glosario §22: anotar bajo el ítem de `auto_archive.py` el historial (decisión 2026-08-01, v9.17.1, issue #1 cerrado, decadencia A/B/C verificada 2026-08-13) — patrón "⚠️ Hallazgo real" ya usado en 22.1b.
3. Cerrar el pendiente de la entrada v9.17.1 con una entrada de Change Log nueva del tipo `[AUDIT]` citando este documento.

### IDs canónicos afectados por el Entregable 1

| Cambio propuesto | Tipo | IDs afectados | Notas de gobernanza |
| --- | --- | --- | --- |
| Extensión inline de §09.7 (añadir referencia a la skill de housekeeping y al reporte `--archive-queue`; sin retitular) | PATCH documental | `KERNEL:GATE-DECISION-007` | Inline, sin sección nueva, sin ID nuevo → no dispara CENSUS-SYNC Regla 1 (KERNEL:DOCUMENTATION-008). Vía `vantage-documentacion-transversal-propuesta` |
| Nueva skill `vantage-housekeeping-archive` | Alta de skill | SKILL LIBRARY (fila nueva) — sin ID de Kernel | Alta vía `--skills` gap report + `vantage-sync-skill-library` |
| Extensión de `status_report.py` (flag `--archive-queue`) | Fix de código + tests | `MANUAL:SCRIPT-GLOSSARY-L1` (entry `status_report.py` — marcar ⚠️ DESACTUALIZADO hasta documentar el flag) | Ticket Bug/Task Tracker propio; KERNEL:GATE-DECISION-009 Nivel 2 (sugerencia + confirmación) |
| Nueva fila en la matriz de ciclo de vida | Extensión de nodo existente | `MANUAL:SCRIPT-GLOSSARY-XREF` | Fila: DOCUMENTADO → movido a `Archive/Legacy_Scripts/` ⇒ remediación acoplada Notion+Glosario en el mismo batch |
| PATCH de la referencia colgante a `vsync_doc_fast.py` en §04.4 | PATCH documental | `KERNEL:ARCHITECTURE-L4` | Inline, sin ID nuevo |

### Formato de bloque propuesto (Regla de Bloque Único — ID y título en la misma línea)

Para la extensión de Kernel §09.7, el texto se inyecta **dentro** del bloque existente `### 09.7 KERNEL:GATE-DECISION-007` (título "Marcado Manual de Archivado") sin crear `NN.N.N`. Ningún bloque nuevo bajo la jerarquía de headings del Kernel — la Matriz Tipográfica Congelada (KERNEL:DOCUMENTATION-001) solo autoriza `## NN` / `### NN.N`.

---

## Entregable 2 — Propuesta de Deprecación (candidatos a archivo)

### Tabla maestra

**Tier A — Mover a `Archive/Legacy_Scripts/` (6 movimientos, riesgo runtime = 0, aristas de entrada verificadas = 0)**

| # | Archivo(s) | Desde | Categoría | Justificación (con evidencia) | Remedio documental acoplado |
| --- | --- | --- | --- | --- | --- |
| A1 | `backfill_next_action_select.py` | `Layer_1/scripts/` | Un solo uso ejecutado | Migración v9.14.2 cerrada: PASS 33/33, 0 huérfanos; script quedó como auditoría post-mortem sin callers (Z1) | Script Library: `Deprecado`/`Archivar`; Glosario §22.1 nota "migración cerrada v9.14.2, movido a Archive" |
| A2 | `toggle_changelog_archive.py` | `Layer_1/scripts/` | Un solo uso ejecutado | Formateo toggle ya aplicado al Archivo Changelog; cero callers (Z2) | Ídem (fila propia en Script Library) |
| A3 | `backfill_archive_fingerprint.py` | `Layer_1/scripts/` | Un solo uso ejecutado | Caso GILSA cerrado (v9.13.0, 12/12 write-back PASS); cero callers (Z3) | Ídem |
| A4 | `patch_vsync_doc.py` + `patch_vsync_doc.STATUS.md` | `Layer_4/scripts/` | Un solo uso ejecutado | PATCH APPLIED (2026-07-05); objetivo ya presente en `vsync_doc.py` (Z4). Mover ambos juntos — el STATUS es la evidencia del patch | Ídem; quitar entrada de §22.1b o anotarla como "movido" |
| A5 | `patch_new_scripts.py` | `Layer_1/tools/` | Un solo uso ejecutado | `--new-scripts` ya nativo en `verify_versions.py`; patcher idempotente hoy no-op (Z5) | Ídem |
| A6 | `extract_score_distribution.py` | `Layer_1/scripts/` | Código muerto | Borrador con datos hardcodeados; hallazgo ya registrado en §22.1b; superado por `extract_scores.py` (Z6) | Ídem; cerrar el "⚠️ Hallazgo real" abierto en §22.1b |

**Tier B — Ya están en `Archive/Legacy_Scripts/`: conservar, renombrar y documentar (0 movimientos)**

| # | Ítem | Categoría | Acción |
| --- | --- | --- | --- |
| B1 | `auto_archive.py` | Mantenimiento histórico | Conservar como referencia (decisión 2026-08-01 + decadencia A/B/C). Script Library → `Deprecado`/`Archivar`. Cierra pendiente v9.17.1 |
| B2 | `DEPRECADO apply_hyperlinks.py`, `DEPRECADO vsync_doc_fast.py` | Mantenimiento histórico | Unificar naming a prefijo `DEPRECATED_` (espacio/idioma mixto hoy) para alinear con `EXCLUDED_FILE_PREFIXES` y con la fila de transición de MANUAL:SCRIPT-GLOSSARY-XREF |
| B3 | `assign_next_action.py` + `vantage-assign.sh` + `DEPRECATED_assign_next_action.md` | Un solo uso ejecutado | Flujo de asignación legacy superado por el pipeline; conservar trio documental junto (el .md es el reporte de deprecación) |
| B4 | `patch_feed.py`, `patch_kernel.py`, `health_check_patch.py`, `reset_fetch_bug.py`, `reset_fetch_bug_rows.py`, `fix_manual_golden_rules_table.py`, `fix_versions_py_artifact.py`, `diagnose_versions_py.py`, `diagnose_kernel_blocks.py`, `analyze_block_ids.py`, `get_canon_anchors.py`, `audit_schema.py`, `dump_trackers.py`, `fetch_hashes.py/.sh`, `skill_to_md.py`, `test_content_fingerprint.py`, `verify_dedup_fix.py` | Un solo uso ejecutado / Código muerto | Conservar como historia (KERNEL:EVOLUTION §17). Sin acción salvo confirmar filas Notion en `Deprecado` si existen |
| B5 | `dump_trackers.py.save` | Código muerto | Eliminar (duplicado accidental de `dump_trackers.py`) |

**Tier C — Artefactos de proceso: retirar del árbol versionado (sin valor de archivo)**

| # | Ítem | Ubicación | Justificación |
| --- | --- | --- | --- |
| C1 | `feed_processor.py.bak2`, `feed_processor.py.bak_prioridad`, `generate_census.py.bak_census010` | `Layer_1/scripts/` | Backups que esquivan `*.bak` del `.gitignore`; ampliar ignore a `*.bak*` (patrón tipo `backup_`/`discarded_` de `verify_versions.py`) |
| C2 | `dedup_fix_verified.patch`, `fix_terminal_protection_layer_1_run.patch` | `Layer_1/scripts/` | Parches ya aplicados |
| C3 | `bug_tracker_full.json`, `task_tracker_full.json`, `out/schema_full.json`, `out/schema_properties.json` | `Layer_1/scripts/` | Dumps de depuración |
| C4 | `graph_v2.json`, `backlinks_v2.json` (stubs de 37/41 B) | `Layer_1/scripts/` | Causa raíz del Hallazgo F2. Retirar los stubs y **corregir `graph_layer.py`** para leer de `Layer_1/data/` (fix con tests, ticket propio) |
| C5 | `contrato_migracion_headings.md`, `generate_census.md`, `DEDUP_AUDIT_GUIDE.md` | `Layer_1/scripts/` | Documentación duplicada del Manual §22; mover a `Archive/Legacy_Scripts/` si aporta historia, o eliminar si §22 ya la absorbe (verificar solapamiento en el batch) |
| C6 | `.vsync_manifest.json.backup` | `Documentación/ACTIVE/` | Byte-idéntico al manifest activo |

**Tier D — Fuera del pipeline: decisión del operador (recomendaciones, no ejecución)**

| # | Ítem | Recomendación | Ancla canónica |
| --- | --- | --- | --- |
| D1 | `facial_analyzer.py` (raíz) | Salir del repo (código extranjero a las 4 capas) | KERNEL:ARCHITECTURE |
| D2 | `index.html` (raíz) | Eliminar duplicado de `skills/index.html` | KERNEL:ARCHITECTURE-L4 (SSOT de skills) |
| D3 | `Video/` (113 MB) y `Outputs/` (127 MB) en git | Política de retención externa / git LFS; `.git` hoy pesa 210 MB | KERNEL:NAMING-CONVENTION (naming de outputs, no su versionado) |
| D4 | `inventario_output/` | Eliminar duplicado de `Layer_1/data/inventario_*` | KERNEL:DOCUMENTATION-008 (Census como SSOT) |
| D5 | `.devin/skills/vantage-hyperlink-loop/` | Re-sincronizar con `skills/` o eliminar (diff verificado) | KERNEL:ARCHITECTURE-L4 "Skills Distribution — SSOT" |
| D6 | `Dashboard/archive/legacy_express_node/`, `Layer_4/archive/bak_cleanup_20260705/`, `Layer_4/archive/unidentified/` | Consolidar bajo `Archive/` raíz o eliminar (ya excluidos del scan) | MANUAL:SCRIPT-GLOSSARY-XREF (estado HUÉRFANO por exclusión de directorio) |
| D7 | Duplicados v9.14.2 (x3) en `Changelog Archivo.md` | Ejecutar `vantage-tidy-changelog` (mover, nunca borrar) | skill `vantage-tidy-changelog` (IDs `CHANGELOG:` / `CHANGELOG_ARCHIVE:`) |

### Orden de ejecución sugerido (batch único con DRY RUN global)

1. Correr `verify_versions.py --scripts` vivo → registrar gap report como línea base.
2. Ejecutar Tier A (6 movimientos `git mv` + remediación Script Library/Glosario en el mismo batch).
3. Ejecutar Tier C1–C3, C6 (retiro de artefactos) y C4 (fix `graph_layer.py` con tests).
4. Presentar Tier B2 (renombrado) + Tier D como tabla de decisión con APROBAR_WRITE por ítem.
5. Cerrar con `vversions --scripts` post-movimiento (debe reportar 80 assets: 86 − 6 de Tier A) y `vversions --sync` si el batch documenta versión nueva.

---

## Regla de cierre — cumplimiento de gobernanza

1. **Matriz Tipográfica Congelada (KERNEL:DOCUMENTATION-001)**: ninguna recomendación crea secciones `NN.N.N` ni modifica la jerarquía `## NN` / `### NN.N`. Los dos PATCH documentales propuestos (KERNEL:GATE-DECISION-007 §09.7 y KERNEL:ARCHITECTURE-L4 §04.4) son extensiones inline de nodos existentes — mismo patrón validado en los batches v9.19.2/v9.20.0 (PATCH-QUALITY-001: invisibilidad estructural, diff mínimo, IDs afectados = ninguno).
2. **Regla de Bloque Único**: todo bloque propuesto lleva ID y título en la misma línea (`### 09.7 KERNEL:GATE-DECISION-007`). No se propone ningún ID canónico nuevo, por lo que **CENSUS-SYNC Regla 1 (KERNEL:DOCUMENTATION-008) no se dispara**.
3. **Mapeo recomendación → ID canónico**: ver tablas de "IDs canónicos afectados" en Entregable 1 y columna "Ancla canónica" en Tier D. Las escrituras de datos (marcado `Archivar`) siguen siendo exclusivas de la skill vigente `vantage-tidy-opportunities-tracker` con guards de KERNEL:GATE-DECISION-010.
4. **Nada se ejecutó en esta auditoría**: todos los cambios requieren DRY RUN + `APROBAR_WRITE` (KERNEL:CONTEXT-INFRASTRUCTURE-002) o contrato PATCH con Write-Back Verification. Los movimientos Tier A son `git mv` reversibles y sin aristas de entrada (verificado).

---

## Anexos

### Anexo 1 — Grafo completo de imports intra-VANTAGE (verificado)

```
layer_1_run.py            → gate_logic, profile_fit, priority_logic
feed_processor.py         → layer_1_run, profile_fit
backfill_class_a.py       → feed_processor, layer_1_run, priority_logic
backfill_archive_fingerprint.py → feed_processor, notion_utils
dedup_opportunities.py    → notion_utils
batch_operations.py       → notion_utils
pipeline_recovery.py      → notion_utils
source_analytics.py       → notion_utils
status_report.py          → notion_utils
weekly_prompt_assembler.py→ notion_utils
generate_entity_index_v2.py → notion_utils, runtime_identity
vantage.py                → agent_api, context_layer, notion_utils, query_layer
agent_api.py              → query_layer, context_layer, notion_utils, graph_layer (lazy)
context_layer.py          → query_layer, notion_utils (lazy)
query_layer.py            → resolver_layer_v1 (lazy)
apply_hyperlinks_notion.py→ generate_census, vantage_id_rules
normalize_heading_ids.py  → vantage_id_rules
Dashboard/dashboard_validation.py → layer_1_run (Layer_1, sys.path hack)
Dashboard/dashboard_notion.py     → layer_1_run, class_b_guard (lazy)
Dashboard/layer_1_run_dash.py     → gate_logic (Layer_1, sys.path hack x3)
```

### Anexo 2 — Ejecuciones `subprocess` verificadas

```
health_check.py   → vantage.py
layer_1_run.py    → dedup_opportunities.py (Fase 6)
vdoc.py           → vsync_doc.py, git_sync.py
vsync_doc.py      → git_sync.py (auto_commit)
```

### Anexo 3 — Wrappers y atajos (capa de entrada, sin cambios propuestos)

`layer_1_pipeline.sh` (7 modos) · `layer_1_wrapper.sh` · `layer_3_mail.sh` · `git_sync_wrapper.sh` · `dashboard_start.sh` · 18 scripts Raycast.

### Anexo 4 — Referencias externas de la auditoría

- GitHub: issue #1 (CLOSED — drift KERNEL:GATE-DECISION-007/auto_archive), #2 (CLOSED — drift dedup), #3 y #4 (OPEN — gate()/terminalidad; fuera del alcance de este saneamiento, ya mapeados en `ISSUE_PROPOSALS.md`).
- Skills fuente de decisiones: `vantage-tidy-opportunities-tracker`, `vantage-sync-script-library`, `vantage-sync-script-glossary`, `vantage-tidy-changelog`, `vantage-create-bug-task`.
- Artefactos raíz relevantes: `MIGRATION_NEXT_ACTION_SELECT_V9.14.2.md` (reporte de la migración cerrada), `ISSUE_PROPOSALS.md` (issues abiertos de la auditoría previa).
