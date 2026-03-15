# OMS — One Man Show

Orchestrates the one-man-show multi-agent discussion engine. Invoked via `/oms` followed by your intent.

## Invocation Modes

| Input | Mode |
|---|---|
| `/oms <task>` | **Task** — default |
| `/oms read <file/url>` | **Onboard** — team reads material, surfaces questions |
| `/oms discover` | **Discover** — explicit project bootstrap |
| `/oms add <role> to the team` | **Task** — route to CTO + EM |

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

---

## Before Running

**Always load:**
- `~/.claude/memory/MEMORY.md` + relevant topic files
- `~/.claude/agents/engine/discussion-rules.md`
- `~/.claude/agents/engine/synthesis-prompt.md`
- `~/.claude/agents/engine/escalation-format.md`
- `~/.claude/agents/shared-context/product/company-direction.md`
- `~/.claude/agents/shared-context/product/product-direction.md`
- `~/.claude/agents/shared-context/engineering/architecture.md`
- `~/.claude/agents/shared-context/engineering/cross-agent-patterns.md`

**Load if exists:** project memory + topic files, `.claude/codemap.md`, project agent ctx files.

**Scoped context per agent** — never give everyone everything:

| Role | Shared context | codemap |
|---|---|---|
| router | all | ✓ |
| facilitator | all | — |
| synthesizer | none (reads from disk log) | — |
| cto | architecture.md, tech-stack.md, cross-agent-patterns.md | — |
| product-manager | company-direction.md, product-direction.md | — |
| engineering-manager | architecture.md, company-direction.md | — |
| backend-developer | tech-stack.md, architecture.md | ✓ |
| frontend-developer | tech-stack.md | ✓ |
| qa-engineer | tech-stack.md | ✓ |
| trainer | none — receives validation-criteria.md | — |

**Context mode**: Router detects `task_mode`, reads the matching `~/.claude/contexts/[mode].md` once, and distills per-agent `agent_briefings` (1–2 sentences each). Never pass the full context file to agents.

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
| facilitator | `~/.claude/agents/facilitator/persona.md` | `facilitator/lessons.md` | `facilitator/MEMORY.md` | Sonnet | After each round (Tier 2+) |
| verification | `~/.claude/agents/verification/persona.md` | `verification/lessons.md` | `verification/MEMORY.md` | Sonnet | On-demand |
| synthesizer | `~/.claude/agents/synthesizer/persona.md` | `synthesizer/lessons.md` | `synthesizer/MEMORY.md` | Sonnet (Opus: 5+ or livelock) | Step 4 (Tier 2+) |
| trainer | `~/.claude/agents/trainer/persona.md` | `trainer/lessons.md` | `trainer/MEMORY.md` | Sonnet | Step 6 — always |

### Discussion Roster (V1)
| Role | File | Lessons | ctx | Memory |
|---|---|---|---|---|
| cto | `~/.claude/agents/cto/persona.md` | `cto/lessons.md` | `cto.ctx.md` | `cto/MEMORY.md` |
| product-manager | `~/.claude/agents/product-manager/persona.md` | `product-manager/lessons.md` | `product-manager.ctx.md` | `product-manager/MEMORY.md` |
| engineering-manager | `~/.claude/agents/engineering-manager/persona.md` | `engineering-manager/lessons.md` | `engineering-manager.ctx.md` | `engineering-manager/MEMORY.md` |
| frontend-developer | `~/.claude/agents/frontend-developer/persona.md` | `frontend-developer/lessons.md` | `frontend-developer.ctx.md` | `frontend-developer/MEMORY.md` |
| backend-developer | `~/.claude/agents/backend-developer/persona.md` | `backend-developer/lessons.md` | `backend-developer.ctx.md` | `backend-developer/MEMORY.md` |
| qa-engineer | `~/.claude/agents/qa-engineer/persona.md` | `qa-engineer/lessons.md` | `qa-engineer.ctx.md` | `qa-engineer/MEMORY.md` |

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

---

## Task ID
Every task: `YYYY-MM-DD-short-slug` (kebab-case, max 6 words, from Router output)
Log path: `logs/tasks/[task-id].md`

---

## Step 1 — Router
Run Router (Haiku):
- Input: CEO intent + all shared context + codemap + project memory + ctx files
- Output must include: `task_id`, `tier`, `activated_agents`, `domain_lead`, `primary_recommender`, `complexity`, `round_cap`, `triz_contradiction`, `premortem_failure_modes`, `agent_briefings`, `stage_gate`, `locked: true`

If `clarifying_questions`: present to CEO, collect answers, re-run Router.
If `stage_gate: "failed"`: fix noted gap, re-run Router.

## Step 1.5 — Path Diversity *(Tier 2+ only)*
Run Path Diversity (Haiku):
- Input: task description + `activated_agents` + `task_mode` + pre-mortem
- Output: N structurally distinct paths, one per agent, each with a different `key_assumption`

If `skip: true`: proceed without seeding. Otherwise inject each agent's path as a "Starting frame to consider" block in their Round 1 prompt. Log paths to task log under `## Path Diversity Seeds` — no CEO display.

## Step 2 — Round 1 (NGT Blind)
Run activated agents **in parallel**. Each receives: persona + MEMORY + scoped shared context + agent_briefing + path seed (if Tier 2+) + pre-mortem block.

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

**Tier 2/3**: Run Facilitator (Sonnet):
- Input: Round 1 outputs + `domain_lead` + `primary_recommender`
- Facilitator runs per `facilitator/persona.md`: Stage-Gate 2, position distribution (Delphi), DA check, epistemic act tracking, proceed_to
- Follow `proceed_to` into Step 3 or Step 4

## Step 3 — Rounds 2+ *(Tier 2+ only)*
For each round:
1. Write `[task-id].checkpoint`: `round=N status=running`
2. Read only `## Round N-1` sections from log (lazy load)
3. Run agents in parallel — each receives: full history from disk + Facilitator's `position_distribution` + any `injections`
4. Collect outputs → checkpoint write `status=complete`
5. Run Facilitator — follow `proceed_to`:
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
- Instruction: "Evaluate this completed task per the tier scope. For each agent, check their lessons.md before classifying — a lesson already present there should be classified as `channel: scenario`, not re-written."

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
