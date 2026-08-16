# Brief para Documentación Transversal — PR #10 (guard de anotación en dedup + fixes autorizados)

**Fecha:** 2026-08-16
**Skill objetivo:** `vantage-documentacion-transversal-propuesta` → `vantage-documentacion-transversal-implementacion`
**Tipo de solicitud:** Documentación transversal de cambio estructural ya mergeado a `main`
**Fuente de código:** PR #10 (`arena/01a00b06-vantage` → `main`, merge `dec979ad`, 2026-08-16)
**Fuentes de decisión:** `handoffs/FEEDBACK_DEVIN_HALLAZGOS_V2.md`, `handoffs/FEEDBACK_DEVIN_MATRIZ_DEDUP.md` (Fase 1 recortada: APROBAR_WRITE; matriz Dedup_Flag: aprobada; guard de layer: aprobado con corrección de contrato)

## Contexto

PR #10 implementó el batch autorizado en el feedback Devin v2 + matriz dedup:

1. **Fix `infer_layer` L2** (`backfill_class_a.py` ~L116): `"layer: l2"` retornaba `("L3", "notas_layer")` → corregido a `("L2", "notas_layer")`. Un backfill ya no puede escribir mal la procedencia. Test del branch L1/L2/L3 + default.
2. **`_extract_text_prop` a módulo** (`feed_processor.py`): helper único a nivel de módulo con firma `(row, prop_name, default="")` — soporta title / rich_text / select / url. Elimina: (a) `NameError` en `_check_historical_rejected_status` (llamaba a una función anidada fuera de scope), (b) `TypeError` en el fingerprint path cuando `schema.location_prop` está seteado (call site de 3 args contra definición de 2), (c) `_extract_title_text` duplicado en `dedup_cross_layer` (unificado en el mismo helper).
3. **Guard de anotación en dedup** (`feed_processor.py` + `profile_fit.py`): predicado nuevo `should_annotate_existing(status)` en `profile_fit.py` (reutiliza `_PROTECTED_STATUSES | _TERMINAL_STATUSES`), consumido vía `should_mutate_existing_page(page, schema)` que lee el Status del **page object de Notion** (`properties.Status.select.name`). Aplica a `_set_dedup_flag_if_needed` (Dedup_Flag, Class B — candidato a archivo, KERNEL:GATE-DECISION-007) y a `_upgrade_layer_if_needed` (layer, Class A — procedencia; se bloquea para no reescribir origen de postulación viva, **no** porque layer sea Class B). El inbound sigue `REVIEW_NEEDED` sin excepción; la jerarquía L1>L2>L3 del entrante queda en Notas del REVIEW_NEEDED nuevo cuando el upgrade se omite. Omisiones reportadas en consola (`⏭️ Dedup_Flag omitido` / `⏭️ Layer upgrade omitido`).
4. **Comentario GAP-03 actualizado** (`write_to_notion`): GAP-03 cerrado v9.19.2; write path Class A por construcción vía `NotionSchema`; guard para actores no-Python vive en `dashboard_notion.py` (`class_b_guard.guard_write_payload()`); FX-1 cerrado.
5. **Tests**: `Layer_1/tests/test_authorized_fixes.py` (192 líneas), `test_profile_fit.py` (+38), `conftest.py`.

Explícitamente FUERA de este batch (no documentar como hecho): cambios a `class_b_guard` / `Positioning_Mode` (pendiente decisión campo a campo), `pipeline_recovery` (ticket de Manual aparte).

## Matriz Dedup_Flag aprobada (referencia)

| Status del existente | ¿Escribir Dedup_Flag / upgrade layer? | Por qué |
|---|---|---|
| Target / Exploratorio / REVIEW_NEEDED / vacío | Sí | Candidato legítimo a tidy |
| Postulado / Postulando / En proceso / Negociando / Sin respuesta / Contratado (_PROTECTED_STATUSES) | No | Postulación viva — tidy no debe verlo |
| Expirada / Rechazado / Archivar / Retirado (_TERMINAL_STATUSES) | No | Ya terminal o en vía de archivo; el flag es ruido |

