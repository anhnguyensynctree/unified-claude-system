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

echo "[PreCompact] State saved before compaction: $SESSION_FILE" >&2
