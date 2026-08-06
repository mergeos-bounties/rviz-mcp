# RViz2 Remote API Bridge — Design Document (bounty #24)

## Overview

Live control bridge between MCP and a remote RViz2 instance over HTTP, with mock
fallback for CI. Live mode is opt-in; mock mode remains the default and never
touches the network.

## Architecture

```
[MCP Client] → [rviz-mcp server] → LiveBackend → HTTP POST/GET → [RViz2 Bridge]
                 ↓ (CI/testing)
              MockBackend (in-memory, offline)
```

## HTTP Contract

Every op uses the same envelope:
- `POST` for operations with a body, `GET` for read-only ops
- Bridge returns `{"ok": true, ...}` on success or `{"ok": false, "error": "..."}` on failure
- `rviz-mcp` fails closed: any transport error → explicit `ok: false`, never falls back to mock data

| Op | Method / Path | Body |
|----|---------------|------|
| `doctor` | `GET /health` | — |
| `config_snapshot` | `GET /config_snapshot` | — |
| `list_displays` | `GET /health` → `rviz.displays` | — |
| `list_panels` | `GET /health` → `rviz.panels` | — |
| `add_display` | `POST /add_display` | `{name, class, topic, enabled}` |
| `remove_display` | `POST /remove_display` | `{name}` |
| `add_panel` | `POST /add_panel` | `{name, class, dock, visible}` |
| `remove_panel` | `POST /remove_panel` | `{name}` |
| `set_fixed_frame` | `POST /set_fixed_frame` | `{frame}` |
| `set_view` | `POST /set_view` | `{view_class, distance, yaw, pitch}` |
| `load_config` | `POST /load_config` | `{path}` |
| `save_config` | `POST /save_config` | `{path}` |
| `screenshot` | `POST /screenshot` | `{path?}` |
| `toggle_topic_visibility` | `POST /toggle_topic` | `{display_name, topic}` |
| `get_topic_visibility` | `POST /topic_visibility` | `{display_name}` |
| `view_presets` | `GET /view_presets` | — |
| `set_view_preset` | `POST /set_view_preset` | `{name}` |
| `display_properties` | `POST /display_properties` | `{display_name}` |
| `update_display_properties` | `POST /update_display` | `{display_name, color?, size?, alpha?}` |

## Bridge Client (`rviz2_bridge.py`)

The `Rviz2BridgeClient` wraps HTTP communication with:
- Token-based auth header (`Authorization: Bearer <token>`)
- Auto-reconnect with exponential backoff (2s–30s, max 5 attempts)
- Request timeout: 5 seconds
- Thread-safe connection state

### Mock behaviour in CI

CI runs in mock mode (`RVIZ_MCP_MODE=live` unset). The `MockRviz2Backend`
provides an in-memory implementation:
- Marker store (add/remove/clear/count)
- View state tracking
- Frame tracking
- Display list management

## Configuration

```json
{
  "rviz2": {
    "host": "localhost",
    "port": 8765,
    "token": "",
    "reconnect_delay": 2,
    "max_reconnect_attempts": 5,
    "request_timeout": 5
  }
}
```

Environment variables:
- `RVIZ_MCP_BRIDGE_URL=http://127.0.0.1:8765` — enable live mode
- `RVIZ_MCP_BRIDGE_TOKEN` — auth token for live mode

## Testing

- `tests/test_rviz2_bridge.py`: 10 unit tests covering mock backend operations
- `tests/test_live_backend_contract.py`: contract validation (URL unset, bad JSON, timeout)
- CI runs mock-only by default; live integration tests gated behind `RVIZ_MCP_BRIDGE_URL`

## Future

- ROS2 topic subscription passthrough
- TF frame publishing
- Interactive marker support
- gRPC streaming for real-time visualization updates
