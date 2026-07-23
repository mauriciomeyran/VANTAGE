---
name: vantage-tidy-changelog
description: Mantiene el Change Log de VANTAGE con las últimas 10 entradas visibles, moviendo el exceso al Archivo Changelog histórico. Usar cuando el Change Log activo supera 10 entradas o cuando se solicita housekeeping documental.
---

## Convención de anuncio (KERNEL:SKILL-ANNOUNCE-CONVENTION)

- Apertura: `TIDYING CHANGELOG...`
- Cierre: `CHANGELOG TIDIED`

## IDs confirmados

- Change Log (activo): `CHANGELOG:` (resuelve vía `resolver_registry_v2.json`, UUID `390938be-fc42-80e7-b429-d7d730339353`)
- Archivo Changelog (histórico completo): `CHANGELOG_ARCHIVE:` (resuelve vía `resolver_registry_v2.json`, UUID `39d938be-fc42-801c-94f6-f11bfe803633`)

## Mecanismo confirmado

- El Change Log activo es una **página de bloques**, no una DB — el mantenimiento es `append`/`notion-update-page` (`update_content`), nunca `notion-create-pages` ni `replace_content`.
- Regla verificada textualmente: solo se mantienen las últimas 10 entradas en la página de consulta continua; el exceso se traslada al Archivo Changelog.
- No existe tag `[PERMANENT]`/`[CRITICAL]` como excepción de migración en ningún schema o documento confirmado — si el operador quiere implementarlo, es una decisión nueva a diseñar, no un mecanismo existente.
- El Change Log es la fuente de verdad de versión para `SP:SYNC-RULE` — la versión que ahí quede es la que se propaga vía `verify_versions.py --sync` a los otros 6 documentos fundacionales.

## Procedimiento

1. Fetch del Change Log activo — contar entradas actuales.
2. **Si son ≤10**: no hay acción, informar "Change Log dentro del límite, sin acción necesaria" y terminar — no generar Dry Run.
3. Si son >10: identificar las entradas más antiguas que exceden las 10 más recientes.
4. Dry Run: tabla con columnas Entrada (primeras palabras) | Fecha | Destino (Archivo Changelog) — mostrando el texto completo de cada entrada a mover como bloque aparte debajo de la tabla, para verificación exacta antes de mover.
5. Esperar variante válida de `APROBAR_WRITE` (ver lista en `vantage-create-bug-task` — nunca `Ok`/`Go`/`yes`).
6. Ejecutar: append de las entradas removidas al Archivo Changelog (preservando contenido íntegro y orden cronológico), luego editar el Change Log activo para dejar solo las 10 más recientes. **Manejo de fallo parcial:** si el append al Archivo tiene éxito pero la edición del Change Log activo falla, el Change Log activo sigue teniendo las entradas duplicadas (viejas + intactas) — no es un estado corrupto, es recuperable: reintentar solo la edición del activo, sin repetir el append (evitaría duplicados en el Archivo). Si el append mismo falla, no editar el activo — abortar la operación completa y reportar el estado sin cambios.
7. Fetch de verificación post-escritura (Write-Back Verification) — un mismatch detiene la operación; una confirmación en chat de "ya se escribió" no es evidencia suficiente por sí sola.

## Disparo de KERNEL:CENSUS-SYNC (Regla 3)

Esta obligación aplica a quien redacta la entrada nueva de Changelog (tipicamente vantage-create-bug-task o la sesion de cierre que documenta el batch), no a este skill — vantage-tidy-changelog solo rota entradas ya existentes entre el activo y el Archivo, nunca las crea. Si al rotar una entrada se detecta que documentaba cierre de tickets con cambio de estado de ID sin que el Census se haya corrido antes, senalarlo como hallazgo — no ejecutar el re-run como parte de este skill.

## Reglas de oro

- Nunca usar `replace_content` en el Change Log si tiene layout de columnas — usar `update_content`.
- Nunca borrar una entrada del Changelog — siempre mover, nunca eliminar.
- Nunca escribir una entrada de Changelog sin haber verificado primero si dispara Regla 1 o Regla 3 de `KERNEL:CENSUS-SYNC`.

## Cierre de sesión standalone (KERNEL:CENSUS-SYNC, Regla 4)

Esta skill modifica documentación (Change Log + Archivo Changelog) — cualquier ejecución que resulte en escritura real debe cerrar con el resumen automático de Regla 4: qué se movió, estado del Census (si se disparó Regla 1/3), y versión resultante. Se presenta sin que el operador lo pida, como reporte de cierre — no reabre la aprobación ya otorgada en el paso 5 del procedimiento.

---

## Fuentes verificadas (sesión 2026-07-19)

Regla de 10 entradas + naturaleza de página de bloques (no DB) del Archivo Changelog: confirmada textualmente contra `KERNEL:CENSUS-SYNC` (Kernel, fetch directo) y contra la Task original (`d2a65ca1...`, Notion, fetch directo) que especifica el mecanismo `notion-update-page`/append. ID de Archivo Changelog: confirmado contra `V | ARCHIVEROS` (Notion, fetch directo) y ya incorporado a `SP:CEDULA-DIGITAL` en esta misma sesión.
