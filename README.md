# rviz-mcp

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.1.0-0E8A16.svg)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-5319E7.svg)](https://modelcontextprotocol.io)
[![MergeOS](https://img.shields.io/badge/MergeOS-bounties-5319E7.svg)](https://github.com/mergeos-bounties)

**rviz-mcp** is an [MCP](https://modelcontextprotocol.io) server so AI agents can control **RViz2** displays, fixed frames, and views — with a full **offline mock** for CI and demos (no ROS/RViz install required).

**Product:** [mergeos-bounties/rviz-mcp](https://github.com/mergeos-bounties/rviz-mcp)

---

## Install (one command)

### Grok — recommended

```bash
pip install "git+https://github.com/mergeos-bounties/rviz-mcp.git" && grok plugin install mergeos-bounties/rviz-mcp --trust
```

This installs the **Python CLI** (`rviz-mcp`) and the **Grok plugin** (skill + MCP server from `.mcp.json`).

Check:

```bash
rviz-mcp version
rviz-mcp doctor
rviz-mcp demo
grok plugin list
grok mcp list
```

Local clone:

```bash
git clone https://github.com/mergeos-bounties/rviz-mcp.git
cd rviz-mcp
pip install -e ".[dev]"
grok plugin install . --trust
```

### Other agents (stdio MCP)

After `pip install "git+https://github.com/mergeos-bounties/rviz-mcp.git"`, point any MCP host at:

| Field | Value |
| --- | --- |
| command | `rviz-mcp` |
| args | `["serve"]` |
| env | `RVIZ_MCP_MODE=mock` |

**Claude Desktop** — merge [examples/claude_desktop_config.json](examples/claude_desktop_config.json) into Claude MCP config.

**Cursor** — merge [examples/cursor_mcp.json](examples/cursor_mcp.json).

**Grok config.toml** (manual, without plugin):

```toml
[mcp_servers.rviz_mcp]
command = "rviz-mcp"
args = ["serve"]
env = { RVIZ_MCP_MODE = "mock" }
enabled = true
```

**One-liner via Grok CLI:**

```bash
pip install "git+https://github.com/mergeos-bounties/rviz-mcp.git"
grok mcp add rviz-mcp -- rviz-mcp serve
```


## Supported AI agents / hosts

| Host | Support | Install |
| --- | --- | --- |
| **Grok** (CLI / TUI / Build) | **Yes** | `grok plugin install mergeos-bounties/rviz-mcp --trust` then `pip install "git+https://github.com/mergeos-bounties/rviz-mcp.git"` |
| **Claude Desktop** | **Yes** | Copy [examples/claude_desktop_config.json](examples/claude_desktop_config.json) into Claude MCP settings |
| **Cursor** | **Yes** | Merge [examples/cursor_mcp.json](examples/cursor_mcp.json) into Cursor MCP config |
| **Claude Code** | **Yes** | stdio MCP: same `command`/`args` as Claude Desktop / Grok |
| **VS Code** (MCP / Continue / Cline) | **Yes** | Generic stdio server config pointing at `rviz-mcp serve` |
| **Windsurf / Cascade** | **Yes** | stdio MCP entry with `rviz-mcp` + `serve` |
| **Codex CLI** | **Yes** (stdio) | Register MCP server command `rviz-mcp serve` in Codex MCP settings |
| **ChatGPT Desktop** | **Partial** | Only if host supports custom MCP stdio servers |
| **Gemini CLI** | **Partial** | Only if MCP stdio plugins are enabled |

All packages speak **MCP over stdio** (`rviz-mcp serve`). Default mode is **mock** (offline, no simulator/terminal/GIMP required).


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
rviz-mcp demo --profile nav
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
| `rviz_list_panels` | Current panel layout |
| `rviz_add_panel` / `rviz_remove_panel` | Manage mock UI panels |
| `rviz_set_fixed_frame` | Fixed frame (e.g. `map`, `odom`) |
| `rviz_set_view` | View controller type + look-at |
| `rviz_load_config` / `rviz_save_config` | Config path (mock records path) |
| `rviz_screenshot` | Mock screenshot path |
| `rviz_export_config` | Export mock config as JSON (`--format json`) or simplified `.rviz`-compatible YAML (`--format yaml`) |

---

## YAML export

Export the current mock display tree, panels, fixed frame, and view as a
simplified, human-inspectable `.rviz`-compatible YAML document.

```powershell
# Print YAML to stdout
rviz-mcp export-config --format yaml

# Write to a file (atomic, refuses overwrites)
rviz-mcp export-config --format yaml --out my_config.rviz

# JSON snapshot (default — unchanged)
rviz-mcp export-config
```

MCP hosts call `rviz_export_config` with `format` and optional `path`:

```json
{"format": "yaml"}
{"format": "yaml", "path": "out/mock-config.rviz"}
```

File exports require a `.rviz` suffix and refuse to overwrite an existing
file or write through a symlink/junction parent. The YAML is **deterministic**:
repeated calls on the same in-memory state produce byte-for-byte identical
output — validated by a golden fixture in CI.

### Limitations

This export is designed for the offline **mock** backend, human inspection
and round-tripping by YAML consumers. It is an RViz-*like* representation,
not a guarantee of byte-for-byte output or complete behavioural fidelity
with native RViz2 configuration files, plugins, or version-specific schemas.

* No **Widgets** tree (RViz property-tree serialisation).
* No **TF prefix** overrides.
* No **Status** blocks, **Materials** or **Textures** panels.
* PascalCase section names follow common RViz conventions but may not match
  every RViz2 version's exact schema.
* The mock `load_config` command records a path but does **not** rehydrate
  a YAML export into memory — this is an *export*, not a serialisation
  round-trip.
* The YAML emitter is **pure Python** (stdlib only); PyYAML is an
  **optional** extra used for validation in tests (`pip install -e ".[yaml]"`).

Review an export before using it with a native RViz2 installation.

### Sample output

```yaml
Panels:
  - Class: "rviz_common/Displays"
    Name: "Displays"
    Dock: "left"
    Visible: true
  - Class: "rviz_common/Views"
    Name: "Views"
    Dock: "right"
    Visible: true
  - Class: "rviz_common/Time"
    Name: "Time"
    Dock: "bottom"
    Visible: true
Visualization Manager:
  Class: ""
  Displays:
    - Class: "rviz_default_plugins/Grid"
      Enabled: true
      Name: "Grid"
      Topic: ""
    - Class: "rviz_default_plugins/TF"
      Enabled: true
      Name: "TF"
      Topic: "/tf"
    - Class: "rviz_default_plugins/RobotModel"
      Enabled: true
      Name: "RobotModel"
      Topic: "/robot_description"
  Global Options:
    Fixed Frame: "map"
  Views:
    Current:
      Class: "rviz_default_plugins/Orbit"
      Distance: 10.0
      Focal Point:
        X: 0.0
        Y: 0.0
        Z: 0.0
      Yaw: 0.5
      Pitch: 0.4
```

---

## Mock display graph quickstart

Run a full mock RViz2 display tree **without RViz2 installed** — useful for CI,
documentation screenshots, and agent demos.

```powershell
# 1. Seed the default display tree (Grid + TF + RobotModel)
rviz-mcp demo

# 2. Inspect the mock config
rviz-mcp status --json

# 3. Export the full config snapshot for agents
rviz-mcp export-config

# 4. Run against the MCP server (Cursor / Claude / Grok)
rviz-mcp serve
# Then query the rviz://config resource
```

```bash
# Non-PowerShell (bash / zsh)
python -m rviz_mcp demo
python -m rviz_mcp status --json
python -m rviz_mcp export-config
python -m rviz_mcp serve
```

The display graph includes class names, topics, and enable state — every field
an agent needs to understand or replicate the layout.

---

## Demo profiles

The default mock seed includes Grid, TF, and RobotModel. The navigation profile
adds Map, LaserScan, and GlobalPath displays for nav-stack demos:

```powershell
rviz-mcp demo --profile nav
```

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
  "panels": [
    { "class": "rviz_common/Displays", "name": "Displays", "dock": "left", "visible": true },
    { "class": "rviz_common/Views", "name": "Views", "dock": "right", "visible": true },
    { "class": "rviz_common/Time", "name": "Time", "dock": "bottom", "visible": true }
  ],
  "config_path": "mock://default.rviz"
}
```

---

## Examples

- [examples/cursor_mcp.json](examples/cursor_mcp.json)
- [examples/claude_desktop_config.json](examples/claude_desktop_config.json)
- [docs/LIVE_BRIDGE.md](docs/LIVE_BRIDGE.md) for live bridge load_config and screenshot endpoints

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
