# G8 — Plan de despliegue / cutover Tracker (orquestador v9)

**Gate:** G8 · **Fecha original:** 2026-09-12 · **Revisión:** 2026-09-13 (G8-R, decisión Mau vía HO-000050)
**Quién escribe Notion:** Claude vía MCP con `APROBAR_WRITE` paso a paso · **Quién mergea git:** Mau
**Quién NO toca Notion prod:** Arena/Devin (esta sesión = solo plan + scripts offline)

> **Binario G8:** existe documento paso-a-paso (comando exacto, validación, rollback) + baseline pre-reingesta + ventana de congelamiento manual + checklist post (matriz radiografía §3.1 toda ✓/~/documentada).
> Ejecución real del cutover = sesión Claude/Mau separada. Este archivo es el runbook.

---

## 0-R. NOTA DE REVISIÓN (G8-R, 2026-09-13) — LEER PRIMERO

**Qué cambió:** la versión original de este plan (2026-09-12) asumía normalización
in-place sobre 24 filas existentes en el Tracker (PASO 1 export → PASO 4 dry-run →
PASO 5 apply de `normalize_tracker_values.py`). Esa asunción quedó obsoleta:

- El Tracker fue borrado manualmente (HO-000048) y **sigue vacío** — confirmado por
  consulta directa `SELECT COUNT(*)` = **0 filas** (2026-09-13, sesión CLAUDE/MM).
- La reingesta vía `feed_processor.py` planeada tras el borrado **nunca se ejecutó**.
- Decisión de Mau (opción A, 2026-09-13): **reescribir este plan para reflejar
  delete+reingest como el camino real**, en vez de forzar la ficción de "24 filas
  a normalizar" contra una tabla vacía.

**Por qué esto simplifica el cutover:** `feed_processor.py` y `layer_1_orchestrator.py`
en su versión actual (post G6–G10, verificada contra el tip real `caf50b8` de
`arena/01a097ad-vantage`, 250 tests passed) **ya escriben vocabulario canónico ES
nativamente** — `Status.OBJETIVO` / `Status.POR_REVISAR` vía enum, nunca el string
legacy `"Target"`. Esto significa que una reingesta limpia sobre Tracker vacío
**no produce valores legacy que migrar**. El script `normalize_tracker_values.py`
(G7) pasa de ser un paso obligatorio a una **red de seguridad opcional**, útil solo
si aparecieran filas con vocabulario legacy por alguna vía distinta a estos writers
(ej. entrada manual, import externo).

**Qué NO cambió:**
- El rename de propiedad `Source_Type ` → `Source_Type` (Q-1) sigue siendo trabajo
  de schema vivo vía MCP — independiente de si hay 0 o 24 filas.
- El prune de opciones select legacy sigue aplicando — de hecho es **más simple**
  ahora: con 0 filas, el conteo "¿algún row usa este valor?" es trivialmente 0
  para todo el vocabulario legacy, sin necesidad de re-query post-apply.
- Freeze → merge → patch como orden de precedencia sigue vigente (F9c).

**Prerequisito bloqueante para PASO 4-R (Reingesta):** el JSON
`consolidated_results_from_tracker.json`, referenciado en HO-000048 S2.1/S2.2 y
HO-000049 S2.8 como "validado y disponible en outputs de sesiones previas", **no
está en el repo clonado** (`git log -1` = `07e1519` en `main`, sin ese archivo en
el árbol). Mau debe volver a adjuntarlo o confirmar su ubicación antes de correr
PASO 4-R. Sin ese archivo, la reingesta no tiene fuente de datos.

---

## 1. Orden canónico revisado (G8-R): freeze → merge → reingesta → patch

```
PASO 0    Preflight offline (esta rama ya verde G0–G10, 250 tests)
PASO 1-R  Baseline pre-reingesta (Tracker vacío, documentar estado)   ← lectura Notion OK
PASO 2    FREEZE manual (Mau anuncia; nadie edita Tracker)
PASO 3    Merge git a main (Mau) — código nuevo ya en main o por mergear
PASO 4-R  Reingesta limpia (feed_processor.py sobre JSON consolidado) ← writes canónicos ES nativos
PASO 5-R  Verificación post-reingesta (0 valores legacy esperado)     ← cero normalize necesario
PASO 6    Schema MCP: rename Source_Type␣ + prune opciones select    ← trivial con 0 legacy rows
PASO 7    Smoke vl1 dry-run + checklist §3.1
PASO 8    Unfreeze + monitor 24h
PASO 9    Rollback SOLO si smoke rojo (ver §5) — ahora es re-vaciar + re-intentar reingesta, no revertir valores
```

