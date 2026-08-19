# Feedback para Devin — Propuestas de mejora a scripts

Gracias por el inventario. Hay ideas útiles, pero el documento trata VANTAGE como un backend multi-servicio y no como lo que es: un pipeline de un solo operador, fail-closed, con contratos en Kernel. Varias propuestas ya existen, otras violan invariantes, y las de “prioridad alta” no están justificadas con evidencia de este repo.

Antes de implementar nada de Fase 1: responde las preguntas del final y re-prioriza contra el código real.

---

## 1. Veredicto

No implementar el plan de 4–6 semanas tal como está.

El análisis describe bien *qué hace* cada archivo a alto nivel, pero:

1. No inventarió infraestructura ya existente (`notion_utils`, `pipeline_recovery`, `feedback_loop`, `cv_a_prep`, `lru_cache` en `profile_fit`).
2. No cruzó las propuestas contra Kernel (`FAIL-PHILOSOPHY`, `GATE-DECISION-004/010`, `SCHEMA-001`).
3. Prioriza performance genérica (paralelo, Redis, ML, circuit breaker) sobre bugs y drift reales del sistema.
4. Confunde *existencia de un campo en Notion* con *ownership de escritura* (Class A/B).

ROI real de Fase 1 tal como está: bajo, y en dos casos (parallel writes + override de gates) es negativo.

---

## 2. Lo que ya existe (no reimplementar)

| Propuesta | Estado real |
|---|---|
| Adaptive backoff / retry en Notion | `notion_utils.py` ya tiene throttle `MIN_INTERVAL=0.35s`, `MAX_RETRIES=3`, backoff `2 ** attempt` en GET/POST/PATCH, y no reintenta 401. |
| Cache de Notion | Cache local con TTL 6h (`NOTION_CACHE_TTL`), persistido en `notion_cache.json`, con `clear-cache` / `metrics`. |
| Checkpointing | `pipeline_recovery.py` ya tiene `save_checkpoint` / `load_checkpoint` / `resume_pipeline`. El problema no es ausencia: el resume está *stubbed* (limpia y reinicia). |
| Feedback loop | `feedback_loop.py` ya calcula conversión por Score band, Source_Type y fit fields. |
| `cv_a_prep.py` | Ya existe. Genera scaffold HANDOFF + hard-block check. No es un script “nuevo”. |
| Cache de alias | `profile_fit._alias_data()` ya tiene `@lru_cache(maxsize=1)`. |
| Modo permisivo en `class_b_guard` | Ya existe: `strict_unknown=False` deja pasar desconocidos. `warn_mode` es el mismo flag con otro nombre. |
| Dry-run en batch / backfill | `batch_operations.py` es read-only sin `--execute`. `backfill_class_a.py` tiene `--dry-run` + confirmación `s/N`. |
| Logging de protecciones en gate | `gate_logic.py` ya loguea `PROTECTED: {id} → {value}` (fix D-004). |
| Métricas Notion | `notion_utils` ya persiste `requests_total`, `cache_hits/misses`, `retries`, `errors_by_status`. |

Si una propuesta no menciona el artefacto existente, no está lista para implementación.

---

## 3. Errores de lectura del código

### 3.1 Hay dos clientes Notion. El plan los trata como uno.

- `feed_processor.py` y `backfill_class_a.py` importan el SDK oficial (`notion_client.Client`) y *excluyen* a propósito `scripts/` del path para no tomar el wrapper local.
- `batch_operations.py`, Dashboard y varios scripts usan el wrapper `notion_utils.Client`.

Consecuencia: meter backoff en `feed_processor` y “cache Redis” en `notion_utils` no arregla el mismo camino. El rate limit tampoco se comparte entre procesos/clientes. Ese es el problema real; Redis no lo resuelve.

### 3.2 `batch_operations.py` no es un framework de batch.

Es un script de un solo propósito: `Status Target → Exploratorio`. El Kernel lo documenta así (`KERNEL:TRIGGER-002` / `vl1 batch`). Un dry-run con diffs, rollback JSON y progress bar asumen un orquestador que no existe. Si el operador no usa `vl1 batch --execute` de forma habitual, esta “prioridad alta” no tiene demanda.

