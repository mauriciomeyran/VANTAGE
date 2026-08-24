# VANTAGE Serial Allocation - Arquitectura Centralizada

## Overview

Sistema centralizado de asignación de seriales VANTAGE accesible por todos los agentes (Claude, Gemini, ChatGPT, Littlebird, Mistral, Perplexity, Grok) vía HTTP API.

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENTES (Varios)                          │
│  Claude │ Gemini │ ChatGPT │ Littlebird │ Mistral │ etc.   │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP API
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          VANTAGE Serial HTTP Server (Central)              │
│          http://localhost:8787                            │
│          - POST /allocate                                  │
│          - GET /health                                     │
└────────────────────┬────────────────────────────────────────┘
                     │ SQLite
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          state/vantage_handoff_counter.sqlite3             │
│          GLOBAL_VANTAGE_COUNTER (autoridad central)         │
└─────────────────────────────────────────────────────────────┘
```

## Componentes

### 1. Servidor HTTP Central

**Archivo:** `Layer_1/scripts/vantage_serial_http_server.py`

**Propósito:** Servidor HTTP central que expone la API de asignación de seriales.

**Endpoints:**
- `POST http://localhost:8787/allocate` - Asignar siguiente serial
- `GET http://localhost:8787/health` - Obtener estado del servicio

**Contrato:**

**POST /allocate**
```json
// Response (Success)
{
  "serial": "HO-000007",
  "authority": "GLOBAL_VANTAGE_COUNTER",
  "status": "ALLOCATED"
}

// Response (Error)
{
  "error": "HANDOFF_SERIAL_UNAVAILABLE",
  "status": "UNAVAILABLE",
  "detail": "Error details"
}
```

**GET /health**
```json
{
  "status": "ok",
  "authority": "GLOBAL_VANTAGE_COUNTER",
  "current_value": 6,
  "next_serial": "HO-000007",
  "database": "/path/to/vantage_handoff_counter.sqlite3"
}
```

### 2. Puente MCP para Claude Desktop

**Archivo:** `tools/claude-desktop-mcp-extension/`

**Propósito:** Extensión MCP que conecta Claude Desktop con el servidor HTTP central.

**Instalación Claude Desktop:**
1. Copiar carpeta `claude-desktop-mcp-extension/` a:
   - macOS: `~/Library/Application Support/Claude/Claude Extensions/`
   - Linux: `~/.config/Claude/Claude Extensions/`
   - Windows: `%APPDATA%\Claude\Claude Extensions\`
2. Reiniciar Claude Desktop
3. La herramienta `allocate_vantage_serial` estará disponible

### 3. Puente MCP para Devin CLI

**Configuración:** `~/.config/devin/mcp_config.json`

**Propósito:** Conecta Devin CLI con el servidor HTTP central.

**Configuración actual:**
```json
{
  "vantage-serial": {
    "command": "python3",
    "args": [
      "/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/scripts/vantage_serial_mcp_bridge.py"
    ],
    "env": {
      "VANTAGE_SERIAL_HTTP_URL": "http://localhost:8787",
      "VANTAGE_SERIAL_TIMEOUT": "10"
    }
  }
}
```

### 4. Script de Inicio

**Archivo:** `Layer_1/scripts/start_vantage_serial_server.sh`

**Propósito:** Iniciar el servidor HTTP central en background.

**Uso:**
```bash
cd /Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/scripts
./start_vantage_serial_server.sh
```

## Configuración por Agente

### Claude (Claude Desktop)

**Método:** Extensión MCP
**Instalación:**
```bash
# Copiar extensión a Claude Extensions
cp -r tools/claude-desktop-mcp-extension \
  ~/Library/Application\ Support/Claude/Claude\ Extensions/

# Reiniciar Claude Desktop
```

**Uso:**
```python
# Claude puede invocar directamente
result = allocate_vantage_serial()
```

### Claude (Devin CLI)

**Método:** MCP Bridge
**Configuración:** Ya configurado en `~/.config/devin/mcp_config.json`

**Uso:**
```python
# Claude/Devin puede invocar vía MCP
result = allocate_vantage_serial({})
```

### Gemini

**Método:** HTTP API Directa
**Configuración:**
```python
import requests

