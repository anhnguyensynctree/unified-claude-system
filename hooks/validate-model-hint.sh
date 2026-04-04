#!/bin/bash
# Validate Model-hint accuracy in cleared-queue.md
# Called as PostToolUse hook when cleared-queue.md is edited

FILE=$(jq -r '.tool_input.file_path // ""' 2>/dev/null)

# Only run if cleared-queue.md was edited
echo "$FILE" | grep -q 'cleared-queue\.md' || exit 0

# Call the Python validation script
[ -f "$FILE" ] && python3 ~/.claude/bin/validate-model-hint.py "$FILE" || true

exit 0
