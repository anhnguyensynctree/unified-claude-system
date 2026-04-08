#!/usr/bin/env bash
# PreToolUse hook: enforce conventional commit format
# Blocks git commit if message doesn't match: type(scope): subject

HOOK_INPUT=$(cat)
CMD=$(echo "$HOOK_INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)

# Only check git commit commands with -m flag
echo "$CMD" | grep -q 'git commit' || exit 0
echo "$CMD" | grep -q '\-m' || exit 0

# Extract commit message — handle both -m "msg" and -m "$(cat <<'EOF'...)"
# For heredoc messages, extract the first non-empty line after the heredoc marker
MSG=$(echo "$CMD" | grep -oE '\-m "([^"]*)"' | head -1 | sed 's/-m "//;s/"$//')
if [ -z "$MSG" ]; then
    # Try heredoc format
    MSG=$(echo "$CMD" | grep -oE "^[a-z]+(\([^)]+\))?: " | head -1)
    # If we can't parse the message, allow it (don't block on parse failures)
    [ -z "$MSG" ] && exit 0
fi

# Check conventional commit format: type(scope): subject
if ! echo "$MSG" | grep -qE '^(feat|fix|chore|docs|refactor|test|perf|style|ci|build|revert)(\([a-zA-Z0-9_/-]+\))?: .+'; then
    echo '[BLOCKED] Commit message must use conventional format: type(scope): subject' >&2
    echo '  Types: feat|fix|chore|docs|refactor|test|perf|style|ci|build|revert' >&2
    echo "  Got: $MSG" >&2
    exit 2
fi

exit 0
