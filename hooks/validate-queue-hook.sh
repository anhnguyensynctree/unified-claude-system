#!/usr/bin/env bash
# PostToolUse hook: auto-fix Model-hint + validate schema on any cleared-queue.md write
set -euo pipefail

FILE=$(jq -r '.tool_input.file_path // ""' 2>/dev/null || true)
echo "$FILE" | grep -q 'cleared-queue\.md' || exit 0

# Auto-fix Model-hint first
python3 ~/.claude/bin/validate-queue.py "$FILE" --fix 2>/dev/null

# Validate — exit 2 blocks the write on violations
if ! python3 ~/.claude/bin/validate-queue.py "$FILE"; then
    echo "[queue-validator] Write blocked — fix violations before saving cleared-queue.md" >&2
    exit 2
fi

exit 0
