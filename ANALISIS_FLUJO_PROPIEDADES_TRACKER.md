# Análisis del Flujo de Cálculo de Propiedades del Tracker

**Fecha:** 2026-07-05  
**Objetivo:** Evaluar la lógica de cálculo de propiedades a cargo de Python en layer_1_run.py, identificar cuáles son relevantes, cuáles son "paja", y proponer un orden lógico.

---

## 1. Flujo Actual de Cálculo (layer_1_run.py)

### PASO 0: URL Gate (Pre-Scoring)
**Props que escribe:**
- `Gate_Decision` → "CREATE" (para bypass) o "BLOCKED"
- `Fetch` → "Bloqueado"
- `Status` → "Expirada"
- `Next_Action` → "Archivar"

**Lógica:**
- Bypass automático para Source_Type in ["Inbound", "Referencia", "Networking"]
- Validación de URL: JD > 100 chars = bypass, agregadores = bypass, career pages = validación CTA
- Si falla: marca como Bloqueado/Expirada/Archivar

**Evaluación:**
- **Relevancia:** ALTA — Es el primer filtro de calidad
- **Lógica sólida:** SÍ — Prioridad absoluta al JD es correcta
- **Problema:** Sobrescribe Gate_Decision antes del scoring completo

---

### PASO 0.5: Asignación de Fuente
**Props que escribe:**
- `Fuente` → "Agregador" o "Career Page Oficial"

**Lógica:**
- `determine_fuente(url)` basado en dominio (linkedin.com, indeed.com, etc.)

**Evaluación:**
- **Relevancia:** MEDIA — Útil para análisis pero no crítico para operación
- **Lógica sólida:** SÍ — Simple y efectiva
- **Problema:** Se calcula después del URL Gate pero no depende de él

---

### Auto-asignación Source_Type
**Props que escribe:**
- `Source_Type` → "Vacante" (si está vacío y tiene URL)

**Lógica:**
- Si Source_Type está vacío y existe URL, asignar "Vacante"

**Evaluación:**
- **Relevancia:** ALTA — Campo crítico para gate logic
- **Lógica sólida:** SÍ — Fix necesario por bugs previos
- **Problema:** Debería ser parte de la ingestión, no del pipeline

---

### PASO 1: Scoring v6.4
**Props que escribe:**
- `VM_Scope` → "Alto" o "Bajo"
- `Score` → 0-100 (número)
- `Role_Class` → "VM", "Pivote", "Otro"
- `Match` → "Muy Alto", "Alto", "Medio", "Bajo"

**Lógica:**
- `get_vm_scope(rol)`: keywords VM en título
- `get_role_class(rol)`: keywords en título
- `calculate_score_v6()`: Base +40, Visual +20, Company +15, Role +10, Recruiter +10, Innovation +5, Scale +5, Pivot +5, Agency +5, Luxury +5 (capped at 100)
- `get_match_level_v6()`: mapeo de Score a Match

**Evaluación:**
- **Relevancia:** ALTA — Core del sistema de priorización
- **Lógica sólida:** PARCIAL — Los pesos son arbitrarios, no basados en datos reales
- **Problema:** No hay feedback loop para ajustar pesos basado en resultados

---

### PASO 1.5: Limpieza por Fit/Exclusiones
**Props que escribe:**
- `Status` → "Expirada"
- `Gate_Decision` → "BLOCKED"
- `Next_Action` → "Archivar"

**Lógica:**
- `profile_misfit_reasons()`: exclusiones de rol, hard blocks de marca, fit VM
- `should_auto_cleanup()`: si status no está protegido y hay reasons

**Evaluación:**
- **Relevancia:** ALTA — Limpieza automática de ruido
- **Lógica sólida:** SÍ — Basado en reglas claras
- **Problema:** Sobrescribe Status/Gate_Decision ya calculados

---

### PASO 2: URL Re-check
**Props que escribe:**
- `Fetch` → "Accesible", "Bloqueado", "Parcial"

**Lógica:**
- `check_url()`: HEAD + GET con headers anti-bot
- Protecciones: no re-check si JD > 100 y ya Accesible, no re-check dominios problemáticos

**Evaluación:**
- **Relevancia:** MEDIA — Útil para detectar URLs expiradas
- **Lógica sólida:** SÍ — Protecciones inteligentes
- **Problema:** Redundante con PASO 0 (ya se validó URL)

---

### PASO 3: Gate Logic
**Props que escribe:**
- `Gate_Decision` → "CREATE", "BLOCKED", "APPLIED"
- `Next_Action` → "Re-check", "Reparar URL", "Verificar JD", "Archivar", "Follow-up", "Interview prep"

**Lógica:**
- `evaluate_application_status()`: si status es Postulado/En proceso/Negociando/Sin respuesta → APPLIED
- `gate()`: CREATE si (Fetch=Accesible/Parcial AND (VM_Scope=Alto OR Role_Class=Pivote))
- Protección: si ya tiene Next_Action, no modificar

