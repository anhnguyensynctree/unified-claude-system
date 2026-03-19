# Performance Rules — Always Follow

## Model Selection
- Haiku: repetitive, clear instructions, worker agents
- Sonnet: default for 90% of tasks
- Opus: failed first attempt, 5+ files, architecture, security-critical
CLI Agent tool uses `model` parameter: `model: "haiku"` / `model: "sonnet"` / `model: "opus"`

## Token Minimization
Every token costs. Apply these at all times:
- Read files at line ranges (offset + limit) — never full read unless necessary
- Use mgrep to locate targets before reading
- Load a rules or context file only when it is directly needed for the task
- Never repeat content already present in context
- Prefer targeted Edit over full Write rewrites
- Cut responses to the minimum that communicates clearly

## Large Output Commands — Use ctx-exec
When a Bash command will produce >5KB output (test runs, build logs, `gh issue list`, `kubectl`, `docker logs`, large diffs), use ctx-exec to filter by intent:
```bash
~/.claude/bin/ctx-exec "intent phrase" <command>
# Examples:
~/.claude/bin/ctx-exec "failing tests" pnpm test
~/.claude/bin/ctx-exec "error warning" npm run build
~/.claude/bin/ctx-exec "open issues" gh issue list --limit 50
```
ctx-exec returns only lines matching the intent (+ 2 lines context). Raw output never enters context window.

## Context Hygiene
- Compact manually at logical phase transitions: after exploration, after a milestone, before switching major tasks
- Never @-reference large doc files inline — use file paths with read guidance
- Do not load reference files that aren't needed for this specific task
- Keep max 5-6 MCPs enabled per project, under 80 total tools active

## Fork Strategy
Use /fork to protect context from branching conversations:
- Suggest fork when switching from planning → implementation
- Suggest fork when a second workstream starts while one is active
- Before forking: flush current decisions to project memory
- Each fork starts lean — only load what that branch needs

## Search
- Use mgrep instead of grep or ripgrep
- Never use grep -r on large directories
- mgrep first, read second — never read blind

## Codebase
- Files under 300 lines = cheaper tokens + higher first-attempt success rate
- Long files force multiple read tool calls, re-reads, risk losing information
- Continuously remove dead code — run /refactor-clean periodically

## Markdown Files
- Every .md file is loaded into context and costs tokens on every read
- Do not create .md files unless explicitly required — prefer inline comments or code
- Allowed without explicit request: README.md, CLAUDE.md, codemap.md, session files, files under .claude/
- Treat each .md like a dependency: only add it if it pulls its weight

## MCP vs CLI Skills
- Prefer CLI skills over MCP for: GitHub, Supabase, Vercel, Railway
- MCP still costs tokens even with lazy loading
- Use MCP only when the CLI equivalent doesn't exist
