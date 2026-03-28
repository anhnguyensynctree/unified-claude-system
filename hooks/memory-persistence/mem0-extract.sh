#!/bin/bash
# SessionEnd hook — extracts memories from transcript via mem0.py

HOOK_INPUT=$(cat)
TRANSCRIPT_PATH=$(echo "$HOOK_INPUT" | jq -r '.transcript_path // empty' 2>/dev/null)
PROJECT_CWD=$(echo "$HOOK_INPUT" | jq -r '.cwd // empty' 2>/dev/null)
PROJECT=$(basename "${PROJECT_CWD:-$(pwd)}")

# mem0.py uses claude -p subprocess (subscription billing) — no API key needed

# Skip for all claude -p subprocesses — shim injects CLAUDE_SUBPROCESS=1 for any -p/--print call
if [ "${CLAUDE_SUBPROCESS:-0}" = "1" ]; then
  exit 0
fi

if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
    echo "[mem0] No transcript available — skipping extraction" >&2
    exit 0
fi


# Steps run at true session exit. Each step has a per-step timeout.
# session-end: single Haiku call → summary + facts + patterns (replaces summary+extract+learn)
# handoff:     last 15 messages verbatim, no API — always succeeds
# check-memory: consolidate topic files if over threshold
DATE=$(date +%Y-%m-%d)
RETRY_FILE="$HOME/.claude/logs/mem0-retry.json"
FAILED_STEPS=""

run_step() {
  local step="$1"; local limit="$2"; shift 2
  echo "[mem0] $step..." >&2
  timeout "$limit" python3 "$HOME/.claude/hooks/memory-persistence/mem0.py" "$@" 2>&1 >&2
  local code=$?
  if [ $code -ne 0 ]; then
    FAILED_STEPS="${FAILED_STEPS}${FAILED_STEPS:+,}\"$step\""
    [ $code -eq 124 ] && echo "[mem0] $step timed out (${limit}s)" >&2 || echo "[mem0] $step failed (exit $code)" >&2
  fi
}

# session-end makes up to 2 Haiku calls (combined extract + dedup) — needs more headroom
# handoff/check-memory: no LLM calls, 25s is generous
SESSION_TIMEOUT="${MEM0_TIMEOUT:-55}"
run_step "session-end"  "$SESSION_TIMEOUT" session-end "$TRANSCRIPT_PATH" "$DATE" "$PROJECT"
run_step "handoff"      25                 handoff     "$TRANSCRIPT_PATH" "$DATE" "$PROJECT"
run_step "check-memory" 25                 check-memory

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
