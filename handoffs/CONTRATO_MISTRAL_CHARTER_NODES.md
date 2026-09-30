# TASK PROMPT: Notion Block Normalization — Project Charter Sub-node Resolution

Proyecto: VANTAGE · Fecha: 2026-09-30 · Emisor: Operador (MM) · Ejecutor: MISTRAL
Gatekeeper del Charter: CLAUDE/MAIN (CHARTER:DECISIONS-011)

---

## 0. Prerrequisitos (verificar antes de tocar nada)

| # | Condición | Cómo verificar |
|---|---|---|
| P1 | PR #17 mergeado a `main` y `git pull` hecho en la máquina donde correrá `vcensus` | `grep -c '"id": "CHARTER:' Layer_1/scripts/generate_census.py` → debe devolver **38** |
| P2 | Credenciales Notion cargadas (`NOTION_TOKEN` en `Layer_1/.env`) | `vcensus` corre sin `[ERROR] Ni NOTION_TOKEN…` |
| P3 | Corrida de control ANTES del cambio | `vcensus` → anotar `IDs sin link`, `IDs con Sección hardcodeada`, `Huérfanos`. Esperado: 31 hardcodeados (los sub-nodos sin DEF) |

Si P1 falla, los 31 aparecerán como **huérfanos** tras la migración (DEF fuera de spec). No es error de la migración: es que falta el pull.

---

## 1. Misión

Convertir los 31 sub-nodos del `V | PROJECT CHARTER` (Notion page `f87938be-fc42-8263-a305-819877d2245f`) de párrafos/list items inline a bloques `heading_3` que `generate_census.py` reconozca como **DEF con sección en vivo**.

Alcance exacto (31, ni uno más):
- `CHARTER:DECISIONS-001..011`
- `CHARTER:FAILURES-001..005`
- `CHARTER:NON-NEGOTIABLES-001..010`
- `CHARTER:MILESTONES-001..005`

Fuera de alcance: `CHARTER:PURPOSE`, `CHARTER:STATUS`, `CHARTER:CONTINUITY` y los 4 headings padre (ya resuelven). No tocar ningún otro bloque.

---

## 2. Regla de formato (derivada del parser real, `generate_census.py` L476-505)

### 2.1 Position-One Rule
El heading debe iniciar con **número de sección**, espacio, **ID canónico**, ` — `, título.

```
<N.n> <CHARTER:PREFIX-XXX> — <Título corto>
```

Por qué NO va el ID en posición 0: `extract_live_section()` aplica `^([\w.]+)` al inicio del heading para obtener la columna **Sección** del Census. Si el heading empieza con `CHARTER:…`, captura la palabra `CHARTER` y las 31 filas del Census quedarían con Sección = "CHARTER". Verificado por simulación:

| Heading | ¿DEF? | Sección |
|---|---|---|
| `CHARTER:DECISIONS-001 — …` | sí | `CHARTER` ← inválido |
| `2.1 CHARTER:DECISIONS-001 — …` | sí | `2.1` ← correcto |
| `[2026-07] CHARTER:DECISIONS-001 — …` (estado actual) | **no** | — |

### 2.2 Numeración
La sección se toma **en vivo** de Notion, y los headings padre ya existentes en la página usan numeración de documento. Los hijos heredan del padre:

| Padre (heading existente en Notion) | Hijos |
|---|---|
| `2. CHARTER:DECISIONS — …` | `2.1` … `2.11` |
| `3. CHARTER:FAILURES — …` | `3.1` … `3.5` |
| `4. CHARTER:NON-NEGOTIABLES — …` | `4.1` … `4.10` |
| `5. CHARTER:MILESTONES — …` | `5.1` … `5.5` |

(`CENSUS_SPEC` local trae otra numeración provisional — 05.x/06.x/02.x/04.x —; se alinea en commit de seguimiento por Arena. La que manda es Notion.)

### 2.3 Prohibido antes del número de sección
Fechas `[YYYY-MM-DD]`, prefijos de lista `1. `, viñetas, backticks, espacios, emojis.

### 2.4 Split heading / cuerpo
Los nodos actuales son párrafos de 3-10 líneas. **No** se mete todo en el heading:
- `heading_3` = `N.n ID — Título` (el título = texto entre ` — ` y el primer `.`/salto de línea del bloque original, máx ~90 caracteres).
- `paragraph` nuevo, inmediatamente debajo = resto del texto original íntegro, **anteponiendo la fecha** si existía (`[2026-09-11] Se eliminó del…`). Ningún carácter del contenido original se pierde.
- Si el bloque original ya era una sola línea corta, solo heading, sin párrafo.

---

## 3. Transformaciones por sección

