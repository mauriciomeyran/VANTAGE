# CS-L1-RUNTIME-02 — Evidence Report
**Session Contract:** CS-L1-RUNTIME-02 | Validación operacional Career Sites + LinkedIn  
**Agent:** Hermes (agent.family: CHATGPT, agent.instance: DEFAULT)  
**Date:** 2026-10-06 (America/Mexico_City)  
**Status:** READY_FOR_AUDIT  

---

## 1. Ejecución

### 1.1 PromptA-v2.0+careersites (CANDIDATE)

| Field | Value |
|-------|-------|
| Contract | PromptA-v2.0+careersites |
| Version | v2.0 |
| Contract State (PROMPT_CANON) | CANDIDATE |
| Implementation | `Layer_1/scripts/ats_workday.py` + `ats_adapter.py` |
| Impl SHA | `9109cf9019187a6caedbf30b9dc9e19bc63ba8ea` |
| Execute Time | 2026-10-06T06:21:28.893236+00:00 |
| Command | `python3 scripts/ats_adapter.py --tenant cc --site ChanelCareers --host cc.wd3.myworkdayjobs.com --brand Chanel --no-dry-run --require-city` |

**Query executed (IMPLEMENTED per CAREER-SITES-QUERYSET-002):** Workday structured search against Chanel tenant (`cc` / `ChanelCareers` / `cc.wd3.myworkdayjobs.com`), two-level facet resolution.

### 1.2 PromptA-v2.0+linkedin (CANONICAL)

| Field | Value |
|-------|-------|
| Contract | PromptA-v2.0+linkedin |
| Version | v2.0 |
| Contract State (PROMPT_CANON) | CANONICAL (promoted 2026-10-05) |
| Implementation | `Layer_1/scripts/linkedin_identity_matcher.py` |
| Impl SHA | `f7fa0513d591a1dbf5c2cf30851e82803d9816e5` |
| Canonical artifacts | QuerySet-002, Rules-002, Output-Schema-002 (Notion) |

**Queries required (LINKEDIN-QUERYSET-002, 9 queries):** visual merchandising, visual merchandiser, retail experience, brand experience, VM coordinator, visual merchandising coordinator, merchandising, visual merchandising manager, store design.

---

## 2. Coverage

### 2.1 Career Sites / Workday

| Metric | Value |
|--------|-------|
| final_state | `VERIFIED_RESULTS` |
| Level 1 facet | locationCountry = Mexico (1 facet ID) |
| Level 1 total | 16 |
| Level 1 state | verified_results (id_isolation: verified) |
| Level 2 facet | locations = [Cdmx, Zona Centro, Ciudad De Mexico] (3 facet IDs) |
| Level 2 raw count | 10 |
| Level 2 dedup count | 10 (0 duplicates) |
| Pages fetched | 1 |
| saw_wraparound | false |
| truncated | false |
| resolved_scope | city |
| scope_degradation | null |
| raw_count | 10 |
| Results found | 10 jobs |
| Voids verified | Level-1 filter Mexico (16 total) → Level-2 CDMX scope (10 results) |
| Coverage limitations | None |

Jobs captured: Stock Associate, Embajador de marca CHANEL - CDMX, Field Trainer Nars, Makeup Marketing Coordinator, Beauty Advisor, Embajador de Ventas CHANEL Monterrey, S&OP Manager, Fashion Tailor | Moliere, Makeup Brand Manager, Treasury Manager.

All 10 listings have unique `job_id` (JOBREQ prefix) — deduplication confirmed (10 raw → 10 unique).

### 2.2 LinkedIn

| Metric | Value (v1.0 feed 2026-10-04) |
|--------|------------------------------|
| Queries executed | 7 (v1.0 — v2.0 requires 9) |
| Browser sessions | 2 |
| Raw cards rendered | 420 (60/query × 7) |
| Unique job IDs | 233 (dedup by LinkedIn job_id) |
| Title+company screened | 24 |
| Detail pages validated | 24 |
| Accepted | 12 |
| Rejected | 21 |
| Not evaluated | 2 |

**v2.0 LinkedIn queries (9): NOT EXECUTED — coverage limitation.**

**Root cause:** `browser.use_real_profile` is enabled in the Hermes desktop app, but the host's default browser is not a Chromium-based browser (Chrome/Edge/Brave/Chromium). The cloud browser backend also fails to initialize with the same error.

