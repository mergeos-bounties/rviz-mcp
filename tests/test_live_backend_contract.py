"""Contract-level tests for the RViz2 live bridge backend (bounty #24).

These tests verify that the live backend fails closed — no mock fallback,
explicit errors, and proper contract validation — without requiring a real
RViz2 instance.

Run: pytest tests/test_live_backend_contract.py -v
"""

from __future__ import annotations

import json
import os
from unittest.mock import patch

import pytest

from rviz_mcp.backend.live import LiveBackend


class DescribeLiveBackendContract:
    """Test that LiveBackend always fails closed when bridge is unavailable."""

    def it_rejects_when_no_url_configured(self):
        """Live backend returns ok:false when RVIZ_MCP_BRIDGE_URL is unset."""
        with patch("rviz_mcp.backend.live.bridge_url", return_value=None):
            backend = LiveBackend()
            result = backend.doctor()
            assert result["ok"] is False
            assert result["connected"] is False
            assert "RVIZ_MCP_BRIDGE_URL" in result.get("message", "")

    def it_handles_connection_refused(self):
        """Live backend returns error on connection refused (no fallback to mock)."""
        backend = LiveBackend()
        with patch("rviz_mcp.backend.live.urlopen", side_effect=OSError("Connection refused")):
            with patch("rviz_mcp.backend.live.bridge_url", return_value="http://127.0.0.1:19999"):
                result = backend.doctor()
                assert result["ok"] is False
                assert result["mode"] == "live"
                assert "Connection refused" in result.get("error", "")

    def it_handles_invalid_json_response(self):
        """Live backend fails on malformed bridge response."""
        backend = LiveBackend()
        fake_resp = type("Resp", (), {"read": lambda s: b"not json", "status": 200})()
        with patch("rviz_mcp.backend.live.bridge_url", return_value="http://127.0.0.1:8765"):
            with patch("rviz_mcp.backend.live.urlopen", return_value=fake_resp):
                result = backend.doctor()
                assert result["ok"] is False
                assert "invalid JSON" in result.get("error", "")

    def it_handles_non_object_json_response(self):
        """Live backend rejects non-object (array, string) bridge responses."""
        backend = LiveBackend()
        fake_resp = type("Resp", (), {"read": lambda s: b'["list", "not", "dict"]', "status": 200})()
        with patch("rviz_mcp.backend.live.bridge_url", return_value="http://127.0.0.1:8765"):
            with patch("rviz_mcp.backend.live.urlopen", return_value=fake_resp):
                result = backend.doctor()
                assert result["ok"] is False
                assert "non-object" in result.get("error", "")

    def it_handles_http_error(self):
        """Live backend handles HTTP 500 from bridge gracefully."""
        from urllib.error import HTTPError
        backend = LiveBackend()
        fake_error = HTTPError(
            "http://127.0.0.1:8765/health", 500,
            "Internal Server Error", {}, None
        )
        with patch("rviz_mcp.backend.live.bridge_url", return_value="http://127.0.0.1:8765"):
            with patch("rviz_mcp.backend.live.urlopen", side_effect=fake_error):
                result = backend.doctor()
                assert result["ok"] is False
                assert result["mode"] == "live"

    def it_handles_timeout(self):
        """Live backend handles timeout without hanging."""
        backend = LiveBackend()
        with patch("rviz_mcp.backend.live.bridge_url", return_value="http://10.255.255.1:8765"):
            with patch("rviz_mcp.backend.live.urlopen", side_effect=TimeoutError("timed out")):
                result = backend.doctor()
                assert result["ok"] is False
                assert "timed out" in result.get("error", "")
