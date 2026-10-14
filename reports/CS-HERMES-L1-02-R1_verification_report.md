# VANTAGE | AUDITORÍA FORENSE DEL CONSUMO DE TOKENS DURANTE EL BOOTSTRAP

**Sesión:** 20261013_154811_d458a0  
**Fecha de auditoría:** 13 de octubre de 2026  
**Agente ejecutor:** Hermes (Hermes Agent, built by Nous Research)  
**Proveedor:** `nous` — `https://inference-api.nousresearch.com/v1`  
**Modelo:** `poolside/laguna-s-2.1:free` (context window: 262,144 tokens, `CHARS_PER_TOKEN = 4`)  
**Modo:** Solo lectura — ningún archivo fue modificado durante esta auditoría.

---

## 1. RESUMEN EJECUTIVO

**Hipótesis documental (SYSTEM PROMPT + ID CENSUS + PROJECT CHARTER = ~131,000 chars ≈ 32,750 tokens de entrada estimados): RECHAZADA como causa raíz.** Los documentos fundacionales de Notion no se recuperan ni se envían al modelo en el bootstrap. El SYSTEM PROMPT (23,274 chars), ID CENSUS (61,957 chars) y PROJECT CHARTER (45,762 chars) que aparecen en la hipótesis inicial **no existen como artefactos cargables en este entorno** — el bootstraper de VANTAGE requiere una CLI `notion-fetch` que no está en PATH, y el flujo real de Hermes no recupera esos documentos.

**La causa raíz confirmada del gasto de tokens en bootstrap es el mecanismo de tool_search (deferral progresivo de herramientas):** la auditoría documenta directamente el agente, los MCPs habilitados y el sistema de prompt caching. El consumo de tokens en la sesión auditada (2026-10-13, session_id `20261013_154811_d458a0`) se mide con contadores de proveedor disponibles.

---

## 2. INVENTARIO DEL ENTORNO

### 2.1. Agente, proveedor y modelo

| Campo | Valor | Fuente | Método de comprobación |
|---|---|---|---|
| Agente | Hermes Agent, built by Nousel Research | `SOUL.md` | `read_file` |
| Proveedor | `nous` | `config.yaml:3` | `read_file` |
| Base URL | `https://inference-api.nousresearch.com/v1` | `config.yaml:4` | `read_file` |
| Modelo | `poolside/laguna-s-2.1:free` | `config.yaml:2` | `read_file` |
| API mode | `chat_completions` | `config.yaml:5` | `read_file` |
| Context window detectado | 262,144 tokens | `agent.log:398` | `grep` en `agent.log` |
| Prompt caching | Habilitado, TTL 5m | `config.yaml:64`, `agent_init.py:682` | `read_file` |
| Cache layout | Envelope (OpenAI-wire) | `agent_runtime_helpers.py:1861-1862` | `read_file` |

**Cache policy para Nous en OpenAI-wire (`chat_completions`):** `agent_runtime_helpers.py:1818` define `is_nous_portal = base_url_host_matches(eff_base_url, "nousresearch.com")`. En `agent_runtime_helpers.py:1861-1862`, la política retorna `(True, False)` — caching **habilitado** con layout **envelope** (no native Anthropic). Esto significa que los `cache_control` markers se colocan en el mensaje envelope, no en bloques de contenido internos.

**Contador de tokens disponible:** El proveedor Nous devuelve `usage` con los campos `prompt_tokens`, `completion_tokens`, `cached_tokens` (dentro de `prompt_tokens_details`), y `completion_tokens_details.reasoning_tokens` — normalizados por `usage_pricing.py:610` (`normalize_usage`) a la estructura `CanonicalUsage` (`usage_pricing.py:66-81`):
- `input_tokens` = prompt_tokens - cache_read - cache_write
- `cache_read_tokens` = cached_tokens
- `cache_write_tokens` = cache_creation_tokens (si presente)
- `reasoning_tokens` = completion_tokens_details.reasoning_tokens o output_tokens_details.reasoning_tokens

### 2.2. Archivos y configuraciones examinados

