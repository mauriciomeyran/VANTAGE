# VANTAGE Layer 1 — CLI del operador

Guía en español llano. Cada comando con **cwd exacto**, flags, qué hace, output esperado y reglas de seguridad.

**Raíz del repo (esta máquina / CI):**  
`/home/user/VANTAGE`  
**Mac de Mau (típico):**  
`/Users/mauriciomeyran/Documents/03 Projects/VANTAGE`

Ajusta `REPO` abajo a tu path. En ejemplos usamos:

```bash
REPO="$(git rev-parse --show-toplevel)"   # desde cualquier subcarpeta del clone
cd "$REPO"
```

---

## 0. Reglas de seguridad (léelas primero)

| Prohibido | Por qué |
|---|---|
| `python3 …/layer_1_orchestrator.py --apply` **sin freeze** de cutover | Escribe Class B al Tracker de prod |
| Cualquier write a Notion prod **sin** `APROBAR_WRITE` (sesión Claude/MCP) | Contrato: Mau autoriza; agente no se auto-autoriza |
| Confiar en `pytest` sin path (todo el árbol `tests/`) | Hay **3 errores de colección ajenos** (`pydantic_settings`) — no son fallas del orquestador |
| Asumir que dry-run con token “no lee” | `--dry-run-live` **sí lee** prod (solo no escribe) |

| Permitido por defecto | |
|---|---|
| Suite de 5 archivos | Siempre |
| `g8` / `g9` / `g10` verifies | Offline, cero Notion |
| Orquestador `--dry-run` | Cliente **fake**, cero red |
| Pipeline sin args / `vl1` | Orquestador dry-run |
| `vl1_sync` sin `--apply` | Proxy read-only; 0 filas a sync es OK |

---

## 1. Suite de tests (5 archivos) — OBLIGATORIO

**cwd:** `$REPO`  
**venv:** preferible `$REPO/.venv` o el del sistema con deps instaladas.

```bash
cd "$REPO"
python3 -m pytest \
  tests/test_layer_1_orchestrator.py \
  tests/test_g3_parity.py \
  tests/test_tracker_flow_v3.py \
  tests/test_vl1_sync.py \
  tests/test_url_gate.py \
  -q
```

| Qué hace | Corre la batería del orquestador Tracker (G2–G10 + url_gate), sin red |
| Output esperado | `270 passed` (o el conteo vigente post-fix); exit 0 |
| **No** uses | `pytest` / `pytest tests/` a secas |

### Por qué no `pytest` en toda la raíz

Al recolectar **todo** `tests/` aparecen **3 errores ajenos conocidos** por dependencia faltante `pydantic_settings` (módulos fuera del alcance orquestador). No indican regresión de Layer 1.  
**Siempre** pasa los 5 paths de arriba.

---

## 2. Verifies offline G8 / G9 / G10

**cwd:** `$REPO`  
**Cero Notion** (solo leen disco).

### G8 — checklist §3.1 / entry points

```bash
cd "$REPO"
python3 Layer_1/scripts/g8_post_checklist.py --offline
```

| Qué hace | Comprueba `layer_1_run` archivado, orch presente, `is_mutable`, tabla G7, writers ES |
| Output esperado | `total=N pass=N fail=0` · exit 0 |

### G9 — anclas docsync mirror

```bash
cd "$REPO"
python3 Layer_1/scripts/g9_docsync_verify.py
```

| Qué hace | Busca strings mandatorios en Kernel/Manual/Aliases/Changelog/tidy/G7 |
| Output esperado | `all anchors present` · exit 0 |

### G10 — handoff de cierre

```bash
cd "$REPO"
python3 Layer_1/scripts/g10_handoff_verify.py
```

| Qué hace | Serial, frase cero Notion ×2, paths Archive, fila G10 |
| Output esperado | `handoff OK` · exit 0 |

---

## 3. Orquestador — `layer_1_orchestrator.py`

**cwd recomendado:** `$REPO/Layer_1` (así resuelve `scripts/` como en pipeline)  
o `$REPO` con `PYTHONPATH=Layer_1/scripts`.

