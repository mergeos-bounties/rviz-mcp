"""Optional live RViz bridge (HTTP/file). Fails closed when unavailable."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from rviz_mcp.config import bridge_file, bridge_url


class LiveBackend:
    name = "live"

    def doctor(self) -> dict[str, Any]:
        url = bridge_url()
        path = bridge_file()
        if url:
            try:
                with urlopen(Request(url.rstrip("/") + "/health", method="GET"), timeout=2) as resp:
                    body = resp.read().decode("utf-8", errors="replace")
                return {
                    "ok": True,
                    "connected": True,
                    "mode": "live",
                    "bridge": "http",
                    "health": body[:500],
                }
            except (URLError, TimeoutError, OSError) as exc:
                return {"ok": False, "connected": False, "mode": "live", "error": str(exc)}
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

    def set_display_props(self, name: str, props_json: str = "{}") -> dict[str, Any]:
        return self._unsupported("set_display_props")

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
        return self._unsupported("load_config")

    def save_config(self, path: str) -> dict[str, Any]:
        return self._unsupported("save_config")

    def screenshot(self, path: str | None = None) -> dict[str, Any]:
        return self._unsupported("screenshot")
