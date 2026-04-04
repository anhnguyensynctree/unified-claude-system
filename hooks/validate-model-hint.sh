#!/bin/bash
# Validate Model-hint accuracy in cleared-queue.md — BLOCKING hook
# Called as PostToolUse hook when cleared-queue.md is edited
# Exits 2 to block write if Model-hint violations found

FILE=$(jq -r '.tool_input.file_path // ""' 2>/dev/null)

# Only run if cleared-queue.md was edited
echo "$FILE" | grep -q 'cleared-queue\.md' || exit 0

# Call the Python validation script
# Returns 0 if all Model-hints correct, 1 if violations found
if ! python3 ~/.claude/bin/validate-model-hint.py "$FILE"; then
    # Model-hint violations found — block the write
    exit 2
fi

exit 0
