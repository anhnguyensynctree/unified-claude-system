# Scenario 057 — Exec Session Golden Path

**Difficulty**: Advanced
**Primary failure mode tested**: Exec session skips Steps 6–8.5 after delivering synthesis; Step 8.5 writes OpenSpec tasks instead of FEATURE drafts; Step 8 does not block for CEO response.
**Criteria tested**: EP1, EP2, EP3, EX1, EX2, EX3, ES1, ES2

## Synthetic CEO Intent

> `/oms exec` — queue is empty, no task given.

Or auto-triggered: cleared-queue.md has no `queued` tasks and CEO runs `/oms` with no argument.

## Setup

Project: sonai. Product-direction.ctx.md has 3 milestones, `l1-architecture` and `question-bank-t-dimension` complete, `extraction-pipeline` with no queued tasks. Auto-trigger condition is met.

## Expected Behavior

**Step 1 — Router:**
- Detects `task_mode: exec` from queue-empty condition
- Activates: CPO (lead), CTO, CLO, CFO, CRO
- Round cap: 2 (standard for exec)
- Outputs `exec_mode: true` — this context tells downstream agents the discussion output goes to CEO, not directly to implementation

**Step 2 — Round 1 (all 5 C-suite agents, parallel, blind NGT):**
- CPO: names one specific milestone to advance with named success criterion (`EX1` requires this). Populates `opportunity_cost` with a named deferred alternative (`EX3`). Proposes action_items for the chosen milestone.
- CTO: states arch prerequisites and tech risks for the chosen milestone. Names any irreversible decisions.
- CFO: provides `cost_estimate` with named assumptions (`CF1`). States `budget_recommendation` as `proceed | proceed with constraint | do not proceed` (`CF2`).
- CLO: populates `legal_risks[]` if the milestone touches personal data, AI content, or platform distribution (`CL1`). States `compliant_path` if risks exist (`CL2`).
- CRO: names what is known vs unknown about the milestone's user value. Flags any research gate recommendations.

**Steps 3–4 — Facilitator + Synthesizer:**
- Exec synthesis produces `recommendation_brief` with product bet, evidence from each C-suite agent cited by agent+round, and `product_direction_update` (`ES1`).
- If any C-suite agent has a `hard_block: true` or `high`-severity CLO objection — preserved in `dissent[]`, not suppressed (`ES2`).

**Step 5 — Log written to `.claude/logs/tasks/[task-id].md`**

**Step 6 — Trainer runs.** Output appended to task log. Does NOT display to CEO unless anomalies found.

**Step 7 — Context Optimizer runs.** Lightweight check. Updates `metrics.md`. Silent if clean.

**Step 8 — BLOCKING step.** OMS presents synthesis to CEO and WAITS. Does not proceed until CEO responds. (`EP3`)

**Step 8.5 — Queue Commit (FEATURE drafts only):**
- CPO writes one FEATURE-NNN block per action_item to cleared-queue.md (`EP2`)
- Each FEATURE contains: Status (draft), Milestone, Type, Departments[], Research-gate, Why, Exec-decision, Acceptance, Validation, Tasks (none), Context-hints
- NO `Spec:`, `Scenarios:`, `Artifacts:`, `Produces:`, or `Verify:` fields — those are task-level OpenSpec fields written after `/oms FEATURE-NNN`

## Failure Signals

- Session log shows synthesis output but no `## Step 6 Trainer` section → EP1 fail
- Session log shows synthesis but no FEATURE drafts in cleared-queue.md → EP1 fail
- FEATURE entry contains `Spec:` or `Artifacts:` field → EP2 fail (wrote task, not feature)
- Cleared-queue.md updated without CEO response recorded in log → EP3 fail
- CPO Round 1 names milestone without success criterion → EX1 fail
- CPO Round 1 has no `opportunity_cost` → EX3 fail
- CLO `legal_risks[]` is empty on a milestone involving user data collection → CL1 fail
- Exec synthesis missing `product_direction_update` → ES1 fail
- CFO hard_block not in `dissent[]` → ES2 fail (blocking)
- Only 1-2 C-suite agents have visible positions in task log → exec skipped open discussion

## Pass Conditions

- All 5 C-suite agents have visible Round 1 positions in the task log
- Synthesis cites each C-suite agent by role+round in `recommendation_brief`
- cleared-queue.md has ≥1 FEATURE-NNN block per action_item
- Each FEATURE block has Why, Exec-decision, Acceptance, Validation fields — no OpenSpec fields
- CEO response is recorded before 8.5 fires
- Trainer and Context Optimizer sections present in log

## Trainer Evaluation Focus

Trainer must verify: (1) all 5 agents posted positions — not just CPO; (2) FEATURE blocks in queue have the feature format, not task format; (3) Step 8 blocking is evidenced by a CEO response entry in the log preceding the queue write.
