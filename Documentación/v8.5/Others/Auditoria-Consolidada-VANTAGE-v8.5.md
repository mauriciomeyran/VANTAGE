# AUDITORÍA CONSOLIDADA — VANTAGE v8.5
### Síntesis de 3 auditorías independientes (Agente A, B, C)

**Metodología de consolidación:** cada hallazgo se clasifica por nivel de consenso:
- 🔴 **CONSENSO TOTAL** (3/3 agentes) — máxima confianza, prioridad de remediación
- 🟠 **CONSENSO PARCIAL** (2/3 agentes) — alta confianza
- 🟡 **HALLAZGO ÚNICO** (1/3 agentes) — requiere validación adicional, pero se conserva por valor de señal

---

## VECTOR 1 — Capa Lógica (Data Integrity)

### 🔴 [C1] Bypass de ownership Class A/B vía edición manual / MCP — **CRÍTICO**
**Consenso: 3/3** (V1-01 Agente A, V1-01 Agente B, V1-LG-001 Agente C)

Los tres agentes detectan la misma vulnerabilidad raíz desde ángulos distintos:
- **Agente A**: el operador puede editar Class A directamente en Notion (URL, JD) sin pasar por RT-1, y Python recalculará Score/Gate sobre ese input sin trazabilidad del cambio.
- **Agente B**: no hay hard-lock técnico que impida que una instrucción de usuario fuerce al LLM a escribir Class B vía MCP, puenteando el motor Python.
- **Agente C**: el HANDOFF de CV-A/CV-B podría transportar campos Class B implícitos sin validación explícita de exclusión.

**Síntesis del riesgo:** la separación Class A/B es sólida *en la capa de reglas documentadas*, pero **no existe ningún guardrail técnico verificable** (ni en Notion, ni en el HANDOFF, ni en MCP) que impida la contaminación cruzada. Es una vulnerabilidad de **gobernanza sin enforcement**, no de diseño lógico.

**Impacto combinado:** corrupción silenciosa de la fuente de verdad, sin audit trail, en al menos tres puntos de entrada distintos (Notion directo, MCP, HANDOFF).

---

### 🔴 [C2] Zona de indefinición en el rango Score 40–59 / tasa de rechazo no auditada — **ALTO/CRÍTICO**
**Consenso: 3/3** (V2-02 Agente A, V2-02 Agente B, V2-PL-002 Agente C)

- **Agente A** es el más específico: identifica una **zona muerta estructural** — CREATE exige Score≥60, BLOCKED exige Score<40, y el rango 40–59 no tiene GateDecision documentado explícitamente, aunque "Para Revisar" lo cubre en Notion.
- **Agente B** y **Agente C** abordan la misma raíz desde el ángulo de la tasa de rechazo: el sistema acepta 50-70% de rechazo como "normal" sin desagregar cuánto de eso es zona 40-59, fallo de URL, Score bajo real, o Hard Blocks.

**Síntesis:** este es el **hallazgo más sólido de las tres auditorías** — converge tanto en la causa (gate lógicamente incompleto) como en el síntoma (tasa de rechazo opaca). Es la vulnerabilidad crítica nombrada explícitamente como tal por Agente A y Agente C en sus veredictos ejecutivos.

**Recomendación consolidada:** documentar explícitamente el GateDecision para Score 40-59 (candidato: nueva categoría "REVIEWNEEDED" o "Candidate-Review") y publicar métricas desagregadas de causa de rechazo (URL / Score / Hard Block / zona 40-59).

---

### 🟠 [C3] Desincronización Status (Class A) vs GateDecision/URL_GATE (Class B) — **ALTO**
**Consenso: 3/3 con matices** (V1-03 Agente A, V1-02 Agente B, V1-LG-003 Agente C)

