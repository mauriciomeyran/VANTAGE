"""
VANTAGE Layer 3 Mail Unit Tests

Test suite for layer_3_mail.py functions, specifically synthetic URL detection.

Bug Tracker: 3be938be-fc42-8195-a602-d3a8c1bf0adf
Fix: Detect synthetic Computrabajo URLs with pattern [rol]-[marca]-2024
"""

import pytest
import sys
from pathlib import Path

# Add scripts directory to path
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

try:
    from layer_3_mail import canonicalize_url, SYNTHETIC_CT_PATTERNS
    LAYER3_AVAILABLE = True
except ImportError:
    LAYER3_AVAILABLE = False
    pytest.skip("layer_3_mail module not available", allow_module_level=True)


# ============================================================================
# Synthetic URL Detection Tests (Bug Fix 3be938be-fc42-8195-a602-d3a8c1bf0adf)
# ============================================================================

class TestSyntheticURLDetection:
    """Test suite for synthetic Computrabajo URL detection fix"""
    
    def test_synthetic_ct_pattern_rol_marca_2024(self):
        """Test that [rol]-[marca]-2024 pattern is detected as synthetic"""
        url = "https://www.computrabajo.com/jobs/visual-merchandiser-hm-2024"
        canonical, reason = canonicalize_url(url)
        assert reason == "SYNTHETIC_AGGREGATOR_URL", \
            f"URL with pattern [rol]-[marca]-2024 should be detected as synthetic, got: {reason}"
    
    def test_synthetic_ct_pattern_with_accents(self):
        """Test that synthetic pattern with URL-encoded accents is detected"""
        url = "https://www.computrabajo.com/jobs/visual-merchandiser-galer%C3%ADas-2024"
        canonical, reason = canonicalize_url(url)
        assert reason == "SYNTHETIC_AGGREGATOR_URL", \
            f"URL with encoded accents should be detected as synthetic, got: {reason}"
    
    def test_synthetic_ct_pattern_with_encoding(self):
        """Test that synthetic pattern with various encoding is detected"""
        url = "https://www.computrabajo.com/jobs/display-coordinator-bodega-auerrer%C3%A1-2024"
        canonical, reason = canonicalize_url(url)
        assert reason == "SYNTHETIC_AGGREGATOR_URL", \
            f"URL with encoding should be detected as synthetic, got: {reason}"
    
    def test_synthetic_ct_pattern_variations(self):
        """Test various synthetic CT patterns from the incident"""
        synthetic_urls = [
            "https://www.computrabajo.com/jobs/vm-coordinator-berhka-2024",
            "https://www.computrabajo.com/jobs/display-coordinator-walmart-2024",
            "https://www.computrabajo.com/jobs/visual-merchandiser-sanborns-2024",
            "https://www.computrabajo.com/jobs/vm-coordinator-stradivarius-2024",
        ]
        
        for url in synthetic_urls:
            canonical, reason = canonicalize_url(url)
            assert reason == "SYNTHETIC_AGGREGATOR_URL", \
                f"URL {url} should be detected as synthetic, got: {reason}"
    
    def test_non_synthetic_ct_url_accepted(self):
        """Test that valid Computrabajo URLs without synthetic pattern are accepted"""
        # This is a hypothetical valid CT URL - in reality would need to be tested
        # against actual CT URLs to ensure pattern doesn't over-match
        url = "https://www.computrabajo.com/ofertas-de-trabajo/visual-merchandiser"
        canonical, reason = canonicalize_url(url)
        assert reason == "", \
            f"Valid CT URL without synthetic pattern should be accepted, got: {reason}"
    
    def test_non_computrabajo_urls_unaffected(self):
        """Test that non-Computrabajo URLs are not affected by synthetic pattern"""
        non_ct_urls = [
            "https://mx.indeed.com/viewjob?jk=85f97a522ec80fc8",
            "https://www.linkedin.com/jobs/view/4414059078",
            "https://www.indeed.com/jobs/view/",
        ]
        
        for url in non_ct_urls:
            canonical, reason = canonicalize_url(url)
            assert reason == "", \
                f"Non-Computrabajo URL {url} should not be detected as synthetic, got: {reason}"
    
    def test_url_original_preserved(self):
        """Test that canonicalize_url returns original URL, not decoded version"""
        url_encoded = "https://www.computrabajo.com/jobs/visual-merchandiser-galer%C3%ADas-2024"
        canonical, reason = canonicalize_url(url_encoded)
        
        # The returned URL should be the original encoded version, not decoded
        assert canonical == url_encoded, \
            f"Original URL should be preserved, got: {canonical}"
    
    def test_current_patterns_still_work(self):
        """Test that existing synthetic patterns still work"""
        existing_patterns = [
            "https://www.computrabajo.com/jobs/123456",  # numeric ID corto
            "https://www.computrabajo.com/jobs/123456789012",  # numeric ID largo
        ]
        
        for url in existing_patterns:
            canonical, reason = canonicalize_url(url)
            assert reason == "SYNTHETIC_AGGREGATOR_URL", \
                f"Existing pattern should still detect {url} as synthetic, got: {reason}"


