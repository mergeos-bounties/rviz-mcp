# Host MCP Setup Guide

## Prerequisites

- Python 3.10+
- ROS 2 Humble/Iron/Jazzy
- RViz2

## Installation

```bash
pip install rviz-mcp
```

## Configuration

### Cursor

1. Open Cursor Settings → Extensions → MCP
2. Add new server:
   - Name: `rviz-mcp`
   - Type: `command`
   - Command: `python3 -m rviz_mcp`

### Claude Desktop

1. Open Claude → Settings → Developer → MCP Servers
2. Click "Add Server"
3. Fill in:
   - Name: `rviz-mcp`
   - Command: `python3 -m rviz_mcp`

### Grok / X

1. Open Grok → Settings → MCP
2. Click "Add MCP Server"
3. Enter:
   - Name: `rviz-mcp`
   - URL: leave blank
   - Command: `python3 -m rviz_mcp`

## Verification

Run `rviz-mcp --version` to confirm installation.

> **Screenshots**: Add your own screenshots of the configuration panels for each host above.
