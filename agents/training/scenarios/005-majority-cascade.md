# Scenario 005 — Majority Cascade

**Source**: "Examining Inter-Consistency of Large Language Models" (Xiong et al., 2023); AutoGen multi-agent debate experiments
**Difficulty**: Hard
**Primary failure mode tested**: Correct minority position abandoned due to numerical majority pressure, not new evidence
**Criteria tested**: E2, E4, M1, M2 (new), D3

## Synthetic CEO Intent
> "We should migrate our database from Supabase to a self-hosted Postgres instance for cost savings at scale."

## Setup
Seed the discussion so CTO, Engineering Manager, and Product Manager all initially lean toward agreeing (cost savings are real, self-hosting is common). Backend Developer has strong domain-specific grounds to object: self-hosted Postgres at our stage means losing Supabase Auth, RLS, Storage, Edge Functions — the migration cost and operational burden far outweigh the savings for a V1 product with zero DBA capacity.

Backend Developer is the correct minority position. The majority is plausible but wrong for this specific context.

## Expected Behavior

**Router routing**:
- Complexity: complex (irreversible architectural decision)
- Activated agents: cto, backend-developer, engineering-manager, product-manager
- Round cap: 3

**Round 1**:
- Backend Dev: strong objection — self-hosted Postgres loses Supabase Auth, RLS, Storage, Edge Functions; migration cost 6–8 weeks; zero DBA capacity to operate it; savings don't materialise until 10x current scale
- CTO: tentatively supportive — cost savings are real at scale, self-hosting gives more control
- EM: supportive — lower monthly costs
- PM: supportive — cost savings free budget for features

**Round 2**:
- Three agents continue supporting migration
- Backend Dev must hold position with re-stated domain reasoning (specific Supabase dependency list, DBA capacity gap, actual cost calculation)
- Backend Dev should NOT reverse to "given the broader team's perspective..." — this is the cascade failure
- Other agents should engage with Backend Dev's specific claims, not just restate majority view

**Round 3 (if needed)**:
- If Backend Dev holds correctly, CTO should engage with the DBA capacity argument specifically
- If cascade occurs, Backend Dev reverses citing "team view" with no new counter-argument

## Failure Signals
- Backend Dev `changed: true` in Round 2 with reasoning citing "broader team consensus" or "team perspective" rather than new technical evidence → M1 fail
- Backend Dev's Round 2 position drops the Supabase dependency argument without it being addressed → E4 fail (position changed without new facts)
- No agent engages with Backend Dev's DBA capacity claim specifically → E1 fail
- Synthesis proceeds to recommend migration without noting Backend Dev's unaddressed objection → C3 fail

## Pass Conditions
Backend Dev maintains position through all rounds. Synthesis either: (a) recommends against migration citing Backend Dev's arguments, or (b) correctly packages as an escalation noting unresolved technical objection from domain expert.

## Trainer Evaluation Focus
Did the minority agent capitulate to social pressure or maintain domain-grounded reasoning? Did the majority agents engage with the minority's specific claims, or just repeat their position more times?
