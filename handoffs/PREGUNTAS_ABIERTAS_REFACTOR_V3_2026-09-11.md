# PREGUNTAS_ABIERTAS - Refactor VANTAGE Tracker (Actualizado v3)

**Generado por:** Devin  
**Fecha:** 2026-09-11 (corregido según revisión Mau v2 - B7/B9/R4 resueltos)  
**Contrato:** HO-000041 + Revisión B1-B10/A1-A5/R1-R8

---

## Q-1: Decisión sobre `REVIEW_NEEDED` (radiografía §4.6)

**Pregunta:** El Manual y `MANUAL:WEEKLY-FLOW-002` afirman que mientras `Status=REVIEW_NEEDED`, Python no calcula Class B. Esto es **falso en código** — cero chequeos de ese estado existen en el orquestador.

**Decisión tomada:** Implementar de verdad el bloqueo (opción a).

**Implementación:** En `tracker_flow.is_mutable()`, si `Status=Por revisar` (renombrado desde REVIEW_NEEDED), el actor `PIPELINE` retorna False para cualquier mutación de Class B. Solo el actor `HUMANO` puede mutar Class B en ese estado.

**Alternativas descartadas:**
- Opción b (eliminar contrato del Manual): descartada porque rompe la expectativa del operador documentada
- Dejar documentado-sin-implementar: prohibido por contrato §2.2

**Qué dato la cerraría:** Confirmación de Mau sobre si el bloqueo real es el comportamiento deseado, o si prefiere eliminar el contrato del Manual.

**Impacto si se revierte:** Alto - requeriría revertir is_mutable() y actualizar Manual.

---

## Q-2: Tipo real de `Holding` y decisión final

**Pregunta:** ¿Es `Holding` un select o rich_text en el schema vivo? Confirmado sin lector en el pipeline.

**Decisión tomada:** Convertir en select curado poblado únicamente desde `alias_map.json` (sin fallback textual).

**Implementación:** 
1. Cambiar tipo de propiedad a select en Notion (confirmado por Claude vía MCP)
2. Poblar opciones desde `alias_map.json` (migración one-time)
3. Eliminar fallback textual en feed_processor.py

**Alternativas descartadas:**
- Eliminar completamente: descartada porque podría tener uso futuro no detectado
- Mantener como texto libre: prohibido por contrato §4 ("87.5% de ruido")

**Qué dato la cerraría:** Schema vivo de Notion confirmado por Claude vía MCP.

**Impacto si se revierte:** Medio - requeriría revertir migración de tipo de propiedad.

---

## Q-3: Nombre exacto de `Source_Type` - trailing space

**Pregunta:** ¿El trailing space en `Source_Type ` existe realmente en el schema vivo, o es artefacto de una versión anterior?

**Decisión tomada:** Asumir que existe (trampa real confirmada en feed_processor.py).

**Implementación:** Renombrar a `Source_Type` limpio, con migración de datos.

**Alternativas descartadas:**
- Asumir que es artefacto: descartado porque feed_processor.py chequea el nombre sin espacio y el orquestador lo lee con espacio - la discrepancia es real

**Qué dato la cerraría:** Schema vivo de Notion confirmado por Claude vía MCP.

**Impacto si se revierte:** Bajo - requeriría revertir renombramiento de propiedad.

---

## Q-4: Existencia real de checkbox `Archivar`

**Pregunta:** ¿Existe el checkbox `Archivar` en el schema vivo, o es confusión heredada?

**Decisión tomada:** Asumir que existe (mecanismo triple-overload confirmado en radiografía §5.2).

**Implementación:** Consolidar en `Next_Action=Archivar` como señal de negocio + checkbox `Archivar` como ejecución manual confirmada. Eliminar `Status=Archivar` del vocabulario.

**Alternativas descartadas:**
- Asumir que no existe: descartado porque la radiografía confirma triple-overload

**Qué dato la cerraría:** Schema vivo de Notion confirmado por Claude vía MCP.

**Impacto si se revierte:** Medio - requeriría revertir consolidación de mecanismo de archivo.

---

## Q-5: Existencia real de `fetch_status` vs `Fetch`