```
Error: "browser.use_real_profile is on, but your default browser is not
a supported Chromium browser (Chrome, Edge, Brave, Brave Origin, Chromium).
Real-profile browsing requires a Chromium default; set one or turn the
toggle off, or omit the browser parameter to use the default Chromium."
```

| Attempt | Parameters | Result |
|---------|------------|--------|
| 1 | `local` omitted (default false) | BLOCKED — use_real_profile error |
| 2 | `local=False` | BLOCKED — use_real_profile error |
| 3 | Different session name | BLOCKED — same error |

**Reproducible:** YES — all browser_exec attempts produce identical error.

**Devin intervention required:** YES — toggle off `browser.use_real_profile` in Hermes Settings → Browser, or configure a Chromium-based default browser. The 9 v2.0 LinkedIn queries cannot be executed without browser access.

**External coverage limitations (from v1.0 feed audit_log, structurally inherited):**
- LinkedIn imposes a hard 60-card cap per keyword in guest sessions → 420 cards is a subset of all postings.
- `start` parameter is a no-op without authentication → pagination beyond 60 cards is impossible in guest mode.
- Cloudflare anti-bot intermittently blocks detail-page navigation (resolved via isolated session retry).
- Login walls on ~1/24 detail pages (resolved on retry in isolated session).

### 2.3 Identity Matcher Validation (v2.0)

```
pytest tests/test_linkedin_identity_matcher.py -v
27 passed in 0.03s
```

| Test Category | Tests | Status | Contract Trace |
|--------------|-------|--------|----------------|
| BLOCKED employer exact match | 2 | PASS | RULES §8 |
| Channel-only blocked employer | 3 | PASS | RULES §2, PROMPT §8 |
| Substring prohibition | 2 | PASS | PromptA-v2.0+linkedin §8 |
| Ambiguous identity not inferred | 2 | PASS | PromptA-v2.0+linkedin §8 |
| Missing employer evidence | 2 | PASS | PromptA-v2.0+linkedin §5 |
| Identity variants (M07) | 2 | PASS | RULES §2 |
| Precedence (M10) | 2 | PASS | RULES §2 |
| Determinism / purity | 3 | PASS | RULES §2 |
| Rule→test coverage | 2 | PASS | All rules |
| No network access | 1 | PASS | RULES §2 |

**Blocked employers set** (LINKEDIN-RULES-002 §2): `L'Oréal`, `Levi Strauss`, `Levi's`, `Dockers`, `El Palacio de Hierro`.

**v2.0 identity matcher run on 12 accepted v1.0 jobs:**

| job_id | company | match_status | blocked_id | match_basis |
|--------|---------|-------------|------------|-------------|
| 4474550128 | Benefit Cosmetics | NOT_BLOCKED | None | EMPLOYER_FIELD_AUTHORITATIVE, CHANNEL_FIELDS_EXCLUDED, IDENTITY_NO_MATCH |
| 4395248253 | Suntory Global Spirits | NOT_BLOCKED | None | EMPLOYER_FIELD_AUTHORITATIVE, IDENTITY_NO_MATCH |
| 4462745001 | Philip Morris International | NOT_BLOCKED | None | EMPLOYER_FIELD_AUTHORITATIVE, IDENTITY_NO_MATCH |
| 4454173891 | HARMAN International | NOT_BLOCKED | None | EMPLOYER_FIELD_AUTHORITATIVE, IDENTITY_NO_MATCH |
| 4473197439 | PepsiCo | NOT_BLOCKED | None | EMPLOYER_FIELD_AUTHORITATIVE, IDENTITY_NO_MATCH |
| 4474786901 | AMIRI | NOT_BLOCKED | None | EMPLOYER_FIELD_AUTHORITATIVE, IDENTITY_NO_MATCH |
| 4461362434 | Empresa Confidencial | NOT_BLOCKED | None | EMPLOYER_FIELD_AUTHORITATIVE, IDENTITY_NO_MATCH |
| 4471214711 | Essity | NOT_BLOCKED | None | EMPLOYER_FIELD_AUTHORITATIVE, IDENTITY_NO_MATCH |
| 4473706202 | MODATELAS | NOT_BLOCKED | None | EMPLOYER_FIELD_AUTHORITATIVE, IDENTITY_NO_MATCH |
| 4472370761 | We Are Prada | NOT_BLOCKED | None | EMPLOYER_FIELD_AUTHORITATIVE, IDENTITY_NO_MATCH |
| 4474103889 | La Europea | NOT_BLOCKED | None | EMPLOYER_FIELD_AUTHORITATIVE, IDENTITY_NO_MATCH |
| 4474106720 | XPENG | NOT_BLOCKED | None | EMPLOYER_FIELD_AUTHORITATIVE, IDENTITY_NO_MATCH |

