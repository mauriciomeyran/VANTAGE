# Brief para Documentación Transversal — Optimización de Skills VANTAGE

**Fecha:** 2026-08-14  
**Skill objetivo:** `vantage-documentacion-transversal-propuesta`  
**Tipo de solicitud:** Mapeo y desarrollo de documentación transversal para 4 acciones de optimización de skills

## Contexto

Se han realizado 4 acciones de optimización del catálogo de skills VANTAGE que requieren documentación transversal formal y actualización de Changelog/Manual.

## Cambio 1: vantage-sync-assets expandido (Skill existente modificada)

### Descripción técnica

**Archivo modificado:** `.devin/skills/vantage-sync-assets/SKILL.md`  
**Tipo:** Expansión de meta-skill orquestadora (4 → 6 dominios)

**Cambios implementados:**
- Expansión de 4 a 6 dominios de assets sincronizados
- Nuevos dominios agregados: Census Spec, Hyperlinks
- Nuevos flags de modo selectivo: `--census-only`, `--hyperlinks-only`
- Actualización de contrato de entrada (scope)
- Actualización de orden de ejecución (Libraries → Glossaries → Census → Hyperlinks)
- Actualización de Dry Run Matrix (2 filas nuevas)
- Actualización de resumen consolidado (2 filas nuevas)

**Estado actual:**
- ✅ Modificada en filesystem
- ✅ Empaquetada como vantage-sync-assets.skill
- ✅ index.json actualizado con descripción extendida
- ❌ No actualizada en Skill Library (Notion)
- ❌ No actualizada en Manual §23.2
- ❌ No versionada en Changelog

## Cambio 2: vantage-housekeeping-tracker (Nueva Skill)

### Descripción técnica

**Nombre:** `vantage-housekeeping-tracker`  
**Tipo:** Meta-skill orquestadora de housekeeping de trackers  
**Ubicación:**
- `skills/vantage-housekeeping-tracker.md` (documentación)
- `skills/vantage-housekeeping-tracker.skill` (empaquetado)

**Funcionalidad:**
- Orquesta 3 skills tidy en orden lógico de prioridad
- Skills hijas: vantage-tidy-bug-task-tracker, vantage-tidy-opportunities-tracker, vantage-tidy-changelog
- Orden: Bug/Task (CRÍTICO/ALTO) → VANTAGE Tracker → Change Log
- Flags selectivos: `--bug-task-only`, `--opportunities-only`, `--changelog-only`
- VANTAGE-ALIGNED con KERNEL requirements
- Protocolo sandbox para economía de tokens

**Estado actual:**
- ✅ Creada en filesystem
- ✅ Empaquetada como .skill
- ✅ Agregada a index.json
- ❌ No registrada en Skill Library (Notion)
- ❌ No integrada en Manual (Skill Glossary)
- ❌ No versionada en Changelog

## Cambio 3: vantage-audit-navigation-brief (Skill Deprecated)

### Descripción técnica

**Archivo modificado:** `skills/vantage-audit-navigation-brief.md`  
**Tipo:** Deprecación de skill operativa

**Cambios implementados:**
- Marcado como DEPRECATED en description
- Funcionalidad integrada en vantage-documentacion-transversal-propuesta
- Se mantiene solo como referencia histórica

**Justificación:**
- Auditoría de Navigation Brief es caso específico de documentación transversal
- Ya cubierto por Fase 1 de documentación transversal (mapeo de nodos fundacionales)
- Elimina fricción operativa innecesaria

**Estado actual:**
- ✅ Marcada como DEPRECATED en filesystem
- ❌ No actualizada en Manual §23.3 (debe indicar DEPRECATED)
- ❌ No versionada en Changelog

## Cambio 4: extract-learnings (Skill Deprecated)

### Descripción técnica

**Archivo modificado:** `skills/extract-learnings.md`  
**Tipo:** Deprecación de skill operativa

