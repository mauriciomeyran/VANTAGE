# AUDITORÍA FORENSE L0 — Runtime de Observabilidad + Lazy Loader

**Fecha:** 2026-09-22 · **Auditor:** agente Arena (arquitectura de sistemas de IA / infraestructura de agentes autónomos)
**Rama auditada:** `arena/01a0c6c6-vantage` @ `85ec3d9` (auto-sync 2026-09-21 19:38)
**Alcance:** capa L0 (vantage.py, agent_api.py, lazy_loader.py, resolver/query/context/graph layers, resolver_registry_v2.json, entity_index_v2.json, graph_v2.json, backlinks_v2.json) + capa de gobernanza documental (Kernel, Manual, System Prompt, Aliases, triggers.json, .hermes.md, manifiestos MCP).

## Declaración de acceso (qué se leyó y qué NO)

| Fuente | Estado |
|---|---|
| `Layer_1/scripts/lazy_loader.py`, `vantage.py`, `agent_api.py`, `resolver_layer_v1.py`, `query_layer.py`, `context_layer.py`, `graph_layer.py`, `notion_utils.py`, `generate_entity_index_v2.py`, `runtime_identity.py`, `update_triggers_json.py`, `verify_versions.py`, `health_check.py`, `layer_1_orchestrator.py`, `allocate_vantage_serial.py`, `mcp_vantage_serial_server.py` | ✅ leídos (completos o las secciones relevantes) |
| `Layer_1/data/*.json` (índice, registry, grafo, backlinks) | ✅ leídos y **validados programáticamente** (parse, conteo de colisiones, ejecución offline de `_get_authorized_prefixes()` y `_parse_route()`) |
| `Documentación/ACTIVE/` (Kernel, Manual, System Prompt, Aliases, Change Log, Changelog Archivo, .vsync_manifest.json) | ✅ leídos (secciones L0/bootstrap/triggers/glosarios) |
| `skills/triggers.json` (28 skills), `.hermes.md`, `.vscode/mcp.json`, `.devin/config.json`, `tools/claude-desktop-mcp-extension/` | ✅ leídos y parseados |
| Notion en vivo (Kernel/Manual/Tracker reales) | ❌ **sin acceso** — no existe `NOTION_TOKEN` en este entorno. Todo hallazgo sobre comportamiento contra la API se fundamenta en código + mirrors del repo |
| Tests | ✅ inventario completo — **no existe `test_lazy_loader.py`** en `Layer_1/tests/` ni `tests/` |

**Convención de citas:** `archivo:línea` o `archivo:función`. Los experimentos offline ejecutados en esta auditoría se marcan como **[EJECUTADO]**.

---

## 1. Mapa de Flujo Punta a Punta (Runtime + Lazy Loader)

### 1.0 Aclaración estructural previa: hay DOS flujos L0, no uno

El sistema llama "Runtime" a un complejo que en realidad son **dos pipelines con SSOT compartido pero stacks HTTP distintos**:

| | **Flujo Documental (Lazy Loader)** | **Flujo de Entidades (Runtime Build + Resolver)** |
|---|---|---|
| Entrada | `PREFIX:CLAVE` (ej. `MANUAL:SETUP`) | `PREFIX:H_xxxx` / `PREFIX:U_xxxx` (ej. `TRACKER:H_93a9…`) |
| Script | `lazy_loader.py` v2.1 | `vantage.py` → `query_layer` → `resolver_layer_v1` → `context_layer` |
| Namespace SSOT | `resolver_registry_v2.json → document_registry` | `resolver_registry_v2.json → data_sources` (+ `entity_index_v2.json`) |
| Stack HTTP | `requests` directo, headers propios, `Notion-Version: 2022-06-28` **hardcodeado** (`lazy_loader.py:227`) | Mixto: `notion_utils.py` (env `NOTION_VERSION`, default `2022-06-28`, cache 6h, throttle 0.35s, retry, métricas) + `resolver_layer_v1._query_notion()` (raw `requests`, default **`2025-09-03`**, `resolver_layer_v1.py:67`, **sin cache**) |
| Contrato | `KERNEL:DOC-CONTRACT` **(⚠️ sección inexistente en el Kernel vivo — ver §4-F16)** | `KERNEL:SCHEMA-005` (4 pasos) + `KERNEL:DOCUMENTATION-003` |

Esta bifurcación es la raíz de varias deudas que se detallan en §4.

### 1.1 Trazabilidad E2E — Ruta Documental: `MANUAL:SETUP`

1. **Solicitud:** agente u operador necesita la sección de setup. La política (MANUAL:LAZY-LOAD, `Manual.md:798-803`) manda Prioridad A = Terminal.
2. **Resolución de página:** el agente obtiene el UUID del Manual desde `SP:DIGITAL-ID-CARD` (`System Prompt.md`, tabla §03: `MANUAL DE USUARIO → 372938be-fc42-8050-9a67-e40857d7806e`) o desde `resolver_registry_v2.json → document_registry.MANUAL` (mismo UUID). ⚠️ Fricción: el Kernel instruye `python lazy_loader.py --page {KERNEL_MASTER} --route {ruta}` (`Kernel.md:908`) con un placeholder **`{KERNEL_MASTER}` que no está definido en ningún script ni constante** — el agente debe cruzar manualmente contra la Cédula Digital o el Registry.
3. **Autorización de prefijo:** `lazy_loader._get_authorized_prefixes()` (`lazy_loader.py:60-91`) lee la sección `document_registry` del Registry, ignora claves `_comment`, y cachea un `frozenset`. **[EJECUTADO offline]:** carga correcta de 11 prefijos `{ALIASES, ARCHIVEROS, BRIEF, CANON, CHANGELOG, CHANGELOG_ARCHIVO, KERNEL, MANUAL, SP, TRACKER, VANTAGE}`. Fallback estático `_STATIC_FALLBACK_PREFIXES = {KERNEL, MANUAL, CANON, TRACKER}` solo si el Registry falta/malestá.
4. **Parseo de ruta:** `_parse_route()` (`lazy_loader.py:118-135`) → `("MANUAL", "SETUP")`; forma canónica `MANUAL:SETUP`. Prefijo no registrado (ej. `BUG:U_x`) → warning + cae a modo legacy **[EJECUTADO]**.
5. **Fetch quirúrgico:** `fetch_lazy_section()` (`lazy_loader.py:201-317`) hace `GET /v1/blocks/{page_id}/children?page_size=100` con retry/backoff `[0,1,2]s` (`_notion_get`, `lazy_loader.py:137-162`), escanea heading a heading; matchea `canonical_form in texto` **o `clave in texto` (substring)**; captura hasta `</payload>` o heading de jerarquía igual/mayor sin la clave (con guard `just_started` contra cierre prematuro); los hijos anida-vía `fetch_block_children_recursive()`.
6. **Salida:** texto plano con `<payload>` strip → **~150 tokens** por lectura, versus ~19k tokens del Kernel completo (77 KB) o ~36k del Manual (142 KB) vía notion-fetch — ahorro >99% por lectura (medido sobre los mirrors del repo, 4 bytes/token aprox).
7. **Parches de Notion:** el loader es **solo lectura** (endpoint `blocks/children` GET). La escritura documental vive en otra vía: DRY RUN → APROBAR_WRITE → Notion Write (`KERNEL:DATA-FLOW`, `Kernel.md:908+`), con parches puntuales vía MCP (`apply_hyperlinks_notion.py` preserva block-ID; `vsync_doc.py` hace delete-all + create-all — riesgo documentado en `KERNEL:ARCHITECTURE-L4`).

