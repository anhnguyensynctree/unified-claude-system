#!/bin/bash
# Stop hook — checks for codemap staleness

HOOK_INPUT=$(cat)
PROJECT_CWD=$(echo "$HOOK_INPUT" | jq -r '.cwd // empty' 2>/dev/null)
CWD="${PROJECT_CWD:-$(pwd)}"

CODEMAP="$CWD/.claude/codemap.md"
if [ -f "$CODEMAP" ] && git -C "$CWD" rev-parse --git-dir > /dev/null 2>&1; then
  NEW_OR_DELETED=$(git -C "$CWD" diff --name-status HEAD~1 HEAD 2>/dev/null | grep -E "^[AD]" | wc -l | tr -d ' ')
  if [ "${NEW_OR_DELETED:-0}" -gt 0 ]; then
    echo "[Codemap] $NEW_OR_DELETED file(s) added/deleted — run /update-codemaps to sync" >&2
  fi
fi
