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

        logging.debug("Improving zoom navigation experience")
        self._improve_zoom_controls()

        logging.debug("Adding legend to HTML file")
        self._add_legend()

        logging.debug("HTML rendering completed")

    def _improve_zoom_controls(self) -> None:
        """
        Improve zoom navigation experience by adding smoother zoom controls.

        Modifies the generated HTML to include better zoom configuration with
        smaller incremental steps for more precise navigation.
        """
        logging.debug("Improving zoom controls in HTML file")

        # Check if output file exists (might not exist in tests)
        import os
        if not os.path.exists(self.output_file):
            logging.debug(f"Output file {self.output_file} does not exist, skipping zoom improvement")
            return

        with open(self.output_file, "r") as f:
            content = f.read()

        # Find the interaction section in the options and add zoom configuration
        old_interaction = '''    "interaction": {
        "dragNodes": true,
        "hideEdgesOnDrag": false,
        "hideNodesOnDrag": false
    }'''

        new_interaction = '''    "interaction": {
        "dragNodes": true,
        "hideEdgesOnDrag": false,
        "hideNodesOnDrag": false,
        "zoomSpeed": 0.5,
        "zoomView": true
    }'''

        if old_interaction in content:
            content = content.replace(old_interaction, new_interaction)
            logging.debug("Found and replaced interaction section")
        else:
            logging.warning("Could not find interaction section to replace")
            logging.debug(f"Looking for: {repr(old_interaction)}")

        with open(self.output_file, "w") as f:
            f.write(content)

        # Verify the change was written
        with open(self.output_file, "r") as f:
            verify_content = f.read()
            if "zoomSpeed" in verify_content:
                logging.debug("Zoom settings successfully written to file")
            else:
                logging.warning("Zoom settings not found in written file")

        logging.debug("Zoom controls improved successfully")

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
let savedViewState = null; // Store zoom/pan state before search

function initializeSearch() {{
    // Store original node colors
    const allNodes = nodes.get({{ returnType: "Object" }});
    for (let nodeId in allNodes) {{
        originalNodeColors[nodeId] = allNodes[nodeId].color;
    }}
}}

function saveCurrentViewState() {{
    // Save current zoom and pan state before performing search
    try {{
        if (typeof network !== 'undefined' && network.getViewPosition && network.getScale) {{
            savedViewState = {{
                position: network.getViewPosition(),
                scale: network.getScale()
            }};
        }}
    }} catch (e) {{
        console.log('Could not save view state:', e);
        savedViewState = null;
    }}
}}

function restoreViewState() {{
    // Restore saved zoom and pan state or fit to view
    try {{
        if (typeof network !== 'undefined') {{
            if (savedViewState && network.moveTo) {{
                // Restore previous view state
                network.moveTo({{
                    position: savedViewState.position,
                    scale: savedViewState.scale,
                    animation: {{
                        duration: 1000,
                        easingFunction: 'easeInOutQuad'
                    }}
                }});
            }} else if (network.fit) {{
                // Fallback to fit to view
                network.fit({{
                    animation: {{
                        duration: 1000,
                        easingFunction: 'easeInOutQuad'
                    }}
                }});
            }}
        }}
    }} catch (e) {{
        console.log('Could not restore view state:', e);
    }}
}}

// Live search dropdown functionality
let searchDropdownTimeout;
let allSearchableNodes = [];

function initializeSearchableNodes() {{
    allSearchableNodes = [];
    for (let nodeId in searchMetadata.nodes) {{
        const metadata = searchMetadata.nodes[nodeId];
        allSearchableNodes.push({{
            id: nodeId,
            metadata: metadata,
            color: originalNodeColors[nodeId] || '#97C2FC',
            shape: getNodeShape(metadata)
        }});
    }}
}}

function getNodeShape(metadata) {{
    if (metadata.rule_type === 'Mixed') return '⬢';
    if (metadata.rule_type === 'Grant') return '▲';
    return '●';
}}

function handleSearchInput(searchTerm) {{
    if (searchTerm === '') {{
        clearSearch();
        hideSearchDropdown();
        showSearchTips();
    }} else {{
        hideSearchTips();
        updateSearchDropdown(searchTerm);
    }}
}}

function handleSearchKeyup(event, searchTerm) {{
    if (event.key === 'Enter') {{
        performEnhancedSearch(searchTerm);
        hideSearchDropdown();
    }} else if (searchTerm === '') {{
        clearSearch();
        hideSearchDropdown();
        showSearchTips();
    }}
}}

