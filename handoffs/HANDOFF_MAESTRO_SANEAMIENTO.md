# HANDOFF MAESTRO — Saneamiento estructural VANTAGE (secuencia única)

**Versión:** 2.0 (consolida y reemplaza `HANDOFF_TERMINAL_GAP_REPORT.md` y `HANDOFF_CLAUDE_NOTION_SIDE.md` — eliminados)
**Fecha:** 2026-08-13
**Fuente de verdad:** `AUDIT_SANEAMIENTO_ESTRUCTURAL.md` (repo root)
**Regla de oro:** toda escritura (Notion o disco) pasa por DRY RUN + variante válida de `APROBAR_WRITE` (nunca "Ok"/"Go"/"yes"). Nada se borra — se mueve o se marca.

---

## Estado de verdad (integrando el reporte de verificación de Claude, 2026-08-13)

| # | Punto | Estado anterior | Estado real confirmado | Acción en este handoff |
| --- | --- | --- | --- | --- |
| V1 | `vantage-housekeeping-archive` | Propuesta de auditoría | 🔴 PENDING — no existía en disco ni Notion | **✅ Creada en disco** por el sandbox (`skills/vantage-housekeeping-archive.md` + `.skill` + `index.json` en sync). Falta solo el **alta en SKILL LIBRARY (Notion)** → tarea C2 |
| V2 | Duplicados v9.14.2 en Archivo Changelog | Pendiente señalado por v9.14.5 | 🔴 ACTIVO — **3 bloques** distintos presentes en vivo | Dedupe vía `vantage-tidy-changelog` → tarea C5 |
| V3 | Patch Kernel "máx. 5 correos" → 10 | Ancla sin localizar | ✅ Ancla localizada: §04.3 `KERNEL:ARCHITECTURE-L3`, párrafo "Campos inmutables". **Ancla #2 adicional en Manual** (ver tabla de PATCHs) | Incluido en batch de PATCHs → tarea C4 |
| V4 | ID del Archivo Changelog | Único en docs | 🔴 **Drift nuevo detectado por este handoff**: `resolver_registry_v2.json` tiene DOS entradas — `CHANGELOG_ARCHIVE=39d938be-fc42-801c-94f6-f11bfe803633` y `CHANGELOG_ARCHIVO=3ba938be-fc42-8011-8947-fb4fa5d1f63f`. Claude fetché en vivo el segundo y ahí vio los 3 bloques | Usar el **ID vivo verificado** (3ba938be…) en C5; reportar el drift en el cierre (no corregir silenciosamente) |

---

## ✅ ESTADO POST-EJECUCIÓN F1 (verificado contra `origin/main`, 2026-08-14)

Las tareas **1–9 (F0/F1, disco) están EJECUTADAS y verificadas** desde el sandbox contra el remoto. Evidencia: commit merge `3eeb3b8` en `main` (parents `ababcde` + `257fae5`), que integra el trabajo de arena + los movimientos del operador:

| Verificación | Resultado |
| --- | --- |
| Merge arena → main | ✅ Integrado (`3eeb3b8 "housekeeping: sync arena + Tier A/B2/C"`) |
| Tier A (6 movimientos) | ✅ 6/6 en `Archive/Legacy_Scripts/` |
| Tier B2 (renombrado) | ✅ `DEPRECATED_apply_hyperlinks.py` + `DEPRECATED_vsync_doc_fast.py` (prefijo estándar verificado en disco) |
| Tier C C1–C3, C6, B5 | ✅ Retirados (`.bak*`, patches, dumps, manifest backup, `.save`) — ~10,000 líneas fuera del árbol |
| **Conteo de assets activos** | ✅ **80** (simulación fiel de `scan_committed_assets` sobre `origin/main`: L1 46 · L3 2 · L4 5 · Dashboard 9 · Raycast 18). El "79" reportado no corresponde al estado final verificado — re-correr `vversions --scripts` para confirmar en vivo |
| `git_sync.py` | ✅ **INTACTO** en `Layer_4/scripts/` |
| Skills | ✅ 28 `.skill` en disco, `index.json` en sync 28/28 |
| C4 (stubs graph/backlinks) | ⏳ Pendiente por diseño — gateado tras fix Devin D1 |
| C5 (docs duplicadas en `scripts/`) | ⏳ Pendiente — decisión de solapamiento con §22 |
| Tier D (fuera de pipeline) | ⏳ Pendiente — decisiones del operador |

