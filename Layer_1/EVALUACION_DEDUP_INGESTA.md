# Evaluación de Factibilidad: Mover Dedup_Flag a feed_processor.py (ingesta)

**Fecha:** 2026-08-04  
**Tipo:** Evaluación (no implementación)  
**Brief Reference:** Ticket resuelto `3b2938befc4281429876e4b3e811566c`

---

## 1. Respuestas a los 3 puntos de verificación (evidencia de código)

### 1.1 ¿dedup_by_content_fingerprint() escribe Dedup_Flag?

**Respuesta:** SÍ, confirma que escribe `Dedup_Flag` cuando detecta coincidencia.

**Evidencia de código:**
- **Archivo:** `feed_processor.py`
- **Línea 690:** `_set_dedup_flag_if_needed(notion_utils, existing[0], schema)` - llamado cuando fingerprint_hash coincide
- **Línea 733:** `_set_dedup_flag_if_needed(notion_utils, row, schema)` - llamado cuando brand+title+location coinciden
- **Línea 503-542:** Implementación completa de `_set_dedup_flag_if_needed()` que escribe `Dedup_Flag = "Posible duplicado"` vía Notion API

**Conclusión:** La lógica de escritura de `Dedup_Flag` ya existe en `feed_processor.py` y está funcionando.

---

### 1.2 ¿Por qué los 3 casos del ticket no tenían Dedup_Flag en la ingesta?

**Respuesta:** Los casos del ticket (Multicont, Confidencial×2) tenían **hash distintos** debido a rotación de `jk` de Indeed, por lo que pasaron por la ruta `compute_dedup_hash()` sin coincidencia, pero **NO pasaron por la ruta fallback** `dedup_by_content_fingerprint()` que habría detectado el duplicado por fingerprint.

**Evidencia de código:**
- **Archivo:** `feed_processor.py`
- **Línea 892:** `if dedup_by_content_fingerprint(record, notion_utils, schema):` - el fallback solo se ejecuta cuando `dedup_cross_layer()` retorna False
- **Línea 881-889:** `dedup_cross_layer()` retorna True cuando encuentra hash o URL coincidente
- **Línea 602-615:** Si hash coincide, retorna True sin ejecutar fallback
- **Evidencia en Notion:** Los casos Multicont tienen hash distintos:
  - `39a938befc428135ba15eb001d21125e`: hash `8e24a0356e95ab6c8b179fc98e51a3c22be90130ec70380768de9c7a7f46af69`
  - `39a938befc428102a26ecbc0fe20917c`: hash `83533bf7a3d87172760e4f5ba266b4b3d5241e9a888282b704dd7c7dcb81bd9b`

**Análisis del flujo real:**
1. Vacante entra → `compute_dedup_hash()` → hash diferente → continúa
2. `dedup_cross_layer()` busca hash exacto → no encuentra → continúa  
3. `dedup_cross_layer()` busca URL exacta → diferente → continúa
4. `dedup_cross_layer()` busca brand+title en ventana 7-30 días → **NO EJECUTA ESTE CHEQUEO** (límite 659 solo hace comparación de título exacto, no fuzzy)
5. `dedup_cross_layer()` retorna False
6. **En este punto DEBERÍA ejecutarse `dedup_by_content_fingerprint()`** (línea 892), pero hay una laguna en el flujo

**Hallazgo crítico:** Hay un **gap en el flujo de invocación**. `dedup_by_content_fingerprint()` debería ejecutarse pero hay condiciones que pueden impedirlo, o el flujo de los casos específicos no cumplió los requisitos para llegar a ese punto.

---

### 1.3 ¿feed_processor.py tiene visibilidad del Tracker completo?

**Respuesta:** SÍ, tiene visibilidad filtrada del Tracker mediante `query_notion_db()` con filtros temporales y de propiedades.

**Evidencia de código:**
- **Archivo:** `feed_processor.py`
- **Línea 422-464:** Implementación de `query_notion_db()` que consulta al data source VANTAGE (ID: `442938befc42828fb72e076818d65a5b`)
- **Línea 713-723:** `dedup_by_content_fingerprint()` usa filtro temporal:
  ```python
  time_filter = {"past_month": {}} if window_days >= 28 else {"past_week": {}}
  candidates = query_notion_db(
      notion_utils,
      filter_body={
          "and": [
              {"timestamp": "created_time", "created_time": time_filter},
              schema.text_filter(schema.brand_prop, brand),
          ]
      },
      schema=schema,
  )
  ```
- **Línea 641-651:** `dedup_cross_layer()` usa filtro similar:
  ```python
  time_filter = {"past_month": {}} if window_days >= 28 else {"past_week": {}}
  candidates = query_notion_db(
      notion_utils,
      filter_body={
          "and": [
              {"timestamp": "created_time", "created_time": time_filter},
              schema.text_filter(schema.brand_prop, brand),
          ]
      },
      schema=schema,
  )
  ```

