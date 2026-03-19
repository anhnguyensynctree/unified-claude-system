#!/bin/bash
# Fires on PreCompact — builds a priority-tiered XML snapshot injected before compaction
# stdout → injected into compaction context
# stderr → shown as hook feedback

SESSIONS_DIR="$HOME/.claude/sessions"
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M)
SESSION_FILE="$SESSIONS_DIR/$DATE-session.tmp"
MAX_BYTES=2048
CWD=$(pwd)

mkdir -p "$SESSIONS_DIR"

# Append compaction marker to session file
{
  echo ""
  echo "=== COMPACTION: $TIME ==="
  echo "Context compacted at this point."
  echo "State above this line is pre-compaction."
} >> "$SESSION_FILE"

# ── Collect data per priority tier ─────────────────────────────────────────

ACTIVE_FILES=$(git -C "$CWD" diff --name-only HEAD 2>/dev/null | head -10)
STAGED_FILES=$(git -C "$CWD" diff --name-only --cached 2>/dev/null | head -10)
BRANCH=$(git -C "$CWD" branch --show-current 2>/dev/null || echo "unknown")
LAST_COMMIT=$(git -C "$CWD" log --oneline -1 2>/dev/null || echo "none")

# CRITICAL: OMS in-progress tasks
OMS_LOGS="$CWD/logs/tasks"
OMS_IN_PROGRESS=""
if [ -d "$OMS_LOGS" ]; then
  while IFS= read -r f; do
    TASK_ID=$(basename "$f" .md)
    LAST_ROUND=$(grep "^## Round" "$f" 2>/dev/null | tail -1)
    OMS_IN_PROGRESS="${OMS_IN_PROGRESS}    <task id=\"${TASK_ID}\" checkpoint=\"${LAST_ROUND}\"/>\n"
  done < <(grep -rL "## Synthesis" "$OMS_LOGS"/*.md 2>/dev/null)
fi

# IMPORTANT: session decisions logged this session
SESSION_DECISIONS=""
if [ -f "$SESSION_FILE" ]; then
  SESSION_DECISIONS=$(grep -iE "(decision|decided|using|chose|implemented|fixed|created)" "$SESSION_FILE" 2>/dev/null | tail -10)
fi

# IMPORTANT: recent memory index
MEMORY_FILE="$HOME/.claude/projects/$(echo "$CWD" | sed 's|/|-|g')/memory/MEMORY.md"
RECENT_MEMORY=""
if [ -f "$MEMORY_FILE" ]; then
  RECENT_MEMORY=$(tail -15 "$MEMORY_FILE" 2>/dev/null)
fi

# ── Build XML snapshot ──────────────────────────────────────────────────────

CRITICAL_BLOCK=""
[ -n "$ACTIVE_FILES" ] && CRITICAL_BLOCK+="    <active-files branch=\"${BRANCH}\">\n$(echo "$ACTIVE_FILES" | sed 's/^/      /')\n    </active-files>\n"
[ -n "$STAGED_FILES" ] && CRITICAL_BLOCK+="    <staged-files>\n$(echo "$STAGED_FILES" | sed 's/^/      /')\n    </staged-files>\n"
[ -n "$LAST_COMMIT" ] && CRITICAL_BLOCK+="    <last-commit>${LAST_COMMIT}</last-commit>\n"
[ -n "$OMS_IN_PROGRESS" ] && CRITICAL_BLOCK+="    <oms-in-progress>\n${OMS_IN_PROGRESS}    </oms-in-progress>\n"

IMPORTANT_BLOCK=""
[ -n "$SESSION_DECISIONS" ] && IMPORTANT_BLOCK+="    <decisions>\n$(echo "$SESSION_DECISIONS" | sed 's/^/      /')\n    </decisions>\n"
[ -n "$RECENT_MEMORY" ] && IMPORTANT_BLOCK+="    <recent-memory>\n$(echo "$RECENT_MEMORY" | sed 's/^/      /')\n    </recent-memory>\n"

# ── Assemble full snapshot ──────────────────────────────────────────────────

SNAPSHOT=""
[ -n "$CRITICAL_BLOCK" ] && SNAPSHOT+="<session-snapshot priority=\"critical\" ts=\"${DATE} ${TIME}\">\n${CRITICAL_BLOCK}</session-snapshot>\n"
[ -n "$IMPORTANT_BLOCK" ] && SNAPSHOT+="<session-snapshot priority=\"important\">\n${IMPORTANT_BLOCK}</session-snapshot>\n"

FULL=$(printf "%b" "$SNAPSHOT")
FULL_BYTES=${#FULL}

# ── Enforce 2KB budget — drop important tier first ─────────────────────────

if [ "$FULL_BYTES" -gt "$MAX_BYTES" ] && [ -n "$IMPORTANT_BLOCK" ]; then
  CRITICAL_ONLY=$(printf "%b" "<session-snapshot priority=\"critical\" ts=\"${DATE} ${TIME}\">\n${CRITICAL_BLOCK}</session-snapshot>\n")
  FULL="$CRITICAL_ONLY"
  FULL_BYTES=${#FULL}
  echo "[PreCompact] Over budget — dropped important tier, kept critical (${FULL_BYTES}B)" >&2
fi

# ── Output to stdout (Claude Code injects this into compaction context) ─────

if [ -n "$FULL" ]; then
  printf "%b" "$FULL"
  echo "[PreCompact] Snapshot injected: ${FULL_BYTES}B at ${DATE} ${TIME}" >&2
else
  echo "[PreCompact] No snapshot data to inject" >&2
fi
