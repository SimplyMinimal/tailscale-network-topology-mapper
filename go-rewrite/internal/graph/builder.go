package graph

import (
	"fmt"
	"log"
	"strings"

	"github.com/tailscale-network-topology-mapper/go-rewrite/internal/models"
)

// GraphBuilder builds network graphs from policy data
type GraphBuilder struct {
	policyData      *models.PolicyData
	ruleLineNumbers *models.RuleLineNumbers
	graph           *models.NetworkGraph
	nodeRuleTypes   map[string]models.RuleType // Track which rule types reference each node
}

// NewGraphBuilder creates a new graph builder
func NewGraphBuilder(policyData *models.PolicyData, ruleLineNumbers *models.RuleLineNumbers) *GraphBuilder {
	return &GraphBuilder{
		policyData:      policyData,
		ruleLineNumbers: ruleLineNumbers,
		graph:           models.NewNetworkGraph(),
		nodeRuleTypes:   make(map[string]models.RuleType),
	}
}

// BuildGraph builds the complete network graph from policy data
func (gb *GraphBuilder) BuildGraph() (*models.NetworkGraph, error) {
	log.Printf("Building network graph from policy data")

	// First pass: Process ACL rules
	if err := gb.processACLRules(); err != nil {
		return nil, fmt.Errorf("failed to process ACL rules: %w", err)
	}

	// Second pass: Process Grant rules
	if err := gb.processGrantRules(); err != nil {
		return nil, fmt.Errorf("failed to process Grant rules: %w", err)
	}

	// Third pass: Update node shapes based on rule types
	gb.updateNodeShapes()

	// Fourth pass: Generate search metadata
	gb.generateSearchMetadata()

	log.Printf("Graph building completed: %d nodes, %d edges",
		gb.graph.GetNodeCount(), gb.graph.GetEdgeCount())

	return gb.graph, nil
}

// processACLRules processes all ACL rules and creates nodes/edges
func (gb *GraphBuilder) processACLRules() error {
	log.Printf("Processing %d ACL rules", len(gb.policyData.ACLs))

	for i, acl := range gb.policyData.ACLs {
		lineNum := 0
		if i < len(gb.ruleLineNumbers.ACLs) {
			lineNum = gb.ruleLineNumbers.ACLs[i]
		}

		if err := gb.processACLRule(acl, lineNum); err != nil {
			return fmt.Errorf("failed to process ACL rule %d: %w", i, err)
		}
	}

	return nil
}

// processACLRule processes a single ACL rule
func (gb *GraphBuilder) processACLRule(acl models.ACLRule, lineNum int) error {
	// Create nodes for all sources and destinations
	for _, src := range acl.Src {
		gb.createNodeFromTarget(src, models.RuleTypeACL, lineNum)
	}

	for _, dst := range acl.Dst {
		gb.createNodeFromTarget(dst, models.RuleTypeACL, lineNum)
	}

	// Create edges between sources and destinations
	for _, src := range acl.Src {
		for _, dst := range acl.Dst {
			gb.createEdge(src, dst, models.RuleTypeACL, lineNum, map[string]interface{}{
				"action":   acl.Action,
				"protocol": acl.Proto,
			})
		}
	}

	return nil
}

// processGrantRules processes all Grant rules and creates nodes/edges
func (gb *GraphBuilder) processGrantRules() error {
	log.Printf("Processing %d Grant rules", len(gb.policyData.Grants))

	for i, grant := range gb.policyData.Grants {
		lineNum := 0
		if i < len(gb.ruleLineNumbers.Grants) {
			lineNum = gb.ruleLineNumbers.Grants[i]
		}

		if err := gb.processGrantRule(grant, lineNum); err != nil {
			return fmt.Errorf("failed to process Grant rule %d: %w", i, err)
		}
	}

	return nil
}

// processGrantRule processes a single Grant rule
func (gb *GraphBuilder) processGrantRule(grant models.GrantRule, lineNum int) error {
	// Create nodes for all sources and destinations
	for _, src := range grant.Src {
		gb.createNodeFromTarget(src, models.RuleTypeGrant, lineNum)
	}

	for _, dst := range grant.Dst {
		gb.createNodeFromTarget(dst, models.RuleTypeGrant, lineNum)
	}

	// Create nodes for via routing
	for _, via := range grant.Via {
		gb.createNodeFromTarget(via, models.RuleTypeGrant, lineNum)
	}

	// Create edges between sources and destinations
	for _, src := range grant.Src {
		for _, dst := range grant.Dst {
			gb.createEdge(src, dst, models.RuleTypeGrant, lineNum, map[string]interface{}{
				"ip":         grant.IP,
				"via":        grant.Via,
				"srcPosture": grant.SrcPosture,
				"dstPosture": grant.DstPosture,
				"app":        grant.App,
			})
		}
	}

	return nil
}

// createNodeFromTarget creates a node from a rule target (src/dst)
func (gb *GraphBuilder) createNodeFromTarget(target string, ruleType models.RuleType, lineNum int) {
	// Skip wildcards
	if target == "*" {
		return
	}

	// Determine node type and create node if it doesn't exist
	nodeType := gb.determineNodeType(target)

	if !gb.graph.HasNode(target) {
		node := models.CreateNode(target, target, nodeType, ruleType)
		node.Tooltip = gb.generateNodeTooltip(target, nodeType)
		gb.graph.AddNode(node)
		gb.nodeRuleTypes[target] = ruleType
	} else {
		// Update rule type if node exists
		if existingRuleType, exists := gb.nodeRuleTypes[target]; exists {
			if existingRuleType != ruleType {
				gb.nodeRuleTypes[target] = models.RuleTypeMixed
			}
		}
	}
}

