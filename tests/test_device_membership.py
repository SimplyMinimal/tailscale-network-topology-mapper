"""
Test suite for tag membership from the Tailscale control plane.
"""
import pytest
from unittest.mock import patch

from services.device_membership import (
    _device_name,
    build_tag_membership,
    fetch_tag_membership,
)


class TestDeviceName:
    """Test cases for the short-name derivation."""

    def test_uses_first_component_of_magicdns_name(self):
        assert _device_name({"name": "web-1.example.ts.net"}) == "web-1"

    def test_falls_back_to_hostname(self):
        assert _device_name({"hostname": "web-2"}) == "web-2"

    def test_falls_back_to_id(self):
        assert _device_name({"id": "nodekey-123"}) == "nodekey-123"

    def test_empty_for_a_device_with_no_identifier(self):
        assert _device_name({}) == ""


class TestBuildTagMembership:
    """Test cases for grouping devices by tag."""

    def test_groups_devices_by_tag(self):
        devices = [
            {"name": "web-1.example.ts.net", "tags": ["tag:web"]},
            {"name": "web-2.example.ts.net", "tags": ["tag:web"]},
            {"name": "db-1.example.ts.net", "tags": ["tag:db"]},
        ]
        assert build_tag_membership(devices) == {
            "tag:db": ["db-1"],
            "tag:web": ["web-1", "web-2"],
        }

    def test_a_device_with_several_tags_appears_under_each(self):
        devices = [{"name": "web-1.example.ts.net", "tags": ["tag:web", "tag:prod"]}]
        membership = build_tag_membership(devices)
        assert membership["tag:web"] == ["web-1"]
        assert membership["tag:prod"] == ["web-1"]

    def test_untagged_devices_are_absent(self):
        # A device owned by a user rather than a tag carries no tags, and the
        # graph has no node for it.
        devices = [
            {"name": "laptop.example.ts.net"},
            {"name": "phone.example.ts.net", "tags": []},
            {"name": "phone-2.example.ts.net", "tags": None},
        ]
        assert build_tag_membership(devices) == {}

    def test_names_are_sorted_and_deduplicated(self):
        devices = [
            {"name": "z.example.ts.net", "tags": ["tag:web"]},
            {"name": "a.example.ts.net", "tags": ["tag:web"]},
            {"name": "a.example.ts.net", "tags": ["tag:web"]},
        ]
        assert build_tag_membership(devices)["tag:web"] == ["a", "z"]

    def test_empty_device_list(self):
        assert build_tag_membership([]) == {}


class TestFetchTagMembership:
    """Test cases for the API path."""

    def test_groups_what_the_api_returns(self):
        devices = [{"name": "web-1.example.ts.net", "tags": ["tag:web"]}]
        with patch(
            "services.device_membership.PolicyFileLoader.load_devices_from_tailscale_api",
            return_value=devices,
        ) as loader:
            assert fetch_tag_membership("key", "example.com") == {"tag:web": ["web-1"]}
            loader.assert_called_once_with("key", "example.com")

    def test_propagates_a_failed_request(self):
        with patch(
            "services.device_membership.PolicyFileLoader.load_devices_from_tailscale_api",
            side_effect=ValueError("Failed to fetch devices from Tailscale API"),
        ):
            with pytest.raises(ValueError, match="Failed to fetch devices"):
                fetch_tag_membership("key", "example.com")
