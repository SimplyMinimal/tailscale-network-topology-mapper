package models

import (
	"encoding/json"
	"fmt"
)

// NodeType represents the type of a network node
type NodeType string

const (
	NodeTypeGroup NodeType = "group"
	NodeTypeTag   NodeType = "tag"
	NodeTypeHost  NodeType = "host"
)

// RuleType represents the type of rule that created a node/edge
type RuleType string

const (
	RuleTypeACL   RuleType = "ACL"
	RuleTypeGrant RuleType = "Grant"
	RuleTypeMixed RuleType = "Mixed"
)

// NodeShape represents the visual shape of a node
type NodeShape string

const (
	NodeShapeDot     NodeShape = "dot"     // ● for ACL-only nodes
	NodeShapeTriangle NodeShape = "triangle" // ▲ for Grant-only nodes
	NodeShapeHexagon NodeShape = "hexagon"  // ⬢ for nodes in both ACL and Grant rules
)

// Node represents a network node in the graph
type Node struct {
	ID       string            `json:"id"`
	Label    string            `json:"label"`
	Color    string            `json:"color"`
	Shape    NodeShape         `json:"shape"`
	Type     NodeType          `json:"type"`
	RuleType RuleType          `json:"rule_type"`
	Tooltip  string            `json:"tooltip"`
	Metadata map[string]interface{} `json:"metadata"`
}

// Edge represents a connection between two nodes
type Edge struct {
	From     string            `json:"from"`
	To       string            `json:"to"`
	Label    string            `json:"label,omitempty"`
	Color    string            `json:"color,omitempty"`
	Metadata map[string]interface{} `json:"metadata"`
}

// NetworkGraph represents the complete network graph
type NetworkGraph struct {
	Nodes    map[string]*Node `json:"nodes"`
	Edges    []*Edge          `json:"edges"`
	Metadata GraphMetadata    `json:"metadata"`
}

// GraphMetadata contains metadata about the graph for search and filtering
type GraphMetadata struct {
	Nodes map[string]NodeMetadata `json:"nodes"`
	Edges map[string]EdgeMetadata `json:"edges"`
}

// NodeMetadata contains searchable metadata for a node
type NodeMetadata struct {
	ID          string   `json:"id"`
	Type        string   `json:"type"`
	RuleType    string   `json:"rule_type"`
	Members     []string `json:"members,omitempty"`
	Protocols   []string `json:"protocols,omitempty"`
	ViaRouting  []string `json:"via_routing,omitempty"`
	Posture     []string `json:"posture,omitempty"`
	Applications []string `json:"applications,omitempty"`
	LineNumbers []int    `json:"line_numbers,omitempty"`
}

// EdgeMetadata contains searchable metadata for an edge
type EdgeMetadata struct {
	From        string   `json:"from"`
	To          string   `json:"to"`
	Protocols   []string `json:"protocols,omitempty"`
	ViaRouting  []string `json:"via_routing,omitempty"`
	Posture     []string `json:"posture,omitempty"`
	Applications []string `json:"applications,omitempty"`
	RuleType    string   `json:"rule_type"`
	LineNumbers []int    `json:"line_numbers,omitempty"`
}

// NewNetworkGraph creates a new empty network graph
func NewNetworkGraph() *NetworkGraph {
	return &NetworkGraph{
		Nodes: make(map[string]*Node),
		Edges: []*Edge{},
		Metadata: GraphMetadata{
			Nodes: make(map[string]NodeMetadata),
			Edges: make(map[string]EdgeMetadata),
		},
	}
}

// AddNode adds a node to the graph
func (g *NetworkGraph) AddNode(node *Node) {
	g.Nodes[node.ID] = node
}

// AddEdge adds an edge to the graph
func (g *NetworkGraph) AddEdge(edge *Edge) {
	g.Edges = append(g.Edges, edge)
}

// GetNode retrieves a node by ID
func (g *NetworkGraph) GetNode(id string) (*Node, bool) {
	node, exists := g.Nodes[id]
	return node, exists
}

// HasNode checks if a node exists in the graph
func (g *NetworkGraph) HasNode(id string) bool {
	_, exists := g.Nodes[id]
	return exists
}

