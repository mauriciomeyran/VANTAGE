# CAREER SITES PROMPT v2
## Version 2.0 — Based on Implementation Evidence

**Status:** CANDIDATE
**Implementation SHA:** 9c32a8f (current HEAD)
**Based on:** Prompt_Career_Sites_2026-10-04.md + feed evidence (2026-09-15_career_sites_result.json, 2026-10-04_career_sites_result.json) + feed_processor.py
**Created:** 2026-10-05

---

## 1. PURPOSE

Retrieve active job postings from official Career Pages and ATS platforms that match the immutable candidate profile, enforcing structured geography for Workday and validating all inclusion/exclusion rules.

---

## 2. SCOPE

### 2.1 TARGET SOURCES (CONTRACTUAL)

The following sources are contemplated in the contract. Implementation status varies by source.

**Official Career Pages**
- Direct career pages of target companies
- Company-hosted ATS portals

**ATS Platforms**
- Workday (structured geography via appliedFacets)
- Greenhouse
- Lever
- SmartRecruiters
- Taleo
- Ashby

**FORBIDDEN SOURCES**
- LinkedIn
- Indeed
- OCC
- Computrabajo
- Bumeran
- Any job aggregator

### 2.2 SOURCE IMPLEMENTATION STATUS

| Source | Implementation Status | Evidence |
|--------|----------------------|----------|
| Career Pages (direct) | UNVERIFIED | No dedicated crawler implementation found |
| Workday | IMPLEMENTED | ats_workday.py + ats_adapter.py en Layer_1/scripts/ (HEAD 9c32a8f): POST /jobs con appliedFacets, discovery de facets, resolución 2-nivel país→ciudad, scope degradation, verify_against, taxonomía de estados |
| Greenhouse | UNVERIFIED | No adapter implementado en el checkout actual |
| Lever | UNVERIFIED | No adapter implementado en el checkout actual |
| SmartRecruiters | UNVERIFIED | No adapter implementado en el checkout actual |
| Taleo | UNVERIFIED | No adapter implementado en el checkout actual |
| Ashby | UNVERIFIED | No adapter implementado en el checkout actual |

**Note:** Workday es el único ATS con adapter implementado. Greenhouse, Lever, SmartRecruiters, Taleo y Ashby son objetivos contractuales sin adapter en el checkout actual. Career Pages (directo) sin crawler dedicado.

### 2.3 GEOGRAPHIC SCOPE

**Primary Location:** Mexico City (CDMX)

**Workday Structured Geography (Contractual)**
- MUST resolve location from `response.facets`
- MUST apply via `appliedFacets`
- MUST NOT use `searchText` as geographic filter
- Location facet IDs are tenant-specific and context-dependent
- NEVER reuse IDs across tenants or sites
- NEVER hardcode location IDs

**Other ATS**
- Accept location from job posting fields
- Validate against CDMX requirement

---

## 3. IMMUTABLE CANDIDATE PROFILE

**Candidate:** Mauricio Meyrán
**Career Family:** Visual Merchandising, Brand Experience, Retail Experience, Store Design

**Accepted Seniority:**
- Coordinator, Senior Coordinator, Lead, Supervisor, Líder, Subgerente, Assistant Manager, Manager, Sr., Jefe, Head (IC only)

**Excluded Seniority (Hard Exclusion):**
- Assistant (standalone only, not "Assistant Manager")
- Asistente
- Auxiliar
- Jr.
- Internship, Intern
- Entry Level

**Industries:**
- Luxury, Premium, Fashion, Beauty, Cosmetics, Fragrances, Jewelry, Sportswear, Experiential Retail

**Location:** Mexico City (CDMX)
**Work Modes:** On-site, Hybrid

---

## 4. HARD EXCLUSIONS

### 4.1 EXCLUDED TITLES

Reject if COMPLETE TITLE contains:
- Store Manager
- Director
- VP
- C-Level
- Assistant (standalone only - "Assistant Manager" is ACCEPTED)
- Asistente
- Auxiliar
- Jr.
- Internship, Intern
- Entry Level
- Pasantía
- Sales Advisor, Vendedor, Asesor Comercial

