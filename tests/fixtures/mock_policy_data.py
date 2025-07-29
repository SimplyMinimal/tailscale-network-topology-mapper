"""
Comprehensive mock policy data for testing.

This module provides static mock data that simulates various Tailscale network
configurations without requiring external files or API calls. The data covers:
- Different node types (devices, subnets, exit nodes)
- Various ACL rules and grant configurations  
- Multiple routing scenarios (via routing, posture checks)
- Edge cases and error conditions

The mock data is designed to be self-contained and easily extensible for
testing new features.
"""

from typing import Dict, List, Any


class MockPolicyData:
    """Comprehensive mock policy data for testing."""
    
    @staticmethod
    def get_basic_policy() -> Dict[str, Any]:
        """Basic policy with minimal data for simple tests."""
        return {
            "groups": {
                "group:admin": ["admin@company.com"],
                "group:dev": ["dev1@company.com", "dev2@company.com"]
            },
            "hosts": {
                "server1": "100.64.1.10",
                "database": "100.64.1.20"
            },
            "tagOwners": {
                "tag:web": ["group:admin"],
                "tag:db": ["group:admin"]
            },
            "acls": [
                {
                    "action": "accept",
                    "src": ["group:admin"],
                    "dst": ["server1:22"]
                }
            ],
            "grants": [
                {
                    "src": ["group:dev"],
                    "dst": ["database"],
                    "ip": ["tcp:5432"]
                }
            ]
        }
    
    @staticmethod
    def get_comprehensive_policy() -> Dict[str, Any]:
        """Comprehensive policy with all features for thorough testing."""
        return {
            "groups": {
                "group:admin": ["admin@company.com", "admin2@company.com"],
                "group:dev": ["dev1@company.com", "dev2@company.com"],
                "group:sales": ["sales1@company.com", "sales2@company.com"],
                "group:contractors": ["contractor@external.com"],
                "group:mobile": ["mobile@company.com"],
                "group:nyc": ["nyc-user@company.com"],
                "group:sre": ["sre@company.com"]
            },
            "hosts": {
                "web-server": "100.64.1.10",
                "database": "100.64.1.20",
                "api-gateway": "100.64.1.30",
                "logging-server": "100.64.1.40",
                "internal-tool": "100.64.1.50",
                "exit-node-nyc": "100.64.1.100",
                "subnet-range": "192.168.1.0/24",
                "production-backend": "104.105.106.0/24"
            },
            "tagOwners": {
                "tag:web": ["group:admin"],
                "tag:database": ["group:admin"],
                "tag:api": ["group:dev"],
                "tag:logging": ["group:sre"],
                "tag:exit-node-nyc": ["group:admin"],
                "tag:production": ["group:admin"],
                "tag:development": ["group:dev"],
                "tag:mobile-device": ["group:mobile"]
            },
            "acls": [
                {
                    "action": "accept",
                    "src": ["group:admin"],
                    "dst": ["tag:web:80", "tag:web:443"]
                },
                {
                    "action": "accept", 
                    "src": ["group:dev"],
                    "dst": ["tag:development:*"]
                },
                {
                    "action": "accept",
                    "src": ["tag:web"],
                    "dst": ["tag:database:5432"]
                },
                {
                    "action": "accept",
                    "src": ["group:sre"],
                    "dst": ["tag:logging:514", "tag:logging:9200"]
                }
            ],
            "grants": [
                {
                    "src": ["group:dev"],
                    "dst": ["api-gateway"],
                    "ip": ["tcp:443", "tcp:8080"],
                    "via": ["tag:exit-node-nyc"]
                },
                {
                    "src": ["group:mobile"],
                    "dst": ["internal-tool"],
                    "ip": ["tcp:443"],
                    "srcPosture": ["posture:complianceDevice", "posture:latestMac"],
                    "app": ["webapp-connector"]
                },
                {
                    "src": ["group:contractors"],
                    "dst": ["web-server"],
                    "ip": ["tcp:80", "tcp:443"],
                    "via": ["api-gateway"],
                    "dstPosture": ["posture:trustedDevice"]
                },
                {
                    "src": ["group:sales"],
                    "dst": ["database"],
                    "ip": ["tcp:5432"],
                    "app": ["service-mesh"],
                    "srcPosture": ["posture:complianceDevice"]
                },
                {
                    "src": ["group:nyc"],
                    "dst": ["logging-server"],
                    "ip": ["tcp:514", "udp:514"],
                    "via": ["internal-tool"],
                    "app": ["deployment-pipeline"]
                },
                {
                    "src": ["group:admin"],
                    "dst": ["subnet-range"],
                    "ip": ["*"]
                },
                {
                    "src": ["tag:mobile-device"],
                    "dst": ["api-gateway"],
                    "ip": ["tcp:443"],
                    "srcPosture": ["posture:mobileCompliance"]
                }
            ]
        }
    
    @staticmethod
    def get_mixed_nodes_policy() -> Dict[str, Any]:
        """Policy designed to test mixed nodes (appearing in both ACLs and grants)."""
        return {
            "groups": {
                "group:mixed": ["mixed@company.com"],
                "group:acl-only": ["acl@company.com"],
                "group:grant-only": ["grant@company.com"]
            },
            "hosts": {
                "mixed-host": "100.64.1.10",
                "acl-host": "100.64.1.20",
                "grant-host": "100.64.1.30"
            },
            "tagOwners": {
                "tag:mixed": ["group:mixed"],
                "tag:acl-only": ["group:acl-only"],
                "tag:grant-only": ["group:grant-only"]
            },
            "acls": [
                {
                    "action": "accept",
                    "src": ["group:mixed"],
                    "dst": ["mixed-host:22"]
                },
                {
                    "action": "accept",
                    "src": ["group:acl-only"],
                    "dst": ["acl-host:80"]
                },
                {
                    "action": "accept",
                    "src": ["tag:mixed"],
                    "dst": ["tag:acl-only:443"]
                }
            ],
            "grants": [
                {
                    "src": ["group:mixed"],
                    "dst": ["mixed-host"],
                    "ip": ["tcp:443"]
                },
                {
                    "src": ["group:grant-only"],
                    "dst": ["grant-host"],
                    "ip": ["tcp:80"]
                },
                {
                    "src": ["tag:mixed"],
                    "dst": ["tag:grant-only"],
                    "ip": ["tcp:8080"]
                }
            ]
        }
    
    @staticmethod
    def get_search_test_policy() -> Dict[str, Any]:
        """Policy specifically designed for testing search functionality."""
        return {
            "groups": {
                "group:search-test": ["search@company.com"],
                "group:protocol-test": ["protocol@company.com"],
                "group:via-test": ["via@company.com"],
                "group:posture-test": ["posture@company.com"],
                "group:app-test": ["app@company.com"]
            },
            "hosts": {
                "search-server": "100.64.1.10",
                "protocol-server": "100.64.1.20",
                "via-server": "100.64.1.30",
                "posture-server": "100.64.1.40",
                "app-server": "100.64.1.50"
            },
            "tagOwners": {
                "tag:searchable": ["group:search-test"]
            },
            "acls": [
                {
                    "action": "accept",
                    "src": ["group:search-test"],
                    "dst": ["search-server:22"]
                }
            ],
            "grants": [
                {
                    "src": ["group:protocol-test"],
                    "dst": ["protocol-server"],
                    "ip": ["tcp:443", "tcp:80", "udp:53"]
                },
                {
                    "src": ["group:via-test"],
                    "dst": ["via-server"],
                    "ip": ["tcp:443"],
                    "via": ["tag:exit-node-nyc", "api-gateway"]
                },
                {
                    "src": ["group:posture-test"],
                    "dst": ["posture-server"],
                    "ip": ["tcp:443"],
                    "srcPosture": ["posture:complianceDevice", "posture:latestMac"],
                    "dstPosture": ["posture:trustedDevice"]
                },
                {
                    "src": ["group:app-test"],
                    "dst": ["app-server"],
                    "ip": ["tcp:443"],
                    "app": ["webapp-connector", "service-mesh", "deployment-pipeline"]
                }
            ]
        }
    
    @staticmethod
    def get_edge_cases_policy() -> Dict[str, Any]:
        """Policy with edge cases and error conditions for robust testing."""
        return {
            "groups": {
                "group:empty": [],
                "group:single": ["single@company.com"],
                "group:special-chars": ["user+test@company.com", "user.test@company.com"]
            },
            "hosts": {
                "localhost": "127.0.0.1",
                "ipv6-host": "::1",
                "cidr-host": "10.0.0.0/8"
            },
            "tagOwners": {
                "tag:empty-owner": [],
                "tag:multi-owner": ["group:single", "group:empty"]
            },
            "acls": [
                {
                    "action": "accept",
                    "src": ["*"],
                    "dst": ["localhost:*"]
                }
            ],
            "grants": [
                {
                    "src": ["group:single"],
                    "dst": ["cidr-host"],
                    "ip": ["*"]
                }
            ]
        }


class MockLineNumbers:
    """Mock line numbers for testing rule references."""
    
    @staticmethod
    def get_basic_line_numbers() -> Dict[str, List[int]]:
        """Basic line numbers for simple tests."""
        return {
            "acls": [10, 15],
            "grants": [25, 30]
        }
    
    @staticmethod
    def get_comprehensive_line_numbers() -> Dict[str, List[int]]:
        """Comprehensive line numbers matching comprehensive policy."""
        return {
            "acls": [50, 55, 60, 65],
            "grants": [80, 90, 100, 110, 120, 130, 140]
        }
