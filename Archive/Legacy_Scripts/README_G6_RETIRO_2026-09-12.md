# G6 retiro — 2026-09-12

Movidos desde el árbol activo (cero borrado físico):

| Archivo | Origen | Motivo |
|---------|--------|--------|
| `layer_1_run.py` | `Layer_1/scripts/` | Reemplazado por `layer_1_orchestrator.py` (vl1) |
| `batch_operations.py` | `Layer_1/scripts/` | Q-10 RETIRAR (Target→Exploratorio no-op) |
| `consolidate_duplicates.py` | `Layer_1/scripts/` | Dedup unificado en orquestador F6 (`choose_survivor`) |
| `sync_status_contratado.py` | `Layer_1/scripts/` | One-shot F13 no-op verificado → archivar |
| `../Dashboard/layer_1_run_dash.py` | `Dashboard/scripts/` | Dash runner viejo; paridad Dashboard via orchestrator |

## Entry points post-G6

- `vl1` / `layer_1_pipeline.sh` (sin args) → `layer_1_orchestrator.py --dry-run`
- `vl1s` / `layer_1_pipeline.sh sync` → `vl1_sync.py` (F13b sidecar, intacto)
- Raycast `vantage-vl1.sh` → pipeline → orchestrator
- Raycast `vantage-dedup.sh` → orchestrator `--dedup-audit` (dry-run)

## Restaurar (rollback)

```bash
git mv Archive/Legacy_Scripts/layer_1_run.py Layer_1/scripts/
# + revert pipeline.sh default case
```
