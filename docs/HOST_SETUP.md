# Host MCP Setup Guide — rviz-mcp

Step-by-step instructions for connecting **rviz-mcp** to the three major AI
hosts: **Cursor**, **Claude Desktop**, and **Grok**.

---

## 0. Prerequisites

```bash
# Clone the repo (optional, needed for local development)
git clone https://github.com/mergeos-bounties/rviz-mcp.git
cd rviz-mcp

# Install from PyPI or directly from git
pip install "git+https://github.com/mergeos-bounties/rviz-mcp.git"

# Verify installation
rviz-mcp --version
rviz-mcp status
```

> **Note:** `rviz-mcp` runs in **mock mode by default**, so no ROS 2 or RViz2
> install is required for basic testing. Set `RVIZ_MCP_MODE=live` and point the
> bridge at a running RViz2 instance to go live.

---

## 1. Cursor

Cursor uses the standard VS Code MCP extension schema.

### Step 1 — Open Cursor settings

`Cmd/Ctrl + ,` → search **"MCP"**.

### Step 2 — Add the server entry

Paste this into `cursor_mcp.json` (or the in-IDE MCP editor):

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

### Step 3 — Save & reload

Press **Cmd/Ctrl + Shift + P** → "Reload Window". Cursor shows a green
connection indicator next to `rviz-mcp` when connected.

### Screenshot reference

```
┌─────────────────────────────────────────────────────┐
│  MCP Servers                                       │
│  ─────────────────────────────────────────────────  │
│  ● rviz-mcp  (connected, stdio)                    │
│    command: rviz-mcp serve                         │
│    env: RVIZ_MCP_MODE=mock                         │
└─────────────────────────────────────────────────────┘
```

---

## 2. Claude Desktop

Claude Desktop expects a JSON config at `~/.config/Claude/claude_desktop_config.json`.

### Step 1 — Locate the config

```bash
# macOS / Linux
mkdir -p ~/.config/Claude
nano ~/.config/Claude/claude_desktop_config.json
```

### Step 2 — Paste the MCP entry

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

> **Warning:** If other MCP servers are already defined, merge this entry into
> the existing `"mcpServers"` object — do not replace the whole file.

### Step 3 — Restart Claude Desktop

Close the app and reopen. The chat window shows "rviz-mcp" under the available
tools.

### Screenshot reference

```
┌─────────────────────────────────────────────────────────────┐
│  Claude Desktop — Project Settings → MCP                    │
│  ─────────────────────────────────────────────────────────── │
│  [X] rviz-mcp                                               │
│      command: rviz-mcp                                      │
│      args: serve                                            │
│      env: RVIZ_MCP_MODE=mock                                │
│      Transport: stdio                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Grok (xAI)

Grok uses a TOML config at `~/.grok/config.toml` (or project-level `.grok/config.toml`).

### Step 1 — Create the config

```bash
mkdir -p ~/.grok
nano ~/.grok/config.toml
```

### Step 2 — Paste the server entry

```toml
[mcp_servers.rviz_mcp]
command = "rviz-mcp"
args = ["serve"]
env = { RVIZ_MCP_MODE = "mock" }
enabled = true
```

### Step 3 — Restart Grok client

Restart your Grok desktop/mobile client. The MCP tools appear automatically.

### Screenshot reference

```
┌─────────────────────────────────────────────────────────────┐
│  ~/.grok/config.toml                                        │
│  ─────────────────────────────────────────────────────────── │
│  [mcp_servers.rviz_mcp]                                     │
│  command = "rviz-mcp"                                       │
│  args = ["serve"]                                           │
│  env = { RVIZ_MCP_MODE = "mock" }                           │
│  enabled = true                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Quick Smoke Test

Once the host is connected, paste this into the chat to verify the tools work:

```
Use rviz-mcp: list_displays, then set_fixed_frame to "base_link",
then call doctor to confirm.
```

Expected response (mock mode):

```json
{
  "ok": true,
  "displays": ["Grid", "TF", "RobotModel"],
  "fixed_frame": "base_link"
}
```

---

## 5. Going Live

To bridge a real RViz2 instance:

```bash
export RVIZ_MCP_MODE=live
export RVIZ_MCP_BRIDGE_PORT=8080   # bridge side
rviz-mcp serve                     # on same host as bridge
```

Then start the live bridge (see `docs/LIVE_BRIDGE.md` for full details).

---

## Troubleshooting

| Symptom                              | Fix                                                                 |
|--------------------------------------|---------------------------------------------------------------------|
| "command not found: rviz-mcp"        | Run `pip install "git+https://github.com/mergeos-bounties/rviz-mcp.git"` |
| Host shows "disconnected"            | Check the MCP logs panel; ensure `rviz-mcp` is in `$PATH`           |
| Python 3.9 error                     | rviz-mcp requires **Python ≥ 3.11**                                 |
| Live bridge refused                  | Confirm RViz2 + bridge are running on `localhost:<port>`            |

---

> 📁 Source example configs: [`examples/`](https://github.com/mergeos-bounties/rviz-mcp/tree/master/examples/)
