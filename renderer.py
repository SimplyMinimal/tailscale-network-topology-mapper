import logging
import json
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
        # Note: show_buttons() disabled in favor of enhanced search interface
        # self.net.show_buttons()
        
        logging.debug(f"Writing HTML file: {output_file}")
        self.net.write_html(output_file)

        logging.debug("Adding enhanced search functionality")
        self._add_enhanced_search()

        logging.debug("Adding legend to HTML file")
        self._add_legend()

        logging.debug("HTML rendering completed")

    def _add_enhanced_search(self) -> None:
        """
        Add enhanced search functionality to the HTML visualization.

        Replaces the basic filter with a comprehensive keyword search that can search
        through node IDs, protocols, via routing, posture checks, and other metadata.
        """
        logging.debug("Creating enhanced search interface")

        # Get searchable metadata from the network graph
        search_metadata = self.network_graph.get_search_metadata()

        # Create the enhanced search HTML and JavaScript
        search_html = f"""
<script>
// Enhanced search metadata
const searchMetadata = {json.dumps(search_metadata)};

// Enhanced search functionality
let searchActive = false;
let originalNodeColors = {{}};

function initializeSearch() {{
    // Store original node colors
    const allNodes = nodes.get({{ returnType: "Object" }});
    for (let nodeId in allNodes) {{
        originalNodeColors[nodeId] = allNodes[nodeId].color;
    }}
}}

function performEnhancedSearch(searchTerm) {{
    if (!searchTerm || searchTerm.trim() === '') {{
        clearSearch();
        return;
    }}

    searchActive = true;
    const term = searchTerm.toLowerCase().trim();
    const allNodes = nodes.get({{ returnType: "Object" }});
    const matchingNodes = [];

    // Search through node metadata
    for (let nodeId in searchMetadata.nodes) {{
        const metadata = searchMetadata.nodes[nodeId];
        let matches = false;

        // Search in node ID
        if (nodeId.toLowerCase().includes(term)) {{
            matches = true;
        }}

        // Search in protocols
        if (metadata.protocols && metadata.protocols.some(p => p.toLowerCase().includes(term))) {{
            matches = true;
        }}

        // Search in via routing
        if (metadata.via && metadata.via.some(v => v.toLowerCase().includes(term))) {{
            matches = true;
        }}

        // Search in posture checks
        if (metadata.posture && metadata.posture.some(p => p.toLowerCase().includes(term))) {{
            matches = true;
        }}

        // Search in apps
        if (metadata.apps && metadata.apps.some(a => a.toLowerCase().includes(term))) {{
            matches = true;
        }}

        // Search in group members
        if (metadata.members && metadata.members.some(m => m.toLowerCase().includes(term))) {{
            matches = true;
        }}

        // Search in rule types
        if (metadata.rule_type && metadata.rule_type.toLowerCase().includes(term)) {{
            matches = true;
        }}

        if (matches) {{
            matchingNodes.push(nodeId);
        }}
    }}

    // Update node appearance
    for (let nodeId in allNodes) {{
        if (matchingNodes.includes(nodeId)) {{
            // Highlight matching nodes
            allNodes[nodeId].color = '#ff6b6b'; // Bright red for matches
            allNodes[nodeId].borderWidth = 4;
        }} else {{
            // Dim non-matching nodes
            allNodes[nodeId].color = 'rgba(200,200,200,0.3)';
            allNodes[nodeId].borderWidth = 1;
        }}
    }}

    // Update the visualization
    const updateArray = Object.values(allNodes);
    nodes.update(updateArray);

    // Update search results count
    document.getElementById('search-results-count').textContent =
        `Found ${{matchingNodes.length}} matching nodes`;
}}

function clearSearch() {{
    if (!searchActive) return;

    searchActive = false;
    const allNodes = nodes.get({{ returnType: "Object" }});

    // Restore original appearance
    for (let nodeId in allNodes) {{
        allNodes[nodeId].color = originalNodeColors[nodeId];
        allNodes[nodeId].borderWidth = 2;
    }}

    // Update the visualization
    const updateArray = Object.values(allNodes);
    nodes.update(updateArray);

    // Clear search results
    document.getElementById('search-results-count').textContent = '';
    document.getElementById('enhanced-search-input').value = '';
}}

// Drag functionality for the search container
let isDragging = false;
let dragOffset = {{ x: 0, y: 0 }};

function initializeDragFunctionality() {{
    const container = document.getElementById('enhanced-search-container');
    const dragHandle = document.getElementById('drag-handle');

    if (!container || !dragHandle) return;

    // Mouse down event on drag handle
    dragHandle.addEventListener('mousedown', function(e) {{
        isDragging = true;
        container.classList.add('dragging');

        const rect = container.getBoundingClientRect();
        dragOffset.x = e.clientX - rect.left;
        dragOffset.y = e.clientY - rect.top;

        // Prevent text selection during drag
        e.preventDefault();
        document.body.style.userSelect = 'none';
    }});

    // Mouse move event for dragging
    document.addEventListener('mousemove', function(e) {{
        if (!isDragging) return;

        e.preventDefault();

        // Calculate new position
        let newX = e.clientX - dragOffset.x;
        let newY = e.clientY - dragOffset.y;

        // Get viewport dimensions
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        const containerRect = container.getBoundingClientRect();

        // Apply boundary constraints
        newX = Math.max(0, Math.min(newX, viewportWidth - containerRect.width));
        newY = Math.max(0, Math.min(newY, viewportHeight - containerRect.height));

        // Update position
        container.style.left = newX + 'px';
        container.style.top = newY + 'px';
        container.style.bottom = 'auto'; // Remove bottom positioning when dragging
    }});

    // Mouse up event to stop dragging
    document.addEventListener('mouseup', function() {{
        if (isDragging) {{
            isDragging = false;
            container.classList.remove('dragging');
            document.body.style.userSelect = '';
        }}
    }});

    // Prevent dragging when clicking on input or buttons
    const searchInput = document.getElementById('enhanced-search-input');
    const searchButtons = container.querySelectorAll('.search-btn');

    [searchInput, ...searchButtons].forEach(element => {{
        if (element) {{
            element.addEventListener('mousedown', function(e) {{
                e.stopPropagation();
            }});
        }}
    }});
}}

// Initialize search when the network is ready
document.addEventListener('DOMContentLoaded', function() {{
    setTimeout(function() {{
        initializeSearch();
        initializeDragFunctionality();
    }}, 1000); // Wait for network to be fully loaded
}});
</script>

<style>
.enhanced-search-container {{
    position: fixed;
    bottom: 20px;
    left: 20px;
    background-color: #ffffff;
    padding: 15px;
    border: 2px solid #007bff;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    z-index: 1000;
    min-width: 300px;
    max-width: 400px;
    cursor: move;
    user-select: none;
}}

.enhanced-search-container.dragging {{
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
    transform: scale(1.02);
    transition: none;
    opacity: 0.9;
}}

.enhanced-search-container:not(.dragging) {{
    transition: all 0.2s ease;
}}

.enhanced-search-container .drag-handle {{
    cursor: move;
    padding: 5px;
    margin: -5px -5px 5px -5px;
    border-radius: 4px 4px 0 0;
    background: linear-gradient(90deg, #007bff, #0056b3);
    color: white;
    font-weight: bold;
    text-align: center;
    font-size: 12px;
}}

.search-input {{
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    margin-bottom: 8px;
}}

.search-input:focus {{
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 2px rgba(0,123,255,0.25);
}}

.search-controls {{
    display: flex;
    gap: 8px;
    margin-bottom: 8px;
}}

.search-btn {{
    padding: 6px 12px;
    border: 1px solid #007bff;
    background-color: #007bff;
    color: white;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
}}

.search-btn:hover {{
    background-color: #0056b3;
}}

.search-btn.secondary {{
    background-color: #6c757d;
    border-color: #6c757d;
}}

.search-btn.secondary:hover {{
    background-color: #545b62;
}}

.search-results {{
    font-size: 12px;
    color: #666;
    margin-top: 5px;
}}

.search-help {{
    font-size: 11px;
    color: #888;
    margin-top: 8px;
    line-height: 1.3;
}}
</style>

<div class="enhanced-search-container" id="enhanced-search-container">
    <div class="drag-handle" id="drag-handle">Search (Drag to Move)</div>

    <input type="text"
           id="enhanced-search-input"
           class="search-input"
           placeholder="Search nodes, protocols, via routes, posture..."
           onkeyup="if(event.key==='Enter') performEnhancedSearch(this.value); else if(this.value==='') clearSearch();"
           oninput="if(this.value==='') clearSearch();">

    <div class="search-controls">
        <button class="search-btn" onclick="performEnhancedSearch(document.getElementById('enhanced-search-input').value)">
            Search
        </button>
        <button class="search-btn secondary" onclick="clearSearch()">
            Clear
        </button>
    </div>

    <div id="search-results-count" class="search-results"></div>

    <div class="search-help">
        <strong>Search tips:</strong><br>
        • Node names: tag:prod, group:admin<br>
        • Group members: dev1, alice@example.com<br>
        • Protocols: tcp:443, udp:161<br>
        • Via routes: exit-node, api-gateway<br>
        • Posture: compliance, latest<br>
        • Rule types: ACL, Grant, Mixed
    </div>
</div>
"""

        # Insert the search functionality into the HTML file
        with open(self.output_file, "r") as f:
            content = f.read()

        # Insert before the closing body tag
        content = content.replace("</body>", f"{search_html}</body>")

        with open(self.output_file, "w") as f:
            f.write(content)

        logging.debug("Enhanced search functionality added successfully")

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