**⚠️ Corrección crítica al reporte de cierre (00:27–00:29 CST):** el huérfano de Notion `git_sync.py` **NO es un script retirado** — nunca estuvo en Tier A/B2 y sigue activo en `Layer_4/scripts/` (es el motor de `vgit`/`vdoc`). Su aparición en "EN NOTION COMO 'Activo' PERO NO EN DISCO" es un **mismatch de título o fila corrupta (auto-link `http://`)** en Script Library. **Prohibido marcarlo `Deprecado`** — la tarea 10 debe investigar esa fila. Los otros dos huérfanos (`extract_score_distribution.py`, `patch_vsync_doc.py`) sí son los esperados post-movimiento → remediar a `Deprecado`/`Archivar`.

**Consecuencia:** el "100% concluido" aplica solo a la **mitad disco (F0/F1)**. Toda la **mitad Notion (F2, tareas 10–15 y 21–23)** y la **mitad código (F3, Devin 16–20)** siguen pendientes. La tabla de abajo se recorre desde la tarea 10.

---

## TABLA MAESTRA — secuencia única de ejecución

| # | Fase | Tarea | Responsable | Script / Skill / Atajo | Salida esperada | Gate | Depende de |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | F0 | ✅ Sincronizar repo (EJECUTADO — merge 3eeb3b8 en main) | Operador | Terminal: `git fetch origin && git merge origin/arena/019ffb49-vantage` | Merge limpio | — | — |
| 2 | F0 | ✅ Preflight (EJECUTADO) | Operador | Terminal (`test -f`, `grep -c`) | "ENV OK · VENV OK" | — | 1 |
| 3 | F0 | ✅ Baseline Scripts (EJECUTADO — guardar .txt como input de tarea 10) | Operador | `vversions --scripts` · Raycast: **VANTAGE Scripts Gap Report** | `vantage_scripts_gap_YYYYMMDD.txt` | — | 2 |
| 4 | F0 | ✅ Baseline Skills (EJECUTADO) | Operador | `vversions --skills` (no hay atajo Raycast; Terminal) | `vantage_skills_gap_YYYYMMDD.txt` | — | 2 |
| 5 | F1 | ✅ Tier A 6/6 (EJECUTADO — verificado en origin/main) | Operador | Terminal (bloque de comandos §C1) | `git status` con 6 renames | APROBAR_WRITE (confirmación) | 3 |
| 6 | F1 | ✅ Tier B2 2/2 (EJECUTADO — prefijo verificado en disco) | Operador | Terminal (§C1) | 2 renames | APROBAR_WRITE | 5 |
| 7 | F1 | ✅ Tier C C1–C3/C6/B5 (EJECUTADO — ~10,000 líneas retiradas) | Operador | Terminal: `git rm` (§C2) | Archivos fuera del árbol | APROBAR_WRITE | 5 |
| 8 | F1 | ✅ Verificación post-movimiento (EJECUTADA — 80 assets, verificado por simulación en sandbox) | Operador | `vversions --scripts` (espera **80**) + `vversions --new-scripts` (espera **0 gaps**) | 2 reportes | — | 5 |
| 9 | F1 | ✅ Commit + push (EJECUTADO — 3eeb3b8 en main) | Operador | `vgit` (o git add/commit/push) | Push OK; `index.json` regenerado por git_sync si hay .skill nuevos | — | 8 |
| 10 | F2 | Consumir gap reports → remediación SCRIPT LIBRARY | Claude (MCP) | Skill `vantage-sync-script-library` | DRY RUN: tabla de filas a actualizar | APROBAR_WRITE | 3, 4, 8 |
| 11 | F2 | Alta de `vantage-housekeeping-archive` en SKILL LIBRARY + sync | Claude (MCP) | Skill `vantage-sync-skill-library` + gap de `--skills` | DRY RUN: fila nueva (Skill/Capa/Estado) | APROBAR_WRITE | 4, 9 |
| 12 | F2 | Batch limpieza auto-link `http://` (~70 filas) | Claude (MCP) | Operación aparte (fuera de alcance de la skill — DRY RUN propio) | DRY RUN: tabla fila→valor limpio | APROBAR_WRITE | 10 |
| 13 | F2 | Batch de PATCHs documentales (4 inline, tabla §P1) | Claude (MCP) | Skill `vantage-documentacion-transversal-propuesta` | DRY RUN con ANTES/DESPUÉS por ancla | APROBAR_WRITE | 10 |
| 14 | F2 | Dedupe Archivo Changelog: 3× v9.14.2 + validar v9.14.3 | Claude (MCP) | Skill `vantage-tidy-changelog` (ID vivo 3ba938be…) | DRY RUN: tabla de bloques a consolidar | APROBAR_WRITE | 10 |
| 15 | F2 | Revisión cruzada de los DRY RUN 13 y 14 (advisory, no bloqueante) | Grok + Mistral | Paste-review (§G1, §M1) | Veredictos PASS/FAIL por criterio | — | 13, 14 (DRY RUNs) |
| 16 | F3 | Fix `graph_layer.py`: leer de `Layer_1/data/` (Hallazgo F2) + tests | Devin | Repo: rama `arena/019ffb49-vantage` | Tests PASS + PR | PR review | 9 |
| 17 | F3 | `status_report.py --archive-queue` + tests (Entregable 1 Fase 2) | Devin | Repo (misma rama) | Tests PASS + PR | PR review | 9 |
| 18 | F3 | Hardening Dashboard: `sys.path` hardcodeado → `LAYER_1_DIR` (Hallazgo F1, 4 puntos) | Devin | Repo | PR + smoke | PR review | 9 |
| 19 | F3 | `.gitignore`: ampliar a `*.bak*` | Devin u Operador | Repo | PR o commit directo | — | 9 |
| 20 | F3 | Retirar stubs `graph_v2.json`/`backlinks_v2.json` de `scripts/` (Tier C4) | Devin | Repo | Solo tras merge de #16 | PR review | 16 |
| 21 | F4 | Cierre documental: entrada Change Log `[AUDIT]` + cierre pendiente v9.17.1 + drift V4 reportado | Claude (MCP) | `vantage-create-bug-task` si hay tickets + draft de entrada | Draft → APROBAR_WRITE | APROBAR_WRITE | 10–14 |
| 22 | F4 | Gate absoluto: `vversions --sync` con `[VEREDICTO FINAL] PASS` | Operador + Claude | Terminal (operador pega output) | PASS | — | 21 |
| 23 | F4 | Ledger CLOSED + resumen Regla 4 (CENSUS-SYNC) | Claude (MCP) | `vantage-session-close` | Fila Ledger `Status: CLOSED` | — | 22 |