**Fragilidad estructural [EJECUTADO/estático]:** el scan solo recorre **bloques hijos de primer nivel** de la página; headings dentro de columns/toggles son invisibles para el matcher (la recursividad solo aplica a los hijos de bloques ya capturados). Es la misma clase de pitfall que el propio Registry documenta para notion-fetch (`known_pitfalls.general: "notion-fetch trunca páginas largas / no resuelve bien column layouts"`, `resolver_registry_v2.json`) — el loader hereda la limitación y nadie la documentó como tal. Además, una ruta con typo agota el scan completo de la página (todas las páginas de API) antes de devolver `ERROR: Ruta no encontrada`.

### 1.2 Trazabilidad E2E — Ruta de Entidades: `resolve TRACKER:H_xxx`

1. **Entrypoint:** `vantage.py resolve` → `_resolve_entity` (docstring "Phase 3").
2. **Carga de índice:** `query_layer.load_index()` parsea `entity_index_v2.json` (400 KB, 864 entidades) y cachea en memoria de proceso.
3. **Lookup:** `resolver_layer_v1._lookup_entity()` (`resolver_layer_v1.py:32-36`) hace **scan lineal O(n)** comparando `entity_id`/`canonical_id`. ⚠️ El diseño se documenta como "lecturas deterministas O(1)"; la implementación es O(n) en CPU y, peor, O(páginas) en red:
4. **Validación en vivo:** `resolve_entity()` (`resolver_layer_v1.py:86-110`) llama `_query_notion(data_source_id)` que **pagina el data source COMPLETO** (con `time.sleep(0.35)` por request, sin cache) para luego filtrar `item.id == page_id`. Para `ARCHIVO_TRACKER` (827 filas ≈ 9 páginas) cada resolve cuesta ~9 requests y ~3-5 s **aunque el page_id ya está en el índice local**. Un `GET /v1/pages/{page_id}` directo sería 1 request.
5. **Registry mapping:** `_source_config()` normaliza `source_db` → `data_source_id` desde `data_sources` del Registry (contrato KERNEL:SCHEMA-005 paso 2, correcto).
6. **Contexto extendido (`vantage.py context`):** `context_layer.assemble_context()` vuelve a resolver (paso 2-4) y además hace `find_entity()` — **doble lookup** del mismo entity_id — luego `GET /pages/{id}` + `GET /blocks/children` paginado vía `notion_utils.notion_get()` (aquí sí hay cache 6h, throttle y métricas).

### 1.3 Runtime Build (`vantage.py sync`)

`sync()` orquesta: carga de `generate_entity_index_v2` con cirugía de `sys.path` (para que el `notion_utils.py` local no tape al SDK `notion-client`; `vantage.py:88-110`) → `build_entities()` sobre los 2 data sources COL (`DB_IDS`, API **2025-09-03** forzada en `make_client()`) → `build_graph()` (join por prefijo de hash16 entre tracker y archivo) → `build_backlinks()` (inversa exacta) → `validate_graph_artifacts()` (sin nodos huérfanos, backlinks ≡ grafo) → **escritura atómica** (`.tmp` → `os.replace`) de los 3 artefactos en `Layer_1/data/`. El auto-sync >24h lo dispara `health_check.py` (`INDEX_STALE_THRESHOLD_HOURS = 24`, `health_check.py:320`; política en `Manual.md:660`).

**Hallazgo de resultado [EJECUTADO]:** los artefactos commiteados están **vacíos por diseño defectuoso**: `graph_v2.json = {"version":"2.0","edges":[]}` y `backlinks_v2.json = {"version":"2.0","backlinks":{}}`. La causa no es falta de sync (el index tiene 864 entidades frescas del último auto-sync) sino que `build_graph()` solo puede crear aristas `archived_from` cuando una fila ARCHIVO y una TRACKER **coexisten con el mismo hash en el mismo snapshot**. Medición real sobre `entity_index_v2.json`: 34 trackers con hash, 600 archivos con hash, **intersección = 0**. El archivado mueve filas entre bases → ambos lados nunca coexisten → **el grafo es estructuralmente incapaz de poblar su único tipo de arista**. Ver §4-F2.

### 1.4 Rol de `resolver_registry_v2.json` como SSOT

Cumple su rol de doble namespace (documento en `status`: "LIVE — Resolver Layer operativo desde 2026-06-15"): `data_sources` (4 fuentes, `entity_prefix` para el Runtime Build) y `document_registry` (11 prefijos → UUID de página fundacional, consumido por `lazy_loader._get_authorized_prefixes()` desde v9.0.5). `runtime_identity.py` centraliza `load_prefix_map()`/`generate_entity_id()` (cierra DT-014) y el Build falla explícito si falta un prefijo — correcto y verificado. **Pero** el propio archivo arrastra defectos (clave JSON duplicada `CHANGELOG_ARCHIVO`, UUID sin dashes en `ARCHIVEROS`) y la sección de contrato que invocan los scripts (`KERNEL:DOC-CONTRACT`) no existe en el Kernel vivo (§4-F4, F16).

