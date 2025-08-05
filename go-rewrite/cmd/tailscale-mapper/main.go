package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"

	"github.com/tailscale-network-topology-mapper/go-rewrite/internal/config"
	"github.com/tailscale-network-topology-mapper/go-rewrite/internal/graph"
	"github.com/tailscale-network-topology-mapper/go-rewrite/internal/parser"
	"github.com/tailscale-network-topology-mapper/go-rewrite/internal/renderer"
)

func main() {
	// Parse command line flags
	var (
		debug      = flag.Bool("debug", false, "Enable debug logging")
		policyFile = flag.String("policy", "", "Path to policy file (overrides config)")
		outputFile = flag.String("output", "network_topology.html", "Output HTML file")
	)
	flag.Parse()

	// Set up logging
	if *debug {
		log.SetFlags(log.LstdFlags | log.Lshortfile)
		log.Println("Debug logging enabled")
	} else {
		log.SetFlags(log.LstdFlags)
	}

	log.Println("Starting Tailscale Network Topology Mapper (Go)")

	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	// Override policy file if specified
	if *policyFile != "" {
		cfg.PolicyFile = *policyFile
	}

	// Ensure policy file exists
	if _, err := os.Stat(cfg.PolicyFile); os.IsNotExist(err) {
		log.Fatalf("Policy file not found: %s", cfg.PolicyFile)
	}

	log.Printf("Using policy file: %s", cfg.PolicyFile)
	log.Printf("Company domain: %s", cfg.CompanyDomain)

	// Parse policy file
	log.Println("Parsing policy file...")
	policyParser := parser.NewPolicyParser(cfg.PolicyFile)
	if err := policyParser.ParsePolicy(); err != nil {
		log.Fatalf("Failed to parse policy: %v", err)
	}

	policyData := policyParser.GetPolicyData()
	ruleLineNumbers := policyParser.GetRuleLineNumbers()
	stats := policyParser.GetStats()

	log.Printf("Policy parsing completed: %d groups, %d hosts, %d ACLs, %d grants",
		stats.Groups, stats.Hosts, stats.ACLs, stats.Grants)

	// Build network graph
	log.Println("Building network graph...")
	graphBuilder := graph.NewGraphBuilder(policyData, ruleLineNumbers)
	networkGraph, err := graphBuilder.BuildGraph()
	if err != nil {
		log.Fatalf("Failed to build network graph: %v", err)
	}

	graphStats := networkGraph.Stats()
	log.Printf("Graph building completed: %v", graphStats)

	// Render to HTML
	log.Printf("Rendering to HTML file: %s", *outputFile)
	htmlRenderer := renderer.NewHTMLRenderer(cfg, networkGraph)
	if err := htmlRenderer.RenderToHTML(*outputFile); err != nil {
		log.Fatalf("Failed to render HTML: %v", err)
	}

	// Get absolute path for output
	absPath, err := filepath.Abs(*outputFile)
	if err != nil {
		absPath = *outputFile
	}

	log.Printf("✅ Network topology map generated successfully!")
	log.Printf("📁 Output file: %s", absPath)
	log.Printf("🌐 Open in browser: file://%s", absPath)

	// Print summary
	fmt.Println("\n" + strings.Repeat("=", 60))
	fmt.Println("🎯 TAILSCALE NETWORK TOPOLOGY MAPPER")
	fmt.Println(strings.Repeat("=", 60))
	fmt.Printf("📊 Policy Statistics:\n")
	fmt.Printf("   • Groups: %d\n", stats.Groups)
	fmt.Printf("   • Hosts: %d\n", stats.Hosts)
	fmt.Printf("   • Tag Owners: %d\n", stats.TagOwners)
	fmt.Printf("   • ACL Rules: %d\n", stats.ACLs)
	fmt.Printf("   • Grant Rules: %d\n", stats.Grants)
	fmt.Printf("   • Postures: %d\n", stats.Postures)
	fmt.Println()
	fmt.Printf("🕸️  Graph Statistics:\n")
	if totalNodes, ok := graphStats["total_nodes"].(int); ok {
		fmt.Printf("   • Total Nodes: %d\n", totalNodes)
	}
	if totalEdges, ok := graphStats["total_edges"].(int); ok {
		fmt.Printf("   • Total Edges: %d\n", totalEdges)
	}
	if nodesByType, ok := graphStats["nodes_by_type"].(map[string]interface{}); ok {
		fmt.Printf("   • Node Types:\n")
		for nodeType, count := range nodesByType {
			fmt.Printf("     - %s: %v\n", nodeType, count)
		}
	}
	if nodesByRuleType, ok := graphStats["nodes_by_rule_type"].(map[string]interface{}); ok {
		fmt.Printf("   • Rule Types:\n")
		for ruleType, count := range nodesByRuleType {
			fmt.Printf("     - %s: %v\n", ruleType, count)
		}
	}
	fmt.Println()
	fmt.Printf("📄 Output: %s\n", absPath)
	fmt.Printf("🔗 URL: file://%s\n", absPath)
	fmt.Println(strings.Repeat("=", 60))
	fmt.Println("💡 Tips:")
	fmt.Println("   • Use the search box to filter nodes by any metadata")
	fmt.Println("   • Drag the search box to reposition it")
	fmt.Println("   • Click nodes to highlight their connections")
	fmt.Println("   • Toggle the legend panel for reference")
	fmt.Println("   • Hover over nodes for detailed tooltips")
	fmt.Println(strings.Repeat("=", 60))
}

// printUsage prints usage information
func printUsage() {
	fmt.Fprintf(os.Stderr, "Usage: %s [options]\n", os.Args[0])
	fmt.Fprintf(os.Stderr, "\nTailscale Network Topology Mapper - Go Edition\n")
	fmt.Fprintf(os.Stderr, "Generates interactive HTML visualizations of Tailscale ACL and Grant rules.\n\n")
	fmt.Fprintf(os.Stderr, "Options:\n")
	flag.PrintDefaults()
	fmt.Fprintf(os.Stderr, "\nExamples:\n")
	fmt.Fprintf(os.Stderr, "  %s                                    # Use default policy.hujson\n", os.Args[0])
	fmt.Fprintf(os.Stderr, "  %s -debug                             # Enable debug logging\n", os.Args[0])
	fmt.Fprintf(os.Stderr, "  %s -policy custom.hujson              # Use custom policy file\n", os.Args[0])
	fmt.Fprintf(os.Stderr, "  %s -output topology.html              # Custom output file\n", os.Args[0])
	fmt.Fprintf(os.Stderr, "\nEnvironment Variables:\n")
	fmt.Fprintf(os.Stderr, "  TS_COMPANY_DOMAIN                     # Override company domain\n")
	fmt.Fprintf(os.Stderr, "  TAILSCALE_TAILNET                     # Tailscale tailnet\n")
	fmt.Fprintf(os.Stderr, "  TAILSCALE_OAUTH_CLIENT_ID             # OAuth client ID\n")
	fmt.Fprintf(os.Stderr, "  TAILSCALE_OAUTH_CLIENT_SECRET         # OAuth client secret\n")
	fmt.Fprintf(os.Stderr, "  TS_API_KEY                            # API key (legacy)\n")
	fmt.Fprintf(os.Stderr, "\nFor more information, visit:\n")
	fmt.Fprintf(os.Stderr, "  https://github.com/SimplyMinimal/tailscale-network-topology-mapper\n")
}

func init() {
	flag.Usage = printUsage
}