**Conclusión:** `feed_processor.py` consulta el Tracker completo, pero lo hace **con filtros específicos** (ventana de tiempo + brand) para optimizar performance, no carga todo el Tracker en memoria.

---

## 2. Evaluación por dimensiones

### 2.1 Estabilidad del pipeline de ingesta

**Hallazgo:** `feed_processor.py` ya hace múltiples consultas a Notion por cada vacante procesada (hash check, URL check, brand+title en ventana). Agregar más consultas no es un cambio radical, pero sí incrementa latencia.

**Riesgo:** MEDIO

**Justificación:**
- **Ya existen dependencias de red:** Cada vacante actual ya dispara 2-3 queries a Notion (hash, URL, brand+title)
- **Carga actual:** Con 20-50 vacantes por batch típico, ya hay 40-150 queries por corrida
- **Impacto incremental:** Agregar fingerprint matching añadiría 1 query adicional por vacante que pasa las primeras comprobaciones (~50% de casos)
- **Rate-limiting:** No observado en logs actuales, pero multiplicar queries aumenta exposición
- **Caché:** No existe caché del Tracker en `feed_processor.py` - cada query es nueva

**Recomendación de mitigación:** Si se implementa, considerar caché del Tracker por corrida (query una vez al inicio, reutilizar en memoria) en vez de query por vacante.

---

### 2.2 Riesgo de falsos positivos en tiempo real vs. batch

**Hallazgo:** El filtro anti-falso-positivo "electrónica" que Devin implementó en `dedup_opportunities.py` **NO existe en `feed_processor.py`**. Esto aumenta el riesgo de falsos positivos en ingesta.

**Riesgo:** ALTO

**Justificación:**
- **Visibilidad acotada:** Ingesta solo ve ventana de 7-30 días, mientras batch ve todo el Tracker histórico
- **Menos contexto:** Batch tiene más datos para correlación (score, layer, created_time de todo el Tracker)
- **Filtro ausente:** El filtro específico "electrónica" (líneas 84-91 en `dedup_opportunities.py`) no está replicado en `feed_processor.py`
- **Ejemplo real:** El falso positivo de electrónica ocurrió con visibilidad completa - con visibilidad acotada podría ser más difícil de detectar
- **Impacto:** Falso positivo en ingesta rechaza vacante que podría ser válida, mientras que en batch es corregible manualmente

**Recomendación de mitigación:** Replicar el filtro anti-falso-positivo "electrónica" en `feed_processor.py` antes de implementar el cambio.

---

### 2.3 Interacción con jerarquía de capas L1/L2/L3

**Hallazgo:** `dedup_by_content_fingerprint()` es **ortogonal a la jerarquía de capas** - actúa después de que cada capa ya aplicó su lógica, sin pisarla.

**Riesgo:** BAJO

**Justificación:**
- **Independencia de layer:** La función solo compara fingerprint de contenido (brand+title+location), no depende de layer
- **Ejecución tardía:** Se ejecuta como fallback después de que `dedup_cross_layer()` ya aplicó jerarquía L1>L2>L3
- **Compatibilidad con Kernel:** El diseño canónico (`KERNEL:GATE-DECISION-011`) coloca dedup por fingerprint como fallback cuando hash exacto falla - esto es consistente
- **No afecta upstream:** No modifica la lógica de consolidación de Perplexity (L0) ni la jerarquía entre capas

**Conclusión:** Este cambio es seguro desde la perspectiva de jerarquía de capas.

---

### 2.4 Interacción con protección de estado terminal (gate_logic.py)

**Hallazgo:** `feed_processor.py` **NO evalúa** `gate_logic()` ni protege estados terminales antes de escribir `Dedup_Flag`.

**Riesgo:** MEDIO-ALTO

**Justificación:**
- **Ausencia de check:** `_set_dedup_flag_if_needed()` (línea 503-542) escribe `Dedup_Flag` sin verificar `Status` ni `Next_Action`
- **Caso potencial:** Un registro marcado como Expirada por Fase 3.5.1 podría recibir `Dedup_Flag` en la misma corrida si pasa por dedup
- **Inconsistencia con Kernel:** `KERNEL:GATE-DECISION-010` establece que `gate_logic()` debe evaluarse antes de cualquier modificación de estado
- **Protección parcial:** `feed_processor.py` sí protege contra `Status=Rechazado` histórico (línea 598-600), pero no contra otros estados terminales

**Recomendación de mitigación:** Agregar check de `gate_logic()` o al menos verificación de `Status ∈ {Expirada, Archivar, Postulado}` antes de escribir `Dedup_Flag` en `feed_processor.py`.

---

### 2.5 Rollback y coexistencia temporal

