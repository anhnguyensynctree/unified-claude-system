# OMS — One Man Show: System Overview

A virtual AI company that runs as a single founder's engineering and product team.
OMS handles decisions, planning, execution, and reporting so the CEO (you) only touches what needs human judgment.

**Last updated:** 2026-03-25 (added /oms-tool)

---

## Mental Model

```
/oms-start          → initialize a project (once)
/oms-exec           → C-suite picks next milestone, drafts FEATUREs
/oms FEATURE-NNN    → team elaborates a feature into tasks
/oms-work           → team executes the task queue
                    ↓
             Executive Brief → CEO (terminal + Discord)
             Daily Brief     → Discord 08:00 UTC

/oms-tool           → scan GitHub/Reddit/HN for trending tools this week → gap analysis vs full system → implement improvements
/oms-tool <url>     → evaluate a specific repo, article, or paper → gap analysis → implement
```

**Separation of concerns:**
- `/oms` = decisions and planning — never writes code
- `/oms-work` = execution only — never re-discusses
- `/oms-exec` = strategy — C-suite only, no engineering agents

---

## Entry Points

### `/oms-start`
One-time project bootstrap. Reads any starting material (idea, PRD, CLAUDE.md, raw notes), runs departmental intake, and generates all `.claude/agents/*.ctx.md` files. Also creates `company-belief.ctx.md`, `product-direction.ctx.md`, `company-hierarchy.md`, and `ceo-decisions.ctx.md`.

Run once per project. Never run again unless rebuilding from scratch.

### `/oms <task>`
The core discussion engine. Routes any task through the multi-agent team and produces a synthesis with `action_items[]`. Output goes to task log + Executive Brief. Never implements — that's `/oms-work`.

**Other `/oms` modes:**
- `/oms read <file|url>` — onboard the team on new material
- `/oms discover` — re-scan project if structure changed significantly
- `/oms think [framework]: <question>` — single-agent framework lens (RICE, JTBD, IDEO, etc.)
- `/oms exec` — alias for `/oms-exec`

### `/oms-exec`
C-suite strategic session. CPO leads, joined by CTO, CRO, CLO, CFO.
Reads `product-direction.ctx.md`, selects the highest-priority milestone with no queued coverage, drafts FEATURE blocks, and appends them to `cleared-queue.md` as `Status: draft`.

Auto-triggers when: queue is empty, a milestone completes, or a cross-department concern is raised.

### `/oms FEATURE-NNN`
Elaboration mode. Takes a FEATURE draft from `cleared-queue.md` and runs the full team to break it into concrete, sized tasks (≤ 3 user interactions per impl task). Writes tasks back to `cleared-queue.md` with full specs and acceptance criteria.

### `/oms-work`
Execution loop. Reads `cleared-queue.md`, runs ready tasks in isolated git worktrees, validates each through `dev → qa → em` (or `researcher → cro → cpo`), commits on DONE, leaves branch open on CTO-STOP.

Triggered from Discord with `/work` in a project channel, or run directly in terminal.

---

## Open Discussion Format

Every `/oms` task runs through the same pipeline:

```
Step 1   Router (Haiku)        — classify complexity, select agents, set tier
Step 1.5 Path Diversity (Haiku)— seed structurally distinct starting frames (Tier 2+)
Step 2   Round 1 (parallel)    — agents post blind positions (NGT)
Step 3   Rounds 2–N            — Facilitator steers, agents respond to each other
Step 3.5 CEO Gate (Haiku)      — checks if CEO input is required before synthesis
Step 4   Synthesizer           — reads full log, produces decision + action_items
Step 5   Log                   — writes task log to logs/tasks/[task-id].md
Step 6   Trainer               — evaluates all agents, writes lessons
Step 7   Context Optimizer     — efficiency check, safe auto-fixes
Step 8   Executive Brief       — writes oms-briefing.md, agent produces CEO memo
```

**Tier system (Cynefin-based):**

| Tier | Type | Max agents | Max rounds | Synthesizer |
|---|---|---|---|---|
| 0 | Trivial | 1 | 1 | None |
| 1 | Simple | 2 | 2 | Inline |
| 2 | Compound | 3 | 2 | Full |
| 3 | Complex | 5 | 4 | Full (Opus if livelock) |

**Pull rule:** only activate agents whose cost exceeds the quality delta they produce for that tier.

---

## Engine Mechanics

### Pre-Facilitator (Haiku) — short-circuit check
Fires before the full Facilitator after every round (Tier 2+). Input: all agent outputs + current round + round cap. Checks only two conditions:
- All agents have `position_delta.changed: false` with non-empty `why_held` — genuine convergence
- Hard round cap reached

