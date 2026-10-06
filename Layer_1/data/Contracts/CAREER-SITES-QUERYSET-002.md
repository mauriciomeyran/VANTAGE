# CAREER SITES QUERYSET v2
## Version 2.0 — Canonical Query Definitions

**Status:** CANDIDATE
**Based on:** Prompt_Career_Sites-v2 + feed evidence
**Created:** 2026-10-05

---

## 1. WORKDAY QUERIES

### 1.1 STATUS

**IMPLEMENTATION STATUS:** IMPLEMENTED

`ats_workday.py` + `ats_adapter.py` exist en Layer_1/scripts/ (checkout HEAD 9c32a8f). Workday structured search implementado: discovery de facets, `appliedFacets`, resolución 2-nivel, scope degradation, `verify_against`, taxonomía de estados.

### 1.2 PROPOSED DISCOVERY QUERY

**Purpose:** Discover available location facets for a tenant/site.

**Method:** POST /jobs
**Payload:**
```json
{
  "appliedFacets": {},
  "limit": 20,
  "offset": 0
}
```

**Expected Output:** `response.facets` containing locationCountry and locations facet values.

**State Classification:** Query itself is discovery; result classified as VERIFIED_RESULTS or UNKNOWN.

---

### 1.3 PROPOSED STRUCTURED LOCATION QUERY

**Purpose:** Query jobs with resolved location facets.

**Method:** POST /jobs
**Payload:**
```json
{
  "appliedFacets": {
    "locationCountry": ["Mexico"],
    "locations": ["<resolved_city_id>"]
  },
  "limit": 20,
  "offset": 0
}
```

**Parameters:**
- `limit`: Capped at 20 (WORKDAY_MAX_LIMIT)
- `offset`: Starts at 0, increments by limit until wraparound or safety cap (2000)
- `searchText`: Optional secondary text filter; MUST NOT be used as primary geographic filter

**Two-Level Resolution (Optional):**
1. Country level: Resolve country facet first
2. City level: Resolve city/location facets from country context

**State Classification:** VERIFIED_RESULTS, VERIFIED_EMPTY, BLOCKED, DNS_FAILURE, TIMEOUT, UNKNOWN.

---

### 1.4 PROPOSED TWO-LEVEL COUNTRY→CITY QUERY

**Purpose:** Country-first resolution when city is not directly resolvable.

**Method:** Sequential queries:
1. Query with country facet only
2. From results, extract city/location facets
3. Query with city/location facets

**Scope Degradation:** If city cannot be resolved, query with country only and explicitly record degradation.

---

## 2. SMARTRECRUITERS QUERIES

### 2.1 STATUS

**IMPLEMENTATION STATUS:** UNVERIFIED

No implementation evidence exists for SmartRecruiters queries in the VANTAGE repository. The query pattern below is a proposed standard for SmartRecruiters API.

### 2.2 PROPOSED COMPANY POSTINGS QUERY

**Purpose:** Retrieve active job postings for a specific company.

**Method:** GET /v1/companies/{company_slug}/postings
**Parameters:**
- `company_slug`: Company identifier (e.g., "Sephora", "Chanel", "benefitcorporation")

**Expected Output:** JSON with `totalFound` and postings array.

**State Classification:**
- HTTP 200 with postings: VERIFIED_RESULTS
- HTTP 200 with totalFound=0: SOURCE_LIMITATION (no active postings)
- HTTP 404/410: SOURCE_LIMITATION (board inaccessible or retired)

---

## 3. GREENHOUSE QUERIES

### 3.1 STATUS

**IMPLEMENTATION STATUS:** UNVERIFIED

No implementation evidence exists for Greenhouse queries in the VANTAGE repository. The query pattern below is a proposed standard for Greenhouse boards-api.

### 3.2 PROPOSED BOARDS API QUERY

**Purpose:** Query job boards via Greenhouse boards-api.

**Method:** GET /v1/boards/{board_slug}/jobs
**Parameters:**
- `board_slug`: Board identifier (e.g., "glossier", "bombas")

**Expected Output:** JSON with job postings.

**State Classification:**
- HTTP 200 with postings: VERIFIED_RESULTS
- HTTP 404: SOURCE_LIMITATION (board does not exist)
- HTTP 200 with no postings matching location: SOURCE_LIMITATION

