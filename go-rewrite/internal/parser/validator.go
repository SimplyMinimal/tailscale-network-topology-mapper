package parser

import (
	"fmt"
	"net"
	"regexp"
	"strconv"
	"strings"

	"github.com/tailscale-network-topology-mapper/go-rewrite/internal/config"
	"github.com/tailscale-network-topology-mapper/go-rewrite/internal/models"
)

// PolicyValidator validates Tailscale policy data
type PolicyValidator struct {
	validProtocols map[string]bool
	emailRegex     *regexp.Regexp
}

// NewPolicyValidator creates a new policy validator
func NewPolicyValidator() *PolicyValidator {
	return &PolicyValidator{
		validProtocols: config.ValidProtocols(),
		emailRegex:     regexp.MustCompile(`^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`),
	}
}

// ValidatePolicy performs comprehensive validation of policy data
func (v *PolicyValidator) ValidatePolicy(policy *models.PolicyData) error {
	if err := v.validateGroups(policy.Groups); err != nil {
		return fmt.Errorf("groups validation failed: %w", err)
	}

	if err := v.validateHosts(policy.Hosts); err != nil {
		return fmt.Errorf("hosts validation failed: %w", err)
	}

	if err := v.validateTagOwners(policy.TagOwners); err != nil {
		return fmt.Errorf("tagOwners validation failed: %w", err)
	}

	if err := v.validateACLs(policy.ACLs); err != nil {
		return fmt.Errorf("ACLs validation failed: %w", err)
	}

	if err := v.validateGrants(policy.Grants); err != nil {
		return fmt.Errorf("grants validation failed: %w", err)
	}

	if err := v.validatePostures(policy.Postures); err != nil {
		return fmt.Errorf("postures validation failed: %w", err)
	}

	return nil
}

// validateGroups validates group definitions
func (v *PolicyValidator) validateGroups(groups map[string][]string) error {
	for groupName, members := range groups {
		if !strings.HasPrefix(groupName, "group:") {
			return fmt.Errorf("group name must start with 'group:': %s", groupName)
		}

		if len(members) == 0 {
			return fmt.Errorf("group cannot be empty: %s", groupName)
		}

		for _, member := range members {
			if err := v.validateGroupMember(member); err != nil {
				return fmt.Errorf("invalid member '%s' in group '%s': %w", member, groupName, err)
			}
		}
	}

	return nil
}

// validateGroupMember validates a single group member
func (v *PolicyValidator) validateGroupMember(member string) error {
	// Check if it's an email address
	if v.emailRegex.MatchString(member) {
		return nil
	}

	// Check if it's a tag reference
	if strings.HasPrefix(member, "tag:") {
		return nil
	}

	// Check if it's another group reference
	if strings.HasPrefix(member, "group:") {
		return nil
	}

	// Check if it's an autogroup
	if strings.HasPrefix(member, "autogroup:") {
		return nil
	}

	return fmt.Errorf("invalid group member format: %s", member)
}

// validateHosts validates host definitions
func (v *PolicyValidator) validateHosts(hosts map[string]string) error {
	for hostName, ip := range hosts {
		if hostName == "" {
			return fmt.Errorf("host name cannot be empty")
		}

		if err := v.validateIPAddress(ip); err != nil {
			return fmt.Errorf("invalid IP address for host '%s': %w", hostName, err)
		}
	}

	return nil
}

// validateIPAddress validates an IP address
func (v *PolicyValidator) validateIPAddress(ip string) error {
	if net.ParseIP(ip) == nil {
		return fmt.Errorf("invalid IP address: %s", ip)
	}
	return nil
}

// validateTagOwners validates tag owner definitions
func (v *PolicyValidator) validateTagOwners(tagOwners map[string][]string) error {
	for tagName, owners := range tagOwners {
		if !strings.HasPrefix(tagName, "tag:") {
			return fmt.Errorf("tag name must start with 'tag:': %s", tagName)
		}

		if len(owners) == 0 {
			return fmt.Errorf("tag must have at least one owner: %s", tagName)
		}

		for _, owner := range owners {
			if !v.emailRegex.MatchString(owner) {
				return fmt.Errorf("tag owner must be a valid email address: %s", owner)
			}
		}
	}

	return nil
}

