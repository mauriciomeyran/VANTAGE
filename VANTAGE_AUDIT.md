# VANTAGE — Audit & Documentation (Phase 0)

**Audit Date:** 2026-06-24  
**Codebase Root:** `/Users/mauriciomeyran/Documents/04-Vantage_CV/`  
**Objective:** Comprehensive documentation of all scripts, fields, and pipeline flows without making changes.

---

## Executive Summary

VANTAGE is a multi-layer job search automation pipeline with three active layers:
- **Layer 1:** Active Recon (feed ingestion, scoring, gate logic)
- **Layer 2:** Strategic Search (currently empty - placeholder)
- **Layer 3:** Mail Pipeline (Gmail → Groq → Notion)
- **Layer 4:** Documentation Sync (Notion ↔ Git)
- **Dashboard:** Web interface for manual operations

**Key Findings:**
- No mcp.json found in codebase
- Field naming inconsistencies (trailing spaces in Notion field names)
- Multiple scoring implementations (v6.4 in layer_1_run.py vs deterministic in scoring_deterministic.py)
- Hash generation centralized in feed_processor.py
- Cross-layer deduplication with priority L1 > L2 > L3

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
- `Source_Type`: "Vacante"
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

**Open questions:**
- What happens when `consolidated_by_l0` flag is missing on mixed L1/L2 feeds? (Warning only, continues processing)

---

### layer_1_run.py
**Location:** `Layer_1/scripts/layer_1_run.py`  
**Role in pipeline:** Main pipeline runner - URL gate, scoring, gate logic, next action assignment  
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

**Open questions:**
- Why does `Source_Type` have a trailing space in some queries but not others?

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

**Open questions:**
- None

---

### scoring_deterministic.py
**Location:** `Layer_1/scripts/scoring_deterministic.py`  
**Role in pipeline:** Alternative scoring implementation (simpler than layer_1_run.py v6.4)  
**Triggered by:** Manual execution  
**Reads:**
- Notion DB (via data_sources API)
- Environment variables: `NOTION_TOKEN`

**Writes:**
- Notion fields: VM_Scope, Score, Match, Role_Class

**Field value map:**
- `VM_Scope`: "Alto", "Bajo"
- `Score`: 2-8 (number, not 0-100)
- `Match`: "Muy Alto", "Alto", "Medio", "Bajo"
- `Role_Class`: "VM", "Pivote", "Otro"

**Failure modes:**
- API errors → Logged, continues

**Open questions:**
- **[ISSUE]** Two different scoring implementations exist (v6.4 in layer_1_run.py vs this file). Which is correct?

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

**Field value map:** N/A (utility library)

**Failure modes:**
- 401 errors → Never retried (credential error)
- 429/5xx errors → Retried with exponential backoff
- Cache failures → Falls through to API

**Open questions:**
- None

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

**Open questions:**
- None

---

### fetch_hashes.py
**Location:** `Layer_1/scripts/fetch_hashes.py`  
**Role in pipeline:** Fetches hash values from Notion and patches entity_index_v2.json  
**Triggered by:** Manual execution  
**Reads:**
- Notion pages (via API)
- `entity_index_v2.json`

**Writes:**
- `entity_index_v2.json` (patches hash coverage)

**Field value map:** N/A

**Failure modes:**
- API errors → Logs error, continues
- Missing entity_index → Exits with error

**Open questions:**
- **[DECISION NEEDED]** This script has hardcoded page IDs. Should it use data source query instead?

---

### consolidate_duplicates.py
**Location:** `Layer_1/scripts/consolidate_duplicates.py`  
**Role in pipeline:** Detects and consolidates duplicate entries in VANTAGE_TRACKER  
**Triggered by:** Manual execution  
**Reads:**
- Notion VANTAGE_TRACKER (via data_sources API)
- Environment variables: `NOTION_TOKEN`

**Writes:**
- Notion: Archives duplicates to ARCHIVO_TRACKER, updates primary with merged notes
- Notion field updates: Notas, URL

