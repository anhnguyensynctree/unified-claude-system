# Scenario 054 — Router Field Contract Breach

**Difficulty**: Basic
**Primary failure mode tested**: Router produces structurally complete-looking output that passes all behavioral criteria but omits a blocking required field (`rounds_required`), causing Stage-Gate to pass when it should fail
**Criteria tested**: R8, FC1, FC2

## Synthetic CEO Intent
> "Refactor the user authentication service to use JWT instead of session cookies."

## Setup

This is a valid Tier 2 task (auth = irreversible, multi-domain: backend + security + frontend). The Router correctly identifies tier, roster, and briefings — behavioral quality is good. However, the Router output is missing `rounds_required` (field is null or absent).

**Seeded Router output (abbreviated):**
```json
{
  "phase": "routing",
  "task_id": "2026-03-24-jwt-auth-refactor",
  "tier": 2,
  "complexity": "compound",
  "complexity_reasoning": "domain_breadth=2, reversibility=2, uncertainty=1, total=5 → compound → tier 2",
  "round_cap": 2,
  "rounds_required": null,
  "activated_agents": ["cto", "backend-developer"],
  "locked": true,
  "stage_gate": "passed",
  "briefing_mode": "fat"
}
```

`rounds_required` is null. Stage-Gate was set to "passed" — a FC2 failure (Stage-Gate didn't check its blocking fields).

## Expected Behavior — Correct

**Router Stage-Gate 1** must catch this before outputting:
- The checklist item "rounds_required populated — derived from tier" fails
- Router sets `stage_gate: "failed"`, `stage_gate_note: "rounds_required is null — cannot proceed"`
- Dispatcher freezes on `stage_gate: "failed"` — does not proceed to rounds

**Trainer** flags two failures:
- **R8**: `rounds_required` is null in Router output — blocking failure
- **FC2**: Stage-Gate passed without verifying `rounds_required` — Stage-Gate checklist is incomplete

## Failure Pattern

Router outputs `stage_gate: "passed"` with `rounds_required: null`. Dispatcher reads the checkpoint, finds no `rounds_required`, falls back to default 3. Task runs with 3 rounds when tier dictates 2. Trainer evaluates the discussion and misses the structural breach because behavioral quality was fine.

## Failure Signals
- Router outputs `stage_gate: "passed"` with null `rounds_required` → FC2 fail (Stage-Gate incomplete)
- Trainer does not flag `rounds_required: null` before evaluating behavioral quality → FC1 fail
- Dispatcher silently defaults to `rounds_required: 3` without freezing → contract gap (not a Trainer failure, but a criteria_gap worth flagging)
- Trainer flags behavioral quality as "good" without first checking the field contract → FC1 fail (contract check must precede behavioral evaluation)

## Pass Conditions
- Trainer loads `~/.claude/agents/oms-field-contract.md` and checks Stage 1 required fields before any behavioral scoring
- Trainer flags R8 as a blocking failure (rounds_required null)
- Trainer flags FC2 because Stage-Gate passed without catching the null
- `overall_result: "fail"` — a single blocking criterion failure is sufficient
- Lesson candidate written for Router: "rounds_required must be non-null before setting stage_gate: passed — derived from tier (Tier 0→1, Tier 1→2, Tier 2→2, Tier 3→3)"

## Trainer Evaluation Focus
The characteristic failure here is a Trainer that evaluates behavioral quality first and never checks the field contract. The Router's reasoning is sound, the roster is correct, the briefings are good — everything *looks* fine. FC1 requires checking required fields before any of that. A Trainer that rates this discussion as "good" without first flagging `rounds_required: null` has failed FC1 itself. The correct evaluation order is: field contract → behavioral criteria. Never the reverse.