**Evaluación:**
- **Relevancia:** ALTA — Decide qué hacer con cada vacante
- **Lógica sólida:** SÍ — Protección de estados terminales es correcta
- **Problema:** Sobrescribe Gate_Decision calculado en PASO 0 y PASO 1.5

---

### PASO 4: Análisis de Patrones
**Props que escribe:**
- Ninguno (solo análisis)

**Lógica:**
- `analyze_outcome_patterns()`: análisis estadístico de resultados

**Evaluación:**
- **Relevancia:** BAJA — Solo informativo, no afecta operación
- **Lógica sólida:** N/A — No escribe props
- **Problema:** No se usa para ajustar scoring (feedback loop faltante)

---

## 2. Problemas Identificados

### 2.1 Sobrescritura de Props
- `Gate_Decision` se escribe 3 veces (PASO 0, PASO 1.5, PASO 3)
- `Status` se escribe 2 veces (PASO 0, PASO 1.5)
- `Next_Action` se escribe 3 veces (PASO 0, PASO 1.5, PASO 3)
- `Fetch` se escribe 2 veces (PASO 0, PASO 2)

**Impacto:** Difícil de entender qué valor es "correcto", lógica fragmentada

### 2.2 Falta de Orden Lógico
El orden actual no refleja dependencias lógicas:
- `Fuente` se calcula después de URL Gate pero no depende de él
- `Source_Type` se auto-asigna después de URL Gate pero debería ser ingestión
- `VM_Scope`, `Role_Class`, `Score`, `Match` se calculan antes de Gate Logic pero Gate Logic depende de ellos
- `Fetch` se valida 2 veces (PASO 0 y PASO 2)

### 2.3 Props "Paja" (No Aportan Valor Operativo)
- `Match` — Es un mapeo de Score, no agrega información nueva
- `Prioridad` — Es un mapeo de Score (1-8), no se usa en gate logic
- `Fuente` — Útil para análisis pero no para operación diaria

---

## 3. Props por Categoría de Relevancia

### CRÍTICAS (Core del sistema)
1. **Source_Type** — Determina qué gate logic aplicar
2. **Status** — Estado del proceso
3. **Gate_Decision** — Decisión del gate
4. **Next_Action** — Acción a tomar
5. **Score** — Priorización (aunque weights arbitrarios)

### ÚTILES pero No Críticas
6. **Fetch** — Estado de URL (útil pero redundante)
7. **VM_Scope** — Clasificación VM (usado en gate logic)
8. **Role_Class** — Clasificación de rol (usado en gate logic)

### "PAJA" (Se pueden eliminar o simplificar)
9. **Match** — Mapeo de Score, no agrega valor
10. **Prioridad** — Mapeo de Score, no se usa en gate logic
11. **Fuente** — Solo para análisis, no afecta operación

### DE INGESTIÓN (No deberían calcularse en pipeline)
12. **hash** — Debe calcularse al crear (ya implementado en L3)
13. **Holding** — Debe venir del feed
14. **Location** — Debe venir del feed

---

## 4. Orden Lógico Propuesto

### Orden Basado en Dependencias

**FASE 1: Validación de Entrada (Pre-Calculo)**
1. `Source_Type` — Debe venir de ingestión, no calcularse
2. `hash` — Debe calcularse al crear (ya implementado)
3. Campos del feed: Rol, Marca, URL, JD, Holding, Location

**FASE 2: Clasificación (Inputs para Gate Logic)**
4. `VM_Scope` — Depende solo de Rol
5. `Role_Class` — Depende solo de Rol
6. `Fuente` — Depende de URL (pero no crítico)
7. `Fetch` — Validación de URL

**FASE 3: Scoring (Priorización)**
8. `Score` — Depende de Rol, Marca, JD, Contacto, VM_Scope, Role_Class

**FASE 4: Gate Logic (Decisión)**
9. `Gate_Decision` — Depende de Source_Type, Fetch, VM_Scope, Role_Class, Status
10. `Next_Action` — Depende de Gate_Decision, Status

**FASE 5: Estado Final**
11. `Status` — Depende de todo lo anterior

### Props que NO deberían calcularse en pipeline
- `Match` — Eliminar (es mapeo de Score)
- `Prioridad` — Eliminar (es mapeo de Score)
- `Fuente` — Opcional, mover a análisis offline

---

## 5. Recomendaciones

### 5.1 Eliminar/Simplificar
1. **Eliminar `Match`** — Es redundante con Score
2. **Eliminar `Prioridad`** — Es redundante con Score
3. **Simplificar `Fuente`** — Calcular solo cuando se necesite análisis, no en cada run