response = requests.post(
    "http://localhost:8787/allocate",
    timeout=10
)
serial_data = response.json()
```

### ChatGPT

**Método:** HTTP API Directa (si tiene acceso HTTP)
**Configuración:**
```python
import requests

response = requests.post(
    "http://localhost:8787/allocate",
    timeout=10
)
serial_data = response.json()
```

### Littlebird

**Método:** HTTP API Directa
**Configuración:**
```python
import requests

response = requests.post(
    "http://localhost:8787/allocate",
    timeout=10
)
serial_data = response.json()
```

### Mistral

**Método:** HTTP API Directa
**Configuración:**
```python
import requests

response = requests.post(
    "http://localhost:8787/allocate",
    timeout=10
)
serial_data = response.json()
```

### Perplexity

**Método:** HTTP API Directa
**Configuración:**
```python
import requests

response = requests.post(
    "http://localhost:8787/allocate",
    timeout=10
)
serial_data = response.json()
```

### Grok

**Método:** HTTP API Directa
**Configuración:**
```python
import requests

response = requests.post(
    "http://localhost:8787/allocate",
    timeout=10
)
serial_data = response.json()
```

## Inicio del Servidor Central

### Opción 1: Manual

```bash
cd /Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/scripts
python3 vantage_serial_http_server.py
```

### Opción 2: Script de inicio

```bash
cd /Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/scripts
./start_vantage_serial_server.sh
```

### Opción 3: Automático en startup

Agregar al alias `start` o al startup del sistema:

```bash
# En start alias o script de inicio
cd /Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/scripts
./start_vantage_serial_server.sh
```

## Verificación

### Verificar servidor HTTP

```bash
# Verificar que el servidor está corriendo
curl http://localhost:8787/health

# Debería devolver:
# {"status":"ok","authority":"GLOBAL_VANTAGE_COUNTER","current_value":6,"next_serial":"HO-000007","database":"..."}
```

### Verificar asignación de serial

```bash
# Asignar un serial (consume un serial real)
curl -X POST http://localhost:8787/allocate

# Debería devolver:
# {"serial":"HO-000007","authority":"GLOBAL_VANTAGE_COUNTER","status":"ALLOCATED"}
```

### Verificar desde Python

```python
import requests

# Verificar estado
response = requests.get("http://localhost:8787/health")
print(response.json())

# Asignar serial
response = requests.post("http://localhost:8787/allocate")
print(response.json())
```

## Troubleshooting

### Servidor no inicia

- Verificar que el puerto 8787 esté disponible
- Verificar permisos en la base de datos
- Verificar que Python 3 esté instalado

### Agentes no pueden conectar

- Verificar que el servidor HTTP esté corriendo
- Verificar firewall no bloquee el puerto 8787
- Verificar URL correcta en configuración de cada agente

### Errores de timeout

- Aumentar `VANTAGE_SERIAL_TIMEOUT` en configuración
- Verificar que el servidor HTTP responda rápidamente
- Verificar conectividad de red

## Archivos

- **Servidor HTTP:** `Layer_1/scripts/vantage_serial_http_server.py`
- **Puente MCP Devin:** `Layer_1/scripts/vantage_serial_mcp_bridge.py`
- **Extensión Claude:** `tools/claude-desktop-mcp-extension/`
- **Script inicio:** `Layer_1/scripts/start_vantage_serial_server.sh`
- **Base de datos:** `state/vantage_handoff_counter.sqlite3`

## Seguridad

- El servidor HTTP actualmente escucha en `localhost:8787` (solo local)
- Para acceso remoto, cambiar `VANTAGE_SERIAL_HOST` a `0.0.0.0`
- Considerar agregar autenticación para acceso remoto
- Considerar HTTPS para producción

## Estado Actual

- **Contador:** 6
- **Próximo serial:** HO-000007
- **Servidor HTTP:** Listo para iniciar
- **Extensión Claude:** Listo para instalar
- **Configuración Devin:** Actualizada
