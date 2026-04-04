# OMS Work Task Schema

Three-layer hierarchy: **Milestone → Feature → Task**

- **Milestone** — product outcome. Owned by CPO. Lives in `product-direction.ctx.md`.
- **Feature** — self-contained capability advancing a milestone. CPO writes. Has its own acceptance criteria. Cross-functional features produce one task per department.
- **Task** — one agent session unit. Full OpenSpec. Written after engineering discussion.

`/oms-work` only executes `queued` tasks. Features are tracked in `cleared-queue.md` alongside tasks.

---

## Feature Format (written by exec Step 8.5 — CPO authors)

```
## FEATURE-NNN — [title]
- **Status:** draft
- **Milestone:** [milestone name from product-direction.ctx.md]
- **Type:** product | engineering | research | cross-functional
- **Departments:** [list of departments involved — e.g. backend-developer, chief-research-officer]
- **Research-gate:** true | false
- **Why:** [exec rationale — one sentence]
- **Exec-decision:** [hard constraint the engineering discussion must respect — cannot be overturned]
- **Acceptance:** [what done looks like at feature level — CPO-readable, non-technical]
- **Validation:** cpo | cpo + cto | cpo + cro | cpo + cro + cto
- **Tasks:** none (populated after /oms <feature> discussion)
- **Context-hints:** [files the feature discussion agents should read]
```

**Research-gate rule:**
- `Research-gate: true` — engineering tasks stay `draft` until ALL research tasks in this feature are `done` AND CRO signs off. Engineering elaboration cannot happen before research findings land.
- `Research-gate: false` — departments work in parallel; interface-contract is agreed upfront in the feature discussion.

**When to set Research-gate: true:**
- Engineering cannot be specified without knowing what research finds (chain_type: direction_selection)
- The feature's Acceptance criteria depends on a research output (e.g. "pipeline correctly weights X" requires knowing what X is)

**When Research-gate: false (parallel):**
- Interface between departments is known upfront — agreed in the feature OMS discussion
- Research is validating a known approach, not discovering a new one

Feature status values:
```
draft → in-progress (first task queued) → done (all tasks done + validation sign-off)
```

Feature done = all its tasks are `done` + CPO (+CTO or +CRO if required) sign off.
All features in a milestone done = milestone done → CPO updates `product-direction.ctx.md`.

---

## Task Draft Format (written by /oms <feature> Step 8.5 — before elaboration)

For cross-functional features, one draft per department. For single-domain features, one draft.

```
## TASK-NNN — [title]
- **Status:** draft
- **Feature:** FEATURE-NNN
- **Milestone:** [milestone name — copied from feature]
- **Department:** backend | frontend | qa | data | research | cto
- **Type:** impl | research
- **Infra-critical:** true | false
- **Interface-contract:** [shared interface agreed in feature discussion — what this task must produce or consume]
- **Depends:** none | TASK-NNN
```

Draft tasks are elaborated into queued tasks by the Task Elaboration Agent.

---

## Task Queued Format (written by Task Elaboration Agent after /oms <feature>)

**REQUIRED FIELDS** — All fields below must be present and non-empty. Validated and auto-synced by `~/.claude/hooks/schema-sync-hook.sh`.

```
## TASK-NNN — [title]
- **Status:** queued
- **Feature:** FEATURE-NNN
- **Milestone:** [milestone name]
- **Department:** backend | frontend | qa | data | research | cto
- **Type:** impl | research | gate
- **Infra-critical:** true | false
- **Spec:** The system SHALL [verb] [object] so that [outcome].
- **Scenarios:** GIVEN [precondition] WHEN [trigger] THEN [outcome] | GIVEN ...
- **Artifacts:** [src/path/file.ts — exports: foo, bar] | [src/path/other.ts — exists with real impl]
- **Produces:** [interface/export/file downstream tasks depend on] | none
- **Verify:** [npm test src/path] | [npm run lint]
- **Context:** [path/to/file.ts, path/to/other.md]
- **Activated:** [agent, agent, ...]
- **Validation:** [agent → agent → agent]
- **Depends:** none | TASK-NNN
- **File-count:** [N] — number of files in Artifacts
- **Model-hint:** qwen-coder | qwen | llama | gpt-oss | nemotron | gemma | stepfun — **REQUIRED, auto-derived from task characteristics, enforced by validation hook**
- **Script-model:** qwen-coder | qwen | llama | gpt-oss | nemotron | gemma | stepfun | omit — model the script's subprocess calls use (required if task produces a long-running script)
- **Script-timeout:** 120s | 150s | 180s | omit — per-call timeout for subprocess inside the script (OpenRouter free tier: 120-180s)
- **Script-partial-results:** true | false | omit — must be true if script loops over N items and calls a slow subprocess
```

