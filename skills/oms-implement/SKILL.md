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

## Step 1.25 — CTO Safety Gate

Before any implementation, scan `action_items[]` for dangerous operations:

**Dangerous flags** (require blocking question before proceeding):
- DB schema migration or DROP/ALTER statements
- Auth flow changes (token logic, session handling, OAuth config)
- Breaking API changes (endpoint removal, response shape change, auth scope change)
- Infrastructure changes (environment variables, deployment config, CI/CD pipeline)
- Any action item containing the words: `migrate`, `drop`, `rename column`, `break`, `remove endpoint`, `revoke`

**Default behavior**: auto-proceed without asking. OMS runs continuously.

**If a dangerous flag is detected** (autonomous mode only — `OMS_BOT=1`):
Write blocking question to `~/.claude/oms-pending/[slug].question`:
```json
{
  "question": "CTO Safety Gate: dangerous operation detected — [flag type]. Action item: [exact item]. Proceed?",
  "context": "DB/auth/breaking-API changes are irreversible — requiring explicit approval",
  "task_id": "[task-id]",
  "step": "safety-gate",
  "asked_at": "[ISO timestamp]"
}
```
Write checkpoint `"next": "waiting_ceo"`. Do not proceed until CEO replies "yes" or equivalent.

**In manual mode** (no `OMS_BOT=1`): present inline in the Step 1 plan confirmation instead of writing a file. CEO's "y" covers it.

## Step 1.5 — Dependency Analysis

Before touching code, classify each action item:

For each item, identify:
- **Files/modules likely affected** — inferred from the item description + codemap
- **Upstream dependency** — does this item require output from a prior item to exist first?

Classify every item as:
- `sequential` — depends on a prior item's output (schema must exist before API, API must exist before frontend, etc.)
- `parallel` — independent, no shared files with other parallel items

Group into `implementation_groups[]`: an ordered list of groups where items within a group are all `parallel` and can run concurrently. Sequential items form singleton groups.

Example:
```
group 1 (parallel): [item 1 — add DB schema, item 2 — update auth config]  ← no dependency between them
group 2 (sequential): [item 3 — add API endpoint]  ← depends on schema from item 1
group 3 (parallel): [item 4 — frontend component, item 5 — update E2E tests]
```

Present to CEO:
```
Implementation plan: [N] groups, [M] items total
  Group 1 (parallel ×2): [item 1], [item 2]
  Group 2 (sequential): [item 3]
  ...
```
No confirmation needed — proceed immediately unless CEO interrupts.

---

## Step 2 — Implement

For each group in `implementation_groups[]` in order:

### Single item (or all-sequential group)
1. TDD: write failing test → implement minimal passing code → refactor
2. Run tests for modified files — must pass before moving to next group
3. Check for `console.log` in modified files
4. Append progress marker to task log: `## Implementation > [item N]: [status]`

### Parallel group (2+ independent items)
1. For each item: launch a worktree Agent (`isolation: "worktree"`, model: Sonnet) with:
   - Full task context: `decision`, their specific `action_item`, `dissent[]`, `reopen_conditions[]`
   - Rules: `dev.md`, `testing.md`, `coding-style.md`
   - Instruction: "Implement only this item. TDD: failing test → minimal pass → refactor. Run tests. Check console.log. Output: `{status: complete|reopen, files_changed[], reopen_reason?: string}`"
2. All agents in the group run concurrently — dispatch in a single message
3. Collect all agent outputs before proceeding
4. If any agent returns `status: reopen`: **stop entire group**, surface to CEO (see Reopen Condition below)
5. Merge each worktree branch in order — if merge conflict: surface specific conflict to CEO before resolving
6. Run full test suite after all merges in the group pass — must be green before starting next group
7. Append per-item progress markers to task log

**Scope lock**: each agent implements only its assigned item. No extra features, no opportunistic refactors. Applies to parallel and sequential paths equally.

**Reopen condition hit**: STOP immediately. Surface to CEO:
```
Reopen condition triggered: [condition]
Context: [what was found during implementation]
Options: (1) adjust implementation to avoid it, (2) re-run /oms with new information
```
Do not guess. Do not push through.

---

## Step 2.5 — Evidence QA (live verification)

After all implementation groups complete and tests pass:

### 1 — Extract acceptance criteria
Read `logs/tasks/[task-id].md`. Find PM's output JSON and extract `acceptance_criteria[]` directly — it is a structured array, not prose. Do not infer or guess criteria from surrounding text.
If PM's `acceptance_criteria[]` is empty or absent: fall back to `action_items[]` as the criteria baseline.

### 2 — Drive browse for each criterion
Auto-start browse daemon per `~/.claude/skills/browse/llms.txt`. Run `status` first to see current URL and page state.

**Output path convention**: all QA media saves to the project's `qa/` directory with task-id in filename:
- Videos: `qa/videos/[task-id]-[criterion-slug]` (passed to `record:start`)
- Screenshots: `qa/screenshots/[task-id]-[criterion-slug].png` (passed to `screenshot`)

The browse daemon resolves these relative to cwd (the project directory).

For each criterion, build a batch command sequence that fully exercises the behavior:
- Navigate to the relevant route (`go <path>`)
- Interact to reach the state under test (`click`, `fill`, `submit`, `key`)
- Screenshot before and after every interaction that changes visible state
- Use `exists` / `visible` / `count` to make assertions on element state
- Flush `console-errors` and `network-errors` after every flow

**Maximize browse per criterion** — one batch call per criterion covering the full interaction sequence, not one command at a time. Use `ctx:create` for flows requiring a fresh session (e.g. persistence after reload, empty state, unauthenticated view).

Never read a URL from config or hardcode one. Use `status` to anchor, then navigate from there.

### 3 — QA verdict
Load `qa-engineer/persona.md`. Input: acceptance criteria + screenshot paths + error logs.

Output required:
```json
{
  "verdict": "PASS | FAIL",
  "criteria_results": [
    { "criterion": "...", "result": "pass|fail", "screenshot": "/path/to.png", "notes": "..." }
  ],
  "console_errors": [],
  "network_errors": []
}
```

### 4 — On FAIL: retry up to 3 times
- Fix the failing implementation
- Re-run browse flows for failing criteria only (not all)
- Track attempt count

After 3 failed attempts — STOP. Escalate to CTO:
- Load `~/.claude/agents/cto/persona.md` + `cto/lessons.md` + `cto/MEMORY.md`
- Input: failing criteria, last screenshot paths, all 3 attempt summaries
- CTO assesses: root cause, whether it's an implementation gap or an acceptance criteria problem
- CTO outputs: `{ resolution: "implementable" | "unresolvable", approach?: string, escalate_to_ceo?: true, reason?: string }`

**If `resolution: "implementable"`**: CTO prescribes the fix approach. Implement it and run one final browse verification. No further retries — this is the last attempt.

**If `resolution: "unresolvable"` or `escalate_to_ceo: true`**: only then surface to CEO:
```
Evidence QA escalated — CTO could not resolve.

Failing criteria:
  - [criterion]: [last QA finding]

CTO assessment: [reason]

Options:
  1. Adjust acceptance criteria with PM — re-verify without re-implementing
  2. Re-run /oms with the implementation constraint as new context
```
Do not guess. Do not push through.

### 5 — On PASS
Append to task log: `## Evidence QA: PASS | [N] criteria verified | [date]`
Proceed to Step 3.

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
