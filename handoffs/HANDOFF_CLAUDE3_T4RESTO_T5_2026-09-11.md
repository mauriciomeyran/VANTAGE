# HANDOFF — Claude #3 · resto T4 + T5 · 2026-09-11 (serial CLAUDE-20260911-04)

Lee PRIMERO. Dos instancias previas murieron por tokens: trabaja en lotes chicos,
entregables PRIMERO (patch + `pytest -q` tail), prosa al final. Cero writes a prod
hasta T5 (hard-gated, aprobación Mau+Arena por paso).

## 0. Base (verifica antes de actuar — Zero-Trust)
1. `git log --oneline -1` + `git status --short` — se espera base `main@bb29edf` limpia.
   Flag: CLAUDE MP veía el bug G3 en línea 1037 vs 1031 de Arena (+6 offset) → confirma tu base.
2. IDs: DATABASE `596938be-fc42-836b-aea7-814a1491bd47` (/databases, API 2022-06-28) vs
   DATA SOURCE `442938be-fc42-828f-b72e-076818d65a5b` (data_sources, API 2025-09-03).

## 1. Estado verificado (no re-hacer)
- T0✅ 36/36 · T1✅ censo (24 filas, Target=0, Q-H1 resuelto) · T2✅ backup
  (sha256 `7da5210c…eb071`, `backups/`) · T3✅ plan cutover aprobado (Paso 5 sandbox recortado).
- **G3/Q-H7 ✅ CERRADO-verificado por Arena:** bug TypeError en `choose_survivor` (unary minus
  sobre layer string) confirmado en pre-fix, fix aplicado, **39/39 reproducido por Arena**.
  Dirección Mau: **L1 gana (Active Search > Passive Intake)** → L1>L2>L3>N/A.
  Patch verificado: `handoffs/T4_G3_diff_2026-09-11.patch` (128 líneas, `git apply`-friendly).
  Aplícalo y corre `pytest -q` (esperado 39 passed). No re-derivar.

## 2. Lo abierto (tu tarea T4-resto)
- **G1 (Gate_Decision): DESCONOCIDO** — CLAUDE MP murió antes de reportar su grep.
  Rehacer: lectores/escritores de `Gate_Decision` en `layer_1_run.py`, `feed_processor`,
  `mcp_dashboard`, módulo viejo. Vivo={…,EXPIRED,REVIEW_NEEDED} vs enum={…,EXPIRADA,REVIEW}.
- **G2 (Next_Action): HALLAZGO + CONTRADICCIÓN ABIERTA.**
  (a) `layer_1_run.py:525-536` (`get_application_next_action`) SÍ escribe Follow-up/
  Interview prep/Re-check cada corrida → NO son valores inertes (corrección al pre-análisis).
  (b) ⚠️ CONTRADICCIÓN: T1 dijo `Next_Action` = select 11 opciones; CLAUDE MP dijo schema
  vivo = `rich_text` y código manda payload `{"select":…}` → mismatch. **Re-fetch el tipo
  de la propiedad en vivo y reconcilia antes de proponer fix.** El diff depende de esto.

## 3. Entrega T4-resto (en este orden)
1. `git log -1` + `status --short` (base).
2. Respuestas: G1 (quién lee/escribe Gate_Decision) + G2 (tipo vivo real + decisión writer/payload).
3. Patch propuesta (solo G1/G2; G3 ya va aparte) + `pytest -q` tail.
4. ALTO obligatorio → esperar aprobación Mau+Arena. T5 (backfill dry-run→apply + wiring
   runner + smoke) solo tras esa aprobación, por micro-pasos.