---

## Gate Task Format (auto-appended — one per milestone, last task)

Gate tasks are not authored through the OMS feature discussion. They are auto-appended to `cleared-queue.md` by the exec agent at milestone planning time — one per milestone, always the final task.

```
## TASK-NNN — Milestone Gate — [milestone name]
- **Status:** queued
- **Feature:** FEATURE-NNN
- **Milestone:** [milestone name]
- **Department:** qa
- **Type:** gate
- **Infra-critical:** false
- **Spec:** The system SHALL pass all E2E scenarios for Milestone [X] with zero failures so that the milestone is closed.
- **Scenarios:** GIVEN all milestone tasks are done WHEN full E2E suite runs THEN 0 test failures AND qa/milestones/[milestone-slug].json is written
- **Artifacts:** qa/milestones/[milestone-slug].json — milestone closed sentinel
- **Produces:** qa/milestones/[milestone-slug].json — milestone gate passed
- **Verify:** ~/.claude/bin/ctx-exec "failing tests" pnpm exec playwright test | ~/.claude/bin/ctx-exec "gate file" ls qa/milestones/[milestone-slug].json
- **Context:** [e2e spec files for this milestone]
- **Activated:** qa
- **Validation:** qa → cpo
- **Depends:** [all final task IDs in milestone, comma-separated]
- **File-count:** 1
- **Model-hint:** sonnet
```

**Gate rules:**
- One gate task per milestone — never per feature
- `Depends` lists ALL final tasks in the milestone (not just direct predecessors)
- `Type: gate` always routes to `sonnet` (Anthropic subscription) — never OpenRouter free models. Gate runs on subscription for reliability and speed.
- When the gate task reaches `done`: the milestone is closed, CPO updates `product-direction.ctx.md`
- Gate task failure = milestone stays open — no partial milestone close allowed
- The sentinel file `qa/milestones/[milestone-slug].json` is written by the gate agent on pass; its absence means the gate never ran

---

## Field Definitions

**Spec** — one sentence, RFC 2119 SHALL. One correct interpretation, no ambiguity.
`The system SHALL reject unauthenticated requests and return HTTP 401.`

**Scenarios** — GIVEN/WHEN/THEN behavioral tests, pipe-separated. Written so QA can verify mechanically.
`GIVEN no Authorization header WHEN POST /api/data THEN response status is 401`

**Artifacts** — every file the executor must produce. Pipe-separated.
`path/to/file — exports: funcA, funcB` or `path/to/file — exists with real impl`

**Produces** — downstream contract. Feeds into dependent tasks' `Context:` verbatim. Write `none` if nothing consumed downstream.

**Verify** — shell commands, deterministic pass/fail. Pipe-separated. Test/build commands MUST be wrapped in ctx-exec — this fires in both interactive Claude and claude -p subprocesses (LLM router + Anthropic). The PreToolUse hook blocks unwrapped commands with exit 2.
```
# Correct — always wrap test/build/lint/tsc in ctx-exec:
~/.claude/bin/ctx-exec "failing tests" pnpm test lib/path/file.test.ts
~/.claude/bin/ctx-exec "type error" npx tsc --noEmit
~/.claude/bin/ctx-exec "lint error" pnpm run lint
```

**Milestone** — exact name from `product-direction.ctx.md`. Never invented.

**Feature** — exact FEATURE-NNN from `cleared-queue.md`. Never invented.

**Interface-contract** (draft only) — the shared interface agreed by all departments in the feature discussion. This is what makes parallel cross-functional tasks safe — every department knows the contract before they start.

**Script-model** — the model the script's internal subprocess calls use. Required whenever a task produces a script that loops and calls claude --print or llm-route.sh. Drives CEO cost awareness at elaboration time. Omit for tasks that produce no such script.

