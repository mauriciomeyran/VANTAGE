---
name: vantage-sync-skill-library
description: Sincroniza el inventario de habilidades (.skill) de VANTAGE en Notion contra el árbol de disco activo, usando el gap report extendido de verify_versions.py --skills. Usar cuando el operador pida "sincronizar Skill Library", "registrar skills nuevas" o similar, o cuando un gap report reciente muestre archivos .skill sin registrar en Notion o entradas huérfanas sin archivo físico correspondiente. No aplica al Bug/Task Tracker (ver vantage-create-bug-task), al VANTAGE Tracker de vacantes, ni al inventario de scripts .py/.sh (ver vantage-sync-script-library) — es exclusivo del inventario de archivos .skill del propio sistema.
---

# VANTAGE — Skill Sync Skill Library

ID sugerido: `vantage-sync-skill-library` · Objetivo: eliminar "fantasmas documentales" en el inventario de `.skill`, garantizando que el sistema opere solo con instrucciones canónicas verificadas en Notion.

## Convención de anuncio (KERNEL:DOCUMENTATION-005)

- Apertura: `SYNCING SKILL LIBRARY...`
- Cierre: `SKILL LIBRARY SYNCED`

## Prerrequisito — resuelto

`verify_versions.py --skills` **existe y está confirmado** (refactor de ArgumentParser, sesión 2026-08-07): `scan_committed_assets(project_root, extensions)` generaliza el escaneo antes exclusivo de `--scripts`, y `get_script_library_titles(..., title_property="Skill")` lee la propiedad título correcta de esta base (`Skill`, distinta de `Script` en SCRIPT LIBRARY). `--scripts` y `--skills` corren de forma independiente sin interferencia mutua. `SKILL_LIBRARY_DATA_SOURCE_ID` ya está fijado en el script (no placeholder) — ver sección siguiente para el valor.

## Manejo de cero candidatos

Si `verify_versions.py --skills` reporta 0 archivos sin registrar y 0 huérfanos, no hay nada que escribir — reportar "Skill Library ya está en sync" y cerrar sin Dry Run ni escritura.

## Contexto operativo

Esta skill NO reemplaza el gap report — lo consume. El reporte de `--skills` es de solo lectura; esta skill es la mitad de escritura: toma esa salida y decide qué registrar, corregir o ignorar en Notion.

## Base de datos SKILL LIBRARY — identidad confirmada

`SKILL_LIBRARY_DATA_SOURCE_ID = "2f1938be-fc42-83c8-8972-07300201136d"` (base nueva, creada 2026-08-07, colgando de VANTAGE Central Hub `36e938be-fc42-81d6-bf40-dfe7dee782a5`, hermana de SCRIPT LIBRARY en el mismo hub). Confirmado por fetch directo y re-fetch de verificación tras ajuste de schema — no requiere resolución adicional.

## Esquema de datos confirmado (SKILL LIBRARY)

Verificado por fetch directo del data source (2026-08-07), tras ajuste manual del operador en Notion UI para alinear con el brief original:

| Propiedad | Tipo / valores válidos | Propósito |
|---|---|---|
| `Skill` | título | Nombre del archivo (ej. `vantage-cv-a.skill`) |
| `Ruta` | texto | Ubicación en el filesystem (ej. `/skills/`) |
| `Descripción` | texto | Resumen ejecutivo de la función de la skill |
| `Estado` | select — `Activo`, `En desarrollo`, `Deprecado` | Estado operativo |
| `Versión Instrucción` | texto | Versión interna de la lógica (ej. `v1.0.2`) |
| `Acción` | select — `Keep`, `Archivar` | Decisión de mantenimiento |
| `Fecha de creación` | created_time (auto, read-only) | Timestamp de alta |

No agregar propiedades fuera de esta lista sin confirmación nueva contra un export/fetch reciente.

## Protección contra auto-link de Notion

Mismo bug ya documentado y confirmado en `vantage-sync-script-library`: Notion autoconvierte patrones tipo `palabra.extensión` (ej. `vantage-cv-a.skill`) en hipervínculos, insertando `http://` en medio del texto. Dado que **todos** los nombres de archivo en esta base terminan en `.skill`, el riesgo es sistemático, no ocasional:

