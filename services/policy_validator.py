import logging
from typing import Dict, List, Union, Any

from config import VALID_PROTOCOLS, MIN_PORT, MAX_PORT


class PolicyValidator:
    """Validates policy structure and content."""

    @staticmethod
    def validate_policy_structure(data: Dict[str, Any]) -> None:
        """
        Validate the overall structure of a policy file.
        
        Args:
            data: Parsed policy data
            
        Raises:
            ValueError: If policy structure is invalid
        """
        logging.debug("Validating policy structure")
        
        # Validate grants structure
        if "grants" in data:
            PolicyValidator._validate_grants_structure(data["grants"])
        
        # Validate ACLs structure  
        if "acls" in data:
            PolicyValidator._validate_acls_structure(data["acls"])
            
        logging.debug("Policy structure validation completed")

    @staticmethod
    def _validate_grants_structure(grants: List[Dict[str, Any]]) -> None:
        """Validate grants structure."""
        for grant_num, grant in enumerate(grants, 1):
            if "src" not in grant:
                raise ValueError(f"Grant {grant_num} missing required 'src' field")
            if "dst" not in grant:
                raise ValueError(f"Grant {grant_num} missing required 'dst' field")
            
            # Validate src field type
            if not isinstance(grant["src"], list):
                raise ValueError(f"Grant {grant_num} 'src' field must be a list")
            
            # Validate IP specifications
            if "ip" in grant:
                PolicyValidator.validate_ip_specifications(grant["ip"], grant_num)

    @staticmethod
    def _validate_acls_structure(acls: List[Dict[str, Any]]) -> None:
        """Validate ACLs structure."""
        for acl_num, acl in enumerate(acls, 1):
            if "src" not in acl:
                raise ValueError(f"ACL {acl_num} missing required 'src' field")
            if "dst" not in acl:
                raise ValueError(f"ACL {acl_num} missing required 'dst' field")

    @staticmethod
    def validate_ip_specifications(ip_specs: Union[str, List[str]], grant_num: int) -> None:
        """
        Validate IP protocol specifications.

        Supports Tailscale grant syntax:
        - Wildcard: "*" (all protocols and ports)
        - Bare port: "53" (any protocol on port 53)
        - Port range: "8000-8999" (any protocol on port range)
        - Protocol only: "tcp" (all TCP traffic)
        - Protocol:port: "tcp:53" (TCP on port 53)
        - Protocol:port-range: "tcp:8000-8999" (TCP on port range)

        Args:
            ip_specs: IP specifications to validate
            grant_num: Grant number for error reporting

        Raises:
            ValueError: If IP specifications are invalid
        """
        if isinstance(ip_specs, str):
            ip_specs = [ip_specs]

        for spec in ip_specs:
            if spec == "*":
                continue

            # Parse protocol:port format
            if ":" in spec:
                protocol, port_spec = spec.split(":", 1)

                # Validate protocol
                if protocol not in VALID_PROTOCOLS:
                    raise ValueError(f"Grant {grant_num}: Invalid protocol '{protocol}'. Valid protocols: {VALID_PROTOCOLS}")

                # Validate port specification
                PolicyValidator._validate_port_specification(port_spec, grant_num, spec)
            else:
                # Could be: bare port number, port range, or protocol name
                # Try to parse as port number or port range first
                if PolicyValidator._is_port_or_range(spec):
                    # Validate as port specification
                    PolicyValidator._validate_port_specification(spec, grant_num, spec)
                elif spec in VALID_PROTOCOLS:
                    # Valid protocol without port
                    pass
                else:
                    raise ValueError(f"Grant {grant_num}: Invalid specification '{spec}'. "
                                   f"Must be a port number, port range, protocol name, or protocol:port format. "
                                   f"Valid protocols: {VALID_PROTOCOLS}")

    @staticmethod
    def _is_port_or_range(spec: str) -> bool:
        """
        Check if a specification is a port number or port range.

        Args:
            spec: Specification to check

        Returns:
            True if spec is a valid port or port range, False otherwise
        """
        # Check for port range
        if "-" in spec:
            try:
                parts = spec.split("-", 1)
                int(parts[0])
                int(parts[1])
                return True
            except (ValueError, IndexError):
                return False
        else:
            # Check for single port
            try:
                int(spec)
                return True
            except ValueError:
                return False

    @staticmethod
    def _validate_port_specification(port_spec: str, grant_num: int, full_spec: str) -> None:
        """Validate port specification."""
        # Handle port ranges
        if "-" in port_spec:
            try:
                start_port, end_port = port_spec.split("-", 1)
                start_port = int(start_port)
                end_port = int(end_port)

                if start_port < MIN_PORT or start_port > MAX_PORT:
                    raise ValueError(f"Grant {grant_num}: Start port {start_port} out of valid range ({MIN_PORT}-{MAX_PORT}) in '{full_spec}'")
                if end_port < MIN_PORT or end_port > MAX_PORT:
                    raise ValueError(f"Grant {grant_num}: End port {end_port} out of valid range ({MIN_PORT}-{MAX_PORT}) in '{full_spec}'")
                if start_port > end_port:
                    raise ValueError(f"Grant {grant_num}: Invalid port range {start_port}-{end_port} in '{full_spec}'")

            except ValueError as e:
                if "invalid literal" in str(e):
                    raise ValueError(f"Grant {grant_num}: Invalid port range format in '{full_spec}'")
                raise
        else:
            # Single port
            try:
                port = int(port_spec)
            except ValueError:
                raise ValueError(f"Grant {grant_num}: Invalid port format in '{full_spec}'")

            if port < MIN_PORT or port > MAX_PORT:
                raise ValueError(f"Grant {grant_num}: Port {port} out of valid range ({MIN_PORT}-{MAX_PORT}) in '{full_spec}'")
