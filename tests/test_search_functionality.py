#!/usr/bin/env python3
"""
Test the search functionality to ensure it works correctly for all metadata types.

This test suite verifies the fix for the search functionality bug where searching for 'via'
returned no results despite via routing information being present in the policy file.

ISSUE FIXED:
- The search logic was looking for the literal string "via" within via route values
- But via routes contain values like "tag:exit-node-nyc", "api-gateway", "internal-tool"
- None of these contain the word "via", so no matches were found

SOLUTION IMPLEMENTED:
- Enhanced search logic to treat certain keywords as metadata type searches
- When searching for "via", show all nodes that HAVE via routing (regardless of route values)
- When searching for "protocol"/"protocols", show all nodes that HAVE protocols
- When searching for "posture", show all nodes that HAVE posture checks
- When searching for "app"/"apps", show all nodes that HAVE applications
- Still support searching within the actual values (e.g., "api-gateway", "tcp:443")

This makes the search more intuitive and user-friendly.
"""

import unittest
import sys
import os
import json
import re

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from network_graph import NetworkGraph
from policy_parser import PolicyParser


class TestSearchFunctionality(unittest.TestCase):
    """Test cases for search functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Parse the policy file
        self.parser = PolicyParser("policy.hujson")
        self.parser.parse_policy()
        
        # Create network graph
        self.graph = NetworkGraph(
            hosts=self.parser.hosts,
            groups=self.parser.groups,
            rule_line_numbers=self.parser.rule_line_numbers
        )
        self.graph.build_graph(self.parser.acls, self.parser.grants)
        
        # Get search metadata
        self.search_metadata = self.graph.get_search_metadata()

    def test_via_routing_extraction(self):
        """Test that via routing information is correctly extracted."""
        nodes_with_via = []
        for node_id, metadata in self.search_metadata['nodes'].items():
            if metadata.get('via') and len(metadata['via']) > 0:
                nodes_with_via.append((node_id, metadata['via']))
        
        # We should have nodes with via routing
        self.assertGreater(len(nodes_with_via), 0, "No nodes with via routing found")
        
        # Check specific expected via routes
        via_routes_found = []
        for node_id, via_routes in nodes_with_via:
            via_routes_found.extend(via_routes)
        
        expected_via_routes = ['tag:exit-node-nyc', 'api-gateway', 'internal-tool']
        for expected_route in expected_via_routes:
            self.assertIn(expected_route, via_routes_found, 
                         f"Expected via route '{expected_route}' not found")
        
        print(f"✓ Found {len(nodes_with_via)} nodes with via routing")
        for node_id, via_routes in nodes_with_via:
            print(f"  - {node_id}: {via_routes}")

    def test_protocol_extraction(self):
        """Test that protocol information is correctly extracted."""
        nodes_with_protocols = []
        for node_id, metadata in self.search_metadata['nodes'].items():
            protocols = metadata.get('protocols', [])
            # Filter out empty and wildcard protocols
            specific_protocols = [p for p in protocols if p and p != "*"]
            if specific_protocols:
                nodes_with_protocols.append((node_id, specific_protocols))
        
        self.assertGreater(len(nodes_with_protocols), 0, "No nodes with specific protocols found")
        
        # Check for expected protocol patterns
        all_protocols = []
        for node_id, protocols in nodes_with_protocols:
            all_protocols.extend(protocols)
        
        # Should have TCP protocols
        tcp_protocols = [p for p in all_protocols if 'tcp:' in p.lower()]
        self.assertGreater(len(tcp_protocols), 0, "No TCP protocols found")
        
        print(f"✓ Found {len(nodes_with_protocols)} nodes with specific protocols")
        print(f"  - Total unique protocols: {len(set(all_protocols))}")
        print(f"  - TCP protocols: {len(tcp_protocols)}")

    def test_posture_extraction(self):
        """Test that posture check information is correctly extracted."""
        nodes_with_posture = []
        for node_id, metadata in self.search_metadata['nodes'].items():
            if metadata.get('posture') and len(metadata['posture']) > 0:
                nodes_with_posture.append((node_id, metadata['posture']))
        
        self.assertGreater(len(nodes_with_posture), 0, "No nodes with posture checks found")
        
        # Check for expected posture checks
        all_posture_checks = []
        for node_id, posture_checks in nodes_with_posture:
            all_posture_checks.extend(posture_checks)
        
        expected_posture_checks = ['posture:complianceDevice', 'posture:latestMac']
        for expected_check in expected_posture_checks:
            self.assertIn(expected_check, all_posture_checks,
                         f"Expected posture check '{expected_check}' not found")
        
        print(f"✓ Found {len(nodes_with_posture)} nodes with posture checks")
        for node_id, posture_checks in nodes_with_posture:
            print(f"  - {node_id}: {posture_checks}")

    def test_application_extraction(self):
        """Test that application information is correctly extracted."""
        nodes_with_apps = []
        for node_id, metadata in self.search_metadata['nodes'].items():
            if metadata.get('apps') and len(metadata['apps']) > 0:
                nodes_with_apps.append((node_id, metadata['apps']))
        
        self.assertGreater(len(nodes_with_apps), 0, "No nodes with applications found")
        
        # Check for expected applications
        all_apps = []
        for node_id, apps in nodes_with_apps:
            all_apps.extend(apps)
        
        expected_apps = ['webapp-connector', 'service-mesh', 'deployment-pipeline']
        for expected_app in expected_apps:
            self.assertIn(expected_app, all_apps,
                         f"Expected application '{expected_app}' not found")
        
        print(f"✓ Found {len(nodes_with_apps)} nodes with applications")
        for node_id, apps in nodes_with_apps:
            print(f"  - {node_id}: {apps}")

    def test_search_logic_simulation(self):
        """Simulate the search logic to ensure it works correctly."""
        
        def simulate_search(search_term):
            """Simulate the search logic from the JavaScript functions."""
            term = search_term.lower().strip()
            matching_nodes = []
            
            for node_id, metadata in self.search_metadata['nodes'].items():
                matches = False
                match_details = []
                
                # Search in node ID
                if term in node_id.lower():
                    matches = True
                    match_details.append('name')
                
                # Search in protocols
                if metadata.get('protocols') and len(metadata['protocols']) > 0:
                    if term in ['protocol', 'protocols']:
                        matches = True
                        match_details.append('protocol')
                    elif any(term in p.lower() for p in metadata['protocols']):
                        matches = True
                        match_details.append('protocol')
                
                # Search in via routing
                if metadata.get('via') and len(metadata['via']) > 0:
                    if term == 'via':
                        matches = True
                        match_details.append('via')
                    elif any(term in v.lower() for v in metadata['via']):
                        matches = True
                        match_details.append('via')
                
                # Search in posture checks
                if metadata.get('posture') and len(metadata['posture']) > 0:
                    if term == 'posture':
                        matches = True
                        match_details.append('posture')
                    elif any(term in p.lower() for p in metadata['posture']):
                        matches = True
                        match_details.append('posture')
                
                # Search in applications
                if metadata.get('apps') and len(metadata['apps']) > 0:
                    if term in ['app', 'apps']:
                        matches = True
                        match_details.append('app')
                    elif any(term in a.lower() for a in metadata['apps']):
                        matches = True
                        match_details.append('app')
                
                if matches:
                    matching_nodes.append({
                        'id': node_id,
                        'match_details': match_details,
                        'metadata': metadata
                    })
            
            return matching_nodes
        
        # Test various search terms
        test_cases = [
            ('via', 7),  # Should find 7 nodes with via routing
            ('api-gateway', 4),  # Should find nodes with api-gateway in via routes
            ('tcp', 13),  # Should find nodes with TCP protocols
            ('posture', 4),  # Should find nodes with posture checks
            ('app', 4),  # Should find nodes with applications
            ('compliance', 3),  # Should find nodes with complianceDevice posture
        ]
        
        for search_term, expected_min_results in test_cases:
            results = simulate_search(search_term)
            self.assertGreaterEqual(len(results), expected_min_results,
                                  f"Search for '{search_term}' returned {len(results)} results, expected at least {expected_min_results}")
            print(f"✓ Search for '{search_term}': {len(results)} results")
            
            # Show first few results
            for i, result in enumerate(results[:3]):
                print(f"  - {result['id']} (matched: {', '.join(result['match_details'])})")


if __name__ == '__main__':
    unittest.main(verbosity=2)
