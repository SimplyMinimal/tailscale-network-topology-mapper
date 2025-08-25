package renderer

import (
	"os"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"github.com/tailscale-network-topology-mapper/go-rewrite/internal/config"
	"github.com/tailscale-network-topology-mapper/go-rewrite/internal/models"
)

func TestHTMLRenderer(t *testing.T) {
	// Create test configuration
	cfg := &config.Config{
		CompanyDomain: "example.com",
		NodeColors: config.NodeColorsConfig{
			Tag:   "#00cc66",
			Group: "#FFFF00",
			Host:  "#ff6666",
		},
		NetworkOptions: config.NetworkOptionsConfig{
			Physics: config.PhysicsConfig{
				Enabled: true,
				Stabilization: struct {
					Iterations int `mapstructure:"iterations"`
				}{Iterations: 100},
				BarnesHut: struct {
					GravitationalConstant float64 `mapstructure:"gravitational_constant"`
					CentralGravity        float64 `mapstructure:"central_gravity"`
					SpringLength          float64 `mapstructure:"spring_length"`
					SpringConstant        float64 `mapstructure:"spring_constant"`
					Damping               float64 `mapstructure:"damping"`
				}{
					GravitationalConstant: -2000.0,
					CentralGravity:        0.3,
					SpringLength:          95.0,
					SpringConstant:        0.04,
					Damping:               0.09,
				},
			},
			Interaction: config.InteractionConfig{
				Hover:                true,
				SelectConnectedEdges: true,
				TooltipDelay:         200,
			},
		},
	}

	// Create test graph
	graph := models.NewNetworkGraph()

	// Add test nodes
	adminNode := models.CreateNode("group:admin", "group:admin", models.NodeTypeGroup, models.RuleTypeACL)
	adminNode.Tooltip = "group:admin\nType: group<br>Members: alice@example.com, bob@example.com"
	graph.AddNode(adminNode)

	devNode := models.CreateNode("tag:dev", "tag:dev", models.NodeTypeTag, models.RuleTypeGrant)
	devNode.Tooltip = "tag:dev\nType: tag<br>Owners: group:dev"
	graph.AddNode(devNode)

	serverNode := models.CreateNode("server1", "server1", models.NodeTypeHost, models.RuleTypeMixed)
	serverNode.Tooltip = "server1\nType: host<br>IP: 10.0.1.100"
	graph.AddNode(serverNode)

	// Add test edges
	edge1 := models.CreateEdge("group:admin", "tag:dev")
	edge1.Metadata["rule_type"] = "ACL"
	edge1.Metadata["action"] = "accept"
	graph.AddEdge(edge1)

	edge2 := models.CreateEdge("tag:dev", "server1")
	edge2.Metadata["rule_type"] = "Grant"
	edge2.Metadata["protocols"] = []string{"tcp:22", "tcp:80"}
	graph.AddEdge(edge2)

	// Add search metadata
	graph.SetNodeMetadata("group:admin", models.NodeMetadata{
		ID:       "group:admin",
		Type:     "group",
		RuleType: "ACL",
		Members:  []string{"alice@example.com", "bob@example.com"},
	})

	graph.SetNodeMetadata("tag:dev", models.NodeMetadata{
		ID:       "tag:dev",
		Type:     "tag",
		RuleType: "Grant",
		Members:  []string{"group:dev"},
	})

	graph.SetNodeMetadata("server1", models.NodeMetadata{
		ID:       "server1",
		Type:     "host",
		RuleType: "Mixed",
		Members:  []string{"10.0.1.100"},
	})

	// Create renderer
	renderer := NewHTMLRenderer(cfg, graph)
	require.NotNil(t, renderer)

	// Test template data preparation
	templateData, err := renderer.prepareTemplateData()
	require.NoError(t, err)
	require.NotNil(t, templateData)

	assert.Equal(t, "Tailscale Network Topology", templateData.Title)
	assert.Equal(t, "example.com", templateData.CompanyDomain)
	assert.Equal(t, "#00cc66", templateData.NodeColors.Tag)
	assert.Equal(t, "#FFFF00", templateData.NodeColors.Group)
	assert.Equal(t, "#ff6666", templateData.NodeColors.Host)

	// Test JSON conversion
	assert.NotEmpty(t, templateData.Nodes)
	assert.NotEmpty(t, templateData.Edges)
	assert.NotEmpty(t, templateData.SearchMetadata)
	assert.NotEmpty(t, templateData.NetworkOptions)

	// Verify JSON is valid
	assert.True(t, strings.HasPrefix(templateData.Nodes, "["))
	assert.True(t, strings.HasSuffix(templateData.Nodes, "]"))
	assert.True(t, strings.HasPrefix(templateData.Edges, "["))
	assert.True(t, strings.HasSuffix(templateData.Edges, "]"))
}

