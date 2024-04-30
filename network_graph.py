from typing import Dict, List, Set, Tuple

from config import COMPANY_DOMAIN


class NetworkGraph:
    def __init__(self):
        self.nodes: Set[str] = set()
        self.edges: List[Tuple[str, str]] = []

    def add_node(self, node: str, color: str, tooltip_text: str) -> None:
        self.nodes.add((node, color, tooltip_text))

    def add_edge(self, src: str, dst: str) -> None:
        self.edges.append((src, dst))

    def build_graph(self, acls: List[Dict[str, List[str]]]) -> None:
        for rule in acls:
            src_nodes = self._resolve_nodes(rule["src"])
            dst_nodes = self._resolve_nodes(rule["dst"])

            for src in src_nodes:
                src_tooltip = f"Hello world: {src}"
                self.add_node(src, self._get_node_color(src), src_tooltip)

            for dst in dst_nodes:
                dst_tooltip = f"Hello world: {dst}"
                self.add_node(dst, self._get_node_color(dst), dst_tooltip)

            for src in src_nodes:
                for dst in dst_nodes:
                    self.add_edge(src, dst)

    def _resolve_nodes(self, nodes: List[str]) -> Set[str]:
        resolved_nodes: Set[str] = set()
        for node in nodes:
            if node.startswith("tag:"):
                resolved_nodes.add(node)
            elif node.startswith("autogroup:"):
                resolved_nodes.add(node)
            elif node.startswith("group:"):
                resolved_nodes.add(node)
            else:
                resolved_nodes.add(node.split(":")[0])
        return resolved_nodes

    def _get_node_color(self, node: str) -> str:
        if node.startswith("tag:"):
            return "#00cc66"  # Green for tags
        elif COMPANY_DOMAIN in node or node.startswith("autogroup:") or node.startswith("group:"):
            return "#FFFF00"  # Yellow for groups
        else:
            return "#ff6666"  # Red for hosts