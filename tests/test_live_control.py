"""Tests for live RViz2 control-path bridge operations."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from rviz_mcp.backend.live import LiveBackend

REQUESTS: list[tuple[str, dict[str, Any] | None]] = []


class ControlBridgeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        REQUESTS.append((self.path, None))
        if self.path.startswith("/health"):
            self._json({"ok": True, "service": "rviz-bridge"})
        elif self.path.startswith("/displays") and "properties" not in self.path:
            self._json({"ok": True, "displays": [{"name": "Grid"}]})
        elif self.path.startswith("/panels") and "add" not in self.path and "remove" not in self.path:
            self._json({"ok": True, "panels": [{"name": "Displays"}]})
        elif self.path.startswith("/config") and "load" not in self.path and "save" not in self.path:
            self._json({"ok": True, "fixed_frame": "map", "displays": [], "panels": []})
        elif self.path.startswith("/view/presets"):
            self._json({"ok": True, "presets": {"orbit": {"distance": 5.0}}})
        elif self.path.startswith("/display/properties"):
            self._json({"ok": True, "properties": {"color": [255,255,255], "size": 0.05, "alpha": 1.0}})
        elif self.path.startswith("/topic/visibility") and "toggle" not in self.path:
            self._json({"ok": True, "topics": ["/scan"]})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        payload = json.loads(raw)
        REQUESTS.append((self.path, payload))
        handlers = {
            "/displays/add": lambda: self._json({"ok": True, "display": payload}),
            "/displays/remove": lambda: self._json({"ok": True, "removed": payload.get("name")}),
            "/panels/add": lambda: self._json({"ok": True, "panel": payload}),
            "/panels/remove": lambda: self._json({"ok": True, "removed": payload.get("name")}),
            "/fixed_frame": lambda: self._json({"ok": True, "fixed_frame": payload.get("frame")}),
            "/view": lambda: self._json({"ok": True, "view": payload}),
            "/load_config": lambda: self._json({"ok": True, "loaded": payload.get("path"), "display_count": 3}),
            "/save_config": lambda: self._json({"ok": True, "saved": payload.get("path")}),
            "/screenshot": lambda: self._json({"ok": True, "path": payload.get("path", "out.png"), "bytes": 128}),
            "/topic/visibility/toggle": lambda: self._json({"ok": True, "toggled": payload.get("topic")}),
            "/view/preset": lambda: self._json({"ok": True, "preset": payload.get("name")}),
            "/display/properties": lambda: self._json({"ok": True, "updated": payload}),
        }
        handler = handlers.get(self.path)
        if handler:
            handler()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return

    def _json(self, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def start_bridge():
    REQUESTS.clear()
    server = ThreadingHTTPServer(("127.0.0.1", 0), ControlBridgeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return server, f"http://{host}:{port}"


def test_set_fixed_frame_posts_to_bridge(monkeypatch):
    server, url = start_bridge()
    monkeypatch.setenv("RVIZ_MCP_BRIDGE_URL", url)
    try:
        result = LiveBackend().set_fixed_frame("odom")
    finally:
        server.shutdown()
        server.server_close()
    assert result["ok"] is True
    assert result["fixed_frame"] == "odom"
    assert ("/fixed_frame", {"frame": "odom"}) in REQUESTS


def test_set_view_posts_to_bridge(monkeypatch):
    server, url = start_bridge()
    monkeypatch.setenv("RVIZ_MCP_BRIDGE_URL", url)
    try:
        result = LiveBackend().set_view(distance=5.0, yaw=0.8, pitch=0.3)
    finally:
        server.shutdown()
        server.server_close()
    assert result["ok"] is True
    assert result["view"]["distance"] == 5.0


def test_add_display_posts_to_bridge(monkeypatch):
    server, url = start_bridge()
    monkeypatch.setenv("RVIZ_MCP_BRIDGE_URL", url)
    try:
        result = LiveBackend().add_display("LaserScan", "rviz_default_plugins/LaserScan", "/scan")
    finally:
        server.shutdown()
        server.server_close()
    assert result["ok"] is True
    assert result["display"]["name"] == "LaserScan"


def test_list_displays_get_request(monkeypatch):
    server, url = start_bridge()
    monkeypatch.setenv("RVIZ_MCP_BRIDGE_URL", url)
    try:
        result = LiveBackend().list_displays()
    finally:
        server.shutdown()
        server.server_close()
    assert isinstance(result, list)
    assert any(d["name"] == "Grid" for d in result)


def test_view_presets_get_request(monkeypatch):
    server, url = start_bridge()
    monkeypatch.setenv("RVIZ_MCP_BRIDGE_URL", url)
    try:
        result = LiveBackend().view_presets()
    finally:
        server.shutdown()
        server.server_close()
    assert result["ok"] is True
    assert "presets" in result


def test_fails_closed_when_bridge_down(monkeypatch):
    server, url = start_bridge()
    server.shutdown()
    server.server_close()
    monkeypatch.setenv("RVIZ_MCP_BRIDGE_URL", url)
    result = LiveBackend().set_fixed_frame("map")
    assert result["ok"] is False
    assert result["connected"] is False
    assert result["mode"] == "live"
    assert "error" in result


def test_fails_closed_without_url(monkeypatch):
    monkeypatch.delenv("RVIZ_MCP_BRIDGE_URL", raising=False)
    result = LiveBackend().add_display("Test")
    assert result["ok"] is False
    assert result["connected"] is False
    assert "RVIZ_MCP_BRIDGE_URL" in result["message"]


def test_config_snapshot_get_request(monkeypatch):
    server, url = start_bridge()
    monkeypatch.setenv("RVIZ_MCP_BRIDGE_URL", url)
    try:
        result = LiveBackend().config_snapshot()
    finally:
        server.shutdown()
        server.server_close()
    assert result["ok"] is True
    assert "fixed_frame" in result


def test_toggle_topic_visibility_posts(monkeypatch):
    server, url = start_bridge()
    monkeypatch.setenv("RVIZ_MCP_BRIDGE_URL", url)
    try:
        result = LiveBackend().toggle_topic_visibility("LaserScan", "/scan")
    finally:
        server.shutdown()
        server.server_close()
    assert result["ok"] is True
    assert result["toggled"] == "/scan"


def test_set_view_preset_posts(monkeypatch):
    server, url = start_bridge()
    monkeypatch.setenv("RVIZ_MCP_BRIDGE_URL", url)
    try:
        result = LiveBackend().set_view_preset("top_down")
    finally:
        server.shutdown()
        server.server_close()
    assert result["ok"] is True
    assert result["preset"] == "top_down"


def test_update_display_properties_posts(monkeypatch):
    server, url = start_bridge()
    monkeypatch.setenv("RVIZ_MCP_BRIDGE_URL", url)
    try:
        result = LiveBackend().update_display_properties("Grid", color=[255,0,0], size=0.1)
    finally:
        server.shutdown()
        server.server_close()
    assert result["ok"] is True
    assert result["updated"]["color"] == [255, 0, 0]
