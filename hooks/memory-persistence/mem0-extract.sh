#!/bin/bash
# SessionEnd hook — extracts memories from transcript via mem0.py

HOOK_INPUT=$(cat)
TRANSCRIPT_PATH=$(echo "$HOOK_INPUT" | jq -r '.transcript_path // empty' 2>/dev/null)

if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
    echo "[mem0] No transcript available — skipping extraction" >&2
    exit 0
fi

python3 "$HOME/.claude/memory/mem0.py" extract "$TRANSCRIPT_PATH" 2>&1 >&2