**Field value map:** N/A

**Failure modes:**
- Concurrent writes → Aborts with MAX_EXPECTED_RESULTS error
- API errors → Logs, continues

**Open questions:**
- None

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

**Failure modes:**
- Terminal state protection prevents overwriting
- API errors → Logged, continues

**Open questions:**
- None

---

### layer_3_mail.py
**Location:** `Layer_3/scripts/layer_3_mail.py`  
**Role in pipeline:** Gmail → Groq → Notion pipeline for job email ingestion  
**Triggered by:** Cron/scheduled execution  
**Reads:**
- Gmail IMAP (label: `.Jobs`)
- Groq API
- Notion DB (for dedup)
- Environment variables: `GMAIL_USER`, `GMAIL_APP_PASS`, `GROQ_API_KEY`, `NOTION_TOKEN`, `NOTION_DB_ID`

**Writes:**
- Notion pages (new job entries)
- Notion fields: Rol, Marca, Status, layer, Source_Type, Holding, Fuente, URL
- Heartbeat file: `~/.vantage/l3_heartbeat.json`

**Field value map:**
- `Status`: "Target"
- `layer`: "L3"
- `Source_Type`: "Vacante"
- `Fuente`: "Indeed", "OCC", "LinkedIn", "Computrabajo", "Bumeran", "Puma", "Swarovski", "Other"
- `Holding`: Valid holdings list or "Investigar"

**Failure modes:**
- Groq rate limit → Retries with backoff
- Groq JSON invalid → Leaves email unread for retry
- Hard block brands → Skips silently
- Notion API error → Logs error, continues

**Open questions:**
- None

---

### profile_fit.py
**Location:** `Layer_1/scripts/profile_fit.py`  
**Role in pipeline:** Profile fit validation and exclusion rules  
**Triggered by:** Imported by layer_1_run.py and other scripts  
**Reads:**
- `alias_map.json`

**Writes:** None (utility library)

**Field value map:** N/A

**Failure modes:** None (pure functions)

**Open questions:**
- None

---

### vantage.py
**Location:** `Layer_1/scripts/vantage.py`  
**Role in pipeline:** Unified runtime entrypoint for query, context, agent API operations  
**Triggered by:** CLI commands  
**Reads:**
- `entity_index_v2.json`
- Notion (via sub-modules)
- Environment variables: `NOTION_TOKEN`

**Writes:**
- `entity_index_v2.json` (when sync() called)

**Field value map:** N/A

**Failure modes:**
- Missing sub-modules → Runtime error
- Sync failure → Preserves old index

**Open questions:**
- None

---

### agent_api.py
**Location:** `Layer_1/scripts/agent_api.py`  
**Role in pipeline:** Natural language query interface for entity operations  
**Triggered by:** CLI or programmatic calls  
**Reads:**
- `entity_index_v2.json`
- Notion (via query_layer, context_layer)
- Environment variables: `NOTION_TOKEN`

**Writes:** None (read-only operations)

**Field value map:** N/A

**Failure modes:**
- Missing graph_layer → Graceful degradation
- API errors → Returns error in response

**Open questions:**
- None

---

### vsync_doc.py
**Location:** `Layer_4/scripts/vsync_doc.py`  
**Role in pipeline:** Syncs Notion documentation to local markdown files  
**Triggered by:** Manual execution  
**Reads:**
- Notion pages (Kernel, System Prompt, Career Canon, Manual, Cheat Sheet)
- Environment variables: `NOTION_TOKEN`

**Writes:**
- Local markdown files in `- Documentación/ACTIVE/`

**Field value map:** N/A

**Failure modes:**
- API errors → Logs error, continues
- Git sync failure → Logs warning

**Open questions:**
- None

---

### query_layer.py
**Location:** `Layer_1/scripts/query_layer.py`  
**Role in pipeline:** Entity index query interface  
**Triggered by:** Imported by vantage.py, agent_api.py  
**Reads:**
- `entity_index_v2.json`

