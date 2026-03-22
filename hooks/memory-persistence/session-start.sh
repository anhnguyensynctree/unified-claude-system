#!/bin/bash
# Fires on SessionStart — injects project context and instructs Claude to apply it

SESSIONS_DIR="$HOME/.claude/sessions"
LEARNED_DIR="$HOME/.claude/skills/learned"
CWD=$(pwd)

mkdir -p "$SESSIONS_DIR"

# --- Project CLAUDE.md (project-scoped context) ---
PROJECT_CLAUDE="$CWD/CLAUDE.md"
GLOBAL_CLAUDE="$HOME/.claude/CLAUDE.md"

if [ -f "$PROJECT_CLAUDE" ] && [ "$PROJECT_CLAUDE" != "$GLOBAL_CLAUDE" ]; then
  echo "## Active Project Context"
  echo ""
  echo "You are working in: $CWD"
  echo "The following project CLAUDE.md is active — read and apply it now:"
  echo ""
  cat "$PROJECT_CLAUDE"
  echo ""
  echo "---"
fi

# --- Retrieved Facts (mem0) ---
ENCODED_PATH=$(echo "$CWD" | sed 's|/|-|g')
FACTS_PATH="$HOME/.claude/projects/$ENCODED_PATH/memory/facts.json"
HOME_ENCODED=$(echo "$HOME" | sed 's|/|-|g')
GLOBAL_FACTS="$HOME/.claude/projects/$HOME_ENCODED/memory/facts.json"

FACTS_OUTPUT=$(python3 "$HOME/.claude/hooks/memory-persistence/mem0.py" retrieve "$FACTS_PATH" "$GLOBAL_FACTS" 2>/dev/null)
if [ -n "$FACTS_OUTPUT" ]; then
  echo "## Retrieved Facts"
  echo ""
  echo "$FACTS_OUTPUT"
  echo ""
  echo "---"
fi

# --- Project memory (if exists) ---
MEMORY_FILE="$HOME/.claude/projects/$ENCODED_PATH/memory/MEMORY.md"

if [ -f "$MEMORY_FILE" ]; then
  echo "## Project Memory"
  echo ""
  cat "$MEMORY_FILE"
  echo ""
  echo "---"
fi

