"""Tests for rviz-mcp YAML export (issue #7).

Covers the mock backend's export_config, the pure-Python YAML serializer,
CLI integration, MCP tool, golden fixture, safety rules, and live-mode
rejection.
"""

from __future__ import annotations

import asyncio
import json
import os
import stat
from pathlib import Path

import pytest
from typer.testing import CliRunner

from rviz_mcp import server as srv
from rviz_mcp.backend import get_backend, switch_mode
from rviz_mcp.backend.live import LiveBackend
from rviz_mcp.backend.mock import MockBackend
from rviz_mcp.cli import app
from rviz_mcp.config import set_mode
from rviz_mcp.export_config import (
    build_rviz_document,
    export_config_to_yaml,
    export_config_to_file,
    serialize_rviz_config,
)

runner = CliRunner()
FIXTURES = Path(__file__).parent / "fixtures"


# ── golden fixture ──────────────────────────────────────────────────────


def test_default_export_matches_golden_fixture():
    """The default mock state must produce the golden fixture byte-for-byte."""
    backend = MockBackend()
    backend.seed_demo()

    yaml_text = export_config_to_yaml(backend)
    golden = (FIXTURES / "default_export.rviz").read_text(encoding="utf-8")

    assert yaml_text == golden, "YAML output diverged from golden fixture"


def test_export_is_deterministic():
    """Repeated exports of the same state must be identical."""
    backend = MockBackend()
    backend.seed_demo()

    y1 = export_config_to_yaml(backend)
    y2 = export_config_to_yaml(backend)

    assert y1 == y2
    assert len(y1.encode("utf-8")) > 0


# ── YAML shape / structure ──────────────────────────────────────────────


def test_yaml_has_top_level_sections():
    backend = MockBackend()
    backend.seed_demo()

    yaml_text = export_config_to_yaml(backend)

    assert "Panels:" in yaml_text
    assert "Visualization Manager:" in yaml_text
    assert "Displays:" in yaml_text
    assert "Global Options:" in yaml_text
    assert "Views:" in yaml_text
    assert "Current:" in yaml_text


def test_yaml_includes_all_default_displays():
    backend = MockBackend()
    backend.seed_demo()

    doc = build_rviz_document(backend.config_snapshot())
    displays = doc["Visualization Manager"]["Displays"]

    display_names = {d["Name"] for d in displays}
    assert {"Grid", "TF", "RobotModel"}.issubset(display_names)


def test_yaml_includes_all_default_panels():
    backend = MockBackend()
    backend.seed_demo()

    doc = build_rviz_document(backend.config_snapshot())
    panels = doc["Panels"]

    panel_names = {p["Name"] for p in panels}
    assert {"Displays", "Views", "Time"}.issubset(panel_names)


def test_yaml_view_has_required_fields():
    backend = MockBackend()
    backend.seed_demo()

    doc = build_rviz_document(backend.config_snapshot())
    view = doc["Visualization Manager"]["Views"]["Current"]

    assert view["Class"] == "rviz_default_plugins/Orbit"
    assert "Distance" in view
    assert "Focal Point" in view
    assert "X" in view["Focal Point"]
    assert "Yaw" in view
    assert "Pitch" in view


def test_yaml_fixed_frame_reflected():
    backend = MockBackend()
    backend.seed_demo()
    backend.set_fixed_frame("odom")

    doc = build_rviz_document(backend.config_snapshot())
    assert doc["Visualization Manager"]["Global Options"]["Fixed Frame"] == "odom"


def test_yaml_view_custom_values():
    backend = MockBackend()
    backend.seed_demo()
    backend.set_view(distance=4.5, yaw=1.25, pitch=0.2)

    doc = build_rviz_document(backend.config_snapshot())
    view = doc["Visualization Manager"]["Views"]["Current"]

    assert view["Distance"] == 4.5
    assert view["Yaw"] == 1.25
    assert view["Pitch"] == 0.2


def test_nav_profile_includes_nav_displays():
    backend = MockBackend()
    backend.seed_demo("nav")

    doc = build_rviz_document(backend.config_snapshot())
    display_names = {d["Name"] for d in doc["Visualization Manager"]["Displays"]}

    assert {"Map", "LaserScan", "GlobalPath"}.issubset(display_names)


# ── mock backend export_config method ────────────────────────────────────


def test_mock_export_config_inline():
    backend = MockBackend()
    backend.seed_demo()

    result = backend.export_config()

    assert result["ok"] is True
    assert result["format"] == "rviz-yaml"
    assert "yaml" in result
    assert result["bytes"] == len(result["yaml"].encode("utf-8"))
    assert result["fixed_frame"] == "map"
    assert result["display_count"] == 3


def test_mock_export_config_file(tmp_path: Path):
    backend = MockBackend()
    backend.seed_demo()
    output = tmp_path / "test_config.rviz"

    result = backend.export_config(str(output))

    assert result["ok"] is True
    assert result["format"] == "rviz-yaml"
    assert result["path"] == str(output)
    assert output.read_text(encoding="utf-8").startswith("Panels:\n")


# ── file export safety rules ─────────────────────────────────────────────


@pytest.mark.parametrize(
    "path",
    [
        "",            # empty
        "   ",         # whitespace-only
        "mock://saved.rviz",  # URL
        "export.yaml",        # wrong extension
        "export.rvizz",       # close but wrong
    ],
)
def test_export_rejects_bad_paths(path: str):
    result = MockBackend().export_config(str(path))
    assert result["ok"] is False
    assert "error" in result