func TestHTMLRendererFileGeneration(t *testing.T) {
	// Create minimal test setup
	cfg := &config.Config{
		CompanyDomain: "test.com",
		NodeColors: config.NodeColorsConfig{
			Tag:   "#00cc66",
			Group: "#FFFF00",
			Host:  "#ff6666",
		},
		NetworkOptions: config.NetworkOptionsConfig{
			Physics: config.PhysicsConfig{
				Enabled: true,
			},
			Interaction: config.InteractionConfig{
				Hover: true,
			},
		},
	}

	graph := models.NewNetworkGraph()
	testNode := models.CreateNode("test", "test", models.NodeTypeHost, models.RuleTypeACL)
	graph.AddNode(testNode)

	renderer := NewHTMLRenderer(cfg, graph)

	// Create temporary file
	tmpFile, err := os.CreateTemp("", "test-output-*.html")
	require.NoError(t, err)
	tmpFile.Close()
	defer os.Remove(tmpFile.Name())

	// Render to HTML
	err = renderer.RenderToHTML(tmpFile.Name())
	require.NoError(t, err)

	// Verify file was created and has content
	content, err := os.ReadFile(tmpFile.Name())
	require.NoError(t, err)
	assert.NotEmpty(t, content)

	htmlContent := string(content)

	// Verify HTML structure
	assert.Contains(t, htmlContent, "<!DOCTYPE html>")
	assert.Contains(t, htmlContent, "<html")
	assert.Contains(t, htmlContent, "</html>")
	assert.Contains(t, htmlContent, "Tailscale Network Topology")

	// Verify vis.js integration
	assert.Contains(t, htmlContent, "vis-network")
	assert.Contains(t, htmlContent, "new vis.Network")
	assert.Contains(t, htmlContent, "new vis.DataSet")

	// Verify search functionality
	assert.Contains(t, htmlContent, "enhanced-search-container")
	assert.Contains(t, htmlContent, "search-input")
	assert.Contains(t, htmlContent, "addEventListener")

	// Verify legend functionality
	assert.Contains(t, htmlContent, "legend-panel")
	assert.Contains(t, htmlContent, "toggleLegend")

	// Verify configuration was applied
	assert.Contains(t, htmlContent, "test.com")
	assert.Contains(t, htmlContent, "#00cc66")
	assert.Contains(t, htmlContent, "#FFFF00")
	assert.Contains(t, htmlContent, "#ff6666")
}

