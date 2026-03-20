# Hooks Documentation

All hooks are configured in ~/.claude/settings.json

## PreToolUse Hooks
- tmux/long-process reminder: fires when Claude runs npm/pnpm/yarn/cargo/pytest
- .md file blocker: blocks creating loose .md files (allows README, CLAUDE, session files)
- git push reminder: nudges to review diff before pushing

## PostToolUse Hooks
- prettier auto-format: runs on .ts/.tsx/.js/.jsx edits if prettier is installed
- console.log warning: warns when console.log found in edited file
- search nudge: suggests mgrep (semantic) or grep (exact) when grep -r is used

## TypeScript Check — Project-Scoped (NOT global)
The tsc hook is intentionally absent from global settings. It must be defined per-project.

**Why:** Global tsc runs from an unknown cwd — in monorepos this causes it to scan the wrong
tsconfig or hang indefinitely. Each project knows its own package layout.

**Template for any TypeScript project's .claude/settings.json:**
```json
{
  "matcher": "Edit",
  "hooks": [{
    "type": "command",
    "timeout": 30,
    "command": "FILE=$(jq -r '.tool_input.file_path'); echo \"$FILE\" | grep -qE '\\.(ts|tsx)$' || exit 0; PKG=$(echo \"$FILE\" | grep -oE '.*/packages/[^/]+'); [ -z \"$PKG\" ] && exit 0; cd \"$PKG\" && node_modules/.bin/tsc --noEmit --skipLibCheck 2>&1 | head -20 >&2 || true"
  }]
}
```
For single-package projects (no `packages/` layout), replace the PKG extraction with a hardcoded
`cd /path/to/project` and use `node_modules/.bin/tsc` directly.

## Stop Hooks
- session-end.sh: persists session state to ~/.claude/sessions/
- evaluate-session.sh: runs continuous learning extraction
- console.log audit: checks all modified files for console.log

## PreCompact Hook
- pre-compact.sh: saves session state before context compaction

## SessionStart Hook
- session-start.sh: checks for recent sessions (last 7 days), notifies of available context
- health-check.sh: validates system integrity — settings schema, script permissions, mem0 syntax, facts.json, API key, Claude Code version (zero context tokens, stderr only)

## SessionEnd Hook
- mem0-extract.sh: extracts facts from session transcript and writes handoff summary (async)

## Notification Hook
- macOS notification: displays system alert when Claude needs attention

## To Disable Per Project
Add to [project]/.claude/settings.json:
{ "hooks": { "PostToolUse": [] } }
This overrides global hooks for that project only.