**Writes:** None (read-only)

**Field value map:** N/A

**Failure modes:**
- Missing index → File error
- Missing resolver_layer → Runtime error

**Open questions:**
- None

---

### context_layer.py
**Location:** `Layer_1/scripts/context_layer.py`  
**Role in pipeline:** Assembles full context (entity + metadata + content) for an entity  
**Triggered by:** Imported by agent_api.py  
**Reads:**
- `entity_index_v2.json`
- Notion pages and blocks
- Environment variables: `NOTION_TOKEN`

**Writes:** None (read-only)

**Field value map:** N/A

**Failure modes:**
- Unknown entity → ResolverError
- API errors → ResolverError

**Open questions:**
- None

---

### graph_layer.py
**Location:** `Layer_1/scripts/graph_layer.py`  
**Role in pipeline:** Graph operations (archived_from, backlinks)  
**Triggered by:** Imported by agent_api.py  
**Reads:**
- `graph_v2.json`
- `backlinks_v2.json`

**Writes:** None (read-only)

**Field value map:** N/A

**Failure modes:**
- Missing JSON files → File error

**Open questions:**
- None

---

### generate_entity_index_v2.py
**Location:** `Layer_1/scripts/generate_entity_index_v2.py`  
**Role in pipeline:** Regenerates entity_index_v2.json from Notion  
**Triggered by:** Manual execution or via vantage.py sync()  
**Reads:**
- Notion VANTAGE_TRACKER and ARCHIVO_TRACKER (via data_sources API)
- Environment variables: `NOTION_TOKEN`

**Writes:**
- `entity_index_v2.json`

**Field value map:** N/A

**Failure modes:**
- API errors → Logs error, aborts
- Preserves old index on failure

**Open questions:**
- None

---

### resolver_layer_v1.py
**Location:** `Layer_1/scripts/resolver_layer_v1.py`  
**Role in pipeline:** Resolves entity_id/canonical_id to page_url  
**Triggered by:** Imported by query_layer.py  
**Reads:**
- `entity_index_v2.json`
- `resolver_registry_v2.json`
- Notion (via data_sources API)
- Environment variables: `NOTION_TOKEN`

**Writes:** None (read-only)

**Field value map:** N/A

**Failure modes:**
- Unknown entity → ResolverError
- Missing registry → ResolverError
- API errors → ResolverError

**Open questions:**
- None

---

## Field Documentation

### hash
**How is it generated:** SHA-256 hash computed by `compute_dedup_hash()` in feed_processor.py  
**From what inputs:** 
- If `fetch_status == "career_page"`: URL (normalized)
- If `fetch_status == "aggregator"`: composite key (brand|title|location)
- If job_id exists and is not generated: job_id
- Fallback: composite key (brand|title|location)

**When in the pipeline:** 
- Generated during feed ingestion (feed_processor.py)
- Backfilled for existing records (backfill_hash.py)

**What script writes it:** 
- `feed_processor.py` (new entries)
- `backfill_hash.py` (existing records)

**Exact string values:** 64-character hexadecimal SHA-256 string

**What happens when missing/null:** 
- New entries: Always computed
- Existing entries: backfill_hash.py can populate
- Missing in index: entity marked as orphan candidate

**Where it sits in pipeline:** Class A field - written at ingestion, used for cross-layer deduplication

---

### Fetch (Notion field)
**Valid values today:** "Accesible", "Bloqueado", "Parcial"  
**What script writes it:** 
- `layer_1_run.py` (URL re-check)
- `feed_processor.py` (sets initial value based on is_agregador())

**What blank means operationally:** 
- Blank → Treated as if URL needs checking
- "Bloqueado" → URL failed validation, Next_Action="Reparar URL"
- "Parcial" → URL partially accessible, Next_Action="Verificar JD"
- "Accesible" → URL valid, can proceed to gate logic

