"""
Test suite for refactored PolicyParser class and related components.
"""
import pytest
import tempfile
import json
import os
from unittest.mock import patch, MagicMock
from policy_parser import PolicyParser
from services.file_loader import PolicyFileLoader
from services.policy_validator import PolicyValidator
from models.policy_data import PolicyData


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
    
    def test_parse_policy_success(self):
        """Test successful policy parsing."""
        test_data = {
            "groups": {"group:test": ["user@example.com"]},
            "hosts": {"host1": "192.168.1.1"},
            "tagOwners": {"tag:web": ["group:admin"]},
            "acls": [{"src": ["group:test"], "dst": ["host1:80"]}],
            "grants": [{"src": ["group:test"], "dst": ["host1:443"]}]
        }
        
        parser = PolicyParser()
        
        # Mock the file loader and validator
        parser._file_loader.load_json_or_hujson = MagicMock(return_value=test_data)
        parser._validator.validate_policy_structure = MagicMock()
        
        parser.parse_policy()
        
        assert parser.groups == test_data["groups"]
        assert parser.hosts == test_data["hosts"]
        assert parser.tag_owners == test_data["tagOwners"]
        assert parser.acls == test_data["acls"]
        assert parser.grants == test_data["grants"]
    
    def test_parse_policy_file_error(self):
        """Test handling of file loading errors."""
        parser = PolicyParser()
        parser._file_loader.load_json_or_hujson = MagicMock(side_effect=ValueError("File not found"))
        
        with pytest.raises(ValueError, match="File not found"):
            parser.parse_policy()
    
    def test_parse_policy_validation_error(self):
        """Test handling of validation errors."""
        test_data = {"grants": [{"dst": ["target"]}]}  # Missing src

        parser = PolicyParser()
        parser._file_loader.load_json_or_hujson = MagicMock(return_value=test_data)
        parser._validator.validate_policy_structure = MagicMock(
            side_effect=ValueError("Grant 1 missing required 'src' field")
        )

        with pytest.raises(ValueError, match="Grant 1 missing required 'src' field"):
            parser.parse_policy()

    @patch.dict('os.environ', {'TAILSCALE_API_KEY': 'test-key', 'TAILSCALE_TAILNET': 'test-tailnet'})
    def test_parse_policy_with_tailscale_validation(self):
        """Test that local validation is skipped when Tailscale validation is used."""
        test_data = {
            "groups": {"group:test": ["user@example.com"]},
            "hosts": {"host1": "192.168.1.1"},
            "tagOwners": {"tag:web": ["group:admin"]},
            "acls": [{"src": ["group:test"], "dst": ["host1:80"]}],
            "grants": [{"src": ["group:test"], "dst": ["host1:443"]}]
        }

        parser = PolicyParser()
        parser._file_loader.load_json_or_hujson = MagicMock(return_value=test_data)
        parser._validator.validate_policy_structure = MagicMock()
        parser._validator.validate_with_tailscale_api = MagicMock()

        parser.parse_policy()

        # Verify Tailscale validation was called with the serialized JSON
        parser._validator.validate_with_tailscale_api.assert_called_once()
        call_args = parser._validator.validate_with_tailscale_api.call_args[0][0]
        assert isinstance(call_args, str)  # Should be JSON string, not file path

        # Verify local validation was NOT called
        parser._validator.validate_policy_structure.assert_not_called()

        # Verify data was still parsed correctly
        assert parser.groups == test_data["groups"]
        assert parser.hosts == test_data["hosts"]

    @patch.dict('os.environ', {}, clear=True)
    def test_parse_policy_without_tailscale_validation(self):
        """Test that local validation is used when Tailscale credentials are not available."""
        test_data = {
            "groups": {"group:test": ["user@example.com"]},
            "hosts": {"host1": "192.168.1.1"},
            "tagOwners": {"tag:web": ["group:admin"]},
            "acls": [{"src": ["group:test"], "dst": ["host1:80"]}],
            "grants": [{"src": ["group:test"], "dst": ["host1:443"]}]
        }

        parser = PolicyParser()
        parser._file_loader.load_json_or_hujson = MagicMock(return_value=test_data)
        parser._validator.validate_policy_structure = MagicMock()

        parser.parse_policy()

        # Verify local validation WAS called
        parser._validator.validate_policy_structure.assert_called_once_with(test_data)

        # Verify data was parsed correctly
        assert parser.groups == test_data["groups"]
        assert parser.hosts == test_data["hosts"]

    @patch.dict('os.environ', {'TAILSCALE_API_KEY': 'test-key', 'TAILSCALE_TAILNET': 'test-tailnet'})
    def test_parse_policy_tailscale_validation_failure(self):
        """Test that Tailscale validation failures are properly raised."""
        test_data = {
            "groups": {"group:test": ["user@example.com"]},
            "hosts": {"host1": "192.168.1.1"},
        }

        parser = PolicyParser()
        parser._file_loader.load_json_or_hujson = MagicMock(return_value=test_data)

        # Mock failed Tailscale validation
        parser._validator.validate_with_tailscale_api = MagicMock(
            side_effect=ValueError("Policy validation failed")
        )

        with pytest.raises(ValueError, match="Policy validation failed"):
            parser.parse_policy()


