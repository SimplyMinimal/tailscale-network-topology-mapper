package config

import (
	"os"
	"path/filepath"

	"github.com/spf13/viper"
)

// Config holds all configuration for the application
type Config struct {
	// Company domain for email validation
	CompanyDomain string `mapstructure:"company_domain"`

	// Policy file path
	PolicyFile string `mapstructure:"policy_file"`

	// Server configuration
	Server ServerConfig `mapstructure:"server"`

	// Tailscale API configuration
	Tailscale TailscaleConfig `mapstructure:"tailscale"`

	// Visualization configuration
	Visualization VisualizationConfig `mapstructure:"visualization"`

	// Node colors
	NodeColors NodeColorsConfig `mapstructure:"node_colors"`

	// Network options
	NetworkOptions NetworkOptionsConfig `mapstructure:"network_options"`
}

// ServerConfig holds HTTP server configuration
type ServerConfig struct {
	Host string `mapstructure:"host"`
	Port int    `mapstructure:"port"`
}

// TailscaleConfig holds Tailscale API configuration
type TailscaleConfig struct {
	Tailnet       string `mapstructure:"tailnet"`
	OAuthClientID string `mapstructure:"oauth_client_id"`
	OAuthSecret   string `mapstructure:"oauth_secret"`
	APIKey        string `mapstructure:"api_key"`
}

// VisualizationConfig holds visualization settings
type VisualizationConfig struct {
	Height                string `mapstructure:"height"`
	Width                 string `mapstructure:"width"`
	Directed              bool   `mapstructure:"directed"`
	FilterMenu            bool   `mapstructure:"filter_menu"`
	SelectMenu            bool   `mapstructure:"select_menu"`
	NeighborhoodHighlight bool   `mapstructure:"neighborhood_highlight"`
	CDNResources          string `mapstructure:"cdn_resources"`
}

// NodeColorsConfig holds color scheme for different node types
type NodeColorsConfig struct {
	Tag   string `mapstructure:"tag"`
	Group string `mapstructure:"group"`
	Host  string `mapstructure:"host"`
}

// NetworkOptionsConfig holds network visualization options
type NetworkOptionsConfig struct {
	Physics     PhysicsConfig     `mapstructure:"physics"`
	Interaction InteractionConfig `mapstructure:"interaction"`
	Zoom        ZoomConfig        `mapstructure:"zoom"`
}

// PhysicsConfig holds physics simulation settings
type PhysicsConfig struct {
	Enabled       bool `mapstructure:"enabled"`
	Stabilization struct {
		Iterations int `mapstructure:"iterations"`
	} `mapstructure:"stabilization"`
	BarnesHut struct {
		GravitationalConstant float64 `mapstructure:"gravitational_constant"`
		CentralGravity        float64 `mapstructure:"central_gravity"`
		SpringLength          float64 `mapstructure:"spring_length"`
		SpringConstant        float64 `mapstructure:"spring_constant"`
		Damping               float64 `mapstructure:"damping"`
	} `mapstructure:"barnes_hut"`
}

// InteractionConfig holds interaction settings
type InteractionConfig struct {
	Hover                bool `mapstructure:"hover"`
	SelectConnectedEdges bool `mapstructure:"select_connected_edges"`
	TooltipDelay         int  `mapstructure:"tooltip_delay"`
}

// ZoomConfig holds zoom settings
type ZoomConfig struct {
	Speed   float64 `mapstructure:"speed"`
	Enabled bool    `mapstructure:"enabled"`
}

// Load loads configuration from environment variables and defaults
func Load() (*Config, error) {
	viper.SetConfigName("config")
	viper.SetConfigType("yaml")
	viper.AddConfigPath(".")
	viper.AddConfigPath("./config")

	// Set defaults
	setDefaults()

	// Read environment variables
	viper.AutomaticEnv()
	viper.SetEnvPrefix("TS")

	// Try to read config file (optional)
	if err := viper.ReadInConfig(); err != nil {
		// Config file not found is OK, we'll use defaults and env vars
		if _, ok := err.(viper.ConfigFileNotFoundError); !ok {
			return nil, err
		}
	}

	var config Config
	if err := viper.Unmarshal(&config); err != nil {
		return nil, err
	}

	// Override with environment variables
	if domain := os.Getenv("TS_COMPANY_DOMAIN"); domain != "" {
		config.CompanyDomain = domain
	}

	if tailnet := os.Getenv("TAILSCALE_TAILNET"); tailnet != "" {
		config.Tailscale.Tailnet = tailnet
	}

	if clientID := os.Getenv("TAILSCALE_OAUTH_CLIENT_ID"); clientID != "" {
		config.Tailscale.OAuthClientID = clientID
	}

	if secret := os.Getenv("TAILSCALE_OAUTH_CLIENT_SECRET"); secret != "" {
		config.Tailscale.OAuthSecret = secret
	}

	if apiKey := os.Getenv("TS_API_KEY"); apiKey != "" {
		config.Tailscale.APIKey = apiKey
	}

	// Set policy file path if not specified
	if config.PolicyFile == "" {
		wd, _ := os.Getwd()
		config.PolicyFile = filepath.Join(wd, "policy.hujson")
	}

	return &config, nil
}

// setDefaults sets default configuration values
func setDefaults() {
	// Company domain
	viper.SetDefault("company_domain", "example.com")

	// Server
	viper.SetDefault("server.host", "0.0.0.0")
	viper.SetDefault("server.port", 8080)

	// Visualization
	viper.SetDefault("visualization.height", "800px")
	viper.SetDefault("visualization.width", "100%")
	viper.SetDefault("visualization.directed", true)
	viper.SetDefault("visualization.filter_menu", false)
	viper.SetDefault("visualization.select_menu", true)
	viper.SetDefault("visualization.neighborhood_highlight", true)
	viper.SetDefault("visualization.cdn_resources", "remote")

	// Node colors
	viper.SetDefault("node_colors.tag", "#00cc66")
	viper.SetDefault("node_colors.group", "#FFFF00")
	viper.SetDefault("node_colors.host", "#ff6666")

	// Network options
	viper.SetDefault("network_options.physics.enabled", true)
	viper.SetDefault("network_options.physics.stabilization.iterations", 100)
	viper.SetDefault("network_options.physics.barnes_hut.gravitational_constant", -2000.0)
	viper.SetDefault("network_options.physics.barnes_hut.central_gravity", 0.3)
	viper.SetDefault("network_options.physics.barnes_hut.spring_length", 95.0)
	viper.SetDefault("network_options.physics.barnes_hut.spring_constant", 0.04)
	viper.SetDefault("network_options.physics.barnes_hut.damping", 0.09)
	viper.SetDefault("network_options.interaction.hover", true)
	viper.SetDefault("network_options.interaction.select_connected_edges", true)
	viper.SetDefault("network_options.interaction.tooltip_delay", 200)
	viper.SetDefault("network_options.zoom.speed", 0.25)
	viper.SetDefault("network_options.zoom.enabled", true)
}

// ValidProtocols returns the set of valid network protocols
func ValidProtocols() map[string]bool {
	return map[string]bool{
		"tcp":       true,
		"udp":       true,
		"icmp":      true,
		"ah":        true,
		"esp":       true,
		"gre":       true,
		"ipv6-icmp": true,
		"ospf":      true,
		"sctp":      true,
	}
}

// PortRange constants
const (
	MinPort = 1
	MaxPort = 65535
)