If either is true: `short_circuit: true` — skip Sonnet Facilitator entirely, jump straight to synthesis. This is the primary cost control mechanism for discussions that converge early.

### Stage Gates
Two quality enforcement checkpoints that can force a re-run:

**Stage-Gate 2** — fires before Round 2. Checks that each agent's output has `warrant` and `reasoning` populated. Any agent missing these is re-run before the round proceeds. Prevents hollow positions advancing through the pipeline.

**Stage-Gate 4** — fires after Synthesizer. Checks that every `rationale[]` entry in the synthesis cites a specific agent and round (e.g. "CTO, Round 2"). Any uncited rationale → re-run Synthesizer with explicit traceability instruction. Ensures the synthesis is traceable, not invented.

### Reversibility Gate
Synthesizer classifies every decision as reversible or irreversible. If `reversibility_gate: "escalated"`:
- Synthesizer does not pick a side
- CEO receives both options with evidence, confidence level, and agent recommendation
- Decision waits for CEO input — never auto-resolved

Reversible decisions proceed automatically. Irreversible ones always surface to CEO.

### CEO Gate (Step 3.5)
Runs after rounds complete, before synthesis. Checks the discussion output against `ceo-mandate.ctx.md` (project-level) or `ceo-mandate.md` (global default). Fires when:
- A decision would contradict a standing CEO mandate
- An agent raises a cross-department concern flagged as CEO-level
- CLO raises a `high` or `critical` legal risk

On trigger: packages a decision brief with both options, evidence, and a recommendation. Posts to `oms-pending/[slug].question` in autonomous mode. In terminal mode, asks directly. Synthesis does not run until CEO responds.

### Capitulation Flags
Facilitator tracks per-agent `capitulation_flags` across rounds. A position change is classified as:
- **Genuine** — agent cites new evidence or a logical counter-argument
- **Capitulation** — agent changed position citing round pressure, social proof, or authority

Capitulation flags are passed to Synthesizer. Capitulated positions are weighted less. Synthesizer notes in `dissent[]` if a capitulated agent held a substantively different view.

### Dissent and Reopen Conditions
Every synthesis output includes:
- `dissent[]` — minority positions that didn't win but were substantive. Preserved in the task log.
- `reopen_conditions[]` — specific circumstances that would invalidate the decision (e.g. "if user testing shows < 40% recognition rate, reopen scope question"). CEO can reference these to know when a closed decision needs revisiting.

### Briefing Mode
Router sets `briefing_mode` based on tier:
- `thin` (Tier 0) — agent receives task_id + role + agent_briefing only. No pre-mortem, no why_chain.
- `fat` (Tier 1+) — agent receives agent_briefing + why_chain + premortem_failure_modes + round_cap.

Thin mode prevents token waste on trivial tasks. Fat mode gives agents the context needed to reason about risk and uncertainty.

### Lazy Log Access
Agents never load the full task log. Each step reads only what it needs:
- Round N agents: only `## Round 1` through `## Round N-1` sections
- Synthesizer: all round sections (not headers/preamble)
- Trainer: relevant sections per tier scope only

This keeps token cost proportional to complexity, not to log size.

### Agent Injection
Facilitator can inject a new agent mid-discussion (`proceed_to: "inject_agent"`). The injected agent receives only the Delphi summary (not the full transcript) to avoid anchoring. One injection per task maximum. Used when a domain gap becomes apparent mid-discussion.

### Escalation
If agents disagree at Tier N after hitting the round cap, the discussion escalates to Tier N+1 and resumes from Round 2 (Round 1 is not re-run). The escalation is logged as a Router classification miss and fed to the Trainer.

### `/oms-capture`
Captures real OMS failures as structured training scenarios. Triggers when:
- CEO stops a task mid-way to correct routing or tier
- Trainer produces `lesson_candidates` with `channel: "scenario"`
- CEO overrides the synthesis decision post-delivery

Captured scenarios are written to `~/.claude/agents/training/scenarios/` and picked up by the nightly training run. This is how real failures become permanent guards.

---

## Company Hierarchy

### C-Suite (exec sessions + domain escalations)
| Role | Domain |
|---|---|
| CPO | Product direction, roadmap, research-to-product translation |
| CTO | Architecture, technical risk, feasibility |
| CRO | Research direction, cross-disciplinary synthesis |
| CLO | Legal, compliance, IP, privacy, platform ToS |
| CFO | Finance, cost, revenue, unit economics |

### Engineering Team (build/plan/refactor/test tasks)
| Role | Domain |
|---|---|
| Product Manager | Scope, user needs, acceptance criteria |
| Engineering Manager | Delivery, team health, spec clarity |
| Backend Developer | APIs, data, services |
| Frontend Developer | UI, components, client logic |
| QA Engineer | Test coverage, acceptance validation |

