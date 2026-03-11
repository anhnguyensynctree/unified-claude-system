#!/bin/bash
# Fires on Stop hook — logs session end and prompts learning extraction

SESSIONS_DIR="$HOME/.claude/sessions"
LEARNED_DIR="$HOME/.claude/skills/learned"
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M)

mkdir -p "$SESSIONS_DIR" "$LEARNED_DIR"

SESSION_FILE="$SESSIONS_DIR/$DATE-session.tmp"

# session-end.sh (Stop hook) handles file creation — just append timestamp if already exists
if [ -f "$SESSION_FILE" ]; then
  echo "" >> "$SESSION_FILE"
  echo "Session ended: $TIME" >> "$SESSION_FILE"
fi

LEARNED_COUNT=$(find "$LEARNED_DIR" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')

echo "[ContinuousLearning] Session logged: $SESSION_FILE" >&2
echo "[ContinuousLearning] Learned skills in library: $LEARNED_COUNT" >&2
echo "[ContinuousLearning] Run /learn to extract patterns from this session" >&2
