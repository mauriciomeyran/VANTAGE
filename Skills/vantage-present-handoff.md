---
name: vantage-present-handoff
description: Genera y entrega un snapshot de contexto de sesion para continuidad en un chat nuevo. Skill independiente, invocable en cualquier momento, no depende de vantage-session-close, aunque esta ultima debe invocarla como parte de su secuencia normal de cierre.
---

## Convencion de anuncio (KERNEL:SKILL-ANNOUNCE-CONVENTION)

- Apertura: HANDING OFF...
- Cierre: HANDOFF DELIVERED

Esta convencion se respeta incluso en el escenario de emergencia (sin tokens): los dos verbos ocupan una sola linea cada uno, no cuentan como prosa adicional prohibida, son el marcador de protocolo, no comentario.

## Exencion de KERNEL:CENSUS-SYNC Regla 4

Esta skill nunca escribe en Notion, es lectura de contexto de sesion unicamente. Por lo tanto no dispara el reporte de cierre de Regla 4 (ese reporte aplica a sesiones con cambios reales a documentacion o bases de datos). Si el Handoff se invoca dentro de vantage-session-close, es esa skill, no esta, la que produce el resumen DRY RUN de cierre si hubo escrituras en la sesion.

## Regla critica, cero friccion, una sola pasada

Al invocar esta skill:

- Prohibido: preambulos, afirmaciones, preguntas de clarificacion, llamadas a Notion MCP para verificar nada nuevo.
- Obligatorio: entregar el handoff completo de inmediato, en un solo bloque, usando exclusivamente lo que ya esta en el contexto de la sesion actual (memoria de trabajo, no fetch nuevo).
- Si algun dato no esta disponible en el contexto actual, se marca [NO DISPONIBLE EN ESTA SESION], nunca se inventa, nunca se detiene la generacion para preguntar.

## Relacion con el Session Ledger (KERNEL:SESSION-LEDGER, seccion 21)

El Ledger tiene 4 propiedades reales: session_id, status (OPEN/CLOSED), opened_at, pending_summary. El campo pending_summary es espejo del bloque COMPLETADO/PENDIENTE del ultimo Session Close, el Handoff que genera esta skill debe ser consistente con ese mismo bloque, no inventar una estructura paralela y desalineada. Si vantage-session-close ya poblo pending_summary en esta sesion, ese contenido es la base del Handoff, no un dato distinto.

Esta skill NUNCA escribe en el Ledger, solo lee/refleja lo que ya existe en el contexto de la sesion. Escritura del Ledger es exclusiva de vantage-session-open (paso 0) y vantage-session-close (paso 6).

## Contenido obligatorio del Handoff

Estructura de salida (Markdown plano):

TITULO: VANTAGE HANDOFF, fecha y hora de sesion

SECCION 1: Session IDs / Notion IDs necesarios para continuar sin friccion
- session_id (Ledger), si existe en contexto
- Cualquier page_id, data_source_id o URL de Notion tocado o relevante en esta sesion

SECCION 2: Pendientes de ESTA sesion (sin resolver al momento del handoff)
- Tareas abiertas, decisiones pendientes, dry-runs sin aprobar

SECCION 3: Pendientes HEREDADOS (de los que se tenga registro en esta sesion)
- Pendientes de sesiones anteriores mencionados o retomados en esta sesion, no se inventa historico no visto

SECCION 4: Ultima accion confirmada
- Ultimo APROBAR_WRITE ejecutado con exito, o ultimo estado verificado

SECCION 5: Contexto operativo minimo para arrancar
- Version de VANTAGE en uso esta sesion, si se conoce
- Cualquier discrepancia de version o gap detectado sin resolver, ver SP:CONSISTENCY

## Ruta alterna de bajo costo (Terminal, sin tokens de chat)

verify_versions.py --bootstrap (Layer_1/scripts/, confirmado por lectura directa del script) genera un dump equivalente: ultima fila del Session Ledger, version vigente del Changelog, tickets CRITICO/ALTO de Bug+Tasks Tracker, via httpx directo a la API de Notion, sin pasar por MCP ni por esta skill. Si el operador prefiere no gastar tokens de chat en absoluto, puede correr ese comando en Terminal y pegar el output de 7 lineas en la siguiente sesion en vez de invocar esta skill. Las dos rutas no se contradicen, resuelven el mismo problema por vias distintas (chat vs Terminal).

## Reglas de oro

- Esta skill nunca abre ni cierra sesion en el Ledger.
- vantage-session-close debe incluir la invocacion de este handoff como parte de su secuencia de cierre normal (ahi si, con tokens disponibles y prosa normal permitida).
- Esta skill es la version de emergencia: minimo consumo, maxima cobertura, una sola pasada.

## Fuentes verificadas (sesion 2026-07-19)

SP:CONSISTENCY: confirmado en System Prompt (seccion 10, regla de reporte de discrepancias), fetch directo, sesion 2026-07-19. No es referencia huerfana.

Estructura de 4 campos del Session Ledger (session_id, status, opened_at, pending_summary): confirmada contra KERNEL:SESSION-LEDGER (seccion 21, Kernel, fetch directo). Ruta alterna --bootstrap: confirmada por lectura directa de verify_versions.py (funcion render_bootstrap_dump), no inferida del nombre del flag.