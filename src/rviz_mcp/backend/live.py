"""Optional live RViz bridge (HTTP/file). Fails closed when unavailable."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from rviz_mcp.config import bridge_file, bridge_url


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

    def doctor(self) -> dict[str, Any]:
        url = bridge_url()
        path = bridge_file()
        if url:
            data = self._request_json("/health")
            if not data.get("ok", True):
                return data
            return {
                "ok": True,
                "connected": True,
                "mode": "live",
                "bridge": "http",
                "health": data,
            }
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

    def _unsupported(self, op: str) -> dict[str, Any]:
        d = self.doctor()
        if not d.get("ok"):
            return d
        return {"ok": False, "error": f"live {op} not wired — configure bridge endpoints"}

    def list_displays(self) -> list[dict[str, Any]]:
        return []

    def list_panels(self) -> list[dict[str, Any]]:
        return []

    def add_display(
        self,
        name: str,
        class_name: str = "rviz_default_plugins/Marker",
        topic: str = "",
        enabled: bool = True,
    ) -> dict[str, Any]:
        return self._unsupported("add_display")

    def remove_display(self, name: str) -> dict[str, Any]:
        return self._unsupported("remove_display")

    def add_panel(
        self,
        name: str,
        class_name: str = "rviz_common/Panel",
        dock: str = "left",
        visible: bool = True,
    ) -> dict[str, Any]:
        return self._unsupported("add_panel")

    def remove_panel(self, name: str) -> dict[str, Any]:
        return self._unsupported("remove_panel")

    def set_fixed_frame(self, frame: str) -> dict[str, Any]:
        return self._unsupported("set_fixed_frame")

    def set_view(
        self,
        view_class: str = "rviz_default_plugins/Orbit",
        distance: float = 10.0,
        yaw: float = 0.5,
        pitch: float = 0.4,
    ) -> dict[str, Any]:
        return self._unsupported("set_view")

    def load_config(self, path: str) -> dict[str, Any]:
        url = bridge_url()
        if url:
            data = self._request_json("/load_config", {"path": path})
            if not data.get("ok", True):
                return data
            return {"ok": True, **data}
        return self._unsupported("load_config")

    def save_config(self, path: str) -> dict[str, Any]:
        return self._unsupported("save_config")

    def screenshot(self, path: str | None = None) -> dict[str, Any]:
        url = bridge_url()
        if url:
            payload = {"path": path} if path else {}
            data = self._request_json("/screenshot", payload)
            if not data.get("ok", True):
                return data
            return {"ok": True, **data}
        return self._unsupported("screenshot")
    def toggle_topic_visibility(self, display_name: str, topic: str) -> dict[str, Any]: return self._unavailable("toggle_topic_visibility")
    def get_topic_visibility(self, display_name: str) -> dict[str, Any]: return self._unavailable("get_topic_visibility")
    def view_presets(self) -> dict[str, Any]: return self._unavailable("view_presets")
    def set_view_preset(self, name: str) -> dict[str, Any]: return self._unavailable("set_view_preset")
    def display_properties(self, display_name: str) -> dict[str, Any]: return self._unavailable("display_properties")
    def update_display_properties(self, display_name: str, color: list[float] | None = None, size: float | None = None, alpha: float | None = None) -> dict[str, Any]: return self._unavailable("update_display_properties")
