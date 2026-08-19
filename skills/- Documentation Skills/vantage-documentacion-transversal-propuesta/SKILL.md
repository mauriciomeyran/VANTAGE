---
name: vantage-documentacion-transversal-propuesta
description: Genera la propuesta inicial de documentación transversal para un cambio estructural (regla, gate, flujo o parche) en VANTAGE — desde la detección del planteamiento hasta el mapeo completo de nodos tocantes en los documentos fundacionales, sin escribir ningún parche todavía. USAR cuando el operador pida "propuesta de documentación transversal", "mapeo de nodos" o similar para un cambio específico, o cuando durante cualquier otra tarea se detecte un cambio estructural (regla de gate, flujo operativo, schema) sin su contraparte documental. Esta es la mitad de solo-lectura del protocolo — no ejecuta DRY RUN ni escritura; para eso, transición explícita a vantage-documentacion-transversal-implementacion tras APROBAR_WRITE de la propuesta.
---

# Documentación Transversal VANTAGE — Fase 1: Propuesta de Nodos

Mitad de mapeo del protocolo de documentación transversal. Identifica qué documentos fundacionales toca un cambio y en qué nodo exacto de cada uno debe integrarse — sin redactar contenido de parche ni tocar Notion. El objetivo de este split es economía de tokens: cargar solo el mapeo cuando eso es lo único que se necesita, y reservar el protocolo completo de redacción/escritura para `vantage-documentacion-transversal-implementacion`.

## Alineación con KERNEL — Economía de Tokens Máxima

**KERNEL:DOCUMENTATION-010** — Protocolo de 6 fases (Mapeo → DRY RUN → Inyección → Write-Back Verification → Changelog + versión → Binary Gate de salida)

**KERNEL:DOCUMENTATION-005** — Convención de Anuncio de Skills: BEGINNING DOCUMENTATION MAPPING... / DOCUMENTATION MAPPING COMPLETE

**KERNEL:FAIL-PHILOSOPHY** — No sugiere workarounds, solo reporta estado y espera instrucción humana

**KERNEL:DOCUMENTATION-012** — Contrato de Cero Inferencia Silenciosa: toda afirmación técnica requiere ancla exacta (PREFIX:KEY)

## Protocolo de Ejecución Sandbox — Economía de Tokens Máxima

**Regla fundamental:** Todos los procesos internos corren en sandbox sin renderizar al operador. Solo se output:
1. `BEGINNING DOCUMENTATION MAPPING...` (inicio)
2. `PROPUESTA PRESENTADA` + propuesta estructurada (resultado final)
3. `DOCUMENTATION MAPPING COMPLETE` (cierre tras APROBAR_WRITE)

**Procesos silenciosos (sandbox interno):**
- Verificación de Changelog reciente
- Validación de consistencia con System Prompt
- Análisis de dependencias cruzadas
- Verificación de duplicidad
- Decisión de ID (nuevo vs reutilización)
- Validación de impacto en Census
- Validación de completitud del mapeo

## Cuándo se activa

**Modo explícito:** el operador pide "propuesta de documentación transversal", "mapeo de nodos", o presenta un cambio (regla nueva, gate nuevo, flujo modificado) y pide ubicarlo documentalmente antes de escribir nada.

**Modo derivado (recordatorio no-bloqueante):** en cualquier punto de la sesión, incluso dentro de otra tarea, si se detecta:
- Un script, schema o flujo operativo cambió pero ningún documento fundacional lo refleja.
- Una decisión de arquitectura se tomó en chat pero no quedó anclada a un `KERNEL:ID` o `MANUAL:ID`.
- El propio Changelog documenta un cambio sin ID canónico asociado (mismo patrón de riesgo ya visto en v9.1.1/v9.2.6: un Changelog puede registrar un write que nunca persistió, o un cambio de código nunca explicado en el Kernel).

En modo derivado: señalar el gap y preguntar si se quiere generar la propuesta ahora o dejarlo en el Tracker — nunca bloquear la tarea original en curso.

## Principio rector: nodo natural, no adendum

