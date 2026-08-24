# Guía de Alineación de Agentes VANTAGE

## Arquitectura Centralizada

Todos los agentes ahora utilizan un **servidor HTTP central** para la asignación de seriales, garantizando consistencia y autoridad única.

```
SERVIDOR HTTP CENTRAL (localhost:8787)
         ↓
    HTTP API (POST /allocate, GET /health)
         ↓
SQLite state/vantage_handoff_counter.sqlite3
         ↓
GLOBAL_VANTAGE_COUNTER (autoridad única)
```

## Matriz de Agentes y Métodos de Conexión

| Agente | Situación Actual | Método con Autoridad Central | Implementación |
|--------|------------------|------------------------------|----------------|
| **Claude** | Puede depender de la cuenta y sus herramientas | Solicita serial directamente | **MCP Bridge** (Devin) + **Extensión MCP** (Desktop) |
| **Gemini** | Sin Terminal/filesystem | Usa API/MCP central | **HTTP API Directa** |
| **ChatGPT** | Depende de herramientas conectadas | Usa API/MCP central | **HTTP API Directa** |
| **Littlebird** | Sin runtime local | Usa API/MCP central | **HTTP API Directa** |
| **Mistral** | Puede tener acceso limitado | Usa API/MCP central | **HTTP API Directa** |
| **Perplexity** | Puede usar GitHub/Notion, pero no tu Mac | Usa API/MCP central | **HTTP API Directa** |
| **Grok** | Sin filesystem local compartido | Usa API/MCP central | **HTTP API Directa** |

## Implementación por Agente

### 1. Claude (Devin CLI)

**Estado:** ✅ Configurado

**Método:** MCP Bridge → HTTP Server

**Configuración:** `~/.config/devin/mcp_config.json`
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

**Uso:**
```python
# Claude/Devin puede invocar
result = allocate_vantage_serial({})
```

### 2. Claude (Claude Desktop)

**Estado:** ⏸️ Requiere instalación

**Método:** Extensión MCP → HTTP Server

**Instalación:**
```bash
# Copiar extensión
cp -r /Users/mauriciomeyran/Documents/03\ Projects/VANTAGE/tools/claude-desktop-mcp-extension \
  ~/Library/Application\ Support/Claude/Claude\ Extensions/

# Instalar dependencias
cd ~/Library/Application\ Support/Claude/Claude\ Extensions/claude-desktop-mcp-extension
npm install

# Reiniciar Claude Desktop
```

**Uso:**
```python
# Claude Desktop puede invocar
result = allocate_vantage_serial()
```

### 3. Gemini

**Estado:** ⏸️ Requiere implementación en código de Gemini

**Método:** HTTP API Directa

**Implementación:**
```python
import requests

def get_vantage_serial():
    try:
        response = requests.post(
            "http://localhost:8787/allocate",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "error": "HANDOFF_SERIAL_UNAVAILABLE",
            "status": "UNAVAILABLE",
            "detail": str(e)
        }

# Uso
serial_data = get_vantage_serial()
if serial_data.get("status") == "ALLOCATED":
    serial = serial_data["serial"]
```

### 4. ChatGPT

**Estado:** ⏸️ Requiere implementación en código de ChatGPT

**Método:** HTTP API Directa

**Implementación:**
```python
import requests

def get_vantage_serial():
    try:
        response = requests.post(
            "http://localhost:8787/allocate",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "error": "HANDOFF_SERIAL_UNAVAILABLE",
            "status": "UNAVAILABLE",
            "detail": str(e)
        }

# Uso
serial_data = get_vantage_serial()
if serial_data.get("status") == "ALLOCATED":
    serial = serial_data["serial"]
```

### 5. Littlebird

**Estado:** ⏸️ Requiere implementación en código de Littlebird

**Método:** HTTP API Directa

**Implementación:**
```python
import requests

def get_vantage_serial():
    try:
        response = requests.post(
            "http://localhost:8787/allocate",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "error": "HANDOFF_SERIAL_UNAVAILABLE",
            "status": "UNAVAILABLE",
            "detail": str(e)
        }

# Uso
serial_data = get_vantage_serial()
if serial_data.get("status") == "ALLOCATED":
    serial = serial_data["serial"]
```

### 6. Mistral

**Estado:** ⏸️ Requiere implementación en código de Mistral

**Método:** HTTP API Directa

**Implementación:**
```python
import requests

def get_vantage_serial():
    try:
        response = requests.post(
            "http://localhost:8787/allocate",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "error": "HANDOFF_SERIAL_UNAVAILABLE",
            "status": "UNAVAILABLE",
            "detail": str(e)
        }

# Uso
serial_data = get_vantage_serial()
if serial_data.get("status") == "ALLOCATED":
    serial = serial_data["serial"]
```

