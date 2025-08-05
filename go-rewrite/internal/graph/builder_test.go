package graph

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"github.com/tailscale-network-topology-mapper/go-rewrite/internal/models"
)

func TestGraphBuilder(t *testing.T) {
	// Create test policy data
	policyData := models.NewPolicyData()
	
	// Add test data
	policyData.Groups["group:admin"] = []string{"alice@example.com", "bob@example.com"}
	policyData.Groups["group:dev"] = []string{"dev@example.com"}
	policyData.Hosts["server1"] = "10.0.1.100"
	policyData.TagOwners["tag:prod"] = []string{"group:admin"}
	policyData.TagOwners["tag:dev"] = []string{"group:dev"}
	
	// Add ACL rules
	policyData.ACLs = []models.ACLRule{
		{
			Action: "accept",
			Src:    []string{"group:admin"},
			Dst:    []string{"*:*"},
			Proto:  "tcp",
		},
		{
			Action: "accept",
			Src:    []string{"group:dev"},
			Dst:    []string{"tag:dev:22"},
		},
	}
	
	// Add Grant rules
	policyData.Grants = []models.GrantRule{
		{
			Src: []string{"group:dev"},
			Dst: []string{"tag:dev"},
			IP:  []string{"tcp:22", "tcp:80"},
		},
		{
			Src: []string{"tag:prod"},
			Dst: []string{"server1"},
			IP:  []string{"tcp:5432"},
			Via: []string{"api-gateway"},
		},
	}

	// Create rule line numbers
	ruleLineNumbers := &models.RuleLineNumbers{
		ACLs:   []int{10, 15},
		Grants: []int{20, 25},
	}

	// Build graph
	builder := NewGraphBuilder(policyData, ruleLineNumbers)
	graph, err := builder.BuildGraph()
	require.NoError(t, err)
	require.NotNil(t, graph)

	// Test nodes were created
	assert.True(t, graph.HasNode("group:admin"))
	assert.True(t, graph.HasNode("group:dev"))
	assert.True(t, graph.HasNode("tag:prod"))
	assert.True(t, graph.HasNode("tag:dev"))
	assert.True(t, graph.HasNode("server1"))

	// Test node types
	adminNode, exists := graph.GetNode("group:admin")
	require.True(t, exists)
	assert.Equal(t, models.NodeTypeGroup, adminNode.Type)
	assert.Equal(t, models.GetNodeColorByType(models.NodeTypeGroup), adminNode.Color)

	tagNode, exists := graph.GetNode("tag:prod")
	require.True(t, exists)
	assert.Equal(t, models.NodeTypeTag, tagNode.Type)
	assert.Equal(t, models.GetNodeColorByType(models.NodeTypeTag), tagNode.Color)

	hostNode, exists := graph.GetNode("server1")
	require.True(t, exists)
	assert.Equal(t, models.NodeTypeHost, hostNode.Type)
	assert.Equal(t, models.GetNodeColorByType(models.NodeTypeHost), hostNode.Color)

	// Test edges were created
	assert.True(t, len(graph.Edges) > 0)

	// Test node rule types (should be mixed since nodes appear in both ACL and Grant rules)
	devNode, exists := graph.GetNode("group:dev")
	require.True(t, exists)
	assert.Equal(t, models.RuleTypeMixed, devNode.RuleType)
	assert.Equal(t, models.GetNodeShapeByRuleType(models.RuleTypeMixed), devNode.Shape)

	// Test graph statistics
	stats := graph.Stats()
	assert.Greater(t, stats["total_nodes"].(int), 0)
	assert.Greater(t, stats["total_edges"].(int), 0)
}

func TestGraphBuilderNodeTypes(t *testing.T) {
	builder := &GraphBuilder{
		policyData: models.NewPolicyData(),
	}

	// Test group detection
	builder.policyData.Groups["group:test"] = []string{"user@example.com"}
	nodeType := builder.determineNodeType("group:test")
	assert.Equal(t, models.NodeTypeGroup, nodeType)

	// Test tag detection
	builder.policyData.TagOwners["tag:test"] = []string{"user@example.com"}
	nodeType = builder.determineNodeType("tag:test")
	assert.Equal(t, models.NodeTypeTag, nodeType)

	// Test host detection
	builder.policyData.Hosts["host1"] = "10.0.1.100"
	nodeType = builder.determineNodeType("host1")
	assert.Equal(t, models.NodeTypeHost, nodeType)

	// Test prefix-based detection
	nodeType = builder.determineNodeType("group:prefix-group")
	assert.Equal(t, models.NodeTypeGroup, nodeType)

	nodeType = builder.determineNodeType("tag:prefix-tag")
	assert.Equal(t, models.NodeTypeTag, nodeType)

	nodeType = builder.determineNodeType("autogroup:internet")
	assert.Equal(t, models.NodeTypeGroup, nodeType)

	// Test default (unknown should be host)
	nodeType = builder.determineNodeType("unknown-target")
	assert.Equal(t, models.NodeTypeHost, nodeType)
}

