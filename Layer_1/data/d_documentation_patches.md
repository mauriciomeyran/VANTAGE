# Parches de Documentación — D-001 a D-004 (Change Log.md)

## 1. Change Log.md (Notion)

**Ubicación:** Documentación/ACTIVE/Change Log.md  
**Sección:** Inicio del documento (líneas 1-4)

### Parche: Nueva entrada v9.21.0 al inicio

**Texto original:**
```
# V | CHANGELOG

---
Tipo: [FIX] [INFRA]
Título: H2 — Protección de terminalidad extendida a Score/Prioridad (KERNEL:GATE-DECISION-010 / GATE-DECISION-006)
```

**Texto nuevo (reemplazar completo):**
```
# V | CHANGELOG

---
Tipo: [FIX] [INFRA]
Título: Técnicas Adicionales — Protección de terminales, observabilidad y guard MCP (GAP-003)
Contexto: Decisiones operador post-auditoría para cerrar gaps técnicos identificados: D-001 (STATUS_TERMINAL_MAP inconsistente), D-002 (GAP-003 escritura MCP sin guard), D-003 (Postulando sin protección), D-004 (falta logging de terminales).
Cambios:
- gate_logic.py — STATUS_TERMINAL_MAP agregado "Expirada": "EXPIRADA" (D-001), alineado con KERNEL:GATE-DECISION-010 que documenta "Expirada" como criterio de terminalidad por Status.
- gate_logic.py — logging de protección de terminales agregado (D-004): formato "[gate_logic] PROTECTED: {entry_id} → {terminal_value} (Status={status}, Next_Action={current_action})".
- dashboard_notion.py — integrado class_b_guard como middleware antes de client.pages.update (D-002), cierra GAP-003: escritura MCP ahora protegida contra campos Class B, fail-closed con error CLASS_B_BLOCKED.
- profile_fit.py — agregado "Postulando" a _PROTECTED_STATUSES (D-003), protege estado activo de aplicación (puede durar días) contra re-cálculo.
IDs afectados: Ninguno nuevo — correcciones de gaps técnicos y mejoras de observabilidad.
Write-Back Verification: Tests pasando (45/45), GAP-003 cerrado, logging operativo en gate_logic().
Pendiente: aplicar parches en Notion via Littlebird; actualizar Change Log v9.21.0.
Versión actualizada: 9.21.0 (CHANGELOG). Resto de fundacionales permanece en v9.20.0 hasta vversions --sync.
---
Tipo: [FIX] [INFRA]
Título: H2 — Protección de terminalidad extendida a Score/Prioridad (KERNEL:GATE-DECISION-010 / GATE-DECISION-006)
```

**Cambios aplicados:**
- Insertada nueva entrada completa v9.21.0 al inicio del Change Log
- Documentado contexto, cambios realizados, IDs afectados, verificación y versión

---

## Instrucciones de Aplicación

### Change Log.md:
1. Abrir Documentación/ACTIVE/Change Log.md en Notion
2. Al inicio del documento, después de "# V | CHANGELOG" y "---"
3. Insertar todo el contenido de la entrada v9.21.0 del "Texto nuevo"
4. Asegurar que el siguiente "---" separa esta entrada de la entrada anterior v9.19.0
5. Guardar cambios

---

**Nota:** Este parche refleja los cambios que ya fueron aplicados al archivo local Change Log.md. Aplicarlo en Notion asegura que la documentación en la nube esté sincronizada con el código actualizado.

**Archivos de referencia:**
- Change Log local: `/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Documentación/ACTIVE/Change Log.md`
- Código modificado:
  - `/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/scripts/gate_logic.py` (D-001, D-004)
  - `/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Dashboard/scripts/dashboard_notion.py` (D-002)
  - `/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/scripts/profile_fit.py` (D-003)