### 5.2 Consolidar Escritura de Props
1. **Unificar escritura de Gate_Decision** — Escribir solo en PASO 3 (Gate Logic)
2. **Unificar escritura de Status** — Escribir solo al final del pipeline
3. **Unificar escritura de Next_Action** — Escribir solo en PASO 3 (Gate Logic)
4. **Unificar validación de Fetch** — Hacer solo una vez (PASO 0 o PASO 2, no ambos)

### 5.3 Reordenar Pipeline
**Nuevo orden propuesto:**
1. Validación de entrada (Source_Type, hash)
2. Clasificación (VM_Scope, Role_Class, Fuente)
3. Scoring (Score)
4. Gate Logic (Gate_Decision, Next_Action)
5. Estado final (Status)

### 5.4 Implementar Feedback Loop
1. **Tracking de outcomes** — Agregar campo "Outcome" (Contratado/Rechazado/Sin respuesta)
2. **Análisis de effectiveness** — Calcular false positives/negatives de gate logic
3. **Ajuste de pesos** — Ajustar scoring weights basado en outcomes históricos

---

## 6. Comparación: Orden Actual vs Orden Propuesto

| Orden Actual | Prop | Escribe | Depende de | Problema |
|--------------|------|---------|-------------|-----------|
| PASO 0 | Gate_Decision | ✓ | Source_Type, URL, JD | Sobrescribe después |
| PASO 0 | Fetch | ✓ | URL | Redundante con PASO 2 |
| PASO 0 | Status | ✓ | URL Gate | Sobrescribe después |
| PASO 0 | Next_Action | ✓ | URL Gate | Sobrescribe después |
| PASO 0.5 | Fuente | ✓ | URL | No crítico |
| Auto | Source_Type | ✓ | URL | Debería ser ingestión |
| PASO 1 | VM_Scope | ✓ | Rol | ✓ Correcto |
| PASO 1 | Score | ✓ | Rol, Marca, JD, Contacto | ✓ Correcto |
| PASO 1 | Role_Class | ✓ | Rol | ✓ Correcto |
| PASO 1 | Match | ✗ | Score | Redundante |
| PASO 1.5 | Status | ✓ | Fit/Exclusiones | Sobrescribe PASO 0 |
| PASO 1.5 | Gate_Decision | ✓ | Fit/Exclusiones | Sobrescribe PASO 0 |
| PASO 1.5 | Next_Action | ✓ | Fit/Exclusiones | Sobrescribe PASO 0 |
| PASO 2 | Fetch | ✓ | URL | Redundante con PASO 0 |
| PASO 3 | Gate_Decision | ✓ | Fetch, VM_Scope, Role_Class | Sobrescribe PASO 0, 1.5 |
| PASO 3 | Next_Action | ✓ | Gate_Decision, Status | Sobrescribe PASO 0, 1.5 |

| Orden Propuesto | Prop | Escribe | Depende de | Justificación |
|-----------------|------|---------|-------------|---------------|
| FASE 1 | Source_Type | ✗ (ingestión) | Feed | Debe venir de feed |
| FASE 1 | hash | ✗ (ingestión) | Feed/URL | Ya implementado en L3 |
| FASE 2 | VM_Scope | ✓ | Rol | Primera clasificación |
| FASE 2 | Role_Class | ✓ | Rol | Primera clasificación |
| FASE 2 | Fuente | ✓ (opcional) | URL | Solo si se necesita análisis |
| FASE 2 | Fetch | ✓ | URL | Validación única |
| FASE 3 | Score | ✓ | Rol, Marca, JD, Contacto, VM_Scope, Role_Class | Scoring |
| FASE 4 | Gate_Decision | ✓ | Source_Type, Fetch, VM_Scope, Role_Class, Status | Gate logic |
| FASE 4 | Next_Action | ✓ | Gate_Decision, Status | Acción a tomar |
| FASE 5 | Status | ✓ | Todo anterior | Estado final |
| - | Match | ✗ | Score | Eliminar (redundante) |
| - | Prioridad | ✗ | Score | Eliminar (redundante) |

---

## 7. Conclusión

### Props que Mantener
- **Core:** Source_Type, Status, Gate_Decision, Next_Action, Score
- **Clasificación:** VM_Scope, Role_Class
- **Validación:** Fetch (consolidado a una validación)

### Props que Eliminar
- **Redundantes:** Match, Prioridad
- **No críticos:** Fuente (opcional, mover a análisis offline)

### Nuevo Orden Lógico
1. Ingestión (Source_Type, hash)
2. Clasificación (VM_Scope, Role_Class)
3. Validación (Fetch)
4. Scoring (Score)
5. Gate Logic (Gate_Decision, Next_Action)
6. Estado Final (Status)

Este orden:
- Elimina sobrescritura de props
- Refleja dependencias lógicas
- Reduce "paja" y redundancia
- Hace el pipeline más mantenible y entendible
