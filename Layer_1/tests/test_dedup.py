"""
VANTAGE Dedup Unit Tests

Test suite for normalize_url() and dedup_cross_layer() functions
with 5 real case fixtures from Bug Tracker 39b938befc4281efa1ccdd5d763bfdbf

Cases:
1. Electrónica Confidencial - URL case normalization
2. Vinos La Naval - URL case normalization 
3. Zegna - URL normalization
4. GILSA - Indeed jk rotation (content fingerprinting)
5. Promotwist - Duplicate detection
"""

import pytest
import sys
from pathlib import Path

# Add scripts directory to path
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from feed_processor import (
    normalize_url,
    dedup_cross_layer,
    content_fingerprint,
    compute_content_fingerprint_hash,
    composite_key,
    sha256_hex,
)


# ============================================================================
# FIXTURES - 5 Real Cases from Bug Tracker
# ============================================================================

@pytest.fixture
def electronica_confidencial_case():
    """Caso 1: Electrónica Confidencial - URL case normalization"""
    return {
        "title": "Visual Merchandiser",
        "brand": "Electrónica Confidencial",
        "brand_raw": "Electrónica Confidencial",
        "location": "Madrid",
        "apply_url": "https://www.electronicaconfidencial.com/careers/visual-merchandising",
        "apply_url_uppercase": "https://www.ELECTRONICACONFIDENCIAL.com/CAREERS/VISUAL-MERCHANDISING",
        "layer": "L1",
    }


@pytest.fixture
def vinos_la_naval_case():
    """Caso 2: Vinos La Naval - URL case normalization"""
    return {
        "title": "Responsable de Visual Merchandising",
        "brand": "Vinos La Naval",
        "brand_raw": "Vinos La Naval",
        "location": "Madrid",
        "apply_url": "https://www.vinoslanaval.com/careers/visual-merchandising",
        "apply_url_uppercase": "https://www.vinoslanaval.com/CAREERS/VISUAL-MERCHANDISING",
        "layer": "L2",
    }


@pytest.fixture
def zegna_case():
    """Caso 3: Zegna - URL normalization"""
    return {
        "title": "Visual Merchandiser LATAM",
        "brand": "Zegna",
        "brand_raw": "Zegna",
        "location": "Mexico City",
        "apply_url": "https://careers.zegnagroup.com/jobs/job-details?JobID=270880336",
        "layer": "L1",
    }


@pytest.fixture
def gilsa_case():
    """Caso 4: GILSA - Indeed jk rotation (content fingerprinting)"""
    return {
        "title": "Visual Merchandiser",
        "brand": "GILSA",
        "brand_raw": "GILSA",
        "location": "Mexico City",
        "jk_variants": [
            "9f45d9e2450010ca",
            "cf3ca0540af5d305", 
            "cf3ca0540af5e1f7cb5"
        ],
        "urls": [
            "https://mx.indeed.com/viewjob?jk=9f45d9e2450010ca",
            "https://mx.indeed.com/viewjob?jk=cf3ca0540af5d305",
            "https://mx.indeed.com/viewjob?jk=cf3ca0540af5e1f7cb5"
        ],
        "layer": "L1",
    }


@pytest.fixture
def promotwist_case():
    """Caso 5: Promotwist - Duplicate detection"""
    return {
        "title": "Visual Merchandiser",
        "brand": "PROMOTWIST SC",
        "brand_raw": "PROMOTWIST SC",
        "location": "Monterrey",
        "apply_url": "https://mx.indeed.com/viewjob?jk=dc2f85f4fe4f954a",
        "layer": "L1",
        "duplicate_url": "https://mx.indeed.com/viewjob?jk=dc2f85f4fe4f954a",  # Same URL
    }


# ============================================================================
# normalize_url() Tests
# ============================================================================

