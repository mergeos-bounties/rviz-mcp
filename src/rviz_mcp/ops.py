"""Core RViz2 display-graph operations — pure functions (no state, no I/O).

These are the inner implementation layer of the 3-layer MCP architecture:
  ops.py   (this file)   — pure functions, stateless
  mock.py  (MockBackend) — stateful backend that calls ops functions
  server.py              — @mcp.tool() decorators that call the backend
"""

from __future__ import annotations

from typing import Any


# ── display CRUD ────────────────────────────────────────────────────────


def list_displays(displays: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Return all displays in the current graph as a list of dicts."""
    return list(displays.values())


def add_display(
    displays: dict[str, dict[str, Any]],
    name: str,
    class_name: str = "rviz_default_plugins/Marker",
    topic: str = "",
    enabled: bool = True,
) -> dict[str, Any]:
    """Add a new display entry to the display graph.

    Returns the new display dict on success, or an error dict if the name
    is already taken.
    """
    if not name or not name.strip():
        return {"ok": False, "error": "display name required"}
    name = name.strip()
    if name in displays:
        return {"ok": False, "error": f"display {name} already exists"}
    entry = {
        "name": name,
        "class": class_name,
        "enabled": bool(enabled),
        "topic": topic,
    }
    displays[name] = entry
    return {"ok": True, "display": dict(entry)}


def remove_display(
    displays: dict[str, dict[str, Any]],
    name: str,
    *,
    protected: tuple[str, ...] = ("Grid",),
) -> dict[str, Any]:
    """Remove a display from the graph by name.

    By default ``"Grid"`` is protected — pass ``protected=()`` to bypass.
    """
    name = (name or "").strip()
    if not name:
        return {"ok": False, "error": "display name required"}
    if name not in displays:
        return {"ok": False, "error": f"unknown display {name}"}
    if name in protected:
        return {"ok": False, "error": f"cannot remove {name} (protected)"}
    del displays[name]
    return {"ok": True, "removed": name}


# ── fixed frame ─────────────────────────────────────────────────────────


def set_fixed_frame(state: dict[str, Any], frame: str) -> dict[str, Any]:
    """Update the fixed-frame id on the shared state dict."""
    frame = (frame or "").strip()
    if not frame:
        return {"ok": False, "error": "frame required"}
    state["fixed_frame"] = frame
    return {"ok": True, "fixed_frame": frame}
