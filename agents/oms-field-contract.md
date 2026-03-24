# OMS Field Contract

## Purpose

Single source of truth for all required output fields across the OMS pipeline. Every agent, every checkpoint field, every step output is listed here with its consumer, blocking status, and current validation state.

**Rule**: any change to an OMS skill, agent persona, or dispatcher that adds, removes, or renames a field must update this file first. This is the type system. Missing a required field here is a blocking criterion (FC1).

**Validation**: Trainer checks against this on every task. Router and Synthesizer self-check their Stage-Gates against it. `/oms-train` runs FC1 as a blocking criterion across all scenarios.

---

## Stage 1 — Router Output

**Written to**: `oms-checkpoint.json` + passed directly to discussion agents
**Consumed by**: `oms-dispatcher.sh` (round dispatch), each activated discussion agent (briefings)

| Field | Type | Null OK | Blocking | Consumer reads | Validated |
|---|---|---|---|---|---|
| `task_id` | string | no | yes | dispatcher: checkpoint key, log filename | Stage-Gate 1 |
| `tier` | 0\|1\|2\|3 | no | yes | dispatcher: Facilitator/Path-Diversity skip rules | R6 |
| `complexity` | simple\|compound\|complex | no | no | trainer: complexity_assessment_accurate | R2 |
| `rounds_required` | integer 1–4 | no | **yes** | dispatcher: when to advance round_N → synthesis | **R8** (blocking) |
| `activated_agents` | string[] | no | yes | dispatcher: builds round prompts for each | R1, R7 |
| `agent_briefings` | object | no | yes | each agent: receives their briefing | R5 |
| `locked` | true | no | yes | signals roster is final; dispatcher rejects unlocked output | Stage-Gate 1 |
| `stage_gate` | passed\|failed | no | yes | dispatcher: aborts task on "failed" | Stage-Gate 1 |
| `briefing_mode` | thin\|fat | no | yes | dispatcher: determines context injection depth | Stage-Gate 1 |
| `premortem_failure_modes` | string[2–3] | no | no | trainer: pre-mortem quality | R5 |
| `overlap_flags` | array | no | no | trainer: boundary discipline | Stage-Gate 1 |
| `why_chain` | object\|omitted | yes | no | discussion agents (fat mode only) | Stage-Gate 1 |
| `context_files` | string[] | yes | no | dispatcher: loads matching ~/.claude/contexts/ files | CM1, CM2 |

**Stage-Gate 1 required**: `task_id`, `tier`, `rounds_required`, `activated_agents`, `agent_briefings`, `locked: true`, `stage_gate: "passed"`, `briefing_mode`

---

## Stage 2 — Discussion Agent Output (all rounds)

**Written by**: all activated discussion agents
**Consumed by**: Facilitator (consensus scoring), Synthesizer (positions + reasoning), Trainer (engagement evaluation)

Base schema from `shared-context/discussion-schema.md`. All fields below are **per-round per-agent**.

| Field | Type | Null OK | Round | Blocking | Consumer reads | Validated |
|---|---|---|---|---|---|---|
| `position` | string (1 sentence) | no | all | yes | Synthesizer: synthesis input | O1 |
| `reasoning` | string[] (≥2 claims) | no | all | yes | Synthesizer: rationale citations; Trainer: reasoning quality | O2 |
| `confidence_level` | high\|medium\|low | no | all | yes | Facilitator: consensus delta | CD1 |
| `confidence_pct` | int 0–100 | no | all | yes | Facilitator: numeric consensus score | CD1 |
| `warrant` | string | no | all | no | Trainer: argument quality | O2 |
| `anticipated_rebuttals` | string[] | no | all | no | Trainer: engagement anticipation | O2 |
| `position_delta.changed` | boolean | no | all | yes | Trainer: M1/E2 check | E2, E3 |
| `position_delta.challenged_by` | string\|null | null in R1 | 2+ | yes | Trainer: E3 (why_held required if non-null) | E3 |
| `position_delta.why_held` | string\|null | null in R1 | 2+ | yes (if challenged) | Trainer: E3 failure if empty when challenged | E3 |
| `position_delta.change_type` | enum\|null | null if !changed | 2+ | yes (if changed) | Trainer: E2 | E2 |
| `position_delta.change_basis` | enum\|null | null if !changed | 2+ | yes (if changed) | Trainer: M1 (social_pressure = instant fail) | E4, M1 |
| `position_delta.source_agent` | string\|null | null if !changed | 2+ | no | Trainer: engagement trace | E2 |
| `position_delta.source_argument` | string\|null | null if !changed | 2+ | no | Trainer: E2 (empty = fail) | E2 |

