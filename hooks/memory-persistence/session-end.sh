#!/bin/bash
# Fires on Stop — persists session state for next session

SESSIONS_DIR="$HOME/.claude/sessions"
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M)
SESSION_FILE="$SESSIONS_DIR/$DATE-session.tmp"

mkdir -p "$SESSIONS_DIR"

if [ ! -f "$SESSION_FILE" ]; then
  cat > "$SESSION_FILE" << EOF
# Session: $DATE
Project: $(basename "${CLAUDE_PROJECT_DIR:-unknown}")
Branch: $(git branch --show-current 2>/dev/null || echo "unknown")
Started: unknown
Ended: $TIME

## What was worked on

## Approaches that WORKED (with evidence)

## Approaches that did NOT work

## What hasn't been attempted yet

## What's left to do

## Key decisions and why
EOF
  echo "[SessionEnd] Session file created: $SESSION_FILE" >&2
else
  echo "" >> "$SESSION_FILE"
  echo "Session ended: $TIME" >> "$SESSION_FILE"
  echo "[SessionEnd] Session updated: $SESSION_FILE" >&2
fi

# --- Memory threshold check ---
GLOBAL_MEMORY="$HOME/.claude/projects/-Users-Lewis/memory/MEMORY.md"
if [ -f "$GLOBAL_MEMORY" ]; then
  line_count=$(wc -l < "$GLOBAL_MEMORY")
  if [ "$line_count" -gt 150 ]; then
    echo "[Memory] MEMORY.md is ${line_count} lines — run /consolidate-memory to compress" >&2
  fi
fi
