#!/bin/bash
# health-check.sh — validates structural integrity of the unified Claude system
# Runs on every SessionStart. Prints nothing if healthy. Warns loudly on failure.
# Never blocks context output — all output goes to stderr.

CLAUDE_DIR="$HOME/.claude"
HOOKS_DIR="$CLAUDE_DIR/hooks/memory-persistence"
SETTINGS="$CLAUDE_DIR/settings.json"
PASS=0
FAIL=0

warn() { echo "[HealthCheck] WARN: $*" >&2; ((FAIL++)); }
ok()   { ((PASS++)); }

# ── 1. settings.json — exists and is valid JSON ──────────────────────────────
if [ ! -f "$SETTINGS" ]; then
  warn "settings.json not found at $SETTINGS"
else
  if ! python3 -c "import json; json.load(open('$SETTINGS'))" 2>/dev/null; then
    warn "settings.json is not valid JSON"
  else
    ok

    # ── 2. Hook structure — every hook object must have 'matcher' and 'hooks' ─
    python3 - "$SETTINGS" <<'PYEOF' 2>&1 | while IFS= read -r line; do warn "$line"; done
import json, sys
settings = json.load(open(sys.argv[1]))

for event, entries in settings.get("hooks", {}).items():
    if not isinstance(entries, list):
        print(f"hooks.{event} must be an array")
        continue
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            print(f"hooks.{event}[{i}] must be an object")
            continue
        if "matcher" not in entry:
            print(f"hooks.{event}[{i}] missing 'matcher' field")
        if "hooks" not in entry:
            print(f"hooks.{event}[{i}] missing 'hooks' field")
            continue
        for j, h in enumerate(entry.get("hooks", [])):
            if "type" not in h:
                print(f"hooks.{event}[{i}].hooks[{j}] missing 'type'")
            if h.get("type") == "command" and "command" not in h:
                print(f"hooks.{event}[{i}].hooks[{j}] type=command but no 'command' field")
PYEOF

    # ── 3. Command paths — every hook command must point to an existing file ──
    python3 - "$SETTINGS" <<'PYEOF' 2>&1 | while IFS= read -r line; do warn "$line"; done
import json, sys, os, re, shutil
settings = json.load(open(sys.argv[1]))
home = os.path.expanduser("~")

for event, entries in settings.get("hooks", {}).items():
    for entry in entries if isinstance(entries, list) else []:
        for h in entry.get("hooks", []) if isinstance(entry, dict) else []:
            cmd = h.get("command", "")
            if not cmd:
                continue
            # Extract the first token (the executable), expand ~ and $HOME
            first = cmd.split()[0]
            first = first.replace("$HOME", home).replace("~", home)
            # Skip inline shell expressions
            if first.startswith(("jq", "echo", "osascript", "git", "npx",
                                  "notify-send", "powershell", "python3",
                                  "FILE=", "rm", "grep", "find", "bash")):
                continue
            if first.startswith("/") and not os.path.exists(first):
                print(f"hooks.{event} command path not found: {first}")
            elif first.startswith("/") and not os.access(first, os.X_OK):
                print(f"hooks.{event} command not executable: {first}")
PYEOF
  fi
fi

# ── 4. Shell scripts — syntax and permissions ─────────────────────────────────
for script in "$HOOKS_DIR"/*.sh; do
  [ -f "$script" ] || continue
  name=$(basename "$script")
  if ! bash -n "$script" 2>/dev/null; then
    warn "$name has bash syntax errors"
  else
    ok
  fi
  if [ ! -x "$script" ]; then
    warn "$name is not executable (run: chmod +x $script)"
  else
    ok
  fi
done

# ── 5. mem0.py — Python syntax valid ─────────────────────────────────────────
MEM0="$HOOKS_DIR/mem0.py"
if [ ! -f "$MEM0" ]; then
  warn "mem0.py not found at $MEM0"
elif ! python3 -c "import ast; ast.parse(open('$MEM0').read())" 2>/dev/null; then
  warn "mem0.py has Python syntax errors"
else
  ok
fi

# ── 6. API key — exists, non-empty, and loadable by mem0.py ─────────────────
KEY_FILE="$HOME/.config/anthropic/key"
if [ ! -f "$KEY_FILE" ]; then
  warn "Anthropic API key not found at $KEY_FILE — mem0 extraction will be skipped"
elif [ ! -s "$KEY_FILE" ]; then
  warn "Anthropic API key file is empty at $KEY_FILE"
else
  # Verify mem0.py can load the key (catches env-only loading bugs)
  KEY_LOADED=$(python3 -c "
import os, sys
sys.path.insert(0, '$(dirname "$MEM0")')
import mem0
print('ok' if mem0.ANTHROPIC_API_KEY else 'missing')
" 2>/dev/null)
  if [ "$KEY_LOADED" != "ok" ]; then
    warn "mem0.py could not load ANTHROPIC_API_KEY — check _load_api_key() in mem0.py"
  else
    ok
  fi
fi

# ── 7. facts.json files — valid JSON arrays ───────────────────────────────────
find "$CLAUDE_DIR/projects" -name "facts.json" 2>/dev/null | while read -r f; do
  if ! python3 -c "
import json, sys
d = json.load(open('$f'))
assert isinstance(d, list), 'not an array'
" 2>/dev/null; then
    warn "Corrupted facts.json: $f"
  fi
done

# ── 8. Claude Code version — check for updates (cached 24h) ──────────────────
VERSION_CACHE="$CLAUDE_DIR/.version-cache"
INSTALLED=$(claude --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)

if [ -n "$INSTALLED" ]; then
  # Read cache: "timestamp|installed|latest"
  CACHE_TS=0
  CACHED_LATEST=""
  if [ -f "$VERSION_CACHE" ]; then
    CACHE_TS=$(cut -d'|' -f1 "$VERSION_CACHE" 2>/dev/null)
    CACHED_LATEST=$(cut -d'|' -f3 "$VERSION_CACHE" 2>/dev/null)
  fi

  NOW=$(date +%s)
  AGE=$(( NOW - CACHE_TS ))

  if [ "$AGE" -gt 86400 ]; then
    # Cache stale — check npm in background, update cache
    (
      LATEST=$(npm view @anthropic-ai/claude-code version 2>/dev/null)
      if [ -n "$LATEST" ]; then
        echo "$(date +%s)|$INSTALLED|$LATEST" > "$VERSION_CACHE"
      fi
    ) &
    CACHED_LATEST=""  # Don't warn this session — will warn next session
  fi

  if [ -n "$CACHED_LATEST" ] && [ "$INSTALLED" != "$CACHED_LATEST" ]; then
    warn "Claude Code update available: $INSTALLED → $CACHED_LATEST (run: brew upgrade claude-code)"
  fi
fi

# ── Summary ───────────────────────────────────────────────────────────────────
if [ "$FAIL" -gt 0 ]; then
  echo "[HealthCheck] $FAIL issue(s) found — run ~/.claude/hooks/memory-persistence/health-check.sh to see details" >&2
fi