Ningún cambio se apila al final de un documento por comodidad. Cada pieza se integra en el nodo donde el flujo de lectura la necesita:

- **Kernel:** el orden de secciones es orden de prioridad operativa — si el contenido pertenece al inicio del flujo, se propone ahí, no después de la última sección existente.
- **Manual:** se lee como narrativa progresiva — el nodo propuesto debe encajar en la secuencia lógica del operador, nunca como capítulo aislado.
- La pregunta que resuelve el nodo no es "¿dónde cabe?" sino "¿en qué punto del flujo de lectura un operador que avanza en orden necesita esta información?".

Extender contratos existentes (`MANUAL:PATCH-QUALITY-001`, `SP:CONSISTENCY`, `KERNEL:GATE-DECISION`, etc.) en vez de reinventarlos. Si el cambio parece requerir un criterio de calidad nuevo, primero verificar si ya existe — citarlo si existe, proponer su alta si no.

## Protocolo de ejecución (Fase 1 — solo mapeo, sandbox interno)

Al activarse, declarar: `BEGINNING DOCUMENTATION MAPPING...`

### Paso 1 — Detectar fases evolutivas del cambio (sandbox interno)
[Proceso interno] Revisar la conversación/contexto disponible y ubicar en qué fase está el desarrollo del cambio (detección → auditoría → redacción → meta-documentación). Esto determina cuántos documentos y con qué profundidad se ven afectados.

### Paso 1.5 — Verificación de Changelog reciente (OBLIGATORIO, sandbox interno)
[Proceso interno] Revisar las últimas 5-10 entradas del Changelog para identificar:
- Cambios estructurales implementados sin documentación transversal
- Altas de scripts/skills que no tienen contraparte documental
- Cambios de schema que no fueron reflejados en KERNEL:SCHEMA
- Funcionalidades nuevas que requieren anchors

Si se detectan gaps, agregarlos al mapeo de nodos como "cambios pendientes de documentación".

### Paso 2 — Fetch operativo obligatorio de candidatos (sandbox interno)
[Proceso interno] `notion-fetch` en vivo de cada documento fundacional candidato — nunca desde memoria de sesión ni desde un volcado de texto previo. Esto captura también el string exacto del anchor (em-dashes, acentos, formato) para uso posterior en Fase 2/3 de implementación. Candidatos típicos según el tipo de cambio:
- Regla de gate / escalamiento → Kernel §9 (`KERNEL:GATE-DECISION*`), Census tabla KERNEL.
- Cambio de flujo operativo → Kernel §11–16, Manual §4 (`MANUAL:FLUJO-001`).
- Regla de consistencia o versión → System Prompt (`SP:CONSISTENCY`, `SP:SYNC-RULE`).
- Cambio de schema de tracker → Kernel §7–8 (`KERNEL:SCHEMA*`, `KERNEL:TRACKER-SCHEMA*`), SP §7 (`SP:SCHEMA`).
- Cualquier alta/baja de ID canónico → ID CENSUS (dispara Regla 1 de CENSUS-SYNC).

### Paso 2.5 — Validación de consistencia con System Prompt (OBLIGATORIO, sandbox interno)
[Proceso interno] Para cada nodo propuesto, verificar contra System Prompt:
- ¿Contradice SP:CONSISTENCY? (ancla exacta requerida)
- ¿Viola algún contrato de SP:GATE-DECISION? (ancla exacta requerida)
- ¿Está alineado con SP:SCHEMA si aplica a datos? (ancla exacta requerida)
- ¿Respecta SP:FAIL-PHILOSOPHY si es sobre manejo de errores? (ancla exacta requerida)

Si hay contradicción, DETENER y reportar al operador con ancla exacta (PREFIX:KEY) antes de continuar.

### Paso 3 — Mapear nodos naturales (sandbox interno)
[Proceso interno] Para cada documento candidato, identificar el nodo exacto de inserción (sección, subsección, ID adyacente) según el principio rector — nunca el final del documento por default. Incluir también documentos no-Notion que el cambio pueda tocar: skills locales (`/mnt/skills/user/`), trackers (Bug/Tasks), y si aplica, el propio Changelog.

