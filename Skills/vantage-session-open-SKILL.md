---
name: vantage-session-open
description: Abre/inicializa una sesión de VANTAGE siguiendo el protocolo formal de arranque (Ledger -> Health Check SP/Census -> Version Check -> Changelog -> Pending -> Snapshot -> Ready). Usa esta skill siempre que el operador indique que empieza una nueva sesión de VANTAGE, diga "abrir sesión", "open session", "arrancamos VANTAGE", "VANTAGE OPEN", "bootstrap", o pida el status/contexto inicial del sistema al inicio del chat. No la actives para operaciones dentro de una sesión ya abierta (CV, SYNC, escrituras) — solo para el arranque formal.
---
VANTAGE: OPEN PROTOCOL

**Regla Estricta (fuente: `verify_versions.py`, MANUAL:SESSION-CYCLE-001 §Apertura)**: Terminal es requisito obligatorio, no ruta preferente. Claude NO realiza fetch ni query MCP directo a Session Ledger, System Prompt, ID Census ni ningún documento fundacional para resolver este protocolo. Toda la información de arranque llega exclusivamente vía los dos outputs de terminal que el operador pega en el chat.

1. BOOTSTRAP: El operador ejecuta localmente `python3 scripts/verify_versions.py --bootstrap` y pega el bloque `[DUMP INICIO SESIÓN VANTAGE]` completo. Este dump contiene: última fila del Session Ledger (session_id, status, opened_at, pending_summary — con advertencia si status quedó `OPEN` por cierre abrupto), versión vigente del Changelog, y snapshot de tickets CRÍTICO/ALTO del Bug/Task Tracker.
2. CHECK: El operador ejecuta localmente `python3 scripts/verify_versions.py --check` y pega la tabla de 7 documentos (Changelog, Kernel, Manual, Canon, SP, Aliases, Census) con su versión. Si algún output (bootstrap o check) falta o está incompleto, Claude se detiene y lo solicita — no improvisa el faltante ni lo reconstruye vía MCP.
3. WRITE: Con ambos payloads en mano, Claude realiza una única escritura: crea la fila nueva en Session Ledger con `status: OPEN`, `session_id` generado por Claude y `opened_at` = ahora. Esta escritura es housekeeping de infraestructura de sesión — no requiere `APROBAR_WRITE`.
4. VALIDATE: Si la tabla del `--check` muestra versión consistente en los 7 documentos → continuar. Si hay drift → reportarlo explícitamente antes de continuar (no bloquea salvo que el documento desincronizado sea el que se va a editar en esta sesión).
5. PENDING: Reportar el `pending_summary` leído del dump de `--bootstrap` (paso 1) — sin queries adicionales.
6. READY: Si status = "PASS" limpio, responder únicamente "VANTAGE: SISTEMA SINCRONIZADO" + versión detectada. Si el status del Ledger anterior quedó `OPEN` (posible cierre abrupto), señalarlo antes del READY.

GUARDRAILS: Cero recursividad. Claude no busca consistencia de archivos leyendo bases de datos completas ni fetch individual de fundacionales; valida basándose exclusivamente en los dos outputs de terminal provistos por el operador.