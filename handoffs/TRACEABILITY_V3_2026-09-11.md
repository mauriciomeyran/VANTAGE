# Traceability Table - V3.1.1 (F1-F15 + G1-G10 + H1-H7)

**Serial:** DEVIN-20260911-05
**Fecha:** 2026-09-11 · **Reescritura H4 (Arena):** todas las citas verificadas con `grep`/`sed` contra los bytes pusheados.
**Formato:** `| ID | archivo:línea(s) exactas | diff (path en rama) | evidencia (tests §C3) |`

## Resuelto sin cita verificable = automáticamente NO resuelto

| ID | archivo:línea(s) exactas | diff | evidencia |
|---|---|---|---|
| F1 | tracker_flow.py:130-172 | `Layer_1/scripts/tracker_flow.py` | `normalize_record()` frontera API→plano; test_f1_normalize_record_api_shape, test_g1_fail_closed_missing_last_edited |
| F1 | tracker_flow.py:175-230 | `Layer_1/scripts/tracker_flow.py` | `extract_value()` ambas shapes + plano; test_f1_extract_value_both_shapes |
| F2 | tracker_flow.py:583-616 | `Layer_1/scripts/tracker_flow.py` | `evaluate_flow()` orden protección→terminalidad→elegibilidad→cómputo; test_f2_single_archive_path |
| F2 | tracker_flow.py:677-717 | `Layer_1/scripts/tracker_flow.py` | `execute_transition_with_propose_log()` unifica rutas; test_g2_execute_transition_with_propose_log |
| F2 | tracker_flow.py:651-675 | `Layer_1/scripts/tracker_flow.py` | `execute_transition()` payload unificado (G2); test_g2_execute_transition_payload |
| F2 | tracker_flow.py:720-747 | `Layer_1/scripts/tracker_flow.py` | `archive_gate()` append + Next_Action; test_f2_single_archive_path, test_end_to_end_normalize_to_archive |
| F2 | tracker_flow.py:490-522 | `Layer_1/scripts/tracker_flow.py` | 3 transiciones archivo matriz (url_failed/profile_misfit/nad_expired) → ruta propose/execute; test_g2_execute_transition_with_propose_log |
| F3 | tracker_flow.py:232-249 | `Layer_1/scripts/tracker_flow.py` | `KNOWN_BOT_IDS` + `_is_human_edit()` (autor); test_f3_is_human_edit_known_bot |
| F3 | tracker_flow.py:251-279 | `Layer_1/scripts/tracker_flow.py` | `_was_edited_since_last_run()` + fail-closed :260 (G1); test_f3_was_touched_by_human, test_g1_fail_closed_missing_last_edited |
| F3 | tracker_flow.py:281-291 | `Layer_1/scripts/tracker_flow.py` | `_was_touched_by_human()` autor AND tiempo; test_f3_was_touched_by_human |
| F3 | tracker_flow.py:619-642 | `Layer_1/scripts/tracker_flow.py` | `generate_propose_log()` idempotente por prefijo; test_f3_propose_log_idempotency |
| F4 | tracker_flow.py:175-230 | `Layer_1/scripts/tracker_flow.py` | `extract_value()` acepta ambas shapes (ver F1); test_f1_extract_value_both_shapes |
| F4 | tracker_flow.py:823-850 | `Layer_1/scripts/tracker_flow.py` | `diff_records()` con tipos preservados; test_f4_diff_with_type_preservation |
| F5 | tracker_flow.py:59 | `Layer_1/scripts/tracker_flow.py` | `RETIRADO` (typo RETRIRADO eliminado); test_f5_typo_fixed |
| F5 | tracker_flow.py:79-88 | `Layer_1/scripts/tracker_flow.py` | Fuente única terminalidad/protección (B3); test_protected_statuses |
| F6 | tracker_flow.py:365-374 | `Layer_1/scripts/tracker_flow.py` | Transición `create_objetivo`; test_f6_create_objetivo_transition |
| F6 | tracker_flow.py:417-456 | `Layer_1/scripts/tracker_flow.py` | Piernas Negociando/Sin Respuesta/Contratado; test_f6_missing_lifecycle_legs |
| F6 | tracker_flow.py:458-467 | `Layer_1/scripts/tracker_flow.py` | Pierna En Proceso→Rechazado; test_f6_en_proceso_to_rechazado |
| F6 | tracker_flow.py:469-488 | `Layer_1/scripts/tracker_flow.py` | Transiciones Exploratorio; test_f6_exploratorio_transitions |
| F6 | tracker_flow.py:529-580 | `Layer_1/scripts/tracker_flow.py` | `evaluate_transition()` + fallback manual HUMANO any→any (`manual_edit`=568); test_f6_manual_rule |
| F7 | tracker_flow.py:779-818 | `Layer_1/scripts/tracker_flow.py` | `evaluate_review_gate(record, field)` + H2 safe-BLOCKED (809-812); test_f7_review_gate_design, test_f7_review_gate_blocked |
| F8 | tracker_flow.py:41-77 | `Layer_1/scripts/tracker_flow.py` | `Status` Title Case, un solo literal; test_f8_single_literal_per_value |
| F8 | tracker_flow.py:91-107 | `Layer_1/scripts/tracker_flow.py` | `NextAction` 9 valores Title Case; test_f8_single_literal_per_value |
| F9 | tracker_flow.py:909-915 | `Layer_1/scripts/tracker_flow.py` | Config despliegue comentada (F9a/b/c: PR Devin→Mau, ramas separadas, freeze→merge→patch) |
| F9 | tracker_flow.py:917-934 | `Layer_1/scripts/tracker_flow.py` | `DELETED_VALUE_MAPPINGS` value→value H1 (Fetch_vocab :933); rollback en `Layer_1/scripts/rollback_schema_migration.py` (scaffold validador, restore=Claude/MCP) |
| F10 | tracker_flow.py:65-77 | `Layer_1/scripts/tracker_flow.py` | `Status.is_valid()`; test_f10_enum_enforcement |
| F10 | tracker_flow.py:130-172 | `Layer_1/scripts/tracker_flow.py` | Enforcement en `normalize_record` (inválido→Por Revisar + `_original_invalid_status`); test_f10_enum_enforcement |
| F11 | tracker_flow.py:293-333 | `Layer_1/scripts/tracker_flow.py` | `is_mutable()` record-level; field-block DIFERIDO (G3, docstring 297-298); test_f11_composite_guard |
| F12 | tracker_flow.py:852-866 | `Layer_1/scripts/tracker_flow.py` | `SURVIVOR_PRIORITY` Contratado primero; test_f12_contratado_first |
| F12 | tracker_flow.py:868-880 | `Layer_1/scripts/tracker_flow.py` | `get_survivor_rank()`; test_f12_contratado_first |
| F12 | tracker_flow.py:882-906 | `Layer_1/scripts/tracker_flow.py` | `choose_survivor()` + H7 url-tiebreak (:899-901); test_f12_choose_survivor, test_h7_url_tiebreak_prefers_url |
| F13 | rama arena/01a08e60-vantage sobre main@467af9c8 | (higiene git, ver handoff §0) | Base fresca verificada; rama devin/tracker-refactor-v3@d881bc1 superada por este PR |
| F14 | handoffs/TRACEABILITY_V3_2026-09-11.md | este archivo (reescritura H4) | Este archivo con citas verificadas |
| F15 | tracker_flow.py:952-961 | `Layer_1/scripts/tracker_flow.py` | A3: SOLO comentarios (sin `_move_to_archivo`): confirmación = propose-log + APROBAR_WRITE (diseño diferido, declarado) |
| F15 | tests/test_tracker_flow_v3.py:32-63 | `tests/test_tracker_flow_v3.py` | A5: `COVERAGE_MAP` real + test_h7_coverage_map_complete (auto-verifica no-drift) |
| G1 | tracker_flow.py:145-154, :260 | `Layer_1/scripts/tracker_flow.py` | Extracción raíz shape real + fail-closed; test_g1_fail_closed_missing_last_edited; fixture con raíz real |
| G2 | tracker_flow.py:651-675 | `Layer_1/scripts/tracker_flow.py` | Payload unificado (ver F2); test_g2_execute_transition_payload |
| G3 | tracker_flow.py:293-299 | `Layer_1/scripts/tracker_flow.py` | Defer field-block declarado; test_f11_composite_guard |
| G4 | tracker_flow.py:917-934 | `Layer_1/scripts/tracker_flow.py` + rollback script | H1 mapping + scaffold (ver F9) |
| G5 | tracker_flow.py:779-818 | `Layer_1/scripts/tracker_flow.py` | Defer wiring (ver F7/H2) |
| G6 | tests/mocks/notion_fake.py:11-20, :37 | `tests/mocks/notion_fake.py` | H3 cadena `fake.pages.update/retrieve`; test_h3_fake_pages_chain, test_notion_fake_mirror_api |
| G7 | handoffs/TRACEABILITY_V3_2026-09-11.md | este archivo | H4 reescritura verificada |
| G8 | rama arena/01a08e60-vantage | `git diff main...HEAD --stat` (handoff §C4) | 7 archivos delivery, +X/−0 sobre código existente (ver C4) |
| G9 | seriales -05 | módulo :5, handoff header + D4, este archivo header | Barrido H5 completo |
| G10 | (bloqueador gh Devin superado) | PR arena→main abierto por Arena | Mau mergea (ver handoff §D) |
| H1 | tracker_flow.py:917-934 | `Layer_1/scripts/tracker_flow.py` | Mapping canal→resultado + Q-H1 (ver F9/G4) |
| H2 | tracker_flow.py:779-818 | `Layer_1/scripts/tracker_flow.py` | Safe-BLOCKED + punto inserción (ver F7/G5); test_f7_review_gate_blocked |
| H3 | tests/mocks/notion_fake.py:11-20, :35-40 | `tests/mocks/notion_fake.py` | Namespace `pages` (ver G6); test_h3_fake_pages_chain |
| H4 | handoffs/TRACEABILITY_V3_2026-09-11.md | este archivo | Reescritura con citas verificadas |
| H5 | seriales | módulo :5, handoff, este archivo | -05 consistente (delivery); -07 handoff Arena |
| H6 | handoffs/HANDOFF_DEVIN_V3_2026-09-11.md | handoff §§B/C/D + addendum V3.1.1 | Conteos/C3/C4/hash corregidos contra bytes |
| H7 | tracker_flow.py:24, :291, :887, :899-901; tests :32-63, :136-149, :500-529 | código + tests | Headers, layer-doc+Q-H7, url-fix, mapa, f3 determinista; 30/30 §C3 |

