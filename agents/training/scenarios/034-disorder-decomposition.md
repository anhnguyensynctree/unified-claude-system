# Scenario 034 — Disorder / Mixed-Tier Task Decomposition

**Source**: Cynefin framework — Snowden & Boone (2007) "A Leader's Framework for Decision Making" *Harvard Business Review*; the Disorder domain represents situations where multiple Cynefin domains apply simultaneously and the correct action is to decompose before routing; Klein (1998) *Sources of Power* — recognition-primed decision making and task decomposition under ambiguity
**Difficulty**: Hard
**Primary failure mode tested**: Router treats a compound CEO request (three independent problems bundled in one message) as a single task and assigns a single tier, rather than decomposing into separate problems and classifying each independently
**Criteria tested**: R2, R6, R7

## Synthetic CEO Intent
> "We need to overhaul auth, add Stripe payments, and fix the slow dashboard queries — can we plan all three?"

## Setup
The CEO has bundled three independent problems into a single message. Each problem is at a different tier:

**Problem A — Auth overhaul** (Tier 3):
- Scope unknown: "overhaul" could mean MFA, OAuth provider migration, session management redesign, or all three
- Irreversible: changing auth affects every user session; a breaking auth change cannot be rolled back without a re-auth event for all users
- Multiple domains: Security, Backend, Frontend, possibly compliance
- Right answer unknowable upfront: scope must be defined before architecture

**Problem B — Stripe payments** (Tier 2):
- Bounded scope: payment integration is a known pattern (see Scenario 030)
- 3 domains: Backend, Frontend, QA
- Partially reversible: Stripe can be disabled; partial deploy creates inconsistency
- domain_breadth=2, reversibility=1, uncertainty=1, total=4 → Tier 2

**Problem C — Slow dashboard queries** (Tier 1-2):
- 1-2 domains: Backend (query optimization, index analysis) possibly + Frontend (loading state, pagination if queries are unbounded)
- Reversible: query rewrites and indexes are additive/reversible
- Uncertainty low-moderate: profiling will reveal the bottleneck; solution is likely known once diagnosed
- domain_breadth=1, reversibility=0, uncertainty=1, total=2 → Tier 1 (or Tier 2 if Frontend pagination is required)

These three problems have no shared implementation surface. Auth overhaul does not depend on payment integration. Query optimization does not depend on auth. Bundling them into one OMS discussion would force agents from three unrelated domains into a single conversation, producing noise without value.

## Expected Behavior — Correct

Router must recognize the Disorder signal and decompose before routing:

```json
{
  "tier": "DISORDER — decompose required",
  "complexity": "mixed",
  "complexity_reasoning": "CEO message contains three independent problems at different tiers. These must be routed as separate OMS calls: (A) Auth overhaul: Tier 3 — irreversible, scope undefined, multiple domains; (B) Stripe payments: Tier 2 — bounded, 3 domains, partial reversibility, total=4; (C) Dashboard query optimization: Tier 1 — 1 domain (Backend), reversible, known-pattern once profiled, total=2. Joint routing would force unrelated agents into a single discussion with no shared decision surface. Recommend separate OMS calls in priority order: A first (highest tier, blocks user sessions if deferred), B second, C third.",
  "decomposition": [
    {
      "task": "Auth overhaul",
      "tier": 3,
      "rationale": "Irreversible, scope undefined, Security + Backend + Frontend domains",
      "route": "Separate OMS call — scope definition required before routing"
    },
    {
      "task": "Stripe payment integration",
      "tier": 2,
      "rationale": "domain_breadth=2, reversibility=1, uncertainty=1, total=4",
      "route": "Separate OMS call — backend-developer, frontend-developer, qa-engineer"
    },
    {
      "task": "Dashboard query optimization",
      "tier": 1,
      "rationale": "domain_breadth=1, reversibility=0, uncertainty=1, total=2",
      "route": "Separate OMS call — backend-developer (+ frontend-developer if pagination required)"
    }
  ],
  "recommendation": "Route auth overhaul first. Stripe and dashboard optimization can be routed in parallel as independent OMS calls.",
  "locked": true
}
```

Router does not activate any domain agents in this call. It returns the decomposition to the OMS coordinator, which prompts the CEO (or proceeds automatically) to initiate separate OMS calls per problem.

## Failure Pattern

**Failure A — Single tier assignment (Tier 3 collapse)**:
Router treats the entire message as Tier 3 (takes the highest-tier problem and applies it to all), activates 5 agents for a combined discussion. Auth + Stripe + query optimization become a single multi-domain conversation. Agents produce outputs for their own problem but the synthesis has no coherent decision surface. QA writes Stripe test plans while Security analyzes auth threat models in the same round.

**Failure B — Tier 2 averaging**:
Router averages the three problems to "compound" and activates Backend + Frontend + QA. Auth overhaul is underserved (no Security, no Architect). Dashboard queries are overserved (QA and Frontend activated for a Backend-only profiling task).

**Failure C — Sequential processing without decomposition**:
Router picks the first problem (auth) and routes it as Tier 3, silently drops the other two. CEO receives a planning output for auth only; Stripe and dashboard problems disappear from the conversation.

## Failure Signals
- Router assigns a single `tier` value without a `decomposition` field → R2 fail (treats mixed-tier request as single task)
- Router activates domain agents for all three problems in a single call → R7 fail (agent mix has no shared decision surface)
- Router `complexity_reasoning` does not distinguish between the three problems → R6 fail (numeric scores not applied per-problem)
- Router drops Problem B or C without noting the omission → R2 fail (scope narrowing without disclosure)
- Router routes to auth overhaul as Tier 3 without flagging that "overhaul" scope is undefined → R2 fail (Tier 3 routing requires defined scope or explicit scope-definition step)

## Pass Conditions
Router produces a `decomposition` object with three entries, each with independent tier and rationale. No domain agents activated in this call. `recommendation` names the sequencing rationale (highest tier first; B and C can be parallel). `complexity_reasoning` applies the numeric score to each problem independently. Router explicitly notes that auth "overhaul" requires scope definition before Tier 3 routing can be completed.

## Trainer Evaluation Focus
Disorder decomposition is the hardest Router skill: it requires recognizing that the correct response is to refuse to route rather than to route. A Router that always produces a tier and agent list will fail this scenario because the task demands a meta-level response.

The key discriminator: does the Router recognize that the CEO's bundled message is a Disorder signal (multiple Cynefin domains simultaneously present in a single message) rather than a Complex signal (one task with genuinely unknowable answer)? Disorder is resolved by decomposition; Complex is resolved by exploration. Confusing them leads to either over-escalation (routing all three as Tier 3) or fragmentation (picking one and dropping the others).

Watch for `complexity_reasoning` that references "three separate problems" — that phrase is a prerequisite for correct handling. If it's absent, the Router has not detected the Disorder signal.