func TestHTMLRendererJSONConversion(t *testing.T) {
	cfg := &config.Config{
		NodeColors: config.NodeColorsConfig{
			Tag:   "#00cc66",
			Group: "#FFFF00",
			Host:  "#ff6666",
		},
	}

	graph := models.NewNetworkGraph()

	// Add nodes with different shapes
	dotNode := models.CreateNode("acl-only", "acl-only", models.NodeTypeHost, models.RuleTypeACL)
	triangleNode := models.CreateNode("grant-only", "grant-only", models.NodeTypeTag, models.RuleTypeGrant)
	hexagonNode := models.CreateNode("mixed", "mixed", models.NodeTypeGroup, models.RuleTypeMixed)

	graph.AddNode(dotNode)
	graph.AddNode(triangleNode)
	graph.AddNode(hexagonNode)

	renderer := NewHTMLRenderer(cfg, graph)

	// Test nodes to JSON
	nodesJSON, err := renderer.nodesToJSON()
	require.NoError(t, err)
	assert.NotEmpty(t, nodesJSON)

	// Should contain vis.js node properties
	assert.Contains(t, nodesJSON, `"id":"acl-only"`)
	assert.Contains(t, nodesJSON, `"label":"acl-only"`)
	assert.Contains(t, nodesJSON, `"shape":"dot"`)
	assert.Contains(t, nodesJSON, `"shape":"triangle"`)
	assert.Contains(t, nodesJSON, `"shape":"hexagon"`)

	// Test edges to JSON
	edge := models.CreateEdge("acl-only", "grant-only")
	edge.Label = "test-edge"
	graph.AddEdge(edge)

	edgesJSON, err := renderer.edgesToJSON()
	require.NoError(t, err)
	assert.NotEmpty(t, edgesJSON)

	// Should contain vis.js edge properties
	assert.Contains(t, edgesJSON, `"from":"acl-only"`)
	assert.Contains(t, edgesJSON, `"to":"grant-only"`)
	assert.Contains(t, edgesJSON, `"label":"test-edge"`)
	assert.Contains(t, edgesJSON, `"arrows"`)

	// Test search metadata to JSON
	graph.SetNodeMetadata("acl-only", models.NodeMetadata{
		ID:   "acl-only",
		Type: "host",
	})

	metadataJSON, err := renderer.searchMetadataToJSON()
	require.NoError(t, err)
	assert.NotEmpty(t, metadataJSON)
	assert.Contains(t, metadataJSON, `"acl-only"`)
}

func TestHTMLRendererNetworkOptions(t *testing.T) {
	cfg := &config.Config{
		NetworkOptions: config.NetworkOptionsConfig{
			Physics: config.PhysicsConfig{
				Enabled: true,
				Stabilization: struct {
					Iterations int `mapstructure:"iterations"`
				}{Iterations: 150},
				BarnesHut: struct {
					GravitationalConstant float64 `mapstructure:"gravitational_constant"`
					CentralGravity        float64 `mapstructure:"central_gravity"`
					SpringLength          float64 `mapstructure:"spring_length"`
					SpringConstant        float64 `mapstructure:"spring_constant"`
					Damping               float64 `mapstructure:"damping"`
				}{
					GravitationalConstant: -3000.0,
					CentralGravity:        0.5,
					SpringLength:          100.0,
					SpringConstant:        0.05,
					Damping:               0.1,
				},
			},
			Interaction: config.InteractionConfig{
				Hover:                false,
				SelectConnectedEdges: false,
				TooltipDelay:         500,
			},
		},
	}

	graph := models.NewNetworkGraph()
	renderer := NewHTMLRenderer(cfg, graph)

	optionsJSON, err := renderer.networkOptionsToJSON()
	require.NoError(t, err)
	assert.NotEmpty(t, optionsJSON)

	// Verify configuration values are included
	assert.Contains(t, optionsJSON, `"enabled":true`)
	assert.Contains(t, optionsJSON, `"iterations":150`)
	assert.Contains(t, optionsJSON, `"gravitationalConstant":-3000`)
	assert.Contains(t, optionsJSON, `"centralGravity":0.5`)
	assert.Contains(t, optionsJSON, `"springLength":100`)
	assert.Contains(t, optionsJSON, `"springConstant":0.05`)
	assert.Contains(t, optionsJSON, `"damping":0.1`)
	assert.Contains(t, optionsJSON, `"hover":false`)
	assert.Contains(t, optionsJSON, `"selectConnectedEdges":false`)
	assert.Contains(t, optionsJSON, `"tooltipDelay":500`)
}

func TestHTMLRendererStats(t *testing.T) {
	cfg := &config.Config{}
	graph := models.NewNetworkGraph()

	// Add some test data
	graph.AddNode(models.CreateNode("node1", "node1", models.NodeTypeHost, models.RuleTypeACL))
	graph.AddNode(models.CreateNode("node2", "node2", models.NodeTypeTag, models.RuleTypeGrant))
	graph.AddEdge(models.CreateEdge("node1", "node2"))

	renderer := NewHTMLRenderer(cfg, graph)
	stats := renderer.GetStats()

	require.NotNil(t, stats)
	assert.Equal(t, 2, stats["total_nodes"])
	assert.Equal(t, 1, stats["total_edges"])
}