**Role-specific required fields** (O3):
- CTO: `frame_challenge` (when PF1/PF2 triggered — optional otherwise)
- Backend Dev: `proposed_api` (when API surface is in scope)
- QA: `risk_level`
- PM: `user_need_served`
- EM: `delivery_feasibility`

---

## Stage 3 — Facilitator Output

**Written by**: `facilitator/persona.md`
**Consumed by**: `oms-dispatcher.sh` (proceed_to → next step), discussion agents (injections broadcast back)

| Field | Type | Null OK | Blocking | Consumer reads | Validated |
|---|---|---|---|---|---|
| `proceed_to` | next_round\|synthesis\|ceo_gate | no | yes | dispatcher: decides round_N+1 vs synthesis | F3 |
| `consensus_reached` | boolean | no | yes | dispatcher: gates synthesis trigger | F3 |
| `position_distribution` | object | no | no | Trainer: convergence assessment | — |
| `injections` | array | yes | no | dispatcher: broadcasts to discussion agents | F4 |
| `convergence_note` | string\|null | yes | no | Trainer: premature convergence check | C1 |
| `round_count` | integer | no | yes | dispatcher: validates against rounds_required | F3 |

---

## Stage 4 — Synthesizer Output

**Written by**: `synthesizer/persona.md` → `logs/tasks/[task-id].md`
**Consumed by**: `oms-dispatcher.sh` (task log write, advance to implement), `oms-implement/SKILL.md` (reads decision + action_items)

| Field | Type | Null OK | Blocking | Consumer reads | Validated |
|---|---|---|---|---|---|
| `task_id` | string | no | yes | log filename; oms-implement: load context | Stage-Gate 4 |
| `decision` | string (1 sentence) | no | yes | oms-implement: Step 1 plan summary | C2, Stage-Gate 4 |
| `action_items` | string[] | no | yes | oms-implement: Step 1.5 dependency analysis, Step 2 | C4, Stage-Gate 4 |
| `rationale` | string[] | no | no | Trainer: claim traceability | Stage-Gate 4 |
| `dissent` | array | yes | no | oms-implement: Step 2 agent context | C3 |
| `reopen_conditions` | array | yes | no | oms-implement: Step 2 scope guard | — |
| `activated_agents` | string[] | no | no | Trainer: tier scope | — |
| `acceptance_criteria` | array | yes | no | oms-implement: Step 2.5 Evidence QA | — |
| `owner_map` | object | no | no | action_items owner assignment | C4 |

**Stage-Gate 4 required**: `task_id`, `decision`, `action_items[]` (non-empty), `rationale[]` (≥1 entry), `stage_gate: "passed"`

---

## Stage 5 — Trainer Output

**Written by**: `trainer/persona.md`
**Consumed by**: `[agent]/lessons.md` writes, `shared-lessons/[category].md`, `results.tsv` (training mode)

| Field | Type | Null OK | Blocking | Consumer reads | Validated |
|---|---|---|---|---|---|
| `task_id` | string | no | yes | log correlation | — |
| `overall_discussion_quality` | good\|mixed\|poor | no | no | team-level trend | — |
| `agent_evaluations` | array | no | yes | per-agent coaching notes | T1 |
| `lesson_candidates` | array | yes | no | lessons.md writes | T1 |
| `complexity_assessment_accurate` | boolean | no | no | Router R2 calibration | T4 |
| `recommended_persona_changes` | array | yes | no | CEO approval chain | — |
| `criteria_gaps` | array | yes | no | validation-criteria.md updates | T3 |
| `meta_retrospective_due` | boolean | no | no | triggers 5-task pattern note | — |

**Lesson format required** (T1): `[date] | [task-id] | importance:[level] | [imperative sentence]` + `Surfaces when:` line. Lesson written without this format fails T1.

---

## Stage 6 — Context Optimizer Output

**Written by**: `context-optimizer/persona.md`
**Consumed by**: `oms-dispatcher.sh` (checkpoint write), CEO approval gate (dangerous trims)

