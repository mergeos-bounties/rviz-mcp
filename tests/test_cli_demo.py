import json

from typer.testing import CliRunner

from rviz_mcp import __version__
from rviz_mcp.backend import get_backend
from rviz_mcp.cli import app
from rviz_mcp.config import set_mode

runner = CliRunner()


def test_demo_exits_zero():
    result = runner.invoke(app, ["demo"])
    assert result.exit_code == 0
    assert "demo complete" in result.stdout


def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0


def test_status_exits_zero():
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "fixed_frame" in result.stdout
    assert "display_count" in result.stdout


def test_status_json():
    set_mode("mock")
    get_backend().seed_demo()  # reset shared mock to known state
    result = runner.invoke(app, ["status", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["mode"] == "mock"
    assert data["version"] == __version__
    assert data["fixed_frame"] == "map"
    assert isinstance(data["display_count"], int)
    assert data["display_count"] == 3
