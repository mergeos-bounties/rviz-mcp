"""Offline RViz2-style display config mock."""

from __future__ import annotations

import json
import time
from typing import Any


class MockBackend:
    name = "mock"

    def __init__(self) -> None:
        self.seed_demo()

    def seed_demo(self) -> dict[str, Any]:
        self._fixed_frame = "map"
        self._view = {
            "class": "rviz_default_plugins/Orbit",
            "distance": 10.0,
            "focal_point": {"x": 0.0, "y": 0.0, "z": 0.0},
            "yaw": 0.5,
            "pitch": 0.4,
        }
        self._displays: dict[str, dict[str, Any]] = {
            "Grid": {
                "name": "Grid",
                "class": "rviz_default_plugins/Grid",
                "enabled": True,
                "topic": "",
                "properties": {},
            },
            "TF": {
                "name": "TF",
                "class": "rviz_default_plugins/TF",
                "enabled": True,
                "topic": "/tf",
                "properties": {},
            },
            "RobotModel": {
                "name": "RobotModel",
                "class": "rviz_default_plugins/RobotModel",
                "enabled": True,
                "topic": "/robot_description",
                "properties": {},
            },
        }
        self._config_path = "mock://default.rviz"
        self._last_shot = None
        return {
            "ok": True,
            "fixed_frame": self._fixed_frame,
            "displays": list(self._displays),
        }

    def doctor(self) -> dict[str, Any]:
        return {
            "ok": True,
            "connected": True,
            "mode": "mock",
            "rviz_required": False,
            "message": "Mock RViz config active — no RViz install needed",
            "fixed_frame": self._fixed_frame,
            "display_count": len(self._displays),
            "config_path": self._config_path,
        }

    def list_displays(self) -> list[dict[str, Any]]:
        return list(self._displays.values())

    def add_display(
        self,
        name: str,
        class_name: str = "rviz_default_plugins/Marker",
        topic: str = "",
        enabled: bool = True,
    ) -> dict[str, Any]:
        if name in self._displays:
            return {"ok": False, "error": f"display {name} already exists"}
        self._displays[name] = {
            "name": name,
            "class": class_name,
            "enabled": bool(enabled),
            "topic": topic,
            "properties": {},
        }
        return {"ok": True, "display": self._displays[name]}

    def remove_display(self, name: str) -> dict[str, Any]:
        if name not in self._displays:
            return {"ok": False, "error": f"unknown display {name}"}
        if name == "Grid":
            return {"ok": False, "error": "cannot remove Grid in mock seed"}
        del self._displays[name]
        return {"ok": True, "removed": name}

    def set_display_props(self, name: str, props_json: str = "{}") -> dict[str, Any]:
        """Set optional properties on a display (color, size, alpha, etc.).

        Args:
            name: Display name to update.
            props_json: JSON string with key/value properties to merge.

        Returns:
            dict with ok/error and the updated display.
        """
        if name not in self._displays:
            return {"ok": False, "error": f"unknown display {name}"}
        try:
            props = json.loads(props_json)
        except json.JSONDecodeError as exc:
            return {"ok": False, "error": f"invalid JSON: {exc}"}
        if not isinstance(props, dict):
            return {"ok": False, "error": "props_json must decode to a JSON object"}
        current = self._displays[name].setdefault("properties", {})
        current.update(props)
        return {"ok": True, "display": self._displays[name]}

    def set_fixed_frame(self, frame: str) -> dict[str, Any]:
        frame = (frame or "map").strip()
        if not frame:
            return {"ok": False, "error": "frame required"}
        self._fixed_frame = frame
        return {"ok": True, "fixed_frame": self._fixed_frame}

    def set_view(
        self,
        view_class: str = "rviz_default_plugins/Orbit",
        distance: float = 10.0,
        yaw: float = 0.5,
        pitch: float = 0.4,
    ) -> dict[str, Any]:
        self._view = {
            "class": view_class,
            "distance": float(distance),
            "focal_point": self._view.get("focal_point", {"x": 0.0, "y": 0.0, "z": 0.0}),
            "yaw": float(yaw),
            "pitch": float(pitch),
        }
        return {"ok": True, "view": self._view}

    def load_config(self, path: str) -> dict[str, Any]:
        self._config_path = path or self._config_path
        return {"ok": True, "loaded": self._config_path, "displays": list(self._displays)}

    def save_config(self, path: str) -> dict[str, Any]:
        self._config_path = path or "mock://saved.rviz"
        return {
            "ok": True,
            "saved": self._config_path,
            "display_count": len(self._displays),
            "fixed_frame": self._fixed_frame,
        }

    def screenshot(self, path: str | None = None) -> dict[str, Any]:
        out = path or f"mock_rviz_{int(time.time())}.png"
        self._last_shot = out
        return {"ok": True, "path": out, "mock": True, "bytes": 0}