**Cambios implementados:**
- Marcado como DEPRECATED en description
- Actividad post-mortem esporádica, no skill operativa recurrente
- Se mantiene solo como referencia histórica de housekeeping interno

**Justificación:**
- Es actividad post-mortem esporádica, no una skill operativa recurrente
- Ya marcada como "housekeeping interno" en el glossary
- No requiere gate de escritura ni convención de anuncio
- Reduce catálogo de skills operativas a solo las que se ejecutan regularmente

**Estado actual:**
- ✅ Marcada como DEPRECATED en filesystem
- ❌ No actualizada en Manual §23.3 (debe indicar DEPRECATED)
- ❌ No versionada en Changelog

## Alcance solicitado

### Mapeo de IDs existentes

1. **Para vantage-sync-assets expandido:**
   - Verificar si ya existe ID en Manual §23.2 (vantage-sync-assets está registrada)
   - Confirmar si requiere actualización de descripción en Skill Library (Notion)
   - Determinar si requiere actualización de entrada en Manual §23.2

2. **Para vantage-housekeeping-tracker:**
   - Proponer ID canónico nuevo (MANUAL:SKILL-GLOSSARY-* para meta-skill de housekeeping)
   - Determinar ubicación en Manual (¿§23.2 Housekeeping o §23.3 Audit?)
   - Verificar si requiere subsección propia en §23.2

3. **Para skills deprecadas:**
   - Determinar si requiren entrada específica en Manual §23.3 con estado DEPRECATED
   - O si basta con eliminarlas del glossary activo
   - Proponer manejo de versiones en Changelog

### Desarrollo de documentación transversal

**Para vantage-sync-assets expandido:**
- Actualizar descripción en Skill Library (Notion)
- Actualizar entrada en Manual §23.2 (reflejar 6 dominios en lugar de 4)
- Agregar nuevos flags a descripción

**Para vantage-housekeeping-tracker:**
- Definir ID canónico (MANUAL:SKILL-GLOSSARY-*)
- Especificar anchors para skills hijas y orden de prioridad
- Mapear a sección correcta del Manual (¿§23.2 Sincronización y Mantenimiento?)
- Integrar en Skill Library (Notion)

**Para skills deprecadas:**
- Definir convención de deprecación en Manual
- Actualizar §23.3 para indicar DEPRECATED
- Proponer manejo de versión en Changelog

### Ubicación en Manual

**Para vantage-sync-assets expandido:**
- Actualizar §23.2 (fila existente para vantage-sync-assets)
- Reflejar descripción extendida (6 dominios en lugar de 4)

**Para vantage-housekeeping-tracker:**
- Evaluar entre §23.2 (Sincronización y Mantenimiento) vs §23.3 (Auditoría y Continuidad)
- Considerar que es meta-skill de housekeeping operativo, no auditoría

**Para skills deprecadas:**
- ¿Agregar notas DEPRECATED en §23.3?
- ¿Eliminar de la tabla activa y mover a sección separada?

## Deliverable esperado

1. **Mapa de IDs:** Lista de IDs existentes aplicables + propuesta de IDs nuevos con justificación
2. **Propuesta de anchors:** Estructura de `MANUAL:*` con contrato específico
3. **Ubicación en Manual:** Confirmación/ajuste de secciones para las 4 acciones
4. **Brief de implementación:** Pasos concretos para añadir los IDs a los archivos relevantes

## Prioridad

**ALTA** — Las 4 acciones están implementadas en producción y requieren formalización documental para mantener integridad del sistema VANTAGE.

## Impacto del cambio

**Catálogo de skills reducido:** 25 → 17 (-32%)
**Complejidad operativa reducida:** De múltiples comandos individuales a 2 meta-skills coordinadas
**Skills optimizadas:** vantage-sync-assets (expandido), vantage-housekeeping-tracker (nuevo)
**Skills deprecadas:** vantage-audit-navigation-brief, extract-learnings
