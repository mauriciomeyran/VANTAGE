---
name: vantage-session-open
description: Bootstrap VANTAGE (Ledger -> Context).
---
VANTAGE: OPEN PROTOCOL

0. ANNOUNCE: SESSION-OPENING...
1. LEDGER: SQL directo vía MCP está bloqueado en este plan (query_data_sources no 
   disponible en este workspace). Usar en su lugar:
   - notion-search sobre el data source del Ledger (collection://38324240-c686-47d0-8082-cee5e4409f88)
   - notion-fetch de la fila más reciente devuelta
   Si Status = OPEN o duplicados -> Reportar WARN. Crear fila nueva (Status: OPEN).
2. HEALTH: Verificar System Prompt + ID Census vía MCP (ya cubierto por el Bootstrap 
   universal, KERNEL:DOCUMENTATION-004).
3. PENDING: Leer campo `Pending Summary` de la fila anterior. Si es `CLOSED-COMPRIMIDO`, 
   priorizar resolución de deuda técnica.
4. SNAPSHOT: Operador pega dump de `--bootstrap`. Si vacío -> "SNAPSHOT: 0 TAREAS 
   CRÍTICAS". Terminal ya no es requisito bloqueante para abrir sesión.
5. READY: SESSION-OPENED: VANTAGE READY (Version/Tier Mode).