**Paralelismo permitido:** F3 (Devin, 16–20) corre en paralelo con F2 (Claude, 10–15) — dominios disjuntos (código vs. Notion). Grok/Mistral (15) revisan mientras el operador decide APROBAR_WRITE.

---

## Contratos de sesión por agente

### §OP — Contrato OPERADOR (Terminal, ~15 min, una sola sentada)

**Rol:** único autor de APROBAR_WRITE y de movimientos de disco. **Nunca pega `NOTION_TOKEN` en un chat.**

```bash
# §C0 — Sincronizar artefactos del sandbox (tarea 1)
cd "$HOME/Documents/03 Projects/VANTAGE"
git fetch origin
git merge origin/arena/019ffb49-vantage   # trae skills/handoffs/audit del sandbox

# §C0.1 — Preflight (tarea 2)
cd Layer_1
test -f config/layer_1.env && echo "ENV OK"
grep -c "NOTION_TOKEN" config/layer_1.env   # ≥1 sin mostrar valor
test -d .venv && echo "VENV OK"

# §C0.2 — Baseline (tareas 3–4)
cd Layer_1/scripts && source ../.venv/bin/activate
python3 verify_versions.py --scripts | tee "$HOME/vantage_scripts_gap_$(date +%Y%m%d).txt"
python3 verify_versions.py --skills  | tee "$HOME/vantage_skills_gap_$(date +%Y%m%d).txt"

# §C1 — Tier A + B2 (tareas 5–6)
cd "$HOME/Documents/03 Projects/VANTAGE"
git mv Layer_1/scripts/backfill_next_action_select.py Archive/Legacy_Scripts/
git mv Layer_1/scripts/toggle_changelog_archive.py  Archive/Legacy_Scripts/
git mv Layer_1/scripts/backfill_archive_fingerprint.py Archive/Legacy_Scripts/
git mv Layer_4/scripts/patch_vsync_doc.py Archive/Legacy_Scripts/
git mv Layer_4/scripts/patch_vsync_doc.STATUS.md Archive/Legacy_Scripts/
git mv Layer_1/tools/patch_new_scripts.py Archive/Legacy_Scripts/
git mv Layer_1/scripts/extract_score_distribution.py Archive/Legacy_Scripts/
git mv "Archive/Legacy_Scripts/DEPRECADO apply_hyperlinks.py" Archive/Legacy_Scripts/DEPRECATED_apply_hyperlinks.py
git mv "Archive/Legacy_Scripts/DEPRECADO vsync_doc_fast.py" Archive/Legacy_Scripts/DEPRECATED_vsync_doc_fast.py

# §C2 — Tier C (tarea 7, gateada)
git rm Layer_1/scripts/feed_processor.py.bak2 Layer_1/scripts/feed_processor.py.bak_prioridad \
       Layer_1/scripts/generate_census.py.bak_census010 \
       Layer_1/scripts/dedup_fix_verified.patch Layer_1/scripts/fix_terminal_protection_layer_1_run.patch \
       Layer_1/scripts/bug_tracker_full.json Layer_1/scripts/task_tracker_full.json \
       Layer_1/scripts/out/schema_full.json Layer_1/scripts/out/schema_properties.json \
       "Documentación/ACTIVE/.vsync_manifest.json.backup" \
       Archive/Legacy_Scripts/dump_trackers.py.save

# §C3 — Verificación + commit (tareas 8–9)
cd Layer_1/scripts && source ../.venv/bin/activate
python3 verify_versions.py --scripts      # esperado: 80 assets
python3 verify_versions.py --new-scripts  # esperado: 0 gaps
cd "$HOME/Documents/03 Projects/VANTAGE" && git status --short
vgit    # o: git add -A && git commit -m "housekeeping: Tier A/B2/C (auditoría 2026-08-13)" && git push
```

