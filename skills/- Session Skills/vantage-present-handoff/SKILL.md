---
name: vantage-present-handoff
description: Handoff compacto de sesión para continuidad en chat nuevo (Tier Free Optimized).
---
VANTAGE: HANDOFF PROTOCOL

0. ANNOUNCE: HANDING OFF...
1. SCOPE: Entrega directa en un solo bloque usando memoria de trabajo actual (sin MCP).
2. ESTRUCTURA (Markdown denso):
   - **S0 (TIMESTAMP9**: Si el operador no brinda la fecha y hora exacta en CDMX, solicitala y colocala al principio del Handoff. Formato: `YYYY-MM-DD HH:MM:SS` (CDMX).
   - **S1 (IDs)**: Session ID, Status Ledger (OPEN/CLOSED/COMPRIMIDO) y URLs Notion activas.
   - **S2 (Pendientes Sesión)**: Tareas abiertas y decisiones críticas sin resolución.
   - **S3 (Heredados)**: Deuda técnica o tareas arrastradas de sesiones previas.
   - **S4 (Última Acción)**: Estado verificado post-ejecución.
   - **S5 (Contexto/Tier)**: Versión VANTAGE + Alerta de sincronización pendiente (si aplica).
3. CLOSING: HANDOFF DELIVERED.