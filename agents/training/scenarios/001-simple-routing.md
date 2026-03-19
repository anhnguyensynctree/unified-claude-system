# Scenario 001 — Simple Routing (Tier 1)

**Difficulty**: Basic
**Primary failure mode tested**: Router over-complexity, role drift
**Criteria tested**: R1, R2, R3, R6, R7, D1, O1
**E1 note**: E1 is not testable here — Tier 1 agreement path skips Round 2 per oms.md spec. E1 on Tier 1 disagreement path covered by scenario 047.

## Synthetic CEO Intent
> "Add a loading spinner to the dashboard page while data is fetching."

## Expected Behavior

**Router routing**:
- Tier: 1
- Complexity: simple
- Cynefin: Complicated (low) — frontend-only, known pattern, fully reversible
- Numeric score: domain_breadth=0, reversibility=0, uncertainty=1, total=1 → Tier 1
- Activated agents: frontend-developer (primary), qa-engineer (secondary)
- Should NOT activate: cto, product-manager, engineering-manager, backend-developer
- Round cap: 2
- No clarifying questions needed — intent is unambiguous

**Round 1**:
- Frontend Dev: states implementation approach (React Suspense or loading state), notes any a11y consideration
- QA: states what test coverage is needed (interaction test for loading state, no regression risk)

**Round 2**:
- Not triggered in the agreement path — OMS proceeds directly to inline synthesis
- If agents disagree (e.g. QA flags a blocking accessibility concern) → Tier 1 escalates to Tier 2 → see scenario 047

**Synthesis**:
- OMS inline synthesis (Tier 1 — no Synthesizer subagent)
- Decision: one sentence on the implementation approach
- Action item: owner = frontend-developer

## Failure Signals
- Router classifies as Tier 0 → R6 fail (needs QA analysis = not trivial)
- Router classifies as Tier 2+ → R2 fail (single domain, reversible)
- Router missing numeric score in `complexity_reasoning` → R6 fail
- CTO or PM activated → R1 fail
- Backend Dev joins discussion → D1 fail
- Frontend Dev position is "it depends" → O1 fail
- More than 2 rounds → R4 fail

## Trainer Evaluation Focus
Does the Router correctly output `tier: 1` with numeric scoring? Does it resist activating agents whose domains aren't touched? Does OMS produce inline synthesis without spawning a Synthesizer subagent? E1 is not in scope — do not flag Round 2 absence as a gap.
