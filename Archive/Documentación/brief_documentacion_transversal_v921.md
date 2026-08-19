# Brief para Documentación Transversal — v9.21

**Fecha:** 2026-08-14  
**Skill objetivo:** `vantage-documentacion-transversal-propuesta`  
**Tipo de solicitud:** Mapeo y desarrollo de documentación transversal

## Contexto

Se han realizado dos cambios significativos en el ecosistema VANTAGE que requieren documentación transversal formal:

1. **Creación de meta-skill `vantage-sync-assets`**: Nueva skill orquestadora que sincroniza los cuatro dominios de assets (Script Library + Script Glossary + Skill Library + Skill Glossary)
2. **Corrección de CENSUS_SPEC**: Agregación de 40 IDs huérfanos al `generate_census.py` para eliminar warnings de integridad documental

## Cambio 1: Meta-Skill `vantage-sync-assets`

### Descripción técnica

**Nombre:** `vantage-sync-assets`  
**Tipo:** Meta-skill orquestadora  
**Ubicación:** 
- `.devin/skills/vantage-sync-assets/SKILL.md`
- `skills/vantage-sync-assets.md` (documentación)
- `skills/vantage-sync-assets.skill` (empaquetado)

**Funcionalidad:**
- Orquesta la sincronización de 4 dominios de assets en orden determinista
- Reutiliza skills hijas sin duplicar lógica
- Soporta modo selectivo con flags (`--scripts-only`, `--skills-only`, etc.)
- Genera resumen consolidado de altas, correcciones y huérfanos

**Skills hijas dependientes:**
1. `vantage-sync-script-library` → SCRIPT LIBRARY (Notion)
2. `vantage-sync-skill-library` → SKILL LIBRARY (Notion)
3. `vantage-sync-script-glossary` → Script Glossary (Manual apéndice 22)
4. `vantage-sync-skill-glossary` → Skill Glossary (Manual apéndice 23)

**Contrato de entrada:**
```yaml
scope: all | scripts | skills | libraries | glossaries
force_refresh_gaps: true | false
skip_zero_gap: true
dry_run_matrix: false
```

**Convención de anuncio:**
- Apertura: `SYNCING ASSETS...`
- Cierre: `ASSETS SYNCED`

**Estado actual:**
- ✅ Creada en filesystem
- ✅ Registrada en Skill Library (Notion)
- ✅ Integrada en Manual §23.2 (Skill Glossary)
- ✅ Versionada en Changelog v9.20.5
- ✅ Sincronizada en fundacionales

## Cambio 2: Corrección de CENSUS_SPEC

### Descripción técnica

**Archivo modificado:** `Layer_1/scripts/generate_census.py`  
**Versión:** v3.0 → v3.1

**Problema resuelto:**
- El `vcensus` reportaba 40 IDs huérfanos (en docs, fuera de CENSUS_SPEC)
- Estos IDs eran principalmente encabezados de sección principales que existían en Kernel.md y Manual.md pero no estaban registrados en el spec

**IDs agregados (32 KERNEL):**
- Encabezados principales: `KERNEL:DOCUMENTATION`, `KERNEL:ARCHITECTURE`, `KERNEL:OWNERSHIP`, etc.
- Subsecciones DOCUMENTATION: `KERNEL:DOCUMENTATION-002` a `KERNEL:DOCUMENTATION-011`
- Subsecciones ARCHITECTURE: `KERNEL:ARCHITECTURE-L1`, `KERNEL:ARCHITECTURE-L2`, etc.
- Subsecciones SCHEMA: `KERNEL:SCHEMA-004` a `KERNEL:SCHEMA-007`
- Subsecciones TRACKER-SCHEMA: `KERNEL:TRACKER-SCHEMA-001`, `KERNEL:TRACKER-SCHEMA-002`
- Subsecciones FAIL-PHILOSOPHY: `KERNEL:FAIL-PHILOSOPHY-001`, `KERNEL:FAIL-PHILOSOPHY-002`
- Subsección GATE-DECISION: `KERNEL:GATE-DECISION-001`

**IDs agregados (8 MANUAL):**
- Encabezados principales: `MANUAL:OBJECTIVE`, `MANUAL:HOW-IT-WORKS`, etc.
- Subsección WEEKLY-FLOW: `MANUAL:WEEKLY-FLOW-003`