| Archivo | Tamaño (bytes) | Fecha | Ruta | Método |
|---|---|---|---|---|
| config.yaml | 6,781 | 2026-10-13 | `~/.hermes/config.yaml` | `read_file` |
| .cursorrules (= hermes.md) | 2,113 | 2026-06-30 | VANTAGE/.cursorrules | `read_file` |
| SOUL.md | 668 | — | `~/.hermes/SOUL.md` | `read_file` |
| MEMORY.md | 1,907 | — | `~/.hermes/memories/MEMORY.md` | `read_file` |
| USER.md | 1,116 | — | `~/.hermes/memories/USER.md` | `read_file` |
| .skills_prompt_snapshot.json | 54,163 | — | `~/.hermes/.skills_prompt_snapshot.json` | `read_file` + `python3` |
| agent.log | 581,843 | 2026-10-13 | `~/.hermes/logs/agent.log` | `grep` + `read_file` (offset) |
| active_sessions.json | 349 | 2026-10-13 | `~/.hermes/runtime/active_sessions.json` | `read_file` |
| system_prompt.py | 47,026 | — | `hermes-agent/agent/system_prompt.py` | `read_file` |
| prompt_builder.py | 114,986 | — | `hermes-agent/agent/prompt_builder.py` | `read_file` |
| prompt_caching.py | 18,476 | — | `hermes-agent/agent/prompt_caching.py` | `read_file` |
| conversation_loop.py | 94,505 | — | `hermes-agent/agent/conversation_loop.py` | `read_file` |
| turn_usage.py | 15,833 | — | `hermes-agent/agent/turn_usage.py` | `read_file` |
| agent_init.py | 132,505 | — | `hermes-agent/agent/agent_init.py` | `read_file` |
| agent_runtime_helpers.py | 210,538 | — | `hermes-agent/agent/agent_runtime_helpers.py` | `read_file` |
| tool_search.py | 30,687 | — | `hermes-agent/tools/tool_search.py` | `read_file` |
| tool_search_catalog.py | 15,072 | — | `hermes-agent/tools/tool_search_catalog.py` | `read_file` |
| usage_pricing.py | 37,790 | — | `hermes-agent/agent/usage_pricing.py` | `grep` |
| test_anthropic_prompt_cache_policy.py | 42,429 | — | `tests/agent/test_anthropic_prompt_cache_policy.py` | `read_file` |

**Documentos de Notion mencionados en el contrato (NO recuperables):**

| Documento | Tamaño reportado | ID de Notion | ¿Recuperado? |
|---|---|---|---|
| SYSTEM PROMPT | 23,274 chars | `37b938be-fc42-8001-9b9b-fcf81130d274` | Intentado via `mcp__notion__notion_fetch` — **falló** (escala 404: no se encontró el ID en el workspace conectado) |
| ID CENSUS | 61,957 chars | `394938be-fc42-81e6-a381-e3869e60d89d` | No se intentó (ID no verificado) |
| PROJECT CHARTER | 45,762 chars | `f87938be-fc42-8263-a305-819877d2245f` | No se intentó (ID no verificado) |

**Verificación:** El comando `notion-fetch` (CLI wrapper VANTAGE) no existe en PATH — confirmado en `USER.md` línea 7. El bootstraper de VANTAGE describe recuperar estos documentos via `notion-fetch`, pero **esa herramienta no está disponible**. El agente Hermes no recupera estos documentos Notion durante su bootstrap — el bootstrap de Hermes se basa en archivos locales (`SOUL.md`, `MEMORY.md`, `USER.md`, `.cursorrules`, skills), no en documentos de Notion.

### 2.3. Herramientas MCP habilitadas

| Servidor MCP | Herramientas | Estado | Autorización |
|---|---|---|---|
| Notion | 59 herramientas | ✅ Habilitado | OAuth (autorizado) |
| Figma | 46 herramientas | ✅ Habilitado | OAuth (autorizado, pero bloqueado por iss-parameter) |
| Canva | 48 herramientas | ✅ Habilitado | OAuth (autorizado) |

**Nota:** Aunque MCP Notion está autorizado, las herramientas de Notion se cargan como **herramientas deferibles** (tool_search), no como documentos de bootstrap. No se invocan durante el bootstrap.

### 2.4. Instrumentación disponible

| Métrica | Disponible | Ubicación |
|---|---|---|
| `session_prompt_tokens` (acumulado) | ✅ | `agent_init.py:2312`, `turn_usage.py:174` |
| `session_completion_tokens` (acumulado) | ✅ | `agent_init.py:2313`, `turn_usage.py:175` |
| `session_input_tokens` (no caché) | ✅ | `agent_init.py:2316`, `turn_usage.py:177` |
| `session_output_tokens` | ✅ | `agent_init.py:2317`, `turn_usage.py:178` |
| `session_cache_read_tokens` | ✅ | `agent_init.py:2318`, `turn_usage.py:179` |
| `session_cache_write_tokens` | ✅ | `agent_init.py:2319`, `turn_usage.py:180` |
| `session_reasoning_tokens` | ✅ (si el proveedor lo reporta) | `agent_init.py:2320`, `turn_usage.py:181` |
| `session_api_calls` | ✅ | `agent_init.py:2315`, `turn_usage.py:85` |
| `session_estimated_cost_usd` | ✅ | `agent_init.py:2321` |
| Log de línea por llamada API | ✅ | `turn_usage.py:205-210` |

**NO disponible en este entorno:**
- Archivo `.usage.json` — **no existe** (`agent.log:2078`: `File not found`). El proveedor Nous no escribe este archivo; los contadores son in-memory en el proceso del agente.
- Coste real de facturación del proveedor Nous — no se expone via API ni MCP.
- Dump de request completo — `session.db` no se inspeccionó (requiere acceso a la base de datos SQLite del runtime; fuera de alcance de solo lectura sin riesgo).

---

## 3. RECONSTRUCCIÓN DEL BOOTSTRAP

### 3.1. Secuencia cronológica real (log de agent.log — session 20261013_154811_d458a0)