---

## 2. Mecanismos de Descubrimiento de Agentes (Bootstrapping & Routing)

### 2.1 Cadena de bootstrapping (cómo un agente "se entera" del L0)

1. **Project Instructions de la plataforma** — único vector de instrucciones activas (`Manual.md:151`). En el repo hay un ejemplar canónico: `.hermes.md` (HERMES/DEFAULT). No hay equivalentes versionados para Claude/Cursor/Devin en el árbol (los de Claude viven en la UI de Notion/Project Instructions).
2. **SP:BOOTLOADER** (`System Prompt.md` §01): al primer mensaje, `BOOTLOADING...` → fetch de **exclusivamente 2 documentos**: SYSTEM PROMPT (`37b938be-…`) + ID CENSUS (`394938be-…`), vía `notion-fetch` (familia MCP-Notion: Claude, Cursor, Devin, ChatGPT, Littlebird, Grok, Hermes) o fetch raw de GitHub (familia GitHub-only: Perplexity, Mistral/Vibe). Falla → 1 reintento → `MODO DEGRADADO`.
3. **KERNEL:DOCUMENTATION-004** (`Kernel.md:93-108`): protocolo espejo en el Kernel. ⚠️ **Cita un ID muerto**: ordena "fetch de SP:BOOTSTRAP-001 y del ID CENSUS" (`Kernel.md:96`), pero la página SYSTEM PROMPT viva ya no contiene `SP:BOOTSTRAP-001` — fue reorganizada como `SP:BOOTLOADER / -001 / -002` (el renombre está trazado en `Changelog Archivo.md:1895-1903` y `:1984-1989`). Un agente que ejecuta literal el Kernel busca una ancla que no existe.
4. **Descubrimiento del Lazy Loader propiamente:** SP:04 `SP:CONTEXT-INFRASTRUCTURE` (`System Prompt.md`: "Terminal (lazy_loader.py): Ruta preferente") → `KERNEL:CONTEXT-INFRASTRUCTURE` (`Kernel.md:892-908`, triaje A/B/C) → `MANUAL:LAZY-LOAD` (`Manual.md:798-803`) → `Aliases.md:15` (vload: "Activa .venv y corre lazy_loader.py –page {ID} –route {ruta}… ~150 tokens"). La cadena es **suficiente en papel**: un agente que consume Kernel+Manual+Aliases sabe qué, cuándo y cómo invocar.
5. **Manifiesto multi-agente (`skills/triggers.json`):** 28 skills con `{trigger[], path, description, last_modified, url, notion_id}` **[EJECUTADO: parse completo — 28/28 con `notion_id` y `url`, y los 28 `path` apuntan a archivos que existen]**. Regla de enrutamiento fija en `SP:BOOTLOADER-001` (propiedad del agente, no del skill): familia MCP-Notion → `notion_id` → notion-fetch; GitHub-only → `url` → fetch raw; Gemini → fuera (Gem con Knowledge manual). Mantenido por `update_triggers_json.py` (alias `vtriggers`), con auto `git push` documentado como decisión consciente (`KERNEL:ARCHITECTURE-L4`).

### 2.2 Contradicción de descubrimiento del manifiesto

`KERNEL:ARCHITECTURE-L4` (`Kernel.md:354`) afirma que el Bootloader hace el fetch de `triggers.json` "junto con SYSTEM PROMPT e ID CENSUS". **El SP:BOOTLOADER vivo solo lista 2 fetches** — el tercer fetch (SKILLS MANIFEST, "no bloqueante") fue documentado en el Changelog Archivo (`:554`: "paso 2 ampliado con tercer fetch… paso 2.1 nuevo: lazy-load por trigger") pero **no está en la versión viva del System Prompt**. Consecuencia operativa: un agente que bootea estrictamente por SP:BOOTLOADER **nunca se entera de que el manifiesto existe**; solo lo descubre si llega a Kernel §4.4. Para la familia GitHub-only esto es crítico: su única ruta al manifiesto es la que el bootloader no les menciona.

### 2.3 Matriz de cobertura por agente (evidencia en repo)

| Agente | Vector de descubrimiento | Evidencia en repo | Estado |
|---|---|---|---|
| Claude (×4 instancias) | Project Instructions + notion-fetch | SP:BOOTLOADER-002 registro (MAIN/KM/MP/MM) | OK |
| Hermes | `.hermes.md` (instrucciones completas, incluye bootloader y restricciones) | `.hermes.md` | ⚠️ Declarado en la lista de familia MCP-Notion del bootloader, pero **ausente del registro de identidad de 10 agentes** (SP:BOOTLOADER-002) → su primera handoff emitiría `IDENTITY_CONFIGURATION_REVIEW_NEEDED` |
| Cursor | `.vscode/mcp.json` (notion-mcp-server HTTP) | `.vscode/mcp.json` | OK; "fuera del registro por diseño" (correcto) |
| Devin | `Layer_1/.devin/config.json` (notion MCP http) | `.devin/config.json` | ⚠️ Kernel L4 dice "Devin no consume el manifiesto — solo Claude y Mistral"; pero Devin sí tiene MCP Notion configurado → puede notion-fetch del Kernel pero no sabe del manifiesto (ambigüedad no resuelta en docs) |
| Perplexity / Mistral | vdigest (gitingest) + raw fetch | `get_vantage_digest.sh`, `SCOUT_MANUAL` no aplica | OK; dependen del repo público |
| Gemini | Gem con Knowledge pre-cargado manual | — | Fuera de flujo (documentado) |
| Arena (este entorno) | Clona el repo; sin MCP Notion, sin Project Instructions | `handoffs/AUDITORIA_TRACKER_E2E_2026-09-11.md` (predecessor) | Descubre L0 por lectura de árbol — válido, pero **no pasa por BOOTLOADING/BOOTLOADED** |

### 2.4 Veredicto de suficiencia documental

