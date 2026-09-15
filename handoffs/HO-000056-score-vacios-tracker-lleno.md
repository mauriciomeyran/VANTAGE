# HO-000056 — Score/VM_Scope/Score_Method no calculados en Notion + 144 registros en tracker

**Serial:** HO-000056  
**Fecha:** 2026-09-14 23:52:00 CDMX  
**De:** GROK-20260914-01 → Claude  
**Estado:** OPEN  

---

## Problema

Tras aplicar parche al `layer_1_orchestrator.py` (write_payload assembly con asignación explícita de campos Class B), ejecuté `--apply` pero:

- **Score, VM_Scope, Score_Method, Prioridad siguen vacíos** en los 29 registros visibles de Notion.
- **90 errores** en el último `--apply` (resumen: 100 procesados, 7 escrituras, 90 errores).
- **144 registros en el tracker** (deberían ser ~24 — múltiples ejecuciones crearon duplicados).

---

## Lo que SÍ funciona (verificado por GROK)

1. **El parche de write_payload está aplicado** (líneas 1211-1239 de `layer_1_orchestrator.py`). Reemplacé el loop `elif` con asignación explícita.
2. **El payload offline es correcto** — verifiqué con el mismo registro de prueba (`Rol='Visual Merchandising por Proyecto'`) y el write_payload incluye `Score=50, Score_Method=DETERMINISTIC, VM_Scope=Alto, Role_Class=VM, Source_Type=job_board, Prioridad=Media`.
3. **El actor es PIPELINE** → `class_b_guard` local (línea 603) debería permitir Class B fields.

---

## Lo que NO logré verificar

1. **Por qué 90 registros lanzan excepción durante Fase Cálculo** — no tengo el traceback, solo el contador de errores.
2. **La estructura del `current` record** que viene del tracker query (¿los campos existen? ¿son del tipo correcto?).
3. **Si `compute_write_diff` está devolviendo payload vacío** para registros que sí deberían tener cambios (línea 679).
4. **El estado real de los 24 registros creados por `run_ingestion`** en Notion — ¿tienen los campos Class B? ¿o están incompletos?
5. **Por qué hay 144 registros** — ¿duplicados de múltiples ejecuciones? ¿o registros legítimos con diferentes estados?

---

## Archivos clave

- `Layer_1/scripts/layer_1_orchestrator.py` — v9.1, parche aplicado en write_payload (líneas 1211-1239), función local `class_b_guard` (líneas 603-629), `guarded_pages_update` (líneas 659-698), loop F3-F4 (líneas 1153-1266).
- `Layer_1/scripts/class_b_guard.py` — módulo importado (CLASS_A_FIELDS, CLASS_B_FIELDS, guard_write_payload).
- `Layer_1/scripts/tracker_flow.py` — `diff_records`, `to_notion_properties`, estructura de записи.

---

## Próximos pasos sugeridos

1. Agregar logging temporal en el loop F3-F4 para capturar el traceback de los 90 errores.
2. Verificar la estructura del `current` record inmediatamente después del query (F0).
3. Verificar `compute_write_diff` output para un registro de prueba.
4. Si los 144 registros son duplicados, limpiar el tracker y re-ejecutar con un solo `--apply` después de confirmar que el cálculo funciona.
5. Si el cálculo funciona pero los campos no llegan a Notion, revisar `guarded_pages_update` → `class_b_guard` → `pages_update` pipeline completo.

---

**Handoff entregado.** Esperando acción de Claude.
