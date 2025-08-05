package parser

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"github.com/tailscale-network-topology-mapper/go-rewrite/internal/models"
	"github.com/tailscale/hujson"
)

// PolicyParser handles parsing of Tailscale policy files
type PolicyParser struct {
	policyFile      string
	policyData      *models.PolicyData
	ruleLineNumbers *models.RuleLineNumbers
}

// NewPolicyParser creates a new policy parser instance
func NewPolicyParser(policyFile string) *PolicyParser {
	return &PolicyParser{
		policyFile:      policyFile,
		policyData:      models.NewPolicyData(),
		ruleLineNumbers: &models.RuleLineNumbers{ACLs: []int{}, Grants: []int{}},
	}
}

// ParsePolicy parses the policy file and extracts all data
func (p *PolicyParser) ParsePolicy() error {
	// Check if file exists
	if _, err := os.Stat(p.policyFile); os.IsNotExist(err) {
		return fmt.Errorf("policy file not found: %s", p.policyFile)
	}

	// Read file content
	content, err := os.ReadFile(p.policyFile)
	if err != nil {
		return fmt.Errorf("failed to read policy file: %w", err)
	}

	// Extract rule line numbers before parsing
	if err := p.extractRuleLineNumbers(string(content)); err != nil {
		return fmt.Errorf("failed to extract rule line numbers: %w", err)
	}

	// Convert HuJSON to JSON if needed
	jsonContent, err := p.convertHuJSONToJSON(string(content))
	if err != nil {
		return fmt.Errorf("failed to convert HuJSON to JSON: %w", err)
	}

	// Parse JSON into policy data
	var rawData map[string]interface{}
	if err := json.Unmarshal([]byte(jsonContent), &rawData); err != nil {
		return fmt.Errorf("failed to parse JSON: %w", err)
	}

	// Convert raw data to PolicyData
	if err := p.convertRawDataToPolicyData(rawData); err != nil {
		return fmt.Errorf("failed to convert raw data: %w", err)
	}

	// Validate the parsed data
	if err := p.policyData.Validate(); err != nil {
		return fmt.Errorf("policy validation failed: %w", err)
	}

	return nil
}

// convertHuJSONToJSON converts HuJSON format to standard JSON using the official Tailscale library
func (p *PolicyParser) convertHuJSONToJSON(content string) (string, error) {
	// Parse the HuJSON content
	ast, err := hujson.Parse([]byte(content))
	if err != nil {
		return "", fmt.Errorf("failed to parse HuJSON: %w", err)
	}

	// Standardize to valid JSON
	ast.Standardize()

	// Convert back to JSON bytes
	jsonBytes := ast.Pack()

	return string(jsonBytes), nil
}

// extractRuleLineNumbers extracts line numbers for ACL and Grant rules
func (p *PolicyParser) extractRuleLineNumbers(content string) error {
	lines := strings.Split(content, "\n")

	inACLs := false
	inGrants := false
	braceDepth := 0

	for i, line := range lines {
		trimmed := strings.TrimSpace(line)

		// Count braces to track nesting
		braceDepth += strings.Count(trimmed, "{") - strings.Count(trimmed, "}")

		// Check for ACLs section
		if strings.Contains(trimmed, `"acls"`) && strings.Contains(trimmed, "[") {
			inACLs = true
			inGrants = false
			continue
		}

		// Check for Grants section
		if strings.Contains(trimmed, `"grants"`) && strings.Contains(trimmed, "[") {
			inGrants = true
			inACLs = false
			continue
		}

		// Reset flags when exiting sections
		if (inACLs || inGrants) && braceDepth <= 0 {
			inACLs = false
			inGrants = false
		}

		// Record line numbers for rule objects
		if (inACLs || inGrants) && strings.Contains(trimmed, "{") {
			lineNum := i + 1 // Convert to 1-based line numbers
			if inACLs {
				p.ruleLineNumbers.ACLs = append(p.ruleLineNumbers.ACLs, lineNum)
			} else if inGrants {
				p.ruleLineNumbers.Grants = append(p.ruleLineNumbers.Grants, lineNum)
			}
		}
	}

	return nil
}