// GetNodeCount returns the number of nodes in the graph
func (g *NetworkGraph) GetNodeCount() int {
	return len(g.Nodes)
}

// GetEdgeCount returns the number of edges in the graph
func (g *NetworkGraph) GetEdgeCount() int {
	return len(g.Edges)
}

// GetNodesByType returns all nodes of a specific type
func (g *NetworkGraph) GetNodesByType(nodeType NodeType) []*Node {
	var nodes []*Node
	for _, node := range g.Nodes {
		if node.Type == nodeType {
			nodes = append(nodes, node)
		}
	}
	return nodes
}

// GetNodesByRuleType returns all nodes created by a specific rule type
func (g *NetworkGraph) GetNodesByRuleType(ruleType RuleType) []*Node {
	var nodes []*Node
	for _, node := range g.Nodes {
		if node.RuleType == ruleType {
			nodes = append(nodes, node)
		}
	}
	return nodes
}

// SetNodeMetadata sets metadata for a node
func (g *NetworkGraph) SetNodeMetadata(nodeID string, metadata NodeMetadata) {
	g.Metadata.Nodes[nodeID] = metadata
}

// SetEdgeMetadata sets metadata for an edge
func (g *NetworkGraph) SetEdgeMetadata(edgeKey string, metadata EdgeMetadata) {
	g.Metadata.Edges[edgeKey] = metadata
}

// GetEdgeKey generates a unique key for an edge
func GetEdgeKey(from, to string) string {
	return fmt.Sprintf("%s->%s", from, to)
}

// ToJSON converts the graph to JSON
func (g *NetworkGraph) ToJSON() ([]byte, error) {
	return json.MarshalIndent(g, "", "  ")
}

// GetSearchMetadata returns metadata formatted for frontend search
func (g *NetworkGraph) GetSearchMetadata() map[string]interface{} {
	return map[string]interface{}{
		"nodes": g.Metadata.Nodes,
		"edges": g.Metadata.Edges,
	}
}

// GetNodeColorByType returns the appropriate color for a node type
func GetNodeColorByType(nodeType NodeType) string {
	switch nodeType {
	case NodeTypeTag:
		return "#00cc66" // Green
	case NodeTypeGroup:
		return "#FFFF00" // Yellow
	case NodeTypeHost:
		return "#ff6666" // Red
	default:
		return "#97C2FC" // Default blue
	}
}

// GetNodeShapeByRuleType returns the appropriate shape for a rule type
func GetNodeShapeByRuleType(ruleType RuleType) NodeShape {
	switch ruleType {
	case RuleTypeACL:
		return NodeShapeDot
	case RuleTypeGrant:
		return NodeShapeTriangle
	case RuleTypeMixed:
		return NodeShapeHexagon
	default:
		return NodeShapeDot
	}
}

// CreateNode creates a new node with the given parameters
func CreateNode(id, label string, nodeType NodeType, ruleType RuleType) *Node {
	return &Node{
		ID:       id,
		Label:    label,
		Color:    GetNodeColorByType(nodeType),
		Shape:    GetNodeShapeByRuleType(ruleType),
		Type:     nodeType,
		RuleType: ruleType,
		Metadata: make(map[string]interface{}),
	}
}

// CreateEdge creates a new edge with the given parameters
func CreateEdge(from, to string) *Edge {
	return &Edge{
		From:     from,
		To:       to,
		Color:    "#848484", // Default gray
		Metadata: make(map[string]interface{}),
	}
}

// Stats returns statistics about the graph
func (g *NetworkGraph) Stats() map[string]interface{} {
	nodesByType := make(map[NodeType]int)
	nodesByRuleType := make(map[RuleType]int)
	
	for _, node := range g.Nodes {
		nodesByType[node.Type]++
		nodesByRuleType[node.RuleType]++
	}
	
	return map[string]interface{}{
		"total_nodes":        len(g.Nodes),
		"total_edges":        len(g.Edges),
		"nodes_by_type":      nodesByType,
		"nodes_by_rule_type": nodesByRuleType,
	}
}
