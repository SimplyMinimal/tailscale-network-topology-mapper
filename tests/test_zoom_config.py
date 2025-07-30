"""
Test suite for zoom configuration in Renderer class.

This test suite verifies that zoom configuration is properly applied
in the renderer, including default and modified settings.
"""
import pytest
import os
import tempfile
from unittest.mock import patch

from ..network_graph import NetworkGraph
from ..renderer import Renderer
from ..config import NETWORK_OPTIONS

class TestZoomConfig:
    """Test cases for zoom configuration in Renderer."""

    def test_zoom_configuration_defaults(self):
        """Test that default zoom configuration is properly applied."""
        # Create a simple network graph for testing
        test_graph = NetworkGraph(
            hosts={"test_host": "192.168.1.1"},
            groups={"test_group": ["user1@example.com", "user2@example.com"]}
        )
        test_graph.add_node("test_node", color="#00ff00", tooltip_text="Test Node")
        test_graph.add_edge("test_node", "test_node")  # Self-edge for testing

        renderer = Renderer(test_graph)

        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tmp_file:
            output_path = tmp_file.name

        try:
            renderer.render_to_html(output_path)

            # Read the generated HTML file
            with open(output_path, 'r') as f:
                content = f.read()

            # Check if zoom configuration is present
            assert '"zoomSpeed": 0.5' in content, "Default zoom speed should be 0.5"
            assert '"zoomView": true' in content, "Default zoom view should be enabled"

        finally:
            # Clean up temporary files
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_zoom_configuration_modified(self):
        """Test that modified zoom configuration is properly applied."""
        # Create a simple network graph for testing
        test_graph = NetworkGraph(
            hosts={"test_host": "192.168.1.1"},
            groups={"test_group": ["user1@example.com", "user2@example.com"]}
        )
        test_graph.add_node("test_node", color="#00ff00", tooltip_text="Test Node")
        test_graph.add_edge("test_node", "test_node")  # Self-edge for testing

        renderer = Renderer(test_graph)

        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tmp_file:
            output_path = tmp_file.name

        try:
            # Save original settings
            original_zoom = NETWORK_OPTIONS.get("zoom", {}).copy()

            # Modify zoom settings
            NETWORK_OPTIONS["zoom"] = {
                "speed": 0.2,      # Slower zoom
                "enabled": False   # Disable zoom
            }

            try:
                renderer.render_to_html(output_path)

                # Read the generated HTML file
                with open(output_path, 'r') as f:
                    content = f.read()

                # Check if modified zoom configuration is present
                assert '"zoomSpeed": 0.2' in content, "Modified zoom speed should be 0.2"
                assert '"zoomView": false' in content, "Modified zoom view should be disabled"

            finally:
                # Restore original settings
                NETWORK_OPTIONS["zoom"] = original_zoom

        finally:
            # Clean up temporary files
            if os.path.exists(output_path):
                os.unlink(output_path)

if __name__ == "__main__":
    pytest.main([__file__])