Los tres coinciden en que `Status` y `GateDecision`/`URL_GATE` son campos independientes que pueden quedar desincronizados, pero enfatizan ángulos distintos:
- **Agente A**: un registro BLOCKED puede seguir visible en vistas activas si el operador cambia Status manualmente; no hay guardia en Notion.
- **Agente B**: no se define cuál campo es "la verdad" en caso de contradicción (ej. Status=Target con Gate=EXPIRED).
- **Agente C**: lo lleva al extremo — cuestiona si `URL_GATE=BLOCKED` siquiera actualiza `Status`, y si Notion sigue siendo creíble como "fuente única de verdad" si no refleja el estado real calculado por Python.

**Síntesis:** problema unánime de **arbitraje de verdad entre capas**. Se necesita una regla de precedencia explícita (¿Class B siempre gana sobre Class A en caso de conflicto?) y un filtro de vista que excluya BLOCKED/EXPIRED independientemente del Status manual.

---

### 🟠 [C4] Registros legacy (pre-v6.0) sin gobernanza de ciclo de vida — **ALTO/MEDIO**
**Consenso: 3/3** (V1-02 Agente A, V1-03 Agente B, V1-LG-002 Agente C)

Coinciden en que la "limpieza masiva de entradas legacy" (v6.0) fue una acción puntual, no una regla activa de schema. Variantes de énfasis:
- **Agente A**: pueden convivir en Ready-to-Apply si Status=Target y Score≥60, sin filtro de versión de ingesta.
- **Agente B**: los campos `layer`/`hash` (introducidos en v7.5) no tienen proceso de migración para registros previos, salvo backfill manual.
- **Agente C**: añade la duda de si Python intenta recalcular Class B sobre legacy con datos incompletos, generando posibles errores de cálculo o falsos positivos en KPIs.

**Síntesis:** gap de versionado de schema sin mecanismo de exclusión automática. Riesgo medible solo si hay volumen real de legacy aún activo.

---

## VECTOR 2 — Rendimiento del Pipeline

### 🔴 [C5] Sin SLA/latencia documentada entre Trigger y Score calculable — **CRÍTICO/ALTO**
**Consenso: 3/3** (V2-01 Agente A, V2-01 Agente B, V2-PL-001 Agente C)

- **Agente A**: solo existe "Pipeline runtime: 2 minutos" como indicador general, no específico al flujo CV-A→Score.
- **Agente B**: aporta el dato más operativo — el Score depende de corridas de `vantage_pipeline.sh` programadas ~3 veces/día, por lo que un registro puede esperar horas sin Score actualizado. Propone una mejora concreta: trigger de scoring on-demand (`vantage.py score --id`) para bajar de ~45 min a segundos.
- **Agente C**: agrega la dimensión de riesgo de **race condition** — lecturas (SYNC/Runtime) podrían ocurrir sobre Class A ya escrito pero Class B aún vacío.

**Síntesis:** es el mismo gap visto desde tres ángulos complementarios (medición / impacto operativo / riesgo técnico). La cifra de Agente B (~45 min, 3 corridas/día) es la más útil como baseline aproximado, aunque no está confirmada documentalmente por ningún agente — tratarla como estimación, no como hecho verificado.

---

### 🟠 [C6] BATCH RULE (lotes de 10) ausente del contrato vigente / sin protocolo de error — **MEDIO**
**Consenso: 3/3** (V2-03 Agente A, V2-03 Agente B, V2-PL-003 Agente C)

Acuerdo total: la regla existe en el Changelog v6.2.1 pero no aparece en Kernel v8.5 ni Manual v8.5 como regla activa. Agente C es el más exhaustivo en preguntas abiertas: ¿reintento automático?, ¿rollback?, ¿notificación de fallo parcial?

**Síntesis:** gap de bajo riesgo inmediato pero alta incertidumbre operativa si el volumen de FEED crece.

---

### 🟡 [C7] Diseño de Gate "agresivo por diseño" sin trazabilidad de causa-raíz del rechazo
**Único: Agente C** (V2-PL-002), aunque conceptualmente se solapa con [C2]

Agente C es el único que pide explícitamente desagregar el % de BLOCKED por causa (URL muerta vs. Score bajo vs. Hard Block) como mejora de observabilidad, no solo como gap lógico. Se mantiene como sub-recomendación de [C2].