// validateACLs validates ACL rules
func (v *PolicyValidator) validateACLs(acls []models.ACLRule) error {
	for i, acl := range acls {
		if err := v.validateACLRule(acl, i); err != nil {
			return err
		}
	}
	return nil
}

// validateACLRule validates a single ACL rule
func (v *PolicyValidator) validateACLRule(acl models.ACLRule, index int) error {
	if acl.Action == "" {
		return fmt.Errorf("ACL rule %d: action cannot be empty", index)
	}

	if acl.Action != "accept" && acl.Action != "drop" {
		return fmt.Errorf("ACL rule %d: action must be 'accept' or 'drop', got '%s'", index, acl.Action)
	}

	if len(acl.Src) == 0 {
		return fmt.Errorf("ACL rule %d: src cannot be empty", index)
	}

	if len(acl.Dst) == 0 {
		return fmt.Errorf("ACL rule %d: dst cannot be empty", index)
	}

	for _, src := range acl.Src {
		if err := v.validateRuleTarget(src); err != nil {
			return fmt.Errorf("ACL rule %d: invalid src '%s': %w", index, src, err)
		}
	}

	for _, dst := range acl.Dst {
		if err := v.validateRuleTarget(dst); err != nil {
			return fmt.Errorf("ACL rule %d: invalid dst '%s': %w", index, dst, err)
		}
	}

	if acl.Proto != "" {
		if err := v.validateProtocol(acl.Proto); err != nil {
			return fmt.Errorf("ACL rule %d: invalid protocol '%s': %w", index, acl.Proto, err)
		}
	}

	return nil
}

// validateGrants validates grant rules
func (v *PolicyValidator) validateGrants(grants []models.GrantRule) error {
	for i, grant := range grants {
		if err := v.validateGrantRule(grant, i); err != nil {
			return err
		}
	}
	return nil
}

// validateGrantRule validates a single grant rule
func (v *PolicyValidator) validateGrantRule(grant models.GrantRule, index int) error {
	if len(grant.Src) == 0 {
		return fmt.Errorf("Grant rule %d: src cannot be empty", index)
	}

	if len(grant.Dst) == 0 {
		return fmt.Errorf("Grant rule %d: dst cannot be empty", index)
	}

	for _, src := range grant.Src {
		if err := v.validateRuleTarget(src); err != nil {
			return fmt.Errorf("Grant rule %d: invalid src '%s': %w", index, src, err)
		}
	}

	for _, dst := range grant.Dst {
		if err := v.validateRuleTarget(dst); err != nil {
			return fmt.Errorf("Grant rule %d: invalid dst '%s': %w", index, dst, err)
		}
	}

	for _, ip := range grant.IP {
		if err := v.validateIPProtocol(ip); err != nil {
			return fmt.Errorf("Grant rule %d: invalid IP protocol '%s': %w", index, ip, err)
		}
	}

	for _, via := range grant.Via {
		if err := v.validateRuleTarget(via); err != nil {
			return fmt.Errorf("Grant rule %d: invalid via '%s': %w", index, via, err)
		}
	}

	for _, posture := range grant.SrcPosture {
		if err := v.validatePostureReference(posture); err != nil {
			return fmt.Errorf("Grant rule %d: invalid srcPosture '%s': %w", index, posture, err)
		}
	}

	for _, posture := range grant.DstPosture {
		if err := v.validatePostureReference(posture); err != nil {
			return fmt.Errorf("Grant rule %d: invalid dstPosture '%s': %w", index, posture, err)
		}
	}

	return nil
}

// validateRuleTarget validates a rule target (src/dst)
func (v *PolicyValidator) validateRuleTarget(target string) error {
	// Wildcard
	if target == "*" {
		return nil
	}

	// Group reference
	if strings.HasPrefix(target, "group:") {
		return nil
	}

	// Tag reference
	if strings.HasPrefix(target, "tag:") {
		return nil
	}

	// Autogroup reference
	if strings.HasPrefix(target, "autogroup:") {
		return nil
	}

	// Email address
	if v.emailRegex.MatchString(target) {
		return nil
	}

	// IP address or CIDR
	if _, _, err := net.ParseCIDR(target); err == nil {
		return nil
	}

	if net.ParseIP(target) != nil {
		return nil
	}

	// Host reference (assume valid if not matching other patterns)
	return nil
}

