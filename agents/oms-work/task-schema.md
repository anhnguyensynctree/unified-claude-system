# OMS Work Task Schema

All tasks in `[project]/.claude/cleared-queue.md` must conform to this format.
Written by the daily OMS session. Executed by `/oms-work`. No CEO gate during execution.

---

## Task Format

```
## TASK-NNN — [title]
- **Status:** queued
- **Type:** impl | research
- **Spec:** [1–3 sentence implementation-ready description — one correct interpretation]
- **Acceptance:** [criterion 1] | [criterion 2] | [criterion 3]
- **Context:** [path/to/file.ts, path/to/other.md]
- **Activated:** [agent, agent, ...]
- **Validation:** [agent → agent → agent]
- **Depends:** none | TASK-NNN
```

---

## Validation Chain Rules

Derived from `Activated` at queue-write time. Written explicitly into each task.
`oms-work` executes the chain literally — no inference, no skipping.

**All tasks must have a validation chain. No exceptions.**

| Task type | Validation chain |
|---|---|
| Research | researcher → cro → cpo |
| Research with product decision output | researcher → cro → cpo → pm |
| Engineering, internal (refactor / infra / bug) | dev → qa → em |
| Engineering, user-facing feature | dev → qa → pm → em |
| CTO / infra-critical | dev → cto |

**PM position**: between QA and EM on user-facing tasks only. Omit on internal tasks.

**Research + impl in one task = queue gate rejection.** Split into two tasks with a Depends link.
The chain never exceeds 4 steps. If yours is longer, the task is too big.

**Extensibility**: new agent types (e.g. game-dev, ml-engineer) are added to `Activated`
and derive their own chain position. No hardcoded modes — chain follows activated agents.

---

## Queue Gate — Enforced Before Enqueueing

At the end of every daily session, before writing to `cleared-queue.md`, each task must
answer YES to all of the following:

- [ ] Spec has one correct interpretation — no ambiguity
- [ ] Acceptance criteria are testable — deterministic pass/fail without CEO judgment
- [ ] All context files exist and are referenced by path
- [ ] No decision required that would change other queued tasks
- [ ] Scope is completable in one Claude session (small-to-medium)

**If any box is unchecked**: re-spec the task now, while CEO is present. Do not queue.

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
