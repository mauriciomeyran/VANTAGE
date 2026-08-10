# Parches de Documentación — Manual.md y Change Log.md

## 1. Manual.md (Notion)

**Ubicación:** Documentación/ACTIVE/Manual.md  
**Sección:** Paso 1 (líneas ~117-122)

### Parche: Actualización de vista Notion

**Texto original:**
```
### Paso 1
Verificar Notion
- READY-TO-APPLY: Espacio de trabajo diario (Score ≥ 60).
- REVIEW_NEEDED: Vacantes en rango Score 40–59.
- ARCHIVE: Score 0 o Status Expirada.
- ALL: Administración general.
```

**Texto nuevo (reemplazar completo):**
```
### Paso 1
Verificar Notion
- READY-TO-APPLY: Espacio de trabajo diario (Score ≥ 60, Gate_Decision=CREATE).
- REVIEW_NEEDED: Vacantes en rango Score 40–59 (Gate_Decision=REVIEW_NEEDED, requieren revisión manual).
- BLOCKED: Score < 40 o fail de scope/fetch (Gate_Decision=BLOCKED).
- ARCHIVE: Score 0 o Status Expirada.
- ALL: Administración general.
```

**Cambios aplicados:**
- READY-TO-APPLY: agregado "(Gate_Decision=CREATE)"
- REVIEW_NEEDED: agregado "(Gate_Decision=REVIEW_NEEDED, requieren revisión manual)"
- Agregada nueva línea: BLOCKED con descripción completa

---

## 2. Checklist.html (Notion)

**Ubicación:** Dashboard/Checklist.html  
**Sección:** Task #17 (línea ~772)

### Parche: Actualización de instrucción Ready-to-Apply

**Texto original:**
```html
<span class="task-text">Abrir vista Ready-to-Apply en Notion y confirmar vacantes con Score ≥ 60 disponibles para el ciclo de aplicación.</span>
```

**Texto nuevo (reemplazar completo):**
```html
<span class="task-text">Abrir vista Ready-to-Apply en Notion y confirmar vacantes con Score ≥ 60 (Gate_Decision=CREATE) disponibles para el ciclo de aplicación. Revisar también vista REVIEW_NEEDED (Score 40-59) para candidatos de calidad borderline.</span>
```

**Cambios aplicados:**
- Agregado "(Gate_Decision=CREATE)" después de Score ≥ 60
- Agregada instrucción: "Revisar también vista REVIEW_NEEDED (Score 40-59) para candidatos de calidad borderline."

---

## 3. Change Log.md (Notion)

**Ubicación:** Documentación/ACTIVE/Change Log.md  
**Sección:** Inicio del documento (líneas 1-4)

### Parche: Nueva entrada v9.18.0 al inicio

**Texto original:**
```
# V | CHANGELOG

---
Tipo: [DOC] [FIX]
```

**Texto nuevo (reemplazar completo):**
```
# V | CHANGELOG

---
Tipo: [FIX] [INFRA]
Título: H1 — Implementación de umbral de Score en gate() (KERNEL:GATE-DECISION-002 / GATE-DECISION-011)
Contexto: Auditoría de conformidad/drift de VANTAGE (sesión arena.ia + Claude, 2026-08-10, GitHub Issue #1, H1) detectó que gate() decidía solo por fetch + VM_Scope + Role_Class y nunca leía Score, violando el contrato del Kernel que define bandas: ≥60 CREATE · 40-59 Para Revisar · <40 BLOCKED. Evidencia: 31/36 filas CREATE con Score<60 en snapshot, mientras Manual/Checklist filtraban por Score≥60.
Cambios:
- layer_1_run.py:457-483 — gate() implementado con umbral de Score: score≥60 → CREATE, score≥40 → REVIEW_NEEDED, score<40 → BLOCKED. Score=None → REVIEW_NEEDED (golden rule: no pérdida silenciosa por dato faltante).
- test_gate_logic.py — actualizado para reflejar contrato actual de gate_logic() (solo protección de terminales) + 9 tests nuevos de Score Band (TestGateScoreBand).
- Manual.md — actualizado para incluir banda REVIEW_NEEDED (Score 40-59) y BLOCKED (Score<40).
- Checklist.html — actualizado para mencionar vista REVIEW_NEEDED en flujo de trabajo.
IDs afectados: Tracker 596938befc42836baea7814a1491bd47 — 9 filas cambiadas de CREATE→REVIEW_NEEDED (Score 40-50), 8 filas permanecen CREATE (Score≥60). Ready-to-Apply (≥60): 8 filas, alineado con contrato.
Write-Back Verification: Tests pasando (41/41), dry-run confirmado, aplicación exitosa al Tracker vivo.
Pendiente: avisar en GitHub Issue #1; actualizar Task Tracker (3b8938be-fc42-8130-b47a-f0150c2502cd) con Status→Hecho y solución documentada.
Versión actualizada: 9.18.0 (CHANGELOG). Resto de fundacionales permanece en v9.17.1 hasta vversions --sync.
---
Tipo: [DOC] [FIX]
```

**Cambios aplicados:**
- Insertada nueva entrada completa v9.18.0 al inicio del Change Log
- Documentado contexto, cambios realizados, IDs afectados, verificación y versión

---

## Instrucciones de Aplicación

### Manual.md:
1. Abrir Documentación/ACTIVE/Manual.md en Notion
2. Localizar sección "Paso 1 - Verificar Notion"
3. Reemplazar el texto completo con el "Texto nuevo" del parche
4. Guardar cambios

### Checklist.html:
1. Abrir Dashboard/Checklist.html en Notion
2. Localizar Task #17 (línea con "Abrir vista Ready-to-Apply...")
3. Reemplazar el contenido del `<span class="task-text">` con el "Texto nuevo"
4. Guardar cambios

### Change Log.md:
1. Abrir Documentación/ACTIVE/Change Log.md en Notion
2. Al inicio del documento, después de "# V | CHANGELOG" y "---"
3. Insertar todo el contenido de la entrada v9.18.0 del "Texto nuevo"
4. Asegurar que el siguiente "---" separa esta entrada de la entrada anterior v9.17.1
5. Guardar cambios

---

**Nota:** Estos parches reflejan los cambios que ya fueron aplicados a los archivos locales. Aplicarlos en Notion asegura que la documentación en la nube esté sincronizada con el código actualizado.
