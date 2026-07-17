# RViz-MCP Host Setup Guide

Guide for connecting AI coding assistants (Cursor, Claude Desktop, Grok) to `rviz-mcp` over the Model Context Protocol (MCP) stdio transport.

**Prerequisites:** Python 3.11+, `rviz-mcp` installed.

```bash
pip install "git+https://github.com/mergeos-bounties/rviz-mcp.git"
# verify
rviz-mcp doctor
```

---

## 1. Cursor

Open Cursor settings → **MCP** → click **Add new MCP server**.

| Field | Value |
|---|---|
| Name | `rviz-mcp` |
| Type | `command` |
| Command | `rviz-mcp` |
| Args | `serve` |
| ENV | `RVIZ_MCP_MODE=mock` |

> **Annotated JSON** (merge this into `~/.cursor/mcp.json` if you prefer editing the file directly):

```json
{
  "mcpServers": {
    "rviz-mcp": {
      "command": "rviz-mcp",
      "args": ["serve"],
      "env": {
        "RVIZ_MCP_MODE": "mock"
      }
    }
  }
}
```

Save → Cursor will start the server. Verify in Cursor's MCP indicator (bottom-right corner) that `rviz-mcp` shows as active (green dot).

> **Screenshot hint:** In Cursor MCP settings the server row shows a colored status dot. Green = connected, grey = not started, red = error. Take a screenshot after confirming the green dot.

---

## 2. Claude Desktop

**macOS / Linux** – open `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows** – open `%APPDATA%\Claude\claude_desktop_config.json`

Merge the `rviz-mcp` block into the existing `mcpServers` object:

```json
{
  "mcpServers": {
    "rviz-mcp": {
      "command": "rviz-mcp",
      "args": ["serve"],
      "env": {
        "RVIZ_MCP_MODE": "mock"
      }
    }
  }
}
```

> Full example (your existing servers are preserved):

```json
{
  "mcpServers": {
    "your-existing-server": {
      "command": "your-command",
      "args": []
    },
    "rviz-mcp": {
      "command": "rviz-mcp",
      "args": ["serve"],
      "env": {
        "RVIZ_MCP_MODE": "mock"
      }
    }
  }
}
```

After saving, **restart Claude Desktop**. In the MCP panel (gear icon → MCP), `rviz-mcp` should appear with a green status indicator.

> **Screenshot hint:** In Claude Desktop, open Settings → MCP. Screenshot shows the server list with `rviz-mcp` entry. Click "rviz-mcp" to expand and show the env var and command.

---

## 3. Grok (CLI / TUI / Build)

### Option A — Grok Plugin (recommended)

```bash
grok plugin install mergeos-bounties/rviz-mcp --trust
```

Then verify:

```bash
grok plugin list       # shows "rviz-mcp" in the list
grok mcp list          # shows "rviz-mcp" as available MCP server
```

> **Screenshot hint:** Terminal output from `grok plugin list` and `grok mcp list`. Both commands should show `rviz-mcp`.

### Option B — Manual Grok config.toml

Edit your `~/.config/grok/config.toml` (or `grok --config <path>`):

```toml
[mcp_servers.rviz_mcp]
command = "rviz-mcp"
args = ["serve"]
env = { RVIZ_MCP_MODE = "mock" }
enabled = true
```

Verify with `grok mcp list`.

### Option C — Grok CLI one-liner

```bash
pip install "git+https://github.com/mergeos-bounties/rviz-mcp.git"
grok mcp add rviz-mcp -- rviz-mcp serve
```

---

## 4. Other Agents (stdio MCP)

`rviz-mcp serve` is a **generic stdio MCP server** — compatible with any MCP host that supports command-based servers.

### Claude Code

Add to `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "rviz-mcp": {
      "command": "rviz-mcp",
      "args": ["serve"],
      "env": {
        "RVIZ_MCP_MODE": "mock"
      }
    }
  }
}
```

### VS Code (MCP extension / Continue / Cline)

Same JSON block as above into your MCP config file (path depends on extension):

```json
{
  "mcpServers": {
    "rviz-mcp": {
      "command": "rviz-mcp",
      "args": ["serve"],
      "env": {
        "RVIZ_MCP_MODE": "mock"
      }
    }
  }
}
```

### Windsurf / Cascade

```json
{
  "mcpServers": {
    "rviz-mcp": {
      "command": "rviz-mcp",
      "args": ["serve"],
      "env": {
        "RVIZ_MCP_MODE": "mock"
      }
    }
  }
}
```

---

## 5. Verifying the Connection

After connecting, use your host's MCP tool panel to run `rviz_doctor`:

```
Tool: rviz_doctor
→ expects JSON response with fields: mode, rviz_mcp_version, fixed_frame, display_count
```

Expected mock output:

```json
{
  "ok": true,
  "mode": "mock",
  "rviz_mcp_version": "0.1.0",
  "fixed_frame": "map",
  "display_count": 3,
  "displays": [
    { "name": "Grid", "class": "rviz_default_plugins/Grid", "enabled": true, "topic": "" },
    { "name": "TF", "class": "rviz_default_plugins/TF", "enabled": true, "topic": "" },
    { "name": "RobotModel", "class": "rviz_default_plugins/RobotModel", "enabled": true, "topic": "" }
  ]
}
```

---

## 6. Troubleshooting

| Symptom | Fix |
|---|---|
| `command not found: rviz-mcp` | Reinstall: `pip install "git+https://github.com/mergeos-bounties/rviz-mcp.git"` |
| Red / error status in MCP panel | Run `rviz-mcp doctor` in terminal to see error; check Python version ≥3.11 |
| Agent can't see rviz tools | Ensure `rviz-mcp serve` is running (not just the CLI commands like `doctor`) |
| "Bad credentials" or auth errors | Only `RVIZ_MCP_MODE=mock` requires no auth; live bridge needs `RVIZ_MCP_BRIDGE_URL` |
| Permission denied | `chmod +x` the `rviz-mcp` binary or use `python -m rviz_mcp serve` |

---

## 7. Screenshots Checklist

- [ ] Cursor: MCP settings page showing `rviz-mcp` with green status dot
- [ ] Claude Desktop: MCP panel with `rviz-mcp` server expanded (env + command visible)
- [ ] Grok: `grok plugin list` and `grok mcp list` output showing `rviz-mcp`
- [ ] Agent tool call: `rviz_doctor` returning JSON (no real secrets/credentials)

---

*See also: [README.md](https://github.com/mergeos-bounties/rviz-mcp) for full feature overview, and [docs/LIVE_BRIDGE.md](LIVE_BRIDGE.md) for connecting to a real RViz2 instance.*