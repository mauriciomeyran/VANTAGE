# Contra-feedback — Hallazgos verificados v2

Las 8 respuestas están bien: honestas y suficientes. El documento nuevo ya es el formato correcto (existe / bug / backlog / viola Kernel). No implementes Fase 1 completa todavía. Hay un P0 listo, un P0 mal anclado, y un “P0” que todavía es diseño, no parche.

---

## Qué se acepta

- Inventario de infraestructura existente (§3): correcto. No reimplementar.
- Rechazo de override / schema dinámico / reglas JSON / ML (§4): correcto. Cerrado.
- Backlog de paralelo / Redis / circuit breaker / scripts CV (§5): correcto. Cerrado hasta evidencia.
- Bug `infer_layer` L2→L3: verificado, fix de una línea, se puede parchear.
- Comentario stale GAP-03 / FX-1: verificado, se puede parchear.

---

## No APROBAR_WRITE todavía sobre `_set_dedup_flag_if_needed`

El hallazgo 1.3 está a medio pensar. Tres problemas:

### 1. `gate_logic()` no es el predicado correcto

`Dedup_Flag='Posible duplicado'` no es recálculo de Score/Gate. Es señal de **candidato a archivar** (`KERNEL:GATE-DECISION-007` → `vantage-tidy-opportunities-tracker`). El riesgo real no es “mutar un terminal”: es marcar para archivo una postulación viva.

`gate_logic()` protege solo:

- Status: `Postulado`, `Rechazado`, `Expirada`
- Next_Action: `Archivar`, `Expirada`

No protege: `En proceso`, `Negociando`, `Sin respuesta`, `Contratado`, `Postulando`.

Esos ya viven en `profile_fit._PROTECTED_STATUSES` / `_TERMINAL_STATUSES` y en `should_auto_cleanup()`. Si el parche es `if gate_logic(entry): return`, un `En proceso` puede quedar como candidato a archivo. Eso es peor que el bug actual.

Ancla correcta: `KERNEL:GATE-DECISION-007` + `profile_fit.should_auto_cleanup`, no `GATE-DECISION-010` como si fuera el mismo contrato que Score/Gate.

`GATE-DECISION-010` dice: un terminal no se sobreescribe por recálculo de Score/Gate. No dice “ningún Class B se toca”. `GATE-DECISION-011` fila de dedup incluso *pide* escribir `Dedup_Flag` en el registro existente coincidente.

### 2. Falta la matriz de decisión

Antes de tocar código, una tabla. Propuesta para que confirmes o corrijas:

| Status / estado del existente | ¿Escribir Dedup_Flag? | Por qué |
|---|---|---|
| Target / Exploratorio / REVIEW_NEEDED | Sí | Candidato legítimo a tidy |
| Postulado / Postulando / En proceso / Negociando / Sin respuesta / Contratado | No | Postulación viva — tidy no debe verlo |
| Rechazado | No (o irrelevante) | `_check_historical_rejected_status` ya bloquea el inbound; no es candidato a archivo por dedup |
| Expirada / Archivar / Retirado | No | Ya está en vía de archivo; el flag es ruido |

El inbound sigue siendo `REVIEW_NEEDED` aunque no se escriba el flag. Eso no se toca.

### 3. `_upgrade_layer_if_needed` es el mismo patrón y no está en el doc

En el mismo match, `feed_processor` puede mutar `layer` del existente si el inbound tiene mayor prioridad. Hacer el guard solo en Dedup_Flag y dejar el upgrade suelto es inconsistente. Mismo batch, misma matriz, o se deja explícitamente fuera con razón.

---

## Correcciones menores al documento

1. **Ancla de `infer_layer`.** `KERNEL:CV-PIPELINE-001` es CV-A (HANDOFF / Positioning Mode), no layers L1/L2/L3. Ancla: `KERNEL:ARCHITECTURE-L1/L2/L3` + `KERNEL:SCHEMA-001` (`layer` es Class A). El fix L3→L2 sigue siendo correcto.

2. **“KERNEL:SCHEMA-001 (Notion)”.** El Kernel no es Notion. Notion = propiedades existentes. Kernel = ownership. Esa confusión fue el error de la v1; no la reintroduzcas en el título.

3. **Dirección del drift Class A/B.** `SCHEMA-001` está *incompleto* frente al Tracker real (Notas, JOB_ID, Contacto, Interview*, Outcome, etc. ya los escribe el operador y el guard los trata como Class A). Reconciliar ≠ encoger el guard hasta el Kernel. Dirección por defecto: Kernel absorbe los campos operativos que ya son Class A de hecho. La excepción es `Positioning_Mode`: Kernel lo declara Class A y el guard no lo tiene — con `strict_unknown=True` un write MCP de Positioning_Mode se bloquea. Ese sí es un hueco del guard. No “actualizar class_b_guard si necesario” sin esa decisión campo por campo.

4. **`pipeline_recovery`.** No es “completar `resume_pipeline()`”. `layer_1_run.py` no llama `save_checkpoint`. El resume no está stubbed: el mecanismo no está cableado. Completar la función sin instrumentar L1 es teatro. Acción correcta de Fase 2: documentar en Manual que `vl1 recovery` hoy es consistency check, no resume. Cablear checkpoints es otro ticket, con evidencia de corridas a medias.

---

## Bug que este documento todavía no vio

`_check_historical_rejected_status` (`feed_processor.py` ~L576–578) llama `_extract_text_prop(...)`, que **no existe a nivel de módulo**. Está definida como función anidada dentro de `dedup_by_content_fingerprint`. Si esa rama encuentra candidatos Rechazado, es `NameError` en runtime.

Verificar y, si se confirma, ese fix entra en el mismo batch que `infer_layer`. Más impacto operativo que el typo de L2.

---

## Qué puedes implementar ahora (Fase 1 recortada)

Aprobado, sin más diseño:

1. `infer_layer`: `"layer: l2"` → `return "L2", "notas_layer"`. Test del branch L1/L2/L3 + default.
2. Comentario GAP-03: GAP-03 cerrado v9.19.2; el guard vive en `dashboard_notion.py`; este write path es Class A por construcción vía `NotionSchema`.
3. Si confirmas el `NameError` de `_extract_text_prop`: extraer helper a módulo y usarlo en ambas funciones.

No aprobado todavía:

- Guard de Dedup_Flag (falta la matriz).
- Cualquier cambio a `class_b_guard` (falta decisión campo a campo).
- Completar `pipeline_recovery`.

Siguiente entregable, una página: la matriz de Dedup_Flag + si `_upgrade_layer_if_needed` entra en el mismo guard + confirmación del `NameError`. Sin eso no hay APROBAR_WRITE del ítem 1.3.
