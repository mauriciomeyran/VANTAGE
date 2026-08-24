# VANTAGE Serial Allocation MCP Server

## Overview

Servidor MCP que expone la funcionalidad de asignación de seriales VANTAGE como una herramienta accesible para Claude/Notion MCP. Permite asignación de seriales sin acceso a Terminal ni filesystem.

## Estado de Implementación

✅ **COMPLETADO Y FUNCIONAL**

- Herramienta visible para Claude: `allocate_vantage_serial`
- Prueba real exitosa: HO-000006 asignado
- Contador incrementado: 5 → 6
- Transporte: stdio
- Reutiliza lógica existente sin duplicación

## Configuración

### Archivo de Configuración MCP

**Ubicación:** `~/.config/devin/mcp_config.json`

**Configuración:**
```json
{
  "vantage-serial": {
    "command": "python3",
    "args": [
      "/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/tools/mcp_vantage_serial_server.py"
    ],
    "env": {
      "VANTAGE_SERIAL_DB": "/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/state/vantage_handoff_counter.sqlite3"
    }
  }
}
```

### Variables de Entorno

- `VANTAGE_SERIAL_DB`: Path a la base de datos SQLite del contador global

### Comando de Arranque

```bash
python3 /Users/mauriciomeyran/Documents/03 Projects/VANTAGE/tools/mcp_vantage_serial_server.py
```

El servidor se inicia automáticamente cuando Claude carga la configuración MCP.

## Uso

### Invocación desde Claude

```python
# Claude puede invocar directamente:
result = allocate_vantage_serial({})
```

### Contrato de la Herramienta

**Input:** `{}` (objeto vacío)

**Output (Éxito):**
```json
{
  "serial": "HO-000006",
  "authority": "GLOBAL_VANTAGE_COUNTER",
  "status": "ALLOCATED"
}
```

**Output (Error):**
```json
{
  "error": "HANDOFF_SERIAL_UNAVAILABLE",
  "status": "UNAVAILABLE",
  "detail": "Error details here"
}
```

## Verificación

### Verificar Herramienta Visible

```bash
# Desde cualquier sesión Claude:
mcp_list_tools("vantage-serial")
```

**Resultado esperado:**
```json
{
  "server_name": "vantage-serial",
  "tools": [
    {
      "name": "allocate_vantage_serial",
      "description": "Allocate the next VANTAGE handoff serial number from GLOBAL_VANTAGE_COUNTER.",
      "inputSchema": {
        "properties": {},
        "type": "object"
      }
    }
  ]
}
```

### Verificar Funcionamiento

```bash
# Ejecutar test dry run (sin consumo real)
cd /Users/mauriciomeyran/Documents/03 Projects/VANTAGE/tools
python3 test_mcp_dry_run.py
```

### Verificar Contador Global

```bash
sqlite3 /Users/mauriciomeyran/Documents/03\ Projects/VANTAGE/state/vantage_handoff_counter.sqlite3 "SELECT * FROM counters;"
```

## Archivos

- **Servidor:** `tools/mcp_vantage_serial_server.py` - Implementación MCP usando FastMCP
- **Test:** `tools/test_mcp_dry_run.py` - Test sin consumo real
- **Lógica original:** `Layer_1/scripts/allocate_vantage_serial.py` - NO MODIFICADO
- **Base de datos:** `state/vantage_handoff_counter.sqlite3` - NO MODIFICADO

## Características

- ✅ Reutiliza lógica existente de `allocate_vantage_serial.py`
- ✅ SQLite transaccional con GLOBAL_VANTAGE_COUNTER
- ✅ Formato HO-XXXXXX (6 dígitos zero-padded)
- ✅ Transporte stdio (estándar MCP)
- ✅ Sin acceso a Terminal requerido
- ✅ Manejo de errores con HANDOFF_SERIAL_UNAVAILABLE
- ✅ Autoridad: GLOBAL_VANTAGE_COUNTER

## Integración con Skills

Los skills de sesión (`vantage-session-close`, `vantage-present-handoff`) ya están documentados para usar esta herramienta vía MCP como prioridad principal, con fallback a Terminal.

## Estado del Sistema

- **Contador actual:** 6
- **Próximo serial:** HO-000007
- **Base de datos:** `state/vantage_handoff_counter.sqlite3`
- **Autoridad:** GLOBAL_VANTAGE_COUNTER
- **Servidor MCP:** Funcional y visible para Claude

## Troubleshooting

### Herramienta no visible para Claude

- Verificar que `~/.config/devin/mcp_config.json` contiene la configuración
- Reiniciar Claude para recargar configuración MCP
- Verificar que el servidor MCP se inicia sin errores

### Error HANDOFF_SERIAL_UNAVAILABLE

- Verificar que la base de datos existe en el path configurado
- Verificar permisos de escritura en la base de datos
- Verificar que GLOBAL_VANTAGE_COUNTER existe en la base de datos

### Servidor no inicia

- Verificar que MCP SDK está instalado: `pip show mcp`
- Verificar Python path en configuración MCP
- Verificar que el script tiene permisos de ejecución