def test_export_rejects_existing_file(tmp_path: Path):
    backend = MockBackend()
    output = tmp_path / "existing.rviz"
    output.write_text("old content")

    result = backend.export_config(str(output))
    assert result["ok"] is False
    assert "already exists" in result["error"]


def test_export_rejects_directory(tmp_path: Path):
    backend = MockBackend()
    output = tmp_path / "adir"
    output.mkdir()

    result = backend.export_config(str(output))
    assert result["ok"] is False
    assert "directory" in result["error"]


def test_export_creates_parent_directories(tmp_path: Path):
    backend = MockBackend()
    output = tmp_path / "deep" / "nested" / "config.rviz"

    result = backend.export_config(str(output))

    assert result["ok"] is True
    assert output.is_file()
    assert "Panels:" in output.read_text(encoding="utf-8")


# ── CLI integration ──────────────────────────────────────────────────────


def test_cli_export_config_json_default():
    result = runner.invoke(app, ["export-config"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert "displays" in data


def test_cli_export_config_yaml():
    result = runner.invoke(app, ["export-config", "--format", "yaml"])
    assert result.exit_code == 0
    assert "Panels:" in result.stdout
    assert "Visualization Manager:" in result.stdout


def test_cli_export_config_yaml_to_file(tmp_path: Path):
    output = tmp_path / "cli_export.rviz"
    result = runner.invoke(
        app, ["export-config", "--format", "yaml", "--out", str(output)]
    )
    assert result.exit_code == 0
    assert "Wrote" in result.stdout
    assert output.is_file()
    assert output.read_text(encoding="utf-8").startswith("Panels:\n")


def test_cli_export_config_json_to_file(tmp_path: Path):
    output = tmp_path / "cli_export.json"
    result = runner.invoke(app, ["export-config", "--out", str(output)])
    assert result.exit_code == 0
    assert output.is_file()
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["ok"] is True


def test_cli_call_export_config():
    set_mode("mock")
    result = runner.invoke(app, ["call", "export_config"])
    assert result.exit_code == 0
    # rprint outputs Rich-formatted dict; just verify it contains key fields
    assert "ok" in result.stdout
    assert "fixed_frame" in result.stdout
    assert "displays" in result.stdout


def test_cli_export_config_rejects_bad_format():
    """Non-existent format should fall through to JSON path."""
    result = runner.invoke(app, ["export-config", "--format", "xml"])
    # Still succeeds because "xml" != "yaml" → JSON path
    assert result.exit_code == 0


# ── MCP tool integration ─────────────────────────────────────────────────


def test_mcp_export_config_json():
    set_mode("mock")
    result = json.loads(srv.rviz_export_config())
    assert result["ok"] is True
    assert "displays" in result


def test_mcp_export_config_yaml():
    set_mode("mock")
    result = json.loads(srv.rviz_export_config(format="yaml"))
    assert result["ok"] is True
    assert result["format"] == "rviz-yaml"
    assert "yaml" in result
    assert "Panels:" in result["yaml"]


def test_mcp_export_config_yaml_file(tmp_path: Path):
    set_mode("mock")
    output = tmp_path / "mcp_export.rviz"
    result = json.loads(
        srv.rviz_export_config(format="yaml", path=str(output))
    )
    assert result["ok"] is True
    assert result["path"] == str(output)
    assert output.is_file()


def test_mcp_tool_is_registered():
    tools = asyncio.run(srv.mcp.list_tools())
    tool_names = {tool.name for tool in tools}
    assert "rviz_export_config" in tool_names


# ── live backend rejection ───────────────────────────────────────────────


def test_live_export_config_is_rejected():
    result = LiveBackend().export_config("out.rviz")
    assert result["ok"] is False
    assert result["mode"] == "live"
    assert "mock-only" in result["error"]


# ── serializer edge cases ────────────────────────────────────────────────


def test_build_rviz_document_rejects_bad_snapshot():
    with pytest.raises(ValueError):
        build_rviz_document({})

    with pytest.raises(ValueError):
        build_rviz_document({"fixed_frame": "", "view": {}, "displays": [], "panels": []})


def test_serialize_with_added_display():
    backend = MockBackend()
    backend.seed_demo()
    backend.add_display("LaserScan", "rviz_default_plugins/LaserScan", "/scan")

    yaml_text = export_config_to_yaml(backend)

    assert "LaserScan" in yaml_text
    assert '"/scan"' in yaml_text


def test_serialize_with_added_panel():
    backend = MockBackend()
    backend.seed_demo()
    backend.add_panel("Selection", "rviz_common/Selection", "left")

    yaml_text = export_config_to_yaml(backend)

    assert "Selection" in yaml_text
    assert '"left"' in yaml_text


def test_float_rounding_stable():
    backend = MockBackend()
    backend.seed_demo()
    backend.set_view(distance=10.123456789, yaw=0.555555555, pitch=0.444444444)

    doc = build_rviz_document(backend.config_snapshot())
    view = doc["Visualization Manager"]["Views"]["Current"]

    assert view["Distance"] == round(10.123456789, 6)
    assert view["Yaw"] == round(0.555555555, 6)
    assert view["Pitch"] == round(0.444444444, 6)


def test_yaml_no_trailing_whitespace():
    backend = MockBackend()
    backend.seed_demo()

    yaml_text = export_config_to_yaml(backend)

    for line in yaml_text.split("\n"):
        assert line == line.rstrip(), f"trailing whitespace on line: {line!r}"