class TestPolicyFileLoader:
    """Test cases for PolicyFileLoader."""
    
    def test_load_json_valid(self):
        """Test loading valid JSON file."""
        test_data = {"groups": {"group:test": ["user@example.com"]}}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name
        
        loader = PolicyFileLoader()
        result = loader.load_json_or_hujson(temp_path)
        assert result == test_data
    
    def test_load_json_file_not_found(self):
        """Test handling of missing file."""
        loader = PolicyFileLoader()
        with pytest.raises(ValueError, match="Error loading policy file"):
            loader.load_json_or_hujson("/nonexistent/file.json")


class TestPolicyValidator:
    """Test cases for PolicyValidator."""
    
    def test_validate_policy_structure_missing_grant_src(self):
        """Test validation of grants with missing src field."""
        data = {"grants": [{"dst": ["target"]}]}  # Missing src
        
        validator = PolicyValidator()
        with pytest.raises(ValueError, match="Grant 1 missing required 'src' field"):
            validator.validate_policy_structure(data)
    
    def test_validate_policy_structure_missing_grant_dst(self):
        """Test validation of grants with missing dst field."""
        data = {"grants": [{"src": ["source"]}]}  # Missing dst
        
        validator = PolicyValidator()
        with pytest.raises(ValueError, match="Grant 1 missing required 'dst' field"):
            validator.validate_policy_structure(data)
    
    def test_validate_policy_structure_invalid_grant_src_type(self):
        """Test validation of grants with wrong src type."""
        data = {"grants": [{"src": "not_a_list", "dst": ["target"]}]}
        
        validator = PolicyValidator()
        with pytest.raises(ValueError, match="Grant 1 'src' field must be a list"):
            validator.validate_policy_structure(data)
    
    def test_validate_ip_specifications_valid(self):
        """Test validation of valid IP specifications."""
        validator = PolicyValidator()
        # These should not raise exceptions
        validator.validate_ip_specifications(["*"], 1)
        validator.validate_ip_specifications(["tcp:443"], 1)
        validator.validate_ip_specifications(["tcp:8000-8999"], 1)
        validator.validate_ip_specifications(["tcp:*"], 1)  # Protocol with wildcard
        validator.validate_ip_specifications(["udp:*"], 1)  # Protocol with wildcard
        validator.validate_ip_specifications(["icmp:*"], 1)  # Protocol with wildcard
        # Test bare port numbers (Tailscale syntax)
        validator.validate_ip_specifications(["53"], 1)
        validator.validate_ip_specifications(["853"], 1)
        validator.validate_ip_specifications(["8000-8999"], 1)
    
    def test_validate_ip_specifications_invalid_format(self):
        """Test validation of invalid IP specification formats."""
        validator = PolicyValidator()

        # Test invalid protocol
        with pytest.raises(ValueError, match="Invalid protocol 'invalid'"):
            validator.validate_ip_specifications(["invalid:443"], 1)

        # Test port out of range with protocol prefix
        with pytest.raises(ValueError, match="Port 99999 out of valid range"):
            validator.validate_ip_specifications(["tcp:99999"], 1)

        # Test invalid bare specification (not a port, range, or protocol)
        with pytest.raises(ValueError, match="Invalid specification 'notaport'"):
            validator.validate_ip_specifications(["notaport"], 1)

        # Test bare port out of range
        with pytest.raises(ValueError, match="Port 99999 out of valid range"):
            validator.validate_ip_specifications(["99999"], 1)

        # Test bare protocol without port (should fail - must use protocol:* or protocol:port)
        with pytest.raises(ValueError, match='Bare protocol "tcp" is invalid'):
            validator.validate_ip_specifications(["tcp"], 1)

        with pytest.raises(ValueError, match='Bare protocol "udp" is invalid'):
            validator.validate_ip_specifications(["udp"], 1)

    @patch.dict('os.environ', {'TAILSCALE_API_KEY': 'test-key', 'TAILSCALE_TAILNET': 'test-tailnet'})
    @patch('requests.post')
    def test_validate_with_tailscale_api_success(self, mock_post):
        """Test successful Tailscale API validation."""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        validator = PolicyValidator()
        # Pass JSON string instead of file path
        policy_json = json.dumps({"acls": []})
        validator.validate_with_tailscale_api(policy_json)

        # Verify API was called correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]['auth'] == ('test-key', '')
        assert 'https://api.tailscale.com/api/v2/tailnet/test-tailnet/acl/validate' in call_args[0]

    @patch.dict('os.environ', {'TAILSCALE_API_KEY': 'test-key', 'TAILSCALE_TAILNET': 'test-tailnet'})
    @patch('requests.post')
    def test_validate_with_tailscale_api_validation_error(self, mock_post):
        """Test Tailscale API validation with policy errors."""
        # Mock API response with validation errors
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "Invalid policy"}
        mock_response.text = '{"error": "Invalid policy"}'
        mock_post.return_value = mock_response

        validator = PolicyValidator()
        # Pass JSON string instead of file path
        policy_json = json.dumps({"acls": []})
        with pytest.raises(ValueError, match="Policy validation failed"):
            validator.validate_with_tailscale_api(policy_json)

    @patch.dict('os.environ', {}, clear=True)
    def test_validate_with_tailscale_api_missing_credentials(self):
        """Test Tailscale API validation with missing credentials."""
        validator = PolicyValidator()
        # Pass JSON string - should fail due to missing credentials
        with pytest.raises(ValueError, match="Missing TAILSCALE_TAILNET environment variable"):
            validator.validate_with_tailscale_api("{\"grants\": []}")

    @patch.dict('os.environ', {'TAILSCALE_API_KEY': 'test-key', 'TAILSCALE_TAILNET': 'test-tailnet'})
    @patch('requests.post')
    def test_validate_with_tailscale_api_http_error(self, mock_post):
        """Test Tailscale API validation with HTTP error."""
        # Mock HTTP error response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = 'Unauthorized'
        mock_post.return_value = mock_response

        validator = PolicyValidator()
        # Pass JSON string instead of file path
        policy_json = json.dumps({"acls": []})
        with pytest.raises(ValueError, match="Policy validation failed \\(HTTP 401\\)"):
            validator.validate_with_tailscale_api(policy_json)


