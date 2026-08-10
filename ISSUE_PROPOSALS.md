# ISSUE_PROPOSALS.md

Estos son los issues detectados por la auditoría automatizada y verificados contra el estado actual del repositorio. Puedes copiar y pegarlos directamente en la interfaz de Issues de GitHub o usar este archivo como base para discusión.

## Issue: Fix: `gate()` no consulta Score — el guard central del Kernel no está implementado

Labels: bug, kernel, gate, critical

Descripción

`KERNEL:GATE-DECISION-002` (Kernel.md L410–414) y `KERNEL:GATE-DECISION-011` fila 2 definen la decisión de gate por umbral de `Score`: **≥60 → CREATE · 40–59 → Para Revisar · <40 → BLOCKED/Archivar**. La función `gate()` real (`Layer_1/scripts/layer_1_run.py:457-471`, verificado en `main`) decide únicamente por `fetch`, `vm_scope`, `role_class` y `source_type` — **el parámetro Score no existe en la firma de la función y no se consulta en ningún branch**.

Evidencia

- Código: `Layer_1/scripts/layer_1_run.py` (extracto):

```python name=Layer_1/scripts/layer_1_run.py url=https://github.com/mauriciomeyran/VANTAGE/blob/main/Layer_1/scripts/layer_1_run.py#L457-L471
def gate(fetch, vm_scope, role_class, source_type, rol="", marca=""):
    from profile_fit import has_vm_title_signal, is_role_excluded, resolve_alias_flags

    if is_role_excluded(rol) or resolve_alias_flags(marca)[0]:
        return "BLOCKED"
    if source_type in ["Inbound", "Referencia", "Networking"]:
        return "CREATE"
    if source_type == "Vacante":
        fetch_ok = fetch in ("Accesible", "Parcial")
        if fetch_ok and vm_scope == "Alto":
            return "CREATE"
        if fetch_ok and role_class == "Pivote" and has_vm_title_signal(rol):
            return "CREATE"
    return "BLOCKED"
```

- Tests: `Layer_1/tests/test_gate_logic.py` no contiene aserciones sobre Score (ver carpeta tests).

Criterio de aceptación

- [ ] Decidir semántica: (a) implementar Score≥60 como guard en `gate()` (añadir `score` como parámetro y tests), o (b) actualizar Kernel/Manual/Checklist para alinearse con la lógica actual de `gate()`.
- [ ] Implementación y tests acordes a la decisión.
- [ ] Changelog y release notes.

---

## Issue: Fix: Terminalidad incompleta — Score/Prioridad se recalculan sobre registros terminales; rama REJECTED inalcanzable

Labels: bug, kernel, terminality, high

Descripción

`KERNEL:GATE-DECISION-010` establece que "un registro terminal no puede ser sobreescrito por recálculo de Score/Gate". En el código actual:

- Fase 3 (Scoring) y Fase 3.6 (Prioridad) iteran sobre `query_all_items(...)` sin filtrar estados terminales — se recalculan Score/Prioridad sobre filas terminales.
- `gate_logic()` retorna un valor terminal no-`None` para `Status="Rechazado"`, y `layer_1_run.py` ejecuta `protected = gate_logic(entry)` seguido de `if protected is not None: continue` antes de `evaluate_rejection_status(status)`, por lo que la rama `REJECTED`+`Post-Mortem` (escritura) nunca se ejecuta.

Evidencia

- Código: `Layer_1/scripts/gate_logic.py` (extracto):

```python name=Layer_1/scripts/gate_logic.py url=https://github.com/mauriciomeyran/VANTAGE/blob/main/Layer_1/scripts/gate_logic.py#L17-L37
STATUS_TERMINAL_MAP = {
    "Postulado": "APPLIED",
    "Rechazado": "REJECTED",
}


def gate_logic(entry):
    status = entry.get("Status") or ""
    if status in STATUS_TERMINAL_MAP:
        return STATUS_TERMINAL_MAP[status]
```

- Código: `Layer_1/scripts/layer_1_run.py` (extracto mostrando la protección y el evaluate_rejection_status inalcanzable):

```python name=Layer_1/scripts/layer_1_run.py url=https://github.com/mauriciomeyran/VANTAGE/blob/main/Layer_1/scripts/layer_1_run.py#L975-L983
protected = gate_logic(entry)
if protected is not None:
    protected_count += 1
    continue

if evaluate_rejection_status(status):
    decision = "REJECTED"
    next_action = "Post-Mortem"
```

- Scoring/Prioridad fases sin guard (extractos): Fase 3: `layer_1_run.py:731-793`; Fase 3.6: `layer_1_run.py:899-931` (ambos recorren `items = query_all_items(...)` sin filtrar estados terminales).

Criterio de aceptación

