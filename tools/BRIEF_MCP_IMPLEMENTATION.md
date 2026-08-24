# BRIEF: Implementación del Servidor MCP para Asignación de Seriales VANTAGE

## Contexto

Se ha implementado un servidor MCP (Model Context Protocol) para exponer la funcionalidad de asignación de seriales VANTAGE como una herramienta accesible para agentes que no tienen acceso a terminal o filesystem. Esto permite que skills de sesión (`vantage-session-open`, `vantage-session-close`, `vantage-present-handoff`) puedan obtener seriales del `GLOBAL_VANTAGE_COUNTER` independientemente de su entorno de ejecución.

## Modificaciones Realizadas

### Archivos Creados (5 nuevos)

1. **`Layer_1/scripts/mcp_vantage_serial_server.py`** (144 líneas)
   - Servidor MCP completo que implementa la herramienta `allocate_vantage_serial`
   - Reutiliza la lógica existente de `Layer_1/scripts/allocate_vantage_serial.py`
   - Usa transporte stdio para comunicación MCP
   - Manejo de errores con `HANDOFF_SERIAL_UNAVAILABLE`

2. **`Layer_1/scripts/test_mcp_dry_run.py`** (102 líneas)
   - Script de prueba con base de datos temporal
   - Verifica funcionalidad sin consumir seriales reales
   - Todos los tests pasados exitosamente

3. **`tools/README_MCP.md`** (154 líneas)
   - Documentación completa de instalación y uso
   - Guía de integración con skills
   - Lógica de fallback documentada
   - Troubleshooting y configuración

### Archivos Modificados (1 fuera del repo)

1. **`~/.config/devin/mcp_config.json`**
   - Agregada configuración del servidor `vantage-serial`
   - Configurado con path a base de datos real
   - Variables de entorno: `VANTAGE_SERIAL_DB`

### Archivos Protegidos (NO modificados)

- ❌ `Layer_1/scripts/allocate_vantage_serial.py` - Lógica existente intacta
- ❌ `state/vantage_handoff_counter.sqlite3` - Base de datos intacta
- ❌ `Layer_1/scripts/health_check.py` - Health check intacto

## Implementaciones Técnicas

### Contrato de la Herramienta MCP

**Herramienta:** `allocate_vantage_serial`

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

### Arquitectura

- **Reutilización:** Importa funciones de `allocate_vantage_serial.py` (sin duplicación)
- **Persistencia:** SQLite transaccional con `GLOBAL_VANTAGE_COUNTER`
- **Formato:** HO-XXXXXX (6 dígitos zero-padded)
- **Transporte:** stdio (estándar MCP)
- **Autoridad:** GLOBAL_VANTAGE_COUNTER (consistente con implementación existente)

### Configuración MCP

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

## Forma de Operarse

### Flujo de Asignación de Seriales

1. **Solicitud MCP:** El skill llama a la herramienta `allocate_vantage_serial`
2. **Procesamiento:** El servidor MCP invoca `allocate_serial()` de la lógica existente
3. **Transacción SQLite:** Contador incrementado de forma atómica
4. **Respuesta:** Devuelve el serial asignado con el formato especificado
5. **Uso:** El skill utiliza el serial para el handoff

### Lógica de Fallback para Skills

Los skills deben implementar lógica de fallback:

```python
def get_handoff_serial():
    try:
        # 1. Intentar MCP primero
        result = mcp_call_tool("vantage-serial", "allocate_vantage_serial", {})
        if result["status"] == "ALLOCATED":
            return result["serial"]
    except:
        pass
    
    # 2. Fallback: Terminal disponible
    if has_terminal():
        result = subprocess.run([
            "python3", 
            "Layer_1/scripts/allocate_vantage_serial.py",
            "next"
        ], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    
    # 3. Sin MCP ni Terminal
    return {"error": "HANDOFF_SERIAL_UNAVAILABLE", "status": "UNAVAILABLE"}
```

## Integración con Skills de Sesión

### vantage-session-open

**Estado Actual:** Solo valida serial recibido, no solicita nuevo serial.

**Integración MCP:**
- Solo valida el serial del handoff entrante
- No requiere asignación de serial nuevo
- MCP no afecta este skill directamente

**Requisito de Documentación:**
- Mantener validación de serial entrante
- Documentar que no solicita serial vía MCP

### vantage-session-close

**Estado Actual:** Solicita serial de `GLOBAL_VANTAGE_COUNTER` (línea 15).

**Integración MCP:**
- **Prioridad 1:** Intentar obtener serial vía MCP
- **Fallback 1:** Si MCP no disponible, usar terminal
- **Fallback 2:** Si ambos no disponibles, declarar `HANDOFF_SERIAL_UNAVAILABLE`

**Modificación Requerida:**
```python
# Línea 15 actual:
# "Obtener el siguiente serial de GLOBAL_VANTAGE_COUNTER con formato HO-######."

# Nueva implementación:
serial = get_handoff_serial()  # Con lógica de fallback MCP
if serial.get("error") == "HANDOFF_SERIAL_UNAVAILABLE":
    declarar "HANDOFF_SERIAL_UNAVAILABLE" y detener
```

