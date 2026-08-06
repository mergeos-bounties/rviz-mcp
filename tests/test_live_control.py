"""Live bridge control-path tests (bounty #24): every op forwards to the HTTP
contract documented in docs/LIVE_BRIDGE.md and fails closed when the bridge is
down.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from rviz_mcp.backend.live import LiveBackend

REQUESTS: list[tuple[str, dict[str, Any] | None]] = []


class ControlBridgeHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            self._json(
                {
                    "ok": True,
                    "service": "rviz-bridge",
                    "mode": "live",
                    "rviz": {"fixed_frame": "map", "display_count": 3, "displays": [], "panels": []},
                }
            )
            return
        if self.path == "/config_snapshot":
            self._json({"ok": True, "fixed_frame": "map", "displays": []})
            return
        if self.path == "/view_presets":
            self._json({"ok": True, "presets": {"orbit": {"type": "orbit"}}})
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        payload = json.loads(raw)
        REQUESTS.append((self.path, payload))
        self._json({"ok": True, "echo": payload})

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _json(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def start_bridge() -> tuple[ThreadingHTTPServer, str]:
    REQUESTS.clear()
    server = ThreadingHTTPServer(("127.0.0.1", 0), ControlBridgeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return server, f"http://{host}:{port}"


def test_live_control_posts_set_fixed_frame(monkeypatch):
    server, url = start_bridge()
    monkeypatch.setenv("RVIZ_MCP_BRIDGE_URL", url)
    try:
        result = LiveBackend().set_fixed_frame("odom")
    finally:
        server.shutdown()
        server.server_close()

    assert result["ok"] is True
    assert result["echo"] == {"frame": "odom"}
    assert REQUESTS == [("/set_fixed_frame", {"frame": "odom"})]


def test_live_control_posts_set_view(monkeypatch):
    server, url = start_bridge()
    monkeypatch.setenv("RVIZ_MCP_BRIDGE_URL", url)
    try:
        result = LiveBackend().set_view("rviz_default_plugins/FPS", distance=5.0)
    finally:
        server.shutdown()
        server.server_close()

    assert result["ok"] is True
    assert result["echo"]["view_class"] == "rviz_default_plugins/FPS"
    assert result["echo"]["distance"] == 5.0
    assert REQUESTS == [("/set_view", {"view_class": "rviz_default_plugins/FPS", "distance": 5.0, "yaw": 0.5, "pitch": 0.4})]


def test_live_control_posts_add_display(monkeypatch):
    server, url = start_bridge()
    monkeypatch.setenv("RVIZ_MCP_BRIDGE_URL", url)
    try:
        result = LiveBackend().add_display("Map", "rviz_default_plugins/Map", topic="/map")
    finally:
        server.shutdown()
        server.server_close()

    assert result["ok"] is True
    assert result["echo"] == {"name": "Map", "class": "rviz_default_plugins/Map", "topic": "/map", "enabled": True}
    assert REQUESTS == [("/add_display", {"name": "Map", "class": "rviz_default_plugins/Map", "topic": "/map", "enabled": True})]


def test_live_control_gets_view_presets(monkeypatch):
    server, url = start_bridge()
    monkeypatch.setenv("RVIZ_MCP_BRIDGE_URL", url)
    try:
        result = LiveBackend().view_presets()
    finally:
        server.shutdown()
        server.server_close()

    assert result["ok"] is True
    assert "orbit" in result["presets"]
    assert REQUESTS == []


def test_live_control_fails_closed_when_bridge_down(monkeypatch):
    server, url = start_bridge()
    server.shutdown()
    server.server_close()
    monkeypatch.setenv("RVIZ_MCP_BRIDGE_URL", url)

    result = LiveBackend().add_display("Map")

    assert result["ok"] is False
    assert result["connected"] is False
    assert result["mode"] == "live"
    assert "error" in result


def test_live_control_no_bridge_url_message():
    result = LiveBackend().set_fixed_frame("odom")
    assert result["ok"] is False
    assert "RVIZ_MCP_BRIDGE_URL" in result["message"]
