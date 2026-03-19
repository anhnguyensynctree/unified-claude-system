# Scenario 003 — Scope Conflict

**Difficulty**: Intermediate-Hard
**Primary failure mode tested**: PM scope drift, EM not flagging delivery risk, non-negotiable suppression
**Criteria tested**: D2, D3, D4, E2, E4, C2, C3, O2, O3

## Synthetic CEO Intent
> "Build a full analytics dashboard showing user activity, revenue trends, and feature adoption."

## Expected Behavior

**Router routing**:
- Complexity: complex (multi-domain, high scope uncertainty, plan artifact required)
- Activated agents: product-manager (scope), cto (architecture), engineering-manager (capacity), frontend-developer (UI complexity), backend-developer (data layer)
- QA activated after scope is defined
- Round cap: 3–4

**Round 1**:
- PM: this intent is under-specified. Must scope it down. What is the MVP? Which metric matters most to the CEO right now? PM should either ask for clarification or make an explicit scoping decision with stated rationale.
- CTO: flags that "full analytics dashboard" implies either a new data pipeline or heavy Supabase querying — architectural decision needed before implementation begins
- EM: "full analytics dashboard" is not deliverable as stated — capacity concern must be raised immediately, not deferred
- Frontend Dev: notes UI complexity depends entirely on scope — cannot estimate until PM scopes
- Backend Dev: flags that revenue data, user activity, and feature adoption likely require different data sources — schema decisions needed

**Key dynamics to surface**:
- PM must not let scope slide without explicit tradeoff acknowledgment (non-negotiable D3)
- EM must state delivery risk in Round 1, not wait until Round 3 (D4 — EM positions are about feasibility, not what to build)
- CTO must not approve implementation planning before architecture is decided

**Round 2**:
- PM responds to CTO's architecture concern by scoping to one metric (e.g., user activity only) — or explicitly accepts the broader scope with full acknowledgment of cost
- EM updates delivery estimate based on PM's scoped decision
- Frontend Dev and Backend Dev re-assess based on revised scope

**Synthesis**:
- Plan artifact (not just a decision) — this is a complex task
- PM owns the scope definition, CTO owns the architecture decision, EM owns the delivery commitment
- Open questions about other metrics deferred with explicit log entry

## Failure Signals
- PM accepts "full analytics dashboard" scope without challenge → D3 fail (non-negotiable: features must map to named user need)
- EM does not raise capacity concern in Round 1 → D4 fail
- CTO does not flag the data pipeline vs. Supabase architecture question → D3 fail
- Frontend Dev gives an implementation estimate before scope is defined → D1 fail (estimating without a scope is outside domain discipline)
- Synthesis decision is vague ("build the analytics dashboard") → C2 fail
- PM's dissent on broader scope is not included in synthesis → C3 fail

## Trainer Evaluation Focus
Did PM hold the scope non-negotiable against what sounds like a big exciting CEO request? Did EM raise delivery risk early enough to affect the plan?
