name: vantage-session-handoff
description: Procesa una conversación completa entregada en formato Markdown (.md) y genera un handoff de sesión exhaustivo y listo para producción, combinando el rigor técnico de Prompt Master con la estructura canónica de VANTAGE Handoff. Permite iniciar una nueva conversación manteniendo el 100% del contexto operativo y eliminando la necesidad de fetches iniciales.
---

# VANTAGE: HANDOFF GENERATOR & CONTEXT TRANSFER

ID Canónico: `KERNEL:HANDOFF-GENERATOR` · Trigger: invocación explícita cuando el operador solicita generar un handoff de sesión a partir de un archivo o volcado `.md` de conversación.
Versión de alineación: v1.2.0 — Rigor de Prompt Master + Estructura Handoff S0-S5 (2026-10-14)

## Responsabilidad

Recibe como entrada el texto o archivo `.md` de una conversación previa. Analiza silenciosa y exhaustivamente todo el historial, extrae las 9 dimensiones clave de contexto, identifica el estado exacto del proyecto/tarea, y produce un bloque copiable de handoff optimizado para transferencia de contexto a un nuevo LLM/Agente, garantizando cero pérdida de información y eliminando fetches redundantes en la nueva sesión.

## Zona Primaria — Identidad, Reglas Duras y Anuncio

**Convención de Anuncio**
- Apertura: `HANDING OFF...`
- Cierre: `HANDOFF DELIVERED`

**Reglas Duras (NUNCA Violables)**
1. **Cero Suposición / Cero Inferencia Silenciosa**: Toda decisión, cambio de código o estado reportado debe basarse estrictamente en la evidencia presente en la conversación `.md`.
2. **Cero Tokens Desperdiciados**: Formato denso, técnico, estructurado y sin preámbulos ni prosa de relleno.
3. **Anclaje de Evidencia Post-Ejecución (S4-EVIDENCE)**: Si la sesión anterior incluyó comandos de terminal, mutaciones de archivos o consultas a APIs/Bases de datos, deben incluirse los comandos exactos y sus outputs crudos verificados.
4. **Regla de Adopción Absoluta**: El handoff generado debe estructurarse para que el LLM receptor adopte los hallazgos evidenciados sin re-ejecutar verificaciones redundantes.
5. **Cero Filtrado de Credenciales**: Omitir o sanitizar cualquier API key, token o secreto encontrado en la conversación procesada.

---

## Zona Media — Protocolo de Extracción e Ingesta (.md)

Antes de redactar el handoff, procesar el archivo `.md` e identificar silenciosamente las siguientes 9 dimensiones de contexto:

| Dimensión | Elementos a extraer del `.md` |
|-----------|--------------------------------|
| **Task / Goal** | Objetivo principal de la sesión procesada y meta operativa inmediata. |
| **Stack & Environment** | Herramientas, modelos, rutas de sistema, versiones y banderas activas. |
| **Completed Work** | Acciones ejecutadas con éxito, archivos creados o editados. |
| **Pending / Next Steps** | Tareas pendientes ordenadas por prioridad técnica (máximo 5 críticas). |
| **Blockers / Debt** | Errores no resueltos, limitaciones identificadas o deuda técnica. |
| **State Evidence** | Comandos ejecutados y outputs crudos obtenidos. |
| **Prior Failures** | Rutas intentadas que fallaron o decisiones descartadas para no repetirlas. |
| **Rules & Directives** | Reglas de operación especiales aplicadas durante la sesión (p. ej. MODO ESTRICTO, restricciones). |
| **Memory Block** | Decisiones arquitectónicas y acuerdos congelados. |

---

## Zona de Salida — Formato del Handoff Producido

El resultado debe entregarse en el siguiente formato estricto:

```yaml
handoff:
  serial: HO-######
  schema_version: "1.1"
  generated_at: "YYYY-MM-DD HH:MM:SS"
  timezone: America/Mexico_City
  generator:
    family: AGENT_FAMILY
    instance: AGENT_INSTANCE
  source_session:
    session_id: SESSION-YYYYMMDD-X
    ledger_status: CLOSED_TO_HANDOFF
  parent_handoff:
    serial: null
  skill:
    loaded: true
    name: vantage-session-handoff
  status: DELIVERED


S0 — Timestamp

YYYY-MM-DD HH:MM:SS CDMX

S1 — Identidad e IDs

HO-###### | AGENT_FAMILY/AGENT_INSTANCE | SESSION-YYYYMMDD-X | Ledger: CLOSED_TO_HANDOFF

S2 — Pendientes Críticos

1. [Prioridad 1]: Descripción clara y precisa de la acción inmediata necesaria.

S3 — Deuda Técnica, Errores y Bloqueadores

⚬ Rutas descartadas / Fallas: [Lo que se intentó y falló para evitar repetirlo]
⚬ Bloqueadores activos: [Factores externos o errores pendientes]
⚬ Deuda acumulada: [Refactorizaciones o pendientes no urgentes]

S4 — Estado Verificado y Última Acción

Describir la última acción ejecutada en la sesión.

S4-EVIDENCE (Evidencia Cruda)

Para cada acción de escritura o verificación en S4:

⚬ Comando exacto: comando --flag
⚬ Output crudo:

[Output exacto obtenido en la sesión anterior]


Nota de Adopción: La instancia receptora de este handoff debe adoptar esta evidencia como válida sin re-ejecutar verificaciones, salvo orden explícita del operador.

S5 — Bloque de Memoria y Contexto Acumulado

## Context & Architecture (Carry Forward)
- Stack / Tools: [Stack técnico confirmado]
- Decisiones congeladas: [Arquitectura locked, parámetros fijados]
- Reglas operativas: [Filtros, exclusiones, banderas de comportamiento]
- Archivos y Rutas clave: [Directorio de trabajo / archivos modificados]


Regla de Ejecución del Skill

1. Cuando el operador proporcione un archivo .md o texto con el historial de una sesión:
2. Emitir inmediatamente: HANDING OFF...
3. Procesar internamente el contenido según el Protocolo de Extracción e Ingesta.
4. Renderizar el bloque de Handoff completo (S0 a S5) optimizado para copiar y pegar directamente en la nueva conversación.
5. Cerrar con la firma:

HANDOFF DELIVERED
Serial: HO-######
Generated by: AGENT_FAMILY/AGENT_INSTANCE
Session: SESSION-YYYYMMDD-X