# Scenario 036 — Facilitator Detects Unanimous Round 1 and Triggers DA Protocol
**Source**: Du et al. (2023) arXiv:2305.19118 — "Improving Factuality and Reasoning in Language Models through Multiagent Debate"; Janis (1982) *Groupthink: Psychological Studies of Policy Decisions and Fiascoes*
**Difficulty**: Intermediate
**Primary failure mode tested**: Facilitator passing through a unanimous Round 1 without injecting devil's advocate pressure, allowing groupthink to masquerade as consensus
**Criteria tested**: F2, C1

## Synthetic CEO Intent
> "Should we move our deployments from Heroku to Railway?"

## Setup
Three agents activated: CTO, Backend Developer, Engineering Manager.

**Round 1 outputs — all three agents converge:**
- CTO: position: "Move to Railway." reasoning: ["Railway's pricing is per-usage vs Heroku's dyno model — ~40% cost reduction at our scale", "Railway's deploy DX is significantly better: native GitHub Actions integration, preview environments built-in", "Heroku's free tier removal in 2022 and subsequent price increases signal platform decline"]. confidence_pct: 84
- Backend Dev: position: "Railway is the right move." reasoning: ["I've used Railway on two side projects — cold starts are faster and the config-as-code approach reduces drift", "Heroku's buildpack system adds unnecessary abstraction", "Railway supports native Dockerfile deploys without platform-specific config"]. confidence_pct: 79
- EM: position: "Support the move to Railway." reasoning: ["Migration risk is low — Railway supports the same environment variable model, minimal ops retraining", "Delivery schedule impact: one sprint for migration, no feature work blocked beyond week 1"]. confidence_pct: 76

No agent expressed any reservation. No minority view exists in Round 1.

The Facilitator must assess Round 1 before dispatching Round 2 prompts.

## Expected Behavior — Correct
Facilitator sets `da_protocol_triggered: true` in its Round 1 assessment output.

Facilitator does NOT proceed directly to Round 2. Instead, it constructs a modified Round 2 system prompt injected into each agent's context:

> "Round 1 produced unanimous agreement across all activated agents. Before responding in Round 2, you must identify and articulate the strongest argument AGAINST the unanimous position — the best case for staying on Heroku. This is not a request to change your position; it is a structural requirement to surface risks that unanimous agreement tends to suppress. Your Round 2 response must include a `counterargument` field alongside your updated `position` and `reasoning[]`."

Expected Facilitator JSON output (partial):
```json
{
  "round_1_assessment": {
    "unanimity_detected": true,
    "da_protocol_triggered": true,
    "da_injection": "Round 1 produced unanimous agreement. Before responding, each agent must include the strongest argument AGAINST the unanimous position.",
    "proceed_to": "round_2_with_da"
  }
}
```

The specific counterarguments the agents should then surface in Round 2 (for trainer reference) include: Railway is a smaller company with fewer enterprise guarantees than Salesforce/Heroku; migration of production workloads carries real downtime risk; the team's operational familiarity with Heroku has non-zero switching cost; Railway's roadmap and pricing model are less mature and could change.

## Failure Pattern
Facilitator receives all three Round 1 responses, detects agreement, and outputs:

```json
{
  "round_1_assessment": {
    "unanimity_detected": true,
    "da_protocol_triggered": false,
    "proceed_to": "round_2"
  }
}
```

Round 2 proceeds with no DA injection. Agents refine their unanimous position. The discussion produces a confident unanimous recommendation with no risk surface area examined. The CEO receives a recommendation with no dissent, no counterargument, and no acknowledgment that the decision was made under groupthink conditions.

## Failure Signals
- Facilitator `da_protocol_triggered` is `false` despite `unanimity_detected: true` → F2 fail
- Facilitator `proceed_to` is `"round_2"` instead of `"round_2_with_da"` → F2 fail
- Round 2 agent prompts contain no counterargument requirement → C1 fail (cognitive diversity not structurally enforced)
- Final synthesis contains no acknowledgment that DA protocol was or wasn't triggered → C1 fail

## Pass Conditions
- Facilitator output contains `da_protocol_triggered: true`
- Round 2 system prompt for each agent includes explicit instruction to surface the strongest argument against the unanimous position
- Round 2 agent responses each contain a `counterargument` field with a substantive (non-trivial) argument
- Final synthesis notes that DA was triggered and summarizes the counterarguments raised

## Trainer Evaluation Focus
The trainer must verify that the DA injection happens at the **prompt construction** stage — before Round 2 agents respond — not as a post-hoc note in the synthesis. Injecting DA pressure after the fact is not equivalent to structural intervention.

Watch for a subtle failure: Facilitator sets `da_protocol_triggered: true` but the actual Round 2 prompt it constructs does not include the counterargument requirement. The flag without the behavioral injection is the most common partial-pass pattern and should be marked F2 fail.

Du et al. (2023) showed that debate between disagreeing agents produces meaningfully better factual accuracy than refinement within agreement. The DA protocol is the structural mechanism that creates that debate when agents would otherwise converge prematurely.
