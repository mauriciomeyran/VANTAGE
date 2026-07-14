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
4.5 SYNC MANIFEST (obligatorio, no opcional): Inmediatamente después de que el paso 4 dé `PASS`, operador corre `python3 scripts/verify_versions.py --sync` y **pega el output**. Expect algo como `SYNCED — manifest updated to v[nueva]`. Este paso es el único que escribe el nuevo baseline a VERSION MANIFEST — sin él, el próximo `--check` seguirá comparando contra la versión anterior aunque CHANGE LOG ya haya avanzado. No saltar este paso aunque el `--check` haya dado PASS: PASS en el paso 4 confirma que los documentos coinciden entre sí, no que el manifest quedó actualizado.
- **Gate**: sin output de `--sync` pegado en esta sesión de cierre, NO avanzar al paso 5/6 — permanecer en 4.5 y solicitarlo explícitamente.
- No asumir que `--sync` corrió solo porque el operador dice "ya está" o "ya lo corrí antes" — exigir el output como evidencia en esta sesión, igual que en el paso 4. Una corrida en una sesión anterior no cuenta para el cierre actual.
5. SUMMARY:
COMPLETADO ESTA SESIÓN: [...]
PENDIENTE: [item — por qué]
6. LEDGER: Fila de `Session ID` actual (collection://8d736032-eef9-4e6e-a05a-df8b8079ebff) -> `Status: CLOSED`, `Closed At` [ahora], `Pending Summary`: [texto paso 5].
7. TERMINATE: "SESIÓN COMPLETADA -> nuevo chat." Nada después.

GUARDRAILS: Census siempre antes que Changelog. Todo Changelog trae bump. No cerrar ticket con ID-change sin Census — Blocked-Census. No cerrar fila de Ledger ajena al session_id actual. Paso 4.5 (`--sync`) es obligatorio en todo cierre con bump de versión — su omisión es la causa raíz conocida de manifest desactualizado (ver incidente 2026-07-14: CHANGE LOG en 9.2.9, manifest congelado en 9.2.8 por --sync nunca ejecutado en el cierre previo). No cerrar fila de Ledger (paso 6) sin output de `--sync` confirmado en el paso 4.5 de esta misma sesión de cierre — "obligatorio" en 4.5 es un gate verificable, no una nota informativa.