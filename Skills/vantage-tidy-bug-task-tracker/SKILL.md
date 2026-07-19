---
name: vantage-tidy-bug-task-tracker
description: Archiva tickets del Bug Tracker o Task Tracker en dos escenarios confirmados por el operador — resolución directa o resolución detectada indirectamente vía Change Log. Requiere Dry Run y APROBAR_WRITE antes de cualquier archivado.
---

## Convención de anuncio (KERNEL:SKILL-ANNOUNCE-CONVENTION)

- Apertura: `TIDYING TRACKER...`
- Cierre: `TRACKER TIDIED`

## IDs confirmados (KERNEL:TRACKER-SCHEMA-001)

| Tracker | DB ID | COL ID |
|---|---|---|
| Bug Tracker | `36e938be-fc42-81f8-8c6f-000b6769ba03` | `36e938be-fc42-81bd-9e1f-dc360b3b45f5` |
| Tasks Tracker | `d2a65ca1-6a35-465d-bcff-b0d82dddd549` | — |

## Limitación real de MCP (confirmada, Task jul-17 + Changelog v9.3.7)

**El archivado real de una página (`archived:true`) NO está expuesto por el MCP de Notion.** Esto redefine lo que esta skill puede hacer de principio a fin:

- Lo que el AI Component **sí puede hacer vía MCP**: (a) crear la copia del ticket en el Archivo correspondiente (`notion-create-pages`), y (b) actualizar el Status del ticket original a su valor terminal (`Resuelto`/`Hecho`) — dejando la fila original **visible pero marcada**, no oculta ni archivada de la vista activa.
- Lo que **requiere Terminal/httpx directo**, fuera del alcance de esta skill: el archivado real a nivel API (mover la página fuera de la vista activa). Si el operador quiere ese paso completado, la skill genera el comando de Terminal como parte de su reporte final — no lo ejecuta, solo lo entrega listo para copiar/pegar:

```bash
curl -X PATCH "https://api.notion.com/v1/pages/{PAGE_ID}" \
  -H "Authorization: Bearer $NOTION_TOKEN" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{"archived": true}'
```

Reemplazar `{PAGE_ID}` por el ID real de cada página original marcada en esta ejecución (uno por línea si son varias). Este patrón usa el endpoint estándar de páginas de la API de Notion (`archived: true` vía PATCH) — no ha sido confirmado contra el comando exacto que el operador ya usó en la sesión del 17 de julio (mencionado pero no capturado en la Task), así que debe tratarse como plantilla de referencia, no como comando verificado end-to-end.

- Consecuencia práctica: tras ejecutar esta skill, el ticket queda **duplicado en dos lugares** (original marcado + copia en Archivo) hasta que el operador corra el paso de Terminal. La skill debe declarar esto explícitamente en su reporte de cierre, no dejarlo implícito.

## Mapeo de campos no-1:1 (confirmado, Task jul-15)

Los destinos de archivo **no son schema idéntico** al tracker vivo — copiar campo por campo sin mapeo falla o pierde datos:

- **Archivo Bug Tracker** (`38b938be-fc42-8047-b820-d98f74c9d78b`): tiene `Fecha_Resolución`, `Solución`, `Prioridad 1` (select) — campos que el Bug Tracker vivo no tiene. Al archivar, completar `Fecha_Resolución` con la fecha de la operación y `Solución` con un resumen (pedir al operador si no es evidente de las Notas). Mapear `Prioridad` (select del vivo) → `Prioridad 1` (select del archivo), no al campo legacy `Prioridad` (number) del archivo.
- **Archivo Task Tracker** (`c2698a3e-50c8-4d92-a2a1-756d9aaed2d2`): tiene `Fecha_Cierre` y `Fecha_Creación` — mismo tipo de mapeo requerido.
- `notion-move-pages` **no remapea propiedades entre schemas distintos** — no usar para este flujo. El patrón correcto es: crear página nueva en el destino con propiedades mapeadas explícitamente, luego `notion-update-page` en el original para marcar Status.

## Escenarios de archivado (únicos dos válidos, confirmados por el operador)

1. **Resolución directa**: el ticket está marcado como resuelto/hecho en su propio Status.
2. **Resolución indirecta detectada vía Change Log**: al revisar el Change Log (activo o Archivo Changelog), se encuentra evidencia de que un bug/task ya fue resuelto en otra sesión, pero esa resolución nunca se registró en el ticket correspondiente del tracker.

No hay ventana de gracia — el archivado es inmediato una vez confirmado el escenario 1 o 2, sujeto siempre a Dry Run + `APROBAR_WRITE`.

## Procedimiento

