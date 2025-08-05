package api

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"golang.org/x/oauth2"
	"golang.org/x/oauth2/clientcredentials"

	"github.com/tailscale-network-topology-mapper/go-rewrite/internal/config"
	"github.com/tailscale-network-topology-mapper/go-rewrite/internal/models"
)

// TailscaleAPIClient handles communication with the Tailscale API
type TailscaleAPIClient struct {
	config     *config.TailscaleConfig
	httpClient *http.Client
	baseURL    string
}

// NewTailscaleAPIClient creates a new Tailscale API client
func NewTailscaleAPIClient(cfg *config.TailscaleConfig) (*TailscaleAPIClient, error) {
	client := &TailscaleAPIClient{
		config:  cfg,
		baseURL: "https://api.tailscale.com/api/v2",
	}

	// Set up HTTP client with authentication
	if err := client.setupAuthentication(); err != nil {
		return nil, fmt.Errorf("failed to setup authentication: %w", err)
	}

	return client, nil
}

// setupAuthentication configures OAuth or API key authentication
func (c *TailscaleAPIClient) setupAuthentication() error {
	// Prefer OAuth client credentials flow
	if c.config.OAuthClientID != "" && c.config.OAuthSecret != "" {
		return c.setupOAuthAuthentication()
	}

	// Fallback to API key authentication
	if c.config.APIKey != "" {
		return c.setupAPIKeyAuthentication()
	}

	return fmt.Errorf("no authentication credentials provided")
}

// setupOAuthAuthentication configures OAuth client credentials authentication
func (c *TailscaleAPIClient) setupOAuthAuthentication() error {
	config := &clientcredentials.Config{
		ClientID:     c.config.OAuthClientID,
		ClientSecret: c.config.OAuthSecret,
		TokenURL:     "https://api.tailscale.com/api/v2/oauth/token",
		Scopes:       []string{"devices", "routes"},
	}

	ctx := context.Background()
	c.httpClient = config.Client(ctx)

	return nil
}

// setupAPIKeyAuthentication configures API key authentication
func (c *TailscaleAPIClient) setupAPIKeyAuthentication() error {
	c.httpClient = &http.Client{
		Timeout: 30 * time.Second,
		Transport: &apiKeyTransport{
			apiKey: c.config.APIKey,
			base:   http.DefaultTransport,
		},
	}

	return nil
}

// apiKeyTransport adds API key authentication to requests
type apiKeyTransport struct {
	apiKey string
	base   http.RoundTripper
}

func (t *apiKeyTransport) RoundTrip(req *http.Request) (*http.Response, error) {
	req.Header.Set("Authorization", "Bearer "+t.apiKey)
	return t.base.RoundTrip(req)
}

// ValidateCredentials validates the API credentials
func (c *TailscaleAPIClient) ValidateCredentials() error {
	url := fmt.Sprintf("%s/tailnet/%s/devices", c.baseURL, c.config.Tailnet)
	
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("failed to make request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusUnauthorized {
		return fmt.Errorf("invalid credentials")
	}

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("API request failed with status: %d", resp.StatusCode)
	}

	return nil
}

// GetDevices retrieves all devices from the Tailscale API
func (c *TailscaleAPIClient) GetDevices() ([]models.Device, error) {
	url := fmt.Sprintf("%s/tailnet/%s/devices", c.baseURL, c.config.Tailnet)
	
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to make request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API request failed with status %d: %s", resp.StatusCode, string(body))
	}

	var deviceList models.DeviceList
	if err := json.NewDecoder(resp.Body).Decode(&deviceList); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return deviceList.Devices, nil
}

// GetTailnetInfo retrieves information about the Tailnet
func (c *TailscaleAPIClient) GetTailnetInfo() (*models.TailnetInfo, error) {
	url := fmt.Sprintf("%s/tailnet/%s", c.baseURL, c.config.Tailnet)
	
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to make request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API request failed with status %d: %s", resp.StatusCode, string(body))
	}

	var tailnetInfo models.TailnetInfo
	if err := json.NewDecoder(resp.Body).Decode(&tailnetInfo); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &tailnetInfo, nil
}

