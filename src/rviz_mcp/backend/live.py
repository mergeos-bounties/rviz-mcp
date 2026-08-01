"""Optional live RViz2 remote bridge (HTTP/file). Fails closed when unavailable.

Live mode forwards every control operation to a trusted local RViz bridge over
the HTTP contract documented in ``docs/LIVE_BRIDGE.md``. Mock mode remains the
default in CI and never touches the network.

Design intent (bounty #24): keep the backend interface identical between mock
and live so the MCP server layer is transport-agnostic. Live mode always fails
closed — a missing/down/ill-formed bridge returns ``ok: false`` with an explicit
error and never falls back to simulated RViz state.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from rviz_mcp.config import bridge_file, bridge_url

# HTTP contract shared by live RViz2 bridges. Each entry maps a backend op to a
# bridge endpoint (GET when payload is None, POST otherwise).
_CONTRACT: dict[str, str] = {
    "doctor": "/health",
    "load_config": "/load_config",
    "save_config": "/save_config",
    "screenshot": "/screenshot",
    "config_snapshot": "/config_snapshot",
    "set_fixed_frame": "/set_fixed_frame",
    "set_view": "/set_view",
    "add_display": "/add_display",
    "remove_display": "/remove_display",
    "add_panel": "/add_panel",
    "remove_panel": "/remove_panel",
    "toggle_topic_visibility": "/toggle_topic",
    "get_topic_visibility": "/topic_visibility",
    "view_presets": "/view_presets",
    "set_view_preset": "/set_view_preset",
    "display_properties": "/display_properties",
    "update_display_properties": "/update_display",
}


class LiveBackend:
    name = "live"

    def _request_json(self, endpoint: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = bridge_url()
        if not url:
            return {
                "ok": False,
                "connected": False,
                "mode": "live",
                "message": "Set RVIZ_MCP_BRIDGE_URL for live HTTP bridge mode",
            }
        method = "POST" if payload is not None else "GET"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Content-Type": "application/json"} if payload is not None else {}
        try:
            target = url.rstrip("/") + endpoint
            with urlopen(Request(target, data=data, headers=headers, method=method), timeout=2) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            return {"ok": False, "connected": False, "mode": "live", "error": str(exc)}

        try:
            result = json.loads(raw)
        except json.JSONDecodeError as exc:
            return {
                "ok": False,
                "connected": False,
                "mode": "live",
                "error": f"bridge returned invalid JSON from {endpoint}: {exc}",
            }
        if not isinstance(result, dict):
            return {
                "ok": False,
                "connected": False,
                "mode": "live",
                "error": f"bridge returned non-object JSON from {endpoint}",
            }
        return result

    def _call(self, op: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Dispatch a backend op to its bridge endpoint, failing closed."""
        endpoint = _CONTRACT.get(op)
        if endpoint is None:
            return {"ok": False, "error": f"live {op} not in bridge contract"}
        data = self._request_json(endpoint, payload)
        if not data.get("ok", True):
            return data
        return {"ok": True, **data}

    def doctor(self) -> dict[str, Any]:
        url = bridge_url()
        path = bridge_file()
        if url:
            data = self._request_json("/health")
            if not data.get("ok", True):
                return data
            return {"ok": True, "connected": True, "mode": "live", "bridge": "http", "health": data}
        if path and Path(path).is_file():
            return {"ok": True, "connected": True, "mode": "live", "bridge": "file", "path": path}
        return {
            "ok": False,
            "connected": False,
            "mode": "live",
            "message": "Set RVIZ_MCP_BRIDGE_URL or RVIZ_MCP_BRIDGE_FILE for live mode",
        }

    def seed_demo(self) -> dict[str, Any]:
        return {"ok": False, "error": "seed_demo is mock-only"}

    def list_displays(self) -> list[dict[str, Any]]:
        """List displays; live bridge returns them on health snapshot if available."""
        data = self._request_json("/health")
        if not data.get("ok", True):
            return []
        displays = (data.get("rviz") or {}).get("displays")
        return list(displays) if isinstance(displays, list) else []

    def list_panels(self) -> list[dict[str, Any]]:
        data = self._request_json("/health")
        if not data.get("ok", True):
            return []
        panels = (data.get("rviz") or {}).get("panels")
        return list(panels) if isinstance(panels, list) else []

    def config_snapshot(self) -> dict[str, Any]:
        return self._call("config_snapshot")

    def add_display(self, name: str, class_name: str = "rviz_default_plugins/Marker", topic: str = "", enabled: bool = True) -> dict[str, Any]:
        return self._call("add_display", {"name": name, "class": class_name, "topic": topic, "enabled": enabled})

    def remove_display(self, name: str) -> dict[str, Any]:
        return self._call("remove_display", {"name": name})

    def add_panel(self, name: str, class_name: str = "rviz_common/Panel", dock: str = "left", visible: bool = True) -> dict[str, Any]:
        return self._call("add_panel", {"name": name, "class": class_name, "dock": dock, "visible": visible})

    def remove_panel(self, name: str) -> dict[str, Any]:
        return self._call("remove_panel", {"name": name})

    def set_fixed_frame(self, frame: str) -> dict[str, Any]:
        return self._call("set_fixed_frame", {"frame": frame})

    def set_view(self, view_class: str = "rviz_default_plugins/Orbit", distance: float = 10.0, yaw: float = 0.5, pitch: float = 0.4) -> dict[str, Any]:
        return self._call("set_view", {"view_class": view_class, "distance": distance, "yaw": yaw, "pitch": pitch})

    def load_config(self, path: str) -> dict[str, Any]:
        return self._call("load_config", {"path": path})

    def save_config(self, path: str) -> dict[str, Any]:
        return self._call("save_config", {"path": path})

    def screenshot(self, path: str | None = None) -> dict[str, Any]:
        return self._call("screenshot", {"path": path} if path else {})

    def toggle_topic_visibility(self, display_name: str, topic: str) -> dict[str, Any]:
        return self._call("toggle_topic_visibility", {"display_name": display_name, "topic": topic})

    def get_topic_visibility(self, display_name: str) -> dict[str, Any]:
        return self._call("get_topic_visibility", {"display_name": display_name})

    def view_presets(self) -> dict[str, Any]:
        return self._call("view_presets")

    def set_view_preset(self, name: str) -> dict[str, Any]:
        return self._call("set_view_preset", {"name": name})

    def display_properties(self, display_name: str) -> dict[str, Any]:
        return self._call("display_properties", {"display_name": display_name})

    def update_display_properties(self, display_name: str, color: list[float] | None = None, size: float | None = None, alpha: float | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"display_name": display_name}
        if color:
            payload["color"] = [float(c) for c in color[:3]]
        if size is not None:
            payload["size"] = float(size)
        if alpha is not None:
            payload["alpha"] = float(alpha)
        return self._call("update_display_properties", payload)