---

## VECTOR 3 — Experiencia (UX / VM Component)

### 🔴 [C8] Sin garantía de visibilidad de Sueldo/Ubicación/Ready-to-Apply sin scroll en el Tracker — **ALTO**
**Consenso: 3/3** (V3-02 Agente A, V3-01 Agente B, V3-UX-002 Agente C)

Acuerdo unánime y casi textual entre los tres: el Manual solo documenta la *existencia* de las 4 vistas (Ready-to-Apply, Para Revisar, Archivar, All), pero no especifica orden de columnas, campos fijos, ni layout. La experiencia depende de configuración manual no contractual.

**Síntesis:** uno de los hallazgos más limpios — sin matices entre agentes. Fácil de remediar con una especificación de columnas fijas en el contrato del Manual.

---

### 🟡 [C9] Conflicto de positioning entre modos N1–N4 sin regla de desempate
**Único: Agente A** (V3-01)

Agente A es el único en notar la asimetría de profundidad entre N1 (1 ancla) y N4 (2 anclas con KPIs) y la ausencia de regla de desempate cuando un JD activa criterios híbridos. Agentes B y C no abordan esto directamente (Agente C toca un tema adyacente —ver C10— pero distinto).

---

### 🟡 [C10] Positioning Modes N1–N4 no conectados operativamente al flujo CV-A
**Único: Agente C** (V3-UX-001)

Agente C señala que, aunque N1-N4 están bien definidos en el Career Canon, no hay evidencia de que CV-A los use para filtrar/priorizar vacantes, ni mapeo documentado hacia `VM_Scope`/`Role_Class`. Es un ángulo distinto de [C9]: no es sobre desempate interno, sino sobre **desconexión entre el Canon y el pipeline operativo**.

---

### 🟡 [C11] Orden cronológico rígido en CV (C01→C05) sin excepción por relevancia
**Único: Agente B** (V3-02, severidad Bajo)

Hallazgo menor, no contradicho por los otros dos, pero tampoco mencionado.

---

## VECTOR 4 — Consumo de Tokens

### 🔴 [C12] Violación de la regla "Terminal/lazy-load como ruta preferente" en CV-B y/o CV-A — **CRÍTICO**
**Consenso: 3/3 con desacuerdo en el detalle técnico** (V4-01 Agente A, V4-01 Agente B, V4-TK-001 Agente C)

Los tres convergen en que el sistema promete eficiencia de tokens vía lazy-load pero la rompe en la práctica — **sin embargo, difieren en cuál trigger es el culpable principal**:
- **Agente A**: el cuello de botella es **CV-B**, que obliga a cargar el Skeleton completo + Tag Registry (48 entradas) + Experience Records en ES/EN simultáneamente.
- **Agente B**: coincide en CV-B y agrega **CANON-UPDATE** como segundo trigger que prohíbe explícitamente Runtime/lazy-load según el System Prompt §3.
- **Agente C**: pone el foco en **CV-A**, señalando que el flujo pasa por Runtime (capa de solo lectura, con throttle de 0.35s/request en operaciones masivas) en vez de usar `lazy_loader.py` como ruta recomendada por el propio System Prompt §5.

**⚠️ Nota de reconciliación:** estas tres versiones **no son necesariamente contradictorias** — es plausible que el problema exista en *varios* triggers (CV-A vía Runtime, CV-B y CANON-UPDATE vía carga completa obligatoria), pero ningún agente individual cubre los tres simultáneamente. Esto sugiere que **el problema real es más amplio que lo que cualquier auditoría individual capturó**: una auditoría de seguimiento debería verificar punto por punto qué trigger usa qué ruta de carga.

**Impacto combinado:** esta es la vulnerabilidad con **mayor divergencia de diagnóstico entre agentes** a pesar de consenso en la existencia del problema — tratar con cautela el detalle técnico citado por cada uno hasta verificar contra el código fuente (`feed_processor.py`, `lazy_loader.py`, `vantage_pipeline.sh`).

