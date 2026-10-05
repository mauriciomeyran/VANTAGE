# CHANGELOG UPDATE

## 2026-10-05 — Layer 1 — Workday Structured ATS Integration

### Added

- Integrated `Layer_1/scripts/ats_workday.py` into the Layer 1 main orchestrator.
- Added structured Workday discovery using `appliedFacets` instead of relying on textual search.
- Added two-level geographic resolution:
  - Country
  - City / Workday location facets
- Added Workday tenant/site scoping to preserve execution boundaries between ATS tenants.
- Added deterministic normalization and Feed Envelope generation for Workday results.
- Added explicit deduplication during Workday result processing.
- Added safe verification path through `--skip-ingestion`, allowing ATS discovery and Feed Envelope generation without Notion mutation.

### Changed

- Workday location discovery now resolves the country before resolving the corresponding city/location facets.
- Workday querying now operates against structured facet values rather than free-text location matching.
- Unstable `workerSubType` metadata is deterministically represented as `unknown` instead of producing nondeterministic downstream behavior.
- Layer 1 now routes `--target-ats workday` through the dedicated Workday adapter.

### Validation

- `Layer_1/tests/test_ats_workday.py`: **41/41 passed**
- General test suite: **232/232 passed**
- Verified integration execution:
  - tenant: `cc`
  - site: `ChanelCareers`
  - country: `Mexico`
  - resolved locations: `Cdmx`, `Zona Centro`, `Ciudad De Mexico`
  - postings retrieved: `10`
  - CDMX match: `100%`
  - duplicates: `0`
  - Feed Envelope: generated successfully
  - ingestion: bypassed safely with `--skip-ingestion`
  - final state: `verified_results`

### Architecture / Safety

- Established tenant/site isolation as a mandatory boundary for Workday discovery.
- Prevented unscoped reuse of Workday facets across tenants.
- Preserved separation between ATS-specific discovery logic and generic Layer 1 orchestration.
- Maintained external mutation protection during integration verification.

### Phase Status

**Phase 2:** CLOSED  
**Phase 3 Option A:** CLOSED  
**Workday adapter integration:** VERIFIED