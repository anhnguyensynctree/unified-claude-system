# unified-claude-system

> A stateful, opinionated Claude Code harness that makes every session start warm — and an autonomous multi-agent pipeline (OMS) that plans, executes, and validates software delivery without manual re-briefing.
> Drop it into `~/.claude`. Claude becomes a development partner backed by a full virtual product team.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/requires-Claude%20Code%20CLI-blue)](https://claude.ai/code)

**One-line install (macOS):**
```bash
git clone https://github.com/anhnguyensynctree/unified-claude-system.git ~/.claude
```
→ [macOS setup](#macos-setup) · [Windows / WSL2](#windows-setup-via-wsl2)

**New here? One prompt does everything:**
```
Set up my global Claude system from https://github.com/anhnguyensynctree/unified-claude-system:
1. Clone it into ~/.claude
2. Run the full setup for my platform (hooks executable, memory initialized, prerequisites checked)
3. Verify everything works: health check, hooks wired, MEMORY.md readable, /hey test
4. Report green/red for each check and fix anything broken
5. Confirm when I'm ready to start with /hey
```

---

## The Problem

Every Claude Code session starts cold. You re-explain your stack, your conventions, what you built yesterday. The same instructions — every single session.

**This system fixes that.** Drop it into `~/.claude` and Claude becomes a stateful development partner:

- **Persistent memory** — decisions, patterns, and project context carry across sessions automatically
- **Enforced conventions** — rules load via hooks, not per-prompt engineering
- **14 context modes** — Claude shifts persona based on what you're doing: dev, test, review, security, debug, plan, ui-ux, architecture, devops, refactor, performance, data, docs, research
- **Automated quality gates** — `console.log`, TypeScript errors, test coverage enforced in real time
- **OMS** — autonomous multi-agent pipeline: plans milestones, executes tasks, validates delivery, posts briefings to Discord without manual re-briefing
- **Cost-tiered routing** — free OpenRouter models for 90%+ of task execution; Sonnet for milestone gates; Opus for architecture decisions and C-suite planning

```
Without this:   "Use pnpm. TDD. Conventional commits. No console.log. 80% coverage minimum."
                "Plan this milestone. Write the tasks. Execute them. Validate delivery."
With this:      Claude already knows. Every session, from the first message.
                OMS handles the rest — plan → execute → validate → brief, autonomously.
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
├── oms-config.json              ← OMS project registry + model_overrides
│
├── rules/                       ← Domain-specific rules (loaded on demand)
│   ├── coding-style.md          ← 300-line max, naming, no console.log
│   ├── testing.md               ← TDD mandatory, 80% coverage, E2E 5-category
│   ├── git-workflow.md          ← Conventional commits, CI required on every PR
│   ├── security.md              ← Secrets policy, API key hard-block, incident log
│   ├── performance.md           ← Model tiers, token minimization, ctx-exec rules
│   ├── patterns.md              ← API shape, async, import order, bun-exec
│   ├── agents.md                ← Delegation protocol, model selection table
│   ├── hooks.md                 ← Hook reference, event types, config
│   ├── design-system.md        ← Stitch as source of truth, design-before-code
│   └── vercel.md                ← Canonical URL, deploy pattern, env vars
│
├── contexts/                    ← Mode-specific prompts (loaded on demand)
│   ├── dev.md, review.md, research.md, test.md
│   ├── ui-ux.md, architecture.md, plan.md, security.md
│   ├── debug.md, devops.md, refactor.md, performance.md
│   └── data.md, docs.md
│
├── hooks/
│   └── memory-persistence/
│       ├── session-start.sh     ← Injects memory + context at session open
│       ├── session-end.sh       ← Codemap staleness check on every stop
│       ├── pre-compact.sh       ← Priority-tiered XML snapshot before compaction
│       ├── mem0-extract.sh      ← Fact extraction + handoff at SessionEnd
│       └── health-check.sh      ← 14-check system integrity validator
│
├── bin/
│   ├── ctx-exec                 ← Filters large command output before context
│   ├── bun-exec.sh              ← Batch 3+ parallel HTTP/API calls into one call
│   ├── discord-bot.py           ← OMS Discord integration (!work, !queue, etc.)
│   ├── oms-work.py              ← OMS task execution orchestrator
│   └── oms_work/                ← Execution engine package (9 modules)
│       ├── config.py            ← Constants, paths, model maps, validator roles
│       ├── queue.py             ← Queue parsing, status, dependency tracking
│       ├── worktree.py          ← Git worktree lifecycle
│       ├── llm.py               ← Claude CLI + LiteLLM proxy routing
│       ├── prompts.py           ← Task prompt builders (impl/research/exec)
│       ├── agent.py             ← WRITE/RUN/DONE loop, smart error extraction
│       ├── validate.py          ← Validators, verify, scenario coverage, verdicts
│       ├── browse.py            ← Browse daemon visual QA
│       └── metrics.py           ← Cost tracking, budget, task metrics
│
├── agents/                      ← OMS agent personas + contracts
│   ├── router/, synthesizer/, trainer/, task-elaboration/
│   ├── facilitator/, path-diversity/, context-optimizer/
│   ├── verification/, executive-briefing-agent/
│   ├── cto/, cpo/, cro/, clo/, cfo/
│   ├── engineering-manager/, backend-developer/, frontend-developer/
│   ├── qa-engineer/, product-manager/, content-strategist/, ux-researcher/
│   ├── oms-work/                ← Task schema and execution contracts
│   └── training/                ← Scenario suite (67+ scenarios)
│
├── skills/
│   ├── browse/                  ← Persistent Playwright browser daemon (/browse)
│   ├── stitch/                  ← AI UI generation via Google Stitch (/stitch)
│   ├── oms/                     ← Multi-agent discussion engine (/oms)
│   ├── oms-start/               ← Initialize OMS for a project (/oms-start)
│   ├── oms-exec/                ← Strategic milestone planning (/oms exec)
│   ├── oms-work/                ← Execute cleared task queue (/oms-work)
│   ├── oms-audit/               ← System health audit (/oms audit)
│   ├── oms-capture/             ← Capture failures as training scenarios
│   ├── oms-tool/                ← External research for system improvement
│   ├── oms-train/               ← Run training scenarios against personas
│   └── continuous-learning/     ← Pattern extraction at session end (/learn)
│
├── handoffs/                    ← Session handoff files (one per session)
└── projects/[encoded-path]/memory/
    ├── MEMORY.md                ← Always-loaded index (<80 lines)
    ├── facts.json               ← Structured facts from session transcripts
    ├── insights.md              ← Cross-topic patterns from consolidation
    └── topics/                  ← Domain memory files (loaded on demand)
```

---

## OMS — One-Man-Show

> **One AI is one blind spot.** OMS convenes a virtual product team inside a single Claude session — each persona argues from its own domain, rounds are structured, and the output is a traceable decision with `action_items[]`, assignees, and reopen conditions. Not an AI answer. A decision audit trail.

### Signature

OMS is defined by five properties that distinguish it from a plain multi-agent prompt:

**1. Scope before execution.** `/oms exec` locks the milestone. `/oms` settles decisions within it. `/oms-work` executes. No step can skip ahead.

**2. Model routing is hook-enforced, not trusted.** Every Agent call in OMS is validated by `enforce-oms-model.sh` (PreToolUse hook) against `oms-config.json`. Wrong model = blocked call. C-suite runs Opus. Infrastructure agents (Router/Facilitator/Synthesizer) run their own configured models regardless of context.

**3. Structured rounds with convergence detection.** Agents don't just "discuss" — they go through pre-mortem, path diversity seeding, facilitated rounds with position delta tracking, livelock detection, and Delphi distribution. A Pre-Facilitator (Haiku, cheap) short-circuits full facilitation when consensus is already present.

**4. Validation is mandatory and multi-layer.** Nothing is "done" until: quality checks pass (deterministic), Verify commands pass (local bash), scenario coverage is confirmed (fuzzy match), and CTO + QA both issue signed-off verdicts (LLM judges). Any layer failure triggers structured retry with extracted error context — not a generic retry.

**5. The system learns.** Failures are captured as structured training scenarios (`/oms-capture`). Scenarios run against personas (`/oms-train`). Patterns that emerge are written back into agent personas. The agent roster improves across runs.

---

### Part 1 — `/oms-start` · Project Initialization

Ingests any starting material (PRD, CLAUDE.md, raw notes, idea) and generates the context files OMS needs to route tasks correctly.

**What it produces:**
- `product-direction.ctx.md` — milestone list, product vision, active departments
- `company-hierarchy.md` — which personas are active for this project
- OMS registration in `~/.claude/oms-config.json`

**When to run:** once per project, before any `/oms` or `/oms exec` call. `/oms` refuses to run without a registered project.

```bash
/oms-start
```

---

### Part 2 — `/oms exec` · Strategic Milestone Planning

C-suite convenes to select and plan the current milestone. Produces FEATURE draft blocks ready for elaboration.

**Roster:** CPO (lead), CTO, CRO, CLO, CFO. PM is excluded — PM participates in engineering rounds, not strategic direction.

**Model:** Opus (enforced). C-suite planning is the spec quality foundation — Opus catches edge cases that Sonnet misses at this stage.

**What it produces:** FEATURE-NNN draft blocks appended to `cleared-queue.md` as `Status: draft`, ready for `/oms FEATURE-NNN` elaboration.

**Auto-selection:** CPO reads `product-direction.ctx.md` + `cleared-queue.md` and proposes the highest-priority milestone with no queued coverage. No manual selection needed.

```bash
/oms exec                               # CPO auto-selects next milestone
/oms exec Q2 milestone — auth + billing # force a specific milestone
/oms exec retro                         # retrospective: re-orient product direction
```

---

### Part 3 — `/oms <intent>` · Engineering Discussion Engine

Runs a structured multi-agent discussion for any technical decision, research question, or high-stakes change.

**Model routing:**

| Agent | Model | Role |
|---|---|---|
| Router | haiku | Classifies tier, activates relevant personas |
| Path Diversity | sonnet | Seeds structurally distinct paths before Round 1 |
| Pre-Facilitator | haiku | Checks convergence — short-circuits if consensus present |
| Full Facilitator | sonnet | Stage-Gate 2, Delphi distribution, livelock detection |
| Synthesizer | sonnet → opus (escalation) | Produces `action_items[]` with traceable rationale |
| Trainer | sonnet | Coaching notes + lesson candidates post-synthesis |
| Validator | haiku | Pass/fail quality gate on output structure |

**Opus escalation:** Synthesizer earns Opus only when Facilitator signals `livelock_signal: "cycling"` or `"deadlock"`, or 5+ agents reach Round 2+ with no convergence. Enforced by hook.

**Tier classification:**
- Tier 0/1: single-department, clear scope → 1-3 agents
- Tier 2+: 2+ departments must agree on a shared artifact → full round structure + CEO gate if needed

**Output:** synthesis with `exec_decision` (What/Constraints/OpenToTeams), `action_items[]` with assignees and reopen conditions, `trainer_notes`, `lesson_candidates`.

```bash
/oms how should we handle optimistic locking for concurrent reservations
/oms research what logging patterns work best for distributed tracing
/oms should we use feature flags or a separate staging tenant for the new billing system
```

---

### Part 4 — `/oms-work` · Autonomous Task Execution Pipeline

Picks up the cleared task queue and executes each task in an isolated git worktree with full validation before commit.

**Model routing per task:**

| Model-hint | Model | Mode | When |
|---|---|---|---|
| `qwen-coder` | Qwen 3 Coder | Agent loop | Impl tasks, primary free model |
| `qwen` | Qwen 3.6 Plus 1M | Agent loop / one-shot | Research primary, impl fallback |
| `gpt-oss` | GPT-OSS 120B | Agent loop | Impl escalation |
| `nemotron` | Nemotron 3 Super | Agent loop | Impl escalation |
| `gemma` | Gemma 3 27B | One-shot | Validation fallback only |
| `llama` | Llama 3.3 70B | One-shot | Validation fallback only |
| `stepfun` | StepFun 3.5 | One-shot | Validation fallback only |
| `sonnet` | Claude Sonnet 4.6 | Agent loop | Gate tasks, infra-critical |
| `haiku` | Claude Haiku 4.5 | Text-only | Validation primary (all tasks) |

**Execution pipeline per task:**

```
cleared-queue.md task
        │
  ┌─ AGENT LOOP ──────────────────────────────────────────────┐
  │ resolve_model() → model from task's Model-hint            │
  │ WRITE/RUN/DONE protocol in isolated git worktree          │
  │ Agent-capable: multi-step loop, adaptive max_steps        │
  │ One-shot: single call + file extraction                   │
  │ Early exit: auto-DONE when all artifacts exist on disk    │
  └───────────────────────────────────────────────────────────┘
        │
  ┌─ QUALITY CHECKS (deterministic) ─────────────────────────┐
  │ File size ≤ 300 lines · No console.log · No secrets      │
  │ Prettier auto-format · Pyright type check                 │
  └───────────────────────────────────────────────────────────┘
        │
  ┌─ VERIFY COMMANDS ─────────────────────────────────────────┐
  │ Runs task's Verify field (pytest/vitest/jest/tsc/eslint)  │
  │ Smart error extraction → structured retry prompt          │
  └───────────────────────────────────────────────────────────┘
        │
  ┌─ SCENARIO COVERAGE ───────────────────────────────────────┐
  │ Fuzzy GIVEN/WHEN/THEN match against test file content     │
  │ Gaps reported to validators                               │
  └───────────────────────────────────────────────────────────┘
        │
  ┌─ VALIDATION (LLM judges) ─────────────────────────────────┐
  │ haiku primary · free models as fallback                   │
  │ impl: dev → qa → em  |  research: researcher → cpo + cro │
  │ QA: per-scenario verdicts, auto-retry on lazy approval    │
  │ Dev: scenario → test function mapping required            │
  │ EM: 5-point checklist (spec/scenarios/tests/size/TODO)    │
  └───────────────────────────────────────────────────────────┘
        │
  ┌─ COMMIT + MERGE ──────────────────────────────────────────┐
  │ git commit in worktree → merge to main → remove worktree  │
  │ Failure: branch kept, Discord notified                    │
  └───────────────────────────────────────────────────────────┘
        │
  ┌─ MILESTONE GATE (Sonnet, once per milestone) ─────────────┐
  │ Re-runs ALL Verify on main · Full E2E suite               │
  │ Screenshots collected → Discord milestone thread          │
  └───────────────────────────────────────────────────────────┘
```

**Determinism guarantee:**

| Layer | Mechanism | Reliable? |
|---|---|---|
| Worktree isolation | Python orchestrator | Deterministic |
| Smart error extraction | Pattern matching (pytest/vitest/jest/tsc/eslint) | Deterministic |
| Quality checks | Local Python code | Deterministic |
| Verify commands | Local bash | Deterministic |
| Scenario coverage | Text fuzzy match | Deterministic |
| LLM validators | haiku + retry on lazy approval | High |
| Milestone gate | Full suite on main | Deterministic |

---

### Part 5 — `/oms-capture` + `/oms-train` · Failure Learning Loop

When an agent behaves badly — wrong model, scope creep, skipped validation, bad synthesis — capture it immediately.

**`/oms-capture`:** structures the real failure as a training scenario (GIVEN/WHEN/THEN) and appends it to `agents/training/scenarios/`. Each scenario has a deterministic pass/fail verdict criteria.

**`/oms-train [ids]`:** runs scenarios against agent personas. Failing scenarios surface which persona or routing rule needs updating. Fixes write back into `persona.md` files.

**`/oms-train --failing`:** only runs scenarios that have failed in a previous run — fast iteration on active regressions.

```bash
/oms-capture                      # capture the failure just observed
/oms-train                        # run all scenarios
/oms-train 042 055 068            # run specific scenarios
/oms-train --failing              # run only previously-failing scenarios
```

---

### Part 6 — `/oms audit` · System Health

Full audit across the four OMS pillars: discussion engine quality, execution fidelity, training coverage, and persona enforcement.

Distinct from the SessionStart health check (which is system integrity). The OMS audit checks semantic correctness — are personas reasoning correctly, are validators actually strict, are training scenarios covering real failure modes?

```bash
/oms audit
```

---

### OMS Workflow

```bash
# Once per project
/oms-start

# Plan the current milestone (C-suite, Opus)
/oms exec

# Settle a technical decision within the milestone (Engineering discussion)
/oms how should we handle token refresh for mobile clients

# Execute cleared tasks
/oms-work

# Capture a failure immediately after observing it
/oms-capture

# Improve the system
/oms-train --failing
```

---

## Core System Components

<details>
<summary><strong>CLAUDE.md — The Global Brain</strong></summary>

Always loaded. Sets operating mode, token minimization rules, memory routing, context fork strategy, before/after task checklists.

Key behaviors it enforces:
- No preamble, no restating the task, no post-task summaries
- No hedging: "it's worth noting", "importantly", "ensure that", "Additionally", "Furthermore"
- Read files at line ranges, not full files
- Load rules only when domain is active
- Write tests before marking any task done
- Use EnterPlanMode for any task touching 3+ files (enforced by hook)

</details>

<details>
<summary><strong>Rules System</strong></summary>

Nine domain files, loaded on demand by CLAUDE.md when the work type matches:

| File | Covers |
|---|---|
| `coding-style.md` | 300-line max, 50-line function max, naming conventions |
| `testing.md` | TDD mandatory, 80% coverage, 5-category E2E, consistency-critical pass^3 |
| `git-workflow.md` | Conventional commits, never commit to main, CI required on every PR |
| `security.md` | No secrets, Anthropic API key hard-block, incident immune system |
| `performance.md` | Haiku/Sonnet/Opus tier table, token minimization, ctx-exec always |
| `patterns.md` | `{ data, error, meta }` API shape, async/await, bun-exec for 3+ HTTP calls |
| `agents.md` | Delegation protocol, explicit `model:` on every Agent call |
| `hooks.md` | Hook event reference, configuration, per-project override pattern |
| `design-system.md` | Stitch as source of truth, generate screen before writing component code |

</details>

<details>
<summary><strong>Context Modes</strong></summary>

**Directory:** `~/.claude/contexts/` — loaded on demand, zero token cost until triggered.

| Mode | Loaded when |
|---|---|
| Development | implementing or building |
| Review | reviewing code or a PR |
| Research | exploring or investigating |
| Testing | writing tests or QA work |
| UI/UX Design | designing interfaces or flows |
| Architecture | system design decisions |
| Planning | sprint or project planning |
| Security | security audits or threat modeling |
| Debugging | diagnosing failures |
| DevOps | CI/CD, infra, deployment |
| Refactor | reducing tech debt |
| Performance | profiling, optimizing, benchmarking |
| Data | data pipelines, ML, analytics |
| Documentation | writing docs, runbooks, ADRs |

</details>

<details>
<summary><strong>Hooks System</strong></summary>

Automated behaviors wired to lifecycle events in `settings.json`.

**PreToolUse (BLOCK — exit 2):**
- Long-running commands (npm/pnpm/yarn/cargo) → requires `run_in_background` or `ctx-exec`
- Loose `.md` files outside allowed paths → blocked
- `git push` → blocked until `/review-pr` runs
- Large output commands (test, lint, build, gh) → requires `ctx-exec` wrapper
- Anthropic API key usage → blocked without Super Permission
- WebFetch / WebSearch → blocked, requires `browse fetch`
- OMS Agent calls with wrong model → blocked by `enforce-oms-model.sh`

**PostToolUse (BLOCK — exit 2):**
- `console.log` in TS/JS files → blocks the edit
- Sparse `.md` files (no heading, <5 lines, placeholders) → blocks the write
- OMS queue schema validation → blocks invalid task writes
- Model-hint validation → blocks incorrect model assignments
- Prettier auto-format on `.ts/.tsx/.js/.jsx` (auto-fix)

**Stop:**
- Codemap staleness check — warns if files added/deleted since last commit

**SessionStart:**
- Injects project `CLAUDE.md`, mem0 facts, `MEMORY.md`, last session handoff (7 days)
- Runs 14-check health check (zero context tokens, stderr only)

**SessionEnd:**
- Handoff summary written to `~/.claude/handoffs/`
- mem0 fact extraction (Haiku via `claude -p --bare`) — deduplicates, auto-consolidates >40 facts
- Memory check — consolidates any topic file over 100 lines

</details>

<details>
<summary><strong>Memory System</strong></summary>

Persistent context that makes Claude continuous across sessions.

```
Session Start
│
├── MEMORY.md injected (index, <80 lines)
│   └── Topic Index routes full topic files on demand
│
├── facts.json injected (structured facts from past transcripts)
│
└── Previous session handoff (last 7 days)
```

| Component | What it does |
|---|---|
| **MEMORY.md index** | Lean routing index — Claude knows what exists without loading everything |
| **Topic files** | Domain memory loaded on demand — token cost scales with task |
| **facts.json** | Structured facts extracted by Haiku at session end |
| **Importance tags** | `high/medium/low` — prune priority for consolidation |
| **Decay pruning** | `importance:low` + >90 days → archived, not deleted |
| **mem0 extraction** | Haiku reads transcript at end, deduplicates against existing facts |
| **/consolidate-memory** | Haiku agent merges, prunes, archives, surfaces cross-topic insights |

**File layout:**
```
~/.claude/projects/[encoded-project-path]/memory/
├── MEMORY.md          ← Always loaded (kept under 80 lines)
├── facts.json         ← Structured extracted facts
├── insights.md        ← Cross-topic patterns from consolidation
└── topics/
    ├── debugging.md   ← Problem → Cause → Fix
    ├── patterns.md    ← Architecture decisions, confirmed patterns
    ├── projects.md    ← Per-project state
    ├── hooks.md       ← Hook config and fixes
    ├── agents.md      ← Agent patterns, model selection
    └── archived.md    ← Decayed or contradicted entries
```

</details>

<details>
<summary><strong>Health Check — 14 Checks</strong></summary>

**File:** `hooks/memory-persistence/health-check.sh`
**Runs:** automatically on every SessionStart. Silent when healthy, warns to stderr on issues.

| # | Check | What it catches |
|---|---|---|
| 1 | mem0 retry | Re-runs steps that failed/timed out last session |
| 2 | `settings.json` schema | Missing `matcher` fields, malformed hook objects |
| 3 | Hook command paths | Scripts moved, deleted, or lost execute permission |
| 4 | Shell script syntax | `bash -n` on every `.sh` in hooks directory |
| 5 | `mem0.py` syntax | Python errors that would silently break fact extraction |
| 6 | Auth mode | Subscription (keychain) or API key — both valid |
| 7 | `bun` installed | Required for browse and stitch skills |
| 8 | `jq` installed | Required by hooks and scripts |
| 9 | `node` installed | Required by browse skill |
| 10 | `node_modules` per skill | Warns with `bun install` command if missing |
| 11 | Playwright browsers | Checks `ms-playwright` cache for browser skills |
| 12 | `facts.json` integrity | Corrupted JSON that would break memory retrieval |
| 13 | mem0 hooks wired | SessionStart/SessionEnd/Stop all point to correct scripts |
| 14 | **OMS model routing coverage** | Every key in `oms-config.json → model_overrides` has a detection branch in `enforce-oms-model.sh` — dead keys are blocked at SessionStart |

Run manually at any time:
```bash
~/.claude/hooks/memory-persistence/health-check.sh
# No output = all healthy
```

</details>

<details>
<summary><strong>Slash Commands</strong></summary>

| Command | What it does |
|---|---|
| `/hey` | Session opener — last session recap + next step, or a dev joke on fresh start |
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
| `/e2e <flow>` | Playwright E2E — data-testid selectors, waitFor patterns, no flakiness |
| `/refactor-clean` | Find unused imports, duplicate logic, oversized files, dead code |
| `/standup` | `git log --since=yesterday` → Yesterday / Today / Blockers |
| `/test-coverage` | Coverage report, files below 80%, write tests for priority gaps |
| `/update-codemaps` | Scan project and write/update `.claude/codemap.md` |
| `/browse` | Start persistent Playwright browser daemon for live testing |
| `/stitch` | Generate, iterate, and track UI screens via Google Stitch |

</details>

<details>
<summary><strong>Skills</strong></summary>

#### `skills/browse/` — Persistent Browser Daemon
Bun HTTP server that keeps a Playwright browser alive across tool calls. Preserves session state (cookies, auth) across 20+ commands.

```bash
cd ~/.claude/skills/browse && bun install
bunx playwright install chromium
```

#### `skills/stitch/` — AI UI Generation
Generates UI screens via Google Stitch. Claude fires it autonomously before writing component code — if no screen exists for the route, it generates one first.

```bash
cd ~/.claude/skills/stitch && npm install
mkdir -p ~/.config/stitch && echo "your-key" > ~/.config/stitch/key && chmod 600 ~/.config/stitch/key
```

#### `bin/ctx-exec` — Large Output Filter
Filters command output before it enters the context window. Required for test runs, builds, and any command producing >5KB output.

```bash
~/.claude/bin/ctx-exec "failing tests" pnpm test
~/.claude/bin/ctx-exec "type error" npx tsc --noEmit
~/.claude/bin/ctx-exec "open issues" gh issue list --limit 50
```

#### `bin/bun-exec.sh` — Parallel HTTP Batching
Batches 3+ independent HTTP/API calls into a single tool invocation.

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

</details>

<details>
<summary><strong>Plugins (Active)</strong></summary>

| Plugin | Purpose |
|---|---|
| `hookify` | GUI for creating and managing hooks |
| `context7` | Up-to-date library documentation in context |
| `mgrep` | Semantic search — replaces `grep -r`, ~50% token reduction |
| `pyright-lsp` | Python type checking on edit |

TypeScript LSP, code-review, and security-guidance plugins are scoped per package in per-project `settings.json` — only loaded where needed.

</details>

---

## The Philosophy

**1. Rules enforced > rules asked for.** Standards in CLAUDE.md + hooks + checklists apply even when you forget to say them. No per-prompt reminders.

**2. Context cost is a first-class concern.** Rules load on demand. Memory is tiered. Plugins are scoped per package. Every file loaded costs tokens — treated like a dependency.

**3. Context forking as a deliberate tool.** Long conversations drift. `/fork` treats context as a resource. When work branches, fork, flush state to memory, start lean.

**4. The system learns from failures.** Security incidents append to `rules/security.md`. OMS failures become training scenarios. Non-trivial solutions extract to `/learn`. The configuration becomes an immune system.

**5. Cost-tiered agents by task type.** Haiku for repetitive tasks and worker agents. Sonnet for 90% of coding. Opus only for architecture decisions, C-suite planning, and when Sonnet failed. Free OpenRouter models for implementation and validation — Sonnet only at milestone gates.

---

## Setup

Choose your platform:
- [macOS setup](#macos-setup)
- [Windows / WSL2 setup](#windows-setup-via-wsl2)

> Claude Code has no native Windows binary. Windows users must run it inside WSL2. All bash hooks and scripts work inside WSL.

---

<details>
<summary><strong>macOS Setup</strong></summary>

### Step 1 — Install Claude Code CLI

Go to [claude.ai/code](https://claude.ai/code) and follow the macOS install instructions.

```bash
claude --version   # verify
```

### Step 2 — Install prerequisites

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

brew install jq gh node python3
curl -fsSL https://bun.sh/install | bash
```

Verify:
```bash
jq --version && gh --version && node --version && python3 --version && bun --version
```

### Step 3 — Back up existing ~/.claude (if any)

```bash
[ -d ~/.claude ] && mv ~/.claude ~/.claude.backup && echo "Backed up to ~/.claude.backup"
```

### Step 4 — Clone into ~/.claude

```bash
git clone https://github.com/anhnguyensynctree/unified-claude-system.git ~/.claude
```

### Step 5 — Make hooks executable

```bash
chmod +x ~/.claude/hooks/memory-persistence/*.sh
chmod +x ~/.claude/bin/*
```

### Step 6 — Configure mem0 auth

**Claude Max subscription (default):**
```bash
mkdir -p ~/.config/anthropic
touch ~/.config/anthropic/key   # empty file = keychain OAuth
chmod 600 ~/.config/anthropic/key
```

**API key users:**
```bash
mkdir -p ~/.config/anthropic
echo "sk-ant-..." > ~/.config/anthropic/key
chmod 600 ~/.config/anthropic/key
```

Never set `ANTHROPIC_API_KEY` in `.zshrc` or `.bashrc` — it will override keychain auth for all `claude -p` calls.

### Step 7 — Initialize global memory

```bash
mkdir -p ~/.claude/projects/-Users-$(whoami)/memory/topics

cat > ~/.claude/projects/-Users-$(whoami)/memory/MEMORY.md << 'EOF'
# Memory Index

Always loaded at session start. Read the Topic Index and load relevant files before starting work.

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

### Step 8 — Install Claude Code plugins

Open Claude Code and run `/plugins`. Install:
- `hookify@claude-plugins-official`
- `context7@claude-plugins-official`
- `mgrep@Mixedbread-Grep`
- `pyright-lsp@claude-plugins-official`

### Step 9 — Set up browse skill (optional — for live web testing)

```bash
cd ~/.claude/skills/browse
bun install
bunx playwright install chromium
```

### Step 10 — Set up Stitch skill (optional — for AI UI generation)

```bash
cd ~/.claude/skills/stitch && npm install
mkdir -p ~/.config/stitch
echo "your-key-here" > ~/.config/stitch/key
chmod 600 ~/.config/stitch/key
```

### Step 11 — Verify

```bash
~/.claude/hooks/memory-persistence/health-check.sh
# No output = all healthy
```

Open Claude Code and run `/hey`.

</details>

---

<details>
<summary><strong>Windows Setup (via WSL2)</strong></summary>

Claude Code runs inside WSL2 on Windows. All bash hooks, scripts, and tools run in the Linux environment.

### Step 1 — Enable WSL2

Open PowerShell as Administrator:
```powershell
wsl --install
```

Restart when prompted. Open the Ubuntu app and complete setup.

### Step 2 — Install Claude Code CLI inside WSL

Open your Ubuntu terminal and follow the Linux install instructions at [claude.ai/code](https://claude.ai/code).

> All remaining steps run **inside the Ubuntu/WSL terminal**.

### Step 3 — Install prerequisites inside WSL

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y jq python3 python3-pip gh

curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs

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

Open `settings.json` and remove the `Notification` block — `osascript` is macOS-only:
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

Optional: replace with `notify-send` (`sudo apt install -y libnotify-bin`).

### Step 7 — Configure mem0 auth

```bash
mkdir -p ~/.config/anthropic
touch ~/.config/anthropic/key && chmod 600 ~/.config/anthropic/key
# API key users: echo "sk-ant-..." > ~/.config/anthropic/key
```

### Step 8 — Initialize global memory

On WSL, your home path is `/home/username` — encoded as `-home-username`:

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
| Hitting errors | topics/debugging.md |
| Architecture decisions | topics/patterns.md |
EOF
```

### Step 9 — Install plugins and verify

Open Claude Code and run `/plugins`. Install:
- `hookify@claude-plugins-official`
- `context7@claude-plugins-official`
- `mgrep@Mixedbread-Grep`
- `pyright-lsp@claude-plugins-official`

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

# 3. MEMORY.md is readable
cat ~/.claude/projects/*/memory/MEMORY.md

# 4. Auth configured
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
# Initialize OMS for a new project (once)
/oms-start

# Plan the current milestone (C-suite, Opus)
/oms exec

# Settle a technical decision within the milestone
/oms how should we handle token refresh for mobile clients

# Execute the cleared task queue
/oms-work

# Capture a failure and improve the system
/oms-capture
/oms-train --failing
```

**UI workflow — design before code:**
```bash
/stitch init --auto
/stitch "dashboard with sidebar and activity feed"
/stitch update dashboard "make sidebar collapsible"
```

---

<details>
<summary><strong>Contributing</strong></summary>

This repo **is** `~/.claude`. Updating the system:

```bash
cd ~/.claude
git add rules/testing.md
git commit -m "feat(testing): raise coverage threshold to 85%"
git push
```

PRs and issues welcome. Especially useful:
- Stack-specific scaffold variants (Rails, Django, Go, Rust)
- Additional OMS agent personas
- Context mode files for domains not yet covered
- Windows/WSL2 setup improvements

</details>

---

## Community

If this system improved your Claude Code workflow, a star helps others find it.
