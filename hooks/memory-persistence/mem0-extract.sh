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

# Extract facts and write handoff — runs once at true session exit
# Each step has a 12s hard limit; hook exits immediately when all complete
DATE=$(date +%Y-%m-%d)
RETRY_FILE="$HOME/.claude/logs/mem0-retry.json"
FAILED_STEPS=""

run_step() {
  local step="$1"; shift
  echo "[mem0] $step..." >&2
  timeout 12 python3 "$HOME/.claude/hooks/memory-persistence/mem0.py" "$@" 2>&1 >&2
  local code=$?
  if [ $code -ne 0 ]; then
    FAILED_STEPS="${FAILED_STEPS}${FAILED_STEPS:+,}\"$step\""
    [ $code -eq 124 ] && echo "[mem0] $step timed out" >&2 || echo "[mem0] $step failed (exit $code)" >&2
  fi
}

run_step "handoff" handoff "$TRANSCRIPT_PATH" "$DATE" "$PROJECT"
run_step "extract" extract "$TRANSCRIPT_PATH"
run_step "learn"   learn   "$TRANSCRIPT_PATH"
run_step "check-memory" check-memory

if [ -n "$FAILED_STEPS" ]; then
  python3 -c "
import json, os
os.makedirs(os.path.expanduser('~/.claude/logs'), exist_ok=True)
with open('$RETRY_FILE', 'w') as f:
    json.dump({'transcript_path': '$TRANSCRIPT_PATH', 'project': '$PROJECT', 'date': '$DATE', 'failed_steps': [$FAILED_STEPS]}, f)
" 2>/dev/null
  echo "[mem0] Failed steps saved to retry on next session start" >&2
else
  rm -f "$RETRY_FILE" 2>/dev/null
fi

echo "[mem0] Done." >&2

# Clean obs log files older than 7 days
find "$HOME/.claude/logs" -name "obs-*.log" -mtime +7 -delete 2>/dev/null || true
