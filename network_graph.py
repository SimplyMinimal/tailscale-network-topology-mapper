import logging
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Union, DefaultDict

from config import COMPANY_DOMAIN, NODE_COLORS
from services import NetworkGraphInterface


class NetworkGraph(NetworkGraphInterface):
    """
    Builds a network graph from Tailscale policy rules (ACLs and grants).
    
    Creates nodes and edges representing network access relationships,
    with support for modern grant features like IP protocols, via routing,
    posture checks, and application-specific access controls.
    """
    
    def __init__(self, hosts: Dict[str, str], groups: Dict[str, List[str]]) -> None:
        """
        Initialize the network graph builder.
        
        Args:
            hosts: Mapping of host names to IP addresses
            groups: Mapping of group names to member lists
        """
        self.hosts = hosts
        self.groups = groups
        self.nodes: Set[Tuple[str, str, str, str]] = set()  # (node_id, color, tooltip, shape)
        self.edges: List[Tuple[str, str]] = []  # (source, destination)
        logging.debug(f"NetworkGraph initialized with {len(hosts)} hosts and {len(groups)} groups")

    def add_node(self, node: str, color: str, tooltip_text: str, shape: str = "dot") -> None:
        """Add a node to the graph with specified color, tooltip, and shape."""
        self.nodes.add((node, color, tooltip_text, shape))
        logging.debug(f"Added node: {node} (color: {color}, shape: {shape})")

    def add_edge(self, src: str, dst: str) -> None:
        """Add a directed edge from source to destination node."""
        self.edges.append((src, dst))
        logging.debug(f"Added edge: {src} -> {dst}")

    def build_graph(self, acls: List[Dict[str, List[str]]], grants: List[Dict[str, Union[str, List[str]]]] = None) -> None:
        """
        Build the network graph from ACL rules and grant rules with optimized performance.

        Tracks which nodes appear in ACLs vs grants to assign appropriate shapes:
        - Dot (●) for ACL-only nodes
        - Triangle (▲) for Grant-only nodes
        - Hexagon (⬢) for nodes referenced in both ACL and Grant rules

        Args:
            acls: List of legacy ACL rules with src/dst fields
            grants: List of modern grant rules with extended features (optional)
        """
        if grants is None:
            grants = []

        logging.debug(f"Building graph from {len(acls)} ACLs and {len(grants)} grants")

        # Batch collections for efficient processing
        all_nodes: Dict[str, Tuple[str, str, str]] = {}  # node_id -> (color, tooltip, shape)
        all_edges: Set[Tuple[str, str]] = set()  # Deduplicated edges

        # Track which nodes appear in ACLs vs grants for shape assignment
        acl_nodes: Set[str] = set()
        grant_nodes: Set[str] = set()

        # Process legacy ACLs in batch
        logging.debug("Processing legacy ACL rules")
        acl_edges = self._process_acls_batch(acls, all_nodes, acl_nodes)
        all_edges.update(acl_edges)

        # Process modern grants in batch
        logging.debug("Processing modern grant rules")
        grant_edges = self._process_grants_batch(grants, all_nodes, grant_nodes)
        all_edges.update(grant_edges)

        # Identify nodes that appear in both ACLs and grants for hexagon shape
        mixed_nodes = acl_nodes.intersection(grant_nodes)
        logging.debug(f"Found {len(mixed_nodes)} nodes referenced in both ACL and Grant rules: {mixed_nodes}")

        # Update shapes and tooltips for mixed nodes (including enhanced versions)
        for node_id in mixed_nodes:
            # Update the base node if it exists
            if node_id in all_nodes:
                color, tooltip, _ = all_nodes[node_id]
                # Enhance tooltip to indicate mixed usage
                enhanced_tooltip = f"{tooltip} (Referenced in both ACL and Grant rules)"
                all_nodes[node_id] = (color, enhanced_tooltip, "hexagon")
                logging.debug(f"Updated node {node_id} to hexagon shape for mixed ACL/Grant usage")

            # Also update any enhanced versions of this node (with protocol specifications)
            for enhanced_node_id in list(all_nodes.keys()):
                if enhanced_node_id.startswith(f"{node_id} [") and enhanced_node_id.endswith("]"):
                    color, tooltip, _ = all_nodes[enhanced_node_id]
                    # Enhance tooltip to indicate mixed usage
                    enhanced_tooltip = f"{tooltip} (Referenced in both ACL and Grant rules)"
                    all_nodes[enhanced_node_id] = (color, enhanced_tooltip, "hexagon")
                    logging.debug(f"Updated enhanced node {enhanced_node_id} to hexagon shape for mixed ACL/Grant usage")

        # Batch add all nodes and edges
        for node_id, (color, tooltip, shape) in all_nodes.items():
            self.nodes.add((node_id, color, tooltip, shape))

        self.edges.extend(list(all_edges))

        logging.debug(f"Graph building completed: {len(self.nodes)} nodes, {len(self.edges)} edges")
        logging.debug(f"Node distribution - ACL-only: {len(acl_nodes - grant_nodes)}, Grant-only: {len(grant_nodes - acl_nodes)}, Mixed: {len(mixed_nodes)}")

    def _process_acls_batch(self, acls: List[Dict], all_nodes: Dict[str, Tuple[str, str, str]], acl_nodes: Set[str]) -> Set[Tuple[str, str]]:
        """
        Process ACL rules in batch for better performance.

        Args:
            acls: List of ACL rule dictionaries
            all_nodes: Dictionary to store node information
            acl_nodes: Set to track nodes that appear in ACL rules

        Returns:
            Set of edges created from ACL rules
        """
        edges: Set[Tuple[str, str]] = set()

        for i, rule in enumerate(acls):
            logging.debug(f"Processing ACL rule {i+1}")

            src_nodes = self._resolve_nodes(rule["src"])
            dst_nodes = self._resolve_nodes(rule["dst"])

            # Track all nodes that appear in ACL rules
            acl_nodes.update(src_nodes)
            acl_nodes.update(dst_nodes)

            # Batch node creation
            for src in src_nodes:
                if src not in all_nodes:
                    all_nodes[src] = (
                        self._get_node_color(src),
                        self._get_node_tooltip(src),
                        "dot"
                    )

            for dst in dst_nodes:
                if dst not in all_nodes:
                    all_nodes[dst] = (
                        self._get_node_color(dst),
                        self._get_node_tooltip(dst),
                        "dot"
                    )

            # Batch edge creation using set comprehension
            rule_edges = {(src, dst) for src in src_nodes for dst in dst_nodes}
            edges.update(rule_edges)

        return edges

    def _process_grants_batch(self, grants: List[Dict], all_nodes: Dict[str, Tuple[str, str, str]], grant_nodes: Set[str]) -> Set[Tuple[str, str]]:
        """
        Process grant rules in batch for better performance.

        Args:
            grants: List of grant rule dictionaries
            all_nodes: Dictionary to store node information
            grant_nodes: Set to track nodes that appear in grant rules

        Returns:
            Set of edges created from grant rules
        """
        edges: Set[Tuple[str, str]] = set()

        for i, grant in enumerate(grants):
            logging.debug(f"Processing grant rule {i+1}")

            src_nodes = self._resolve_nodes(grant["src"])
            dst_nodes = self._resolve_grant_destinations(grant)

            # Track base node IDs (without protocol enhancements) for intersection logic
            grant_nodes.update(src_nodes)
            # For destination nodes, extract base node IDs by removing protocol enhancements
            base_dst_nodes = set()
            for dst in dst_nodes:
                # Extract base node ID by removing protocol enhancement (e.g., "node [tcp:443]" -> "node")
                if " [" in dst and dst.endswith("]"):
                    base_node = dst.split(" [")[0]
                    base_dst_nodes.add(base_node)
                else:
                    base_dst_nodes.add(dst)
            grant_nodes.update(base_dst_nodes)

            # Batch node creation
            for src in src_nodes:
                if src not in all_nodes:
                    all_nodes[src] = (
                        self._get_node_color(src),
                        self._get_grant_src_tooltip(src, grant),
                        "triangle"
                    )

            for dst in dst_nodes:
                if dst not in all_nodes:
                    all_nodes[dst] = (
                        self._get_node_color(dst),
                        self._get_grant_dst_tooltip(dst, grant),
                        "triangle"
                    )

            # Batch edge creation using set comprehension
            rule_edges = {(src, dst) for src in src_nodes for dst in dst_nodes}
            edges.update(rule_edges)

        return edges

    def _resolve_nodes(self, nodes: List[str]) -> Set[str]:
        logging.debug(f"Resolving nodes: {nodes}")
        resolved_nodes: Set[str] = set()
        for node in nodes:
            resolved_nodes.add(node)
            logging.debug(f"Resolved node: {node}")
        logging.debug(f"Total resolved nodes: {len(resolved_nodes)}")
        return resolved_nodes

    def _get_node_color(self, node: str) -> str:
        """Determine the color for a node based on its type."""
        if node.startswith("tag:"):
            return NODE_COLORS["tag"]
        elif COMPANY_DOMAIN in node or node.startswith("autogroup:") or node.startswith("group:"):
            return NODE_COLORS["group"]
        else:
            return NODE_COLORS["host"]

    def _resolve_grant_destinations(self, grant: Dict[str, Union[str, List[str]]]) -> Set[str]:
        logging.debug(f"Resolving grant destinations for: {grant}")
        dst_nodes = self._resolve_nodes(grant["dst"])
        
        # Handle IP protocol specifications
        if "ip" in grant and grant["ip"] != ["*"]:
            logging.debug(f"Processing IP specifications: {grant['ip']}")
            enhanced_dst_nodes = set()
            for dst in dst_nodes:
                # Format protocols more readably
                ip_specs = []
                current_proto = None
                ports = []
                
                for spec in grant["ip"]:
                    if ":" in spec:
                        proto, port = spec.split(":", 1)
                        if proto != current_proto:
                            if current_proto and ports:
                                ip_specs.append(f"{current_proto}:{','.join(ports)}")
                                ports = []
                            current_proto = proto
                        ports.append(port)
                    else:
                        if current_proto and ports:
                            ip_specs.append(f"{current_proto}:{','.join(ports)}")
                        ip_specs.append(spec)
                        current_proto = None
                        ports = []
                
                if current_proto and ports:
                    ip_specs.append(f"{current_proto}:{','.join(ports)}")
                
                # Create enhanced node with consolidated protocols
                enhanced_node = f"{dst} [{', '.join(ip_specs)}]"
                enhanced_dst_nodes.add(enhanced_node)
                logging.debug(f"Enhanced destination with protocols: {enhanced_node}")
            logging.debug(f"Grant destinations enhanced to: {enhanced_dst_nodes}")
            return enhanced_dst_nodes
        
        logging.debug(f"Grant destinations (no IP enhancement): {dst_nodes}")
        return dst_nodes

    def _get_grant_src_tooltip(self, node: str, grant: Dict[str, Union[str, List[str]]]) -> str:
        base_tooltip = self._get_node_tooltip(node)
        
        # Add posture check information if present
        if "srcPosture" in grant:
            posture_info = ", ".join(grant["srcPosture"])
            base_tooltip += f"\nPosture: {posture_info}"
        
        return base_tooltip

    def _get_grant_dst_tooltip(self, node: str, grant: Dict[str, Union[str, List[str]]]) -> str:
        base_tooltip = self._get_node_tooltip(node)
        
        # Add IP protocol information if present
        if "ip" in grant and grant["ip"] != ["*"]:
            ip_info = ", ".join(grant["ip"])
            base_tooltip += f"\nProtocols: {ip_info}"
        
        # Add via routing information if present
        if "via" in grant:
            via_info = ", ".join(grant["via"])
            base_tooltip += f"\nVia: {via_info}"
        
        # Add app information if present
        if "app" in grant:
            app_info = ", ".join(grant["app"]) if isinstance(grant["app"], list) else grant["app"]
            base_tooltip += f"\nApp: {app_info}"
        
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