**Entrega al final:** pegar los 2 `.txt` de baseline + 2 reportes post-movimiento en el chat de Claude → es su input formal. Confirmar en chat qué ejecutaste ("Tier A ✅ / Tier C ✅ / SKIP…").

---

### §CL — Contrato CLAUDE (MCP Notion — el más largo)

**Apertura:** `vantage-session-open` (Ledger OPEN → Health → Pending → Snapshot → READY). **Cierre:** `vantage-session-close` (tareas 21–23). **Anuncios:** apertura/cierre por skill (`KERNEL:SKILL-ANNOUNCE-CONVENTION`).

**C1 (tarea 10) — Script Library.** Input: 2 gap reports (baseline + post-movimiento). Con `vantage-sync-script-library`:
- Filas de los 6 zombies Tier A → `Estado=Deprecado`, `Acción=Archivar` (nunca eliminar filas).
- Huérfanos esperados `auto_archive.py`, `vsync_doc_fast.py`, `vantage-assign.sh`, `apply_hyperlinks.py` → deprecar o **update de título** (`apply_hyperlinks.py` → `apply_hyperlinks_notion.py`, mismo script renombrado — preguntar al operador primero).
- Clasificar todo lo nuevo según la tabla de la skill. DRY RUN → APROBAR_WRITE → Write-Back Verification con fetch real.

**C2 (tarea 11) — Skill Library.** Input: gap de `--skills` (28 `.skill` en disco al momento del cierre F1 — verificar conteo vivo con `ls skills/*.skill | wc -l`). Alta de `vantage-housekeeping-archive` (Ruta `skills/vantage-housekeeping-archive.skill`, Estado `Activo`) + cualquier otro gap. DRY RUN + APROBAR_WRITE.

**C3 (tarea 12) — Batch `http://`.** ~70 filas con `Script`/`Ruta` corrompidos. DRY RUN propio: tabla `Fila | valor corrupto | valor limpio`. Escribir como texto plano. ~70 updates — ofrecer lotes.

**C4 (tarea 13) — PATCHs documentales (un solo DRY RUN, 4 parches inline):**

