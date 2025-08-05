package models

import (
	"encoding/json"
	"fmt"
)

// PolicyData represents the complete Tailscale policy structure
type PolicyData struct {
	Groups     map[string][]string                    `json:"groups,omitempty"`
	Hosts      map[string]string                      `json:"hosts,omitempty"`
	TagOwners  map[string][]string                    `json:"tagOwners,omitempty"`
	ACLs       []ACLRule                              `json:"acls,omitempty"`
	Grants     []GrantRule                            `json:"grants,omitempty"`
	Postures   map[string][]string                    `json:"postures,omitempty"`
	AutoGroups map[string][]string                    `json:"autogroups,omitempty"`
}

// ACLRule represents a legacy ACL rule
type ACLRule struct {
	Action string   `json:"action"`
	Src    []string `json:"src"`
	Dst    []string `json:"dst"`
	Proto  string   `json:"proto,omitempty"`
}

// GrantRule represents a modern grant rule with extended features
type GrantRule struct {
	Src        []string               `json:"src"`
	Dst        []string               `json:"dst"`
	IP         []string               `json:"ip,omitempty"`
	Via        []string               `json:"via,omitempty"`
	SrcPosture []string               `json:"srcPosture,omitempty"`
	DstPosture []string               `json:"dstPosture,omitempty"`
	App        map[string]interface{} `json:"app,omitempty"`
}

// RuleLineNumbers tracks line numbers for rules in the policy file
type RuleLineNumbers struct {
	ACLs   []int `json:"acls"`
	Grants []int `json:"grants"`
}

// PolicyStats provides statistics about the parsed policy
type PolicyStats struct {
	Groups    int `json:"groups"`
	Hosts     int `json:"hosts"`
	TagOwners int `json:"tag_owners"`
	ACLs      int `json:"acls"`
	Grants    int `json:"grants"`
	Postures  int `json:"postures"`
}

// GetStats returns statistics about the policy data
func (p *PolicyData) GetStats() PolicyStats {
	return PolicyStats{
		Groups:    len(p.Groups),
		Hosts:     len(p.Hosts),
		TagOwners: len(p.TagOwners),
		ACLs:      len(p.ACLs),
		Grants:    len(p.Grants),
		Postures:  len(p.Postures),
	}
}

// Validate performs basic validation on the policy data
func (p *PolicyData) Validate() error {
	if p.Groups == nil {
		p.Groups = make(map[string][]string)
	}
	if p.Hosts == nil {
		p.Hosts = make(map[string]string)
	}
	if p.TagOwners == nil {
		p.TagOwners = make(map[string][]string)
	}
	if p.ACLs == nil {
		p.ACLs = []ACLRule{}
	}
	if p.Grants == nil {
		p.Grants = []GrantRule{}
	}
	if p.Postures == nil {
		p.Postures = make(map[string][]string)
	}
	if p.AutoGroups == nil {
		p.AutoGroups = make(map[string][]string)
	}

	// Validate ACL rules
	for i, acl := range p.ACLs {
		if len(acl.Src) == 0 {
			return fmt.Errorf("ACL rule %d: src cannot be empty", i)
		}
		if len(acl.Dst) == 0 {
			return fmt.Errorf("ACL rule %d: dst cannot be empty", i)
		}
		if acl.Action == "" {
			return fmt.Errorf("ACL rule %d: action cannot be empty", i)
		}
	}

	// Validate Grant rules
	for i, grant := range p.Grants {
		if len(grant.Src) == 0 {
			return fmt.Errorf("Grant rule %d: src cannot be empty", i)
		}
		if len(grant.Dst) == 0 {
			return fmt.Errorf("Grant rule %d: dst cannot be empty", i)
		}
	}

	return nil
}

// FromJSON creates PolicyData from JSON bytes
func (p *PolicyData) FromJSON(data []byte) error {
	return json.Unmarshal(data, p)
}

// ToJSON converts PolicyData to JSON bytes
func (p *PolicyData) ToJSON() ([]byte, error) {
	return json.MarshalIndent(p, "", "  ")
}

// GetAllGroups returns all group names including autogroups
func (p *PolicyData) GetAllGroups() []string {
	groups := make([]string, 0, len(p.Groups)+len(p.AutoGroups))
	
	for group := range p.Groups {
		groups = append(groups, group)
	}
	
	for group := range p.AutoGroups {
		groups = append(groups, group)
	}
	
	return groups
}

// GetAllTags returns all tag names from tagOwners
func (p *PolicyData) GetAllTags() []string {
	tags := make([]string, 0, len(p.TagOwners))
	
	for tag := range p.TagOwners {
		tags = append(tags, tag)
	}
	
	return tags
}

// GetAllHosts returns all host names
func (p *PolicyData) GetAllHosts() []string {
	hosts := make([]string, 0, len(p.Hosts))
	
	for host := range p.Hosts {
		hosts = append(hosts, host)
	}
	
	return hosts
}

// IsGroup checks if a name is a group (including autogroups)
func (p *PolicyData) IsGroup(name string) bool {
	if _, exists := p.Groups[name]; exists {
		return true
	}
	if _, exists := p.AutoGroups[name]; exists {
		return true
	}
	return false
}

// IsTag checks if a name is a tag
func (p *PolicyData) IsTag(name string) bool {
	_, exists := p.TagOwners[name]
	return exists
}

// IsHost checks if a name is a host
func (p *PolicyData) IsHost(name string) bool {
	_, exists := p.Hosts[name]
	return exists
}

// GetGroupMembers returns members of a group (including autogroups)
func (p *PolicyData) GetGroupMembers(groupName string) []string {
	if members, exists := p.Groups[groupName]; exists {
		return members
	}
	if members, exists := p.AutoGroups[groupName]; exists {
		return members
	}
	return nil
}

// GetTagOwners returns owners of a tag
func (p *PolicyData) GetTagOwners(tagName string) []string {
	if owners, exists := p.TagOwners[tagName]; exists {
		return owners
	}
	return nil
}

// GetHostIP returns the IP address of a host
func (p *PolicyData) GetHostIP(hostName string) string {
	if ip, exists := p.Hosts[hostName]; exists {
		return ip
	}
	return ""
}

// NewPolicyData creates a new PolicyData instance with initialized maps
func NewPolicyData() *PolicyData {
	return &PolicyData{
		Groups:     make(map[string][]string),
		Hosts:      make(map[string]string),
		TagOwners:  make(map[string][]string),
		ACLs:       []ACLRule{},
		Grants:     []GrantRule{},
		Postures:   make(map[string][]string),
		AutoGroups: make(map[string][]string),
	}
}
