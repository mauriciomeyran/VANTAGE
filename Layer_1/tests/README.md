# VANTAGE Test Suite

Comprehensive pytest unit test suite for VANTAGE Layer 1 pipeline functions.

## Overview

This test suite provides coverage for critical deduplication, gate logic, and scoring functions to prevent regression on production fixes (v9.5.3).

## Test Structure

### 1. Dedup Tests (`test_dedup.py`)
**Functions tested:**
- `normalize_url()` - URL normalization with lowercase path
- `dedup_cross_layer()` - Cross-layer deduplication  
- `content_fingerprint()` - Content-based fingerprinting for Indeed jk rotation
- `composite_key()` - Brand+title+location composite key

**Real case fixtures from Bug Tracker 39b938befc4281efa1ccdd5d763bfdbf:**
1. **Electrónica Confidencial** - URL case normalization
2. **Vinos La Naval** - URL case normalization
3. **Zegna** - URL normalization
4. **GILSA** - Indeed jk rotation (3 different jk for same position)
5. **Promotwist** - Duplicate detection

**Test coverage:**
- URL path lowercase normalization (Caso 1, 2)
- Tracking parameter removal (including jk per v9.4.3 fix)
- Scheme and netloc normalization
- Content fingerprinting for Indeed jk rotation (Caso 4) - **SEPARATE from jk exclusion**
- Case-insensitive matching
- Integration tests for hash consistency

**Note on GILSA case (Caso 4):** The GILSA test validates `content_fingerprint()`/`dedup_by_content_fingerprint()`, NOT `normalize_url()`. The Indeed jk rotation problem (Caso 4b) is NOT resolved by excluding jk from the hash (v9.4.3 fix), but by the separate content fingerprinting mechanism that compares título+empresa+ubicación regardless of jk value.

### 2. Gate Logic Tests (`test_gate_logic.py`)
**Functions tested (from actual code audit):**
- `gate_logic(entry)` - Main gate logic with terminal state protection
- `evaluate_gate(fetch, vm_scope, role_class)` - Gate decision evaluation
- `gate(fetch, vm_scope, role_class, source_type, rol, marca)` - Gate from layer_1_run.py
- `evaluate_application_status(status)` - Application status evaluation
- `evaluate_rejection_status(status)` - Rejection status evaluation
- `get_application_next_action(status)` - Application next action mapping

**Test coverage:**
- Terminal state protection (Archivar, Expirada)
- APPLIED gate decision with various statuses
- CREATE gate decision logic
- BLOCKED gate decision with different fetch states
- Source type handling (Inbound, Referencia, Networking, Vacante)
- Application status workflows
- Integration tests for complete workflows

### 3. Scoring Tests (`test_scoring.py`)
**Functions tested (from actual code audit):**
- `calculate_score_v6(entry)` - Main scoring function (v6.4)
- `get_score_band(score)` - Score band mapping (if available)

**Scoring v6.4 components tested:**
1. Base Score: +40 (passed URL_GATE)
2. Visual Signal: +20 (visual terms in JD)
3. Company Impact: +15 (high-impact companies)
4. Role Quality: +10 (quality titles)
5. Recruiter Presence: +10 (contact info)
6. Innovation/Cool DNA: +5 (innovative companies)
7. Scale Bonus: +5 (scale companies + manager)
8. Pivot Bonus: +5 (pivot roles)
9. Agency Bonus: +5 (marketing agencies)
10. Luxury Heritage: +5 (luxury brands)

**Test coverage:**
- Individual bonus component testing
- Combined bonuses testing
- Score cap at 100
- Case-insensitive company matching
- Spanish visual terms
- Integration tests for realistic scenarios

## Code Audit Findings

### Gate Logic Functions (Verified)
- `gate_logic()` in `gate_logic.py` - Main gate logic with terminal state protection
- `evaluate_gate()` in `gate_logic.py` - Gate decision evaluation
- `gate()` in `layer_1_run.py` - Gate function with source type handling
- `evaluate_application_status()` in `layer_1_run.py` - Application status check
- `evaluate_rejection_status()` in `layer_1_run.py` - Rejection status check
- `get_application_next_action()` in `layer_1_run.py` - Next action mapping

### Scoring Functions (Verified)
- `calculate_score_v6()` in `layer_1_run.py` - Main scoring function v6.4
- `get_score_band()` in `feedback_loop.py` - Score band mapping (optional)

## Installation

```bash
# Install pytest (added to requirements.txt)
pip install pytest

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_dedup.py -v

# Run specific test class
pytest tests/test_dedup.py::TestNormalizeUrl -v

# Run specific test
pytest tests/test_dedup.py::TestNormalizeUrl::test_lowercase_path_electronica_confidencial -v
```

## Test Results

All 77 tests passing:
- `test_dedup.py`: 16 tests ✅
- `test_gate_logic.py`: 36 tests ✅  
- `test_scoring.py`: 25 tests ✅

## Configuration

- **pytest.ini**: Test discovery and configuration
- **requirements.txt**: Updated to include pytest>=7.4.0
- **tests/__init__.py**: Test package initialization

## Regression Prevention

This test suite specifically prevents regression on:
- URL normalization fixes (v9.5.3) - Caso 1, 2
- Title case-insensitive dedup (v9.5.3) - Caso 2
- jk parameter exclusion from tracking params (v9.4.3)
- Content fingerprinting for Indeed jk rotation
- Terminal state protection in gate logic
- Scoring component calculations

## Notes

- Tests follow SP:CONSISTENCY §10.5 - based on actual code audit, not assumptions
- All function names verified against actual implementation
- Test fixtures based on real production cases from Bug Tracker
- Tests are designed to be fast, deterministic, and isolated