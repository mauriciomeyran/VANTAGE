# Brief para Documentación Transversal — Skills VANTAGE

**Fecha:** 2026-08-14  
**Skill objetivo:** `vantage-documentacion-transversal-propuesta`  
**Tipo de solicitud:** Mapeo y desarrollo de documentación transversal para 4 skills VANTAGE

## Contexto

Se han realizado modificaciones significativas en 4 skills del sistema VANTAGE que requieren documentación transversal formal y actualización de Changelog:

1. **vantage-sync-assets** — Nueva meta-skill orquestadora (creada)
2. **vantage-documentacion-transversal-propuesta** — Skill de propuesta mejorada (actualizada)
3. **vantage-documentacion-transversal-implementacion** — Skill de implementación mejorada (actualizada)
4. **vantage-skill-updater** — Nueva skill de evaluación de compliance (creada)

## Cambio 1: vantage-sync-assets (Nueva Skill)

### Descripción técnica

**Nombre:** `vantage-sync-assets`  
**Tipo:** Meta-skill orquestadora  
**Ubicación:** 
- `.devin/skills/vantage-sync-assets/SKILL.md`
- `skills/vantage-sync-assets.md` (documentación)
- `skills/vantage-sync-assets.skill` (empaquetado)

**Funcionalidad:**
- Orquesta sincronización de 4 dominios de assets (Script Library + Script Glossary + Skill Library + Skill Glossary)
- Reutiliza skills hijas sin duplicar lógica
- Soporta modo selectivo con flags
- Genera resumen consolidado de altas, correcciones y huérfanos

**Skills hijas dependientes:**
1. `vantage-sync-script-library` → SCRIPT LIBRARY (Notion)
2. `vantage-sync-skill-library` → SKILL LIBRARY (Notion)
3. `vantage-sync-script-glossary` → Script Glossary (Manual apéndice 22)
4. `vantage-sync-skill-glossary` → Skill Glossary (Manual apéndice 23)

**Estado actual:**
- ✅ Creada en filesystem
- ✅ Registrada en Skill Library (Notion)
- ✅ Integrada en Manual §23.2 (Skill Glossary)
- ✅ Versionada en Changelog v9.20.5
- ✅ Sincronizada en fundacionales

## Cambio 2: vantage-documentacion-transversal-propuesta (Skill Mejorada)

### Descripción técnica

**Archivo modificado:** `skills/vantage-documentacion-transversal-propuesta.md`  
**Tipo:** Mejora de rigor de mapeo de nodos

**Mejoras implementadas:**
- Integración de KERNEL:DOCUMENTATION-010 (Protocolo 6 fases)
- Integración de KERNEL:DOCUMENTATION-005 (Convención de Anuncio)
- Integración de KERNEL:DOCUMENTATION-012 (Cero Inferencia Silenciosa)
- Protocolo sandbox para economía de tokens máxima
- 8 nuevos pasos de validación (1.5, 2.5, 3.5, 3.6, 4.5, 4.6)
- Criterios explícitos para "susceptibles de actualización"
- Criterios para nuevo ID vs reutilización
- Checklist de validación pre-propuesta

**Problema resuelto:**
- Reducir riesgo de nodos omitidos en propuestas de documentación transversal
- Maximizar economía de tokens (solo 3 outputs visibles)
- Alinear con lineamientos activos del sistema VANTAGE

## Cambio 3: vantage-documentacion-transversal-implementacion (Skill Mejorada)

### Descripción técnica

**Archivo modificado:** `skills/vantage-documentacion-transversal-implementacion.md`  
**Tipo:** Mejora de rigor de implementación

**Mejoras implementadas:**
- Integración de KERNEL:DOCUMENTATION-010 (Protocolo 6 fases)
- Integración de KERNEL:DOCUMENTATION-005 (Convención de Anuncio)
- Integración de KERNEL:DOCUMENTATION-012 (Cero Inferencia Silenciosa)
- Protocolo sandbox para economía de tokens máxima
- Todas las fases de escritura marcadas como sandbox interno
- Write-Back Verification como proceso silencioso
- Validación de Census como proceso silencioso
- Checklist pre-cierre mejorado con anclas exactas

**Problema resuelto:**
- Ciclo completo sin fricciones entre propuesta e implementación
- Economía de tokens máxima aplicada
- Consistencia transversal garantizada

## Cambio 4: vantage-skill-updater (Nueva Skill)

### Descripción técnica

**Nombre:** `vantage-skill-updater`  
**Tipo:** Skill de evaluación y actualización de compliance  
**Ubicación:**
- `skills/vantage-skill-updater.md` (documentación)
- `skills/vantage-skill-updater.skill` (empaquetado)

