from rviz_mcp.backend import get_backend
from rviz_mcp.backend.mock import MockBackend
from rviz_mcp.config import set_mode


def test_seed_and_displays():
    b = MockBackend()
    s = b.seed_demo()
    assert s["ok"] is True
    assert s["profile"] == "default"
    displays = b.list_displays()
    assert any(d["name"] == "Grid" for d in displays)
    assert b.doctor()["ok"] is True


def test_nav_seed_profile():
    b = MockBackend()
    s = b.seed_demo(profile="nav")
    assert s["ok"] is True
    assert s["profile"] == "nav"
    displays = b.list_displays()
    names = {d["name"] for d in displays}
    assert {"Map", "LaserScan", "GlobalPath"}.issubset(names)
    assert next(d for d in displays if d["name"] == "Map")["topic"] == "/map"
    assert next(d for d in displays if d["name"] == "LaserScan")["topic"] == "/scan"
    assert next(d for d in displays if d["name"] == "GlobalPath")["topic"] == "/plan"
    assert b.doctor()["config_path"] == "mock://nav.rviz"


def test_seed_and_manage_panels():
    b = MockBackend()
    panels = b.list_panels()
    names = {p["name"] for p in panels}
    assert {"Displays", "Views", "Time"}.issubset(names)

    add = b.add_panel("Selection", "rviz_common/Selection", "left")
    assert add["ok"] is True
    assert add["panel"]["dock"] == "left"
    assert any(p["name"] == "Selection" for p in b.config_snapshot()["panels"])

    duplicate = b.add_panel("Selection")
    assert duplicate["ok"] is False

    remove = b.remove_panel("Selection")
    assert remove["ok"] is True
    assert not any(p["name"] == "Selection" for p in b.list_panels())


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


def test_config_snapshot_shape():
    b = MockBackend()
    b.seed_demo()
    b.set_fixed_frame("odom")
    snap = b.config_snapshot()
    assert snap["ok"] is True
    assert snap["fixed_frame"] == "odom"
    assert snap["display_count"] == len(snap["displays"])
    assert any(d["name"] == "Grid" for d in snap["displays"])
    assert snap["view"]["class"].startswith("rviz_default_plugins/")
    assert any(p["class"] == "rviz_common/Displays" for p in snap["panels"])
    assert snap["config_path"]