**Exact strings used in code:** 
- `layer_1_run.py`: "Accesible", "Bloqueado", "Parcial"
- `feed_processor.py`: "aggregator", "career_page" (internal mapping to Fetch field)

**What happens when missing/null:** 
- layer_1_run.py will attempt to check URL
- Gate logic treats missing as "Bloqueado" equivalent

---

### VM_Scope
**Classification logic:** 
- "Alto" if role title contains VM keywords: "visual merchandising", "visual", "vm", "brand environment", "estándares visuales", "store design", "retail design"
- "Bajo" otherwise

**Inputs determining value:** Role title field

**Why all entries might show same value:** 
- If all roles lack VM keywords, all will be "Bajo"
- If data source is filtered to VM roles only, all will be "Alto"

**Exact strings:** "Alto", "Bajo"

**What script writes it:** 
- `layer_1_run.py` (get_vm_scope function)
- `scoring_deterministic.py` (get_vm_scope function)

**What happens when missing/null:** Computed from title, never null

---

### Prioridad
**Scoring logic end-to-end:** 
- **layer_1_run.py v6.4:** 0-100 scale based on:
  - Base: +40 (passed URL gate)
  - Visual signal: +20 (keywords in JD)
  - Company impact: +15 (high impact brands)
  - Role quality: +10 (manager, coordinator, lead, etc.)
  - Recruiter presence: +10
  - Innovation DNA: +5 (innovative companies)
  - Scale bonus: +5 (scale company + manager)
  - Pivot bonus: +5 (pivot roles)
  - Agency bonus: +5 (experience agencies)
  - Luxury heritage: +5 (luxury brands)
  - Capped at 100

- **scoring_deterministic.py:** 2-8 scale based on VM_Scope + Role_Class matrix:
  - Alto + VM = 8
  - Alto + Pivote = 6
  - Bajo + VM = 5
  - Bajo + Pivote = 3
  - Other = 2

**What script writes it:** 
- `feed_processor.py` (sets default "4" for new entries)
- `layer_1_run.py` (updates based on v6.4 scoring)
- `scoring_deterministic.py` (updates based on matrix)

**Exact strings:** "1", "2", "3", "4", "5", "6", "7", "8" (select field in Notion)

**What happens when missing/null:** 
- New entries: Default "4"
- Existing entries: Recalculated by scoring scripts

**[ISSUE]** Two different scoring systems exist with incompatible scales

---

### Job_ID
**Data type in Notion:** rich_text  
**Who writes it:** 
- `feed_processor.py` (from feed JSON)
- `layer_1_blueprint.json` (Make.com integration)

**Naming convention:** 
- From feed: Whatever the source provides
- Generated pattern detection: `^(?:gen[_-]?|auto[_-]?|tmp[_-]?|unknown|n/?a|none|null|)$` (treated as generated/invalid)

**Why it might be empty:** 
- Feed doesn't provide job_id
- Job_id is generated/placeholder
- URL-based dedup used instead

**Exact strings:** Variable (from source) or empty

**What happens when missing/null:** 
- Hash generation falls back to URL or composite key
- No impact on pipeline if URL exists

---

### Status
**Valid values and exact strings:** 
- "Nueva" (new entry)
- "Target" (ready for action)
- "Postulado" (applied)
- "En proceso" (in process)
- "Negociando" (negotiating)
- "Sin respuesta" (no response)
- "Expirada" (expired)
- "Rechazado" (rejected)
- "Archivar" (archive)
- "Retirado" (withdrawn)
- "Contratado" (hired)
- "REVIEW_NEEDED" (feed_processor only)

**Scripts that filter by Status:** 
- `layer_1_run.py`: Skips "Expirada", "Rechazado", "Archivar" for URL gate
- `profile_fit.py`: Protected statuses (Postulado, En proceso, Negociando, Sin respuesta, Contratado) prevent auto-cleanup
- Terminal statuses (Expirada, Rechazado, Archivar, Retirado) prevent auto-cleanup
- `agent_api.py`: Filters for active vs archived