**Exclusion Matching Logic:**
- Exact phrase match for multi-word terms (e.g., "Store Manager", "Assistant Manager")
- Token-level match for single-word terms (e.g., "Assistant", "Director", "VP")
- "Assistant Manager" → ACCEPTED (valid seniority per Career Canon)
- "Assistant" alone → REJECTED (excluded term)
- "Asistente" → REJECTED (excluded term)
- "Auxiliar" → REJECTED (excluded term)

### 4.2 BLOCKED COMPANIES

- L'Oréal (all divisions)
- Levi's
- El Palacio de Hierro

Dockers is not a blocked employer (operator decision 2026-10-07).

### 4.3 LOCATION EXCLUSION

Reject remote roles outside Mexico City (CDMX).

---

## 5. INCLUSION RULES

### 5.1 PRE-INCLUSION CHECK

Every result MUST satisfy:

✓ Company explicitly identified
✓ URL accessible
✓ Explicit visual signal inside JD
✓ Posting age:
  - Preferred: ≤14 days
  - Acceptable: ≤21 days only if fit remains strong
✓ Title passes all exclusions

If any check fails: Exclude the item. Record issue in `datos_calidad_advertencias`.

### 5.2 WORKDAY VERIFIED_EMPTY REQUIREMENTS (CONTRACTUAL)

`verified_empty` is permitted ONLY when:
- Location facet was resolved
- `appliedFacets` was used
- Query terminated without wraparound or truncation
- `searchText` did NOT act as location mechanism

A 403, Cloudflare, Akamai, DNS failure, timeout, unresolvable facet, missing facets, or incomplete query MUST NOT be reported as zero vacancies.

---

## 6. WORKDAY STRUCTURED GEOGRAPHY (CONTRACTUAL)

### 6.1 FACET RESOLUTION

- Workday geography = structured facets
- Discovery: POST /jobs with empty `appliedFacets` → response.facets
- Location facets: `locationCountry`, `locations`
- Two-level resolution: Country → City/Location

### 6.2 CONTEXT ISOLATION

- Facet IDs are tenant-specific
- Context required: tenant, site, facetParameter, descriptor
- NEVER reuse IDs across tenants
- NEVER hardcode location IDs
- HTTP 200 does NOT prove facet matched requested location

### 6.3 STATE CLASSIFICATION

Every Workday query MUST be classified with exactly one state:
- `VERIFIED_RESULTS`
- `VERIFIED_EMPTY`
- `BLOCKED`
- `DNS_FAILURE`
- `TIMEOUT`
- `UNKNOWN`

---

## 7. OUTPUT FORMAT

Return ONLY the Prompt A JSON schema with:

```
prompt_variant: "A-weekly-unified-careersites"
prompt_version: "PromptA-v2.0+careersites"
```

**Envelope Structure:**
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

**Job Posting Fields (Contractual):**
- `titulo` (Job title)
- `empresa` (Company name)
- `url` (Application URL)
- `location` (Location description)
- `fecha_publicacion` (Posting age or date)

**Runtime Normalization:**
- These Spanish field names are normalized to English equivalents by `feed_processor.py`:
  - `titulo` → `title`
  - `empresa` → `brand_raw` / `brand`
  - `url` → `apply_url`
  - `fecha_publicacion` → `posted_on` (not currently normalized)

Never duplicate keys. Never output text outside JSON.

---

## 8. AUDIT TYPES

Allowed audit types:
- DNS
- HTTP
- Timeout
- Filled
- Expired
- Redirect
- Cloudflare

Technical evidence only. Never duplicate information inside `datos_calidad_advertencias`.

---

## 9. LIMITATIONS (SOURCE LIMITATIONS, NOT IMPLEMENTATION BUGS)

The following are source limitations, not implementation defects:
- Guest/session caps
- 403/Akamai/Cloudflare blocks
- DNS failures
- Boards returning HTTP 200 with totalFound=0
- 404 on Greenhouse/Lever API endpoints
- Portals inaccesibles (e.g., Sephora MX 410)
- Absence of VM vacancies in specific markets
- Geographic restrictions by ATS

These should be recorded in audit as technical findings, not treated as code defects.
