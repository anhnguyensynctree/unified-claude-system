#!/usr/bin/env bash
# PostToolUse hook: BLOCK sparse/placeholder .md files
# Matcher: Edit|Write on .md files
FILE=$(jq -r '.tool_input.file_path')
echo "$FILE" | grep -qE '\.md$' || exit 0
[ -f "$FILE" ] || exit 0

FAIL=0
LINES=$(grep -c '[^[:space:]]' "$FILE" 2>/dev/null || echo 0)
HAS_HEADING=$(grep -c '^#' "$FILE" 2>/dev/null || echo 0)
HAS_PLACEHOLDER=$(grep -cE '^\[empty|^TODO[^:]|^\.\.\.$' "$FILE" 2>/dev/null || echo 0)

if [ "$HAS_HEADING" -eq 0 ]; then
    echo "[BLOCKED] .md missing # heading" >&2
    FAIL=1
fi
if [ "$LINES" -lt 5 ]; then
    echo "[BLOCKED] .md too sparse ($LINES lines) — minimum 5 substantive lines" >&2
    FAIL=1
fi
if [ "$HAS_PLACEHOLDER" -gt 0 ]; then
    echo "[BLOCKED] .md has unfilled placeholders" >&2
    FAIL=1
fi
[ "$FAIL" -eq 1 ] && exit 2
exit 0
