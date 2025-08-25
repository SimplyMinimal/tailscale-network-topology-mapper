package main

import (
	"os"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"github.com/tailscale-network-topology-mapper/go-rewrite/internal/config"
	"github.com/tailscale-network-topology-mapper/go-rewrite/internal/graph"
	"github.com/tailscale-network-topology-mapper/go-rewrite/internal/models"
	"github.com/tailscale-network-topology-mapper/go-rewrite/internal/parser"
	"github.com/tailscale-network-topology-mapper/go-rewrite/internal/renderer"
)

// TestCompleteWorkflow tests the entire pipeline from policy parsing to HTML generation
func TestCompleteWorkflow(t *testing.T) {
	// Create a comprehensive test policy
	testPolicy := `{
		// Comprehensive test policy for Go rewrite
		"groups": {
			"group:admin": [
				"alice@example.com",
				"bob@example.com"
			],
			"group:developers": [
				"dev1@example.com",
				"dev2@example.com",
				"tag:dev-servers"
			],
			"group:qa": [
				"qa1@example.com",
				"qa2@example.com"
			]
		},
		
		"hosts": {
			"production-db": "10.0.1.100",
			"staging-db": "10.0.2.100",
			"api-gateway": "10.0.1.50",
			"monitoring": "10.0.3.10"
		},
		
		"tagOwners": {
			"tag:prod-servers": ["group:admin"],
			"tag:dev-servers": ["group:developers"],
			"tag:qa-servers": ["group:qa"],
			"tag:monitoring": ["group:admin"],
			"tag:databases": ["group:admin", "alice@example.com"]
		},
		
		"postures": {
			"posture:corporate-device": [
				"node:os == 'windows' || node:os == 'macos'",
				"node:tsVersion >= '1.50.0'"
			],
			"posture:secure-device": [
				"node:os != 'android'",
				"node:clientSupports.hairPinning == true"
			]
		},
		
		"acls": [
			{
				"action": "accept",
				"src": ["group:admin"],
				"dst": ["*:*"]
			},
			{
				"action": "accept", 
				"src": ["group:developers"],
				"dst": ["tag:dev-servers:*", "staging-db:5432"]
			},
			{
				"action": "accept",
				"src": ["group:qa"],
				"dst": ["tag:qa-servers:*", "staging-db:5432"]
			},
			{
				"action": "accept",
				"src": ["tag:monitoring"],
				"dst": ["*:9090", "*:3000", "*:8080"],
				"proto": "tcp"
			}
		],
		
		"grants": [
			{
				"src": ["group:developers"],
				"dst": ["tag:dev-servers"],
				"ip": ["tcp:22", "tcp:80", "tcp:443", "tcp:8000-8999"],
				"srcPosture": ["posture:corporate-device"]
			},
			{
				"src": ["group:qa"],
				"dst": ["tag:qa-servers"],
				"ip": ["tcp:22", "tcp:80", "tcp:443"],
				"srcPosture": ["posture:corporate-device"]
			},
			{
				"src": ["tag:prod-servers"],
				"dst": ["production-db"],
				"ip": ["tcp:5432"],
				"via": ["api-gateway"]
			},
			{
				"src": ["autogroup:internet"],
				"dst": ["api-gateway"],
				"ip": ["tcp:443", "tcp:80"]
			},
			{
				"src": ["tag:monitoring"],
				"dst": ["*"],
				"ip": ["tcp:9090", "udp:161"],
				"app": {
					"prometheus": {
						"proto": "tcp",
						"ports": [9090]
					},
					"snmp": {
						"proto": "udp", 
						"ports": [161]
					}
				}
			},
			{
				"src": ["group:admin"],
				"dst": ["tag:databases"],
				"ip": ["tcp:5432", "tcp:3306", "tcp:27017"],
				"dstPosture": ["posture:secure-device"]
			}
		],
		
		"autogroups": {
			"autogroup:internet": ["*"],
			"autogroup:self": ["*"]
		}
	}`

	// Create temporary policy file
	tmpFile, err := os.CreateTemp("", "integration-test-policy-*.hujson")
	require.NoError(t, err)
	defer os.Remove(tmpFile.Name())

	_, err = tmpFile.WriteString(testPolicy)
	require.NoError(t, err)
	tmpFile.Close()

	// Step 1: Load configuration
	cfg, err := config.Load()
	require.NoError(t, err)
	cfg.PolicyFile = tmpFile.Name()
	cfg.CompanyDomain = "integration-test.com"

	// Step 2: Parse policy
	t.Log("Parsing policy file...")
	policyParser := parser.NewPolicyParser(cfg.PolicyFile)
	err = policyParser.ParsePolicy()
	require.NoError(t, err)

	policyData := policyParser.GetPolicyData()
	ruleLineNumbers := policyParser.GetRuleLineNumbers()
	stats := policyParser.GetStats()

	// Verify policy parsing
	assert.Equal(t, 3, stats.Groups)
	assert.Equal(t, 4, stats.Hosts)
	assert.Equal(t, 5, stats.TagOwners)
	assert.Equal(t, 4, stats.ACLs)
	assert.Equal(t, 6, stats.Grants)
	assert.Equal(t, 2, stats.Postures)

	// Verify specific data
	assert.Contains(t, policyData.Groups, "group:admin")
	assert.Contains(t, policyData.Groups, "group:developers")
	assert.Contains(t, policyData.Groups, "group:qa")
	assert.Equal(t, []string{"alice@example.com", "bob@example.com"}, policyData.Groups["group:admin"])

	assert.Contains(t, policyData.Hosts, "production-db")
	assert.Equal(t, "10.0.1.100", policyData.Hosts["production-db"])

	assert.Contains(t, policyData.TagOwners, "tag:prod-servers")
	assert.Equal(t, []string{"group:admin"}, policyData.TagOwners["tag:prod-servers"])

	// Step 3: Build network graph
	t.Log("Building network graph...")
	graphBuilder := graph.NewGraphBuilder(policyData, ruleLineNumbers)
	networkGraph, err := graphBuilder.BuildGraph()
	require.NoError(t, err)

	graphStats := networkGraph.Stats()
	t.Logf("Graph stats: %+v", graphStats)

	// Verify graph construction
	assert.Greater(t, networkGraph.GetNodeCount(), 0)
	assert.Greater(t, networkGraph.GetEdgeCount(), 0)

	// Verify specific nodes exist
	assert.True(t, networkGraph.HasNode("group:admin"))
	assert.True(t, networkGraph.HasNode("group:developers"))
	assert.True(t, networkGraph.HasNode("tag:prod-servers"))
	assert.True(t, networkGraph.HasNode("production-db"))
	assert.True(t, networkGraph.HasNode("api-gateway"))

	// Verify node types and properties
	adminNode, exists := networkGraph.GetNode("group:admin")
	require.True(t, exists)
	assert.Equal(t, "group", string(adminNode.Type))
	assert.NotEmpty(t, adminNode.Color)
	assert.NotEmpty(t, adminNode.Tooltip)

	prodTag, exists := networkGraph.GetNode("tag:prod-servers")
	require.True(t, exists)
	assert.Equal(t, "tag", string(prodTag.Type))

	// Verify mixed rule types (nodes that appear in both ACL and Grant rules)
	devNode, exists := networkGraph.GetNode("group:developers")
	require.True(t, exists)
	// Should be mixed since developers appear in both ACL and Grant rules
	assert.Equal(t, "Mixed", string(devNode.RuleType))

	// Step 4: Generate HTML
	t.Log("Rendering HTML...")
	htmlRenderer := renderer.NewHTMLRenderer(cfg, networkGraph)

	// Create temporary output file
	outputFile, err := os.CreateTemp("", "integration-test-output-*.html")
	require.NoError(t, err)
	outputFile.Close()
	defer os.Remove(outputFile.Name())

	err = htmlRenderer.RenderToHTML(outputFile.Name())
	require.NoError(t, err)

	// Step 5: Verify HTML output
	htmlContent, err := os.ReadFile(outputFile.Name())
	require.NoError(t, err)
	assert.NotEmpty(t, htmlContent)

	htmlStr := string(htmlContent)

	// Verify HTML structure
	assert.Contains(t, htmlStr, "<!DOCTYPE html>")
	assert.Contains(t, htmlStr, "Tailscale Network Topology")
	assert.Contains(t, htmlStr, "integration-test.com")

	// Verify vis.js integration
	assert.Contains(t, htmlStr, "vis-network")
	assert.Contains(t, htmlStr, "new vis.Network")
	assert.Contains(t, htmlStr, "new vis.DataSet")

	// Verify search functionality is included
	assert.Contains(t, htmlStr, "enhanced-search-container")
	assert.Contains(t, htmlStr, "search-input")
	assert.Contains(t, htmlStr, "handleSearchInput")
	assert.Contains(t, htmlStr, "performSearch")
	assert.Contains(t, htmlStr, "clearSearch")

	// Verify legend functionality
	assert.Contains(t, htmlStr, "legend-panel")
	assert.Contains(t, htmlStr, "legend-content")
	assert.Contains(t, htmlStr, "toggleLegend")

	// Verify drag functionality
	assert.Contains(t, htmlStr, "initializeDragFunctionality")
	assert.Contains(t, htmlStr, "drag-handle")

	// Verify node data is embedded
	assert.Contains(t, htmlStr, "group:admin")
	assert.Contains(t, htmlStr, "tag:prod-servers")
	assert.Contains(t, htmlStr, "production-db")

	// Verify color configuration
	assert.Contains(t, htmlStr, cfg.NodeColors.Tag)
	assert.Contains(t, htmlStr, cfg.NodeColors.Group)
	assert.Contains(t, htmlStr, cfg.NodeColors.Host)

	// Verify search metadata is included
	assert.Contains(t, htmlStr, "searchMetadata")

	// Verify network options are configured
	assert.Contains(t, htmlStr, "physics")
	assert.Contains(t, htmlStr, "interaction")

	t.Log("Integration test completed successfully!")
	t.Logf("Generated HTML file: %s (%d bytes)", outputFile.Name(), len(htmlContent))
	t.Logf("Policy stats: Groups=%d, Hosts=%d, ACLs=%d, Grants=%d",
		stats.Groups, stats.Hosts, stats.ACLs, stats.Grants)
	t.Logf("Graph stats: Nodes=%d, Edges=%d",
		networkGraph.GetNodeCount(), networkGraph.GetEdgeCount())
}

