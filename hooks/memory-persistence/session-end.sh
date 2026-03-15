#!/bin/bash
# Fires on Stop — persists session state for next session

SESSIONS_DIR="$HOME/.claude/sessions"
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M)
PROJECT=$(basename "${CLAUDE_PROJECT_DIR:-$(pwd)}")
SESSION_FILE="$SESSIONS_DIR/$DATE-$PROJECT-session.tmp"

mkdir -p "$SESSIONS_DIR"

if [ ! -f "$SESSION_FILE" ]; then
  cat > "$SESSION_FILE" << EOF
# Session: $DATE
Project: $PROJECT
Dir: ${CLAUDE_PROJECT_DIR:-$(pwd)}
Branch: $(git -C "${CLAUDE_PROJECT_DIR:-$(pwd)}" branch --show-current 2>/dev/null || echo "unknown")
Ended: $TIME

<!-- Handoff auto-populated by mem0 at SessionEnd -->
EOF
  echo "[SessionEnd] Session file created: $SESSION_FILE" >&2
else
  echo "" >> "$SESSION_FILE"
  echo "Session ended: $TIME" >> "$SESSION_FILE"
  echo "[SessionEnd] Session updated: $SESSION_FILE" >&2
fi

# --- Codemap staleness check ---
CWD="${CLAUDE_PROJECT_DIR:-$(pwd)}"
CODEMAP="$CWD/.claude/codemap.md"
if [ -f "$CODEMAP" ] && git -C "$CWD" rev-parse --git-dir > /dev/null 2>&1; then
  # Check if any files were created or deleted since codemap was last written
  CODEMAP_AGE=$(stat -f %m "$CODEMAP" 2>/dev/null || stat -c %Y "$CODEMAP" 2>/dev/null)
  NEW_OR_DELETED=$(git -C "$CWD" diff --name-status HEAD~1 HEAD 2>/dev/null | grep -E "^[AD]" | wc -l | tr -d ' ')
  if [ "${NEW_OR_DELETED:-0}" -gt 0 ]; then
    echo "[Codemap] $NEW_OR_DELETED file(s) added/deleted this session — run /update-codemaps to sync" >&2
  fi
fi

# --- Memory threshold check ---
GLOBAL_MEMORY="$HOME/.claude/projects/-Users-Lewis/memory/MEMORY.md"
if [ -f "$GLOBAL_MEMORY" ]; then
  line_count=$(wc -l < "$GLOBAL_MEMORY")
  if [ "$line_count" -gt 150 ]; then
    echo "[Memory] MEMORY.md is ${line_count} lines — run /consolidate-memory to compress" >&2
  fi
fi
