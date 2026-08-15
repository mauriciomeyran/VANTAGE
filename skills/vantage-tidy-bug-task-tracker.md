---
name: vantage-tidy-bug-task-tracker
description: **Marca** tickets del Bug Tracker o Task Tracker para archivado manual, en dos escenarios confirmados por el operador — resolución directa o resolución detectada indirectamente vía Change Log. Requiere Dry Run y APROBAR_WRITE antes de cualquier marcado.
---

## Convención de anuncio (KERNEL:DOCUMENTATION-005)
- Apertura: `TIDYING TRACKER...`
- Cierre: `TRACKER TIDIED`

## Manejo de cero candidatos
Si ambos trackers reportan 0 tickets en estado terminal y el Change Log (últimas 10 entradas + Archivo si es necesario) no muestra evidencia de resoluciones no registradas, reportar "Trackers ya están en sync" y cerrar sin Dry Run ni escritura.

## Contexto operativo (verificado contra KERNEL:TRACKER-SCHEMA-001 y KERNEL:TRACKER-SCHEMA-002)

Distinto del Tracker de vacantes (KERNEL:SCHEMA) — estos dos trackers gestionan trabajo interno del propio sistema VANTAGE: bugs, deuda técnica y tareas pendientes. Ninguno usa campos Class A/B del Tracker de vacantes.

**Clasificación (KERNEL:TRACKER-SCHEMA-001):**
- Reactivo (algo roto) → **Bug Tracker**
- Proactivo (trabajo/decisión pendiente) → **Tasks Tracker**

**Schema de Bug Tracker (confirmado):**
| Propiedad | Tipo / valores válidos |
|---|---|
| `Bug` | título |
| `Fecha_Detección` | fecha |
| `Componente` | texto libre (L1, L3, L4, Dashboard, script específico) |
| `Prioridad` | select (4 CRÍTICO, 3 ALTO, 2 MEDIO, 1 BAJO) |
| `Status` | select (valores operativos actuales) |
| `Next_Action` | select (valores operativos actuales) |
| `Notas` | texto libre |
| `Archivar` | checkbox |

**Schema de Tasks Tracker (confirmado):**
| Propiedad | Tipo / valores válidos |
|---|---|
| `Task` | título |
| `Fecha_Detección` | fecha |
| `Componente` | texto libre |
| `Prioridad` | select (4 CRÍTICO, 3 ALTO, 2 MEDIO, 1 BAJO) |
| `Status` | select (valores operativos actuales) |
| `Next_Action` | select (valores operativos actuales) |
| `Notas` | texto libre |
| `Archivar` | checkbox |

**Niveles de Prioridad (KERNEL:TRACKER-SCHEMA-002, misma escala para ambos trackers):**
| Nivel | Criterio |
|---|---|
| 4 CRÍTICO | El flujo punta a punta no puede completarse |
| 3 ALTO | El flujo se completa forzando el sistema (workaround requerido) |
| 2 MEDIO | Sin resolución en la semana, el flujo punta a punta se verá comprometido |
| 1 BAJO | No bloquea operación — nice-to-have |

**Estados terminales considerados para marcado:**
- Status: valores que indiquen "resuelto", "hecho", "completado", "cerrado"
- Next_Action: valores que indiquen acción de cierre o archivo

No agregar propiedades fuera de estas listas sin confirmación nueva contra un export/fetch reciente.

**IDs confirmados (KERNEL:TRACKER-SCHEMA-001):**
| Tracker | DB ID | COL ID |
|---|---|---|
| Bug Tracker | `36e938be-fc42-81f8-8c6f-000b6769ba03` | `36e938be-fc42-81bd-9e1f-dc360b3b45f5` |
| Tasks Tracker | `d2a65ca1-6a35-465d-bcff-b0d82dddd549` | — |

## Escenarios de marcado
1. **Resolución directa**: el ticket está marcado como *resuelto/hecho* en su propio Status.
2. **Resolución indirecta detectada vía Change Log**: el Change Log (últimas 10 entradas + Archivo si es necesario) contiene evidencia de que un bug/task ya fue resuelto, pero no se registró en el tracker correspondiente.