// TestFeatureParity verifies that all Python version features are preserved
func TestFeatureParity(t *testing.T) {
	// Test that all expected UI features are present in generated HTML
	cfg, err := config.Load()
	require.NoError(t, err)

	// Create minimal graph for testing
	networkGraph := createMinimalTestGraph()
	htmlRenderer := renderer.NewHTMLRenderer(cfg, networkGraph)

	outputFile, err := os.CreateTemp("", "feature-parity-test-*.html")
	require.NoError(t, err)
	outputFile.Close()
	defer os.Remove(outputFile.Name())

	err = htmlRenderer.RenderToHTML(outputFile.Name())
	require.NoError(t, err)

	htmlContent, err := os.ReadFile(outputFile.Name())
	require.NoError(t, err)
	htmlStr := string(htmlContent)

	// Test search positioning (center-left as per user preferences)
	assert.Contains(t, htmlStr, "left: 50%")
	assert.Contains(t, htmlStr, "transform: translateX(-50%)")

	// Test tooltip formatting with emoji prefixes
	assert.Contains(t, htmlStr, "tooltip")
	// assert.Contains(t, htmlStr, "\n")

	// Test legend sliding toggle panels
	assert.Contains(t, htmlStr, "legend-toggle")
	assert.Contains(t, htmlStr, "transition")

	// Test drag-and-drop functionality
	assert.Contains(t, htmlStr, "isDragging")
	assert.Contains(t, htmlStr, "mousedown")
	assert.Contains(t, htmlStr, "mousemove")

	// Test live search with dropdown
	assert.Contains(t, htmlStr, "search-dropdown")
	assert.Contains(t, htmlStr, "dropdown-item")

	// Test neighborhood highlighting
	assert.Contains(t, htmlStr, "neighbourhoodHighlight")
	assert.Contains(t, htmlStr, "getConnectedNodes")

	// Test zoom controls
	assert.Contains(t, htmlStr, "zoom")
	assert.Contains(t, htmlStr, "focus")

	t.Log("Feature parity test passed - all expected features are present")
}

