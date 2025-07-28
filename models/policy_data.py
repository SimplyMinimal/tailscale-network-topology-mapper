from dataclasses import dataclass, field
from typing import Dict, List, Union, Any

@dataclass
class PolicyData:
    """Data class for storing parsed policy information."""

    groups: Dict[str, List[str]] = field(default_factory=dict)
    hosts: Dict[str, str] = field(default_factory=dict)
    tag_owners: Dict[str, List[str]] = field(default_factory=dict)
    acls: List[Dict[str, Union[str, List[str]]]] = field(default_factory=list)
    grants: List[Dict[str, Union[str, List[str]]]] = field(default_factory=list)

    def __post_init__(self):
        """Validate data types after initialization."""
        if not isinstance(self.groups, dict):
            raise TypeError("groups must be a dictionary")
        if not isinstance(self.hosts, dict):
            raise TypeError("hosts must be a dictionary")
        if not isinstance(self.tag_owners, dict):
            raise TypeError("tag_owners must be a dictionary")
        if not isinstance(self.acls, list):
            raise TypeError("acls must be a list")
        if not isinstance(self.grants, list):
            raise TypeError("grants must be a list")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PolicyData':
        """Create PolicyData from dictionary."""
        return cls(
            groups=data.get("groups", {}),
            hosts=data.get("hosts", {}),
            tag_owners=data.get("tagOwners", {}),
            acls=data.get("acls", []),
            grants=data.get("grants", [])
        )

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about the policy data."""
        return {
            "groups": len(self.groups),
            "hosts": len(self.hosts),
            "tag_owners": len(self.tag_owners),
            "acls": len(self.acls),
            "grants": len(self.grants)
        }