---

## 4. LEVER QUERIES

### 4.1 STATUS

**IMPLEMENTATION STATUS:** UNVERIFIED

No implementation evidence exists for Lever queries in the VANTAGE repository. The query pattern below is a proposed standard for Lever API.

### 4.2 PROPOSED POSTINGS API QUERY

**Purpose:** Query job postings via Lever API.

**Method:** GET /v0/postings
**Parameters:**
- Lever-specific team identifiers

**Expected Output:** JSON with job postings.

**State Classification:**
- HTTP 200 with postings: VERIFIED_RESULTS
- HTTP 404: SOURCE_LIMITATION (team/board does not exist)

---

## 5. TALEO/ASHBY QUERIES

### 5.1 STATUS

**IMPLEMENTATION STATUS:** UNVERIFIED

No implementation evidence exists for Taleo or Ashby platforms in the VANTAGE repository. These platforms are listed as allowed sources in the contract but no specific query patterns were demonstrated in the available evidence.

Query patterns for Taleo and Ashby should be documented when implementation evidence becomes available.

---

## 6. CAREER PAGES NAVIGATION

### 6.1 DIRECT CRAWLING

**Purpose:** Navigate official career pages and extract job postings.

**Method:** Direct HTTP GET to career page URLs followed by HTML parsing.

**Scope:** Limited to companies with official career pages not backed by major ATS.

**State Classification:**
- HTTP 200 with job listings: VERIFIED_RESULTS
- HTTP 404/410: SOURCE_LIMITATION (page retired)
- DNS failure: DNS_FAILURE
- Timeout: TIMEOUT

---

## 7. QUERY PARAMETERS AND FACETS

### 7.1 WORKDAY FACET PARAMETERS (PROPOSED)

**Location Facets:**
- `locationCountry`: Country-level facet
- `locations`: City/location-level facet

**Validation:**
- Facet IDs MUST be validated against tenant context
- `verify_against()` MUST re-derive IDs from facets/context before use

### 7.2 SEARCHTEXT USAGE

**RULE QS-001:** `searchText` is an OPTIONAL secondary text filter. It MUST NOT be used as the primary geographic mechanism for Workday.

**RULE QS-002:** When `searchText` is present and results are 0, the state MUST be UNKNOWN (not VERIFIED_EMPTY), as the text filter may have over-constrained the query.

---

## 8. PAGINATION STRATEGY

### 8.1 WORKDAY PAGINATION (PROPOSED)

**Strategy:** Offset-based with safety cap

**Parameters:**
- `limit`: 20 (WORKDAY_MAX_LIMIT)
- `offset`: 0, 20, 40, ... up to safety cap (2000)

**Termination Conditions:**
- Page returns fewer than `limit` jobs (partial page = last)
- Page returns 0 new jobs (wraparound detected)
- Offset reaches safety cap

**Deduplication:** Stable key from externalPath, jobReqId, or title.

---

## 9. VERIFICATION REQUIREMENTS

### 9.1 QUERY VERIFICATION

Every query result MUST include:
- State classification
- Evidence (audit trail)
- Scope information (tenant, site, facets applied)
- Job count (verified vs total from source)

### 9.2 CONTEXT VERIFICATION

For Workday:
- `verify_against()` MUST be called to validate facet IDs against active context
- Cross-tenant reuse MUST be detected and flagged

---

## 10. QUERY EXECUTION ORDER

### 10.1 CONTRACTUAL PROCESSING SEQUENCE

The following sequence is the contractual order specified in the prompt. Implementation verification has not been performed as the relevant ATS adapter files do not exist in the repository.

**Recommended Order:**
1. Career Pages (direct navigation)
2. ATS (Workday, Greenhouse, Lever, SmartRecruiters, Taleo, Ashby)
3. Validation
4. Extraction
5. Output

**Note:** This order represents the contractual target sequence. Actual implementation may vary and should be verified against code when ATS adapters are implemented. Workday adapter: IMPLEMENTED (ats_workday.py + ats_adapter.py, HEAD 9c32a8f). Other ATS: no adapters in current checkout.
