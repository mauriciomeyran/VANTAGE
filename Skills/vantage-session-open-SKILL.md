---
name: vantage-session-open
description: Bootstrap VANTAGE (Ledger -> Version Check -> Changelog -> Context).
---
VANTAGE: OPEN PROTOCOL

0. LEDGER: Query SESSION LEDGER (collection://8d736032-eef9-4e6e-a05a-df8b8079ebff) (Fila más reciente)[span_3](start_span)[span_3](end_span). status != CLOSED -> WARN[span_4](start_span)[span_4](end_span). Crear fila: `Session ID` [generado], `Status: OPEN`, `Opened At` [ahora][span_5](start_span)[span_5](end_span). (1 sola llamada).
1. HEALTH: Confirmar SYSTEM PROMPT + ID CENSUS fetched vía MCP[span_6](start_span)[span_6](end_span). Falla -> STOP, "VANTAGE: MODO DEGRADADO[span_7](start_span)"[span_7](end_span).
2. VERSION: El operador ejecutará localmente `python3 scripts/verify_versions.py --check` y pegará el output en este chat[span_8](start_span)[span_8](end_span). 
   - **Regla Estricta**: Claude tiene prohibido realizar fetch manual o individual de los componentes fundacionales mediante llamadas MCP de lectura[span_9](start_span)[span_9](end_span). Si el operador no ha pegado el output, Claude se detiene y lo solicita.
3. LOG: Última entrada de V-CHANGELOG (1 solo fetch del bloque superior), resumen de 1 frase[span_10](start_span)[span_10](end_span).
4. PENDING: Leer el campo `Pending Summary` de la fila del Ledger obtenida en el Paso 0[span_11](start_span)[span_11](end_span). No hacer queries adicionales.
5. SNAPSHOT: El operador pegará el dump crítico generado mediante el flag `--bootstrap` local. Queda estrictamente prohibido que Claude intente buscar o leer tareas adicionales a través de la API[span_12](start_span)[span_12](end_span). Si no hay tareas críticas en el dump, reportar "SNAPSHOT: 0 TAREAS CRÍTICAS".
6. READY: "VANTAGE READY" + versión[span_13](start_span)[span_13](end_span).

GUARDRAILS: Cero recursividad. Claude no busca consistencia de archivos leyendo bases de datos completas[span_14](start_span)[span_14](end_span); valida basándose exclusivamente en el output de la terminal local provisto por el operador[span_15](start_span)[span_15](end_span).