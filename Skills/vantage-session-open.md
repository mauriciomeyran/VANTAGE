---
name: vantage-session-open
description: Bootstrap VANTAGE (Ledger -> Changelog -> Context).
---
VANTAGE: OPEN PROTOCOL

0. ANNOUNCE: Declara el inicio del protocolo respondiendo: SESSION-OPENING...
1. LEDGER: Query SESSION LEDGER (collection://38324240-c686-47d0-8082-cee5e4409f88) (Fila más reciente). status != CLOSED -> WARN. Crear fila: `Session ID` [generado], `Status: OPEN`, `Opened At` [ahora]. (1 sola llamada).
2. HEALTH: Confirmar SYSTEM PROMPT + ID CENSUS fetched vía MCP. Falla -> STOP, "VANTAGE: MODO DEGRADADO".
3. LOG: Última entrada de V-CHANGELOG (1 solo fetch del bloque superior), resumen de 1 frase.
4. PENDING: Leer el campo `Pending Summary` de la fila del Ledger obtenida en el Paso 1. No hacer queries adicionales.
5. SNAPSHOT: El operador pegará el dump crítico generado mediante el flag `--bootstrap` local. Queda estrictamente prohibido que Claude intente buscar o leer tareas adicionales a través de la API. Si no hay tareas críticas en el dump, reportar "SNAPSHOT: 0 TAREAS CRÍTICAS".
6. READY: Declara el cierre del protocolo respondiendo: SESSION-OPENED: VANTAGE READY + versión.

NOTA (v9.6.2): La verificación de versión de los 7 documentos fundacionales ya no ocurre en la apertura de sesión. El modo Check (`--check`) de `verify_versions.py` fue eliminado — la única verificación de versión real vive ahora en `--sync` (modo de escritura), ejecutado exclusivamente en el cierre de sesión (`vantage-session-close`, Paso 4). Si el operador necesita confirmar versión durante una sesión abierta, debe correr `--sync` manualmente o esperar al cierre formal.

GUARDRAILS: Cero recursividad. Claude no busca consistencia de archivos leyendo bases de datos completas; valida basándose exclusivamente en el output de la terminal local provisto por el operador.
