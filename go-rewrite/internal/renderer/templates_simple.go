package renderer

// GetBaseTemplate returns the main HTML template
func GetBaseTemplate() string {
	return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{.Title}}</title>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }
        
        #network-container {
            width: 100%;
            height: 800px;
            border: 1px solid #ddd;
            background-color: white;
        }
        
        .view-mode-container {
            position: fixed;
            top: 20px;
            left: 20px;
            background-color: #ffffff;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            z-index: 1000;
            font-size: 12px;
        }
        
        .enhanced-search-container {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background-color: #ffffff;
            padding: 15px;
            border: 2px solid #007bff;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
            min-width: 300px;
        }
        
        .search-input {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            box-sizing: border-box;
        }
        
        .legend-panel {
            position: fixed;
            top: 20px;
            right: 20px;
            background-color: #ffffff;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            z-index: 1000;
            min-width: 250px;
        }
        
        .legend-header {
            background-color: #f8f9fa;
            padding: 12px 15px;
            border-bottom: 1px solid #ddd;
            border-radius: 8px 8px 0 0;
            cursor: pointer;
            font-weight: bold;
        }
        
        .legend-content {
            padding: 15px;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            margin-bottom: 8px;
            font-size: 13px;
        }
        
        .legend-color {
            width: 16px;
            height: 16px;
            border-radius: 50%;
            margin-right: 10px;
            border: 1px solid #ddd;
        }
    </style>
</head>
<body>
    <div class="view-mode-container">
        <h4>View Mode</h4>
        <div>Interactive Network Topology</div>
        <div style="font-size: 10px; color: #666; margin-top: 4px;">
            Company: {{.CompanyDomain}}
        </div>
    </div>

    <div id="network-container"></div>
    
    <div class="enhanced-search-container">
        <input type="text" id="search-input" class="search-input" placeholder="Search nodes...">
        <div id="search-results" style="margin-top: 8px; font-size: 12px; color: #666;"></div>
    </div>
    
    <div class="legend-panel">
        <div class="legend-header" onclick="toggleLegend()">
            <span>Legend</span>
        </div>
        <div id="legend-content" class="legend-content">
            <h4>Node Types (Colors)</h4>
            <div class="legend-item">
                <span class="legend-color" style="background-color: {{.NodeColors.Group}};"></span>
                <span>Groups & Autogroups</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background-color: {{.NodeColors.Tag}};"></span>
                <span>Tags</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background-color: {{.NodeColors.Host}};"></span>
                <span>Hosts & IPs</span>
            </div>
            
            <h4>Rule Types (Shapes)</h4>
            <div class="legend-item">
                <span style="margin-right: 10px;">●</span>
                <span>ACL Rules Only</span>
            </div>
            <div class="legend-item">
                <span style="margin-right: 10px;">▲</span>
                <span>Grant Rules Only</span>
            </div>
            <div class="legend-item">
                <span style="margin-right: 10px;">⬢</span>
                <span>Both ACL & Grant Rules</span>
            </div>
        </div>
    </div>
    
    <script>
        // Network data
        const nodes = new vis.DataSet(JSON.parse({{.Nodes}}));
        const edges = new vis.DataSet(JSON.parse({{.Edges}}));
        const data = { nodes: nodes, edges: edges };

        // Network options
        const options = JSON.parse({{.NetworkOptions}});

        // Search metadata
        const searchMetadata = JSON.parse({{.SearchMetadata}});
        
        // Create network
        const container = document.getElementById('network-container');
        const network = new vis.Network(container, data, options);
        
        // Basic search functionality
        document.getElementById('search-input').addEventListener('input', function(e) {
            const query = e.target.value.toLowerCase();
            const results = document.getElementById('search-results');
            
            if (query === '') {
                results.textContent = '';
                // Reset all node colors
                const allNodes = nodes.get();
                allNodes.forEach(node => {
                    node.color = getOriginalColor(node.id);
                });
                nodes.update(allNodes);
                return;
            }
            
            // Simple search implementation
            const allNodes = nodes.get();
            let matchCount = 0;
            
            allNodes.forEach(node => {
                if (node.id.toLowerCase().includes(query) || 
                    (node.label && node.label.toLowerCase().includes(query))) {
                    node.color = '#ff6b6b'; // Highlight color
                    matchCount++;
                } else {
                    node.color = 'rgba(200,200,200,0.3)'; // Dim color
                }
            });
            
            nodes.update(allNodes);
            results.textContent = 'Found ' + matchCount + ' matching nodes';
        });
        
        function getOriginalColor(nodeId) {
            // Simple color assignment based on node type
            if (nodeId.startsWith('group:') || nodeId.startsWith('autogroup:')) {
                return '{{.NodeColors.Group}}';
            } else if (nodeId.startsWith('tag:')) {
                return '{{.NodeColors.Tag}}';
            } else {
                return '{{.NodeColors.Host}}';
            }
        }
        
        function toggleLegend() {
            const content = document.getElementById('legend-content');
            if (content.style.display === 'none') {
                content.style.display = 'block';
            } else {
                content.style.display = 'none';
            }
        }
        
        // Neighborhood highlighting
        network.on("click", function(params) {
            if (params.nodes.length > 0) {
                const selectedNode = params.nodes[0];
                const connectedNodes = network.getConnectedNodes(selectedNode);
                const allNodes = nodes.get();
                
                allNodes.forEach(node => {
                    if (connectedNodes.includes(node.id) || node.id === selectedNode) {
                        node.color = getOriginalColor(node.id);
                    } else {
                        node.color = 'rgba(200,200,200,0.5)';
                    }
                });
                
                nodes.update(allNodes);
            }
        });
    </script>
</body>
</html>`
}
