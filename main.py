import logging

from policy_parser import PolicyParser
from network_graph import NetworkGraph
from renderer import Renderer


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:
        parser = PolicyParser()
        parser.parse_policy()
    except ValueError as e:
        logging.error(str(e))
        return

    network_graph = NetworkGraph(parser.hosts, parser.groups)
    network_graph.build_graph(parser.acls, parser.grants)

    renderer = Renderer(network_graph)
    renderer.render_to_html("network_topology.html")

    logging.info("Network topology rendered successfully.")


if __name__ == "__main__":
    main()