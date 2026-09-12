# G8 — Plan de despliegue / cutover Tracker (orquestador v9)

**Gate:** G8 · **Fecha:** 2026-09-12 · **Rama tip pre-cutover:** ver `git log -1` al ejecutar  
**Quién escribe Notion:** Claude vía MCP con `APROBAR_WRITE` paso a paso · **Quién mergea git:** Mau  
**Quién NO toca Notion prod:** Arena/Devin (esta sesión = solo plan + scripts offline)

> **Binario G8:** existe documento paso-a-paso (comando exacto, validación, rollback) + export pre-migración + ventana de congelamiento manual + checklist post (matriz radiografía §3.1 toda ✓/~/documentada).  
> Ejecución real del cutover = sesión Claude/Mau separada. Este archivo es el runbook.

---

## 0. IDs y artefactos (no intercambiables)

| Recurso | Valor | Uso |
|---|---|---|
| **DATABASE** ID | `596938be-fc42-836b-aea7-814a1491bd47` | `/databases` API 2022-06-28 — schema props |
| **DATA SOURCE** ID | `442938be-fc42-828f-b72e-076818d65a5b` | `data_sources.query` API 2025-09-03 — filas |
| Backup CSV sha256 (ground truth §4) | `7da5210c2bda170c6b590272d0d21f70691a31a74dfaf6b1c4244c1f8b7eb071` | 24/24 filas al censo |
| Tabla G7 | `Layer_1/docs/G7_NORMALIZATION_TABLE.md` + `tracker_flow.NORMALIZATION_TABLE` | valores |
| Script valores | `Layer_1/scripts/normalize_tracker_values.py` | dry-run / `--apply` |
| Export snapshot | `Layer_1/scripts/export_tracker_snapshot.py` | pre/post JSON |
| Rollback valores | `Layer_1/scripts/rollback_schema_migration.py` | reverse map + validate |
| Checklist offline | `Layer_1/scripts/g8_post_checklist.py` | matriz §3.1 código |
| Entry live | `layer_1_orchestrator.py` via `layer_1_pipeline.sh` / `vl1` | dry-run default |
| Sidecar F13b | `vl1_sync.py` | intacto |

---

## 1. Orden canónico (F9 / B9): freeze → merge → patch

```
PASO 0  Preflight offline (esta rama ya verde G0–G7)
PASO 1  Export pre-migración (JSON+sha256)          ← lectura Notion OK
PASO 2  FREEZE manual (Mau anuncia; nadie edita Tracker)
PASO 3  Merge git a main (Mau) — código nuevo + schema viejo = ventana corta
PASO 4  Dry-run normalización valores (G7 script)   ← cero writes
PASO 5  APPLY normalización valores                 ← APROBAR_WRITE
PASO 6  Schema MCP: rename Source_Type␣ + prune opciones select
PASO 7  Smoke vl1 dry-run + checklist §3.1
PASO 8  Unfreeze + monitor 24h
PASO 9  Rollback SOLO si smoke rojo (ver §5)
```

**Prohibido:** merge sin freeze; patch schema antes de export; apply valores sin dry-run pegado; `git revert` a ciegas (recrea options duplicadas — usar rollback scripteado).

---

## 2. PASO 0 — Preflight offline (Arena/CI, cero Notion)

```bash
cd "$(git rev-parse --show-toplevel)"
git log --oneline -1
git status --short          # debe vacío en tip de entrega
git branch --show-current

# Suite G*
.venv/bin/python -m pytest \
  tests/test_layer_1_orchestrator.py \
  tests/test_g3_parity.py \
  tests/test_tracker_flow_v3.py \
  tests/test_vl1_sync.py -q

# Entry points
test ! -f Layer_1/scripts/layer_1_run.py
test -f Layer_1/scripts/layer_1_orchestrator.py
test -f Archive/Legacy_Scripts/layer_1_run.py
grep -q 'layer_1_orchestrator.py' Layer_1/layer_1_pipeline.sh

# Checklist código §3.1 (is_mutable unificado)
.venv/bin/python Layer_1/scripts/g8_post_checklist.py --offline
# esperado: exit 0, todas las celdas LIVE/TERMINAL = PROTECTED para PIPELINE
```

