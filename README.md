# unified-claude-system

A production-grade configuration layer for Claude Code CLI. Treats Claude like a senior engineer on a real team: opinionated, consistent, memory-persistent, and cost-aware.

> Built and maintained by [@anhnguyensynctree](https://github.com/anhnguyensynctree)

---

## What This Is

Out of the box, Claude Code is powerful but stateless. Every session starts cold. It doesn't know your project, your conventions, what you fixed yesterday, or what you prefer not to do.

This system solves that:

- **Persistent memory** — Claude remembers what it learned last session
- **Enforced conventions** — rules load automatically, not trusted to per-prompt engineering
- **Automated quality gates** — hooks catch `console.log`, run TypeScript checks, validate .md quality in real time
- **Cost control** — token usage minimized by design throughout every file
- **Skill accumulation** — patterns discovered during work are extracted and reused

The result: Claude behaves like a developer who has worked in your codebase for months.

---

## Directory Structure

```
~/.claude/
├── CLAUDE.md                    ← Global operating instructions (always loaded)
├── settings.json                ← Hook wiring + plugin config + model
├── keybindings.json             ← Custom keyboard shortcuts
├── policy-limits.json           ← Safety constraints
├── statusline-command.sh        ← Custom status line (dir + git branch + ctx%)
│
├── rules/                       ← Domain-specific rules (loaded on demand)
│   ├── coding-style.md          ← File size, naming, quality standards
│   ├── testing.md               ← TDD, 80% coverage, consistency-critical
│   ├── git-workflow.md          ← Conventional commits, branch naming
│   ├── security.md              ← Secrets, injection, immune system pattern
│   ├── performance.md           ← Model selection, token minimization
│   ├── patterns.md              ← API shapes, async, error handling
│   ├── agents.md                ← Delegation, model tiers, dispatch protocol
│   └── hooks.md                 ← Hook reference and documentation
│
├── contexts/                    ← Mode-specific prompts
│   ├── dev.md                   ← Implementation mode
│   ├── review.md                ← Code review mode
│   └── research.md              ← Exploration mode
│
├── commands/                    ← Slash command definitions (/command-name)
│   ├── tdd.md                   ← RED → GREEN → IMPROVE workflow
│   ├── commit.md                ← Conventional commit with safety checks
│   ├── plan.md                  ← 5-phase implementation planning
│   ├── scaffold-project.md      ← Full monorepo bootstrap
│   ├── breakdown.md             ← Task decomposition with model tiers
│   ├── fork.md                  ← Context initialization in new session
│   ├── consolidate-memory.md    ← Haiku-powered memory compression
│   ├── review-pr.md             ← Structured PR review
│   ├── e2e.md                   ← E2E test generation
│   ├── debug.md                 ← Systematic debugging workflow
│   ├── learn.md                 ← Pattern extraction
│   ├── standup.md               ← Git log standup report
│   ├── refactor-clean.md        ← Codebase cleanup
│   ├── test-coverage.md         ← Coverage analysis
│   └── update-codemaps.md       ← Codemap regeneration
│
├── hooks/
│   └── memory-persistence/
│       ├── session-start.sh     ← Injects context at session open
│       ├── session-end.sh       ← Persists state at session close
│       ├── pre-compact.sh       ← Saves state before context compaction
│       └── mem0-extract.sh      ← Extracts structured facts from transcripts
│
└── skills/
    ├── continuous-learning/
    │   ├── SKILL.md             ← Skill definition
    │   └── evaluate-session.sh  ← Pattern extraction on Stop hook
    ├── strategic-compact.md
    └── codemap-updater.md
```

---

## Core Components

### CLAUDE.md — The Global Brain

Always loaded. Sets operating mode, token minimization rules, memory routing, context fork strategy, before/after task checklists.

Key behaviors it enforces:
- No preamble, no restating the task, no post-task summaries
- Read files at line ranges, not full files
- Load rules only when domain is active
- Compact after each major phase
- Write tests before marking any task done

### Rules System

Seven domain files, loaded on demand:

| File | Covers |
|---|---|
| `coding-style.md` | Max 300 lines/file, max 50 lines/function, naming conventions |
| `testing.md` | TDD mandatory, 80% coverage, consistency-critical pass^3 rule |
| `git-workflow.md` | Conventional commits, never commit to main |
| `security.md` | No hardcoded secrets, immune system pattern — appends every incident as a new rule |
| `performance.md` | Haiku/Sonnet/Opus tier selection, token minimization |
| `patterns.md` | `{ data, error, meta }` API shape, async/await, import ordering |
| `agents.md` | Delegation protocol, model selection per task type |

### Hooks System

Automated behaviors wired to lifecycle events in `settings.json`:

**PreToolUse:**
- Long-process reminder when npm/pnpm/yarn/cargo/pytest are run
- Hard blocks (exit 2) creating loose `.md` files outside allowed paths
- Git push reminder to run `/review-pr` first

**PostToolUse:**
- Prettier auto-format on every `.ts/.tsx/.js/.jsx` edit
- TypeScript check (`tsc --noEmit`) on every `.ts/.tsx` edit
- Pyright check on every `.py` edit
- `console.log` warning on every file edit
- Markdown quality check (heading, line count, no placeholders)
- mgrep nudge when `grep -r` is used

**Stop / SessionEnd:**
- Session state written to `sessions/YYYY-MM-DD-session.tmp`
- Continuous learning evaluation runs
- `console.log` audit across all modified files
- mem0 fact extraction from session transcript (async)

**SessionStart:**
- Injects project `CLAUDE.md` if found in cwd
- Loads retrieved mem0 facts
- Loads project `MEMORY.md`
- Loads last session notes (within 7 days)

### Memory System — Tiered

```
~/.claude/projects/[encoded-project-path]/memory/
├── MEMORY.md          ← Always loaded (kept under 80 lines)
├── insights.md        ← Cross-topic patterns from consolidation
└── topics/
    ├── debugging.md   ← [context] Problem → Cause → Fix
    ├── patterns.md    ← Architecture decisions, confirmed patterns
    ├── projects.md    ← Per-project blocks
    ├── hooks.md       ← Hook config and fixes
    ├── scaffold.md    ← Scaffold workflow decisions
    └── agents.md      ← Agent patterns, model selection
```

MEMORY.md is a lean index. Topic files load only when the domain matches the current task. Memory is compressed by `/consolidate-memory` using a Haiku agent (cost-efficient).

Every `##` section is tagged `| importance:high/medium/low`. Low-importance content is pruned first.

### Slash Commands

| Command | What it does |
|---|---|
| `/tdd <task>` | RED → GREEN → IMPROVE with 80% coverage check |
| `/commit` | Conventional commit — stages specific files, shows message for approval |
| `/plan <task>` | 5-phase: research → plan → implement → review → verify |
| `/scaffold-project` | Full monorepo (Next.js + Supabase + pnpm workspaces + Turborepo) |
| `/breakdown <task>` | Decompose into subtasks with model tiers and parallelization flags |
| `/fork` | Initialize context in a new session (loads memory, session, CLAUDE.md) |
| `/review-pr` | Structured review: Blockers / Suggestions / Looks Good with file:line |
| `/consolidate-memory` | Haiku agent compresses all memory files |
| `/learn` | Extract and save a reusable pattern immediately |
| `/debug <issue>` | Systematic debugging workflow |

### Plugins (Active)

| Plugin | Purpose |
|---|---|
| `hookify` | GUI for creating and managing hooks |
| `context7` | Up-to-date library documentation in context |
| `mgrep` | Semantic search — replaces `grep -r`, ~50% token reduction |
| `pyright-lsp` | Python type checking on edit |

TypeScript LSP, code-review, and security-guidance plugins are scoped **per package** in per-project `settings.json` — only loaded where needed.

---

## The Philosophy

**1. Rules enforced > rules asked for**
Putting standards in CLAUDE.md + hooks + checklists means they apply even when you forget to say them. No per-prompt reminders needed.

**2. Separation of concerns on context cost**
Every file loaded costs tokens. Rules load on demand. Memory is tiered. Plugins are scoped per package. The overhead at session start is minimal; richness is available when needed.

**3. Context forking as a first-class tool**
Long conversations drift. `/fork` treats context as a resource. When work branches, fork, flush state to memory, start lean.

**4. The system learns**
Security incidents get appended to `rules/security.md`. Bug fixes go to `topics/debugging.md`. Non-trivial solutions are extracted with `/learn`. The configuration becomes an immune system.

**5. Cost-tiered agents**
- Haiku — repetitive tasks, worker agents, memory consolidation (5x cheaper than Opus)
- Sonnet — default for 90% of coding tasks
- Opus — first attempt failed, 5+ files, architectural decisions, security-critical

---

## Setup

### Prerequisites

- [Claude Code CLI](https://claude.ai/code)
- Node.js (for prettier, tsc)
- Python 3 (for mem0 scripts)
- `jq` — `brew install jq`
- `gh` CLI — `brew install gh`

### Install

```bash
# Clone into ~/.claude
git clone https://github.com/anhnguyensynctree/unified-claude-system.git ~/.claude

# Make hooks executable
chmod +x ~/.claude/hooks/memory-persistence/*.sh
chmod +x ~/.claude/skills/continuous-learning/evaluate-session.sh

# Initialize your global memory
mkdir -p ~/.claude/projects/-Users-$(whoami)/memory/topics
```

Create `~/.claude/projects/-Users-$(whoami)/memory/MEMORY.md`:

```markdown
# Memory Index

## User Preferences | importance:high
- [your preferences here]

## Topic Index | importance:high
| When... | Load |
|---|---|
| Hitting errors | topics/debugging.md |
| Architecture decisions | topics/patterns.md |
```

### First Session

Open Claude Code. Run:

```
/fork
```

Claude loads all context and asks what you want to work on.

### First Project

```
/scaffold-project
```

Answers 4 questions, generates full monorepo with memory initialized at the correct path.

---

## Workflows

```bash
# Start a new day
/fork

# Implement a feature with TDD
/tdd add payment webhook handler

# Plan a complex task
/plan refactor authentication system

# Commit cleanly
/commit

# Review a PR before merge
/review-pr

# Extract a pattern you just solved
/learn

# Compress memory when it grows
/consolidate-memory
```

---

## Iterating and Contributing

This repo **is** `~/.claude`. Updating the system:

```bash
cd ~/.claude
# make changes to any config file
git add rules/testing.md  # or whichever file changed
git commit -m "feat(testing): raise coverage threshold to 85%"
git push
```

PRs and issues welcome. If you adapt this for a different stack, open a PR — especially for non-Next.js/Supabase scaffold variants.

---

## License

MIT
