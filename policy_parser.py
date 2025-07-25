import json
import hjson
import logging
from typing import Any, Dict, List, Tuple, Union

from config import POLICY_FILE


class PolicyParser:
    def __init__(self, policy_file: str = POLICY_FILE):
        self.policy_file = policy_file
        self.groups: Dict[str, List[str]] = {}
        self.hosts: Dict[str, str] = {}
        self.tag_owners: Dict[str, List[str]] = {}
        self.acls: List[Dict[str, Union[str, List[str]]]] = []
        self.grants: List[Dict[str, Union[str, List[str]]]] = []
        logging.debug(f"PolicyParser initialized with policy file: {policy_file}")

    def load_json_or_hujson(self, filename: str) -> Any:
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
        except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
            logging.error(f"Failed to load/parse file '{filename}': {e}")
            raise ValueError(f"Error decoding '{filename}': {e}")
        logging.debug(f"Policy file loaded successfully with {len(data)} top-level keys")
        return data

    def parse_policy(self) -> None:
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