function updateSearchDropdown(searchTerm) {{
    if (!searchTerm || searchTerm.trim() === '') {{
        hideSearchDropdown();
        return;
    }}

    const term = searchTerm.toLowerCase().trim();
    const matchingNodes = [];

    // Search through all nodes
    for (let node of allSearchableNodes) {{
        const metadata = node.metadata;
        let matches = false;
        let matchDetails = [];

        // Search in node ID
        if (node.id.toLowerCase().includes(term)) {{
            matches = true;
            matchDetails.push('name');
        }}

        // Search in protocols
        if (metadata.protocols && metadata.protocols.length > 0) {{
            // If searching for "protocol" or "protocols", match any node that has protocols
            if (term === 'protocol' || term === 'protocols') {{
                matches = true;
                matchDetails.push('protocol');
            }} else if (metadata.protocols.some(p => p.toLowerCase().includes(term))) {{
                // Otherwise, search within the protocol values
                matches = true;
                matchDetails.push('protocol');
            }}
        }}

        // Search in via routing
        if (metadata.via && metadata.via.length > 0) {{
            // If searching for "via", match any node that has via routing
            if (term === 'via') {{
                matches = true;
                matchDetails.push('via');
            }} else if (metadata.via.some(v => v.toLowerCase().includes(term))) {{
                // Otherwise, search within the via route values
                matches = true;
                matchDetails.push('via');
            }}
        }}

        // Search in posture checks
        if (metadata.posture && metadata.posture.length > 0) {{
            // If searching for "posture", match any node that has posture checks
            if (term === 'posture') {{
                matches = true;
                matchDetails.push('posture');
            }} else if (metadata.posture.some(p => p.toLowerCase().includes(term))) {{
                // Otherwise, search within the posture values
                matches = true;
                matchDetails.push('posture');
            }}
        }}

        // Search in applications
        if (metadata.apps && metadata.apps.length > 0) {{
            // If searching for "app" or "apps", match any node that has applications
            if (term === 'app' || term === 'apps') {{
                matches = true;
                matchDetails.push('app');
            }} else if (metadata.apps.some(a => a.toLowerCase().includes(term))) {{
                // Otherwise, search within the app values
                matches = true;
                matchDetails.push('app');
            }}
        }}

        // Search in group members
        if (metadata.members && metadata.members.some(m => m.toLowerCase().includes(term))) {{
            matches = true;
            matchDetails.push('member');
        }}

        // Search in rule references
        if (metadata.src_rules && metadata.src_rules.some(r => r.toLowerCase().includes(term))) {{
            matches = true;
            matchDetails.push('rule');
        }}
        if (metadata.dst_rules && metadata.dst_rules.some(r => r.toLowerCase().includes(term))) {{
            matches = true;
            matchDetails.push('rule');
        }}

        // Search in rule type
        if (metadata.rule_type && metadata.rule_type.toLowerCase().includes(term)) {{
            matches = true;
            matchDetails.push('type');
        }}

        if (matches) {{
            matchingNodes.push({{
                ...node,
                matchDetails: matchDetails
            }});
        }}
    }}

    // Limit results to prevent performance issues
    const limitedResults = matchingNodes.slice(0, 15);
    displaySearchDropdown(limitedResults, term);
}}

function displaySearchDropdown(matchingNodes, searchTerm) {{
    const dropdown = document.getElementById('search-dropdown');

    if (matchingNodes.length === 0) {{
        dropdown.innerHTML = '<div class="search-dropdown-item" style="color: #999; cursor: default;">No matching nodes found</div>';
    }} else {{
        dropdown.innerHTML = matchingNodes.map(node => {{
            const details = node.matchDetails.join(', ');
            return `
                <div class="search-dropdown-item" onclick="selectSearchResult('${{node.id}}')">
                    <div class="node-indicator" style="background-color: ${{node.color}};"></div>
                    <div class="node-shape">${{node.shape}}</div>
                    <div class="node-info">
                        <div class="node-name">${{node.id}}</div>
                        <div class="node-details">Matches: ${{details}} | Type: ${{node.metadata.rule_type}}</div>
                    </div>
                </div>
            `;
        }}).join('');
    }}

    dropdown.style.display = 'block';
}}

function selectSearchResult(nodeId) {{
    // Set the search input to the selected node
    document.getElementById('enhanced-search-input').value = nodeId;

    // Save view state before search if not already saved
    if (!searchActive) {{
        saveCurrentViewState();
    }}

    // Perform the search to highlight the node
    performEnhancedSearch(nodeId);

    // Hide the dropdown
    hideSearchDropdown();

    // Focus and center on the selected node
    focusOnNode(nodeId);
}}

function focusOnNode(nodeId) {{
    // Try to focus on the node in the network
    try {{
        if (typeof network !== 'undefined' && network.focus) {{
            network.focus(nodeId, {{
                scale: 1.5,
                animation: {{
                    duration: 1000,
                    easingFunction: 'easeInOutQuad'
                }}
            }});
        }}
    }} catch (e) {{
        console.log('Could not focus on node:', e);
    }}
}}

