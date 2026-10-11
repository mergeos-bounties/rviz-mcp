# Host MCP Setup — Cursor, Claude Desktop, Grok

This guide shows how to point each supported MCP host at **rviz-mcp**. All snippets
use **mock mode** (`RVIZ_MCP_MODE=mock`) so they work with no ROS/RViz install.

> No secrets appear in any snippet below. Every value is a local command path and an
> environment flag.

---

## 0. Install once

```bash
pip install "git+https://github.com/mergeos-bounties/rviz-mcp.git"
rviz-mcp version   # sanity check
```

The installed entry point is the `rviz-mcp` console script; hosts launch it with
`serve` over stdio.

---

## 1. Cursor

Merge the following into your Cursor MCP config (`~/.cursor/mcp.json`, or the
per-project `.cursor/mcp.json`):

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

Annotated:

| Key | Meaning |
|---|---|
| `command` | The console script installed by pip. Use an absolute path (`which rviz-mcp`) if your host does not inherit your shell `PATH`. |
| `args` | `["serve"]` runs the stdio MCP server. |
| `env.RVIZ_MCP_MODE` | `mock` = offline demo backend; set `live` only when a real RViz bridge is running. |

---

## 2. Claude Desktop

Open **Settings → Developer → Edit Config** (creates
`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS,
`%APPDATA%\Claude\claude_desktop_config.json` on Windows) and merge:

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

Restart Claude Desktop after saving. The `rviz-mcp` tools appear under the tools
(🔌) menu.

---

## 3. Grok

**Recommended — via the plugin** (installs both the skill and the MCP server from
`.mcp.json`):

```bash
pip install "git+https://github.com/mergeos-bounties/rviz-mcp.git" \
  && grok plugin install mergeos-bounties/rviz-mcp --trust
```

**Manual — paste into `~/.grok/config.toml`** (or a project `.grok/config.toml`):

```toml
[mcp_servers.rviz_mcp]
command = "rviz-mcp"
args = ["serve"]
env = { RVIZ_MCP_MODE = "mock" }
enabled = true
```

---

## 4. Claude Code

Same stdio shape as Claude Desktop / Grok:

```bash
claude mcp add rviz-mcp -- rviz-mcp serve
```

Then set `RVIZ_MCP_MODE=mock` in your environment (or the host's env block).

---

## 5. Verify the host sees the tools

From any host, ask the agent to call `rviz_mcp_list_displays` (mock mode returns the
seeded panel). If the tool is missing:

1. `which rviz-mcp` — confirm the console script resolves; paste the absolute path
   into `command` if not.
2. `rviz-mcp doctor` — confirms the server starts.
3. Re-open the host config; most hosts read MCP config only at startup.

---

## Compatibility

| Host | Supported | Install |
|---|---|---|
| Grok (CLI / TUI / Build) | Yes | `grok plugin install mergeos-bounties/rviz-mcp --trust` + pip |
| Claude Desktop | Yes | Merge the JSON above into Claude MCP settings |
| Cursor | Yes | Merge the JSON above into Cursor MCP config |
| Claude Code | Yes | `claude mcp add rviz-mcp -- rviz-mcp serve` |