# --- Project-scoped annotations ---
ANNOTATIONS_DIR="$HOME/.claude/annotations/$ENCODED_PATH"
if [ -d "$ANNOTATIONS_DIR" ]; then
  ANNOTATIONS=$(cat "$ANNOTATIONS_DIR"/*.md 2>/dev/null)
  if [ -n "$ANNOTATIONS" ]; then
    echo "## Project Annotations"
    echo ""
    echo "$ANNOTATIONS"
    echo ""
    echo "---"
  fi
fi

# --- Always-active entries from topic files (ctx: always) ---
TOPICS_DIR="$HOME/.claude/projects/$ENCODED_PATH/memory/topics"
GLOBAL_TOPICS_DIR="$HOME/.claude/projects/$HOME_ENCODED/memory/topics"

for dir in "$TOPICS_DIR" "$GLOBAL_TOPICS_DIR"; do
  if [ -d "$dir" ]; then
    ALWAYS_ENTRIES=$(awk '
      /^## .*\| ctx: always/ { found=1; print; next }
      /^## / { found=0 }
      found { print }
    ' "$dir"/*.md 2>/dev/null)
    if [ -n "$ALWAYS_ENTRIES" ]; then
      echo "## Always-Active Memory"
      echo ""
      echo "$ALWAYS_ENTRIES"
      echo ""
      echo "---"
      break
    fi
  fi
done

# --- Previous sessions (project-scoped, last 7 days) ---
HANDOFFS_DIR="$HOME/.claude/handoffs"
PROJECT=$(basename "${CLAUDE_PROJECT_DIR:-$CWD}")

# All project sessions from last 7 days, newest first
ALL_SESSIONS=$(find "$HANDOFFS_DIR" -name "*-${PROJECT}-session.tmp" -mtime -7 2>/dev/null | sort -r)
# Fallback: any recent session if no project-specific ones found
[ -z "$ALL_SESSIONS" ] && ALL_SESSIONS=$(find "$HANDOFFS_DIR" -name "*.tmp" -mtime -7 2>/dev/null | sort -r | head -1)
LATEST=$(echo "$ALL_SESSIONS" | head -1)

if [ -n "$LATEST" ]; then
  echo "## Previous Session Notes"
  echo ""

  # Show Session Summary from ALL recent sessions (merged context)
  SESSION_COUNT=$(echo "$ALL_SESSIONS" | wc -l | tr -d ' ')
  if [ "$SESSION_COUNT" -gt 1 ]; then
    echo "### All Recent Sessions (${SESSION_COUNT} sessions)"
    echo ""
    for f in $ALL_SESSIONS; do
      FNAME=$(basename "$f" | sed 's/-session\.tmp//')
      echo "#### $FNAME"
      # Extract only the Session Summary block (not the tail — too verbose)
      awk '/^## Session Summary/{found=1; next} /^---/{found=0} found{print}' "$f"
      echo ""
    done
  else
    # Single session — show full file
    cat "$LATEST"
    echo ""
  fi

  # Always show the tail from the MOST RECENT session only
  if [ "$SESSION_COUNT" -gt 1 ]; then
    echo "### Last Session Tail (most recent: $(basename "$LATEST" | sed 's/-session\.tmp//'))"
    awk '/^## Handoff/{found=1} found{print}' "$LATEST"
    echo ""
  fi

  echo "---"
  echo "## Session Opening"
  echo ""
  echo "When the user first messages you this session, open with a brief recap:"
  echo "1. **Recent work:** what was accomplished across all recent sessions (from Session Summaries above)"
  echo "2. **Left off at:** the final state from the most recent session tail"
  echo "3. **Next step:** use the 'Next:' line from the most recent Session Summary, otherwise infer"
  echo ""
  echo "Keep it to 4-5 lines total. Use Claude Code subscription tokens — no external API call."
  echo ""
  echo "---"
fi

# --- Terminal resume banner (stderr — visible to user at session start) ---
if [ -n "$LATEST" ]; then
  DATE=$(basename "$LATEST" | grep -oE '^[0-9]{4}-[0-9]{2}-[0-9]{2}')
  # Extract summary narrative (first non-empty line after ## Session Summary)
  SUMMARY=$(awk '/^## Session Summary/{found=1; next} found && /^[^[:space:]]/{print; exit} /^---/{found=0}' "$LATEST" | cut -c1-90)
  # Extract Next: line from summary block
  NEXT=$(grep -m1 '^Next:' "$LATEST" | sed 's/^Next: //' | cut -c1-90)
  # Fallback: try **Next step:** from handoff tail
  [ -z "$NEXT" ] && NEXT=$(grep -m1 '^\*\*Next step:\*\*' "$LATEST" | sed 's/\*\*Next step:\*\* //' | cut -c1-90)
  echo "" >&2
  echo "┌─ Resume: $DATE · $PROJECT ─────────────────────────────────────────────" >&2
  [ -n "$SUMMARY" ] && printf "│ Last  → %s\n" "$SUMMARY" >&2
  [ -n "$NEXT"    ] && printf "│ Next  → %s\n" "$NEXT" >&2
  echo "└────────────────────────────────────────────────────────────────────────" >&2
  echo "" >&2
fi

# Stderr notices only
LEARNED_COUNT=$(find "$LEARNED_DIR" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
[ "$LEARNED_COUNT" -gt 0 ] && echo "[SessionStart] $LEARNED_COUNT learned skills in $LEARNED_DIR" >&2

# --- System health check ---
"$HOME/.claude/hooks/memory-persistence/health-check.sh"

exit 0
