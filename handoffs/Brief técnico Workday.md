# VANTAGE — Technical Documentation Brief
## Workday ATS Adapter + Layer 1 Integration

**Version:** v1.1.0  
**Date:** 2026-10-05  
**Component:** Layer 1  
**Adapter:** `Layer_1/scripts/ats_workday.py`  
**Orchestrator:** `Layer_1/scripts/layer1_orchestrator.py`  
**Reference Handoff:** `HO-20261005-01`  
**Validation status:** VERIFIED  
**Evidence status:** Adopted from S4. No Workday re-test required.

---

## 1. Purpose

`ats_workday.py` is the structured ATS adapter used by VANTAGE Layer 1 to discover and normalize job postings exposed through Workday's CXS infrastructure.

The adapter replaces the unreliable model of relying primarily on textual job-search queries with structured filtering through Workday `appliedFacets`.

Its responsibility is to isolate Workday-specific discovery mechanics from the generic Layer 1 orchestration pipeline while returning results in the common Feed Envelope consumed downstream.

The adapter was integrated into the Layer 1 main orchestrator during Phase 3 Option A.

---

## 2. Architectural Position

The adapter sits between the external ATS and the Layer 1 orchestration layer:

    Workday CXS
        │
        ▼
    ats_workday.py
        │
        ├── tenant/site resolution
        ├── facet resolution
        ├── structured query
        ├── location filtering
        ├── normalization
        └── deduplication
        │
        ▼
    Feed Envelope
        │
        ▼
    Layer 1 orchestrator
        │
        ├── gating
        ├── ingestion control
        └── downstream processing

The adapter therefore owns Workday-specific transport and query semantics. Layer 1 remains responsible for orchestration and system-level controls.

---

## 3. Structured Discovery Model

The central design change is the move from textual search to structured Workday facets.

The query is constructed around Workday's `appliedFacets` mechanism rather than attempting to encode location requirements into free-text search terms.

This provides a deterministic separation between:

- country selection
- city/location selection
- posting retrieval
- result normalization

The verified execution against the Chanel Workday tenant produced:

- tenant: `cc`
- site: `ChanelCareers`
- Workday host: `cc.wd3.myworkdayjobs.com`
- country facet: `Mexico`
- resolved locations: `Cdmx`, `Zona Centro`, `Ciudad De Mexico`
- postings retrieved: `10`
- CDMX match rate: `100%`
- duplicates: `0`

This is the reference implementation for the structured ATS pattern.

---

## 4. Two-Level Location Resolution

Location resolution follows a two-level model:

    Level 1: Country
        Mexico
          │
          ▼
    Level 2: City / Location
        Cdmx
        Zona Centro
        Ciudad De Mexico

The first level establishes the geographic scope.

The second level resolves the concrete Workday location facets associated with the requested city/market.

This separation is important because Workday does not necessarily represent a city through a single canonical textual value. A single business location can surface through multiple Workday facet values.

The verified Chanel execution resolved:

`Mexico → [Cdmx, Zona Centro, Ciudad De Mexico]`

The resulting query returned 10 postings with 100% CDMX match.

The adapter therefore avoids treating a single city string as the complete geographic contract.

---

## 5. Tenant and Site Isolation

Workday is multi-tenant by design. The adapter must treat the tenant/site pair as part of the query identity rather than as incidental configuration.

Example verified target:

    tenant = cc
    site   = ChanelCareers

The resulting Workday CXS endpoint was:

    cc.wd3.myworkdayjobs.com

The adapter must never allow a resolved facet, posting, or query response from one tenant to be silently reused for another tenant.

The isolation boundary is therefore:

    Tenant
       │
       └── Site
             │
             └── Facets
                    │
                    └── Postings

A facet discovered for tenant A must not become an implicit candidate for tenant B.

This is particularly important when multiple brands use Workday infrastructure with similar endpoint structures.

---

## 6. Cross-Tenant Contamination Prevention

Cross-tenant contamination is prevented conceptually through explicit tenant/site scoping at discovery and query time.

The adapter should maintain the following invariant:

    resolved tenant == requested tenant
    resolved site   == requested site
    returned postings belong to that tenant/site scope

No global facet cache or unscoped location mapping should be treated as authoritative across tenants.

Any future optimization involving caching must preserve this isolation boundary. A cached object must be keyed by the complete Workday context required to reproduce the query, rather than by a generic location string alone.

This requirement is architectural, not merely a data-cleaning step.

---

## 7. Six-Way State Machine

The Workday integration uses a six-way deterministic state classification to prevent ambiguous execution outcomes from collapsing into a generic success/failure result.

The important architectural rule is that each terminal or degraded condition must be represented explicitly and must remain distinguishable from a successful result set.

The verified execution reached:

    FINAL STATE: verified_results

The adapter also explicitly handles instability in `workerSubType` by classifying the value deterministically as:

    workerSubType = unknown

