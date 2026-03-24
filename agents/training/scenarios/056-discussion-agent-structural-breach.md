# Scenario 056 — Discussion Agent Structural Breach (Stage 2 → Stage 3 Seam)

**Difficulty**: Intermediate
**Primary failure mode tested**: A discussion agent produces output that passes behavioral reading but is structurally broken — `position` is missing, `confidence_pct` contradicts `confidence_level`, or `position_delta` is malformed in Round 2. Facilitator and Synthesizer silently consume broken input; Trainer must catch FC1 before evaluating reasoning quality.
**Criteria tested**: FC1, O1, O4, CD1, E2

## Synthetic CEO Intent
> "Should we migrate our background job processing from Redis queues to a database-backed queue (e.g. Postgres-backed with pg-boss) to reduce infrastructure complexity?"

## Setup

Tier 2 task. CTO and Backend Dev are activated. Round 1 runs normally. In Round 2, Backend Dev produces structurally broken output:

**Seeded Backend Dev Round 2 output:**
```json
{
  "position": null,
  "reasoning": [
    "Redis offers lower latency for high-throughput queues",
    "pg-boss adds Postgres load but removes a separate Redis instance",
    "Team already has Postgres expertise — operational simplicity favors pg-boss for this scale"
  ],
  "confidence_level": "high",
  "confidence_pct": 35,
  "warrant": "At our job volume, Postgres queue overhead is negligible — infra simplicity outweighs latency advantage",
  "position_delta": {
    "changed": true,
    "change_type": "partial_revision",
    "change_basis": "new_tradeoff",
    "source_agent": "cto",
    "source_argument": "CTO noted operational cost of maintaining two datastores exceeds latency benefit at <1k jobs/day"
  }
}
```

Two structural failures:
1. `position: null` — O1 fail, FC1 fail (blocking field missing)
2. `confidence_pct: 35` with `confidence_level: "high"` — CD1 fail (high requires ≥70)

## Expected Behavior — Correct

**Trainer** catches both structural failures before evaluating cross-agent engagement:

1. **FC1**: `position` is null — blocking field missing in Stage 2 output. Trainer must not read `reasoning[]` to infer a position — null is null.
2. **CD1**: `confidence_pct: 35` contradicts `confidence_level: "high"` — high requires ≥70. This is a structural inconsistency, not a behavioral nuance.
3. Trainer notes that `reasoning[]` content is sound — but this does not rescue the structural failures
4. Trainer does NOT flag E2 (position change quality) — the change_basis and source_argument are correct. The structural breach is separate from the behavioral quality of the change.

`overall_result: "fail"` — FC1 is blocking.

## Failure Pattern A — Trainer skips field contract
Trainer reads `reasoning[]`, finds it substantive, infers Backend Dev's position from the reasoning ("clearly favors pg-boss"), and evaluates E2/E3 engagement quality. FC1 and CD1 are never flagged. Discussion rated "mixed" because of the null position but not treated as a blocking structural failure.

## Failure Pattern B — Trainer conflates structural and behavioral
Trainer flags `position: null` as an O1 failure (behavioral — position must be actionable) without flagging it as FC1 (structural — required field missing). These are separate failures with different severity. O1 is non-blocking; FC1 is blocking. Only flagging O1 produces `overall_result: "partial"` instead of `"fail"`.

## Failure Signals
- Trainer infers position from `reasoning[]` rather than treating null as a structural failure → FC1 fail (the Trainer failed FC1 itself)
- Trainer flags `position: null` as O1 only (non-blocking) without also flagging FC1 → misclassified severity
- `overall_result: "partial"` or `"pass"` — should be `"fail"` (FC1 is blocking)
- Trainer evaluates E2 engagement quality before confirming FC1 is clear → wrong evaluation order
- CD1 (`confidence_pct: 35` vs `confidence_level: "high"`) not flagged → structural inconsistency missed

## Pass Conditions
- Trainer loads field contract and checks Stage 2 required fields before any behavioral evaluation
- Trainer flags FC1: `position: null` — blocking field missing, cannot proceed to behavioral evaluation for this agent
- Trainer flags CD1: `confidence_pct: 35` with `confidence_level: "high"` — contradiction, structural inconsistency
- Trainer notes `reasoning[]` quality separately but does not use it to rescue the null `position`
- Trainer does NOT flag E2 — the position_delta fields are correctly populated; structural breach is independent of change quality
- `overall_result: "fail"` with FC1 as the blocking criterion
- Lesson candidate for Backend Dev: "position must never be null — if uncertain, express uncertainty in the position wording itself; null fails FC1 regardless of reasoning quality"
- Lesson candidate for Backend Dev: "confidence_pct must match confidence_level: high ≥ 70, medium 40–69, low < 40 — mismatched values fail CD1 and undermine Facilitator consensus scoring"

## Trainer Evaluation Focus
Two distinct failure modes are being tested simultaneously. The Trainer must separate them cleanly:
- FC1 (`position: null`) is a structural breach — caught by contract check, not behavioral reading
- CD1 (confidence mismatch) is a structural inconsistency — caught by schema validation, not reasoning quality

Both must be flagged independently. The trap is the rich `reasoning[]` content — it makes the output look substantive and pressures the Trainer to infer a position. Resist this: the contract requires `position` to be a populated string. Null means null. The Trainer that infers from reasoning has itself failed FC1's evaluation order rule.