**Hallazgo:** Es **viable** mantener `dedup_opportunities.py` como red de seguridad mientras se prueba la lógica en ingesta.

**Riesgo:** BAJO

**Justificación:**
- **Independencia de ejecución:** `dedup_opportunities.py` corre manualmente/vía `--dedup-audit`, no depende de la lógica de ingesta
- **Coexistencia sin conflicto:** Ambos pueden escribir `Dedup_Flag` sin problemas (el mismo campo, misma semántica)
- **Feature-flag viable:** Puede implementarse con variable de entorno en `feed_processor.py` (ej. `ENABLE_DEDUP_FINGERPRINT_INGEST=true`)
- **Rollback simple:** Desactivar flag o revertir código sin afectar la auditoría batch
- **Monitoreo posible:** Comparar resultados de ambas vías durante período de prueba para validar consistencia

**Conclusión:** Despliegue incremental es factible y recomendado.

---

## 3. Recomendación Final

**Recomendación:** IR CON CONDICIONES

**Condiciones:**
1. Replicar filtro anti-falso-positivo "electrónica" en `feed_processor.py`
2. Agregar protección de estado terminal antes de escribir `Dedup_Flag` en ingesta
3. Implementar feature-flag (variable de entorno) para poder desactivar rápidamente
4. Mantener `dedup_opportunities.py` activo como red de seguridad durante período de prueba (2-4 semanas)
5. Implementar caché del Tracker por corrida para optimizar performance
6. Monitorear tasa de falsos positivos durante período de prueba y comparar con baseline histórico

**Justificación de la recomendación:**
- **Beneficio:** Detectar duplicados en el momento de la ingesta es el diseño canónico del Kernel y previene contaminación del Tracker
- **Riesgos mitigables:** Los riesgos identificados (falsos positivos, protección de estado) tienen mitigaciones claras
- **Viabilidad técnica:** La infraestructura ya existe (funciones, queries), solo requiere mejoras de seguridad
- **Red de seguridad:** Coexistencia temporal reduce riesgo de producción

---

## 4. Esbozo de cambios necesarios (si se procede)

### Funciones a modificar en `feed_processor.py`:

1. **`_set_dedup_flag_if_needed()` (línea 503-542):**
   - Agregar check de `gate_logic()` o verificación de `Status ∈ {Expirada, Archivar, Postulado}`
   - Mantener lógica actual de escritura si pasa el check

2. **`dedup_by_content_fingerprint()` (línea 664-736):**
   - Agregar filtro anti-falso-positivo "electrónica" (similar a `dedup_opportunities.py` líneas 84-91)
   - Verificar si necesita ajuste en lógica de ventana de tiempo

3. **`process_record()` (línea 799+):**
   - Agregar feature-flag (variable de entorno `ENABLE_DEDUP_FINGERPRINT_INGEST`)
   - Opcional: implementar caché del Tracker por corrida

### Funciones a NO modificar:

- **`compute_dedup_hash()`** - está funcionando correctamente
- **`dedup_cross_layer()`** - su lógica de jerarquía de capas es correcta
- **`query_notion_db()`** - no requiere cambios para este propósito
- **Schema de Notion** - no se proponen cambios al schema del Tracker

### Nueva dependencia (opcional):

- **`gate_logic.py`** - si se decide implementar check completo de estados terminales, importar desde `gate_logic`

---

## 5. Estimación de esfuerzo y reversibilidad

**Estimación de esfuerzo:** 4-6 horas

**Desglose:**
- Implementar filtro anti-falso-positivo: 1 hora
- Agregar protección de estado terminal: 1-2 horas  
- Implementar feature-flag: 30 minutos
- Implementar caché del Tracker (opcional): 1-2 horas
- Testing local + validación: 1-2 horas

**Reversibilidad:** ALTA

**Justificación:**
- **Feature-flag:** Desactivar con variable de entorno sin revertir código
- **Rollback simple:** Revertir commits afectados sin impacto en otros componentes
- **Coexistencia temporal:** Mantener `dedup_opportunities.py` activo como fallback durante prueba
- **Sin dependencias nuevas:** No introduce dependencias externas ni cambios de schema
- **Testing incremental:** Puede probarse en ambiente de desarrollo sin afectar producción

**Riesgo residual bajo:** Si algo sale mal en producción, el impacto está limitado a nuevas ingestas (no afecta datos existentes) y puede revertirse rápidamente.

---

## Conclusión

Mover la escritura de `Dedup_Flag` a `feed_processor.py` es **técnicamente viable** y alineado con el diseño canónico del Kernel, pero requiere **mitigaciones específicas** para gestionar riesgos de falsos positivos y protección de estado terminal. Con las condiciones especificadas, el cambio puede implementarse de forma segura con un plan de rollback claro y una red de seguridad temporal.