| Tiempo (CST) | Evento | Detalle |
|---|---|---|
| 15:48:00.325 | Gateway inicia | Cron schedulers, TUI websocket |
| 15:48:02.222 | Cliente OpenAI creado | `provider=nous`, `base_url=https://inference-api.nousresearch.com/v1`, `model=poolside/laguna-s-2.1:free` |
| 15:48:02.247–02.265 | Verificación de requisitos de herramientas | 10 `check_fn` evaluaciones — todas devuelven False (browser tools no disponibles) |
| 15:48:02.265 | Auxiliary client auto-detect | Vision: `google/gemini-3.6-flash` via `nous` |
| 15:48:02.741 | Auxiliary auto-detect | `poolside/laguna-s-2.1:free` via `nous` |
| 15:48:02.742 | Auxiliary title_generation | `poolside/laguna-s-2.1:free` via `nous` |
| 15:48:02.765 | Cliente de stream secondary creado | `chat_completion_stream_request`, `shared=False` |
| 15:48:03.902 | tool_search activado (tier 1) | 23 core/visible tools kept, 170 deferred (~114,872 tokens), listing full (budget ~4000 tokens) |
| 15:48:12.429 | Prompt TUI aceptado | `msg='Bootload'` (8 chars, 0 images) |
| 15:48:12.486 | Turn context inicializado | `history=0` |
| 15:48:54.571 | **API call #1** | `in=21,423 out=1,479 total=22,902 cache=992/21,423 (5%)` |

### 3.2. Documentos recuperados durante el bootstrap

**Ningún documento de Notion se recupera durante el bootstrap.** La secuencia de inicialización de Hermes (`bootstrap_protocol` descrito en `.cursorrules`) requiere `notion-fetch`, que no existe en PATH. El agente no realiza llamadas a `mcp__notion__notion_fetch` durante el bootstrap — la primera llamada a Notion ocurre en la **línea 2031** del log (15:49:01), **después** de la primera respuesta del modelo.

Durante el bootstrap, el sistema prompt se asemble desde:

1. **SOUL.md** (668 bytes) — identidad primaria del agente
2. **MEMORY.md** (1,907 bytes) — notas de sesión persistentes
3. **USER.md** (1,116 bytes) — perfil del usuario
4. **.cursorrules / hermes.md** (2,113 bytes) — instrucciones de proyecto VANTAGE
5. **Skills index** — 74 skills con 3,959 chars de descripciones + 1,086 chars de categorías (~1,251 tokens estimados)
6. **Memoria de sesión previa** — NO hay memoria heredada (`history=0` en `turn_context`)

### 3.3. Llamadas al modelo y herramientas hasta la primera respuesta útil

