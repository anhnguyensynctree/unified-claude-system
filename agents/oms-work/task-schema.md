# OMS Work Task Schema

All tasks in `[project]/.claude/cleared-queue.md` must conform to this format.
Written by the daily OMS session. Executed by `/oms-work`. No CEO gate during execution.

---

## Task Format

```
## TASK-NNN — [title]
- **Status:** queued
- **Type:** impl | research
- **Milestone:** [milestone name from product-direction.ctx.md] | none
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

**Scenarios** — GIVEN/WHEN/THEN behavioral tests, pipe-separated. Written so QA can verify
each one mechanically — no judgment required.
`GIVEN no Authorization header WHEN POST /api/data THEN response is 401`

**Artifacts** — explicit file-level outputs the executor MUST produce. Pipe-separated.
Format: `path/to/file — exports: funcA, funcB` or `path/to/file — exists with real impl`
Agent reads this before starting — zero guessing about what files to create.

**Produces** — what downstream tasks consume from this task. Feeds directly into
dependent tasks' `Context:` field. Write `none` if nothing is consumed downstream.
`src/auth/tokens.ts — exports: generateToken, verifyToken`

**Verify** — shell commands to run after agent validation. Deterministic pass/fail.
Pipe-separated. Use project-relative paths.
`npm test src/auth | npm run lint`

**Milestone** — the named milestone from `product-direction.ctx.md` this task advances.
All tasks under the same milestone share one Discord thread. Use `none` only for standalone
ops tasks with no milestone anchor. Name must match exactly as it appears in product-direction.

**Context** — files the executor reads as background. Inlined into the dispatch prompt
at execution time — no cold reads. List only files that exist.

---

## Validation Chain Rules

Derived from `Activated` at queue-write time. Written explicitly into each task.
`oms-work` executes the chain literally — no inference, no skipping.

**All tasks must have a validation chain. No exceptions.**

| Task type | Validation chain |
|---|---|
| Research | researcher → cro → cpo |
| Engineering (any) | dev → qa → em |
| CTO / infra-critical | dev → cto |

**Why no PM in engineering chains**: PM's contribution is the spec and scenarios,
written at queue-commit time. QA validates against those scenarios — PM has already done their job.

**CPO in research chains**: research produces new findings not known at queue-commit time.
CPO evaluates strategic fit — genuinely new judgment required.

**Research + impl in one task = queue gate rejection.** Split into two tasks with Depends.
The chain never exceeds 3 steps.

---

## Queue Gate — Enforced Before Enqueueing

At the end of every daily session, before writing to `cleared-queue.md`, each task must
answer YES to all of the following:

- [ ] Spec uses SHALL — one correct interpretation, no ambiguity
- [ ] Spec makes no forward reference to unknown research output ("whatever research finds" = instant fail)
- [ ] Every scenario is GIVEN/WHEN/THEN — deterministic pass/fail without CEO judgment
- [ ] Artifacts list every file the executor must produce, with exports
- [ ] Produces declares what downstream tasks depend on (or explicitly `none`)
- [ ] All Context files exist and are referenced by path
- [ ] No decision required that would change other queued tasks
- [ ] Scope is completable in one Claude session (small-to-medium)

**If any box is unchecked**: re-spec now, while CEO is present. Do not queue.

---

## Status Values

```
queued → in-progress → done
                     → cto-stop
```

- `cto-stop`: that task pauses; all other tasks continue; CEO reviews at next daily session
- A task that hits `cto-stop` is never re-queued automatically — CEO must re-spec and re-add

---

## Dependency Format

```
Depends: none              # no blocker, eligible immediately
Depends: TASK-001          # blocked until TASK-001 is done
Depends: TASK-001, TASK-002 # blocked until both are done
```

Dependency resolution is done by `oms-work` at runtime — parallel where possible,
sequential only where `Depends` requires it.

The `Produces` field of a completed task maps directly to the `Context` field of tasks
that `Depends` on it. Wire these explicitly at queue-commit time.