**Suficiente con 4 defectos activos:** (a) las referencias rotas `SP:BOOTSTRAP-001` y `KERNEL:DOC-CONTRACT` (esta última es citada por 4 scripts — `lazy_loader.py:10,51,57,127`, `generate_id_inventory.py:90-91`, `verify_versions.py:29` — y `normalize_heading_ids.py:12` hasta especifica su formato esperado `## §22 — KERNEL:DOC-CONTRACT`, **sección inexistente en el Kernel vivo**); (b) el alias `vload`/`vtrig` vive en el `.zshrc` del operador, no en el repo — un agente remoto (Arena/Devin cloud) debe reconstruir el comando desde Aliases.md y buscar UUIDs a mano; (c) placeholder `{KERNEL_MASTER}` sin resolución mecánica; (d) el Manual arrastra instrucciones retiradas que desorientan al bootstrapper (§4-F17).

---

## 3. Evaluación de Políticas de Ahorro de Tokens (Lineamientos vs. Ejecución Real)

### 3.1 Inventario de lineamientos

| Documento | Regla | Naturaleza |
|---|---|---|
| `KERNEL:CONTEXT-INFRASTRUCTURE-001` (`Kernel.md:896-902`) | Triaje de costos: A: Terminal, B: MCP, C: Upload. "Priorizar Opción A". MCP "autorizado para lectura, DRY RUN y modificación documental cuando exista instrucción explícita" | Persuasiva |
| `MANUAL:LAZY-LOAD` (`Manual.md:798-803`) | Prioridad A = `lazy_loader.py` (~150 tokens/lectura). Prioridad B = MCP **"reservado exclusivamente para escrituras… No se usa para lectura de reglas o contratos"** | Persuasiva (más dura) |
| `SP:04 CONTEXT-INFRASTRUCTURE` | Terminal preferente; MCP para "lectura, DRY RUN y actualización documental ante instrucción explícita" | Persuasiva |
| `SP:09 MCP-ROUTING-NOTES` | "Extracción masiva de filas: Terminal local, no MCP" | Persuasiva |
| `SP:11 VERSION-CHECK-TOOL` | `verify_versions.py` en Terminal "para mitigar costos de llamadas MCP" | Persuasiva |

**Incoherencia inter-documental (marcada como hallazgo, no suposición):** el Manual **prohíbe** MCP para lectura de reglas; el Kernel y el System Prompt **autorizan** MCP de lectura con instrucción explícita. Tres documentos fundacionales que un mismo agente carga en el mismo boot dan dos respuestas distintas a "¿puedo notion-fetch del Kernel?". Bajo `SP:CONSISTENCY` esto debería detener la sesión; en la práctica, cada agente elige la interpretación que le convenga — la política no tiene árbitro.

### 3.2 ¿Existen guards coercitivos?

**No para lectura.** El único guard técnico real es `class_b_guard.py` (escritura de campos Class B vía MCP, GAP-03) y los gates del pipeline (URL gate, hard blocks). **No existe ningún mecanismo que**: (a) intercepte o contabilice una lectura MCP masiva, (b) compare el costo en tokens de la Ruta B contra la Ruta A en tiempo de sesión, (c) exija justificación previa por payload >N tokens. `notion_utils` lleva métricas (`requests_total`, `cache_hits`, `METRICS_PATH`) pero **solo del stack Python** — el tráfico MCP de los agentes es invisible para la observabilidad del sistema. La adherencia a la Ruta A es, hoy, un asunto de disciplina del LLM lector, no de arquitectura.

### 3.3 El Runtime propio erosiona la cuota que la política protege

Contraste medido sobre el código:

| Operación | Costo real | Costo que la política "Ruta A" promete |
|---|---|---|
| `vload KERNEL:X` | ~150 tokens de contexto (1-N requests API, invisibles al contexto) | ~150 tokens ✅ |
| notion-fetch Kernel completo | ~19k tokens (77 KB) | — |
| notion-fetch Manual completo | ~36k tokens (142 KB) | — |
| `vantage.py ask "archived history"` → `agent_api._handle_show_archived_history()` (`agent_api.py:194-225`) | Query sin filtros a ARCHIVO_TRACKER y **retorna las 827 filas** (page_id, título, status, marca, url) ≈ **25-35k tokens al contexto del agente** — más que leer el Manual completo | "economía de contexto" ❌ |
| `vantage.py ask "show active roles"` → `_handle_show_roles()` (`agent_api.py:111-130`) | 37 entidades × `assemble_context()`; cada una dispara `resolve_entity()` = **query completo del data source** + 2 GETs ≈ ~110+ requests, minutos de latencia (throttle 0.35s, sin cache en el resolver) | — |
| `vresolve TRACKER:H_x` | O(n) scan local + query completo del data source para validar 1 página | "lecturas deterministas O(1)" ❌ |

**Conclusión del eje:** la política está bien diseñada para el flujo documental (lazy_loader cumple su promesa de ~150 tokens) pero (1) no es coercitiva, (2) está contradicha entre sus propios documentos, (3) no tiene observabilidad de cumplimiento, y (4) el Runtime de entidades — que se supone es el mecanismo anti-MCP — contiene handlers que perforan el contexto más agresivamente que un notion-fetch. Un agente que obedece la Ruta A y corre `vask "show archived history"` sufre peor erosión que si hubiera hecho el fetch masivo que la política le prohíbe.

### 3.4 Brechas concretas donde los agentes ignoran el Lazy Loader

1. **Boot sin manifiesto** (§2.2): quien no llega a Kernel §4.4 no sabe que hay carga bajo demanda por trigger y opera de memoria o fetch masivo.
2. **`vprint.sh` roto** (`Manual.md:1160-1162`, hallazgo documentado pero **no corregido**): ruta incompleta — un agente que intenta la vista "listo para actuar hoy" falla y recalienta con MCP.
3. **Manual con smoke tests "esperados a fallar"** (`Manual.md:232`: "este es el que hoy falló por el archivo borrado en el commit 29fc7f0; seguirá fallando igual hasta que restauremos ese archivo"): la nota congelada de una sesión pasada instruye al agente a **aceptar el fallo del Runtime como normal** — el peor mensaje posible para la adopción de la Ruta A.
4. **`vcontext` documentado mal** (`Aliases.md:25-26` dice que trae "relaciones, backlinks" sobre graph/backlinks; `vantage.py context()` en realidad ejecuta `assemble_context()` = página completa + bloques): el agente que busca economía (grafo local = 0 tokens de red) recibe una lectura completa de página sin saberlo.

---

## 4. Informe Forense de Deuda Técnica y Errores de Implementación

Severidad: 🔴 crítico · 🟠 alto · 🟡 medio · ⚪ bajo/higiénico.

