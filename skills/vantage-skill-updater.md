---
name: vantage-skill-updater
description: Evalúa y actualiza skills existentes para alinearlas con VANTAGE system requirements (KERNEL:DOCUMENTATION-010, DOCUMENTATION-005, FAIL-PHILOSOPHY, DOCUMENTATION-012, DOCUMENTATION-001, DOCUMENTATION-008). Verifica cumplimiento de protocolo sandbox, economía de tokens, anclas exactas, Census compliance, y Matriz Tipográfica Congelada. USAR cuando el operador pida "actualizar skills con requisitos VANTAGE", "evaluar compliance de skills", o cuando quiera alinear skills existentes con estándares del sistema.
---

# VANTAGE Skill Updater — VANTAGE Requirements Compliance

Evalúa y actualiza skills existentes para asegurar cumplimiento de los requisitos del sistema VANTAGE, siguiendo protocolo sandbox para máxima economía de tokens.

## Convención de Anuncio (KERNEL:DOCUMENTATION-005)

- Apertura: `BEGINNING SKILL EVALUATION...`
- Cierre: `SKILL EVALUATION COMPLETE`

## Protocolo Sandbox — Economía de Tokens Máxima

**Regla fundamental:** Todos los procesos internos corren en sandbox sin renderizar al operador. Solo se output:
1. `BEGINNING SKILL EVALUATION...` (inicio)
2. `EVALUATION RESULTS` + propuesta de actualizaciones (resultado final)
3. `SKILL EVALUATION COMPLETE` (cierre tras APROBAR_WRITE)

**Procesos silenciosos (sandbox interno):**
- Lectura y análisis de skills existentes
- Verificación de cumplimiento de KERNEL requirements
- Generación de propuestas de actualización
- Validación de anclas exactas
- Verificación de protocolo sandbox

## VANTAGE System Requirements a Verificar

### KERNEL:DOCUMENTATION-010 — Protocolo de 6 fases
- ¿La skill sigue el protocolo de documentación transversal si aplica?
- ¿Mapea nodos naturales (no adendum al final)?
- ¿Valida consistencia con System Prompt?
- ¿Ejecuta Write-Back Verification post-escritura?

### KERNEL:DOCUMENTATION-005 — Convención de Anuncio
- ¿La skill declara inicio con verbo en gerundio/participio?
- ¿La skill declara cierre con verbo correspondiente?
- ¿Usa convención [VERBO-ING]... / [VERBO-ED]?

### KERNEL:DOCUMENTATION-012 — Cero Inferencia Silenciosa
- ¿Toda afirmación técnica incluye ancla exacta (PREFIX:KEY)?
- ¿Patrón de anclaje: [CONCEPTO] debe seguir [KERNEL:ID] — explicación?

