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
    
    def __init__(self, hosts: Dict[str, str], groups: Dict[str, List[str]], rule_line_numbers: Dict[str, List[int]] = None) -> None:
        """
        Initialize the network graph builder.

        Args:
            hosts: Mapping of host names to IP addresses
            groups: Mapping of group names to member lists
            rule_line_numbers: Optional mapping of rule types to line numbers
        """
        self.hosts = hosts
        self.groups = groups
        self.rule_line_numbers = rule_line_numbers or {'acls': [], 'grants': []}
        self.nodes: Set[Tuple[str, str, str, str]] = set()  # (node_id, color, tooltip, shape)
        self.edges: List[Tuple[str, str]] = []  # (source, destination)
        # Store searchable metadata for enhanced search functionality
        self.node_metadata: Dict[str, Dict[str, Union[str, List[str]]]] = {}  # node_id -> metadata
        self.edge_metadata: Dict[Tuple[str, str], Dict[str, Union[str, List[str]]]] = {}  # edge -> metadata
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

        # Update shapes for mixed nodes (comprehensive tooltips will handle the mixed indication)
        for node_id in mixed_nodes:
            # Update the base node if it exists
            if node_id in all_nodes:
                color, tooltip, _ = all_nodes[node_id]
                all_nodes[node_id] = (color, tooltip, "hexagon")
                logging.debug(f"Updated node {node_id} to hexagon shape for mixed ACL/Grant usage")

            # Also update any enhanced versions of this node (with protocol specifications)
            for enhanced_node_id in list(all_nodes.keys()):
                if enhanced_node_id.startswith(f"{node_id} [") and enhanced_node_id.endswith("]"):
                    color, tooltip, _ = all_nodes[enhanced_node_id]
                    all_nodes[enhanced_node_id] = (color, tooltip, "hexagon")
                    logging.debug(f"Updated enhanced node {enhanced_node_id} to hexagon shape for mixed ACL/Grant usage")

        # Update all tooltips with comprehensive information now that metadata is complete
        self._update_comprehensive_tooltips(all_nodes)

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

            # Store searchable metadata for nodes
            for src in src_nodes:
                if src not in all_nodes:
                    all_nodes[src] = (
                        self._get_node_color(src),
                        self._get_node_tooltip(src),
                        "dot"
                    )
                # Store searchable metadata
                if src not in self.node_metadata:
                    self.node_metadata[src] = {
                        "node_id": src,
                        "rule_type": "ACL",
                        "src_rules": [],
                        "dst_rules": [],
                        "protocols": [],
                        "via": [],
                        "posture": [],
                        "apps": [],
                        "members": self._get_node_members(src)
                    }
                # Add line number if available
                line_info = ""
                if self.rule_line_numbers and i < len(self.rule_line_numbers.get('acls', [])):
                    line_num = self.rule_line_numbers['acls'][i]
                    line_info = f" (Ln {line_num})"
                self.node_metadata[src]["src_rules"].append(f"ACL rule {i+1}{line_info}")

            for dst in dst_nodes:
                if dst not in all_nodes:
                    all_nodes[dst] = (
                        self._get_node_color(dst),
                        self._get_node_tooltip(dst),
                        "dot"
                    )
                # Store searchable metadata
                if dst not in self.node_metadata:
                    self.node_metadata[dst] = {
                        "node_id": dst,
                        "rule_type": "ACL",
                        "src_rules": [],
                        "dst_rules": [],
                        "protocols": [],
                        "via": [],
                        "posture": [],
                        "apps": [],
                        "members": self._get_node_members(dst)
                    }
                # Add line number if available
                line_info = ""
                if self.rule_line_numbers and i < len(self.rule_line_numbers.get('acls', [])):
                    line_num = self.rule_line_numbers['acls'][i]
                    line_info = f" (Ln {line_num})"
                self.node_metadata[dst]["dst_rules"].append(f"ACL rule {i+1}{line_info}")

            # Store edge metadata and create edges
            for src in src_nodes:
                for dst in dst_nodes:
                    edge = (src, dst)
                    edges.add(edge)
                    # Store searchable edge metadata
                    self.edge_metadata[edge] = {
                        "src": src,
                        "dst": dst,
                        "rule_type": "ACL",
                        "rule_index": i + 1,
                        "action": rule.get("action", "accept"),
                        "protocols": [],
                        "via": [],
                        "posture": [],
                        "apps": []
                    }

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

            # Extract grant metadata for searching
            protocols = grant.get("ip", [])
            via_routes = grant.get("via", [])
            src_posture = grant.get("srcPosture", [])
            dst_posture = grant.get("dstPosture", [])
            apps = []
            if "app" in grant:
                app_field = grant["app"]
                if isinstance(app_field, dict):
                    # New object format: {"domain/capability": [{}]}
                    apps = list(app_field.keys())
                elif isinstance(app_field, list):
                    # Legacy array format: ["capability"]
                    apps = app_field
                elif isinstance(app_field, str):
                    # Single string format
                    apps = [app_field]

            # Store searchable metadata for source nodes
            for src in src_nodes:
                if src not in all_nodes:
                    all_nodes[src] = (
                        self._get_node_color(src),
                        self._get_grant_src_tooltip(src, grant),
                        "triangle"
                    )
                # Store/update searchable metadata
                if src not in self.node_metadata:
                    self.node_metadata[src] = {
                        "node_id": src,
                        "rule_type": "Grant",
                        "src_rules": [],
                        "dst_rules": [],
                        "protocols": [],
                        "via": [],
                        "posture": [],
                        "apps": [],
                        "members": self._get_node_members(src)
                    }
                elif self.node_metadata[src]["rule_type"] == "ACL":
                    self.node_metadata[src]["rule_type"] = "Mixed"

                # Add line number if available
                line_info = ""
                if self.rule_line_numbers and i < len(self.rule_line_numbers.get('grants', [])):
                    line_num = self.rule_line_numbers['grants'][i]
                    line_info = f" (Ln {line_num})"
                self.node_metadata[src]["src_rules"].append(f"Grant rule {i+1}{line_info}")
                self.node_metadata[src]["protocols"].extend(protocols)
                self.node_metadata[src]["via"].extend(via_routes)
                self.node_metadata[src]["posture"].extend(src_posture)
                self.node_metadata[src]["apps"].extend(apps)

            # Store searchable metadata for destination nodes
            for dst in dst_nodes:
                if dst not in all_nodes:
                    all_nodes[dst] = (
                        self._get_node_color(dst),
                        self._get_grant_dst_tooltip(dst, grant),
                        "triangle"
                    )
                # Store/update searchable metadata
                base_dst = dst.split(" [")[0] if " [" in dst and dst.endswith("]") else dst
                if base_dst not in self.node_metadata:
                    self.node_metadata[base_dst] = {
                        "node_id": base_dst,
                        "rule_type": "Grant",
                        "src_rules": [],
                        "dst_rules": [],
                        "protocols": [],
                        "via": [],
                        "posture": [],
                        "apps": [],
                        "members": self._get_node_members(base_dst)
                    }
                elif self.node_metadata[base_dst]["rule_type"] == "ACL":
                    self.node_metadata[base_dst]["rule_type"] = "Mixed"

                # Add line number if available
                line_info = ""
                if self.rule_line_numbers and i < len(self.rule_line_numbers.get('grants', [])):
                    line_num = self.rule_line_numbers['grants'][i]
                    line_info = f" (Ln {line_num})"
                self.node_metadata[base_dst]["dst_rules"].append(f"Grant rule {i+1}{line_info}")
                self.node_metadata[base_dst]["protocols"].extend(protocols)
                self.node_metadata[base_dst]["via"].extend(via_routes)
                self.node_metadata[base_dst]["posture"].extend(dst_posture)
                self.node_metadata[base_dst]["apps"].extend(apps)

            # Store edge metadata and create edges
            for src in src_nodes:
                for dst in dst_nodes:
                    edge = (src, dst)
                    edges.add(edge)
                    # Store searchable edge metadata
                    self.edge_metadata[edge] = {
                        "src": src,
                        "dst": dst,
                        "rule_type": "Grant",
                        "rule_index": i + 1,
                        "protocols": protocols,
                        "via": via_routes,
                        "posture": src_posture + dst_posture,
                        "apps": apps
                    }

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

    def _get_node_members(self, node: str) -> List[str]:
        """
        Get the member list for a node if it's a group.

        Args:
            node: The node identifier

        Returns:
            List of group members if the node is a group, empty list otherwise
        """
        if node in self.groups:
            return self.groups[node]
        else:
            return []

    def _get_comprehensive_tooltip(self, node: str) -> str:
        """
        Generate comprehensive tooltip with all available metadata.

        Args:
            node: The node identifier

        Returns:
            Comprehensive tooltip showing all rule information with ACL/Grant differentiation
        """
        # Start with basic node information
        tooltip_lines = []

        # Add basic node information
        basic_info = self._get_node_tooltip(node)
        tooltip_lines.append(f"{node}")

        # Add node-specific details (IP, host info, etc.) - but not group members (handled in metadata section)
        if basic_info != node and not node in self.groups:  # Only add if it's different from the node name and not a group
            tooltip_lines.append(f"ℹ️  {basic_info}")


        # Get comprehensive metadata if available
        if node in self.node_metadata:
            metadata = self.node_metadata[node]

            # Add rule type information with appropriate emoji
            rule_type = metadata.get("rule_type", "Unknown")
            if rule_type == "ACL":
                tooltip_lines.append("🔒 Legacy ACL Rules")
            elif rule_type == "Grant":
                tooltip_lines.append("🎯 Modern Grant Rules")
            elif rule_type == "Mixed":
                tooltip_lines.append("🔄 Mixed (ACL + Grant Rules)")

            # Add rule references with clear categorization
            src_rules = metadata.get("src_rules", [])
            dst_rules = metadata.get("dst_rules", [])

            if src_rules or dst_rules:
                tooltip_lines.append("📋 Rule References:")
                if src_rules:
                    tooltip_lines.append(f"  • Source: {', '.join(src_rules)}")
                if dst_rules:
                    tooltip_lines.append(f"  • Destination: {', '.join(dst_rules)}")

            # Add protocol information
            protocols = metadata.get("protocols", [])
            if protocols:
                unique_protocols = list(set(protocols))  # Remove duplicates
                if unique_protocols and unique_protocols != ["*"]:  # Don't show wildcard protocols
                    tooltip_lines.append(f"🌐 Protocols: {', '.join(unique_protocols)}")

            # Add via routing information
            via_routes = metadata.get("via", [])
            if via_routes:
                unique_via = list(set(via_routes))  # Remove duplicates
                tooltip_lines.append(f"🛤️  Via Routes: {', '.join(unique_via)}")

            # Add posture check information
            posture_checks = metadata.get("posture", [])
            if posture_checks:
                unique_posture = list(set(posture_checks))  # Remove duplicates
                tooltip_lines.append(f"🔐 Posture Checks: {', '.join(unique_posture)}")

            # Add application information
            apps = metadata.get("apps", [])
            if apps:
                unique_apps = list(set(apps))  # Remove duplicates
                tooltip_lines.append(f"📱 Applications: {', '.join(unique_apps)}")

            # Add group member information if available
            members = metadata.get("members", [])
            if members:
                # Limit displayed members to avoid overly long tooltips
                if len(members) <= 5:
                    tooltip_lines.append(f"👥 Group Members: {', '.join(members)}")
                else:
                    tooltip_lines.append(f"👥 Group Members: {', '.join(members[:3])}, ... (+{len(members)-3} more)")

        # If this is a group but no metadata was available, still show group members
        elif node in self.groups:
            group_members = ", ".join(self.groups[node])
            if len(self.groups[node]) <= 5:
                tooltip_lines.append(f"👥 Group Members: {group_members}")
            else:
                tooltip_lines.append(f"👥 Group Members: {', '.join(self.groups[node][:3])}, ... (+{len(self.groups[node])-3} more)")

        return "\n".join(tooltip_lines)

    def _update_comprehensive_tooltips(self, all_nodes: Dict[str, Tuple[str, str, str]]) -> None:
        """
        Update all node tooltips with comprehensive information after metadata collection.

        Args:
            all_nodes: Dictionary of node_id -> (color, tooltip, shape) to update
        """
        for node_id in all_nodes.keys():
            color, _, shape = all_nodes[node_id]
            # Generate comprehensive tooltip using collected metadata
            comprehensive_tooltip = self._get_comprehensive_tooltip(node_id)
            # Update the node tuple with the new tooltip
            all_nodes[node_id] = (color, comprehensive_tooltip, shape)
            logging.debug(f"Updated comprehensive tooltip for node: {node_id}")

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
        """
        Generate comprehensive tooltip for grant source nodes.

        Args:
            node: The node identifier
            grant: The grant rule dictionary

        Returns:
            Comprehensive tooltip with all available metadata, or basic tooltip with grant info if metadata not available
        """
        # If metadata is available, use comprehensive tooltip
        if node in self.node_metadata:
            return self._get_comprehensive_tooltip(node)

        # Fallback to basic tooltip with grant information (for backward compatibility)
        base_tooltip = self._get_node_tooltip(node)

        # Add posture check information if present
        if "srcPosture" in grant:
            posture_info = ", ".join(grant["srcPosture"])
            base_tooltip += f"\nPosture: {posture_info}"

        return base_tooltip

    def _get_grant_dst_tooltip(self, node: str, grant: Dict[str, Union[str, List[str]]]) -> str:
        """
        Generate comprehensive tooltip for grant destination nodes.

        Args:
            node: The node identifier (may include protocol enhancement)
            grant: The grant rule dictionary

        Returns:
            Comprehensive tooltip with all available metadata, or basic tooltip with grant info if metadata not available
        """
        # Extract base node ID for metadata lookup
        base_node = node.split(" [")[0] if " [" in node and node.endswith("]") else node

        # If metadata is available, use comprehensive tooltip
        if base_node in self.node_metadata:
            return self._get_comprehensive_tooltip(base_node)

        # Fallback to basic tooltip with grant information (for backward compatibility)
        base_tooltip = self._get_node_tooltip(base_node)

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
            app_field = grant["app"]
            if isinstance(app_field, dict):
                # New object format: {"domain/capability": [{}]}
                app_info = ", ".join(app_field.keys())
            elif isinstance(app_field, list):
                # Legacy array format: ["capability"]
                app_info = ", ".join(app_field)
            else:
                # Single string format
                app_info = str(app_field)
            base_tooltip += f"\nApp: {app_info}"

        # Add destination posture check information if present
        if "dstPosture" in grant:
            posture_info = ", ".join(grant["dstPosture"])
            base_tooltip += f"\nPosture: {posture_info}"

        return base_tooltip

    def get_search_metadata(self) -> Dict[str, Dict[str, Union[str, List[str]]]]:
        """
        Get searchable metadata for all nodes and edges.

        Returns:
            Dictionary containing searchable metadata for enhanced search functionality
        """
        return {
            "nodes": self.node_metadata,
            "edges": {f"{edge[0]}->{edge[1]}": metadata for edge, metadata in self.edge_metadata.items()}
        }

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