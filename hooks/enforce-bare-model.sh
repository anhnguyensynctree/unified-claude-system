#!/usr/bin/env bash
# PreToolUse hook: enforce --bare and --model on all claude -p / --print calls
# Even with shim injection, enforce explicitly for defense-in-depth.

HOOK_INPUT=$(cat)
CMD=$(echo "$HOOK_INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)

# Only check commands that invoke claude with -p or --print
echo "$CMD" | grep -qE 'claude\b' || exit 0
echo "$CMD" | grep -qE '\-p\b|--print\b' || exit 0

# Check for --bare
if ! echo "$CMD" | grep -q '\-\-bare'; then
    echo '[BLOCKED] claude -p/--print must include --bare (skip hooks/LSP/attribution). See rules/security.md § daily-cosmos incident.' >&2
    exit 2
fi

# Check for --model
if ! echo "$CMD" | grep -q '\-\-model'; then
    echo '[BLOCKED] claude -p/--print must include --model <model-id>. See rules/security.md § cadence incident.' >&2
    exit 2
fi

exit 0