function showSearchDropdown() {{
    const input = document.getElementById('enhanced-search-input');
    if (input.value.trim() !== '') {{
        updateSearchDropdown(input.value);
    }}
}}

function hideSearchDropdown() {{
    document.getElementById('search-dropdown').style.display = 'none';
}}

function hideSearchDropdownDelayed() {{
    // Delay hiding to allow clicking on dropdown items
    searchDropdownTimeout = setTimeout(() => {{
        hideSearchDropdown();
    }}, 200);
}}

function showSearchTips() {{
    document.getElementById('search-help').style.display = 'block';
}}

function hideSearchTips() {{
    document.getElementById('search-help').style.display = 'none';
}}

function performEnhancedSearch(searchTerm) {{
    if (!searchTerm || searchTerm.trim() === '') {{
        clearSearch();
        return;
    }}

    // Save current view state before performing search
    if (!searchActive) {{
        saveCurrentViewState();
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
        if (metadata.protocols && metadata.protocols.length > 0) {{
            // If searching for "protocol" or "protocols", match any node that has protocols
            if (term === 'protocol' || term === 'protocols') {{
                matches = true;
            }} else if (metadata.protocols.some(p => p.toLowerCase().includes(term))) {{
                // Otherwise, search within the protocol values
                matches = true;
            }}
        }}

        // Search in via routing
        if (metadata.via && metadata.via.length > 0) {{
            // If searching for "via", match any node that has via routing
            if (term === 'via') {{
                matches = true;
            }} else if (metadata.via.some(v => v.toLowerCase().includes(term))) {{
                // Otherwise, search within the via route values
                matches = true;
            }}
        }}

        // Search in posture checks
        if (metadata.posture && metadata.posture.length > 0) {{
            // If searching for "posture", match any node that has posture checks
            if (term === 'posture') {{
                matches = true;
            }} else if (metadata.posture.some(p => p.toLowerCase().includes(term))) {{
                // Otherwise, search within the posture values
                matches = true;
            }}
        }}

        // Search in apps
        if (metadata.apps && metadata.apps.length > 0) {{
            // If searching for "app" or "apps", match any node that has applications
            if (term === 'app' || term === 'apps') {{
                matches = true;
            }} else if (metadata.apps.some(a => a.toLowerCase().includes(term))) {{
                // Otherwise, search within the app values
                matches = true;
            }}
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

    // Restore zoom and pan state
    restoreViewState();

    // Clear search results
    document.getElementById('search-results-count').textContent = '';
    document.getElementById('enhanced-search-input').value = '';

    // Reset saved view state
    savedViewState = null;
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
        initializeSearchableNodes();
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

.search-dropdown {{
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: white;
    border: 1px solid #ddd;
    border-top: none;
    border-radius: 0 0 4px 4px;
    max-height: 200px;
    overflow-y: auto;
    z-index: 1000;
    display: none;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}}

.search-dropdown-item {{
    padding: 8px 12px;
    cursor: pointer;
    border-bottom: 1px solid #f0f0f0;
    font-size: 12px;
    display: flex;
    align-items: center;
}}

.search-dropdown-item:hover {{
    background-color: #f8f9fa;
}}

.search-dropdown-item:last-child {{
    border-bottom: none;
}}

.search-dropdown-item .node-indicator {{
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-right: 8px;
    border: 1px solid #999;
}}

.search-dropdown-item .node-shape {{
    margin-right: 8px;
    font-size: 14px;
}}

.search-dropdown-item .node-info {{
    flex: 1;
}}

.search-dropdown-item .node-name {{
    font-weight: bold;
    color: #333;
}}

.search-dropdown-item .node-details {{
    color: #666;
    font-size: 11px;
    margin-top: 2px;
}}
</style>

<div class="enhanced-search-container" id="enhanced-search-container">
    <div class="drag-handle" id="drag-handle">Search (Drag to Move)</div>

    <div style="position: relative;">
        <input type="text"
               id="enhanced-search-input"
               class="search-input"
               placeholder="Type to filter..."
               onkeyup="handleSearchKeyup(event, this.value)"
               oninput="handleSearchInput(this.value)"
               onfocus="showSearchDropdown()"
               onblur="hideSearchDropdownDelayed()">

        <div id="search-dropdown" class="search-dropdown">
            <!-- Dropdown items will be populated by JavaScript -->
        </div>
    </div>

    <div class="search-controls">
        <button class="search-btn" onclick="performEnhancedSearch(document.getElementById('enhanced-search-input').value)">
            Search
        </button>
        <button class="search-btn secondary" onclick="clearSearch()">
            Clear
        </button>
    </div>

    <div id="search-results-count" class="search-results"></div>

    <div id="search-help" class="search-help">
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
<!-- Legend Toggle Button -->
<div id="legend-toggle" style="position: fixed; top: 10px; right: 10px; z-index: 1001; background-color: #4CAF50; color: white; border: none; border-radius: 5px; padding: 10px; cursor: pointer; font-family: Arial, sans-serif; font-size: 14px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
    📊 Legend
</div>

<!-- Sliding Legend Panel -->
<div id="legend-panel" style="position: fixed; top: 0; right: 0; width: 300px; height: 100vh; background-color: #f5f5f5; border-left: 1px solid #ccc; font-family: Arial, sans-serif; font-size: 12px; z-index: 1000; transform: translateX(0); transition: transform 0.3s ease-in-out; overflow-y: auto; box-shadow: -2px 0 5px rgba(0,0,0,0.1);">
    <div style="padding: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <h3 style="margin: 0; font-size: 16px; color: #333;">Legend</h3>
            <button id="legend-close" style="background: none; border: none; font-size: 18px; cursor: pointer; color: #666; padding: 0; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center;">×</button>
        </div>

        <div style="margin-bottom: 20px;">
            <h4 style="margin: 0 0 12px 0; font-size: 14px; font-weight: bold; color: #333;">Node Types (Colors)</h4>
            <div style="margin-bottom: 8px;">
                <div style="background-color: {group_color}; width: 20px; height: 20px; display: inline-block; margin-right: 10px; border: 1px solid #999; border-radius: 3px;"></div>
                <span style="vertical-align: top; line-height: 20px;">Groups</span>
            </div>
            <div style="margin-bottom: 8px;">
                <div style="background-color: {tag_color}; width: 20px; height: 20px; display: inline-block; margin-right: 10px; border: 1px solid #999; border-radius: 3px;"></div>
                <span style="vertical-align: top; line-height: 20px;">Tags</span>
            </div>
            <div style="margin-bottom: 8px;">
                <div style="background-color: {host_color}; width: 20px; height: 20px; display: inline-block; margin-right: 10px; border: 1px solid #999; border-radius: 3px;"></div>
                <span style="vertical-align: top; line-height: 20px;">Hosts</span>
            </div>
        </div>

        <div style="margin-bottom: 20px;">
            <h4 style="margin: 0 0 12px 0; font-size: 14px; font-weight: bold; color: #333;">Rule Types (Shapes)</h4>
            <div style="margin-bottom: 8px;">
                <span style="font-size: 18px; margin-right: 10px; color: #333;">●</span>
                <span style="vertical-align: top; line-height: 18px;">ACL rules only</span>
            </div>
            <div style="margin-bottom: 8px;">
                <span style="font-size: 18px; margin-right: 10px; color: #333;">▲</span>
                <span style="vertical-align: top; line-height: 18px;">Grant rules only</span>
            </div>
            <div style="margin-bottom: 8px;">
                <span style="font-size: 18px; margin-right: 10px; color: #333;">⬢</span>
                <span style="vertical-align: top; line-height: 18px;">Both ACL and Grant rules</span>
            </div>
        </div>

        <div style="border-top: 1px solid #ddd; padding-top: 15px; font-size: 11px; color: #666;">
            <p style="margin: 0 0 8px 0;"><strong>Tip:</strong> Hover over nodes for detailed information including rule references with line numbers.</p>
            <p style="margin: 0;"><strong>Search:</strong> Use the search box to filter nodes by any metadata.</p>
        </div>
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {{
    const toggleButton = document.getElementById('legend-toggle');
    const legendPanel = document.getElementById('legend-panel');
    const closeButton = document.getElementById('legend-close');

    let isVisible = true; // Default to visible

    function toggleLegend() {{
        isVisible = !isVisible;
        if (isVisible) {{
            legendPanel.style.transform = 'translateX(0)';
            toggleButton.style.display = 'none';
        }} else {{
            legendPanel.style.transform = 'translateX(100%)';
            toggleButton.style.display = 'block';
        }}
    }}

    // Toggle button click
    toggleButton.addEventListener('click', function() {{
        toggleLegend();
    }});

    // Close button click
    closeButton.addEventListener('click', function() {{
        toggleLegend();
    }});

    // Initialize - legend is visible by default
    legendPanel.style.transform = 'translateX(0)';
    toggleButton.style.display = 'none';
}});
</script>
""".format(
            group_color=group_color, tag_color=tag_color, host_color=host_color
        )

        logging.debug("Appending legend to HTML file")
        with open(self.output_file, "a") as f:
            f.write(legend_html)
        logging.debug("Legend added successfully")