# unified-claude-system

> Claude Code with persistent memory, enforced conventions, 10 context modes, and automated quality gates.
> Every session starts warm — Claude remembers your codebase, your decisions, and what you did yesterday.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/requires-Claude%20Code%20CLI-blue)](https://claude.ai/code)

**One-line install (macOS):**
```bash
git clone https://github.com/anhnguyensynctree/unified-claude-system.git ~/.claude
```
→ [Full macOS setup](#macos-setup) · [Windows / WSL2](#windows-setup-via-wsl2)

**Newcomer? One prompt does everything:**
Open Claude Code (anywhere — no project needed), paste this, and Claude handles the rest:
```
Set up my global Claude system from https://github.com/anhnguyensynctree/unified-claude-system:
1. Clone it into ~/.claude
2. Run the full setup for my platform (hooks executable, memory initialized, prerequisites checked)
3. Verify everything works: health check, hooks wired, MEMORY.md readable, /hey test
4. Report green/red for each check and fix anything broken
5. Confirm when I'm ready to start with /hey
```

![unified-claude-system architecture](assets/overview.svg)

---

## The Problem

Every Claude Code session starts cold. You re-explain your stack, your conventions, what you built yesterday. The same instructions — every single session.

**This system fixes that.** Drop it into `~/.claude` and Claude becomes a stateful development partner:

- **Persistent memory** — remembers decisions, patterns, and project context across sessions without manual re-briefing
- **Enforced conventions** — rules load automatically via hooks, not trusted to per-prompt engineering
- **14 context modes** — Claude shifts persona and priorities based on what you're doing: dev, test, review, security, debug, plan, ui-ux, architecture, devops, refactor, performance, data, docs, research — each loaded on demand, zero token cost until triggered
- **Automated quality gates** — catches `console.log`, runs TypeScript checks, enforces test coverage in real time
- **Cost-tiered agent dispatch** — Haiku for worker tasks, Sonnet for 90% of coding, Opus for architecture — never overpay
- **Continuous learning** — patterns discovered during work are extracted and reused in future sessions
- **[OMS v0.6](#oms--one-man-show)** — multi-agent discussion engine that convenes a virtual product team, plans milestones, executes tasks, and validates delivery autonomously

```
Without this:   "Use pnpm. TDD. Conventional commits. No console.log. 80% coverage minimum."
With this:      Claude already knows. Every session, from the first message.
```

---

## Who Is This For?

- **Claude Code CLI users** tired of re-briefing Claude every session
- **Solo developers** who want a consistent, opinionated AI pair programmer
- **Teams** who want Claude to follow the same conventions across all members
- **Cost-conscious users** — token usage is minimized by design, not afterthought

---

## Directory Structure

```
~/.claude/
├── CLAUDE.md                    ← Global operating instructions (always loaded)
├── settings.json                ← Hook wiring + plugin config + model
├── keybindings.json             ← Custom keyboard shortcuts
├── policy-limits.json           ← Safety constraints
├── statusline-command.sh        ← Custom status line (dir + git branch + ctx%)
├── oms-config.json              ← OMS project registry
├── oms-overview.md              ← OMS system architecture reference
│
├── rules/                       ← Domain-specific rules (loaded on demand)
│   ├── coding-style.md
│   ├── testing.md
│   ├── git-workflow.md
│   ├── security.md
│   ├── performance.md
│   ├── patterns.md
│   ├── agents.md
│   ├── hooks.md
│   ├── design-system.md
│   └── vercel.md
│
├── contexts/                    ← Mode-specific prompts (loaded on demand)
│   ├── dev.md, review.md, research.md, test.md
│   ├── ui-ux.md, architecture.md, plan.md, security.md
│   ├── debug.md, devops.md, refactor.md, performance.md
│   ├── data.md, docs.md
│
├── commands/                    ← Slash command definitions
│   ├── hey.md                   ← Session opener
│   ├── tdd.md, commit.md, plan.md
│   ├── scaffold-project.md, breakdown.md, fork.md
│   ├── consolidate-memory.md, review-pr.md, e2e.md
│   ├── debug.md, learn.md, standup.md
│   ├── refactor-clean.md, test-coverage.md, update-codemaps.md
│   └── oms-work.md              ← Execute OMS task queue
│
├── hooks/
│   └── memory-persistence/      ◄★ the memory engine lives here
│       ├── session-start.sh     ← Injects context at session open
│       ├── session-end.sh       ← Codemap staleness check on every stop
│       ├── pre-compact.sh       ← Emits priority-tiered XML snapshot before compaction
│       ├── mem0-extract.sh      ← Runs session-end extraction + handoff at SessionEnd
│       └── health-check.sh      ← Validates system integrity on every session start
│
├── bin/
│   ├── ctx-exec                 ← Filters large command output before it enters context
│   ├── bun-exec.sh              ← Batch 3+ parallel HTTP/API calls into one tool invocation
│   ├── discord-bot.py           ← OMS Discord integration
│   └── oms-work.py              ← OMS autonomous task execution engine
│
├── agents/                      ← OMS agent personas
│   ├── router/, synthesizer/, trainer/, task-elaboration/
│   ├── cto/, cpo/, clo/, cro/
│   ├── engineering-manager/, backend-developer/, qa-engineer/
│   ├── product-manager/, content-strategist/, ux-researcher/
│   ├── executive-briefing-agent/
│   ├── context-optimizer/
│   ├── shared-lessons/          ← Cross-agent learned patterns
│   ├── oms-audit/
│   ├── oms-work/                ← Task schema and execution contracts
│   ├── oms-field-contract.md    ← Inter-agent field contracts
│   └── training/                ← Scenario suite (067 scenarios)
│
├── skills/
│   ├── browse/                  ← Persistent Playwright browser daemon (/browse)
│   ├── stitch/                  ← AI UI generation — Google Stitch wrapper (/stitch)
│   ├── oms/                     ← Multi-agent discussion engine (/oms)
│   ├── oms-start/               ← Initialize OMS for a project (/oms-start)
│   ├── oms-exec/                ← Strategic milestone planning (/oms exec)
│   ├── oms-work/                ← Execute cleared task queue (/oms-work)
│   ├── oms-audit/               ← System health audit (/oms audit)
│   ├── oms-capture/             ← Capture failures as training scenarios (/oms-capture)
│   ├── oms-tool/                ← External research for system improvement (/oms-tool)
│   ├── oms-train/               ← Run training scenarios (/oms-train)
│   └── continuous-learning/     ← Pattern extraction at session end (/learn)
│
├── handoffs/                    ◄★ session handoff files (one per session)
│   └── YYYY-MM-DD-sessionid-project-session.tmp
│
└── projects/[encoded-path]/memory/   ◄★ per-project persistent memory
    ├── MEMORY.md                ← Always loaded index (<80 lines)
    ├── insights.md              ← Cross-topic patterns from consolidation
    ├── facts.json               ← Structured facts extracted from transcripts
    └── topics/
        ├── agents.md, hooks.md, patterns.md
        ├── scaffold.md, debugging.md, projects.md
        └── archived.md
```

---

## ★ Memory Layer — The Core

> Every other component enforces standards. The memory layer is what makes Claude *continuous* — able to carry context, decisions, and learned patterns across sessions without manual re-briefing.

```
Session Start
│
├── MEMORY.md injected (index, <80 lines)
│   └── Topic Index routes full topic files on demand
│
├── ctx: always entries injected inline (zero extra file load)
│   └── model selection, API shapes, error handling, preferences
│
├── facts.json injected (structured facts from past transcripts)
│
└── Previous session handoff injected from ~/.claude/handoffs/ (last 7 days)
```

| Component | What it does | Benefit |
|---|---|---|
| **MEMORY.md index** | Lean routing index | Claude knows what exists without loading everything |
| **Topic files** | Domain-specific memory, loaded on demand | Token cost scales with task, not total knowledge |
| **ctx: always injection** | Critical entries injected at session start without a file load | Always-relevant knowledge in context at near-zero cost |
| **Entry schema** (`importance`, `updated`, `ctx`) | Every entry tagged with priority, age, and scope | Enables automated decay and targeted projection |
| **Decay pruning** | `importance:low` + >90 days → archived, not deleted | Memory stays lean; history is preserved |
| **Dedup + contradiction archiving** | Consolidation merges duplicates, moves old contradicted entries to `archived.md` | No silent overwrites; memory stays coherent |
| **mem0 fact extraction** | Haiku reads session transcript at end, extracts and deduplicates facts | Structured facts persist without manual writes |
| **Session hooks** | Start injects full context; end persists state and warns on size | Every session starts warm; nothing lost between sessions |
| **/consolidate-memory** | Haiku agent merges, prunes, archives, surfaces cross-topic insights | Routine maintenance is automated and cheap |
| **Continuous learning** | Pattern extraction at session end + `/learn` for immediate capture | Non-trivial solutions accumulate as reusable skills |

**Entry schema** — every `##` header in every topic file carries four tags:

```
## Section Name | importance:high | updated: 2026-03-07 | ctx: always
```

`ctx` values: `always` · `agent` · `debug` · `scaffold` · `hook` · `pattern` · `project`

Entries tagged `ctx: always` are extracted and injected at session start without loading their full file. All other entries load only when their domain is active.

---

<details>
<summary><strong>Core Components</strong></summary>

### CLAUDE.md — The Global Brain

Always loaded. Sets operating mode, token minimization rules, memory routing, context fork strategy, before/after task checklists.

Key behaviors it enforces:
- No preamble, no restating the task, no post-task summaries
- No hedging filler: "it's worth noting", "importantly", "ensure that", "Additionally", "Furthermore"
- Read files at line ranges, not full files
- Load rules only when domain is active
- Compact after each major phase
- Write tests before marking any task done

### Rules System

Nine domain files, loaded on demand:

| File | Covers |
|---|---|
| `coding-style.md` | Max 300 lines/file, max 50 lines/function, naming conventions |
| `testing.md` | TDD mandatory, 80% coverage, consistency-critical pass^3 rule |
| `git-workflow.md` | Conventional commits, never commit to main |
| `security.md` | No hardcoded secrets, immune system pattern — appends every incident as a new rule |
| `performance.md` | Haiku/Sonnet/Opus tier selection, token minimization |
| `patterns.md` | `{ data, error, meta }` API shape, async/await, import ordering |
| `agents.md` | Delegation protocol, model selection per task type |
| `hooks.md` | Hook reference, event types, configuration |
| `design-system.md` | Stitch as source of truth, design-before-code contract |

### Context Modes

**Directory:** `~/.claude/contexts/`
Loaded on demand by CLAUDE.md when the work type changes. Zero token cost until triggered.

| Mode | Persona | Loaded when |
|---|---|---|
| Development | Senior full-stack engineer, TDD-first | implementing or building |
| Review | Principal engineer, correctness/security bias | reviewing code or a PR |
| Research | Technical analyst, explicit about unknowns | exploring or investigating |
| Testing | Senior QA engineer, adversarial mindset | writing tests or QA work |
| UI/UX Design | Senior product designer with frontend fluency | designing interfaces or flows |
| Architecture | Staff architect, trade-off obsessed | system design decisions |
| Planning | Engineering lead, scope-disciplined | sprint or project planning |
| Security | AppSec engineer, OWASP-anchored | security audits or threat modeling |
| Debugging | Systematic debugger, hypothesis-driven | diagnosing failures |
| DevOps | Senior DevOps/SRE, automation-first | CI/CD, infra, deployment |
| Refactor | Clean code engineer, DRY-obsessed | refactoring or reducing tech debt |
| Performance | Performance engineer, profiler-first | profiling, optimizing, benchmarking |
| Data | Senior data engineer, pipeline-safety bias | data pipelines, ML, analytics |
| Documentation | Technical writer with developer empathy | writing docs, runbooks, ADRs |

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

**Stop:**
- Codemap staleness check — warns if files were added/deleted since last commit

**SessionStart:**
- Injects project `CLAUDE.md` if found in cwd
- Loads retrieved mem0 facts
- Loads project `MEMORY.md`
- Loads last session notes (within 7 days)
- Runs system health check (zero context tokens, stderr only)

**SessionEnd:**
- Handoff summary written to `~/.claude/handoffs/YYYY-MM-DD-sessionid-project-session.tmp`
- mem0 fact extraction (Haiku via `claude -p`) — deduplicates against existing facts, auto-consolidates if >40
- Pattern extraction into topic files (`topics/*.md`, `insights.md`)
- Memory check — consolidates any topic file over 100 lines
- `session-end` step: 55s timeout. `handoff`/`check-memory`: 25s each. Outer hook ceiling: 60s.
- Runs after `/exit` completes — you never wait for it
- Failed steps written to `~/.claude/logs/mem0-retry.json` for retry on next session start

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
    ├── agents.md      ← Agent patterns, model selection
    └── archived.md    ← Decayed or contradicted entries (never deleted)
```

**Entry schema** — every `##` header carries four tags:
```
## Section Name | importance:high | updated: 2026-03-07 | ctx: always
```

| Tag | Values | Purpose |
|---|---|---|
| `importance` | `high/medium/low` | Prune priority — low pruned first |
| `updated` | `YYYY-MM-DD` | Decay tracking |
| `ctx` | `always`, `agent`, `debug`, `scaffold`, `hook`, `pattern`, `project` | Projection scope |

### Slash Commands

| Command | What it does |
|---|---|
| `/hey` | Session opener — shows last session recap + next step, or a dev joke on fresh start |
| `/tdd <task>` | RED → GREEN → IMPROVE with 80% coverage check |
| `/commit` | Conventional commit — stages specific files, shows message for approval |
| `/plan <task>` | 5-phase: research → plan → implement → review → verify |
| `/scaffold-project` | Full monorepo (Next.js + Supabase + pnpm workspaces + Turborepo) |
| `/breakdown <task>` | Decompose into subtasks with model tiers and parallelization flags |
| `/fork` | Initialize context in a new session (loads memory, session, CLAUDE.md) |
| `/review-pr` | Structured review: Blockers / Suggestions / Looks Good with file:line |
| `/pr` | Generate PR description — shows for approval before creating |
| `/consolidate-memory` | Haiku agent compresses all memory files |
| `/learn` | Extract and save a reusable pattern immediately |
| `/debug <issue>` | Systematic debugging workflow |
| `/e2e <flow>` | Playwright E2E tests — data-testid selectors, waitFor patterns, no flakiness |
| `/refactor-clean` | Find unused imports, duplicate logic, oversized files, dead code |
| `/standup` | `git log --since=yesterday` → Yesterday / Today / Blockers format |
| `/test-coverage` | Run coverage report, list files below 80%, write tests for highest-priority gaps |
| `/update-codemaps` | Scan project and write/update `.claude/codemap.md` |
| `/pipeline-init` | Set up the 6-layer test standard for a multi-stage pipeline |

### mem0 — Structured Fact Extraction

**File:** `hooks/memory-persistence/mem0.py`
**Auth:** Uses `claude -p` subprocess — no API key required for Claude Max subscribers.

mem0 is a lightweight memory extraction script that runs at session end via `SessionEnd` hook. It reads the session transcript, uses Haiku to extract memorable facts, deduplicates them against existing memory, and writes them to `facts.json`. At next session start, those facts are injected into context automatically.

**Auth modes** — auto-detected, no configuration needed:
- **Claude Max subscription** — `~/.config/anthropic/key` is empty or absent → `claude -p` uses keychain OAuth → subscription billing
- **API key users** — store key in `~/.config/anthropic/key` (chmod 600) → mem0 loads it automatically for `claude -p`

Never set `ANTHROPIC_API_KEY` in your shell environment — it will override keychain auth and bill unexpectedly.

**What it extracts:**
- User preferences and workflow decisions
- Technical choices (tools, frameworks, patterns selected)
- Project context (what you're building, constraints)
- Problems solved or discovered
- Session summary + next step (written to handoff file)

**Cost:** mem0 uses `claude-haiku-4-5-20251001` — cheapest available model. Extraction runs on the last 120 messages. Subscription users: zero API cost.

### System Health Check

**File:** `hooks/memory-persistence/health-check.sh`
**Runs:** automatically on every `SessionStart` — silent when healthy, warns to stderr on issues.

| Check | What it catches |
|---|---|
| mem0 retry | Re-runs steps that failed/timed out last session |
| `settings.json` schema | Missing `matcher` fields, malformed hook objects |
| Hook command paths | Scripts that have been moved, deleted, or lost execute permission |
| Shell script syntax | `bash -n` on every `.sh` in the hooks directory |
| `mem0.py` syntax | Python syntax errors that would silently break fact extraction |
| Auth mode | Subscription (keychain) or API key — both valid, neither warns |
| `bun` installed | Required for browse and stitch skills |
| `jq` installed | Required by hooks and scripts |
| `node` installed | Required by browse skill |
| `node_modules` per skill | Warns with `bun install` command if missing |
| Playwright browsers | Checks `ms-playwright` cache for skills that use Playwright |
| `facts.json` integrity | Corrupted JSON that would break memory retrieval |
| mem0 hooks wired | Verifies SessionStart/SessionEnd/Stop all point to correct scripts |
| Stitch API key | Warns with setup instructions if missing |
| Claude Code version | Installed vs latest (cached 24h, background fetch from npm) |

Run manually at any time:
```bash
~/.claude/hooks/memory-persistence/health-check.sh
# No output = all healthy
```

### Skills

#### `skills/browse/` — Persistent Browser Daemon

A Bun HTTP server that keeps a Playwright browser alive across multiple Claude tool calls. Invoked via `/browse`.

**Why:** cold-starting a browser per command loses cookies, auth sessions, and adds latency. The daemon preserves session state across 20+ commands — log in once, then navigate/interact freely.

**Setup:**
```bash
cd ~/.claude/skills/browse
bun install
bunx playwright install chromium
```

Start before using `/browse`:
```bash
bun run server.ts &
```

**Key features:**
- Named browser contexts (`ctx:admin`, `ctx:guest`) — test multiple auth states simultaneously
- Video recording (`record:start` / `record:stop`) for multi-step QA flows
- `eval <js>` — evaluate JavaScript in page context
- Idle timeout — auto-shuts down when inactive

#### `skills/stitch/` — AI UI Generation

A Node.js skill that generates, iterates, and tracks UI screens using Google Stitch. Invoked via `/stitch`. Claude fires it autonomously before writing any component code.

**Setup:**
```bash
cd ~/.claude/skills/stitch && npm install

# Store Google Stitch API key (get from stitch.withgoogle.com → Settings → API Keys)
mkdir -p ~/.config/stitch
echo "your-key-here" > ~/.config/stitch/key
chmod 600 ~/.config/stitch/key
```

**Autonomous workflow:**
```
You: "build the login page"
Claude: checks design/stitch/manifest.json
        → no login screen → stitch auto "login page with email and password"
        → reads generated HTML → implements component matching the design
```

**Manual commands:**
```bash
stitch init --auto                          # propose style config from project docs
stitch auto "a checkout flow with order summary"
stitch variants login --range REIMAGINE --count 3
stitch list
```

#### `bin/ctx-exec` — Large Output Filter

Filters command output before it enters the context window. Use when a command produces >5KB output.

```bash
~/.claude/bin/ctx-exec "failing tests" pnpm test
~/.claude/bin/ctx-exec "error warning" npm run build
~/.claude/bin/ctx-exec "open issues" gh issue list --limit 50
```

#### `bin/bun-exec.sh` — Parallel HTTP Batching

Batches 3+ independent HTTP/API calls into a single tool invocation, eliminating per-call context overhead.

```bash
cat > /tmp/task.ts << 'EOF'
const [a, b, c] = await Promise.all([
  fetch("https://api.example.com/a").then(r => r.json()),
  fetch("https://api.example.com/b").then(r => r.json()),
  fetch("https://api.example.com/c").then(r => r.json()),
]);
console.log(JSON.stringify({ data: { a, b, c }, error: null }));
EOF
~/.claude/bin/bun-exec.sh /tmp/task.ts
```

### Plugins (Active)

| Plugin | Purpose |
|---|---|
| `hookify` | GUI for creating and managing hooks |
| `context7` | Up-to-date library documentation in context |
| `mgrep` | Semantic search — replaces `grep -r`, ~50% token reduction |
| `pyright-lsp` | Python type checking on edit |

TypeScript LSP, code-review, and security-guidance plugins are scoped **per package** in per-project `settings.json` — only loaded where needed.

</details>

---

## OMS — One-Man-Show (v0.6)

> A multi-agent discussion engine that simulates a full product team inside a single Claude session. When the decision matters, don't ask one AI — convene a room.

OMS solves the single-perspective problem. On complex or cross-domain questions, a single AI answer is a single blind spot. OMS activates a roster of specialized personas — each arguing from their own domain — runs structured rounds, then produces a traceable synthesis with `action_items[]`. Minority positions are steelmanned. Reopen conditions are defined. The output isn't an AI answer; it's a decision audit trail.

### What's new in v0.6

- **Milestone hierarchy** — projects have milestones; milestones have tasks. Work is always scoped to one milestone at a time.
- **Step 0 queue check** — before any execution, OMS checks if there are already cleared tasks in the queue and runs them first. No duplicate elaboration.
- **One-milestone exec** — `/oms exec` now focuses on a single milestone per discussion. Cleaner scope, faster decisions.
- **PM out of exec** — C-suite only in exec discussions. Product Manager participates in engineering rounds, not strategic direction.
- **CRO always active in exec** — revenue impact is evaluated on every strategic discussion.
- **Auto-confirm cross-milestone contracts** — dependency contracts between milestones confirm automatically on the happy path, no CEO gate required.
- **New agents** — content-strategist, ux-researcher, executive-briefing-agent.
- **oms-work replaces oms-implement** — unified execution engine with schema validation, cost tracking, and Discord integration.

### When to use it

- Architecture decisions that cut across security, performance, and delivery
- High-stakes changes where a wrong call is expensive to reverse
- Research questions where the right framework is itself unknown
- Strategic product direction where engineering, product, and business pull differently

For routine tasks — a bug fix, a simple feature — just ask Claude directly. OMS is for decisions where you'd normally call a meeting.

### Skill suite

| Command | Phase | What it does |
|---|---|---|
| `/oms-start` | Setup | Initialize OMS for a project — run once before anything else |
| `/oms <intent>` | Discussion | Run a multi-agent discussion, get a synthesis with `action_items[]` |
| `/oms exec` | Strategic | C-suite milestone planning — CTO, CRO, CLO, CPO, CTO (no PM) |
| `/oms-work` | Execution | Execute cleared tasks in the queue with full validation |
| `/oms-capture` | Learning | Capture a real failure as a training scenario |
| `/oms-train [ids]` | Maintenance | Run training scenarios against agent personas |
| `/oms audit` | Maintenance | Token and context audit across OMS system |
| `/oms-tool` | Improvement | External research scan (GitHub/Reddit/HN) to identify system improvements |

### Hierarchy

```
Project
└── Milestone (one at a time)
    └── Tasks (cleared → in progress → done)
```

`/oms exec` plans the current milestone. `/oms` discusses tasks within it. `/oms-work` executes the cleared queue.

### Modes

**Engineering** (default) — technical tasks. The system classifies complexity and activates only the personas the task warrants. A button label change gets one agent. A database migration gets five.

**Research** — activated when the task requires domain expertise rather than engineering judgment. Produces a framework map of where the field agrees, where it conflicts, and what remains unknown.

**Exec** — C-suite milestone planning. CTO, CRO, CLO, CPO discuss scope, dependencies, and delivery order. Produces milestone roadmap and updates project direction. PM is not in exec — they participate in engineering rounds only.

### Discussion → Execution

OMS produces a decision. `/oms-work` executes it.

`/oms` locks scope and outputs `action_items[]` with assignees, rationale, and reopen conditions. `/oms-work` picks up the cleared task queue, dispatches items as parallel agents, runs the full test suite, and validates delivery — CTO checks code quality, QA checks requirement fidelity. Nothing closes until both sign off.

### Workflow

```bash
# Once per project
/oms-start

# Plan the current milestone (C-suite, no PM)
/oms exec Q2 milestone — payments and user onboarding

# Settle a technical decision within the milestone
/oms how should we handle optimistic locking for concurrent reservations

# Execute cleared tasks
/oms-work

# If an agent behaved badly, capture it
/oms-capture

# Research mode — domain knowledge questions
/oms how should we design the question bank to maximize honest self-reflection
```

### Project setup

`/oms-start` ingests any starting material — CLAUDE.md, README, PRD, raw notes — asks which departments are active, runs a short intake questionnaire, and generates the context files OMS needs to route tasks correctly.

OMS registers projects in `~/.claude/oms-config.json`. Without `/oms-start`, `/oms` will refuse to run.

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
- Haiku — repetitive tasks, worker agents, memory consolidation (~20x cheaper than Sonnet)
- Sonnet — default for 90% of coding tasks
- Opus — first attempt failed, 5+ files, architectural decisions, security-critical

---

## Setup

Choose your platform:
- [macOS](#macos-setup)
- [Windows (via WSL2)](#windows-setup-via-wsl2)

> **Note:** Claude Code has no native Windows binary. Windows users must run it inside WSL2 (Ubuntu). All bash hooks and scripts work inside WSL.

---

<details>
<summary><strong>macOS Setup</strong></summary>

### Step 1 — Install Claude Code CLI

Go to [claude.ai/code](https://claude.ai/code) and follow the install instructions for macOS.

Verify it works:
```bash
claude --version
```

### Step 2 — Install prerequisites

```bash
# Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Required tools
brew install jq          # JSON parsing used by all hooks
brew install gh          # GitHub CLI (for /pr, /review-pr workflows)
brew install node        # Node.js — for prettier + tsc
brew install python3     # Python 3 — for mem0 fact extraction

# Bun — for browse and stitch skills
curl -fsSL https://bun.sh/install | bash
```

Verify:
```bash
jq --version && gh --version && node --version && python3 --version && bun --version
```

### Step 3 — Back up your existing ~/.claude (if any)

```bash
[ -d ~/.claude ] && mv ~/.claude ~/.claude.backup && echo "Backed up to ~/.claude.backup"
```

### Step 4 — Clone this repo into ~/.claude

```bash
git clone https://github.com/anhnguyensynctree/unified-claude-system.git ~/.claude
```

### Step 5 — Make hooks executable

```bash
chmod +x ~/.claude/hooks/memory-persistence/*.sh
chmod +x ~/.claude/bin/*
```

### Step 6 — Configure mem0 auth

mem0 uses `claude -p` subprocess — no separate API key needed for Claude Max subscribers.

**Claude Max subscription (default):**
```bash
# Leave ~/.config/anthropic/key empty — mem0 uses keychain OAuth automatically
mkdir -p ~/.config/anthropic
touch ~/.config/anthropic/key   # empty file is correct
chmod 600 ~/.config/anthropic/key
```

**API key users (no subscription):**
```bash
mkdir -p ~/.config/anthropic
echo "sk-ant-..." > ~/.config/anthropic/key
chmod 600 ~/.config/anthropic/key
```

Never set `ANTHROPIC_API_KEY` in `.zshrc` or `.bashrc` — it will override keychain auth for all `claude -p` calls.

### Step 7 — Initialize your global memory

```bash
mkdir -p ~/.claude/projects/-Users-$(whoami)/memory/topics
```

Create the memory index file:
```bash
cat > ~/.claude/projects/-Users-$(whoami)/memory/MEMORY.md << 'EOF'
# Memory Index

Always loaded at session start. Read the Topic Index and load relevant files before starting work.

## User Preferences | importance:high
- [Add your preferences here — e.g. "Prefers pnpm over npm"]

## Active Context | importance:high
- Setup complete

## Topic Index | importance:high
Load with Read tool when task domain matches:

| When... | Load |
|---|---|
| Hitting errors, non-obvious fixes | topics/debugging.md |
| Architecture or API decisions | topics/patterns.md |
EOF
```

### Step 8 — Install Claude Code plugins

Open Claude Code and run:
```
/plugins
```

Install:
- `hookify@claude-plugins-official`
- `context7@claude-plugins-official`
- `mgrep@Mixedbread-Grep`
- `pyright-lsp@claude-plugins-official` (if you use Python)

### Step 9 — Set up browse skill (optional — for live web testing)

```bash
cd ~/.claude/skills/browse
bun install
bunx playwright install chromium
```

### Step 10 — Set up Stitch skill (optional — for AI UI generation)

The `/stitch` skill requires Node.js dependencies and a Google Stitch API key.

```bash
# Install dependencies
cd ~/.claude/skills/stitch && npm install

# Store Stitch API key (get from stitch.withgoogle.com → Settings → API Keys)
mkdir -p ~/.config/stitch
echo "your-key-here" > ~/.config/stitch/key
chmod 600 ~/.config/stitch/key
```

Optional — make `stitch` available as a global CLI:
```bash
ln -sf ~/.claude/skills/stitch/stitch.mjs ~/bin/stitch
```

### Step 11 — Verify the system

Run the health check:
```bash
~/.claude/hooks/memory-persistence/health-check.sh
# No output = all healthy
```

Open Claude Code and run `/hey`. You should see either a session recap or a dev joke. Either output means the system is running correctly.

</details>

---

<details>
<summary><strong>Windows Setup (via WSL2)</strong></summary>

Claude Code runs inside WSL2 on Windows. All bash hooks, scripts, and tools run in the Linux environment.

### Step 1 — Enable WSL2

Open PowerShell as Administrator and run:
```powershell
wsl --install
```

This installs WSL2 with Ubuntu by default. Restart your machine when prompted. Open the Ubuntu app and complete setup.

### Step 2 — Install Claude Code CLI inside WSL

Open your Ubuntu terminal and follow the Linux install instructions at [claude.ai/code](https://claude.ai/code).

> All remaining steps run **inside the Ubuntu/WSL terminal**, not in PowerShell or CMD.

### Step 3 — Install prerequisites inside WSL

```bash
sudo apt update && sudo apt upgrade -y

# Core tools
sudo apt install -y jq python3 python3-pip gh

# Node.js
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs

# Bun
curl -fsSL https://bun.sh/install | bash
```

### Step 4 — Back up and clone

```bash
[ -d ~/.claude ] && mv ~/.claude ~/.claude.backup
git clone https://github.com/anhnguyensynctree/unified-claude-system.git ~/.claude
```

### Step 5 — Make hooks executable

```bash
chmod +x ~/.claude/hooks/memory-persistence/*.sh
chmod +x ~/.claude/bin/*
```

### Step 6 — Disable the macOS notification hook

Find and delete the `Notification` block in `settings.json` — it uses `osascript` which is macOS-only:

```bash
nano ~/.claude/settings.json
```

Remove:
```json
"Notification": [
  {
    "matcher": "",
    "hooks": [
      {
        "type": "command",
        "command": "osascript -e 'display notification \"Claude needs your attention\" with title \"Claude Code\"' 2>/dev/null || true"
      }
    ]
  }
],
```

> Optional: replace with `notify-send` (requires `sudo apt install -y libnotify-bin`).

### Step 7 — Configure mem0 auth

```bash
mkdir -p ~/.config/anthropic

# Claude Max subscription (empty file = keychain OAuth):
touch ~/.config/anthropic/key && chmod 600 ~/.config/anthropic/key

# API key users (no subscription):
# echo "sk-ant-..." > ~/.config/anthropic/key && chmod 600 ~/.config/anthropic/key
```

### Step 8 — Initialize global memory

On Linux/WSL, your home path is `/home/username` — encoded as `-home-username`:

```bash
mkdir -p ~/.claude/projects/-home-$(whoami)/memory/topics

cat > ~/.claude/projects/-home-$(whoami)/memory/MEMORY.md << 'EOF'
# Memory Index

## User Preferences | importance:high
- [Add your preferences here]

## Active Context | importance:high
- Setup complete

## Topic Index | importance:high
| When... | Load |
|---|---|
| Hitting errors, non-obvious fixes | topics/debugging.md |
| Architecture or API decisions | topics/patterns.md |
EOF
```

### Step 9 — Install plugins and verify

Open Claude Code and run `/plugins`. Install:
- `hookify@claude-plugins-official`
- `context7@claude-plugins-official`
- `mgrep@Mixedbread-Grep`
- `pyright-lsp@claude-plugins-official`

Run the health check:
```bash
~/.claude/hooks/memory-persistence/health-check.sh
```

Open Claude Code and run `/hey` to confirm the system is working.

</details>

---

<details>
<summary><strong>Verify Your Installation</strong></summary>

```bash
# 1. Hooks are executable
ls -la ~/.claude/hooks/memory-persistence/
# All .sh files should show -rwxr-xr-x

# 2. Memory directory exists
ls ~/.claude/projects/
# Should show your encoded home path directory

# 3. MEMORY.md is readable
cat ~/.claude/projects/*/memory/MEMORY.md

# 4. Auth configured (one of:)
wc -c ~/.config/anthropic/key   # 0 = subscription mode; >0 = API key mode

# 5. Prerequisites installed
jq --version && node --version && python3 --version && bun --version

# 6. System health check passes
~/.claude/hooks/memory-persistence/health-check.sh
# No output = all healthy
```

</details>

---

## Keeping Your Config Up to Date

```bash
cd ~/.claude
git pull origin main
```

Your `projects/` directory (personal memory and sessions) is gitignored — never touched by a pull.

Review diffs before pulling if you've customized `settings.json` or `CLAUDE.md`:
```bash
cd ~/.claude
git fetch origin
git diff origin/main -- settings.json CLAUDE.md
```

---

## Workflows

```bash
# Start every session
/hey

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

**OMS workflow:**
```bash
# Initialize OMS for a new project
/oms-start

# Plan the current milestone (C-suite discussion)
/oms exec Q2 milestone — auth and billing

# Discuss a specific technical decision
/oms how should we handle token refresh for mobile clients

# Execute the cleared task queue
/oms-work
```

**UI workflow — design before code:**
```bash
/stitch init --auto
/stitch "dashboard with sidebar and activity feed"
/stitch update dashboard "make sidebar collapsible"
/stitch variants login --range REIMAGINE --count 3
```

---

<details>
<summary><strong>Iterating and Contributing</strong></summary>

This repo **is** `~/.claude`. Updating the system:

```bash
cd ~/.claude
git add rules/testing.md
git commit -m "feat(testing): raise coverage threshold to 85%"
git push
```

PRs and issues welcome. If you adapt this for a different stack, open a PR — especially for non-Next.js/Supabase scaffold variants.

</details>

---

## Community

If this system improved your Claude Code workflow, a star helps others find it.

**Contributions especially welcome for:**
- Stack-specific scaffold variants (Rails, Django, Go, Rust)
- Additional OMS agent personas
- Context mode files for domains not yet covered
- Windows/WSL2 setup improvements
