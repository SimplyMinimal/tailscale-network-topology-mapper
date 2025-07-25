"""
Test suite for PolicyParser class.
"""
import pytest
import tempfile
import json
from unittest.mock import patch
from policy_parser import PolicyParser


class TestPolicyParser:
    """Test cases for PolicyParser."""
    
    def test_init(self):
        """Test PolicyParser initialization."""
        parser = PolicyParser("/test/path")
        assert parser.policy_file == "/test/path"
        assert parser.groups == {}
        assert parser.hosts == {}
        assert parser.tag_owners == {}
        assert parser.acls == []
        assert parser.grants == []
    
    def test_load_json_valid(self):
        """Test loading valid JSON file."""
        test_data = {"groups": {"group:test": ["user@example.com"]}}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name
        
        parser = PolicyParser()
        result = parser.load_json_or_hujson(temp_path)
        assert result == test_data
    
    def test_load_json_file_not_found(self):
        """Test handling of missing file."""
        parser = PolicyParser()
        with pytest.raises(ValueError, match="Policy file not found"):
            parser.load_json_or_hujson("/nonexistent/file.json")
    
    def test_validate_policy_structure_missing_grant_src(self):
        """Test validation of grants with missing src field."""
        parser = PolicyParser()
        parser.grants = [{"dst": ["target"]}]  # Missing src
        
        with pytest.raises(ValueError, match="Grant 1 missing required 'src' field"):
            parser._validate_policy_structure()
    
    def test_validate_policy_structure_missing_grant_dst(self):
        """Test validation of grants with missing dst field."""
        parser = PolicyParser()
        parser.grants = [{"src": ["source"]}]  # Missing dst
        
        with pytest.raises(ValueError, match="Grant 1 missing required 'dst' field"):
            parser._validate_policy_structure()
    
    def test_validate_policy_structure_invalid_grant_src_type(self):
        """Test validation of grants with wrong src type."""
        parser = PolicyParser()
        parser.grants = [{"src": "not_a_list", "dst": ["target"]}]
        
        with pytest.raises(ValueError, match="Grant 1 'src' must be a list"):
            parser._validate_policy_structure()
    
    def test_validate_ip_specifications_valid(self):
        """Test validation of valid IP specifications."""
        parser = PolicyParser()
        # These should not raise exceptions
        parser._validate_ip_specifications(["*"], 1)
        parser._validate_ip_specifications(["tcp:443"], 1)
        parser._validate_ip_specifications(["tcp:8000-8999"], 1)
        parser._validate_ip_specifications(["tcp"], 1)
    
    def test_validate_ip_specifications_invalid_port_range(self):
        """Test validation of invalid port ranges."""
        parser = PolicyParser()
        
        with pytest.raises(ValueError, match="port out of range"):
            parser._validate_ip_specifications(["tcp:70000"], 1)
        
        with pytest.raises(ValueError, match="invalid port range"):
            parser._validate_ip_specifications(["tcp:8000-7000"], 1)
    
    def test_validate_ip_specifications_invalid_format(self):
        """Test validation of invalid IP specification format."""
        parser = PolicyParser()
        
        # Test invalid port specification (gets caught as port error, not IP spec error)
        with pytest.raises(ValueError, match="invalid port specification"):
            parser._validate_ip_specifications(["tcp:443:extra"], 1)
        
        with pytest.raises(ValueError, match="invalid port specification"):
            parser._validate_ip_specifications(["tcp:abc"], 1)
    
    def test_parse_policy_complete_structure(self):
        """Test parsing a complete policy structure."""
        test_policy = {
            "groups": {"group:test": ["user@example.com"]},
            "hosts": {"server": "192.168.1.1"},
            "tagOwners": {"tag:web": ["admin@example.com"]},
            "acls": [{"action": "accept", "src": ["group:test"], "dst": ["server:22"]}],
            "grants": [{"src": ["group:test"], "dst": ["tag:web"], "ip": ["tcp:443"]}]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_policy, f)
            temp_path = f.name
        
        parser = PolicyParser(temp_path)
        parser.parse_policy()
        
        assert parser.groups == test_policy["groups"]
        assert parser.hosts == test_policy["hosts"]
        assert parser.tag_owners == test_policy["tagOwners"]
        assert parser.acls == test_policy["acls"]
        assert parser.grants == test_policy["grants"]


if __name__ == "__main__":
    pytest.main([__file__])