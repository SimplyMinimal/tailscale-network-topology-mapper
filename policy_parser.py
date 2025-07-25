import json
import hjson
import logging
from typing import Any, Dict, List, Tuple, Union

from config import POLICY_FILE, VALID_PROTOCOLS, MIN_PORT, MAX_PORT


class PolicyParser:
    """
    Parser for Tailscale policy files supporting both legacy ACLs and modern grants.
    
    Parses JSON/HuJSON policy files and extracts groups, hosts, tag owners,
    ACL rules, and grant rules with comprehensive validation.
    """
    
    def __init__(self, policy_file: str = POLICY_FILE) -> None:
        """
        Initialize the policy parser.
        
        Args:
            policy_file: Path to the policy file to parse (defaults to config.POLICY_FILE)
        """
        self.policy_file = policy_file
        self.groups: Dict[str, List[str]] = {}
        self.hosts: Dict[str, str] = {}
        self.tag_owners: Dict[str, List[str]] = {}
        self.acls: List[Dict[str, Union[str, List[str]]]] = []
        self.grants: List[Dict[str, Union[str, List[str]]]] = []
        logging.debug(f"PolicyParser initialized with policy file: {policy_file}")

    def load_json_or_hujson(self, filename: str) -> Any:
        """
        Load and parse a JSON or HuJSON file.
        
        Args:
            filename: Path to the file to load
            
        Returns:
            Parsed data structure
            
        Raises:
            ValueError: If file cannot be found, accessed, or parsed
        """
        logging.debug(f"Loading policy file: {filename}")
        try:
            with open(filename, "r") as f:
                try:
                    logging.debug("Attempting to parse as JSON")
                    data = json.load(f)
                    logging.debug("Successfully parsed as JSON")
                except ValueError:
                    logging.debug("JSON parsing failed, attempting HuJSON")
                    f.seek(0)
                    data = hjson.load(f)
                    logging.debug("Successfully parsed as HuJSON")
        except FileNotFoundError as e:
            logging.error(f"Policy file not found: '{filename}'")
            raise ValueError(f"Policy file not found: '{filename}'")
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON/HuJSON syntax in '{filename}': {e}")
            raise ValueError(f"Invalid JSON/HuJSON syntax in '{filename}': {e}")
        except PermissionError as e:
            logging.error(f"Permission denied reading '{filename}': {e}")
            raise ValueError(f"Permission denied reading '{filename}': {e}")
        except Exception as e:
            logging.error(f"Unexpected error loading '{filename}': {e}")
            raise ValueError(f"Unexpected error loading '{filename}': {e}")
        logging.debug(f"Policy file loaded successfully with {len(data)} top-level keys")
        return data

    def parse_policy(self) -> None:
        """
        Parse the policy file and extract all sections.
        
        Extracts groups, hosts, tag owners, ACLs, and grants from the policy file.
        Performs comprehensive validation of the parsed data.
        
        Raises:
            ValueError: If policy file is invalid or contains structural errors
        """
        logging.debug("Starting policy parsing")
        try:
            policy_data = self.load_json_or_hujson(self.policy_file)
        except ValueError as e:
            logging.error(f"Policy file loading failed: {e}")
            raise ValueError(f"Error parsing policy file: {e}")

        logging.debug("Extracting policy sections")
        self.groups = policy_data.get("groups", {})
        logging.debug(f"Found {len(self.groups)} groups: {list(self.groups.keys())}")
        
        self.hosts = policy_data.get("hosts", {})
        logging.debug(f"Found {len(self.hosts)} hosts: {list(self.hosts.keys())}")
        
        self.tag_owners = policy_data.get("tagOwners", {})
        logging.debug(f"Found {len(self.tag_owners)} tag owners: {list(self.tag_owners.keys())}")
        
        self.acls = policy_data.get("acls", [])
        logging.debug(f"Found {len(self.acls)} ACL rules")
        for i, acl in enumerate(self.acls):
            logging.debug(f"ACL {i+1}: src={acl.get('src', [])}, dst={acl.get('dst', [])}")
        
        self.grants = policy_data.get("grants", [])
        logging.debug(f"Found {len(self.grants)} grant rules")
        for i, grant in enumerate(self.grants):
            src = grant.get('src', [])
            dst = grant.get('dst', [])
            ip = grant.get('ip', ['*'])
            via = grant.get('via', [])
            app = grant.get('app', [])
            posture = grant.get('srcPosture', [])
            logging.debug(f"Grant {i+1}: src={src}, dst={dst}, ip={ip}, via={via}, app={app}, posture={posture}")
        
        logging.debug("Policy parsing completed successfully")
        self._validate_policy_structure()

    def _validate_policy_structure(self) -> None:
        """Validate the parsed policy structure for common issues."""
        logging.debug("Starting policy structure validation")
        
        # Validate groups structure
        for group_name, members in self.groups.items():
            if not isinstance(members, list):
                raise ValueError(f"Group '{group_name}' members must be a list, got {type(members)}")
            if not group_name.startswith("group:"):
                logging.warning(f"Group name '{group_name}' doesn't follow 'group:' convention")
        
        # Validate hosts structure
        for host_name, ip_addr in self.hosts.items():
            if not isinstance(ip_addr, str):
                raise ValueError(f"Host '{host_name}' IP address must be a string, got {type(ip_addr)}")
        
        # Validate grants structure
        for i, grant in enumerate(self.grants):
            grant_num = i + 1
            
            # Required fields
            if "src" not in grant:
                raise ValueError(f"Grant {grant_num} missing required 'src' field")
            if "dst" not in grant:
                raise ValueError(f"Grant {grant_num} missing required 'dst' field")
            
            # Validate src and dst are lists
            if not isinstance(grant["src"], list):
                raise ValueError(f"Grant {grant_num} 'src' must be a list")
            if not isinstance(grant["dst"], list):
                raise ValueError(f"Grant {grant_num} 'dst' must be a list")
            
            # Validate optional fields are lists when present
            for field in ["ip", "via", "app", "srcPosture"]:
                if field in grant and not isinstance(grant[field], list):
                    raise ValueError(f"Grant {grant_num} '{field}' must be a list when specified")
            
            # Validate IP specifications
            if "ip" in grant:
                self._validate_ip_specifications(grant["ip"], grant_num)
        
        # Validate ACLs structure
        for i, acl in enumerate(self.acls):
            acl_num = i + 1
            if "src" not in acl:
                raise ValueError(f"ACL {acl_num} missing required 'src' field")
            if "dst" not in acl:
                raise ValueError(f"ACL {acl_num} missing required 'dst' field")
        
        logging.debug("Policy structure validation completed successfully")

    def _validate_ip_specifications(self, ip_specs: List[str], grant_num: int) -> None:
        """Validate IP protocol specifications in grants."""
        import re
        
        port_range_pattern = re.compile(r'^(\d+)(?:-(\d+))?$')
        
        for ip_spec in ip_specs:
            if ip_spec == "*":
                continue
                
            if ":" in ip_spec:
                # Protocol:port format like "tcp:443" or "tcp:8000-8999"
                parts = ip_spec.split(":", 1)
                if len(parts) != 2:
                    raise ValueError(f"Grant {grant_num} invalid IP specification: '{ip_spec}'")
                
                protocol, port_spec = parts
                if protocol not in VALID_PROTOCOLS:
                    logging.warning(f"Grant {grant_num} unknown protocol '{protocol}' in '{ip_spec}'")
                
                # Validate port specification
                if not port_range_pattern.match(port_spec):
                    raise ValueError(f"Grant {grant_num} invalid port specification: '{port_spec}'")
                
                # Validate port ranges
                match = port_range_pattern.match(port_spec)
                if match:
                    start_port = int(match.group(1))
                    end_port = int(match.group(2)) if match.group(2) else start_port
                    
                    if not (MIN_PORT <= start_port <= MAX_PORT) or not (MIN_PORT <= end_port <= MAX_PORT):
                        raise ValueError(f"Grant {grant_num} port out of range ({MIN_PORT}-{MAX_PORT}): '{port_spec}'")
                    
                    if start_port > end_port:
                        raise ValueError(f"Grant {grant_num} invalid port range '{port_spec}': start > end")
            else:
                # Just protocol
                if ip_spec not in VALID_PROTOCOLS:
                    logging.warning(f"Grant {grant_num} unknown protocol: '{ip_spec}'")