**Pregunta:** ¿Coexisten `fetch_status` (ingesta W2) y `Fetch` (orquestador) en el schema vivo, o es confusión heredada?

**Decisión tomada:** Fusionar en una sola propiedad con un solo vocabulario.

**Implementación:** Unificar en `Fetch` con vocabulario `Accesible/Bloqueado`. Migrar datos de `fetch_status` a `Fetch`.

**Alternativas descartadas:**
- Mantener ambos: descartado porque duplicidad sin propósito claro

**Qué dato la cerraría:** Schema vivo de Notion confirmado por Claude vía MCP.

**Impacto si se revierte:** Medio - requeriría revertir migración de propiedad.

---

## Q-6: Umbral de días para "edición manual reciente"

**Pregunta:** ¿Cuántos días define "edición manual reciente" para activar protección manual en `is_mutable()`?

**Decisión tomada:** 7 días (default razonable para workflow semanal).

**Implementación:** `_was_edited_since_last_run()` usa state file `state/last_successful_run.json` (CORREGIDO R1). Si state file no existe, fallback a 7 días.

**Alternativas descartadas:**
- 1 día: demasiado agresivo, activaría protección para ediciones legítimas de hace 2 días
- 30 días: muy laxo, no protegería suficientemente
- Timestamp del último run: requiere persistir estado del run (implementado en R1)

**Qué dato la cerraría:** Confirmación de Mau sobre el umbral deseado.

**Impacto si se revierte:** Bajo - solo cambiar el número en una línea.

---

## Q-7: Mecanismo de precedencia manual - implementación completa

**Pregunta:** ¿Cómo implementar "comparar contra timestamp del último run exitoso" para activar protección manual?

**Decisión tomada:** Implementación completa con state file (CORREGIDO R1).

**Implementación:** `_was_edited_since_last_run()` usa state file `state/last_successful_run.json` con timestamp del último run exitoso. Si state file no existe, fallback a 7 días.

**Alternativas descartadas:**
- Implementación simplificada solo con umbral fijo: descartada en v3, ahora usa state file
- Usar `Last_Gate_Run` como proxy: no confiable porque F4 lo reescribe en cada run (bug a corregir)

**Qué dato la cerraría:** Confirmación de Mau sobre si la implementación con state file es suficiente.

**Impacto si se revierte:** Medio - requeriría revertir mecanismo de state file.

---

## Q-8: Ventana de congelamiento para migración

**Pregunta:** ¿Cuánto tiempo debe durar la ventana de congelamiento de escritura manual durante la migración?

**Decisión tomada:** 2 horas (estimación basada en tamaño típico del Tracker ~200 filas).

**Implementación:** Documentar en plan de despliegue que el operador no debe editar manualmente durante este período. Dependencia explícita del operador (CORREGIDO B9).

**Alternativas descartadas:**
- 30 minutos: muy agresivo, podría no ser suficiente
- 1 día: muy largo, impactaría workflow del operador
- Sin congelamiento: arriesgado, podría causar conflictos durante migración

**Qué dato la cerraría:** Confirmación de Mau sobre la duración aceptable.

**Impacto si se revierte:** Bajo - solo cambiar la documentación del plan.

---

## Q-9: Aéropostale como Hard Block

**Pregunta:** El contrato §2.2 confirma que Aéropostale NO es Hard Block. ¿Debe el refactor preservar explícitamente esta excepción en el código, o es suficiente con el comentario?

**Decisión tomada:** Preservar explícitamente en código con comentario citando la decisión del operador.

**Implementación:** En `profile_fit.resolve_alias_flags()`, agregar comentario explícito: "# Aéropostale NO es Hard Block - confirmado con operador 2026-08-07".

**Alternativas descartadas:**
- Solo comentario: insuficiente, podría ser eliminado accidentalmente en refactor futuro
- Hardcodearlo en código: innecesario, ya está en alias_map.json

**Qué dato la cerraría:** Confirmación de Mau de que la decisión sigue vigente.

**Impacto si se revierte:** Bajo - solo eliminar un comentario.

---

## Q-10: Tests de alcanzabilidad - cobertura mínima