# ============================================================================
# Integration Tests - 21 URLs from Incident
# ============================================================================

class TestIncidentURLs:
    """Test the 21 URLs from the specific incident that triggered this fix"""
    
    def test_all_21_incident_urls_processed_correctly(self):
        """Test that all 21 incident URLs are processed correctly"""
        incident_urls = [
            # Indeed/LinkedIn (should NOT be detected as synthetic)
            ("https://mx.indeed.com/viewjob?jk=85f97a522ec80fc8", False),
            ("https://www.linkedin.com/jobs/view/4454554329/?lipi=...", False),
            ("https://www.linkedin.com/jobs/view/4414059078", False),
            
            # Computrabajo synthetic URLs (should BE detected as synthetic)
            ("https://www.computrabajo.com/jobs/visual-merchandiser-hm-2024", True),
            ("https://www.computrabajo.com/jobs/visual-merchandiser-oxxo-2024", True),
            ("https://www.computrabajo.com/jobs/display-coordinator-walmart-2024", True),
            ("https://www.computrabajo.com/jobs/visual-merchandiser-coppel-2024", True),
            ("https://www.computrabajo.com/jobs/vm-coordinator-berhka-2024", True),
            ("https://www.computrabajo.com/jobs/visual-merchandiser-sanborns-2024", True),
            ("https://www.computrabajo.com/jobs/display-coordinator-liverpool-2024", True),
            ("https://www.computrabajo.com/jobs/visual-merchandiser-the-store-2024", True),
            ("https://www.computrabajo.com/jobs/vm-coordinator-stradivarius-2024", True),
            ("https://www.computrabajo.com/jobs/visual-merchandiser-mass-2024", True),
            ("https://www.computrabajo.com/jobs/display-coordinator-bodega-auerrer%C3%A1-2024", True),
            ("https://www.computrabajo.com/jobs/visual-merchandiser-suburbia-2024", True),
            ("https://www.computrabajo.com/jobs/vm-coordinator-ovni-2024", True),
            ("https://www.computrabajo.com/jobs/visual-merchandiser-galer%C3%ADas-2024", True),
            ("https://www.computrabajo.com/jobs/display-coordinator-coppel-2024", True),
            ("https://www.computrabajo.com/jobs/visual-merchandiser-liverpool-2024", True),
            ("https://www.computrabajo.com/jobs/vm-coordinator-sanborns-2024", True),
            ("https://www.computrabajo.com/jobs/display-coordinator-berhka-2024", True),
        ]
        
        correct_count = 0
        for url, should_be_synthetic in incident_urls:
            canonical, reason = canonicalize_url(url)
            is_synthetic = (reason == "SYNTHETIC_AGGREGATOR_URL")
            
            if is_synthetic == should_be_synthetic:
                correct_count += 1
            else:
                print(f"FAIL: {url} - Expected synthetic={should_be_synthetic}, got={is_synthetic}, reason={reason}")
        
        assert correct_count == len(incident_urls), \
            f"Expected {len(incident_urls)}/21 correct decisions, got {correct_count}/21"