**Script-timeout** — per-call timeout for each subprocess invocation inside the script. Required when Script-model is set. Must match the model: OpenRouter free tier (all models) ≤ 120-180s (fair-use queueing). The script must wrap each call in `Promise.race` with this timeout and continue on failure.

**Script-partial-results** — must be `true` when the script loops over N items. Means: write partial JSON to disk after each item, never accumulate-then-write at the end. CEO can inspect partial output even if the run is killed or a profile stalls.

**Context** — files pre-loaded at execution time. List only files that exist.

---

## Task Sizing Rules (EM enforces at elaboration time)

A task is the right size when ALL are true:
- One Spec sentence covers all its Artifacts — if two sentences needed, split
- ≤ 4 files changed
- One clear Verify command exists
- Completable in one Claude session without needing a decision from another in-flight task
- Does not mix research + impl (always split with Depends)

If any rule fails: elaboration agent splits into two tasks with `Depends`.

**Model-hint derivation** (auto at elaboration time):

*Code Generation & Implementation:*
- File-count ≤ 3 + Type: impl + Verify exists → `Model-hint: qwen-coder` (primary for code)
- File-count ≤ 3 + Type: impl + speed-critical flag → `Model-hint: gemma` (fastest option)
- File-count = 4 + Type: impl → MUST split before queuing (violates sizing rules)
- File-count > 4 → MUST split before queuing (violates sizing rules)

*Analysis & Reasoning:*
- Type: research + File-count ≤ 3 → `Model-hint: qwen` (best reasoning, 1M context)
- Type: research + File-count 4-5 → `Model-hint: gpt-oss` (120B, large context)
- Type: research + large-context flag → `Model-hint: nemotron` (262K context)
- Type: research + speed-critical flag → `Model-hint: gemma` (fastest, good quality)

*Subscription Routes (Quality Gates):*
- Type: gate → `Model-hint: sonnet` (always — E2E gate runs on Sonnet for reliability)
- Infra-critical: true + any Type → `Model-hint: sonnet` (highest reliability requirement)

---

## Validation Chain Rules

**Task chains** (derived from Activated + Department):

| Task type | Validation chain |
|---|---|
| Research | researcher → cro → cpo |
| Engineering (any) | dev → qa → em |
| CTO / infra-critical | dev → cto |
| Gate | qa → cpo |

**Feature sign-off** (runs after all tasks in feature are done):

| Feature type | Sign-off |
|---|---|
| product | cpo |
| engineering | cpo + cto |
| research | cpo + cro |
| cross-functional | cpo + cto |

---

## Queue Gate — Enforced Before Promoting draft → queued

All validations below are BLOCKING (exit 2) — write is blocked if any fail.

**Three layers of validation (all fire automatically on Edit/Write):**
1. **Schema validation** — required fields, format compliance
2. **Schema sync** — REQUIRED_FIELDS auto-synced from task-schema.md ← NOW BLOCKING
3. **Model-hint validation** — all queued tasks have correct Model-hint

If any validation fails, fix and try saving again.

- [ ] Spec uses SHALL — one correct interpretation, no ambiguity
- [ ] Spec makes no forward reference to unknown research output
- [ ] Every scenario is GIVEN/WHEN/THEN — deterministic pass/fail
- [ ] Artifacts lists every file with exports
- [ ] Produces declares downstream contract (or `none`)
- [ ] Verify field is non-empty for all impl tasks (required — milestone gate runs these on main)
- [ ] All Verify test/build/lint/tsc commands wrapped in ctx-exec (hook blocks unwrapped commands in both interactive + claude -p)
- [ ] Script-model + Script-timeout + Script-partial-results set when task produces a looping subprocess script
- [ ] All Context files exist and are referenced by path
- [ ] No decision required that would change other queued tasks
- [ ] Scope is completable in one Claude session
- [ ] Feature field references a real FEATURE-NNN in this queue
- [ ] Interface-contract from feature discussion is in Context (cross-functional tasks)
- [ ] **Model-hint is set and correct** (validated by ~/.claude/hooks/validate-model-hint.sh on every write)

---

## Validation Hooks — All Blocking

### 1. Schema Validation (validate-queue-hook.sh)
Validates queue against this schema on every Edit/Write to `cleared-queue.md`:
- All REQUIRED_FIELDS present
- Field format compliance (SHALL language, GIVEN/WHEN/THEN, etc.)
- No oversized tasks (>4 files)
- Cross-milestone dependencies valid

