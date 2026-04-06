#!/usr/bin/env bash
# PostToolUse hook: BLOCK edits that introduce console.log
# Matcher: Edit|Write on .ts/.tsx/.js/.jsx/.py files
FILE=$(jq -r '.tool_input.file_path')
echo "$FILE" | grep -qE '\.(ts|tsx|js|jsx)$' || exit 0
[ -f "$FILE" ] || exit 0
MATCHES=$(grep -n 'console\.log' "$FILE" 2>/dev/null)
if [ -n "$MATCHES" ]; then
    echo "[BLOCKED] console.log found — remove before continuing:" >&2
    echo "$MATCHES" | head -5 >&2
    exit 2
fi
exit 0
