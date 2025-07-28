import logging
from typing import Dict, List, Union

from config import POLICY_FILE
from services import PolicyParserInterface
from services.file_loader import PolicyFileLoader
from services.policy_validator import PolicyValidator
from models.policy_data import PolicyData


class PolicyParser(PolicyParserInterface):
    """
    Parser for Tailscale policy files supporting both legacy ACLs and modern grants.
    
    Refactored to follow single responsibility principle with separated concerns:
    - File loading handled by PolicyFileLoader
    - Validation handled by PolicyValidator  
    - Data storage handled by PolicyData
    """
    
    def __init__(self, policy_file: str = POLICY_FILE) -> None:
        """
        Initialize the policy parser.
        
        Args:
            policy_file: Path to the policy file to parse (defaults to config.POLICY_FILE)
        """
        self.policy_file = policy_file
        self._policy_data: PolicyData = PolicyData()
        self._file_loader = PolicyFileLoader()
        self._validator = PolicyValidator()
        logging.debug(f"PolicyParser initialized with policy file: {policy_file}")

    @property
    def groups(self) -> Dict[str, List[str]]:
        """Get parsed groups data."""
        return self._policy_data.groups

    @property
    def hosts(self) -> Dict[str, str]:
        """Get parsed hosts data."""
        return self._policy_data.hosts

    @property
    def tag_owners(self) -> Dict[str, List[str]]:
        """Get parsed tag owners data."""
        return self._policy_data.tag_owners

    @property
    def acls(self) -> List[Dict[str, Union[str, List[str]]]]:
        """Get parsed ACL rules."""
        return self._policy_data.acls

    @property
    def grants(self) -> List[Dict[str, Union[str, List[str]]]]:
        """Get parsed grant rules."""
        return self._policy_data.grants

    def parse_policy(self) -> None:
        """
        Parse the policy file and extract all data.
        
        Raises:
            ValueError: If policy file cannot be loaded or is invalid
        """
        logging.debug(f"Starting policy parsing for: {self.policy_file}")
        
        # Load the policy file
        raw_data = self._file_loader.load_json_or_hujson(self.policy_file)
        
        # Validate the policy structure
        self._validator.validate_policy_structure(raw_data)
        
        # Create policy data object
        self._policy_data = PolicyData.from_dict(raw_data)
        
        # Log statistics
        stats = self._policy_data.get_stats()
        logging.debug(f"Policy parsing completed: {stats}")
        
        logging.info(f"Successfully parsed policy with {stats['groups']} groups, "
                    f"{stats['hosts']} hosts, {stats['acls']} ACLs, {stats['grants']} grants")
