---
name: vantage-tidy-bug-task-tracker
description: "Marca tickets del Bug Tracker o Task Tracker como Archivar = True en dos escenarios confirmados por el operador — resolución directa o resolución detectada indirectamente vía Change Log. Requiere Dry Run y APROBAR_WRITE antes de marcar cualquier archivo"
---

---
name: vantage-tidy-bug-task-tracker
description: **Marca** tickets del Bug Tracker o Task Tracker para archivado manual, en dos escenarios confirmados por el operador — resolución directa o resolución detectada indirectamente vía Change Log. Requiere Dry Run y APROBAR_WRITE antes de cualquier marcado.

---

## Convención de anuncio (KERNEL:SKILL-ANNOUNCE-CONVENTION)
- Apertura: `TIDYING TRACKER...`
- Cierre: `TRACKER TIDIED`

---

## IDs confirmados (KERNEL:TRACKER-SCHEMA-001)
   Tracker       | DB ID                          | COL ID                          |
 |---------------|--------------------------------|---------------------------------|
 | Bug Tracker   | `36e938be-fc42-81f8-8c6f-000b6769ba03` | `36e938be-fc42-81bd-9e1f-dc360b3b45f5` |
 | Tasks Tracker | `d2a65ca1-6a35-465d-bcff-b0d82dddd549`   | —                               |

---

## Escenarios de marcado
1. **Resolución directa**: el ticket está marcado como *resuelto/hecho* en su propio Status.
2. **Resolución indirecta detectada vía Change Log**: el Change Log (activo o Archivo) contiene evidencia de que un bug/task ya fue resuelto, pero no se registró en el tracker correspondiente.

---
## Procedimiento
1. Recorrer Bug Tracker y Task Tracker buscando Status en estado terminal (*resuelto/hecho*).
2. Cruzar contra el Change Log (últimas 10 entradas + Archivo si es necesario) para detectar resoluciones no registradas.
3. Clasificar cada candidato por Prioridad (CRÍTICO/ALTO/MEDIO/BAJO — KERNEL:TRACKER-SCHEMA-002).
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

---
## Reglas de oro
- Nunca borrar — siempre **marcar** preservando el historial.
- Nunca marcar sin Dry Run + `APROBAR_WRITE`.
- Si el Status no es terminal: marcar como *"candidato ambiguo"* y consultar al operador.
- Whitelisting de campos: declarar en Dry Run; campos fuera de whitelist se reportan.
- **Sin reversión automática**: corrección manual (desmarcar `Archivar` en el original).

---
## Cierre de sesión (KERNEL:CENSUS-SYNC, Regla 4)
Post-`APROBAR_WRITE`, reportar:
- Total de tickets marcados por escenario (1 directo / 2 vía Changelog).
- Si algún marcado disparó cambio de estado de ID (→ Regla 1 de CENSUS-SYNC).