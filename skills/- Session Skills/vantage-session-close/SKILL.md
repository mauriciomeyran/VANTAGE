---
name: vantage-session-close
description: Cierre de sesión VANTAGE (Optimizado para ahorro de tokens/Tier Free).
---
VANTAGE: CLOSE PROTOCOL

0. ANNOUNCE: CLOSING SESSION...
0.5. TOKEN-GATE: Si hay alerta de tokens o instrucción "cierre rápido/comprimido", activar **MODO COMPRIMIDO** (omite pasos 3-4, activa 3'-5'). Default: **MODO COMPLETO**.
1. INVENTORY: Operador declara si hubo cambios. Si NO hubo, saltar al paso 6.
2. CENSUS: Si hubo cambios de ID, requiere output local de `generate_census.py`. Falla -> Blocked-Census.
3. CHANGELOG, TIMESTAMP & VERSION: 
   - *Completo*: Draft texto plano -> `APROBAR_WRITE`. Si el operador no brinda la fecha y hora exacta en CDMX, solicitala y colocala al principio del update.  Formato: `YYYY-MM-DD HH:MM:SS` (CDMX). Actualizar la versión de CHANGELOG con el numero asignado al update recien escrito para que el operador haga --sync
4. VERIFY & SYNC: **Gate Absoluto**. Requiere output local de `verify_versions.py --sync`. Validar `[VEREDICTO FINAL] PASS`. 
   - *Comprimido*: Si no hay output, marcar `SYNC PENDIENTE` en Ledger.
5. SUMMARY: Bloque homologado (mismas 5 secciones de handoff). 
   - *Comprimido*: Formato bullet de una línea por sección. Priorizar IDs y Pendientes.
6. LEDGER: Update Notion -> `Status: CLOSED` o `CLOSED-COMPRIMIDO`, `Closed At` [now], `Pending Summary` [bloque paso 5].
7. TERMINATE: SESSION CLOSED -> nuevo chat.