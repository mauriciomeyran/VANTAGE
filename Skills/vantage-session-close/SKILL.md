---
name: vantage-session-close
description: Close VANTAGE (Inventory -> Census -> Changelog/Version -> Verify -> Ledger -> Handoff).
---
VANTAGE: CLOSE PROTOCOL

1. INVENTORY: Writes / cambios de ticket / cambios de estado de ID esta sesión. Nada cambió -> saltar a 6.
2. CENSUS: Algún ID cambió estado -> regenerar (Terminal `generate_census.py`) ANTES del Changelog, orden estricto. Sin Terminal -> marcar ticket(s) `Blocked-Census`, decirlo explícitamente.
3. CHANGELOG + VERSION: Draft entry (DRY RUN, antes/después) -> esperar `APROBAR_WRITE`. El bump actualiza `Versión` del CHANGE LOG en la misma escritura — referencia única. Confirmar patch vs minor si no es obvio.
4. VERIFY: Operador corre `python3 scripts/verify_versions.py --check`, pega output. Expect `PASS — all components at v[nueva]`. Mismatch -> "FAIL — WRITE-BACK MISMATCH", STOP.
   - Sin Terminal -> fallback: re-fetch de los 6 fundacionales, solo lectura, comparar.
5. SUMMARY:
COMPLETADO ESTA SESIÓN: [...]
PENDIENTE: [item — por qué]
6. LEDGER: Fila de `Session ID` actual (collection://8d736032-eef9-4e6e-a05a-df8b8079ebff) -> `Status: CLOSED`, `Closed At` [ahora], `Pending Summary`: [texto paso 5].
7. TERMINATE: "SESIÓN COMPLETADA -> nuevo chat." Nada después.

GUARDRAILS: Census siempre antes que Changelog. Todo Changelog trae bump. No cerrar ticket con ID-change sin Census — Blocked-Census. No cerrar fila de Ledger ajena al session_id actual. `verify_versions.py --sync` escribe el nuevo baseline a VERSION MANIFEST (collection://02331706-d2f5-43d1-8166-ed53b690dbd7) directo, sin registro previo de page_ids — correrlo tras `--check` en verde.