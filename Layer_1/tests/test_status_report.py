"""
VANTAGE Status Report Unit Tests

Test suite for status_report.py functions:
- inspect_archive_queue() function
- --archive-queue CLI flag functionality
- Archive queue inspection and formatting
"""

import pytest
import sys
import os
import argparse
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from io import StringIO

# Add scripts directory to path
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_graph_stats():
    """Mock graph statistics"""
    return {
        "total_edges": 10,
        "total_nodes": 8,
        "edges_by_type": {
            "archived_from": 3,
            "reference": 5,
            "related_to": 2
        }
    }


@pytest.fixture
def mock_graph_stats_no_archive():
    """Mock graph statistics without archived_from edges"""
    return {
        "total_edges": 7,
        "total_nodes": 8,
        "edges_by_type": {
            "reference": 5,
            "related_to": 2
        }
    }


# ============================================================================
# inspect_archive_queue() Tests
# ============================================================================

class TestInspectArchiveQueue:
    """Test suite for inspect_archive_queue() function"""
    
    @patch("graph_layer.graph_stats")
    def test_inspect_archive_queue_with_archived_edges(self, mock_graph_stats_fn, mock_graph_stats):
        """Test inspect_archive_queue with archived_from edges present"""
        import status_report
        
        mock_graph_stats_fn.return_value = mock_graph_stats
        
        # Capture stdout
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            result = status_report.inspect_archive_queue()
        
        output = captured_output.getvalue()
        
        assert result is True, \
            "inspect_archive_queue should return True on success"
        assert "ARCHIVE QUEUE INSPECTION" in output, \
            "Output should contain archive queue inspection header"
        assert "Total edges: 10" in output, \
            "Output should show total edges count"
        assert "Total nodes: 8" in output, \
            "Output should show total nodes count"
        assert "archived_from: 3" in output, \
            "Output should show archived_from edges count"
        assert "Archived From Edges: 3" in output, \
            "Output should show archived_from edges summary"
        assert "Hay 3 relaciones de archivo en el grafo" in output, \
            "Output should show warning about archived relationships"
    
    @patch("graph_layer.graph_stats")
    def test_inspect_archive_queue_without_archived_edges(self, mock_graph_stats_fn, mock_graph_stats_no_archive):
        """Test inspect_archive_queue without archived_from edges"""
        import status_report
        
        mock_graph_stats_fn.return_value = mock_graph_stats_no_archive
        
        # Capture stdout
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            result = status_report.inspect_archive_queue()
        
        output = captured_output.getvalue()
        
        assert result is True, \
            "inspect_archive_queue should return True on success"
        assert "Archived From Edges: 0" in output, \
            "Output should show 0 archived_from edges"
        assert "No hay relaciones de archivo pendientes" in output, \
            "Output should show success message when no archived edges"
    
    @patch("graph_layer.graph_stats")
    def test_inspect_archive_queue_import_error(self, mock_graph_stats_fn):
        """Test inspect_archive_queue handles import errors gracefully"""
        import status_report
        
        # Force an import error by making graph_stats unavailable
        mock_graph_stats_fn.side_effect = ImportError("graph_layer not found")
        
        # Capture stdout
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            result = status_report.inspect_archive_queue()
        
        output = captured_output.getvalue()
        
        assert result is False, \
            "inspect_archive_queue should return False on import error"
        assert "Error importing graph_layer" in output, \
            "Output should show import error message"
    
    @patch("graph_layer.graph_stats")
    def test_inspect_archive_queue_general_error(self, mock_graph_stats_fn):
        """Test inspect_archive_queue handles general errors gracefully"""
        import status_report
        
        # Force a general error
        mock_graph_stats_fn.side_effect = Exception("Unexpected error")
        
        # Capture stdout
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            result = status_report.inspect_archive_queue()
        
        output = captured_output.getvalue()
        
        assert result is False, \
            "inspect_archive_queue should return False on general error"
        assert "Error inspecting archive queue" in output, \
            "Output should show general error message"


# ============================================================================
# CLI Argument Tests
# ============================================================================

class TestStatusReportCLI:
    """Test suite for status_report.py CLI arguments"""
    
    @patch("argparse.ArgumentParser")
    @patch("status_report.inspect_archive_queue")
    @patch("status_report.load_dotenv")
    @patch.dict(os.environ, {"NOTION_TOKEN": "test_token"})
    def test_archive_queue_flag_triggers_inspection(self, mock_load_dotenv, mock_inspect, mock_parser):
        """Test that --archive-queue flag triggers archive queue inspection"""
        import status_report
        
        # Mock argparse to simulate --archive-queue flag
        test_args = ["status_report.py", "--archive-queue"]
        
        mock_args = MagicMock()
        mock_args.archive_queue = True
        mock_parser.return_value.parse_args.return_value = mock_args
        
        with patch('sys.argv', test_args):
            status_report.main()
        
        # Verify inspect_archive_queue was called
        mock_inspect.assert_called_once()
    
    @patch("argparse.ArgumentParser")
    @patch("status_report.load_dotenv")
    @patch("status_report.query_database")
    @patch.dict(os.environ, {"NOTION_TOKEN": "test_token"})
    def test_no_archive_queue_flag_runs_normal_report(self, mock_load_dotenv, mock_query, mock_parser):
        """Test that without --archive-queue flag, normal report runs"""
        import status_report
        
        # Mock query_database to return empty results
        mock_query.return_value = []
        
        # Mock argparse to simulate no --archive-queue flag
        test_args = ["status_report.py"]
        
        mock_args = MagicMock()
        mock_args.archive_queue = False
        mock_parser.return_value.parse_args.return_value = mock_args
        
        with patch('sys.argv', test_args):
            status_report.main()
        
        # Verify normal report flow (query_database should be called)
        mock_query.assert_called_once()


# ============================================================================
# Integration Tests
# ============================================================================

class TestStatusReportIntegration:
    """Integration tests for status report functionality"""
    
    @patch("graph_layer.graph_stats")
    def test_archive_queue_integration_with_graph_layer(self, mock_graph_stats_fn, mock_graph_stats):
        """Test integration between inspect_archive_queue and graph_layer"""
        import status_report
        
        mock_graph_stats_fn.return_value = mock_graph_stats
        
        # Test that the function can successfully call graph_layer functions
        result = status_report.inspect_archive_queue()
        
        assert result is True, \
            "Integration with graph_layer should work correctly"
        mock_graph_stats_fn.assert_called_once()
    
    def test_status_report_module_structure(self):
        """Test that status_report module has expected structure"""
        import status_report
        
        # Verify key functions exist
        assert hasattr(status_report, 'inspect_archive_queue'), \
            "status_report should have inspect_archive_queue function"
        assert hasattr(status_report, 'main'), \
            "status_report should have main function"
        assert hasattr(status_report, 'query_database'), \
            "status_report should have query_database function"
        assert hasattr(status_report, 'txt'), \
            "status_report should have txt function"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
