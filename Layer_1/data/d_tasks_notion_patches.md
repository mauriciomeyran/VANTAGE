# Parches para Tareas Técnicas D-001 a D-004

## 1. D-001 — STATUS_TERMINAL_MAP en gate_logic.py

**Ubicación:** Layer_1/scripts/gate_logic.py  
**Sección:** Líneas 17-21

### Parche: Agregar "Expirada" a STATUS_TERMINAL_MAP

**Texto original:**
```python
STATUS_TERMINAL_MAP = {
    "Postulado": "APPLIED",
    "Rechazado": "REJECTED",
}
```

**Texto nuevo (reemplazar completo):**
```python
STATUS_TERMINAL_MAP = {
    "Postulado": "APPLIED",
    "Rechazado": "REJECTED",
    "Expirada": "EXPIRADA",  # D-001 FIX: Alineado con KERNEL:GATE-DECISION-010 que documenta "Expirada" como criterio de terminalidad por Status
}
```

**Justificación:**
- Consistencia arquitectónica con KERNEL:GATE-DECISION-010
- Documento Kernel documenta "Expirada" como criterio de terminalidad por Status
- Código actual solo protege vía TERMINAL_ACTIONS (Next_Action), creando inconsistencia

---

## 2. D-002 — Integrar class_b_guard en dashboard_notion.py

**Ubicación:** Dashboard/scripts/dashboard_notion.py  
**Sección:** Líneas 124-129

### Parche: Integrar class_b_guard como middleware

**Texto original:**
```python
    if not properties:
        return {'success': False, 'error': 'PATCH_EMPTY'}

    try:
        client.pages.update(page_id=page_id, properties=properties)
        return {'success': True, 'error': None}
```

**Texto nuevo (reemplazar completo):**
```python
    if not properties:
        return {'success': False, 'error': 'PATCH_EMPTY'}

    # D-002 FIX (GAP-003): Integrar class_b_guard como middleware antes de escritura
    # Importar class_b_guard desde Layer_1/scripts
    import sys, os
    sys.path.insert(0, os.path.expanduser("~/Documents/03 Projects/VANTAGE/Layer_1/scripts"))
    from class_b_guard import guard_write_payload

    # Aplicar guard a las properties antes de enviar a Notion
    guard_result = guard_write_payload(properties, strict_unknown=True)
    if not guard_result.is_clean:
        print(f"[CLASS_B_GUARD] {guard_result.report()}")
        # Fallar fuertemente si hay campos Class B en el payload
        return {'success': False, 'error': 'CLASS_B_BLOCKED'}
    
    # Usar payload limpio
    properties = guard_result.clean_payload

    try:
        client.pages.update(page_id=page_id, properties=properties)
        return {'success': True, 'error': None}
```

**Justificación:**
- Cierra GAP-003: escritura MCP sin guard Class B es hueco de seguridad
- class_b_guard ya existe con lógica correcta, solo requiere integración
- Fail-closed: payload con campos Class B rechazado con error CLASS_B_BLOCKED

---

## 3. D-003 — Agregar "Postulando" a _PROTECTED_STATUSES

**Ubicación:** Layer_1/scripts/profile_fit.py  
**Sección:** Líneas 38-41

### Parche: Agregar "Postulando" a _PROTECTED_STATUSES

**Texto original:**
```python
_PROTECTED_STATUSES = frozenset({
    "Postulado", "En proceso", "Negociando", "Sin respuesta", "Contratado",
})
```

**Texto nuevo (reemplazar completo):**
```python
_PROTECTED_STATUSES = frozenset({
    "Postulado", "En proceso", "Negociando", "Sin respuesta", "Contratado",
    "Postulando",  # D-003 FIX: Protege estado activo de aplicación (puede durar días)
})
```

**Justificación:**
- "Postulando" no es transitorio breve — puede durar días mientras espera respuesta del empleador
- Sin protección, re-run del pipeline podría cambiar Score/Gate Decision en registro activo en aplicación
- Consistente con otros estados protegidos que duran días/semanas

---

## 4. D-004 — Logging de protección de terminales en gate_logic()

**Ubicación:** Layer_1/scripts/gate_logic.py  
**Sección:** Líneas 24-47 (función gate_logic completa)

### Parche: Agregar logging cuando retorna valor terminal

**Texto original:**
```python
def gate_logic(entry):
    """
    Protección de estados terminales.

    Args:
        entry: dict con al menos "Status" y "Next_Action".

    Returns:
        str  — valor terminal ("APPLIED", "REJECTED", "Archivar", "Expirada")
               si el registro NO debe ser recalculado.
        None — el registro es elegible para recálculo por gate().
    """
    status = entry.get("Status") or ""
    if status in STATUS_TERMINAL_MAP:
        return STATUS_TERMINAL_MAP[status]

    current_action = entry.get("Next_Action") or ""
    if current_action in TERMINAL_ACTIONS:
        return current_action

    return None
```

**Texto nuevo (reemplazar completo):**
```python
def gate_logic(entry):
    """
    Protección de estados terminales.

    Args:
        entry: dict con al menos "Status" y "Next_Action".

    Returns:
        str  — valor terminal ("APPLIED", "REJECTED", "Archivar", "Expirada")
               si el registro NO debe ser recalculado.
        None — el registro es elegible para recálculo por gate().
    """
    status = entry.get("Status") or ""
    if status in STATUS_TERMINAL_MAP:
        terminal_value = STATUS_TERMINAL_MAP[status]
        # D-004 FIX: Logging de protección de terminales para observabilidad
        entry_id = entry.get("id", "unknown")[:8] if "id" in entry else "unknown"
        current_action = entry.get("Next_Action") or ""
        print(f"[gate_logic] PROTECTED: {entry_id} → {terminal_value} (Status={status}, Next_Action={current_action})")
        return terminal_value

    current_action = entry.get("Next_Action") or ""
    if current_action in TERMINAL_ACTIONS:
        # D-004 FIX: Logging de protección de terminales para observabilidad
        entry_id = entry.get("id", "unknown")[:8] if "id" in entry else "unknown"
        print(f"[gate_logic] PROTECTED: {entry_id} → {current_action} (Status={status}, Next_Action={current_action})")
        return current_action

    return None
```

**Justificación:**
- Mejora observabilidad de protección de terminales en pipeline runs
- Permite identificar qué registros fueron protegidos y por qué criterio
- Format: `[gate_logic] PROTECTED: {entry_id} → {terminal_value} (Status={status}, Next_Action={current_action})`

---

## Instrucciones de Aplicación

### gate_logic.py:
1. Abrir Layer_1/scripts/gate_logic.py en Notion
2. Aplicar Parche D-001 (líneas 17-21)
3. Aplicar Parche D-004 (líneas 24-47)
4. Guardar cambios

### profile_fit.py:
1. Abrir Layer_1/scripts/profile_fit.py en Notion
2. Aplicar Parche D-003 (líneas 38-41)
3. Guardar cambios

### dashboard_notion.py:
1. Abrir Dashboard/scripts/dashboard_notion.py en Notion
2. Aplicar Parche D-002 (líneas 124-143)
3. Guardar cambios

### Verificación:
1. Ejecutar: `cd Layer_1 && source .venv/bin/activate && python -m pytest tests/test_gate_logic.py -v`
2. Esperar: 45 tests pasando

---

**Archivos de referencia:**
- gate_logic.py local: `/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/scripts/gate_logic.py`
- profile_fit.py local: `/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/scripts/profile_fit.py`
- dashboard_notion.py local: `/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Dashboard/scripts/dashboard_notion.py`
- class_b_guard.py: `/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/scripts/class_b_guard.py`