### Bloque A — Inconsistencias de API

**F1 🟠 Mezcla de versiones de Notion API en 3 stacks HTTP no unificados.** Evidencia:
- `lazy_loader.py:227` → `"Notion-Version": "2022-06-28"` **hardcodeado**, ignora la variable `NOTION_VERSION` que `notion_utils._notion_version()` sí respeta (`notion_utils.py:14-17`).
- `resolver_layer_v1.py:67` → `os.environ.get("NOTION_VERSION", "2025-09-03")` — **mismo env, distinto default** que notion_utils.
- `generate_entity_index_v2.py:55` → `DATA_SOURCES_API_VERSION = "2025-09-03"` forzada sobre el SDK.
- Dualidad intra-script: `clean_script_library_links.py:41` (2025-09-03) vs `:178` (2022-06-28 "para /v1/pages"); `verify_versions.py:165/178/456` mismo patrón dual (documentado como consciente, con causa raíz de HTTP 400 fantasma en el comentario `verify_versions.py:49-61`).
- Otros: `generate_census.py:28`, `normalize_heading_ids.py:66`, `layer_3_mail.py:509` (2022-06-28) vs `vsync_doc.py:47`, `extract_scores*.py`, `feedback_loop.py`, `update_triggers_json.py` (2025-09-03).
Hoy funciona porque `/v1/pages` y `/v1/blocks` siguen atendiendo 2022-06-28 y los endpoints `data_sources/*` exigen 2025-09-03; pero cada script decide por su cuenta, y el default divergente entre los dos módulos "canónicos" (notion_utils vs resolver) es una trampa de migración (cuando Notion retire 2022-06-28, fallarán primero lazy_loader y generate_census, y nadie tiene el inventario de quién usa qué).

### Bloque B — Fragilidad del Grafo/Registry

**F2 🔴 `graph_v2.json` y `backlinks_v2.json` estructuralmente vacíos por diseño imposible.** `build_graph()` (`generate_entity_index_v2.py:196-244`) solo crea aristas `ARCHIVO→TRACKER` cuando comparten `hash[:16]` **en el mismo snapshot**. Medición [EJECUTADO] sobre el índice real: 34 tracker-hashes, 600 archivo-hashes, **intersección 0** — el archivado traslada la fila entre bases, luego ambos lados jamás coexisten. Todo el subsistema (`graph_layer.py`, `get_archived_from`, `backlinks`, la mitad del docstring de `agent_api`) opera sobre un grafo muerto: `graph_stats()` devolverá `{"total_edges": 0}` para siempre. El docstring de `build_graph` ("Deterministic: no fabricated edges") es honesto, pero el artefacto y su validación (`validate_graph_artifacts` PASS sobre vacío) dan falsa impresión de salud.

**F3 🔴 82 entity_ids duplicados en el índice (9.5%).** [EJECUTADO] `entity_index_v2.json` contiene 864 filas con **82 entity_ids repetidos** (ej. `TRACKER:H_1977ee872221bcee` ×2; `ARCHIVO:H_cd20d1d624a0645f` ×3). Causa: `generate_entity_id()` (`runtime_identity.py:113-124`) deriva el ID de `hash[:16]`, y hay **81 hashes duplicados en ARCHIVO_TRACKER** (reposts/vacantes re-publicadas con el mismo fingerprint). Consecuencia: el "identificador canónico" no es canónico; `_lookup_entity()` (scan lineal) retorna silenciosamente el **primero**, y un resolve puede apuntar a la página equivocada. Ni `validate_graph_artifacts` ni ningún otra validación detecta colisiones de PK.

**F4 🟡 `resolver_registry_v2.json` con clave JSON duplicada y formato de UUID inconsistente.** [EJECUTADO: parse con `object_pairs_hook`] — `document_registry` contiene `CHANGELOG_ARCHIVO` **dos veces** (mismo valor → json lo resuelve al último; daño latente, no activo) y `ARCHIVEROS: "3bb938befc4280cd8ea3fc8ba78f570c"` **sin dashes** frente a los 10 restantes con dashes (cosmético pero rompe comparaciones de igualdad por string y valida la regla de estilo del propio SP:DIGITAL-ID-CARD). Un linter JSON con `unique_keys` habría atrapado ambos.

**F5 🟠 Dos rutas de escritura divergentes para los artefactos del grafo.** El CLI standalone escribe en `Layer_1/scripts/` (`generate_entity_index_v2.py:393,401`: `graph_path = _SCRIPTS_DIR / "graph_v2.json"`), mientras el lector (`graph_layer.py:8`: `../data`) y `vantage.py sync()` (líneas ~180-190: `_scripts_dir.parent / "data"`) usan `Layer_1/data/`. Un operador que corre `python3 generate_entity_index_v2.py` a mano regenera el índice en `data/` pero **los grafos quedan en `scripts/`**, donde nadie los lee — y como hoy el grafo es vacío, el defecto es invisible. Es el patrón "script parcialmente migrado" en estado puro.

**F6 🟡 `graph_layer.py` carga el grafo a nivel de módulo (import-time).** `graph_v2, backlinks_v2 = _load_graph_data()` al importar → datos congelados por proceso; `vantage.py sync()` tiene que parchear con `importlib.reload(graph_layer)` (`vantage.py`, bloque post-sync). Si el archivo falta/corrapeado, el import **revienta todo el runtime** (agent_api degrada a `_GRAPH_AVAILABLE=False` solo si el import falla, pero vantage.py importa graph_layer vía agent_api con try/except — la resiliencia depende de orden de imports).

**F7 🟠 Detección de staleness basada en `mtime` — miente en entornos clonados.** `vantage.py status()` usa `os.path.getmtime(ENTITY_INDEX_PATH)`; el índice **no tiene campo `generated_at` interno**. En cualquier clone fresco (Arena, Devin, CI), mtime = momento del clone → `index_age_hours ≈ 0` y el guard >24h (`health_check.py:320`, auto-sync según `Manual.md:660`) **nunca se dispara aunque los datos tengan semanas**. Este sandbox es la prueba: `status()` reportaría un índice "fresco" de 864 entidades cuyo snapshot real es del último auto-sync local del operador.

