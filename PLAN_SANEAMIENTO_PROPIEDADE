# Plan de Trabajo — Saneamiento y Optimización de Propiedades del Tracker

**Fecha:** 2026-07-05  
**Objetivo:** Eliminar redundancias, consolidar lógica de cálculo, y reordenar el pipeline de propiedades del tracker VANTAGE_TRACKER  
**Alcance:** Layer 1 (layer_1_run.py), propiedades de Notion, y scripts relacionados

---

## Resumen Ejecutivo

**Problema principal:** El pipeline actual escribe las mismas propiedades múltiples veces en diferentes pasos, no refleja dependencias lógicas, y mantiene campos redundantes que no aportan valor operativo.

**Impacto esperado:**
- Reducción de llamadas a API de Notion (~40% menos writes)
- Eliminación de confusión sobre qué valor es "correcto"
- Pipeline más mantenible y entendible
- Schema más limpio y enfocado

**Estimado esfuerzo:** 2-3 días de desarrollo + testing

---

## Bloque 1 — Decisiones de Schema (Deben tomarse primero)

| # | Tipo | Prioridad | Descripción | Impacto | Dependencias | Riesgo si no se atiende | Fix/acción propuesta | Complejidad |
|---|------|-----------|-------------|---------|--------------|------------------------|-------------|
| 1 | Decisión | CRÍTICA | ¿Eliminar campo `Match`? | Schema simplificado | Ninguna | Campo redundante permanece, confusión | Eliminar Match de schema de Notion, remover de todos los scripts | M |
| 2 | Decisión | CRÍTICA | ¿Eliminar campo `Prioridad`? | Schema simplificado | Ninguna | Campo redundante permanece, confusión | Eliminar Prioridad de schema de Notion, remover de todos los scripts | M |
| 3 | Decisión | MEDIA | ¿Mantener `Fuente` en schema o mover a análisis offline? | Schema enfocado | Ninguna | Campo no crítico ocupa espacio | Opción A: Mantener / Opción B: Eliminar y calcular solo en análisis | S |
| 4 | Decisión | MEDIA | ¿Consolidar `Fetch` a una sola validación? | Eliminar redundancia | Ninguna | Doble validación continua | Elegir: PASO 0 (URL Gate) o PASO 2 (URL Re-check) | S |

---

## Bloque 2 — Eliminación de Props Redundantes

| # | Tipo | Prioridad | Descripción | Impacto | Dependencias | Riesgo si no se atiende | Fix/acción propuesta | Complejidad |
|---|------|-----------|-------------|---------|--------------|------------------------|-------------|
| 5 | Deuda técnica | ALTA | Eliminar `Match` de layer_1_run.py | Eliminar redundancia | Decisión #1 | Código mantiene lógica innecesaria | Remover get_match_level_v6(), eliminar update_props["Match"] | S |
| 6 | Deuda técnica | ALTA | Eliminar `Prioridad` de layer_1_run.py | Eliminar redundancia | Decisión #2 | Código mantiene lógica innecesaria | Remover mapeo Score→Prioridad | S |
| 7 | Deuda técnica | MEDIA | Eliminar `Fuente` de layer_1_run.py (opcional) | Simplificar pipeline | Decisión #3 | Campo se calcula innecesariamente | Remover PASO 0.5 si se decide eliminar | S |
| 8 | Deuda técnica | BAJA | Eliminar `Match` y `Prioridad` de otros scripts | Consistencia | #5, #6 | Inconsistencia entre scripts | Buscar y eliminar referencias en gate_logic.py, assign_next_action.py, etc. | M |

---

## Bloque 3 — Consolidación de Escritura de Props

| # | Tipo | Prioridad | Descripción | Impacto | Dependencias | Riesgo si no se atiende | Fix/acción propuesta | Complejidad |
|---|------|-----------|-------------|---------|--------------|------------------------|-------------|
| 9 | Bug | ALTA | Consolidar `Gate_Decision` a una sola escritura | Eliminar sobrescritura | Ninguna | Confusión sobre valor correcto | Escribir Gate_Decision solo en PASO 3 (Gate Logic), remover de PASO 0 y 1.5 | M |
| 10 | Bug | ALTA | Consolidar `Status` a una sola escritura | Eliminar sobrescritura | Ninguna | Confusión sobre valor correcto | Escribir Status solo al final del pipeline (PASO 5), remover de PASO 0 y 1.5 | M |
| 11 | Bug | ALTA | Consolidar `Next_Action` a una sola escritura | Eliminar sobrescritura | Ninguna | Confusión sobre valor correcto | Escribir Next_Action solo en PASO 3 (Gate Logic), remover de PASO 0 y 1.5 | M |
| 12 | Bug | MEDIA | Consolidar `Fetch` a una sola validación | Eliminar redundancia | Decisión #4 | Doble validación continúa | Elegir una validación y eliminar la otra | M |

