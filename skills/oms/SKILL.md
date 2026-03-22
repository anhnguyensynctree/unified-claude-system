---
name: oms
description: Orchestrate a one-man-show multi-agent discussion. Usage: /oms followed by your intent.
---
# OMS — One Man Show

Orchestrates the one-man-show multi-agent discussion engine. Invoked via `/oms` followed by your intent.

## Invocation Modes

| Input | Mode |
|---|---|
| `/oms <task>` | **Task** — default |
| `/oms read <file/url>` | **Onboard** — team reads material, surfaces questions |
| `/oms discover` | **Discover** — explicit project bootstrap |
| `/oms add <role> to the team` | **Task** — route to CTO + EM |
| `/oms exec` | **Exec** — C-suite strategic discussion; auto-triggered at milestones |

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
- Tier 2+: `~/.claude/agents/engine/synthesis-prompt.md`, `~/.claude/agents/engine/escalation-format.md`
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
| Role | File | Lessons | Memory | Model | When |
|---|---|---|---|---|---|
| router | `~/.claude/agents/router/persona.md` | `router/lessons.md` | `router/MEMORY.md` | Haiku | Step 1 |
| path-diversity | `~/.claude/agents/path-diversity/persona.md` | `path-diversity/lessons.md` | `path-diversity/MEMORY.md` | Haiku | Step 1.5 (Tier 2+) |
| pre-facilitator | *(inline — no persona file)* | — | — | Haiku | Before full Facilitator each round (Tier 2+) |
| facilitator | `~/.claude/agents/facilitator/persona.md` | `facilitator/lessons.md` | `facilitator/MEMORY.md` | Sonnet | After each round (Tier 2+, when pre-facilitator requires it) |
| verification | `~/.claude/agents/verification/persona.md` | `verification/lessons.md` | `verification/MEMORY.md` | Sonnet | On-demand |
| ceo-gate | `~/.claude/agents/ceo-gate/persona.md` | — | `ceo-gate/MEMORY.md` | Haiku | Step 3.5 (Tier 1+) — always a quick pass, escalates on match |
| synthesizer | `~/.claude/agents/synthesizer/persona.md` | `synthesizer/lessons.md` | `synthesizer/MEMORY.md` | Sonnet (Opus: 5+ or livelock) | Step 4 (Tier 2+) |
| trainer | `~/.claude/agents/trainer/persona.md` | `trainer/lessons.md` | `trainer/MEMORY.md` | Sonnet | Step 6 — always |

### Discussion Roster (V1)

**Engineering agents** — activated for `build`, `architecture`, `debug`, `plan`, `refactor`, `security`, `test`, `performance`, `ui-ux` tasks:

| Role | File | Lessons | ctx | Memory |
|---|---|---|---|---|
| cto | `~/.claude/agents/cto/persona.md` | `cto/lessons.md` | `cto.ctx.md` | `cto/MEMORY.md` |
| product-manager | `~/.claude/agents/product-manager/persona.md` | `product-manager/lessons.md` | `product-manager.ctx.md` | `product-manager/MEMORY.md` |
| engineering-manager | `~/.claude/agents/engineering-manager/persona.md` | `engineering-manager/lessons.md` | `engineering-manager.ctx.md` | `engineering-manager/MEMORY.md` |
| frontend-developer | `~/.claude/agents/frontend-developer/persona.md` | `frontend-developer/lessons.md` | `frontend-developer.ctx.md` | `frontend-developer/MEMORY.md` |
| backend-developer | `~/.claude/agents/backend-developer/persona.md` | `backend-developer/lessons.md` | `backend-developer.ctx.md` | `backend-developer/MEMORY.md` |
| qa-engineer | `~/.claude/agents/qa-engineer/persona.md` | `qa-engineer/lessons.md` | `qa-engineer.ctx.md` | `qa-engineer/MEMORY.md` |

**Research C-Suite** — activated for all `research` tasks and `exec` tasks as domain lead:

| Role | File | Lessons | Memory | Domain |
|---|---|---|---|---|
| chief-research-officer | `~/.claude/agents/chief-research-officer/persona.md` | `chief-research-officer/lessons.md` | `chief-research-officer/MEMORY.md` | Research direction, cross-disciplinary synthesis, research-to-product translation |

**New C-Suite** — activated for `exec` tasks and tasks within their domain scope:

