import logging
import argparse

from policy_parser import PolicyParser
from network_graph import NetworkGraph
from renderer import Renderer
from config import LOG_FORMAT


def main():
    parser = argparse.ArgumentParser(description="Tailscale Network Topology Mapper")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format=LOG_FORMAT
    )
    
    logging.info("Starting Tailscale Network Topology Mapper")
    logging.debug(f"Debug logging enabled: {args.debug}")

    try:
        logging.debug("Initializing PolicyParser")
        policy_parser = PolicyParser()
        logging.debug("Parsing policy file")
        policy_parser.parse_policy()
        logging.debug(f"Policy parsing completed. Found {len(policy_parser.groups)} groups, {len(policy_parser.hosts)} hosts, {len(policy_parser.acls)} ACLs, {len(policy_parser.grants)} grants")
    except ValueError as e:
        logging.error(f"Policy parsing failed: {str(e)}")
        return

    logging.debug("Initializing NetworkGraph")
    network_graph = NetworkGraph(policy_parser.hosts, policy_parser.groups)
    logging.debug("Building network graph from ACLs and grants")
    network_graph.build_graph(policy_parser.acls, policy_parser.grants)
    logging.debug(f"Network graph built with {len(network_graph.nodes)} nodes and {len(network_graph.edges)} edges")

    logging.debug("Initializing Renderer")
    renderer = Renderer(network_graph)
    logging.debug("Rendering network topology to HTML")
    renderer.render_to_html("network_topology.html")

    logging.info("Network topology rendered successfully.")


if __name__ == "__main__":
    main()