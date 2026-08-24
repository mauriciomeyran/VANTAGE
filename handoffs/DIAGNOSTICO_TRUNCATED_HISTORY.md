# Diagnóstico — "Truncated agent history (111 chars)"

**Fecha:** 2026-08-19 · **Estado:** causa raíz identificada y probada · Branch `arena/01a01a41-vantage`

---

## Resumen

El bug **no** era el bug no determinista de watchdogs de `browser-use`, ni
`browser_max_steps` bajo. Eran **dos defectos de nuestro propio código** que
se combinaron para ocultar el error real:

1. `main.py` silenciaba **todos** los logs (por eso "no había logs").
2. `_history_to_text()` reportaba el log de navegación **como si fuera el
   resultado** del agente (por eso el mensaje decía "truncated" en vez del error).

Ambos están corregidos y cubiertos con tests.

---

## Hipótesis del handoff — verificación

| Hipótesis | Veredicto |
|---|---|
| `browser_max_steps` bajo (ej. 1) | **Descartada.** Default 70; `.env.example` 70. El diagnóstico ahora lo imprime. |
| Bug no determinista de watchdogs | **Descartada.** El fallo es determinista y reproducible byte a byte. |
| Falta de verbosidad de logging | **Confirmada como síntoma, con otra causa** — ver Causa Raíz A. |
| LLM decide "done" prematuro | **Descartada.** `is_done()` es `False`; el agente nunca terminó. |
| Banner/modal de LinkedIn | **Descartada.** La navegación tiene éxito; fallan los pasos de razonamiento. |

---

## Causa Raíz A — los logs estaban silenciados dos veces

`main.py` hacía:

```python
logging.basicConfig(level=logging.CRITICAL, force=True)   # línea ~33
sys.stderr = open(os.devnull, 'w')                        # en main()
```

`browser-use` loguea a través del **root logger**. Ponerlo en `CRITICAL` apaga
sus `INFO`, `DEBUG`, `WARNING` **y `ERROR`**. Además, `setup_logging()` de
`browser-use` hace *early-return* si el root ya tiene handlers:

```python
if logging.getLogger().hasHandlers() and not force_setup:
    return logging.getLogger('browser_use')
```

Como `basicConfig` ya instaló uno, `BROWSER_USE_LOGGING_LEVEL=debug` **nunca
tuvo efecto**. Verificado:

```
root level: CRITICAL
Would an ERROR log be emitted? False
```

Esto explica exactamente por qué `2>&1 | tee` y el modo debug no revelaron nada:
no era falta de verbosidad, los logs se estaban descartando activamente.

**Fix:** logs van a `stderr` en nivel `INFO` (configurable con `SCOUT_LOG_LEVEL`).
`stdout` sigue siendo JSON puro. `SCOUT_QUIET=1` restaura el silencio anterior.

---

## Causa Raíz B — reportábamos el log de navegación como resultado

En `browser-use` 0.11.13:

- `final_result()` → devuelve contenido **solo si el agente llamó `done`**.
- `extracted_content()` → devuelve **todas** las acciones intermedias.

El código viejo probaba una y luego la otra:

```python
for attr in ("final_result", "extracted_content"):   # ← el fallback es el bug
```

Cuando el agente fallaba en cada paso, `final_result()` era `None` y caíamos a
`extracted_content()`, que devolvía la lista con la única acción exitosa: la
navegación inicial. `str()` de esa lista mide **exactamente 111 caracteres**:

```
['🔗 Navigated to https://www.linkedin.com/jobs/search/?keywords=Visual%20Merchandising&location=Mexico%20City']
```

Reproducido byte a byte en `tests/test_agent_history_diagnostics.py`. Los 3
intentos fallaban idénticamente porque la causa era determinista, tal como
sospechaba el handoff.

Mientras tanto, `history.errors()` contenía el error real de cada paso, y nunca
lo leíamos.

**Fix:** `_history_to_text()` ya no hace fallback. Se añadió `summarize_history()`
que expone `is_done / is_successful / has_errors / errors / number_of_steps`, y
el audit_log ahora incluye el error real en vez de "truncated history".

---

## Causa Raíz C (probable, del entorno) — nombre de modelo inválido

`browser_max_steps` era 70, así que el agente tenía pasos de sobra: los gastó
fallando. `Agent._verify_and_setup_llm()` en 0.11.13 es un **stub vacío**:

```python
def _verify_and_setup_llm(self):
    if getattr(self.llm, '_verified_api_keys', None) is True or CONFIG.SKIP_LLM_API_KEY_VERIFICATION:
        setattr(self.llm, '_verified_api_keys', True)
        return True
    # …no valida nada más
```