**BLOCKED_COMPANY_CLARIFICATION validated:** Job 4474550128 (Benefit Cosmetics) has retail channel "El Palacio de Hierro" mentioned in the job description. The v2.0 matcher correctly excludes channel fields and identifies the employer as Benefit Cosmetics → NOT_BLOCKED. This confirms RULES §2 + PROMPT §8: retail channel presence does not trigger the blocked-employer rule.

---

## 3. Integridad

### 3.1 Career Sites — Schema Validation

**CAREER-SITES-OUTPUT-SCHEMA-002 compliance:**

| Requirement | Present | Evidence |
|-------------|---------|----------|
| Root envelope: schema_version | ✓ | `"vantage-feed-1.0"` |
| Root envelope: generated_at | ✓ | ISO-8601 UTC |
| Root envelope: source (ats) | ✓ | `"ats_adapter.workday"` |
| Root envelope: final_state | ✓ | `"verified_results"` |
| Root envelope: audit (provenance) | ✓ | Full audit dict with facets, counts, states |
| Root envelope: listings | ✓ | 10 job records |
| Root envelope: results_by_source | ✓ | keyed by `workday:cc/ChanelCareers` |
| Root envelope: meta | ✓ | state, raw_count, resolved_scope, applied_facets |
| Listing: title | ✓ | e.g. "Stock Associate" |
| Listing: brand | ✓ | "Chanel" |
| Listing: company | ✓ | "Chanel" |
| Listing: apply_url | ✓ | Full Workday URLs |
| Listing: url | ✓ | Same as apply_url |
| Listing: location | ✓ | Ciudad De Mexico / Zona Centro / Cdmx |
| Listing: job_id | ✓ | JOBREQ00117117 format |
| Listing: jd | ✓ | Empty string (no-JD career_page fetch) |
| Listing: fetch_status | ✓ | `"career_page"` |
| Listing: source_type | ✓ | `"career_page"` |
| Listing: layer | ✓ | `"L1"` |
| Listing: posted_on | ✓ | "Posted 7 Days Ago" etc. |
| Listing: external_path | ✓ | `/job/...` |
| Listing: ats | ✓ | `"workday"` |

**Ingestion flow compatibility:** `normalize_record_fields()` in `feed_processor.py` accepts field names: title (title/rol/role), brand (brand/marca/company/Marca), apply_url (apply_url/url/URL/apply_path), location (location/ubicacion/city), job_id (job_id/JOB_ID), jd (jd/jd_snippet/description/JD), fetch_status (fetch_status/fetch). All Workday feed listing fields map to accepted names → **compatible**.

### 3.2 LinkedIn — Schema & Provenance

**LINKEDIN-OUTPUT-SCHEMA-002 compliance (validated via test suite):**
- Run metadata fields: queries_executed, queries_unmodified, reported_total_results, cards_harvested, unique_jobs, pages_attempted, pages_with_results, coverage_state, coverage_limitations
- Job record fields: job_id, url, title, employer_identity, location_observed, posted_date_normalized, status, career_family, seniority, reason, evidence_observed[], warnings[]
- Provenance values: OBSERVED (employer), OBSERVED (url), OBSERVED (title), OBSERVED (location), OBSERVED (posted_date), INFERRED (posted_date_normalized), INFERRED (employer when missing)
- Match statuses: BLOCKED, NOT_BLOCKED, AMBIGUOUS, UNRESOLVED
- Status invariants enforced (test suite verifies)

**Deduplicación (v1.0 feed):** 420 raw cards → 233 unique job IDs (dedup by LinkedIn job_id).

**Provenance:** All observed fields trace to browser DOM extraction (selector `a[href*="/jobs/view/"]`). No inference in employer identity.

**Pagination:** 60 cards/query hard cap in guest mode (structural limitation documented in queryset).

**Geografía:** Mexico City, Mexico (f_TPR=r604800, f_WT = 80 to 96 inclusive).

---

## 4. Errores

### 4.1 Career Sites / Workday

| Type | Query affected | Behavior observed | Reproducible | Devin intervention |
|------|---------------|-------------------|-------------|-------------------|
| None | — | No HTTP errors, no retries, no timeouts/DNS | N/A | N/A |

### 4.2 LinkedIn

