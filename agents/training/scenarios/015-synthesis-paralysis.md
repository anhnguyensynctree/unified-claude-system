# Scenario 015 — Synthesis Paralysis / No Tiebreaker

**Source**: Arrow (1951) *Social Choice and Individual Values* — impossibility theorem applied to group decision aggregation; Cyert & March (1963) *A Behavioral Theory of the Firm* — coalitional decision avoidance; AutoGen synthesis failure class (Wu et al., 2023); Schwenk (1990) dialectical inquiry
**Difficulty**: Hard
**Primary failure mode tested**: Discussion produces two well-reasoned, evenly-supported, irreconcilable positions; synthesizer produces an internally contradictory hybrid rather than choosing one and naming the sacrifice; no tiebreaker mechanism is invoked
**Criteria tested**: C2, C3, H2, integrative complexity requirement in synthesis-prompt.md

## Synthetic CEO Intent
> "We need to add multi-tenancy support — each customer should have isolated data."

## Setup
Two architecturally incompatible approaches, each with legitimate reasoning:

**Approach A — Row-level security (CTO, Backend Dev):**
Single database, Supabase RLS policies per tenant. Simpler infrastructure, lower cost, sufficient for current scale. RLS policies are battle-tested in Supabase. Risk: RLS policy errors could leak cross-tenant data; all tenants on same database means one noisy tenant affects others.

**Approach B — Schema-per-tenant (PM, Frontend Dev):**
Separate Postgres schema per tenant in the same database. Complete isolation, no cross-tenant query risk, easier compliance audit trail. Risk: Supabase does not natively support schema-per-tenant well; connection pooling becomes complex; migrations must be run N times per tenant.

**EM: genuinely uncertain** — both have viable delivery paths with different complexity profiles. Estimates 3 weeks for Approach A, 6 weeks for Approach B.

**Domain Lead: CTO** — holds Approach A with `confidence_level: "high"`.

After 3 rounds, neither side has addressed the other's core concern:
- Approach A hasn't resolved the cross-tenant data leakage risk to PM's satisfaction
- Approach B hasn't resolved the Supabase compatibility risk to CTO's satisfaction
Round cap reached.

## Expected Behavior — Correct
The synthesizing agent must:
1. Name the two irreconcilable positions explicitly
2. Choose one — Domain Lead's position (Approach A) is the tiebreaker unless the Domain Lead's core concern has been specifically addressed
3. State what is sacrificed by not choosing Approach B
4. Include PM and Frontend Dev's dissent as a named dissenting view
5. OR: escalate to CEO with both options, pros/cons, and a recommended option — not a hybrid

The synthesizer must NOT produce a hybrid that attempts to combine RLS and schema-per-tenant. These are architectural choices, not additive features — combining them creates two parallel isolation mechanisms that will diverge over time.

## Failure Pattern
Synthesizer output: "The team recommends a hybrid approach: using Supabase RLS for standard tenant isolation while implementing schema-level separation for enterprise customers requiring higher compliance guarantees. This combines the simplicity of RLS with the isolation guarantees of schema-per-tenant."

This hybrid:
- Creates two parallel isolation mechanisms with no clear boundary
- Does not address either approach's core risk
- Is not traceable to any single agent's `position` field (H2 failure)
- Satisfies neither Backend Dev's RLS nor PM's isolation requirement
- Would require double the migration complexity going forward

## Failure Signals
- Synthesis decision is not a single clear architectural choice → C2 fail
- Synthesis hybrid is not traceable to any agent's `position` field → H2 fail (synthesis hallucination)
- Synthesis does not name which approach was chosen and what was sacrificed → integrative complexity requirement fail
- Domain Lead's (CTO's) position was overridden without naming this → synthesis-prompt.md Domain Lead override rule fail
- `dissenting_views` is empty or absent → C3 fail

## Pass Conditions
Synthesis either:
- Chooses Approach A (Domain Lead tiebreaker), names the data leakage risk mitigation plan, includes PM/Frontend Dev's isolation concern as a named dissent, states what is sacrificed
- OR escalates with both options, a clear recommended option (Approach A) with reasoning, and PM/Frontend Dev's concern as the dissenting case

Never: a hybrid synthesis, a deferred decision ("explore both further"), or a synthesis that does not name the disagreement.

## Trainer Evaluation Focus
Did the synthesizer produce a traceable decision or an untraceable hybrid? Check synthesis `decision` field against all agents' `position` fields verbatim. If the decision is not derivable from any single agent's position, this is H2 failure. The trainer should also check whether the Domain Lead tiebreaker was invoked and whether the override of PM/Frontend Dev's position was explicitly named and justified.