```bash
cd "$REPO/Layer_1"
# opcional: source .venv/bin/activate
```

### 3.1 `--dry-run` (default / fake)

```bash
cd "$REPO/Layer_1"
python3 scripts/layer_1_orchestrator.py --dry-run
# equivalente práctico:
python3 scripts/layer_1_orchestrator.py
```

| Qué hace | Pipeline F0–F6 con **NotionClientFake** — cero red, cero writes |
| Output esperado | Log `DRY RUN`, summary (`writes=0`, etc.), exit 0 |
| Token | **No** requiere `NOTION_TOKEN` |

### 3.2 `--dry-run-live` (lee prod, no escribe)

```bash
cd "$REPO/Layer_1"
export NOTION_TOKEN=…   # o config/layer_1.env cargado por dotenv
python3 scripts/layer_1_orchestrator.py --dry-run-live
```

| Qué hace | Cliente real, **query** al DATA SOURCE; escrituras bloqueadas por dry-run |
| Output esperado | Summary sobre filas reales; `writes=0` |
| Token | **Obligatorio** — sin token exit 1 |
| Seguridad | Solo lectura; aún así es prod — no lo corras en CI pública con secretos |

### 3.3 `--apply` (escritura — gateado)

```bash
cd "$REPO/Layer_1"
export NOTION_TOKEN=…
python3 scripts/layer_1_orchestrator.py --apply
# opcional combinar:
python3 scripts/layer_1_orchestrator.py --apply --dedup-audit
```

| Qué hace | Writes reales vía `guarded_pages_update` + `class_b_guard` |
| Output esperado | Summary con `writes≥0`; exit 0 si sin errores fatales |
| Token | **Obligatorio** |
| **PROHIBIDO** sin | freeze de cutover (G8) + intención explícita del operador |

### 3.4 `--dedup-audit`

```bash
cd "$REPO/Layer_1"
python3 scripts/layer_1_orchestrator.py --dry-run --dedup-audit
```

| Qué hace | Tras el pipeline, F6 survivor L1>L2>L3>N/A + flag solo si `is_mutable` |
| Output esperado | Bloque `Dedup: groups=… flagged=… protected=…` |
| Con `--apply` | Puede escribir `Dedup_Flag` (Class B) en no-protegidos |

---

## 4. Pipeline shell — `layer_1_pipeline.sh` / `vl1`

**cwd al invocar:** irrelevante si pasas path absoluto; el script hace `cd` a `LAYER_1_DIR`.

```bash
# Default LAYER_1_DIR (Mac Mau):
# $HOME/Documents/03 Projects/VANTAGE/Layer_1
# Override en sandbox/CI:
export LAYER_1_DIR="$REPO/Layer_1"
```

### 4.1 Sin args = default = orquestador dry-run (= lo que hace `vl1`)

```bash
export LAYER_1_DIR="$REPO/Layer_1"
bash "$REPO/Layer_1/layer_1_pipeline.sh"
# Raycast vantage-vl1.sh → mismo default
```

| Qué hace | `python3 scripts/layer_1_orchestrator.py --dry-run` |
| Output esperado | Banner pipeline + summary orch + “Para escribir: … --apply” |
| Requiere | `.venv` bajo `LAYER_1_DIR` y `config/layer_1.env` o `.env` (el shell los chequea aunque dry-run fake no use token) |

### 4.2 Subcomandos (verificados contra el `case` del script)

| Args | Script / acción | Notas |
|---|---|---|
| `tracker` | `status_report.py` | Reporte de status |
| `analytics` | `source_analytics.py` | Fuentes / efectividad |
| `batch` | **RETIRADO** (Q-10/G6) | Solo imprime nota + **exit 0**; no corre nada. Archive: `Archive/Legacy_Scripts/batch_operations.py` |
| `recovery` | `pipeline_recovery.py` | Consistencia / checkpoints |
| `profile` | `profile_evolution.py` | Perfil / config |
| `sync` | `vl1_sync.py` | Sidecar F13b **dry-run** |
| `backfill [args…]` | `backfill_class_a.py "$@"` | Class A layer/hash; pasa flags al script |
| `feed <file> [layer]` | `feed_processor.py --file … --layer` | `file` relativo → `feeds/…`; layer default 1 |