---

## Bloque 4 — Reordenamiento del Pipeline

| # | Tipo | Prioridad | Descripción | Impacto | Dependencias | Riesgo si no se atiende | Fix/acción propuesta | Complejidad |
|---|------|-----------|-------------|---------|--------------|------------------------|-------------|
| 13 | Refactor | ALTA | Reordenar pasos en layer_1_run.py | Reflejar dependencias lógicas | #9, #10, #11, #12 | Pipeline no refleja lógica real | Nuevo orden: FASE 1 (Clasificación) → FASE 2 (Validación) → FASE 3 (Scoring) → FASE 4 (Gate Logic) → FASE 5 (Estado) | L |
| 14 | Refactor | MEDIA | Mover `Source_Type` auto-asignación a ingestión | Lógica correcta | Ninguna | Campo se calcula en lugar equivocado | Implementar en feed_processor.py y layer_3_mail.py, remover de layer_1_run.py | M |
| 15 | Refactor | BAJA | Actualizar comentarios y documentación | Mantenibilidad | #13 | Documentación desactualizada | Actualizar comentarios en layer_1_run.py para reflejar nuevo orden | S |

---

## Bloque 5 — Validación y Testing

| # | Tipo | Prioridad | Descripción | Impacto | Dependencias | Riesgo si no se atiende | Fix/acción propuesta | Complejidad |
|---|------|-----------|-------------|---------|--------------|------------------------|-------------|
| 16 | Calidad | ALTA | Test de regresión para scoring | Prevenir bugs | #5, #6 | Scoring podría romperse sin tests | Crear test unitario para calculate_score_v6() con casos edge | M |
| 17 | Calidad | ALTA | Test de regresión para gate logic | Prevenir bugs | #9, #10, #11 | Gate logic podría romperse sin tests | Crear test unitario para gate() con todos los casos | M |
| 18 | Calidad | MEDIA | Test de integración de pipeline completo | Prevenir bugs | #13 | Pipeline completo podría romperse | Crear test que simula pipeline completo con mocks | L |
| 19 | Calidad | BAJA | Validar que props eliminadas no rompen scripts | Prevenir bugs | #5, #6, #7, #8 | Scripts podrían tener referencias huérfanas | Buscar referencias a Match/Prioridad en todo el codebase | S |

---

## Orden de Ejecución Recomendado

### FASE 1 — Decisiones (1 día)
1. Decisión #1: Eliminar Match
2. Decisión #2: Eliminar Prioridad
3. Decisión #3: Fuente (mantener o eliminar)
4. Decisión #4: Consolidar Fetch

### FASE 2 — Eliminación de redundancias (0.5 días)
5. Tarea #5: Eliminar Match de layer_1_run.py
6. Tarea #6: Eliminar Prioridad de layer_1_run.py
7. Tarea #7: Eliminar Fuente (si aplica)
8. Tarea #8: Eliminar Match/Prioridad de otros scripts

### FASE 3 — Consolidación (1 día)
9. Tarea #9: Consolidar Gate_Decision
10. Tarea #10: Consolidar Status
11. Tarea #11: Consolidar Next_Action
12. Tarea #12: Consolidar Fetch

### FASE 4 — Reordenamiento (1 día)
13. Tarea #13: Reordenar pasos en layer_1_run.py
14. Tarea #14: Mover Source_Type a ingestión
15. Tarea #15: Actualizar documentación

### FASE 5 — Validación (0.5 días)
16. Tarea #16: Test scoring
17. Tarea #17: Test gate logic
18. Tarea #18: Test integración
19. Tarea #19: Validar referencias huérfanas

---

## Detalle de Implementación

### Tarea #9: Consolidar Gate_Decision
**Estado actual:** Escrito en PASO 0 (bypass), PASO 1.5 (misfit), PASO 3 (gate logic)

**Cambio propuesto:**
- PASO 0: NO escribir Gate_Decision (solo leer para bypass)
- PASO 1.5: NO escribir Gate_Decision (solo usar para limpieza)
- PASO 3: Escribir Gate_Decision como única fuente de verdad

