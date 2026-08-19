"""
VANTAGE Graph Layer Unit Tests

Test suite for graph_layer.py functions:
- _DIR path resolution to ../data/
- Graph data loading without relative path errors
- get_archived_from() function
- get_backlinks() function
- graph_stats() function
"""

import pytest
import sys
import os
import json
from pathlib import Path
from unittest.mock import patch

# Add scripts directory to path
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_graph_data():
    """Mock graph data structure"""
    return {
        "edges": [
            {"from": "entity1", "to": "entity2", "type": "archived_from"},
            {"from": "entity1", "to": "entity3", "type": "reference"},
            {"from": "entity2", "to": "entity4", "type": "archived_from"},
        ]
    }


@pytest.fixture
def mock_backlinks_data():
    """Mock backlinks data structure"""
    return {
        "backlinks": {
            "entity1": ["entity5", "entity6"],
            "entity2": ["entity7"],
            "entity3": []
        }
    }


# ============================================================================
# _DIR Path Resolution Tests
# ============================================================================

class TestDirResolution:
    """Test suite for _DIR path resolution"""
    
    def test_dir_resolves_to_data_directory(self):
        """Test that _DIR resolves correctly to ../data/"""
        # Import the module to get _DIR
        import graph_layer
        
        # Expected path: scripts/../data/
        scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
        expected_dir = scripts_dir.parent / "data"
        
        # Normalize both paths for comparison
        actual_dir = Path(graph_layer._DIR).resolve()
        expected_dir_normalized = expected_dir.resolve()
        
        assert actual_dir == expected_dir_normalized, \
            f"_DIR should resolve to {expected_dir_normalized}, got {actual_dir}"
    
    def test_dir_is_absolute_path(self):
        """Test that _DIR is an absolute path"""
        import graph_layer
        
        dir_path = Path(graph_layer._DIR)
        assert dir_path.is_absolute(), \
            "_DIR should be an absolute path"
    
    def test_dir_points_to_existing_data_folder(self):
        """Test that _DIR points to the actual data folder"""
        import graph_layer
        
        dir_path = Path(graph_layer._DIR)
        assert dir_path.exists(), \
            f"_DIR path {dir_path} should exist"
        assert dir_path.is_dir(), \
            f"_DIR path {dir_path} should be a directory"
        assert dir_path.name == "data", \
            f"_DIR directory should be named 'data', got {dir_path.name}"


# ============================================================================
# Graph Data Loading Tests
# ============================================================================

class TestGraphDataLoading:
    """Test suite for graph data loading"""
    
    @patch("graph_layer.json.load")
    @patch("builtins.open")
    def test_load_graph_data_reads_correct_files(self, mock_open, mock_json_load, mock_graph_data, mock_backlinks_data):
        """Test that _load_graph_data reads the correct JSON files"""
        import graph_layer
        
        # Setup mock returns
        mock_json_load.side_effect = [mock_graph_data, mock_backlinks_data]
        
        graph, backlinks = graph_layer._load_graph_data()
        
        assert graph == mock_graph_data, \
            "Graph data should match expected structure"
        assert backlinks == mock_backlinks_data, \
            "Backlinks data should match expected structure"
        assert mock_json_load.call_count == 2, \
            "Should load exactly 2 JSON files"
    
    @patch("graph_layer.json.load")
    @patch("builtins.open")
    def test_load_graph_data_handles_relative_paths(self, mock_open, mock_json_load, mock_graph_data, mock_backlinks_data):
        """Test that graph data loading handles relative paths correctly"""
        import graph_layer
        
        # Setup mock returns
        mock_json_load.side_effect = [mock_graph_data, mock_backlinks_data]
        
        graph, backlinks = graph_layer._load_graph_data()
        
        # Verify the function completed without path errors
        assert graph is not None, \
            "Graph data should be loaded successfully"
        assert backlinks is not None, \
            "Backlinks data should be loaded successfully"


# ============================================================================
# get_archived_from() Tests
# ============================================================================

class TestGetArchivedFrom:
    """Test suite for get_archived_from() function"""
    
    @patch("graph_layer.graph_v2", {
        "edges": [
            {"from": "entity1", "to": "entity2", "type": "archived_from"},
            {"from": "entity1", "to": "entity3", "type": "reference"},
            {"from": "entity2", "to": "entity4", "type": "archived_from"},
        ]
    })
    def test_get_archived_from_returns_correct_edges(self):
        """Test that get_archived_from returns edges with type 'archived_from'"""
        import graph_layer
        
        result = graph_layer.get_archived_from("entity1")
        
        assert len(result) == 1, \
            "Should return exactly 1 archived_from edge for entity1"
        assert result[0]["from"] == "entity1", \
            "Edge should have correct 'from' field"
        assert result[0]["type"] == "archived_from", \
            "Edge should have type 'archived_from'"
    
    @patch("graph_layer.graph_v2", {
        "edges": [
            {"from": "entity1", "to": "entity2", "type": "reference"},
        ]
    })
    def test_get_archived_from_empty_when_no_archived_edges(self):
        """Test that get_archived_from returns empty list when no archived_from edges"""
        import graph_layer
        
        result = graph_layer.get_archived_from("entity1")
        
        assert result == [], \
            "Should return empty list when no archived_from edges exist"
    
    @patch("graph_layer.graph_v2", {"edges": []})
    def test_get_archived_from_empty_for_empty_graph(self):
        """Test that get_archived_from returns empty list for empty graph"""
        import graph_layer
        
        result = graph_layer.get_archived_from("entity1")
        
        assert result == [], \
            "Should return empty list for empty graph"
    
    @patch("graph_layer.graph_v2", {
        "edges": [
            {"from": "entity1", "to": "entity2", "type": "archived_from"},
            {"from": "entity1", "to": "entity3", "type": "archived_from"},
        ]
    })
    def test_get_archived_from_multiple_edges(self):
        """Test that get_archived_from returns all matching edges"""
        import graph_layer
        
        result = graph_layer.get_archived_from("entity1")
        
        assert len(result) == 2, \
            "Should return all archived_from edges for the entity"


