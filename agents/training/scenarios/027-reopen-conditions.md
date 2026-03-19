# Scenario 027 — Reopening Conditions Derivation

**Difficulty**: Medium
**Primary failure mode tested**: Synthesizer inventing reopening conditions not grounded in the discussion, or failing to derive conditions from explicitly-stated agent concerns
**Criteria tested**: RV3, SY1, C4

## Synthetic CEO Intent
> "Implement rate limiting using a Redis-backed token bucket at the API gateway."

## Setup
Decision converges clearly: all agents agree on Redis token bucket implementation. Synthesis confidence is high. The decision is partially reversible (can switch to different algorithm or storage, but requires deployment + potential brief downtime).

However, agents raised specific conditional concerns in the discussion:

- **CTO (Round 1)**: "Redis adds operational complexity — if we don't have Redis in production already, this introduces a new infrastructure dependency. Rate limiting only warrants Redis if we're seeing abuse or genuinely need cross-instance coordination."
- **Backend Dev (Round 2)**: "The token bucket implementation in the chosen library hasn't been audited for thread safety under high concurrency — if we hit >500 req/s on a single instance, we should re-evaluate."
- **Engineering Manager (Round 1)**: "This adds to the oncall burden. If Redis goes down, does rate limiting fail open or closed? The answer to that question should be in the decision."
- **QA (Round 2)**: "We need load test results at 2x expected peak before I'd sign off on this going to production."

## Expected Synthesizer Behavior

**Reopening conditions** (must all be derived from agent-stated concerns):
1. `{ "condition": "Reopen if Redis is not already in production stack at deployment time — validate Redis dependency before proceeding", "derived_from": "cto", "round": 1 }`
2. `{ "condition": "Reopen if sustained request rate exceeds 500 req/s on a single instance — reassess thread safety and library choice", "derived_from": "backend-developer", "round": 2 }`
3. `{ "condition": "Reopen if fail-open/fail-closed behavior is not explicitly decided before deployment", "derived_from": "engineering-manager", "round": 1 }`

**Action items** (from QA concern):
- QA's load test requirement must appear as a blocking action item before deployment, not a suggestion

## Failure Signals
- `reopen_conditions[]` contains `{ "condition": "Reopen if performance degrades" }` with no derivation from a specific agent statement → RV3 fail (generic invented condition)
- `reopen_conditions[]` is empty despite 3 explicit conditional concerns in the discussion → RV3 fail (failed to derive)
- QA's load test requirement appears only in synthesis rationale, not as an action item with an owner → C4 fail
- EM's fail-open/fail-closed concern not captured as either a reopen condition or an action item → SY2 fail (dissent that doubles as a decision gap)

## Pass Conditions
At least 3 `reopen_conditions[]` entries, each with `derived_from` traceable to a specific agent + round. QA load test is a blocking action item. No invented conditions without discussion basis.

## Trainer Evaluation Focus
Did the Synthesizer extract all explicitly-stated conditional concerns? Did it distinguish reopening conditions (future events that change the decision) from action items (things to do now)? Were the `derived_from` fields accurate?
