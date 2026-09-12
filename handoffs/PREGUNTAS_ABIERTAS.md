# PREGUNTAS ABIERTAS — Refactor Orquestador Tracker

## Q-1: ¿Cuál es el nombre exacto de la propiedad Source_Type en el schema vivo?
**Decisión tomada (CORREGIDA):** Implementar `"Source_Type"` limpio (sin trailing space) y actualizar TODOS los lectores/escritores. El rename del schema vivo se ordena en G7/G8 (Claude/MCP) ANTES del cutover.  
**Rationale:** Contradice §4-v1 (normalización: Source_Type␣ trailing space → Source_Type limpio con migración).  
**Alternativas descartadas:** Mantener `"Source_Type "` con espacio (inconsistente con §4-v1).  
**Qué dato la cerraría:** Schema vivo de Notion tras rename MCP.  
**Impacto si se revierte:** Alto — rompe normalización §4-v1 y crea drift schema/código.

## Q-2: ¿El valor "Target" en Status debe ser renombrado a "Objetivo" según §4-v1?
**Decisión tomada (CONFIRMADA):** NO renombrar. `tracker_flow.py` v1 ya usa `Status.OBJETIVO = "Objetivo"` en enums. El valor "Target" en datos legacy se mapeará a "Objetivo" en normalización.  
**Matiz:** Rename ya ejecutado y verificado en prod (v9.21.56+T1). Rationale actualizado: el rename de schema vivo ya ocurrió, ahora solo falta migración de datos legacy.  
**Alternativas descartadas:** Mantener "Target" como valor activo (inconsistente con design v1).  
**Qué dato la cerraría:** Confirmación de Mau sobre preferencia de valor operativo.  
**Impacto si se revierte:** Medio — afecta UI/operador pero no lógica de pipeline.

## Q-3: ¿Cómo debe tratarse "Holding" en normalización §4-v1?
**Decisión tomada (CORREGIDA PARCIAL):** Convertir a select curado desde alias_map (valor canónico de marca cuando existe). Holdings reales (Nike Inc., LVMH) se migran, JAMÁS se vacían. Placeholders → vacío. Criterio por categoría vive en Task 3d8938be.  
**Rationale:** Curado OK, pero holdings reales deben preservarse (pérdida de datos valor).  
**Alternativas descartadas:** Mantener como texto libre con 87.5% ruido (radiografía §5.2.4).  
**Qué dato la cerraría:** Task 3d8938be en Tasks Tracker (criterio por categoría).  
**Impacto si se revierte:** Alto — pérdida de holdings corporativos reales.

## Q-4: ¿Debemos implementar el bloqueo Class-B-mientras-REVIEW_NEEDED documentado en KERNEL:GATE-DECISION-010?
**Decisión tomada (ACEPTADA CONDICIONAL):** NO implementar en código. SOLO válida si G9 deroga/reescribe KERNEL:GATE-DECISION-010. Si G9 no deroga, gate rojo automático.  
**Rationale:** La auditoría §4.6 confirma que el contrato es fictional en el lado lector.  
**Alternativas descartadas:** Implementar bloqueo real (requeriría cambios mayores en múltiples fases).  
**Qué dato la cerraría:** G9 (docsync) debe derogar/reescribir KERNEL:GATE-DECISION-010.  
**Impacto si se revierte:** ALTO — gate rojo automático si G9 no deroga el contrato fictional.

## Q-5: ¿Cuál es la ventana de tiempo para "edición manual reciente" en precedencia manual §2.3?
**Decisión tomada:** Usar "desde el último run exitoso" como ventana. Detectar `Last_Gate_Run` en cada fila y comparar con `last_edited_time`. Si `last_edited_time > Last_Gate_Run` y autor es humano → inmunidad a mutación destructiva.  
**Alternativas descartadas:** Ventana fija (ej. 7 días) — menos determinista.  
**Qué dato la cerraría:** Preferencia de operador sobre granularidad de ventana.  
**Impacto si se revierte:** Bajo — solo ajusta parámetro de ventana.

## Q-6: ¿Debe el nuevo orquestador conservar el re-query en cada fase?
**Decisión tomada:** NO. Un solo re-query inicial, luego snapshot en memoria. Fases operan sobre datos stale de fases anteriores (como hoy F3.5/F3.5.1/F3.6), pero esto se corrige unificando el cómputo de expiración NAD (F0+F3.5.1) y asegurando writes condicionados a diff real.  
**Alternativas descartadas:** Re-query por fase (performance costoso, write-churn en Last_Gate_Run).  
**Qué dato la cerraría:** Requerimiento de performance vs consistency.  
**Impacto si se revierte:** Medio — afecta performance y diseño de snapshot.

## Q-7: ¿Cómo debe tratarse el bug día/mes :125 en priority_logic.py?
**Decisión tomada:** NO tocar el bug. Portar la llamada a priority_logic.py desde layer_1_run.py sin modificar la lógica interna. El bug queda documentado en backlog (radiografía §1.1-F3.6).  
**Alternativas descartadas:** Fixear el bug (fuera de alcance de este contrato).  
**Qué dato la cerraría:** Autorización explícita para extender alcance a fixes de bugs.  
**Impacto si se revierte:** Bajo — el bug es edge case específico.

## Q-8: ¿Debe dedup consolidarse en un solo mecanismo ingesta+fuzzy?
**Decisión tomada:** SÍ. Unificar dedup_cross_layer (ingesta) + dedup_opportunities.py (fuzzy post-hoc) en un solo módulo con survivor canónico L1>L2>L3>N/A y guard `is_mutable`. consolidate_duplicates.py se retira (es trash físico sin confirmación).  
**Alternativas descartadas:** Mantener dos mecanismos separados (duplicación de lógica, inconsistencia).  
**Qué dato la cerraría:** Confirmación de que no hay otras dependencias en consolidate_duplicates.py.  
**Impacto si se revierte:** Alto — arquitectura de dedup completamente diferente.

## Q-9: ¿Debe class_b_guard generalizarse a TODAS las vías de escritura?
**Decisión tomada:** SÍ. Generalizar class_b_guard como middleware fail-closed para TODAS las vías (pipeline, ingesta, MCP, batch). Esto cierra D-002 completamente.  
**Alternativas descartadas:** Mantener exención para alguna vía (reintroduce asimetría).  
**Qué dato la cerraría:** Confirmación de que no hay edge cases donde class_b_guard fallaría.  
**Impacto si se revierte:** Alto — seguridad de escritura comprometida.

## Q-10: ¿Cómo debe tratarse batch_operations.py?
**Decisión tomada:** Retirar como tool recurrente. Convertir a migración versionada de un solo uso (flip masivo Target→Exploratorio) si hay necesidad histórica documentada. Si no, simplemente archivar.  
**Alternativas descartadas:** Mantener como tool vigente (sin guard is_mutable, riesgo alto).  
**Qué dato la cerraría:** Verificar si hay dependencias o uso recurrente en scripts/Raycast.  
**Impacto si se revierte:** Bajo — script de uso limitado.