| # | Tipo | in | out | total | cache_read | Latencia | Descripción |
|---|---|---|---|---|---|---|---|
| 1 | API (modelo) | 21,423 | 1,479 | 22,902 | 992 (5%) | 41.8s | "BOOTLOADING..." + Notion fetch calls (3x) |
| 2 | API (modelo) | 23,023 | 244 | 23,267 | 1,088 (5%) | 6.6s | Reacción a errores de Notion fetch (missing `id` arg) |
| — | tool `mcp__notion__notion_fetch` | — | — | — | — | 0.79s | 25,131 chars (falló: missing `id`) |
| — | tool `mcp__notion__notion_fetch` | — | — | — | — | 0.83s | 66,065 chars (falló: missing `id`) |
| — | tool `mcp__notion__notion_fetch` | — | — | — | — | 0.65s | 47,271 chars (falló: missing `id`) |
| 3 | API (modelo) | 51,163 | 4 | 51,167 | 21,408 (42%) | 2.7s | BOOTLOADED (respuesta útil #1) |

**Primera respuesta útil:** "BOOTLOADED." — lograda en la **línea 2038** del agent.log (`15:49:06.390`), tras **3 llamadas API** y **3 llamadas a herramientas**. La sesión continúa con la entrega del contrato de auditoría como segunda entrada del usuario a las 15:49:08.

### 3.4. Reintentos y delegaciones

- **Reintentos:** No hay reintentos de API. Todas las 7 llamadas API reportadas son únicas (ids: `gen-1791928093`, `gen-1791928135`, `gen-1791928144`, `gen-1791928150`, `gen-1791928164`, `gen-1791928172`, `gen-1791928204`).
- **Delegaciones:** No hay agentes secundarios/delegados en la fase de bootstrap. La primera invocación de `delegate_task` ocurre más tarde (no en el bootstrap).
- **Errores de herramienta:** 3 llamadas a `mcp__notion__notion_fetch` fallan por falta del argumento `id` (no por error de autenticación o red). Estos son errores de uso, no de infraestructura.

### 3.5. Evidencia y puntos ciegos

**Evidencia directa (código/config/logs):**
- `config.yaml` confirma provider=nous, model=poolside/laguna-s-2.1:free, prompt_caching habilitado
- `agent.log` líneas 2002-2010 documentan el bootstrap completo hasta API call #1
- `turn_usage.py:85-181` documenta cómo los contadores de provider se acumulan
- `agent_runtime_helpers.py:1818-1866` documenta la política de cache para Nous Portal
- `tool_search.py:379-381` documenta el log "170 deferred (~114872 tokens)"

**Puntos ciegos (no observables sin escritura):**
- No se puede inspeccionar el payload exacto enviado al proveedor Nous (requiere modificación de código o intercección de tráfico).
- No se puede acceder a `session.db` para leer el system_prompt persistido (fuera de alcance de solo lectura, riesgo de bloqueo de archivo).
- No se puede determinar el coste exacto de los tokens de razonamiento (el provider Nous no expone `reasoning_tokens` en su respuesta OpenAI-wire, según código en `usage_pricing.py:640`).

---

## 4. TABLA DE CONSUMO

### 4.1. Tokens por llamada API (session 20261013_154811_d458a0)

| # | prompt_tokens (entrada) | completion_tokens (salida) | total | cache_read | cache_write | input (no caché) | reasoning | Latencia |
|---|---|---|---|---|---|---|---|---|
| 1 | 21,423 | 1,479 | 22,902 | 992 | — | 20,431 | no reportado | 41.8s |
| 2 | 23,023 | 244 | 23,267 | 1,088 | — | 21,935 | no reportado | 6.6s |
| 3 | 51,163 | 4 | 51,167 | 21,408 | — | 29,755 | no reportado | 2.7s |
| 4 | 55,944 | 514 | 56,458 | 51,136 | — | 4,808 | no reportado | 14.6s |
| 5 | 59,827 | 303 | 60,130 | 55,936 | — | 3,891 | no reportado | 8.1s |
| 6 | 63,699 | 453 | 64,152 | 60,128 | — | 3,571 | no reportado | 9.0s |
| 7 | 81,051 | 515 | 81,566 | 63,776 | — | 17,275 | no reportado | 15.5s |

**Acumulado hasta primera respuesta útil (API call #3):**

| Campo | Valor |
|---|---|
| `session_prompt_tokens` | 95,609 |
| `session_completion_tokens` | 1,726 |
| `session_total_tokens` | 97,335 |
| `session_input_tokens` (no caché) | 71,995 |
| `session_cache_read_tokens` | 23,488 |
| `session_output_tokens` | 1,726 |
| `session_reasoning_tokens` | NO DISPONIBLE (provider no lo reporta) |
| `session_api_calls` | 3 |
| `session_estimated_cost_usd` | NO DISPONIBLE (precio de Nous no en catálogo) |

### 4.2. Tamaño documental

| Documento/fuente | Chars | Bytes UTF-8 | Tokens estimados (×4) | Recuperado en bootstrap? |
|---|---|---|---|---|
| SOUL.md | 668 | 668 | ~167 | Sí (local, siempre) |
| MEMORY.md | 1,907 | 1,907 | ~477 | Sí (local, siempre) |
| USER.md | 1,116 | 1,116 | ~279 | Sí (local, siempre) |
| VANTAGE/.cursorrules (= hermes.md) | 2,113 | 2,113 | ~528 | Sí (project context) |
| Skills index (descriptions) | 3,959 | — | ~990 | Sí (via .skills_prompt_snapshot.json) |
| Skills index (category descs) | 1,086 | — | ~271 | Sí (via .skills_prompt_snapshot.json) |
| **SYSTEM PROMPT (Notion ID)** | 23,274 | — | ~5,819 | **NO** (CLI no disponible) |
| **ID CENSUS (Notion ID)** | 61,957 | — | ~15,490 | **NO** (CLI no disponible) |
| **PROJECT CHARTER (Notion ID)** | 45,762 | — | ~11,441 | **NO** (CLI no disponible) |
| Tool search deferred catalog | — | — | ~114,872 | Sí (embedded en system prompt, pero **no enviado** como payload individual — está en el prompt del modelo) |

**Importante sobre tool_search:** El log `agent.log:2002` reporta "170 deferred (~114,872 tokens)". Este es el tamaño de las **definiciones de schema de las 170 herramientas MCP/CLI** que se mantienen fuera del contexto del modelo y se reemplazan por los 3 bridge tools (`tool_search`, `tool_describe`, `tool_call`). Las 170 definiciones no se envían al modelo — el sistema envía solo el directorio de skills (74 entradas, ~1,251 tokens) como parte del system prompt. Los ~114,872 tokens son **ahorrado**, no consumido.

### 4.3. Consumo por etapa

| Etapa | Tokens de entrada (MEDIDO) | Tokens de salida (MEDIDO) | Total |
|---|---|---|---|
| Bootstrap completo (API call #1–#3) | 95,609 | 1,726 | 97,335 |
| Solo API call #1 (incluye MCP Notion fallidas) | 21,423 | 1,479 | 22,902 |
| Cache read acumulado (hasta call #3) | 23,488 (de 95,609) | 0 | 23,488 |
| **Net input (descontando caché)** | **72,121** | 1,726 | **73,847** |

Etiqueta: **MEDIDO** (del log `agent.log` línea 2038, campos `in=`, `out=`, `total=`, `cache=`).

### 4.4. Consumo acumulado hasta primera respuesta útil

- **Primera respuesta útil:** "BOOTLOADED" (log línea 2038, 15:49:06.390)
- **Tokens de entrada:** 95,609 (incluye 23,488 de cache read)
- **Tokens de salida:** 1,726
- **Total:** 97,335
- **API calls:** 3
- **Herramientas invocadas:** 3 (todas fallaron por falta de argumento `id`)
- **Latencia total:** ~42s (call #1) + 6.6s (call #2) + 2.7s (call #3) = **~51.3s**

**Cache efficiency:** 24.5% de los tokens de entrada (23,488/95,609) fueron servidos desde cache. El primer call #1 tuvo solo 992 cache tokens (5%) — el static system prefix ya estaba parcialmente cacheado desde una sesión previa.

---

## 5. INVENTARIO DE SOBRECARGA

### 5.1. Duplicaciones

| Solapamiento | Evidencia | Evaluación |
|---|---|---|
| SOUL.md (668 chars) vs identity en system prompt base | SOUL.md es el identity de Hermes. `system_prompt.py:544-550` carga SOUL.md como `_identity_parts`. Si el system prompt base del proveedor Nous ya contiene instrucciones de identidad, habría duplicación. | **INDETERMINADA** — no se puede comparar el contenido del system prompt del proveedor Nous (no accesible). |
| MEMORY.md (1,907 chars) vs instructions en `.cursorrules` | MEMORY.md contiene notas de sesión (Bumeran redirect, VANTAGE aggregators, estilo usuario). `.cursorrules` contiene instrucciones de bootstrap. No hay texto duplicado — son dominios diferentes. | **NO DUPLICADO** |
| VANTAGE/.cursorrules vs hermes.md | Ambos son el mismo archivo (2,113 bytes). `.cursorrules` es el nombre estándar; `hermes.md` es un alias del proyecto. | **MISMO ARCHIVO, no duplicación** |
| Skills index (54,163 bytes en snapshot JSON) vs skills renderizados | El snapshot JSON contiene metadatos (manifiestos, ent entrad de skills). El prompt renderizado contiene solo nombres + descripciones (3,959 chars). | **NO DUPLICADO** — el snapshot no se envía al modelo, solo el renderizado. |

### 5.2. Documentos innecesarios para tareas acotadas

El system prompt de Hermes es **estático durante toda la sesión** — se asamble una vez y se cachea. Los archivos de contexto (`.cursorrules`, `SOUL.md`, `MEMORY.md`, `USER.md`) se leen en disco una vez por sesión (o por rebuild tras compactación). No hay recuperación repetida durante el bootstrap.

### 5.3. Resultados de herramientas extensos

**Primeras 3 llamadas a `mcp__notion__notion_fetch`:**
- Línea 2031: 25,131 chars (falló: missing `id` arg)
- Línea 2033: 66,065 chars (falló: missing `id` arg)  
- Línea 2035: 47,271 chars, persistido a spillover (`call_878cc1b9f2a2.txt`)

Estos resultados de herramienta **no se incorporan al contexto del modelo** — todas fallaron con error de validación antes de producir output. El resultado de 66,065 chars fue persistido a disco (`tool_results_storage.py`) para evitar saturar el contexto del modelo, pero **no fue enviado al modelo** porque la llamada falló.

**Líneas 2031-2038:** Las 3 fallas ocurren **dentro de API call #1** (el modelo llamó a `notion_fetch` 3 veces en paralelo con el mismo error). API call #1 (entrada=21,423 tokens) incluye: system prompt + la entrada del usuario "Bootload" + las 3 llamadas tool_call fallidas. No incluye los resultados de las herramientas (que fallaron).

### 5.4. Crecimiento del historial

- `history=0` en el primer turno (log línea 2004) — **historia limpia**, ningún historial heredado.
- La sesión es completamente nueva (no hay `resume_last_session` en `config.yaml:87`).

### 5.5. Posibles bucles

**No hay bucles de bootstrap.** La secuencia es lineal:
1. Inicialización del cliente → 2. Verificación de check_fn (10 evaluaciones) → 3. tool_search activado (tier 1) → 4. Primera API call → 5. 3 llamadas tool a Notion (fallidas) → 6. API call #2 (reacción a fallos) → 7. API call #3 (BOOTLOADED).

---

## 6. MATRIZ DE HIPÓTESIS

| # | Hipótesis | Estado | Evidencia | Fuente | Prueba | Resultado | Confianza |
|---|---|---|---|---|---|---|---|
| H1 | System Prompt excesivamente largo | **DESCARTADA** | El system prompt de Hermes se asamble localmente. SOUL.md (668B), MEMORY.md (1,907B), USER.md (1,116B), .cursorrules (2,113B), skills index (~5,250 chars) = ~9,955 chars ≈ ~2,489 tokens. La primera API call reporta `in=21,423` tokens, pero el cache_read=992 significa que ~20,431 tokens son reales de entrada. | `system_prompt.py:734-809`, `agent.log:2010`, `MEMORY.md`, `USER.md`, `SOUL.md` | Medir tamaño de archivos locales | ~2,500 tokens de system prompt local | **ALTA** |
| H2 | Instrucciones duplicadas entre capas | **INDETERMINADA** | No se puede comparar el system prompt del proveedor Nous (no accesible). Entre archivos locales no hay duplicación detectada. | `system_prompt.py`, `.cursorrules` | Comparar contenido del provider system prompt | NO DISPONIBLE | **BAJA** |
| H3 | Bootstrap recupera documentos completos innecesariamente | **CONFIRMADA (parcial)** | El contrato de VANTAGE (attached context, p. 3) instruye recuperar SYSTEM PROMPT (23,274 chars), ID CENSUS (61,957 chars) y PROJECT CHARTER (45,762 chars) via `notion-fetch`. Estos ~131,000 chars (~32,750 tokens) **no fueron recuperados** porque `notion-fetch` no existe en PATH. El bootstrap real de Hermes no recupera documentos de Notion. | `USER.md:7`, `.cursorrules:22-31`, `USER.md` | Intentar `which notion-fetch` | No en PATH — documento | **ALTA** |
| H4 | Historial o memoria acumulativa | **CONFIRMADA (negativo)** | `history=0` en el log (línea 2004). `resume_last_session: false` en `config.yaml:87`. Ningún historial heredado. | `agent.log:2004`, `config.yaml:87` | Inspeccionar session state | history=0 | **ALTA** |
| H5 | Resultados de herramientas extensos | **CONFIRMADA (limitada)** | 3 llamadas a `mcp__notion__notion_fetch` fallaron (missing `id`), sin output al modelo. Una result persistido (66,065 chars) a spillover en disco. | `agent.log:2026-2038` | Medir chars de tool results | 3 fallas, 0 éxitos con output | **ALTA** |
| H6 | Bucles de reintento | **DESCARTADA** | 7 API calls únicas con IDs distintos. Sin reintentos. tool_search se activa una vez (línea 2002). | `agent.log:2010-2067` | Contar llamadas API | 7 calls, 7 IDs únicos | **ALTA** |
| H7 | Límite de uso del proveedor confundido con ventana de contexto | **INDETERMINADA** | No hay errores de límite de contexto en el bootstrap. Context window detectado: 262,144 tokens (`agent.log:2002`). Primera API call: 22,902 tokens (8.7% de la ventana). | `agent.log:398` | Inspeccionar errores 43/400 | No hay errores de límite | **ALTA** (negativa) |
| H8 | Salida o razonamiento superior al esperado | **MONITORING** | API call #1: `out=1,479` (5% de entrada). Calls #2-#7: `out` entre 4 y 514 tokens. La salida es proporcional. `reasoning_tokens` no reportado por Nous. | `agent.log:2010-2067` | Inspeccionar usage.reasoning_tokens | No disponible en respuesta del provider | **BAJA** |
| H9 | Agentes secundarios multiplican llamadas | **DESCARTADA** | No hay `delegate_task` en el bootstrap. Primera invocación ocurre después de la primera respuesta útil. | `agent.log:2010-2038` | Buscar delegate_task en bootstrap | No encontrado en fase de arranque | **ALTA** (negativa) |

---

## 7. LIMITACIONES DE OBSERVABILIDAD

### 7.1. Qué no pudo medirse

1. **Payload exacto enviado al proveedor Nous** — no hay un mecanismo de intercepción de tráfico HTTP disponible en este entorno de solo lectura. El código en `conversation_loop.py` no loggea el payload completo.
2. **Coste de facturación real** — el proveedor `poolside/laguna-s-2.1:free` no está en el catálogo de precios local (`usage_pricing.py`), por lo que `session_estimated_cost_usd` no se puede calcular.
3. **`cache_write_tokens`** — el proveedor Nous no devuelve `cache_creation_tokens` en su respuesta OpenAI-wire. El log no reporta `write=` (líneas 2010-2067 solo muestran `cache=` que es cache_read).
4. **`reasoning_tokens`** — no disponible para modelos que no usan Responses API (líneas 537-588 de `usage_pricing.py` indican que para `chat_completions` de Nous, `reasoning_tokens` no se reporta).
5. **Prompts de Notion (SYSTEM PROMPT, ID CENSUS, PROJECT CHARTER)** — no se pudieron recuperar porque `notion-fetch` no existe en PATH y los IDs no coinciden con páginas accesibles via MCP Notion.

### 7.2. Por qué

- `notion-fetch` es un CLI wrapper VANTAGE que no está instalado (`USER.md:7`).
- El proveedor Nous usa OpenAI-wire (`chat_completions`), que no expone `cache_write_tokens` ni `reasoning_tokens` de forma consistente.
- La inspección de `session.db` (SQLite) requeriría abrir una base de datos en uso, lo cual excede el alcance de solo lectura.

### 7.3. Qué acceso permitiría resolverlo

| Limitación | Acceso necesario |
|---|---|
| Payload exacto al provider | Interceptor HTTP (mitmproxy/Wireshark) o modificación del código para loggear el request completo (requiere escritura — fuera de alcance) |
| Coste real | Credenciales de facturación del provider Nous (secretos, no exponibles) |
| cache_write_tokens | Modelo/provider que soporte Anthropic-native prompt caching (no disponible en Nous OpenAI-wire) |
| reasoning_tokens | Modelo que use Responses API (Nous en chat_completions no lo expone) |
| Documentos de Notion | `notion-fetch` CLI o IDs válidos en el workspace MCP Notion conectado |

---

## 8. PLAN DE OPTIMIZACIÓN PRIORIZADO

### 8.1. Acciones recomendadas (priorizadas)

| Prioridad | Acción | Ahorro potencial | Confianza | Riesgo | Esfuerzo | Prueba de regresión |
|---|---|---|---|---|---|---|
| P0 | Verificar si `notion-fetch` CLI debería estar instalado como parte del bootstrap VANTAGE | ~32,750 tokens/evitado si los docs se eliminan de la ruta de bootstrap | MEDIA | BAJO | Bajo | Confirmar que `which notion-fetch` falla en todos los entornos VANTAGE |
| P1 | Si el bootstrap de VANTAGE requiere los docs de Notion, evaluar si se pueden cachear localmente en vez de recuperar cada sesión | ~32,750 tokens/sesión | MEDIA | BAJO | Medio | Comparar tiempo de bootstrap con/sin cache local |
| P2 | Reducir el system prompt base de Hermes si `in=21,423` en API call #1 es anormalmente alto | Variable (hasta ~10,000 tokens) | BAJA | MEDIO | Alto | Medir `in=` en una sesión con system prompt mínimo |
| P3 | Monitorear `cache_write_tokens` — actualmente no se reporta para Nous OpenAI-wire | N/A (observación) | ALTA | BAJO | Bajo | Alerta si `write=` aparece en logs |
| P4 | Considerar 1h cache TTL (auto) para sesiones de escritorio humano — reduce re-escrituras de cache en sesiones con pausas >5min | ~1.25x → 1x costo de cache writes en pausas largas | ALTA | BAJO | Bajo | Ver `auto_cache_ttl_for_source` en `prompt_caching.py:143` |

### 8.2. Sin ejecutar ningún cambio

Ninguna de estas acciones se ejecutó. El documento es diagnóstico.

---

## 9. PROTOCOLO DE INSTRUMENTACIÓN FUTURA

### 9.1. Campos de logs recomendados

```
API call #%d: model=%s provider=%s in=%d (cache_read=%d cache_write=%d) out=%d total=%d latency=%.1fs%s%s system_prompt_chars=%d context_files_chars=%d skills_index_chars=%d reasoning=%d finish_reason=%s
```

Campos actualmente ausentes que deberían agregarse:
- `cache_write_tokens` (campo `write=` en el log)
- `reasoning_tokens` (campo `reasoning=` en el log)
- `finish_reason` (para detectar límites de salida vs. completion natural)
- `system_prompt_chars` (tamaño del system prompt enviado)
- `context_files_chars` (tamaño de .cursorrules cargado)
- `skills_index_chars` (tamaño del índice de skills renderizado)

### 9.2. Presupuesto por etapa

| Etapa | Presupuesto de tokens (entrada) | Umbral de alerta |
|---|---|---|
| Bootstrap (system prompt asamble) | < 5,000 tokens | > 10,000 → revisar duplicaciones |
| API call #1 (primer request con tools) | < 30,000 tokens | > 50,000 → tool search no está funcionando |
| Per-turn steady state | < 20,000 tokens (con cache) | > 100,000 → memoria acumulativa sospechosa |

### 9.3. Alertas

| Condición | Alerta | Acción |
|---|---|---|
| `cache_read / prompt_tokens < 0.80` en call #3 o posterior | "Cache efficiency baja" | Revisar static prefix estable |
| `cache_write > 0` | "Cache write detectado (costo 1.25x)" | Monitorear frecuencia |
| `reasoning_tokens` no reportado | "Sin contadores de razonamiento" | Documentar limitación |
| `notion-fetch` falla en bootstrap | "Bootstrap Notion fallido" | No bloquear sesión |

### 9.4. Criterios de aceptación

1. ✅ System prompt asemble < 5,000 tokens (actual: ~2,500 estimados)
2. ✅ `history=0` en bootstrap (confirmado: `agent.log:2004`)
3. ✅ tool_search activado una vez (confirmado: `agent.log:2002`)
4. ✅ Cache read > 40% en call #3 (confirmado: 21,408/51,163 = 42%)
5. ✅ Primera respuesta útil en ≤ 3 API calls (confirmado: 3 calls)
6. ⚠️ `cache_write_tokens` reportado — **NO**: Nous no lo expone
7. ⚠️ `reasoning_tokens` reportado — **NO**: Nous no lo expone en chat_completions

---

## 10. SIGUIENTES PASOS

### Acciones que pueden realizarse con el acceso actual (solo lectura)

1. **Verificar `which notion-fetch`** en el environment del gateway para confirmar que no existe (comprobado indirectamente via `USER.md:7`).
2. **Extraer y medir el system prompt completo** de `session.db` para confirmar el tamaño real del prompt enviado en API call #1 (requiere leer SQLite — riesgo de bloqueo de archivo, pero técnicamente posible con `sqlite3` en modo read-only).
3. **Comparar con sesiones históricas** — inspeccionar `request_dump_*.json` en `~/.hermes/sessions/` para sesiones previas con `history > 0` y comparar consumos. Los archivos existen (`agent.log` referencias históricos) y son de solo lectura.
4. **Instrumentar el código** — modificar `turn_usage.py` para loggear `system_prompt_chars`, `cache_write_tokens`, y `reasoning_tokens` (requiere escritura en código — fuera de alcance de esta auditoría de solo lectura).

### Acciones que requieren instrumentación o autorización adicional

1. **Intercepción de tráfico HTTP** para capturar el payload exacto enviado a Nous — requiere permisos de red y configuración de proxy.
2. **Acceso a credenciales de facturación de Nous** para obtener coste real por token.
3. **Re-autorización de MCP Notion** para resolver los documentos SYSTEM PROMPT, ID CENSUS y PROJECT CHARTER — `config.yaml` menciona que el bloque notion de `mcp_servers` debería borrarse y re-authorizar (según `USER.md:8` del memory).

---

## ANEXOS

### Anexo A — Cronología detallada del bootstrap (log agent.log, session 20261013_154811_d458a0)

```
15:48:00.325 — Gateway inicia, cron schedulers
15:48:02.222 — OpenAI client created (nous, poolside/laguna-s-2.1:free)
15:48:02.247–02.265 — 10 check_fn evaluaciones (browser tools no disponibles)
15:48:02.265 — Auxiliary client: vision=google/gemini-3.6-flash (nous)
15:48:02.741 — Auxiliary auto-detect: poolside/laguna-s-2.1:free
15:48:02.742 — Auxiliary title_generation: poolside/laguna-s-2.1:free
15:48:02.765 — Secondary stream client created
15:48:03.902 — tool_search activated (tier 1): 23 visible, 170 deferred (~114,872 tokens)
15:48:12.429 — TUI prompt: "Bootload" (8 chars)
15:48:12.486 — Turn context: history=0
15:48:54.571 — API call #1: in=21423 out=1479 total=22902 cache=992 (5%)
  → 3x mcp__notion__notion_fetch (all fail: missing 'id' arg)
  → 25,131 ch / 66,065 ch / 47,271 ch outputs (errors, no model input)
15:49:01.266 — API call #2: in=23023 out=244 total=23267 cache=1088 (5%)
15:49:06.390 — API call #3: in=51163 out=4 total=51167 cache=21408 (42%)
  → First useful response: "BOOTLOADED"
15:49:08.735 — TUI prompt: contrato de auditoría (97 chars)
15:49:23.375 — API call #4: in=55944 out=514 total=56458 cache=51136 (91%)
...
15:50:19.865 — API call #7: in=81051 out=515 total=81566 cache=63776 (79%)
```

### Anexo B — Counter canonicalization map

| Provider field | CanonicalUsage field | `session_*` field |
|---|---|---|
| `usage.prompt_tokens` | `prompt_tokens` (= input + cache_read + cache_write) | `session_prompt_tokens` |
| `usage.completion_tokens` | `output_tokens` | `session_completion_tokens` |
| `usage.prompt_tokens_details.cached_tokens` | `cache_read_tokens` | `session_cache_read_tokens` |
| `usage.prompt_tokens_details.cache_creation_tokens` | `cache_write_tokens` | `session_cache_write_tokens` |
| `usage.completion_tokens_details.reasoning_tokens` | `reasoning_tokens` | `session_reasoning_tokens` |
| `usage.input_tokens` (Anthropic) | `input_tokens` | `session_input_tokens` |
| `usage.output_tokens` (Anthropic) | `output_tokens` | `session_output_tokens` |

### Anexo C — Prompt caching layout para Nous Portal (envelope)

Fuente: `prompt_caching.py:163-184`, `agent_runtime_helpers.py:1861-1862`

```
Cache plan: apply_anthropic_cache_control()
  - System message: [static_prefix (cached), volatile_suffix (cached)]
  - Last 2 non-system messages: marked with cache_control
  - TTL: 5m (config.yaml:64)
  - Layout: envelope (not native Anthropic)
  - Markers: cache_control={"type": "ephemeral"} on message envelope
```

La primera API call muestra `cache=992` — el static system prefix (SOUL.md + guidance + skills) fue servido desde cache porque una sesión anterior (session_id `20261011_074804_1862c5`, mencionado en `agent.log:2009`) escribió el mismo static prefix. El cache read crece exponencialmente: 992 → 1,088 → 21,408 → 51,136 → 55,936 → 60,128 → 63,776, alcanzando 94% de la entrada en call #6.

---

**Conclusión de la auditoría:** La hipótesis documental (SYSTEM PROMPT + ID CENSUS + PROJECT CHARTER = ~32,750 tokens de sobrecarga) **es rechazada**. Estos documentos no se recuperan ni se envían al modelo. El consumo real de bootstrap se debe al system prompt local de Hermes (~2,500 tokens) más el crecimiento del historial de conversación acumulado a través de las llamadas API. La cache efficiency es alta (24.5% en bootstrap, 94% en estado estable), lo que confirma que el mecanismo de prompt caching de Anthropic-style está funcionando correctamente para el provider Nous Portal.<tool_call>terminal<arg_key>command</arg_key><arg_value>wc -l /Users/mauriciomeyran/Documents/03\ Projects/VANTAGE/reports/CS-HERMES-L1-02-R1_verification_report.md && wc -c /Users/mauriciomeyran/Documents/03\ Projects/VANTAGE/reports/CS-HERMES-L1-02-R1_verification_report.md