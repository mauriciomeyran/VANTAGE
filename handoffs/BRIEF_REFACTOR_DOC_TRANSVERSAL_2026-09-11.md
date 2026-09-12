# BRIEF — Documentación transversal del refactor Tracker · 2026-09-11

Insumo para `vantage-documentacion-transversal-propuesta` (Fase 1: mapeo de nodos, solo
lectura). NO contiene parches. Tras `PROPUESTA PRESENTADA`, el operador decide
`APROBAR_WRITE` → transición a `-implementacion` (DRY RUN → inyección → write-back).

## 1. Cambio estructural (qué pasó, fases evolutivas)

Refactor/e2e del Tracker VANTAGE verificado en 5 fases con evidencia (seriales Arena
CLAUDE-20260911-01…05). Detección→auditoría→implementación están cerradas; falta la
meta-documentación (este brief). Cero escrituras a prod en todo el ciclo.

- **T0** (`bb29edf`): 6 tests F13/F13b (Outcome→Status auto-sync + writeback + runner batch)
  + 3 minors en one-shot `sync_status_contratado.py`. Suite 36/36.
- **T1**: censo read-only (24 filas; Status 12/12 = enum; Target=0; fantasmas=0; Q-H1 resuelto
  Fetch={Accesible:22,Bloqueado:2}; layer L1=10/L3=12/N/A=2/L2=0).
- **T2**: backup CSV nativo sha256 `7da5210c…eb071`, 24/24.
- **T4**: G3 bug real TypeError en `choose_survivor` (unary minus sobre layer string) → fix
  `LAYER_SURVIVOR_PRIORITY` + `get_layer_rank` + 3 tests (39/39). Dirección operador: L1 gana
  (Active Search > Passive Intake) → L1>L2>L3>N/A. G1 enum `GateDecision` desalineado
  (REVIEW/EXPIRADA) → alineado a vivo (REVIEW_NEEDED/EXPIRED). G2 Next_Action: select-11
  confirmado, sin fix (deuda-doc: vocabulario EN del writer vs enum ES, sin single source).
- **T5**: backfill `--dry-run` = 0 filas + cross-check MCP n=0 → `--apply` no-op. Outcome 100% vacío.

## 2. Traducción operativa (qué significa corriendo)

- **Hoy corre (prod, vía `vl1`):** `layer_1_pipeline.sh` default → `layer_1_run.py` v7.5
  (6 fases, monolito). Writer vivo: strings hardcodeados (REVIEW_NEEDED, Follow-up…), no enums.
- **Lo nuevo:** `tracker_flow.py` = librería core + tests (39), sin entry point ejecutable.
  Nada programado (sin cron); modelo del operador = reactivo por alias.
- **IDs:** DATABASE `596938be-…` (/databases, API 2022-06-28, one-shot) vs DATA SOURCE
  `442938be-…` (data_sources, API 2025-09-03, tracker_flow). No intercambiables.
- **Diferidos explícitos:** runner thin + alias sidecar (T6); wiring cron (solo si se quiere
  programar); reemplazo del default vl1 (NO — apagaría fases vivas); limpieza vocab prod;
  retiro one-shot (D6, verificado-no-op); Prioridad dual (D5).

## 3. Nodos candidatos sugeridos (Claude verifica con fetch vivo, Paso 2 del skill)

- `KERNEL:TRACKER-SCHEMA` (§08): schema vivo auditado (12/4/11/6/2/4 opciones por prop).
- `KERNEL:GATE-DECISION` (§09): valores canónicos REVIEW_NEEDED/EXPIRED + patrón writer-live.
- `KERNEL:DEDUP-LAYER-UPGRADE` (09.12): resolución Q-H7 (dirección L1 + fix string-layer).
  Corroboración: jerarquía L1>L2>L3 ya declarada en `KERNEL:ARCHITECTURE-L1/L2/L3`
  (§04.1–04.3, reglas de dedup) y `KERNEL:CONTEXT-INFRASTRUCTURE-001` (§15.1) — la decisión
  del operador es consistente con Kernel, no solo criterio ad-hoc.
- `MANUAL:SCRIPT-GLOSSARY-XREF` (§22.6): `tracker_flow.py`, `sync_status_contratado.py`
  (y futuro `vl1_sync.py` de T6) ausentes del glosario sincronizado → estado NO_DOCUMENTADO;
  transitar ciclo XREF (vversions --new-scripts → skill → DRY RUN → APROBAR_WRITE).
- `KERNEL:DOCUMENTATION-011`: Evaluación de Impacto — citar en saneamiento repo (artefacto aparte).
- `MANUAL`: flujo VL1 (dispatch + cadena vl1), glosario scripts L1 (§22.1, gap web_ui.py preexistente).
- `SP:SCHEMA` (§7), `SP:DIGITAL-ID-CARD` (§03, IDs), `SP:CONSISTENCY` (validación obligatoria).
- `Career Canon`: evaluado sin impacto esperado (scope CV). Bug Tracker: cerrar/documentar
  TypeError + G1 (resueltos). Census: alta/baja de ID canónico NO anticipada (cambios son
  código) — Claude confirma per DOC-008; si no hay alta, no dispara Regla 1.

## 4. Evidencia disponible (anclas)

Commits: `bb29edf` (T0), `e635f16`+auto-syncs (0 .py); patch combinado G3+G1 (159 líneas,
39 verde, `handoffs/`); md5 base `6a41a7e0…`/`7e274a6d…`; hash backup `7da5210c…`; actas
`handoffs/CIERRE_DEPLOY_TRACKER_2026-09-11.md`, `VEREDICTO_CLAUDE_T0`(+A1). Tests:
`tests/test_tracker_flow_v3.py` (39), `tests/mocks/notion_fake.py`, suite `Layer_1/tests`
con 2 fallas preexistentes documentadas (day/month `priority_logic.py:125`, ANSI health_check).

## 5. Fuera de alcance de Fase 1

Contenido de parche, DRY RUN, escritura Notion, versionado (todo en `-implementacion`
tras APROBAR_WRITE). No re-auditar código: auditoría cerrada con bytes. Economía tokens:
lotes chicos, entregables primero (skill lo exige: solo 3 outputs visibles).
Protocolo evidencia vigente: S4-EVIDENCE + Regla de Adopción (v9.21.56, skills sesión
v1.2.0) — la instancia receptora adopta evidencia del operador sin re-verificar, salvo
contradicción explícita o inconsistencia interna. Ya registrado en changelog v9.21.56:
fix endpoint `data_sources.query()`, dry-run operador 24/0/24, task Holding
`3d8938be-…`, verificación rename Status — NO duplicar en esta doc.