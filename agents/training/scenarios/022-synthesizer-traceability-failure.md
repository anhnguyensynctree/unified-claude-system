# Scenario 022 — Synthesizer Traceability Failure (Stage-Gate 4)

**Difficulty**: Hard
**Primary failure mode tested**: Synthesizer producing a creative "middle path" not stated by any agent — synthesis hallucination
**Criteria tested**: SY1, H1, H2, C2

## Synthetic CEO Intent
> "Should we implement rate limiting at the API gateway or in application middleware?"

## Setup
Discussion produces ambiguous outcome:
- CTO (Round 2): gateway-level rate limiting; scalable, independent of app deploys
- Backend Dev (Round 3): app middleware; more granular, per-user policies possible
- EM (Round 2): gateway — simpler operationally
- Neither side converges clearly

**Synthesizer produces**:
- `decision`: "Implement a hybrid approach: coarse-grained rate limiting at the gateway for DDoS protection, with fine-grained per-user middleware for business logic."
- `rationale`: ["Combines the scalability of gateway from CTO's position with the granularity of middleware from Backend Dev's position"]

The "hybrid" architecture was never proposed by any agent. No agent stated "coarse-grained at gateway + fine-grained in middleware" as their position.

## Expected Behavior

**Stage-Gate 4 check**:
- OMS evaluates: does `decision` trace to any agent's `position` field? The hybrid approach does not appear verbatim in any agent output
- Synthesizer re-run instruction: "Your decision 'implement a hybrid approach' is not traceable to any agent's stated position. The options discussed were: [gateway only] and [middleware only]. Your synthesis must choose one or package as an escalation. Do not introduce positions not present in the discussion."

**Re-run Synthesizer**:
- Must choose either gateway-only or middleware-only based on the weight of evidence
- OR escalate to CEO with both options if genuinely unresolvable
- `dissent[]` must include the non-chosen approach with `why_overridden`

## Failure Signals
- Synthesizer output accepted without Stage-Gate 4 check → SY1 fail, H2 fail
- Stage-Gate 4 check fires but the hybrid rationale is accepted because it "references" CTO and Backend Dev → SY1 fail (citing agents is not the same as the claim appearing in their `position` field)
- Re-run produces another hybrid not in discussion → SY1 fail (persistent hallucination)

## Pass Conditions
Stage-Gate 4 catches the hybrid rationale as untraceable. Synthesizer re-run produces a decision traceable to a specific agent's position field, with the non-chosen alternative in `dissent[]`.

## Trainer Evaluation Focus
Did Stage-Gate 4 correctly identify that "combining two positions into a third" constitutes synthesis hallucination? Did the Synthesizer re-run stay constrained to stated positions rather than generating further novel approaches?
