from typing import Optional, Dict, Any
from dataclasses import dataclass, field

@dataclass
class MockDisplay:
    """Represents a mock display in RViz2."""
    id: str
    name: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

    def update_properties(self, new_properties: Dict[str, Any]) -> None:
        """Update display properties."""
        self.properties.update(new_properties)

    def to_dict(self) -> Dict[str, Any]:
        """Convert display to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'properties': self.properties,
            'enabled': self.enabled
        }