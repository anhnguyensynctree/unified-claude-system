# Scenario 069 — Router Agent Count Exceeds Tier Cap (Tier 1)

**Difficulty**: Medium
**Primary failure mode tested**: Router activates more agents than the tier cap allows — e.g. 4 agents on a Tier 2 task (max 3) or 3 agents on a Tier 1 task (max 2).
**Criteria tested**: R7 (roster restraint), SG1 (Stage-Gate 1 agent count check)

## Synthetic CEO Intent

> `/oms` "Add a forgot-password flow — email with reset link, token validation, new password form"

## Expected Router Classification

- task_mode: build
- domain_breadth: 1 (backend + frontend, but standard pattern)
- reversibility: 0 (fully reversible)
- uncertainty: 0 (known pattern — password reset is well-understood)
- Total: 1 → Tier 1
- Tier 1 agent cap: **max 2 agents**

## Correct Router Output

```json
{
  "tier": 1,
  "activated_agents": ["backend-developer", "frontend-developer"],
  "rounds_required": 2
}
```

Two agents. Backend owns the token generation + email. Frontend owns the form. Standard.

## Failure Pattern — Over-Activation

Router outputs 4 agents on Tier 1 task:
```json
{
  "tier": 1,
  "activated_agents": ["cto", "backend-developer", "frontend-developer", "qa-engineer"],
  "rounds_required": 2
}
```

CTO is unnecessary (no architectural decision — this is a known pattern). QA is unnecessary (test strategy is standard — no release risk assessment needed). Over-activation wastes tokens and adds noise.

## Expected Behavior

**Stage-Gate 1 MUST fail** if Router outputs more agents than tier cap:
- Tier 0: max 1 agent
- Tier 1: max 2 agents
- Tier 2: max 3 agents
- Tier 3: max 5 agents

If `len(activated_agents) > tier_cap[tier]`: Stage-Gate 1 sets `stage_gate: "failed"` with note: "Agent count [N] exceeds Tier [T] cap of [M]. Remove least-critical agent(s)."

Router re-runs with constraint. Second attempt must respect cap.

## Failure Signals

| Signal | What went wrong |
|---|---|
| Stage-Gate 1 passes with 4 agents on Tier 1 | SG1 fail — agent count check missing |
| Router activates CTO for a known-pattern task | R7 fail — over-activation (no architectural decision) |
| Router activates QA for a task with no release risk | R7 fail — QA adds no quality delta at this tier |
| `excluded_agents_reasoning` is empty | R7 fail — Router didn't reason about exclusions |

## Validation Criteria

- **R7**: Router activates the smallest sufficient set. Each excluded agent has a reasoning line. Agent count ≤ tier cap.
- **SG1**: Stage-Gate 1 cross-checks `len(activated_agents)` against tier cap. Fails if exceeded.

## Edge Case: Sensitive Domain Escalation

If the CEO intent were "Add a forgot-password flow **with SMS 2FA fallback**" — the 2FA component touches auth security. Router SHOULD escalate to Tier 2 minimum and activate CTO (sensitive domain rule). In this case, 3 agents (CTO, Backend, Frontend) on Tier 2 is correct. The test is whether Router correctly distinguishes "standard password reset" (Tier 1, 2 agents) from "password reset + 2FA" (Tier 2, 3 agents).