**Validación:** pytest verde · `g8_post_checklist --offline` exit 0 · status vacío.

---

## 3. PASO 1 — Export pre-migración

### 3.1 Comando (Claude/Mau con token lectura)

```bash
cd Layer_1
source .venv/bin/activate   # o repo .venv
export NOTION_TOKEN=…       # NUNCA pegar en chat

python3 scripts/export_tracker_snapshot.py \
  --out "data/exports/pre_cutover_$(date -u +%Y%m%dT%H%M%SZ).json" \
  --data-source-id 442938be-fc42-828f-b72e-076818d65a5b
```

### 3.2 Offline / CI (fixture)

```bash
python3 Layer_1/scripts/export_tracker_snapshot.py \
  --fixture tests/fixtures/g7_normalization_fixture.json \
  --out /tmp/g8_export_fixture.json
```

### 3.3 Validación export

- Archivo JSON lista de records API (`id` + `properties`).
- `sha256sum <export.json>` anotado en acta de cutover.
- `len(records) >= 24` (o conteo prod actual si creció).
- Columnas clave presentes: `Status`, `Next_Action`, `Gate_Decision`, `Source_Type ` y/o `Source_Type`, `Holding`.
- Copia del export **fuera del repo** (Drive/secure) además de `Layer_1/data/exports/` (gitignored si pesa).

**Rollback depende de este archivo.** Sin export = no hay PASO 5/6.

---

## 4. PASO 2 — Congelamiento manual

| Acción | Owner | Detalle |
|---|---|---|
| Anuncio | Mau | “Tracker en freeze cutover v9 — no editar filas ni schema” |
| Duración | Mau | Estimado 30–90 min (PASO 3–7) |
| Quién puede romper freeze | Solo Mau | Excepción escrita en chat |
| Pipeline | Mau | No correr `vl1 --apply` ni feed write durante freeze |
| Dashboard/MCP | Mau/Claude | Sin `notion-update-page` salvo pasos APROBAR_WRITE de este plan |
| Señal de freeze ON | | Nota en Notas de una fila sentinel **o** mensaje Slack/iMessage + timestamp en acta |
| Señal de freeze OFF | PASO 8 | Acta + “unfreeze” explícito |

**Validación freeze:** ningún `last_edited_time` humano nuevo entre export y post-checklist (comparar sample 5 page_ids).

---

## 5. PASO 3 — Merge git (Mau)

```bash
# En máquina Mau — NO Arena push a main
git fetch origin
git checkout main
git merge --ff-only <rama-entrega>   # o PR GitHub merge
git log --oneline -3
# Verificar entry:
test ! -f Layer_1/scripts/layer_1_run.py
grep orchestrator Layer_1/layer_1_pipeline.sh
```

**Ventana riesgo:** código nuevo + schema viejo (Source_Type␣, options EN). Mitigación: dual-read `SOURCE_TYPE_PROP_ALIASES` + enum legacy EN de lectura + writers ya ES (G7). No dejar esta ventana > freeze.

**Validación:** `vl1` / pipeline default dry-run arranca (puede fallar sin token — OK si el binario resuelve a orch).

---

## 6. PASO 4 — Dry-run normalización valores (G7)

```bash
cd Layer_1
python3 scripts/normalize_tracker_values.py --dry-run \
  --data-source-id 442938be-fc42-828f-b72e-076818d65a5b \
  --state-out state/g7_normalize_state_dry.json \
  | tee /tmp/g7_dryrun_$(date -u +%Y%m%dT%H%M%SZ).log
```

**Validación (pegar en acta):**

