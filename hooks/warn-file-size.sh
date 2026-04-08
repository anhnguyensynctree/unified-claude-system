#!/usr/bin/env bash
# PostToolUse hook: warn when edited file exceeds 300 lines
# Per coding-style.md: max 300 lines per file

HOOK_INPUT=$(cat)
FILE=$(echo "$HOOK_INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)

[ -z "$FILE" ] && exit 0
[ -f "$FILE" ] || exit 0

# Skip non-code files and system files
echo "$FILE" | grep -qE '\.(ts|tsx|js|jsx|py|go|rs|java|rb)$' || exit 0
echo "$FILE" | grep -qE '(\.claude/|node_modules/|\.next/|dist/)' && exit 0

LINES=$(wc -l < "$FILE" 2>/dev/null | tr -d ' ')
if [ "$LINES" -gt 300 ]; then
    echo "[WARN] File exceeds 300-line limit: $FILE ($LINES lines). Consider splitting." >&2
fi

exit 0
