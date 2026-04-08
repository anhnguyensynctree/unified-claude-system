#!/bin/bash
# PostToolUse — appends lightweight tool observations to a session log.
# Gives mem0 extract/handoff a dense action timeline beyond sampled transcript.

[ "${CLAUDE_SUBPROCESS:-0}" = "1" ] && exit 0

HOOK_INPUT=$(cat)
TOOL=$(echo "$HOOK_INPUT" | jq -r '.tool_name // empty' 2>/dev/null)
SESSION_ID=$(echo "$HOOK_INPUT" | jq -r '.session_id // empty' 2>/dev/null)

[ -z "$SESSION_ID" ] && exit 0
[ -z "$TOOL" ] && exit 0

OBS_FILE="$HOME/.claude/logs/obs-${SESSION_ID}.log"
mkdir -p "$HOME/.claude/logs"

# Cap file at ~50KB to avoid unbounded growth in long sessions
[ -f "$OBS_FILE" ] && [ "$(wc -c < "$OBS_FILE" 2>/dev/null)" -gt 51200 ] && exit 0

TIME=$(date +%H:%M)

case "$TOOL" in
  Edit|Write|MultiEdit)
    FILE=$(echo "$HOOK_INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
    [ -z "$FILE" ] && exit 0
    echo "[$TIME] $TOOL: $FILE" >> "$OBS_FILE"
    ;;
  Read)
    FILE=$(echo "$HOOK_INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
    [ -z "$FILE" ] && exit 0
    echo "[$TIME] Read: $FILE" >> "$OBS_FILE"
    ;;
  Bash)
    CMD=$(echo "$HOOK_INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null | cut -c1-100)
    [ -z "$CMD" ] && exit 0
    echo "[$TIME] Bash: $CMD" >> "$OBS_FILE"
    ;;
  *)
    exit 0
    ;;
esac

exit 0
