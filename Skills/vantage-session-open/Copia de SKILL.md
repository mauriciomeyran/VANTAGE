---
name: vantage-session-open
description: Bootstrap VANTAGE (Ledger -> Version Check -> Changelog -> Context).
---
VANTAGE: OPEN PROTOCOL

0. LEDGER: Query SESSION LEDGER (collection://8d736032-eef9-4e6e-a05a-df8b8079ebff), fila más reciente por `Opened At`. status != CLOSED -> WARN. Crear fila: `Session ID` [generado], `Status: OPEN`, `Opened At` [ahora].
1. HEALTH: Confirmar SYSTEM PROMPT + ID CENSUS fetched vía MCP. Falla -> STOP, "VANTAGE: MODO DEGRADADO".
2. VERSION: Operador corre `python3 scripts/verify_versions.py --check` (Layer_1/), pega output.
   - Expect: `PASS — all components at vX.X.X`.
   - Fail: `OUTDATED: [name] -> [version]` y/o `VERSION SET: {...}` -> STOP, reportar, esperar.
   - Sin Terminal -> fallback: fetch de los 6 fundacionales, comparar vs CHANGE LOG.
3. LOG: Última entrada de V-CHANGELOG, resumen 1 frase.
4. PENDING: `Pending Summary` de la fila cerrada del Ledger. Si estaba OPEN (paso 0) + vacío -> "PENDING ITEMS UNKNOWN", no asumir ninguno.
5. SNAPSHOT: Bug/Tasks Tracker por Prioridad — detalle CRÍTICO/ALTO, conteo MEDIO/BAJO.
6. READY: "VANTAGE READY" + versión. Algún paso falló -> "BOOTSTRAP INCOMPLETE", nada después.

GUARDRAILS: Sin escrituras salvo Ledger (paso 0). Sin pasos inventados. Nunca `notion-query-data-sources`/`query_database_view` (bloqueado) — Terminal o fetch directo.