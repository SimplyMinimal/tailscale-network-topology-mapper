"""
Secure policy file loading and parsing service.

This module provides secure file loading capabilities for Tailscale policy files
with support for both JSON and HuJSON (Human JSON) formats. All file operations
use security validation to prevent path traversal attacks and other vulnerabilities.

The loader automatically detects file format and handles parsing errors gracefully,
providing detailed error messages for debugging policy file issues.

Classes:
    PolicyFileLoader: Secure file loading and parsing service

Supported Formats:
    - JSON: Standard JSON format
    - HuJSON: Human-friendly JSON with comments and relaxed syntax

Security Features:
    - Path traversal attack prevention
    - File extension validation
    - File size limits
    - Secure file reading with UTF-8 encoding
"""

import json
import hjson
import logging
import re
from typing import Any, Dict, List, Tuple

from security_utils import SecureFileHandler


class PolicyFileLoader:
    """
    Secure policy file loading and parsing service.

    Provides secure loading and parsing of Tailscale policy files with support
    for both standard JSON and HuJSON formats. Uses comprehensive security
    validation to prevent common file-based attacks.

    The loader automatically detects the file format and falls back from JSON
    to HuJSON parsing if needed, enabling flexible policy file formats while
    maintaining security.

    Features:
    - Automatic JSON/HuJSON format detection
    - Secure file path validation
    - Comprehensive error handling and logging
    - UTF-8 encoding enforcement
    """

    @staticmethod
    def load_json_or_hujson(filename: str) -> Any:
        """
        Load and parse a JSON or HuJSON file securely.
        
        Args:
            filename: Path to the file to load
            
        Returns:
            Parsed data structure
            
        Raises:
            ValueError: If file cannot be found, accessed, or parsed
        """
        logging.debug(f"Loading policy file: {filename}")
        try:
            # Validate file path
            validated_path = SecureFileHandler.validate_file_path(filename)
            logging.debug(f"File path validated: {validated_path}")

            # Read file content securely
            content = SecureFileHandler.safe_read_file(validated_path)

            try:
                logging.debug("Attempting to parse as JSON")
                data = json.loads(content)
                logging.debug("Successfully parsed as JSON")
            except json.JSONDecodeError:
                logging.debug("JSON parsing failed, attempting HuJSON")
                data = hjson.loads(content)
                logging.debug("Successfully parsed as HuJSON")

        except (FileNotFoundError, PermissionError, ValueError) as e:
            logging.error(f"Secure file loading failed: {e}")
            raise ValueError(f"Error loading policy file: {e}")
        except Exception as e:
            logging.error(f"Unexpected error loading file: {e}")
            raise ValueError(f"Unexpected error loading file: {e}")

        logging.debug(f"Policy file loaded successfully with {len(data)} top-level keys")
        return data

    @staticmethod
    def extract_rule_line_numbers(filename: str) -> Dict[str, List[int]]:
        """
        Extract line numbers for ACL and grant rules from the policy file.

        Args:
            filename: Path to the policy file

        Returns:
            Dictionary with 'acls' and 'grants' keys containing lists of line numbers

        Raises:
            ValueError: If file cannot be accessed or parsed
        """
        logging.debug(f"Extracting rule line numbers from: {filename}")
        try:
            # Validate file path
            validated_path = SecureFileHandler.validate_file_path(filename)

            # Read file content securely
            content = SecureFileHandler.safe_read_file(validated_path)
            lines = content.split('\n')

            acl_line_numbers = []
            grant_line_numbers = []

            in_acls_array = False
            in_grants_array = False

            for line_num, line in enumerate(lines, 1):
                stripped_line = line.strip()

                # Skip empty lines and comments
                if not stripped_line or stripped_line.startswith('//') or stripped_line.startswith('#'):
                    continue

                # Track section boundaries
                if '"acls"' in stripped_line or "'acls'" in stripped_line:
                    if '[' in stripped_line:
                        # Array starts on same line
                        in_acls_array = True
                        in_grants_array = False
                    continue
                elif '"grants"' in stripped_line or "'grants'" in stripped_line:
                    if '[' in stripped_line:
                        # Array starts on same line
                        in_grants_array = True
                        in_acls_array = False
                    continue
                elif stripped_line == '[' and (in_acls_array or in_grants_array):
                    # Array starts on next line
                    continue
                elif (stripped_line.startswith('"') and ':' in stripped_line and
                      not stripped_line.startswith('"\t') and not stripped_line.startswith('"action') and
                      not stripped_line.startswith('"src') and not stripped_line.startswith('"dst') and
                      not stripped_line.startswith('"ip') and not stripped_line.startswith('"via') and
                      not stripped_line.startswith('"app') and not stripped_line.startswith('"srcPosture') and
                      not stripped_line.startswith('"dstPosture')):
                    # New top-level section (not a rule property)
                    in_acls_array = False
                    in_grants_array = False
                    continue
                elif stripped_line == ']':
                    # End of array
                    in_acls_array = False
                    in_grants_array = False
                    continue

                # Look for rule objects (lines that start with '{' and are in an array)
                if stripped_line == '{':
                    if in_acls_array:
                        acl_line_numbers.append(line_num)
                    elif in_grants_array:
                        grant_line_numbers.append(line_num)

            logging.debug(f"Found {len(acl_line_numbers)} ACL rules and {len(grant_line_numbers)} grant rules")
            return {
                'acls': acl_line_numbers,
                'grants': grant_line_numbers
            }

        except Exception as e:
            logging.error(f"Error extracting rule line numbers: {e}")
            raise ValueError(f"Error extracting rule line numbers: {e}")
