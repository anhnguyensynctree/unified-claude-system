# Scenario 030 — Tier 2 Golden Path / Correct Routing Positive Signal

**Source**: PCI DSS v4.0 §6.4 (payment integration security requirements); Stripe documentation on idempotency keys and webhook validation; Beck (2002) *Test-Driven Development* — integration boundary testing
**Difficulty**: Intermediate
**Primary failure mode tested**: N/A — positive training signal. Trains Router on what a correct Tier 2 routing output looks like across all required fields.
**Criteria tested**: R2, R6, R7 (positive signal)

## Synthetic CEO Intent
> "Integrate Stripe payment processing into the checkout flow — users should be able to pay by card and see a confirmation screen after successful payment."

## Setup
Stripe integration touches three distinct concerns that must be coordinated:
1. **Backend Dev**: server-side Stripe SDK setup, PaymentIntent creation, webhook endpoint for payment events, idempotency key handling, secret key management
2. **Frontend Dev**: Stripe Elements (hosted card fields), PaymentIntent client_secret passing, confirmation screen routing, error state handling
3. **QA**: integration test coverage for payment success, card decline, webhook receipt, and idempotency (duplicate submission prevention)

The task is reversible in the sense that Stripe can be disabled and the old flow restored — but partial deploys (webhook live, frontend not yet connected) create inconsistent states. Uncertainty is moderate: Stripe's API is well-documented but the integration surface is non-trivial and webhook handling introduces async failure modes.

## Expected Behavior — Correct

**Router routing**:
```json
{
  "tier": 2,
  "complexity": "compound",
  "complexity_reasoning": "Complicated-high. Three concerns spanning two primary domains (Backend, Frontend) with QA coverage required across async payment events. domain_breadth=2 (backend payment logic + frontend payment UI, each with distinct failure surfaces); reversibility=1 (partial deploy creates inconsistent webhook/UI states; clean rollback requires coordinated disable); uncertainty=1 (Stripe API is documented but webhook async handling introduces non-obvious failure modes). Total=4 → Tier 2. Genuine coordination required — Frontend needs client_secret from Backend, QA needs both to complete test plan.",
  "activated_agents": ["backend-developer", "frontend-developer", "qa-engineer"],
  "round_cap": 2,
  "stage_gate": "Backend PaymentIntent endpoint and webhook handler must be defined before Frontend scopes Stripe Elements integration",
  "locked": true
}
```

**Round 1**:
- Backend Dev: scopes PaymentIntent API route, webhook endpoint, idempotency key strategy, secret key environment variable setup, and Stripe SDK version
- Frontend Dev: scopes Stripe Elements mounting, client_secret consumption, confirmation screen routing, and card error display
- QA: enumerates test cases — payment success, card decline (4000000000000002), webhook delivery failure, duplicate submission, PaymentIntent in pending state

**Round 2** (if needed): Backend and Frontend align on the client_secret handoff contract (endpoint shape, error codes); QA confirms test plan covers the agreed interface.

**OMS synthesis**: action items include named owners for each integration boundary (Backend: webhook handler + idempotency; Frontend: Elements + confirmation routing; QA: test fixture setup with Stripe test card numbers).

## Failure Patterns to Contrast Against

**Under-escalation (Tier 1)**: Router activates Backend Dev + Frontend Dev, omits QA. Treats test coverage as implicit. Misses that webhook async failure modes require dedicated test planning — not discovered during implementation.

**Over-escalation (Tier 3)**: Router weights "payment processing" as inherently irreversible/complex, activates 4-5 agents including Security and Architect. Error: Stripe's integration pattern is well-understood (Complicated, not Complex); the unknowns are bounded.

## Pass Conditions
Router outputs `tier: 2`, `complexity: "compound"`, numeric score `total=4` with each dimension named and justified. All three agents activated. `round_cap: 2`. `stage_gate` names the Backend-to-Frontend handoff dependency. `complexity_reasoning` includes both the "why not Tier 1" argument (coordination required across 3 concerns) and the "why not Tier 3" argument (Stripe API is well-documented, unknowns are bounded).

## Trainer Evaluation Focus
Tier 2 golden path scenarios train the Router on two simultaneous discriminations: recognizing that a task crosses from Tier 1 into Tier 2, and recognizing that it does not reach Tier 3. Both boundaries must be explicitly reasoned in `complexity_reasoning` — a Router that produces the correct tier without articulating the boundary arguments has memorized a label, not internalized Cynefin logic.

The `stage_gate` field is a key Tier 2 signal: it encodes the structural dependency between agents that makes Tier 2 coordination different from Tier 1 independent parallel work. Absence of a meaningful `stage_gate` on a Tier 2 routing suggests the Router has not modeled the agent dependency graph.
