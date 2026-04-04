---
name: oms
description: Orchestrate a one-man-show multi-agent discussion. Usage: /oms followed by your intent.
---
# OMS — One Man Show

Orchestrates the one-man-show multi-agent discussion engine. Invoked via `/oms` followed by your intent.

## ⚑ Output Discipline — Read Before Any Step

**NEVER output agent positions, round transcripts, internal engine reasoning, or JSON to the user.**

All agent work (Router output, Round 1–N positions, Facilitator analysis, Synthesizer internals, Trainer output, Context Optimizer JSON) is written to the task log file and shown to no one. The only things displayed to the user are:

1. **Router confirmation** (one line): `Routing: [task-id] | Tier [N] | [agents] | [N] rounds`
2. **CEO Gate** (only if triggered): the brief requiring input
3. **After synthesis** — invoke the Executive Briefing Agent (see Executive Briefing section above)
4. **Step 8.5 queue write** (one line): tasks written to cleared-queue.md
5. **Errors or blocking questions** that require CEO input

Silence is correct behavior for Steps 1–7 internals. Do not narrate progress, do not display agent reasoning, do not summarize what each agent said during the discussion. The user reads the task log if they want the full transcript.

---

## Executive Briefing — Required at End of Every Workflow

**Every workflow ends by writing `.claude/oms-briefing.md` then invoking the Executive Briefing Agent. No exceptions.**

**Step 1 — Write the briefing file**
Write `.claude/oms-briefing.md` using the schema at `~/.claude/agents/executive-briefing-agent/briefing-schema.md`.
Populate it from: task log, `cleared-queue.md` state, `product-direction.ctx.md`, any risks/blockers surfaced.

**Step 2 — Invoke the agent**
Load `~/.claude/agents/executive-briefing-agent/persona.md` + `executive-briefing-agent/lessons.md`.
The agent reads `.claude/oms-briefing.md` and outputs the executive brief. That is the final output to the CEO.

**For `/oms all`**: write one briefing file per feature as it completes (agent reads each), then overwrite with roll-up data at the end for a final consolidated brief.
**For `/oms-exec`**: briefing file includes which milestone was chosen, features drafted, queue state after write.
**For `/oms-work`**: briefing file includes all tasks completed/stopped, milestone progress, product direction.

**Step 3 — Append to daily log**
After the agent outputs the brief, append to `.claude/oms-daily-log.md`:
```
## YYYY-MM-DDTHH:MMZ | [workflow-type]
• [status bullet]
• [win or blocker bullet]
• [CEO action bullet or "No decision required"]
Built: [item 1] — [impact on product/users]
Built: [item 2] — [impact on product/users]
```
TL;DR bullets come from `### 📊 Executive TL;DR`. Built lines come from `### 🚀 What Was Done`.
This file accumulates all workflow runs for the day. The Discord daily brief reads it each morning.

---

## Invocation Modes

| Input | Mode |
|---|---|
| `/oms <task>` | **Task** — default |
| `/oms read <file/url>` | **Onboard** — team reads material, surfaces questions. For URLs: use browse `fetch <url>` (see `~/.claude/skills/browse/llms.txt`) — not WebFetch. |
| `/oms discover` | **Discover** — explicit project bootstrap |
| `/oms add <role> to the team` | **Task** — route to CTO + EM |
| `/oms exec` | **Exec** — C-suite strategic discussion; auto-triggered at milestones |
| `/oms all` | **Elaborate All** — runs `/oms FEATURE-NNN` for every `Status: draft` feature in `cleared-queue.md`, sequentially |
| `/oms think [framework]: <question>` | **Framework** — CEO invokes a named lens on a specific question |
| `/oms pivot` or natural language ("we're pivoting", "direction change") | **Pivot** — triggers `/oms-start` in pivot mode (full re-scope: Steps 2, 2.5, 3, 3.5, 5). CEO-initiated, rare. |
| `/oms new department` or "add [dept] department" | **New Department** — triggers `/oms-start` in new-department mode (Steps 3 + 3.5 only). |
| `/oms update` + pasted material or file | **Product Update** — triggers `/oms-start` in product-update mode (Step 5 only, external material → ctx file sync). Alternatively: paste material directly and say "sync ctx files" — skips /oms-start entirely for simple updates. |

## Framework Invocation Mode

When CEO uses `/oms think [framework]: <question>`, route to the framework owner and run a focused single-round analysis. Skip full discussion engine — this is a targeted lens, not a full task.

| Framework | Owner | What to produce |
|---|---|---|
| `rice` | CPO | RICE score + Kano class + Now/Next/Later slot for the named item |
| `kano` | CPO | Classify the feature: basic / performance / delighter — with evidence |
| `jtbd` | CRO + Human Behavior | 3-layer job map: functional / emotional / social |
| `desirability` | CRO | Desirability verdict + evidence basis + latent vs absent need call |
| `feasibility` | CTO | Feasibility assessment: blockers, effort, timeline risk |
| `viability` | CPO + CFO | Revenue, retention, moat — does this sustain itself? |
| `ideo` | Synthesizer | All three IDEO dimensions evaluated in parallel |
| `impact-risk` | Synthesizer | Expected value vs downside — proportionality check |
| `now-next-later` | CPO | Slot the named items into Now/Next/Later with rationale |

**Rules:**
- One framework, one question — do not run multiple frameworks in a single `think` call
- Output must include the framework's named output fields (from the owning agent's persona)
- No checkpoint written — this is advisory, not a pipeline step
- CEO can combine with a task: `/oms think jtbd: [then run task]` — JTBD output becomes briefing input for Router

---

## Session-Level Rules — apply throughout this entire session

- **External URLs**: always use browse `fetch <url>` (see `~/.claude/skills/browse/llms.txt`). Never use the built-in WebFetch tool for content extraction.
- **Parallel API calls (3+)**: write a TS file and run `~/.claude/bin/bun-exec.sh`. Never make sequential tool calls for independent HTTP requests.

These rules apply to the orchestrator, all agents, and all modes. No exceptions.

---

## Step 0 — Project Bootstrap (first run only)
Check if `.claude/agents/router.ctx.md` exists in the current project.

**If not:** run project discovery.
1. Read any that exist: `CLAUDE.md`, `.claude/codemap.md`, `package.json`, `tsconfig.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`
2. Identify: runtime, framework, database, auth, key packages, monorepo structure
3. Generate ctx files (only where meaningful project-specific context exists):
   - `router.ctx.md` — routing bias, package structure, log path, complexity hints
   - `cto.ctx.md`, `backend-developer.ctx.md`, `frontend-developer.ctx.md`
4. Tell CEO: "First run — generated `.claude/agents/` context. Review anytime."

**If exists:** skip entirely.

**Company context check:** if `.claude/agents/company-belief.ctx.md` does not exist in the current project, tell CEO: "Run `/oms-start` to initialize project context before routing this task." — then stop. Do not proceed to Step 1 until it exists.

