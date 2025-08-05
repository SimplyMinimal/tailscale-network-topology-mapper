package models

import (
	"time"
)

// Device represents a Tailscale device from the API
type Device struct {
	ID                   string    `json:"id"`
	Name                 string    `json:"name"`
	Hostname             string    `json:"hostname"`
	ClientVersion        string    `json:"clientVersion"`
	UpdateAvailable      bool      `json:"updateAvailable"`
	OS                   string    `json:"os"`
	Created              time.Time `json:"created"`
	LastSeen             time.Time `json:"lastSeen"`
	KeyExpiryDisabled    bool      `json:"keyExpiryDisabled"`
	Expires              time.Time `json:"expires"`
	Authorized           bool      `json:"authorized"`
	IsExternal           bool      `json:"isExternal"`
	MachineKey           string    `json:"machineKey"`
	NodeKey              string    `json:"nodeKey"`
	BlocksIncomingConnections bool `json:"blocksIncomingConnections"`
	EnabledRoutes        []string  `json:"enabledRoutes"`
	AdvertisedRoutes     []string  `json:"advertisedRoutes"`
	ClientConnectivity   ClientConnectivity `json:"clientConnectivity"`
	Addresses            []string  `json:"addresses"`
	Tags                 []string  `json:"tags"`
	User                 string    `json:"user"`
	Online               bool      `json:"online"`
}

// ClientConnectivity represents the connectivity information for a device
type ClientConnectivity struct {
	Endpoints     []string          `json:"endpoints"`
	Derp          string            `json:"derp"`
	MappingVariesByDestIP bool      `json:"mappingVariesByDestIP"`
	Latency       map[string]Latency `json:"latency"`
	ClientSupports ClientSupports   `json:"clientSupports"`
}

// Latency represents latency information to DERP regions
type Latency struct {
	Preferred bool    `json:"preferred"`
	LatencyMs float64 `json:"latencyMs"`
}

// ClientSupports represents client capability information
type ClientSupports struct {
	HairPinning     bool `json:"hairPinning"`
	IPv6            bool `json:"ipv6"`
	PCP             bool `json:"pcp"`
	PMP             bool `json:"pmp"`
	UPnP            bool `json:"upnp"`
	UDP             bool `json:"udp"`
}

// DeviceList represents a list of devices from the Tailscale API
type DeviceList struct {
	Devices []Device `json:"devices"`
}

// TailnetInfo represents information about a Tailnet
type TailnetInfo struct {
	Name         string `json:"name"`
	ID           string `json:"id"`
	Organization string `json:"organization"`
	DNS          DNS    `json:"dns"`
}

// DNS represents DNS configuration for a Tailnet
type DNS struct {
	Nameservers   []string          `json:"nameservers"`
	SearchDomains []string          `json:"searchDomains"`
	MagicDNS      bool              `json:"magicDNS"`
	Resolvers     []DNSResolver     `json:"resolvers"`
}

// DNSResolver represents a DNS resolver configuration
type DNSResolver struct {
	Addr string `json:"addr"`
}

// PostureCheck represents a device posture check result
type PostureCheck struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	DeviceID    string                 `json:"deviceId"`
	Status      string                 `json:"status"`
	LastChecked time.Time              `json:"lastChecked"`
	Attributes  map[string]interface{} `json:"attributes"`
}

// LiveTopologyData represents the combined live topology data
type LiveTopologyData struct {
	Devices      []Device      `json:"devices"`
	TailnetInfo  TailnetInfo   `json:"tailnetInfo"`
	PostureChecks []PostureCheck `json:"postureChecks"`
	LastUpdated  time.Time     `json:"lastUpdated"`
}

// IsOnline returns true if the device is currently online
func (d *Device) IsOnline() bool {
	return d.Online
}

// IsExpired returns true if the device key has expired
func (d *Device) IsExpired() bool {
	if d.KeyExpiryDisabled {
		return false
	}
	return time.Now().After(d.Expires)
}

