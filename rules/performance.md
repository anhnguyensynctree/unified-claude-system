# Performance Rules — Always Follow

## Model Selection
See `rules/agents.md` § Model Selection Per Task for the full decision table.
- Haiku = judge/worker (pass/fail, extraction, mechanical)
- Sonnet = builder (code gen, synthesis, briefings, research)
- Opus = architect (failed on Sonnet, 5+ files, high-stakes)
CLI Agent tool uses `model` parameter: `model: "haiku"` / `model: "sonnet"` / `model: "opus"`

## Token Minimization
Every token costs. Apply these at all times:
- Read files at line ranges (offset + limit) — never full read unless necessary
- Use mgrep to locate targets before reading
- Load a rules or context file only when it is directly needed for the task
- Never repeat content already present in context
- Prefer targeted Edit over full Write rewrites
- Cut responses to the minimum that communicates clearly

## Debug Loop — Fork + ctx-exec (Always Apply)
A debug loop is any sequence of: run test → read error → edit → repeat.

- **Always pipe test output through ctx-exec** — never let raw `pnpm test` output hit context:
  ```bash
  ~/.claude/bin/ctx-exec "failing tests" pnpm test
  ~/.claude/bin/ctx-exec "type error" npx tsc --noEmit
  ```
- **Fork before iteration 3** — if the loop has not resolved in 2 attempts, `/fork` to an isolated context before continuing. Each failed attempt leaves noise in context that compounds cost.
- **Why:** The blinded-judge fix on 2026-03-31 required 5 context compactions in one session because raw test output filled the 200k window on each iteration. Estimated 500k+ extra input tokens.

## Large Output Commands — Always Use ctx-exec
Do not rely on size detection — the first run is already too late. Always use ctx-exec for these command patterns:

```bash
# Test runners — always
~/.claude/bin/ctx-exec "failing tests" pnpm test
~/.claude/bin/ctx-exec "failing tests" vitest run
~/.claude/bin/ctx-exec "failing tests" npx jest

# Type check + lint — always
~/.claude/bin/ctx-exec "type error" npx tsc --noEmit
~/.claude/bin/ctx-exec "lint error" pnpm run lint

# Build — always
~/.claude/bin/ctx-exec "error warning" npm run build
~/.claude/bin/ctx-exec "error warning" pnpm build

# GitHub / infra — always
~/.claude/bin/ctx-exec "open issues" gh issue list --limit 50
~/.claude/bin/ctx-exec "failed" gh run view
~/.claude/bin/ctx-exec "error" docker logs <container>
~/.claude/bin/ctx-exec "error" kubectl logs <pod>

# Large diffs — always
~/.claude/bin/ctx-exec "changed" git diff
```

Raw bash is fine for: `git status`, `ls`, `cat <single-file>`, `echo`, simple one-liners.

The PostToolUse hook warns when raw output exceeds 5KB — that is the fallback catch, not the primary guard.

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
