"""
Test suite for UI bug fixes to prevent regressions.

This module tests all 7 UI bug fixes that were implemented:
1. Reset Selection button functionality
2. Dropdown placeholder behavior
3. Enhanced Search Clear button
4. Keyboard navigation for search results
5. Legend positioning
6. Legend button layout
7. Auto-scroll functionality during keyboard navigation

All tests use mock data and HTML parsing to verify functionality.
"""

import pytest
import tempfile
import os
from bs4 import BeautifulSoup
import re
from unittest.mock import patch, MagicMock

# Import the classes we need to test
from renderer import Renderer
from network_graph import NetworkGraph
from tests.fixtures.mock_policy_data import MockPolicyData, MockLineNumbers
from tests.test_utils import TestGraphBuilder


class TestUIBugFixes:
    """Test suite for UI bug fixes to prevent regressions."""

    @pytest.fixture
    def mock_renderer(self):
        """Create a renderer with mock data for testing."""
        # Create temporary output file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False)
        temp_file.close()

        # Create network graph using test builder
        graph = TestGraphBuilder.create_comprehensive_graph()

        # Create renderer
        renderer = Renderer(graph)
        
        yield renderer, temp_file.name
        
        # Cleanup
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

    def test_reset_selection_button_functionality(self, mock_renderer):
        """Test Fix #1: Reset Selection button functionality."""
        renderer, output_file = mock_renderer
        
        # Render the HTML
        renderer.render_to_html(output_file)
        
        # Read the generated HTML
        with open(output_file, 'r') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check that Reset Selection button exists
        reset_button = soup.find('button', string=re.compile(r'Reset Selection'))
        assert reset_button is not None, "Reset Selection button not found"
        
        # Check that button calls resetSelection() function
        onclick_attr = reset_button.get('onclick', '')
        assert 'resetSelection()' in onclick_attr, f"Reset button should call resetSelection(), got: {onclick_attr}"
        
        # Check that resetSelection function is defined in JavaScript
        assert 'function resetSelection()' in html_content, "resetSelection function not defined"
        
        # Check that function includes TomSelect clearing logic
        assert 'selectNodeTomSelect.clear()' in html_content, "resetSelection should clear TomSelect component"
        
        # Check that function includes fallback for original select element
        assert 'selectElement.selectedIndex = 0' in html_content, "resetSelection should have fallback for select element"

    def test_dropdown_placeholder_behavior(self, mock_renderer):
        """Test Fix #2: Dropdown placeholder behavior."""
        renderer, output_file = mock_renderer

        # Render the HTML
        renderer.render_to_html(output_file)
        
        # Read the generated HTML
        with open(output_file, 'r') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the select element
        select_element = soup.find('select', id='select-node')
        assert select_element is not None, "Select element not found"
        
        # Find the first option (placeholder)
        first_option = select_element.find('option')
        assert first_option is not None, "First option not found"
        
        # Check that placeholder option has correct attributes
        assert first_option.get('value') == '', "Placeholder option should have empty value"
        assert first_option.has_attr('disabled'), "Placeholder option should be disabled"
        assert first_option.has_attr('selected'), "Placeholder option should be selected"
        
        # Check that placeholder text is correct
        assert 'Select a Node by ID' in first_option.get_text(), "Placeholder text should be 'Select a Node by ID'"

    def test_enhanced_search_clear_button(self, mock_renderer):
        """Test Fix #3: Enhanced Search Clear button."""
        renderer, output_file = mock_renderer

        # Render the HTML
        renderer.render_to_html(output_file)
        
        # Read the generated HTML
        with open(output_file, 'r') as f:
            html_content = f.read()
        
        # Check that clearSearch function exists
        assert 'function clearSearch()' in html_content, "clearSearch function not defined"
        
        # Check that clearSearch always clears input (no early return)
        clear_function_match = re.search(r'function clearSearch\(\)\s*\{(.*?)\}', html_content, re.DOTALL)
        assert clear_function_match, "clearSearch function not found"
        
        clear_function_body = clear_function_match.group(1)
        
        # Check that input is cleared at the beginning
        assert "document.getElementById('enhanced-search-input').value = ''" in clear_function_body, \
            "clearSearch should clear input at the beginning"
        
        # Check that it doesn't have early return before clearing input
        lines = clear_function_body.split('\n')
        input_clear_line = None
        early_return_line = None
        
        for i, line in enumerate(lines):
            if "value = ''" in line:
                input_clear_line = i
            if "if (!searchActive) return" in line:
                early_return_line = i
        
        if early_return_line is not None and input_clear_line is not None:
            assert input_clear_line < early_return_line, \
                "Input should be cleared before checking searchActive"

    def test_keyboard_navigation_functionality(self, mock_renderer):
        """Test Fix #4: Keyboard navigation for search results."""
        renderer, output_file = mock_renderer

        # Render the HTML
        renderer.render_to_html(output_file)
        
        # Read the generated HTML
        with open(output_file, 'r') as f:
            html_content = f.read()
        
        # Check that selectedDropdownIndex variable exists
        assert 'selectedDropdownIndex = -1' in html_content, "selectedDropdownIndex variable not defined"
        
        # Check that handleSearchKeyup function includes keyboard navigation
        assert 'ArrowDown' in html_content, "ArrowDown key handling not found"
        assert 'ArrowUp' in html_content, "ArrowUp key handling not found"
        assert 'event.key === \'Enter\'' in html_content, "Enter key handling not found"
        assert 'event.key === \'Escape\'' in html_content, "Escape key handling not found"
        
        # Check that updateDropdownSelection function exists
        assert 'function updateDropdownSelection(' in html_content, "updateDropdownSelection function not defined"
        
        # Check that dropdown items have data-node-id attributes
        assert 'data-node-id=' in html_content, "Dropdown items should have data-node-id attributes"

    def test_legend_positioning(self, mock_renderer):
        """Test Fix #5: Legend positioning."""
        renderer, output_file = mock_renderer

        # Render the HTML
        renderer.render_to_html(output_file)
        
        # Read the generated HTML
        with open(output_file, 'r') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the legend panel
        legend_panel = soup.find('div', id='legend-panel')
        assert legend_panel is not None, "Legend panel not found"
        
        # Check positioning styles
        style_attr = legend_panel.get('style', '')
        assert 'top: 90px' in style_attr, "Legend should be positioned at top: 90px"
        assert 'height: calc(100vh - 90px)' in style_attr, "Legend height should be calc(100vh - 90px)"

    def test_legend_button_layout(self, mock_renderer):
        """Test Fix #6: Legend button layout."""
        renderer, output_file = mock_renderer

        # Render the HTML
        renderer.render_to_html(output_file)
        
        # Read the generated HTML
        with open(output_file, 'r') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check that dropdown uses col-8 instead of col-10
        dropdown_div = soup.find('div', class_=re.compile(r'col-8'))
        assert dropdown_div is not None, "Dropdown should use col-8 class"
        
        # Check that there are two col-2 divs (Reset Selection and Legend buttons)
        col_2_divs = soup.find_all('div', class_=re.compile(r'col-2'))
        assert len(col_2_divs) >= 2, "Should have at least 2 col-2 divs for buttons"
        
        # Check that legend button exists and has correct onclick
        legend_button = soup.find('button', string=re.compile(r'Legend'))
        assert legend_button is not None, "Legend button not found"
        
        onclick_attr = legend_button.get('onclick', '')
        assert 'toggleLegend()' in onclick_attr, f"Legend button should call toggleLegend(), got: {onclick_attr}"

    def test_auto_scroll_functionality(self, mock_renderer):
        """Test Fix #7 (Phase 0): Auto-scroll functionality during keyboard navigation."""
        renderer, output_file = mock_renderer

        # Render the HTML
        renderer.render_to_html(output_file)
        
        # Read the generated HTML
        with open(output_file, 'r') as f:
            html_content = f.read()
        
        # Check that updateDropdownSelection function includes auto-scroll logic
        assert 'updateDropdownSelection' in html_content, "updateDropdownSelection function not found"
        
        # Check for scroll calculation logic
        assert 'itemTop' in html_content, "Auto-scroll should calculate item top position"
        assert 'itemBottom' in html_content, "Auto-scroll should calculate item bottom position"
        assert 'scrollTop' in html_content, "Auto-scroll should use scrollTop property"
        
        # Check for scroll boundary conditions
        assert 'dropdownTop' in html_content, "Auto-scroll should check dropdown top boundary"
        assert 'dropdownBottom' in html_content, "Auto-scroll should check dropdown bottom boundary"

    def test_tomselect_integration(self, mock_renderer):
        """Test TomSelect integration and initialization."""
        renderer, output_file = mock_renderer

        # Render the HTML
        renderer.render_to_html(output_file)
        
        # Read the generated HTML
        with open(output_file, 'r') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check that TomSelect CSS is included
        tomselect_css = soup.find('link', href=re.compile(r'tom-select.*\.css'))
        assert tomselect_css is not None, "TomSelect CSS not found"
        
        # Check that TomSelect JS is included
        tomselect_js = soup.find('script', src=re.compile(r'tom-select.*\.js'))
        assert tomselect_js is not None, "TomSelect JS not found"
        
        # Check that TomSelect is initialized
        assert 'new TomSelect(' in html_content, "TomSelect initialization not found"
        assert 'selectNodeTomSelect =' in html_content, "TomSelect instance variable not found"
        
        # Check TomSelect configuration
        assert 'placeholder: "Select a Node by ID"' in html_content, "TomSelect placeholder not configured"
        assert 'create: false' in html_content, "TomSelect should have create: false"

    def test_all_fixes_integration(self, mock_renderer):
        """Test that all fixes work together without conflicts."""
        renderer, output_file = mock_renderer

        # Render the HTML
        renderer.render_to_html(output_file)
        
        # Read the generated HTML
        with open(output_file, 'r') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Verify all major components exist
        components = {
            'select_element': soup.find('select', id='select-node'),
            'reset_button': soup.find('button', string=re.compile(r'Reset Selection')),
            'legend_button': soup.find('button', string=re.compile(r'Legend')),
            'legend_panel': soup.find('div', id='legend-panel'),
            'search_input': soup.find('input', id='enhanced-search-input'),
            'search_dropdown': soup.find('div', id='search-dropdown')
        }
        
        for component_name, component in components.items():
            assert component is not None, f"{component_name} not found in HTML"
        
        # Verify JavaScript functions exist
        js_functions = [
            'resetSelection',
            'clearSearch',
            'handleSearchKeyup',
            'updateDropdownSelection',
            'toggleLegend'
        ]
        
        for func_name in js_functions:
            assert f'function {func_name}(' in html_content, f"JavaScript function {func_name} not found"
        
        # Verify basic HTML structure is valid
        assert '<html>' in html_content and '</html>' in html_content, \
            "HTML structure should be complete"
        
        # Verify CSS and JS dependencies are included
        assert 'tom-select' in html_content, "TomSelect dependency not included"
        assert 'bootstrap' in html_content, "Bootstrap dependency not included"