---

### 🟠 [C13] Sobre-carga de contexto en triggers de baja complejidad (FAST / DRY RUN duplicado)
**Consenso: 2/3** (V4-02 Agente A, V4-02 Agente B)

- **Agente A**: el trigger FAST (URL única) debería evitar cargar el AI Component completo, pero en la práctica el operador abre sesión completa de Claude para una sola vacante.
- **Agente B**: ángulo distinto pero relacionado — el protocolo DRY RUN obligatorio implica que el LLM procesa la información dos veces (preview + write), duplicando costo de tokens en cada escritura, no solo en FAST.

**Síntesis:** dos formas de "duplicación de carga" distintas pero compatibles; ambas reducibles con el mismo principio (cachear o reutilizar el primer pase en vez de repetir el cómputo completo).

---

## VEREDICTOS EJECUTIVOS — COMPARACIÓN

| | Agente A | Agente B | Agente C |
|---|---|---|---|
| **Vulnerabilidad crítica nombrada** | Zona muerta Score 40-59 [C2] | Bypass de Runtime en CV-B/CANON-UPDATE [C12] | Desincronización URL_GATE↔Notion [C3] |
| **Mejora de mayor impacto sugerida** | Documentar gate para 40-59 | Trigger de scoring on-demand | Definir cuándo usar lazy_loader vs Runtime |
| **Puntaje de solidez** | **7.2/10** | **7.2/10** | **6/10** |

**Nota sobre la divergencia de puntaje:** Agentes A y B coinciden exactamente en 7.2/10 pero por razones distintas (A penaliza por zona muerta + Tracker + trazabilidad de ediciones; B penaliza por contradicción tokens/promesa de eficiencia). Agente C es más severo (6/10) porque pondera explícitamente la falta de documentación operativa y el riesgo de desincronización entre capas como fallas de confiabilidad, no solo de claridad documental.

---

## RANKING CONSOLIDADO DE PRIORIDAD DE REMEDIACIÓN

1. **[C1]** Bypass de ownership Class A/B sin enforcement técnico — *gobernanza, 3/3*
2. **[C2]** Zona muerta Score 40-59 + opacidad de tasa de rechazo — *lógica de gate, 3/3*
3. **[C3]** Desincronización Status↔GateDecision/URL_GATE — *arbitraje de verdad, 3/3*
4. **[C12]** Incumplimiento de ruta lazy-load en triggers pesados — *eficiencia, 3/3 con diagnóstico divergente, requiere verificación de código*
5. **[C5]** Sin SLA de latencia Trigger→Score — *observabilidad, 3/3*
6. **[C8]** Sin garantía de layout del Tracker — *UX, 3/3*
7. **[C4]** Gobernanza de registros legacy — *schema, 3/3*
8. **[C6]** BATCH RULE sin protocolo de error — *resiliencia, 3/3*
9. **[C13]** Duplicación de carga en FAST/DRY RUN — *eficiencia secundaria, 2/3*
10. **[C9]/[C10]** Positioning Modes: desempate interno y desconexión con CV-A — *UX/estrategia, hallazgos únicos complementarios*
11. **[C11]** Rigidez cronológica del CV — *UX menor, único, severidad baja*

---

## PUNTAJE CONSOLIDADO

**Promedio simple de los tres puntajes: 6.8/10**

Dado que el hallazgo más severo en discrepancia ([C12]) y el más unánime en gravedad ([C1], [C2], [C3]) apuntan a **falta de enforcement técnico más que a errores de diseño**, la arquitectura conceptual del sistema parece sólida (los tres agentes elogian la separación Class A/B y el Career Canon), pero **la distancia entre lo documentado y lo verificable en código/Notion** es el patrón que se repite en los tres reportes. Se recomienda que la próxima auditoría incluya inspección directa de `feed_processor.py`, `lazy_loader.py` y la configuración real de vistas en Notion, en lugar de basarse solo en documentación.
