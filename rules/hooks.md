# Hooks Documentation

All hooks are configured in ~/.claude/settings.json

## PreToolUse Hooks
- tmux/long-process reminder: fires when Claude runs npm/pnpm/yarn/cargo/pytest
- .md file blocker: blocks creating loose .md files (allows README, CLAUDE, session files)
- git push reminder: nudges to review diff before pushing

## PostToolUse Hooks
- prettier auto-format: runs on .ts/.tsx/.js/.jsx edits if prettier is installed
- TypeScript check: runs tsc --noEmit after .ts/.tsx edits
- console.log warning: warns when console.log found in edited file
- search nudge: suggests mgrep (semantic) or grep (exact) when grep -r is used

## Stop Hooks
- session-end.sh: persists session state to ~/.claude/sessions/
- evaluate-session.sh: runs continuous learning extraction
- console.log audit: checks all modified files for console.log

## PreCompact Hook
- pre-compact.sh: saves session state before context compaction

## SessionStart Hook
- session-start.sh: checks for recent sessions (last 7 days), notifies of available context

## Notification Hook
- macOS notification: displays system alert when Claude needs attention

## To Disable Per Project
Add to [project]/.claude/settings.json:
{ "hooks": { "PostToolUse": [] } }
This overrides global hooks for that project only.
