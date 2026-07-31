"""Tests for set-fixed-frame — rviz-mcp issue #20.

MCP 3-layer coverage:
  * src/rviz_mcp/ops.py           — set_fixed_frame
  * src/rviz_mcp/backend/mock.py  — MockBackend delegating to ops
  * src/rviz_mcp/server.py        — @mcp.tool() rviz_set_fixed_frame
"""

import pytest

from rviz_mcp.backend.mock import MockBackend
from rviz_mcp import ops


class TestSetFixedFrameOps:
    """Unit tests for the stateless ops.set_fixed_frame."""

    def test_set_valid_frame(self):
        state: dict = {"fixed_frame": "map"}
        result = ops.set_fixed_frame(state, "odom")
        assert result["ok"] is True
        assert result["fixed_frame"] == "odom"
        assert state["fixed_frame"] == "odom"

    def test_set_same_frame(self):
        state: dict = {"fixed_frame": "map"}
        result = ops.set_fixed_frame(state, "map")
        assert result["ok"] is True
        assert state["fixed_frame"] == "map"

    def test_set_empty_frame(self):
        state: dict = {"fixed_frame": "map"}
        result = ops.set_fixed_frame(state, "")
        assert result["ok"] is False
        assert "frame required" in result["error"]
        # State unchanged
        assert state["fixed_frame"] == "map"

    def test_set_frame_with_spaces(self):
        """Whitespace is stripped, valid frame is applied."""
        state: dict = {"fixed_frame": "map"}
        result = ops.set_fixed_frame(state, "  base_link  ")
        assert result["ok"] is True
        assert state["fixed_frame"] == "base_link"

    def test_set_whitespace_only_frame(self):
        state: dict = {"fixed_frame": "map"}
        result = ops.set_fixed_frame(state, "   ")
        assert result["ok"] is False
        assert "frame required" in result["error"]

    def test_common_ros_frames(self):
        """Cover the common ROS frame naming conventions."""
        state: dict = {"fixed_frame": "map"}
        for frame in ("odom", "base_link", "base_footprint", "camera_link",
                      "laser", "world", "earth", "utm", "gps"):
            result = ops.set_fixed_frame(state, frame)
            assert result["ok"] is True
            assert state["fixed_frame"] == frame


class TestMockBackendFixedFrame:
    """Integration tests through the MockBackend."""

    @pytest.fixture
    def mock(self) -> MockBackend:
        mock = MockBackend()
        mock.seed_demo()
        return mock

    def test_initial_frame(self, mock):
        assert mock._fixed_frame == "map"

    def test_set_fixed_frame(self, mock):
        result = mock.set_fixed_frame("odom")
        assert result["ok"] is True
        assert result["fixed_frame"] == "odom"
        assert mock._fixed_frame == "odom"

    def test_set_fixed_frame_empty(self, mock):
        original = mock._fixed_frame
        result = mock.set_fixed_frame("")
        assert result["ok"] is False
        assert mock._fixed_frame == original  # unchanged

    def test_chain_multiple_frames(self, mock):
        frames = ["odom", "base_link", "camera_link", "map"]
        for f in frames:
            result = mock.set_fixed_frame(f)
            assert result["ok"] is True
            assert mock._fixed_frame == f

    def test_doctor_reflects_fixed_frame(self, mock):
        mock.set_fixed_frame("odom")
        doc = mock.doctor()
        assert doc["fixed_frame"] == "odom"

    def test_config_snapshot_reflects_fixed_frame(self, mock):
        mock.set_fixed_frame("gps")
        snap = mock.config_snapshot()
        assert snap["fixed_frame"] == "gps"

    def test_save_config_reflects_fixed_frame(self, mock):
        mock.set_fixed_frame("world")
        cfg = mock.save_config("test.rviz")
        assert cfg["fixed_frame"] == "world"