**Queue state check (always — runs after bootstrap):**
Read `.claude/cleared-queue.md` if it exists. This is the ONLY file that counts as the task queue. Do NOT read `priority-queue.md` or any backlog file — those are CPO planning artifacts, not the executable queue.

Always print one status line before proceeding — no exceptions:
- File missing: `Queue: cleared-queue.md not found → empty`
- File exists, no queued/draft tasks: `Queue: [N] tasks total, 0 active → exec`
- File exists, draft tasks only: `Queue: [N] draft tasks — ready for /oms <task> discussion: [TASK-001 title, ...]`
- File exists, queued tasks: `Queue: [N] queued — [TASK-001 title, TASK-002 title, ...]`
- Attention needed: `Queue: ⚑ [N] need attention ([TASK-NNN cto-stop], [TASK-NNN needs-review])`

1. If `cto-stop` or `needs-review` tasks exist → brief CEO before proceeding:
   `"⚑ N tasks need attention: TASK-NNN (cto-stop — reason), TASK-NNN (needs-review — upstream changed)"`
   - `cto-stop` → re-spec inline; write new task to queue; continue
   - `needs-review` → interface changed upstream; re-spec this task only; continue
   - CEO can skip any → proceed to step 2

2. If only `draft` tasks exist AND no task was given → show drafts and prompt:
   `"[N] draft tasks from exec — run /oms <task title> to discuss each one, or /oms exec to plan another milestone"`
   - List each draft: `TASK-NNN — [title] | Why: [exec rationale]`
   - Stop. Do not auto-proceed.

3. If no `queued` or `draft` tasks remain AND no task was given → auto-trigger exec session:
   - Print: `No queued tasks and no task given — triggering exec session`
   - Read `.claude/agents/product-direction.ctx.md`
   - Print: `Reading product-direction.ctx.md — building milestone gap report`
   - Build milestone gap report: for each milestone, classify as `complete` (all tasks done) / `in-progress` (tasks queued or running) / `no coverage` (0 tasks in queue)
   - Print gap report: `Milestones: [name] complete | [name] in-progress | [name] no coverage`
   - Set `task_mode: exec` — activate CPO (lead), CTO, CFO, CLO, CRO
   - Inject gap report into CPO's briefing: milestone status + "select ONE milestone to advance next and plan its action_items"
   - Run exec discussion → Synthesis → Step 8.5 queues tasks for chosen milestone
   - Do NOT ask CEO "what's the task?" — exec fires automatically

4. Otherwise → proceed normally to Step 1:
   - If CEO gave a task (with or without queued/draft tasks): route the CEO's task to Step 1. Print `Task given — routing to Step 1`.
   - If a CEO gives a draft task title (e.g. `/oms TASK-001 extraction pipeline`): load the draft from cleared-queue.md as context, inject `Why` and `Exec-decision` into agent briefings, run full engineering discussion, Step 8.5 promotes draft → queued with full OpenSpec.
   - If queue has queued tasks but no task given: print `[N] queued tasks ready — run /oms-work to execute, or give me a task to discuss`. Stop.

---

## Before Running

**Phase 1 — pre-Router (always load):**
- `~/.claude/memory/MEMORY.md` + relevant topic files
- `~/.claude/agents/router/persona.md` + `router/lessons.md`
- `~/.claude/agents/shared-context/engineering/architecture.md`
- `~/.claude/agents/shared-context/engineering/cross-agent-patterns.md`
- Project memory + topic files (if exists)
- `.claude/codemap.md` (if exists)
- All project `.claude/agents/*.ctx.md` files
- `.claude/agents/company-hierarchy.md` (if exists) — defines active departments and rostered agents; pass to Router as `project_active_departments` and `project_available_agents`
- `.claude/agents/research.ctx.md` (if exists) — project-specific research context; inject into all domain expert agent briefings on `research` tasks

> Note: `~/.claude/agents/shared-context/product/company-direction.md` describes the OMS system itself — never load it for project tasks. Project direction lives in `.claude/agents/company-belief.ctx.md`.

**Phase 2 — post-Router (tier-gated):**
- Tier 1+: `~/.claude/agents/engine/discussion-rules.md`
- Tier 2+: `~/.claude/agents/engine/escalation-format.md`
- All tiers: `~/.claude/agents/trainer/persona.md` + `trainer/lessons.md` (Tier 0 = routing-check only, skip full eval)
- `~/.claude/agents/shared-context/product/product-direction.md` (only when task_mode requires product context)

**Load if exists:** `.claude/codemap.md`, project agent ctx files (already in Phase 1).

**Scoped context per agent** — never give everyone everything:

| Role | Shared context | codemap |
|---|---|---|
| router | all | ✓ |
| facilitator | all | — |
| ceo-gate | all discussion round outputs + ceo-mandate.ctx.md (project) or ceo-mandate.md (global default) | — |
| synthesizer | none (reads from disk log) + ceo_decision constraint if CEO Gate fired | — |
| cto | architecture.md, tech-stack.md, cross-agent-patterns.md | — |
| product-manager | company-belief.ctx.md, product-direction.ctx.md | — |
| engineering-manager | architecture.md, company-belief.ctx.md | — |
| backend-developer | tech-stack.md, architecture.md | ✓ |
| frontend-developer | tech-stack.md | ✓ |
| qa-engineer | tech-stack.md | ✓ |
| trainer | none — receives validation-criteria.md | — |
| chief-research-officer | research-synthesis.md, research.ctx.md (if exists) | — |
| human-behavior-researcher | research-synthesis.md, research.ctx.md (if exists) | — |
| data-intelligence-analyst | research-synthesis.md, research.ctx.md (if exists) | — |
| content-platform-researcher | research-synthesis.md, research.ctx.md (if exists) | — |
| clinical-safety-researcher | research-synthesis.md, research.ctx.md (if exists) | — |
| language-communication-researcher | research-synthesis.md, research.ctx.md (if exists) | — |
| philosophy-ethics-researcher | research-synthesis.md, research.ctx.md (if exists) | — |
| cultural-historical-researcher | research-synthesis.md, research.ctx.md (if exists) | — |
| biological-evolutionary-researcher | research-synthesis.md, research.ctx.md (if exists) | — |
| cpo | company-belief.ctx.md, product-direction.ctx.md | — |
| clo | company-belief.ctx.md | — |
| cfo | company-belief.ctx.md | — |

**Context mode**: Router detects `task_mode` and outputs `context_files[]`. Most modes map to one file; four modes always pair two: `ui-ux` (ui-ux + design-quality), `security` (security + architecture), `test` (test + dev), `refactor` (refactor + test). `performance` conditionally adds `architecture.md` only when the bottleneck is systemic. Router reads all context files once and distills per-agent `agent_briefings` (1–2 sentences each). Never pass full context files to agents.

| Mode | Context files loaded | Rationale |
|---|---|---|
| exec | `company-belief.ctx.md` + `product-direction.ctx.md` | exec discussions require company vision + current product state; no engineering or research context loaded unless escalation requires it |

---

## Tier Activation Matrix

