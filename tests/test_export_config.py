"""Tests for the export-config CLI tool and rviz_export_config MCP tool."""

from pathlib import Path

import yaml
from typer.testing import CliRunner

from rviz_mcp.backend import get_backend
from rviz_mcp.cli import app
from rviz_mcp.config import set_mode

runner = CliRunner()
_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


def _ensure_seeded() -> None:
    """Reset the mock backend to a known default state."""
    set_mode("mock")
    b = get_backend()
    b.seed_demo(profile="default")
    b.set_fixed_frame("map")


def test_export_config_cli_yaml() -> None:
    """CLI export-config outputs valid YAML."""
    _ensure_seeded()
    result = runner.invoke(app, ["export-config"])
    assert result.exit_code == 0
    data = yaml.safe_load(result.stdout)
    assert data["ok"] is True
    assert data["mode"] == "mock"
    assert data["fixed_frame"] == "map"
    assert isinstance(data["displays"], list)
    assert data["display_count"] == 3
    assert "view" in data
    assert data["view"]["class"].startswith("rviz_default_plugins/")
    assert isinstance(data["panels"], list)


def test_export_config_compact() -> None:
    """CLI export-config with --compact flag still produces valid YAML."""
    _ensure_seeded()
    result = runner.invoke(app, ["export-config", "--compact"])
    assert result.exit_code == 0
    data = yaml.safe_load(result.stdout)
    assert data["fixed_frame"] == "map"


def test_export_config_golden_fixture() -> None:
    """CLI export-config output matches the golden fixture."""
    _ensure_seeded()
    b = get_backend()
    b.set_fixed_frame("map")
    result = runner.invoke(app, ["export-config"])
    assert result.exit_code == 0

    fixture_path = _FIXTURE_DIR / "export_config_default.yaml"
    if not fixture_path.exists():
        # Write the golden fixture if it doesn't exist yet
        fixture_path.parent.mkdir(parents=True, exist_ok=True)
        fixture_path.write_text(result.stdout)
    expected = fixture_path.read_text().strip()
    assert result.stdout.strip() == expected, (
        f"CLI output differs from golden fixture {fixture_path}\n"
        f"--- actual ---\n{result.stdout.strip()}\n"
        f"--- expected ---\n{expected}"
    )


def test_export_config_mcp_tool_via_server() -> None:
    """rviz_export_config MCP tool returns valid YAML."""
    from rviz_mcp.server import rviz_export_config

    _ensure_seeded()
    raw = rviz_export_config()
    data = yaml.safe_load(raw)
    assert data["ok"] is True
    assert data["mode"] == "mock"
    assert data["fixed_frame"] == "map"
    assert isinstance(data["displays"], list)
    assert data["display_count"] == 3
    assert "view" in data
    assert "panels" in data


def test_export_config_call_dispatch() -> None:
    """rviz_export_config via CLI call subcommand returns YAML."""
    _ensure_seeded()
    result = runner.invoke(app, ["call", "export_config"])
    assert result.exit_code == 0
    data = yaml.safe_load(result.stdout)
    assert data["ok"] is True
    assert data["fixed_frame"] == "map"
