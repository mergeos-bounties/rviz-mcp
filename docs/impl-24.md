# Live RViz2 Remote API Bridge — Design & Stub

**Issue:** mergeos-bounties/rviz-mcp #24
**Bounty:** 200 MRG
**Status:** stub / design phase
**Branch:** feat/impl-24-*

---

## 1. Motivation

The current live backend (`src/rviz_mcp/backend/live.py`) forwards only three
operations to an external HTTP bridge: `GET /health`, `POST /load_config`, and
`POST /screenshot`. All other operations (`add_display`, `set_fixed_frame`,
`set_view`, etc.) return `_unsupported` in live mode.

We need a **remote API bridge** that exposes the full RViz2 display-control
surface so an MCP server running in live mode can drive a real RViz2 instance
over the network — no shell access, no ROS workspace, no X11 forwarding required.

### Use cases

| Actor | Goal |
|-------|------|
| CI pipeline | Drive a headless RViz2 container, take screenshots, validate display trees |
| Remote operator | Tweak RViz displays on a robot from a laptop over WiFi |
| AI agent (live) | Full RViz2 control through MCP tools when RVIZ_MCP_MODE=live |
| Integration test | Spin up bridge + RViz2, run display CRUD assertions |

---

## 2. Architecture

```
+--------------+    MCP/stdio     +--------------+    HTTP/WS     +-----------------+
|  AI Agent    | <-------------> |  rviz-mcp     | <-------------> |  Remote Bridge   |
|  (Grok/Cursor)|                 |  (live mode)  |               |  (rviz2-bridge)  |
+--------------+                  +--------------+               +--------+--------+
                                                                          |
                                                                   +------v------+
                                                                   |   RViz2     |
                                                                   |  (real)     |
                                                                   +-------------+
```

### 2.1 rviz-mcp (MCP server)

- Runs on the operator's machine or inside the AI agent host.
- In `live` mode, forwards MCP tool calls to the remote bridge via HTTP/WebSocket.
- Fail-closed: if the bridge is unreachable, returns `ok: false`.

### 2.2 Remote Bridge (rviz2-bridge)

- Runs **on the same host as RViz2** (or a container with access to the ROS 2
  graph and RViz2 Python API).
- Exposes a REST+WebSocket API for full RViz2 control.
- Written in Python 3.11+ using `aiohttp` or `FastAPI` + `uvicorn`.

### 2.3 Transport

| Path | Method | Purpose |
|------|--------|---------|
| `GET /health` | GET | Liveness + RViz status |
| `GET /displays` | GET | List displays |
| `POST /displays` | POST | Add display |
| `DELETE /displays/{name}` | DELETE | Remove display |
| `GET /displays/{name}` | GET | Display properties |
| `PATCH /displays/{name}` | PATCH | Update display props |
| `GET /panels` | GET | List panels |
| `POST /panels` | POST | Add panel |
| `DELETE /panels/{name}` | DELETE | Remove panel |
| `PUT /fixed_frame` | PUT | Set fixed frame |
| `PUT /view` | PUT | Set view controller |
| `GET /view/presets` | GET | List view presets |
| `PUT /view/preset/{name}` | PUT | Apply view preset |
| `POST /config/load` | POST | Load .rviz config file |
| `POST /config/save` | POST | Save current config |
| `POST /screenshot` | POST | Capture screenshot |
| `GET /topics` | GET | List ROS topics |
| `POST /topics/{display}/visibility` | POST | Toggle topic visibility |
| `WS /events` | WebSocket | Stream RViz state changes |

### 2.4 Authentication

- **Loopback-only by default** (`127.0.0.1`). No auth required.
- **Shared secret** via `RVIZ_MCP_BRIDGE_TOKEN` env var for remote deployments.
- Token sent as `Authorization: Bearer <token>` header.

---

## 3. Stub Implementation

The stub lives in `src/rviz_mcp/bridge/` and provides:

### 3.1 RemoteBridge class

Every stub method returns:

```json
{
  "ok": false,
  "stub": true,
  "endpoint": "<method_path>",
  "message": "RemoteBridge stub"
}
```

### 3.2 Integration with LiveBackend

LiveBackend will be updated to delegate to RemoteBridge instead of returning
_unsupported. The stub bridge returns ok:false for all operations, preserving
the fail-closed contract.

---

## 4. Bridge Server (future work)

A companion package rviz2-bridge will implement the server side:

```
rviz2-bridge/
+-- pyproject.toml
+-- src/
|   +-- rviz2_bridge/
|       +-- __init__.py
|       +-- app.py
|       +-- rviz_api.py
|       +-- websocket.py
|       +-- auth.py
+-- tests/
```

---

## 5. Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| RVIZ_MCP_MODE | mock or live | mock |
| RVIZ_MCP_BRIDGE_URL | Remote bridge base URL | (none) |
| RVIZ_MCP_BRIDGE_TOKEN | Shared secret for auth | (none) |
| RVIZ_MCP_BRIDGE_TIMEOUT | Request timeout (seconds) | 5 |

---

## 6. Testing Strategy

| Layer | Tool | Scope |
|-------|------|-------|
| Stub unit tests | pytest | RemoteBridge returns correct stub shapes |
| Live backend tests | pytest + unittest.mock | LiveBackend delegates to bridge, fails closed |
| Integration (future) | pytest + testcontainers | Spin up bridge + headless RViz2 |
| CI | GitHub Actions (ci-24.yml) | Stub import smoke + mock regression |

---

## 7. Deliverables for This PR

- [x] docs/impl-24.md — this design document
- [x] .github/workflows/ci-24.yml — CI workflow for live bridge stub
- [x] src/rviz_mcp/bridge/__init__.py — package init + factory
- [x] src/rviz_mcp/bridge/remote.py — RemoteBridge stub
- [ ] tests/test_remote_bridge.py — stub unit tests (future)
- [ ] src/rviz_mcp/backend/live.py — delegate to RemoteBridge (future)
- [ ] rviz2-bridge companion package (future bounty)

---

## 8. References

- RViz2 Architecture Overview (docs.ros.org)
- MCP Specification (modelcontextprotocol.io)
- ROS 2 Python API (docs.ros2.org)
- Existing docs/LIVE_BRIDGE.md