- `written=0`
- `would_write` = N reportado
- pre→post: `Follow-up`→0, `Interview prep`→0, `Re-check`→0
- `EXPIRADA` Gate → `EXPIRED`
- `Target` Status →0 (ya era 0 en censo; idempotente)
- `Holding=Investigar` → vacío; `LVMH`/`Nike Inc.` sin cambio
- `errors=0`

Si N o diffs sorpresivos → **STOP**, no PASO 5. Revisar export vs tabla G7.

---

## 7. PASO 5 — APPLY valores (Claude/Mau + APROBAR_WRITE)

```text
APROBAR_WRITE cutover-G8-PASO5 normalize_tracker_values
scope: Status/Next_Action/Gate_Decision/Holding per NORMALIZATION_TABLE
backup: <path export PASO1 sha256=…>
dry-run log: <path PASO4>
```

```bash
python3 scripts/normalize_tracker_values.py --apply \
  --data-source-id 442938be-fc42-828f-b72e-076818d65a5b \
  --state-out state/g7_normalize_state_apply.json \
  | tee /tmp/g7_apply_$(date -u +%Y%m%dT%H%M%SZ).log
```

**Validación inmediata:**

```bash
# 2ª pasada debe ser no-op
python3 scripts/normalize_tracker_values.py --dry-run \
  --state-out state/g7_normalize_state_post.json
# would_write=0
```

Sample 5 page_ids del log apply: fetch MCP/UI confirma valores ES.

---

## 8. PASO 6 — Schema vivo (Claude MCP only)

### 8.1 Rename propiedad `Source_Type ` → `Source_Type` (Q-1)

**Comando MCP (plantilla — ajustar a tool real de la sesión Claude):**

```text
APROBAR_WRITE cutover-G8-PASO6a rename-prop
database_id: 596938be-fc42-836b-aea7-814a1491bd47
from: "Source_Type "    # trailing space
to:   "Source_Type"
# Notion UI alternativa: Settings → Property → Rename (si MCP no expone rename)
```

**Lectores/escritores ya dual-key** (no requieren commit extra post-rename):

| Path | Cómo |
|---|---|
| `tracker_flow.SOURCE_TYPE_PROP_ALIASES` | `("Source_Type ", "Source_Type")` |
| `layer_1_orchestrator.py` | dual get |
| `feed_processor.py` | loop candidates |
| `class_b_guard.py` | listar **ambas** keys en CLASS_A hasta confirmar rename (ver §8.3) |
| `priority_logic.py` / `source_analytics.py` / `cross_tracker_match.py` | dual o legacy; post-rename prefer clean |

**Validación:** query 1 fila → propiedad visible `Source_Type` sin espacio; código dual-read sigue OK.

### 8.2 Prune opciones select legacy

| Propiedad | Quitar opciones (post-migración valores) | Dejar |
|---|---|---|
| `Next_Action` | `Follow-up`, `Interview prep`, `Re-check`, `Ninguna`, `Expirada` (como NA) | 9 canónicos ES G7 |
| `Status` | `Target`, `Archivar` (opción), `REVIEW_NEEDED` (si existía como Status) | 12 enum `Status` |
| `Gate_Decision` | `EXPIRADA` si aparece como option | 6 enum `GateDecision` |
| `Holding` | n/a (rich_text) | — |

**MCP/UI:** eliminar option solo si conteo de filas con ese valor = 0 (re-query). Si >0 → re-correr PASO 5.

```text
APROBAR_WRITE cutover-G8-PASO6b prune-options
props: Next_Action, Status, Gate_Decision
remove: <lista arriba tras conteo 0>
```

### 8.3 class_b_guard post-rename

Tras confirmar rename en schema:

```python
# CLASS_A_FIELDS: reemplazar "Source_Type " por "Source_Type"
# o mantener ambas una release (fail-open lectura).
```

Commit docs/código menor = G9 docsync batch si no se hace aquí.

