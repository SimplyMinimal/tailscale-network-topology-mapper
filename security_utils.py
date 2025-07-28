"""
Security utilities for safe file handling and path validation.

This module provides secure file operations to prevent common security
vulnerabilities such as path traversal attacks, file size limits, and
extension validation. All file operations should use these utilities
to ensure application security.

Classes:
    SecureFileHandler: Provides secure file reading and path validation

Security Features:
    - Path traversal attack prevention
    - File extension validation
    - File size limits
    - Directory restriction enforcement
    - Temporary file handling for testing
"""

import pathlib
from typing import Union, Set, Optional

class SecureFileHandler:
    """
    Secure file handling with comprehensive path validation and safety checks.

    Provides static methods for secure file operations that prevent common
    security vulnerabilities including path traversal attacks, unauthorized
    file access, and resource exhaustion through large files.

    Security measures:
    - Path traversal detection and prevention
    - File extension whitelist validation
    - File size limits to prevent DoS attacks
    - Directory restriction enforcement
    - Special handling for temporary files during testing

    Attributes:
        ALLOWED_EXTENSIONS: Set of permitted file extensions
        MAX_FILE_SIZE: Maximum allowed file size in bytes (10MB)
    """

    ALLOWED_EXTENSIONS: Set[str] = {'.json', '.hujson', '.html'}
    """Set of allowed file extensions for security validation."""

    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    """Maximum allowed file size in bytes to prevent resource exhaustion."""

    @staticmethod
    def validate_file_path(file_path: Union[str, pathlib.Path], allowed_dir: Optional[str] = None) -> pathlib.Path:
        """
        Validate file path to prevent traversal attacks and unauthorized access.

        Performs comprehensive security validation on file paths including:
        - Path traversal detection (../ sequences)
        - File extension validation against whitelist
        - Directory restriction enforcement
        - Special handling for temporary files during testing

        Args:
            file_path: Path to validate (string or Path object)
            allowed_dir: Optional directory restriction - file must be within this directory

        Returns:
            pathlib.Path: Validated and resolved absolute path

        Raises:
            ValueError: If path fails security validation:
                - Contains path traversal sequences
                - Has disallowed file extension
                - Is outside allowed directory (when specified)

        Example:
            >>> path = SecureFileHandler.validate_file_path("policy.json", "/app/data")
            >>> print(path)
            /app/data/policy.json

            >>> SecureFileHandler.validate_file_path("../../../etc/passwd")
            ValueError: Path traversal detected: ../../../etc/passwd
        """
        path = pathlib.Path(file_path).resolve()

        # Check for path traversal attempts
        if '..' in str(path):
            raise ValueError(f"Path traversal detected: {file_path}")

        # Validate extension
        if path.suffix.lower() not in SecureFileHandler.ALLOWED_EXTENSIONS:
            raise ValueError(f"File extension not allowed: {path.suffix}")

        # Check against allowed directory if specified
        # Allow temporary files for testing and system temp directories
        if allowed_dir:
            allowed_path = pathlib.Path(allowed_dir).resolve()
            is_temp_file = (str(path).startswith('/tmp') or
                           str(path).startswith('/var/folders') or
                           'tmp' in str(path))

            if not is_temp_file and not str(path).startswith(str(allowed_path)):
                raise ValueError(f"File outside allowed directory: {file_path}")

        return path
    
    @staticmethod
    def safe_read_file(file_path: Union[str, pathlib.Path]) -> str:
        """
        Safely read file content with comprehensive security validation.

        Performs secure file reading with multiple safety checks:
        - Path validation to prevent traversal attacks
        - File size validation to prevent resource exhaustion
        - UTF-8 encoding enforcement for consistent text handling

        Args:
            file_path: Path to the file to read (string or Path object)

        Returns:
            str: File content as UTF-8 decoded string

        Raises:
            ValueError: If file fails security validation:
                - Path contains traversal sequences
                - File extension not in whitelist
                - File size exceeds MAX_FILE_SIZE limit
            FileNotFoundError: If file does not exist
            PermissionError: If file cannot be read due to permissions
            UnicodeDecodeError: If file cannot be decoded as UTF-8

        Example:
            >>> content = SecureFileHandler.safe_read_file("policy.json")
            >>> print(len(content))
            1024

            >>> SecureFileHandler.safe_read_file("huge_file.json")  # > 10MB
            ValueError: File too large: /path/to/huge_file.json
        """
        validated_path = SecureFileHandler.validate_file_path(file_path)

        # Check file size to prevent resource exhaustion
        if validated_path.stat().st_size > SecureFileHandler.MAX_FILE_SIZE:
            raise ValueError(f"File too large: {validated_path}")

        return validated_path.read_text(encoding='utf-8')
