"""
Test utilities for the Tailscale Network Topology Mapper test suite.

This module provides helper functions and classes to support isolated,
self-contained testing without external dependencies.
"""

import tempfile
import json
import os
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch
from contextlib import contextmanager

from policy_parser import PolicyParser
from network_graph import NetworkGraph
from renderer import Renderer
from tests.fixtures.mock_policy_data import MockPolicyData, MockLineNumbers


class MockPolicyParser:
    """Mock PolicyParser that uses static test data instead of files."""
    
    def __init__(self, policy_data: Optional[Dict[str, Any]] = None, 
                 line_numbers: Optional[Dict[str, Any]] = None):
        """Initialize with mock data."""
        self.policy_data = policy_data or MockPolicyData.get_basic_policy()
        self.rule_line_numbers = line_numbers or MockLineNumbers.get_basic_line_numbers()
        self._parsed = False
    
    def parse_policy(self) -> None:
        """Mock parse_policy that sets data from constructor."""
        self._parsed = True
    
    @property
    def groups(self) -> Dict[str, Any]:
        """Return mock groups data."""
        if not self._parsed:
            raise ValueError("Must call parse_policy() first")
        return self.policy_data.get("groups", {})
    
    @property
    def hosts(self) -> Dict[str, Any]:
        """Return mock hosts data."""
        if not self._parsed:
            raise ValueError("Must call parse_policy() first")
        return self.policy_data.get("hosts", {})
    
    @property
    def tag_owners(self) -> Dict[str, Any]:
        """Return mock tag owners data."""
        if not self._parsed:
            raise ValueError("Must call parse_policy() first")
        return self.policy_data.get("tagOwners", {})
    
    @property
    def acls(self) -> list:
        """Return mock ACLs data."""
        if not self._parsed:
            raise ValueError("Must call parse_policy() first")
        return self.policy_data.get("acls", [])
    
    @property
    def grants(self) -> list:
        """Return mock grants data."""
        if not self._parsed:
            raise ValueError("Must call parse_policy() first")
        return self.policy_data.get("grants", [])


class TestGraphBuilder:
    """Helper class to build test network graphs with mock data."""
    
    @staticmethod
    def create_basic_graph() -> NetworkGraph:
        """Create a basic network graph for testing."""
        policy_data = MockPolicyData.get_basic_policy()
        line_numbers = MockLineNumbers.get_basic_line_numbers()
        
        graph = NetworkGraph(
            hosts=policy_data["hosts"],
            groups=policy_data["groups"],
            rule_line_numbers=line_numbers
        )
        graph.build_graph(policy_data["acls"], policy_data["grants"])
        return graph
    
    @staticmethod
    def create_comprehensive_graph() -> NetworkGraph:
        """Create a comprehensive network graph for testing."""
        policy_data = MockPolicyData.get_comprehensive_policy()
        line_numbers = MockLineNumbers.get_comprehensive_line_numbers()
        
        graph = NetworkGraph(
            hosts=policy_data["hosts"],
            groups=policy_data["groups"],
            rule_line_numbers=line_numbers
        )
        graph.build_graph(policy_data["acls"], policy_data["grants"])
        return graph
    
    @staticmethod
    def create_mixed_nodes_graph() -> NetworkGraph:
        """Create a graph specifically for testing mixed nodes."""
        policy_data = MockPolicyData.get_mixed_nodes_policy()
        line_numbers = MockLineNumbers.get_basic_line_numbers()
        
        graph = NetworkGraph(
            hosts=policy_data["hosts"],
            groups=policy_data["groups"],
            rule_line_numbers=line_numbers
        )
        graph.build_graph(policy_data["acls"], policy_data["grants"])
        return graph
    
    @staticmethod
    def create_search_test_graph() -> NetworkGraph:
        """Create a graph specifically for testing search functionality."""
        policy_data = MockPolicyData.get_search_test_policy()
        line_numbers = MockLineNumbers.get_basic_line_numbers()
        
        graph = NetworkGraph(
            hosts=policy_data["hosts"],
            groups=policy_data["groups"],
            rule_line_numbers=line_numbers
        )
        graph.build_graph(policy_data["acls"], policy_data["grants"])
        return graph


@contextmanager
def temporary_policy_file(policy_data: Dict[str, Any]):
    """Context manager that creates a temporary policy file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(policy_data, f, indent=2)
        temp_path = f.name
    
    try:
        yield temp_path
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@contextmanager
def mock_policy_parser(policy_data: Optional[Dict[str, Any]] = None,
                      line_numbers: Optional[Dict[str, Any]] = None):
    """Context manager that patches PolicyParser with mock data."""
    mock_parser = MockPolicyParser(policy_data, line_numbers)
    
    with patch('policy_parser.PolicyParser', return_value=mock_parser):
        yield mock_parser


class SearchTestHelper:
    """Helper class for testing search functionality."""
    
    @staticmethod
    def simulate_search(search_metadata: Dict[str, Any], search_term: str) -> list:
        """
        Simulate the search logic from the JavaScript functions.
        
        This replicates the client-side search behavior for testing purposes.
        """
        term = search_term.lower().strip()
        matching_nodes = []
        
        for node_id, metadata in search_metadata['nodes'].items():
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


class HTMLTestHelper:
    """Helper class for testing HTML output."""
    
    @staticmethod
    def extract_search_metadata_from_html(html_content: str) -> Optional[Dict[str, Any]]:
        """Extract search metadata from rendered HTML for testing."""
        import re
        
        # Look for the searchMetadata variable in the HTML
        pattern = r'const searchMetadata = ({.*?});'
        match = re.search(pattern, html_content, re.DOTALL)
        
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                return None
        return None
    
    @staticmethod
    def check_html_features(html_content: str) -> Dict[str, bool]:
        """Check if various HTML features are present."""
        return {
            'has_search_input': 'id="enhanced-search-input"' in html_content,
            'has_search_dropdown': 'id="search-dropdown"' in html_content,
            'has_clear_button': 'onclick="clearSearch()"' in html_content,
            'has_legend': 'Legend' in html_content,
            'has_zoom_reset': 'restoreViewState()' in html_content,
            'has_search_metadata': 'const searchMetadata' in html_content,
            'has_drag_functionality': 'initializeDragFunctionality' in html_content
        }