**3.1 Identificación del nodo natural:**
- Sección/subsección donde el flujo de lectura necesita esta información
- ID adyacente más relevante para contexto
- Posición en la narrativa progresiva (no adendum)

**3.2 Análisis de dependencias cruzadas:**
- Búsqueda inversa en Census de IDs que citan el nodo (KERNEL:DOCUMENTATION-011)
- Identificación de referencias cruzadas en otros documentos
- Skills locales que dependen del contrato
- Documentos susceptibles de actualización para armonía

**3.3 Verificación de duplicidad:**
- ¿El contenido ya existe en otro documento? (ancla exacta requerida)
- ¿El concepto ya está documentado bajo otro ID? (ancla exacta requerida)
- ¿Hay redundancia operativa con otra sección? (ancla exacta requerida)

Si se detecta duplicidad:
- Si es el mismo concepto, proponer consolidación en vez de nuevo nodo
- Si es matiz distinto, justificar por qué requiere separación (con ancla exacta)
- Si es redundancia, proponer eliminación en vez de alta (con ancla exacta)

**3.4 Decisión de ID (nuevo vs reutilización):**
- Aplicar criterios explícitos de nuevo ID vs reutilización (KERNEL:DOCUMENTATION-001)
- Si ambigüedad, preguntar al operador (con ancla exacta)

**3.5 Validación de consistencia:**
- Verificar contra SP:CONSISTENCY (ancla exacta requerida)
- Verificar contra otros contratos del System Prompt (ancla exacta requerida)
- Si contradicción, detener y reportar (con ancla exacta)

**3.6 Inclusión de documentos no-Notion:**
- Skills locales (`/mnt/skills/user/`)
- Trackers (Bug/Tasks)
- Changelog si aplica
- generate_census.py si afecta CENSUS_SPEC

### Paso 4 — Presentar la propuesta estructurada (único output visible)
[ÚNICO OUTPUT AL OPERADOR] Entregar al operador, sin contenido de parche todavía:
- Documento(s) y nodo(s)/sección(es) exactos donde se integraría cada pieza.
- IDs nuevos propuestos (`KERNEL:ID` / `MANUAL:ID` / etc.) o IDs existentes que se reutilizan.
- Si dispara `KERNEL:CENSUS-SYNC` Regla 1 (alta/baja de ID canónico → regeneración de Census obligatoria antes de cerrar).
- Lista completa de documentos/skills "susceptibles de actualización para armonía" — aunque no reciban contenido nuevo, si una referencia cruzada suya queda desactualizada por el cambio, se listan aquí.
- Requisitos de `APROBAR_WRITE` que aplicarán en la fase de implementación (para que el operador sepa qué viene).

Declarar: `PROPUESTA PRESENTADA`

### Paso 4.5 — Validación de impacto en Census (OBLIGATORIO, sandbox interno)
[Proceso interno] Para cada nodo propuesto, verificar:
- ¿Es alta/baja de ID canónico? → Dispara CENSUS-SYNC Regla 1 (KERNEL:DOCUMENTATION-008)
- ¿Es cambio de sección/nombre de ID existente? → Requiere actualización de Census
- ¿Es cambio que afecta la estructura de CENSUS_SPEC? → Requiere actualización del script generate_census.py

Si afecta el Census, declarar explícitamente en la propuesta final:
- Qué acción de Census se requiere (regeneración, actualización de spec, etc.)
- Cuándo debe ejecutarse (antes/después de la implementación)
- Qué comandos exactos debe correr el operador (vcensus, vversions --sync)

### Paso 4.6 — Validación de completitud del mapeo (OBLIGATORIO, sandbox interno)
[Proceso interno] Antes de presentar la propuesta, verificar:
- [ ] Todos los documentos fundacionales candidatos fueron evaluados
- [ ] Todas las dependencias cruzadas fueron identificadas
- [ ] Todos los gaps del Changelog reciente fueron considerados
- [ ] Todas las inconsistencias con System Prompt fueron resueltas (con anclas exactas)
- [ ] Todas las duplicidades potenciales fueron verificadas (con anclas exactas)
- [ ] El impacto en Census fue evaluado (según KERNEL:DOCUMENTATION-008)
- [ ] La lista de "susceptibles de actualización" está justificada

