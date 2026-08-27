# Host Setup — rviz-mcp

This guide shows how to connect `rviz-mcp` to the most common agent hosts.
The server speaks stdio MCP, so any host that can launch a command works.

## Prerequisites

```bash
pip install "git+https://github.com/mergeos-bounties/rviz-mcp.git"
rviz-mcp version
rviz-mcp doctor      # validates the environment (no ROS required for mock mode)
```

The `doctor` command runs fully offline using the built-in mock, so you can
verify your install before connecting any host.

## Grok (recommended)

Grok installs the CLI **and** the plugin (skill + MCP server) in one step:

```bash
pip install "git+https://github.com/mergeos-bounties/rviz-mcp.git" && \
  grok plugin install mergeos-bounties/rviz-mcp --trust
```

Verify:

```bash
grok plugin list
grok mcp list
```

## Claude Desktop

Add the server to your `claude_desktop_config.json` (`mcpServers` block):

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

`RVIZ_MCP_MODE=mock` uses the offline bridge — no ROS/RViz needed. Set it to
`live` only when a real RViz2 instance is reachable.

## Cursor

Cursor reads `.mcp.json` at the workspace root. Create or merge:

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

After saving, open **Settings → MCP** and confirm `rviz-mcp` shows as
connected. Use "Restart MCP" if it does not appear immediately.

## Annotated JSON (no secrets)

A minimal valid stdio launch payload:

```json
{
  "command": "rviz-mcp",
  "args": ["serve"],
  "env": {
    "RVIZ_MCP_MODE": "mock"
  }
}
```

> Never put tokens, SSH keys, or ROS auth in this config. The mock bridge
> needs no credentials; the live bridge authenticates via your existing
> ROS environment, not via this file.

## Troubleshooting

- **`command not found: rviz-mcp`** — ensure the install finished and the
  Python scripts dir is on your `PATH` (or use the full path to the binary).
- **Host shows disconnected** — run `rviz-mcp doctor`; if it passes, restart
  the MCP host process.
- **Live mode errors** — confirm RViz2 is running and reachable; fall back to
  `RVIZ_MCP_MODE=mock` for local development.

See also [LIVE_BRIDGE.md](./LIVE_BRIDGE.md) for connecting a real RViz2 instance.
