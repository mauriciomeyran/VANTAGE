---
name: vantage-documentacion-transversal-implementacion
description: Ejecuta la implementación completa de documentación transversal una vez autorizada una propuesta de nodos — DRY RUN, aprobación, inyección, write-back verification, changelog/versión, y entrega final. USAR tras APROBAR_WRITE de una propuesta generada por vantage-documentacion-transversal-propuesta, o cuando el operador active explícitamente "implementación de documentación transversal" sobre un mapeo de nodos ya existente. No usar para generar el mapeo inicial — eso corresponde al skill de propuesta.
---

# Documentación Transversal VANTAGE — Fase 2: Implementación

Mitad de escritura del protocolo de documentación transversal. Requiere como insumo un mapeo de nodos ya autorizado (típicamente producido por `vantage-documentacion-transversal-propuesta`, o presentado directamente por el operador si el mapeo ya se hizo en otra sesión). Cubre desde el DRY RUN hasta el cierre verificado.

## Cuándo se activa

- Inmediatamente después de que el operador autoriza una propuesta de nodos (Fase 1 completada, con tokens válidos: `APROBAR_WRITE`, `APROBAR`, `SÍ`, `sí`, `YEP`, `yep`).
- Modo recordatorio: si en sesión se detecta un gap estructural que requiere parches múltiples para coherencia transversal y el operador ya tiene claro el mapeo de nodos (no requiere pasar por Fase 1 de nuevo).

Si no existe un mapeo de nodos previo y autorizado, detener y redirigir a `vantage-documentacion-transversal-propuesta` primero — este skill no infiere nodos por su cuenta.

## Principio rector: nodo natural + PATCH-QUALITY-001

Inyectar en el flujo de lectura (Kernel: prioridad operativa; Manual: narrativa progresiva), nunca como adendum. Este skill **no redefine** criterios de calidad documental — hereda los 5 filtros de `MANUAL:PATCH-QUALITY-001`:

1. **Invisibilidad estructural** — el parche no debe notarse como "pegado"; hereda tono y jerarquía del documento padre.
2. **Continuidad de voz** — técnico-estratégico, directo, cero preámbulos (Bloque 02 de preferencias del operador).
3. **Progresión narrativa** — el documento se lee como flujo lógico, no como lista de partes.
4. **Diff mínimo** — cambiar lo necesario; no reescribir secciones completas si un parche quirúrgico basta.
5. **Coherencia transversal** — el cambio no debe contradecir otra sección sin resolución explícita.

Si surge la tentación de definir un criterio de calidad nuevo, verificar primero si ya existe en `MANUAL:PATCH-QUALITY-001` — citarlo si existe, proponer su alta ahí si no, nunca crear un contrato paralelo.

## Protocolo de ejecución

Al activarse, declarar: `RESUMING DOCUMENTATION — IMPLEMENTATION PHASE...`

### Fase 2 — DRY RUN de parches + Aprobación

1. Con el mapeo de nodos ya autorizado como insumo, generar el DRY RUN real: contenido completo de cada parche, en su nodo ya autorizado, con los IDs nuevos (si aplica) ya definidos.
2. Re-fetch en vivo de cada documento objetivo inmediatamente antes de redactar el DRY RUN — el mapeo de Fase 1 pudo haberse generado en otra sesión y el documento pudo cambiar desde entonces.
3. Validar cada parche contra los 5 filtros de `MANUAL:PATCH-QUALITY-001`.
4. **No escribir nada a Notion sin `APROBAR_WRITE` explícito** (tokens válidos: `APROBAR_WRITE`, `APROBAR`, `SÍ`, `sí`, `YEP`, `yep` — inválidos: `Ok`, `Go`, `yes`, `YES`). Este es un gate distinto e independiente del de autorización de la propuesta (Fase 1) — aplica sin excepción, incluso si el operador ya vio un DRY RUN idéntico antes en la misma sesión. Puede aprobarse por parche individual o por lote completo; declarar cuál aplica antes de escribir.

### Fase 3 — Inyección

Escribir cada parche autorizado respetando:
- Jerarquía tipográfica preexistente (H1/H2/H3).
- Negritas para conceptos clave y KPIs, cursivas para roles/cargos — solo si el documento objetivo ya usa esa convención.
- Transición lógica con el párrafo anterior y posterior (progresión narrativa) — el parche vive en su nodo, no se apila.
- `update_content` con `old_str`/`new_str` para páginas con column layout blocks (`replace_content` es poco fiable en esos casos). Si `old_str` no matchea, re-fetch en vivo antes de reintentar — nunca reintentar a ciegas sobre contenido cacheado.

