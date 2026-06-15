# 📅 VANTAGE v7.5 — Rutina Operativa

## RUTINA SEMANAL ESTÁNDAR

### 🗓️ LUNES 9:00-9:30 AM (Rutina Principal)

**Paso 1: Pipeline de limpieza**
```bash
vantagep
```
*Propósito: Limpiar estado actual antes de agregar nuevas*

**Paso 2: Status check**
```
Claude chat nuevo → "STATUS"
```
*Revisar aplicaciones pendientes y NADs vencidas*

**Paso 3: Búsqueda semanal**
```
Claude → "SEARCH-WEEK"
```
*Copiar prompt generado por Claude*

**Paso 4: Discovery execution**
```
Perplexity → pegar prompt → copiar JSON resultado
```

**Paso 5: Feed processing**
```
Claude → "Hay un Feed nuevo, procésalo"
[pegar JSON de Perplexity]
```
*Seguir DRY RUN → APROBAR_WRITE*

**Paso 6: Pipeline final**
```bash
vantagep
```
*URL Gate + Fuente + Scoring v6.4 (backfill Score/Fuente vacíos)*

**Paso 7: Review activo**
```
Notion → Vista "Pipeline Activo" 
```
*Planificar aplicaciones de la semana*

### 🗓️ 1º y 3º LUNES (Búsqueda Ejecutiva)

**Agregar después del Paso 5:**
```
Claude → "SEARCH-EXEC"
Perplexity → ejecutar prompt ejecutivo
Claude → procesar segundo JSON
APROBAR_WRITE
```
*Luego continuar con Paso 6-7 normal*

### 🗓️ MIÉRCOLES (Check Opcional - 15 min)

```bash
# Solo si tienes tiempo
vantagep
```
```
Notion → Vista "Blocked" → resolver URLs fáciles
```

### 🗓️ EXCEPCIONES

**Lunes festivo:** Mover rutina completa al **martes mismo horario**  
**Perplexity down:** Ejecutar rutina sin discovery, solo pipeline + STATUS  
**Claude limitado:** Usar rutina manual mínima (solo pipeline)

## RUTINA MANUAL MÍNIMA (Backup)

Si Claude no está disponible:
```bash
1. vantagep
2. Notion → Pipeline Activo → aplicar
3. Manual search en LinkedIn/portales
4. Agregar entradas manual en Notion
5. vantagep
```

## MÉTRICAS DE ÉXITO RUTINA

**Semanal:**
- [ ] Rutina completada en <30 min
- [ ] 5-15 nuevas oportunidades descubiertas
- [ ] Pipeline Activo mantiene 3-8 entradas
- [ ] 0 NADs vencidas acumulándose

**Mensual:**
- [ ] >80% de rutinas ejecutadas
- [ ] Calidad discovery constante
- [ ] Tiempo rutina no aumenta
- [ ] Sistema sigue siendo útil, no tedioso

---
*LAYER_1 path: ~/Documents/04-VANTAGE_CV/LAYER_1/*  
*Alias: `vantagep` → ~/vantage_pipeline.sh → wrappers/layer_1_wrapper.sh*
