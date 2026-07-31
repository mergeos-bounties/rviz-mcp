"""RViz2 remote API bridge — stub with mock backend for CI."""

import json
import time
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RViz2RemoteClient:
    """Stub client for RViz2 WebSocket remote control."""
    
    def __init__(self, host: str = "localhost", port: int = 9090, token: str = "",
                 reconnect_delay: float = 2.0, max_reconnect: int = 5):
        self.host = host
        self.port = port
        self.token = token
        self.reconnect_delay = reconnect_delay
        self.max_reconnect = max_reconnect
        self._connected = False
        self._reconnect_count = 0
    
    @property
    def connected(self) -> bool:
        return self._connected
    
    def connect(self) -> bool:
        """Attempt to connect to RViz2. Returns true on success."""
        self._connected = True
        self._reconnect_count = 0
        logger.info(f"Connected to RViz2 at {self.host}:{self.port}")
        return True
    
    def disconnect(self):
        """Disconnect from RViz2."""
        self._connected = False
        logger.info("Disconnected from RViz2")
    
    def set_view(self, point: List[float], orientation: List[float]) -> Dict[str, Any]:
        """Set camera position and orientation."""
        return {"ok": True, "point": point, "orientation": orientation}
    
    def add_marker(self, topic: str, marker_type: str, pose: Dict[str, Any],
                   scale: Dict[str, float], color: List[float]) -> Dict[str, Any]:
        """Add a visualization marker."""
        marker_id = f"marker_{hash(topic)}_{int(time.time() * 1000)}"
        return {"ok": True, "marker_id": marker_id, "topic": topic}
    
    def remove_marker(self, topic: str, marker_id: str) -> Dict[str, Any]:
        """Remove a marker by ID."""
        return {"ok": True, "marker_id": marker_id}
    
    def clear_all_markers(self) -> Dict[str, Any]:
        """Remove all markers."""
        return {"ok": True, "count": 0}
    
    def set_display_type(self, topic: str, display_type: str) -> Dict[str, Any]:
        """Change display type for a topic."""
        return {"ok": True, "topic": topic, "display_type": display_type}
    
    def get_display_list(self) -> Dict[str, Any]:
        """List active displays."""
        return {"ok": True, "displays": []}


class MockRViz2Backend:
    """Mock RViz2 backend for testing/CI."""
    
    def __init__(self):
        self._markers: Dict[str, List[Dict]] = {}
        self._view = {"point": [0, 0, 0], "orientation": [0, 0, 0, 1]}
        self._display_types: Dict[str, str] = {}
    
    def set_view(self, point: List[float], orientation: List[float]) -> Dict[str, Any]:
        self._view = {"point": point, "orientation": orientation}
        return {"ok": True, **self._view}
    
    def add_marker(self, topic: str, marker_type: str, pose: Dict[str, Any],
                   scale: Dict[str, float], color: List[float]) -> Dict[str, Any]:
        marker_id = f"mock_marker_{len(self._markers.get(topic, []))}"
        marker = {
            "id": marker_id, "type": marker_type, "pose": pose,
            "scale": scale, "color": color
        }
        if topic not in self._markers:
            self._markers[topic] = []
        self._markers[topic].append(marker)
        return {"ok": True, "marker_id": marker_id, "topic": topic}
    
    def remove_marker(self, topic: str, marker_id: str) -> Dict[str, Any]:
        if topic in self._markers:
            self._markers[topic] = [m for m in self._markers[topic] if m["id"] != marker_id]
        return {"ok": True, "marker_id": marker_id}
    
    def clear_all_markers(self) -> Dict[str, Any]:
        count = sum(len(v) for v in self._markers.values())
        self._markers.clear()
        return {"ok": True, "count": count}
    
    def set_display_type(self, topic: str, display_type: str) -> Dict[str, Any]:
        self._display_types[topic] = display_type
        return {"ok": True, "topic": topic, "display_type": display_type}
    
    def get_display_list(self) -> Dict[str, Any]:
        return {"ok": True, "displays": list(self._display_types.keys())}
    
    def set_clip_near(self, near: float) -> Dict[str, Any]:
        return {"ok": True, "near": near}
    
    def set_clip_far(self, far: float) -> Dict[str, Any]:
        return {"ok": True, "far": far}
    
    def reset(self) -> Dict[str, Any]:
        self.__init__()
        return {"ok": True}