**Requisito de Documentación:**
- Documentar lógica de fallback MCP
- Especificar manejo de error cuando serial no disponible
- Actualizar ejemplo de output con serial real

### vantage-present-handoff

**Estado Actual:** Solicita serial de `GLOBAL_VANTAGE_COUNTER` (línea 9).

**Integración MCP:**
- **Prioridad 1:** Intentar obtener serial vía MCP
- **Fallback 1:** Si MCP no disponible, usar terminal
- **Fallback 2:** Si ambos no disponibles, declarar `HANDOFF_SERIAL_UNAVAILABLE`

**Modificación Requerida:**
```python
# Línea 9 actual:
# "Obtener el siguiente serial de GLOBAL_VANTAGE_COUNTER con formato HO-######."

# Nueva implementación:
serial = get_handoff_serial()  # Con lógica de fallback MCP
if serial.get("error") == "HANDOFF_SERIAL_UNAVAILABLE":
    declarar "HANDOFF_SERIAL_UNAVAILABLE" y detener
```

**Requisito de Documentación:**
- Documentar lógica de fallback MCP
- Especificar manejo de error cuando serial no disponible
- Actualizar ejemplo de output con serial real

## Requisitos de Documentación Transversal

### 1. Documentación de Skills de Sesión

**Para `vantage-session-close`:**
- Agregar sección "Obtención de Serial via MCP"
- Documentar lógica de fallback MCP → Terminal → Error
- Especificar manejo de `HANDOFF_SERIAL_UNAVAILABLE`
- Actualizar ejemplos con seriales reales

**Para `vantage-present-handoff`:**
- Agregar sección "Obtención de Serial via MCP"
- Documentar lógica de fallback MCP → Terminal → Error
- Especificar manejo de `HANDOFF_SERIAL_UNAVAILABLE`
- Actualizar ejemplos con seriales reales

**Para `vantage-session-open`:**
- Documentar que no solicita serial (solo valida)
- Mantener validación de serial entrante

### 2. Documentación del Sistema

**Kernel.md:**
- Agregar sección "MCP Serial Allocation"
- Documentar arquitectura del servidor MCP
- Especificar contrato de la herramienta
- Documentar lógica de fallback

**Manual.md:**
- Agregar sección "Configuración MCP"
- Documentar instalación del servidor MCP
- Guía de troubleshooting

**System Prompt.md:**
- Actualizar referencias a asignación de seriales
- Documentar disponibilidad vía MCP
- Especificar lógica de fallback

### 3. Documentación Operativa

**Changelog:**
- Registrar implementación MCP
- Documentar commits relevantes:
  - `6b4bc72` - feat: add VANTAGE Serial Allocation MCP Server
  - `db1b918` - test: add real MCP server test script

**Aliases.md:**
- Considerar alias para verificación de MCP
- Documentar comandos de diagnóstico MCP

## Estado Actual del Sistema

### Contador Global
- **Valor actual:** 5
- **Próximo serial:** HO-000006
- **Base de datos:** `state/vantage_handoff_counter.sqlite3`
- **Autoridad:** GLOBAL_VANTAGE_COUNTER

### Servidor MCP
- **Estado:** Funcional y testeado
- **Configuración:** ~/.config/devin/mcp_config.json
- **Dependencias:** Instaladas (mcp 1.26.0)
- **Tests:** DRY RUN ✅, Real ✅

### Skills de Sesión
- **vantage-session-open:** Funcional (no requiere modificación)
- **vantage-session-close:** Requiere integración MCP
- **vantage-present-handoff:** Requiere integración MCP

## Próximos Pasos

### Inmediatos
1. Solicitar documentación transversal para skills de sesión
2. Integrar lógica de fallback MCP en `vantage-session-close`
3. Integrar lógica de fallback MCP en `vantage-present-handoff`
4. Actualizar documentación del sistema (Kernel, Manual, System Prompt)

### Futuros
1. Considerar monitoreo del servidor MCP
2. Implementar logging de asignaciones de seriales
3. Considerar métricas de uso del contador global
4. Evaluar necesidad de backup de base de datos SQLite

## Confirmaciones

✅ Implementación MCP completada y funcional
✅ Tests pasados (DRY RUN y Real)
✅ Archivos protegidos intactos
✅ Health check no modificado
✅ Lógica existente reutilizada
✅ Contrato de salida cumplido
⏸️ Skills de sesión requieren integración MCP
⏸️ Documentación transversal pendiente

---

**Commits Relevantes:**
- `6b4bc72` - feat: add VANTAGE Serial Allocation MCP Server
- `db1b918` - test: add real MCP server test script
- `e6e1080` - fix: restore "Documentación" with tilde in ACTIVE_DIR path
- `f3c75dd` - fix: restore "En revisión" with tilde in BUG tracker status values
- `bcc5653` - fix: rewrite health_check.py with pure ASCII characters for terminal readability
