# Test Suite Documentation

## Overview

This test suite provides comprehensive coverage for the Tailscale Network Topology Mapper with a focus on isolation, reliability, and regression prevention. All tests use mock data instead of external dependencies to ensure consistent and reliable test execution.

## Test Structure

### Core Test Files

- **`test_policy_parser.py`** - Tests for policy file parsing and validation
- **`test_network_graph.py`** - Tests for network graph construction and node/edge creation
- **`test_renderer.py`** - Tests for HTML rendering and visualization generation
- **`test_hexagon_feature.py`** - Tests for mixed nodes (hexagon shapes) functionality
- **`test_search_functionality.py`** - Tests for search functionality with mock data

### Enhanced Test Files

- **`test_policy_parser_comprehensive.py`** - Comprehensive policy parsing tests with edge cases
- **`test_renderer_comprehensive.py`** - Comprehensive rendering tests with all features
- **`test_regression_prevention.py`** - Regression prevention tests for critical functionality

### Test Utilities and Fixtures

- **`tests/fixtures/mock_policy_data.py`** - Mock policy data for various test scenarios
- **`tests/test_utils.py`** - Test utilities and helper classes

## Mock Data Structure

### MockPolicyData Class

The `MockPolicyData` class provides several predefined policy configurations:

#### `get_basic_policy()`
Basic policy with minimal configuration for simple tests:
- 2 groups: `group:admin`, `group:dev`
- 2 hosts: `server1`, `database`
- 1 ACL rule and 1 grant rule

#### `get_comprehensive_policy()`
Comprehensive policy with all features for thorough testing:
- 7 groups including mobile, contractors, and special cases
- 8 hosts including servers, databases, and exit nodes
- 8 tag owners for various services
- 4 ACL rules with different protocols and destinations
- 7 grant rules with via routing, posture checks, and applications

#### `get_mixed_nodes_policy()`
Policy specifically designed to test mixed nodes (appearing in both ACL and grant rules):
- Nodes that appear as both sources and destinations
- Tests hexagon shape assignment

#### `get_search_test_policy()`
Policy optimized for testing search functionality:
- Nodes with specific metadata for search testing
- Various protocols, via routes, posture checks, and applications

#### `get_edge_cases_policy()`
Policy with edge cases and special scenarios:
- Empty groups
- Special characters in usernames
- Localhost configurations
- Unusual but valid policy structures

### MockLineNumbers Class

Provides mock line number data for testing rule reference functionality:
- Maps ACL and grant rules to line numbers
- Used for testing tooltip generation with line references

## Test Utilities

### TestGraphBuilder

Helper class for creating test network graphs:

```python
# Create a basic graph for simple tests
graph = TestGraphBuilder.create_basic_graph()

# Create a comprehensive graph with all features
graph = TestGraphBuilder.create_comprehensive_graph()

# Create a graph specifically for testing mixed nodes
graph = TestGraphBuilder.create_mixed_nodes_graph()

# Create a graph optimized for search testing
graph = TestGraphBuilder.create_search_test_graph()
```

### SearchTestHelper

Helper class for testing search functionality:

```python
# Simulate search logic
results = SearchTestHelper.simulate_search(search_metadata, 'tcp')

# Test various search terms
for term in ['via', 'protocol', 'posture', 'app']:
    results = SearchTestHelper.simulate_search(search_metadata, term)
    assert len(results) > 0
```

### HTMLTestHelper

Helper class for testing HTML output:

```python
# Extract search metadata from rendered HTML
metadata = HTMLTestHelper.extract_search_metadata_from_html(html_content)

# Check for HTML features
features = HTMLTestHelper.check_html_features(html_content)
assert features['has_search_input']
assert features['has_legend']
```

### MockPolicyParser

Mock implementation of PolicyParser for testing without files:

```python
# Create mock parser with test data
mock_parser = MockPolicyParser(policy_data, line_numbers)
mock_parser.parse_policy()

# Access parsed data
groups = mock_parser.groups
hosts = mock_parser.hosts
acls = mock_parser.acls
grants = mock_parser.grants
```

## Test Isolation Principles

### No External Dependencies

- **No real policy files**: All tests use mock data instead of `policy.hujson`
- **No network calls**: No dependencies on Tailscale API or external services
- **No file system dependencies**: Tests create temporary files when needed

### Consistent Test Data

- **Predictable results**: Mock data ensures consistent test outcomes
- **Version control friendly**: Test data is committed and versioned
- **Easy to modify**: Mock data can be easily updated for new test scenarios

### Independent Test Execution

- **No shared state**: Each test creates its own mock data
- **Parallel execution**: Tests can run in parallel without conflicts
- **Order independence**: Tests can run in any order

## Regression Prevention

### Critical Functionality Tests

The regression prevention test suite covers:

1. **Search Functionality**: Ensures the search bug fix doesn't regress
2. **Tooltip Content**: Verifies comprehensive tooltip generation
3. **Mixed Nodes**: Tests hexagon shape assignment for mixed nodes
4. **HTML Rendering**: Validates all critical HTML elements
5. **Legend Functionality**: Ensures legend contains all expected elements
6. **Drag Functionality**: Tests drag-and-drop search interface
7. **Policy Parsing**: Tests edge cases in policy parsing
8. **Graph Building**: Validates network graph construction
9. **Search Metadata**: Tests search metadata generation

### Test Coverage Areas

- **User Interface**: Search, tooltips, legends, drag functionality
- **Data Processing**: Policy parsing, graph building, metadata generation
- **Rendering**: HTML output, JavaScript integration, CSS styling
- **Edge Cases**: Empty policies, special characters, unusual configurations

## Running Tests

### Run All Tests
```bash
cd tests
python -m pytest -v
```

### Run Specific Test Categories
```bash
# Core functionality
python -m pytest test_policy_parser.py test_network_graph.py test_renderer.py -v

# Enhanced tests
python -m pytest test_*_comprehensive.py -v

# Regression prevention
python -m pytest test_regression_prevention.py -v

# Search functionality
python -m pytest test_search_functionality.py -v
```

### Run Tests with Coverage
```bash
python -m pytest --cov=.. --cov-report=html
```

## Adding New Tests

### For New Features

1. Add mock data to `MockPolicyData` if needed
2. Create test utilities in `test_utils.py` if helpful
3. Add comprehensive tests in appropriate `test_*_comprehensive.py` file
4. Add regression prevention tests in `test_regression_prevention.py`

### For Bug Fixes

1. Create a test that reproduces the bug using mock data
2. Fix the bug
3. Ensure the test passes
4. Add a regression test to prevent the bug from returning

### Best Practices

- Use mock data instead of external files
- Test both positive and negative cases
- Include edge cases and error conditions
- Verify user-facing functionality works as expected
- Add regression tests for critical features
- Keep tests independent and isolated
