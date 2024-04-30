from typing import List, Tuple

from pyvis.network import Network

from network_graph import NetworkGraph


class Renderer:
    def __init__(self, network_graph: NetworkGraph):
        self.network_graph = network_graph
        self.net = Network(
            height="800px",
            width="100%",
            notebook=True,
            directed=True,
            filter_menu=True,
            select_menu=True,
            neighborhood_highlight=True,
            cdn_resources="remote",
        )

    def render_to_html(self, output_file: str) -> None:
        for node, color, tooltip_text in self.network_graph.nodes:
            self.net.add_node(node, color=color, title=tooltip_text)

        for src, dst in self.network_graph.edges:
            self.net.add_edge(src, dst, arrows={"to": {"enabled": True}})

        self._add_legend()
        self.net.show_buttons()
        self.net.write_html(output_file)

    def _add_legend(self) -> None:
        group_color = "#FFFF00"
        tag_color = "#00cc66"
        host_color = "#ff6666"

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

        with open("network_topology.html", "a") as f:
            f.write(legend_html)