---

## 9. PASO 7 — Smoke + checklist radiografía §3.1

### 9.1 Smoke pipeline

```bash
# dry-run orquestador (fake o token read-only)
cd Layer_1
python3 scripts/layer_1_orchestrator.py --dry-run
# o: bash layer_1_pipeline.sh   # default orch dry-run

python3 scripts/vl1_sync.py --dry-run   # F13b sidecar intacto
```

**Validación:** exit 0 · writes=0 · summary sin traceback.

### 9.2 Matriz §3.1 — estado post G2–G7 (código)

Fuente de verdad unificada: `tracker_flow.is_mutable` + `PROTECTED_STATUSES`  
(LIVE ∪ TERMINAL). Writers viejos (W1/W3/W4) **archivados (G6)**.

| Status (canónico) | is_mutable PIPELINE | Fases orch (F1–F6) | Notas cutover |
|---|---|---|---|
| Objetivo | ✓ mutable | compute OK | era Target; Q-2 done |
| Exploratorio | ✓ mutable | compute OK | operativo |
| Por Revisar | ✓ mutable | compute OK | era REVIEW_NEEDED Status |
| Postulando | ✗ PROTECTED | skip write | LIVE |
| Postulado | ✗ PROTECTED | skip write | LIVE + gate_logic APPLIED |
| En Proceso | ✗ PROTECTED | skip write | LIVE (cerraba hueco §3.1) |
| Negociando | ✗ PROTECTED | skip write | LIVE |
| Sin Respuesta | ✗ PROTECTED | skip write | LIVE |
| Contratado | ✗ PROTECTED_ABSOLUTE | skip write | F12 survivor first |
| Rechazado | ✗ PROTECTED | skip write | TERMINAL |
| Expirada | ✗ PROTECTED | skip write | TERMINAL |
| Retirado | ✗ PROTECTED | skip write | TERMINAL; absorbe Status=Archivar |

**Celdas radiografía vieja (W1 multi-lista):** todas **documentadas como RESUELTAS por retiro W1 + is_mutable único**, no por parche a 7 whitelists.

| Hallazgo §3.1 | Post cutover | Evidencia |
|---|---|---|
| Target archivable F3.5 | ✓ N/A | Target→Objetivo; W1 Archive; misfit solo si is_mutable |
| LIVE NAD-archive | ✓ PROTECTED | `PROTECTED_STATUSES` includes LIVE |
| Contratado re-gatea | ✓ PROTECTED_ABSOLUTE | is_mutable short-circuit |
| 7 listas distintas | ✓ una | `is_mutable` |
| W3 fork divergente | ✓ retirado | `Archive/Dashboard/layer_1_run_dash.py` |
| W4 consolidate trash | ✓ retirado | Archive + dedup orch F6 + guard |
| manual-first | ✓ | G5 `_was_touched_by_human` |
| conditional writes | ✓ | G4 `guarded_pages_update` + diff |
| Source_Type␣ | ~ → ✓ en PASO 6 | dual-read hasta rename |
| Next_Action EN | ~ → ✓ en PASO 5–6 | G7 writers ES + prune |

### 9.3 Comando checklist

```bash
python3 Layer_1/scripts/g8_post_checklist.py --offline
# con export post:
python3 Layer_1/scripts/g8_post_checklist.py \
  --export data/exports/post_cutover_….json
```

**Validación:** exit 0 · tabla impresa sin `FAIL`.

### 9.4 Export post (opcional pero recomendado)

```bash
python3 scripts/export_tracker_snapshot.py \
  --out "data/exports/post_cutover_$(date -u +%Y%m%dT%H%M%SZ).json"
sha256sum data/exports/post_cutover_*.json
```

---

## 10. PASO 8 — Unfreeze + monitor

