from __future__ import annotations

import json
from typing import Any, Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from rviz_mcp import __version__
from rviz_mcp.backend import get_backend, switch_mode
from rviz_mcp.config import get_mode, set_mode

app = typer.Typer(help="rviz-mcp — MCP server for RViz2", no_args_is_help=True)
tools_app = typer.Typer(help="List / probe tools")
app.add_typer(tools_app, name="tools")
console = Console()

TOOL_NAMES = [
    "rviz_mode",
    "rviz_doctor",
    "rviz_seed_demo",
    "rviz_list_displays",
    "rviz_list_panels",
    "rviz_add_display",
    "rviz_remove_display",
    "rviz_add_panel",
    "rviz_remove_panel",
    "rviz_set_fixed_frame",
    "rviz_set_view",
    "rviz_load_config",
    "rviz_save_config",
    "rviz_screenshot",
]


@app.command("version")
def version_cmd() -> None:
    rprint({"version": __version__, "mode": get_mode()})


@app.command("doctor")
def doctor_cmd() -> None:
    b = get_backend()
    info = b.doctor()
    info["rviz_mcp_version"] = __version__
    info["mode"] = get_mode()
    rprint(info)


@app.command("status")
def status_cmd(
    json_out: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Show current RViz state: fixed_frame, display count, mode, version."""
    b = get_backend()
    info = b.doctor()
    status = {
        "fixed_frame": info.get("fixed_frame"),
        "display_count": info.get("display_count", len(b.list_displays())),
        "mode": get_mode(),
        "version": __version__,
    }
    if json_out:
        typer.echo(json.dumps(status))
    else:
        rprint(status)


@app.command("demo")
def demo_cmd(
    profile: str = typer.Option("default", "--profile", help="Mock seed profile: default or nav."),
) -> None:
    """Offline smoke: seed displays, add LaserScan, set frame/view, screenshot."""
    set_mode("mock")
    b = get_backend()
    rprint(b.seed_demo(profile=profile))
    rprint(b.doctor())
    rprint({"displays": b.list_displays()})
    if not any(d.get("name") == "LaserScan" for d in b.list_displays()):
        rprint(
            {
                "add": b.add_display(
                    "LaserScan",
                    "rviz_default_plugins/LaserScan",
                    "/scan",
                    True,
                )
            }
        )
    rprint({"frame": b.set_fixed_frame("odom")})
    rprint({"view": b.set_view(distance=8.0, yaw=0.8, pitch=0.3)})
    rprint({"save": b.save_config("mock://demo.rviz")})
    rprint({"shot": b.screenshot("demo_rviz.png")})
    rprint("rviz-mcp demo complete (mock).")


@tools_app.command("list")
def tools_list() -> None:
    table = Table(title="rviz-mcp tools")
    table.add_column("Tool")
    for n in TOOL_NAMES:
        table.add_row(n)
    console.print(table)


@app.command("call")
def call_cmd(
    tool: str = typer.Argument(..., help="Short name e.g. doctor or rviz_doctor"),
    arg: Optional[list[str]] = typer.Argument(None, help="key=value pairs"),
) -> None:
    b = get_backend()
    name = tool if tool.startswith("rviz_") else f"rviz_{tool}"
    kv: dict[str, Any] = {}
    for a in arg or []:
        if "=" in a:
            k, v = a.split("=", 1)
            try:
                kv[k] = json.loads(v)
            except json.JSONDecodeError:
                kv[k] = v
    dispatch = {
        "rviz_mode": lambda: switch_mode(str(kv.get("mode", get_mode()))),
        "rviz_doctor": b.doctor,
        "rviz_seed_demo": b.seed_demo,
        "rviz_list_displays": b.list_displays,
        "rviz_list_panels": b.list_panels,
        "rviz_add_display": lambda: b.add_display(
            str(kv.get("name", "Marker")),
            str(kv.get("class_name", "rviz_default_plugins/Marker")),
            str(kv.get("topic", "")),
            bool(kv.get("enabled", True)),
        ),
        "rviz_remove_display": lambda: b.remove_display(str(kv.get("name", ""))),
        "rviz_add_panel": lambda: b.add_panel(
            str(kv.get("name", "Panel")),
            str(kv.get("class_name", "rviz_common/Panel")),
            str(kv.get("dock", "left")),
            bool(kv.get("visible", True)),
        ),
        "rviz_remove_panel": lambda: b.remove_panel(str(kv.get("name", ""))),
        "rviz_set_fixed_frame": lambda: b.set_fixed_frame(str(kv.get("frame", "map"))),
        "rviz_set_view": lambda: b.set_view(
            str(kv.get("view_class", "rviz_default_plugins/Orbit")),
            float(kv.get("distance", 10.0)),
            float(kv.get("yaw", 0.5)),
            float(kv.get("pitch", 0.4)),
        ),
        "rviz_load_config": lambda: b.load_config(str(kv.get("path", "mock://default.rviz"))),
        "rviz_save_config": lambda: b.save_config(str(kv.get("path", "mock://saved.rviz"))),
        "rviz_screenshot": lambda: b.screenshot(kv.get("path")),
    }
    if name not in dispatch:
        raise typer.BadParameter(f"unknown tool {name}")
    rprint(dispatch[name]())


@app.command("serve")
def serve_cmd() -> None:
    from rviz_mcp.server import run_stdio

    run_stdio()


def main() -> None:
    app()


if __name__ == "__main__":
    app()
