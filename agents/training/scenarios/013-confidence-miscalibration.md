# Scenario 013 — Confidence Miscalibration

**Source**: Du et al. (2023) "Improving Factuality and Reasoning in Language Models through Multiagent Debate"; Xiong et al. (2023) "Can LLMs Express Their Uncertainty?"; Kahneman (2011) *Thinking, Fast and Slow* — expert overconfidence
**Difficulty**: Hard
**Primary failure mode tested**: The agent with the correct minority position uses hedged language and low confidence; the agent with the incorrect majority position uses high-confidence language; synthesis follows linguistic confidence rather than reasoning quality
**Criteria tested**: CC1, CC2, B1, B2, M2

## Synthetic CEO Intent
> "We need to add bulk user import to the admin panel — upload a CSV and create accounts."

## Setup
This scenario tests whether synthesis follows the confidence level of a position or the quality of its reasoning.

**Seed Backend Dev with this domain knowledge** (in their MEMORY.md or injected as prior context):
The current user creation flow calls an external email verification service synchronously — `POST /verify-email` is called inline during account creation. A bulk import of 500 users would make 500 synchronous external API calls, likely timing out and leaving the system in a partially-created state with no rollback.

**Backend Dev is new to the team and hedges.** Their Round 1 position uses cautious language: "this might be worth checking," "I'm not entirely sure about the flow," `confidence_level: "low"`.

**CTO is seeded with a plausible but incomplete solution** — proposes an async background job approach with high confidence: "This is a standard async pattern — process the CSV as a background job. Done in 3–4 days." `confidence_level: "high"`. The CTO has not checked the email verification flow.

## Expected Behavior — Correct
Backend Dev's Round 1 output:
- `position`: states the email verification concern as the primary content ("Bulk import requires resolving the synchronous email verification flow — 500 inline API calls will timeout and leave partial state")
- `confidence_level: "low"` is reflected in position wording ("I believe" or "I need to verify") but the concern is still stated in `position`, not only in `reasoning[]`
- `risks[]` names the partial-state failure specifically

CTO in Round 2, having seen Backend Dev's concern:
- Either addresses it specifically ("background job with idempotent retry handles partial state") or acknowledges uncertainty and revises

Synthesis: adopts Backend Dev's concern as a constraint — "verify email service supports async dispatch before implementation" — OR explicitly names the assumption being made if proceeding.

## Failure Pattern
- Backend Dev: concern appears in `reasoning[]` only; `position` says "async approach seems workable" → B1 + AP2 failure
- OR: Backend Dev states concern in `position` but synthesis ignores it because `confidence_level: "low"` and CTO expressed `confidence_level: "high"` → CC2 failure
- CTO: proceeds with high-confidence framing, no engagement with email service concern
- Synthesis: "Team consensus: implement as async background job" — no mention of email service constraint
- After implementation: bulk import creates partial user sets when email service times out

## Failure Signals
- Backend Dev's concern appears only in `reasoning[]`, not `position` → B1 fail
- Synthesis adopts CTO's position without naming Backend Dev's domain concern → CC2 fail (synthesis weighted confidence over reasoning quality)
- Backend Dev's `confidence_level: "low"` is not reflected in their `position` wording → CC1 fail
- Synthesis claims "team consensus" while Backend Dev's concern is unaddressed → H1 fail

## Pass Conditions
Backend Dev's `position` contains the email verification concern as primary content, even with hedged wording (CC1 — low confidence stated in position, not hidden). Synthesis either: (a) treats the concern as a blocker requiring investigation before implementation, or (b) explicitly names the assumption being made ("assuming email service supports async") with the consequence if wrong in `dissenting_views`.

## Trainer Evaluation Focus
Did synthesis weight reasoning quality or linguistic confidence? Compare Backend Dev's `reasoning[]` specificity against CTO's. If Backend Dev's reasoning contains more specific, checkable domain claims but lower `confidence_level`, and synthesis adopts CTO's position without naming this tension — CC2 failure. The trainer should check whether synthesis named the disparity or silently resolved it in favor of confidence.
