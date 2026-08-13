---
name: vantage-sync-script-library
description: Sincroniza la base SCRIPT LIBRARY de Notion contra el árbol de disco activo (Layer_1, Layer_3, Layer_4, Dashboard, Raycast) usando el gap report de verify_versions.py --scripts. Usar cuando el operador pida "sincronizar Script Library", "registrar scripts nuevos" o similar, o cuando un gap report reciente muestre entradas "SIN REGISTRAR EN NOTION" o huérfanos que requieran resolución. No aplica al Bug/Task Tracker (ver vantage-create-bug-task) ni al VANTAGE Tracker de vacantes — es exclusivo del inventario de scripts del propio sistema.
---

## Convención de anuncio (KERNEL:DOCUMENTATION-005)

- Apertura: `SYNCING SCRIPT LIBRARY...`
- Cierre: `SCRIPT LIBRARY SYNCED`

## Manejo de cero candidatos

Si `verify_versions.py --scripts` reporta 0 en "SIN REGISTRAR EN NOTION" y 0 huérfanos, no hay nada que escribir — reportar "Script Library ya está en sync" y cerrar sin Dry Run ni escritura.

## Contexto operativo

Esta skill NO reemplaza el gap report — lo consume. El reporte de `--scripts` (vía `VANTAGE Scripts Gap Report` en Raycast o `python3 verify_versions.py --scripts` en terminal) es de solo lectura; esta skill es la mitad de escritura que falta: toma esa salida y decide qué registrar, corregir o ignorar en Notion.

**Prerrequisito de exclusión limpia:** antes de correr el gap report que alimenta esta skill, confirmar que `EXCLUDED_DIR_NAMES` en `verify_versions.py` incluye tanto `.venv` como `venv` (bug de exclusión incompleta detectado y corregido en sesión 2026-08-05 — si el reporte trae cientos de entradas de `site-packages`, ese fix no se aplicó y hay que aplicarlo primero).

**Schema de SCRIPT LIBRARY (confirmado vía CSV export, sesión 2026-08-05):**

| Propiedad | Tipo / valores válidos |
|---|---|
| `Script` | título |
| `Ruta` | texto (ej. `Layer_1/scripts/health_check.py`) |
| `Capa` | `L1`, `L3`, `L4`, `Dashboard`, `Raycast` |
| `Descripción` | texto libre |
| `Dependencias` | texto libre, frecuentemente vacío |
| `Estado` | exclusivamente `Activo`, `En desarrollo`, `Deprecado` — no inventar otros valores |
| `Acción` | exclusivamente `Keep`, `Archivar` |
| `Fecha de creación` | fecha |

No agregar propiedades fuera de esta lista sin confirmación nueva contra un export/fetch reciente.

`SCRIPT_LIBRARY_DATA_SOURCE_ID = "ea914544-338f-485e-ac1b-7f137a5c9cee"` (confirmado en `verify_versions.py`).

**Bug de auto-link de Notion (detectado en CSV export 2026-08-05, afecta el 100% de las filas existentes):** Notion autoconvierte patrones tipo `palabra.extensión` (ej. `health_check.py`) en hipervínculos, insertando `http://` en medio del texto (`health_http://check.py`). Esto corrompe `Ruta` y `Script` en las 70 filas actuales.
- **Al leer** cualquier fila existente para comparar contra disco, limpiar la corrupción primero: `texto.replace("http://", "")` antes de cualquier match de nombre.
- **Al escribir** filas nuevas, pegar el nombre de archivo como texto plano (no como texto enriquecido que dispare el auto-link de Notion) — verificar en el Dry Run que el valor propuesto para `Ruta`/`Script` no contenga `http://` antes de confirmar `APROBAR_WRITE`.
- Esta skill NO incluye limpieza retroactiva de las 70 filas corruptas — es un batch de escritura separado y más riesgoso (70 updates), fuera de alcance aquí. Si el operador lo pide explícitamente, tratarlo como una operación aparte con su propio Dry Run.

## Clasificación de cada línea del gap report

Para cada entrada en "SIN REGISTRAR EN NOTION", clasificar antes de proponer acción — no tratarlas todas igual:

| Categoría | Señal | Acción propuesta |
|---|---|---|
| Script real nuevo, nunca registrado | Vive en `Layer_1/scripts`, `Layer_3`, `Layer_4`, `Dashboard`, o `Raycast`, con lógica propia (no wrapper trivial) | Proponer alta en Notion |
| Wrapper de Raycast sin registrar | Vive en `Raycast/vantage-*.sh` | Proponer alta en Notion (son scripts operativos igual que los demás, solo que thin wrappers) |
| Script deprecado o de un solo uso | Prefijo `DEPRECATED_`, o nombre sugiere migración puntual (ej. `backfill_*`, `toggle_*` de una sola corrida ya ejecutada) | Preguntar al operador si sigue vigente antes de registrar — no asumir que todo lo que aparece en disco debe registrarse |

