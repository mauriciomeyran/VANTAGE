# CAREER SITES OUTPUT SCHEMA v2
## Version 2.0 — Canonical Output Schema

**Status:** CANDIDATE
**Based on:** 2026-09-15_career_sites_result.json + feed_processor.py
**Created:** 2026-10-05

---

## 1. ENVELOPE STRUCTURE

The Career Sites discovery produces a JSON envelope consumed by the VANTAGE feed pipeline.

### 1.1 ROOT ENVELOPE (CONTRACTUAL OUTPUT)

This is the envelope format expected from the prompt contract (Prompt A + Wrapper):

```json
{
  "candidate": "Mauricio Meyrán",
  "search_date": "YYYY-MM-DD",
  "prompt_variant": "A-weekly-unified-careersites",
  "prompt_version": "PromptA-v2.0+careersites",
  "fuente": "Career Pages Oficiales + ATS (Workday, Greenhouse, Lever, SmartRecruiters, Taleo, Ashby)",
  "busqueda_realizada": true,
  "resultados": [/* array of job postings */],
  "rechazados": [/* array of rejected items */],
  "datos_calidad_advertencias": [/* array of audit findings */]
}
```

**Evidence:** This format is verified in feed `2026-10-04_career_sites_result.json` (and `2026-09-15_career_sites_result.json`).

### 1.2 FIELD MAPPING TO RUNTIME

When the contractual envelope is processed by `feed_processor.py`, field normalization occurs:

| Contractual Field | Runtime Normalized Field | Normalization Logic |
|-------------------|--------------------------|---------------------|
| `titulo` | `title` | normalize_record_fields() accepts "title", "rol", "role", "Rol" |
| `empresa` | `brand_raw` / `brand` | normalize_record_fields() accepts "brand", "marca", "company", "Marca" |
| `fecha_publicacion` | `posted_on` | NOT normalized por feed_processor.py — pendiente implementación |
| `url` | `apply_url` | normalize_record_fields() accepts "apply_url", "url", "URL", "apply_path" |

**Note:** The runtime uses English field names internally (`title`, `brand`, `apply_url`, `location`, `job_id`, `jd`). The contractual envelope uses Spanish field names (`titulo`, `empresa`, `fecha_publicacion`). This mapping is handled by `normalize_record_fields()` in feed_processor.py.

---

## 2. JOB POSTING RECORD

### 2.1 REQUIRED FIELDS (Contractual)

Every job posting record in the contractual envelope MUST include:

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `titulo` | string | Job title | JD text / ATS metadata |
| `empresa` | string | Company name | JD text / ATS metadata |
| `url` | string | Application URL | ATS / career page |
| `location` | string | Location description | JD text / ATS metadata |
| `fecha_publicacion` | string | Posting age or date | ATS metadata / heuristic |

**Note:** The field `status` is NOT included in the contractual envelope. It is a runtime field managed by the VANTAGE pipeline (tracker_flow.py) and does not belong to the prompt output schema.

### 2.2 OPTIONAL FIELDS (Contractual)

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `job_id` | string | Internal job identifier | ATS (jobReqId, externalPath) |
| `jd` | string | Full job description | JD text |
| `marca` | string | Brand (if applicable) | Company mapping |
| `holding` | string | Holding company (if applicable) | Company mapping |
| `layer` | string | Layer assignment (L1) | Orchestrator |
| `fetch_status` | string | URL verification result | URL gate |
| `source` | string | Source name | ATS name / career page domain |

### 2.3 RUNTIME NORMALIZED FIELDS

After processing by `feed_processor.py`, the following fields are normalized:

| Runtime Field | Accepted Aliases | Notes |
|---------------|------------------|-------|
| `title` | `titulo`, `rol`, `role`, `Rol` | Normalized via `normalize_record_fields()` |
| `brand_raw` | `empresa`, `brand`, `marca`, `company`, `Marca` | Normalized via `normalize_record_fields()` |
| `apply_url` | `url`, `URL`, `apply_path` | Normalized via `normalize_record_fields()` |
| `location` | `ubicacion`, `city` | Normalized via `normalize_record_fields()` |
| `job_id` | `JOB_ID` | Normalized via `normalize_record_fields()` |
| `jd` | `jd_snippet`, `description`, `JD` | Normalized via `normalize_record_fields()` |

---

## 3. WORKDAY FEED SCHEMA (IMPLEMENTED)

### 3.1 STATUS

**IMPLEMENTATION STATUS:** IMPLEMENTED

`ats_adapter.py` (Layer_1/scripts/) produce el envelope `vantage-feed-1.0` compatible con `normalize_envelope()` de feed_processor.py. Verificado contra checkout HEAD 9c32a8f.

### 3.2 PROPOSED ATS_ADAPTER ENVELOPE

If a Workday adapter were implemented, it would likely produce:

```json
{
  "schema_version": "vantage-feed-1.0",
  "generated_at": "ISO-8601 timestamp",
  "source": "ats_adapter.workday",
  "ats": "workday",
  "tenant": "tenant_code",
  "site": "site_name",
  "host": "workday_host",
  "brand": "brand_name",
  "final_state": "VERIFIED_RESULTS|VERIFIED_EMPTY|BLOCKED|DNS_FAILURE|TIMEOUT|UNKNOWN",
  "audit": { /* audit trail */ },
  "scope_degradation": { /* degradation info or null */ },
  "consolidated_by_l0": false,
  "listings": [/* job records */],
  "results_by_source": {
    "workday:tenant/site": [/* job records */]
  },
  "meta": {
    "raw_count": integer,
    "state": "final_state",
    "resolved_scope": "country|city",
    "applied_facets": { /* facet mapping */ }
  }
}
```