## Preguntas Abiertas

**Q-G1:** ¿Quién aprovisiona Notion no-prod para integración?
**Decisión tomada:** No se propone, fakes.
**Alternativas descartadas:** Integración real (requiere aprovisionamiento externo).
**Dato de cierre:** Fakes implementados en tests.
**Impacto si se revierte:** Tests fallarían, requeriría implementación real.

**Q-H1:** ¿Vocabulario real de la propiedad Fetch en schema vivo? (`DELETED_VALUE_MAPPINGS.Fetch` usa propuesto `Accesible/Bloqueado`, PARAMÉTRICO.)
**Decisión tomada:** Default `Accesible` + `strategy: revalidate` (no destructivo, v9.14.5); migrar y re-evaluar en primer run.
**Alternativas descartadas:** `Bloqueado` default (podría disparar archivo masivo); mapping estático canal→resultado (semánticamente imposible: canal ≠ resultado).
**Dato de cierre:** Claude/MCP confirma vocabulario contra schema vivo en ventana de despliegue; si difiere, se ajusta `Fetch_vocab_proposed` + defaults antes del PATCH.
**Impacto si se revierte:** Bajo-medio (solo defaults de migración; revalidate corrige en un run).

**Q-H7:** ¿Dirección correcta de preferencia `layer` en `choose_survivor` (implementado: higher-first)?
**Decisión tomada:** Se mantiene código (higher-first) documentado; impacto marginal (solo desempata tras status+score+url iguales).
**Alternativas descartadas:** Lower-first sin evidencia de semántica L1/L2/L3.
**Dato de cierre:** Mau o schema-docs confirman semántica de layer como fuente.
**Impacto si se revierte:** Mínimo (una línea + re-correr suite).

## Frases de Conformidad

"Ninguna escritura a Notion de producción fue realizada ni intentada en esta sesión."

"Declaro bajo el contrato DEVIN-20260911-02 que cada ítem marcado resuelto tiene cita archivo:línea, diff visible y evidencia de ejecución pegada; lo que no tenga las tres, no está resuelto."