| # | Destino | Ancla exacta (ANTES → DESPUÉS) | Restricción |
| --- | --- | --- | --- |
| P1 | Kernel §04.3 `KERNEL:ARCHITECTURE-L3` | `máx. 5 correos por corrida` → `máx. 10 correos por corrida` (párrafo "Campos inmutables"; código real: `GROQ_MAX_EMAILS_PER_RUN=10`, `layer_3_mail.py` L40) | Inline, sin ID nuevo |
| P2 | Manual (sección vl3) | `debe procesar hasta 5 correos` → `debe procesar hasta 10 correos` + marcar la nota de discrepancia del env-vars table y el hallazgo #7 de XREF como RESUELTO (batch saneamiento 2026-08-13) | Inline |
| P3 | Kernel §09.7 `KERNEL:GATE-DECISION-007` | Añadir al párrafo del mecanismo vigente: referencia a `vantage-housekeeping-archive` (consolidación del ciclo) y a `status_report.py --archive-queue` (reporte, PENDIENTE de código) | Inline dentro del bloque existente, sin retitular |
| P4 | Kernel §04.4 `KERNEL:ARCHITECTURE-L4` | (a) "riesgo conocido": quitar referencia colgante a `vsync_doc_fast.py` (deprecado) — citar solo `vsync_doc.py`; (b) skills "(actualmente 12)" → "(actualmente N)" con N = `ls skills/*.skill | wc -l` en vivo (28 al cierre F1) | Inline |

Validar contra PATCH-QUALITY-001 (invisibilidad estructural, continuidad de voz, diff mínimo, sin IDs nuevos). Decisión pendiente de operador: **`KERNEL:SKILL-ANNOUNCE-CONVENTION`** → Opción A (reanclar referencias al nodo del Manual que ya describe la convención; sin alta de ID, sin Census) recomendada; Opción B (alta formal) solo si el operador la elige — dispara CENSUS-SYNC R1.

**C5 (tarea 14) — Dedupe Archivo Changelog.** Con `vantage-tidy-changelog`, sobre el **ID vivo verificado** `3ba938be-fc42-8011-8947-fb4fa5d1f63f` (el que Claude ya fetché y contiene los 3 bloques): consolidar los 3 bloques v9.14.2 (conservar el contenido del bloque "Consolidado", anotar los otros 2 como duplicados movidos) + validar v9.14.3 (posible x2). Regla de oro: **mover, nunca borrar**. DRY RUN → APROBAR_WRITE → fetch de verificación.

**C6 (tareas 21–23) — Cierre.** Entrada Change Log `[AUDIT]`: Tier A/B2/C ejecutados, remediación Script/Skill Library, batch http://, PATCHs P1–P4, dedupe C5, **cierre del pendiente v9.17.1** (auto_archive.py → CONSERVAR como referencia histórica), drift V4 reportado (no corregido). Gate absoluto: pedir output de `vversions --sync` con PASS. Ledger CLOSED con resumen Regla 4.

**Golden rules Claude:** estados Script Library solo `{Activo, En desarrollo, Deprecado}` · nunca borrar filas/entradas · Write-Back Verification con fetch (no "ya se escribió") · nunca Class B por MCP (`class_b_guard.py`, KERNEL:GATE-DECISION-003) · Matriz Tipográfica `## NN`/`### NN.N` únicamente · Regla de Bloque Único.

---

### §DV — Contrato DEVIN (código, paralelo a Claude)

**Rama:** partir de `arena/019ffb49-vantage`; PRs hacia la misma rama (no push directo a main). **Prohibido:** tocar Notion, `Documentación/ACTIVE/*`, o los 6 zombies movidos. **Obligatorio:** tests por cambio (patrón `Layer_1/tests/test_*.py`).

| # | Ticket a crear (vía Claude/Bug Tracker) | Cambio | Aceptación |
| --- | --- | --- | --- |
| D1 | F2 graph_layer | `graph_layer.py`: cargar `Layer_1/data/graph_v2.json` y `backlinks_v2.json` (ruta `_DIR.parent/"data"`) en vez de los stubs de `scripts/` | Tests: `graph_stats`/`get_backlinks` con fixture de data; PR |
| D2 | --archive-queue | `status_report.py`: flag `--archive-queue` (tabla de `Archivar=True` agrupada por criterio con page IDs; read-only) | Tests + salida de ejemplo en PR |
| D3 | F1 sys.path | Dashboard: reemplazar los 4 `sys.path.insert(..., "~/Documents/03 Projects/VANTAGE/Layer_1/scripts")` por resolución de `LAYER_1_DIR` (env con fallback al literal) | `smoke_dashboard.py` PASS |
| D4 | .gitignore | Ampliar patrones a `*.bak*` | PR |
| D5 | C4 stubs | Tras merge de D1: `git rm` stubs `scripts/graph_v2.json` + `backlinks_v2.json` | PR |

