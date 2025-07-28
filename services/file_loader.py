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
from typing import Any

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