### KERNEL:DOCUMENTATION-001 — Canonical Document ID Contract
- ¿IDs siguen formato [PREFIX]:[KEY]?
- ¿Cumple Regla de Bloque Único (ID en heading ###)?
- ¿Respeta Matriz Tipográfica Congelada?

### KERNEL:DOCUMENTATION-008 — Census Compliance
- ¿Skills que crean IDs canónicos disparan CENSUS-SYNC Regla 1?
- ¿Skills que modifican estructura actualizan CENSUS_SPEC?
- ¿Ejecutan `vcensus` + `vversions --sync` antes de cerrar?

### Economía de Tokens Máxima
- ¿La skill tiene máximo 3 outputs visibles?
- ¿Los procesos internos corren en sandbox sin renderizar?
- ¿Solo outputs: inicio, resultado, cierre?

## Proceso de Ejecución

### Paso 1 — Identificar skills a evaluar (sandbox interno)
[Proceso interno] Determinar qué skills evaluar:
- Skills específicas solicitadas por el operador
- Todas las skills en `/skills/` si se solicita evaluación completa
- Skills en `.devin/skills/` si aplica

### Paso 2 — Leer y analizar cada skill (sandbox interno)
[Proceso interno] Para cada skill:
- Leer contenido completo de SKILL.md
- Verificar cada KERNEL requirement
- Identificar gaps de compliance
- Clasificar severidad (CRÍTICO / ALTO / MEDIO / BAJO)

### Paso 3 — Generar propuesta de actualizaciones (sandbox interno)
[Proceso interno] Para cada skill con gaps:
- Generar propuestas específicas de actualización
- Incluir anclas exactas KERNEL en cada propuesta
- Priorizar por severidad
- Estimar complejidad de implementación

### Paso 4 — Presentar resultados (único output visible)
[OUTPUT VISIBLE] Presentar al operador:
- Resumen de evaluación por skill
- Gaps detectados clasificados por severidad
- Propuestas de actualización con anclas exactas
- Estimación de esfuerzo por skill

Declarar: `EVALUATION RESULTS`

### Paso 5 — Esperar autorización explícita
Esperar confirmación del operador para ejecutar actualizaciones. Tokens válidos: `APROBAR_WRITE`, `APROBAR`, `SÍ`, `sí`, `YEP`, `yep`.

### Paso 6 — Ejecutar actualizaciones (sandbox interno)
[Proceso interno] Para cada skill autorizada:
- Aplicar actualizaciones propuestas
- Respetar convención de anuncio (KERNEL:DOCUMENTATION-005)
- Integrar protocolo sandbox (economía de tokens)
- Incluir anclas exactas (KERNEL:DOCUMENTATION-012)
- Verificar Census compliance si aplica

### Paso 7 — Validación post-actualización (sandbox interno)
[Proceso interno] Para cada skill actualizada:
- Verificar que todos los KERNEL requirements se cumplen
- Validar que protocolo sandbox esté integrado
- Confirmar que anclas exactas estén presentes
- Verificar que convención de anuncio esté correcta

### Paso 8 — Presentar resumen final (output visible)
[OUTPUT VISIBLE] Presentar al operador:
- Skills actualizadas exitosamente
- Skills que requieren revisión manual
- Skills que no requieren cambios
- Recomendaciones de seguimiento

Declarar: `SKILL EVALUATION COMPLETE`

## Criterios de Severidad

**CRÍTICO:**
- Falta de convención de anuncio (KERNEL:DOCUMENTATION-005)
- Falta de anclas exactas en afirmaciones técnicas (KERNEL:DOCUMENTATION-012)
- Violación de Regla de Bloque Único (KERNEL:DOCUMENTATION-001)

**ALTO:**
- Falta de protocolo sandbox (economía de tokens)
- Skills que crean IDs sin Census compliance (KERNEL:DOCUMENTATION-008)
- Falta de Write-Back Verification en skills de escritura

**MEDIO:**
- Falta de Matriz Tipográfica Congelada
- Inconsistencia menor en formato de IDs
- Falta de validación de consistencia con System Prompt

**BAJO:**
- Mejoras cosméticas en descripción
- Optimización de prosa
- Reorganización de secciones sin impacto funcional

## Reglas de Oro

- **Nunca actualizar sin APROBAR_WRITE explícito** — gates independientes por skill
- **Siempre incluir anclas exactas** — KERNEL:DOCUMENTATION-012 es obligatorio
- **Mantener economía de tokens** — protocolo sandbox en todas las skills
- **Priorizar CRÍTICO y ALTO** — MEDIO y BAJO pueden posponerse
- **Pres backward compatibility** — no romper funcionalidad existente

## No Aplica A

- Skills fuera del sistema VANTAGE (Anthropic built-in, otros sistemas)
- Skills que ya cumplen todos los KERNEL requirements
- Skills en formato binario que no pueden leerse como texto

## Output de la Skill

El output es exclusivamente:
1. `BEGINNING SKILL EVALUATION...` (inicio)
2. `EVALUATION RESULTS` + propuesta de actualizaciones (resultado)
3. `SKILL EVALUATION COMPLETE` (cierre)

Nunca contenido intermedio de análisis, never dumps de texto completo, never outputs de proceso interno — todo corre en sandbox.
