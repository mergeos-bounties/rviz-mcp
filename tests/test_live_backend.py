from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from rviz_mcp.backend.live import LiveBackend


REQUESTS: list[tuple[str, dict[str, Any]]] = []


class BridgeHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._json({"ok": True, "service": "rviz-bridge", "mode": "live"})
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        payload = json.loads(raw)
        REQUESTS.append((self.path, payload))
        if self.path == "/load_config":
            self._json({"ok": True, "loaded": payload["path"], "display_count": 3})
            return
        if self.path == "/screenshot":
            self._json(
                {
                    "ok": True,
                    "path": payload.get("path") or "rviz-live.png",
                    "mime_type": "image/png",
                    "bytes": 128,
                }
            )
            return
        self.send_response(404)
        self.end_headers()

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
    server = ThreadingHTTPServer(("127.0.0.1", 0), BridgeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return server, f"http://{host}:{port}"


def test_live_doctor_reads_health_json(monkeypatch):
    server, url = start_bridge()
    monkeypatch.setenv("RVIZ_MCP_BRIDGE_URL", url)
    try:
        result = LiveBackend().doctor()
    finally:
        server.shutdown()
        server.server_close()

    assert result["ok"] is True
    assert result["connected"] is True
    assert result["bridge"] == "http"
    assert result["health"]["service"] == "rviz-bridge"


def test_live_load_config_posts_path(monkeypatch):
    server, url = start_bridge()
    monkeypatch.setenv("RVIZ_MCP_BRIDGE_URL", url)
    try:
        result = LiveBackend().load_config("/tmp/demo.rviz")
    finally:
        server.shutdown()
        server.server_close()

    assert result["ok"] is True
    assert result["loaded"] == "/tmp/demo.rviz"
    assert REQUESTS == [("/load_config", {"path": "/tmp/demo.rviz"})]


def test_live_screenshot_posts_optional_path(monkeypatch):
    server, url = start_bridge()
    monkeypatch.setenv("RVIZ_MCP_BRIDGE_URL", url)
    try:
        result = LiveBackend().screenshot("out.png")
    finally:
        server.shutdown()
        server.server_close()

    assert result["ok"] is True
    assert result["path"] == "out.png"
    assert result["mime_type"] == "image/png"
    assert REQUESTS == [("/screenshot", {"path": "out.png"})]


def test_live_load_config_fails_closed_when_bridge_down(monkeypatch):
    server, url = start_bridge()
    server.shutdown()
    server.server_close()
    monkeypatch.setenv("RVIZ_MCP_BRIDGE_URL", url)

    result = LiveBackend().load_config("/tmp/demo.rviz")

    assert result["ok"] is False
    assert result["connected"] is False
    assert result["mode"] == "live"
    assert "error" in result
