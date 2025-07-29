"""
Comprehensive test suite for Renderer class with enhanced functionality testing.

This test suite covers all renderer functionality including HTML generation,
search integration, legend creation, and interactive features using mock data
to ensure test isolation and reliability.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch

from renderer import Renderer
from tests.test_utils import TestGraphBuilder, HTMLTestHelper


class TestRendererComprehensive:
    """Comprehensive test cases for Renderer with mock data."""
    
    def test_render_basic_graph(self):
        """Test rendering a basic graph to HTML."""
        graph = TestGraphBuilder.create_basic_graph()
        renderer = Renderer(graph)
        
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            renderer.render_to_html(temp_path)
            
            # Verify file was created
            assert os.path.exists(temp_path)
            
            # Read and verify content
            with open(temp_path, 'r') as f:
                content = f.read()
            
            # Check for basic HTML structure
            assert '<html>' in content
            assert '</html>' in content
            assert 'network' in content.lower()
            
            # Check for nodes from mock data
            assert 'group:admin' in content
            assert 'group:dev' in content
            assert 'server1' in content
            assert 'database' in content
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_render_comprehensive_graph(self):
        """Test rendering a comprehensive graph with all features."""
        graph = TestGraphBuilder.create_comprehensive_graph()
        renderer = Renderer(graph)
        
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            renderer.render_to_html(temp_path)
            
            # Verify file was created
            assert os.path.exists(temp_path)
            
            # Read and verify content
            with open(temp_path, 'r') as f:
                content = f.read()
            
            # Check for comprehensive features
            features = HTMLTestHelper.check_html_features(content)

            # Check for search elements with correct IDs
            assert 'id="enhanced-search-input"' in content, "Should have search input"
            assert 'id="search-dropdown"' in content, "Should have search dropdown"
            assert 'onclick="clearSearch()"' in content, "Should have clear button"
            assert features['has_legend'], "Should have legend"
            assert features['has_zoom_reset'], "Should have zoom reset functionality"
            assert features['has_search_metadata'], "Should have search metadata"
            assert 'initializeDragFunctionality' in content, "Should have drag functionality"
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_search_metadata_integration(self):
        """Test that search metadata is properly integrated into HTML."""
        graph = TestGraphBuilder.create_search_test_graph()
        renderer = Renderer(graph)
        
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            renderer.render_to_html(temp_path)
            
            # Read content
            with open(temp_path, 'r') as f:
                content = f.read()
            
            # Extract search metadata
            search_metadata = HTMLTestHelper.extract_search_metadata_from_html(content)
            assert search_metadata is not None, "Should have search metadata"
            
            # Verify metadata structure
            assert 'nodes' in search_metadata
            assert 'edges' in search_metadata
            
            # Check for expected nodes from search test data
            nodes = search_metadata['nodes']
            assert 'group:search-test' in nodes
            assert 'group:protocol-test' in nodes
            assert 'group:via-test' in nodes
            assert 'group:posture-test' in nodes
            assert 'group:app-test' in nodes
            
            # Verify node metadata structure
            for node_id, metadata in nodes.items():
                assert 'node_id' in metadata
                assert 'rule_type' in metadata
                assert 'protocols' in metadata
                assert 'via' in metadata
                assert 'posture' in metadata
                assert 'apps' in metadata
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_mixed_nodes_rendering(self):
        """Test rendering of mixed nodes (hexagon shapes)."""
        graph = TestGraphBuilder.create_mixed_nodes_graph()
        renderer = Renderer(graph)
        
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            renderer.render_to_html(temp_path)
            
            # Read content
            with open(temp_path, 'r') as f:
                content = f.read()
            
            # Extract search metadata to check node types
            search_metadata = HTMLTestHelper.extract_search_metadata_from_html(content)
            assert search_metadata is not None
            
            # Check for mixed nodes
            mixed_nodes = [
                node_id for node_id, metadata in search_metadata['nodes'].items()
                if metadata.get('rule_type') == 'Mixed'
            ]
            
            assert len(mixed_nodes) > 0, "Should have mixed nodes"
            
            # Verify mixed nodes are in content
            for node_id in mixed_nodes:
                assert node_id in content
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_legend_content(self):
        """Test that legend contains all expected elements."""
        graph = TestGraphBuilder.create_comprehensive_graph()
        renderer = Renderer(graph)
        
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            renderer.render_to_html(temp_path)
            
            # Read content
            with open(temp_path, 'r') as f:
                content = f.read()
            
            # Check for legend elements
            assert 'Legend' in content
            assert 'Groups' in content
            assert 'Tags' in content
            assert 'Hosts' in content
            assert 'ACL rules only' in content
            assert 'Grant rules only' in content
            assert 'Both ACL and Grant rules' in content
            
            # Check for color indicators
            assert '#FFFF00' in content  # Yellow for groups
            assert '#00cc66' in content  # Green for tags
            assert '#ff6666' in content  # Red for hosts
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_interactive_features(self):
        """Test that interactive features are properly included."""
        graph = TestGraphBuilder.create_comprehensive_graph()
        renderer = Renderer(graph)
        
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            renderer.render_to_html(temp_path)
            
            # Read content
            with open(temp_path, 'r') as f:
                content = f.read()
            
            # Check for interactive JavaScript functions
            interactive_functions = [
                'handleSearchInput',
                'clearSearch',
                'restoreViewState',
                'saveCurrentViewState',
                'updateSearchDropdown',
                'initializeDragFunctionality',
                'performEnhancedSearch'
            ]

            for func in interactive_functions:
                assert func in content, f"Should have {func} function"
            
            # Check for event handlers
            assert 'oninput=' in content
            assert 'onclick=' in content
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_empty_graph_rendering(self):
        """Test rendering an empty graph."""
        from network_graph import NetworkGraph
        
        # Create empty graph
        graph = NetworkGraph({}, {})
        graph.build_graph([], [])
        
        renderer = Renderer(graph)
        
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            renderer.render_to_html(temp_path)
            
            # Verify file was created
            assert os.path.exists(temp_path)
            
            # Read and verify content
            with open(temp_path, 'r') as f:
                content = f.read()
            
            # Should still have basic structure
            assert '<html>' in content
            assert 'Legend' in content
            assert 'searchMetadata' in content
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @patch('renderer.Network')
    def test_network_configuration_parameters(self, mock_network):
        """Test that Network is configured with correct parameters."""
        graph = TestGraphBuilder.create_basic_graph()
        renderer = Renderer(graph)
        
        # Check that Network was called with correct configuration
        mock_network.assert_called_once()
        call_kwargs = mock_network.call_args[1]
        
        # Verify configuration parameters
        assert call_kwargs['height'] == "800px"
        assert call_kwargs['width'] == "100%"
        assert call_kwargs['directed'] is True
        assert call_kwargs['filter_menu'] is False
        assert call_kwargs['select_menu'] is True
        assert call_kwargs['neighborhood_highlight'] is True


if __name__ == "__main__":
    pytest.main([__file__])