### 3.3 `backfill_class_a.py` no es un job masivo recurrente.

Es catch-up de `layer` / `hash` / `Prioridad` sobre huecos. Ya es dry-run + confirmación. `query_notion_db` tiene `MAX_PAGES=20`. ThreadPool de 3 workers contra Notion (~3 req/s) no da 3–5x: da 429s. El claim de ROI “muy alto” no tiene medición (tamaño típico del backfill, duración actual, tasa de fallo).

### 3.4 `cv_b_prep.py` / `cv_validator.py` no caben como scripts deterministas.

CV-B y QA son skills de juicio (`KERNEL:CV-PIPELINE-002`, `KERNEL:TRIGGER-003`): Positioning Mode, Anti-cloning, Canon check, GO/NO-GO sobre PDF. Un script puede chequear presencia de campos del HANDOFF o conteo de `figma_text_id`. No puede “validar contra estándares VANTAGE” sin reimplementar Claude. `cv_a_prep.py` existe precisamente porque *esa* parte sí es determinista (hard block + scaffold).

### 3.5 Pydantic / structlog / sklearn / Redis / circuitbreaker.

Ninguno está en `Layer_1/requirements.txt` (`dotenv`, `requests`, `notion-client`, `pyyaml`, `pytest`). Cada dependencia nueva necesita justificación de operador-único, no de plataforma.

---

## 4. Propuestas que violan Kernel — no implementar

Estos no son “prioridad baja”. Son incompatibles con el contrato.

### 4.1 Override en `gate_logic.py`

`KERNEL:GATE-DECISION-004`: *“Un gate que puede sobreescribirse manualmente no es un gate — es una sugerencia.”*

`KERNEL:PURPOSE-001` #3: *“Gate decision no se sobreescribe manualmente. RT-1 permite corregir inputs Class A para que Python recalcule.”*

El camino canónico ya existe: corregir Class A → pipeline recalcula. Un `override=True` con reason es exactamente lo que el Kernel prohíbe.

### 4.2 Reglas de protección “customizables vía JSON/Notion”

`gate_logic.py` es la fuente ejecutable de `KERNEL:GATE-DECISION-010`. Las constantes están hardcoded *a propósito* y tienen 840 líneas de tests. Externalizarlas a JSON/Notion abre drift y bypass. Si hay que cambiar un terminal, se cambia el módulo + Kernel + tests en el mismo batch.

### 4.3 Schema dinámico desde Notion en `class_b_guard`

El propio módulo lo dice: sync manual con `KERNEL:SCHEMA-001`; no hay sync automático Notion → archivo.

Notion responde “qué propiedades existen”. El guard responde “quién puede escribirlas”. Cargar el schema vivo de Notion como Class A/B mezcla las dos cosas y puede promover un campo Class B a escribible porque “está en la DB”.

El drift real (ver §6) se resuelve alineando las tres listas canónicas, no leyendo Notion.

### 4.4 Modo permisivo / warn_mode como default de desarrollo

`KERNEL:FAIL-PHILOSOPHY` + el docstring del guard: *un guard que deja pasar lo desconocido no es un guard*. `strict_unknown=False` ya existe para casos explícitos. No ampliarlo ni hacerlo default.

### 4.5 ML para clasificar roles

`profile_fit.py` es un allow/deny determinista (regex + señales VM + hard_block de alias). El Kernel exige que Score/fit/exclusiones sean reproducibles. Un clasificador TF-IDF/Naive Bayes introduce no-determinismo, dependencia de entrenamiento y cero dataset etiquetado. Si un rol se cuela o se bloquea mal, se ajusta el patrón — no se entrena un modelo.

---

## 5. Propuestas con forma correcta pero mal priorizadas / mal ubicadas

### Adaptive backoff en `feed_processor`

Útil *solo* si hay 429s reales en el SDK oficial. No copiar otra implementación: o se unifica el cliente hacia `notion_utils` (que ya tiene backoff), o se configura el retry del SDK. No un tercer mecanismo.

