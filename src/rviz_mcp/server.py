"""FastMCP server: RViz2 tools for AI agents."""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from rviz_mcp.backend import get_backend, switch_mode
from rviz_mcp.config import get_mode

mcp = FastMCP(
    "rviz-mcp",
    instructions=(
        "RViz2 MCP server. Prefer mock mode offline. "
        "Typical flow: rviz_doctor → rviz_list_displays → rviz_add_display → rviz_set_fixed_frame."
    ),
)


def _j(data: Any) -> str:
    return json.dumps(data, indent=2, default=str)


@mcp.resource("rviz://config")
def rviz_config_resource() -> str:
    """Snapshot of the current RViz config (fixed_frame, view, displays, panels).

    Read-only MCP resource addressable at ``rviz://config``. In mock mode it
    returns the in-memory display tree; in live mode it surfaces whatever the
    backend can report.
    """
    b = get_backend()
    snap = getattr(b, "config_snapshot", None)
    if callable(snap):
        return _j(snap())
    return _j(
        {
            "ok": True,
            "mode": get_mode(),
            "backend": b.name,
            "displays": b.list_displays(),
            "doctor": b.doctor(),
        }
    )


@mcp.tool()
def rviz_mode(mode: str | None = None) -> str:
    """Get or set RViz backend mode (mock|live)."""
    if mode:
        return _j(switch_mode(mode))
    b = get_backend()
    return _j({"mode": get_mode(), "backend": b.name, "doctor": b.doctor()})


@mcp.tool()
def rviz_doctor() -> str:
    """Check mock/live RViz connectivity."""
    return _j(get_backend().doctor())


@mcp.tool()
def rviz_seed_demo() -> str:
    """Reset the mock RViz display tree (mock only)."""
    return _j(get_backend().seed_demo())


@mcp.tool()
def rviz_list_displays() -> str:
    """List displays in the current config."""
    return _j(get_backend().list_displays())


@mcp.tool()
def rviz_list_panels() -> str:
    """List RViz UI panels in the current layout."""
    return _j(get_backend().list_panels())


@mcp.tool()
def rviz_add_display(
    name: str,
    class_name: str = "rviz_default_plugins/Marker",
    topic: str = "",
    enabled: bool = True,
) -> str:
    """Add a display by class name."""
    return _j(get_backend().add_display(name, class_name, topic, enabled))


@mcp.tool()
def rviz_remove_display(name: str) -> str:
    """Remove a display by name."""
    return _j(get_backend().remove_display(name))


@mcp.tool()
def rviz_add_panel(
    name: str,
    class_name: str = "rviz_common/Panel",
    dock: str = "left",
    visible: bool = True,
) -> str:
    """Add a mock RViz UI panel to the layout."""
    return _j(get_backend().add_panel(name, class_name, dock, visible))


@mcp.tool()
def rviz_remove_panel(name: str) -> str:
    """Remove a mock RViz UI panel by name."""
    return _j(get_backend().remove_panel(name))


@mcp.tool()
def rviz_set_fixed_frame(frame: str) -> str:
    """Set the fixed frame (e.g. map, odom, base_link)."""
    return _j(get_backend().set_fixed_frame(frame))


@mcp.tool()
def rviz_set_view(
    view_class: str = "rviz_default_plugins/Orbit",
    distance: float = 10.0,
    yaw: float = 0.5,
    pitch: float = 0.4,
) -> str:
    """Configure the view controller."""
    return _j(get_backend().set_view(view_class, distance, yaw, pitch))


@mcp.tool()
def rviz_load_config(path: str) -> str:
    """Load an RViz config path (mock records the path)."""
    return _j(get_backend().load_config(path))


@mcp.tool()
def rviz_save_config(path: str) -> str:
    """Save current mock config path."""
    return _j(get_backend().save_config(path))


@mcp.tool()
def rviz_screenshot(path: str | None = None) -> str:
    """Capture a mock screenshot path (live bridge may write a real PNG)."""
    return _j(get_backend().screenshot(path))


@mcp.tool()
def rviz_export_config() -> str:
    """Export current mock RViz config for agents as a JSON snapshot.

    Returns fixed_frame, view, displays, panels, and config_path — useful for
    agents that need to inspect or replicate the current RViz state.
    """
    b = get_backend()
    snap = getattr(b, "config_snapshot", None)
    if callable(snap):
        return _j(snap())
    return _j(
        {
            "ok": False,
            "error": "config_snapshot not available in this backend",
            "backend": b.name,
        }
    )


def run_stdio() -> None:
    mcp.run(transport="stdio")


@mcp.tool()
def rviz_toggle_topic(display_name: str, topic: str) -> str:
    """Toggle topic visibility for a display."""
    return _j(get_backend().toggle_topic_visibility(display_name, topic))


@mcp.tool()
def rviz_topic_visibility(display_name: str) -> str:
    """Get visible topics for a display."""
    return _j(get_backend().get_topic_visibility(display_name))


@mcp.tool()
def rviz_view_presets() -> str:
    """List view controller presets (orbit, fps, top_down, front)."""
    return _j(get_backend().view_presets())


@mcp.tool()
def rviz_set_view_preset(name: str) -> str:
    """Set view controller to a named preset."""
    return _j(get_backend().set_view_preset(name))


@mcp.tool()
def rviz_display_properties(display_name: str) -> str:
    """Get display property bag (color, size, alpha, type)."""
    return _j(get_backend().display_properties(display_name))


@mcp.tool()
def rviz_update_display(
    display_name: str,
    color: list[float] | None = None,
    size: float | None = None,
    alpha: float | None = None,
) -> str:
    """Update display properties (color, size, alpha)."""
    return _j(get_backend().update_display_properties(display_name, color, size, alpha))
