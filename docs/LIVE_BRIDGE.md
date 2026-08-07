# Live bridge HTTP contract

rviz-mcp can run in live mode by forwarding selected operations to a local
RViz bridge. The full HTTP contract covers all backend operations: health,
display/panel management, frame/view control, config, screenshots, topic
visibility, view presets, and display properties.

Mock mode remains the default and does not use the network. Use live mode only
when a trusted local RViz bridge is available:

    :RVIZ_MCP_MODE = "live"
    :RVIZ_MCP_BRIDGE_URL = "http://127.0.0.1:8765"
    rviz-mcp doctor
    rviz-mcp call load_config path=C:\work\demo.rviz
    rviz-mcp call screenshot path=rviz-live.png

Do not put tokens, private URLs, or credentials in the bridge configuration.
Prefer loopback URLs for local desktop automation.

## Endpoint table

Each backend operation maps to exactly one bridge endpoint:

| Operation                   | Method | Endpoint                    |
|-----------------------------|--------|-----------------------------|
| doctor / health             | GET    | /health                     |
| list_displays               | GET    | /displays                   |
| list_panels                 | GET    | /panels                     |
| add_display                 | POST   | /displays/add               |
| remove_display              | POST   | /displays/remove            |
| add_panel                   | POST   | /panels/add                 |
| remove_panel                | POST   | /panels/remove              |
| set_fixed_frame             | POST   | /fixed_frame                |
| set_view                    | POST   | /view                       |
| load_config                 | POST   | /load_config                |
| save_config                 | POST   | /save_config                |
| screenshot                  | POST   | /screenshot                 |
| config_snapshot             | GET    | /config                     |
| toggle_topic_visibility     | POST   | /topic/visibility/toggle    |
| get_topic_visibility        | GET    | /topic/visibility           |
| view_presets                | GET    | /view/presets               |
| set_view_preset             | POST   | /view/preset                |
| display_properties          | GET    | /display/properties         |
| update_display_properties   | POST   | /display/properties         |

All POST endpoints accept a JSON body. GET endpoints may use query parameters
at the bridge implementor's discretion.

---

## GET /health

Returns bridge connectivity and runtime metadata.

Example response:


---

## GET /displays

List all displays in the current RViz config.

Response: 

---

## POST /displays/add

Add a new display. Body: 

Response: 

---

## POST /displays/remove

Remove a display by name. Body: 

Response: 

---

## GET /panels

List all UI panels. Response: 

---

## POST /panels/add

Add a UI panel. Body: 

---

## POST /panels/remove

Remove a panel by name. Body: 

---

## POST /fixed_frame

Set the fixed frame. Body: 

Response: 

---

## POST /view

Configure the view controller.

Body: 

---

## POST /load_config

Load an RViz config path. Body: 

Response: 

---

## POST /save_config

Save the current config. Body: 

Response: 

---

## POST /screenshot

Capture a screenshot. Body (optional): 

Response: 

---

## GET /config

Full config snapshot. Response includes fixed_frame, view, displays, panels, config_path.

---

## POST /topic/visibility/toggle

Toggle topic visibility. Body: 

---

## GET /topic/visibility

Get visible topics for a display. Query: .

---

## GET /view/presets

List available view controller presets.

Response:


---

## POST /view/preset

Set view to a named preset. Body: 

---

## GET /display/properties

Get display property bag. Query: .

---

## POST /display/properties

Update display properties.

Body: 

---

## Failure behavior

Live mode fails closed. If the bridge is missing, down, returns invalid JSON, or
returns non-object JSON, rviz-mcp reports  and does not fall back to
mock data.

Example:


This preserves offline mock tests while keeping live integrations honest: a live
host sees an explicit failure instead of simulated RViz state when the bridge is
unavailable.
