import logging
from typing import List, Tuple

from pyvis.network import Network

from network_graph import NetworkGraph
from config import VISUALIZATION_CONFIG, NODE_COLORS


class Renderer:
    """
    Renders network graphs to interactive HTML visualizations using Pyvis.
    
    Creates interactive network visualizations with node selection, filtering,
    and neighborhood highlighting capabilities. Includes a color-coded legend
    for different node types (groups, tags, hosts).
    """
    
    def __init__(self, network_graph: NetworkGraph) -> None:
        """
        Initialize the renderer with a network graph.
        
        Args:
            network_graph: NetworkGraph instance containing nodes and edges to render
        """
        self.network_graph = network_graph
        self.output_file = ""  # Track the output file for legend
        logging.debug(f"Renderer initialized with {len(network_graph.nodes)} nodes and {len(network_graph.edges)} edges")
        self.net = Network(**VISUALIZATION_CONFIG)
        logging.debug("Pyvis Network object created with configuration")

    def render_to_html(self, output_file: str) -> None:
        """
        Render the network graph to an interactive HTML file.
        
        Args:
            output_file: Path where the HTML file should be written
        """
        logging.debug(f"Starting HTML rendering to: {output_file}")
        self.output_file = output_file  # Store for legend
        
        logging.debug("Adding nodes to visualization")
        for node, color, tooltip_text in self.network_graph.nodes:
            self.net.add_node(node, color=color, title=tooltip_text)
            logging.debug(f"Added visualization node: {node} (color: {color})")

        logging.debug("Adding edges to visualization")
        for src, dst in self.network_graph.edges:
            self.net.add_edge(src, dst, arrows={"to": {"enabled": True}})
            logging.debug(f"Added visualization edge: {src} -> {dst}")

        logging.debug("Configuring visualization buttons")
        self.net.show_buttons()
        
        logging.debug(f"Writing HTML file: {output_file}")
        self.net.write_html(output_file)
        
        logging.debug("Adding legend to HTML file")
        self._add_legend()
        
        logging.debug("HTML rendering completed")


    def _add_legend(self) -> None:
        """Add a color-coded legend to the HTML visualization."""
        logging.debug("Creating legend HTML")
        group_color = NODE_COLORS["group"]
        tag_color = NODE_COLORS["tag"]
        host_color = NODE_COLORS["host"]

        legend_html = """
<div style="position: absolute; top: 10px; right: 10px; background-color: #f5f5f5; padding: 10px; border: 1px solid #ccc;">
    <h3>Legend</h3>
    <div style="background-color: {group_color}; width: 20px; height: 20px; display: inline-block;"></div>
    <span>Group</span><br>
    <div style="background-color: {tag_color}; width: 20px; height: 20px; display: inline-block;"></div>
    <span>Tag</span><br>
    <div style="background-color: {host_color}; width: 20px; height: 20px; display: inline-block;"></div>
    <span>Host</span>
</div>
""".format(
            group_color=group_color, tag_color=tag_color, host_color=host_color
        )

        logging.debug("Appending legend to HTML file")
        with open(self.output_file, "a") as f:
            f.write(legend_html)
        logging.debug("Legend added successfully")