Para cada entrada en "EN NOTION COMO 'Activo' PERO NO EN DISCO" (huérfanos), clasificar:

| Categoría | Señal | Acción propuesta |
|---|---|---|
| Mismatch de nombre/título | Existe un script en disco con nombre similar pero no idéntico (ej. Notion dice `apply_hyperlinks.py`, disco tiene `apply_hyperlinks_notion.py`) | Preguntar al operador si es el mismo script renombrado — si confirma, proponer `update` del título en la fila existente en vez de crear una nueva |
| Ausencia real | Sin candidato similar en disco | Preguntar al operador si el script se eliminó intencionalmente — si confirma, proponer marcar la fila como inactiva (no eliminar la fila, ver Reglas de oro) |

## Procedimiento

1. Correr o recibir el gap report más reciente de `--scripts`. Si tiene más de ~5 minutos de antigüedad en la sesión, volver a correrlo — el árbol de disco pudo cambiar.
2. Clasificar cada entrada según las tablas de arriba. Presentar la clasificación al operador antes de tocar Notion.
3. Para cualquier huérfano ambiguo (mismatch vs ausencia real), preguntar — nunca asumir.
4. Confirmar schema vivo de SCRIPT LIBRARY (ver arriba) si no se ha hecho ya en esta sesión.
5. **Dry Run**: presentar la lista completa de altas propuestas (título, ruta, y cualquier otro campo confirmado) y las correcciones propuestas a huérfanos, separadas claramente.
6. Esperar variante válida de `APROBAR_WRITE`: `APROBAR_WRITE` · `APROBAR` · `SÍ` · `sí` · `YEP` · `yep`. Eliminados por RAI-03: `Ok` · `Go` · `YES` · `yes`.
7. Ejecutar `notion-create-pages` (altas) y/o `notion-update-page` (correcciones de huérfanos) contra `ea914544-338f-485e-ac1b-7f137a5c9cee`.
8. Fetch de verificación post-escritura (double-fetch si la primera relectura devuelve estado pre-write).
9. Cerrar con resumen: cuántas altas, cuántas correcciones, cuántos huérfanos quedaron pendientes de decisión del operador.

## Reglas de oro

- Nunca crear una fila nueva para un huérfano que probablemente es un mismatch de nombre — eso duplica el registro en vez de corregirlo. Preguntar primero.
- Nunca marcar una fila huérfana como eliminada/borrada directamente — proponer inactivar (whitelisting de campos aplica igual que en `vantage-create-bug-task`), la decisión de borrar en firme es del operador fuera de esta skill.
- Nunca inventar campos del schema de SCRIPT LIBRARY sin confirmarlos en vivo primero.
- No registrar automáticamente scripts que parezcan de un solo uso (`backfill_*`, `toggle_*`, migraciones puntuales) sin confirmar con el operador que siguen vigentes — evita ensuciar la Library con código ya ejecutado y no reutilizable.
- Si el gap report trae un volumen anómalo de entradas (cientos, cuando la sesión anterior reportó decenas), sospechar del bug de exclusión de `venv`/`.venv` antes de proceder — no tratar ese volumen como señal real de scripts nuevos.

## Cierre de sesión standalone (KERNEL:CENSUS-SYNC, Regla 4)

Si esta skill produce una escritura real fuera de una sesión formal `vantage-session-open`/`close`, cerrar con resumen breve de lo escrito (altas, correcciones) antes de terminar el turno, consistente con el resto del protocolo VANTAGE.

---

## Fuentes verificadas (sesión 2026-08-05)

`SCRIPT_LIBRARY_DATA_SOURCE_ID` confirmado por lectura directa de `verify_versions.py` (Layer_1/scripts). Bug de exclusión `.venv` vs `venv` detectado y corregido en la misma sesión (línea 67 del script, confirmado con `grep` post-fix). Schema completo de SCRIPT LIBRARY (`Capa`, `Ruta`, `Descripción`, `Dependencias`, `Estado`, `Acción`, `Script`, `Fecha de creación`) confirmado por inspección directa de export CSV de la base (70 filas). Valores válidos de `Estado` (`Activo`/`En desarrollo`/`Deprecado`) y `Acción` (`Keep`/`Archivar`) confirmados por enumeración de valores únicos en el mismo CSV. Corrupción de auto-link de Notion (`http://` insertado en `Ruta`/`Script`) confirmada en el 100% de las 70 filas del mismo export.
