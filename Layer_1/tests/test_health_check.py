"""
VANTAGE Health Check Unit Tests

Test suite for health_check.py functions:
- check_auto_link_corruption() function
- Auto-link corruption detection patterns
- Advisory output formatting
"""

import pytest
import sys
import os
import re
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

# Add scripts directory to path
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_md_with_underscore_http():
    """Sample markdown content with _http:// pattern"""
    return """
# Test Document

This is a test document with a corrupted link:
_link_http://example.com

Another _http://test.org pattern.
"""

@pytest.fixture
def sample_md_with_auto_links():
    """Sample markdown content with auto-link patterns"""
    return """
# Test Document

Here are some auto-links:
[example.com](http://example.com)
[test.org](http://test.org)
[my-file.md](http://my-file.md)
"""

@pytest.fixture
def sample_md_clean():
    """Sample markdown content without corruption patterns"""
    return """
# Test Document

This is a clean document with normal links:
[Example](https://example.com)
[Test](http://test.org/page)
[Internal Link](../other-file.md)
"""

@pytest.fixture
def sample_md_mixed():
    """Sample markdown content with both good and bad patterns"""
    return """
# Test Document

Good link: [Example](https://example.com)
Bad auto-link: [test.com](http://test.com)
Another good: [Docs](../docs.md)
Underscore corruption: _http://bad.org
"""


# ============================================================================
# Pattern Detection Tests
# ============================================================================

class TestAutoLinkPatterns:
    """Test suite for auto-link corruption pattern detection"""
    
    def test_underscore_pattern_detection(self):
        """Test that _http:// pattern is correctly detected"""
        underscore_pattern = re.compile(r'_http://')
        
        test_string = "This has _http://example.com in it"
        matches = underscore_pattern.findall(test_string)
        
        assert len(matches) == 1, \
            "Should detect exactly one _http:// pattern"
        assert matches[0] == "_http://", \
            "Should match the exact _http:// pattern"
    
    def test_auto_link_pattern_detection(self):
        """Test that auto-link pattern [text](http://text) is correctly detected"""
        auto_link_pattern = re.compile(r'\[([^\]]+)\]\(http[s]?://\1\)')
        
        test_string = "[example.com](http://example.com)"
        matches = auto_link_pattern.findall(test_string)
        
        assert len(matches) == 1, \
            "Should detect exactly one auto-link pattern"
        assert matches[0] == "example.com", \
            "Should extract the text from the auto-link"
    
    def test_auto_link_pattern_with_https(self):
        """Test that auto-link pattern works with HTTPS"""
        auto_link_pattern = re.compile(r'\[([^\]]+)\]\(http[s]?://\1\)')
        
        test_string = "[secure.com](https://secure.com)"
        matches = auto_link_pattern.findall(test_string)
        
        assert len(matches) == 1, \
            "Should detect HTTPS auto-link pattern"
    
    def test_normal_links_not_detected_as_auto_links(self):
        """Test that normal links are not detected as auto-links"""
        auto_link_pattern = re.compile(r'\[([^\]]+)\]\(http[s]?://\1\)')
        
        test_string = "[Example](https://example.com/page)"
        matches = auto_link_pattern.findall(test_string)
        
        assert len(matches) == 0, \
            "Normal links should not be detected as auto-links"
    
    def test_internal_links_not_detected_as_auto_links(self):
        """Test that internal links are not detected as auto-links"""
        auto_link_pattern = re.compile(r'\[([^\]]+)\]\(http[s]?://\1\)')
        
        test_string = "[Docs](../docs.md)"
        matches = auto_link_pattern.findall(test_string)
        
        assert len(matches) == 0, \
            "Internal links should not be detected as auto-links"


# ============================================================================
# check_auto_link_corruption() Tests
# ============================================================================

