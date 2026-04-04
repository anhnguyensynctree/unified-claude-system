#!/bin/bash
# PostToolUse hook: auto-sync REQUIRED_FIELDS in validate-queue.py when task-schema.md is edited
# BLOCKING: Write fails if schema changes detected (developer must update both files together)
set -euo pipefail

FILE=$(jq -r '.tool_input.file_path // ""' 2>/dev/null || true)
echo "$FILE" | grep -q 'task-schema\.md' || exit 0

# Run sync script and capture output
OUTPUT=$(python3 ~/.claude/bin/sync-queue-schema.py 2>&1)
SYNC_EXIT=$?

# Always show output
echo "$OUTPUT" | grep -v '^$' >&2 || true

# Block if sync failed (means schema.md changed, needs developer attention)
if [ $SYNC_EXIT -ne 0 ]; then
    echo "[schema-sync] ⚠️  Schema validation failed — fix and try again" >&2
    exit 2
fi

# Success: sync already in sync, or changes were applied
exit 0
