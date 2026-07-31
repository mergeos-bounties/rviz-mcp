"""Core RViz2 operations — pure functions (no state, no I/O).

MCP 3-layer architecture — ops layer for set-fixed-frame (#20).
"""

from __future__ import annotations

from typing import Any


def set_fixed_frame(state: dict[str, Any], frame: str) -> dict[str, Any]:
    """Update the fixed-frame id on the shared state dict."""
    frame = (frame or "").strip()
    if not frame:
        return {"ok": False, "error": "frame required"}
    state["fixed_frame"] = frame
    return {"ok": True, "fixed_frame": frame}
