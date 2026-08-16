# Feedback — Confirmación NameError + matriz Dedup_Flag

Fase 1 recortada: **APROBAR_WRITE**.

Matriz Dedup_Flag: **aprobada**.

Guard de `layer`: **aprobado con corrección de contrato**. No implementes hasta leer el punto 3.

---

## 1. NameError — confirmado, y hay un segundo bug en la misma función

La extracción a módulo está bien. Al bajarla, no copies la firma de 2 args a ciegas.

Hoy hay **dos** call sites con 3 argumentos y una definición de 2:

```
580-582  _check_historical_rejected_status  → NameError (no está en scope)
701-711  def _extract_text_prop(row, prop_name)   # 2 args
727-729  dedup_by_content_fingerprint
         _extract_text_prop(row, schema.location_prop or "location", "")  # 3 args → TypeError
```

Línea 729 vive *dentro* de la función que define el helper. Si `schema.location_prop` está seteado, el fingerprint path ya revienta con `TypeError`, no solo el histórico.

Al extraer:

```python
def _extract_text_prop(row: dict, prop_name: str, default: str = "") -> str:
    ...
    return default
```

Y unificar `_extract_title_text` (L634, anidada en `dedup_cross_layer`) en el mismo helper. Tres extractores para el mismo objeto Notion es el bug de clase `txt()` que ya rompió Score/Prioridad.

Tests mínimos:

- rich_text multi-chunk
- title multi-chunk
- select
- url
- prop ausente → `default`
- llamada de 3 args `(row, prop, "")` no explota

---

## 2. Matriz Dedup_Flag — aprobada

Implementación:

- Un helper, no `gate_logic()`. Ej. `should_annotate_existing(status) -> bool` que reutilice `profile_fit._PROTECTED_STATUSES | _TERMINAL_STATUSES` (o `not should_auto_cleanup` no aplica: ese pide `reasons`).
- Leer `Status` del **page object de Notion** (`properties.Status.select.name`), no `entry.get("Status")`. `gate_logic` espera un dict plano; el existente es payload de API. Si mezclas los dos, el guard no dispara nunca.
- El inbound sigue `REVIEW_NEEDED`. No se toca.
- Ancla en comentario: `KERNEL:GATE-DECISION-007` + `profile_fit` protected/terminal. No cites `GATE-DECISION-010` como si esto fuera recálculo de Score.

---

## 3. `layer` — mismo guard, razón distinta. No es Class B.

`KERNEL:SCHEMA-001`: `layer` es **Class A**. `Dedup_Flag` es **Class B**.

“Ambas son mutaciones Class B” es falso. Si eso entra al código o a un comentario, reabre el drift que estamos cerrando.

Sí al mismo predicado de Status, por esta razón y no la otra:

- No reescribir procedencia de una postulación viva (Class A del operador ya actuó).
- La jerarquía L1>L2>L3 del inbound se puede dejar en `Notas` del REVIEW_NEEDED nuevo. No hace falta mutar el existente.

No al razonamiento “es Class B, luego el guard de Class B aplica”.

---

## 4. Qué implementar en este batch

| Ítem | ¿Va? |
|---|---|
| `infer_layer` L2 | Sí + test L1/L2/L3/default |
| Comentario GAP-03 | Sí |
| `_extract_text_prop` a módulo, firma con `default`, unificar title | Sí + tests |
| Guard Dedup_Flag según matriz | Sí, helper compartido, Status desde Notion page |
| Mismo predicado en `_upgrade_layer_if_needed` | Sí, con comentario Class A / procedencia |
| `class_b_guard` / Positioning_Mode | No |
| `pipeline_recovery` | No — ticket de Manual aparte |

DRY RUN de los tres scripts tocados (`feed_processor` no se corre contra Notion en este batch salvo tests locales). Tests primero, write de Tracker después, y solo si hay un caso real que quieras re-ingerir.

Cuando esté el diff: archivo + línea, y el predicado de Status citado una sola vez. Sin reabrir Redis, override, ni schema dinámico.
