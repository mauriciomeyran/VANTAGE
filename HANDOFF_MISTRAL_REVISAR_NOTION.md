# HANDOFF — Revisión de Referencias en Notion (Cambio de Carpeta Documentación)

**Fecha:** 2026-07-05  
**Asignado a:** Mistral (Claude/MCP)  
**Contexto:** Carpeta "- Documentación" renombrada a "Documentación"  
**Objetivo:** Revisar y actualizar referencias al nombre antiguo en páginas de Notion

---

## Contexto del Cambio

**Cambio realizado:**
- Carpeta: `- Documentación` → `Documentación`
- Scripts fixeados: health_check.py, vsync_doc.py
- Documentación actualizada: SETUP.md
- Estado: Completado y validado

**Referencias ya identificadas en código Python:**
- ✅ health_check.py — Fixeado (path relativo)
- ✅ vsync_doc.py — Fixeado (path relativo)
- ✅ SETUP.md — Actualizado

---

## Tarea: Revisar Referencias en Notion

### Páginas de Notion a Revisar

**Páginas fundacionales (más probables de tener referencias):**
1. **System Prompt** (ID: 37b938be-fc42-8001-9b9b-fcf81130d274)
2. **Manual** (ID: 372938be-fc42-8050-9a67-e40857d7806e)
3. **Kernel** (ID: 377938be-fc42-805e-a408-c9ae518d4fe7)
4. **Career Canon** (ID: 377938be-fc42-8089-93f2-f52dbd2dec6c)
5. **Change Log** (ID: 390938be-fc42-80e7-b429-d7d730339353)
6. **Aliases** (ID: 37c938be-fc42-80d4-b9ae-f5969830331b)

### Patrones de Búsqueda

**Buscar en cada página:**
- `- Documentación` (con guión y espacio)
- `- Documentación` (con guión y tilde Unicode)
- `/Users/mauriciomeyran/Documents/04-Vantage_CV/- Documentación`
- Cualquier path absoluto que contenga "- Documentación"

### Acción si se encuentra referencia

**Si es referencia histórica (ej: en Change Log):**
- ❌ NO modificar (es historia)
- ✅ Dejar como está

**Si es referencia operativa (ej: en System Prompt, Manual, Kernel):**
- ✅ Actualizar a "Documentación" (sin guión)
- ✅ Si es path absoluto, considerar cambiar a relativo

**Si es duda:**
- ⚠️ Anotar en findings para revisión manual

---

## Método de Revisión

### Paso 1: Acceder a cada página de Notion
Usar MCP Notion server para leer cada página por ID

### Paso 2: Buscar patrones
Buscar strings específicos en el contenido de cada página

### Paso 3: Clasificar findings
- **Histórico:** Change Log, reportes, validation reports → NO modificar
- **Operativo:** System Prompt, Manual, Kernel, Career Canon → SÍ modificar
- **Dudoso:** Anotar para revisión manual

### Paso 4: Actualizar si aplica
Para cada referencia operativa encontrada:
- Reemplazar `- Documentación` → `Documentación`
- Reemplazar paths absolutos → paths relativos si aplica

### Paso 5: Reportar findings
Crear reporte con:
- Páginas revisadas
- Referencias encontradas
- Acciones tomadas
- Referencias no modificadas (con justificación)

---

## Formato de Reporte Esperado

```markdown
# Reporte: Revisión de Referencias en Notion

## Páginas Revisadas
- [x] System Prompt (37b938be-fc42-8001-9b9b-fcf81130d274)
- [x] Manual (372938be-fc42-8050-9a67-e40857d7806e)
- [x] Kernel (377938be-fc42-805e-a408-c9ae518d4fe7)
- [x] Career Canon (377938be-fc42-8089-93f2-f52dbd2dec6c)
- [x] Change Log (390938be-fc42-80e7-b429-d7d730339353)
- [x] Aliases (37c938be-fc42-80d4-b9ae-f5969830331b)

## Referencias Encontradas

### System Prompt
- [x] Referencia 1: "path en línea X" → ACCIÓN: Actualizado / NO MODIFICADO (histórico)

### Manual
- [x] Referencia 1: "path en línea Y" → ACCIÓN: Actualizado / NO MODIFICADO (histórico)

## Resumen
- Páginas revisadas: 6
- Referencias encontradas: N
- Referencias actualizadas: N
- Referencias no modificadas: N (históricas)
```

---

## Notas Importantes

1. **Prioridad:** Baja — Referencias en Notion no rompen código, solo desactualizan documentación
2. **Riesgo:** Bajo — Si algo se rompe, es fácil revertir
3. **Conservar historia:** NO modificar Change Log ni reportes históricos
4. **Paths absolutos:** Si se encuentran, evaluar si pueden ser relativos

---

## Herramientas Disponibles

- **MCP Notion server:** Configurado en `.vscode/mcp.json`
- **Acceso directo:** IDs de todas las páginas listados arriba
- **Buscador:** Usar búsqueda de texto en cada página

---

## Tiempo Estimado

- 10-15 minutos por página
- Total: 60-90 minutos

---

## Definición de Terminado

- [ ] Todas las 6 páginas revisadas
- [ ] Referencias operativas actualizadas
- [ ] Referencias históricas identificadas y no modificadas
- [ ] Reporte generado
- [ ] Cambios verificados en Notion

---

**FIN DEL HANDOFF**