1. Recorrer Bug Tracker y Task Tracker buscando Status en estado terminal (resuelto/hecho — confirmar el valor exacto de Status según schema real de cada tracker antes de asumir).
2. Cruzar contra el Change Log (últimas 10 + Archivo si es necesario) buscando menciones de tickets sin reflejar su resolución en el tracker.
3. Clasificar cada candidato con su Prioridad real (CRÍTICO/ALTO/MEDIO/BAJO — KERNEL:TRACKER-SCHEMA-002) para que el Dry Run permita al operador priorizar la revisión.
4. **Si no hay candidatos** (ningún ticket en estado terminal ni evidencia de resolución no registrada): informar "sin candidatos de archivado en esta corrida" y terminar — no generar Dry Run vacío ni pedir `APROBAR_WRITE` sobre nada.
5. Presentar **Dry Run**: lista de tickets candidatos a archivar, con el escenario (1 o 2), la evidencia textual que sustenta cada uno, y su Prioridad. Formato: tabla con columnas Ticket | Escenario | Evidencia | Prioridad — misma estructura en cada corrida, no descriptiva libre.
6. Esperar variante válida de `APROBAR_WRITE`.
7. Ejecutar: (a) crear página en el Archivo correspondiente vía `notion-create-pages`, con propiedades mapeadas explícitamente según la tabla de arriba — nunca copia 1:1 sin mapeo. La copia hereda el mismo valor de Status terminal que se fija en el original (paso 7b) — nunca se deja vacío ni se asigna un valor fijo distinto de archivo. (b) `notion-update-page` sobre el ticket original para fijar su Status terminal. La fila original queda visible pero marcada — el archivado real (`archived:true`, fuera de la vista activa) no es alcanzable vía MCP y requiere el paso de Terminal descrito arriba.
8. Si algún ticket archivado estaba anotado con el tag `[CENSUS-SYNC-R1]` (ver `vantage-create-bug-task`, `KERNEL:CENSUS-SYNC` §20), ejecutar o recomendar el re-run de `generate_census.py` antes de cerrar el reporte.
9. Fetch de verificación post-escritura sobre ambas páginas (original marcada + copia creada).

## Nota de arquitectura (gap conocido, documentado en el propio sistema)

El Task real en Notion (`39e938be-fc42-81e3-b82d-ebe5f5c16d70`) documenta que housekeeping/archivado son **4 mecanismos distintos con mapeo de campos no-1:1**, no una sola rutina genérica:
1. Bug → Archivo Bug
2. Task → Archivo Task
3. Vacantes expiradas → Archivo Tracker
4. Changelog → mantener 10 recientes, mover exceso a página de bloques

Esta skill cubre únicamente (1) y (2). La (3) vive en `vantage-tidy-opportunities-tracker`. La (4) vive en `vantage-tidy-changelog`.

## Reglas de oro

- Nunca borrar — siempre mover/archivar preservando registro histórico completo.
- Nunca archivar sin Dry Run explícito y `APROBAR_WRITE` previo.
- Si el Status del ticket no es inequívocamente terminal, no asumir — marcar como "candidato ambiguo" y preguntar al operador en el Dry Run.
- Whitelisting de campos (mitigación GAP-03): cualquier escritura vía MCP en este flujo declara whitelist de campos en el Dry Run; campos fuera de whitelist se remueven automáticamente y se reportan.
- **No existe mecanismo de reversión en esta skill.** Si un ticket se archiva por error, la corrección es manual: restaurar Status en el original y eliminar la copia del Archivo a mano en Notion. Esta skill no ofrece "deshacer" — el Dry Run es la única salvaguarda antes de escribir.

## Cierre de sesión standalone (KERNEL:CENSUS-SYNC, Regla 4)

Toda ejecución de esta skill que resulte en archivado real (post-`APROBAR_WRITE`) cierra con un resumen automático: cuántos tickets se archivaron por escenario (1 directo / 2 vía Changelog), y si algún archivado disparó cambio de estado de ID (→ Regla 1 de CENSUS-SYNC, ver `vantage-create-bug-task`). Se presenta sin que el operador lo pida.

---

## Fuentes verificadas (sesión 2026-07-19)

Limitación de `archived:true` no expuesto vía MCP: confirmada contra Task Tracker vivo (fila jul-17, "Crear skills para HANDOFF, TASK, BUG, CHANGELOG", Notion CSV) con referencia cruzada a Changelog v9.3.7 — no inferida ni asumida. Mapeo de campos no-1:1 (`Fecha_Resolución`/`Solución`/`Prioridad 1` en Archivo Bug; `Fecha_Cierre`/`Fecha_Creación` en Archivo Task): confirmado por comparación directa de schema vivo vs. schema de archivo (Notion, fetch directo de ambas DBs) y por la Task original que especifica el mapeo (Notion CSV, fila jul-15). Advertencia sobre `notion-move-pages`: tomada textual de esa misma Task, no inferida.
