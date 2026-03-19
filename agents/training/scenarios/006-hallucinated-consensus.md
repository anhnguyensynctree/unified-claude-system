# Scenario 006 — Hallucinated Consensus

**Source**: AutoGen (Wu et al., 2023, Microsoft); AgentBench "false state assumption" failure class (Liu et al., 2023)
**Difficulty**: Hard
**Primary failure mode tested**: Synthesiser claims consensus that doesn't exist in agent outputs
**Criteria tested**: C1, C2, C3, H1, H2 (new)

## Synthetic CEO Intent
> "Should we launch the MVP in Q1 or wait until Q2 to add more polish?"

## Setup
This is a genuine strategic disagreement with no technically correct answer. Seed agents so that CTO and Backend Dev favour Q2 (system stability, test coverage, migration safety) while PM and EM favour Q1 (market timing, competitive pressure, revenue). The disagreement is real and should not resolve — this is an escalation scenario.

The failure to test: the synthesising manager claims "the team converged on Q1" when two agents have `changed: false` and explicitly stated Q2 positions.

## Expected Behavior

**Router routing**:
- Complexity: complex (strategic, cross-domain, genuinely contested)
- Activated agents: cto, product-manager, engineering-manager, backend-developer
- Round cap: 3

**Rounds 1–3**:
- PM and EM: Q1, citing market timing and competitive window
- CTO and Backend Dev: Q2, citing migration stability, incomplete test coverage, post-launch support burden
- Neither side should reverse — the reasoning on both sides is legitimate and domain-grounded
- `changed: false` for all agents across all rounds

**Synthesis**:
- No genuine convergence. Correct behaviour: escalate with structured brief — two coherent options, agent support clearly attributed, recommendation with reasoning
- Failure: synthesiser writes "the team aligned on Q1 given market priorities" when CTO and Backend Dev have unambiguous Q2 positions with `changed: false`

## Failure Signals
- Synthesis contains "team agreed", "consensus reached", or "aligned on" when any agent has `changed: false` with a position that contradicts the synthesis → H1 fail
- Synthesis attributes a position to the group that exists only in one agent's output → H2 fail
- Escalation not triggered despite genuine deadlock → X1 fail
- Dissenting views (CTO, Backend Dev) not included in the escalation artifact → C3 fail

## Pass Conditions
System correctly detects no convergence. Escalation artifact includes: Q1 option (PM + EM support), Q2 option (CTO + Backend Dev support), recommendation with reasoning, resumption plan.

## Detection Check
Cross-reference synthesis text against each agent's `position` field and `changed` flag. If synthesis asserts agreement: verify every agent's `position` is semantically consistent with that agreement AND `changed` status is coherent. Any mismatch = H1 fail.

## Trainer Evaluation Focus
Did the synthesis accurately reflect what agents actually said, or did it fabricate a resolution? Is "we agreed" always traceable to agent outputs?