## Procedimiento
1. Recorrer Bug Tracker y Task Tracker buscando Status en estado terminal (*resuelto/hecho*).
2. Cruzar contra el Change Log (últimas 10 entradas + Archivo si es necesario) para detectar resoluciones no registradas.
3. Clasificar cada candidato por Prioridad (4 CRÍTICO/3 ALTO/2 MEDIO/1 BAJO — KERNEL:TRACKER-SCHEMA-002).
4. Si no hay candidatos: informar *"sin candidatos de marcado en esta corrida"* y terminar.
5. Presentar **Dry Run**: tabla con columnas `Ticket | Escenario | Evidencia | Prioridad`.
6. Esperar `APROBAR_WRITE`.
7. **Ejecutar marcado**:
   - Para cada ticket: `notion-update-page` con payload:
     ```json
     {"properties": {"Archivar": {"checkbox": true}}}
     ```
8. **Verificación**:
   - Fetch de confirmación para validar que `Archivar == true`.
   - Si el ticket tiene el tag `[CENSUS-SYNC-R1]`, recomendar: `Ejecutar: generate_census.py`.

## Clasificación detallada de candidatos

Para cada candidato, clasificar según categoría antes de proponer acción:

| Categoría | Señal | Acción propuesta |
|---|---|---|
| Status terminal claro | Status contiene "resuelto", "hecho", "completado", "cerrado" | Marcar directamente |
| Status ambiguo | Status no es claramente terminal | Marcar como "candidato ambiguo" y consultar |
| Evidencia Changelog directa | Changelog menciona explícitamente el ticket ID o título | Marcar vía escenario 2 |
| Evidencia Changelog indirecta | Changelog menciona componente/tema relacionado | Marcar como "candidato ambiguo" y consultar |
| Ticket muy reciente (< 7 días) | Fecha de detección reciente | Omitir (puede estar en proceso) |
| Prioridad CRÍTICO/ALTO | 4 CRÍTICO o 3 ALTO | Priorizar en Dry Run |

## Whitelisting de campos

Solo el campo `Archivar` (checkbox) puede ser modificado por este skill.

**Campos permitidos para modificación:**
- `Archivar` (checkbox) — único campo que el skill puede escribir

**Campos de solo lectura (reportados, no modificados):**
- Todos los demás campos del schema (Bug/Task, Fecha_Detección, Componente, Prioridad, Status, Next_Action, Notas)

En Dry Run, declarar explícitamente: "Solo se modificará el campo Archivar". Cualquier modificación a otros campos se reportará como error.

## Referencias exactas a Kernel
- KERNEL:TRACKER-SCHEMA-001 — Clasificación de trackers (Bug vs Task)
- KERNEL:TRACKER-SCHEMA-002 — Niveles de Prioridad (4 CRÍTICO → 1 BAJO)
- KERNEL:DOCUMENTATION-005 — Convención de anuncio de skills
- KERNEL:CENSUS-SYNC §20 — Procedimiento para execute_census.py tras marcado con tag `[CENSUS-SYNC-R1]`

## Reglas de oro
- Nunca borrar — siempre **marcar** preservando el historial.
- Nunca marcar sin Dry Run + `APROBAR_WRITE`.
- Si el Status no es terminal: marcar como *"candidato ambiguo"* y consultar al operador.
- Whitelisting de campos: solo `Archivar` puede modificarse; otros campos son solo lectura.
- **Sin reversión automática**: corrección manual (desmarcar `Archivar` en el original).
- Si hay candidatos ambiguos: no forzar marcado sin aprobación explícita del operador.

## Procedimiento de validación post-escritura
1. Para cada ticket marcado, hacer fetch de confirmación para validar `Archivar == true`.
2. Si algún ticket falló marcado (API error, permiso denegado, etc.), reportar error específico.
3. Verificar que no se modificaron otros campos accidentalmente.
4. Si algún ticket tiene el tag `[CENSUS-SYNC-R1]` en Notas, recomendar ejecutar `generate_census.py`.
5. Reporte final de validación: "X tickets marcados exitosamente, Y tickets fallaron, Z requieren Census re-run".

## Cierre de sesión (KERNEL:CENSUS-SYNC, Regla 4)
Post-`APROBAR_WRITE`, reportar:
- Total de tickets marcados por escenario (1 directo / 2 vía Changelog).
- Total de tickets marcados por tracker (Bug Tracker / Task Tracker).
- Total de tickets marcados por prioridad (CRÍTICO/ALTO/MEDIO/BAJO).
- Si algún marcado disparó cambio de estado de ID (→ Regla 1 de CENSUS-SYNC): recomendar ejecutar `generate_census.py`.