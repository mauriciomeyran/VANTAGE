---
name: vantage-create-bug-task
description: Crea un nuevo ticket en el Bug Tracker o Task Tracker de VANTAGE. Usar cuando el operador reporta un defecto de sistema (Bug Tracker) o una tarea pendiente/mejora (Task Tracker) durante cualquier sesión. Ambos trackers son DBs de Notion distintas — no se deben confundir sus IDs.
---

## Convención de anuncio (KERNEL:SKILL-ANNOUNCE-CONVENTION)

Esta skill declara su propio verbo en gerundio/participio al abrir y cerrar su protocolo — nunca un mensaje genérico compartido ni el lenguaje de cierre del Bootstrap (`BOOTLOADED`):
- Apertura: `LOGGING TICKET...`
- Cierre: `TICKET LOGGED`

## Manejo de cero candidatos

No aplica a esta skill de forma directa (es creación puntual de un ticket, no un batch) — el caso relevante es: si el operador pide crear un ticket pero la clasificación (Bug vs Task) resulta ambigua incluso tras preguntar, no crear nada y reportar la ambigüedad sin ticket parcial.

## Contexto operativo (verificado contra KERNEL:TRACKER-SCHEMA-001)

Distinto del Tracker de vacantes (KERNEL:SCHEMA) — estos dos trackers gestionan trabajo interno del propio sistema VANTAGE: bugs, deuda técnica y tareas pendientes. Ninguno usa campos Class A/B del Tracker de vacantes.

**Clasificación (KERNEL:TRACKER-SCHEMA-001):**
- Reactivo (algo roto) → **Bug Tracker**
- Proactivo (trabajo/decisión pendiente) → **Tasks Tracker**

| Tracker | DB ID | COL ID |
|---|---|---|
| Bug Tracker | `36e938be-fc42-81f8-8c6f-000b6769ba03` | `36e938be-fc42-81bd-9e1f-dc360b3b45f5` |
| Tasks Tracker | `d2a65ca1-6a35-465d-bcff-b0d82dddd549` | — |

Campos reales confirmados en schema: `Bug`/título, `Fecha_Detección`, `Componente`, `Prioridad`, `Status`, `Next_Action`, `Notas`. **No existe campo `Tags`** en ninguno de los dos trackers — no inventar uno. No existe formato de ID secuencial (`BUG-0001`, etc.) — el identificador único de facto es el `page_id`/`url` que Notion asigna. No inventar formatos de ID.

**Niveles de Prioridad (KERNEL:TRACKER-SCHEMA-002, misma escala para ambos trackers):**

| Nivel | Criterio |
|---|---|
| CRÍTICO | El flujo punta a punta no puede completarse |
| ALTO | El flujo se completa forzando el sistema (workaround requerido) |
| MEDIO | Sin resolución en la semana, el flujo punta a punta se verá comprometido |
| BAJO | No bloquea operación — nice-to-have |

## Gancho con KERNEL:CENSUS-SYNC Regla 1

Si el ticket que se está creando documenta o anticipa un cambio de estado de un ID canónico (ej. un Bug que, al resolverse, hará que un ID pase de Stub→Ok en el Census), esta skill no ejecuta el re-run de `generate_census.py` en el momento de creación — ese disparo ocurre al cierre del ticket (ver `vantage-tidy-bug-task-tracker`, que sí lo ejecuta). Esta skill solo debe anotar el tag literal `[CENSUS-SYNC-R1]` (`KERNEL:CENSUS-SYNC` §20) en el campo `Notas` del ticket, para que `vantage-tidy-bug-task-tracker` lo detecte sin tener que inferirlo de nuevo.

## Procedimiento

1. **Clasificar**: ¿defecto de comportamiento (Bug) o tarea/mejora pendiente (Task)? Si es ambiguo, preguntar al operador antes de proceder — no asumir.
2. **Asignar Prioridad** usando exclusivamente la escala de 4 niveles arriba — no inventar niveles intermedios.
3. **Completar campos** según el schema real de cada tracker. No agregar campos inexistentes.
4. **Componente**: usar Capa real si aplica (`L1`, `L3`, `L4`, `Dashboard`) o nombre de módulo/script afectado.
5. **Dry Run**: presentar al operador el registro completo (todos los campos, incluida Prioridad clasificada) antes de escribir.
6. Esperar variante válida de `APROBAR_WRITE`: `APROBAR_WRITE` · `APROBAR` · `SÍ` · `sí` · `YEP` · `yep`. Eliminados por RAI-03: `Ok` · `Go` · `YES` · `yes` — nunca aceptar estos como autorización.
7. Ejecutar `notion-create-pages` con el `data_source_id`/DB ID correcto según el tracker elegido — verificar dos veces que no se está escribiendo en el tracker equivocado.
8. Fetch de verificación post-escritura. Si la caché de la misma sesión devuelve estado pre-write, reintentar una vez.

## Reglas de oro

- Nunca escribir en el tracker equivocado — confirmar Bug vs Task antes del Dry Run, no después.
- Nunca inventar un ID secuencial o campo no confirmado en el schema (ej. `Tags`).
- Class B (Score, Gate_Decision, VM_Scope, Role_Class, Match, Next_Action, Fetch, Fuente) es dominio exclusivo de Python en el Tracker de **vacantes** — no aplica a Bug/Task Tracker, que no tiene esos campos en absoluto.
- Whitelisting de campos (mitigación GAP-03, KERNEL:GATE-DECISION-003): toda llamada de escritura vía MCP debe declarar en el mismo Dry Run la whitelist de campos a escribir. Cualquier campo fuera de esa whitelist en el payload se remueve automáticamente antes de ejecutar, y se reporta al operador.

## Cierre de sesión standalone (KERNEL:CENSUS-SYNC, Regla 4)

Si esta skill se ejecuta fuera de una sesión formal `vantage-session-open`/`close` y produce una escritura real (post-`APROBAR_WRITE`), debe cerrar con un resumen breve de lo modificado — página creada, tracker afectado, Prioridad asignada — antes de terminar el turno. Esto no reabre aprobaciones ya otorgadas; solo consolida lo que quedó escrito, consistente con el reporte de cierre que exige esa Regla para cualquier sesión con cambios a documentación o bases de datos.

---

## Fuentes verificadas (sesión 2026-07-19)

IDs de DB/COL de Bug y Tasks Tracker: confirmados contra `SP:CEDULA-DIGITAL` (System Prompt, Notion, fetch directo) tras corrección de un par DB/COL invertido detectado en esta misma sesión. Escala de Prioridad (4 niveles): confirmada contra `KERNEL:TRACKER-SCHEMA-002` (Kernel, fetch directo) y `SP:SCHEMA`. Ausencia de campo `Tags` y de ID secuencial: confirmada contra schema vivo de ambos trackers (Notion, fetch directo) — no inferida.