This prevents transient or incomplete Workday metadata from producing nondeterministic behavior.

**Documentation constraint:** the S4 handoff confirms the existence and deterministic behavior of the six-way state machine but does not enumerate the six canonical state names. Those labels should be copied from the implementation before publishing them as normative documentation. They should not be reconstructed from memory or inferred from the execution log.

---

## 8. Normalization and Feed Envelope

The adapter does not terminate at raw Workday JSON.

Its output is normalized into the VANTAGE Feed Envelope so that Layer 1 can consume Workday results without embedding Workday-specific response semantics throughout the orchestrator.

Verified execution:

    Feed Envelope generated:
    /var/folders/s7/.../vantage_ats_feed_20261005_004848.json

The envelope therefore constitutes the adapter/orchestrator boundary.

Future structured ATS adapters should target the same boundary rather than creating provider-specific downstream ingestion paths.

---

## 9. Deduplication

The verified Workday run performed explicit deduplication.

Result:

    postings retrieved: 10
    duplicates: 0

Deduplication is therefore part of the adapter's result normalization rather than being left entirely to downstream consumers.

The adapter should preserve deterministic identity for postings so that repeated or overlapping facet results do not generate duplicate downstream records.

---

## 10. Error and Metadata Degradation

The Workday implementation distinguishes between a usable result and unstable metadata.

The verified example is `workerSubType`.

Rather than failing the entire query when this metadata is unstable, the value is deterministically represented as:

    unknown

This establishes an important design principle:

> Unstable optional metadata should degrade locally when safe, rather than corrupting the identity or validity of the complete result set.

This principle must not be generalized to mandatory query or tenant-identification data without explicit evidence.

---

## 11. Layer 1 Orchestration

Phase 3 Option A wired the Workday adapter into the Layer 1 main orchestrator.

Verified invocation:

    python Layer_1/scripts/layer1_orchestrator.py \
      --target-ats workday \
      --tenant cc \
      --site ChanelCareers \
      --skip-ingestion

The `--target-ats workday` selector routes execution to the Workday adapter.

The tenant and site parameters establish the external scope.

The `--skip-ingestion` flag provides a safe verification boundary by allowing discovery and Feed Envelope generation without committing results into Notion.

Verified outcome:

    Gating Control: --skip-ingestion active.
    Ingestion to Notion bypassed safely.
    FINAL STATE: verified_results

---

## 12. Ingestion Safety

The Workday integration was verified with ingestion explicitly disabled.

This establishes a separation between:

1. external discovery,
2. result normalization,
3. envelope generation,
4. downstream ingestion.

The adapter can therefore be validated independently of external mutation.

This is especially important for future ATS integrations because endpoint behavior, tenant isolation, location mapping and result quality can be tested before any Notion mutation occurs.

---

## 13. Validation Evidence

### Unit tests

    pytest Layer_1/tests/test_ats_workday.py -p no:cacheprovider

Verified result:

    41 passed in 0.28s

### Layer 1 integration

    python Layer_1/scripts/layer1_orchestrator.py \
      --target-ats workday \
      --tenant cc \
      --site ChanelCareers \
      --skip-ingestion

Verified result:

    ATS Discovery: Initiating Workday CXS payload
    Facets Resolved: locationCountry='Mexico'
    locations=['Cdmx', 'Zona Centro', 'Ciudad De Mexico']
    Query Executed: 10 postings retrieved
    100% CDMX match
    Deduplication: 0 duplicates
    Feed Envelope generated
    Ingestion bypassed safely
    FINAL STATE: verified_results

The official handoff additionally reports:

    General suite: 232/232 tests passed

This evidence is adopted without repeating the Workday tests.

---

## 14. Architectural Contract for Future ATS Adapters

The Workday implementation establishes the following reusable boundary for structured ATS integrations:

    ATS-specific adapter
        ↓
    Structured discovery
        ↓
    Provider-specific filtering
        ↓
    Deterministic normalization
        ↓
    Deduplication
        ↓
    Feed Envelope
        ↓
    Layer 1 orchestration
        ↓
    Gates / ingestion controls

Future adapters must not be assumed to behave like Workday.

Each provider must first be investigated for:

- endpoint availability
- authentication requirements
- tenant/site model
- structured filtering capabilities
- pagination
- location representation
- posting identity
- error semantics
- rate limits
- edge protection
- metadata completeness

Only after those characteristics are established should the provider be mapped onto the common Layer 1 adapter contract.

---

## 15. Operational Status

**Workday adapter:** integrated  
**Layer 1 wiring:** complete  
**Unit validation:** 41/41 passed  
**General suite:** 232/232 passed  
**Feed Envelope:** verified  
**Tenant isolation:** explicit architectural requirement  
**Location resolution:** Country → City/Location  
**Structured filtering:** `appliedFacets`  
**Ingestion safety:** verified with `--skip-ingestion`  
**Current terminal evidence:** `verified_results`

**Phase 3 Option A:** CLOSED.