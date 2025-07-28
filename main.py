"""
Tailscale Network Topology Mapper - Main Application Entry Point

This module provides the main entry point for the Tailscale network topology mapping
application. It orchestrates the parsing of Tailscale policy files, building of
network graphs, and rendering of interactive HTML visualizations.

The application supports both legacy ACL rules and modern grant rules, providing
comprehensive visualization of network access relationships within a Tailscale
network infrastructure.

Example:
    Run with default settings:
        $ python main.py

    Run with debug logging:
        $ python main.py --debug

Author: Tailscale Network Topology Mapper Team
"""

import logging
import argparse

from policy_parser import PolicyParser
from network_graph import NetworkGraph
from renderer import Renderer
from config import LOG_FORMAT
from services import PolicyParserInterface, NetworkGraphInterface, RendererInterface
from services.container import DIContainer


def setup_dependency_injection() -> DIContainer:
    """
    Set up dependency injection container with service registrations.

    Creates and configures a dependency injection container with all required
    service implementations. This promotes loose coupling and makes the
    application more testable and maintainable.

    Returns:
        DIContainer: Configured dependency injection container with all
            service implementations registered.

    Example:
        >>> container = setup_dependency_injection()
        >>> parser = container.get(PolicyParserInterface)
        >>> isinstance(parser, PolicyParser)
        True
    """
    container = DIContainer()

    # Register service implementations
    container.register(PolicyParserInterface, PolicyParser)
    container.register(NetworkGraphInterface, NetworkGraph)
    container.register(RendererInterface, Renderer)

    return container


def main() -> None:
    """
    Main application entry point.

    Parses command line arguments, configures logging, sets up dependency
    injection, and orchestrates the complete network topology mapping workflow.

    The workflow consists of:
    1. Policy file parsing (JSON/HuJSON format)
    2. Network graph construction from ACL/grant rules
    3. Interactive HTML visualization rendering

    Command Line Arguments:
        --debug: Enable debug-level logging for detailed execution information

    Raises:
        SystemExit: On successful completion or unhandled errors

    Example:
        >>> main()  # Processes default policy file and generates visualization
    """
    parser = argparse.ArgumentParser(
        description="Tailscale Network Topology Mapper",
        epilog="Generates interactive HTML visualizations of Tailscale network access policies"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging for detailed execution information"
    )
    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format=LOG_FORMAT
    )

    logging.info("Starting Tailscale Network Topology Mapper")
    logging.debug(f"Debug logging enabled: {args.debug}")

    # Set up dependency injection
    container = setup_dependency_injection()

    try:
        logging.debug("Initializing PolicyParser via DI container")
        policy_parser = container.get(PolicyParserInterface)
        logging.debug("Parsing policy file")
        policy_parser.parse_policy()
        logging.debug(f"Policy parsing completed. Found {len(policy_parser.groups)} groups, {len(policy_parser.hosts)} hosts, {len(policy_parser.acls)} ACLs, {len(policy_parser.grants)} grants")
    except ValueError as e:
        logging.error(f"Policy parsing failed: {str(e)}")
        return

    logging.debug("Initializing NetworkGraph via DI container")
    network_graph = NetworkGraph(policy_parser.hosts, policy_parser.groups)
    logging.debug("Building network graph from ACLs and grants")
    network_graph.build_graph(policy_parser.acls, policy_parser.grants)
    logging.debug(f"Network graph built with {len(network_graph.nodes)} nodes and {len(network_graph.edges)} edges")

    logging.debug("Initializing Renderer via DI container")
    renderer = Renderer(network_graph)
    logging.debug("Rendering network topology to HTML")
    renderer.render_to_html("network_topology.html")

    logging.info("Network topology rendered successfully.")


if __name__ == "__main__":
    main()