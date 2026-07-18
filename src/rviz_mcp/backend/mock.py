"""Offline RViz2-style display config mock."""

from __future__ import annotations

import time
from typing import Any


class MockBackend:
    name = "mock"

    def __init__(self) -> None:
        self.seed_demo()

    def seed_demo(self, profile: str = "default") -> dict[str, Any]:
        profile = (profile or "default").strip().lower()
        self._fixed_frame = "map"
        self._view = {
            "class": "rviz_default_plugins/Orbit",
            "distance": 10.0,
            "focal_point": {"x": 0.0, "y": 0.0, "z": 0.0},
            "yaw": 0.5,
            "pitch": 0.4,
        }
        self._displays = self._seed_displays(profile)
        self._panels = self._seed_panels()
        self._config_path = f"mock://{profile}.rviz"
        self._last_shot = None
        return {
            "ok": True,
            "profile": profile,
            "fixed_frame": self._fixed_frame,
            "displays": list(self._displays),
        }

    def _seed_displays(self, profile: str) -> dict[str, dict[str, Any]]:
        displays: dict[str, dict[str, Any]] = {
            "Grid": {
                "name": "Grid",
                "class": "rviz_default_plugins/Grid",
                "enabled": True,
                "topic": "",
            },
            "TF": {
                "name": "TF",
                "class": "rviz_default_plugins/TF",
                "enabled": True,
                "topic": "/tf",
            },
            "RobotModel": {
                "name": "RobotModel",
                "class": "rviz_default_plugins/RobotModel",
                "enabled": True,
                "topic": "/robot_description",
            },
        }
        if profile == "nav":
            displays.update(
                {
                    "Map": {
                        "name": "Map",
                        "class": "rviz_default_plugins/Map",
                        "enabled": True,
                        "topic": "/map",
                    },
                    "LaserScan": {
                        "name": "LaserScan",
                        "class": "rviz_default_plugins/LaserScan",
                        "enabled": True,
                        "topic": "/scan",
                    },
                    "GlobalPath": {
                        "name": "GlobalPath",
                        "class": "rviz_default_plugins/Path",
                        "enabled": True,
                        "topic": "/plan",
                    },
                }
            )
        return displays

    def _seed_panels(self) -> dict[str, dict[str, Any]]:
        return {
            "Displays": {
                "class": "rviz_common/Displays",
                "name": "Displays",
                "dock": "left",
                "visible": True,
            },
            "Views": {
                "class": "rviz_common/Views",
                "name": "Views",
                "dock": "right",
                "visible": True,
            },
            "Time": {
                "class": "rviz_common/Time",
                "name": "Time",
                "dock": "bottom",
                "visible": True,
            },
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

    def list_panels(self) -> list[dict[str, Any]]:
        return list(self._panels.values())

    def config_snapshot(self) -> dict[str, Any]:
        """Full snapshot of the current mock RViz config.

        Returns fixed_frame, the view controller, the display tree, panel
        layout, and the tracked config path — the shape served by the
        ``rviz://config`` MCP resource.
        """
        displays = [dict(d) for d in self._displays.values()]
        return {
            "ok": True,
            "mode": "mock",
            "fixed_frame": self._fixed_frame,
            "view": dict(self._view),
            "displays": displays,
            "display_count": len(displays),
            "panels": [dict(p) for p in self._panels.values()],
            "config_path": self._config_path,
        }

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
        }
        return {"ok": True, "display": self._displays[name]}

    def remove_display(self, name: str) -> dict[str, Any]:
        if name not in self._displays:
            return {"ok": False, "error": f"unknown display {name}"}
        if name == "Grid":
            return {"ok": False, "error": "cannot remove Grid in mock seed"}
        del self._displays[name]
        return {"ok": True, "removed": name}

    def add_panel(
        self,
        name: str,
        class_name: str = "rviz_common/Panel",
        dock: str = "left",
        visible: bool = True,
    ) -> dict[str, Any]:
        name = (name or "").strip()
        if not name:
            return {"ok": False, "error": "panel name required"}
        if name in self._panels:
            return {"ok": False, "error": f"panel {name} already exists"}
        self._panels[name] = {
            "name": name,
            "class": class_name,
            "dock": dock or "left",
            "visible": bool(visible),
        }
        return {"ok": True, "panel": self._panels[name]}

    def remove_panel(self, name: str) -> dict[str, Any]:
        name = (name or "").strip()
        if name not in self._panels:
            return {"ok": False, "error": f"unknown panel {name}"}
        del self._panels[name]
        return {"ok": True, "removed": name}

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

    def toggle_topic_visibility(self, display_name: str, topic: str) -> dict[str, Any]:
        """Toggle topic visibility for a display."""
        disp = self._displays.get(display_name)
        if not disp:
            return {"ok": False, "error": f"display {display_name} not found"}
        topics = disp.setdefault("topics", [])
        if topic in topics:
            topics.remove(topic)
            return {"ok": True, "display": display_name, "topic": topic, "visible": False}
        else:
            topics.append(topic)
            return {"ok": True, "display": display_name, "topic": topic, "visible": True}

    def get_topic_visibility(self, display_name: str) -> dict[str, Any]:
        disp = self._displays.get(display_name)
        if not disp:
            return {"ok": False, "error": f"display {display_name} not found"}
        return {"ok": True, "display": display_name, "topics": disp.get("topics", [])}

    def view_presets(self) -> dict[str, Any]:
        """List view controller presets."""
        return {
            "ok": True,
            "presets": {
                "orbit": {"type": "orbit", "distance": 5.0, "yaw": 0.0, "pitch": 0.8},
                "fps": {"type": "fps", "position": [0, 0, 2], "look_at": [0, 0, 0]},
                "top_down": {"type": "top_down_ortho", "scale": 10.0},
                "front": {"type": "orbit", "yaw": 0.0, "pitch": 0.0},
            }
        }

    def set_view_preset(self, name: str) -> dict[str, Any]:
        presets = self.view_presets()["presets"]
        if name not in presets:
            return {"ok": False, "error": f"unknown preset: {name}. Available: {sorted(presets)}"}
        preset = presets[name]
        self._views["current"] = preset
        return {"ok": True, "preset": name, "view": preset}

    def display_properties(self, display_name: str) -> dict[str, Any]:
        """Get display property bag (color, size, alpha)."""
        disp = self._displays.get(display_name)
        if not disp:
            return {"ok": False, "error": f"display {display_name} not found"}
        return {
            "ok": True,
            "display": display_name,
            "properties": {
                "color": disp.get("color", [255, 255, 255]),
                "size": disp.get("size", 0.05),
                "alpha": disp.get("alpha", 1.0),
                "type": disp.get("type", "?"),
                "fixed_frame": disp.get("fixed_frame", "map"),
            }
        }

    def update_display_properties(
        self, display_name: str, color: list[float] | None = None,
        size: float | None = None, alpha: float | None = None,
    ) -> dict[str, Any]:
        disp = self._displays.get(display_name)
        if not disp:
            return {"ok": False, "error": f"display {display_name} not found"}
        if color:
            disp["color"] = [float(c) for c in color[:3]]
        if size is not None:
            disp["size"] = float(size)
        if alpha is not None:
            disp["alpha"] = float(alpha)
        return self.display_properties(display_name)

    def export_rviz_yaml(self) -> dict[str, Any]:
        """Export the current mock config as a .rviz-compatible YAML dict.

        The output can be serialised to YAML and round-tripped into a real
        RViz2 instance with limited fidelity (see export limitations below).
        """
        import io, yaml

        snap = self.config_snapshot()

        # Build the .rviz YAML structure
        rviz_doc: dict[str, Any] = {
            "Panels": [
                {
                    "Class": p["class"],
                    "Embedded": False,
                    "Floating": False,
                    "Name": p.get("name", p["class"].split("/")[-1]),
                    "Title": p.get("name", p["class"].split("/")[-1]),
                    "Visible": p.get("visible", True),
                }
                for p in snap.get("panels", [])
            ],
            "Visualization Manager": {
                "Displays": [
                    self._display_to_rviz(display)
                    for display in snap.get("displays", [])
                ],
                "Enabled": True,
                "Global Options": {
                    "Background Color": [48, 48, 48],
                    "Fixed Frame": snap.get("fixed_frame", "map"),
                    "Frame Rate": 30,
                    "Sync": False,
                },
                "Help": {},
                "Name": "Root",
                "Selection": "",
                "Sim Time": True,
            },
        }

        view = snap.get("view", {})
        rviz_doc["Visualization Manager"]["View Controllers"] = [
            {
                "Class": view.get("class", "rviz_default_plugins/Orbit"),
                "Distance": view.get("distance", 10.0),
                "Enable": True,
                "Focal Point": {
                    "X": view.get("focal_point", {}).get("x", 0.0),
                    "Y": view.get("focal_point", {}).get("y", 0.0),
                    "Z": view.get("focal_point", {}).get("z", 0.0),
                },
                "Name": "View",
                "Pitch": view.get("pitch", 0.4),
                "Target Frame": "<Fixed Frame>",
                "Yaw": view.get("yaw", 0.5),
            }
        ]

        # Dump to YAML string for the returned dict
        buf = io.StringIO()
        yaml.safe_dump(rviz_doc, buf, default_flow_style=False, sort_keys=False)
        return {
            "ok": True,
            "yaml": buf.getvalue(),
            "mock": True,
            "export_type": "rviz_yaml",
            "display_count": snap.get("display_count", 0),
            "limitations": [
                "Colour values use default flat colour (no per-display customisation).",
                "Advanced display properties (topic QoS, colour transform, alpha) are not preserved.",
                "Toolbars and tree-expansion state are not included.",
                "Round-trip fidelity is approximate — inspect the YAML and adjust manually.",
            ],
        }

    def _display_to_rviz(self, display: dict[str, Any]) -> dict[str, object]:
        """Convert a mock display dict to .rviz YAML display entry."""
        cls = display.get("class", "rviz_default_plugins/Marker")
        return {
            "Alpha": display.get("alpha", 1.0),
            "Autocompute Intensity Bounds": True,
            "Autocompute Value Bounds": {"Max Value": True, "Min Value": True},
            "Axis": "Z",
            "Channel Name": "",
            "Class": cls,
            "Color": display.get("color", [255, 255, 255]),
            "Color Transformer": "FlatColor",
            "Enabled": display.get("enabled", True),
            "Name": display.get("name", "Display"),
            "Status": {"Status": None},
            "Topic": display.get("topic", ""),
            "Value": True,
        }
