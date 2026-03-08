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
GLOBAL_FACTS="$HOME/.claude/projects/-Users-Lewis/memory/facts.json"

FACTS_OUTPUT=$(python3 "$HOME/.claude/memory/mem0.py" retrieve "$FACTS_PATH" "$GLOBAL_FACTS" 2>/dev/null)
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

# --- Always-active entries from topic files (ctx: always) ---
TOPICS_DIR="$HOME/.claude/projects/$ENCODED_PATH/memory/topics"
GLOBAL_TOPICS_DIR="$HOME/.claude/projects/-Users-Lewis/memory/topics"

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

# --- Previous session (only if it has content beyond template) ---
LATEST=$(find "$SESSIONS_DIR" -name "*.tmp" -mtime -7 2>/dev/null | sort -r | head -1)

if [ -n "$LATEST" ]; then
  CONTENT=$(grep -v "^Session ended:" "$LATEST" | grep -v "^$" | tail -n +8 | grep -v "^##" | tr -d '\n')
  if [ -n "$CONTENT" ]; then
    echo "## Previous Session Notes"
    echo ""
    cat "$LATEST"
    echo ""
    echo "---"
  fi
fi

# Stderr notices only
LEARNED_COUNT=$(find "$LEARNED_DIR" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
[ "$LEARNED_COUNT" -gt 0 ] && echo "[SessionStart] $LEARNED_COUNT learned skills in $LEARNED_DIR" >&2
exit 0