**Nuevas funcionalidades agregadas:**
- `--auto-fix-orphans`: Detección interactiva y corrección de IDs huérfanos
- `--sync-to-notion [page_id]`: Sincronización del census a página de Notion especificada

## Alcance solicitado

### Mapeo de IDs existentes

1. **Para `vantage-sync-assets`:**
   - Verificar si ya existen IDs canónicos aplicables
   - Buscar patrones similares en skills de sincronización existentes
   - Identificar si `KERNEL:DOCUMENTATION-005` (Convención de Anuncio de Skills) aplica

2. **Para corrección CENSUS_SPEC:**
   - Confirmar que los IDs agregados no colisionan con otros existentes
   - Verificar si hay alguna convención de nomenclatura para encabezados principales

### Desarrollo de documentación transversal

**Para `vantage-sync-assets`:**
- Definir IDs canónicos nuevos si no existen
- Especificar anchors para:
  - Convención de anuncio (¿reutilizar `KERNEL:DOCUMENTATION-005`?)
  - Contrato de orquestación (¿proponer `KERNEL:ORCHESTRATION-*`?)
  - Resumen consolidado de sync (¿proponer `KERNEL:ASSETS-SYNC-REPORT`?)
- Mapear la skill a la sección correcta del Manual (ya está en §23.2, confirmar)

**Para CENSUS_SPEC v3.1:**
- Documentar las nuevas funcionalidades (`--auto-fix-orphans`, `--sync-to-notion`)
- Especificar anchors para:
  - Contrato de auto-corrección de IDs (¿proponer `KERNEL:CENSUS-AUTOFIX`?)
  - Contrato de sincronización Notion (¿proponer `KERNEL:CENSUS-NOTION-SYNC`?)
- Actualizar versión en documentación relevante

### Ubicación en Manual

**Para `vantage-sync-assets`:**
- Confirmar que §23.2 (Sincronización y Mantenimiento Documental) es la ubicación correcta
- Verificar si requiere subsección propia o basta con entrada narrativa

**Para CENSUS_SPEC:**
- Determinar si las nuevas funcionalidades requieren entrada en Manual o basta con documentación en Kernel

## Deliverable esperado

1. **Mapa de IDs:** Lista de IDs existentes aplicables + propuesta de IDs nuevos con justificación
2. **Propuesta de anchors:** Estructura de `KERNEL:*` y `MANUAL:*` con contrato específico
3. **Ubicación en Manual:** Confirmación/ajuste de secciones para ambas funcionalidades
4. **Brief de implementación:** Pasos concretos para añadir los IDs a los archivos relevantes

## Preguntas para el operador

1. ¿Los encabezados principales de sección (ej. `KERNEL:DOCUMENTATION`, `MANUAL:OBJECTIVE`) deben tener IDs canónicos o son considerados ruido estructural?
2. ¿La convención de anuncio de `vantage-sync-assets` debe reutilizar `KERNEL:DOCUMENTATION-005` o crear su propio anchor?
3. ¿Las nuevas funcionalidades de `generate_census.py` (auto-fix, sync-to-notion) requieren documentación en Manual o basta con actualización de Kernel?
4. ¿El patrón de orquestación de `vantage-sync-assets` es reutilizable para futuras meta-skills? Si es así, ¿debe documentarse como patrón genérico?

## Relación con documentos existentes

**Reutiliza patrones de:**
- `vantage-sync-script-library` (schema Notion, APROBAR_WRITE, Write-Back Verification)
- `vantage-sync-skill-library` (extracción de frontmatter, protección auto-link)
- `vantage-sync-script-glossary` (shapes técnicos, diff mínimo en Manual)
- `vantage-sync-skill-glossary` (shape narrativo, clasificación temática)

**Extiende:**
- `KERNEL:DOCUMENTATION-005` (Convención de Anuncio de Skills)
- `KERNEL:DOCUMENTATION-007` (Version-Check Tool)
- `KERNEL:DOCUMENTATION-009` (Census Sync)

**Corrige:**
- Inconsistencia en CENSUS_SPEC (40 IDs huérfanos)
- Falta de herramientas de mantenimiento documental automatizadas

## Prioridad

**Alta** — Ambos cambios están en producción y requieren formalización documental para mantener integridad del sistema VANTAGE.
