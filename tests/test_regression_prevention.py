"""
Regression prevention test suite for the Tailscale Network Topology Mapper.

This test suite is designed to catch regressions in critical functionality
that users depend on, including search features, tooltip generation,
visualization rendering, and interactive elements.
"""

import pytest
import tempfile
import os
import json
from unittest.mock import patch

from tests.test_utils import TestGraphBuilder, SearchTestHelper, HTMLTestHelper
from tests.fixtures.mock_policy_data import MockPolicyData
from renderer import Renderer


class TestRegressionPrevention:
    """Regression prevention tests for critical user-facing functionality."""
    
    def test_search_functionality_regression(self):
        """
        Regression test for search functionality.
        
        This test ensures that the search bug fix (where 'via' searches returned
        no results) doesn't regress and that all search types continue to work.
        """
        graph = TestGraphBuilder.create_comprehensive_graph()
        search_metadata = graph.get_search_metadata()
        
        # Test the specific bug that was fixed: searching for 'via'
        via_results = SearchTestHelper.simulate_search(search_metadata, 'via')
        assert len(via_results) > 0, "REGRESSION: 'via' search should return results"
        
        # Test other metadata type searches
        protocol_results = SearchTestHelper.simulate_search(search_metadata, 'protocol')
        assert len(protocol_results) > 0, "REGRESSION: 'protocol' search should return results"
        
        posture_results = SearchTestHelper.simulate_search(search_metadata, 'posture')
        assert len(posture_results) > 0, "REGRESSION: 'posture' search should return results"
        
        app_results = SearchTestHelper.simulate_search(search_metadata, 'app')
        assert len(app_results) > 0, "REGRESSION: 'app' search should return results"
        
        # Test value-based searches
        tcp_results = SearchTestHelper.simulate_search(search_metadata, 'tcp')
        assert len(tcp_results) > 0, "REGRESSION: 'tcp' value search should return results"
        
        gateway_results = SearchTestHelper.simulate_search(search_metadata, 'gateway')
        assert len(gateway_results) > 0, "REGRESSION: 'gateway' value search should return results"
    
    def test_tooltip_content_regression(self):
        """
        Regression test for tooltip content generation.
        
        Ensures that tooltips contain all expected metadata and formatting.
        """
        graph = TestGraphBuilder.create_comprehensive_graph()
        
        # Check that nodes have comprehensive tooltips
        tooltip_found = False
        for node, color, tooltip_text, shape in graph.nodes:
            if 'group:admin' in node:
                tooltip_found = True

                # Check for essential tooltip elements (using actual format from code)
                # The comprehensive tooltip uses different text patterns
                assert ('🔒 Legacy ACL Rules' in tooltip_text or
                       '🎯 Modern Grant Rules' in tooltip_text or
                       '🔄 Mixed (ACL + Grant Rules)' in tooltip_text), "REGRESSION: Tooltip missing rule type"

                # Check for emoji formatting (using actual emojis from code)
                has_metadata = ('🌐 Protocols:' in tooltip_text or
                              '🛤️  Via Routes:' in tooltip_text or
                              '🔐 Posture Checks:' in tooltip_text or
                              '📱 Applications:' in tooltip_text or
                              '👥 Group Members:' in tooltip_text)

                assert has_metadata, "REGRESSION: Tooltip missing metadata sections"
                break

        assert tooltip_found, "REGRESSION: Could not find expected node for tooltip testing"
    
    def test_mixed_nodes_hexagon_regression(self):
        """
        Regression test for mixed nodes (hexagon shapes).
        
        Ensures that nodes appearing in both ACL and Grant rules get hexagon shapes.
        """
        graph = TestGraphBuilder.create_mixed_nodes_graph()
        
        # Check for hexagon shapes
        hexagon_found = False
        for node, color, tooltip_text, shape in graph.nodes:
            if shape == 'hexagon':
                hexagon_found = True
                assert 'Mixed' in tooltip_text, "REGRESSION: Hexagon node should have 'Mixed' in tooltip"
                break
        
        assert hexagon_found, "REGRESSION: No hexagon shapes found for mixed nodes"
    
    def test_html_rendering_regression(self):
        """
        Regression test for HTML rendering functionality.
        
        Ensures that all critical HTML elements are present in rendered output.
        """
        graph = TestGraphBuilder.create_comprehensive_graph()
        renderer = Renderer(graph)
        
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            renderer.render_to_html(temp_path)
            
            with open(temp_path, 'r') as f:
                content = f.read()
            
            # Critical HTML elements that must be present
            critical_elements = [
                '<html>',
                '</html>',
                'id="enhanced-search-input"',
                'id="search-dropdown"',
                'const searchMetadata',
                'Legend',
                'restoreViewState',
                'initializeDragFunctionality'
            ]
            
            for element in critical_elements:
                assert element in content, f"REGRESSION: Missing critical HTML element: {element}"
            
            # Check that search metadata is valid JSON
            search_metadata = HTMLTestHelper.extract_search_metadata_from_html(content)
            assert search_metadata is not None, "REGRESSION: Search metadata is not valid JSON"
            assert 'nodes' in search_metadata, "REGRESSION: Search metadata missing nodes"
            assert 'edges' in search_metadata, "REGRESSION: Search metadata missing edges"
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_legend_functionality_regression(self):
        """
        Regression test for legend functionality.
        
        Ensures that the legend contains all expected elements and colors.
        """
        graph = TestGraphBuilder.create_comprehensive_graph()
        renderer = Renderer(graph)
        
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            renderer.render_to_html(temp_path)
            
            with open(temp_path, 'r') as f:
                content = f.read()
            
            # Legend elements that must be present
            legend_elements = [
                'Groups',
                'Tags', 
                'Hosts',
                'ACL rules only',
                'Grant rules only',
                'Both ACL and Grant rules',
                '#FFFF00',  # Yellow for groups
                '#00cc66',  # Green for tags
                '#ff6666',  # Red for hosts
                '●',        # Circle for ACL
                '▲',        # Triangle for Grant
                '⬢'         # Hexagon for Mixed
            ]
            
            for element in legend_elements:
                assert element in content, f"REGRESSION: Missing legend element: {element}"
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_drag_functionality_regression(self):
        """
        Regression test for drag functionality.
        
        Ensures that drag-related JavaScript functions are present.
        """
        graph = TestGraphBuilder.create_basic_graph()
        renderer = Renderer(graph)
        
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            renderer.render_to_html(temp_path)
            
            with open(temp_path, 'r') as f:
                content = f.read()
            
            # Drag functionality elements
            drag_elements = [
                'initializeDragFunctionality',
                'isDragging',
                'dragOffset',
                'mousedown',
                'mousemove',
                'mouseup',
                'drag-handle'
            ]
            
            for element in drag_elements:
                assert element in content, f"REGRESSION: Missing drag functionality: {element}"
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_policy_parsing_edge_cases_regression(self):
        """
        Regression test for policy parsing edge cases.
        
        Ensures that edge cases in policy files don't break parsing.
        """
        from policy_parser import PolicyParser
        from tests.test_utils import temporary_policy_file
        
        # Test empty policy
        empty_policy = {
            "groups": {},
            "hosts": {},
            "tagOwners": {},
            "acls": [],
            "grants": []
        }
        
        with temporary_policy_file(empty_policy) as temp_path:
            parser = PolicyParser(temp_path)
            parser.parse_policy()  # Should not raise an exception
            
            assert parser.groups == {}
            assert parser.hosts == {}
            assert parser.acls == []
            assert parser.grants == []
        
        # Test policy with edge cases
        edge_case_policy = MockPolicyData.get_edge_cases_policy()
        
        with temporary_policy_file(edge_case_policy) as temp_path:
            parser = PolicyParser(temp_path)
            parser.parse_policy()  # Should not raise an exception
            
            # Should handle special characters
            assert "group:special-chars" in parser.groups
            assert "user+test@company.com" in parser.groups["group:special-chars"]
    
    def test_network_graph_building_regression(self):
        """
        Regression test for network graph building.
        
        Ensures that graph building handles various policy configurations correctly.
        """
        # Test with comprehensive policy
        graph = TestGraphBuilder.create_comprehensive_graph()
        
        # Should have nodes and edges
        assert len(graph.nodes) > 0, "REGRESSION: No nodes created from comprehensive policy"
        assert len(graph.edges) > 0, "REGRESSION: No edges created from comprehensive policy"
        
        # Should have different node types (using actual tooltip format)
        node_types = set()
        for node, color, tooltip_text, shape in graph.nodes:
            # Check for actual rule type indicators in tooltips
            if '🔒 Legacy ACL Rules' in tooltip_text:
                node_types.add('ACL')
            elif '🎯 Modern Grant Rules' in tooltip_text:
                node_types.add('Grant')
            elif '🔄 Mixed (ACL + Grant Rules)' in tooltip_text:
                node_types.add('Mixed')

        # Should have at least one node type (comprehensive policy should have grants)
        assert len(node_types) >= 1, f"REGRESSION: Should have node types, found: {node_types}"
    
    def test_search_metadata_generation_regression(self):
        """
        Regression test for search metadata generation.
        
        Ensures that search metadata contains all expected fields and structure.
        """
        graph = TestGraphBuilder.create_search_test_graph()
        search_metadata = graph.get_search_metadata()
        
        # Check metadata structure
        assert 'nodes' in search_metadata, "REGRESSION: Search metadata missing nodes"
        assert 'edges' in search_metadata, "REGRESSION: Search metadata missing edges"
        
        # Check node metadata structure
        for node_id, metadata in search_metadata['nodes'].items():
            required_fields = ['node_id', 'rule_type', 'protocols', 'via', 'posture', 'apps']
            for field in required_fields:
                assert field in metadata, f"REGRESSION: Node metadata missing field: {field}"
            
            # Check that lists are actually lists
            list_fields = ['protocols', 'via', 'posture', 'apps']
            for field in list_fields:
                assert isinstance(metadata[field], list), f"REGRESSION: {field} should be a list"


if __name__ == "__main__":
    pytest.main([__file__])
