#!/usr/bin/env bash
# PreToolUse hook: BLOCK edits to 3+ unique files without a plan
# Enforces: "Use EnterPlanMode for any task touching 3+ files"
# Tracks unique file edits per session via observation log.

HOOK_INPUT=$(cat)
FILE=$(echo "$HOOK_INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
SESSION_ID=$(echo "$HOOK_INPUT" | jq -r '.session_id // empty' 2>/dev/null)

[ -z "$FILE" ] && exit 0
[ -z "$SESSION_ID" ] && exit 0

# --- Exceptions: don't count these toward the 3-file limit ---

# System/config files
echo "$FILE" | grep -qE '\.claude/' && exit 0

# Test files (writing tests doesn't need a plan)
echo "$FILE" | grep -qE '\.(test|spec)\.(ts|tsx|js|jsx)$' && exit 0
echo "$FILE" | grep -qE '(test_|_test)\.' && exit 0
echo "$FILE" | grep -qE '(__tests__|e2e|tests)/' && exit 0

# Config/lockfiles
echo "$FILE" | grep -qE '\.(json|yaml|yml|toml|lock|env|gitignore)$' && exit 0

# OMS task execution (has its own planning)
[ "${OMS_BOT:-0}" = "1" ] && exit 0

# --- Check if a plan exists for this session ---
PLANS_DIR="$HOME/.claude/plans"
TODAY=$(date +%Y-%m-%d)

# If any plan file was created/modified today, allow edits
if [ -d "$PLANS_DIR" ]; then
    RECENT_PLAN=$(find "$PLANS_DIR" -name "*.md" -newer /tmp/.claude-session-start 2>/dev/null | head -1)
    # Fallback: check for today's plans by modification date
    if [ -z "$RECENT_PLAN" ]; then
        RECENT_PLAN=$(find "$PLANS_DIR" -name "*.md" -newermt "$TODAY" 2>/dev/null | head -1)
    fi
    [ -n "$RECENT_PLAN" ] && exit 0
fi

# --- Count unique files edited this session ---
OBS_FILE="$HOME/.claude/logs/obs-${SESSION_ID}.log"
[ -f "$OBS_FILE" ] || exit 0

# Count unique file paths from Edit/Write/MultiEdit entries (excluding exceptions)
UNIQUE_FILES=$(grep -E '(Edit|Write|MultiEdit):' "$OBS_FILE" 2>/dev/null \
    | grep -oE '/[^ ]+' \
    | grep -vE '(\.claude/|\.test\.|\.spec\.|__tests__|e2e/|tests/|\.(json|yaml|yml|toml|lock|env))' \
    | sort -u \
    | wc -l \
    | tr -d ' ')

# Include the current file in the count if it's not already tracked
CURRENT_IN_LOG=$(grep -c "$FILE" "$OBS_FILE" 2>/dev/null)
if [ "$CURRENT_IN_LOG" -eq 0 ]; then
    UNIQUE_FILES=$((UNIQUE_FILES + 1))
fi

if [ "$UNIQUE_FILES" -ge 3 ]; then
    echo "[BLOCKED] ${UNIQUE_FILES} unique files modified without a plan." >&2
    echo "  Use EnterPlanMode first for multi-file changes." >&2
    echo "  Or create a plan file in ~/.claude/plans/ to proceed." >&2
    exit 2
fi

exit 0