| Field | Type | Null OK | Blocking | Consumer reads | Validated |
|---|---|---|---|---|---|
| `status` | clean\|trimmed\|flagged | no | yes | dispatcher: continue vs pause | — |
| `over_activated_agents` | array | yes | no | Trainer: R7 calibration | — |
| `pipeline_integrity_signals` | array | yes | no | CEO: escalation context | — |
| `actions_taken` | array | yes | no | CEO: trim audit | — |
| `ceo_approval_required` | boolean | no | yes | dispatcher: pause if true | — |

---

## Checkpoint Fields (`oms-checkpoint.json`)

**Written by**: `oms-dispatcher.sh` + `oms-post-step.py`
**Consumed by**: `oms-dispatcher.sh` on every invocation (resume, skip, force-advance)

| Field | Type | Null OK | Blocking | Written by | Notes |
|---|---|---|---|---|---|
| `next` | string | no | yes | dispatcher force-advance | validated against allowlist after every write — invalid value → `pipeline_frozen` immediately |
| `task_id` | string | no | yes | dispatcher at router step | checkpoint filename key |
| `session_id` | string | yes | no | oms-post-step.py | used for --resume; cleared on fallback |
| `rounds_required` | integer | no | yes | oms-post-step.py from Router output | R8 — dispatcher defaults to 3 if missing (masked failure) |
| `steps_written` | string[] | yes | no | oms-post-step.py | idempotency guard for cpo_backlog, trainer |
| `frozen_step` | string | yes | no | _freeze_pipeline() | set on pipeline_frozen; consumed by skip handler |
| `slug` | string | no | yes | dispatcher | project identifier |

---

## Watcher — Pipeline Integrity Agent

**Fires when**: `pipeline_frozen` written to checkpoint (both trigger points)
**Consumed by**: dispatcher (calls `oms-watcher.py` at each freeze point)
**Source of truth for bugs**: `~/.claude/agents/watcher/bug-list.md`

| Field | Type | Null OK | Blocking | Notes |
|---|---|---|---|---|
| `fix_attempts` | object | yes | no | keyed by `{bug_id}:{frozen_step}:{task_id}` — max 2 auto-fixes per key |
| `frozen_step` | string | yes | no | set on freeze, cleared on successful fix |

**Loop mitigation**: `fix_attempts[key] >= 2` → escalate to CEO, do not retry.

---

## FC1 — Field Contract Validation (new blocking criterion)

**Added to**: `validation-criteria.md` under Concern 4 — Output Quality
**Applies to**: all modes (engineering, research, exec)

**FC1**: All required fields listed in `oms-field-contract.md` for each stage must be non-null in agent output. A missing required field is a blocking failure regardless of whether downstream steps have fallbacks. Fallbacks mask the failure — they do not fix it.

**FC2**: Stage-Gate checklists must include at least one check per blocking field listed in this contract. A Stage-Gate that passes without verifying blocking fields fails FC2.

---

## Change → Required Updates

When a field changes, these are the minimum files that must also be updated:

| What changed | Files to update |
|---|---|
| New field on any stage boundary | This file (add row) → agent Stage-Gate checklist → Trainer blocking criteria if blocking |
| Field removed or renamed | This file → agent Stage-Gate → all downstream consumers (dispatcher prompts, agent personas that read it) → training scenarios that assert the field |
| `next` allowlist entry added/removed | This file → dispatcher allowlist in `oms-dispatcher.sh` |
| Dispatcher force-advance table entry added | This file (checkpoint section) → dispatcher pre-step validation (add required input field check) |
| New OMS step added to pipeline | This file (new stage or checkpoint row) → dispatcher: case statement + force-advance table + pre-step validation + allowlist + model selection |
| Agent output schema field added | This file → agent's Stage-Gate checklist → `discussion-schema.md` (if shared field) → training scenario that tests the agent |
| Training scenario references a field | This file → scenario's `Criteria tested` list must include FC1 if testing contract compliance |

**Rule**: a dispatcher fallback that defaults a missing field is evidence of a contract gap — add the field to this file and the upstream Stage-Gate before adding the fallback.

## Update Protocol

When any of the following changes, update this file **before** merging:
- New field added to any agent JSON schema
- Existing field removed or renamed
- A downstream consumer starts reading a new field
- A fallback is added in the dispatcher (signals a contract gap — add the field here)
- A new OMS skill (oms-implement, oms-train, etc.) reads agent output

**Who updates**: the person/agent making the OMS change.
**Who verifies**: Trainer evaluates FC1/FC2 in next `/oms-train` run after the change.