class TestCheckAutoLinkCorruption:
    """Test suite for check_auto_link_corruption() function (D5-real version)"""
    
    @patch("health_check.ACTIVE_DIR")
    @patch("health_check.REPO_ROOT")
    @patch("health_check.DATA_DIR")
    def test_check_auto_link_with_underscore_corruption(self, mock_data_dir, mock_repo_root, mock_active_dir, 
                                                          sample_md_with_underscore_http, tmp_path):
        """Test detection of _http:// corruption pattern"""
        import health_check
        
        # Create temporary test file
        test_file = tmp_path / "test.md"
        test_file.write_text(sample_md_with_underscore_http)
        
        # Mock directories
        mock_active_dir.exists.return_value = True
        mock_active_dir.glob.return_value = [test_file]
        
        mock_repo_root.__truediv__.return_value.exists.return_value = False
        mock_data_dir.exists.return_value = False
        
        # Capture stdout
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            result = health_check.check_auto_link_corruption()
        
        output = captured_output.getvalue()
        
        assert result is True, \
            "check_auto_link_corruption should return True (advisory)"
        assert "auto-link" in output.lower(), \
            "Output should mention auto-link check"
        assert "patrones sospechosos" in output or "patterns" in output.lower(), \
            "Output should mention suspicious patterns"
    
    @patch("health_check.ACTIVE_DIR")
    @patch("health_check.REPO_ROOT")
    @patch("health_check.DATA_DIR")
    def test_check_auto_link_with_auto_link_corruption(self, mock_data_dir, mock_repo_root, mock_active_dir,
                                                        sample_md_with_auto_links, tmp_path):
        """Test detection of auto-link corruption pattern"""
        import health_check
        
        # Create temporary test file
        test_file = tmp_path / "test.md"
        test_file.write_text(sample_md_with_auto_links)
        
        # Mock directories
        mock_active_dir.exists.return_value = True
        mock_active_dir.glob.return_value = [test_file]
        
        mock_repo_root.__truediv__.return_value.exists.return_value = False
        mock_data_dir.exists.return_value = False
        
        # Capture stdout
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            result = health_check.check_auto_link_corruption()
        
        output = captured_output.getvalue()
        
        assert result is True, \
            "check_auto_link_corruption should return True (advisory)"
        assert "auto-link" in output.lower(), \
            "Output should mention auto-link check"
    
    @patch("health_check.ACTIVE_DIR")
    @patch("health_check.REPO_ROOT")
    @patch("health_check.DATA_DIR")
    def test_check_auto_link_clean_content(self, mock_data_dir, mock_repo_root, mock_active_dir,
                                           sample_md_clean, tmp_path):
        """Test with clean content (no corruption)"""
        import health_check
        
        # Create temporary test file
        test_file = tmp_path / "test.md"
        test_file.write_text(sample_md_clean)
        
        # Mock directories
        mock_active_dir.exists.return_value = True
        mock_active_dir.glob.return_value = [test_file]
        
        mock_repo_root.__truediv__.return_value.exists.return_value = False
        mock_data_dir.exists.return_value = False
        
        # Capture stdout
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            result = health_check.check_auto_link_corruption()
        
        output = captured_output.getvalue()
        
        assert result is True, \
            "check_auto_link_corruption should return True (advisory)"
        assert "sin corrupción detectada" in output or "no corruption" in output.lower(), \
            "Output should report no corruption detected"
    
    @patch("health_check.ACTIVE_DIR")
    @patch("health_check.REPO_ROOT")
    @patch("health_check.DATA_DIR")
    def test_check_auto_link_mixed_content(self, mock_data_dir, mock_repo_root, mock_active_dir,
                                            sample_md_mixed, tmp_path):
        """Test with mixed content (both good and bad patterns)"""
        import health_check
        
        # Create temporary test file
        test_file = tmp_path / "test.md"
        test_file.write_text(sample_md_mixed)
        
        # Mock directories
        mock_active_dir.exists.return_value = True
        mock_active_dir.glob.return_value = [test_file]
        
        mock_repo_root.__truediv__.return_value.exists.return_value = False
        mock_data_dir.exists.return_value = False
        
        # Capture stdout
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            result = health_check.check_auto_link_corruption()
        
        output = captured_output.getvalue()
        
        assert result is True, \
            "check_auto_link_corruption should return True (advisory)"
        assert "patrones sospechosos" in output or "patterns" in output.lower(), \
            "Output should report suspicious patterns in mixed content"
    
    @patch("health_check.ACTIVE_DIR")
    @patch("health_check.REPO_ROOT")
    @patch("health_check.DATA_DIR")
    def test_check_auto_link_nonexistent_directory(self, mock_data_dir, mock_repo_root, mock_active_dir):
        """Test handling of nonexistent directories"""
        import health_check
        
        # Mock directories as nonexistent
        mock_active_dir.exists.return_value = False
        mock_repo_root.__truediv__.return_value.exists.return_value = False
        mock_data_dir.exists.return_value = False
        
        # Capture stdout
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            result = health_check.check_auto_link_corruption()
        
        output = captured_output.getvalue()
        
        assert result is True, \
            "check_auto_link_corruption should return True even with no directories"
    
    @patch("health_check.ACTIVE_DIR")
    @patch("health_check.REPO_ROOT")
    @patch("health_check.DATA_DIR")
    def test_check_auto_link_entity_description_corruption(self, mock_data_dir, mock_repo_root, mock_active_dir):
        """Test D5-real: detection of corruption in entity descriptions (simplified)"""
        import health_check
        
        # Mock directories - only DATA_DIR exists to test the code path
        mock_active_dir.exists.return_value = False
        mock_repo_root.__truediv__.return_value.exists.return_value = False
        mock_data_dir.exists.return_value = True
        mock_data_dir.__truediv__.return_value.exists.return_value = False  # No entity_index file
        
        # Capture stdout
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            result = health_check.check_auto_link_corruption()
        
        output = captured_output.getvalue()
        
        assert result is True, \
            "check_auto_link_corruption should return True (advisory)"
        assert "entity_index_v2.json no encontrado" in output, \
            "Output should report missing entity index file"
    
    @patch("health_check.ACTIVE_DIR")
    @patch("health_check.REPO_ROOT")
    @patch("health_check.DATA_DIR")
    def test_check_auto_link_read_error_handling(self, mock_data_dir, mock_repo_root, mock_active_dir, tmp_path):
        """Test graceful handling of file read errors"""
        import health_check
        
        # Create a file that will cause read error
        test_file = tmp_path / "test.md"
        test_file.write_text("content")
        
        # Mock to raise permission error
        def mock_glob_error(pattern):
            class FailingFile:
                def read_text(self, encoding='utf-8'):
                    raise PermissionError("Permission denied")
                name = "test.md"
            return [FailingFile()]
        
        mock_active_dir.exists.return_value = True
        mock_active_dir.glob = mock_glob_error
        
        mock_repo_root.__truediv__.return_value.exists.return_value = False
        mock_data_dir.exists.return_value = False
        
        # Should not raise exception, just handle gracefully
        result = health_check.check_auto_link_corruption()
        
        assert result is True, \
            "check_auto_link_corruption should handle read errors gracefully"


