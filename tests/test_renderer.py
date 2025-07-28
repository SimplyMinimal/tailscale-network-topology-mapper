"""
Test suite for Renderer class.
"""
import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from renderer import Renderer
from network_graph import NetworkGraph


class TestRenderer:
    """Test cases for Renderer."""
    
    def test_init(self):
        """Test Renderer initialization."""
        # Create a mock network graph
        mock_graph = Mock(spec=NetworkGraph)
        mock_graph.nodes = set()
        mock_graph.edges = []
        
        renderer = Renderer(mock_graph)
        assert renderer.network_graph == mock_graph
        assert renderer.output_file == ""
        assert renderer.net is not None
    
    def test_render_to_html_creates_file(self):
        """Test that render_to_html creates an HTML file."""
        # Create a mock network graph with some data
        mock_graph = Mock(spec=NetworkGraph)
        mock_graph.nodes = {
            ("node1", "#FF0000", "Test tooltip 1", "dot"),
            ("node2", "#00FF00", "Test tooltip 2", "triangle")
        }
        mock_graph.edges = [("node1", "node2")]
        mock_graph.get_search_metadata.return_value = {
            "nodes": {
                "node1": {"node_id": "node1", "rule_type": "ACL", "protocols": [], "via": [], "posture": [], "apps": []},
                "node2": {"node_id": "node2", "rule_type": "Grant", "protocols": ["tcp:443"], "via": [], "posture": [], "apps": []}
            },
            "edges": {
                "node1->node2": {"src": "node1", "dst": "node2", "rule_type": "ACL", "protocols": [], "via": [], "posture": [], "apps": []}
            }
        }
        
        renderer = Renderer(mock_graph)
        
        # Use temporary file
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            renderer.render_to_html(temp_path)
            
            # Check that file was created and has content
            assert os.path.exists(temp_path)
            with open(temp_path, 'r') as f:
                content = f.read()
                assert len(content) > 0
                assert "node1" in content
                assert "node2" in content
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_add_legend_appends_to_file(self):
        """Test that _add_legend properly appends legend to HTML file."""
        mock_graph = Mock(spec=NetworkGraph)
        mock_graph.nodes = set()
        mock_graph.edges = []
        mock_graph.get_search_metadata.return_value = {"nodes": {}, "edges": {}}
        
        renderer = Renderer(mock_graph)
        
        # Create a temporary file with initial content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as temp_file:
            temp_file.write("<html><body>Initial content</body></html>")
            temp_path = temp_file.name
        
        try:
            renderer.output_file = temp_path
            renderer._add_legend()
            
            # Check that legend was appended
            with open(temp_path, 'r') as f:
                content = f.read()
                assert "Initial content" in content
                assert "Legend" in content
                assert "Group" in content
                assert "Tag" in content
                assert "Host" in content
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @patch('renderer.Network')
    def test_network_configuration(self, mock_network):
        """Test that Network is configured with correct parameters."""
        mock_graph = Mock(spec=NetworkGraph)
        mock_graph.nodes = set()
        mock_graph.edges = []
        
        renderer = Renderer(mock_graph)
        
        # Check that Network was called with correct configuration
        mock_network.assert_called_once()
        call_kwargs = mock_network.call_args[1]
        
        assert call_kwargs['height'] == "800px"
        assert call_kwargs['width'] == "100%"
        assert call_kwargs['directed'] is True
        assert call_kwargs['filter_menu'] is False  # Updated: now disabled in favor of enhanced search
        assert call_kwargs['select_menu'] is True
        assert call_kwargs['neighborhood_highlight'] is True
    
    def test_output_file_tracking(self):
        """Test that output file is properly tracked for legend."""
        mock_graph = Mock(spec=NetworkGraph)
        mock_graph.nodes = set()
        mock_graph.edges = []
        mock_graph.get_search_metadata.return_value = {"nodes": {}, "edges": {}}
        
        renderer = Renderer(mock_graph)
        
        # Initially empty
        assert renderer.output_file == ""
        
        # Mock the Network.write_html method to avoid actual file operations
        with patch.object(renderer.net, 'write_html'):
            with patch.object(renderer, '_add_enhanced_search'):
                with patch.object(renderer, '_add_legend'):
                    renderer.render_to_html("test_output.html")

                    # Should be set after render_to_html call
                    assert renderer.output_file == "test_output.html"


if __name__ == "__main__":
    pytest.main([__file__])