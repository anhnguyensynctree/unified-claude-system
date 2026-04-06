#!/usr/bin/env bash
# PreToolUse hook: BLOCK grep -r (use mgrep or Grep tool instead)
# Matcher: Bash
CMD=$(jq -r '.tool_input.command')
echo "$CMD" | grep -qE 'grep\s+(-[a-zA-Z]*r|--recursive|-r)' || exit 0
echo "[BLOCKED] grep -r detected. Use the Grep tool or mgrep skill instead." >&2
exit 2