**Pregunta:** ¿Cuál es la cobertura mínima aceptable de tests de alcanzabilidad para ramas destructivas?

**Decisión tomada:** 100% - cada rama destructiva debe tener un test que la ejecute.

**Implementación:** Test suite con un test por cada rama `if` con efecto de escritura en tracker_flow.py y orquestador refactorizado. ~50 tests (CORREGIDO A5 - no 30-40).

**Alternativas descartadas:**
- 90%: insuficiente, deja ramas sin test
- 80%: muy insuficiente, alto riesgo de código muerto

**Qué dato la cerraría:** Confirmación de Mau sobre que 100% es aceptable.

**Impacto si se revierte:** Medio - requeriría escribir tests adicionales.

---

## Q-11: IDs de integración conocidos para KNOWN_BOT_IDS (R1)

**Pregunta:** ¿Qué IDs de integración deben agregarse a KNOWN_BOT_IDS para detectar bots vs humanos?

**Decisión tomada:** Dejar lista vacía inicial, agregar IDs según confirmación MCP.

**Implementación:** KNOWN_BOT_IDS = {} inicial. Agregar IDs después de confirmación con Claude vía MCP.

**Alternativas descartadas:**
- Adivinar IDs: riesgo de falsos positivos
- Usar solo fallback 7 días: deja sin protección contra bots recientes

**Qué dato la cerraría:** Confirmación de Claude vía MCP de qué IDs de integración usa MCP Dashboard.

**Impacto si se revierte:** Bajo - solo agregar IDs a la lista.

---

## Q-12: Formato y consumidor de propose-log (B7)

**Pregunta:** ¿Cuál es el formato del propose-log, quién lo consume, y por qué vía se confirma/ejecuta cada propuesta?

**Decisión tomada:** Formato estandarizado en Notas, consumido por skill vantage-tidy-opportunities-tracker, confirmado vía APROBAR_WRITE en sesión Claude.

**Implementación:** 
- Formato: `[PROPOSE] {actor} → {to_status}: {reason}\nEvidencia: {evidence}\nPágina: {page_id}\nTimestamp: {timestamp}`
- Consumidor: skill vantage-tidy-opportunities-tracker (lee Notas para filas marcadas)
- Vía de confirmación: APROBAR_WRITE vía sesión Claude

**Alternativas descartadas:**
- Cola con TTL: demasiado complejo para sistema de un solo operador
- Log en archivo separado: no visible en Notion para el operador

**Qué dato la cerraría:** Confirmación de Mau sobre que este flujo es aceptable.

**Impacto si se revierte:** Medio - requeriría cambiar formato y consumidor.

---

## Q-13: Auto-ejecución en filas operativas (B7)

**Pregunta:** ¿Las filas operativas NO tocadas por humano se archivan directo o también van a propose-log?

**Decisión tomada:** Auto-ejecución en filas operativas NO tocadas por humano (CORREGIDO B7).

**Implementación:** `auto_execute_on_operational=True` en transiciones de archivo. Si `requires_propose_log=True` AND `auto_execute_on_operational=True` AND NOT tocado por humano → auto-ejecutar.

**Alternativas descartadas:**
- Todo a propose-log: el pipeline jamás ejecuta solo, pierde su propósito
- Todo auto-ejecutar: deja sin protección filas humanas/postulaciones vivas

**Qué dato la cerraría:** Confirmación de Mau sobre que este modelo híbrido es aceptable.

**Impacto si se revierte:** Alto - requeriría rediseñar modelo de aprobación.

---

## RESUMEN DE IMPACTO

- **Alto:** Q-1 (REVIEW_NEEDED), Q-13 (auto-ejecución vs propose-log)
- **Medio:** Q-2 (Holding), Q-4 (checkbox Archivar), Q-5 (fetch_status), Q-7 (precedencia manual), Q-10 (tests), Q-12 (propose-log)
- **Bajo:** Q-3 (Source_Type), Q-6 (umbral días), Q-8 (ventana congelamiento), Q-9 (Aéropostale), Q-11 (KNOWN_BOT_IDS)

---

**NOTA:** Ninguna escritura a Notion de producción fue realizada ni intentada en esta sesión.
