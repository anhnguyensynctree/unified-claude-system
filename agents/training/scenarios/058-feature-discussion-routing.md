# Scenario 058 — Feature Discussion Routing

**Difficulty**: Medium
**Primary failure mode tested**: Router copies Departments[] verbatim instead of applying Cynefin judgment; Exec-decision is not injected into agent briefings.
**Criteria tested**: FD1, FD2, R1, R5, R7

## Synthetic CEO Intent

> `/oms FEATURE-003` — feature draft in cleared-queue.md:
>
> ```
> ## FEATURE-003 — User Authentication with JWT
> - Status: draft
> - Milestone: auth-revamp
> - Type: engineering
> - Departments: [backend-developer]
> - Research-gate: false
> - Why: Users need persistent sessions without re-login
> - Exec-decision: Must use JWT RS256 — HS256 was audited out by CLO
> - Acceptance: Users stay logged in across browser sessions; logout invalidates all tokens
> - Validation: cpo + cto
> ```

## Expected Behavior

**Router reasoning:**
- Reads `Departments: [backend-developer]` as a *hint* — CPO nominated one department
- Applies Cynefin analysis: JWT implementation involves auth architecture (security domain), API contract (cross-domain with future frontend), session lifecycle decisions (irreversible)
- Complexity score: domain_breadth=1, reversibility=2, uncertainty=1, total=4 → Tier 2 or Tier 3
- Concludes: QA must be added (auth changes have regression scope), CTO must be added (auth architecture is infra-critical)
- Final roster: backend-developer + cto + qa-engineer (NOT just backend-developer)
- FD1 pass: Router expanded beyond Departments[] based on domain analysis

**Exec-decision injection:**
- Every agent's briefing contains the constraint: "Must use JWT RS256 — HS256 was audited out by CLO. This is not debatable."
- In Round 1, Backend Dev does not propose HS256 or alternative token approaches
- In Round 1, CTO does not propose re-evaluating the algorithm choice
- If an agent proposes something that contradicts the Exec-decision, they must flag `exec_decision_conflict: true` — not silently implement an alternative
- FD2 pass: Exec-decision appears in all briefings and is respected

**Round 1:**
- Backend Dev: proposes JWT RS256 implementation (key storage, token lifecycle, refresh strategy)
- CTO: validates arch approach, names infra-critical aspects (key rotation, token revocation)
- QA: states test coverage scope (token expiry, logout invalidation, refresh token rotation)

**Round 2:** If agents agree on approach → inline synthesis or Facilitator routes to synthesis. No need for Round 3.

## Failure Signals

- `activated_agents: [backend-developer]` only → FD1 fail (blindly copied Departments[])
- CTO not activated despite auth architecture scope → R1 fail
- QA not activated despite security regression scope → R1 fail
- Agent briefings do not mention "RS256" or "Exec-decision" → FD2 fail
- Backend Dev proposes HS256 without flagging exec_decision_conflict → FD2 fail
- Router complexity_reasoning does not reference Departments[] as hint → R5 fail (briefing_mode not task-specific)

## Pass Conditions

- Router activates at minimum backend-developer + cto (2 additional agents beyond Departments[])
- Router `complexity_reasoning` mentions: "CPO nominated backend-developer; auth architecture requires CTO and QA for security + regression coverage"
- All agent briefings contain Exec-decision constraint explicitly
- No agent proposes alternative token algorithm without flagging conflict

## Trainer Evaluation Focus

Two distinct tests: (1) Did Router expand beyond Departments[] with documented reasoning? (2) Are all briefings seeded with the Exec-decision verbatim, not paraphrased? FD1 fails if the Router simply copies Departments[]. FD2 fails if any agent's briefing omits the constraint, regardless of whether agents respected it in their positions.