// convertRawDataToPolicyData converts raw JSON data to PolicyData struct
func (p *PolicyParser) convertRawDataToPolicyData(rawData map[string]interface{}) error {
	// Parse groups
	if groups, ok := rawData["groups"].(map[string]interface{}); ok {
		p.policyData.Groups = make(map[string][]string)
		for groupName, members := range groups {
			if memberList, ok := members.([]interface{}); ok {
				var stringMembers []string
				for _, member := range memberList {
					if memberStr, ok := member.(string); ok {
						stringMembers = append(stringMembers, memberStr)
					}
				}
				p.policyData.Groups[groupName] = stringMembers
			}
		}
	}

	// Parse hosts
	if hosts, ok := rawData["hosts"].(map[string]interface{}); ok {
		p.policyData.Hosts = make(map[string]string)
		for hostName, ip := range hosts {
			if ipStr, ok := ip.(string); ok {
				p.policyData.Hosts[hostName] = ipStr
			}
		}
	}

	// Parse tagOwners
	if tagOwners, ok := rawData["tagOwners"].(map[string]interface{}); ok {
		p.policyData.TagOwners = make(map[string][]string)
		for tagName, owners := range tagOwners {
			if ownerList, ok := owners.([]interface{}); ok {
				var stringOwners []string
				for _, owner := range ownerList {
					if ownerStr, ok := owner.(string); ok {
						stringOwners = append(stringOwners, ownerStr)
					}
				}
				p.policyData.TagOwners[tagName] = stringOwners
			}
		}
	}

	// Parse postures
	if postures, ok := rawData["postures"].(map[string]interface{}); ok {
		p.policyData.Postures = make(map[string][]string)
		for postureName, rules := range postures {
			if ruleList, ok := rules.([]interface{}); ok {
				var stringRules []string
				for _, rule := range ruleList {
					if ruleStr, ok := rule.(string); ok {
						stringRules = append(stringRules, ruleStr)
					}
				}
				p.policyData.Postures[postureName] = stringRules
			}
		}
	}

	// Parse ACLs
	if acls, ok := rawData["acls"].([]interface{}); ok {
		for _, aclInterface := range acls {
			if aclMap, ok := aclInterface.(map[string]interface{}); ok {
				acl := models.ACLRule{}

				if action, ok := aclMap["action"].(string); ok {
					acl.Action = action
				}

				if src, ok := aclMap["src"].([]interface{}); ok {
					for _, s := range src {
						if srcStr, ok := s.(string); ok {
							acl.Src = append(acl.Src, srcStr)
						}
					}
				}

				if dst, ok := aclMap["dst"].([]interface{}); ok {
					for _, d := range dst {
						if dstStr, ok := d.(string); ok {
							acl.Dst = append(acl.Dst, dstStr)
						}
					}
				}

				if proto, ok := aclMap["proto"].(string); ok {
					acl.Proto = proto
				}

				p.policyData.ACLs = append(p.policyData.ACLs, acl)
			}
		}
	}

	// Parse Grants
	if grants, ok := rawData["grants"].([]interface{}); ok {
		for _, grantInterface := range grants {
			if grantMap, ok := grantInterface.(map[string]interface{}); ok {
				grant := models.GrantRule{}

				if src, ok := grantMap["src"].([]interface{}); ok {
					for _, s := range src {
						if srcStr, ok := s.(string); ok {
							grant.Src = append(grant.Src, srcStr)
						}
					}
				}

				if dst, ok := grantMap["dst"].([]interface{}); ok {
					for _, d := range dst {
						if dstStr, ok := d.(string); ok {
							grant.Dst = append(grant.Dst, dstStr)
						}
					}
				}

				if ip, ok := grantMap["ip"].([]interface{}); ok {
					for _, i := range ip {
						if ipStr, ok := i.(string); ok {
							grant.IP = append(grant.IP, ipStr)
						}
					}
				}

				if via, ok := grantMap["via"].([]interface{}); ok {
					for _, v := range via {
						if viaStr, ok := v.(string); ok {
							grant.Via = append(grant.Via, viaStr)
						}
					}
				}

				if srcPosture, ok := grantMap["srcPosture"].([]interface{}); ok {
					for _, sp := range srcPosture {
						if spStr, ok := sp.(string); ok {
							grant.SrcPosture = append(grant.SrcPosture, spStr)
						}
					}
				}

				if dstPosture, ok := grantMap["dstPosture"].([]interface{}); ok {
					for _, dp := range dstPosture {
						if dpStr, ok := dp.(string); ok {
							grant.DstPosture = append(grant.DstPosture, dpStr)
						}
					}
				}

				if app, ok := grantMap["app"].(map[string]interface{}); ok {
					grant.App = app
				}

				p.policyData.Grants = append(p.policyData.Grants, grant)
			}
		}
	}

	return nil
}

// GetPolicyData returns the parsed policy data
func (p *PolicyParser) GetPolicyData() *models.PolicyData {
	return p.policyData
}

// GetRuleLineNumbers returns the rule line numbers
func (p *PolicyParser) GetRuleLineNumbers() *models.RuleLineNumbers {
	return p.ruleLineNumbers
}

// GetStats returns statistics about the parsed policy
func (p *PolicyParser) GetStats() models.PolicyStats {
	return p.policyData.GetStats()
}