```bash
export LAYER_1_DIR="$REPO/Layer_1"
bash "$REPO/Layer_1/layer_1_pipeline.sh" tracker
bash "$REPO/Layer_1/layer_1_pipeline.sh" analytics
bash "$REPO/Layer_1/layer_1_pipeline.sh" batch          # exit 0, retired
bash "$REPO/Layer_1/layer_1_pipeline.sh" recovery
bash "$REPO/Layer_1/layer_1_pipeline.sh" profile
bash "$REPO/Layer_1/layer_1_pipeline.sh" sync
bash "$REPO/Layer_1/layer_1_pipeline.sh" backfill --dry-run   # si el script lo soporta
bash "$REPO/Layer_1/layer_1_pipeline.sh" feed 2026-09-12_feed.json 1
```

Comando desconocido → usage + exit 1.

---

## 5. Sidecar F13b — `vl1_sync.py`

**cwd:** `$REPO/Layer_1` (o path al script).

```bash
cd "$REPO/Layer_1"
python3 scripts/vl1_sync.py              # dry-run default
python3 scripts/vl1_sync.py --dry-run    # idéntico
python3 scripts/vl1_sync.py --apply      # GATEADO: hoy NO escribe (T6) — exit con mensaje
```

| Qué hace | Reconciliación Outcome→Status; dry-run usa proxy que **intercepta** `pages.update` |
| Output esperado dry-run | checked/synced/skipped; **0 filas a escribir es OK** (Outcome vacío en prod) |
| `--apply` | Bloqueado en T6 por diseño — no ejecuta writes aunque pases el flag |
| Token | Lectura requiere token/env si no usas fixture interno |

---

## 6. IDs Notion (no intercambiables)

| Recurso | ID | Uso |
|---|---|---|
| DATA SOURCE | `442938be-fc42-828f-b72e-076818d65a5b` | `data_sources.query` (orch, vl1_sync) |
| DATABASE | `596938be-fc42-836b-aea7-814a1491bd47` | schema `/databases` |
| Bot Make (`KNOWN_BOT_IDS`) | `36e938be-fc42-81bc-a82a-00271388079d` | deteccion bot vs humano |

---

## 7. Cheatsheet mínimo diario

```bash
cd "$(git rev-parse --show-toplevel)"

# 1) Salud código
python3 -m pytest tests/test_layer_1_orchestrator.py tests/test_g3_parity.py \
  tests/test_tracker_flow_v3.py tests/test_vl1_sync.py tests/test_url_gate.py -q

# 2) Docs/gates offline
python3 Layer_1/scripts/g8_post_checklist.py --offline
python3 Layer_1/scripts/g9_docsync_verify.py
python3 Layer_1/scripts/g10_handoff_verify.py

# 3) Pipeline = vl1 dry-run
export LAYER_1_DIR="$PWD/Layer_1"
bash Layer_1/layer_1_pipeline.sh
```

**Nunca** el paso 4 en frío:

```bash
# NO sin freeze + APROBAR_WRITE / intención explícita:
# python3 Layer_1/scripts/layer_1_orchestrator.py --apply
```

---

## 8. Referencias

- Orquestador: `Layer_1/scripts/layer_1_orchestrator.py`
- Core: `Layer_1/scripts/tracker_flow.py`
- Pipeline: `Layer_1/layer_1_pipeline.sh`
- Cutover: `Layer_1/docs/G8_DEPLOYMENT_PLAN.md`
- Docsync: `Layer_1/docs/G9_DOCSYNC_PACKAGE.md`
- Handoff cierre: `handoffs/HANDOFF_G10_CIERRE_ORQUESTADOR_2026-09-12.md`
