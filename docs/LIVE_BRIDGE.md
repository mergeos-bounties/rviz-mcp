# Live bridge HTTP contract

`rviz-mcp` can run in `live` mode by forwarding selected operations to a local
RViz bridge. The initial live HTTP contract covers bridge health, config loading,
and screenshots:

- `GET /health`
- `POST /load_config`
- `POST /screenshot`

Mock mode remains the default and does not use the network. Use live mode only
when a trusted local RViz bridge is available:

```powershell
$env:RVIZ_MCP_MODE = "live"
$env:RVIZ_MCP_BRIDGE_URL = "http://127.0.0.1:8765"
rviz-mcp doctor
rviz-mcp call load_config path=C:\work\demo.rviz
rviz-mcp call screenshot path=rviz-live.png
```

Do not put tokens, private URLs, or credentials in the bridge configuration.
Prefer loopback URLs for local desktop automation.

## GET /health

Returns bridge connectivity and runtime metadata used by `LiveBackend.doctor()`.

OpenAPI-style notes:

```yaml
get:
  summary: Read live RViz bridge health
  responses:
    "200":
      description: Bridge is reachable.
      content:
        application/json:
          schema:
            type: object
            required: [ok]
            properties:
              ok:
                type: boolean
              service:
                type: string
              mode:
                type: string
              version:
                type: string
              rviz:
                type: object
```

Example:

```json
{
  "ok": true,
  "service": "rviz-bridge",
  "mode": "live",
  "version": "0.1.0",
  "rviz": {
    "fixed_frame": "map",
    "display_count": 3
  }
}
```

`rviz-mcp doctor` wraps this response:

```json
{
  "ok": true,
  "connected": true,
  "mode": "live",
  "bridge": "http",
  "health": {
    "ok": true,
    "service": "rviz-bridge",
    "mode": "live"
  }
}
```

## POST /load_config

Loads an RViz config path through the live bridge.

OpenAPI-style notes:

```yaml
post:
  summary: Load an RViz config file
  requestBody:
    required: true
    content:
      application/json:
        schema:
          type: object
          required: [path]
          properties:
            path:
              type: string
  responses:
    "200":
      description: Config load result.
      content:
        application/json:
          schema:
            type: object
            required: [ok]
            properties:
              ok:
                type: boolean
              loaded:
                type: string
              display_count:
                type: integer
```

Request:

```json
{
  "path": "C:\\work\\demo.rviz"
}
```

Response:

```json
{
  "ok": true,
  "loaded": "C:\\work\\demo.rviz",
  "display_count": 3
}
```

## POST /screenshot

Captures an RViz screenshot through the live bridge. `path` is optional; if it is
omitted, the bridge may choose the output path.

OpenAPI-style notes:

```yaml
post:
  summary: Capture an RViz screenshot
  requestBody:
    required: false
    content:
      application/json:
        schema:
          type: object
          properties:
            path:
              type: string
  responses:
    "200":
      description: Screenshot capture result.
      content:
        application/json:
          schema:
            type: object
            required: [ok, path]
            properties:
              ok:
                type: boolean
              path:
                type: string
              mime_type:
                type: string
              bytes:
                type: integer
```

Request:

```json
{
  "path": "rviz-live.png"
}
```

Response:

```json
{
  "ok": true,
  "path": "rviz-live.png",
  "mime_type": "image/png",
  "bytes": 128
}
```

## Failure behavior

Live mode fails closed. If the bridge is missing, down, returns invalid JSON, or
returns non-object JSON, `rviz-mcp` reports `ok: false` and does not fall back to
mock data.

Example:

```json
{
  "ok": false,
  "connected": false,
  "mode": "live",
  "error": "<connection error>"
}
```

This preserves offline mock tests while keeping live integrations honest: a live
host sees an explicit failure instead of simulated RViz state when the bridge is
unavailable.

## Live control path (bounty #24)

Beyond health/config/screenshot, `rviz-mcp` live mode forwards the full backend
interface to the bridge over a single HTTP contract. Mock mode remains the
default in CI and never touches the network.

Every op below uses the same envelope: a JSON body on `POST` (GET for
read-only ops with no body), and the bridge returns `{"ok": true, ...}` on
success or `{"ok": false, "error": "..."}` on failure. `rviz-mcp` fails closed:
any transport error, invalid JSON, or non-object body yields an explicit
`ok: false` response and never falls back to mock data.

| Op | Method / Path | Body |
|----|---------------|------|
| doctor | `GET /health` | — |
| config_snapshot | `GET /config_snapshot` | — |
| list displays | `GET /health` → `rviz.displays` | — |
| list panels | `GET /health` → `rviz.panels` | — |
| add_display | `POST /add_display` | `{name, class, topic, enabled}` |
| remove_display | `POST /remove_display` | `{name}` |
| add_panel | `POST /add_panel` | `{name, class, dock, visible}` |
| remove_panel | `POST /remove_panel` | `{name}` |
| set_fixed_frame | `POST /set_fixed_frame` | `{frame}` |
| set_view | `POST /set_view` | `{view_class, distance, yaw, pitch}` |
| load_config | `POST /load_config` | `{path}` |
| save_config | `POST /save_config` | `{path}` |
| screenshot | `POST /screenshot` | `{path?}` |
| toggle_topic_visibility | `POST /toggle_topic` | `{display_name, topic}` |
| get_topic_visibility | `POST /topic_visibility` | `{display_name}` |
| view_presets | `GET /view_presets` | — |
| set_view_preset | `POST /set_view_preset` | `{name}` |
| display_properties | `POST /display_properties` | `{display_name}` |
| update_display_properties | `POST /update_display` | `{display_name, color?, size?, alpha?}` |

### Stub / mock default in CI

CI runs in mock mode (`RVIZ_MCP_MODE` unset). Live is opt-in: set
`RVIZ_MCP_BRIDGE_URL=http://127.0.0.1:8765`. Stub bridge contracts are exercised
in a separate job only when a real bridge is present, so offline mock tests stay
green. The `_CONTRACT` table in `src/rviz_mcp/backend/live.py` is the single
source of truth for the op → endpoint mapping; adding a live op means adding one
row and one method.