**Note:** This envelope format is compatible with `feed_processor.py`'s `normalize_envelope()` function, which accepts `results_by_source`, `listings`, or `consolidated_results` as top-level arrays.

### 3.3 PROPOSED WORKDAY JOB RECORD

```json
{
  "title": "Job Title",
  "brand": "Brand Name",
  "company": "Brand Name",
  "apply_url": "https://.../externalPath",
  "url": "https://.../externalPath",
  "location": "Location text",
  "job_id": "jobReqId or externalPath",
  "jd": "",
  "fetch_status": "career_page",
  "source_type": "career_page",
  "layer": "L1",
  "posted_on": "ISO-8601 date",
  "external_path": "externalPath",
  "ats": "workday"
}
```

**Note:** Workday structured search does not fetch full JD. The `jd` field would be intentionally empty. Full JD extraction would require a subsequent fetch.

---

## 4. REJECTED ITEM SCHEMA

### 4.1 REJECTION RECORD

```json
{
  "titulo": "Job Title",
  "empresa": "Company Name",
  "url": "Application URL",
  "fecha_publicacion": "Posting age",
  "motivo_rechazo": "Reason for rejection"
}
```

**Rejection Reasons:**
- Location outside CDMX
- Posting age >21 days
- Title contains excluded term
- Blocked company
- No visual signal in JD
- URL inaccessible
- Source limitation (DNS, 403, 404, etc.)

---

## 5. AUDIT WARNING SCHEMA

### 5.1 DATA QUALITY WARNING

```json
{
  "tipo_auditoria": "DNS|HTTP|Timeout|Filled|Expired|Redirect|Cloudflare",
  "fuente": "Source name or URL",
  "evidencia": "Technical finding description",
  "fecha": "YYYY-MM-DD"
}
```

**Audit Types:**
- DNS: NXDOMAIN or DNS resolution failure
- HTTP: HTTP error code (403, 404, 410, 500, etc.)
- Timeout: Request timeout
- Filled: No active postings (totalFound=0)
- Expired: Posting age exceeds threshold
- Redirect: URL redirects
- Cloudflare: Cloudflare protection detected

---

## 6. STATE CLASSIFICATION

### 6.1 WORKDAY STATES

| State | Description | Criteria |
|-------|-------------|----------|
| `VERIFIED_RESULTS` | Valid results obtained | HTTP 200 with job postings, location facet resolved, no wraparound |
| `VERIFIED_EMPTY` | Zero results with guarantees | HTTP 200 with 0 postings, location facet resolved, appliedFacets used, no wraparound, searchText not used as location |
| `BLOCKED` | Access denied | 403, security check, Cloudflare, Akamai |
| `DNS_FAILURE` | DNS resolution failed | NXDOMAIN, nodename not found |
| `TIMEOUT` | Request timeout | Connection timeout, read timeout |
| `UNKNOWN` | Any other error | Unclassified error, unexpected response |

---

## 7. COMPATIBILITY WITH NOTION CLASS A

### 7.1 FIELD MAPPING

The output schema maps to Notion Class A fields as follows:

| Schema Field | Notion Property | Notes |
|-------------|-----------------|-------|
| `titulo` | Rol | Job title |
| `empresa` | Marca | Company name |
| `url` | URL | Application URL |
| `location` | NAD (if location-specific) | Location text |
| `jd` | JD | Job description |
| `marca` | Marca | Brand (if distinct from company) |
| `holding` | Holding | Holding company |
| `layer` | layer | L1 |

**Note:** The `status` field is managed by the VANTAGE pipeline (tracker_flow.py) and is not part of the prompt output schema. It is set during Class A creation and subsequent pipeline processing.

### 7.2 FLOW TO NOTION

1. Feed JSON → feed_processor.py → normalize_envelope
2. Normalized record → Notion pages.create (Class A)
3. Class A populated → vantage-pipeline → Class B calculation (Score, Gate, etc.)

---

## 8. SCOPE DEGRADATION RECORD

### 8.1 DEGRADATION STRUCTURE

```json
{
  "requested_scope": "city",
  "resolved_scope": "country",
  "reason": "City facet could not be resolved, fell back to country"
}
```

**Scope Values:**
- `country`: Country-level resolution
- `city`: City/location-level resolution
- `null`: No degradation

---

## 9. AUDIT TRAIL

### 9.1 AUDIT STRUCTURE

```json
{
  "applied_facets": { /* facet mapping */ },
  "search_text": "optional search text",
  "pages": integer,
  "raw_count": integer,
  "state": "final_state",
  "first_total": integer,
  "saw_wraparound": boolean,
  "truncated": boolean
}
```

---

## 10. VERSIONING

### 10.1 SCHEMA VERSION

Current schema version: `vantage-feed-1.0`

Evolution: The schema is designed to be backward-compatible with feed_processor.py while allowing for future extensions.

### 10.2 PROMPT VERSION

Current prompt version: `PromptA-v2.0+careersites`

Previous version: `PromptA-v1.0+careersites` (evidenced in 2026-09-15 feed)

Version bump rationale: v2 contract formalized from implementation evidence. ats_workday.py + ats_adapter.py implemented (HEAD 9c32a8f).