// validateIPProtocol validates an IP protocol specification
func (v *PolicyValidator) validateIPProtocol(ipProto string) error {
	// Wildcard
	if ipProto == "*" {
		return nil
	}

	// Parse protocol:port format
	parts := strings.Split(ipProto, ":")
	if len(parts) != 2 {
		return fmt.Errorf("invalid format, expected 'protocol:port'")
	}

	protocol := parts[0]
	portSpec := parts[1]

	// Validate protocol
	if err := v.validateProtocol(protocol); err != nil {
		return err
	}

	// Validate port specification
	return v.validatePortSpec(portSpec)
}

// validateProtocol validates a network protocol
func (v *PolicyValidator) validateProtocol(protocol string) error {
	if !v.validProtocols[protocol] {
		return fmt.Errorf("unsupported protocol: %s", protocol)
	}
	return nil
}

// validatePortSpec validates a port specification
func (v *PolicyValidator) validatePortSpec(portSpec string) error {
	// Wildcard
	if portSpec == "*" {
		return nil
	}

	// Port range (e.g., "8000-8080")
	if strings.Contains(portSpec, "-") {
		parts := strings.Split(portSpec, "-")
		if len(parts) != 2 {
			return fmt.Errorf("invalid port range format")
		}

		startPort, err := strconv.Atoi(parts[0])
		if err != nil {
			return fmt.Errorf("invalid start port: %s", parts[0])
		}

		endPort, err := strconv.Atoi(parts[1])
		if err != nil {
			return fmt.Errorf("invalid end port: %s", parts[1])
		}

		if startPort < config.MinPort || startPort > config.MaxPort {
			return fmt.Errorf("start port out of range: %d", startPort)
		}

		if endPort < config.MinPort || endPort > config.MaxPort {
			return fmt.Errorf("end port out of range: %d", endPort)
		}

		if startPort > endPort {
			return fmt.Errorf("start port cannot be greater than end port")
		}

		return nil
	}

	// Single port
	port, err := strconv.Atoi(portSpec)
	if err != nil {
		return fmt.Errorf("invalid port number: %s", portSpec)
	}

	if port < config.MinPort || port > config.MaxPort {
		return fmt.Errorf("port out of range: %d", port)
	}

	return nil
}

// validatePostures validates posture definitions
func (v *PolicyValidator) validatePostures(postures map[string][]string) error {
	for postureName, rules := range postures {
		if !strings.HasPrefix(postureName, "posture:") {
			return fmt.Errorf("posture name must start with 'posture:': %s", postureName)
		}

		if len(rules) == 0 {
			return fmt.Errorf("posture must have at least one rule: %s", postureName)
		}

		for _, rule := range rules {
			if err := v.validatePostureRule(rule); err != nil {
				return fmt.Errorf("invalid posture rule in '%s': %w", postureName, err)
			}
		}
	}

	return nil
}

// validatePostureRule validates a single posture rule
func (v *PolicyValidator) validatePostureRule(rule string) error {
	// Basic validation - posture rules have complex syntax
	// This is a simplified validation
	if strings.TrimSpace(rule) == "" {
		return fmt.Errorf("posture rule cannot be empty")
	}

	// Check for basic posture rule patterns
	validPatterns := []string{
		"node:os",
		"node:osVersion",
		"node:tsVersion",
		"node:clientSupports",
	}

	for _, pattern := range validPatterns {
		if strings.Contains(rule, pattern) {
			return nil
		}
	}

	// If no known pattern is found, assume it's valid (extensible)
	return nil
}

// validatePostureReference validates a posture reference
func (v *PolicyValidator) validatePostureReference(posture string) error {
	if !strings.HasPrefix(posture, "posture:") {
		return fmt.Errorf("posture reference must start with 'posture:'")
	}
	return nil
}