**What happens when missing/null:** Treated as "Nueva" equivalent

---

### Gate_Decision
**CREATE vs BLOCKED triggers:** 
**layer_1_run.py gate() function:**
- **CREATE if:**
  - Source_Type in ["Inbound", "Referencia", "Networking"] (bypass)
  - Source_Type == "Vacante" AND Fetch in ("Accesible", "Parcial") AND VM_Scope == "Alto"
  - Source_Type == "Vacante" AND Fetch in ("Accesible", "Parcial") AND Role_Class == "Pivote" AND has_vm_title_signal(rol)

- **BLOCKED if:**
  - is_role_excluded(rol) returns true
  - resolve_alias_flags(marca) returns hard_block=true
  - None of the CREATE conditions met

**Threshold:** No numeric threshold - boolean logic based on field combinations

**Where defined:** 
- `layer_1_run.py` (main gate function)
- `gate_logic.py` (standalone implementation)
- `assign_next_action.py` (gate_logic_complete function)

**What script writes it:** 
- `layer_1_run.py`
- `gate_logic.py`
- `assign_next_action.py`

**Exact strings:** "CREATE", "BLOCKED", "APPLIED"

**What happens when missing/null:** Recalculated on next pipeline run

---

### Fuente / Source_Type
**Are they the same field:** No - separate fields

**Fuente:**
- **Who writes it:** `layer_1_run.py` (determine_fuente function)
- **Values:** "Agregador", "Career Page Oficial"
- **Logic:** Based on domain matching (linkedin.com, indeed.com, occ.com.mx, glassdoor.com, bumeran.com, computrabajo.com)
- **When written:** Paso 0.5 of layer_1_run.py

**Source_Type:**
- **Who writes it:** 
  - `feed_processor.py` (sets "Vacante")
  - `layer_1_blueprint.json` (Make.com sets "Vacante")
  - Dashboard scripts (reads and can write)
- **Values:** "Vacante", "Inbound", "Referencia", "Networking"
- **Logic:** Categorical field indicating entry source
- **When written:** At ingestion

**[ISSUE]** Source_Type field has trailing space in some places ("Source_Type " vs "Source_Type")

---

### Fetch (Notion field) vs fetch (action)
**Conflation analysis:** 
- **Notion field "Fetch":** Stores URL accessibility status ("Accesible", "Bloqueado", "Parcial")
- **Action "fetch":** Not a standard action in codebase
- **Internal field "fetch_status":** Used in feed_processor.py ("aggregator", "career_page")

**Where conflated:** 
- `feed_processor.py` uses `fetch_status` internally
- `layer_1_run.py` uses `Fetch` Notion field
- No direct conflation in code - distinct purposes

**[DECISION NEEDED]** Naming inconsistency could cause confusion - consider renaming internal field

---

## Dry Trace Simulation

### Representative Input: New LinkedIn Job Entry

