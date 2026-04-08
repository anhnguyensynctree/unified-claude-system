#!/usr/bin/env bash
# PreToolUse hook: block Co-Authored-By trailers in commits
# Per git-workflow.md: NEVER add Co-Authored-By trailers

HOOK_INPUT=$(cat)
CMD=$(echo "$HOOK_INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)

echo "$CMD" | grep -q 'git commit' || exit 0

if echo "$CMD" | grep -qi 'Co-Authored-By'; then
    echo '[BLOCKED] Co-Authored-By trailers are not allowed. See rules/git-workflow.md.' >&2
    exit 2
fi

exit 0