class TestNormalizeUrl:
    """Test suite for normalize_url() function"""
    
    def test_lowercase_path_electronica_confidencial(self, electronica_confidencial_case):
        """Test that path is normalized to lowercase (Caso 1)"""
        url_original = electronica_confidencial_case["apply_url"]
        url_uppercase = electronica_confidencial_case["apply_url_uppercase"]
        
        normalized_original = normalize_url(url_original)
        normalized_uppercase = normalize_url(url_uppercase)
        
        assert normalized_original == normalized_uppercase, \
            "URLs with different case should normalize to the same value"
        
        # Verify path is lowercase
        parsed_uppercase = normalized_uppercase.split('/')
        path_part = '/'.join(parsed_uppercase[3:]) if len(parsed_uppercase) > 3 else ""
        assert path_part == path_part.lower(), \
            "Path should be normalized to lowercase"
    
    def test_lowercase_path_vinos_la_naval(self, vinos_la_naval_case):
        """Test that path is normalized to lowercase (Caso 2)"""
        url_original = vinos_la_naval_case["apply_url"]
        url_uppercase = vinos_la_naval_case["apply_url_uppercase"]
        
        normalized_original = normalize_url(url_original)
        normalized_uppercase = normalize_url(url_uppercase)
        
        assert normalized_original == normalized_uppercase, \
            "URLs with different case should normalize to the same value"
    
    def test_tracking_param_removal(self):
        """Test that tracking parameters are removed (including jk per v9.4.3 fix)"""
        url_with_tracking = "https://example.com/job?utm_source=google&jk=abc123&ref=linkedin"
        normalized = normalize_url(url_with_tracking)
        
        assert "utm_source" not in normalized, \
            "utm_source parameter should be removed"
        assert "ref" not in normalized, \
            "ref parameter should be removed"
        assert "jk" not in normalized, \
            "jk parameter should be removed (v9.4.3 fix - jk excluded as tracking param)"
    
    def test_scheme_normalization(self):
        """Test that scheme is normalized to lowercase"""
        url_uppercase = "HTTPS://EXAMPLE.COM/job"
        normalized = normalize_url(url_uppercase)
        
        assert normalized.startswith("https://"), \
            "Scheme should be normalized to lowercase"
    
    def test_netloc_normalization(self):
        """Test that netloc is normalized to lowercase"""
        url_uppercase = "https://EXAMPLE.COM/job"
        normalized = normalize_url(url_uppercase)
        
        assert "example.com" in normalized, \
            "Netloc should be normalized to lowercase"
    
    def test_empty_url(self):
        """Test handling of empty URL"""
        assert normalize_url("") == "", \
            "Empty URL should return empty string"
        assert normalize_url(None) == "", \
            "None URL should return empty string"
    
    def test_url_without_scheme(self):
        """Test handling of URL without scheme"""
        url_no_scheme = "example.com/job"
        normalized = normalize_url(url_no_scheme)
        
        assert normalized.startswith("https://"), \
            "URL without scheme should get https:// prefix"


# ============================================================================
# content_fingerprint() Tests
# ============================================================================

class TestContentFingerprint:
    """Test suite for content_fingerprint() function"""
    
    def test_gilsa_jk_rotation(self, gilsa_case):
        """Test that Indeed jk rotation produces same fingerprint (Caso 4)"""
        fingerprints = []
        
        for i, jk in enumerate(gilsa_case["jk_variants"]):
            record = {
                "title": gilsa_case["title"],
                "brand": gilsa_case["brand"],
                "brand_raw": gilsa_case["brand_raw"],
                "location": gilsa_case["location"],
                "job_id": jk,
                "apply_url": gilsa_case["urls"][i],
            }
            fp = content_fingerprint(record)
            fingerprints.append(fp)
        
        # All fingerprints should be identical
        assert len(set(fingerprints)) == 1, \
            "All GILSA records with different jk should have same fingerprint"
    
    def test_case_insensitivity(self):
        """Test that fingerprint is case-insensitive"""
        record_lower = {
            "title": "visual merchandiser",
            "brand": "gilsa",
            "location": "mexico city",
        }
        record_upper = {
            "title": "VISUAL MERCHANDISER",
            "brand": "GILSA",
            "location": "MEXICO CITY",
        }
        
        fp_lower = content_fingerprint(record_lower)
        fp_upper = content_fingerprint(record_upper)
        
        assert fp_lower == fp_upper, \
            "Fingerprint should be case-insensitive"
    
    def test_different_positions_different_fingerprints(self):
        """Test that different positions have different fingerprints"""
        record1 = {
            "title": "Visual Merchandiser",
            "brand": "GILSA",
            "location": "Mexico City",
        }
        record2 = {
            "title": "Store Manager",
            "brand": "GILSA",
            "location": "Mexico City",
        }
        
        fp1 = content_fingerprint(record1)
        fp2 = content_fingerprint(record2)
        
        assert fp1 != fp2, \
            "Different positions should have different fingerprints"
    
    def test_missing_fields_handling(self):
        """Test handling of missing fields"""
        record_no_location = {
            "title": "Visual Merchandiser",
            "brand": "GILSA",
            "location": "",
        }
        
        fp = content_fingerprint(record_no_location)
        assert fp is not None, \
            "Fingerprint should handle missing location"
        assert isinstance(fp, str), \
            "Fingerprint should return a string"


