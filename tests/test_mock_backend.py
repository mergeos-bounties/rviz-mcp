from rviz_mcp.backend import get_backend
from rviz_mcp.backend.mock import MockBackend
from rviz_mcp.config import set_mode


def test_seed_and_displays():
    b = MockBackend()
    s = b.seed_demo()
    assert s["ok"] is True
    displays = b.list_displays()
    assert any(d["name"] == "Grid" for d in displays)
    assert b.doctor()["ok"] is True


def test_add_frame_view_shot():
    b = MockBackend()
    b.seed_demo()
    add = b.add_display("PointCloud", "rviz_default_plugins/PointCloud2", "/points")
    assert add["ok"] is True
    assert b.set_fixed_frame("base_link")["fixed_frame"] == "base_link"
    assert b.set_view(distance=5.0)["ok"] is True
    shot = b.screenshot("out.png")
    assert shot["path"] == "out.png"
    assert b.remove_display("PointCloud")["ok"] is True


def test_get_backend_mock():
    set_mode("mock")
    assert get_backend().name == "mock"


def test_set_display_props():
    b = MockBackend()
    b.seed_demo()

    # Set properties on an existing display
    result = b.set_display_props("Grid", '{"color": [255, 0, 0], "alpha": 0.8}')
    assert result["ok"] is True
    assert result["display"]["properties"] == {"color": [255, 0, 0], "alpha": 0.8}

    # Properties are reflected in list_displays
    displays = b.list_displays()
    grid = next(d for d in displays if d["name"] == "Grid")
    assert grid["properties"]["color"] == [255, 0, 0]

    # Merge additional properties
    result = b.set_display_props("Grid", '{"size": 0.5}')
    assert result["ok"] is True
    assert result["display"]["properties"]["color"] == [255, 0, 0]
    assert result["display"]["properties"]["size"] == 0.5

    # Unknown display
    result = b.set_display_props("DoesNotExist", '{}')
    assert result["ok"] is False
    assert "unknown display" in result["error"]

    # Invalid JSON
    result = b.set_display_props("Grid", "not json")
    assert result["ok"] is False
    assert "invalid JSON" in result["error"]

    # Non-dict JSON
    result = b.set_display_props("Grid", "[1, 2, 3]")
    assert result["ok"] is False
    assert "JSON object" in result["error"]

    # New displays have empty properties
    b.add_display("TestDisplay")
    displays = b.list_displays()
    td = next(d for d in displays if d["name"] == "TestDisplay")
    assert td["properties"] == {}
