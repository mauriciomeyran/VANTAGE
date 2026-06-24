# VANTAGE — Audit & Documentation (Phase 0)

**Audit Date:** 2026-06-24  
**Last Updated:** 2026-06-24 (sesión cierre)  
**Codebase Root:** `/Users/mauriciomeyran/Documents/04-Vantage_CV/`  
**Objective:** Comprehensive documentation of all scripts, fields, and pipeline flows without making changes.

---

## Executive Summary

VANTAGE is a multi-layer job search automation pipeline with three active layers:
- **Layer 1:** Active Recon (feed ingestion, scoring, gate logic)
- **Layer 2:** Strategic Search — **directorio vacío, sin scripts**
- **Layer 3:** Mail Pipeline (Gmail → Groq → Notion)
- **Layer 4:** Documentation Sync (Notion ↔ Git)
- **Dashboard:** Web interface for manual operations

**Key Findings (estado original):**
- No mcp.json found in codebase
- Field naming inconsistencies (trailing spaces in Notion field names)
- Multiple scoring implementations (v6.4 en layer_1_run.py vs deterministic en scoring_deterministic.py)
- Hash generation centralized en feed_processor.py
- Cross-layer deduplication with priority L1 > L2 > L3

**Resolución sesión 2026-06-24:** Ver sección "Changelog de Correcciones" al final.

---

## Script Documentation

### feed_processor.py
**Location:** `Layer_1/scripts/feed_processor.py`  
**Role in pipeline:** Ingests JSON feeds (from discovery sources like you.com/Grok/LinkedIn) and writes to Notion Opportunities DB  
**Triggered by:** Manual CLI execution with `--file` and `--layer` flags  
**Reads:**
- JSON feed files (from `feeds/` directory)
- `alias_map.json` (brand resolution)
- Notion DB schema (via Client)
- Environment variables: `NOTION_TOKEN`, `NOTION_DB_OPPORTUNITIES`, `NOTION_ARCHIVE_PAGE_ID`

**Writes:**
- Notion pages (new entries only)
- Notion fields: title, brand, status, hash, layer, fetch_status, location, holding, apply_url, Source_Type, Prioridad, notes
- Dry run markdown files (when `--dry-run` flag used)

**Field value map:**
- `status`: "Target" (CLEAN), "REVIEW_NEEDED" (blocked/review)
- `layer`: "L1", "L2", "L3" (from CLI arg)
- `fetch_status`: "aggregator", "career_page"
- `Source_Type `: "Vacante" — usa nombre dinámico del schema, no hardcodea el espacio
- `Prioridad`: "4" (default for new entries)
- `Fuente`: "Agregador" (if fetch_status=aggregator), "Career Page Oficial" (if career_page)

**Failure modes:**
- Missing URL → disposition="REVIEW_NEEDED", notes="MISSING_URL"
- Hard blocked brand → disposition="BLOCKED"
- Alias not resolved → disposition="REVIEW_NEEDED"
- Role excluded → disposition="BLOCKED"
- Dedup cross-layer match → disposition="REVIEW_NEEDED"
- URL gate failure → disposition="REVIEW_NEEDED"
- Empty title → disposition="REVIEW_NEEDED"

**Open questions:** Ninguna.

---

### layer_1_run.py
**Location:** `Layer_1/scripts/layer_1_run.py`  
**Role in pipeline:** Main pipeline runner — URL gate, scoring, gate logic, next action assignment  
**Triggered by:** Manual execution or cron/scheduler  
**Reads:**
- Notion VANTAGE_TRACKER DB (via data_sources API)
- Environment variables: `NOTION_TOKEN`

**Writes:**
- Notion fields: Fetch, Status, Gate_Decision, Next_Action, Fuente, VM_Scope, Score, Match, Role_Class

**Field value map:**
- `Fetch`: "Accesible", "Bloqueado", "Parcial"
- `Status`: "Expirada", "Nueva", "Target", "Postulado", "En proceso", "Negociando", "Sin respuesta", "Rechazado", "Archivar", "Contratado"
- `Gate_Decision`: "CREATE", "BLOCKED", "APPLIED"
- `Next_Action`: "Re-check", "Reparar URL", "Verificar JD", "Archivar", "Follow-up", "Interview prep"
- `Fuente`: "Agregador", "Career Page Oficial"
- `VM_Scope`: "Alto", "Bajo"
- `Score`: 0-100 (number)
- `Match`: "Muy Alto", "Alto", "Medio", "Bajo"
- `Role_Class`: "VM", "Pivote", "Otro"

