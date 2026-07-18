from __future__ import annotations

import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

from rviz_mcp.bridge_stub import make_server


def _get_json(url: str, method: str = "GET", payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=2) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _start_server() -> tuple[ThreadingHTTPServer, int]:
    server = make_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, server.server_address[1]


def test_bridge_stub_health():
    server, port = _start_server()
    try:
        data = _get_json(f"http://127.0.0.1:{port}/health")
    finally:
        server.shutdown()
        server.server_close()

    assert data["ok"] is True
    assert data["service"] == "rviz-bridge"
    assert data["version"] == "0.1.0"
    assert data["rviz"]["display_count"] == 3


def test_bridge_stub_load_config():
    server, port = _start_server()
    try:
        data = _get_json(
            f"http://127.0.0.1:{port}/load_config",
            method="POST",
            payload={"path": "/tmp/demo.rviz"},
        )
    finally:
        server.shutdown()
        server.server_close()

    assert data["ok"] is True
    assert data["loaded"] == "/tmp/demo.rviz"
    assert data["display_count"] == 3


def test_bridge_stub_screenshot_optional_path():
    server, port = _start_server()
    try:
        data = _get_json(
            f"http://127.0.0.1:{port}/screenshot",
            method="POST",
            payload={"path": "out.png"},
        )
    finally:
        server.shutdown()
        server.server_close()

    assert data["ok"] is True
    assert data["path"] == "out.png"
    assert data["mime_type"] == "image/png"
    assert data["bytes"] == 128


def test_bridge_stub_load_config_requires_path():
    server, port = _start_server()
    try:
        data = _get_json(
            f"http://127.0.0.1:{port}/load_config",
            method="POST",
            payload={},
        )
    finally:
        server.shutdown()
        server.server_close()

    assert data["ok"] is False
    assert "error" in data
