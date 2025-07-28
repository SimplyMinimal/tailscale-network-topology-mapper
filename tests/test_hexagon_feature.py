"""
Test cases for the hexagon shape feature in NetworkGraph.

Tests that nodes appearing in both ACL and grant rules are correctly
identified and assigned hexagon shapes with enhanced tooltips.
"""

import pytest
from unittest.mock import Mock
from network_graph import NetworkGraph


class TestHexagonFeature:
    """Test cases for hexagon shape feature."""

    def setup_method(self):
        """Set up test fixtures."""
        self.hosts = {"host1": "100.64.1.1"}
        self.groups = {"group:test": ["user@example.com"]}
        self.network_graph = NetworkGraph(self.hosts, self.groups)

    def test_acl_only_nodes_get_dot_shape(self):
        """Test that nodes appearing only in ACL rules get dot shape."""
        acls = [
            {
                "action": "accept",
                "src": ["tag:acl-only"],
                "dst": ["host1:22"]
            }
        ]
        grants = []

        self.network_graph.build_graph(acls, grants)

        # Find the ACL-only node
        acl_only_nodes = [
            (node_id, shape) for node_id, color, tooltip, shape in self.network_graph.nodes
            if node_id == "tag:acl-only"
        ]

        assert len(acl_only_nodes) == 1
        node_id, shape = acl_only_nodes[0]
        assert shape == "dot"

    def test_grant_only_nodes_get_triangle_shape(self):
        """Test that nodes appearing only in grant rules get triangle shape."""
        acls = []
        grants = [
            {
                "src": ["tag:grant-only"],
                "dst": ["host1"],
                "ip": ["tcp:22"]
            }
        ]

        self.network_graph.build_graph(acls, grants)

        # Find the grant-only node
        grant_only_nodes = [
            (node_id, shape) for node_id, color, tooltip, shape in self.network_graph.nodes
            if node_id == "tag:grant-only"
        ]

        assert len(grant_only_nodes) == 1
        node_id, shape = grant_only_nodes[0]
        assert shape == "triangle"

    def test_mixed_nodes_get_hexagon_shape(self):
        """Test that nodes appearing in both ACL and grant rules get hexagon shape."""
        acls = [
            {
                "action": "accept",
                "src": ["tag:mixed"],
                "dst": ["host1:22"]
            }
        ]
        grants = [
            {
                "src": ["tag:mixed"],
                "dst": ["host1"],
                "ip": ["tcp:443"]
            }
        ]

        self.network_graph.build_graph(acls, grants)

        # Find the mixed node
        mixed_nodes = [
            (node_id, shape, tooltip) for node_id, color, tooltip, shape in self.network_graph.nodes
            if node_id == "tag:mixed"
        ]

        assert len(mixed_nodes) == 1
        node_id, shape, tooltip = mixed_nodes[0]
        assert shape == "hexagon"
        assert "Referenced in both ACL and Grant rules" in tooltip

    def test_multiple_mixed_nodes(self):
        """Test multiple nodes appearing in both ACL and grant rules."""
        acls = [
            {
                "action": "accept",
                "src": ["tag:mixed1", "tag:mixed2"],
                "dst": ["host1:22"]
            }
        ]
        grants = [
            {
                "src": ["tag:mixed1"],
                "dst": ["tag:mixed2"],
                "ip": ["tcp:443"]
            }
        ]

        self.network_graph.build_graph(acls, grants)

        # Find all hexagon nodes
        hexagon_nodes = [
            node_id for node_id, color, tooltip, shape in self.network_graph.nodes
            if shape == "hexagon"
        ]

        # Both mixed nodes should be hexagons
        assert "tag:mixed1" in hexagon_nodes
        assert "tag:mixed2" in hexagon_nodes

    def test_enhanced_tooltip_for_mixed_nodes(self):
        """Test that mixed nodes have enhanced tooltips."""
        acls = [
            {
                "action": "accept",
                "src": ["group:test"],
                "dst": ["host1:22"]
            }
        ]
        grants = [
            {
                "src": ["group:test"],
                "dst": ["host1"],
                "ip": ["tcp:443"]
            }
        ]

        self.network_graph.build_graph(acls, grants)

        # Find the mixed group node
        mixed_group_nodes = [
            (node_id, tooltip) for node_id, color, tooltip, shape in self.network_graph.nodes
            if node_id == "group:test" and shape == "hexagon"
        ]

        assert len(mixed_group_nodes) == 1
        node_id, tooltip = mixed_group_nodes[0]
        assert "Referenced in both ACL and Grant rules" in tooltip

    def test_no_mixed_nodes_when_separate_rules(self):
        """Test that no hexagon shapes are created when ACL and grant rules don't overlap."""
        acls = [
            {
                "action": "accept",
                "src": ["tag:acl-only"],
                "dst": ["host1:22"]
            }
        ]
        grants = [
            {
                "src": ["tag:grant-only"],
                "dst": ["host1"],
                "ip": ["tcp:443"]
            }
        ]

        self.network_graph.build_graph(acls, grants)

        # Find all hexagon nodes
        hexagon_nodes = [
            node_id for node_id, color, tooltip, shape in self.network_graph.nodes
            if shape == "hexagon"
        ]

        assert len(hexagon_nodes) == 0

    def test_empty_rules_no_hexagons(self):
        """Test that empty rule sets don't create hexagon nodes."""
        self.network_graph.build_graph([], [])

        # Find all hexagon nodes
        hexagon_nodes = [
            node_id for node_id, color, tooltip, shape in self.network_graph.nodes
            if shape == "hexagon"
        ]

        assert len(hexagon_nodes) == 0
