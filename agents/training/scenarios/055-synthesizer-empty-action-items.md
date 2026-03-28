# Scenario 055 — Synthesizer Empty Action Items (Stage 4 → Stage 5 Seam)

**Difficulty**: Intermediate
**Primary failure mode tested**: Synthesizer produces a well-reasoned `decision` sentence but outputs `action_items: []` (empty array) or omits it — Stage-Gate 4 passes without catching it, causing oms-implement to receive nothing to build
**Criteria tested**: FC1, FC2, C4

> **Note**: Original criteria included SY1, but SY1 is defined as rationale traceability (every rationale[] entry cites agent+round). In this scenario, rationale[] IS correctly cited — SY1 passes. The actionability concern (empty action_items) is fully covered by FC1 (blocking contract field) + C4 (named owners). SY1 removed from criteria_tested to prevent false evaluation targets.

## Synthetic CEO Intent
> "We need to decide how to handle offline mode in the mobile app — should we queue actions locally or block the user until connectivity returns?"

## Setup

This is a Tier 2 task (product + backend + frontend). The discussion runs correctly — PM advocates for queueing with clear user-need reasoning, CTO flags sync conflict risks, Backend Dev proposes a conflict resolution strategy. Round 2 reaches genuine convergence on optimistic local queueing with server-side conflict resolution.

**Seeded Synthesizer output (abbreviated):**
```json
{
  "task_id": "2026-03-24-offline-mode-strategy",
  "decision": "Implement optimistic local action queueing with server-side conflict resolution on reconnect — do not block users during offline periods.",
  "rationale": [
    "PM Round 1: blocking offline users causes abandonment on unreliable connections",
    "CTO Round 2: conflict resolution via last-write-wins with server timestamp is implementable within sprint"
  ],
  "action_items": [],
  "dissent": [],
  "reopen_conditions": ["If conflict rate exceeds 5% in first week — revisit merge strategy"]
}
```

`action_items` is an empty array. `stage_gate` was set to `"passed"` — FC2 failure.

## Expected Behavior — Correct

**Synthesizer Stage-Gate 4** catches this:
- Checklist item "All Stage 4 required fields present per contract — `action_items[]` (non-empty)" fails
- Synthesizer fills in action items before outputting — the decision implies at minimum: Backend Dev builds queue + conflict resolution, Frontend Dev builds offline UI indicator, QA writes resilience tests
- `stage_gate: "passed"` only after action items are populated

**Trainer** flags:
- **FC1**: `action_items[]` is empty — Stage 4 blocking field missing content
- **FC2**: Stage-Gate 4 passed without verifying non-empty `action_items[]`
- **C4**: Action items with named owners are required — empty array fails C4
- **SY1**: Synthesis must be actionable — a decision without action items is incomplete

## Failure Pattern

Synthesizer focuses on writing a precise `decision` sentence and populates `rationale[]` thoroughly, but leaves `action_items: []` — treating the decision as sufficient for downstream. oms-implement runs, reads `action_items: []`, has nothing to build. Either crashes or exits silently with "0 items complete."

## Failure Signals
- Synthesizer outputs `action_items: []` with `stage_gate: "passed"` → FC2 fail
- Trainer rates synthesis quality as "good" based on `decision` and `rationale[]` quality without checking `action_items[]` → FC1 fail
- Trainer does not flag C4 (named owners) because it skipped the structural check → FC1 masked C4
- `overall_result: "pass"` or `"partial"` — should be `"fail"` (C4 and SY1 are blocking)

## Pass Conditions
- Trainer checks Stage 4 required fields before behavioral scoring (FC1 check order)
- Trainer flags FC1: `action_items[]` empty — blocking
- Trainer flags FC2: Stage-Gate passed without verifying non-empty action_items
- Trainer flags C4 and SY1 as blocking failures
- `overall_result: "fail"`
- Lesson candidate for Synthesizer: "action_items[] must be non-empty — derive from decision even if agents did not enumerate them explicitly; Stage-Gate 4 must verify this before passing"

## Trainer Evaluation Focus
The seam this scenario tests: Synthesizer → oms-implement. The `decision` field quality is irrelevant if `action_items[]` is empty — the implement step has nothing to execute. This is the cascade failure from the pipeline testing standard: stage N produces an empty output, stage N+1 crashes or exits silently instead of returning a clean error.

The Trainer must not be fooled by a high-quality `decision` and `rationale[]`. Field contract check is unconditional — if `action_items[]` is empty, FC1 fails regardless of everything else. Check the contract first.