// GetPrimaryAddress returns the primary IP address of the device
func (d *Device) GetPrimaryAddress() string {
	if len(d.Addresses) > 0 {
		return d.Addresses[0]
	}
	return ""
}

// HasTag returns true if the device has the specified tag
func (d *Device) HasTag(tag string) bool {
	for _, t := range d.Tags {
		if t == tag {
			return true
		}
	}
	return false
}

// GetTagsString returns a comma-separated string of tags
func (d *Device) GetTagsString() string {
	if len(d.Tags) == 0 {
		return ""
	}
	
	result := d.Tags[0]
	for i := 1; i < len(d.Tags); i++ {
		result += ", " + d.Tags[i]
	}
	return result
}

// GetStatus returns a human-readable status string
func (d *Device) GetStatus() string {
	if !d.Authorized {
		return "unauthorized"
	}
	if d.IsExpired() {
		return "expired"
	}
	if d.IsOnline() {
		return "online"
	}
	return "offline"
}

// GetLastSeenDuration returns how long ago the device was last seen
func (d *Device) GetLastSeenDuration() time.Duration {
	return time.Since(d.LastSeen)
}

// IsExitNode returns true if the device is advertising exit node routes
func (d *Device) IsExitNode() bool {
	for _, route := range d.AdvertisedRoutes {
		if route == "0.0.0.0/0" || route == "::/0" {
			return true
		}
	}
	return false
}

// IsSubnetRouter returns true if the device is advertising subnet routes
func (d *Device) IsSubnetRouter() bool {
	return len(d.AdvertisedRoutes) > 0 && !d.IsExitNode()
}

// GetDeviceType returns a string describing the device type based on its configuration
func (d *Device) GetDeviceType() string {
	if d.IsExitNode() {
		return "exit-node"
	}
	if d.IsSubnetRouter() {
		return "subnet-router"
	}
	if len(d.Tags) > 0 {
		return "tagged-device"
	}
	return "client-device"
}

// NewLiveTopologyData creates a new LiveTopologyData instance
func NewLiveTopologyData() *LiveTopologyData {
	return &LiveTopologyData{
		Devices:       []Device{},
		PostureChecks: []PostureCheck{},
		LastUpdated:   time.Now(),
	}
}

// AddDevice adds a device to the live topology data
func (ltd *LiveTopologyData) AddDevice(device Device) {
	ltd.Devices = append(ltd.Devices, device)
}

// GetDeviceByID returns a device by its ID
func (ltd *LiveTopologyData) GetDeviceByID(id string) (*Device, bool) {
	for i, device := range ltd.Devices {
		if device.ID == id {
			return &ltd.Devices[i], true
		}
	}
	return nil, false
}

// GetDevicesByTag returns all devices with a specific tag
func (ltd *LiveTopologyData) GetDevicesByTag(tag string) []Device {
	var devices []Device
	for _, device := range ltd.Devices {
		if device.HasTag(tag) {
			devices = append(devices, device)
		}
	}
	return devices
}

// GetOnlineDevices returns all online devices
func (ltd *LiveTopologyData) GetOnlineDevices() []Device {
	var devices []Device
	for _, device := range ltd.Devices {
		if device.IsOnline() {
			devices = append(devices, device)
		}
	}
	return devices
}

// GetStats returns statistics about the live topology
func (ltd *LiveTopologyData) GetStats() map[string]interface{} {
	onlineCount := 0
	taggedCount := 0
	exitNodeCount := 0
	subnetRouterCount := 0
	
	for _, device := range ltd.Devices {
		if device.IsOnline() {
			onlineCount++
		}
		if len(device.Tags) > 0 {
			taggedCount++
		}
		if device.IsExitNode() {
			exitNodeCount++
		}
		if device.IsSubnetRouter() {
			subnetRouterCount++
		}
	}
	
	return map[string]interface{}{
		"total_devices":      len(ltd.Devices),
		"online_devices":     onlineCount,
		"tagged_devices":     taggedCount,
		"exit_nodes":         exitNodeCount,
		"subnet_routers":     subnetRouterCount,
		"last_updated":       ltd.LastUpdated,
	}
}
