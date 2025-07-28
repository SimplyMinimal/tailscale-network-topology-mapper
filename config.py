"""
Configuration module for Tailscale Network Topology Mapper.

This module contains all configuration constants, settings, and default values
used throughout the application. It provides centralized configuration management
for network visualization, policy parsing, security validation, and logging.

The configuration supports environment variable overrides for deployment
flexibility and includes comprehensive validation settings for Tailscale
policy files.

Environment Variables:
    TS_COMPANY_DOMAIN: Override the default company domain for email validation

Constants:
    COMPANY_DOMAIN: Company domain for email validation
    POLICY_FILE: Default path to the Tailscale policy file
    NODE_COLORS: Color scheme for different node types in visualizations
    VISUALIZATION_CONFIG: Pyvis network visualization settings
    LOG_FORMAT: Standard logging format string
    VALID_PROTOCOLS: Set of valid network protocols for grant validation
    MIN_PORT/MAX_PORT: Valid port range limits
    NODE_OPTIONS: Available node visualization options
    NETWORK_OPTIONS: Available network layout options
"""

import os
from typing import Dict, Set, Any

# Company domain configuration
COMPANY_DOMAIN: str = "example.com"
"""
Default company domain for email validation.

Can be overridden by setting the TS_COMPANY_DOMAIN environment variable.
Used for validating email addresses in group membership definitions.
"""

if "TS_COMPANY_DOMAIN" in os.environ:
    COMPANY_DOMAIN = os.environ["TS_COMPANY_DOMAIN"]
    print(f'Using {COMPANY_DOMAIN} as company domain')

# Policy file configuration
POLICY_FILE: str = os.path.join(os.path.dirname(__file__), "policy.hujson")
"""
Default path to the Tailscale policy file.

Points to 'policy.hujson' in the same directory as this configuration file.
Supports both JSON and HuJSON (Human JSON) formats.
"""

# Node color configuration
NODE_COLORS: Dict[str, str] = {
    "tag": "#00cc66",      # Green for tags
    "group": "#FFFF00",    # Yellow for groups and autogroups
    "host": "#ff6666"      # Red for hosts
}
"""
Color scheme for different node types in network visualizations.

Maps node types to hexadecimal color codes:
- tag: Green (#00cc66) - Tailscale tags and tag-based rules
- group: Yellow (#FFFF00) - User groups and autogroups
- host: Red (#ff6666) - Individual hosts and IP addresses
"""

# Visualization configuration
VISUALIZATION_CONFIG: Dict[str, Any] = {
    "height": "800px",
    "width": "100%",
    "notebook": True,
    "directed": True,
    "filter_menu": True,
    "select_menu": True,
    "neighborhood_highlight": True,
    "cdn_resources": "remote"
}
"""
Pyvis network visualization configuration settings.

Controls the appearance and behavior of the interactive HTML network graph:
- height/width: Canvas dimensions
- notebook: Jupyter notebook compatibility
- directed: Show directional arrows on edges
- filter_menu: Enable node/edge filtering controls
- select_menu: Enable node selection interface
- neighborhood_highlight: Highlight connected nodes on selection
- cdn_resources: Use remote CDN for JavaScript libraries
"""

# Logging configuration
LOG_FORMAT: str = "%(levelname)s [%(filename)s:%(lineno)d]: %(message)s"
"""
Standard logging format string for consistent log output.

Includes log level, source file name, line number, and message content.
Used throughout the application for debugging and monitoring.
"""

# Valid network protocols for grant validation
VALID_PROTOCOLS: Set[str] = {
    "tcp", "udp", "icmp", "ah", "esp", "gre",
    "ipv6-icmp", "ospf", "sctp"
}
"""
Set of valid network protocols for Tailscale grant validation.

Contains all supported IP protocols that can be specified in grant rules.
Used for validating protocol specifications in policy files to ensure
only supported protocols are allowed.

Supported protocols:
- tcp: Transmission Control Protocol
- udp: User Datagram Protocol
- icmp: Internet Control Message Protocol
- ah: Authentication Header (IPSec)
- esp: Encapsulating Security Payload (IPSec)
- gre: Generic Routing Encapsulation
- ipv6-icmp: ICMPv6 for IPv6
- ospf: Open Shortest Path First
- sctp: Stream Control Transmission Protocol
"""

# Port range limits
MIN_PORT: int = 1
"""Minimum valid port number for network services."""

MAX_PORT: int = 65535
"""Maximum valid port number for network services."""

# Node visualization options
NODE_OPTIONS: Dict[str, Any] = {
    "font": {"size": 12, "color": "black"},
    "borderWidth": 2,
    "borderWidthSelected": 3,
    "chosen": {"node": True, "label": True},
    "labelHighlightBold": True,
    "mass": 1,
    "scaling": {
        "min": 10,
        "max": 30,
        "label": {
            "enabled": True,
            "min": 8,
            "max": 20
        }
    }
}
"""
Node visualization options for Pyvis network graphs.

Defines the appearance and behavior of individual nodes in the network
visualization, including fonts, borders, selection behavior, and scaling.

Options:
- font: Text appearance for node labels
- borderWidth: Normal and selected border thickness
- chosen: Enable node and label selection
- labelHighlightBold: Bold labels when highlighted
- mass: Node mass for physics simulation
- scaling: Size scaling based on node importance
"""

# Network visualization options
NETWORK_OPTIONS: Dict[str, Any] = {
    "nodes": {
        "font": {"size": 12},
        "borderWidth": 2,
        "chosen": True
    },
    "edges": {
        "arrows": {"to": {"enabled": True, "scaleFactor": 1}},
        "color": {"color": "#848484", "highlight": "#ff0000"},
        "width": 2,
        "smooth": {"enabled": True, "type": "continuous"}
    },
    "physics": {
        "enabled": True,
        "stabilization": {"iterations": 100},
        "barnesHut": {
            "gravitationalConstant": -2000,
            "centralGravity": 0.3,
            "springLength": 95,
            "springConstant": 0.04,
            "damping": 0.09
        }
    },
    "interaction": {
        "hover": True,
        "selectConnectedEdges": True,
        "tooltipDelay": 200
    }
}