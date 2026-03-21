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
- Never write: "it's worth noting", "importantly", "ensure that", "it is important to", "it should be noted"
- Never start sentences with: "Additionally", "Furthermore", "Moreover", "In conclusion", "Certainly"
- No hedging: cut "may", "might", "could potentially", "in some cases" unless uncertainty is genuinely material

## Output Completeness — Always Active
A partial output is a broken output. Never truncate or shortcut:
- Deliver every file, function, and section requested — count deliverables before starting
- Banned: `// ...`, `// rest of code`, `// implement here`, `// similar to above`, `// TODO`, bare `...`
- Banned: "let me know if you want me to continue", "for brevity", "the rest follows the same pattern"
- Never show a skeleton when a full implementation was requested
- When approaching token limit: write to a clean breakpoint, then output `[PAUSED — X of Y complete. Send "continue" to resume from: <next section>]`
- On "continue": resume exactly where stopped — no recap, no repetition

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

## Core Principles
- **No Laziness** — find root causes, no temporary fixes, senior developer standards

## Default Operating Mode
Unless told otherwise:
- Prioritize working, tested code over speed
- Keep files under 300 lines
- Run tests before considering a task done
- Check for console.log before finishing
- Never modify files outside the task scope
- For non-trivial implementations: pause before presenting and ask "is there a more elegant solution?" — skip for simple/obvious fixes

## Markdown File Standards
Every .md costs tokens on load and shapes Claude's behavior. Rules for all .md writes:
- Files under .claude/ — allowed only when improving workflow, rules, or memory; subject to strict quality gate below
- README.md at project root — always allowed
- Any .md in a project's docs/ folder — always allowed; docs/ is the base folder for all documentation writing
- Any .md in a project's design/stitch/ folder — always allowed; managed exclusively by the /stitch skill
- All other .md files anywhere — require explicit user request

Quality gate — applies to every .md, especially files under .claude/:
- Must have a # heading
- Minimum 5 substantive lines — no stub or placeholder files
- No unfilled placeholders ([empty], TODO, ...)
- Dense and scannable — every line earns its place; cut anything decorative
- A shallow .claude/ file is worse than no file — it loads as false context every session

## Switching Modes
When asked to review, audit, critique, or give feedback on code or a PR → read ~/.claude/contexts/review.md and apply it
When asked to research, explore, investigate, or understand a codebase or topic → read ~/.claude/contexts/research.md and apply it
When asked to implement, build, add, create, or develop a feature → read ~/.claude/contexts/dev.md and apply it
When asked to write, fix, debug, run, or review tests, E2E, Playwright, Cypress, Vitest, Jest, or QA → read ~/.claude/contexts/test.md and apply it
When asked to design, build, or review UI, UX, components, layouts, or interface flows → read ~/.claude/contexts/ui-ux.md AND ~/.claude/contexts/design-quality.md AND rules/design-system.md AND ~/.claude/skills/stitch/llms.txt; check design/stitch/manifest.json for existing screens; run stitch skill autonomously per llms.txt trigger rules before writing any component code
When asked to design, plan, or review system architecture, backend design, APIs, or data models → read ~/.claude/contexts/architecture.md and apply it
When asked to plan, break down, scope, or roadmap a sprint, project, feature, or milestone → read ~/.claude/contexts/plan.md and apply it
When asked to audit, harden, review, or fix security, vulnerabilities, or auth → read ~/.claude/contexts/security.md and apply it
When asked to debug, diagnose, trace, or investigate a failure, error, crash, or unexpected behavior → read ~/.claude/contexts/debug.md and apply it
When asked to handle CI/CD, pipelines, infrastructure, deployment, Docker, Terraform, or DevOps → read ~/.claude/contexts/devops.md and apply it
When asked to refactor, clean up, restructure, simplify, or reduce technical debt → read ~/.claude/contexts/refactor.md and apply it
When asked to profile, optimize, improve performance, reduce latency, or fix slow code → read ~/.claude/contexts/performance.md and apply it
When asked to work on data pipelines, ETL, ML, analytics, transforms, or data engineering → read ~/.claude/contexts/data.md and apply it
When asked to write, update, or generate documentation, runbooks, ADRs, changelogs, or API reference → read ~/.claude/contexts/docs.md and apply it
When asked to test, verify, explore, or QA a live URL, staging environment, localhost app, or web interface → use /browse skill (persistent browser daemon — do NOT cold-start Playwright)
When asked to check web design, UI layout, visual correctness, or how something looks in the browser → use /browse skill: screenshot first, then inspect, then report findings

## Available Tools & Skills
Never guess a tool or skill's API — read its llms.txt first before using.

| Skill/Tool | llms.txt | When to use |
|---|---|---|
| /stitch | ~/.claude/skills/stitch/llms.txt | Any UI generation, screen design, component implementation |
| /browse | ~/.claude/skills/browse/llms.txt | Test or verify live URLs, localhost apps, authenticated flows, UI screenshots |
| /oms | ~/.claude/skills/oms/llms.txt | Architecture decisions, multi-domain tasks, high-stakes changes, research synthesis |
| rv (remotion) | ~/code/tools/remotion/llms.txt | Render any video — ShortVideo (9:16), LandscapeVideo (16:9), Audiogram (1:1) |

## Before Starting Any Task
1. Check if .claude/codemap.md exists → read it for navigation
2. Check if .claude/sessions/ has a recent session file → offer to restore context
3. For any task with 3+ steps or architectural decisions: output a plan first, get confirmation, then implement — never jump straight to code
4. If something goes sideways mid-task: STOP, re-plan, then continue — don't push through

## After Completing Any Task
1. Confirm tests were written for every new/modified component, service, hook, or route
2. Run targeted tests for modified files — must pass
3. Run full test suite — no regressions
4. Add E2E test if a user-facing flow was added or changed
5. Check for console.log in modified files
6. Update .claude/codemap.md if structure changed
7. Write any new decisions or patterns to project memory
8. Self-check: "Would a staff engineer approve this?" — if no, fix it before presenting

## Rules Reference
Read only the relevant file:
- Security → rules/security.md
- Code style → rules/coding-style.md
- Testing → rules/testing.md
- Git → rules/git-workflow.md
- Agents → rules/agents.md
- Performance/tokens → rules/performance.md
- API patterns → rules/patterns.md
- Design system / UI generation → rules/design-system.md
