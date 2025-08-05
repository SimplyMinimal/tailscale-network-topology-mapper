package renderer

import (
	"bytes"
	"encoding/json"
	"fmt"
	"html/template"
	"log"
	"os"

	"github.com/tailscale-network-topology-mapper/go-rewrite/internal/config"
	"github.com/tailscale-network-topology-mapper/go-rewrite/internal/models"
)

// TemplateData holds data for template rendering
type TemplateData struct {
	Title          string
	Nodes          string // JSON string of nodes
	Edges          string // JSON string of edges
	SearchMetadata string // JSON string of search metadata
	NetworkOptions string // JSON string of network options
	NodeColors     NodeColorsData
	CompanyDomain  string
}

// NodeColorsData holds color configuration for nodes
type NodeColorsData struct {
	Tag   string
	Group string
	Host  string
}

// HTMLRenderer renders network graphs to interactive HTML visualizations
type HTMLRenderer struct {
	config *config.Config
	graph  *models.NetworkGraph
}

// NewHTMLRenderer creates a new HTML renderer
func NewHTMLRenderer(cfg *config.Config, graph *models.NetworkGraph) *HTMLRenderer {
	return &HTMLRenderer{
		config: cfg,
		graph:  graph,
	}
}

// RenderToHTML renders the network graph to an interactive HTML file
func (r *HTMLRenderer) RenderToHTML(outputFile string) error {
	log.Printf("Starting HTML rendering to: %s", outputFile)

	// Prepare template data
	templateData, err := r.prepareTemplateData()
	if err != nil {
		return fmt.Errorf("failed to prepare template data: %w", err)
	}

	// Create the complete template
	tmpl, err := r.createTemplate()
	if err != nil {
		return fmt.Errorf("failed to create template: %w", err)
	}

	// Render the template
	var buf bytes.Buffer
	if err := tmpl.Execute(&buf, templateData); err != nil {
		return fmt.Errorf("failed to execute template: %w", err)
	}

	// Write to file
	if err := os.WriteFile(outputFile, buf.Bytes(), 0644); err != nil {
		return fmt.Errorf("failed to write HTML file: %w", err)
	}

	log.Printf("HTML rendering completed successfully")
	return nil
}

// prepareTemplateData prepares all data needed for template rendering
func (r *HTMLRenderer) prepareTemplateData() (*TemplateData, error) {
	// Convert nodes to JSON
	nodesJSON, err := r.nodesToJSON()
	if err != nil {
		return nil, fmt.Errorf("failed to convert nodes to JSON: %w", err)
	}

	// Convert edges to JSON
	edgesJSON, err := r.edgesToJSON()
	if err != nil {
		return nil, fmt.Errorf("failed to convert edges to JSON: %w", err)
	}

	// Convert search metadata to JSON
	searchMetadataJSON, err := r.searchMetadataToJSON()
	if err != nil {
		return nil, fmt.Errorf("failed to convert search metadata to JSON: %w", err)
	}

	// Convert network options to JSON
	networkOptionsJSON, err := r.networkOptionsToJSON()
	if err != nil {
		return nil, fmt.Errorf("failed to convert network options to JSON: %w", err)
	}

	return &TemplateData{
		Title:          "Tailscale Network Topology",
		Nodes:          nodesJSON,
		Edges:          edgesJSON,
		SearchMetadata: searchMetadataJSON,
		NetworkOptions: networkOptionsJSON,
		NodeColors: NodeColorsData{
			Tag:   r.config.NodeColors.Tag,
			Group: r.config.NodeColors.Group,
			Host:  r.config.NodeColors.Host,
		},
		CompanyDomain: r.config.CompanyDomain,
	}, nil
}

// nodesToJSON converts graph nodes to JSON format for vis.js
func (r *HTMLRenderer) nodesToJSON() (string, error) {
	var visNodes []map[string]interface{}

	for _, node := range r.graph.Nodes {
		visNode := map[string]interface{}{
			"id":          node.ID,
			"label":       node.Label,
			"color":       node.Color,
			"title":       node.Tooltip,
			"font":        map[string]interface{}{"size": 12, "color": "black"},
			"borderWidth": 2,
			"chosen":      true,
		}

		// Set shape based on node shape
		switch node.Shape {
		case models.NodeShapeTriangle:
			visNode["shape"] = "triangle"
		case models.NodeShapeHexagon:
			visNode["shape"] = "hexagon"
		default:
			visNode["shape"] = "dot"
		}

		visNodes = append(visNodes, visNode)
	}

	jsonBytes, err := json.Marshal(visNodes)
	if err != nil {
		return "", err
	}

	return string(jsonBytes), nil
}

