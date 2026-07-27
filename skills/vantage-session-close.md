---
name: vantage-session-close
description: Close VANTAGE (Inventory -> Census -> Changelog/Version -> Verify -> Ledger).
---
VANTAGE: CLOSE PROTOCOL

0. ANNOUNCE: Declara el inicio del protocolo respondiendo: CLOSING SESSION...
1. INVENTORY: El operador declara directamente si hubo cambios en la sesión. Si el operador explícitamente indica que no hubo cambios, saltar directamente al paso 6. Claude no debe escanear el historial del chat para intentar deducir cambios.
2. CENSUS: Si el operador declaró cambios de ID, se requiere el output de `generate_census.py` ejecutado localmente. Sin este output, marcar ticket(s) como `Blocked-Census`.
3. CHANGELOG + VERSION: Generar borrador (draft) en texto plano. Esperar confirmación `APROBAR_WRITE` del operador.
4. VERIFY & SYNC: **Gate absoluto**. El operador ejecutará `python3 scripts/verify_versions.py --sync` localmente y pegará el output completo. Claude valida el string `[VEREDICTO FINAL] PASS`. Claude no avanza al paso 5 sin recibir este output de texto en la sesión actual. Prohibido hacer llamadas MCP a los 7 documentos para verificar — la verificación vive en el output del script (relectura post-escritura), no en fetch adicional. (Fusiona los antiguos pasos 4/`--check` y 4.5/`--sync` — ver Changelog v9.6.2: `--check` nunca emitía un veredicto real y quedó retirado del script.)
5. SUMMARY: Generar el bloque completo homologado con `vantage-present-handoff` (KERNEL:SESSION-LEDGER, campo `pending_summary`) — mismas 5 secciones, misma profundidad, sin recortar a un resumen de 1-2 líneas:
   - SECCION 1: Session IDs / Notion IDs necesarios para continuar sin fricción
   - SECCION 2: Pendientes de ESTA sesión (sin resolver al momento del cierre)
   - SECCION 3: Pendientes HEREDADOS (de los que se tenga registro en esta sesión)
   - SECCION 4: Última acción confirmada
   - SECCION 5: Contexto operativo mínimo para arrancar la siguiente sesión
6. LEDGER: Actualizar la fila de `Session ID` correspondiente a esta sesión en la base de datos (collection://38324240-c686-47d0-8082-cee5e4409f88) -> `Status: CLOSED`, `Closed At` [ahora], `Pending Summary` [bloque completo de 5 secciones del paso 5, sin truncar].
7. TERMINATE: Declara el cierre del protocolo respondiendo: SESSION CLOSED -> nuevo chat. No generar texto posterior.

GUARDRAILS: Toda validación de integridad es externa (operador + scripts de Python locales). Claude actúa como el validador logístico del pipeline, no como el ejecutor del escaneo de archivos.

NOTA (homologación Pending Summary ↔ Handoff): `Pending Summary` deja de ser un resumen degradado de 1-2 líneas. Debe tener la misma estructura y longitud que el output de `vantage-present-handoff`, para que la trazabilidad de deuda técnica (bugs críticos bloqueantes, tasks nice-to-have) sobreviva íntegra de una sesión a la siguiente sin importar si el cierre fue proactivo (esta skill) o reactivo (handoff en frío).
