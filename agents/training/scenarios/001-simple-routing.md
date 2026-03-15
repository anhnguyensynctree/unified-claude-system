# Scenario 001 — Simple Routing (Tier 1)

**Difficulty**: Basic
**Primary failure mode tested**: Router over-complexity, role drift, parallel monologues
**Criteria tested**: R1, R2, R3, R6, R7, D1, E1, O1

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
- Frontend Dev and QA should reference each other's Round 1 positions
- No position changes expected unless QA raised an accessibility concern (spinner must be screen-reader accessible)

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
- Round 2 agents don't reference each other → E1 fail
- Frontend Dev position is "it depends" → O1 fail
- More than 2 rounds → R4 fail

## Trainer Evaluation Focus
Does the Router correctly output `tier: 1` with numeric scoring? Does it resist activating agents whose domains aren't touched? Does OMS produce inline synthesis without spawning a Synthesizer subagent?