**Funcionalidad:**
- Evalúa skills existentes contra 7 KERNEL requirements
- Verifica protocolo sandbox y economía de tokens
- Verifica anclas exactas (KERNEL:DOCUMENTATION-012)
- Verifica Census compliance (KERNEL:DOCUMENTATION-008)
- Actualiza skills para alinear con estándares VANTAGE
- Clasifica gaps por severidad (CRÍTICO / ALTO / MEDIO / BAJO)

**Estado actual:**
- ✅ Creada en filesystem
- ✅ Empaquetada como .skill
- ✅ Agregada a index.json
- ❌ No registrada en Skill Library (Notion)
- ❌ No integrada en Manual (Skill Glossary)
- ❌ No versionada en Changelog

## Alcance solicitado

### Mapeo de IDs existentes

1. **Para vantage-sync-assets:**
   - Verificar si ya existe ID canónico en Manual §23.2
   - Confirmar si requiere subsección propia o basta con entrada narrativa

2. **Para skills de documentación transversal mejoradas:**
   - Verificar si hay IDs para "protocolo sandbox" o "economía de tokens"
   - Buscar patrones similares en skills de sincronización existentes
   - Identificar si KERNEL:DOCUMENTATION-010 ya cubre mejoras

3. **Para vantage-skill-updater:**
   - Proponer ID canónico nuevo (MANUAL:SKILL-GLOSSARY-* para skill de evaluación)
   - Determinar ubicación en Manual (¿§23.2 o §23.4?)
   - Verificar si requiere subsección propia en §23.2

### Desarrollo de documentación transversal

**Para vantage-sync-assets:**
- Definir IDs canónicos nuevos si no existen
- Especificar anchors para:
  - Convención de anuncio (¿reutilizar KERNEL:DOCUMENTATION-005?)
  - Contrato de orquestación (¿proponer KERNEL:ORCHESTRATION-*?)
  - Resumen consolidado de sync (¿proponer KERNEL:ASSETS-SYNC-REPORT?)
- Confirmar ubicación en Manual §23.2

**Para skills de documentación transversal mejoradas:**
- Documentar mejoras de rigor en Kernel
- Especificar anchors para:
  - Protocolo sandbox (¿proponer KERNEL:SANDBOX-PROTOCOL?)
  - Economía de tokens (¿proponer KERNEL:TOKEN-ECONOMY?)
  - Validación de completitud (¿proponer KERNEL:COMPLETENESS-CHECK?)
- Determinar si requieren entrada propia o basta con actualización de KERNEL:DOCUMENTATION-010

**Para vantage-skill-updater:**
- Definir ID canónico (MANUAL:SKILL-GLOSSARY-*)
- Especificar anchors para:
  - Criterios de severidad (¿proponer KERNEL:SEVERITY-CRITERIA?)
  - Protocolo de evaluación (¿proponer KERNEL:SKILL-EVAL-PROTOCOL?)
- Mapear a sección correcta del Manual (¿§23.2 Sincronización y Mantenimiento o §23.4 Estilos de Escritura?)

### Ubicación en Manual

**Para vantage-sync-assets:**
- Confirmar §23.2 (Sincronización y Mantenimiento Documental) es correcto
- Verificar si requiere subsección propia

**Para skills de documentación transversal mejoradas:**
- Determinar si las mejoras de KERNEL:DOCUMENTATION-010 requieren entrada propia
- O si basta con actualización de la sección existente (03.10)

**Para vantage-skill-updater:**
- Evaluar entre §23.2 (Sincronización y Mantenimiento) vs §23.4 (Estilos de Escritura)
- Considerar que es skill de meta-gobernanza, no escritura

## Deliverable esperado

1. **Mapa de IDs:** Lista de IDs existentes aplicables + propuesta de IDs nuevos con justificación
2. **Propuesta de anchors:** Estructura de `KERNEL:*` y `MANUAL:*` con contrato específico
3. **Ubicación en Manual:** Confirmación/ajuste de secciones para las 4 skills
4. **Brief de implementación:** Pasos concretos para añadir los IDs a los archivos relevantes

## Prioridad

**ALTA** — Las 4 skills están en producción o listas para producción y requieren formalización documental para mantener integridad del sistema VANTAGE.

## Notas específicas

**vantage-sync-assets:** Ya está registrada en Skill Library y Manual, pero puede requerir documentación de mejoras si hubo ajustes post-creación.

**Skills de documentación transversal:** Las mejoras son significativas (8 nuevos pasos, protocolo sandbox) y pueden requerir entrada en Kernel para documentar el nuevo estándar.

**vantage-skill-updater:** Es skill nueva con función de meta-gobernanza, requiere registro completo (Skill Library + Manual + Changelog).
