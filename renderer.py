import logging
from typing import List, Tuple

from pyvis.network import Network

from network_graph import NetworkGraph
from config import VISUALIZATION_CONFIG, NODE_COLORS
from services import RendererInterface


class Renderer(RendererInterface):
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
        for node, color, tooltip_text, shape in self.network_graph.nodes:
            self.net.add_node(node, color=color, title=tooltip_text, shape=shape)
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
        """
        Add a comprehensive legend to the HTML visualization.

        Includes both color coding for node types and shape coding for rule types:
        - Colors: Yellow (groups), Green (tags), Red (hosts)
        - Shapes: Dot (ACL-only), Triangle (Grant-only), Hexagon (both ACL and Grant)
        """
        logging.debug("Creating legend HTML")
        group_color = NODE_COLORS["group"]
        tag_color = NODE_COLORS["tag"]
        host_color = NODE_COLORS["host"]

        legend_html = """
<div style="position: absolute; top: 10px; right: 10px; background-color: #f5f5f5; padding: 15px; border: 1px solid #ccc; border-radius: 5px; font-family: Arial, sans-serif; font-size: 12px; max-width: 250px;">
    <h3 style="margin-top: 0; margin-bottom: 10px; font-size: 14px;">Legend</h3>

    <div style="margin-bottom: 15px;">
        <h4 style="margin: 0 0 8px 0; font-size: 12px; font-weight: bold;">Node Types (Colors)</h4>
        <div style="margin-bottom: 5px;">
            <div style="background-color: {group_color}; width: 20px; height: 20px; display: inline-block; margin-right: 8px; border: 1px solid #999;"></div>
            <span>Groups</span>
        </div>
        <div style="margin-bottom: 5px;">
            <div style="background-color: {tag_color}; width: 20px; height: 20px; display: inline-block; margin-right: 8px; border: 1px solid #999;"></div>
            <span>Tags</span>
        </div>
        <div style="margin-bottom: 5px;">
            <div style="background-color: {host_color}; width: 20px; height: 20px; display: inline-block; margin-right: 8px; border: 1px solid #999;"></div>
            <span>Hosts</span>
        </div>
    </div>

    <div>
        <h4 style="margin: 0 0 8px 0; font-size: 12px; font-weight: bold;">Rule Types (Shapes)</h4>
        <div style="margin-bottom: 5px;">
            <span style="font-size: 16px; margin-right: 8px;">●</span>
            <span>ACL rules only</span>
        </div>
        <div style="margin-bottom: 5px;">
            <span style="font-size: 16px; margin-right: 8px;">▲</span>
            <span>Grant rules only</span>
        </div>
        <div style="margin-bottom: 5px;">
            <span style="font-size: 16px; margin-right: 8px;">⬢</span>
            <span>Both ACL and Grant rules</span>
        </div>
    </div>
</div>
""".format(
            group_color=group_color, tag_color=tag_color, host_color=host_color
        )

        logging.debug("Appending legend to HTML file")
        with open(self.output_file, "a") as f:
            f.write(legend_html)
        logging.debug("Legend added successfully")