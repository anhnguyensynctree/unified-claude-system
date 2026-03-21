---
name: browse
description: Persistent browser daemon for live web testing, UI verification, and authenticated flows. Use when Claude needs to interact with a running web app — staging, localhost, or production.
---
# Browse — Persistent Browser Daemon

Playwright-backed HTTP daemon. The browser stays alive between commands — auth, cookies, localStorage persist across the full session. Use for interactive QA and UI verification. Use E2E Playwright tests for CI/CD regression coverage.

## Auto-Start (runs before every /browse command)

Before executing any browse command, always run this check first:

```bash
SKILL_DIR="$HOME/.claude/skills/browse"
STATE="$SKILL_DIR/.state.json"

# Check if daemon is alive
if [ -f "$STATE" ]; then
  PORT=$(node -e "console.log(require('$STATE').port)")
  ALIVE=$(curl -s --max-time 1 http://127.0.0.1:$PORT/health | grep -c '"ok":true' || echo 0)
else
  ALIVE=0
fi

# Start daemon if not running
if [ "$ALIVE" = "0" ]; then
  echo "Starting browse daemon..."
  ~/.bun/bin/bun run "$SKILL_DIR/server.ts" > "$SKILL_DIR/.daemon.log" 2>&1 &
  # Wait for state file to appear (max 5s)
  for i in 1 2 3 4 5; do
    sleep 1
    [ -f "$STATE" ] && break
  done
  echo "Browse daemon ready"
fi
```

If the daemon fails to start, check `~/.claude/skills/browse/.daemon.log` for errors.

## Setup (one-time)

```bash
cd ~/.claude/skills/browse
bun install
bun run install-browsers   # installs Chromium
```

## Starting the Daemon

```bash
bun run ~/.claude/skills/browse/server.ts
```

State is written to `~/.claude/skills/browse/.state.json` (port + token, mode 0o600). The daemon shuts down automatically after 30 min of idle. Restart anytime — existing state file is replaced.

Set `BROWSE_PORT=9000` to use a fixed port. Set `BROWSE_IDLE_TIMEOUT=3600000` for 1hr timeout.

## Calling Commands

Read state file for port + token, then POST to `/command`:

```bash
STATE=$(cat ~/.claude/skills/browse/.state.json)
PORT=$(echo $STATE | node -e "process.stdin.resume();let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>console.log(JSON.parse(d).port))")
TOKEN=$(echo $STATE | node -e "process.stdin.resume();let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>console.log(JSON.parse(d).token))")

# Single command
curl -s -X POST http://127.0.0.1:$PORT/command \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"command": "go localhost:3000"}'

# Batch commands (prefer — fewer tool calls)
curl -s -X POST http://127.0.0.1:$PORT/command \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"commands": ["go localhost:3000", "screenshot", "console-errors"]}'
```

## Command Batching

Send multiple commands in one HTTP call — fewer tool uses, fewer tokens:

```json
{
  "commands": [
    "go localhost:3000/login",
    "fill [name=email] test@example.com",
    "fill [name=password] password123",
    "click [type=submit]",
    "screenshot"
  ]
}
```

Batch stops on first error and returns `executed` count alongside results.

## Multi-Context (named browser contexts)

Each context has isolated cookies/auth/storage — test multiple auth states simultaneously:

```bash
# Create and switch to admin context
{"command": "ctx:create admin"}

# Create guest context
{"command": "ctx:create guest"}

# Switch between contexts
{"command": "ctx:switch admin"}
{"command": "go /admin-dashboard"}

{"command": "ctx:switch guest"}
{"command": "go /admin-dashboard"}   # should be blocked

# List all contexts
{"command": "ctx:list"}

# Clean up
{"command": "ctx:destroy guest"}
```

## All Commands

### Navigation
| Command | Description |
|---|---|
| `go <url>` | Navigate (waits for networkidle) |
| `reload` | Reload current page |
| `back` / `forward` | Browser history |

### Interaction
| Command | Description |
|---|---|
| `click <selector>` | Click element |
| `fill <selector> <value>` | Fill input (quote values with spaces) |
| `select <selector> <value>` | Select dropdown option |
| `hover <selector>` | Hover element |
| `key <key>` | Press key: Enter, Tab, Escape, ArrowDown, etc. |
| `scroll <selector\|top\|bottom>` | Scroll page or element into view |

### Reading
| Command | Description |
|---|---|
| `screenshot` | Capture viewport as PNG |
| `screenshot:full` | Capture full-page PNG |
| `text` | Extract all visible text |
| `html [selector]` | Get HTML (capped at 5000 chars) |
| `console-errors` | Flush buffered console errors/warnings |
| `network-errors` | Flush buffered 4xx/5xx + failed requests |

### Inspection
| Command | Description |
|---|---|
| `exists <selector>` | Check element presence |
| `visible <selector>` | Check element visibility |
| `value <selector>` | Get input value |
| `attr <selector> <attr>` | Get attribute value |
| `count <selector>` | Count matching elements |
| `status` | Current URL, title, contexts, tabs |

### Viewport & Tabs
| Command | Description |
|---|---|
| `viewport <width> <height>` | Set viewport size |
| `new-tab [url]` | Open new tab (optional URL) |
| `switch-tab <index>` | Switch to tab by index |
| `close-tab` | Close current tab |
| `tabs` | List all open tabs |

### Context
| Command | Description |
|---|---|
| `ctx:create [name]` | Create isolated context + make active |
| `ctx:list` | List all contexts |
| `ctx:switch <name>` | Switch active context |
| `ctx:destroy <name>` | Destroy context (not default) |

## Response Shape

Every command returns structured JSON — always includes page state and flushed errors:

```json
{
  "ok": true,
  "screenshot": "/path/to/file.png",
  "page": { "url": "http://localhost:3000/dashboard", "title": "Dashboard" },
  "new_console_errors": [{ "type": "error", "text": "...", "ts": 1234567890 }],
  "new_network_errors": [{ "url": "...", "status": 404, "method": "GET", "ts": 1234567890 }],
  "interactive": { "inputs": 3, "buttons": 5, "links": 12, "forms": 1 }
}
```

`new_console_errors` and `new_network_errors` only appear when there are new entries since the last call (buffer is flushed on read).

Use the Read tool with the returned screenshot path to display inline.

## QA Patterns

```json
// Page load check
{"commands": ["go localhost:3000", "console-errors", "screenshot"]}

// Auth flow
{"commands": ["go localhost:3000/login", "fill [name=email] test@x.com", "fill [name=password] pw", "click [type=submit]", "screenshot"]}

// Responsive check
{"commands": ["go localhost:3000", "screenshot", "viewport 375 812", "screenshot"]}

// Two auth states
ctx:create admin → login as admin
ctx:create user  → login as user
ctx:switch admin → go /admin-panel  (should 200)
ctx:switch user  → go /admin-panel  (should 403)
```

## Notes

- Smart waiting: `go`, `reload`, `back`, `forward` wait for `networkidle`. `click` and `key` wait up to 3s for networkidle, then continue regardless.
- State file: `~/.claude/skills/browse/.state.json` (mode 0o600)
- Screenshots: `~/.claude/skills/browse/.screenshots/`
- Daemon auto-shuts after 30min idle; restart anytime
- Crash → check `.daemon.log`, restart daemon