**Failure modes:**
- URL gate failure → Status="Expirada", Fetch="Bloqueado", Gate_Decision="BLOCKED", Next_Action="Archivar"
- Protected terminal states → No modification
- API errors → Logged as warnings, continues processing

**Fix aplicado 2026-06-24:** `Source_Type ` (con espacio) normalizado en Pasos 0, 2 y 3. Antes leía sin espacio → valor vacío silencioso → gate() trataba como "Vacante" por default. Corregido Fix A.

**Open questions:** Ninguna.

---

### gate_logic.py
**Location:** `Layer_1/scripts/gate_logic.py`  
**Role in pipeline:** Standalone gate logic evaluator with terminal state protection  
**Triggered by:** Manual execution for testing  
**Reads:**
- Notion DB (via data_sources API)
- Environment variables: `NOTION_TOKEN`

**Writes:**
- Notion fields: Gate_Decision, Next_Action

**Field value map:**
- `Gate_Decision`: "CREATE", "BLOCKED"
- `Next_Action`: "Follow-up", "Interview prep", "Re-check", "Reparar URL", "Verificar JD", "Archivar"

**Failure modes:**
- Terminal state protection prevents overwriting manual "Archivar"/"Expirada" actions
- Missing fields → Uses empty string defaults

**Open questions:** Ninguna.

---

### scoring_deterministic.py
**Location:** `Layer_1/scripts/scoring_deterministic.py`  
**Role in pipeline:** ~~Alternative scoring implementation~~ **DEPRECADO** — reemplazado por layer_1_run.py v6.4  
**Status:** Conservado en disco por referencia histórica. No ejecutar.

**Scoring canónico:** `layer_1_run.py` v6.4 (escala 0-100). 29 entradas actualizadas en sesión anterior.

**Open questions:** Ninguna (decisión tomada).

---

### notion_utils.py
**Location:** `Layer_1/scripts/notion_utils.py`  
**Role in pipeline:** Notion API client wrapper with caching, throttling, retry logic  
**Triggered by:** All scripts that interact with Notion  
**Reads:**
- Environment variables: `NOTION_TOKEN`, `NOTION_VERSION`, `NOTION_MIN_INTERVAL`, `NOTION_CACHE_TTL`, `NOTION_MAX_RETRIES`
- Cache file: `notion_cache.json`
- Metrics file: `notion_metrics.json`

**Writes:**
- Cache file: `notion_cache.json`
- Metrics file: `notion_metrics.json`

**Failure modes:**
- 401 errors → Never retried (credential error)
- 429/5xx errors → Retried with exponential backoff
- Cache failures → Falls through to API

**Open questions:** Ninguna.

---

### backfill_hash.py
**Location:** `Layer_1/scripts/backfill_hash.py`  
**Role in pipeline:** Backfills hash field for existing records that don't have it  
**Triggered by:** Manual execution  
**Reads:**
- Notion VANTAGE_TRACKER and ARCHIVO_TRACKER (via data_sources API)
- Environment variables: `NOTION_TOKEN`

**Writes:**
- Notion field: `hash` (rich_text)

**Field value map:**
- `hash`: SHA-256 hex string (64 characters)

**Failure modes:**
- Missing brand/title/url → Skips record
- Hash computation error → Logs error, continues

**Open questions:** Ninguna.

---

### fetch_hashes.py
**Location:** `Layer_1/scripts/fetch_hashes.py`  
**Role in pipeline:** Obtiene hashes de VANTAGE y ARCHIVO TRACKER y actualiza entity_index_v2.json  
**Triggered by:** Manual execution  
**Reads:**
- Notion VANTAGE_TRACKER y ARCHIVO_TRACKER (via data_sources API, paginación completa)
- `entity_index_v2.json` (en Layer_1/scripts/)

**Writes:**
- `entity_index_v2.json` (patches hash coverage)

**Reescritura 2026-06-24 (Fix E):**
- Eliminados 34 page IDs hardcodeados
- Migrado a paginación completa via `data_sources/{id}/query` (mismo patrón que consolidate_duplicates.py)
- Ruta de entity_index resuelta desde `__file__` (no más `~/output/` hardcodeado)
- Token via `dotenv`, httpx consistente con el resto del codebase

**Failure modes:**
- API errors → raise_for_status, aborta
- Missing entity_index → Exits with error message

**Open questions:** Ninguna.

---

### consolidate_duplicates.py
**Location:** `Layer_1/scripts/consolidate_duplicates.py`  
**Role in pipeline:** Detects and consolidates duplicate entries in VANTAGE_TRACKER  
**Triggered by:** Manual execution (`vdedup`)  
**Reads:**
- Notion VANTAGE_TRACKER (via data_sources API)
- Environment variables: `NOTION_TOKEN`