**Cierre Devin:** resumen por PR: diffs, tests corridos (comando + resultado), nada más tocado. No cierra tickets — solo código.

---

### §G1 — Contrato GROK (review advisory, paste-based, no bloqueante)

**Input:** pegar el DRY RUN de Claude C5 (tabla de dedupe del Archivo Changelog). **Criterios:**
1. Los 3 bloques v9.14.2 quedan representados (contenido del "Consolidado" íntegro; los otros 2 anotados como duplicados, no vaciados).
2. Orden cronológico preservado; ninguna entrada eliminada (mover ≠ borrar).
3. v9.14.3 x2 validado y resuelto en el mismo batch.
4. ID destino correcto (`3ba938be-fc42-8011-8947-fb4fa5d1f63f`).

**Output:** tabla `Criterio | Veredicto (PASS/FAIL) | Evidencia (cita del DRY RUN)`. Cualquier FAIL → Claude revisa antes de pedir APROBAR_WRITE.

### §M1 — Contrato MISTRAL (review advisory, paste-based, no bloqueante)

**Input:** pegar el DRY RUN de Claude C4 (los 4 PATCHs con ANTES/DESPUÉS). **Criterios (PATCH-QUALITY-001):**
1. Matriz Tipográfica: solo `## NN`/`### NN.N`; cero `NN.N.N`.
2. Invisibilidad estructural: inline en bloques existentes, sin secciones nuevas, sin retitular.
3. Anclas exactas: cada PATCH cita el texto ANTES literal y el DESPUÉS mínimo.
4. Sin IDs canónicos nuevos (→ sin CENSUS-SYNC R1).
5. Regla de Bloque Único: ID + título en la misma línea.

**Output:** igual formato que §G1. Cualquier FAIL → Claude revisa antes de pedir APROBAR_WRITE.

---

## IDs y referencias rápidas

| Recurso | ID |
| --- | --- |
| SCRIPT LIBRARY | `ea914544-338f-485e-ac1b-7f137a5c9cee` |
| SKILL LIBRARY | `2f1938be-fc42-83c8-8972-07300201136d` |
| VANTAGE Tracker DB / Col | `596938be-fc42-836b-aea7-814a1491bd47` / `442938be-fc42-828f-b72e-076818d65a5b` |
| ARCHIVO TRACKER (no tocar) | `674696fd-94b6-464a-ac1f-64b0cc917e15` |
| Change Log / Archivo Changelog | `390938be-fc42-80e7-b429-d7d730339353` / **vivo: `3ba938be-fc42-8011-8947-fb4fa5d1f63f`** (drift V4 a reportar) |
| Kernel / Manual / Aliases (páginas) | `377938be-fc42-805e-a408-c9ae518d4fe7` / `372938be-fc42-8050-9a67-e40857d7806e` / `37c938be-fc42-80d4-b9ae-f5969830331b` |
| Artefactos del sandbox | rama `arena/019ffb49-vantage`: `skills/vantage-housekeeping-archive.md` + `.skill`, `skills/index.json` (28, en sync), `handoffs/HANDOFF_MAESTRO_SANEAMIENTO.md` |

## Check de cierre global (cuando todo esté en verde)

- [ ] `vversions --scripts` → 80 assets, 0 huérfanos críticos sin remediar
- [ ] `vversions --skills` → 28 registradas, housekeeping-archive `Activo` en Notion
- [ ] `vversions --new-scripts` → 0 gaps · `vversions --sync` → `[VEREDICTO FINAL] PASS`
- [ ] Archivo Changelog: 1 solo bloque v9.14.2 consolidado (verificar fetch en vivo)
- [ ] Kernel §04.3 dice 10 correos; §04.4 dice 28 skills y sin referencia a vsync_doc_fast
- [ ] Change Log: entrada `[AUDIT]` cerrando v9.17.1 · Ledger `CLOSED` · git limpio y pusheado
- [ ] `AUDIT_SANEAMIENTO_ESTRUCTURAL.md` actualizado con el estado final (opcional: nota de cierre)
