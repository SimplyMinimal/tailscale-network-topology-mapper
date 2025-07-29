"""
Test suite for NetworkGraph class.
"""
import pytest
from network_graph import NetworkGraph


class TestNetworkGraph:
    """Test cases for NetworkGraph."""
    
    def test_init(self):
        """Test NetworkGraph initialization."""
        hosts = {"server": "192.168.1.1"}
        groups = {"group:test": ["user@example.com"]}
        
        graph = NetworkGraph(hosts, groups)
        assert graph.hosts == hosts
        assert graph.groups == groups
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0
    
    def test_add_node(self):
        """Test adding nodes to the graph."""
        graph = NetworkGraph({}, {})
        graph.add_node("test_node", "#FF0000", "Test tooltip")
        
        assert len(graph.nodes) == 1
        assert ("test_node", "#FF0000", "Test tooltip", "dot") in graph.nodes
    
    def test_add_edge(self):
        """Test adding edges to the graph."""
        graph = NetworkGraph({}, {})
        graph.add_edge("source", "destination")
        
        assert len(graph.edges) == 1
        assert ("source", "destination") in graph.edges
    
    def test_get_node_color_tag(self):
        """Test node color assignment for tags."""
        graph = NetworkGraph({}, {})
        color = graph._get_node_color("tag:web")
        assert color == "#00cc66"  # Green for tags
    
    def test_get_node_color_group(self):
        """Test node color assignment for groups."""
        graph = NetworkGraph({}, {})
        color = graph._get_node_color("group:admin")
        assert color == "#FFFF00"  # Yellow for groups
    
    def test_get_node_color_autogroup(self):
        """Test node color assignment for autogroups."""
        graph = NetworkGraph({}, {})
        color = graph._get_node_color("autogroup:member")
        assert color == "#FFFF00"  # Yellow for autogroups
    
    def test_get_node_color_host(self):
        """Test node color assignment for hosts."""
        graph = NetworkGraph({}, {})
        color = graph._get_node_color("server")
        assert color == "#ff6666"  # Red for hosts
    
    def test_resolve_nodes(self):
        """Test node resolution."""
        graph = NetworkGraph({}, {})
        nodes = graph._resolve_nodes(["node1", "node2", "node1"])  # Duplicate should be removed
        
        assert len(nodes) == 2
        assert "node1" in nodes
        assert "node2" in nodes
    
    def test_get_node_tooltip_host(self):
        """Test tooltip generation for hosts."""
        hosts = {"server": "192.168.1.1"}
        graph = NetworkGraph(hosts, {})
        
        tooltip = graph._get_node_tooltip("server")
        assert tooltip == "192.168.1.1"
    
    def test_get_node_tooltip_group(self):
        """Test tooltip generation for groups."""
        groups = {"group:admin": ["admin1@example.com", "admin2@example.com"]}
        graph = NetworkGraph({}, groups)
        
        tooltip = graph._get_node_tooltip("group:admin")
        assert "Group Members: admin1@example.com, admin2@example.com" in tooltip
    
    def test_get_node_tooltip_autogroup(self):
        """Test tooltip generation for autogroups."""
        graph = NetworkGraph({}, {})
        tooltip = graph._get_node_tooltip("autogroup:member")
        assert tooltip == "autogroup:member"
    
    def test_resolve_grant_destinations_with_ip_protocols(self):
        """Test grant destination resolution with IP protocols."""
        graph = NetworkGraph({}, {})
        grant = {
            "dst": ["server"],
            "ip": ["tcp:443", "udp:53"]
        }

        destinations = graph._resolve_grant_destinations(grant)
        assert len(destinations) == 1  # Now groups protocols into single destination
        assert "server [tcp:443, udp:53]" in destinations
    
    def test_resolve_grant_destinations_without_ip_protocols(self):
        """Test grant destination resolution without IP protocols."""
        graph = NetworkGraph({}, {})
        grant = {
            "dst": ["server"],
            "ip": ["*"]
        }
        
        destinations = graph._resolve_grant_destinations(grant)
        assert len(destinations) == 1
        assert "server" in destinations
    
    def test_get_grant_src_tooltip_with_posture(self):
        """Test grant source tooltip with posture checks."""
        graph = NetworkGraph({}, {})
        grant = {"srcPosture": ["osVersion:>=10.15"]}
        
        tooltip = graph._get_grant_src_tooltip("group:mobile", grant)
        assert "Posture: osVersion:>=10.15" in tooltip
    
    def test_get_grant_dst_tooltip_with_protocols(self):
        """Test grant destination tooltip with protocols."""
        graph = NetworkGraph({}, {})
        grant = {"ip": ["tcp:443", "tcp:80"]}
        
        tooltip = graph._get_grant_dst_tooltip("server", grant)
        assert "Protocols: tcp:443, tcp:80" in tooltip
    
    def test_get_grant_dst_tooltip_with_via(self):
        """Test grant destination tooltip with via routing."""
        graph = NetworkGraph({}, {})
        grant = {"via": ["gateway"]}
        
        tooltip = graph._get_grant_dst_tooltip("server", grant)
        assert "Via: gateway" in tooltip
    
    def test_get_grant_dst_tooltip_with_app(self):
        """Test grant destination tooltip with app specification."""
        graph = NetworkGraph({}, {})
        grant = {"app": {"example.com/webapp-connector": [{}]}}

        tooltip = graph._get_grant_dst_tooltip("server", grant)
        assert "App: example.com/webapp-connector" in tooltip

    def test_get_grant_dst_tooltip_with_dst_posture(self):
        """Test grant destination tooltip with destination posture checks."""
        graph = NetworkGraph({}, {})
        grant = {"dstPosture": ["osVersion:>=10.15", "deviceTrust:trusted"]}

        tooltip = graph._get_grant_dst_tooltip("server", grant)
        assert "Posture: osVersion:>=10.15, deviceTrust:trusted" in tooltip

    def test_comprehensive_tooltip_with_metadata(self):
        """Test comprehensive tooltip generation with full metadata."""
        graph = NetworkGraph({}, {"group:test": ["user@example.com"]})

        # Simulate building a graph to populate metadata
        acls = [{"action": "accept", "src": ["group:test"], "dst": ["server:22"]}]
        grants = [{"src": ["group:test"], "dst": ["server"], "ip": ["tcp:443"], "via": ["gateway"], "srcPosture": ["trusted"]}]

        graph.build_graph(acls, grants)

        # Get comprehensive tooltip for the mixed node
        tooltip = graph._get_comprehensive_tooltip("group:test")

        # Verify comprehensive information is included
        assert "group:test" in tooltip
        assert "👥 Group Members: user@example.com" in tooltip
        assert "🔄 Mixed (ACL + Grant Rules)" in tooltip
        assert "📋 Rule References:" in tooltip
        assert "Source: ACL rule 1, Grant rule 1" in tooltip
        assert "🌐 Protocols: tcp:443" in tooltip
        assert "🛤️  Via Routes: gateway" in tooltip
        assert "🔐 Posture Checks: trusted" in tooltip

    def test_line_numbers_in_tooltips(self):
        """Test that line numbers are included in rule references when available."""
        # Create mock line numbers
        line_numbers = {'acls': [10, 25], 'grants': [45, 60]}
        graph = NetworkGraph({}, {"group:test": ["user@example.com"]}, line_numbers)

        # Simulate building a graph to populate metadata
        acls = [{"action": "accept", "src": ["group:test"], "dst": ["server:22"]}]
        grants = [{"src": ["group:test"], "dst": ["server"], "ip": ["tcp:443"]}]

        graph.build_graph(acls, grants)

        # Get comprehensive tooltip for the mixed node
        tooltip = graph._get_comprehensive_tooltip("group:test")

        # Verify line numbers are included in rule references
        assert "Source: ACL rule 1 (Ln 10), Grant rule 1 (Ln 45)" in tooltip
    
    def test_build_graph_with_acls(self):
        """Test building graph from ACL rules."""
        hosts = {"server": "192.168.1.1"}
        groups = {"group:admin": ["admin@example.com"]}
        graph = NetworkGraph(hosts, groups)
        
        acls = [
            {"src": ["group:admin"], "dst": ["server"]}
        ]
        
        graph.build_graph(acls)
        
        # Should have 2 nodes (source and destination) and 1 edge
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1
        
        # Check edge exists
        assert ("group:admin", "server") in graph.edges
    
    def test_build_graph_with_grants(self):
        """Test building graph from grant rules."""
        hosts = {"server": "192.168.1.1"}
        groups = {"group:admin": ["admin@example.com"]}
        graph = NetworkGraph(hosts, groups)
        
        grants = [
            {"src": ["group:admin"], "dst": ["server"], "ip": ["tcp:443"]}
        ]
        
        graph.build_graph([], grants)
        
        # Should have 2 nodes and 1 edge
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1
        
        # Check that enhanced destination node exists (grouped protocols)
        assert ("group:admin", "server [tcp:443]") in graph.edges


if __name__ == "__main__":
    pytest.main([__file__])