**Writes:**
- Notion: Archives duplicates to ARCHIVO_TRACKER, updates primary with merged notes
- Notion field updates: Notas, URL

**Fix aplicado 2026-06-24 (Fix C):** Lectura de `Source_Type ` corregida (con espacio). Dato no usado en lógica de dedup — bug inocuo pero corregido para consistencia.

**Nota:** ARCHIVO_TRACKER_DB no tiene la propiedad `Source_Type ` — se omite intencionalmente en `_move_to_archivo()`. Correcto.

**Open questions:** Ninguna.

---

### assign_next_action.py
**Location:** `Layer_1/scripts/assign_next_action.py`  
**Role in pipeline:** Assigns Next_Action based on gate logic with terminal state protection  
**Triggered by:** Manual execution  
**Reads:**
- Notion DB (via data_sources API)
- Environment variables: `NOTION_TOKEN`

**Writes:**
- Notion fields: Gate_Decision, Next_Action

**Field value map:**
- `Gate_Decision`: "CREATE", "BLOCKED", "APPLIED"
- `Next_Action`: "Follow-up", "Interview prep", "Re-check", "Reparar URL", "Verificar JD", "Archivar"

**Fix aplicado 2026-06-24 (Fix B):**
- `Source_Type` → `Source_Type ` (con espacio)
- DS_ID obsoleto (`4e542b37...`) → DS_ID canónico (`442938be...`)

**Deuda técnica activa:** No pagina — usa `client.data_sources.query(...)["results"]` sin loop. Con >100 registros trunca silenciosamente. Único pendiente abierto de esta sesión.

**Open questions:**
- **[PENDIENTE]** Agregar paginación completa (mismo patrón que consolidate_duplicates.py / layer_1_run.py).

---

### layer_3_mail.py
**Location:** `Layer_3/scripts/layer_3_mail.py`  
**Nota:** El audit original tenía la ruta incorrecta (`Layer_1/scripts/`). Ruta real: `Layer_3/scripts/`.  
**Role in pipeline:** Gmail → Groq → Notion pipeline for job email ingestion  
**Triggered by:** Cron/scheduled execution  
**Reads:**
- Gmail IMAP (label: `.Jobs`)
- Groq API (`llama-3.1-8b-instant`, temperature=0)
- Notion DB (for dedup check)
- Environment variables: `GMAIL_USER`, `GMAIL_APP_PASS`, `GROQ_API_KEY`, `NOTION_TOKEN`, `NOTION_DB_ID`

**Writes:**
- Notion pages (new job entries)
- Notion fields: Rol, Marca, Status, layer, Source_Type, Holding, Fuente, URL, **hash** (añadido Fix D)
- Heartbeat file: `~/.vantage/l3_heartbeat.json`

**Field value map:**
- `Status`: "Target"
- `layer`: "L3"
- `Source_Type`: "Vacante" — **nota:** escribe sin trailing space (inconsistente con schema). Ver nota en Source_Type.
- `Fuente`: "Indeed", "OCC", "LinkedIn", "Computrabajo", "Bumeran", "Puma", "Swarovski", "Other"
- `Holding`: Valid holdings list or "Investigar"
- `hash`: SHA-256 hex (64 chars) — añadido 2026-06-24

**Fix aplicado 2026-06-24 (Fix D):**
- Añadida función `_compute_l3_hash(rol, marca, url)` compatible con `feed_processor.compute_dedup_hash`
- Hash escrito en `create_notion_page()` al momento de creación
- Elimina dependencia de backfill posterior para cross-layer dedup

**Hash logic L3:**
- Si URL comienza con "http": `sha256("url:{url}")`
- Fallback: `sha256("agg:{brand}|{title}|")`
- Compatible con el branch `career_page`/`aggregator` de feed_processor

**Failure modes:**
- Groq rate limit → Retries con backoff exponencial (hasta 90s + jitter)
- Groq JSON invalid → Deja email sin leer para retry en siguiente ejecución
- Hard block brands → Skips silenciosamente (EXCLUDED_SENDERS + _HARD_BLOCK_BRANDS regex)
- Notion API error → Logs error, continues
- URL sintética/alucinada por Groq → Rechazada por `canonicalize_url()` (SYNTHETIC_CT_PATTERNS)

**Open questions:** Ninguna.

---