**F8 🟠 El Resolver no pasa por `notion_utils` (sin cache, sin métricas, sin retry disciplinado).** `_query_notion()` (`resolver_layer_v1.py:47-84`) usa `requests` crudo con `time.sleep(0.35)` fijo y `raise ResolverError` ante 4xx — fuera del circuito de cache 6h/throttle/retry-backoff/metrics de `notion_utils.notion_get()`. Resultado: las operaciones de lectura más caras del sistema (query completo por resolve) son **las únicas sin cache ni telemetría**.

### Bloque C — Parámetros vestigiales y herencia

**F9 🟠 Infraestructura de seriales MCP/HTTP huérfana de su política.** `SP:BOOTLOADER-002` decreta: "MCP, HTTP y acceso directo a SQLite no son rutas válidas de asignación ni fallback" — solo `vserial` vía Terminal. Sin embargo, siguen vivos y sin marcar deprecado: `mcp_vantage_serial_server.py` (cuyo `README_MCP.md` celebra exactamente lo prohibido: "Permite asignación de seriales **sin acceso a Terminal**"), `tools/claude-desktop-mcp-extension/` (bridge a `http://localhost:8787`, inoperante en entornos remotos), y el modo servidor Flask de `allocate_vantage_serial.py:98` (`--port 8787`, consumido por `health_check.py:500`). Los archivados correctos (`DEPRECATED_vantage_serial_http_server.sh`, `DEPRECATED_vantage_serial_mcp_bridge.py`) están en Archive, pero sus sucesores activos violan el contrato vigente. O se retiran, o la política se actualiza — hoy hay dos verdades.

**F10 ⚪ `config/layer_2.env.example` en la raíz** — Layer_2 fue eliminado en v9.3.9 (Kernel L4 y `Layer_1/VANTAGE_ARCHITECTURE.md:26`); el ejemplo de env sobrevivió a la limpieza.

**F11 ⚪ Vestigios documentados pero no corregidos:** `toggle_changelog_archive.py --apply` "no tiene efecto real" (`Manual.md:1108-1110`); `vprint.sh` con ruta incorrecta (`Manual.md:1160-1162`); ambos son deuda conocida viviendo como nota, no como fix.

**F12 🟡 Tres estrategias de carga de `.env` inconsistentes.** `vantage.py:33` → `load_dotenv("../.env")` **relativo al CWD** (solo funciona si se corre desde `Layer_1/scripts`, exactamente como instruye el Manual — frágil ante cualquier wrapper con otro CWD); `lazy_loader.py:326-329` → anclado a `__file__` pero apuntando a **otro archivo** (`Layer_1/config/layer_1.env`); `generate_entity_index_v2.py:36` → anclado, `Layer_1/.env` con `override=True`. Dos archivos de env distintos en juego y un entrypoint principal dependiente del directorio de invocación.

**F13 🟠 `update_triggers_json.py` no portable y con contrato de descubrimiento divergente de su doc.** `SKILLS_PATH`/`TRIGGERS_PATH` hardcodeadas a `/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/...` (`update_triggers_json.py:41-42`) — cualquier otro entorno (o un clone del repo por un agente) rompe el generador del manifiesto SSOT. Además, `KERNEL:ARCHITECTURE-L4` dice que el script "detecta altas nuevas (carpeta con SKILL.md válido)", pero `discover_skill_files()` solo hace glob de `skills/*.md` plano (`update_triggers_json.py:60-63`) — el descubrimiento por carpeta/SKILL.md descrito no existe en el código.

**F14 🟠 Contaminación del repo raíz (higiene que afecta a cada agente que clona).** El árbol mezcla: el subsistema **VANTAGE Scout** (proyecto distinto: `main.py`, `src/`, `web_ui.py`, `MANUAL.md` —que es el manual de Scout, no del sistema—, `SCOUT_MANUAL.md`, `simulacion_archivo_notas.py`), dumps de datos (`reingest_consolidated_format.json`, `vantage_output_careersites_20260908.json`), `VANTAGE_digest.txt` (snapshot gitingest), `README_VANTAGE.txt` (**4.2 MB**) y un audio de **40.5 MB** (`Estrategias_para_tu_entrevista_directiva_en_Nike.m4a`) versionado en git. Cada `git clone --depth 1` que hace la familia GitHub-only (Kernel L4) descarga ~45 MB de ruido no documental, y un agente que busca "Manual.md" encuentra el de Scout.

### Bloque D — Documentación vs código real (marcados como incoherencias, no suposiciones)

**F15 🔴 `KERNEL:DOC-CONTRACT` no existe.** Citado como contrato normativo por `lazy_loader.py` (×4), `generate_id_inventory.py:90-91`, `verify_versions.py:29`, y con formato esperado `## §22 — KERNEL:DOC-CONTRACT` en `normalize_heading_ids.py:12` — grep completo sobre `Documentación/ACTIVE/Kernel.md`: **0 resultados**. El contrato que autoriza los prefijos documentales del Lazy Loader vive solo en el código y en el Registry; el documento que se supone SSOT de gobernanza no lo contiene.

**F16 🟡 Referencia de bootstrap a ID retirado.** `Kernel.md:96` (KERNEL:DOCUMENTATION-004) ordena fetch de `SP:BOOTSTRAP-001`; la página viva usa `SP:BOOTLOADER*`. El propio Changelog Archivo (v9.7.3, `:1895-1903`) documenta el renombre y un caso idéntico de drift no propagado.

**F17 🟠 Manual con tres instrucciones retiradas/erróneas activas:** (1) paso de setup que enseña el cierre "VANTAGE: SISTEMA SINCRONIZADO" (`Manual.md:154`) — frase retirada oficialmente en v9.7.3 a favor de `BOOTLOADED: DOCUMENTOS CARGADOS`; (2) "Resultado esperado: Status: READY (4,200+ blocks indexed)" (`Manual.md:169`) — `vantage.py status()` no produce ese output (produce JSON con `total_entities`; hoy 864); (3) smoke tests documentados como "seguirán fallando" (`Manual.md:232-233`). Un agente recién booteado que lea el Manual aprenderá protocolo retirado y expectativas falsas del Runtime.

**F18 🟡 `vcontext` mal documentado** (ver §3.4-4): Aliases describe graph/backlinks; el código hace fetch completo de página. Nada en el Runtime expone graph/backlinks por alias — irónicamente, la única consulta de grafo (`ask "relation TRACKER:H_x"`) consulta un grafo vacío (F2).

