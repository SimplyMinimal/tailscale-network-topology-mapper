"""
Tag membership from the Tailscale control plane.

The policy file states what a tag may do. It does not state which machine
carries that tag, and the renderer cannot infer it: a tag node in the graph
stands for a rule, not for hardware. This module supplies the missing half by
reading the tailnet's devices from the Tailscale API and grouping them by tag.

The result feeds two things in the visualisation:
    - the device count and names shown on every tag node
    - the device nodes that `--with-devices` draws on demand

Functions:
    build_tag_membership: Group device objects by the tags they carry
    fetch_tag_membership: Read the devices from the API, then group them
"""
import logging
from typing import Any, Dict, List

from services.file_loader import PolicyFileLoader


def _device_name(device: Dict[str, Any]) -> str:
    """
    Short, human-readable name for a device.

    The API's `name` is the MagicDNS FQDN ("host.tailnet.ts.net"); the label on
    a graph node wants the first component. `hostname` and `id` are fallbacks
    for a device the API returns without a name.
    """
    name = device.get("name") or device.get("hostname") or device.get("id", "")
    return name.split(".")[0]


def build_tag_membership(devices: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Group devices by the tags they carry.

    Args:
        devices: Device objects as returned by the Tailscale API

    Returns:
        Mapping of tag ("tag:example") to the sorted device names carrying it.
        Devices owned by a user rather than a tag carry no tags and are absent
        from the result.

    Example:
        >>> build_tag_membership([
        ...     {"name": "web-1.example.ts.net", "tags": ["tag:web"]},
        ...     {"name": "web-2.example.ts.net", "tags": ["tag:web"]},
        ...     {"name": "laptop.example.ts.net"},
        ... ])
        {'tag:web': ['web-1', 'web-2']}
    """
    membership: Dict[str, List[str]] = {}
    for device in devices:
        name = _device_name(device)
        if not name:
            continue
        for tag in device.get("tags") or []:
            membership.setdefault(tag, []).append(name)
    return {tag: sorted(set(names)) for tag, names in sorted(membership.items())}


def fetch_tag_membership(api_key: str, tailnet: str) -> Dict[str, List[str]]:
    """
    Read the tailnet's devices and group them by tag.

    Args:
        api_key: Tailscale API key
        tailnet: Tailscale tailnet

    Returns:
        Mapping of tag to the device names carrying it

    Raises:
        ValueError: If the API request fails or the response cannot be parsed
    """
    devices = PolicyFileLoader.load_devices_from_tailscale_api(api_key, tailnet)
    membership = build_tag_membership(devices)
    logging.info(
        f"Read {sum(len(names) for names in membership.values())} tag assignments "
        f"across {len(membership)} tags"
    )
    return membership
