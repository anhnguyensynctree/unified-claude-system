#!/usr/bin/env bash
# PostToolUse hook: auto-sync REQUIRED_FIELDS in validate-queue.py when task-schema.md is edited
set -euo pipefail

FILE=$(jq -r '.tool_input.file_path // ""' 2>/dev/null || true)
echo "$FILE" | grep -q 'task-schema\.md' || exit 0

python3 ~/.claude/bin/sync-queue-schema.py 2>&1 | grep -v '^$' >&2 || true

exit 0
