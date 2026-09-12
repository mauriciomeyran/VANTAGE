# HANDOFF T6 — Sidecar reactivo `vl1s` (go-live) · 2026-09-11 (serial CLAUDE-20260911-06)

Objetivo: poner en vivo un runner THIN aditivo para el sync F13b, invocación reactiva
(igual UX que `vl1`), sin tocar el default. Cero writes a prod en T6 (código + dry-run
read-only). `--apply` explícitamente EXCLUIDO (gate futuro, cuando Outcome no esté vacío).

## 0. Base (Zero-Trust, primero)
`git log --oneline -1` + `git status --short` + `grep -c get_layer_rank
Layer_1/scripts/tracker_flow.py` (esperado ≥2: fix G3 presente) + `pytest
tests/test_tracker_flow_v3.py -q` (esperado 39 passed).
Si falta G3/G1 → ALTO, avisar a Mau (él tiene el patch combinado; no re-derivar).

## 1. Cadena viva (verificada en repo, no tocar)
`vl1` → `Raycast/vantage-vl1.sh` → `layer_1_pipeline.sh` (default, sin args) →
`python3 scripts/layer_1_run.py` (pipeline v7.5, 6 fases, writer vivo con strings
hardcodeados). `tracker_flow.py` es librería sin entry point (su `__main__` solo imprime
enums) — por eso T6 construye el runner en vez de "redirigir el alias".

## 2. Spec (4 piezas, modelo reactivo — sin cron)
1. **`Layer_1/scripts/vl1_sync.py`**: argparse `--dry-run` (default) / `--apply`;
   reutiliza `.venv` + `.env`/`config/layer_1.env`; `Client(auth=NOTION_TOKEN)`;
   DATA SOURCE ID `442938be-fc42-828f-b72e-076818d65a5b` desde env (NO database ID);
   llama `run_outcome_status_sync(client, ds_id)`; exit 0/1; log stdout.
2. **Case `sync`** en `layer_1_pipeline.sh` (patrón `run_module` existente).
3. **Clon Raycast `vantage-vl1sync.sh`** (patrón notificaciones Hero/Basso de vantage-vl1.sh).
4. **Alias `vl1s`** (instrucción para Mau, no archivo).
Registro doc: al cerrar, `vl1_sync.py` entra al ciclo XREF (MANUAL:SCRIPT-GLOSSARY-XREF):
`vversions --new-scripts` → skill `vantage-sync-script-glossary` → DRY RUN → APROBAR_WRITE.

## 3. Tests + aceptación
3 tests nuevos (args default-dry-run; dry-run-no-write con `NotionClientFake`;
apply-gate respeta flag) → objetivo **42 passed** (39+3). Smoke vivo: `vl1s --dry-run`
esperado **0 filas** (consistente con T5). `vl1` viejo verificado corriendo igual después.

## 4. Fuera de alcance / prohibido
Reemplazo del default `vl1`, migración de fases, cron/launchd, `--apply` real,
cualquier write a Notion prod, auto-remediación de glosario (matriz XREF: solo señales).

## 5. Protocolo (2 muertes por tokens previas)
Lotes chicos, entregables PRIMERO (diff + pytest tail), prosa al final. ALTO tras smoke
seco → esperar declaración sidecar-live de Mau+Arena. Base trabajo: repo main limpio.