### Fase 4 — Write-Back Verification (obligatoria, no opcional)

Después de cada escritura: **re-fetch de solo lectura** de la sección modificada, comparando contra el contenido esperado. Si hay mismatch → `WRITE-BACK MISMATCH`, reportar y no continuar sin resolución. Un Changelog o confirmación en chat de "ya se escribió" nunca es evidencia suficiente por sí sola (cache de Notion puede devolver estado pre-write en el primer fetch; doble-fetch es el patrón confiable).

### Fase 5 — Changelog y versión

1. Generar la entrada correspondiente en el Change Log (`390938be-fc42-80e7-b429-d7d730339353`) — única fuente de historial de versión; nunca escribir changelog dentro de los documentos individuales.
2. Actualizar la propiedad Versión del Change Log (referencia oficial del sistema) en la misma operación.
3. Si el cambio dio de alta o baja un ID canónico, ejecutar/recordar `KERNEL:CENSUS-SYNC` Regla 1 (regenerar Census) antes de cerrar el ticket asociado.
4. Confirmar al operador que Changelog y versión están escritos y verificados, para que corra `--sync` en Terminal sobre el resto de los documentos fundacionales.

### Fase 6 — Salida (Binary Gate)

Presentar al operador, para el resumen final de lo inyectado:
- **Opción A — Full Data Dump:** documento(s) completo(s) ya parchado(s), de una vez.
- **Opción B — Step-by-Step:** bloque por bloque, con explicación de cada cambio, esperando confirmación entre pasos.

Al entregar el resumen de salida, declarar el cierre del protocolo respondiendo: `DOCUMENTATION FINISHED`

## Checklist de validación pre-cierre

Antes de considerar la implementación completa, verificar:

- [ ] **Nodo:** cada bloque nuevo vive en el nodo autorizado en Fase 1, ningún adendum al final por default.
- [ ] **Re-fetch previo al DRY RUN:** documentos objetivo releídos en vivo antes de redactar (no se asumió el mapeo de Fase 1 como vigente sin verificar).
- [ ] **Changelog:** entrada generada, versión actualizada y coincidente en los documentos tocados.
- [ ] **Census:** si se creó/eliminó un ID canónico, `KERNEL:CENSUS-SYNC` Regla 1 ejecutada o explícitamente delegada al operador.
- [ ] **Consistencia:** el parche no contradice el System Prompt ni otro documento fundacional (`SP:CONSISTENCY`); no duplica contenido ya existente.
- [ ] **Write-Back:** re-fetch de verificación (Fase 4) sin mismatch pendiente.
- [ ] **Sync:** operador confirmado para correr `--sync` en Terminal.
- [ ] **Binary Gate:** opción elegida (Full Data Dump / Step-by-Step) y confirmación recibida.

Si algún punto falla, detener y reportar el gap — no declarar `DOCUMENTATION FINISHED` a medias.

## Deuda técnica y mitigación (patrón recurrente)

Toda implementación de este tipo deja como deuda mínima la regeneración de Census cuando hubo alta de ID. Plan de mitigación estándar: el operador ejecuta `generate_census.py` + `vversions --sync` (1–2 comandos, riesgo bajo, mitigación inmediata post-inyección). Si el operador pospone `APROBAR_WRITE` de algún parche del lote, registrar el pendiente en el tracker correspondiente (ver skill de propuesta, sección "Gestión de propuestas pendientes") en vez de asumir que se resolverá solo.

## Reglas de oro

- **Cero paternalismo** — no explicar lo evidente, actuar como socio técnico.
- **Honestidad estructural** — si el contenido nuevo contradice algo ya documentado, DETENER y reportar la discrepancia (`SP:CONSISTENCY`) en vez de escribir sobre la contradicción.
- **Token-efficient** — densidad de información sobre extensión.
- **Fail-fast** — si Terminal no está disponible para verificación de versión y la tarea lo requiere, detener y reportarlo; no hay bypass automatizado vía MCP para ese chequeo (`KERNEL:FAIL-PHILOSOPHY`).

## Limitación conocida — alcance por cuenta/sesión

Este archivo vive en `/mnt/skills/user/` de una cuenta/instalación específica de Claude. No viaja automáticamente a otra cuenta de claude.ai. Si el objetivo es que el protocolo de documentación transversal persista sin importar qué cuenta se use, la fuente de verdad canónica del contrato debe vivir también en un documento que se fetchea igual en cualquier cuenta (Kernel o System Prompt vía Notion MCP) — este skill y su contraparte de propuesta deben citar ese ID canónico en vez de duplicar la lógica únicamente aquí.
