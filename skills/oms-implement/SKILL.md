---
name: oms-implement
description: Implement action items from a completed OMS synthesis. Isolated execution phase — never re-discusses. Validates delivery quality via CTO review and QA requirement check.
---
# OMS Implement

Executes `action_items[]` from a completed `/oms` task. Decision is settled — this skill builds it, tests it, then validates delivery quality and requirement fidelity before presenting to CEO.

## Invocation
```
/oms-implement [task-id]   # implement from specific OMS task log
/oms-implement             # picks up latest task from topics/oms-history.md
```

## Prerequisites
`logs/tasks/[task-id].md` must exist with a completed synthesis.
If not found: "Run /oms first to settle the approach, then /oms-implement to build it." — stop.

---

## Step 0 — Load Context
1. Read `~/.claude/contexts/dev.md` — apply implementation mode
2. Read `~/.claude/contexts/review.md` — loaded now, applied in Step 3
3. Read task log at `logs/tasks/[task-id].md`
4. Extract from synthesis section:
   - `decision` — the settled approach
   - `action_items[]` — ordered list of what to build
   - `activated_agents[]` — which agents shaped the decision (used to select reviewers in Step 3)
   - `dissent[]` — known tradeoffs to stay aware of
   - `reopen_conditions[]` — if hit during impl, stop and surface to CEO
5. Read `~/.claude/rules/testing.md` — mandatory

---

## Step 1 — Plan Confirmation
Present to CEO before touching code:
```
Implementing: [task-id]
Decision: [one-line decision from synthesis]

Action items:
  1. [item]
  2. [item]
  ...

Dissent notes: [any from synthesis, or "none"]
Reopen conditions: [list, or "none"]

Proceed? (y / adjust)
```
Wait for confirmation. If CEO adjusts scope: update the plan only. Do NOT re-run OMS — if the OMS decision itself is wrong, say so and offer to re-run `/oms` instead.

---

## Step 2 — Implement
For each action item in sequence:
1. TDD: write failing test → implement minimal passing code → refactor
2. Run tests for modified files — must pass before moving to next item
3. Check for `console.log` in modified files
4. Append progress marker to task log: `## Implementation > [item N]: [status]`

**Scope lock**: implement only what is in `action_items[]`. No extra features, no opportunistic refactors.

**Reopen condition hit**: STOP immediately. Surface to CEO:
```
Reopen condition triggered: [condition]
Context: [what was found during implementation]
Options: (1) adjust implementation to avoid it, (2) re-run /oms with new information
```
Do not guess. Do not push through.

---

## Step 3 — Delivery Validation

Two parallel reviews against the completed diff. Run concurrently.

### 3a — CTO Code Quality Review
Load: `~/.claude/agents/cto/persona.md` + `cto/lessons.md` + `cto/MEMORY.md`
Also load domain reviewer if relevant to the task:
- Backend-heavy task → `backend-developer/persona.md` + lessons + MEMORY
- Frontend-heavy task → `frontend-developer/persona.md` + lessons + MEMORY
- Both domains touched → load both

Apply `~/.claude/contexts/review.md` — this is the review standard.

Input:
- The OMS synthesis: `decision`, `action_items[]`, `dissent[]`
- The full diff of what was built (files changed, key logic added)

Evaluate as staff engineer reviewing a PR:
- Code quality, architecture alignment, security, performance, test coverage
- Does the implementation match the intent of the OMS decision?
- Any patterns that contradict `cross-agent-patterns.md` or project architecture?

Output required: `quality: pass|fail`, `issues[]` (severity: critical|major|minor), `architecture_aligned: true|false`

### 3b — QA Requirement Check
Load: `~/.claude/agents/qa-engineer/persona.md` + `qa-engineer/lessons.md` + `qa-engineer/MEMORY.md`

Input:
- `action_items[]` from synthesis
- The diff

For each action item: was it implemented? Fully or partially?
Any scope creep — changes outside `action_items[]`?

Output required: `items_satisfied[]` (per item: complete|partial|missing), `scope_creep[]`

---

## Step 3 — Outcome Handling

**All clear** (`quality: pass` + all items complete + no critical scope creep):
Present to CEO:
```
Delivery validated.
CTO: [brief quality note]
QA: all [N] action items complete
Tests: passing
```

**Issues found**: present clearly grouped:
```
CTO review — [critical/major issues]
QA check — [missing or partial items] / [scope creep]
```
For each issue: implement correction or get explicit CEO sign-off to accept it. Log outcome.

**Critical architecture misalignment** (`architecture_aligned: false`): stop. Present the gap. Offer to re-run `/oms` with the implementation finding as new context.

---

## Step 4 — Log
Append to `logs/tasks/[task-id].md` under `## Implementation`:
```
Status: complete | Date: YYYY-MM-DD
Files changed: [list]
Quality: pass/fail  Architecture aligned: true/false
Items: [N/N complete]  Scope creep: [list or none]
Issues resolved: [list or none]
```

Update `topics/oms-history.md`:
```
## [task-id] | implemented: YYYY-MM-DD
Files: [list]  Quality: [pass/fail]  Items: [N/N]  Issues: [list or none]
```

---

## Standing Rules
- Decision is locked — implementation only, no re-discussion mid-build
- Scope is `action_items[]` only — refuse additions not in the list
- Tests are mandatory — no exceptions
- CTO and QA review the delivery, not the decision — they do not re-open the architecture debate
- Trainer does not run after `/oms-implement` — Trainer evaluated the OMS discussion; CTO + QA evaluate the delivery
- If implementation reveals the OMS decision is fundamentally wrong: stop, flag, offer to re-run `/oms`
- All code follows `~/.claude/rules/coding-style.md` and `~/.claude/contexts/dev.md`