Backoff propuesto `min(0.35 * 2^n, 5s)` es más agresivo que el de `notion_utils` (`2 ** attempt`, 2s / 4s / 8s). Unificar política, no divergir.

### Cache de URLs procesadas (`~/.vantage_cache/processed_urls.json`)

Dedup ya consulta Notion por hash, URL y brand+title (30d) + fingerprint. Un cache local de 7 días puede *ocultar* una URL que el operador quiere re-evaluar (REVIEW_NEEDED resuelto, JD nuevo, jk rotado). Si el dolor es N queries por vacante, la mitigación correcta ya está escrita en `EVALUACION_DEDUP_INGESTA.md`: **caché del Tracker por corrida en memoria**, no un JSON en home.

### Logging estructurado (structlog)

Aceptable más adelante con `logging` stdlib + JSON formatter. No nueva dependencia. Hoy el operador lee stdout de una corrida semanal, no un agregador.

### Rollback de backfill / batch

Razonable como *export del preview* (los valores que se van a escribir), no como sistema de rollback automático. Notion no es transaccional; un `batch_rollback.json` desactualizado es más peligroso que no tenerlo. El preview + confirmación ya cubren el caso de un operador único.

### Circuit breaker + Redis + histogramas p50/p95/p99

Fuera de escala. Un Mac, un operador, ~3 req/s, corridas semanales. Circuit breaker tiene sentido con N servicios y failover. Aquí el fallback es “reportar y esperar instrucción humana” (`FAIL-PHILOSOPHY-001`).

---

## 6. Trabajo de alto valor que el documento no menciona

Esto es lo que sí vale un ticket, en este orden.

### P0 — Contratos / correctness

1. **Bug en `infer_layer()`** (`backfill_class_a.py` ~L116): si Notas contiene `layer: l2`, retorna `("L3", "notas_layer")`. Debe ser L2. Hoy un backfill puede *escribir mal* el layer.

2. **Drift Class A/B entre tres fuentes de verdad:**

   | Campo | Kernel SCHEMA-001 | class_b_guard | Golden Rules-002 |
   |---|---|---|---|
   | `Positioning_Mode` | Class A | ausente | — |
   | `Last_Gate_Run` | Class B | ausente | ausente |
   | `Match` | no en SCHEMA-001 | Class B | protegido |
   | `JD_Quality` | no en SCHEMA-001 | Class B | protegido |
   | `Score_Method` | Class B | Class B | ausente |
   | Contacto, Notas, JOB_ID, Interview*, Apply/Rej Date, Outcome, Optimizar, Postular, Archivar, URL Notion | no en SCHEMA-001 | Class A | — |

   Acción: una tabla reconciliada Kernel ↔ guard ↔ Golden Rules, y un test que falle si `CLASS_A_FIELDS` / `CLASS_B_FIELDS` se desvían. No “cargar desde Notion”.

3. **`_set_dedup_flag_if_needed()` no consulta `gate_logic()`.** Puede marcar `Dedup_Flag` en registros terminales (Postulado / Rechazado / Expirada). Ya señalado en `EVALUACION_DEDUP_INGESTA.md` §2.4.

4. **Comentario stale en `feed_processor.write_to_notion`:** sigue diciendo “FX-1 open / MCP sin guard”. GAP-03 está cerrado (v9.19.2); el guard vive en `dashboard_notion.py`. El comentario miente.

### P1 — Performance real (sin infra nueva)

5. **Caché in-memory del Tracker por corrida de `feed_processor`.** Cada vacante dispara 2–4 queries Notion. Un batch de 20–50 vacantes = 40–200 calls. Precargar una vez y resolver hash/URL/fingerprint en proceso. Esto *sí* reduce rate-limit. Redis no.

6. **Unificar cliente Notion.** Decidir: o `feed_processor`/`backfill` pasan al wrapper (heredan throttle+retry+metrics), o el wrapper deja de existir como segundo camino. Hoy el backoff que propones no cubre el camino que más escribe.

