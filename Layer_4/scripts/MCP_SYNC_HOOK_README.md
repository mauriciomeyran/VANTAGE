# MCP Sync Hook — Documentación

## Propósito

Implementar el mecanismo de sincronización permanente de mirrors fundacionales tras writes MCP a Notion, según decisión S2.1 / R2-3 del VANTAGE AUDIT TRACKER.

## Documentos Fundacionales (8)

| Documento              | page_id                              | key en vsync_doc.py   |
|------------------------|--------------------------------------|-----------------------|
| Kernel                 | 377938be-fc42-805e-a408-c9ae518d4fe7 | kernel                |
| System Prompt          | 37b938be-fc42-8001-9b9b-fcf81130d274 | system_prompt         |
| Career Canon           | 377938be-fc42-8089-93f2-f52dbd2dec6c | career_canon          |
| Manual                 | 372938be-fc42-8050-9a67-e40857d7806e | manual                |
| Aliases                | 37c938be-fc42-80d4-b9ae-f5969830331b | aliases               |
| Change Log             | 390938be-fc42-80e7-b429-d7d730339353 | change_log            |
| Brief                  | 3a3938be-fc42-8008-9e90-ec435c01f50d | brief                 |
| Changelog Archivo      | 3ba938be-fc42-8011-8947-fb4fa5d1f63f | change_log_archivo    |

## Scripts

1. **trigger_sync_after_mcp_write.py**  
   - Recibe `page_id`.  
   - Si es fundacional → dispara `vsync_doc.py --direction notion --doc <key>` en **background** (no-bloqueante).  
   - Si el sync falla, solo loguea warning; no aborta el write original.

2. **mcp_sync_wrapper.sh**  
   Wrapper shell fino que invoca el script Python.

3. **notion_write_wrapper.py**  
   **Estado: Experimental / Stub.**  
   No está terminado ni es usado por ningún script del repo. Contiene la lista de los 8 documentos y la llamada al trigger, pero la lógica real de escritura a Notion está pendiente (TODO). No usar en producción hasta que se complete o se elimine.

## Limitación importante (aceptada)

El servidor MCP de Notion está configurado a nivel de sistema (`~/.config/devin/mcp_config.json`), **fuera del repo**.  
Por tanto, **no es posible interceptar automáticamente** los writes que realizan los agentes (Claude, Cursor, Devin, etc.) desde dentro de VANTAGE.

## Solución práctica vigente

Después de cualquier write MCP a un documento fundacional, invocar manualmente:

```bash
./Layer_4/scripts/mcp_sync_wrapper.sh <page_id>