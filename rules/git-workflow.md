# Git Workflow Rules — Always Follow

## Commit Format
- Always use conventional commits: feat|fix|chore|docs|refactor|test|perf
- Format: <type>(<scope>): <subject>
- Subject: under 72 chars, imperative mood ("add" not "added")
- Add body if the change needs explanation
- Reference issue numbers when available: "fixes #123"

## Branch Naming
- Format: <type>/<short-description>
- Examples: feat/user-auth, fix/login-redirect, chore/update-deps

## Rules
- Never commit directly to main
- Always review diff before committing
- Never include console.log, secrets, or commented-out code in commits
- NEVER add `Co-Authored-By` trailers to commits or PR descriptions — not for Claude, not for any tool

## Pre-Commit / PR Checklist — Always Run Before Marking Work Done
Every task, every PR, every agent — all six must pass:

1. **Clean repo** — `git ls-files | grep -E "node_modules|\.next|dist/|out/|coverage/|\.env$"` — any results = blocked
2. **No console.log** — `git diff --name-only HEAD | xargs grep -l "console\.log" 2>/dev/null` — any results = blocked
3. **Type check** — `pnpm exec tsc --noEmit` (or `npx tsc --noEmit`) — zero errors
4. **Lint** — `pnpm exec eslint . --max-warnings 0` (or the project's `lint` script) — zero errors
5. **Tests + coverage** — `pnpm test` (or equivalent) — all passing, coverage ≥ 80%
6. **E2E** — `pnpm exec playwright test` — all passing. Required if any user-facing flow was added or changed. If no E2E suite exists yet and a flow was touched: write the spec first, then run it.

Adapt commands to the project's package manager and scripts. If a check doesn't apply (e.g. no TypeScript, no lint script), note it explicitly — never silently skip. Never mark a task done with any check failing.

## CI/CD — Required for Every GitHub Project
Every project with a GitHub repo must have a GitHub Actions CI pipeline that runs the same checklist above on every PR and every merge to main. No exceptions.
- CI setup belongs in the first milestone — never deferred to a later feature
- No feature work merges without CI passing
- Production deploys gate on CI — never bypass it with a direct push

### CI Pipeline Order (web projects with Vercel)
```
1. lint + typecheck + unit tests
2. E2E (playwright) — against localhost or test env
3. Deploy to Vercel → capture preview URL
4. Lighthouse CI — run against Vercel preview URL
   lhci autorun --collect.url=$VERCEL_URL
   Thresholds: performance ≥ 85, accessibility ≥ 95, best-practices ≥ 90
5. Post Lighthouse scores as PR comment
```
Lighthouse runs AFTER deploy — it needs the real URL. Never run it against localhost in CI.
`lighthouserc.json` lives at project root. Vercel token + project IDs in GitHub Actions secrets.

### CI Shell Script Rules
- **Never `|| true` on a step that produces a value used downstream** — silent failures mask real breakage
- **Validate captured variables before use**: `[ -z "$DEPLOY_URL" ] && echo "ERROR: ..." && exit 1`
- **Strip ANSI codes from CLI output before grepping**: `sed 's/\x1b\[[0-9;]*m//g'` — CLIs (Vercel, etc.) add color codes in CI that break `^`-anchored regexes
- **Use `grep -oE` not `grep -E`** when extracting a substring — `-o` returns only the match, making surrounding characters irrelevant

## Parallel Work (CLI)
- Use `EnterWorktree` or `--worktree` flag for isolated parallel work
- Each worktree gets its own branch based on HEAD
- Use `isolation: "worktree"` on Agent tool calls for agents that need their own repo copy
- Aim for orthogonal tasks — minimal overlap in files between worktrees
- Worktrees live in `.claude/worktrees/` and auto-cleanup on session exit
