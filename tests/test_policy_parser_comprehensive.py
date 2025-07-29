"""
Comprehensive test suite for PolicyParser with mock data and edge cases.

This test suite ensures the PolicyParser works correctly with various
policy configurations without relying on external files.
"""

import pytest
import tempfile
import json
from unittest.mock import patch, MagicMock

from policy_parser import PolicyParser
from tests.test_utils import MockPolicyParser, temporary_policy_file
from tests.fixtures.mock_policy_data import MockPolicyData


class TestPolicyParserComprehensive:
    """Comprehensive test cases for PolicyParser with mock data."""
    
    def test_parse_basic_policy(self):
        """Test parsing a basic policy configuration."""
        policy_data = MockPolicyData.get_basic_policy()
        
        with temporary_policy_file(policy_data) as temp_path:
            parser = PolicyParser(temp_path)
            parser.parse_policy()
            
            # Verify parsed data
            assert parser.groups == policy_data["groups"]
            assert parser.hosts == policy_data["hosts"]
            assert parser.tag_owners == policy_data["tagOwners"]
            assert parser.acls == policy_data["acls"]
            assert parser.grants == policy_data["grants"]
    
    def test_parse_comprehensive_policy(self):
        """Test parsing a comprehensive policy with all features."""
        policy_data = MockPolicyData.get_comprehensive_policy()
        
        with temporary_policy_file(policy_data) as temp_path:
            parser = PolicyParser(temp_path)
            parser.parse_policy()
            
            # Verify comprehensive data
            assert len(parser.groups) == 7
            assert len(parser.hosts) == 8
            assert len(parser.tag_owners) == 8
            assert len(parser.acls) == 4
            assert len(parser.grants) == 7
            
            # Check specific groups
            assert "group:admin" in parser.groups
            assert "group:dev" in parser.groups
            assert "group:mobile" in parser.groups
            
            # Check specific hosts
            assert "api-gateway" in parser.hosts
            assert "database" in parser.hosts
            assert "exit-node-nyc" in parser.hosts
            
            # Check ACL structure
            for acl in parser.acls:
                assert "action" in acl
                assert "src" in acl
                assert "dst" in acl
            
            # Check grant structure
            for grant in parser.grants:
                assert "src" in grant
                assert "dst" in grant
                assert "ip" in grant
    
    def test_parse_edge_cases_policy(self):
        """Test parsing policy with edge cases."""
        policy_data = MockPolicyData.get_edge_cases_policy()
        
        with temporary_policy_file(policy_data) as temp_path:
            parser = PolicyParser(temp_path)
            parser.parse_policy()
            
            # Verify edge cases are handled
            assert "group:empty" in parser.groups
            assert len(parser.groups["group:empty"]) == 0
            
            assert "group:special-chars" in parser.groups
            assert "user+test@company.com" in parser.groups["group:special-chars"]
            
            assert "localhost" in parser.hosts
            assert parser.hosts["localhost"] == "127.0.0.1"
    
    def test_mock_policy_parser(self):
        """Test the MockPolicyParser utility."""
        policy_data = MockPolicyData.get_basic_policy()
        mock_parser = MockPolicyParser(policy_data)
        
        # Should require parse_policy() call first
        with pytest.raises(ValueError, match="Must call parse_policy"):
            _ = mock_parser.groups
        
        # After parsing, should return mock data
        mock_parser.parse_policy()
        assert mock_parser.groups == policy_data["groups"]
        assert mock_parser.hosts == policy_data["hosts"]
        assert mock_parser.acls == policy_data["acls"]
        assert mock_parser.grants == policy_data["grants"]
    
    def test_policy_validation_errors(self):
        """Test that policy validation catches errors."""
        # Test invalid grant structure
        invalid_policy = {
            "groups": {},
            "hosts": {},
            "tagOwners": {},
            "acls": [],
            "grants": [
                {"dst": ["target"]}  # Missing src field
            ]
        }
        
        with temporary_policy_file(invalid_policy) as temp_path:
            parser = PolicyParser(temp_path)
            
            with pytest.raises(ValueError, match="Grant 1 missing required 'src' field"):
                parser.parse_policy()
    
    def test_file_loading_errors(self):
        """Test handling of file loading errors."""
        parser = PolicyParser("/nonexistent/file.json")
        
        with pytest.raises(ValueError, match="Error loading policy file"):
            parser.parse_policy()
    
    def test_line_number_extraction(self):
        """Test that line numbers are properly extracted."""
        policy_data = MockPolicyData.get_basic_policy()
        
        with temporary_policy_file(policy_data) as temp_path:
            parser = PolicyParser(temp_path)
            
            # Mock the line number extraction
            with patch.object(parser._file_loader, 'extract_rule_line_numbers') as mock_extract:
                mock_extract.return_value = {"acls": [10, 15], "grants": [25, 30]}
                
                parser.parse_policy()
                
                # Verify line numbers were extracted
                assert parser.rule_line_numbers == {"acls": [10, 15], "grants": [25, 30]}
                mock_extract.assert_called_once_with(temp_path)
    
    def test_policy_statistics(self):
        """Test policy statistics generation."""
        policy_data = MockPolicyData.get_comprehensive_policy()
        
        with temporary_policy_file(policy_data) as temp_path:
            parser = PolicyParser(temp_path)
            parser.parse_policy()
            
            # Check that we can access policy data statistics
            # This tests the integration with PolicyData
            assert len(parser.groups) > 0
            assert len(parser.hosts) > 0
            assert len(parser.acls) > 0
            assert len(parser.grants) > 0
    
    def test_empty_policy_sections(self):
        """Test handling of empty policy sections."""
        empty_policy = {
            "groups": {},
            "hosts": {},
            "tagOwners": {},
            "acls": [],
            "grants": []
        }
        
        with temporary_policy_file(empty_policy) as temp_path:
            parser = PolicyParser(temp_path)
            parser.parse_policy()
            
            # Should handle empty sections gracefully
            assert parser.groups == {}
            assert parser.hosts == {}
            assert parser.tag_owners == {}
            assert parser.acls == []
            assert parser.grants == []
    
    def test_policy_with_complex_grants(self):
        """Test parsing policy with complex grant configurations."""
        policy_data = MockPolicyData.get_comprehensive_policy()
        
        with temporary_policy_file(policy_data) as temp_path:
            parser = PolicyParser(temp_path)
            parser.parse_policy()
            
            # Find grants with various features
            grants_with_via = [g for g in parser.grants if "via" in g]
            grants_with_posture = [g for g in parser.grants if "srcPosture" in g or "dstPosture" in g]
            grants_with_apps = [g for g in parser.grants if "app" in g]
            
            assert len(grants_with_via) > 0, "Should have grants with via routing"
            assert len(grants_with_posture) > 0, "Should have grants with posture checks"
            assert len(grants_with_apps) > 0, "Should have grants with applications"
            
            # Verify specific grant features
            for grant in grants_with_via:
                assert isinstance(grant["via"], list)
                assert len(grant["via"]) > 0
            
            for grant in grants_with_posture:
                if "srcPosture" in grant:
                    assert isinstance(grant["srcPosture"], list)
                if "dstPosture" in grant:
                    assert isinstance(grant["dstPosture"], list)
            
            for grant in grants_with_apps:
                assert isinstance(grant["app"], dict)
                assert len(grant["app"]) > 0
    
    def test_policy_with_mixed_protocols(self):
        """Test parsing policy with various protocol specifications."""
        policy_data = MockPolicyData.get_comprehensive_policy()
        
        with temporary_policy_file(policy_data) as temp_path:
            parser = PolicyParser(temp_path)
            parser.parse_policy()
            
            # Check for various protocol types in grants
            all_protocols = []
            for grant in parser.grants:
                if "ip" in grant:
                    all_protocols.extend(grant["ip"])
            
            # Should have TCP protocols
            tcp_protocols = [p for p in all_protocols if "tcp:" in p]
            assert len(tcp_protocols) > 0, "Should have TCP protocols"
            
            # Should have UDP protocols
            udp_protocols = [p for p in all_protocols if "udp:" in p]
            assert len(udp_protocols) > 0, "Should have UDP protocols"
            
            # Should have wildcard protocols
            wildcard_protocols = [p for p in all_protocols if p == "*"]
            assert len(wildcard_protocols) > 0, "Should have wildcard protocols"


if __name__ == "__main__":
    pytest.main([__file__])