| Role | File | Lessons | Memory | Domain |
|---|---|---|---|---|
| cpo | `~/.claude/agents/cpo/persona.md` | `cpo/lessons.md` | `cpo/MEMORY.md` | Product direction, research-to-product translation, roadmap ownership |
| clo | `~/.claude/agents/clo/persona.md` | `clo/lessons.md` | `clo/MEMORY.md` | All legal — compliance, contracts, IP, privacy, platform ToS |
| cfo | `~/.claude/agents/cfo/persona.md` | `cfo/lessons.md` | `cfo/MEMORY.md` | All finance — cost tracking, revenue, P&L, unit economics |

**Domain Research Agents** — project-scoped; only available if declared in `.claude/agents/company-hierarchy.md`. PhD-equivalent, 40+ years expertise standard.

Core research agents (likely in most research projects):
| Role | File | Lessons | Memory | Research Question |
|---|---|---|---|---|
| human-behavior-researcher | `~/.claude/agents/human-behavior-researcher/persona.md` | `human-behavior-researcher/lessons.md` | `human-behavior-researcher/MEMORY.md` | How and why do people behave, decide, and change? |
| data-intelligence-analyst | `~/.claude/agents/data-intelligence-analyst/persona.md` | `data-intelligence-analyst/lessons.md` | `data-intelligence-analyst/MEMORY.md` | What do our metrics and patterns actually tell us? |

Domain specialist agents (project-scoped per company-hierarchy):
| Role | File | Lessons | Memory | Research Question |
|---|---|---|---|---|
| content-platform-researcher | `~/.claude/agents/content-platform-researcher/persona.md` | `content-platform-researcher/lessons.md` | `content-platform-researcher/MEMORY.md` | How does content perform on this platform and why? |
| clinical-safety-researcher | `~/.claude/agents/clinical-safety-researcher/persona.md` | `clinical-safety-researcher/lessons.md` | `clinical-safety-researcher/MEMORY.md` | What psychological risks exist and how do we protect users? |
| language-communication-researcher | `~/.claude/agents/language-communication-researcher/persona.md` | `language-communication-researcher/lessons.md` | `language-communication-researcher/MEMORY.md` | How should this be phrased, structured, and conveyed? |
| philosophy-ethics-researcher | `~/.claude/agents/philosophy-ethics-researcher/persona.md` | `philosophy-ethics-researcher/lessons.md` | `philosophy-ethics-researcher/MEMORY.md` | What are the ethical implications and what does this mean? |
| cultural-historical-researcher | `~/.claude/agents/cultural-historical-researcher/persona.md` | `cultural-historical-researcher/lessons.md` | `cultural-historical-researcher/MEMORY.md` | What do culture, history, and social structures tell us? |
| biological-evolutionary-researcher | `~/.claude/agents/biological-evolutionary-researcher/persona.md` | `biological-evolutionary-researcher/lessons.md` | `biological-evolutionary-researcher/MEMORY.md` | What biological and evolutionary forces shape this? |

Domain research agents carry universal domain knowledge — no ctx.md. Project-specific context is injected via `.claude/agents/research.ctx.md` on research tasks. Domain researchers do not replace engineering agents on implementation tasks but may join them when the task has a human-understanding dimension.

Each agent's effective prompt = persona.md + lessons.md + ctx.md (if exists) + MEMORY.md + `agent_briefings.[role]` from Router.

**Load order**: persona.md (identity) → lessons.md (learned behaviors) → ctx.md + MEMORY.md (task context) → agent_briefing (task distillation).

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
E. Each agent writes what they learned to their `MEMORY.md` under `## Onboarding: [project] | [date]`

Trainer does not evaluate onboarding sessions.

## Exec Mode — `/oms exec` or auto-triggered at milestone

The executive discussion. C-suite meets to evaluate product direction, translate research insights into product bets, and surface strategic decisions. CEO is NOT in the room — exec produces a recommendation that goes TO the CEO.

**Roster**: CPO (domain lead), CTO, CRO, CLO, CFO — all always active in exec discussions.
**Facilitator**: always runs. Same open-discussion format as engineering tasks.
**Synthesizer**: always runs. Output is a recommendation brief, not an implementation plan.
**Trainer**: evaluates after every exec session.

**Auto-trigger conditions** (Router detects and fires oms exec automatically):
- A milestone defined in `product-direction.ctx.md` has been reached
- Research has produced a synthesis that requires a product direction decision
- Any C-suite agent raises a cross-department concern during a task discussion
- CLO raises a `high` or `critical` legal risk in any discussion

**Exec output to CEO** (3–5 bullets max):
- What was decided and why (one sentence each)
- Any tough decisions requiring CEO approval (escalated only if C-suite cannot resolve)
- `product-direction.ctx.md` updated by CPO post-exec