Router outputs `tier: 0|1|2|3` using Cynefin classification. Every feature is pull-activated by this value — nothing fires speculatively.

| | Tier 0 — Trivial | Tier 1 — Simple | Tier 2 — Compound | Tier 3 — Complex |
|---|---|---|---|---|
| **Cynefin** | Obvious | Complicated, low-stakes | Complicated, high-stakes | Complex |
| **Signals** | 1 domain, known pattern, reversible | 1–2 domains, needs analysis, reversible | 2–3 domains, tradeoffs, partial reversibility | 3+ domains OR irreversible OR high uncertainty |
| **Max agents** | 1 | 2 | 3 | 5 |
| **Path Diversity** | — | — | ✓ | ✓ |
| **Max rounds** | 1 | 2 | 2 | 4 |
| **Facilitator** | — | OMS direct check | Full | Full (DCI + DA + livelock) |
| **Verification** | — | — | on-demand | on-demand |
| **Synthesizer** | — | Inline (OMS) | Full | Full |
| **Trainer scope** | Router only | Router + agents | All engine + agents | All |

**Pull rule**: over-processing is waste. An agent whose cost exceeds the quality delta it produces for that tier does not activate.

**Escalation**: if agents disagree at Tier N after hitting the round cap → escalate to Tier N+1, resume from Round 2 (don't restart Round 1). Log the escalation as a Router classification miss.

---

## Agent Registry

### Engine Roles
| Role | File | Lessons | Model | When |
|---|---|---|---|---|
| router | `~/.claude/agents/router/persona.md` | `router/lessons.md` | Haiku | Step 1 |
| path-diversity | `~/.claude/agents/path-diversity/persona.md` | `path-diversity/lessons.md` | Haiku | Step 1.5 (Tier 2+) |
| pre-facilitator | *(inline — no persona file)* | — | Haiku | Before full Facilitator each round (Tier 2+) |
| facilitator | `~/.claude/agents/facilitator/persona.md` | `facilitator/lessons.md` | Sonnet | After each round (Tier 2+, when pre-facilitator requires it) |
| verification | `~/.claude/agents/verification/persona.md` | `verification/lessons.md` | Sonnet | On-demand |
| ceo-gate | `~/.claude/agents/ceo-gate/persona.md` | — | Haiku | Step 3.5 (Tier 1+) — always a quick pass, escalates on match |
| synthesizer | `~/.claude/agents/synthesizer/persona.md` | `synthesizer/lessons.md` | Sonnet (Opus: livelock confirmed, or 5+ agents round 2+ no convergence) | Step 4 (Tier 2+) |
| trainer | `~/.claude/agents/trainer/persona.md` | `trainer/lessons.md` | Sonnet | Step 6 — always |
| executive-briefing-agent | `~/.claude/agents/executive-briefing-agent/persona.md` | `executive-briefing-agent/lessons.md` | Sonnet | Terminal — fires once after every workflow completes. Reads `.claude/oms-briefing.md`. Never participates in discussion rounds. |

### Discussion Roster (V1)

**Engineering agents** — activated for `build`, `architecture`, `debug`, `plan`, `refactor`, `security`, `test`, `performance`, `ui-ux` tasks:

| Role | File | Lessons | ctx |
|---|---|---|---|
| cto | `~/.claude/agents/cto/persona.md` | `cto/lessons.md` | `cto.ctx.md` |
| product-manager | `~/.claude/agents/product-manager/persona.md` | `product-manager/lessons.md` | `product-manager.ctx.md` |
| engineering-manager | `~/.claude/agents/engineering-manager/persona.md` | `engineering-manager/lessons.md` | `engineering-manager.ctx.md` |
| frontend-developer | `~/.claude/agents/frontend-developer/persona.md` | `frontend-developer/lessons.md` | `frontend-developer.ctx.md` |
| backend-developer | `~/.claude/agents/backend-developer/persona.md` | `backend-developer/lessons.md` | `backend-developer.ctx.md` |
| qa-engineer | `~/.claude/agents/qa-engineer/persona.md` | `qa-engineer/lessons.md` | `qa-engineer.ctx.md` |

**Research C-Suite** — activated for all `research` tasks and `exec` tasks as domain lead:

| Role | File | Lessons | Domain |
|---|---|---|---|
| chief-research-officer | `~/.claude/agents/chief-research-officer/persona.md` | `chief-research-officer/lessons.md` | Research direction, cross-disciplinary synthesis, research-to-product translation |

**New C-Suite** — activated for `exec` tasks and tasks within their domain scope:

| Role | File | Lessons | Domain |
|---|---|---|---|
| cpo | `~/.claude/agents/cpo/persona.md` | `cpo/lessons.md` | Product direction, research-to-product translation, roadmap ownership |
| clo | `~/.claude/agents/clo/persona.md` | `clo/lessons.md` | All legal — compliance, contracts, IP, privacy, platform ToS |
| cfo | `~/.claude/agents/cfo/persona.md` | `cfo/lessons.md` | All finance — cost tracking, revenue, P&L, unit economics |

**Domain Research Agents** — project-scoped; only available if declared in `.claude/agents/company-hierarchy.md`. PhD-equivalent, 40+ years expertise standard.

Core research agents (likely in most research projects):
| Role | File | Lessons | Research Question |
|---|---|---|---|
| human-behavior-researcher | `~/.claude/agents/human-behavior-researcher/persona.md` | `human-behavior-researcher/lessons.md` | How and why do people behave, decide, and change? |
| data-intelligence-analyst | `~/.claude/agents/data-intelligence-analyst/persona.md` | `data-intelligence-analyst/lessons.md` | What do our metrics and patterns actually tell us? |

Domain specialist agents (project-scoped per company-hierarchy):
| Role | File | Lessons | Research Question |
|---|---|---|---|
| content-platform-researcher | `~/.claude/agents/content-platform-researcher/persona.md` | `content-platform-researcher/lessons.md` | How does content perform on this platform and why? |
| clinical-safety-researcher | `~/.claude/agents/clinical-safety-researcher/persona.md` | `clinical-safety-researcher/lessons.md` | What psychological risks exist and how do we protect users? |
| language-communication-researcher | `~/.claude/agents/language-communication-researcher/persona.md` | `language-communication-researcher/lessons.md` | How should this be phrased, structured, and conveyed? |
| philosophy-ethics-researcher | `~/.claude/agents/philosophy-ethics-researcher/persona.md` | `philosophy-ethics-researcher/lessons.md` | What are the ethical implications and what does this mean? |
| cultural-historical-researcher | `~/.claude/agents/cultural-historical-researcher/persona.md` | `cultural-historical-researcher/lessons.md` | What do culture, history, and social structures tell us? |
| biological-evolutionary-researcher | `~/.claude/agents/biological-evolutionary-researcher/persona.md` | `biological-evolutionary-researcher/lessons.md` | What biological and evolutionary forces shape this? |

Domain research agents carry universal domain knowledge — no ctx.md. Project-specific context is injected via `.claude/agents/research.ctx.md` on research tasks. Domain researchers do not replace engineering agents on implementation tasks but may join them when the task has a human-understanding dimension.

Each agent's effective prompt = persona.md + lessons.md + ctx.md (if exists) + `agent_briefings.[role]` from Router.

**Load order**: persona.md (identity) → lessons.md (learned behaviors) → ctx.md (task context) → agent_briefing (task distillation).

---

## Discover Mode
1. Run Step 0 if needed
2. Run all agents in parallel — each reads project files found in bootstrap, produces a 3–5 bullet domain summary
3. Router collects summaries → writes `.claude/agents/project-brief.md`
4. Tell CEO: "Project discovered. Run `/oms read <PRD>` to onboard, or start a task."

No rounds, no trainer eval, no synthesis.

## Onboard Mode — `/oms read <file or url>`
A. Load material (read file, folder, or fetch URL)
B. Run all agents in parallel — each produces: domain summary (3–5 bullets) + domain-specific blocking/clarifying questions
C. Router deduplicates and groups questions by urgency: **blocking** vs **clarifying**. Presents to CEO.
D. CEO answers questions. Router distributes answers to relevant agents.
E. Each agent writes what they learned to the project-layer `[project]/.claude/agents/[agent]/lessons.md` under a `## Onboarding: [project] | [date]` header

Trainer does not evaluate onboarding sessions.

## Elaborate All Mode — `/oms all`

Reads `cleared-queue.md` and runs a **decomp pipeline** (not the full strategic discussion engine) for every FEATURE block with `Status: draft`, sequentially in order. Each FEATURE becomes a set of `Status: queued` TASK blocks with full OpenSpec fields (Spec, Scenarios, Artifacts, Produces, Verify, Depends).

The goal is decomposition — cataloging what a feature involves across domains. But complex cross-department features embed real design decisions (who owns the shared interface? how to split ownership across teams?). The pipeline branches on complexity: simple features use a lightweight decomp path; complex features get the full discussion engine.

**Decomp pipeline (per FEATURE)**:

**D1 — Router (Haiku)**
- Input: feature block (`Departments[]`, `Exec-decision`, `Why`, `Context-hints`) + project ctx files + codemap
- Output: `activated_agents` (hard-capped to declared roster + `Departments[]`), `expertise_gaps[]` (agents NOT in roster that would be useful — do not activate them), `tier`
- **Pipeline branch**:
  - Tier 0/1 (single dept or clear scope, no cross-team design decisions) → continue with D2→D5 decomp path below
  - Tier 2+ (cross-dept tradeoffs, architectural decisions embedded in scope, multiple valid decompositions) → **skip D2–D5, run full Steps 1–8.5 for this feature** (Facilitator, Synthesizer, and all). The `Exec-decision` constraint still applies as a hard ceiling on all agent briefings. This is where the open discussion engine earns its place.

**D2 — Proposal Round (all activated agents, parallel)**
- Each agent receives: persona + `Exec-decision` constraint + `Why` + `Context-hints`
- Each agent outputs: their domain's proposed tasks (Spec, Scenarios, Artifacts, Produces, Verify), cross-team interfaces needed (what they Produce that other teams Depend on), and any risks or open questions within their domain
- This is a parallel, blind pass — agents do not see each other's proposals yet

**D2.5 — Cross-Review Pass (Tier 0/1 only — all activated agents, parallel, one pass)**
- Each agent receives: their D2 proposal + all other agents' D2 proposals
- Each agent outputs only: (a) conflicts — "my task X conflicts with [agent]'s task Y because [reason]", (b) missing pieces — "I need [artifact/interface] from [domain] that nobody is producing", (c) scope flags — "task [title] is too large — should split at [boundary]"
- Agents do NOT rewrite their full proposals here — conflict/gap flags only
- OMS resolves all flags inline before D3: adjusts task boundaries, adds missing Produces, splits oversized tasks
- **Escalation rule**: if OMS cannot resolve a flag inline (e.g. two agents have incompatible approaches with no clear winner) → this feature escalates to full Steps 1–8.5. Do not silently override agent disagreement.
- Purpose: catch cross-team assumptions for simple features. For complex features, Tier 2+ routing in D1 already sent them to full discussion — D2.5 never fires for those.

**D3 — Interface-Contract Pass (inline, no separate agent)**
- OMS resolves cross-team Depends: ensure every `Produces` from one agent's tasks aligns with `Depends` in another agent's tasks, after D2.5 amendments
- If a contract gap remains (team A needs X but no team produces X): flag as `cto-stop` on the relevant task, not a roster change

**D4 — OpenSpec Write**
- Merge all agent task proposals into OpenSpec TASK-NNN blocks
- Apply scaffold artifact rules: if any `Spec:` contains "initialize", "scaffold", "create project", "pnpm install", or "npm install" → `.gitignore` MUST appear in `Artifacts:`. Missing it is a spec defect; fix before writing.
- Replace the FEATURE block in `cleared-queue.md` with elaborated TASK-NNN blocks (`Status: queued`)
- Output: "FEATURE-NNN → [N] tasks queued" and continue

**D5 — Trainer (Router + decomp accuracy only)**
- Evaluates: roster restraint, `Departments[]` hard cap respected, interface contracts resolved, no scope creep beyond `Exec-decision`
- Does NOT run full SBI eval — this is not a strategic discussion

**Execution**:
1. Read `cleared-queue.md` — collect all `Status: draft` FEATURE blocks
2. If none: output "No draft features found. Run /oms-exec to generate features first." and stop.
3. For each FEATURE (in order, one at a time): run D1 → D2 → D3 → D4 → D5
4. After all features elaborated: output the queue summary (format below), then the CEO Product Summary roll-up (see Output Discipline section), then "**Next: run /oms-work to begin execution.**"

   **CEO Product Summary roll-up for `/oms all`** — after queue summary, output one consolidated block:
   ```
   ━━━ CEO Summary ━━━━━━━━━━━━━━━━━━━━━━━━
   What happened:   [N features elaborated into X tasks — what the milestone now covers in plain English]
   Product impact:  [what this milestone delivers for users when executed]
   Milestone:       [milestone name — X tasks ready, Y with ceo-gate, Z large tasks flagged]
   Pros:            [why this plan is solid]
   Cons/Risks:      [biggest risks in the task plan or scope gaps]
   Blockers:        [ceo-gate tasks that need approval before running, or "None"]
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ```

   **Expertise gap gate** — if any `expertise_gaps[]` were collected across all features, present a blocking gate BEFORE outputting "Next: /oms-work". CEO must acknowledge each gap:
   ```
   ⚑ Expertise gaps detected — resolve before running /oms-work:

   [role] — needed for: [which feature/task] because [why]
     (a) Proceed without — accept the risk
     (b) Add this agent — create persona + add to company-hierarchy.md
         → Non-standard agent (add to existing department): create ~/.claude/agents/[role]/persona.md + add to company-hierarchy.md Non-Standard Agents section
         → New department: run /oms-start (update path → "new department") — re-elaborates affected features after
     (c) Dismiss — not relevant to this project
   ```
   Wait for CEO response on each gap before proceeding. Only output "**Next: run /oms-work**" once all gaps are acknowledged.
   If no expertise gaps: output "**Next: run /oms-work to begin execution.**" immediately after the CEO summary.

Features with `Research-gate: true` are elaborated last.
Never pause between features — run all sequentially without CEO input unless an actual escalation fires.

**Queue summary format** (Phase 3 output):
```
[N] tasks queued across [M] features:

[milestone name]:
  [STATUS] TASK-NNN  [dept]  [title]  [SIZE]  [GATE]  depends: [none | TASK-NNN]

Status icons: · queued  ✓ done  → in-progress  ⚑ cto-stop
SIZE: small (1 Spec + ≤3 Scenarios + ≤3 Artifacts) | medium | large (flag — consider splitting)
GATE: no-gate (Tier 0-1) | ceo-gate (Tier 2-3, cross-dept or irreversible)

Can start immediately (no deps): TASK-NNN, TASK-NNN, ...
```

**SIZE classification**:
- `small` — 1 SHALL Spec, ≤3 Scenarios, ≤3 Artifact paths, single department
- `medium` — 1 SHALL Spec, 4-6 Scenarios, ≤5 Artifacts, 1-2 departments
- `large` — flag with ⚠ — recommend splitting before execution

**GATE classification**:
- `no-gate` — single department, reversible, Tier 0-1
- `ceo-gate` — cross-department, irreversible change, architectural decision, or legal/financial impact (Tier 2-3)

---

## Exec Mode — `/oms exec` or auto-triggered at milestone

The executive discussion. C-suite meets to evaluate product direction, translate research insights into product bets, and surface strategic decisions. CEO is NOT in the room — exec produces a recommendation that goes TO the CEO.

**Exec follows the same full step pipeline as any other task — Steps 1 through 8.5, no exceptions.** The only differences from a regular task are the roster, context, and synthesis output format. Do not skip or abbreviate any step.

**Retrospective mode** — exec is runnable even when the queue is empty or no new milestone is planned. In this mode, Router skips milestone gap report and instead runs history injection only. C-suite reviews patterns, re-orients direction, and updates `product-direction.ctx.md`. No FEATURE blocks are written. Triggered automatically when `cleared-queue.md` has no `Status: draft` features and no queued milestone gap.

**Step-by-step for exec:**
1. **Step 1 — Router**: classify as exec, set tier (exec is always Tier 2 minimum), output `task_id`, `activated_agents` = CPO+CTO+CRO+CLO+CFO, `agent_briefings` with milestone gap report injected into CPO's briefing.

   **Before building agent briefings — always, on every exec run**, Router reads two history sources and injects them as shared context into ALL C-suite briefings:
   - **`## Known Failure Patterns`** — read `.claude/cleared-queue.md`, extract all CTO-stop entries and `needs-review` notes. Group recurring themes (same root cause appearing 2+ times). If none: omit section.
   - **`## Previous Milestone Signals`** — read `.claude/agents/product-direction.ctx.md` completed milestones section. Extract: what shipped, what got reworked, what took longer than scoped. If no completed milestones: omit section.

   These sections appear in every C-suite agent's briefing so every exec discussion starts with full project memory. No explicit trigger needed — this runs whether planning a new milestone or running retro.
2. **Step 1.5 — Path Diversity**: run (exec is Tier 2+) — each C-suite agent gets a distinct strategic frame
3. **Step 2 — Round 1**: all 5 agents post positions in parallel, blind NGT. Display each position to CEO.
4. **Step 3 — Rounds 2+**: Facilitator runs between rounds. Continue until convergence or round cap.
5. **Step 4 — Synthesizer**: output is a recommendation brief (milestone selected, `action_items[]`, `roster_changes[]`, rationale). Update `product-direction.ctx.md`. Each `roster_changes[]` entry must include `{ role, domain_brief, non_negotiables, sponsored_by }`.
   - The sponsoring C-suite head must provide `domain_brief` and `non_negotiables` during their round position, not after synthesis.
   - Facilitator enforces two things before synthesis: (1) if a C-suite agent flags a roster need without a domain brief → inject back to them; (2) if the domain_brief contains project-specific details (schema names, product names, stack choices) → flag and ask for the generic domain version. Personas are project-agnostic — project specifics go in ctx.md, not the persona.
6. **Step 5 — Log**: write task log to `.claude/logs/tasks/[task-id].md`
7. **Step 6 — Trainer**: evaluates exec session
8. **Step 7 — Context Optimizer**: lightweight check
9. **Step 8 — CEO feedback**: present brief, wait for response
10. **Step 8.5 — Queue Commit**: elaborate `action_items[]` → OpenSpec tasks → write to `cleared-queue.md`. For each entry in `roster_changes[]`, write a CEO-gate task block before the milestone's feature tasks.

The exec session is not complete until `cleared-queue.md` is written with OpenSpec tasks.

**`roster_changes[]`** — when exec surfaces a need to expand the team:

Exec agents (CPO/CTO/CRO/CLO/CFO) may flag that a milestone requires expertise the current roster lacks. Common cases:
- Legal/compliance risk the current team can't evaluate → CLO or a compliance specialist
- Research domain the milestone depends on → CRO + relevant domain researcher
- Technical domain outside the current engineers (mobile, ML, infra) → non-standard agent
- Financial model or unit economics work → CFO

These surface as `roster_changes[]` in Synthesizer output — not as inline activations. Each becomes a `Status: queued, Gate: ceo-gate` task in the queue written before the milestone tasks:

```
TASK-NNN: Add [role] to engineering roster
Spec:     ⛔ Read ~/.claude/agents/engine/agent-creation-rules.md FIRST. Do not write a single line of persona until this file is read and the C-Suite Narrowing Gate (CPO + CTO checks) passes.
          Then: create ~/.claude/agents/[role]/persona.md from the domain_brief captured in this task's Context field. Add to .claude/agents/company-hierarchy.md under [department] > Non-Standard Agents.
Context:  [domain_brief and non_negotiables from Synthesizer roster_changes entry — injected here at task-write time]
Gate:     ceo-gate — CEO approves before this task executes
Depends:  none
Blocks:   [TASK-NNN of the milestone tasks that need this expertise]
```

**Persona authorship** — the sponsoring C-suite head provides `domain_brief` and `non_negotiables` during their exec round. Synthesizer captures `{ role, domain_brief, non_negotiables, sponsored_by }` in `roster_changes[]` and injects the brief into the task's Context field at queue-write time. OMS writes the persona from that brief. The C-suite head is the author; OMS is the typist.

**Persona standard** — `~/.claude/agents/engine/agent-creation-rules.md` is the hard gate. Required structure: `## Identity`, `## Activation Condition`, `## Primary Output`, `## Non-Negotiables`, `## Working Guidelines`. Project-specific knowledge goes in the project's ctx.md, not the persona — Facilitator enforces this when the domain_brief is captured. Line targets: engineering 70, researcher 65, C-suite 60. Create empty `lessons.md` and `MEMORY.md` alongside persona.

**History bootstrapping** — not needed. New agents start with empty `lessons.md`. Task specs are self-contained; project-specific context is in ctx.md files. Trainer populates lessons.md organically after each task cycle.

**Department expansion (e.g. CFO adding a unit-economics-analyst)** — same `roster_changes[]` path. The sponsoring C-suite head (CFO, CTO, CRO, etc.) surfaces the need in the exec discussion. Synthesizer includes it in `roster_changes[]`. CEO-gate task is written before the milestone tasks it unblocks. The C-suite head's department is updated in `company-hierarchy.md` when the agent is created.

For a full new department (not a single agent): the task Spec references `/oms-start` update path ("new department") instead of direct persona creation.
CEO approves this task at the CEO gate, then it runs before the milestone. `/oms-work` respects the Blocks dependency — milestone tasks wait.

**Exec output to CEO** — executive summary only (see Output Discipline at top of this file). Round transcripts go to task log only. No narration of agent positions during the discussion.

**Exec context** — Router loads for exec tasks:
- `company-belief.ctx.md` (all C-suite read this)
- `product-direction.ctx.md` (CPO leads, all read)
- All department C-suite personas

---

## Task ID
Every task: `YYYY-MM-DD-short-slug` (kebab-case, max 6 words, from Router output)
Log path: `.claude/logs/tasks/[task-id].md`

---

## OMS Scope Rule
**OMS is for decisions, not execution.** It answers: "What should we build and why?" — not "How do we build it right now?"

- `/oms <task>` → produces a synthesis with `action_items[]`
- Implementation follows separately: direct coding, or `/oms-work` (runs post-synthesis only)
- Never invoke `/oms implement ...` — implementation inputs are wasted ceremony after architecture is settled
- If the task is already decided and you have `action_items`: skip OMS entirely, go implement

---

## Step 1 — Router
Run Router (Haiku):
- Input: CEO intent + all shared context + codemap + project memory + ctx files
- Output must include: `task_id`, `tier`, `activated_agents`, `domain_lead`, `primary_recommender`, `complexity`, `round_cap`, `triz_contradiction`, `premortem_failure_modes`, `agent_briefings`, `briefing_mode`, `why_chain` (if company context is real), `stage_gate`, `locked: true`

**Feature discussion routing (when CEO runs `/oms FEATURE-NNN` or during `/oms all`):**
- Read the feature draft from `cleared-queue.md` — load `Departments[]`, `Research-gate`, `Exec-decision`, `Why`, `Context-hints`
- Inject `Exec-decision` as a hard constraint into ALL agent briefings — it cannot be overturned
- `Departments[]` is a **hard cap** — only activate agents declared in the project's `company-hierarchy.md` roster AND listed in `Departments[]`. Do not add agents outside this set.
  - If Router detects that the feature requires expertise not present in the roster (e.g. security, legal, research), do NOT add those agents inline. Instead: append to `expertise_gaps[]` in Router output — these surface to CEO in the final summary.
  - Swapping within the declared departments is allowed (e.g. preferring backend-developer over engineering-manager for a data-heavy task) — justify in `why_chain`
- If `Research-gate: true`: activate research agents as domain lead; engineering agents present but do not own the interface-contract until research findings are known

If `clarifying_questions`: present to CEO, collect answers, re-run Router.
If `stage_gate: "failed"`: fix noted gap, re-run Router.

## Step 1.5 — Path Diversity *(Tier 2+ only)*
Run Path Diversity (Haiku):
- Input: task description + `activated_agents` + `task_mode` + pre-mortem
- Output: N structurally distinct paths, one per agent, each with a different `key_assumption`

If `skip: true`: proceed without seeding. Otherwise inject each agent's path as a "Starting frame to consider" block in their Round 1 prompt. Log paths to task log under `## Path Diversity Seeds` — no CEO display.

## Step 2 — Round 1 (NGT Blind)
Run activated agents **in parallel**. Each receives: persona + MEMORY + scoped shared context + agent_briefing + path seed (if Tier 2+) + pre-mortem block.

**Briefing mode** (from Router `briefing_mode`):
- `thin` (Tier 0): task_id + role + agent_briefing only — no pre-mortem, no why_chain
- `fat` (Tier 1+): agent_briefing + why_chain + premortem_failure_modes + round_cap

Instruction: "Post your Round 1 position. You have not seen other agents' positions yet."

**Checkpoint**: append Round 1 outputs to `logs/tasks/[task-id].md` immediately. Full agent positions go to the log only — not displayed to CEO.

**After Round 1 — branch by tier:**

**Tier 0**: Present agent's `position` + `action_items` to CEO → jump to Step 5.

**Tier 1**: OMS checks Stage-Gate 2 directly (warrant + reasoning populated?). Re-run any failing agent.
- If agents agree → OMS inline synthesis: present combined `position` + `action_items` → Step 5
- If agents disagree → escalate to Tier 2: run Facilitator, proceed as Tier 2

**Tier 2/3**: Pre-Facilitator (Haiku), then full Facilitator only if needed:
1. **Pre-Facilitator (Haiku)** — Input: all Round 1 agent outputs + current round number + `round_cap`. Check only: (a) all agents `position_delta.changed: false` with non-empty `why_held`, OR (b) hard cap reached. Output: `{short_circuit: bool, reason: string}`. If `short_circuit: true`: skip full Facilitator, jump directly to Step 4.
2. **Full Facilitator (Sonnet)** — only when `short_circuit: false`. Input: Round 1 outputs + `domain_lead` + `primary_recommender`. Runs per `facilitator/persona.md`: Stage-Gate 2, position distribution (Delphi), DA check, epistemic act tracking, `targeted_injections`. Follow `proceed_to` into Step 3 or Step 4.

## Step 3 — Rounds 2+ *(Tier 2+ only)*
For each round:
1. Write `[task-id].checkpoint`: `round=N status=running`
2. Read only `## Round N-1` sections from log (lazy load)
3. Run agents in parallel — each receives: full history from disk + Facilitator's `position_distribution` + any `injections`
4. Collect outputs → checkpoint write `status=complete`
5. Pre-Facilitator (Haiku) convergence check → if `short_circuit: true` → jump to Step 4. Otherwise run full Facilitator (Sonnet) — follow `proceed_to`:
   - `round_N` → continue
   - `verify` → run Verification (Sonnet) on `disputed_claims[]` only (no full transcript). Prepend `injections[]` to next round.
   - `inject_agent` → brief new agent with Delphi summary only (no transcript). One injection per task max.
   - `compatibility_check` → one targeted round on the interface conflict
   - `synthesis` → proceed to Step 4
6. Apply `capitulation_flags` per-agent injections
7. Append round outputs to task log. No CEO display during rounds — full transcript is log-only.

Continue until `proceed_to: "synthesis"` or hard cap (5 rounds).

## Step 3.5 — CEO Gate *(Tier 1+ only)*
Run CEO Gate per `ceo-gate/persona.md` — fires after all rounds complete, before Synthesizer. Tier 0 skips.

- Input: all round outputs + `ceo-mandate.ctx.md` (project) or global default
- Phase 1 (Haiku): classify against CEO-mandatory categories (1,2,4,9) and bufferable categories (3,5,6,7,8,10)
- Phase 2: if triggered, 1-round C-suite blind NGT on the flagged decision
- Phase 3: surface Ratification Brief (mandatory + C-suite resolved) or Strategic Brief (C-suite split/hard_block)

**Routes:**
- `route: "synthesize"` → Decision Log covered it (auto-pilot) or no threshold crossed → proceed to Step 4
- `route: "absorb"` → C-suite resolved a bufferable category → inject `ceo_decision` constraint into Synthesizer, proceed to Step 4
- `route: "ceo_brief"` → present brief to CEO inline; wait for response before Step 4. Log CEO response in task log under `## CEO Feedback` before proceeding.

## Step 4 — Synthesizer *(Tier 2+ only)*
Run Synthesizer (Sonnet first; escalate to Opus only if: livelock confirmed by Facilitator, OR 5+ agents AND round 2+ with no convergence signal):
- Input: full log from disk (all rounds) + Router's `domain_lead` / `primary_recommender` / `activated_agents` + Facilitator `capitulation_flags` + per-agent `confidence_pct` per round
- Instruction: "Synthesize. Cite agent + round for every rationale claim. Apply reversibility gate. Derive reopening conditions."

**Stage-Gate 4**: verify all `rationale[]` entries cite agent + round. If any uncited → re-run Synthesizer with traceability instruction.

If `reversibility_gate: "escalated"` → present decision brief to CEO (both options, evidence, confidence note). Do not override.
If `escalation_required: true` → package per `escalation-format.md`.
Otherwise: proceed to Step 5 (log), then invoke the Executive Briefing Agent (see Executive Briefing section at top). Full agent transcripts, JSON blobs, rationale citations, and internal engine output go to the task log only.

## Step 5 — Log
Append final synthesis to `.claude/logs/tasks/[task-id].md`. Delete `[task-id].checkpoint`.

Log header:
```
# [task-id]: [CEO intent verbatim]
Date: YYYY-MM-DD  Tier: N  Domain Lead: [role]  Agents: [list]  Rounds: N
Pre-mortem: [modes]
```

Session file:
```bash
echo "OMS [$task_id] | tier:$tier | agents:$agents | decision:$one_line" >> "$SESSION_FILE"
```

Project memory (`topics/oms-history.md`):
```
## [task-id] | [date] | importance:medium
Decision: [one sentence]  Agents: [list]  Tier: N  Log: .claude/logs/tasks/[task-id].md
```

## Step 6 — Trainer
Trainer always runs. Scope scales by tier:

| Tier | What trainer evaluates |
|---|---|
| 0 | Router only — complexity/tier accuracy, roster restraint, briefing quality |
| 1 | Router + all activated agents — routing accuracy, position quality, domain discipline |
| 2 | All engine agents (Router, Path Diversity, Facilitator, Synthesizer) + all discussion agents |
| 3 | All — full SBI evaluation including confidence delta accuracy, reversibility gate, reopening conditions |
| Any — CEO corrected something | Always Router; plus whichever agent the correction targets |
| Stage-Gate 4 failed | Synthesizer specifically — traceability discipline |

Trainer call:
- Input: `trainer/persona.md` + lessons.md + MEMORY + `validation-criteria.md` + relevant log sections (lazy — load only what the tier scope requires)
- Context to inject: `tier`, `activated_agents`, and `agent_task_counts` — count of prior tasks per activated agent, read from `~/.claude/agents/training/results.tsv` or `topics/oms-history.md`
- Instruction: "Evaluate this completed task per the tier scope. Tier: [N]. Activated agents: [list]. Agent task counts: { [role]: [N], ... }. For each agent, check their lessons.md before classifying — a lesson already present should be `channel: scenario`, not re-written."

**After trainer output:**

1. **Write lessons** — for each `lesson_candidates` entry with `channel: "lesson"`:
   - Check `~/.claude/agents/[agent]/lessons.md` for a matching rule (4-word fingerprint match)
   - If not present: append `[date] | [task-id]: [lesson]` to that agent's `lessons.md`
   - If already present: upgrade to `channel: "scenario"` — flag for Step 8

2. **Write cross-agent patterns** — if `cross_agent_patterns` non-empty: append to `shared-context/engineering/cross-agent-patterns.md`

4. **Flag scenario candidates** — collect all `lesson_candidates` with `channel: "scenario"` → pass to Step 8

If `complexity_assessment_accurate: false`: inject correction to Router memory.
If `meta_retrospective_due: true`: notify CEO — "Run `/compact-agent-memory [agent]`."

After all trainer outputs are written, proceed to Step 7.

## Step 7 — Context Optimizer

Load `~/.claude/agents/context-optimizer/persona.md` and `~/.claude/agents/context-optimizer/metrics.md`.

**Mode 1 (every task — always):** Run post-task lightweight check against `.claude/logs/tasks/[task-id].md`. Also read Trainer output from the task log — correlate lesson quality signals with efficiency findings (e.g. Trainer flagged over-discussion → wasted rounds confirmed). Execute safe auto-fixes immediately (facts.json consolidation, archive markers on >300-line logs). Update `metrics.md`.

**Mode 2 (full audit — when triggered):** Check `task_count_since_last_audit` in `metrics.md`. If ≥10, OR Router flagged `milestone_reached: true` this task → run full audit across all OMS living documents (all `.ctx.md` files including `ceo-decisions.ctx.md`, persona dedup/upgrade pipeline, engine health, efficiency patterns). Post non-blocking Discord summary (3-5 bullets). Reset audit counter. Any engine changes or persona trims require CEO approval before executing.

Output: JSON per schema in persona.md. Append `## Efficiency Check` to task log only if `status != "clean"`. Never surface clean results to CEO.

After Context Optimizer completes, proceed to Step 8.

## Step 8 — CEO Feedback + Scenario Capture

**Blocking step (manual mode):** Present the synthesis to CEO and wait for their response before proceeding to Step 8.5. Do not continue until CEO has confirmed or given feedback.

**Memory routing** (always):
- Routing/complexity correction → Router memory
- Synthesis traceability correction → Synthesizer memory
- Process correction (false convergence, livelock missed) → Facilitator memory
- Cancellation → Router memory (training signal for future tier calls)

**Scenario capture triggers** (run `/oms-capture` when any apply):
- CEO stopped the task mid-way to correct routing or tier → always capture
- Trainer produced any `lesson_candidates` with `channel: "scenario"` → present each to CEO
- CEO overrides the synthesis decision post-delivery → flag for capture

When capture is triggered, present to CEO:
```
Scenario capture available for this task:
[agent/engine]: [what failed] — [what correct behavior is]
Run /oms-capture to extract as a training scenario? (y/n)
```

If CEO declines: log the skip in the task log under `## Capture Decision` with reason.
If CEO approves: run `/oms-capture [task-id]`.

After CEO feedback is collected and scenario decisions are logged, proceed to Step 8.5.

## Next Step Signposting

Every step output must end with a **Next:** line telling CEO what happens next. Format:

```
Next: [Step N+1 name] — [one-line description of what it does]
```

Examples:
- After Router: `Next: Round 1 — 3 agents post positions in parallel (NGT blind)`
- After Round 1: `Next: Facilitator — checks convergence, decides proceed/escalate`
- After Synthesis: `Next: Step 6 Trainer — evaluates discussion quality, writes lessons`
- After Trainer: `Next: Step 7 Context Optimizer — lightweight efficiency check`
- After Context Optimizer: `Next: Step 8 — CEO feedback + queue write`
- After `/oms all` feature: `Next: FEATURE-002 elaboration — [dept] agents`
- After `/oms all` complete: `Next: /oms-work — executes [N] tasks in dependency order`

Skip the Next line only when the pipeline is complete and there is genuinely nothing left to do.

---

## Auto-Proceed Rules

**Never ask for confirmation before Step 8.5** — if synthesis is complete and there is no CEO escalation flag, write to `cleared-queue.md` immediately. Do not output "Confirm to proceed" or any equivalent prompt. The only gates that stop the pipeline are:
- An actual CEO escalation (`escalation_required: true` from Synthesizer)
- A `hard_block` from CEO Gate
- A `cto-stop` written to the queue

Everything else proceeds automatically.

---

## LLM Model Selection Per OMS Command

Every OMS command has an optimal model. This table governs which model runs the REPL session or subprocess.

| Command | Model | Why |
|---|---|---|
| `/oms <task>` (Tier 0-1) | Sonnet | Default discussion, low complexity |
| `/oms <task>` (Tier 2) | Sonnet | Multi-agent discussion, needs reliable synthesis |
| `/oms <task>` (Tier 3) | Sonnet → Opus (Synthesizer only) | Complex reasoning at synthesis stage |
| `/oms exec` | Sonnet | C-suite strategic discussion — Sonnet handles well |
| `/oms exec` (complex: 4+ milestones, major pivot) | Opus | Deep strategic reasoning, catches edge cases in specs |
| `/oms all` | Sonnet | Sequential feature elaboration |
| `/oms think [fw]` | Sonnet | Single-agent, low overhead |
| `/oms-start` | Sonnet | Project bootstrap, agent creation |
| `/oms-start` (complex: regulated, multi-department) | Opus | Better at identifying department needs and constraints |
| `/oms-work` task (Model-hint: qwen) | Qwen-coder via LiteLLM | ≤3 files impl, has Verify, free |
| `/oms-work` task (Model-hint: qwen36) | Qwen-3.6 via LiteLLM | Research tasks, free — sonnet retry on CRO fail |
| `/oms-work` task (Model-hint: sonnet) | Sonnet | 4 files impl, infra-critical, or default |
| `/oms-work` browse QA | Sonnet | Multi-step tool chain, visual analysis |
| `/oms-audit` | Sonnet | System health check |
| `/oms-train` | Sonnet | Scenario validation |

**Key principle:** OMS discussions (where specs are born) stay on Anthropic models — spec quality is the foundation. OMS execution (where specs are implemented) can route to external LLMs because the spec already defines success criteria.

**Opus trigger conditions for OMS discussions:**
- Synthesizer: livelock confirmed by Facilitator (primary trigger — earned, not assumed)
- Synthesizer: 5+ agents AND still no convergence after round 2 (escalate, not default)
- `/oms exec` when product-direction.ctx.md has 4+ milestones with no coverage
- `/oms-start` for projects touching regulated data, payments, or 3+ departments
- CEO explicitly requests deeper analysis

**Default for 5-agent exec discussions: Sonnet.** Most C-suite discussions converge in 1–2 rounds. Only escalate to Opus if Facilitator signals deadlock or repeated position cycling.

---

## Session Budget Estimates

Calibrated against real task cost data from the autonomous pipeline ($20/5h session window as reference). Percentages are % of one full session.

| Command | Tier | Typical % | Range | Notes |
|---|---|---|---|---|
| `/oms-exec` | — | ~5% | 3–8% | C-suite only, 1-2 rounds, FEATURE drafts — no direct bot data; estimated from exec log size vs engineering tasks |
| `/oms FEATURE-NNN` | Tier 2 | ~8% | 5–12% | 2 rounds + synthesis + trainer. Real: qbank-os-docs $1.61 = 8% |
| `/oms FEATURE-NNN` | Tier 3 | ~16% | 12–22% | 3-4 rounds + synthesis + trainer. Real: qbank-os-design $3.12 = 16%, telos-schema-spec $3.25 = 16% |
| `/oms all` (N features) | — | N × 12% | — | Sequential; 3 Tier 2-3 features ≈ 36–50% |
| `/oms think [fw]` | — | ~1% | 0.5–2% | Single-agent lens, no discussion engine |
| `/oms-work` task | — | ~3% | 2–5% | Implement only — no discussion; estimate |
| `/oms-audit --quick` | — | ~2% | 1–3% | Inline scan, no subagents |
| `/oms-audit` full | — | ~10% | 8–15% | 6 parallel subagents |

**Warning signals from real data**: tasks that looped (repeated round_1 28×) consumed 21%; runaway tasks can exceed 100% of one session. If a task is still running after 20%, check for repetition.

**Planning rule**: queue high-cost tasks (Tier 3, `/oms all` with 4+ features) at the start of a session when full budget is available.

---

## CEO Display Format

**CEO sees executive summary only.** Full agent positions go to the log file — not displayed.

**After each step, display:**
```
[Step name] complete
Decision: [one sentence]
Rationale: [2-3 bullets max — agent + one-line position]
Action items: [numbered list]
Dissent: [agent: one sentence — only if present]
Next: [step name] — [what it does]
```

**Never display:**
- Full agent transcripts
- JSON blobs
- Internal pre-facilitator or stage-gate output
- Trainer evaluation detail (lesson written = silent; lesson injected to file = silent)
- Context Optimizer clean status (silent by definition)

Full discussion transcript, trainer output, and efficiency check results are written to the task log. CEO can `Read logs/tasks/[task-id].md` to inspect any step in full.

---

## Standing Rules

**Lazy log access** — only load what the current step needs:

| When | Load |
|---|---|
| Round N | Only `## Round 1` through `## Round N-1` sections |
| Synthesis | All round sections (not headers/preamble) |
| Doc/summary | `oms-history.md` first; specific task log only if needed |

**Always reference logs for docs** — never write from memory alone. `oms-history.md` is the index; task logs are the detail.

---

## Error Handling
- Invalid JSON from agent → re-run with schema reminder
- Stage-Gate 2 failure → re-run failing agent before Round 2
- Router cannot route → ask CEO for more context
- Stage-Gate 4 failure → re-run Synthesizer with traceability instruction
- Hard cap hit → synthesize from best available; escalate if unresolved disagreement is consequential
- Memory write fails → log skip, continue (non-blocking)
