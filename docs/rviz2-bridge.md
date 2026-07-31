# RViz2 Remote API Bridge — Design Document

## Overview
Live control bridge between MCP and a remote RViz2 instance via WebSocket.

## Architecture
```
[MCP Client] → [rviz-mcp server] → [rviz2_bridge.py] → WebSocket → [RViz2 Instance]
                                                              ↓
                                                         [MockBackend] (CI/testing)
```

## Components

### RemoteClient
- Connects to RViz2 WebSocket endpoint
- Supports authentication (token-based)
- Auto-reconnect with exponential backoff

### Display API
- `set_view(point, orientation)` — position the camera
- `add_marker(topic, marker_type, pose, scale, color)` — add visualization marker
- `remove_marker(topic, marker_id)` — remove marker
- `clear_all_markers()` — reset all markers
- `set_display_type(topic, display_type)` — change display type
- `get_display_list()` — list active displays

### MockBackend (CI)
- In-memory marker store
- View state tracking
- No actual WebSocket — returns mock responses

## Configuration
```json
{
  "rviz2": {
    "host": "localhost",
    "port": 9090,
    "token": "",
    "reconnect_delay": 2,
    "max_reconnect_attempts": 5
  }
}
```

## Future
- ROS2 topic subscription passthrough
- TF frame publishing
- Interactive marker support