**F19 🟡 Hermes fuera del registro de identidad** (ver §2.3): `.hermes.md` declara identidad conforme, SP:BOOTLOADER lo lista en la familia MCP-Notion, pero SP:BOOTLOADER-002 no lo registra → primera handoff = `IDENTITY_CONFIGURATION_REVIEW_NEEDED` garantizado.

**F20 ⚪ Colisión de namespaces TRACKER (conocida y aceptada, pero activa).** `TRACKER` existe simultáneamente en `data_sources` (entity_prefix de filas) y en `document_registry` (UUID de página del tracker). `lazy_loader._parse_route("TRACKER:algo")` lo trata como ruta documental válida; una ruta ambigua tipo `TRACKER:SETUP` matchearía headings del tracker en vez de fallar. El diseño lo documenta ("namespace independiente"), pero nada distingue la intención del llamador.

### Bloque E — Latencia y fricción de handshake

| Fricción | Evidencia | Impacto |
|---|---|---|
| Resolver sin cache, sleep fijo 0.35s/página | `resolver_layer_v1.py:47-84` | Cada `vresolve` ≈ 9 requests + ~3-5s sobre ARCHIVO; `show roles` ≈ minutos |
| Doble resolución en `assemble_context` | `context_layer.py` pasos 1-2 (`resolve_entity` + `find_entity`) | 2× parseo del índice de 400 KB por entidad |
| Cache 6h de notion_utils no compartida entre procesos clientes | `notion_utils.py` (CACHE_PATH local al scripts dir) | L3/cron/agentes en máquinas distintas no comparten cache; el file-cache escribe JSON completo en cada hit (`_save_cache` en cada `_cache_set`) |
| Lazy loader: scan completo en miss | `fetch_lazy_section` | Ruta con typo = coste de leer la página entera por API antes del ERROR |
| Serial handshake local-only | `:8787` localhost (`allocate_vantage_serial.py:98`, `server.js:18`) | Asignación de serial imposible desde entornos remotos (coherente con SP:BOOTLOADER-002, pero deja a Arena/Devin sin vía alguna) |
| `triggers.json` con riesgo de caché de fetch documentado | Kernel L4 ("reintentar con cache-busting") | Fricción de actualización intra-sesión conocida y manual |

---

## 5. Propuesta de Arquitectura Mejorada (Matriz de Impacto / ROI)

Principio rector: **el sistema ya entiende que su activo es el contexto de los agentes**; las mejoras priorizan (1) que la Ruta A sea siempre la opción dominante en la práctica (no solo en el papel), (2) que los artefactos cumplan lo que sus nombres prometen, (3) que la política tenga dientes mecánicos.

### P1. Resolver v3 — validación puntual en vez de query masiva
- **Cambio técnico:** en `resolver_layer_v1.resolve_entity()`, sustituir `_query_notion(data_source_id)` (query completo + filtrado) por `GET /v1/pages/{page_id}` (1 request) usando el `page_id` que ya vive en `entity_index_v2.json`. Índice en memoria como dict `{entity_id: row}` construido una vez en `load_index()` (elimina el scan O(n) y el doble lookup de `context_layer`). Enrutar el HTTP por `notion_utils` (cache + throttle + métricas + retry).
- **Fricción que elimina:** latencia de 3-5 s por resolve; ~110+ requests por `show active roles`; telemetría ciega (F8); doble parseo de 400 KB.
- **Aporte:** latencia −95% por resolve; requests −N×; todo el tráfico de lectura queda medido en `notion_metrics.json`; base para cache coherente.

### P2. Grafo honesto o grafo real (decidir, no simular)
- **Cambio técnico:** dos opciones excluyentes: (a) **fuente de relación real** — derivar `archived_from` del momento de archivado (la nota determinista `generate_archive_notes()` / `Last_Gate_Run` ya lleva la trazabilidad) o matching difuso (marca+rol) entre ARCHIVO y TRACKER históricos; o (b) **retiro temporal** — marcar `build_graph/build_backlinks/graph_layer` como `SUSPENDED` con un solo check en `sync()` que escriba `{"status":"suspended","reason":"no relation source"}` en lugar de artefactos vacíos que "validan PASS". Añadir a `validate_graph_artifacts()` la validación de **unicidad de `entity_id`** (F3) y fallback de sufijo colisión (`H_<hash16>#2`) en `generate_entity_id()`.
- **Fricción que elimina:** grafo muerto con apariencia viva; IDs canónicos ambiguos (82/864); `ask "relation…"` devolviendo stats vacías sin explicación.
- **Aporte:** robustez determinista (PK única garantizada); elimina código-fantasma de la superficie cognitiva de los agentes.

### P3. Un solo contrato de versión de API y un solo lugar para paths
- **Cambio técnico:** constante única `NOTION_VERSION` leída solo desde `notion_utils._notion_version()` (default `2025-09-03`); `lazy_loader.py:227`, `generate_census.py:28`, `normalize_heading_ids.py:66`, `layer_3_mail.py:509` dejan de hardcodear. Igual para artefactos: `runtime_identity.py` o `resolver_layer_v1` exportan `DATA_DIR` y `DOC_REGISTRY_PATH`; `generate_entity_index_v2.py:393,401` escribe a `DATA_DIR` (F5). Añadir `generated_at` + `source_commit` dentro de los 3 JSON y que `status()`/`health_check` prefieran ese campo sobre mtime (F7).
- **Fricción que elimina:** 3 stacks HTTP divergentes; artefactos escritos donde nadie lee; staleness mentiroso en clones.
- **Aporte:** robustez ante deprecación de API por parte de Notion; detección de staleness real en cualquier entorno (incl. agentes remotos); un solo lugar que auditar.

### P4. `vload` como comando de repo (economía sin dependencia del .zshrc del operador)
- **Cambio técnico:** script `Layer_1/scripts/vload.py` (o flag `--auto-page` en lazy_loader) que resuelva el UUID desde `document_registry`: `vload KERNEL:SCHEMA-004` sin UUID. Wrapper shell + entrada en Raycast. Tests offline con fixture mock de bloques (hoy **cero tests** para el componente estrella de la economía de tokens).
- **Fricción que elimina:** placeholder `{KERNEL_MASTER}`; búsqueda manual de UUIDs por parte de agentes remotos; reglas de matching sin red de regresión (substring match, cierre por `</payload>`, bloques en columns — F de §1.1).
- **Aporte:** baja el costo de transacción de la Ruta A a cero-fricción para **todos** los agentes (no solo el Mac local); cada lectura sigue en ~150 tokens; la política se vuelve el camino de menor resistencia.

