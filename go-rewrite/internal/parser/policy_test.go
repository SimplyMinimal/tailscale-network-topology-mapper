package parser

import (
	"encoding/json"
	"os"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestPolicyParser(t *testing.T) {
	// Create a temporary test policy file
	testPolicy := `{
		// Test policy with comments
		"groups": {
			"group:admin": ["alice@example.com", "bob@example.com"],
			"group:dev": ["dev@example.com"]
		},
		"hosts": {
			"server1": "10.0.1.100",
			"server2": "10.0.1.101"
		},
		"tagOwners": {
			"tag:prod": ["group:admin"],
			"tag:dev": ["group:dev"]
		},
		"acls": [
			{
				"action": "accept",
				"src": ["group:admin"],
				"dst": ["*:*"]
			}
		],
		"grants": [
			{
				"src": ["group:dev"],
				"dst": ["tag:dev"],
				"ip": ["tcp:22", "tcp:80"]
			}
		]
	}`

	// Create temporary file
	tmpFile, err := os.CreateTemp("", "test-policy-*.hujson")
	require.NoError(t, err)
	defer os.Remove(tmpFile.Name())

	_, err = tmpFile.WriteString(testPolicy)
	require.NoError(t, err)
	tmpFile.Close()

	// Test parsing
	parser := NewPolicyParser(tmpFile.Name())
	err = parser.ParsePolicy()
	require.NoError(t, err)

	policyData := parser.GetPolicyData()
	require.NotNil(t, policyData)

	// Test groups
	assert.Len(t, policyData.Groups, 2)
	assert.Contains(t, policyData.Groups, "group:admin")
	assert.Contains(t, policyData.Groups, "group:dev")
	assert.Equal(t, []string{"alice@example.com", "bob@example.com"}, policyData.Groups["group:admin"])

	// Test hosts
	assert.Len(t, policyData.Hosts, 2)
	assert.Equal(t, "10.0.1.100", policyData.Hosts["server1"])
	assert.Equal(t, "10.0.1.101", policyData.Hosts["server2"])

	// Test tagOwners
	assert.Len(t, policyData.TagOwners, 2)
	assert.Equal(t, []string{"group:admin"}, policyData.TagOwners["tag:prod"])

	// Test ACLs
	assert.Len(t, policyData.ACLs, 1)
	acl := policyData.ACLs[0]
	assert.Equal(t, "accept", acl.Action)
	assert.Equal(t, []string{"group:admin"}, acl.Src)
	assert.Equal(t, []string{"*:*"}, acl.Dst)

	// Test Grants
	assert.Len(t, policyData.Grants, 1)
	grant := policyData.Grants[0]
	assert.Equal(t, []string{"group:dev"}, grant.Src)
	assert.Equal(t, []string{"tag:dev"}, grant.Dst)
	assert.Equal(t, []string{"tcp:22", "tcp:80"}, grant.IP)

	// Test stats
	stats := parser.GetStats()
	assert.Equal(t, 2, stats.Groups)
	assert.Equal(t, 2, stats.Hosts)
	assert.Equal(t, 2, stats.TagOwners)
	assert.Equal(t, 1, stats.ACLs)
	assert.Equal(t, 1, stats.Grants)
}

func TestPolicyParserValidation(t *testing.T) {
	// Test invalid JSON structure
	invalidPolicy := `{
		"acls": [
			{
				"action": "",  // Empty action should fail validation
				"src": [],     // Empty src should fail validation
				"dst": ["*:*"]
			}
		]
	}`

	tmpFile, err := os.CreateTemp("", "invalid-policy-*.hujson")
	require.NoError(t, err)
	defer os.Remove(tmpFile.Name())

	_, err = tmpFile.WriteString(invalidPolicy)
	require.NoError(t, err)
	tmpFile.Close()

	parser := NewPolicyParser(tmpFile.Name())
	err = parser.ParsePolicy()
	require.Error(t, err) // Should fail validation
}

func TestPolicyParserFileNotFound(t *testing.T) {
	parser := NewPolicyParser("nonexistent-file.hujson")
	err := parser.ParsePolicy()
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "policy file not found")
}

