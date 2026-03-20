#!/bin/bash
# Fires on Stop — persists session state for next session

SESSIONS_DIR="$HOME/.claude/sessions"
HANDOFFS_DIR="$HOME/.claude/handoffs"
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M)

# Stop hook pipes JSON with cwd, transcript_path, session_id
HOOK_INPUT=$(cat)
PROJECT_CWD=$(echo "$HOOK_INPUT" | jq -r '.cwd // empty' 2>/dev/null)
TRANSCRIPT_PATH=$(echo "$HOOK_INPUT" | jq -r '.transcript_path // empty' 2>/dev/null)
PROJECT=$(basename "${PROJECT_CWD:-$(pwd)}")
SESSION_FILE="$HANDOFFS_DIR/$DATE-$PROJECT-session.tmp"

mkdir -p "$HANDOFFS_DIR"

if [ ! -f "$SESSION_FILE" ]; then
  cat > "$SESSION_FILE" << EOF
# Session: $DATE
Project: $PROJECT
Dir: ${PROJECT_CWD:-$(pwd)}
Branch: $(git -C "${PROJECT_CWD:-$(pwd)}" branch --show-current 2>/dev/null || echo "unknown")
Ended: $TIME

<!-- Handoff auto-populated by mem0 at SessionEnd -->
EOF
fi


# --- Codemap staleness check ---
CWD="${PROJECT_CWD:-$(pwd)}"
CODEMAP="$CWD/.claude/codemap.md"
if [ -f "$CODEMAP" ] && git -C "$CWD" rev-parse --git-dir > /dev/null 2>&1; then
  NEW_OR_DELETED=$(git -C "$CWD" diff --name-status HEAD~1 HEAD 2>/dev/null | grep -E "^[AD]" | wc -l | tr -d ' ')
  if [ "${NEW_OR_DELETED:-0}" -gt 0 ]; then
    echo "[Codemap] $NEW_OR_DELETED file(s) added/deleted this session — run /update-codemaps to sync" >&2
  fi
fi

# --- Memory threshold check ---
HOME_ENCODED=$(echo "$HOME" | sed 's|/|-|g')
GLOBAL_MEMORY="$HOME/.claude/projects/${HOME_ENCODED}/memory/MEMORY.md"
if [ -f "$GLOBAL_MEMORY" ]; then
  line_count=$(wc -l < "$GLOBAL_MEMORY")
  if [ "$line_count" -gt 150 ]; then
    echo "[Memory] MEMORY.md is ${line_count} lines — run /consolidate-memory to compress" >&2
  fi
fi
