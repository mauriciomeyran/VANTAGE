# DEPRECATED: assign_next_action.py

**Fecha de deprecación:** 2026-08-03  
**Motivo:** Duplicación de lógica con divergencia de negocio

---

## Qué hacía

Shortcut manual de Raycast para recalcular Next_Action sobre el Tracker, bajo demanda. Invocaba `assign_next_action.py` que implementaba lógica de gate y next_action independiente del pipeline principal.

---

## Por qué se archivó

`assign_next_action.py` duplica la lógica de las siguientes funciones que ya viven en `layer_1_run.py` Fase 4:
- `gate()` 
- `evaluate_rejection_status()`
- `evaluate_application_status()`
- `get_application_next_action()`

La implementación en `assign_next_action.py` estaba divergiendo de la versión canónica en `layer_1_run.py`, creando dos fuentes de verdad para la misma lógica de negocio.

---

## Bugs conocidos en la versión archivada (NO revivir tal cual)

### (a) No maneja Status="Rechazado" explícitamente
- **Comportamiento actual:** Caía al default BLOCKED → Archivar
- **Comportamiento correcto:** Debería ser REJECTED → Ninguna
- **Función afectada:** `gate_logic_complete()` no tiene caso específico para "Rechazado"

### (b) Es MÁS permisivo con Role_Class="Pivote"
- **Comportamiento actual:** `gate_logic_complete()` retorna CREATE con solo `(vm_scope=="Alto" or role_class=="Pivote")`
- **Comportamiento correcto:** `gate()` en `layer_1_run.py` requiere `has_vm_title_signal(rol)` además de role_class="Pivote"
- **Verificación por traza:** Entrada `("Vacante","Accesible","Bajo","Pivote")` → "CREATE" en `assign_next_action.py`, pero "BLOCKED" en `gate()` si el rol no tiene señal VM en el título

---

## Camino correcto para revivirlo

Si se necesita manualmente un shortcut de Raycast para recalcular Next_Action:

1. **NO reimplementar la lógica de gate por separado**
2. Reescribir `vantage-assign.sh` para que invoque la lógica de `layer_1_run.py` Fase 4:
   - Importar las funciones canónicas: `gate()`, `evaluate_rejection_status()`, `evaluate_application_status()`, `get_application_next_action()`
   - Usar esas funciones directamente en lugar de reescribirlas
3. Mantener una sola fuente de verdad para la lógica de Gate/Next_Action

---

## Archivos movidos

- `Layer_1/scripts/assign_next_action.py` → `Layer_1/scripts/deprecated/assign_next_action.py`
- `Raycast/vantage-assign.sh` → `Layer_1/scripts/deprecated/vantage-assign.sh`

Ambos archivos se mantienen en `/deprecated/` por razones de auditoría y posible referencia histórica, pero no deben ser usados en producción.