Si algún punto falla, DETENER y completar antes de presentar la propuesta.

### Criterios explícitos para "susceptibles de actualización" (sandbox interno)

[Proceso interno] Un documento/skill se considera susceptible si:
1. **Referencia directa:** Cita explícitamente el ID que se está modificando
2. **Dependencia contractual:** Su operación depende del contrato que se cambia
3. **Referencia conceptual:** Describe el concepto/flujo que se está modificando
4. **Cascada de impacto:** Un cambio en este documento dispara cambios en otros
5. **Consistencia de versión:** Tiene versión que debe mantenerse sincronizada

NO se considera susceptible si:
- Solo menciona el tema tangencialmente sin dependencia operativa
- Es un documento de metadatos (índices, manifests) que se actualiza automáticamente
- El cambio es puramente cosmético (formato, sin impacto operativo)

### Criterios para nuevo ID vs reutilización (sandbox interno)

[Proceso interno] **Crear nuevo ID si:**
- Es un concepto/contrato completamente nuevo
- Requiere sección propia con subsecciones anidadas (siguiendo Matriz Tipográfica Congelada)
- Tiene ciclo de vida independiente del concepto padre
- Necesita referencias cruzadas específicas

**Reutilizar ID existente si:**
- Es extensión de un contrato ya existente (añadir criterio, matiz)
- El concepto ya está documentado y solo requiere actualización
- No requiere estructura de subsecciones separada
- Las referencias cruzadas existentes siguen siendo válidas

**Ambigüedad:** Si no está claro, PREGUNTAR al operador antes de proponer (con ancla exacta de KERNEL:DOCUMENTATION-001).

### Paso 5 — Esperar autorización explícita
No redactar un solo parche ni hacer DRY RUN. Esperar confirmación del operador sobre el mapeo de nodos. Tokens de autorización válidos para pasar a implementación: `APROBAR_WRITE`, `APROBAR`, `SÍ`, `sí`, `YEP`, `yep` (inválidos: `Ok`, `Go`, `yes`, `YES` — estos no cuentan como autorización, solo como acuse conversacional).

Al recibir autorización válida, indicar explícitamente que la continuación requiere invocar `vantage-documentacion-transversal-implementacion` y no continuar la redacción dentro de este skill.

Declarar: `DOCUMENTATION MAPPING COMPLETE`

## Salida de este skill

El output de Fase 1 es exclusivamente:
1. El bloque de propuesta (Paso 4).
2. La confirmación de que se requiere transición a `-implementacion` para continuar.

Nunca contenido de parche completo, nunca escritura a Notion, nunca DRY RUN — eso vive en la otra mitad del protocolo.

## Limitación conocida

Esta propuesta es mapeo estático — no ejecuta inyección ni verifica write-back. Requiere transición explícita a `vantage-documentacion-transversal-implementacion` para la implementación completa (DRY RUN → Inyección → Write-Back → Changelog → Salida).

## Gestión de propuestas pendientes

Si el operador decide no avanzar a implementación ahora, registrar en **Tasks Tracker** (`d2a65ca1-6a35-465d-bcff-b0d82dddd549`):
- Título: `[DOC] Propuesta pendiente: [descripción breve]`.
- Prioridad: Alta (flujo crítico) / Media (mejora no urgente) / Baja (cosmético).
- IDs relacionados: los `KERNEL:ID`/`MANUAL:ID` afectados o propuestos, y el mapeo de nodos ya generado (para no repetir Fase 1 en la siguiente sesión).
- Contexto: qué cambio documenta y por qué se pospuso.

Revisar el Tracker al inicio de cada sesión (`vantage-session-open`) para no perder propuestas de mapeo pendientes.