- **Al leer** cualquier fila existente para comparar contra disco, limpiar la corrupción primero: `texto.replace("http://", "")` antes de cualquier match de nombre.
- **Al escribir** filas nuevas, pegar el nombre de archivo como texto plano — verificar en el Dry Run que el valor propuesto para `Ruta`/`Skill` no contenga `http://` antes de confirmar `APROBAR_WRITE`.
- Esta skill no incluye limpieza retroactiva de filas ya corruptas — si se detecta corrupción existente al primer sync, tratarla como batch de escritura separado con su propio Dry Run, igual que en `vantage-sync-script-library`.

### Segundo vector confirmado — corrupción en `Descripción` (sesión 2026-08-1x)

El bug de auto-link no se limita a `Skill`/`Ruta`. Se confirmó que Notion también inyecta `http://` en `Descripción` cuando el texto contiene un patrón `palabra.extensión` (ej. una mención a `algo.py` dentro del resumen ejecutivo) — incluso si el texto de origen llega ya limpio al momento de construir la escritura. La corrupción ocurre **en el guardado** (`update_properties`/`create_pages`), no antes, por lo que no es detectable inspeccionando el string previo al `write`.

- **Al escribir** `Descripción`, evitar cualquier patrón `palabra.extensión` dentro del texto libre. Workaround confirmado: reescribir `palabra.py` como `palabra (py)` (paréntesis en vez de punto-extensión) antes de enviar el `update_properties`.
- **Write-Back Verification obligatoria en `Descripción`** además de `Skill`/`Ruta` — el doble fetch post-escritura debe revisar los tres campos, no solo los dos ya documentados.
- Pendiente de verificar: si el mismo patrón aplicado a `.skill` (no solo `.py`) dentro de `Descripción` (texto libre, distinto del campo `Skill`) dispara el mismo bug. Sin evidencia confirmada aún — tratar con la misma precaución preventiva hasta confirmar o descartar en una futura alta.

## Clasificación de cada línea del gap report

Para cada entrada en "SIN REGISTRAR EN NOTION", clasificar antes de proponer acción:

| Categoría | Señal | Acción propuesta |
|---|---|---|
| Skill real nueva, nunca registrada | Archivo `.skill` válido en `/skills/`, con `SKILL.md` bien formado | Proponer alta en Notion |
| Skill en desarrollo / borrador | Nombre sugiere prueba (`test-*`, `draft-*`) o el operador la mencionó como WIP en la sesión | Proponer alta con `Estado = En desarrollo`, no `Activo` |

Para cada entrada en "EN NOTION PERO NO EN DISCO" (huérfanos), clasificar:

| Categoría | Señal | Acción propuesta |
|---|---|---|
| Mismatch de nombre | Existe un `.skill` en disco con nombre similar pero no idéntico | Preguntar al operador si es la misma skill renombrada — si confirma, proponer `update` del título en la fila existente en vez de crear una nueva |
| Ausencia real | Sin candidato similar en disco | Preguntar al operador si la skill se eliminó intencionalmente — si confirma, proponer marcar `Estado = Deprecado` (no eliminar la fila) |

## Extracción de descripción — Cero Inferencia

No inventar el campo `Descripción`. Extraerlo directamente del YAML frontmatter (`description:`) del `SKILL.md` asociado a cada archivo `.skill`. Si el `.skill` está empaquetado (binario/zip) y no se puede leer el frontmatter directamente, descomprimir primero o solicitar el `SKILL.md` fuente antes de escribir cualquier descripción — nunca resumir a partir del nombre del archivo.

## Procedimiento

