"""Remote RViz2 bridge client — stub for design phase (issue #24).

Exports:
    RemoteBridge — stub client that returns ok:false for all endpoints
    get_bridge   — factory respecting RVIZ_MCP_BRIDGE_URL / _TOKEN
"""

from __future__ import annotations

import os

# Re-export RemoteBridge at runtime for direct imports
from rviz_mcp.bridge.remote import RemoteBridge  # used for re-export


def get_bridge():
    """Return a RemoteBridge instance configured from environment variables."""

    base_url = (os.environ.get("RVIZ_MCP_BRIDGE_URL") or "http://127.0.0.1:8765").strip()
    token = (os.environ.get("RVIZ_MCP_BRIDGE_TOKEN") or "").strip() or None
    timeout_str = (os.environ.get("RVIZ_MCP_BRIDGE_TIMEOUT") or "5").strip()
    try:
        timeout = float(timeout_str)
    except ValueError:
        timeout = 5.0

    return RemoteBridge(base_url=base_url, token=token, timeout=timeout)
