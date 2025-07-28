"""
Service interfaces for dependency injection architecture.

This module defines abstract base classes (interfaces) for the core services
in the Tailscale Network Topology Mapper application. These interfaces enable
dependency injection, improve testability, and promote loose coupling between
components.

The interfaces follow the Dependency Inversion Principle by defining contracts
that concrete implementations must fulfill, allowing for easy substitution
of implementations for testing or different deployment scenarios.

Interfaces:
    PolicyParserInterface: Contract for policy file parsing services
    NetworkGraphInterface: Contract for network graph building services
    RendererInterface: Contract for visualization rendering services
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any

class PolicyParserInterface(ABC):
    """
    Abstract interface for policy parsing services.

    Defines the contract for services that parse Tailscale policy files
    and extract structured data for network graph construction. Implementations
    should handle both JSON and HuJSON formats and support both legacy ACL
    rules and modern grant rules.

    The interface promotes separation of concerns by isolating policy parsing
    logic from graph building and rendering components.
    """

    @abstractmethod
    def parse_policy(self) -> None:
        """
        Parse the policy file and extract structured data.

        Implementations should:
        - Load and parse JSON/HuJSON policy files
        - Validate policy structure and content
        - Extract groups, hosts, ACLs, and grants
        - Handle parsing errors gracefully

        Raises:
            ValueError: If policy file is invalid or malformed
            FileNotFoundError: If policy file cannot be found
        """
        pass

class NetworkGraphInterface(ABC):
    """
    Abstract interface for network graph building services.

    Defines the contract for services that construct network graphs from
    parsed policy data. Implementations should create nodes and edges
    representing network access relationships from ACL and grant rules.

    The interface supports both legacy ACL rules and modern grant rules
    with their extended features like IP protocols and via routing.
    """

    @abstractmethod
    def build_graph(self, acls: List[Dict[str, Any]], grants: List[Dict[str, Any]]) -> None:
        """
        Build the network graph from ACL and grant rules.

        Implementations should:
        - Process ACL rules for legacy policy support
        - Process grant rules with modern features
        - Create appropriate nodes for groups, tags, and hosts
        - Generate edges representing access relationships
        - Handle protocol specifications and port ranges

        Args:
            acls: List of ACL rule dictionaries from policy file
            grants: List of grant rule dictionaries from policy file

        Note:
            The graph structure should be accessible through instance
            attributes after this method completes.
        """
        pass

class RendererInterface(ABC):
    """
    Abstract interface for visualization rendering services.

    Defines the contract for services that render network graphs to
    interactive HTML visualizations. Implementations should create
    user-friendly visualizations with appropriate styling, legends,
    and interactive features.

    The interface supports various output formats and visualization
    libraries while maintaining a consistent API.
    """

    @abstractmethod
    def render_to_html(self, output_file: str) -> None:
        """
        Render the network graph to an interactive HTML file.

        Implementations should:
        - Generate interactive HTML visualization
        - Include appropriate styling and legends
        - Support node selection and filtering
        - Handle large graphs efficiently
        - Provide user-friendly navigation controls

        Args:
            output_file: Path where the HTML file should be written

        Raises:
            PermissionError: If output file cannot be written
            ValueError: If graph data is invalid or empty
        """
        pass