**Blocks write (exit 2) if violations found.**

### 2. Schema Sync (schema-sync-hook.sh) — **NOW BLOCKING**
Auto-syncs REQUIRED_FIELDS in `validate-queue.py` when `task-schema.md` is edited:
- Parses "Task Queued Format" section from this file
- Extracts required field list (excludes Status, Script-*, omit fields)
- Auto-updates `validate-queue.py` if mismatch detected
- **Blocks write (exit 2) if schema validation fails**

**Behavior:**
```
Edit task-schema.md, add new required field
    ↓
[schema-sync] added fields: New-Field
[schema-sync] validate-queue.py updated (17 required fields)
    ↓
✓ Write succeeds
validate-queue.py now includes New-Field in REQUIRED_FIELDS
```

This ensures both files stay in sync automatically — no manual updates needed.

### 3. Model-Hint Enforcement (validate-model-hint.sh)
Validates all queued tasks have correct Model-hint on every Edit/Write to `cleared-queue.md`:
1. **Missing Model-hint** on any queued task
2. **Wrong Model-hint** — doesn't match auto-derived value based on Type + File-count + flags
3. **Contradictory flags** — impl+large-context, speed-critical+large-context+≥4 files

**Blocks write (exit 2) if violations found.**

**Auto-derivation rules:** See §Model-hint derivation (line 183–200).

---

## Status Flow

```
Feature:  draft → in-progress → done (all tasks done + sign-off)
Task:     draft → queued → in-progress → done
                                       → cto-stop
          queued → needs-review → queued | re-spec
```

---

## Model Routing Rules (oms-work executor)

Model-hint is auto-derived at elaboration time. oms-work reads it to route task execution via llm-route.sh (free tier) or claude -p (subscription).

| Model-hint | Route | Type | Cost | Latency | When to use |
|---|---|---|---|---|---|
| `qwen-coder` | LiteLLM → qwen3-coder:free | Code generation | Free | ~100s | Impl ≤3 files, code-heavy |
| `qwen` | LiteLLM → qwen3.6-plus:free | Analysis/reasoning | Free | ~130s | Research, deep reasoning, 1M context |
| `gpt-oss` | LiteLLM → gpt-oss-120b:free | Analysis/reasoning | Free | ~130s | Research, 120B parameters, general reasoning |
| `nemotron` | LiteLLM → nemotron-3-super:free | Analysis/reasoning | Free | ~120s | Research, large context (262K), NVIDIA-opt |
| `llama` | LiteLLM → llama-3.3-70b:free | General purpose | Free | ~120s | General reasoning, proven track record |
| `gemma` | LiteLLM → gemma-3-27b:free | Fast fallback | Free | ~70s | Speed-critical, small task, lightweight |
| `stepfun` | LiteLLM → stepfun-3.5-flash:free | Medium tasks | Free | ~90s | Medium complexity, fallback option |
| `sonnet` | claude -p --model sonnet | Quality gate | Subscription | ~20-30s | Gate tasks, infra-critical, highest reliability |

**Fallback chains** (automatic escalation if timeout/error):
- **Code tasks:** qwen-coder → llama → gemma → [timeout]
- **Research tasks:** qwen → gpt-oss → nemotron → llama → gemma → [timeout]
- **Speed-critical:** gemma → stepfun → llama → [timeout]
- **Large context:** nemotron (262K) → qwen (1M) → gpt-oss (131K) → [timeout]

**Quality gates (subscription only):**
- **Gate tasks (milestone validation):** Always Sonnet — never OpenRouter models
- **Infra-critical tasks:** Always Sonnet — critical reliability requirement
- **CRO validation failure on research:** Auto-retry with Sonnet before marking failed (cost-quality tradeoff)

**Browser QA (Phase 2):** Always runs on Sonnet — never routed to external LLMs.

---

## Dependency Format

```
Depends: none              # no blocker
Depends: TASK-001          # blocked until TASK-001 done
Depends: TASK-001, TASK-002
```

Cross-functional tasks in the same feature can run in parallel (no Depends between them) once the interface-contract is agreed. Sequential only when one department's output is another's input.
