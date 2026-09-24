# MCP Sync Hook — Documentación

## Propósito

Implementar el mecanismo de sincronización permanente de mirrors fundacionales tras writes MCP a Notion, según contrato HO-000062 (R2-3).

## Requisito Original

> "Disparar vsync_doc.py --direction notion (unidireccional Notion→local ÚNICAMENTE) tras cualquier write exitoso vía MCP a uno de los 6 documentos fundacionales (Kernel, System Prompt, Career Canon, Manual, Aliases, Change Log)."

## Documentos Fundacionales (6)

| Documento | page_id | key en vsync_doc.py |
|-----------|---------|---------------------|
| Kernel | 377938be-fc42-805e-a408-c9ae518d4fe7 | kernel |
| System Prompt | 37b938be-fc42-8001-9b9b-fcf81130d274 | system_prompt |
| Career Canon | 377938be-fc42-8089-93f2-f52dbd2dec6c | career_canon |
| Manual | 372938be-fc42-8050-9a67-e40857d7806e | manual |
| Aliases | 37c938be-fc42-80d4-b9ae-f5969830331b | aliases |
| Change Log | 390938be-fc42-80e7-b429-d7d730339353 | change_log |

## Implementación

### Scripts Creados

1. **trigger_sync_after_mcp_write.py** - Script Python que:
   - Recibe un page_id como argumento
   - Verifica si corresponde a un documento fundacional
   - Si es fundacional, ejecuta `vsync_doc.py --direction notion --doc <key>`

2. **mcp_sync_wrapper.sh** - Wrapper shell para invocar el script Python

### Limitación Importante

El servidor MCP de Notion está configurado a nivel de sistema en `~/.config/devin/mcp_config.json` (fuera del repo VANTAGE). Por lo tanto, **no es posible agregar un hook automático post-write directamente en el servidor MCP desde dentro del repo**.

### Solución Práctica

El mecanismo implementado requiere **invocación manual** después de un write MCP:

```bash
# Después de realizar un write MCP a un documento fundacional:
cd ~/Documents/03\ Projects/VANTAGE
./Layer_4/scripts/mcp_sync_wrapper.sh <page_id>

# Ejemplo:
./Layer_4/scripts/mcp_sync_wrapper.sh 377938be-fc42-805e-a408-c9ae518d4fe7
```

### Integración Futura (Si se requiere automatización completa)

Para lograr automatización completa (hook post-write automático), se requeriría:

1. Modificar la configuración MCP a nivel de sistema (`~/.config/devin/mcp_config.json`)
2. Implementar un middleware proxy que intercepte llamadas MCP
3. O esperar a que el servidor MCP soporte hooks post-write nativos

Esta implementación está fuera del alcance del contrato actual, ya que requiere modificar configuración del sistema operativo del operador, no solo el repo VANTAGE.

## Sync Manual Inicial (Completado)

Los 6 documentos fundacionales fueron sincronizados manualmente una vez el 2026-09-22:

- ✅ Kernel (763 bloques)
- ✅ System Prompt (151 bloques)
- ✅ Career Canon (308 bloques)
- ✅ Manual (912 bloques)
- ✅ Aliases (29 bloques)
- ✅ Change Log (43 bloques)

## Uso Recomendado

1. **Workflow actual**: Después de cualquier write MCP a Notion que modifique un documento fundacional, ejecutar el wrapper manualmente con el page_id correspondiente.

2. **Alternativa**: El operador puede seguir usando los horarios fijos de vgit/vdoc (09:00/15:00/21:00) para sync automático, y usar este wrapper solo cuando necesite sync inmediato fuera de esas ventanas.

## Contrato de Sesión

Referencia: HO-000062, item R2-3
Fecha de implementación: 2026-09-22