**Prohibido:** merge sin freeze; patch schema antes de baseline; reingesta sin
confirmar fuente JSON íntegra; `git revert` a ciegas (recrea options duplicadas —
usar rollback scripteado).

**PASO 4/5 originales (`normalize_tracker_values.py --dry-run`/`--apply`) pasan a
OPCIONALES** — ver §6-R. Se conservan documentados por si en el futuro entra data
por una vía que no sea `feed_processor.py`/`layer_1_orchestrator.py`.

---

## 2. PASO 0 — Preflight offline (Arena/CI, cero Notion)

```bash
cd "$(git rev-parse --show-toplevel)"
git log --oneline -1
git status --short          # debe vacío en tip de entrega
git branch --show-current

# Suite G* (250 tests confirmados en sesión 2026-09-13 sobre caf50b8)
python3 -m pytest \
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
python3 Layer_1/scripts/g8_post_checklist.py --offline
# esperado: exit 0, 37/37 PASS (confirmado 2026-09-13)
```

**Validación:** pytest verde (250 passed) · `g8_post_checklist --offline` 37/37 PASS · status vacío.

**Nota de dependencias:** `test_g3_parity.py` carga `Archive/Legacy_Scripts/layer_1_run.py`
por path, que importa `httpx` directo — no declarado en `Layer_1/requirements.txt`.
Instalar `httpx` explícitamente además de `pip install -r Layer_1/requirements.txt`
o el collection de pytest falla antes de correr un solo test.

---

## 3-R. PASO 1-R — Baseline pre-reingesta (reemplaza export de 24 filas)

Ya no hay 24 filas que exportar como backup — el objetivo de este paso cambia de
"backup para rollback" a "evidencia documentada de que el Tracker está vacío antes
de reingestar", para que cualquier discrepancia post-reingesta sea auditable.

### 3-R.1 Comando (Claude/Mau con token lectura)

```bash
cd Layer_1
source .venv/bin/activate
export NOTION_TOKEN=…       # NUNCA pegar en chat

python3 scripts/export_tracker_snapshot.py \
  --out "data/exports/baseline_pre_reingesta_$(date -u +%Y%m%dT%H%M%SZ).json" \
  --data-source-id 442938be-fc42-828f-b72e-076818d65a5b
```

### 3-R.2 Validación baseline

- `n_records == 0` (confirmado por consulta directa SQL el 2026-09-13; si el
  comando devuelve `n_records > 0`, **detener** — alguien reingestó o el
  supuesto de Tracker vacío ya no es válido, re-evaluar plan).
- `sha256sum` del baseline anotado en acta, aunque sea un JSON casi vacío —
  sirve como timestamp verificable de "así estaba antes de la reingesta".

**A diferencia del plan original, este archivo NO es la fuente de rollback** — con
0 filas no hay nada que restaurar hacia atrás; el "rollback" real de esta versión
del plan es re-vaciar filas recién creadas por la reingesta si algo sale mal (ver §11-R).

---

## 4. PASO 2 — Congelamiento manual

| Acción | Owner | Detalle |
|---|---|---|
| Anuncio | Mau | "Tracker en freeze cutover v9 (reingesta) — no editar filas ni schema" |
| Duración | Mau | Estimado 30–90 min (PASO 3–7) |
| Quién puede romper freeze | Solo Mau | Excepción escrita en chat |
| Pipeline | Mau | No correr `vl1 --apply` fuera de PASO 4-R durante freeze |
| Dashboard/MCP | Mau/Claude | Sin `notion-update-page` salvo pasos APROBAR_WRITE de este plan |
| Señal de freeze ON | | Nota en Notas de una fila sentinel **o** mensaje Slack/iMessage + timestamp en acta |
| Señal de freeze OFF | PASO 8 | Acta + "unfreeze" explícito |

**Validación freeze:** ningún `last_edited_time` humano nuevo entre baseline y post-checklist en filas creadas por la reingesta.

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

**Nota (2026-09-13):** al momento de esta revisión, `main` está en `07e1519` y
`arena/01a097ad-vantage` en `caf50b8` con el código G0–G10 completo — el merge
descrito aquí sigue pendiente de ejecución por Mau. Verificar `git log -1` en el
momento real del cutover, no asumir que sigue siendo el mismo tip.