### P5. Saneamiento documental dirigido (los 5 arreglos de mayor retorno)
1. Crear la sección `KERNEL:DOC-CONTRACT` (§22, formato `## §22 — …` que `normalize_heading_ids.py:12` ya especifica) o re-apuntar las 8 citas del código al ID real (F15).
2. `Kernel.md:96`: `SP:BOOTSTRAP-001` → `SP:BOOTLOADER` (F16).
3. `Manual.md`: retirar "VANTAGE: SISTEMA SINCRONIZADO" (→ `BOOTLOADED: DOCUMENTOS CARGADOS`), corregir el output esperado de `status`, y **borrar/resolver la nota de smoke-tests "seguirán fallando"** (F17).
4. Resolver la contradicción MCP-lectura con **una tabla única de triaje** referenciada por los 3 documentos (F §3.1).
5. `Aliases.md`: corregir `vcontext`; agregar fila Hermes al registro SP:BOOTLOADER-002 (F19); documentar en SP:BOOTLOADER el fetch del manifiesto o corregir Kernel L4 (F §2.2).
- **Aporte:** puro ahorro de tokens de boot (menos re-lecturas para resolver contradicciones) y menos desvíos de agentes hacia Ruta B por instrucciones falsas.

### P6. Presupuestos de payload en Agent API (que el Runtime no perfore el contexto)
- **Cambio técnico:** a `_handle_show_archived_history`, `_handle_show_bugs`, `_handle_show_roles`: parámetro `--limit`/`summary` por defecto (top-N + agregados; detalle bajo demanda). Regla simple: ningún handler retorna >X registros (p. ej. 25) sin flag explícito. Documentar en MANUAL:SCRIPT-GLOSSARY.
- **Fricción que elimina:** el mayor vector de erosión de contexto interno del sistema (827 filas ≈ 30k tokens en una llamada, F §3.3).
- **Aporte:** el Runtime pasa a ser coherente con MANUAL:LAZY-LOAD; sesiones con cuota estable.

### P7. Lint de gobernanza (CI local o `vgit` hook)
- **Cambio técnico:** `pytest`/script `validate_governance.py` que verifique en cada push: JSON del registry sin claves duplicadas y UUIDs con formato uniforme (F4); `triggers.json` ↔ `skills/*.md` paridad y paths existentes; Referencias `SP:*`/`KERNEL:*` citadas por scripts existen en los mirrors ACTIVE (hubiera atrapado F15/F16); artefactos del Runtime con `generated_at` fresco al commitear; `/skills/` sin huérfanos.
- **Fricción que elimina:** el patrón recurrente "drift documental detectado por auditorías post-hoc" (el propio repo tiene 2 auditorías E2E previas en `handoffs/`).
- **Aporte:** convierte SP:CONSISTENCY de aspiración a gate mecánico; ~0 tokens (corre en Terminal).

### P8. Higiene del repo (costo de cada clon multi-agente)
- **Cambio técnico:** mover Scout a `scout/` (o repo aparte); `git rm --cached` del `.m4a` (40.5 MB) y dumps raíz; `README_VANTAGE.txt` (4.2 MB) a almacenamiento externo o genera bajo demanda vía `vdigest`; renombrar/aclarar `MANUAL.md` (Scout) para no colisionar con el Manual del sistema; eliminar `config/layer_2.env.example` (F10); decidir retiro o re-validación de la infra serial MCP (F9).
- **Aporte:** clones −99% de peso para la familia GitHub-only y agentes bash; menos superficie de confusión de descubrimiento (§2).

### Matriz de impacto / ROI

| # | Cambio | Fricción eliminada | Tokens | Latencia | Robustez | Esfuerzo | Prioridad |
|---|---|---|---|---|---|---|---|
| P1 | Resolver v3 (page puntual + dict + notion_utils) | resolves de minutos; telemetría ciega | ▲▲ (contextos de ask) | ▲▲▲ | ▲▲ | M | **P0** |
| P6 | Presupuestos de payload en Agent API | ~30k tokens por ask mal elegido | ▲▲▲ | ▲ | ▲ | S | **P0** |
| P5 | Saneamiento documental (5 fixes) | boots con instrucciones falsas/contradictorias | ▲▲ | — | ▲ | S | **P0** |
| P3 | Versión API + paths + generated_at únicos | futuras deprecaciones; staleness mentiroso | — | ▲ | ▲▲▲ | M | P1 |
| P2 | Grafo honesto + PK única | IDs ambiguos; grafo muerto | — | — | ▲▲▲ | M | P1 |
| P4 | `vload` de repo + tests | UUID lookup manual; sin regresión del loader | ▲▲ | ▲ | ▲▲ | M | P1 |
| P7 | Lint de gobernanza | drift detectado a posteriori | ▲ (evita re-lecturas) | — | ▲▲ | M | P2 |
| P8 | Higiene del repo | clones 45 MB; confusión de descubrimiento | ▲ | ▲ (red) | ▲ | S | P2 |

### Suposiciones explícitas (por transparencia, conforme a las reglas de la auditoría)
1. Se asume que los mirrors `Documentación/ACTIVE/*.md` del commit auditado reflejan las páginas Notion vivas (sin `NOTION_TOKEN` no fue posible verificarlo; `.vsync_manifest.json` registra hashes SHA-256 por documento que permitirían verificar con `vsync_doc.py --dry` en el entorno del operador).
2. El comportamiento en producción de `vantage.py ask` (número real de requests y latencias) es estimación derivada del código (throttle 0.35 s, tamaños de data source del índice), no de un perfil en vivo.
3. La cuantificación de tokens usa el aproximado ~4 bytes/token para texto en español; el orden de magnitud es robusto aunque el factor varíe por tokenizador.
4. No se evaluó el pipeline de ingesta L1/L3 (ya auditado en `handoffs/AUDITORIA_TRACKER_E2E_2026-09-11.md`); este informe se limita a L0 + gobernanza de descubrimiento.