# ============================================================================
# Integration Tests
# ============================================================================

class TestHealthCheckIntegration:
    """Integration tests for health check functionality"""
    
    def test_health_check_module_structure(self):
        """Test that health_check module has expected structure"""
        import health_check
        
        # Verify key functions exist
        assert hasattr(health_check, 'check_auto_link_corruption'), \
            "health_check should have check_auto_link_corruption function"
        assert hasattr(health_check, 'main'), \
            "health_check should have main function"
        assert hasattr(health_check, 'check_env'), \
            "health_check should have check_env function"
        assert hasattr(health_check, 'check_git'), \
            "health_check should have check_git function"
    
    @patch("health_check.check_auto_link_corruption")
    def test_auto_link_check_in_main_checks(self, mock_auto_link_check):
        """Test that auto_link check is included in main checks"""
        import health_check
        
        # Mock all other checks to avoid side effects
        with patch.object(health_check, 'check_system_version', return_value=True), \
             patch.object(health_check, 'check_env', return_value=True), \
             patch.object(health_check, 'check_git', return_value=True), \
             patch.object(health_check, 'check_vgit_last', return_value=True), \
             patch.object(health_check, 'check_notion_reachable', return_value=True), \
             patch.object(health_check, 'check_docs_sync', return_value=True), \
             patch.object(health_check, 'check_vdoc_last', return_value=True), \
             patch.object(health_check, 'check_index_age', return_value=True), \
             patch.object(health_check, 'check_layer3_heartbeat', return_value=True), \
             patch.object(health_check, 'check_census_age', return_value=True), \
             patch.object(health_check, 'check_pending_tickets', return_value=True):
            
            # Capture sys.exit to prevent actual exit
            with patch('sys.exit') as mock_exit:
                health_check.main()
        
        # Verify auto_link check was called
        mock_auto_link_check.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