**Archivos a modificar:**
- layer_1_run.py (líneas 562-565, 770, 917)

**Testing:**
- Verificar que bypass funcione sin escribir Gate_Decision
- Verificar que misfit cleanup funcione sin escribir Gate_Decision
- Verificar que gate logic final sea correcto

---

### Tarea #10: Consolidar Status
**Estado actual:** Escrito en PASO 0 (URL Gate), PASO 1.5 (misfit)

**Cambio propuesto:**
- PASO 0: NO escribir Status (solo leer para skip)
- PASO 1.5: NO escribir Status (solo usar para limpieza)
- Nueva FASE 5: Escribir Status al final basado en Gate_Decision y otros factores

**Archivos a modificar:**
- layer_1_run.py (líneas 594, 769, nueva lógica FASE 5)

**Testing:**
- Verificar que status se calcule correctamente al final
- Verificar que misfit cleanup funcione sin escribir Status

---

### Tarea #11: Consolidar Next_Action
**Estado actual:** Escrito en PASO 0 (URL Gate), PASO 1.5 (misfit), PASO 3 (gate logic)

**Cambio propuesto:**
- PASO 0: NO escribir Next_Action (solo leer para skip)
- PASO 1.5: NO escribir Next_Action (solo usar para limpieza)
- PASO 3: Escribir Next_Action como única fuente de verdad

**Archivos a modificar:**
- layer_1_run.py (líneas 595, 771, 918)

**Testing:**
- Verificar que Next_Action se calcule correctamente en gate logic
- Verificar que protección de estados terminales funcione

---

### Tarea #13: Reordenar Pipeline
**Orden actual:**
- PASO 0: URL Gate (pre-scoring)
- PASO 0.5: Fuente
- Auto: Source_Type
- PASO 1: Scoring
- PASO 1.5: Limpieza fit
- PASO 2: URL Re-check
- PASO 3: Gate Logic
- PASO 4: Análisis patrones

**Nuevo orden propuesto:**
- FASE 1: Clasificación (VM_Scope, Role_Class)
- FASE 2: Validación (Fetch)
- FASE 3: Scoring (Score)
- FASE 4: Gate Logic (Gate_Decision, Next_Action)
- FASE 5: Estado Final (Status)

**Archivos a modificar:**
- layer_1_run.py (reestructurar completo)

**Testing:**
- Test de integración completo
- Verificar que dependencias se respeten

---

## Métricas de Éxito

### Antes
- Llamadas a API de Notion por run: ~20-30 (múltiples escrituras de misma prop)
- Props redundantes: 3 (Match, Prioridad, Fuente)
- Sobrescritura de props: 4 (Gate_Decision, Status, Next_Action, Fetch)

### Después
- Llamadas a API de Notion por run: ~10-15 (una escritura por prop)
- Props redundantes: 0
- Sobrescritura de props: 0

---

## Riesgos y Mitigaciones

### Riesgo #1: Romper gate logic existente
**Mitigación:** Tests de regresión (tareas #16, #17)
**Rollback:** Mantener branch de backup con versión actual

### Riesgo #2: Scripts externos dependen de props eliminadas
**Mitigación:** Búsqueda de referencias (tarea #19)
**Rollback:** Revertir eliminación si se encuentran dependencias críticas

### Riesgo #3: Schema de Notion no se puede modificar fácilmente
**Mitigación:** Decisión #1 y #2 son manuales en Notion
**Rollback:** Mantener campos como "en desuso" si no se pueden eliminar

---

## Definición de Terminado

- [ ] Decisiones #1-4 tomadas y documentadas
- [ ] Props redundantes eliminadas de todos los scripts
- [ ] Sobrescritura de props eliminada
- [ ] Pipeline reordenado según nuevo orden lógico
- [ ] Tests de regresión pasando
- [ ] Documentación actualizada
- [ ] Run de prueba exitoso en data de staging

---

## Apéndice: Scripts Afectados

### Scripts que modifican directamente layer_1_run.py
- layer_1_run.py (principal)

### Scripts que podrían tener referencias a props eliminadas
- gate_logic.py
- assign_next_action.py
- cleanup_misfits.py
- source_analytics.py
- consolidate_duplicates.py
- agent_api.py
- status_report.py

### Scripts que leen props del tracker
- query_layer.py
- context_layer.py
- resolver_layer_v1.py
- generate_entity_index_v2.py
- fetch_hashes.py

---

**FIN DEL PLAN DE TRABAJO**
