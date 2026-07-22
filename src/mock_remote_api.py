from typing import Dict, Any
from src.config import Config

class MockRemoteAPI:
    def __init__(self, config: Config):
        self.config = config
        self.connected = False

    def connect(self) -> bool:
        """Mock connection to the remote RViz2 API"""
        self.connected = True
        return self.connected

    def disconnect(self) -> None:
        """Mock disconnection from the remote RViz2 API"""
        self.connected = False

    def send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Mock sending a command to the remote RViz2 API"""
        if not self.connected:
            raise ConnectionError("Not connected to remote API")

        # Mock response
        return {"status": "success", "command": command, "mock": True}

    def get_display_info(self) -> Dict[str, Any]:
        """Mock getting information about the current display"""
        if not self.connected:
            raise ConnectionError("Not connected to remote API")

        # Mock response
        return {"display": "mock_display", "status": "active", "mock": True}