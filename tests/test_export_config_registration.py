from __future__ import annotations

import asyncio
import json

from typer.testing import CliRunner

from rviz_mcp import cli
from rviz_mcp import server as srv
from rviz_mcp.backend.mock import MockBackend


runner = CliRunner()


class ExportBackend(MockBackend):
    def export_config(self, path: str | None = None) -> dict:
        return {"ok": True, "path": path, "format": "rviz-yaml"}


def test_export_tool_is_listed() -> None:
    assert "rviz_export_config" in cli.TOOL_NAMES

    result = runner.invoke(cli.app, ["tools", "list"])

    assert result.exit_code == 0
    assert "rviz_export_config" in result.stdout


def test_cli_dispatches_export_path(monkeypatch) -> None:
    monkeypatch.setattr(cli, "get_backend", lambda: ExportBackend())

    result = runner.invoke(cli.app, ["call", "export_config", "path=out/config.rviz"])

    assert result.exit_code == 0
    assert "out/config.rviz" in result.stdout


def test_cli_dispatches_export_without_path(monkeypatch) -> None:
    monkeypatch.setattr(cli, "get_backend", lambda: ExportBackend())

    result = runner.invoke(cli.app, ["call", "export_config"])

    assert result.exit_code == 0
    assert "'path': None" in result.stdout


def test_server_export_tool_dispatches(monkeypatch) -> None:
    monkeypatch.setattr(srv, "get_backend", lambda: ExportBackend())

    payload = json.loads(srv.rviz_export_config("out/config.rviz"))

    assert payload == {
        "ok": True,
        "path": "out/config.rviz",
        "format": "rviz-yaml",
    }


def test_server_export_tool_is_registered() -> None:
    tools = asyncio.run(srv.mcp.list_tools())

    assert "rviz_export_config" in {tool.name for tool in tools}
