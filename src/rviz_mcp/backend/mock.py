"""Offline RViz2-style display config mock."""

from __future__ import annotations

import os
import stat
import time
from pathlib import Path
import tempfile
from typing import Any

from rviz_mcp.yaml_export import serialize_rviz_config


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

    def export_config(self, path: str | None = None) -> dict[str, Any]:
        """Export the current mock state as a simplified, RViz-like YAML document."""
        snapshot = self.config_snapshot()
        try:
            yaml_text = serialize_rviz_config(snapshot)
        except (TypeError, ValueError) as exc:
            return {"ok": False, "error": f"could not serialize export: {exc}"}
        result: dict[str, Any] = {
            "ok": True,
            "format": "rviz-yaml",
            "fixed_frame": self._fixed_frame,
            "display_count": len(self._displays),
        }
        if path is None:
            result["yaml"] = yaml_text
            result["bytes"] = len(yaml_text.encode("utf-8"))
            return result

        raw_path = path.strip()
        if not raw_path:
            return {"ok": False, "error": "export path must not be empty"}
        if "://" in raw_path:
            return {"ok": False, "error": "export path must be a local filesystem path"}

        output = Path(raw_path).expanduser()
        temp_path: Path | None = None
        try:
            if output.is_dir():
                raise IsADirectoryError(f"export path is a directory: {output}")
            if output.suffix.lower() != ".rviz":
                raise ValueError("export path must use the .rviz extension")
            if output.exists() or output.is_symlink():
                raise FileExistsError(f"export path already exists: {output}")
            if _has_linked_parent(output):
                raise OSError(f"export path has a symlink or junction parent: {output}")
            output.parent.mkdir(parents=True, exist_ok=True)
            if _has_linked_parent(output):
                raise OSError(f"export path has a symlink or junction parent: {output}")

            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=output.parent,
                prefix=f".{output.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temp_path = Path(temporary.name)
                temporary.write(yaml_text.encode("utf-8"))
                temporary.flush()
                os.fsync(temporary.fileno())

            # A hard link publishes the completed bytes atomically and fails
            # if another process created the destination after our checks.
            os.link(temp_path, output)
        except (OSError, ValueError) as exc:
            return {"ok": False, "error": f"could not write export: {exc}"}
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

        result.update({"path": str(output), "bytes": len(yaml_text.encode("utf-8"))})
        return result

    def screenshot(self, path: str | None = None) -> dict[str, Any]:
        out = path or f"mock_rviz_{int(time.time())}.png"
        self._last_shot = out
        return {"ok": True, "path": out, "mock": True, "bytes": 0}


def _has_linked_parent(path: Path) -> bool:
    """Return whether an existing parent is a symlink or Windows junction."""
    parent = path.parent
    while True:
        if parent.exists() and _is_link_or_reparse_point(parent):
            return True
        if parent == parent.parent:
            return False
        parent = parent.parent


def _is_link_or_reparse_point(path: Path) -> bool:
    """Detect symlinks and Windows reparse points on Python 3.11+."""
    if path.is_symlink():
        return True
    attributes = getattr(os.lstat(path), "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(attributes & reparse_flag)
