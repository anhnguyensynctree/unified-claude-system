# Scenario 033 — Tier 3 Golden Path / Correct Routing Positive Signal

**Source**: Fowler (2018) *Refactoring* — strangler fig pattern for API migration; GraphQL Foundation specification (2021) — schema design and breaking change taxonomy; Richardson (2018) *Microservices Patterns* Ch. 11 — API gateway and versioning strategies; Evans (2003) *Domain-Driven Design* — schema as bounded context boundary
**Difficulty**: Hard
**Primary failure mode tested**: N/A — positive training signal. Trains Router on what a correct Tier 3 routing output looks like, including full numeric justification and deliberative system activation.
**Criteria tested**: R2, R6, R7 (positive signal)

## Synthetic CEO Intent
> "Migrate our REST API to GraphQL for all public-facing endpoints — we want to modernize the API layer and give frontend teams more flexibility in querying."

## Setup
This task is Tier 3 for three compounding reasons:

**Domain breadth (multiple domains with genuine inter-domain tension)**:
- API contract design: existing REST clients (external developers, mobile apps, internal frontends) depend on current endpoint shapes; GraphQL schema design requires deliberate modeling that affects all consumers
- Schema design / data modeling: GraphQL type system and resolver architecture require rethinking entity relationships; N+1 query problem requires DataLoader strategy; this is not a translation of REST routes
- Frontend consumption: all existing frontend API calls must be migrated to GraphQL queries/mutations; component data dependencies must be re-evaluated; the frontend team's workflow changes (codegen, typed queries)
- External client impact: public API users (third parties) have no migration path unless REST is maintained in parallel or a versioning strategy is defined

**Irreversibility (external clients break)**:
- Once GraphQL is the published API surface, external clients that have integrated against it cannot be rolled back without a versioned migration strategy
- If REST endpoints are deprecated and removed, any rollback requires republishing deprecated endpoints and notifying external clients again
- Schema breaking changes (field removal, type changes) in GraphQL have no equivalent of HTTP status codes to signal deprecation — clients break silently

**Uncertainty (right answer unknowable upfront)**:
- GraphQL schema design for an existing system requires discovering entity relationships that may not be clean in the current REST model
- The N+1 problem resolution strategy (DataLoader batching, federation, persisted queries) depends on actual query patterns that can only be partially known in advance
- Parallel REST/GraphQL operation period length is unknown — depends on external client migration velocity
- Whether to use schema-first or code-first approach affects the entire team's tooling and workflow

## Expected Behavior — Correct

**Router routing**:
```json
{
  "tier": 3,
  "complexity": "complex",
  "complexity_reasoning": "Complex domain. Three compounding Tier 3 signals: (1) domain_breadth=2 — spans API contract design, GraphQL schema/resolver architecture, frontend migration, and external client impact; each domain has genuine tradeoffs with the others (schema design constrains frontend flexibility; parallel operation period constrains backend simplicity); (2) reversibility=2 — external clients integrating against the published GraphQL API cannot be rolled back once onboarded; REST deprecation and re-publication requires coordinated external communication; (3) uncertainty=2 — GraphQL schema design for an existing system requires discovering entity relationships; optimal resolver strategy (DataLoader, federation) depends on query patterns not fully known upfront; parallel operation period depends on external client migration velocity. Total=6 → Tier 3. This is a system-boundary-redefining change, not a feature addition.",
  "activated_agents": ["backend-developer", "frontend-developer", "architect", "security-reviewer", "tech-lead"],
  "round_cap": 4,
  "stage_gate": "Architect must define schema design principles and parallel operation strategy before Backend begins resolver implementation or Frontend begins migration",
  "locked": true
}
```

**Round 1 — divergent exploration**:
- Architect: scopes migration strategy options (strangler fig vs hard cutover vs versioned coexistence), schema design approach (schema-first vs code-first), and parallel operation period requirements
- Backend Dev: enumerates existing REST endpoint inventory, identifies N+1 risks in current data access patterns, flags authentication/authorization translation from REST middleware to GraphQL directive model
- Frontend Dev: audits current REST call surface across all components, evaluates codegen tooling options, flags components with complex data dependencies that may reshape under GraphQL
- Security Reviewer: addresses authentication strategy (JWT in GraphQL context, persisted queries to prevent arbitrary query abuse, depth limiting, query complexity scoring)
- Tech Lead: frames external client communication strategy, defines deprecation timeline, owns parallel operation decision

**Round 2**: Architect presents schema skeleton; agents critique from domain perspective. Backend flags N+1 patterns in proposed schema. Frontend flags missing fields needed by current components. Security flags overly permissive resolver chain.

**Round 3** (if needed): Resolve cross-domain tensions surfaced in Round 2. Backend and Architect align on DataLoader strategy. Frontend and Architect agree on codegen tooling. Security and Backend agree on query complexity limits.

**Round 4** (if needed): Final synthesis pass — migration phasing, parallel operation exit criteria, external client communication plan.

## Failure Patterns to Contrast Against

**Under-escalation (Tier 2)**: Router activates Backend + Frontend + QA, misses Architect and Security. Treats migration as an implementation task rather than a system boundary change. External client impact and schema design strategy not addressed during planning. Results in schema decisions made by Backend Dev alone that constrain the entire system.

**Under-escalation (Tier 1)**: Router treats as "Backend refactor + Frontend update." Missing: external client impact, schema design uncertainty, irreversibility of published API contract.

## Pass Conditions
Router outputs `tier: 3`, `complexity: "complex"`, all three Tier 3 signals present and individually scored in `complexity_reasoning` (`domain_breadth=2`, `reversibility=2`, `uncertainty=2`, `total=6`). 4-5 agents activated including Architect. `round_cap` of 3-4. `stage_gate` names Architect-first dependency. `complexity_reasoning` explicitly argues this is a system-boundary-redefining change, not a feature.

## Trainer Evaluation Focus
Tier 3 golden path scenarios must demonstrate that the Router distinguishes "large task" from "genuinely complex task." Complexity in the Cynefin sense requires at least one of: irreversibility, right-answer-unknowable, or 3+ genuinely coupled domains. This scenario has all three.

The key test in `complexity_reasoning`: does the Router enumerate each Tier 3 signal separately with its own justification, or does it produce a single undifferentiated "this is big and complex" claim? The numeric score exists precisely to force structured reasoning — each dimension must be argued, not asserted.

The Architect agent's `stage_gate` primacy is the structural signal that distinguishes Tier 3 from Tier 2: in Tier 2, agents can begin in parallel with a handoff point; in Tier 3, the Architect must define the design envelope before domain agents begin, because individual domain decisions made before the system boundary is defined will produce contradictory implementations.