### Research Team (research tasks, project-scoped)
Declared in `.claude/agents/company-hierarchy.md`. Core agents available to all projects:
- **Chief Research Officer** — research direction, cross-disciplinary synthesis
- **Human Behavior Researcher** — how and why people behave
- **Data Intelligence Analyst** — what metrics actually tell us

Domain specialists (activated per project): clinical-safety, language-communication, philosophy-ethics, cultural-historical, biological-evolutionary, content-platform.

### Engine Agents (never in discussion rounds)
| Role | When |
|---|---|
| Router | Step 1 — every task |
| Path Diversity | Step 1.5 — Tier 2+ |
| Facilitator | After each round — Tier 2+ |
| Verification | On-demand — disputed claims |
| CEO Gate | Step 3.5 — always a quick pass |
| Synthesizer | Step 4 — Tier 2+ |
| Trainer | Step 6 — every task |
| Context Optimizer | Step 7 — every task |
| Executive Briefing Agent | Step 8 — every workflow |

---

## Task Lifecycle

```
FEATURE draft (Status: draft)        ← written by /oms-exec
    ↓ /oms FEATURE-NNN
Task specs (Status: queued)          ← written by elaboration
    ↓ /oms-work
Running in git worktree              ← isolated branch per task
    ↓ validators pass
Status: done + branch committed      ← merged to main manually
    ↓ or
Status: cto-stop + branch open       ← re-spec at next session
```

**Queue file:** `[project]/.claude/cleared-queue.md`
**Worktrees:** `[project]/.claude/worktrees/TASK-NNN`
**Branches:** `oms-work/task-nnn`

---

## Executive Briefing

Every workflow ends the same way:

1. OMS writes `.claude/oms-briefing.md` (schema: `~/.claude/agents/executive-briefing-agent/briefing-schema.md`)
2. Executive Briefing Agent reads it and outputs the CEO memo (terminal)
3. TL;DR + What Was Done posted to Discord milestone thread
4. Both sections appended to `.claude/oms-daily-log.md`

**Memo sections:** Executive TL;DR · What Was Done · Key Decisions & Trade-offs · Product & Milestone Impact · CEO Radar · Next Action

---

## Discord Integration

| Trigger | Where | What happens |
|---|---|---|
| `/work` in project channel | Discord | Runs `/oms-work <slug>` via `claude --print` |
| `/oms <idea>` in project channel | Discord | Saves to `oms-ideas.md`, prompts to run in terminal |
| Any message in project channel | Discord | Observer Q&A (read-only, reads task logs) |
| Any message in project thread | Discord | Observer Q&A on that thread's context |
| 08:00 UTC daily | `#updates` | Daily brief: queue state, costs, today's TL;DRs + Built items |
| Monday 09:00 UTC | `#radar` | Infrastructure radar: GitHub, Reddit, HN — AI/tooling trends |

**Milestone threads:** created automatically by `oms_discord.py` when the first task for a milestone runs. All task statuses + exec brief post there.

---

## Learning & Quality

**Trainer** — evaluates every task after synthesis. Writes lessons to agent `lessons.md` files. Flags scenario candidates for `/oms-capture`.

**Nightly training** — `oms-train-nightly.sh` runs `/oms-train --failing` when new scenarios exist. 66 scenarios currently, all green.

**Shared lessons** — cross-agent patterns written to `~/.claude/agents/shared-lessons/`.

**Context Optimizer** — post-task lightweight check (every run) + full audit every 10 tasks or at milestone. Flags bloat, dedup, archive candidates. Never trims without CEO approval.

---

## Key Files

| File | Purpose |
|---|---|
| `[project]/.claude/cleared-queue.md` | Single source of truth for all tasks |
| `[project]/.claude/oms-briefing.md` | Written per workflow, read by Executive Briefing Agent |
| `[project]/.claude/oms-daily-log.md` | Accumulates TL;DRs across all workflow runs |
| `[project]/.claude/agents/product-direction.ctx.md` | Milestones and current priorities |
| `[project]/.claude/agents/company-belief.ctx.md` | Vision, values, constraints |
| `[project]/.claude/agents/company-hierarchy.md` | Active departments and rostered agents |
| `~/.claude/oms-config.json` | Projects registry, channel IDs, budget config |
| `~/.claude/agents/training/results.tsv` | All training run results |
| `~/.claude/logs/tasks/[task-id].md` | Full discussion log per task |

---

## Updating This Document

Update this file whenever:
- A new workflow or command is added
- An agent is added, removed, or renamed
- The discussion format changes (tiers, round caps, engine steps)
- Discord integration changes
- The task lifecycle changes

This is the entry point for understanding the system. SKILL.md files are the implementation detail.