# ============================================================================
# composite_key() Tests  
# ============================================================================

class TestCompositeKey:
    """Test suite for composite_key() function"""
    
    def test_composite_key_consistency(self):
        """Test that composite_key is consistent"""
        record = {
            "title": "Visual Merchandiser",
            "brand": "GILSA",
            "location": "Mexico City",
        }
        
        ck1 = composite_key(record)
        ck2 = composite_key(record)
        
        assert ck1 == ck2, \
            "Composite key should be consistent for same record"
    
    def test_composite_key_case_insensitive(self):
        """Test that composite_key is case-insensitive"""
        record_lower = {
            "title": "visual merchandiser",
            "brand": "gilsa",
            "location": "mexico city",
        }
        record_upper = {
            "title": "VISUAL MERCHANDISER",
            "brand": "GILSA",
            "location": "MEXICO CITY",
        }
        
        ck_lower = composite_key(record_lower)
        ck_upper = composite_key(record_upper)
        
        assert ck_lower == ck_upper, \
            "Composite key should be case-insensitive"


# ============================================================================
# Integration Tests
# ============================================================================

class TestDedupIntegration:
    """Integration tests for dedup functionality"""
    
    def test_url_normalization_before_hashing(self, electronica_confidencial_case):
        """Test that URLs are normalized before hashing (Caso 1)"""
        url1 = electronica_confidencial_case["apply_url"]
        url2 = electronica_confidencial_case["apply_url_uppercase"]
        
        hash1 = sha256_hex(f"url:{normalize_url(url1)}")
        hash2 = sha256_hex(f"url:{normalize_url(url2)}")
        
        assert hash1 == hash2, \
            "URLs should be normalized before hashing to prevent duplicates"
    
    def test_gilsa_fingerprint_consistency(self, gilsa_case):
        """Test that GILSA fingerprint is consistent across jk variants (Caso 4)"""
        fingerprint_hashes = []
        
        for i, jk in enumerate(gilsa_case["jk_variants"]):
            record = {
                "title": gilsa_case["title"],
                "brand": gilsa_case["brand"],
                "brand_raw": gilsa_case["brand_raw"],
                "location": gilsa_case["location"],
                "job_id": jk,
                "apply_url": gilsa_case["urls"][i],
            }
            fp_hash = compute_content_fingerprint_hash(record)
            fingerprint_hashes.append(fp_hash)
        
        # All fingerprint hashes should be identical
        assert len(set(fingerprint_hashes)) == 1, \
            "All GILSA records should have same fingerprint hash"
    
    def test_promotwist_duplicate_detection(self, promotwist_case):
        """Test that Promotwist duplicate is detected (Caso 5)"""
        record1 = {
            "title": promotwist_case["title"],
            "brand": promotwist_case["brand"],
            "brand_raw": promotwist_case["brand_raw"],
            "location": promotwist_case["location"],
            "apply_url": promotwist_case["apply_url"],
            "layer": promotwist_case["layer"],
        }
        
        record2 = {
            "title": promotwist_case["title"],
            "brand": promotwist_case["brand"],
            "brand_raw": promotwist_case["brand_raw"],
            "location": promotwist_case["location"],
            "apply_url": promotwist_case["duplicate_url"],
            "layer": "L2",
        }
        
        # Both should produce the same hash since URLs are identical
        from feed_processor import compute_dedup_hash
        hash1 = compute_dedup_hash(record1)
        hash2 = compute_dedup_hash(record2)
        
        assert hash1 == hash2, \
            "Promotwist duplicates should have same hash"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])