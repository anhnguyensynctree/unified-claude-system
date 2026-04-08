#!/usr/bin/env bash
# PreToolUse hook: enforce reading llms.txt before invoking a skill
# Checks session observation log for recent Read of the skill's llms.txt

HOOK_INPUT=$(cat)
SKILL=$(echo "$HOOK_INPUT" | jq -r '.tool_input.skill // empty' 2>/dev/null)

[ -z "$SKILL" ] && exit 0

# Extract base skill name (handle "namespace:skill" format)
BASE_SKILL=$(echo "$SKILL" | sed 's/.*://')

# Check if llms.txt exists for this skill
LLMS_FILE="$HOME/.claude/skills/$BASE_SKILL/llms.txt"
if [ ! -f "$LLMS_FILE" ]; then
    # No llms.txt to read — allow (skill may not have one)
    exit 0
fi

# Check observation log for recent Read of this llms.txt
SESSION_ID=$(echo "$HOOK_INPUT" | jq -r '.session_id // empty' 2>/dev/null)
OBS_FILE="$HOME/.claude/logs/obs-${SESSION_ID}.log"

# Fallback: use most recent obs log if session ID not available
if [ ! -f "$OBS_FILE" ]; then
    OBS_FILE=$(ls -t "$HOME/.claude/logs"/obs-*.log 2>/dev/null | head -1)
fi

if [ -n "$OBS_FILE" ] && [ -f "$OBS_FILE" ]; then
    # Check if llms.txt was read in this session
    if grep -q "Read:.*$BASE_SKILL/llms.txt" "$OBS_FILE" 2>/dev/null; then
        exit 0  # Already read — allow
    fi
    # Also check broader pattern — any read of this skill's files
    if grep -q "Read:.*skills/$BASE_SKILL/" "$OBS_FILE" 2>/dev/null; then
        exit 0  # Read something in the skill dir — close enough
    fi
fi

echo "[BLOCKED] Read llms.txt before using skill: $LLMS_FILE" >&2
echo "  Run: Read tool on $LLMS_FILE first, then invoke the skill." >&2
exit 2
