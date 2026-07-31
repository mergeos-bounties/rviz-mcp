"""Tests for display-graph CRUD operations — rviz-mcp issue #19.

MCP 3-layer coverage:
  * src/rviz_mcp/ops.py           — list_displays, add_display, remove_display
  * src/rviz_mcp/backend/mock.py  — MockBackend delegating to ops
  * src/rviz_mcp/server.py        — @mcp.tool() rviz_list_displays, rviz_add_display,
                                    rviz_remove_display
"""

import pytest

from rviz_mcp.backend.mock import MockBackend
from rviz_mcp import ops


# ── pure ops layer ─────────────────────────────────────────────────────


class TestDisplayOps:
    """Unit tests for the stateless ops.py functions."""

    @pytest.fixture
    def empty(self) -> dict:
        return {}

    @pytest.fixture
    def seeded(self) -> dict:
        return {
            "Grid": {
                "name": "Grid",
                "class": "rviz_default_plugins/Grid",
                "enabled": True,
                "topic": "",
            },
        }

    # -- list_displays ---------------------------------------------------

    def test_list_displays_empty(self, empty):
        assert ops.list_displays(empty) == []

    def test_list_displays_seeded(self, seeded):
        result = ops.list_displays(seeded)
        assert len(result) == 1
        assert result[0]["name"] == "Grid"

    # -- add_display -----------------------------------------------------

    def test_add_display(self, empty):
        result = ops.add_display(empty, "LaserScan", topic="/scan")
        assert result["ok"] is True
        assert result["display"]["name"] == "LaserScan"
        assert result["display"]["class"] == "rviz_default_plugins/Marker"
        assert result["display"]["topic"] == "/scan"
        assert result["display"]["enabled"] is True
        assert "LaserScan" in empty
        assert len(empty) == 1

    def test_add_display_duplicate(self, seeded):
        result = ops.add_display(seeded, "Grid")
        assert result["ok"] is False
        assert "already exists" in result["error"]

    def test_add_display_empty_name(self, empty):
        result = ops.add_display(empty, "")
        assert result["ok"] is False
        assert "name required" in result["error"]

    def test_add_display_disabled(self, empty):
        result = ops.add_display(empty, "Map", enabled=False)
        assert result["ok"] is True
        assert result["display"]["enabled"] is False

    # -- remove_display --------------------------------------------------

    def test_remove_display(self, seeded):
        # Grid is protected by default, but we can remove with protected=()
        result = ops.remove_display(seeded, "Grid", protected=())
        assert result["ok"] is True
        assert result["removed"] == "Grid"
        assert "Grid" not in seeded

    def test_remove_display_protected(self, seeded):
        result = ops.remove_display(seeded, "Grid")
        assert result["ok"] is False
        assert "cannot remove" in result["error"]

    def test_remove_display_unknown(self, empty):
        result = ops.remove_display(empty, "Bogus")
        assert result["ok"] is False
        assert "unknown" in result["error"]

    def test_remove_display_empty_name(self, empty):
        result = ops.remove_display(empty, "")
        assert result["ok"] is False
        assert "name required" in result["error"]


# ── MockBackend layer ──────────────────────────────────────────────────


class TestMockBackendDisplays:
    """Integration tests through the MockBackend."""

    @pytest.fixture
    def mock(self) -> MockBackend:
        mock = MockBackend()
        mock.seed_demo()
        return mock

    def test_list_displays_after_seed(self, mock):
        displays = mock.list_displays()
        assert len(displays) >= 3
        names = {d["name"] for d in displays}
        assert "Grid" in names
        assert "TF" in names
        assert "RobotModel" in names

    def test_add_display_backend(self, mock):
        result = mock.add_display("MyMarker", topic="/my_topic")
        assert result["ok"] is True
        disp = result["display"]
        assert disp["name"] == "MyMarker"
        assert disp["topic"] == "/my_topic"

        # Verify it appears in list
        displays = mock.list_displays()
        names = {d["name"] for d in displays}
        assert "MyMarker" in names

    def test_add_display_duplicate_backend(self, mock):
        mock.add_display("Foo")
        result = mock.add_display("Foo")
        assert result["ok"] is False

    def test_remove_display_backend(self, mock):
        # Add a non-protected display first
        mock.add_display("ToRemove")
        result = mock.remove_display("ToRemove")
        assert result["ok"] is True
        assert result["removed"] == "ToRemove"

        names = {d["name"] for d in mock.list_displays()}
        assert "ToRemove" not in names

    def test_remove_display_grid_protected(self, mock):
        result = mock.remove_display("Grid")
        assert result["ok"] is False
        assert "cannot remove" in result["error"]

    def test_remove_display_unknown_backend(self, mock):
        result = mock.remove_display("NonExistent")
        assert result["ok"] is False
        assert "unknown" in result["error"]

    def test_full_crud_cycle(self, mock):
        """Add → list-verify → remove → list-verify."""
        mock.add_display("TestDisplay", class_name="rviz_default_plugins/MarkerArray",
                         topic="/test", enabled=False)

        displays = mock.list_displays()
        names = {d["name"] for d in displays}
        assert "TestDisplay" in names

        td = next(d for d in displays if d["name"] == "TestDisplay")
        assert td["class"] == "rviz_default_plugins/MarkerArray"
        assert td["topic"] == "/test"
        assert td["enabled"] is False

        mock.remove_display("TestDisplay")
        names = {d["name"] for d in mock.list_displays()}
        assert "TestDisplay" not in names