### profile_fit.py
**Location:** `Layer_1/scripts/profile_fit.py`  
**Role in pipeline:** Profile fit validation and exclusion rules  
**Triggered by:** Imported by layer_1_run.py, cleanup_misfits.py, assign_next_action.py  
**Reads:** `alias_map.json`  
**Writes:** None (utility library — pure functions)  
**Open questions:** Ninguna.

---

### cleanup_misfits.py
**Location:** `Layer_1/scripts/cleanup_misfits.py`  
**Role in pipeline:** Marca como Expirada vacantes fuera de perfil VM  
**Triggered by:** Manual execution  
**Reads:** Notion VANTAGE_TRACKER (via data_sources API)  
**Writes:** Notion fields: Status, Gate_Decision, Next_Action  
**Nota:** Ya usaba `Source_Type ` con espacio — correcto desde origen.  
**Open questions:** Ninguna.

---

### vantage.py / agent_api.py / query_layer.py / context_layer.py / graph_layer.py
Sin cambios esta sesión. Documentación original válida.

---

### vsync_doc.py
**Location:** `Layer_4/scripts/vsync_doc.py` (alias `vdoc`)  
**Role in pipeline:** Sync bidireccional Notion ↔ local markdown  
**Flags:** `dry`, `notion`, `local`  
**vdoc run + vdoc notion aplicados** al cierre de esta sesión (operador confirmó).  
**Open questions:** Ninguna.

---

### generate_entity_index_v2.py / resolver_layer_v1.py
Sin cambios esta sesión. Documentación original válida.

---

## Field Documentation

### hash
**How is it generated:** SHA-256 por `compute_dedup_hash()` en feed_processor.py  
**Inputs:**
- `career_page`: `sha256("url:{normalized_url}")`
- `aggregator`: `sha256("agg:{brand}|{title}|{location}")`
- job_id válido: `sha256("job_id:{job_id}")`
- Fallback: `sha256("fallback:{brand}|{title}|{location}")`

**Scripts que escriben hash:**
- `feed_processor.py` — L1/L2, en ingestion
- `layer_3_mail.py` — L3, en ingestion (añadido Fix D, 2026-06-24)
- `backfill_hash.py` — backfill para entradas históricas sin hash

**Estado:** L3 ya no depende de backfill para dedup cross-layer.

---

### Source_Type / Source_Type (trailing space)
**Situación real del campo en Notion:** El campo existe con trailing space: `"Source_Type "`.  
**Estado del sweep 2026-06-24:**

| Archivo | Uso | Estado |
|---|---|---|
| `feed_processor.py` | Schema dinámico — no hardcodea el nombre | ✅ |
| `layer_1_run.py` Paso 1.5 | `Source_Type ` con espacio | ✅ |
| `layer_1_run.py` Pasos 0, 2, 3 | Corregido Fix A | ✅ |
| `cleanup_misfits.py` | `Source_Type ` con espacio | ✅ |
| `assign_next_action.py` | Corregido Fix B | ✅ |
| `consolidate_duplicates.py` | Corregido Fix C (dato inocuo) | ✅ |
| `layer_3_mail.py` | Escribe `"Source_Type"` sin espacio | ⚠️ |

**Nota layer_3_mail.py:** Escribe `"Source_Type": {"select": ...}` sin trailing space. Si Notion tiene el campo con espacio, esta escritura puede fallar silenciosamente o crear un campo nuevo. Sin embargo, dado que el campo `Source_Type` no es crítico para el pipeline de L3 (no afecta gate ni scoring), el impacto es bajo. Fix pendiente si se observan errores en Notion.

---

### Job_ID
**Estado:** Huérfano en Python. Feed_processor lo lee del feed para el hash pero no lo persiste en Notion. Solo se popula vía Make.com (`layer_1_blueprint.json`).  
**Convención de nomenclatura:** Ninguna propia del pipeline Python. Make.com mapea el campo `JOB_ID` desde el feed externo.  
**Impacto si vacío:** Hash cae a URL o composite key — sin impacto funcional.

---

### Fetch (Notion) vs fetch_status (interno)
**Son campos distintos, sin colisión:**
- `fetch_status` (interno, Python): `"aggregator"` / `"career_page"` — determina estrategia de hash y URL gate. Nunca escrito directamente en Notion como `fetch_status`.
- `Fetch` (Notion, rich_text): `"Accesible"` / `"Bloqueado"` / `"Parcial"` — escrito por `layer_1_run.py` Paso 2.
- `feed_processor.py` mapea `fetch_status` → campo `Fuente` en Notion, no a `Fetch`.

---

### Positioning Mode
**No existe en ningún script del pipeline.** Concepto exclusivo del Career Canon (L0). No hay campo en Notion ni referencia en código.

---

