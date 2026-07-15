"""Tests for rviz-mcp export_config (issue #7 / mirror #228)."""
from __future__ import annotations

from pathlib import Path
import sys

# Mirror the rviz_mcp source layout (the project's [tool.pytest.ini_options]
# already does this, but we re-do it here so the test file works standalone).
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

from rviz_mcp.backend import get_backend  # noqa: E402
from rviz_mcp.commands.export_config import (  # noqa: E402
    SCHEMA_VERSION,
    build_export,
    export_config,
    to_yaml,
    _as_list_of_dicts,
    _yaml_scalar,
)


@pytest.fixture(autouse=True)
def _reset_mock(monkeypatch):
    monkeypatch.setenv("RVIZ_MCP_MODE", "mock")
    get_backend.__globals__["_BACKEND"] = None  # reset cached singleton
    yield


def test_schema_version_is_string():
    assert isinstance(SCHEMA_VERSION, str)
    assert SCHEMA_VERSION.startswith("rviz-mcp-export")


def test_export_returns_yaml_text():
    be = get_backend()
    text = export_config(be)
    assert isinstance(text, str)
    assert "FixedFrame:" in text
    assert "Displays:" in text
    assert "View:" in text


def test_export_has_header_metadata():
    be = get_backend()
    text = export_config(be)
    assert "generator: rviz-mcp" in text
    assert f"schema: {SCHEMA_VERSION}" in text


def test_export_includes_default_displays():
    be = get_backend()
    data = build_export(be)
    displays = data["Displays"]
    for name in ("Grid", "TF", "RobotModel"):
        assert name in displays, f"missing default display: {name}"


def test_export_includes_default_panels():
    be = get_backend()
    data = build_export(be)
    panels = data["Panels"]
    for name in ("Displays", "Views", "Time"):
        assert name in panels, f"missing default panel: {name}"


def test_export_view_has_required_fields():
    be = get_backend()
    data = build_export(be)
    view = data["View"]
    for key in ("Class", "Distance", "FocalPointX", "FocalPointY",
                "FocalPointZ", "Yaw", "Pitch"):
        assert key in view, f"missing view field: {key}"


def test_export_fixed_frame_is_map():
    be = get_backend()
    data = build_export(be)
    assert data["FixedFrame"] == "map"


def test_export_to_file(tmp_path, monkeypatch):
    monkeypatch.setenv("RVIZ_MCP_MODE", "mock")
    get_backend.__globals__["_BACKEND"] = None
    be = get_backend()
    target = tmp_path / "out.rviz.yaml"
    text = export_config(be, path=str(target))
    assert target.exists()
    assert target.read_text(encoding="utf-8") == text


def test_export_yaml_round_trip():
    """The exported YAML should parse back to an equivalent dict via PyYAML."""
    be = get_backend()
    text = export_config(be)
    try:
        import yaml
    except ImportError:
        pytest.skip("PyYAML not installed")
    parsed = yaml.safe_load(text)
    assert isinstance(parsed, dict)
    assert parsed["FixedFrame"] == "map"
    assert "Grid" in parsed["Displays"]


def test_as_list_of_dicts_normalises_list():
    out = _as_list_of_dicts([{"name": "A"}, {"name": "B"}])
    assert len(out) == 2


def test_as_list_of_dicts_normalises_dict():
    out = _as_list_of_dicts({"A": {"class": "x"}, "B": {"class": "y"}})
    names = sorted(o["name"] for o in out)
    assert names == ["A", "B"]


def test_as_list_of_dicts_handles_none():
    assert _as_list_of_dicts(None) == []


def test_as_list_of_dicts_handles_garbage():
    assert _as_list_of_dicts(123) == []


def test_yaml_scalar_special_strings_quoted():
    # Strings with colons or starting with ? must be quoted
    assert _yaml_scalar("hello") == "hello"
    assert _yaml_scalar("a: b").startswith('"')
    assert _yaml_scalar("?why").startswith('"')


def test_yaml_scalar_bool_int_float_none():
    assert _yaml_scalar(True) == "true"
    assert _yaml_scalar(False) == "false"
    assert _yaml_scalar(42) == "42"
    assert _yaml_scalar(3.14) in ("3.14",)
    assert _yaml_scalar(None) == "null"


def test_cli_runs_export_config(monkeypatch, capsys):
    """Calling export_config() should print YAML the CLI invocation would."""
    monkeypatch.setenv("RVIZ_MCP_MODE", "mock")
    get_backend.__globals__["_BACKEND"] = None
    be = get_backend()
    out = export_config(be)
    print(out, end="")
    captured = capsys.readouterr()
    assert "FixedFrame:" in captured.out
    assert "Displays:" in captured.out


def test_cli_with_out_writes_file(monkeypatch, tmp_path):
    """The underlying export_config(path=...) writes the file."""
    monkeypatch.setenv("RVIZ_MCP_MODE", "mock")
    get_backend.__globals__["_BACKEND"] = None
    be = get_backend()
    target = tmp_path / "snapshot.yaml"
    text = export_config(be, path=str(target))
    assert target.exists()
    assert target.read_text(encoding="utf-8") == text