7. **`pipeline_recovery.resume_pipeline()` está stubbed.** El Manual (`vl1 recovery`) promete retomar desde el paso fallido. El código limpia el checkpoint y reinicia. Completar el resume, o documentar que no existe. No crear un segundo sistema de checkpoints en `batch_operations`.

### P2 — Tests y drift documental

8. No hay tests de `feed_processor`, `class_b_guard`, `profile_fit`. `gate_logic` está bien cubierto. El siguiente test de más valor es `class_b_guard` vs Kernel (listas), no métricas in-memory de protecciones.

9. Drift documental que el plan no toca y sí opera el pipeline CV:
   - QA skill = 7 ítems; `KERNEL:TRIGGER-003` sigue diciendo 6.
   - Skill CV-A HANDOFF = 8 campos (`observaciones`); Kernel = 7.
   - `VANTAGE_ARCHITECTURE.md` marca `feed_processor` como “Pending (P1)” y describe un schema viejo.

---

## 7. Re-priorización (si se continúa)

Descartar Fases 3–4 (Redis, circuit breaker, ML, scripts auxiliares de CV) hasta que haya evidencia.

**Fase 1 real (días, no semanas):**

1. Fix `infer_layer` L2→L3.
2. Reconciliar Class A/B + test de contrato en `class_b_guard`.
3. Guard de terminalidad antes de escribir `Dedup_Flag`.
4. Caché in-memory del Tracker en `feed_processor` (con feature flag si se quiere).
5. Corregir comentario FX-1 / GAP-03.

**Fase 2 (solo con evidencia):**

6. Unificar cliente Notion.
7. Completar o recortar `pipeline_recovery`.
8. Tests de `feed_processor` (sanitize / envelope / hard_block / dispositions) sin red.

No entrar a parallel writes, override de gates, schema dinámico, ni dependencias nuevas.

---

## 8. Preguntas que necesito respondidas antes de APROBAR_WRITE

1. ¿Qué evidencia hay de 429s, backfills interrumpidos, o progreso perdido en las últimas 4–6 semanas? Logs, timestamps, tickets. Sin eso, Fase 1 original no tiene demanda.

2. ¿Mediste cuántas filas toca un `vl1 backfill` típico y cuánto tarda hoy? El “3–5x” necesita denominador.

3. ¿Notaste que `feed_processor` y `backfill` *no* usan `notion_utils`? Si sí, ¿por qué el backoff nuevo no vive en el cliente que ellos sí usan?

4. ¿Cómo reconciliás `gate_logic(..., override=True)` con `KERNEL:GATE-DECISION-004` y `PURPOSE-001` #3?

5. ¿Inventariaste `pipeline_recovery.py`, `feedback_loop.py`, `cv_a_prep.py` y el `lru_cache` de `profile_fit` antes de proponerlos como nuevos?

6. ¿Quién opera Redis en esta máquina, y qué proceso además de una corrida semanal de L1 se beneficiaría de cache distribuido?

7. Para `cv_validator.py`: ¿qué checks serían deterministas (campos presentes, count de `figma_text_id`) vs juicio (Canon, Anti-cloning, GO/NO-GO)? Si es lo segundo, no es un script.

8. `class_b_guard` declara sync *manual* con Kernel. ¿Por qué la fuente debería pasar a ser el schema vivo de Notion y no al revés (test que falle si el guard diverge del Kernel)?

---

## 9. Cómo quiero el siguiente entregable

No otro plan de 4 fases. Un documento corto:

- Hallazgos verificados contra archivo + línea (como en `EVALUACION_DEDUP_INGESTA.md`).
- Separación explícita: ya existe / bug real / mejora opcional / viola Kernel.
- Para cada ítem propuesto: evidencia de dolor (log, ticket, medición) o se baja a backlog.
- Cero dependencias nuevas salvo justificación de operador-único.
- Cualquier cambio a `gate_logic`, Class A/B o terminalidad trae test + ancla Kernel en el mismo batch.

El sistema no necesita más resiliencia de plataforma. Necesita menos drift entre contrato y código.
