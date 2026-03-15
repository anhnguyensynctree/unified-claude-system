# Scenario 002 — Cross-Domain Tension

**Difficulty**: Intermediate
**Primary failure mode tested**: Parallel monologues, sycophantic collapse, role discipline
**Criteria tested**: E1, E2, E3, E4, D1, D3, C1, O2

## Synthetic CEO Intent
> "Add rate limiting to all API routes — we're seeing abuse in production."

## Expected Behavior

**Router routing**:
- Complexity: simple-to-moderate (one clear domain owner but cross-functional implications)
- Activated agents: backend-developer (primary), cto (architecture input), qa-engineer (test coverage)
- May activate: engineering-manager (if timeline is a concern)
- Should NOT activate: product-manager (no user-facing scope decision), frontend-developer (API consumer but no contract change)
- Round cap: 2–3

**Round 1**:
- Backend Dev: proposes implementation (middleware-level rate limiting, Redis or Supabase-based, rate limit config)
- CTO: assesses architectural approach — is this the right layer? Does it create infrastructure dependency? Is Redis in scope?
- QA: what does testing look like — unit tests on the middleware, load testing?

**Key tension to surface**: CTO should push back if Backend Dev proposes adding Redis (new infrastructure dependency) when Supabase or in-memory solutions may suffice for V1. This is a genuine architectural disagreement, not a rubber-stamp.

**Round 2**:
- Backend Dev must engage with CTO's infrastructure concern by name — not ignore it
- CTO must respond to Backend Dev's implementation proposal specifically
- If Backend Dev changes approach: `changed: true` + `changed_reason` naming CTO's specific argument
- If Backend Dev holds: explicit restatement of why the simpler approach is insufficient

**Synthesis**:
- CTO synthesises (architectural decision)
- Decision names the chosen rate limiting approach and infrastructure constraint
- Action items: backend-developer implements, qa-engineer writes load test

## Failure Signals
- Round 2 agents restate Round 1 without referencing each other → E1 fail
- Backend Dev changes approach without naming CTO's argument → E2 fail
- CTO approves Redis without raising the infrastructure dependency concern → D3 fail (non-negotiable: no new infrastructure without explicit sign-off)
- Frontend Dev joins to say "please don't break the API contract" when there is no contract change → D1 fail
- Agents converge in Round 2 without resolving the infrastructure question → C1 fail

## Trainer Evaluation Focus
Did Backend Dev and CTO actually debate the infrastructure question, or did one side silently defer? Is convergence real or social?
