# CAREER SITES RULES v2
## Version 2.0 — Canonical Rules for Career Sites Discovery

**Status:** CANDIDATE
**Based on:** Prompt_Career_Sites-v2 + Career Canon + feed evidence
**Created:** 2026-10-05

---

## 1. EMPLOYER IDENTITY

### 1.1 EMPLOYER AUTHORITY

The employer identity is determined SOLELY by the explicit employer/company field in the job posting.

**RULE CS-001:** Retail channel, store, client, or distribution partner mentions MUST NOT become employer identity. These fields are excluded from employer matching.

**RULE CS-002:** Brand mentions in non-employer fields (retail_channel, client, distribution_partner) MUST NOT trigger employer-based blocking rules.

---

## 2. INCLUSION CRITERIA

### 2.1 TITLE VALIDATION

**RULE CS-003:** Title evaluation MUST use the complete title string. Partial title matching is not permitted for exclusion.

**RULE CS-004:** Titles containing excluded terms MUST be rejected regardless of context.

**Exclusion Matching Logic:**
- Exact phrase match for multi-word terms (e.g., "Store Manager", "Assistant Manager")
- Token-level match for single-word terms (e.g., "Assistant", "Director", "VP")
- "Assistant Manager" → ACCEPTED (valid seniority)
- "Assistant" alone → REJECTED (excluded term)
- "Asistente" → REJECTED (excluded term)
- "Auxiliar" → REJECTED (excluded term)

### 2.2 VISUAL SIGNAL REQUIREMENT

**RULE CS-005:** Every accepted result MUST contain an explicit visual signal within the job description that aligns with Visual Merchandising, Brand Experience, or Store Design.

### 2.3 POSTING AGE

**RULE CS-006:** Preferred posting age is ≤14 days. Posting age ≤21 days is acceptable ONLY if fit remains strong. Posting age >21 days MUST be rejected.

### 2.4 LOCATION

**RULE CS-007:** Roles outside Mexico City (CDMX) MUST be rejected. Remote roles outside Mexico MUST be rejected.

---

## 3. BLOCKING RULES

### 3.1 BLOCKED COMPANIES

**RULE CS-008:** Jobs from the following companies MUST be rejected:
- L'Oréal (all divisions)
- Levi's
- Dockers
- El Palacio de Hierro

**IMPLEMENTATION:** hard_blocks.json + hard_block_gate.py (blocked_employer_term). Substring case-insensitive match.

**RULE CS-009:** Blocked company detection MUST be identity-based, not substring-based. Partial overlap (e.g., "Dockers Heroico") MUST NOT trigger blocking.

---

## 4. WORKDAY STRUCTURED GEOGRAPHY RULES

### 4.1 FACET RESOLUTION

**RULE CS-010:** Workday location MUST be resolved from `response.facets` via POST /jobs with empty `appliedFacets`. No dedicated `/facets` endpoint exists.

**IMPLEMENTED:** ats_workday.py — `WorkdayClient.discover()` POST /jobs con `appliedFacets: {}`, extrae `response.facets`.

**RULE CS-011:** Location facets MUST be applied via `appliedFacets` in the query payload. `searchText` MUST NOT be used as a geographic filter.

**IMPLEMENTED:** ats_workday.py — `search()` construye payload con `appliedFacets`; `searchText` es filtro secundario opcional (never primary).

### 4.2 CONTEXT ISOLATION

**RULE CS-012:** Facet IDs are tenant-specific and context-dependent. The complete context (tenant, site, facetParameter, descriptor) MUST be preserved. NEVER reuse a facet ID across tenants or sites.

**RULE CS-013:** NEVER hardcode location IDs. HTTP 200 with results does NOT prove the facet matched the requested location.

### 4.3 TWO-LEVEL RESOLUTION

**RULE CS-014:** Workday location resolution follows a two-level model:
- Level 1: Country (e.g., Mexico)
- Level 2: City/Location (e.g., Cdmx, Zona Centro, Ciudad De Mexico)

A single city may resolve to multiple Workday facet values. All resolved values MUST be included in `appliedFacets`.

### 4.4 SCOPE DEGRADATION

**RULE CS-015:** Scope degradation (city → country) MUST be explicit. When a city cannot be resolved, the system MUST fall back to country and explicitly record the degradation. Silent degradation is forbidden.

---

## 5. VERIFIED_EMPTY REQUIREMENTS

### 5.1 VERIFIED_EMPTY CONDITIONS

**RULE CS-016:** A Workday query result of 0 postings MAY be classified as `VERIFIED_EMPTY` ONLY when ALL of the following are satisfied:
- Location facet was successfully resolved
- `appliedFacets` was used in the query
- Query terminated without wraparound or truncation
- `searchText` did NOT act as the location mechanism

**RULE CS-017:** A 403, Cloudflare, Akamai, DNS failure, timeout, unresolvable facet, missing facets, or incomplete query MUST NOT be reported as zero vacancies. These MUST be classified as BLOCKED, DNS_FAILURE, TIMEOUT, or UNKNOWN.

---

## 6. PAGINATION AND WRAPAROUND

### 6.1 PAGINATION

**RULE CS-018:** Workday pagination MUST use offset-based pagination with a safety cap (default: 2000) to prevent infinite loops.

**RULE CS-019:** Wraparound circular pagination MUST be detected. When a page provides no new job postings, pagination MUST terminate.

### 6.2 DEDUPLICATION

**RULE CS-020:** Duplicate job postings MUST be deduplicated using a stable key (externalPath, jobReqId, or title in that order).

---

## 7. ERROR CLASSIFICATION

### 7.1 STATE TAXONOMY

Every Workday query MUST be classified with exactly one state:
- `VERIFIED_RESULTS`: Valid results obtained
- `VERIFIED_EMPTY`: Zero results with all verification guarantees satisfied
- `BLOCKED`: Access denied (403, security check, Cloudflare, Akamai)
- `DNS_FAILURE`: DNS resolution failed
- `TIMEOUT`: Request timeout
- `UNKNOWN`: Any other error condition

**IMPLEMENTED:** ats_workday.py — `QueryState` enum + `WorkdayClient._post_jobs()` classify transport errors. `search()` machine enforces state transitions.

### 7.2 HTTP 400 HANDLING

**RULE CS-021:** HTTP 400 responses MUST be classified as:
- `payload_rejected` (not retryable): Workday CXS envelope indicates facet ID malformed, limit>20, or facet does not exist
- `bad_request_non_cxs` (retryable): HTTP 400 without Workday error envelope, possibly from intermediate layer

---

## 8. SOURCE LIMITATIONS

The following are SOURCE LIMITATIONS, not implementation defects:

### 8.1 ACCESS LIMITATIONS
- Guest/session caps on ATS portals
- 403/Akamai/Cloudflare blocks
- Geographic restrictions by ATS

### 8.2 AVAILABILITY LIMITATIONS
- DNS failures
- HTTP 410 Gone (portal retired)
- HTTP 404 on API endpoints
- Boards returning HTTP 200 with totalFound=0 (no active postings)

### 8.3 DATA LIMITATIONS
- Absence of VM vacancies in specific markets
- Incomplete job metadata (e.g., unstable workerSubType)

These conditions MUST be recorded in audit findings but MUST NOT be treated as code defects requiring correction.