1. Mau: “unfreeze Tracker cutover v9” + timestamp.
2. 24h: no correr `--apply` masivo; solo dry-runs.
3. Si Mau edita filas: manual-first las protege en próximo vl1.
4. G9 docsync (Kernel §§07/09, Manual, Changelog, tidy skill) en paralelo o justo después.

---

## 11. PASO 9 / §5 — Rollback

### 5.1 Cuándo

- PASO 5 apply con valores corruptos / conteos absurdos.
- PASO 6 rename rompe lectores no dual-key (no debería).
- Smoke PASO 7 rojo no trivial.

### 5.2 Rollback valores (preferido)

```bash
# Valida backup y emite plan reverso (dry-run default)
python3 Layer_1/scripts/rollback_schema_migration.py \
  --input data/exports/pre_cutover_….json \
  --dry-run

# Apply reverso (APROBAR_WRITE cutover-G8-ROLLBACK)
python3 Layer_1/scripts/rollback_schema_migration.py \
  --input data/exports/pre_cutover_….json \
  --apply
```

Reverso usa `ROLLBACK_VALUE_MAPPINGS` (inverso de G7 donde es seguro).  
**Holding** vaciado desde `Investigar`: **no se re-inventa** “Investigar” (evita re-ruido); solo restaura si backup trae valor no-placeholder.

### 5.3 Rollback schema rename

- UI Notion: renombrar `Source_Type` → `Source_Type ` **solo si** hace falta (dual-read tolera clean).
- Re-añadir options select legacy solo si writers viejos resucitan (no aplica post-G6).

### 5.4 Rollback git

```bash
# Mau only — revert del merge commit de cutover
git revert -m 1 <merge_sha>
# NO reescribir valores vía código viejo sin export
```

### 5.5 Lo que NO es rollback

- `git revert` sin export.
- Re-escribir valores eliminados como options nuevas sin prune plan.
- Trash físico de filas.

---

## 12. Matriz de comandos rápidos (cheat sheet)

| Paso | Comando | Write? | Owner |
|---|---|---|---|
| 0 | `pytest` + `g8_post_checklist.py --offline` | No | Arena/CI |
| 1 | `export_tracker_snapshot.py --out …` | No (read) | Claude/Mau |
| 2 | anuncio freeze | No | Mau |
| 3 | `git merge` main | disco | Mau |
| 4 | `normalize_tracker_values.py --dry-run` | No | Claude/Mau |
| 5 | `… --apply` + `APROBAR_WRITE` | **Sí** | Claude/Mau |
| 6a | MCP/UI rename Source_Type | **Sí schema** | Claude |
| 6b | MCP/UI prune options | **Sí schema** | Claude |
| 7 | `layer_1_orchestrator.py --dry-run` + checklist | No | Mau |
| 8 | unfreeze | No | Mau |
| 9 | `rollback_schema_migration.py` | **Sí** si apply | Claude/Mau |

---

## 13. Acta mínima de cutover (copiar al cerrar)

```
CUTOVER G8 Tracker v9
date_utc:
operator:
pre_export_path:
pre_export_sha256:
freeze_on:
merge_sha:
g7_dry_would_write:
g7_apply_written:
g7_second_pass_would_write: 0
source_type_renamed: yes/no
options_pruned: [list]
post_export_sha256:
checklist_offline: PASS
checklist_export: PASS/SKIP
unfreeze_on:
incidents:
rollback_used: no/yes→detail
```

---

## 14. Fuera de alcance G8 (siguientes gates)

| Gate | Qué |
|---|---|
| **G9** | Kernel §§07/09 + derogación GATE-DECISION-010 (Q-4), Manual, tidy skill, Changelog |
| **G10** | Handoff serial + frase cero Notion prod |

---

## 15. Conformidad

- Cero escritura a Notion de producción en la sesión que **solo** entrega este plan.
- Ejecución cutover = sesión distinta con token + APROBAR_WRITE.
- Orden freeze→merge→patch respetado (F9c).
- PR/merge git = Mau (F9a).