## Nodos parcheados (local, ACTIVE/ — pendiente `vdoc local`)

| # | Doc | Nodo / ancla | Cambio |
|---|---|---|---|
| N1 | Kernel | KERNEL:GATE-DECISION-007 (09.7) | Párrafo nuevo "Guard de anotación en ingesta (PR #10)": predicado, sets de Status, lectura desde page object, distinción vs gate_logic(), inbound intacto |
| N2 | Kernel | KERNEL:GATE-DECISION-011 (09.11) | Fila de dedup match de la matriz: efecto Class B condicionado a should_annotate_existing(Status) |
| N3 | Manual | MANUAL:DATA-MANAGEMENT § Dedup | Bullet nuevo "Guard de anotación (PR #10)" entre resolución de flags y ventana |
| N4 | Manual | Glosario § feed_processor.py | Párrafo "Hardening PR #10" (helper único, guard, GAP-03) |
| N5 | Manual | Glosario § profile_fit.py | should_annotate_existing documentado + consumidor nuevo |
| N6 | Manual | Glosario § backfill_class_a.py | Fix infer_layer L2 documentado |

Anclas conforme al contra-feedback: `KERNEL:GATE-DECISION-007` + `profile_fit` protected/terminal (NO GATE-DECISION-010 como si fuera recálculo de Score); `infer_layer` anclado a ARCHITECTURE-L1/L2/L3 + SCHEMA-001 (layer es Class A), no a CV-PIPELINE-001.

## Draft de entrada Change Log (pendiente timestamp del operador — KERNEL:DOCUMENTATION-010)

```
Tipo: [DOC]
Alcance:
- Kernel (KERNEL:GATE-DECISION-007, 09.7 — guard de anotación en ingesta; KERNEL:GATE-DECISION-011, 09.11 — fila dedup match condicionada)
- Manual (MANUAL:DATA-MANAGEMENT § Dedup — bullet guard PR #10; Glosario §22 — feed_processor.py, profile_fit.py, backfill_class_a.py)
Contexto: PR #10 (merge dec979ad, 2026-08-16) implementó el batch autorizado en FEEDBACK_DEVIN_MATRIZ_DEDUP (Fase 1 recortada): fix infer_layer L2, _extract_text_prop consolidado a módulo (cierra NameError en _check_historical_rejected_status y TypeError en fingerprint path), guard should_annotate_existing sobre Dedup_Flag y upgrade de layer en registros existentes (matriz aprobada: _PROTECTED_STATUSES | _TERMINAL_STATUSES), y comentario GAP-03 actualizado (FX-1 cerrado). El código llegó a main sin su contraparte documental — esta entrada la cierra.
Cambios: [ver tabla de nodos N1–N6 del brief brief_doc_transversal_pr10_dedup_guard.md]
IDs afectados: Ninguno (todas las ediciones reutilizan IDs existentes — no dispara KERNEL:CENSUS-SYNC Regla 1).
Pendiente (fuera de esta entrada):
- vversions --sync para propagar al resto de los fundacionales.
- Decisión campo a campo class_b_guard / Positioning_Mode (backlog, feedback v2 §3).
- Ticket de Manual para pipeline_recovery (vl1 recovery hoy es consistency check, no resume).
```

## Qué falta después de este brief (lado operador / Mac)

1. `git merge` de la branch de esta sesión (o merge del PR).
2. `vdoc kernel dry` + `vdoc manual dry` → revisar → `vdoc local kernel` + `vdoc local manual` (local → Notion, con APROBAR_WRITE).
3. Entrada Change Log en Notion con timestamp CDMX provisto por el operador.
4. `vversions --sync` para propagar la versión.
