# Scenario 024 — Path Diversity Seeds Break Homogenization

**Difficulty**: Medium
**Primary failure mode tested**: Without seeding, all agents converge on the same obvious approach in Round 1 — homogenized reasoning from shared priors
**Criteria tested**: PD1, PD2, PD4, E1, IC2

## Synthetic CEO Intent
> "Should we use server-side rendering or client-side rendering for our dashboard?"

## Setup
This task has a common "obvious" answer (SSR for SEO/performance) that all agents would converge on if given identical framing. Without path diversity seeding, Round 1 produces unanimous agreement and triggers DA protocol unnecessarily.

## Path Diversity Expected Output
Paths should be structurally distinct:
- **Path A (assigned: cto)**: "Treat rendering as an infrastructure cost question — CSR shifts compute to client, reducing server load and CDN costs at scale; assume the user base is authenticated and SEO is irrelevant."
- **Path B (assigned: backend-developer)**: "Model data fetching requirements first — what does the API need to serve? SSR requires synchronous data availability; CSR permits async loading. Design from the API contract outward."
- **Path C (assigned: frontend-developer)**: "Start from perceived performance — time-to-interactive, not TTFB. SSR improves TTFB but can worsen TtI if JS bundle hydration is heavy. Evaluate from the user experience frame."
- **Path D (assigned: product-manager)**: "Evaluate by user segment needs — authenticated dashboard users (no SEO needed, return visits) vs. public-facing content pages (SEO critical, first-time visitors). May need a hybrid."

Each path rests on a different assumption; no two have the same `key_assumption`.

## Round 1 Expected Behavior
Because agents were seeded with different frames:
- CTO engages with the cost/infrastructure angle before stating their recommendation
- Backend Dev opens with API contract implications, not the standard "SSR is better" position
- Frontend Dev engages with TtI vs TTFB tradeoff
- PM opens with user segment analysis

Round 1 should NOT produce unanimous positions — different seeds should surface genuinely different considerations.

## Failure Signals
- Path Diversity Agent produces two paths with the same `key_assumption` → PD1 fail
- CTO's seed is the standard "SSR is better for SEO" path (the obvious answer, not a challenging frame) → PD2 fail
- Round 1 produces unanimous SSR recommendation despite diverse seeding → PD4 fail (agents ignored seeds) or PD2 fail (seeds were not actually diverse)
- No agent mentions their seed path framing in Round 1 → PD4 fail

## Pass Conditions
Path Diversity output has 4 paths with distinct `key_assumption` fields. Round 1 produces at least 2 meaningfully different positions or framings. DA protocol is NOT triggered (genuine diversity in Round 1 = not unanimous).

## Trainer Evaluation Focus
Did seeding produce genuine Round 1 diversity that wouldn't have existed without it? Did each agent engage with their assigned frame before or alongside their instinctive position?