- [ ] Excluir filas terminales en Fase 3 y 3.6 (reusar `gate_logic()` o check equivalente).
- [ ] Decidir y aplicar mecanismo para escribir `REJECTED`+`Post-Mortem` (p.ej. ejecutar `evaluate_rejection_status` antes de `gate_logic()`).
- [ ] Tests que aseguren que terminal no se sobrescribe y que la transición a Rechazado escribe la acción Post-Mortem al menos una vez.
- [ ] Corregir/backfill las filas residuales.

---

## Issue: Drift: Dedup implementado ≠ dedup documentado (`REJECTED_DUPLICATE` vs `Dedup_Flag='Posible duplicado'`)

Labels: drift, kernel, dedup, documentation, high

Descripción

`KERNEL:GATE-DECISION-011` documenta: match dedup en ventana 30d → `Gate_Decision=REJECTED_DUPLICATE`, `Dedup_Flag=True`, `Next_Action=Descartar`. En la implementación actual (`Layer_1/scripts/feed_processor.py`) no existe `REJECTED_DUPLICATE` ni `Descartar`. La implementación real escribe `REVIEW_NEEDED` en la entrada entrante y asigna `Dedup_Flag='Posible duplicado'` al registro existente.

Evidencia

- Código: `Layer_1/scripts/feed_processor.py` (extractos relevantes):

```python name=Layer_1/scripts/feed_processor.py url=https://github.com/mauriciomeyran/VANTAGE/blob/main/Layer_1/scripts/feed_processor.py#L503-L541
def _set_dedup_flag_if_needed(
    notion_utils: Client,
    page: dict,
    schema: NotionSchema,
) -> None:
    ...
    if current_dedup_flag != "Posible duplicado":
        notion_utils.pages.update(
            page_id=page_id,
            properties={dedup_flag_prop: {"select": {"name": "Posible duplicado"}}}
        )
```

```python name=Layer_1/scripts/feed_processor.py url=https://github.com/mauriciomeyran/VANTAGE/blob/main/Layer_1/scripts/feed_processor.py#L881-L890
if dedup_cross_layer(record, notion_utils, schema):
    return ProcessedRecord(
        record=record,
        hash_key=hash_key,
        disposition="REVIEW_NEEDED",
        notes="semi-duplicate (dedup cross-layer)",
        brand=record["brand"],
        holding=holding or "",
    )
```

Criterio de aceptación

- [ ] Acordar semántica: (a) mantener implementación y actualizar Kernel a `REVIEW_NEEDED`/`Posible duplicado`, o (b) implementar `REJECTED_DUPLICATE` en schema.
- [ ] Actualizar Kernel/Doc/changelog.
- [ ] Investigar por qué `dedup_cross_layer` no colapsó los duplicados observados y aplicar corrección/backfill.

---

## Issue: Drift: `KERNEL:GATE-DECISION-007` documenta `auto_archive.py` como activo; el script vive solo en `Archive/Legacy_Scripts/`

Labels: drift, kernel, documentation, high

Descripción

`KERNEL:GATE-DECISION-007` describe `Next_Action='Archivar' Y Dedup_Flag='Posible duplicado' → archivado automático vía auto_archive.py`. En `main` `auto_archive.py` no existe en `Layer_1/scripts/` y solo está en `Archive/Legacy_Scripts/auto_archive.py`. La decisión operatoria documentada en `skills/vantage-tidy-opportunities-tracker.md` (2026-08-01) indica que el archivado automático fue abandonado.

Evidencia

- Código: `Archive/Legacy_Scripts/auto_archive.py` (extracto):

```python name=Archive/Legacy_Scripts/auto_archive.py url=https://github.com/mauriciomeyran/VANTAGE/blob/main/Archive/Legacy_Scripts/auto_archive.py#L5-L10
"""
VANTAGE Auto-Archive — Ejecución automática de archivado

Archiva páginas en VANTAGE TRACKER cuando:
  - Next_Action='Archivar' 
  - Dedup_Flag='Posible duplicado'

Las páginas se mueven a ARCHIVO TRACKER con soft-delete.
"""
```

- Repo check: `Layer_1/scripts/auto_archive.py` → no existe (404), `Archive/Legacy_Scripts/auto_archive.py` → existe.

Criterio de aceptación

- [ ] Reescribir `KERNEL:GATE-DECISION-007` para eliminar referencia a `auto_archive.py` activo y documentar flujo vigente (archivado manual).
- [ ] Changelog y cierre/re-etiquetado del ticket "Dedup Caso 5…".
- [ ] Decidir si conservar `auto_archive.py` en Archive o eliminarlo definitivamente.

---

### Notas
- Si quieres que convierta estos borradores en issues reales ahora los puedo crear (títulos, labels y cuerpos ya preparados). ¿Los creo ahora en `mauriciomeyran/VANTAGE`?