1. `verify_versions.py --skills` ya está confirmado como disponible (ver Prerrequisito arriba) — no requiere verificación previa a cada corrida.
2. Usar `SKILL_LIBRARY_DATA_SOURCE_ID = "2f1938be-fc42-83c8-8972-07300201136d"` (ya confirmado, ver arriba).
3. Correr o recibir el gap report más reciente de `--skills`. Si tiene más de ~5 minutos de antigüedad en la sesión, volver a correrlo.
4. Clasificar cada entrada según las tablas de arriba. Presentar la clasificación al operador antes de tocar Notion.
5. Para cualquier huérfano ambiguo (mismatch vs ausencia real), preguntar — nunca asumir.
6. Extraer `Descripción` del YAML frontmatter de cada `SKILL.md` — nunca inventarla (ver Extracción de descripción).
7. **Dry Run**: presentar la lista completa de altas propuestas (todos los campos del esquema) y las correcciones propuestas a huérfanos, separadas claramente.
8. Esperar variante válida de `APROBAR_WRITE`: `APROBAR_WRITE` · `APROBAR` · `SÍ` · `sí` · `YEP` · `yep`.
9. Ejecutar `notion-create-pages` (altas) y/o actualización de página (correcciones de huérfanos) contra el `data_source_id` confirmado.
10. **Write-Back Verification**: fetch de verificación post-escritura para cada entrada creada/actualizada (double-fetch si la primera relectura devuelve estado pre-write). Este paso replica el patrón ya establecido en `vantage-sync-script-library` — el brief original lo cita bajo `KERNEL:03.10` (Documentación Transversal), pero ese anchor cubre un contrato distinto (detección de contenido operativo sin ancla documental); la obligación real de re-fetch post-escritura vive en la disciplina general de `SP:CONSISTENCY` / multi-agent verification, no en `KERNEL:03.10`. Se aplica el paso por su contenido operativo confirmado, sin forzar la cita del anchor incorrecto.
11. Cerrar con resumen: cuántas altas, cuántas correcciones, cuántos huérfanos quedaron pendientes de decisión del operador.

## Reglas de oro

- Nunca crear una fila nueva para un huérfano que probablemente es un mismatch de nombre — eso duplica el registro en vez de corregirlo. Preguntar primero.
- Nunca marcar una fila huérfana como eliminada directamente — proponer `Estado = Deprecado`, la decisión de borrar en firme es del operador fuera de esta skill.
- Nunca inventar campos del schema de SKILL LIBRARY sin confirmarlos en vivo primero contra un export/fetch real, una vez la base exista.
- No registrar automáticamente skills que parezcan borradores o pruebas sin confirmar con el operador que siguen vigentes.
- Ambos prerrequisitos (flag `--skills` e identidad de SKILL LIBRARY) están resueltos — esta skill opera en su forma completa.

## Fuentes verificadas (sesión 2026-08-07)

`KERNEL:DOCUMENTATION-005` (03.5, Convención de Anuncio de Skills) confirmado en ID Census vigente v9.14.3. El anchor `KERNEL:03.10` citado en el brief original para Write-Back Verification fue verificado como `KERNEL:DOCUMENTATION-010` ("Documentación Transversal") en el ID Census — existe como ID, pero su contenido no corresponde al contrato de re-fetch post-escritura citado; se documenta la desalineación en el paso 10 sin bloquear la skill.

Base SKILL LIBRARY creada en vivo esta sesión: página inicial (`notion-create-pages`) resultó en página simple sin schema — confirmado que `notion-create-pages` no soporta creación de databases con propiedades tipadas. El operador creó la database real manualmente en Notion UI, colgando de VANTAGE Central Hub (`36e938be-fc42-81d6-bf40-dfe7dee782a5`). Primer fetch reveló schema clonado de SCRIPT LIBRARY (con `Capa` en vez de `Versión Instrucción`); el operador ajustó el schema en Notion UI y el re-fetch de verificación confirmó `Capa` removida y `Versión Instrucción` (texto) agregada. `SKILL_LIBRARY_DATA_SOURCE_ID = "2f1938be-fc42-83c8-8972-07300201136d"` confirmado por este re-fetch.

El flag `--skills` de `verify_versions.py` **está confirmado** (refactor de ArgumentParser, sesión 2026-08-07): `scan_committed_assets` generaliza el escaneo por extensión, `render_scripts_gap_report` acepta `label`/`data_source_id`/`title_property` dinámicos, y `get_script_library_titles` expone `title_property` (default `"Script"`, `"Skill"` para esta base) — sin regresión sobre `--scripts`. Validado con `py_compile` y `--help`.