| Sección | Patrón actual (tipo) | Resultado |
|---|---|---|
| DECISIONS | `[fecha] CHARTER:DECISIONS-XXX — Título. Cuerpo…` (`paragraph`) | `heading_3`: `2.n CHARTER:DECISIONS-XXX — Título` + `paragraph`: `[fecha] Cuerpo…` |
| FAILURES | `CHARTER:FAILURES-XXX — Título. Cuerpo…` (`paragraph`) | `heading_3`: `3.n CHARTER:FAILURES-XXX — Título` + `paragraph`: `Cuerpo…` |
| NON-NEGOTIABLES | `CHARTER:NON-NEGOTIABLES-XXX — Texto…` (`numbered_list_item`) | `heading_3`: `4.n CHARTER:NON-NEGOTIABLES-XXX — Texto corto` + `paragraph` con el resto si excede una oración |
| MILESTONES | `CHARTER:MILESTONES-XXX — Hito n — Título. Cuerpo…` (`paragraph`) | `heading_3`: `5.n CHARTER:MILESTONES-XXX — Hito n — Título` + `paragraph`: `Cuerpo…` |

---

## 4. Restricción de la API de Notion (crítica)

`PATCH /v1/blocks/{block_id}` **no permite cambiar `type`** (paragraph → heading_3 devuelve HTTP 400). Pipeline obligatorio por bloque:

1. `PATCH /v1/blocks/{parent_id}/children` con `after: <block_id original>` → append `heading_3` (+ `paragraph` del cuerpo).
2. Verificar 200 y capturar los nuevos `block_id`.
3. `DELETE /v1/blocks/{block_id original}`.
4. Nunca borrar antes de confirmar el append.

Consecuencia: los 31 bloques cambian de `block_id`. Los hyperlinks previos que apuntaran a esos párrafos quedan obsoletos; se regeneran en el paso `vhyperlinks --apply` posterior (fuera de este contrato). Entregar tabla `old_block_id → new_heading_id, new_paragraph_id`.

`Notion-Version`: usar la misma que `notion_utils._notion_version()` (default `2025-09-03`).

---

## 5. Protocolo de ejecución

### Fase A — DRY RUN (sin escritura). Entregar y detenerse.
Tabla de 31 filas:

| # | ID | block_id actual | tipo actual | texto actual (primeros 80 chars) | heading propuesto | cuerpo propuesto (primeros 60 chars) |

Más: confirmación de P1/P2/P3 y la salida de la corrida de control.
**Esperar `APROBAR_WRITE` del operador.** Sin esa palabra no hay escritura (CHARTER:NON-NEGOTIABLES-002).

### Fase B — WRITE (solo tras APROBAR_WRITE)
Ejecutar §4 para los 31 en orden de documento. Si cualquier append falla, **detener** sin borrar nada y reportar.

### Fase C — Verificación (re-fetch, no reporte optimista — CHARTER:NON-NEGOTIABLES-003)
1. Re-fetch de la página: 31 bloques `heading_3` cuyo `plain_text` cumple regex
   `^\d+\.\d+ CHARTER:(DECISIONS|FAILURES|NON-NEGOTIABLES|MILESTONES)-\d{3} — .+`
   y 0 bloques restantes que contengan `CHARTER:*-\d{3}` con tipo ≠ `heading_3` (excepto la lista de STATUS que enumera los rangos `001..011`, que es texto, no DEF).
2. `vcensus` (sin flags). Salida requerida:
   - `IDs en spec: 294`
   - `IDs sin link: 0`
   - `IDs con Sección hardcodeada (sin heading 'N' detectable en vivo): 0`
   - `Huérfanos: 0`
3. En `Layer_1/data/V_ID_CENSUS_PRODUCTION.md`: las 31 filas `CHARTER:*-NNN` con Sección `2.n/3.n/4.n/5.n` y **sin** `⚠︎sin verificar en vivo`.
4. `vcensus --debug-id CHARTER:DECISIONS-001 CHARTER:NON-NEGOTIABLES-010` → ambos `is_def=True` con `seccion` no nula.

**No ejecutar** `--sync-to-notion`, `vhyperlinks --apply` ni `vdoc`: eso es del operador en pasos posteriores.

---

## 6. Definition of Done

- [ ] 31 `heading_3` nuevos en Notion con formato `N.n CHARTER:PREFIX-XXX — Título`.
- [ ] 31 bloques originales eliminados; 0 pérdida de texto (cuerpos preservados en párrafos).
- [ ] Ningún bloque fuera de los 31 modificado (diff de re-fetch vs snapshot de Fase A).
- [ ] `vcensus`: 294 / 0 sin link / 0 hardcodeados / 0 huérfanos.
- [ ] Entregables: tabla Fase A, tabla `old_id → new_ids`, salida literal de `vcensus` (pegada, no parafraseada), lista de las 31 filas del MD.

## 7. Fuera de alcance / no hacer
- No editar `generate_census.py`, `CENSUS_SPEC` ni ningún archivo del repo.
- No tocar `V | CHANGELOG` ni la propiedad `Versión` de ninguna página.
- No renumerar ni reescribir los headings padre.
- No "arreglar" los 8 huérfanos REF-sin-DEF de `inventario_huerfanos.md`.