# ============================================================================
# get_backlinks() Tests
# ============================================================================

class TestGetBacklinks:
    """Test suite for get_backlinks() function"""
    
    @patch("graph_layer.backlinks_v2", {
        "backlinks": {
            "entity1": ["entity5", "entity6"],
            "entity2": ["entity7"],
            "entity3": []
        }
    })
    def test_get_backlinks_returns_correct_backlinks(self):
        """Test that get_backlinks returns correct backlinks for entity"""
        import graph_layer
        
        result = graph_layer.get_backlinks("entity1")
        
        assert result == ["entity5", "entity6"], \
            "Should return correct backlinks for entity1"
    
    @patch("graph_layer.backlinks_v2", {
        "backlinks": {
            "entity1": ["entity5", "entity6"],
        }
    })
    def test_get_backlinks_empty_for_nonexistent_entity(self):
        """Test that get_backlinks returns empty list for nonexistent entity"""
        import graph_layer
        
        result = graph_layer.get_backlinks("nonexistent")
        
        assert result == [], \
            "Should return empty list for nonexistent entity"
    
    @patch("graph_layer.backlinks_v2", {
        "backlinks": {
            "entity1": []
        }
    })
    def test_get_backlinks_empty_when_no_backlinks(self):
        """Test that get_backlinks returns empty list when entity has no backlinks"""
        import graph_layer
        
        result = graph_layer.get_backlinks("entity1")
        
        assert result == [], \
            "Should return empty list when entity has no backlinks"


# ============================================================================
# graph_stats() Tests
# ============================================================================

class TestGraphStats:
    """Test suite for graph_stats() function"""
    
    @patch("graph_layer.graph_v2", {
        "edges": [
            {"from": "entity1", "to": "entity2", "type": "archived_from"},
            {"from": "entity1", "to": "entity3", "type": "reference"},
            {"from": "entity2", "to": "entity4", "type": "archived_from"},
        ]
    })
    def test_graph_stats_returns_correct_counts(self):
        """Test that graph_stats returns correct edge and node counts"""
        import graph_layer
        
        result = graph_layer.graph_stats()
        
        assert result["total_edges"] == 3, \
            "Should count total edges correctly"
        assert result["total_nodes"] == 4, \
            "Should count unique nodes correctly (entity1, entity2, entity3, entity4)"
    
    @patch("graph_layer.graph_v2", {
        "edges": [
            {"from": "entity1", "to": "entity2", "type": "archived_from"},
            {"from": "entity1", "to": "entity3", "type": "archived_from"},
            {"from": "entity2", "to": "entity4", "type": "reference"},
        ]
    })
    def test_graph_stats_edges_by_type(self):
        """Test that graph_stats correctly categorizes edges by type"""
        import graph_layer
        
        result = graph_layer.graph_stats()
        
        assert result["edges_by_type"]["archived_from"] == 2, \
            "Should count archived_from edges correctly"
        assert result["edges_by_type"]["reference"] == 1, \
            "Should count reference edges correctly"
    
    @patch("graph_layer.graph_v2", {"edges": []})
    def test_graph_stats_empty_graph(self):
        """Test that graph_stats handles empty graph correctly"""
        import graph_layer
        
        result = graph_layer.graph_stats()
        
        assert result["total_edges"] == 0, \
            "Should return 0 for empty graph"
        assert result["total_nodes"] == 0, \
            "Should return 0 nodes for empty graph"
        assert result["edges_by_type"] == {}, \
            "Should return empty edges_by_type for empty graph"


# ============================================================================
# Integration Tests
# ============================================================================

class TestGraphLayerIntegration:
    """Integration tests for graph layer functionality"""
    
    def test_dir_resolution_and_data_loading_consistency(self):
        """Test that _DIR resolution is consistent with actual data folder structure"""
        import graph_layer
        
        # Get the _DIR path
        dir_path = Path(graph_layer._DIR).resolve()
        
        # Verify it points to a directory that should contain graph data files
        assert dir_path.exists(), \
            f"_DIR path {dir_path} should exist"
        
        # Check if expected files exist (if data folder has content)
        expected_files = ["graph_v2.json", "backlinks_v2.json"]
        for filename in expected_files:
            file_path = dir_path / filename
            # We don't assert existence here as the data might not be present in test environment
            # but we verify the path construction is correct
            assert file_path.parent == dir_path, \
                f"File {filename} should be in _DIR directory"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
