---
name: vantage-sync-skill-library
description: Sincroniza el inventario de habilidades (.skill) de VANTAGE en Notion contra el árbol de disco activo, usando el gap report extendido de verify_versions.py --skills. Además, en cada alta o actualización escribe el contenido completo del SKILL.md como body de la página Notion. Usar cuando el operador pida "sincronizar Skill Library", "registrar skills nuevas" o similar, o cuando un gap report reciente muestre archivos .skill sin registrar en Notion o entradas huérfanas sin archivo físico correspondiente. No aplica al Bug/Task Tracker (ver vantage-create-bug-task), al VANTAGE Tracker de vacantes, ni al inventario de scripts .py/.sh (ver vantage-sync-script-library) — es exclusivo del inventario de archivos .skill del propio sistema.
---

# VANTAGE — Skill Sync Skill Library

ID sugerido: `vantage-sync-skill-library` · Objetivo: eliminar "fantasmas documentales" en el inventario de `.skill` y garantizar que el body de cada página Notion contenga la lógica completa canónica.

## Convención de anuncio (KERNEL:DOCUMENTATION-005)

- Apertura: `SYNCING SKILL LIBRARY...`
- Cierre: `SKILL LIBRARY SYNCED`

## Prerrequisito — resuelto

`verify_versions.py --skills` **existe y está confirmado** (refactor de ArgumentParser, sesión 2026-08-07): `scan_committed_assets(project_root, extensions)` generaliza el escaneo antes exclusivo de `--scripts`, y `get_script_library_titles(..., title_property="Skill")` lee la propiedad título correcta de esta base (`Skill`, distinta de `Script` en SCRIPT LIBRARY). `--scripts` y `--skills` corren de forma independiente sin interferencia mutua. `SKILL_LIBRARY_DATA_SOURCE_ID` ya está fijado en el script (no placeholder) — ver sección siguiente para el valor.

## Manejo de cero candidatos

Si `verify_versions.py --skills` reporta 0 archivos sin registrar y 0 huérfanos, no hay nada que escribir — reportar "Skill Library ya está en sync" y cerrar sin Dry Run ni escritura.

## Contexto operativo

Esta skill consume el gap report de `--skills` (solo lectura) y ejecuta la mitad de escritura: altas de filas nuevas + escritura del body completo del `SKILL.md` correspondiente.

Para la carga masiva inicial de skills **ya existentes**, usar el script local `bulk_upload_skill_bodies.py` (API directa, sin MCP) para no consumir tokens de agente.

## Base de datos SKILL LIBRARY — identidad confirmada

`SKILL_LIBRARY_DATA_SOURCE_ID = "2f1938be-fc42-83c8-8972-07300201136d"` (base nueva, creada 2026-08-07, colgando de VANTAGE Central Hub `36e938be-fc42-81d6-bf40-dfe7dee782a5`, hermana de SCRIPT LIBRARY en el mismo hub). Confirmado por fetch directo y re-fetch de verificación tras ajuste de schema — no requiere resolución adicional.

## Esquema de datos confirmado (SKILL LIBRARY)

| Propiedad | Tipo / valores válidos | Propósito |
|---|---|---|
| `Skill` | título | Nombre del archivo / carpeta |
| `Ruta` | texto | Ubicación en el filesystem |
| `Descripción` | texto | Resumen del frontmatter |
| `Estado` | select — `Activo`, `En desarrollo`, `Deprecado` | Estado operativo |
| `Acción` | select — `Keep`, `Archivar` | Decisión de mantenimiento |
| `Fecha de creación` | created_time (auto) | Timestamp de alta |

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

## Procedimiento (actualizado)

1. Correr o recibir gap report fresco de `verify_versions.py --skills`.
2. Clasificar entradas y presentar al operador.
3. Extraer `Descripción` del frontmatter.
4. **Dry Run**: lista de altas + correcciones de huérfanos + confirmación de que se escribirá el body completo.
5. Esperar `APROBAR_WRITE` (o variantes válidas).
6. Ejecutar altas (`notion-create-pages`) / updates de propiedades.
7. **Nuevo — Escritura de body**:
   - Para cada página creada o actualizada, leer el `SKILL.md` completo del disco.
   - Usar `replace_content` (o equivalente) para escribir el markdown completo como body de la página.
   - Si la página ya tenía body y no se pidió `--force` conceptual, preguntar o saltar.
8. **Write-Back Verification**:
   - Re-fetch de propiedades (`Skill`, `Ruta`, `Descripción`).
   - Re-fetch del body y comprobar que contiene el frontmatter + secciones principales del `SKILL.md`.
9. Cerrar con resumen: altas, correcciones, bodies escritos, huérfanos pendientes.

## Reglas de oro (añadidas)

- Nunca dejar una fila Activo con body vacío tras un alta nueva.
- Para la carga histórica masiva de skills ya existentes usar siempre el script local `bulk_upload_skill_bodies.py` (no esta skill vía MCP).
- Esta skill solo escribe body en el contexto de altas/actualizaciones nuevas o explícitamente solicitadas.

## Fuentes verificadas

KERNEL:DOCUMENTATION-005, SP:CONSISTENCY, schema vivo de Skill Library (2026-08-07 + re-fetch posteriores).
