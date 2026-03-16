#!/bin/bash
# SessionEnd hook — extracts memories from transcript via mem0.py

HOOK_INPUT=$(cat)
TRANSCRIPT_PATH=$(echo "$HOOK_INPUT" | jq -r '.transcript_path // empty' 2>/dev/null)
PROJECT_CWD=$(echo "$HOOK_INPUT" | jq -r '.cwd // empty' 2>/dev/null)
PROJECT=$(basename "${PROJECT_CWD:-$(pwd)}")

# Load API key from secure file — not from shell environment (so Claude Code uses subscription billing)
if [ -f "$HOME/.config/anthropic/key" ]; then
  export ANTHROPIC_API_KEY=$(cat "$HOME/.config/anthropic/key")
fi

if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
    echo "[mem0] No transcript available — skipping extraction" >&2
    exit 0
fi

# Extract facts into memory (async — runs after exit)
python3 "$HOME/.claude/hooks/memory-persistence/mem0.py" extract "$TRANSCRIPT_PATH" 2>&1 >&2
python3 "$HOME/.claude/hooks/memory-persistence/mem0.py" learn "$TRANSCRIPT_PATH" 2>&1 >&2
