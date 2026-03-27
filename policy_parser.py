import logging
from typing import Dict, List, Union, Optional
import os
import json

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
    
    def __init__(
        self,
        policy_file: Optional[str] = POLICY_FILE,
        use_remote_policy: bool = False,
        validate_with_api: bool = False,
        api_key: Optional[str] = None,
        tailnet: Optional[str] = None,
    ) -> None:
        """
        Initialize the policy parser.

        Args:
            policy_file: Path to the policy file to parse (defaults to config.POLICY_FILE).
                         If use_remote_policy is True, this can be None.
            use_remote_policy: If True, fetch policy file via Tailscale API instead of local file.
            validate_with_api: If True, use Tailscale API validation (ignored if use_remote_policy is True).
            api_key: Tailscale API key (overrides TAILSCALE_API_KEY env var).
            tailnet: Tailscale tailnet (overrides TAILSCALE_TAILNET env var).
        """
        self.policy_file = policy_file
        self.use_remote_policy = use_remote_policy
        self.validate_with_api = validate_with_api
        # Resolve credentials: CLI args > environment variables
        self.api_key = api_key or os.environ.get("TAILSCALE_API_KEY")
        self.tailnet = tailnet or os.environ.get("TAILSCALE_TAILNET")
        self._policy_data: PolicyData = PolicyData()
        self._file_loader = PolicyFileLoader()
        self._validator = PolicyValidator()
        self._rule_line_numbers: Dict[str, List[int]] = {"acls": [], "grants": []}
        logging.debug(
            f"PolicyParser initialized with remote policy={use_remote_policy}, "
            f"validate with API={validate_with_api}, policy file={policy_file}"
        )

    def _ensure_credentials(self) -> None:
        """Ensure Tailscale API credentials are available, raise ValueError if missing."""
        if not self.api_key or not self.tailnet:
            raise ValueError(
                "Tailscale API credentials required. Provide --tailscale-api-key and --tailscale-tailnet "
                "or set TAILSCALE_API_KEY and TAILSCALE_TAILNET environment variables."
            )

    def _fetch_remote_policy(self) -> Dict[str, Union[str, List[str]]]:
        """Fetch policy file from Tailscale API."""
        self._ensure_credentials()
        logging.info(
            f"Fetching policy file from Tailscale API for tailnet: {self.tailnet}"
        )
        try:
            raw_data = self._file_loader.load_from_tailscale_api(
                self.api_key, self.tailnet
            )
            logging.debug("Successfully fetched remote policy file")
            return raw_data
        except Exception as e:
            logging.error(f"Failed to fetch remote policy: {e}")
            raise ValueError(f"Failed to fetch remote policy from Tailscale API: {e}")

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

    @property
    def rule_line_numbers(self) -> Dict[str, List[int]]:
        """Get line numbers for ACL and grant rules."""
        return self._rule_line_numbers

    def parse_policy(self) -> None:
        """
        Parse the policy file and extract all data.

        The parsing behavior depends on configuration:
        - If use_remote_policy=True: Fetch policy from Tailscale API (validation skipped)
        - If validate_with_api=True and credentials available: Use Tailscale API validation
        - Otherwise: Use local policy structure validation

        Raises:
            ValueError: If policy file cannot be loaded or is invalid
        """
        if self.use_remote_policy:
            logging.debug("Fetching remote policy file via Tailscale API")
            raw_data = self._fetch_remote_policy()
            # No file for line numbers when using remote policy
            self._rule_line_numbers = {"acls": [], "grants": []}
            # Skip validation entirely (per spec)
            logging.debug("Skipping validation for remote policy file")
        else:
            logging.debug(f"Starting policy parsing for: {self.policy_file}")
            # Load the policy file FIRST
            raw_data = self._file_loader.load_json_or_hujson(self.policy_file)
            # Extract rule line numbers
            self._rule_line_numbers = self._file_loader.extract_rule_line_numbers(
                self.policy_file
            )
            # Determine validation method
            if self._should_validate_with_api():
                # Serialize the raw data to JSON string for Tailscale API validation
                policy_json = json.dumps(raw_data)
                self._validator.validate_with_tailscale_api(
                    policy_json, self.api_key, self.tailnet
                )
                logging.debug("Using Tailscale validation API")
            else:
                logging.debug("Using local policy structure validation")
                self._validator.validate_policy_structure(raw_data)

        # Create policy data object
        self._policy_data = PolicyData.from_dict(raw_data)

        # Log statistics
        stats = self._policy_data.get_stats()
        logging.debug(f"Policy parsing completed: {stats}")

        logging.info(
            f"Successfully parsed policy with {stats['groups']} groups, "
            f"{stats['hosts']} hosts, {stats['acls']} ACLs, {stats['grants']} grants"
        )

    def _should_validate_with_api(self) -> bool:
        """Determine if we should validate with Tailscale API."""
        if not self.validate_with_api:
            return False
        # Ensure credentials are present
        if self.api_key and self.tailnet:
            return True
        # If credentials missing, we cannot validate with API; fallback to local validation
        logging.warning(
            "Tailscale API credentials missing - falling back to local validation. "
            "Set --tailscale-api-key and --tailscale-tailnet or environment variables."
        )
        return False