**Exec context** — Router loads for exec tasks:
- `company-belief.ctx.md` (all C-suite read this)
- `product-direction.ctx.md` (CPO leads, all read)
- All department C-suite personas

---

## Task ID
Every task: `YYYY-MM-DD-short-slug` (kebab-case, max 6 words, from Router output)
Log path: `logs/tasks/[task-id].md`

---

## OMS Scope Rule
**OMS is for decisions, not execution.** It answers: "What should we build and why?" — not "How do we build it right now?"

- `/oms <task>` → produces a synthesis with `action_items[]`
- Implementation follows separately: direct coding, or `/oms-implement` (runs post-synthesis only)
- Never invoke `/oms implement ...` — implementation inputs are wasted ceremony after architecture is settled
- If the task is already decided and you have `action_items`: skip OMS entirely, go implement

---

## Step 1 — Router
Run Router (Haiku):
- Input: CEO intent + all shared context + codemap + project memory + ctx files
- Output must include: `task_id`, `tier`, `activated_agents`, `domain_lead`, `primary_recommender`, `complexity`, `round_cap`, `triz_contradiction`, `premortem_failure_modes`, `agent_briefings`, `briefing_mode`, `why_chain` (if company context is real), `stage_gate`, `locked: true`

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

**Checkpoint**: append Round 1 outputs to `logs/tasks/[task-id].md` immediately.

Display to CEO:
```
Round 1
[Agent]: [position]
```

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
7. Display: one line per agent — position + changed flag

Continue until `proceed_to: "synthesis"` or hard cap (5 rounds).

## Step 4 — Synthesizer *(Tier 2+ only)*
Run Synthesizer (Sonnet; Opus if 5+ agents or livelock):
- Input: full log from disk (all rounds) + Router's `domain_lead` / `primary_recommender` / `activated_agents` + Facilitator `capitulation_flags` + per-agent `confidence_pct` per round
- Instruction: "Synthesize. Cite agent + round for every rationale claim. Apply reversibility gate. Derive reopening conditions."

**Stage-Gate 4**: verify all `rationale[]` entries cite agent + round. If any uncited → re-run Synthesizer with traceability instruction.

If `reversibility_gate: "escalated"` → present decision brief to CEO (both options, evidence, confidence note). Do not override.
If `escalation_required: true` → package per `escalation-format.md`.
Otherwise: present `decision`, `rationale`, `action_items`, `dissent[]`, `reopen_conditions[]` to CEO.

## Step 5 — Log
Append final synthesis to `logs/tasks/[task-id].md`. Delete `[task-id].checkpoint`.

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
Decision: [one sentence]  Agents: [list]  Tier: N  Log: logs/tasks/[task-id].md
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

2. **Inject memory facts** — for each evaluated agent:
   ```bash
   python3 ~/.claude/agents/memory/agent-mem-extract.py inject [agent] "fact"
   ```

3. **Write cross-agent patterns** — if `cross_agent_patterns` non-empty: append to `shared-context/engineering/cross-agent-patterns.md`

4. **Flag scenario candidates** — collect all `lesson_candidates` with `channel: "scenario"` → pass to Step 8

If `complexity_assessment_accurate: false`: inject correction to Router memory.
If `meta_retrospective_due: true`: notify CEO — "Run `/compact-agent-memory [agent]`."

## Step 7 — Compact Check
```bash
python3 ~/.claude/agents/memory/agent-mem-extract.py check
```
Over threshold → tell CEO: "[role] memory is [N] lines — run `/compact-agent-memory [role]` when convenient."

## Step 8 — CEO Feedback + Scenario Capture

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

---

## Standing Rules

**Lazy log access** — only load what the current step needs:

| When | Load |
|---|---|
| Round N | Only `## Round 1` through `## Round N-1` sections |
| Synthesis | All round sections (not headers/preamble) |
| Doc/summary | `oms-history.md` first; specific task log only if needed |
| Status check | `.checkpoint` file only |

**Always reference logs for docs** — never write from memory alone. `oms-history.md` is the index; task logs are the detail.

---

## Error Handling
- Invalid JSON from agent → re-run with schema reminder
- Stage-Gate 2 failure → re-run failing agent before Round 2
- Router cannot route → ask CEO for more context
- Stage-Gate 4 failure → re-run Synthesizer with traceability instruction
- Hard cap hit → synthesize from best available; escalate if unresolved disagreement is consequential
- Memory write fails → log skip, continue (non-blocking)