Es decir, un modelo inexistente **no falla al arrancar**: falla en cada paso con
404 hasta agotar `max_failures`, dejando en la historia solo la navegación.

Confirmar en el equipo del operador con:

```bash
python3 tools/diagnose_agent_run.py --wrapper Prompt_LinkedIn --config-only
```

Nota adicional: si `LLM_COST_LIMIT < 1.0`, `build_llm()` cambiaba silenciosamente
a `gemini-1.5-flash`, **descontinuado** — reproduce este mismo bug. Ahora emite
un `WARNING` explícito.

---

## Cambios

| Archivo | Cambio |
|---|---|
| `main.py` | Logs a `stderr` en vez de descartarse; `stdout` sigue siendo JSON puro. `SCOUT_QUIET=1` opcional. |
| `src/browser_agent.py` | `_history_to_text()` sin fallback engañoso; nuevo `summarize_history()`; `preflight_llm()` falla rápido y sin reintentos; warning en el fallback barato. |
| `tools/diagnose_agent_run.py` | Script de diagnóstico de un solo intento (reemplaza el one-liner del handoff). |
| `tests/test_agent_history_diagnostics.py` | 8 tests, incluida la reproducción exacta de los 111 chars. |

Tests: 22 passing (antes 14). Los 5 fallos restantes son **preexistentes** y
ajenos a esta cadena (mocks desactualizados en `test_llm_providers.py` que
parchean `_chat_openai` / `langchain_google_genai`, ya no usados tras migrar a
las clases nativas de `browser-use`; y una ruta hardcodeada `vantage_scout/` en
`test_cli_dry_run`).

---

## Adenda — Ollama local (pendiente del handoff original)

El handoff pedía dejar el proveedor en **Ollama local** y en la primera pasada
quedó en Gemini. Corregido, y al hacerlo apareció un bug adicional:

**La rama de Ollama nunca habría funcionado.** `build_llm()` llamaba:

```python
ChatOllama(model=..., base_url=..., temperature=0)
```

Pero en `browser-use` 0.11.13 `ChatOllama` es un `@dataclass` con exactamente
`(model, host, timeout, client_params, ollama_options)`. Verificado:

```
current repo call FAILS -> ChatOllama.__init__() got an unexpected keyword argument 'base_url'
```

No existe `base_url` ni `temperature`. El primer intento de usar Ollama habría
muerto con `TypeError` antes de abrir el navegador. Además el import era
`from browser_use.llm.ollama import ChatOllama`, que tampoco resuelve — la clase
vive en `browser_use.llm.ollama.chat`.

Correcciones:

- `LLM_PROVIDER` default → `ollama` (antes `gemini`).
- `ChatOllama(model=..., host=..., timeout=..., ollama_options={"temperature": 0})`.
- Nuevo `OLLAMA_TIMEOUT` (default 300s): la inferencia local es lenta y el timeout
  por defecto de httpx aborta pasos legítimos a medio camino.
- El preflight, si el proveedor es Ollama, indica `ollama serve` / `ollama pull`
  en vez de hablar de API keys.
- `requirements.txt`: se añade el SDK `ollama` (que es lo que importa `ChatOllama`)
  y se retiran los paquetes `langchain-*`, que ya no se usan tras migrar a las
  clases nativas de `browser-use`. `browser-use` queda pineado a `==0.11.13`.

4 tests nuevos corren contra la librería real y fallarían si alguien reintroduce
`base_url=`/`temperature=`.

**Nota sobre el modelo:** `qwen2.5vl:7b` es de visión, que es lo correcto —
el agente navega a partir de screenshots (`use_vision=True`). Si se cambia a un
modelo sin visión, el agente queda ciego. Confirma con `ollama list` que lo
tienes descargado.

---

## Siguiente paso para el operador

```bash
ollama serve                      # en otra terminal, si no corre ya
ollama list                       # confirma que qwen2.5vl:7b está descargado
python3 tools/diagnose_agent_run.py --wrapper Prompt_LinkedIn --config-only
```

No abre el navegador. Imprime `browser_max_steps`, el proveedor y modelo
efectivos, y prueba el LLM con un prompt trivial. Si el preflight pasa, corre sin
`--config-only` para la corrida real con logs visibles.

Si tu `.env` tiene `LLM_PROVIDER=gemini` escrito explícitamente, sobreescribe el
nuevo default — cámbialo a `ollama` (o bórralo) para usar el modelo local.