### Gate_Decision
**CREATE triggers:**
- Source_Type in ["Inbound", "Referencia", "Networking"] (bypass automático)
- Source_Type == "Vacante" AND Fetch in ("Accesible", "Parcial") AND VM_Scope == "Alto"
- Source_Type == "Vacante" AND Fetch in ("Accesible", "Parcial") AND Role_Class == "Pivote" AND has_vm_title_signal(rol)

**BLOCKED triggers:**
- is_role_excluded(rol)
- resolve_alias_flags(marca) → hard_block=True
- Ninguna condición CREATE cumplida

**Scripts que escriben Gate_Decision:** layer_1_run.py, gate_logic.py, assign_next_action.py

---

### Scoring (canónico: layer_1_run.py v6.4, escala 0-100)
- Base: +40 (pasó URL gate)
- Visual signal en JD: +20
- Company impact (high impact brands): +15
- Role quality (manager/coordinator/lead): +10
- Recruiter presence: +10
- Innovation DNA: +5
- Scale bonus: +5
- Pivot bonus: +5
- Agency bonus: +5
- Luxury heritage: +5
- Cap: 100

**Match levels:** Muy Alto ≥80 · Alto ≥60 · Medio ≥40 · Bajo <40  
**scoring_deterministic.py:** DEPRECADO.

---

## Dry Trace — Estado actualizado post-fixes

### Entrada L3 (post Fix D)
1. Gmail → Groq extrae vacante
2. `_compute_l3_hash()` calcula hash en el momento
3. `create_notion_page()` escribe: Rol, Marca, Status, layer, Source_Type, Holding, Fuente, URL, **hash**
4. `layer_1_run.py` corre: URL Gate → Scoring → Gate → Next_Action
5. Cross-layer dedup funcional desde el momento de creación (no requiere backfill)

---

## Changelog de Correcciones — Sesión 2026-06-24

| Fix | Archivo | Descripción | Riesgo |
|---|---|---|---|
| A | `layer_1_run.py` | `Source_Type` → `Source_Type ` en Pasos 0, 2, 3 | Bajo |
| B | `assign_next_action.py` | `Source_Type` → `Source_Type ` + DS_ID obsoleto corregido | Bajo |
| C | `consolidate_duplicates.py` | Lectura `Source_Type` → `Source_Type ` (dato inocuo) | Bajo |
| D | `layer_3_mail.py` | Añadido hash en creación (`_compute_l3_hash`) | Bajo |
| E | `fetch_hashes.py` | Reescritura completa — paginación DS, sin IDs hardcodeados | Medio |

**Resueltos de sesiones anteriores (on record):**
- `scoring_deterministic.py` deprecado — `layer_1_run.py` v6.4 es canónico (29 entradas actualizadas)
- `assign_next_action.py` corregido de `select` → `rich_text` para `Next_Action`
- `feed_processor.py` + `layer_3_mail.py` + `cleanup_misfits.py`: sweep Source_Type parcial completado

**Documentación:**
- `vdoc run` + `vdoc notion` aplicados al cierre por el operador

---

## Pendiente Único Activo

**assign_next_action.py — Sin paginación**
- **Issue:** `client.data_sources.query(data_source_id=ds_id)["results"]` sin loop — trunca silenciosamente en >100 registros
- **Fix:** Implementar loop de paginación idéntico al de `consolidate_duplicates.py` / `layer_1_run.py`
- **Riesgo:** MEDIO — Next_Action no se asigna a entradas fuera de la primera página
- **Dependencia:** Ninguna
- **Prioridad:** Alta cuando el tracker supere 100 entradas activas

---

## Appendix: Data Source IDs canónicos

| DB | ID canónico | Fuente de verdad |
|---|---|---|
| VANTAGE_TRACKER (data source) | `442938be-fc42-828f-b72e-076818d65a5b` | consolidate_duplicates.py, layer_1_run.py, fetch_hashes.py |
| VANTAGE_TRACKER (DB) | `596938be-fc42-836b-aea7-814a1491bd47` | generate_entity_index_v2.py |
| ARCHIVO_TRACKER (data source) | `674696fd-94b6-464a-ac1f-64b0cc917e15` | backfill_hash.py, fetch_hashes.py |
| ARCHIVO_TRACKER (DB) | `4ec34e1b-5286-48c9-afbd-d57c6eb76053` | generate_entity_index_v2.py |
| TRACKER V2 (obsoleto) | `4e542b37-6e52-4418-89b7-a0eeb3138307` | schema_full.json, assign_next_action.py (corregido) |

---

**Audit actualizado — 2026-06-24**