**Step 1: Layer 3 Mail Pipeline (layer_3_mail.py)**
1. Gmail fetches unread email from .Jobs label
2. Groq extracts job: rol="VM Coordinator", marca="Zara", url="https://linkedin.com/jobs/view/123456"
3. Canonicalize URL: Removes tracking params, normalizes path
4. VM filter: Passes (contains "VM")
5. Dedup check: URL not in Notion → proceed
6. Write to Notion:
   - Rol: "VM Coordinator"
   - Marca: "Zara"
   - Status: "Target"
   - layer: "L3"
   - Source_Type: "Vacante"
   - Fuente: "LinkedIn"
   - URL: canonicalized URL
   - Holding: "Inditex" (normalized)
   - **hash**: Not set (Layer 3 doesn't compute hash)

**Step 2: Layer 1 Pipeline (layer_1_run.py)**
1. URL Gate: LinkedIn is aggregator → bypass validation, set Fetch="Accesible"
2. Fuente assignment: "Agregador"
3. Scoring v6.4:
   - Base: +40
   - Visual signal: +20 (VM in title)
   - Company impact: +15 (Zara/Inditex)
   - Role quality: +10 (Coordinator)
   - Score: 85
   - Match: "Muy Alto"
   - VM_Scope: "Alto"
   - Role_Class: "VM"
4. Gate logic: Fetch="Accesible" AND VM_Scope="Alto" → Gate_Decision="CREATE"
5. Next_Action: "Re-check"
6. **hash**: Still empty (Layer 3 entries lack hash)

**Step 3: Backfill Hash (backfill_hash.py)**
1. Query for records without hash
2. Compute hash: fetch_status="aggregator" → hash = sha256(f"agg:{brand|title|location}")
3. Write hash to Notion

**Step 4: Entity Index Generation (generate_entity_index_v2.py)**
1. Query all records from VANTAGE_TRACKER
2. Generate entity_id: "TRACKER:H_{hash[:16]}"
3. Write to entity_index_v2.json

**Assumptions made without validation:**
- Layer 3 entries will eventually get hash via backfill
- No cross-layer dedup occurs until hash is populated
- Gateway validation bypass for aggregators is always safe

---

## Notion API Payload Audit

### feed_processor.py write_to_notion()
**Function:** `build_notion_properties()` → `write_to_notion()`

**Payload structure:**
```json
{
  "title_prop": {"title": [{"text": {"content": "..."}}]},
  "brand_prop": {"rich_text": [{"text": {"content": "..."}}]} or {"select": {"name": "..."}},
  "status_prop": {"select": {"name": "Target"|"REVIEW_NEEDED"}},
  "hash_prop": {"rich_text": [{"text": {"content": "..."}}]},
  "layer_prop": {"select": {"name": "L1"|"L2"|"L3"}},
  "fetch_status_prop": {"select": {"name": "aggregator"|"career_page"}},
  "fuente_prop": {"rich_text": [{"text": {"content": "Agregador"|"Career Page Oficial"}}]},
  "location_prop": {"rich_text": [{"text": {"content": "..."}}]},
  "holding_prop": {"rich_text": [{"text": {"content": "..."}}]},
  "url_prop": {"url": "https://..."},
  "Source_Type ": {"select": {"name": "Vacante"}},
  "Prioridad": {"select": {"name": "4"}},
  "notes_prop": {"rich_text": [{"text": {"content": "..."}}]}
}
```

**[CRITICAL BUG]** `Source_Type ` has trailing space in property name - this must match Notion schema exactly

---

### layer_1_run.py updates
**Multiple pages.update() calls with different payloads:**

**URL Gate failure:**
```json
{
  "Fetch": {"rich_text": [{"text": {"content": "Bloqueado"}}]},
  "Status": {"select": {"name": "Expirada"}},
  "Next_Action": {"rich_text": [{"text": {"content": "Archivar"}}]},
  "Gate_Decision": {"select": {"name": "BLOCKED"}}
}
```

**Fuente assignment:**
```json
{
  "Fuente": {"rich_text": [{"text": {"content": "Agregador"|"Career Page Oficial"}}]}
}
```

**Scoring update:**
```json
{
  "VM_Scope": {"rich_text": [{"text": {"content": "Alto"|"Bajo"}}]},
  "Score": {"number": 0-100},
  "Role_Class": {"select": {"name": "VM"|"Pivote"|"Otro"}},
  "Match": {"select": {"name": "Muy Alto"|"Alto"|"Medio"|"Bajo"}}
}
```

**Gate logic update:**
```json
{
  "Gate_Decision": {"select": {"name": "CREATE"|"BLOCKED"|"APPLIED"}},
  "Next_Action": {"select": {"name": "Re-check"|"Reparar URL"|"Verificar JD"|"Archivar"|"Follow-up"|"Interview prep"}}
}
```

**[CRITICAL BUG]** Next_Action is written as rich_text in URL Gate but select in Gate Logic - inconsistent types

---

### layer_3_mail.py create_notion_page()
**Payload structure:**
```json
{
  "Rol": {"title": [{"text": {"content": "..."}}]},
  "Marca": {"rich_text": [{"text": {"content": "..."}}]},
  "Status": {"select": {"name": "Target"}},
  "layer": {"select": {"name": "L3"}},
  "Source_Type ": {"select": {"name": "Vacante"}},
  "Holding": {"rich_text": [{"text": {"content": "..."}}]},
  "Fuente": {"rich_text": [{"text": {"content": "..."}}]},
  "URL": {"url": "https://..."}
}
```

**[CRITICAL BUG]** `Source_Type ` has trailing space - must match Notion schema

---

## Cross-Reference with External Configurations

### mcp.json
**Result:** Not found in codebase

### Notion Integration Configurations
**layer_1_blueprint.json (Make.com integration):**
- Database ID: "4e542b37-6e52-4418-89b7-a0eeb3138307"
- Field mappings:
  - "Source_Type " (with trailing space)
  - "Rol" (title)
  - "Marca" (text)
  - "URL" (url)
  - "JD" (text)
  - "JOB_ID" (text)
  - "Raw Source" (select)
  - "Status" (select, default "Nueva")
  - "Fuente" (select, default "Agregador")

**schema_full.json (archive):**
- Database ID: "b14cc6fc-0151-4c22-8b11-690162236107"
- Data Source ID: "4e542b37-6e52-4418-89b7-a0eeb3138307"
- This appears to be an old schema reference

**resolver_registry_v2.json:**
- Maps source_db names to data_source_ids
- Used by resolver_layer_v1.py

---

## Prioritized List of Changes

### Critical Bugs (Fix Immediately)
1. **[CRITICAL] Source_Type field name inconsistency**
   - **Issue:** Trailing space in "Source_Type " in feed_processor.py, layer_3_mail.py, layer_1_blueprint.json
   - **Impact:** Schema mismatch could cause API errors
   - **Dependency:** None
   - **Risk:** HIGH - API failures
   - **Fix:** Standardize to "Source_Type" (no trailing space) across all files

2. **[CRITICAL] Next_Action field type inconsistency**
   - **Issue:** Written as rich_text in URL Gate but select in Gate Logic (layer_1_run.py)
   - **Impact:** Type mismatch could cause API errors or data loss
   - **Dependency:** None
   - **Risk:** HIGH - Data corruption
   - **Fix:** Standardize to select type everywhere

3. **[CRITICAL] Two incompatible scoring systems**
   - **Issue:** layer_1_run.py uses 0-100 scale, scoring_deterministic.py uses 2-8 scale
   - **Impact:** Confusion about which is correct, inconsistent scores
   - **Dependency:** None
   - **Risk:** MEDIUM - Data inconsistency
   - **Fix:** Decide on one system and deprecate the other

### High Priority (Fix Soon)
4. **Layer 3 entries lack hash at creation**
   - **Issue:** layer_3_mail.py doesn't compute hash, relies on backfill
   - **Impact:** Cross-layer dedup doesn't work until backfill runs
   - **Dependency:** None
   - **Risk:** MEDIUM - Duplicate entries possible
   - **Fix:** Add hash computation to layer_3_mail.py using feed_processor.compute_dedup_hash

5. **fetch_hashes.py uses hardcoded page IDs**
   - **Issue:** Not scalable, requires manual updates
   - **Impact:** Maintenance burden
   - **Dependency:** None
   - **Risk:** LOW - Maintenance issue
   - **Fix:** Use data source query instead

6. **Missing validation in feed_processor.py**
   - **Issue:** consolidated_by_l0 flag warning only, no enforcement
   - **Impact:** Mixed L1/L2 feeds without dedup could create duplicates
   - **Dependency:** None
   - **Risk:** MEDIUM - Data quality
   - **Fix:** Add enforcement mode or auto-consolidation

### Medium Priority (Technical Debt)
7. **Internal field naming inconsistency**
   - **Issue:** fetch_status (internal) vs Fetch (Notion field)
   - **Impact:** Confusion for developers
   - **Dependency:** None
   - **Risk:** LOW - Developer experience
   - **Fix:** Rename internal field to avoid confusion

8. **Layer 2 is empty**
   - **Issue:** Layer 2 directory exists but no scripts
   - **Impact:** Incomplete architecture
   - **Dependency:** None
   - **Risk:** LOW - Architecture
   - **Fix:** Implement or remove Layer 2

9. **Multiple gate logic implementations**
   - **Issue:** gate_logic.py, assign_next_action.py, layer_1_run.py all have gate logic
   - **Impact:** Maintenance burden, potential divergence
   - **Dependency:** None
   - **Risk:** LOW - Maintenance
   - **Fix:** Consolidate to single module

### Low Priority (Nice to Have)
10. **Add schema validation before Notion writes**
    - **Issue:** No validation that field values match Notion schema
    - **Impact:** Silent failures possible
    - **Dependency:** None
    - **Risk:** LOW - Data quality
    - **Fix:** Add schema validation step

11. **Improve error handling in layer_3_mail.py**
    - **Issue:** Some errors leave email unread, could cause infinite retry loop
    - **Impact:** Resource waste
    - **Dependency:** None
    - **Risk:** LOW - Resource usage
    - **Fix:** Add max retry count and fallback to mark as seen

12. **Add comprehensive logging**
    - **Issue:** Inconsistent logging across scripts
    - **Impact:** Difficult debugging
    - **Dependency:** None
    - **Risk:** LOW - Debugging
    - **Fix:** Standardize logging framework

---

## Open Questions Requiring Resolution

1. **Scoring System:** Which scoring system is canonical - layer_1_run.py v6.4 (0-100) or scoring_deterministic.py (2-8)?
2. **Source_Type Field:** Should the trailing space in "Source_Type " be removed from Notion schema or kept in code?
3. **Next_Action Type:** Should Next_Action be rich_text or select in Notion schema?
4. **Layer 2 Purpose:** What is the intended purpose of Layer 2, and should it be implemented?
5. **Hash Backfill:** Should hash computation be moved to ingestion time (Layer 3) to avoid backfill dependency?
6. **Gate Logic Consolidation:** Which gate logic implementation should be canonical?
7. **Fetch Status Naming:** Should internal fetch_status be renamed to avoid confusion with Fetch field?

---

## Appendix: Data Source IDs

**Current Data Source IDs (from code):**
- VANTAGE_TRACKER: "442938be-fc42-828f-b72e-076818d65a5b" (backfill_hash.py)
- VANTAGE_TRACKER: "596938be-fc42-836b-aea7-814a1491bd47" (generate_entity_index_v2.py)
- ARCHIVO_TRACKER: "674696fd-94b6-464a-ac1f-64b0cc917e15" (backfill_hash.py)
- ARCHIVO_TRACKER: "4ec34e1b-5286-48c9-afbd-d57c6eb76053" (generate_entity_index_v2.py)
- TRACKER V2 (old): "4e542b37-6e52-4418-89b7-a0eeb3138307" (schema_full.json)

**[ISSUE]** Multiple different IDs for same databases - need verification of which is correct

---

## Estado de Fixes Post-Auditoría

| Fix | Descripción | Estado |
|-----|-------------|--------|
| A | Source_Type trailing space (layer_1_run.py) | CERRADO |
| B | assign_next_action.py DS_ID | CERRADO |
| C | consolidate_duplicates.py | CERRADO |
| D | Hash L3 en creación (layer_3_mail.py) | CERRADO |
| E | fetch_hashes.py reescritura | CERRADO |
| F | Paginación assign_next_action.py + corrección DS_ID | **VALIDADO EN PRODUCCIÓN — 2026-06-26** |

---

**Audit Complete**
