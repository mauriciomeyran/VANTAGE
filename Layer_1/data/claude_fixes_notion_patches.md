# Parches para Correcciones Claude — Kernel.md y layer_1_run.py

## 1. Kernel.md (Notion)

**Ubicación:** Documentación/ACTIVE/Kernel.md  
**Sección:** 09.11 KERNEL:GATE-DECISION-011 (líneas ~503)

### Parche: Corrección de Fila 3 según feedback Claude

**Texto original (línea 503):**
```
| [ENTRY] | feed_processor.py ingesta JSON | URL muerta OR Score < 60 | BLOCKED | Python | Gate_Decision=BLOCKED, Score=0 (si URL muerta) |
```

**Texto nuevo (reemplazar completo):**
```
| [ENTRY] | feed_processor.py ingesta JSON | URL muerta OR Score < 40 | BLOCKED | Python | Gate_Decision=BLOCKED, Score=0 (si URL muerta) |
| [ENTRY] | feed_processor.py ingesta JSON | URL viva + Score 40–59 + Status=Target | REVIEW_NEEDED | Python | Gate_Decision=REVIEW_NEEDED, Score, VM_Scope, Role_Class, Next_Action |
```

**Cambios aplicados:**
- Corregido "Score < 60 → BLOCKED" a "Score < 40 → BLOCKED" (alinea con trifásico 09.2)
- Agregada nueva fila para banda 40-59 → REVIEW_NEEDED

**Justificación (feedback Claude):**
"fila [ENTRY] ... URL muerta OR Score < 60 → BLOCKED contradice el trifásico de 09.2 (banda 40–59 debería ir a REVIEW_NEEDED, no BLOCKED)"

---

## 2. layer_1_run.py (Notion)

**Ubicación:** Layer_1/scripts/layer_1_run.py  
**Sección:** Fase 4 - Gate logic y Next Actions (líneas ~1018-1090)

### Parche A: Detección manual de Status=Postulado sin Gate_Decision=APPLIED

**Texto original (líneas ~1018-1028):**
```python
# v9.14.6: JD_Quality == "JD Completo" → priorizar Optimizar (CV-A ready)
jd_quality = txt(props.get("JD_Quality"))

if evaluate_rejection_status(status):
    decision = "REJECTED"
    next_action = "Post-Mortem"
    rejected_status_count += 1
elif evaluate_application_status(status):
    decision = "APPLIED"
    next_action = get_application_next_action(status)
    applied_count += 1
```

**Texto nuevo (reemplazar completo):**
```python
# v9.14.6: JD_Quality == "JD Completo" → priorizar Optimizar (CV-A ready)
jd_quality = txt(props.get("JD_Quality"))

# H9 FIX (Observabilidad Opción A): Detección manual de Status=Postulado sin Gate_Decision=APPLIED
if status == "Postulado" and current_gate != "APPLIED":
    print(f"  [OBSERVABILIDAD] {item['id'][:8]}: Status=Postulado pero Gate_Decision={current_gate or '(vacío)'} → sugerencia manual: establecer Gate_Decision=APPLIED")

if evaluate_rejection_status(status):
    decision = "REJECTED"
    next_action = "Post-Mortem"
    rejected_status_count += 1
elif evaluate_application_status(status):
    decision = "APPLIED"
    next_action = get_application_next_action(status)
    applied_count += 1
```

### Parche B: Agregar campo Last_Gate_Run (Observabilidad Opción A)

**Texto original (líneas ~1069-1090):**
```python
        changes = []
        if current_gate != decision:
            changes.append(f"Gate: {current_gate}->{decision}")
        if current_action != next_action:
            changes.append(f"Action: {current_action}->{next_action}")

        update = {
            "Gate_Decision": {"select": {"name": decision}},
            "Next_Action": {"select": {"name": next_action}}
        }

        if not DRY_RUN:
            try:
                client.pages.update(page_id=item["id"], properties=update)
                gate_updates += 1
                if changes:
                    empresa = txt(props.get("Marca")) or "Sin empresa"
                    gate_changes.append(f"[{item['id'][:8]}] {empresa}: {', '.join(changes)}")
            except Exception as e:
                print(f"X Error gate {item['id'][:8]}: {e}")
        else:
```

**Texto nuevo (reemplazar completo):**
```python
        changes = []
        if current_gate != decision:
            changes.append(f"Gate: {current_gate}->{decision}")
        if current_action != next_action:
            changes.append(f"Action: {current_action}->{next_action}")

        # H9 FIX (Observabilidad Opción A): Agregar Last_Gate_Run timestamp
        from datetime import datetime
        last_gate_run = datetime.now().isoformat()

        update = {
            "Gate_Decision": {"select": {"name": decision}},
            "Next_Action": {"select": {"name": next_action}},
            "Last_Gate_Run": {"date": {"start": last_gate_run}}
        }

        if not DRY_RUN:
            try:
                client.pages.update(page_id=item["id"], properties=update)
                gate_updates += 1
                if changes:
                    empresa = txt(props.get("Marca")) or "Sin empresa"
                    gate_changes.append(f"[{item['id'][:8]}] {empresa}: {', '.join(changes)}")
            except Exception as e:
                print(f"X Error gate {item['id'][:8]}: {e}")
        else:
```

**Cambios aplicados:**
- Parche A: Detección manual de Status=Postulado sin Gate_Decision=APPLIED con log de sugerencia
- Parche B: Agregado campo Last_Gate_Run (date) con timestamp ISO en cada actualización de gate

**Justificación:**
- Observabilidad Opción A: Campo único Last_Gate_Run por simplicidad inicial
- Transición APPLIED Opción B: Detección manual con sugerencia para preservar control del operador

---

## 3. Schema Tracker (Notion) — Agregar campo Last_Gate_Run

**Requiere:** Modificación manual del schema del Tracker (DB 442938be-fc42-828f-b72e-076818d65a5b)

### Acción: Agregar nuevo campo al schema

**Nombre del campo:** Last_Gate_Run  
**Tipo:** Date  
**Descripción:** Timestamp de última ejecución de gate logic (Fase 4) - Observabilidad H9

**Pasos:**
1. Abrir Tracker en Notion
2. Agregar nueva propiedad "Last_Gate_Run" con tipo Date
3. (Opcional) Agregar descripción del campo

---

## Instrucciones de Aplicación

### Kernel.md:
1. Abrir Documentación/ACTIVE/Kernel.md en Notion
2. Localizar sección 09.11 KERNEL:GATE-DECISION-011 (tabla de transición)
3. Reemplazar línea 503 con el "Texto nuevo" del Parche 1
4. Insertar nueva fila después de línea 503 con la segunda fila del "Texto nuevo"
5. Guardar cambios

### layer_1_run.py:
1. Abrir Layer_1/scripts/layer_1_run.py en Notion
2. Localizar sección Fase 4 (líneas ~1018-1090)
3. Aplicar Parche A (detección manual de Status=Postulado)
4. Aplicar Parche B (campo Last_Gate_Run)
5. Guardar cambios

### Schema Tracker:
1. Abrir Tracker en Notion
2. Agregar campo Last_Gate_Run (tipo Date) al schema
3. Guardar cambios

---

**Nota:** Estos parches corrigen problemas identificados por Claude en el feedback:
- KERNEL:GATE-DECISION-011 fila 3: alineado con trifásico 09.2
- Observabilidad H9: implementado con campo Last_Gate_Run
- Transición APPLIED: implementado con detección manual

**Archivos de referencia:**
- Kernel local: `/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Documentación/ACTIVE/Kernel.md`
- Código local: `/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/scripts/layer_1_run.py`
