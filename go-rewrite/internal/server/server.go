package server

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"github.com/gorilla/mux"

	"github.com/tailscale-network-topology-mapper/go-rewrite/internal/api"
	"github.com/tailscale-network-topology-mapper/go-rewrite/internal/config"
	"github.com/tailscale-network-topology-mapper/go-rewrite/internal/graph"
	"github.com/tailscale-network-topology-mapper/go-rewrite/internal/models"
	"github.com/tailscale-network-topology-mapper/go-rewrite/internal/parser"
	"github.com/tailscale-network-topology-mapper/go-rewrite/internal/renderer"
)

// Server represents the HTTP server
type Server struct {
	config       *config.Config
	router       *mux.Router
	httpServer   *http.Server
	apiClient    *api.TailscaleAPIClient
	policyData   *models.PolicyData
	networkGraph *models.NetworkGraph
}

// NewServer creates a new HTTP server instance
func NewServer(cfg *config.Config) (*Server, error) {
	server := &Server{
		config: cfg,
		router: mux.NewRouter(),
	}

	// Initialize Tailscale API client if configured
	if cfg.Tailscale.Tailnet != "" {
		apiClient, err := api.NewTailscaleAPIClient(&cfg.Tailscale)
		if err != nil {
			log.Printf("Warning: Failed to initialize Tailscale API client: %v", err)
		} else {
			server.apiClient = apiClient
		}
	}

	// Load and parse policy data
	if err := server.loadPolicyData(); err != nil {
		return nil, fmt.Errorf("failed to load policy data: %w", err)
	}

	// Set up routes
	server.setupRoutes()

	// Create HTTP server
	server.httpServer = &http.Server{
		Addr:         fmt.Sprintf("%s:%d", cfg.Server.Host, cfg.Server.Port),
		Handler:      server.router,
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	return server, nil
}

// loadPolicyData loads and parses the policy file
func (s *Server) loadPolicyData() error {
	log.Printf("Loading policy data from: %s", s.config.PolicyFile)

	// Parse policy file
	policyParser := parser.NewPolicyParser(s.config.PolicyFile)
	if err := policyParser.ParsePolicy(); err != nil {
		return fmt.Errorf("failed to parse policy: %w", err)
	}

	s.policyData = policyParser.GetPolicyData()
	ruleLineNumbers := policyParser.GetRuleLineNumbers()

	// Build network graph
	graphBuilder := graph.NewGraphBuilder(s.policyData, ruleLineNumbers)
	networkGraph, err := graphBuilder.BuildGraph()
	if err != nil {
		return fmt.Errorf("failed to build network graph: %w", err)
	}

	s.networkGraph = networkGraph

	stats := s.policyData.GetStats()
	log.Printf("Policy loaded: %d groups, %d hosts, %d ACLs, %d grants",
		stats.Groups, stats.Hosts, stats.ACLs, stats.Grants)

	return nil
}

// setupRoutes configures all HTTP routes
func (s *Server) setupRoutes() {
	// Static file serving
	s.router.HandleFunc("/", s.handleIndex).Methods("GET")
	s.router.HandleFunc("/network_topology.html", s.handleNetworkTopology).Methods("GET")

	// API routes
	api := s.router.PathPrefix("/api/v1").Subrouter()
	api.HandleFunc("/health", s.handleHealth).Methods("GET")
	api.HandleFunc("/stats", s.handleStats).Methods("GET")
	api.HandleFunc("/policy", s.handlePolicy).Methods("GET")
	api.HandleFunc("/graph", s.handleGraph).Methods("GET")
	api.HandleFunc("/graph/metadata", s.handleGraphMetadata).Methods("GET")

	// Live topology API routes (if API client is available)
	if s.apiClient != nil {
		api.HandleFunc("/devices", s.handleDevices).Methods("GET")
		api.HandleFunc("/devices/{id}", s.handleDeviceByID).Methods("GET")
		api.HandleFunc("/devices/tag/{tag}", s.handleDevicesByTag).Methods("GET")
		api.HandleFunc("/devices/online", s.handleOnlineDevices).Methods("GET")
		api.HandleFunc("/live-topology", s.handleLiveTopology).Methods("GET")
		api.HandleFunc("/tailnet", s.handleTailnetInfo).Methods("GET")
	}

	// Admin routes
	admin := s.router.PathPrefix("/admin").Subrouter()
	admin.HandleFunc("/reload", s.handleReload).Methods("POST")
	admin.HandleFunc("/generate", s.handleGenerate).Methods("POST")

	// Add CORS middleware
	s.router.Use(s.corsMiddleware)
	s.router.Use(s.loggingMiddleware)
}

// Start starts the HTTP server
func (s *Server) Start() error {
	log.Printf("Starting server on %s", s.httpServer.Addr)
	return s.httpServer.ListenAndServe()
}

// Stop gracefully stops the HTTP server
func (s *Server) Stop(ctx context.Context) error {
	log.Println("Stopping server...")
	return s.httpServer.Shutdown(ctx)
}

// handleIndex serves the main index page
func (s *Server) handleIndex(w http.ResponseWriter, r *http.Request) {
	// Redirect to network topology
	http.Redirect(w, r, "/network_topology.html", http.StatusFound)
}

// handleNetworkTopology serves the network topology HTML
func (s *Server) handleNetworkTopology(w http.ResponseWriter, r *http.Request) {
	// Generate HTML on-the-fly
	htmlRenderer := renderer.NewHTMLRenderer(s.config, s.networkGraph)
	
	// Create temporary file
	tempFile := filepath.Join(os.TempDir(), "network_topology.html")
	if err := htmlRenderer.RenderToHTML(tempFile); err != nil {
		http.Error(w, fmt.Sprintf("Failed to generate HTML: %v", err), http.StatusInternalServerError)
		return
	}
	defer os.Remove(tempFile)

	// Serve the file
	http.ServeFile(w, r, tempFile)
}

// handleHealth returns server health status
func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	health := map[string]interface{}{
		"status":    "healthy",
		"timestamp": time.Now().UTC(),
		"version":   "1.0.0",
		"services": map[string]interface{}{
			"policy_parser": "available",
			"graph_builder": "available",
			"html_renderer": "available",
		},
	}

	if s.apiClient != nil {
		if err := s.apiClient.ValidateCredentials(); err != nil {
			health["services"].(map[string]interface{})["tailscale_api"] = "error: " + err.Error()
		} else {
			health["services"].(map[string]interface{})["tailscale_api"] = "available"
		}
	} else {
		health["services"].(map[string]interface{})["tailscale_api"] = "not_configured"
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(health)
}

// handleStats returns statistics about the policy and graph
func (s *Server) handleStats(w http.ResponseWriter, r *http.Request) {
	stats := map[string]interface{}{
		"policy": s.policyData.GetStats(),
		"graph":  s.networkGraph.Stats(),
	}

	if s.apiClient != nil {
		stats["api"] = s.apiClient.GetAPIStats()
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(stats)
}

// handlePolicy returns the parsed policy data
func (s *Server) handlePolicy(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(s.policyData)
}

// handleGraph returns the network graph data
func (s *Server) handleGraph(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(s.networkGraph)
}

// handleGraphMetadata returns the graph search metadata
func (s *Server) handleGraphMetadata(w http.ResponseWriter, r *http.Request) {
	metadata := s.networkGraph.GetSearchMetadata()
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(metadata)
}

// handleDevices returns all devices from Tailscale API
func (s *Server) handleDevices(w http.ResponseWriter, r *http.Request) {
	if s.apiClient == nil {
		http.Error(w, "Tailscale API not configured", http.StatusServiceUnavailable)
		return
	}

	devices, err := s.apiClient.GetDevices()
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to get devices: %v", err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(devices)
}

// handleDeviceByID returns a specific device by ID
func (s *Server) handleDeviceByID(w http.ResponseWriter, r *http.Request) {
	if s.apiClient == nil {
		http.Error(w, "Tailscale API not configured", http.StatusServiceUnavailable)
		return
	}

	vars := mux.Vars(r)
	deviceID := vars["id"]

	device, err := s.apiClient.GetDeviceByID(deviceID)
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to get device: %v", err), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(device)
}

// handleDevicesByTag returns devices with a specific tag
func (s *Server) handleDevicesByTag(w http.ResponseWriter, r *http.Request) {
	if s.apiClient == nil {
		http.Error(w, "Tailscale API not configured", http.StatusServiceUnavailable)
		return
	}

	vars := mux.Vars(r)
	tag := vars["tag"]

	devices, err := s.apiClient.GetDevicesByTag(tag)
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to get devices by tag: %v", err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(devices)
}

// handleOnlineDevices returns all online devices
func (s *Server) handleOnlineDevices(w http.ResponseWriter, r *http.Request) {
	if s.apiClient == nil {
		http.Error(w, "Tailscale API not configured", http.StatusServiceUnavailable)
		return
	}

	devices, err := s.apiClient.GetOnlineDevices()
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to get online devices: %v", err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(devices)
}

// handleLiveTopology returns complete live topology data
func (s *Server) handleLiveTopology(w http.ResponseWriter, r *http.Request) {
	if s.apiClient == nil {
		http.Error(w, "Tailscale API not configured", http.StatusServiceUnavailable)
		return
	}

	liveData, err := s.apiClient.GetLiveTopologyData()
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to get live topology: %v", err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(liveData)
}

// handleTailnetInfo returns Tailnet information
func (s *Server) handleTailnetInfo(w http.ResponseWriter, r *http.Request) {
	if s.apiClient == nil {
		http.Error(w, "Tailscale API not configured", http.StatusServiceUnavailable)
		return
	}

	tailnetInfo, err := s.apiClient.GetTailnetInfo()
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to get Tailnet info: %v", err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(tailnetInfo)
}

// handleReload reloads the policy data
func (s *Server) handleReload(w http.ResponseWriter, r *http.Request) {
	if err := s.loadPolicyData(); err != nil {
		http.Error(w, fmt.Sprintf("Failed to reload policy: %v", err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "reloaded"})
}

// handleGenerate generates a new HTML file
func (s *Server) handleGenerate(w http.ResponseWriter, r *http.Request) {
	outputFile := "network_topology.html"
	if filename := r.URL.Query().Get("filename"); filename != "" {
		outputFile = filename
	}

	htmlRenderer := renderer.NewHTMLRenderer(s.config, s.networkGraph)
	if err := htmlRenderer.RenderToHTML(outputFile); err != nil {
		http.Error(w, fmt.Sprintf("Failed to generate HTML: %v", err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"status":   "generated",
		"filename": outputFile,
	})
}