class TestPolicyData:
    """Test cases for PolicyData."""
    
    def test_from_dict(self):
        """Test creating PolicyData from dictionary."""
        data = {
            "groups": {"group:test": ["user@example.com"]},
            "hosts": {"host1": "192.168.1.1"},
            "tagOwners": {"tag:web": ["group:admin"]},
            "acls": [{"src": ["group:test"], "dst": ["host1:80"]}],
            "grants": [{"src": ["group:test"], "dst": ["host1:443"]}]
        }
        
        policy_data = PolicyData.from_dict(data)
        
        assert policy_data.groups == data["groups"]
        assert policy_data.hosts == data["hosts"]
        assert policy_data.tag_owners == data["tagOwners"]
        assert policy_data.acls == data["acls"]
        assert policy_data.grants == data["grants"]
    
    def test_get_stats(self):
        """Test getting statistics from PolicyData."""
        policy_data = PolicyData(
            groups={"group1": [], "group2": []},
            hosts={"host1": "ip1"},
            acls=[{"rule": 1}],
            grants=[{"rule": 1}, {"rule": 2}]
        )
        
        stats = policy_data.get_stats()
        
        assert stats["groups"] == 2
        assert stats["hosts"] == 1
        assert stats["acls"] == 1
        assert stats["grants"] == 2
