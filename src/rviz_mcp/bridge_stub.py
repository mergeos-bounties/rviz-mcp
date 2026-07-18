"""Standalone HTTP stub for the live RViz bridge.

This emulates the live bridge HTTP contract documented in
``docs/LIVE_BRIDGE.md`` (``GET /health``, ``POST /load_config``,
``POST /screenshot``) so ``RVIZ_MCP_MODE=live`` can be exercised offline.

Run it with ``rviz-mcp bridge-stub`` or import ``make_server`` for tests.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

SERVICE = "rviz-bridge"
BRIDGE_VERSION = "0.1.0"


class BridgeStubHandler(BaseHTTPRequestHandler):
    # In-memory stub state, mutated by load_config.
    displays: list[dict[str, Any]] = [
        {"name": "Grid", "class": "rviz_default_plugins/Grid", "enabled": True, "topic": ""},
        {"name": "TF", "class": "rviz_default_plugins/TF", "enabled": True, "topic": ""},
        {
            "name": "RobotModel",
            "class": "rviz_default_plugins/RobotModel",
            "enabled": True,
            "topic": "",
        },
    ]

    def _json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_payload(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (json.JSONDecodeError, ValueError):
            return {}

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._json(
                {
                    "ok": True,
                    "service": SERVICE,
                    "mode": "live",
                    "version": BRIDGE_VERSION,
                    "rviz": {
                        "fixed_frame": "map",
                        "display_count": len(self.displays),
                    },
                }
            )
            return
        self._json({"ok": False, "error": f"unknown endpoint {self.path}"}, status=404)

    def do_POST(self) -> None:  # noqa: N802
        payload = self._read_payload()
        if self.path == "/load_config":
            self._json(self._load_config(payload))
            return
        if self.path == "/screenshot":
            self._json(self._screenshot(payload))
            return
        self._json({"ok": False, "error": f"unknown endpoint {self.path}"}, status=404)

    def _load_config(self, payload: dict[str, Any]) -> dict[str, Any]:
        path = payload.get("path", "")
        if not path:
            return {"ok": False, "error": "load_config requires 'path'"}
        return {"ok": True, "loaded": path, "display_count": len(self.displays)}

    def _screenshot(self, payload: dict[str, Any]) -> dict[str, Any]:
        path = payload.get("path") or "rviz-live.png"
        return {"ok": True, "path": path, "mime_type": "image/png", "bytes": 128}


def make_server(host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    """Create (but do not start) a stub bridge HTTP server."""
    return ThreadingHTTPServer((host, port), BridgeStubHandler)


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    """Start the stub bridge and block until interrupted."""
    server = make_server(host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
