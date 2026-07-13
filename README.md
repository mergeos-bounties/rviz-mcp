# rviz-mcp

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.1.0-0E8A16.svg)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-5319E7.svg)](https://modelcontextprotocol.io)
[![MergeOS](https://img.shields.io/badge/MergeOS-bounties-5319E7.svg)](https://github.com/mergeos-bounties)

**rviz-mcp** is an [MCP](https://modelcontextprotocol.io) server so AI agents can control **RViz2** displays, fixed frames, and views — with a full **offline mock** for CI and demos (no ROS/RViz install required).

**Product:** [mergeos-bounties/rviz-mcp](https://github.com/mergeos-bounties/rviz-mcp)

---

## Highlights

| Capability | Description |
| --- | --- |
| **Offline mock** | Display tree, fixed frame, view controller |
| **Live bridge** | Optional HTTP/file bridge when `RVIZ_MCP_MODE=live` |
| **MCP stdio** | Cursor / Claude / Grok host integration |
| **CLI** | `status` · `demo` · `doctor` · `serve` · `call` |

---

## Quick start

```powershell
cd rviz-mcp
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
rviz-mcp demo
rviz-mcp doctor
rviz-mcp status
pytest -q
```

```powershell
rviz-mcp serve
```

---

## Modes

| Mode | Env | Behavior |
| --- | --- | --- |
| **mock** (default) | `RVIZ_MCP_MODE=mock` | In-memory RViz config |
| **live** | `RVIZ_MCP_MODE=live` + bridge URL/file | Forwards to local RViz bridge |

---

## Tools

| Tool | Purpose |
| --- | --- |
| `rviz_doctor` | Connectivity / config health |
| `status` (CLI) | Fixed frame, display count, mode, version (`--json` supported) |
| `rviz_seed_demo` | Reset mock displays (Grid, TF, RobotModel) |
| `rviz_list_displays` | Current display tree |
| `rviz_add_display` / `rviz_remove_display` | Manage displays |
| `rviz_set_fixed_frame` | Fixed frame (e.g. `map`, `odom`) |
| `rviz_set_view` | View controller type + look-at |
| `rviz_load_config` / `rviz_save_config` | Config path (mock records path) |
| `rviz_screenshot` | Mock screenshot path |

---

## Resources

| URI | Purpose |
| --- | --- |
| `rviz://config` | Read-only snapshot of the current config: `fixed_frame`, `view`, `displays` (with `display_count`), `panels`, and `config_path`. Served from the mock display tree offline. |

Example payload:

```json
{
  "ok": true,
  "mode": "mock",
  "fixed_frame": "map",
  "view": { "class": "rviz_default_plugins/Orbit", "distance": 10.0 },
  "displays": [
    { "name": "Grid", "class": "rviz_default_plugins/Grid", "enabled": true, "topic": "" }
  ],
  "display_count": 3,
  "panels": [ { "class": "rviz_common/Displays", "name": "Displays" } ],
  "config_path": "mock://default.rviz"
}
```

---

## Examples

- [examples/cursor_mcp.json](examples/cursor_mcp.json)
- [examples/claude_desktop_config.json](examples/claude_desktop_config.json)

---

## Development

```powershell
ruff check src tests
pytest -q
rviz-mcp tools list
```

---

## MergeOS bounties

Star → claim issue → PR to **master** → MRG **25–200**.  
See [mergeos](https://github.com/mergeos-bounties/mergeos).

---

## License

MIT · MergeOS / ThanhTrucSolutions
