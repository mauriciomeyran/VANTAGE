---
name: vantage-documentacion-transversal-propuesta
description: Genera la propuesta inicial de documentación transversal para un cambio estructural (regla, gate, flujo o parche) en VANTAGE — desde la detección del planteamiento hasta el mapeo completo de nodos tocantes en los documentos fundacionales, sin escribir ningún parche todavía. USAR cuando el operador pida "propuesta de documentación transversal", "mapeo de nodos" o similar para un cambio específico, o cuando durante cualquier otra tarea se detecte un cambio estructural (regla de gate, flujo operativo, schema) sin su contraparte documental. Esta es la mitad de solo-lectura del protocolo — no ejecuta DRY RUN ni escritura; para eso, transición explícita a vantage-documentacion-transversal-implementacion tras APROBAR_WRITE de la propuesta.
---

# Documentación Transversal VANTAGE — Fase 1: Propuesta de Nodos

Mitad de mapeo del protocolo de documentación transversal. Identifica qué documentos fundacionales toca un cambio y en qué nodo exacto de cada uno debe integrarse — sin redactar contenido de parche ni tocar Notion. El objetivo de este split es economía de tokens: cargar solo el mapeo cuando eso es lo único que se necesita, y reservar el protocolo completo de redacción/escritura para `vantage-documentacion-transversal-implementacion`.

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

## Protocolo de ejecución (Fase 1 — solo mapeo)

Al activarse, declarar: `BEGINNING DOCUMENTATION MAPPING...`

### Paso 1 — Detectar fases evolutivas del cambio
Revisar la conversación/contexto disponible y ubicar en qué fase está el desarrollo del cambio (detección → auditoría → redacción → meta-documentación). Esto determina cuántos documentos y con qué profundidad se ven afectados.

### Paso 2 — Fetch operativo obligatorio de candidatos
`notion-fetch` en vivo de cada documento fundacional candidato — nunca desde memoria de sesión ni desde un volcado de texto previo. Esto captura también el string exacto del anchor (em-dashes, acentos, formato) para uso posterior en Fase 2/3 de implementación. Candidatos típicos según el tipo de cambio:
- Regla de gate / escalamiento → Kernel §9 (`KERNEL:GATE-DECISION*`), Census tabla KERNEL.
- Cambio de flujo operativo → Kernel §11–16, Manual §4 (`MANUAL:FLUJO-001`).
- Regla de consistencia o versión → System Prompt (`SP:CONSISTENCY`, `SP:SYNC-RULE`).
- Cambio de schema de tracker → Kernel §7–8 (`KERNEL:SCHEMA*`, `KERNEL:TRACKER-SCHEMA*`), SP §7 (`SP:SCHEMA`).
- Cualquier alta/baja de ID canónico → ID CENSUS (dispara Regla 1 de CENSUS-SYNC).

### Paso 3 — Mapear nodos naturales
Para cada documento candidato, identificar el nodo exacto de inserción (sección, subsección, ID adyacente) según el principio rector — nunca el final del documento por default. Incluir también documentos no-Notion que el cambio pueda tocar: skills locales (`/mnt/skills/user/`), trackers (Bug/Tasks), y si aplica, el propio Changelog.

### Paso 4 — Presentar la propuesta estructurada
Entregar al operador, sin contenido de parche todavía:
- Documento(s) y nodo(s)/sección(es) exactos donde se integraría cada pieza.
- IDs nuevos propuestos (`KERNEL:ID` / `MANUAL:ID` / etc.) o IDs existentes que se reutilizan.
- Si dispara `KERNEL:CENSUS-SYNC` Regla 1 (alta/baja de ID canónico → regeneración de Census obligatoria antes de cerrar).
- Lista completa de documentos/skills "susceptibles de actualización para armonía" — aunque no reciban contenido nuevo, si una referencia cruzada suya queda desactualizada por el cambio, se listan aquí.
- Requisitos de `APROBAR_WRITE` que aplicarán en la fase de implementación (para que el operador sepa qué viene).

### Paso 5 — Esperar autorización explícita
No redactar un solo parche ni hacer DRY RUN. Esperar confirmación del operador sobre el mapeo de nodos. Tokens de autorización válidos para pasar a implementación: `APROBAR_WRITE`, `APROBAR`, `SÍ`, `sí`, `YEP`, `yep` (inválidos: `Ok`, `Go`, `yes`, `YES` — estos no cuentan como autorización, solo como acuse conversacional).

Al recibir autorización válida, indicar explícitamente que la continuación requiere invocar `vantage-documentacion-transversal-implementacion` y no continuar la redacción dentro de este skill.

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