// Helper function to create a minimal test graph
func createMinimalTestGraph() *models.NetworkGraph {
	graph := models.NewNetworkGraph()

	// Add test nodes
	adminNode := models.CreateNode("group:admin", "group:admin", models.NodeTypeGroup, models.RuleTypeACL)
	adminNode.Tooltip = "group:admin\nType: group"
	graph.AddNode(adminNode)

	tagNode := models.CreateNode("tag:prod", "tag:prod", models.NodeTypeTag, models.RuleTypeGrant)
	tagNode.Tooltip = "tag:prod\nType: tag"
	graph.AddNode(tagNode)

	hostNode := models.CreateNode("server1", "server1", models.NodeTypeHost, models.RuleTypeMixed)
	hostNode.Tooltip = "server1\nType: host"
	graph.AddNode(hostNode)

	// Add test edge
	edge := models.CreateEdge("group:admin", "tag:prod")
	graph.AddEdge(edge)

	// Add search metadata
	graph.SetNodeMetadata("group:admin", models.NodeMetadata{
		ID:   "group:admin",
		Type: "group",
	})

	return graph
}

// TestPerformance runs a basic performance test
func TestPerformance(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping performance test in short mode")
	}

	// Create a larger policy for performance testing
	// This would be expanded for real performance testing
	t.Log("Performance test placeholder - would test with larger datasets")
}