### 7. Perplexity

**Estado:** ⏸️ Requiere implementación en código de Perplexity

**Método:** HTTP API Directa

**Implementación:**
```python
import requests

def get_vantage_serial():
    try:
        response = requests.post(
            "http://localhost:8787/allocate",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "error": "HANDOFF_SERIAL_UNAVAILABLE",
            "status": "UNAVAILABLE",
            "detail": str(e)
        }

# Uso
serial_data = get_vantage_serial()
if serial_data.get("status") == "ALLOCATED":
    serial = serial_data["serial"]
```

### 8. Grok

**Estado:** ⏸️ Requiere implementación en código de Grok

**Método:** HTTP API Directa

**Implementación:**
```python
import requests

def get_vantage_serial():
    try:
        response = requests.post(
            "http://localhost:8787/allocate",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "error": "HANDOFF_SERIAL_UNAVAILABLE",
            "status": "UNAVAILABLE",
            "detail": str(e)
        }

# Uso
serial_data = get_vantage_serial()
if serial_data.get("status") == "ALLOCATED":
    serial = serial_data["serial"]
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

### Opción 3: Automático (recomendado)

Agregar al alias `start`:
```bash
# En .zshrc o script de inicio
cd /Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/scripts
./start_vantage_serial_server.sh
```

## Contrato HTTP Universal

### POST /allocate

**Request:**
```http
POST http://localhost:8787/allocate
Content-Type: application/json
{}
```

**Response (Success):**
```json
{
  "serial": "HO-000007",
  "authority": "GLOBAL_VANTAGE_COUNTER",
  "status": "ALLOCATED"
}
```

**Response (Error):**
```json
{
  "error": "HANDOFF_SERIAL_UNAVAILABLE",
  "status": "UNAVAILABLE",
  "detail": "Error details"
}
```

### GET /health

**Request:**
```http
GET http://localhost:8787/health
```

**Response:**
```json
{
  "status": "ok",
  "authority": "GLOBAL_VANTAGE_COUNTER",
  "current_value": 6,
  "next_serial": "HO-000007",
  "database": "/path/to/vantage_handoff_counter.sqlite3"
}
```

## Verificación Universal

### Desde cualquier agente con Python:

```python
import requests

# Verificar servidor
response = requests.get("http://localhost:8787/health")
print("Estado del servidor:", response.json())

# Asignar serial
response = requests.post("http://localhost:8787/allocate")
print("Serial asignado:", response.json())
```

### Desde terminal:

```bash
# Verificar servidor
curl http://localhost:8787/health

# Asignar serial
curl -X POST http://localhost:8787/allocate
```

## Actualización de Skills

### vantage-session-close

**Actualización requerida:** Reemplazar lógica de asignación de serial

**Antes:**
```python
# Obtiene serial de GLOBAL_VANTAGE_COUNTER (método local)
serial = get_local_serial()
```

**Después:**
```python
# Obtiene serial del servidor HTTP central
import requests

def get_vantage_serial():
    try:
        response = requests.post(
            "http://localhost:8787/allocate",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "ALLOCATED":
            return data["serial"]
        else:
            raise Exception(data.get("error", "Unknown error"))
    except Exception as e:
        # Fallback a método local si HTTP falla
        return get_local_serial_fallback()

serial = get_vantage_serial()
```

### vantage-present-handoff

**Actualización requerida:** Igual que vantage-session-close

## Resumen de Implementación

| Componente | Estado | Archivo |
|------------|--------|---------|
| Servidor HTTP Central | ✅ Funcional | `Layer_1/scripts/vantage_serial_http_server.py` |
| Puente MCP Devin | ✅ Configurado | `Layer_1/scripts/vantage_serial_mcp_bridge.py` |
| Extensión Claude Desktop | ⏸️ Listo para instalar | `tools/claude-desktop-mcp-extension/` |
| Script de inicio | ✅ Creado | `Layer_1/scripts/start_vantage_serial_server.sh` |
| Documentación | ✅ Completada | `tools/README_CENTRALIZED_ARCHITECTURE.md` |

## Próximos Pasos

1. **Iniciar servidor HTTP central** de forma permanente
2. **Instalar extensión Claude Desktop** si lo usas
3. **Actualizar código de agentes** (Gemini, ChatGPT, etc.) con HTTP API
4. **Actualizar skills** (vantage-session-close, vantage-present-handoff)
5. **Verificar** que todos los agentes pueden asignar seriales correctamente

## Estado Actual del Sistema

- **Contador:** 6
- **Próximo serial:** HO-000007
- **Servidor HTTP:** Listo para iniciar
- **Autoridad:** GLOBAL_VANTAGE_COUNTER (única y centralizada)
- **Base de datos:** `state/vantage_handoff_counter.sqlite3`
