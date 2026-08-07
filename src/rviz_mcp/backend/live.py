"""Optional live RViz bridge (HTTP/file). Fails closed when unavailable.

Full HTTP contract for live mode -- all backend operations are forwarded to
a local RViz bridge. Mock remains the default in CI.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from rviz_mcp.config import bridge_file, bridge_url

# ---------------------------------------------------------------------------
# HTTP contract -- every backend op maps to (method, endpoint)
# ---------------------------------------------------------------------------
_CONTRACT: dict[str, tuple[str, str]] = {
    "doctor":                   ("GET",  "/health"),
    "list_displays":            ("GET",  "/displays"),
    "list_panels":              ("GET",  "/panels"),
    "add_display":              ("POST", "/displays/add"),
    "remove_display":           ("POST", "/displays/remove"),
    "add_panel":                ("POST", "/panels/add"),
    "remove_panel":             ("POST", "/panels/remove"),
    "set_fixed_frame":          ("POST", "/fixed_frame"),
    "set_view":                 ("POST", "/view"),
    "load_config":              ("POST", "/load_config"),
    "save_config":              ("POST", "/save_config"),
    "screenshot":               ("POST", "/screenshot"),
    "config_snapshot":          ("GET",  "/config"),
    "toggle_topic_visibility":  ("POST", "/topic/visibility/toggle"),
    "get_topic_visibility":     ("GET",  "/topic/visibility"),
    "view_presets":             ("GET",  "/view/presets"),
    "set_view_preset":          ("POST", "/view/preset"),
    "display_properties":       ("GET",  "/display/properties"),
    "update_display_properties": ("POST", "/display/properties"),
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _first_line(error: BaseException) -> str:
    return str(error).split(chr(10))[0]


def _bridge_unavailable(op_name: str) -> dict[str, Any]:
    return {
        "ok": False,
        "connected": False,
        "mode": "live",
        "message": f"Live bridge not configured for {op_name}. Set RVIZ_MCP_BRIDGE_URL.",
    }


class LiveBackend:
    name = "live"

    def _request_json(self, endpoint, payload=None):
        url = bridge_url()
        if not url:
            return {"ok": False, "connected": False, "mode": "live", "message": "Set RVIZ_MCP_BRIDGE_URL for live HTTP bridge mode"}
        method = "POST" if payload is not None else "GET"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Content-Type": "application/json"} if data else {}
        try:
            target = url.rstrip("/") + endpoint
            req = Request(target, data=data, headers=headers, method=method)
            with urlopen(req, timeout=2) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            return {"ok": False, "connected": False, "mode": "live", "error": _first_line(exc)}
        try:
            result = json.loads(raw)
        except json.JSONDecodeError as exc:
            return {"ok": False, "connected": False, "mode": "live", "error": f"bridge returned invalid JSON from {endpoint}: {_first_line(exc)}"}
        if not isinstance(result, dict):
            return {"ok": False, "connected": False, "mode": "live", "error": f"bridge returned non-object JSON from {endpoint}"}
        return result

    def _bridge_op(self, op, **kwargs):
        url = bridge_url()
        if not url:
            return _bridge_unavailable(op)
        method, endpoint = _CONTRACT.get(op, ("GET", f"/{op}"))
        payload = kwargs if method == "POST" else None
        result = self._request_json(endpoint, payload)
        if not result.get("ok", True):
            return result
        return {"ok": True, **result}

    def doctor(self):
        url = bridge_url()
        path = bridge_file()
        if url:
            data = self._request_json("/health")
            if not data.get("ok", True):
                return data
            return {"ok": True, "connected": True, "mode": "live", "bridge": "http", "health": data}
        if path and Path(path).is_file():
            return {"ok": True, "connected": True, "mode": "live", "bridge": "file", "path": path}
        return {"ok": False, "connected": False, "mode": "live", "message": "Set RVIZ_MCP_BRIDGE_URL or RVIZ_MCP_BRIDGE_FILE for live mode"}

    def seed_demo(self):
        return {"ok": False, "error": "seed_demo is mock-only"}

    def list_displays(self):
        result = self._bridge_op("list_displays")
        return result.get("displays", []) if result.get("ok") else []

    def add_display(self, name, class_name="rviz_default_plugins/Marker", topic="", enabled=True):
        return self._bridge_op("add_display", name=name, class_name=class_name, topic=topic, enabled=enabled)

    def remove_display(self, name):
        return self._bridge_op("remove_display", name=name)

    def list_panels(self):
        result = self._bridge_op("list_panels")
        return result.get("panels", []) if result.get("ok") else []

    def add_panel(self, name, class_name="rviz_common/Panel", dock="left", visible=True):
        return self._bridge_op("add_panel", name=name, class_name=class_name, dock=dock, visible=visible)

    def remove_panel(self, name):
        return self._bridge_op("remove_panel", name=name)

    def set_fixed_frame(self, frame):
        return self._bridge_op("set_fixed_frame", frame=frame)

    def set_view(self, view_class="rviz_default_plugins/Orbit", distance=10.0, yaw=0.5, pitch=0.4):
        return self._bridge_op("set_view", view_class=view_class, distance=distance, yaw=yaw, pitch=pitch)

    def load_config(self, path):
        return self._bridge_op("load_config", path=path)

    def save_config(self, path):
        return self._bridge_op("save_config", path=path)

    def config_snapshot(self):
        return self._bridge_op("config_snapshot")

    def screenshot(self, path=None):
        kwargs = {}
        if path:
            kwargs["path"] = path
        return self._bridge_op("screenshot", **kwargs)

    def toggle_topic_visibility(self, display_name, topic):
        return self._bridge_op("toggle_topic_visibility", display_name=display_name, topic=topic)

    def get_topic_visibility(self, display_name):
        return self._bridge_op("get_topic_visibility", display_name=display_name)

    def view_presets(self):
        return self._bridge_op("view_presets")

    def set_view_preset(self, name):
        return self._bridge_op("set_view_preset", name=name)

    def display_properties(self, display_name):
        return self._bridge_op("display_properties", display_name=display_name)

    def update_display_properties(self, display_name, color=None, size=None, alpha=None):
        kwargs = {"display_name": display_name}
        if color is not None:
            kwargs["color"] = color
        if size is not None:
            kwargs["size"] = size
        if alpha is not None:
            kwargs["alpha"] = alpha
        return self._bridge_op("update_display_properties", **kwargs)