**Ventana riesgo:** con Tracker vacío, la ventana "código nuevo + schema viejo"
(Source_Type␣, options EN) es de **impacto mínimo** — no hay filas legacy que el
código nuevo pueda malinterpretar. El riesgo real de esta ventana pasa a ser que
alguien reingeste con el pipeline viejo antes del merge (por eso el freeze cubre
también el PASO 4-R, no solo edición manual).

**Validación:** `vl1` / pipeline default dry-run arranca (puede fallar sin token — OK si el binario resuelve a orch).

---

## 6-R. PASO 4-R — Reingesta limpia (reemplaza normalización de valores)

### 6-R.1 Prerequisito

Confirmar ubicación y sha256 de `consolidated_results_from_tracker.json` (o el
nombre que tenga la fuente validada). **No está en el repo** — Mau debe adjuntarlo
o indicar su ruta local antes de este paso.

### 6-R.2 Comando

```bash
cd Layer_1
source .venv/bin/activate
export NOTION_TOKEN=…

# Dry-run primero — SIEMPRE
python3 scripts/feed_processor.py \
  --input /ruta/a/consolidated_results_from_tracker.json \
  --dry-run

# Revisar output: cuántos registros, qué Status asignaría (Objetivo/Por Revisar),
# cuántos pasarían URL Gate, cuántos quedarían Fetch=Bloqueado.
```

```bash
# Apply — requiere APROBAR_WRITE
python3 scripts/feed_processor.py \
  --input /ruta/a/consolidated_results_from_tracker.json \
  --apply
```

```text
APROBAR_WRITE cutover-G8R-PASO4 feed_processor_reingesta
scope: creación de filas nuevas en Tracker desde JSON consolidado
baseline: <path PASO 1-R sha256=…>
dry-run log: <adjuntar output>
```

### 6-R.3 Validación

- Conteo de filas creadas == conteo de registros en el JSON fuente (menos dedup
  esperado, si aplica).
- Sample de 5 filas: `Status` ∈ {`Objetivo`, `Por Revisar`} — nunca `Target` ni
  `REVIEW_NEEDED` crudo.
- `Source_Type` (o `Source_Type ` según qué exista en schema vivo al momento)
  poblado con `Vacante` por default salvo que el JSON traiga otro valor.
- `Holding`: placeholders (`Investigar`, `N/A`, etc.) llegan vacíos, no como
  texto — confirmar contra un par de filas con holding real vs. sin holding.

Si algo no cuadra → **STOP**, no seguir a PASO 5-R. No hay "rollback de valores"
aquí — el remedio es archivar/borrar las filas mal-creadas y re-correr con el
JSON corregido (ver §11-R).

---

## 7-R. PASO 5-R — Verificación de vocabulario post-reingesta

Reemplaza el antiguo PASO 5 (apply de `normalize_tracker_values.py`). Con
writers ya emitiendo canónico ES, este paso es una **auditoría de confirmación**,
no una migración.

```bash
python3 scripts/export_tracker_snapshot.py \
  --out "data/exports/post_reingesta_$(date -u +%Y%m%dT%H%M%SZ).json"

python3 scripts/g8_post_checklist.py \
  --export data/exports/post_reingesta_….json
```

**Validación esperada:**
- `export.legacy_next_action_zero` → PASS (0 filas con `Follow-up`/`Interview prep`/`Re-check`/`Ninguna`)
- `export.legacy_status_zero` → PASS (0 filas con `Target`/`Archivar` como Status)

**Si aparece vocabulario legacy** (posible si el JSON fuente trae datos crudos de
una exportación vieja en vez de pasar por `feed_processor.py`): correr como red
de seguridad el script G7 original, ahora ya no como paso obligatorio sino
correctivo puntual:

```bash
python3 scripts/normalize_tracker_values.py --dry-run \
  --data-source-id 442938be-fc42-828f-b72e-076818d65a5b
# revisar would_write; si >0, --apply con APROBAR_WRITE como en el plan original §7 (ver Anexo)
```

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

**Validación:** query 1 fila (de las recién reingestadas) → propiedad visible `Source_Type` sin espacio; código dual-read sigue OK.

### 8.2 Prune opciones select legacy (simplificado — 0 filas legacy garantizado)

| Propiedad | Quitar opciones | Dejar |
|---|---|---|
| `Next_Action` | `Follow-up`, `Interview prep`, `Re-check`, `Ninguna`, `Expirada` (como NA) | 9 canónicos ES G7 |
| `Status` | `Target`, `Archivar` (opción), `REVIEW_NEEDED` (si existía como Status) | 12 enum `Status` |
| `Gate_Decision` | `EXPIRADA` si aparece como option | 6 enum `GateDecision` |
| `Holding` | n/a (rich_text) | — |