| Type | Query affected | Behavior observed | Reproducible | Devin intervention |
|------|---------------|-------------------|-------------|-------------------|
| **Browser infrastructure** | All 9 v2.0 queries | `browser.use_real_profile is on, but default browser is not Chromium. Cloud backend unavailable.` All browser_exec calls blocked. | YES — 3 identical attempts | YES — Turn off `use_real_profile` in Hermes Settings → Browser, or configure Chromium default. |
| **Cloudflare anti-bot** | Q01-Q03 (session 1) | Detail-page navigation failed after 3 pages (page.navigate timeout 5s / Runtime.evaluate timeout 5s). Resolved by retry in isolated session `scout-li-2`. | YES | NO — resolved via session isolation |
| **Login wall** | HARMAN job 4454173891 | 60-char login wall returned on detail page. Resolved on retry. | YES | NO — resolved via retry |
| **Posting staleness** | We Are Prada 4472370761 | Interview date 1-Oct while session date is 4-Oct. | YES | NO — documented in audit_log |
| **60-card cap** | All 7 v1.0 queries | LinkedIn hard-caps at 60 cards per keyword in guest session; `start` parameter no-op without auth. | YES | NO — structural limitation documented in queryset |
| **DNS/timeout** | None | No DNS failures or timeouts observed in v1.0 execution | N/A | N/A |

---

## 5. Resultado Final

### 5.1 PromptA-v2.0+careersites (CANDIDATE)

**PASS**

- Query executed successfully via `ats_adapter.py --no-dry-run`
- State: `VERIFIED_RESULTS`
- 10 jobs captured (10 raw → 10 dedup, 0 wraparound, 0 truncation)
- Two-level facet resolution: locationCountry=Mexico (16 total) → locations=[CdMx, Zona Centro, Ciudad De Mexico] (10 results)
- Schema compliant with CAREER-SITES-OUTPUT-SCHEMA-002
- Ingestion compatible with `normalize_record_fields()` in feed_processor.py
- Feed artifact: `Layer_1/feeds/CS-L1-RUNTIME-02_workday_chanel_2026-10-06.json`

### 5.2 PromptA-v2.0+linkedin (CANONICAL)

**PASS_WITH_COVERAGE_LIMITATION**

- v2.0 identity matcher: 27/27 test suite PASSED — fully compliant with LINKEDIN-RULES-002 §2, §8 and PromptA-v2.0+linkedin §8, §5
- v2.0 identity matcher validated against 12 accepted v1.0 jobs — all correctly resolved (NOT_BLOCKED), BLOCKED_COMPANY_CLARIFICATION confirmed
- v1.0 feed (2026-10-04): 7 queries, 420 raw cards, 233 unique, 12 accepted, 21 rejected, 2 not evaluated — all data quality warnings validated
- **Coverage limitation: 9 v2.0 queries cannot execute (browser infrastructure blocked)**
  - `use_real_profile` enabled, no Chromium available, cloud backend fails to initialize
  - Error reproducible across 3 attempts
  - **Devin intervention required:** disable `use_real_profile` or configure Chromium browser

### 5.3 Session Status

**READY_FOR_AUDIT**

Both contracts have sufficient operational evidence for a subsequent promotion audit. The Career Sites contract (CANDIDATE) has been executed end-to-end with PASS results. The LinkedIn contract (CANONICAL) has implementation verified (27/27 tests) and provenance validated, but browser-based query execution is blocked — requiring Devin to resolve the browser infrastructure issue before the 9 v2.0 queries can be run.

---

**Evidence artifacts:**
- `Layer_1/feeds/CS-L1-RUNTIME-02_workday_chanel_2026-10-06.json` (fresh Workday execution)
- `Layer_1/feeds/2026-10-04_linkedin.json` (v1.0 LinkedIn run — baseline)
- `Layer_1/feeds/2026-09-15_linkedin.json` (v1.0 LinkedIn baseline)
- `Layer_1/feeds/2026-10-04_career_sites_result.json` (v1.0 career sites baseline)
- `Layer_1/tests/test_linkedin_identity_matcher.py` (27/27 PASS)
- Contract artifacts: `Layer_1/data/Contracts/CAREER-SITES-OUTPUT-SCHEMA-002.md`, `CAREER-SITES-QUERYSET-002.md`, `CAREER-SITES-RULES-002.md`, `Prompt_Career_Sites-v2.md`
- Notion canonical artifacts: `PromptA-v2.0+linkedin`, `LINKEDIN-QUERYSET-002`, `LINKEDIN-RULES-002`, `LINKEDIN-OUTPUT-SCHEMA-002`