// edgesToJSON converts graph edges to JSON format for vis.js
func (r *HTMLRenderer) edgesToJSON() (string, error) {
	var visEdges []map[string]interface{}

	for _, edge := range r.graph.Edges {
		visEdge := map[string]interface{}{
			"from":   edge.From,
			"to":     edge.To,
			"arrows": map[string]interface{}{"to": map[string]interface{}{"enabled": true}},
			"color":  map[string]interface{}{"color": "#848484", "highlight": "#ff0000"},
			"width":  2,
			"smooth": map[string]interface{}{"enabled": true, "type": "continuous"},
		}

		if edge.Label != "" {
			visEdge["label"] = edge.Label
		}

		visEdges = append(visEdges, visEdge)
	}

	jsonBytes, err := json.Marshal(visEdges)
	if err != nil {
		return "", err
	}

	return string(jsonBytes), nil
}

// searchMetadataToJSON converts search metadata to JSON
func (r *HTMLRenderer) searchMetadataToJSON() (string, error) {
	metadata := r.graph.GetSearchMetadata()
	jsonBytes, err := json.Marshal(metadata)
	if err != nil {
		return "", err
	}
	return string(jsonBytes), nil
}

// networkOptionsToJSON converts network options to JSON for vis.js
func (r *HTMLRenderer) networkOptionsToJSON() (string, error) {
	options := map[string]interface{}{
		"nodes": map[string]interface{}{
			"font":        map[string]interface{}{"size": 12},
			"borderWidth": 2,
			"chosen":      true,
		},
		"edges": map[string]interface{}{
			"arrows": map[string]interface{}{"to": map[string]interface{}{"enabled": true, "scaleFactor": 1}},
			"color":  map[string]interface{}{"color": "#848484", "highlight": "#ff0000"},
			"width":  2,
			"smooth": map[string]interface{}{"enabled": true, "type": "continuous"},
		},
		"physics": map[string]interface{}{
			"enabled":       r.config.NetworkOptions.Physics.Enabled,
			"stabilization": map[string]interface{}{"iterations": r.config.NetworkOptions.Physics.Stabilization.Iterations},
			"barnesHut": map[string]interface{}{
				"gravitationalConstant": r.config.NetworkOptions.Physics.BarnesHut.GravitationalConstant,
				"centralGravity":        r.config.NetworkOptions.Physics.BarnesHut.CentralGravity,
				"springLength":          r.config.NetworkOptions.Physics.BarnesHut.SpringLength,
				"springConstant":        r.config.NetworkOptions.Physics.BarnesHut.SpringConstant,
				"damping":               r.config.NetworkOptions.Physics.BarnesHut.Damping,
			},
		},
		"interaction": map[string]interface{}{
			"hover":                r.config.NetworkOptions.Interaction.Hover,
			"selectConnectedEdges": r.config.NetworkOptions.Interaction.SelectConnectedEdges,
			"tooltipDelay":         r.config.NetworkOptions.Interaction.TooltipDelay,
		},
		"configure": map[string]interface{}{
			"enabled": false,
		},
	}

	jsonBytes, err := json.Marshal(options)
	if err != nil {
		return "", err
	}

	return string(jsonBytes), nil
}

// createTemplate creates the complete HTML template
func (r *HTMLRenderer) createTemplate() (*template.Template, error) {
	// Create a new template using the simple template
	tmpl, err := template.New("main").Parse(GetBaseTemplate())
	if err != nil {
		return nil, fmt.Errorf("failed to parse template: %w", err)
	}

	return tmpl, nil
}

// GetStats returns statistics about the rendered graph
func (r *HTMLRenderer) GetStats() map[string]interface{} {
	return r.graph.Stats()
}