**Con Tracker reingestado desde cero por writers canónicos, el conteo "¿algún row
usa este valor legacy?" es 0 por construcción** — no hace falta re-query de
verificación previa al prune como exigía el plan original (esa cautela era
necesaria contra datos legacy reales; aquí no los hay). Aun así, correr un
conteo rápido antes de borrar la opción no cuesta nada y es buena disciplina:

```text
APROBAR_WRITE cutover-G8-PASO6b prune-options
props: Next_Action, Status, Gate_Decision
remove: <lista arriba>
verificado: 0 filas con estos valores post-reingesta (PASO 5-R)
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
cd Layer_1
python3 scripts/layer_1_orchestrator.py --dry-run
python3 scripts/vl1_sync.py --dry-run   # F13b sidecar intacto
```

**Validación:** exit 0 · writes=0 (o writes esperados si el dry-run detecta filas recién reingestadas con campos Class B por calcular) · summary sin traceback.

### 9.2 Matriz §3.1 — estado post G2–G10 (código)

Fuente de verdad unificada: `tracker_flow.is_mutable` + `PROTECTED_STATUSES`
(LIVE ∪ TERMINAL). Writers viejos (W1/W3/W4) **archivados (G6)**.

| Status (canónico) | is_mutable PIPELINE | Fases orch (F1–F6) | Notas cutover |
|---|---|---|---|
| Objetivo | ✓ mutable | compute OK | valor de reingesta CLEAN |
| Exploratorio | ✓ mutable | compute OK | operativo |
| Por Revisar | ✓ mutable | compute OK | valor de reingesta REVIEW |
| Postulando | ✗ PROTECTED | skip write | LIVE |
| Postulado | ✗ PROTECTED | skip write | LIVE + gate_logic APPLIED |
| En Proceso | ✗ PROTECTED | skip write | LIVE |
| Negociando | ✗ PROTECTED | skip write | LIVE |
| Sin Respuesta | ✗ PROTECTED | skip write | LIVE |
| Contratado | ✗ PROTECTED_ABSOLUTE | skip write | F12 survivor first |
| Rechazado | ✗ PROTECTED | skip write | TERMINAL |
| Expirada | ✗ PROTECTED | skip write | TERMINAL |
| Retirado | ✗ PROTECTED | skip write | TERMINAL |

**Nota:** con Tracker recién reingestado, se espera que la mayoría de filas caiga
en Objetivo/Por Revisar/Exploratorio — los estados LIVE/TERMINAL solo aparecerán
si el JSON fuente ya traía vacantes en proceso avanzado (poco probable en una
reingesta desde discovery).

### 9.3 Comando checklist

```bash
python3 Layer_1/scripts/g8_post_checklist.py --offline
python3 Layer_1/scripts/g8_post_checklist.py \
  --export data/exports/post_reingesta_….json
```

**Validación:** exit 0 · tabla impresa sin `FAIL`.

---

## 10. PASO 8 — Unfreeze + monitor

1. Mau: "unfreeze Tracker cutover v9 (reingesta)" + timestamp.
2. 24h: no correr reingesta masiva adicional; solo dry-runs / vl1 normal.
3. Si Mau edita filas: manual-first las protege en próximo vl1.
4. G9 docsync (ya aplicado en `caf50b8` — confirmar si Notion necesita el mismo
   write-back o si esta sesión ya lo hizo) en paralelo o justo después.

---

## 11-R. PASO 9 / §5 — Rollback (reingesta, no valores)

### 11-R.1 Cuándo

- PASO 4-R apply crea filas con datos corruptos / conteo absurdo vs. JSON fuente.
- PASO 6 rename rompe lectores no dual-key (no debería).
- Smoke PASO 7 rojo no trivial.

### 11-R.2 Rollback de reingesta (reemplaza rollback de valores)

No hay "valores previos" que restaurar — el rollback es deshacer la creación:

```bash
# 1. Identificar page_ids creados por la reingesta (del log --apply de PASO 4-R)
# 2. Archivar o borrar esas páginas específicas vía MCP/UI (no hay script
#    automatizado para esto todavía — ejecutar manualmente con la lista de
#    page_ids del log, uno por uno o vía notion-create-pages inverso si existe
#    borrado en batch).
# 3. Confirmar Tracker vuelve a 0 filas (o al conteo pre-reingesta si había
#    algo más que no se tocó).
```

`rollback_schema_migration.py` (diseñado para revertir *valores* de filas
existentes) **no aplica aquí** salvo que se haya corrido PASO 5-R correctivo
(normalize --apply) — en ese caso sí sirve para esa porción específica.

