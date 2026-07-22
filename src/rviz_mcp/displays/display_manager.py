from typing import Dict, List, Optional
from .display import MockDisplay

class DisplayManager:
    """Manages displays in RViz2."""

    def __init__(self):
        self.displays: Dict[str, MockDisplay] = {}

    def create_display(self, display_data: Dict[str, Any]) -> MockDisplay:
        """Create a new mock display."""
        display = MockDisplay(**display_data)
        self.displays[display.id] = display
        return display

    def get_display(self, display_id: str) -> Optional[MockDisplay]:
        """Get a display by ID."""
        return self.displays.get(display_id)

    def get_all_displays(self) -> List[MockDisplay]:
        """Get all displays."""
        return list(self.displays.values())

    def update_display(self, display_id: str, update_data: Dict[str, Any]) -> Optional[MockDisplay]:
        """Update a display's properties."""
        display = self.get_display(display_id)
        if display:
            display.update_properties(update_data)
        return display

    def delete_display(self, display_id: str) -> bool:
        """Delete a display."""
        if display_id in self.displays:
            del self.displays[display_id]
            return True
        return False