func TestGraphBuilderEdgeCreation(t *testing.T) {
	policyData := models.NewPolicyData()
	policyData.ACLs = []models.ACLRule{
		{
			Action: "accept",
			Src:    []string{"group:admin"},
			Dst:    []string{"server1"},
			Proto:  "tcp",
		},
	}

	ruleLineNumbers := &models.RuleLineNumbers{
		ACLs: []int{10},
	}

	builder := NewGraphBuilder(policyData, ruleLineNumbers)
	graph, err := builder.BuildGraph()
	require.NoError(t, err)

	// Should have created an edge from group:admin to server1
	found := false
	for _, edge := range graph.Edges {
		if edge.From == "group:admin" && edge.To == "server1" {
			found = true
			assert.Equal(t, "ACL", edge.Metadata["rule_type"])
			assert.Equal(t, 10, edge.Metadata["line_number"])
			assert.Equal(t, "accept", edge.Metadata["action"])
			assert.Equal(t, "tcp", edge.Metadata["protocol"])
			break
		}
	}
	assert.True(t, found, "Expected edge from group:admin to server1")
}

func TestGraphBuilderGrantRules(t *testing.T) {
	policyData := models.NewPolicyData()
	policyData.Grants = []models.GrantRule{
		{
			Src:        []string{"group:dev"},
			Dst:        []string{"tag:dev"},
			IP:         []string{"tcp:22", "tcp:80"},
			Via:        []string{"gateway"},
			SrcPosture: []string{"posture:secure"},
			DstPosture: []string{"posture:compliant"},
			App: map[string]interface{}{
				"ssh": map[string]interface{}{
					"proto": "tcp",
					"ports": []int{22},
				},
			},
		},
	}

	ruleLineNumbers := &models.RuleLineNumbers{
		Grants: []int{20},
	}

	builder := NewGraphBuilder(policyData, ruleLineNumbers)
	graph, err := builder.BuildGraph()
	require.NoError(t, err)

	// Check that via node was created
	assert.True(t, graph.HasNode("gateway"))

	// Check edge metadata
	found := false
	for _, edge := range graph.Edges {
		if edge.From == "group:dev" && edge.To == "tag:dev" {
			found = true
			assert.Equal(t, "Grant", edge.Metadata["rule_type"])
			assert.Equal(t, 20, edge.Metadata["line_number"])
			
			// Check complex metadata
			if ip, ok := edge.Metadata["ip"].([]string); ok {
				assert.Contains(t, ip, "tcp:22")
				assert.Contains(t, ip, "tcp:80")
			}
			
			if via, ok := edge.Metadata["via"].([]string); ok {
				assert.Contains(t, via, "gateway")
			}
			
			break
		}
	}
	assert.True(t, found, "Expected edge from group:dev to tag:dev")
}

func TestGraphBuilderSearchMetadata(t *testing.T) {
	policyData := models.NewPolicyData()
	policyData.Groups["group:admin"] = []string{"alice@example.com", "bob@example.com"}
	policyData.TagOwners["tag:prod"] = []string{"group:admin"}
	policyData.Hosts["server1"] = "10.0.1.100"

	policyData.ACLs = []models.ACLRule{
		{
			Action: "accept",
			Src:    []string{"group:admin"},
			Dst:    []string{"server1"},
		},
	}

	ruleLineNumbers := &models.RuleLineNumbers{
		ACLs: []int{10},
	}

	builder := NewGraphBuilder(policyData, ruleLineNumbers)
	graph, err := builder.BuildGraph()
	require.NoError(t, err)

	// Test search metadata generation
	metadata := graph.GetSearchMetadata()
	require.NotNil(t, metadata)

	nodes, ok := metadata["nodes"].(map[string]models.NodeMetadata)
	require.True(t, ok)

	// Check group metadata
	if groupMeta, exists := nodes["group:admin"]; exists {
		assert.Equal(t, "group", groupMeta.Type)
		assert.Equal(t, []string{"alice@example.com", "bob@example.com"}, groupMeta.Members)
	}

	// Check tag metadata
	if tagMeta, exists := nodes["tag:prod"]; exists {
		assert.Equal(t, "tag", tagMeta.Type)
		assert.Equal(t, []string{"group:admin"}, tagMeta.Members)
	}

	// Check host metadata
	if hostMeta, exists := nodes["server1"]; exists {
		assert.Equal(t, "host", hostMeta.Type)
		assert.Equal(t, []string{"10.0.1.100"}, hostMeta.Members)
	}
}

func TestGraphBuilderWildcardHandling(t *testing.T) {
	policyData := models.NewPolicyData()
	policyData.ACLs = []models.ACLRule{
		{
			Action: "accept",
			Src:    []string{"*"},
			Dst:    []string{"group:admin"},
		},
		{
			Action: "accept",
			Src:    []string{"group:admin"},
			Dst:    []string{"*"},
		},
	}

	ruleLineNumbers := &models.RuleLineNumbers{
		ACLs: []int{10, 15},
	}

	builder := NewGraphBuilder(policyData, ruleLineNumbers)
	graph, err := builder.BuildGraph()
	require.NoError(t, err)

	// Wildcards should not create nodes
	assert.False(t, graph.HasNode("*"))
	
	// But group:admin should exist
	assert.True(t, graph.HasNode("group:admin"))

	// Should have fewer edges due to wildcard filtering
	edgeCount := len(graph.Edges)
	assert.Equal(t, 0, edgeCount) // No edges should be created with wildcards
}
