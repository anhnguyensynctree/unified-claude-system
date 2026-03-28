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

```
## TASK-NNN — [title]
- **Status:** queued
- **Feature:** FEATURE-NNN
- **Milestone:** [milestone name]
- **Department:** backend | frontend | qa | data | research | cto
- **Type:** impl | research
- **Spec:** The system SHALL [verb] [object] so that [outcome].
- **Scenarios:** GIVEN [precondition] WHEN [trigger] THEN [outcome] | GIVEN ...
- **Artifacts:** [src/path/file.ts — exports: foo, bar] | [src/path/other.ts — exists with real impl]
- **Produces:** [interface/export/file downstream tasks depend on] | none
- **Verify:** [npm test src/path] | [npm run lint]
- **Context:** [path/to/file.ts, path/to/other.md]
- **Activated:** [agent, agent, ...]
- **Validation:** [agent → agent → agent]
- **Depends:** none | TASK-NNN
```

---

## Field Definitions

**Spec** — one sentence, RFC 2119 SHALL. One correct interpretation, no ambiguity.
`The system SHALL reject unauthenticated requests and return HTTP 401.`

**Scenarios** — GIVEN/WHEN/THEN behavioral tests, pipe-separated. Written so QA can verify mechanically.
`GIVEN no Authorization header WHEN POST /api/data THEN response status is 401`

**Artifacts** — every file the executor must produce. Pipe-separated.
`path/to/file — exports: funcA, funcB` or `path/to/file — exists with real impl`

**Produces** — downstream contract. Feeds into dependent tasks' `Context:` verbatim. Write `none` if nothing consumed downstream.

**Verify** — shell commands, deterministic pass/fail. Pipe-separated.

**Milestone** — exact name from `product-direction.ctx.md`. Never invented.

**Feature** — exact FEATURE-NNN from `cleared-queue.md`. Never invented.

**Interface-contract** (draft only) — the shared interface agreed by all departments in the feature discussion. This is what makes parallel cross-functional tasks safe — every department knows the contract before they start.

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

---

## Validation Chain Rules

**Task chains** (derived from Activated + Department):

| Task type | Validation chain |
|---|---|
| Research | researcher → cro → cpo |
| Engineering (any) | dev → qa → em |
| CTO / infra-critical | dev → cto |

**Feature sign-off** (runs after all tasks in feature are done):

| Feature type | Sign-off |
|---|---|
| product | cpo |
| engineering | cpo + cto |
| research | cpo + cro |
| cross-functional | cpo + cto |

---

## Queue Gate — Enforced Before Promoting draft → queued

- [ ] Spec uses SHALL — one correct interpretation, no ambiguity
- [ ] Spec makes no forward reference to unknown research output
- [ ] Every scenario is GIVEN/WHEN/THEN — deterministic pass/fail
- [ ] Artifacts lists every file with exports
- [ ] Produces declares downstream contract (or `none`)
- [ ] All Context files exist and are referenced by path
- [ ] No decision required that would change other queued tasks
- [ ] Scope is completable in one Claude session
- [ ] Feature field references a real FEATURE-NNN in this queue
- [ ] Interface-contract from feature discussion is in Context (cross-functional tasks)

---

## Status Flow

```
Feature:  draft → in-progress → done (all tasks done + sign-off)
Task:     draft → queued → in-progress → done
                                       → cto-stop
          queued → needs-review → queued | re-spec
```

---

## Dependency Format

```
Depends: none              # no blocker
Depends: TASK-001          # blocked until TASK-001 done
Depends: TASK-001, TASK-002
```

Cross-functional tasks in the same feature can run in parallel (no Depends between them) once the interface-contract is agreed. Sequential only when one department's output is another's input.