func TestHuJSONToJSONConversion(t *testing.T) {
	parser := NewPolicyParser("")

	huJSON := `{
		// This is a comment
		"key": "value", // Another comment
		/* Block comment */
		"array": [1, 2, 3],
		"trailing": "comma",
	}`

	jsonStr, err := parser.convertHuJSONToJSON(huJSON)
	require.NoError(t, err)

	// Should not contain comments
	assert.NotContains(t, jsonStr, "//")
	assert.NotContains(t, jsonStr, "/*")

	// Should be valid JSON
	var result map[string]interface{}
	err = json.Unmarshal([]byte(jsonStr), &result)
	require.NoError(t, err)

	// Verify the parsed content
	assert.Equal(t, "value", result["key"])
	assert.Equal(t, "comma", result["trailing"])

	// Verify array content
	array, ok := result["array"].([]interface{})
	require.True(t, ok)
	assert.Len(t, array, 3)
	assert.Equal(t, float64(1), array[0])
	assert.Equal(t, float64(2), array[1])
	assert.Equal(t, float64(3), array[2])
}

func TestRuleLineNumberExtraction(t *testing.T) {
	testPolicy := `{
		"acls": [
			{
				"action": "accept",
				"src": ["group:admin"],
				"dst": ["*:*"]
			},
			{
				"action": "accept", 
				"src": ["group:dev"],
				"dst": ["tag:dev:*"]
			}
		],
		"grants": [
			{
				"src": ["group:dev"],
				"dst": ["tag:dev"]
			}
		]
	}`

	parser := NewPolicyParser("")
	err := parser.extractRuleLineNumbers(testPolicy)
	require.NoError(t, err)

	lineNumbers := parser.GetRuleLineNumbers()
	assert.Len(t, lineNumbers.ACLs, 2)
	assert.Len(t, lineNumbers.Grants, 1)
}

func TestPolicyDataMethods(t *testing.T) {
	// Create test policy data
	tmpFile, err := os.CreateTemp("", "test-policy-*.hujson")
	require.NoError(t, err)
	defer os.Remove(tmpFile.Name())

	testPolicy := `{
		"groups": {
			"group:admin": ["alice@example.com"],
			"group:dev": ["dev@example.com"]
		},
		"hosts": {
			"server1": "10.0.1.100"
		},
		"tagOwners": {
			"tag:prod": ["group:admin"]
		}
	}`

	_, err = tmpFile.WriteString(testPolicy)
	require.NoError(t, err)
	tmpFile.Close()

	parser := NewPolicyParser(tmpFile.Name())
	err = parser.ParsePolicy()
	require.NoError(t, err)

	policyData := parser.GetPolicyData()

	// Test helper methods
	assert.True(t, policyData.IsGroup("group:admin"))
	assert.False(t, policyData.IsGroup("not-a-group"))

	assert.True(t, policyData.IsTag("tag:prod"))
	assert.False(t, policyData.IsTag("not-a-tag"))

	assert.True(t, policyData.IsHost("server1"))
	assert.False(t, policyData.IsHost("not-a-host"))

	// Test getters
	members := policyData.GetGroupMembers("group:admin")
	assert.Equal(t, []string{"alice@example.com"}, members)

	owners := policyData.GetTagOwners("tag:prod")
	assert.Equal(t, []string{"group:admin"}, owners)

	ip := policyData.GetHostIP("server1")
	assert.Equal(t, "10.0.1.100", ip)

	// Test collections
	allGroups := policyData.GetAllGroups()
	assert.Contains(t, allGroups, "group:admin")
	assert.Contains(t, allGroups, "group:dev")

	allTags := policyData.GetAllTags()
	assert.Contains(t, allTags, "tag:prod")

	allHosts := policyData.GetAllHosts()
	assert.Contains(t, allHosts, "server1")
}
