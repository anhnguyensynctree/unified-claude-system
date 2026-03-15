#!/bin/bash
# Fires on PreCompact — saves state before context compaction happens

SESSIONS_DIR="$HOME/.claude/sessions"
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M)
SESSION_FILE="$SESSIONS_DIR/$DATE-session.tmp"

mkdir -p "$SESSIONS_DIR"

echo "" >> "$SESSION_FILE"
echo "=== COMPACTION: $TIME ===" >> "$SESSION_FILE"
echo "Context compacted at this point." >> "$SESSION_FILE"
echo "State above this line is pre-compaction." >> "$SESSION_FILE"

# --- OMS in-progress task detection ---
CWD=$(pwd)
OMS_LOGS="$CWD/logs/tasks"
if [ -d "$OMS_LOGS" ]; then
  # Find task logs missing a Synthesis section = in-progress
  IN_PROGRESS=$(grep -rL "## Synthesis" "$OMS_LOGS"/*.md 2>/dev/null)
  if [ -n "$IN_PROGRESS" ]; then
    echo "" >> "$SESSION_FILE"
    echo "=== OMS IN-PROGRESS TASKS ===" >> "$SESSION_FILE"
    for f in $IN_PROGRESS; do
      TASK_ID=$(basename "$f" .md)
      LAST_ROUND=$(grep "^## Round" "$f" | tail -1)
      echo "Task: $TASK_ID | Last checkpoint: $LAST_ROUND | Resume: read $f" >> "$SESSION_FILE"
    done
    echo "[PreCompact] OMS in-progress tasks noted in session file" >&2
  fi
fi

echo "[PreCompact] State saved before compaction: $SESSION_FILE" >&2
