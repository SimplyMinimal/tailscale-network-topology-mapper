package utils

import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"fmt"
	"net"
	"regexp"
	"strings"
)

// ValidateEmail validates an email address format
func ValidateEmail(email string) bool {
	emailRegex := regexp.MustCompile(`^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`)
	return emailRegex.MatchString(email)
}

// ValidateIPAddress validates an IP address (IPv4 or IPv6)
func ValidateIPAddress(ip string) bool {
	return net.ParseIP(ip) != nil
}

// ValidateCIDR validates a CIDR notation
func ValidateCIDR(cidr string) bool {
	_, _, err := net.ParseCIDR(cidr)
	return err == nil
}

// ValidatePort validates a port number
func ValidatePort(port int) bool {
	return port >= 1 && port <= 65535
}

// ValidatePortRange validates a port range string (e.g., "8000-8080")
func ValidatePortRange(portRange string) bool {
	if !strings.Contains(portRange, "-") {
		return false
	}

	parts := strings.Split(portRange, "-")
	if len(parts) != 2 {
		return false
	}

	// Parse start and end ports
	var startPort, endPort int
	if _, err := fmt.Sscanf(parts[0], "%d", &startPort); err != nil {
		return false
	}
	if _, err := fmt.Sscanf(parts[1], "%d", &endPort); err != nil {
		return false
	}

	return ValidatePort(startPort) && ValidatePort(endPort) && startPort <= endPort
}

// ValidateHostname validates a hostname format
func ValidateHostname(hostname string) bool {
	if len(hostname) == 0 || len(hostname) > 253 {
		return false
	}

	// Hostname regex pattern
	hostnameRegex := regexp.MustCompile(`^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$`)
	return hostnameRegex.MatchString(hostname)
}

// ValidateTailscaleTag validates a Tailscale tag format
func ValidateTailscaleTag(tag string) bool {
	if !strings.HasPrefix(tag, "tag:") {
		return false
	}

	tagName := strings.TrimPrefix(tag, "tag:")
	if len(tagName) == 0 {
		return false
	}

	// Tag name should contain only alphanumeric characters, hyphens, and underscores
	tagRegex := regexp.MustCompile(`^[a-zA-Z0-9_-]+$`)
	return tagRegex.MatchString(tagName)
}

// ValidateTailscaleGroup validates a Tailscale group format
func ValidateTailscaleGroup(group string) bool {
	if !strings.HasPrefix(group, "group:") {
		return false
	}

	groupName := strings.TrimPrefix(group, "group:")
	if len(groupName) == 0 {
		return false
	}

	// Group name should contain only alphanumeric characters, hyphens, and underscores
	groupRegex := regexp.MustCompile(`^[a-zA-Z0-9_-]+$`)
	return groupRegex.MatchString(groupName)
}

// ValidateAutogroup validates a Tailscale autogroup format
func ValidateAutogroup(autogroup string) bool {
	if !strings.HasPrefix(autogroup, "autogroup:") {
		return false
	}

	autogroupName := strings.TrimPrefix(autogroup, "autogroup:")
	validAutogroups := []string{
		"internet",
		"self",
		"member",
		"admin",
		"owner",
		"shared",
		"tagged",
	}

	for _, valid := range validAutogroups {
		if autogroupName == valid {
			return true
		}
	}

	return false
}

// SanitizeInput sanitizes user input by removing potentially dangerous characters
func SanitizeInput(input string) string {
	// Remove null bytes
	sanitized := strings.ReplaceAll(input, "\x00", "")

	// Remove control characters except tab, newline, and carriage return
	var result strings.Builder
	for _, r := range sanitized {
		if r >= 32 || r == '\t' || r == '\n' || r == '\r' {
			result.WriteRune(r)
		}
	}

	return result.String()
}

// GenerateRandomString generates a random string of specified length
func GenerateRandomString(length int) (string, error) {
	bytes := make([]byte, length)
	if _, err := rand.Read(bytes); err != nil {
		return "", err
	}
	return base64.URLEncoding.EncodeToString(bytes)[:length], nil
}

// GenerateSecureToken generates a cryptographically secure random token
func GenerateSecureToken(length int) (string, error) {
	bytes := make([]byte, length)
	if _, err := rand.Read(bytes); err != nil {
		return "", err
	}
	return hex.EncodeToString(bytes), nil
}

// HashString creates a SHA-256 hash of a string
func HashString(input string) string {
	hash := sha256.Sum256([]byte(input))
	return hex.EncodeToString(hash[:])
}

// IsPrivateIP checks if an IP address is in a private range
func IsPrivateIP(ip string) bool {
	parsedIP := net.ParseIP(ip)
	if parsedIP == nil {
		return false
	}

	// Check for private IPv4 ranges
	private4Ranges := []string{
		"10.0.0.0/8",
		"172.16.0.0/12",
		"192.168.0.0/16",
		"127.0.0.0/8", // Loopback
	}

	for _, cidr := range private4Ranges {
		_, network, _ := net.ParseCIDR(cidr)
		if network.Contains(parsedIP) {
			return true
		}
	}

	// Check for private IPv6 ranges
	if parsedIP.To4() == nil { // IPv6
		// Link-local
		if strings.HasPrefix(ip, "fe80:") {
			return true
		}
		// Unique local
		if strings.HasPrefix(ip, "fc00:") || strings.HasPrefix(ip, "fd00:") {
			return true
		}
		// Loopback
		if ip == "::1" {
			return true
		}
	}

	return false
}

// IsTailscaleIP checks if an IP address is in the Tailscale CGNAT range
func IsTailscaleIP(ip string) bool {
	parsedIP := net.ParseIP(ip)
	if parsedIP == nil {
		return false
	}

	// Tailscale uses 100.64.0.0/10 (CGNAT range)
	_, tailscaleNetwork, _ := net.ParseCIDR("100.64.0.0/10")
	return tailscaleNetwork.Contains(parsedIP)
}

// ValidateProtocol validates a network protocol name
func ValidateProtocol(protocol string) bool {
	validProtocols := map[string]bool{
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

	return validProtocols[strings.ToLower(protocol)]
}

// EscapeHTML escapes HTML special characters
func EscapeHTML(input string) string {
	replacements := map[string]string{
		"&":  "&amp;",
		"<":  "&lt;",
		">":  "&gt;",
		"\"": "&quot;",
		"'":  "&#39;",
	}

	result := input
	for char, escape := range replacements {
		result = strings.ReplaceAll(result, char, escape)
	}

	return result
}

// ValidateJSONString performs basic JSON string validation
func ValidateJSONString(jsonStr string) bool {
	// Basic validation - check for balanced braces and quotes
	braceCount := 0
	inString := false
	escaped := false

	for i, char := range jsonStr {
		if escaped {
			escaped = false
			continue
		}

		switch char {
		case '\\':
			if inString {
				escaped = true
			}
		case '"':
			inString = !inString
		case '{', '[':
			if !inString {
				braceCount++
			}
		case '}', ']':
			if !inString {
				braceCount--
				if braceCount < 0 {
					return false
				}
			}
		}

		// Check for invalid control characters outside strings
		if !inString && char < 32 && char != '\t' && char != '\n' && char != '\r' {
			return false
		}

		// Check for unterminated string at end
		if i == len(jsonStr)-1 && inString {
			return false
		}
	}

	return braceCount == 0 && !inString
}

// TruncateString truncates a string to a maximum length with ellipsis
func TruncateString(input string, maxLength int) string {
	if len(input) <= maxLength {
		return input
	}

	if maxLength <= 3 {
		return input[:maxLength]
	}

	return input[:maxLength-3] + "..."
}
