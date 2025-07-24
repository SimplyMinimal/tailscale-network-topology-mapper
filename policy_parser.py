import json
import hjson
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

    def load_json_or_hujson(self, filename: str) -> Any:
        try:
            with open(filename, "r") as f:
                try:
                    data = json.load(f)
                except ValueError:
                    f.seek(0)
                    data = hjson.load(f)
        except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
            raise ValueError(f"Error decoding '{filename}': {e}")
        return data

    def parse_policy(self) -> None:
        try:
            policy_data = self.load_json_or_hujson(self.policy_file)
        except ValueError as e:
            raise ValueError(f"Error parsing policy file: {e}")

        self.groups = policy_data.get("groups", {})
        self.hosts = policy_data.get("hosts", {})
        self.tag_owners = policy_data.get("tagOwners", {})
        self.acls = policy_data.get("acls", [])
        self.grants = policy_data.get("grants", [])