### 11-R.3 Rollback schema rename

- UI Notion: renombrar `Source_Type` → `Source_Type ` **solo si** hace falta (dual-read tolera clean).
- Re-añadir options select legacy solo si writers viejos resucitan (no aplica post-G6).

### 11-R.4 Rollback git

```bash
git revert -m 1 <merge_sha>
```

### 11-R.5 Lo que NO es rollback

- `git revert` sin identificar page_ids de la reingesta.
- Dejar filas huérfanas a medio revertir sin conteo final verificado.
- Trash físico de filas fuera de Notion (usar Archivar/Retirado, no delete API si se puede evitar).

---

## 12. Matriz de comandos rápidos (cheat sheet, G8-R)

| Paso | Comando | Write? | Owner |
|---|---|---|---|
| 0 | `pytest` + `g8_post_checklist.py --offline` | No | Arena/CI |
| 1-R | `export_tracker_snapshot.py --out … ` (baseline, espera n=0) | No (read) | Claude/Mau |
| 2 | anuncio freeze | No | Mau |
| 3 | `git merge` main | disco | Mau |
| 4-R | `feed_processor.py --input … --apply` + `APROBAR_WRITE` | **Sí** | Claude/Mau |
| 5-R | `export_tracker_snapshot.py` + `g8_post_checklist.py --export` | No (read) | Claude/Mau |
| 6a | MCP/UI rename Source_Type | **Sí schema** | Claude |
| 6b | MCP/UI prune options | **Sí schema** | Claude |
| 7 | `layer_1_orchestrator.py --dry-run` + checklist | No | Mau |
| 8 | unfreeze | No | Mau |
| 9-R | archivar/borrar page_ids de reingesta fallida | **Sí** si necesario | Claude/Mau |

---

## 13-R. Acta mínima de cutover (G8-R, copiar al cerrar)

```
CUTOVER G8-R Tracker v9 (delete+reingest)
date_utc:
operator:
baseline_path (PASO 1-R):
baseline_n_records: 0 (esperado)
freeze_on:
merge_sha:
reingesta_input_source:       # ruta/nombre del JSON consolidado usado
reingesta_input_sha256:
reingesta_dry_run_n:          # cuántas filas crearía
reingesta_apply_written:      # cuántas filas creó realmente
post_reingesta_legacy_na_zero: PASS/FAIL
post_reingesta_legacy_status_zero: PASS/FAIL
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

## 14. Fuera de alcance G8-R (siguientes gates / trabajo pendiente)

| Ítem | Qué | Estado |
|---|---|---|
| **G9** | Kernel §§07/09 + derogación GATE-DECISION-010 (Q-4), Manual, tidy skill, Changelog | Ya aplicado en `caf50b8` (verificado 2026-09-13) |
| **G10** | Handoff serial + frase cero Notion prod | Ya cerrado (`ARENA-20260912-G10`) |
| **Q-11** | Excepción de una sola pasada reubicada a `manual_first_protection` | Ya aplicado (`caf50b8`), posterior a G10 |
| **Merge a main** | `main` real sigue en `07e1519`; `arena/01a097ad-vantage` en `caf50b8` | **Pendiente** — Mau ejecuta PASO 3 |
| **Localizar JSON consolidado** | Prerequisito de PASO 4-R | **Bloqueante** — Mau debe re-adjuntar o indicar ruta |

---

## 15. Conformidad

- Cero escritura a Notion de producción en la sesión que **solo** entrega/revisa este plan.
- Ejecución cutover = sesión distinta con token + APROBAR_WRITE.
- Orden freeze→merge→reingesta→patch respetado (F9c, adaptado a G8-R).
- PR/merge git = Mau (F9a).

---

## Anexo — Plan original (normalización in-place, 24 filas) — DEPRECADO

Se conserva como referencia histórica y como red de seguridad correctiva (ver
§7-R) por si en algún momento entra data con vocabulario legacy por una vía
distinta a `feed_processor.py`/`layer_1_orchestrator.py`. **No usar como plan
primario de cutover** — la decisión vigente (2026-09-13) es G8-R arriba.

El detalle completo de PASO 4/PASO 5 originales (`normalize_tracker_values.py
--dry-run` / `--apply` sobre 24 filas) vive en el historial de git de este
archivo (`git log -p Layer_1/docs/G8_DEPLOYMENT_PLAN.md`) — no se duplica aquí
para evitar dos fuentes de verdad divergentes sobre el mismo script.