from typing import Dict, List, Set, Tuple, Union

from config import COMPANY_DOMAIN


class NetworkGraph:
    def __init__(self, hosts: Dict[str, str], groups: Dict[str, List[str]]):
        self.hosts = hosts
        self.groups = groups
        self.nodes: Set[Tuple[str, str, str]] = set()
        self.edges: List[Tuple[str, str]] = []

    def add_node(self, node: str, color: str, tooltip_text: str) -> None:
        self.nodes.add((node, color, tooltip_text))

    def add_edge(self, src: str, dst: str) -> None:
        self.edges.append((src, dst))

    def build_graph(self, acls: List[Dict[str, List[str]]], grants: List[Dict[str, List[str]]] = None) -> None:
        if grants is None:
            grants = []
            
        # Process legacy ACLs
        for rule in acls:
            src_nodes = self._resolve_nodes(rule["src"])
            dst_nodes = self._resolve_nodes(rule["dst"])

            for src in src_nodes:
                src_tooltip = self._get_node_tooltip(src)
                self.add_node(src, self._get_node_color(src), src_tooltip)

            for dst in dst_nodes:
                dst_tooltip = self._get_node_tooltip(dst)
                self.add_node(dst, self._get_node_color(dst), dst_tooltip)

            for src in src_nodes:
                for dst in dst_nodes:
                    self.add_edge(src, dst)
        
        # Process modern grants
        for grant in grants:
            src_nodes = self._resolve_nodes(grant["src"])
            dst_nodes = self._resolve_grant_destinations(grant)

            for src in src_nodes:
                src_tooltip = self._get_grant_src_tooltip(src, grant)
                self.add_node(src, self._get_node_color(src), src_tooltip)

            for dst in dst_nodes:
                dst_tooltip = self._get_grant_dst_tooltip(dst, grant)
                self.add_node(dst, self._get_node_color(dst), dst_tooltip)

            for src in src_nodes:
                for dst in dst_nodes:
                    self.add_edge(src, dst)

    def _resolve_nodes(self, nodes: List[str]) -> Set[str]:
        resolved_nodes: Set[str] = set()
        for node in nodes:
            resolved_nodes.add(node)
            # if node.startswith("tag:"):
            #     resolved_nodes.add(node)
            # elif node.startswith("autogroup:"):
            #     resolved_nodes.add(node)
            # elif node.startswith("group:"):
            #     resolved_nodes.add(node)
            # else:
            #     resolved_nodes.add(node.split(":")[0])
        return resolved_nodes

    def _get_node_color(self, node: str) -> str:
        if node.startswith("tag:"):
            return "#00cc66"  # Green for tags
        elif COMPANY_DOMAIN in node or node.startswith("autogroup:") or node.startswith("group:"):
            return "#FFFF00"  # Yellow for groups
        else:
            return "#ff6666"  # Red for hosts

    def _resolve_grant_destinations(self, grant: Dict[str, Union[str, List[str]]]) -> Set[str]:
        dst_nodes = self._resolve_nodes(grant["dst"])
        
        # Handle IP protocol specifications
        if "ip" in grant and grant["ip"] != ["*"]:
            enhanced_dst_nodes = set()
            for dst in dst_nodes:
                for ip_spec in grant["ip"]:
                    if ":" in ip_spec:  # Port specification like "tcp:443"
                        enhanced_dst_nodes.add(f"{dst}:{ip_spec}")
                    else:  # Protocol specification like "tcp"
                        enhanced_dst_nodes.add(f"{dst}:{ip_spec}")
            return enhanced_dst_nodes
        
        return dst_nodes

    def _get_grant_src_tooltip(self, node: str, grant: Dict[str, Union[str, List[str]]]) -> str:
        base_tooltip = self._get_node_tooltip(node)
        
        # Add posture check information if present
        if "srcPosture" in grant:
            posture_info = ", ".join(grant["srcPosture"])
            base_tooltip += f" | Posture: {posture_info}"
        
        return base_tooltip

    def _get_grant_dst_tooltip(self, node: str, grant: Dict[str, Union[str, List[str]]]) -> str:
        base_tooltip = self._get_node_tooltip(node)
        
        # Add IP protocol information if present
        if "ip" in grant and grant["ip"] != ["*"]:
            ip_info = ", ".join(grant["ip"])
            base_tooltip += f" | Protocols: {ip_info}"
        
        # Add via routing information if present
        if "via" in grant:
            via_info = ", ".join(grant["via"])
            base_tooltip += f" | Via: {via_info}"
        
        # Add app information if present
        if "app" in grant:
            app_info = ", ".join(grant["app"]) if isinstance(grant["app"], list) else grant["app"]
            base_tooltip += f" | App: {app_info}"
        
        return base_tooltip

    def _get_node_tooltip(self, node: str) -> str:
        if node.split(":")[0] in self.hosts:
            # Return IP address of host
            return self.hosts[node.split(":")[0]]
        elif node in self.groups:
            # Return group members of the group
            group_members = ", ".join(self.groups[node])
            return f"Group Members: {group_members}"
        elif node.startswith("autogroup:"):
            return node
        else:
            return node