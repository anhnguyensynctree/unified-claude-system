# Global Claude Instructions

## Shell Environment
CLI runs in the user's native shell (zsh). No wrappers needed.
If a command requires specific env (nvm, pyenv), use the full path or source the profile.

## Power User Mode — Always Active
The user is an experienced developer. Operate accordingly:
- No preamble, no "great question", no restating the task
- No confirmation of understanding — just act
- No post-task summaries unless explicitly asked
- Responses as short as the task allows — prefer code over prose
- Never explain what you're about to do — do it, then note only what matters

## Token Minimization — Always Active
Context is expensive. Minimize usage at every step:
- Read files at specific line ranges when possible, not full files
- Use mgrep to locate before reading
- Load rules/context files only when directly relevant
- Compact after each major phase — do not wait for auto-compact
- Never repeat information already in context
- Prefer targeted edits over full rewrites

## Fork — Use Proactively
Suggest /fork when the conversation is about to branch:
- Switching from planning to implementation
- Starting a second feature while one is in progress
- Isolating experimental or risky work
- Before forking: write current decisions to memory so the fork has context

## Memory — Tiered System
Memory is split across files. MEMORY.md is always loaded — it is the index, not the store.

**On every session start / fork / compact:**
1. MEMORY.md loads automatically (session-start hook)
2. Read the Topic Index in MEMORY.md
3. Load any topic files relevant to the current task using the Read tool

**Writing new memory — route to correct file:**
- User prefs / workflow changes → MEMORY.md
- Debugging fix → `topics/debugging.md`
- Architecture/API decision → `topics/patterns.md`
- Project update → `topics/projects.md`
- Hook change → `topics/hooks.md`
- Scaffold change → `topics/scaffold.md`
- Agent pattern → `topics/agents.md`

**Importance tags — every `##` header must have one:**
- `importance:high` — affects every session, always relevant
- `importance:medium` — relevant to active projects or recent work
- `importance:low` — reference only, prune first during consolidation

**Thresholds:** Run `/consolidate-memory` when any topic file exceeds 100 lines or MEMORY.md exceeds 80 lines. Consolidation uses Haiku — zero extra cost beyond session tokens.

## Default Operating Mode
Unless told otherwise:
- Prioritize working, tested code over speed
- Keep files under 300 lines
- Run tests before considering a task done
- Check for console.log before finishing
- Never modify files outside the task scope

## Markdown File Standards
Every .md costs tokens on load and shapes Claude's behavior. Rules for all .md writes:
- Files under .claude/ — allowed only when improving workflow, rules, or memory; subject to strict quality gate below
- README.md at project root — always allowed
- Any .md in a project's docs/ folder — only allowed when docs context is active
- All other .md files anywhere — require explicit user request

Quality gate — applies to every .md, especially files under .claude/:
- Must have a # heading
- Minimum 5 substantive lines — no stub or placeholder files
- No unfilled placeholders ([empty], TODO, ...)
- Dense and scannable — every line earns its place; cut anything decorative
- A shallow .claude/ file is worse than no file — it loads as false context every session

## Switching Modes
When asked to review code or a PR → read ~/.claude/contexts/review.md and apply it
When asked to research or explore → read ~/.claude/contexts/research.md and apply it
When asked to implement or build → read ~/.claude/contexts/dev.md and apply it
When asked to write tests or QA → read ~/.claude/contexts/test.md and apply it
When asked to design UI, UX, or interface flows → read ~/.claude/contexts/ui-ux.md and apply it
When asked to design system architecture or backend design → read ~/.claude/contexts/architecture.md and apply it
When asked to plan a sprint, project, or roadmap → read ~/.claude/contexts/plan.md and apply it
When asked to audit for security or do a security review → read ~/.claude/contexts/security.md and apply it
When asked to debug or diagnose a failure → read ~/.claude/contexts/debug.md and apply it
When asked to handle CI/CD, infrastructure, deployment, or DevOps → read ~/.claude/contexts/devops.md and apply it
When asked to refactor, clean up, or reduce technical debt → read ~/.claude/contexts/refactor.md and apply it
When asked to profile, optimize, or improve performance → read ~/.claude/contexts/performance.md and apply it
When asked to work on data pipelines, ML, analytics, or data engineering → read ~/.claude/contexts/data.md and apply it
When asked to write documentation, runbooks, ADRs, or API reference → read ~/.claude/contexts/docs.md and apply it

## Before Starting Any Task
1. Check if .claude/codemap.md exists → read it for navigation
2. Check if .claude/sessions/ has a recent session file → offer to restore context
3. For multi-file tasks: create a plan first, do not jump to implementation

## After Completing Any Task
1. Confirm tests were written for every new/modified component, service, hook, or route
2. Run targeted tests for modified files — must pass
3. Run full test suite — no regressions
4. Add E2E test if a user-facing flow was added or changed
5. Check for console.log in modified files
6. Update .claude/codemap.md if structure changed
7. Write any new decisions or patterns to project memory

## Rules Reference
Read only the relevant file:
- Security → rules/security.md
- Code style → rules/coding-style.md
- Testing → rules/testing.md
- Git → rules/git-workflow.md
- Agents → rules/agents.md
- Performance/tokens → rules/performance.md
- API patterns → rules/patterns.md