// determineNodeType determines the type of a node based on its name
func (gb *GraphBuilder) determineNodeType(target string) models.NodeType {
	// Check if it's a group
	if strings.HasPrefix(target, "group:") || strings.HasPrefix(target, "autogroup:") {
		return models.NodeTypeGroup
	}

	// Check if it's a tag
	if strings.HasPrefix(target, "tag:") {
		return models.NodeTypeTag
	}

	// Check if it's in the groups map
	if gb.policyData.IsGroup(target) {
		return models.NodeTypeGroup
	}

	// Check if it's in the tagOwners map
	if gb.policyData.IsTag(target) {
		return models.NodeTypeTag
	}

	// Check if it's in the hosts map
	if gb.policyData.IsHost(target) {
		return models.NodeTypeHost
	}

	// Default to host for unknown targets
	return models.NodeTypeHost
}

// createEdge creates an edge between two nodes
func (gb *GraphBuilder) createEdge(from, to string, ruleType models.RuleType, lineNum int, metadata map[string]interface{}) {
	// Skip wildcards
	if from == "*" || to == "*" {
		return
	}

	edge := models.CreateEdge(from, to)
	edge.Metadata = metadata
	edge.Metadata["rule_type"] = string(ruleType)
	edge.Metadata["line_number"] = lineNum

	gb.graph.AddEdge(edge)

	// Set edge metadata for search
	edgeKey := models.GetEdgeKey(from, to)
	edgeMetadata := models.EdgeMetadata{
		From:        from,
		To:          to,
		RuleType:    string(ruleType),
		LineNumbers: []int{lineNum},
	}

	// Extract protocols from metadata
	if protocols, ok := metadata["ip"].([]string); ok {
		edgeMetadata.Protocols = protocols
	}
	if protocol, ok := metadata["protocol"].(string); ok && protocol != "" {
		edgeMetadata.Protocols = []string{protocol}
	}

	// Extract via routing
	if via, ok := metadata["via"].([]string); ok {
		edgeMetadata.ViaRouting = via
	}

	// Extract posture checks
	if srcPosture, ok := metadata["srcPosture"].([]string); ok {
		edgeMetadata.Posture = append(edgeMetadata.Posture, srcPosture...)
	}
	if dstPosture, ok := metadata["dstPosture"].([]string); ok {
		edgeMetadata.Posture = append(edgeMetadata.Posture, dstPosture...)
	}

	// Extract applications
	if app, ok := metadata["app"].(map[string]interface{}); ok {
		for appName := range app {
			edgeMetadata.Applications = append(edgeMetadata.Applications, appName)
		}
	}

	gb.graph.SetEdgeMetadata(edgeKey, edgeMetadata)
}

// updateNodeShapes updates node shapes based on rule types
func (gb *GraphBuilder) updateNodeShapes() {
	log.Printf("Updating node shapes based on rule types")

	for nodeID, ruleType := range gb.nodeRuleTypes {
		if node, exists := gb.graph.GetNode(nodeID); exists {
			node.RuleType = ruleType
			node.Shape = models.GetNodeShapeByRuleType(ruleType)
		}
	}
}

// generateSearchMetadata generates metadata for search functionality
func (gb *GraphBuilder) generateSearchMetadata() {
	log.Printf("Generating search metadata")

	for nodeID, node := range gb.graph.Nodes {
		metadata := models.NodeMetadata{
			ID:       nodeID,
			Type:     string(node.Type),
			RuleType: string(node.RuleType),
		}

		// Add group members
		if node.Type == models.NodeTypeGroup {
			if members := gb.policyData.GetGroupMembers(nodeID); members != nil {
				metadata.Members = members
			}
		}

		// Add tag owners
		if node.Type == models.NodeTypeTag {
			if owners := gb.policyData.GetTagOwners(nodeID); owners != nil {
				metadata.Members = owners
			}
		}

		// Add host IP
		if node.Type == models.NodeTypeHost {
			if ip := gb.policyData.GetHostIP(nodeID); ip != "" {
				metadata.Members = []string{ip}
			}
		}

		gb.graph.SetNodeMetadata(nodeID, metadata)
	}
}

// generateNodeTooltip generates a tooltip for a node
func (gb *GraphBuilder) generateNodeTooltip(nodeID string, nodeType models.NodeType) string {
	var tooltip strings.Builder

	tooltip.WriteString(fmt.Sprintf("%s\n", nodeID))
	tooltip.WriteString(fmt.Sprintf("Type: %s\n", nodeType))

	switch nodeType {
	case models.NodeTypeGroup:
		if members := gb.policyData.GetGroupMembers(nodeID); members != nil {
			tooltip.WriteString(fmt.Sprintf("Members: %s\n", strings.Join(members, ", ")))
		}
	case models.NodeTypeTag:
		if owners := gb.policyData.GetTagOwners(nodeID); owners != nil {
			tooltip.WriteString(fmt.Sprintf("Owners: %s\n", strings.Join(owners, ", ")))
		}
	case models.NodeTypeHost:
		if ip := gb.policyData.GetHostIP(nodeID); ip != "" {
			tooltip.WriteString(fmt.Sprintf("IP: %s\n", ip))
		}
	}

	return tooltip.String()
}

// GetGraph returns the built graph
func (gb *GraphBuilder) GetGraph() *models.NetworkGraph {
	return gb.graph
}
