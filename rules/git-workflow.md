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

## Parallel Work (CLI)
- Use `EnterWorktree` or `--worktree` flag for isolated parallel work
- Each worktree gets its own branch based on HEAD
- Use `isolation: "worktree"` on Agent tool calls for agents that need their own repo copy
- Aim for orthogonal tasks — minimal overlap in files between worktrees
- Worktrees live in `.claude/worktrees/` and auto-cleanup on session exit