// GetPostureChecks retrieves posture check results (if available)
func (c *TailscaleAPIClient) GetPostureChecks() ([]models.PostureCheck, error) {
	// Note: This endpoint may not be available in all Tailscale plans
	// This is a placeholder implementation
	url := fmt.Sprintf("%s/tailnet/%s/posture", c.baseURL, c.config.Tailnet)
	
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to make request: %w", err)
	}
	defer resp.Body.Close()

	// If endpoint doesn't exist, return empty slice
	if resp.StatusCode == http.StatusNotFound {
		return []models.PostureCheck{}, nil
	}

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API request failed with status %d: %s", resp.StatusCode, string(body))
	}

	var postureChecks []models.PostureCheck
	if err := json.NewDecoder(resp.Body).Decode(&postureChecks); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return postureChecks, nil
}

// GetLiveTopologyData retrieves complete live topology data
func (c *TailscaleAPIClient) GetLiveTopologyData() (*models.LiveTopologyData, error) {
	liveData := models.NewLiveTopologyData()

	// Get devices
	devices, err := c.GetDevices()
	if err != nil {
		return nil, fmt.Errorf("failed to get devices: %w", err)
	}
	liveData.Devices = devices

	// Get Tailnet info
	tailnetInfo, err := c.GetTailnetInfo()
	if err != nil {
		// Don't fail if Tailnet info is not available
		fmt.Printf("Warning: Could not retrieve Tailnet info: %v\n", err)
	} else {
		liveData.TailnetInfo = *tailnetInfo
	}

	// Get posture checks (optional)
	postureChecks, err := c.GetPostureChecks()
	if err != nil {
		// Don't fail if posture checks are not available
		fmt.Printf("Warning: Could not retrieve posture checks: %v\n", err)
	} else {
		liveData.PostureChecks = postureChecks
	}

	liveData.LastUpdated = time.Now()

	return liveData, nil
}

// RefreshDevices refreshes device data and returns updated devices
func (c *TailscaleAPIClient) RefreshDevices() ([]models.Device, error) {
	return c.GetDevices()
}

// GetDeviceByID retrieves a specific device by ID
func (c *TailscaleAPIClient) GetDeviceByID(deviceID string) (*models.Device, error) {
	devices, err := c.GetDevices()
	if err != nil {
		return nil, err
	}

	for _, device := range devices {
		if device.ID == deviceID {
			return &device, nil
		}
	}

	return nil, fmt.Errorf("device not found: %s", deviceID)
}

// GetDevicesByTag retrieves all devices with a specific tag
func (c *TailscaleAPIClient) GetDevicesByTag(tag string) ([]models.Device, error) {
	devices, err := c.GetDevices()
	if err != nil {
		return nil, err
	}

	var taggedDevices []models.Device
	for _, device := range devices {
		if device.HasTag(tag) {
			taggedDevices = append(taggedDevices, device)
		}
	}

	return taggedDevices, nil
}

// GetOnlineDevices retrieves all currently online devices
func (c *TailscaleAPIClient) GetOnlineDevices() ([]models.Device, error) {
	devices, err := c.GetDevices()
	if err != nil {
		return nil, err
	}

	var onlineDevices []models.Device
	for _, device := range devices {
		if device.IsOnline() {
			onlineDevices = append(onlineDevices, device)
		}
	}

	return onlineDevices, nil
}

// GetAPIStats returns statistics about API usage
func (c *TailscaleAPIClient) GetAPIStats() map[string]interface{} {
	authMethod := "unknown"
	if c.config.OAuthClientID != "" && c.config.OAuthSecret != "" {
		authMethod = "oauth"
	} else if c.config.APIKey != "" {
		authMethod = "api_key"
	}

	return map[string]interface{}{
		"base_url":      c.baseURL,
		"tailnet":       c.config.Tailnet,
		"auth_method":   authMethod,
		"client_configured": c.httpClient != nil,
	}
}
