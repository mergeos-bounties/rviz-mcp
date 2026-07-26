# Host MCP Setup Guide (Cursor / Claude Desktop / Grok)

This guide documents how to connect `rviz-mcp` to modern AI agent hosts.

---

## 1. Cursor IDE Setup

Add `rviz-mcp` to your Cursor settings under **Features -> MCP Servers -> Add new MCP server**:

- **Name**: `rviz-mcp`
- **Type**: `stdio`
- **Command**: `uvx rviz-mcp` (or `python -m rviz_mcp`)

### `~/.cursor/mcp.json`
```json
{
  "mcpServers": {
    "rviz-mcp": {
      "command": "uvx",
      "args": ["rviz-mcp"]
    }
  }
}
```

---

## 2. Claude Desktop Setup

In Claude Desktop, open **Settings -> Developer -> Edit Config**:

### `claude_desktop_config.json`
```json
{
  "mcpServers": {
    "rviz-mcp": {
      "command": "uvx",
      "args": ["rviz-mcp"]
    }
  }
}
```

---

## 3. Grok / Generic MCP Agent Setup

For custom agent hosts supporting stdio MCP servers:

```json
{
  "name": "rviz-mcp",
  "transport": "stdio",
  "command": "python",
  "args": ["-m", "rviz_mcp.server"]
}
```

---

## 4. Verification

Once connected, ask your agent:
> *"Run `rviz_doctor` to check connectivity."*

Expected JSON response:
```json
{
  "ok": true,
  "connected": true,
  "mode": "mock",
  "rviz_required": false,
  "message": "Mock RViz config active — no RViz install needed",
  "fixed_frame": "map",
  "display_count": 3
}
```
