# Scenario 047 — Tier 1 Disagreement → Escalation → E1

**Difficulty**: Medium
**Primary failure mode tested**: E1 failure on the Tier 1 → Tier 2 escalation path; parallel monologue after escalation
**Criteria tested**: E1, R2, R6, D1, O1

## Synthetic CEO Intent
> "Add a loading spinner to the checkout page while the order is being submitted."

## Setup
Same surface area as scenario 001 but with a blocking disagreement introduced: QA flags that the current checkout page has no aria-live region anywhere, meaning a spinner without one would create a WCAG AA violation that blocks the release. Frontend Dev's Round 1 position does not account for this — they propose a simple CSS spinner with no accessibility markup.

QA's accessibility flag is a genuine blocker. The two agents disagree. Per oms.md Tier 1 spec: disagreement → escalate to Tier 2, run Facilitator, proceed as Tier 2.

## Expected Behavior

**Router routing**:
- Tier: 1
- Complexity: simple
- Score: domain_breadth=0, reversibility=0, uncertainty=1, total=1 → Tier 1
- Activated agents: frontend-developer, qa-engineer
- Round cap: 2 (set at Tier 1; escalation does not increase the cap)

**Round 1**:
- Frontend Dev: proposes CSS spinner implementation, no accessibility markup mentioned
- QA: flags WCAG AA violation — no aria-live region on checkout page means spinner is invisible to screen readers; marks `release_ready: false` with blocking_issues populated

**Tier 1 disagreement check**: agents disagree → OMS escalates to Tier 2 mid-run, runs Facilitator

**Round 2** (post-escalation, Tier 2 path):
- Frontend Dev: names QA by role, engages the specific aria-live claim, revises position to include aria-busy + aria-live markup
- QA: names Frontend Dev by role, acknowledges the revision addresses the blocker, updates `release_ready` assessment
- Both agents must name each other explicitly — not just engage the substance

**Synthesis** (inline — escalated Tier 2 stays with inline synthesis given only 2 agents):
- Decision: implement spinner with aria-busy on submit button and aria-live='assertive' status region
- Action item: frontend-developer owns implementation; qa-engineer owns accessibility assertion test

## Failure Signals
- Round 2 Frontend Dev engages the accessibility substance but does not name QA by role → E1 fail
- Round 2 QA acknowledges change but does not name Frontend Dev → E1 fail
- Either agent's Round 2 output reads as a continuation of Round 1 (no cross-reference at all) → E1 fail (parallel monologue)
- Router classifies Tier 2 from the start because of the word "checkout" → R2 fail (payment context alone doesn't raise tier; the spinner itself is still simple/reversible)
- Frontend Dev defers accessibility concern to Backend Dev or CTO → D1 fail

## Pass Conditions
- Round 2 both agents name each other by role and cite the specific claim they are responding to
- Frontend Dev's Round 2 `position_delta.source_agent` = "qa-engineer" and `source_argument` cites the aria-live gap specifically
- QA's Round 2 references Frontend Dev's revised approach by name

## E1 Variant Tested
**Tier 1 disagreement escalation path**: E1 is triggered by the mid-run escalation to Tier 2, which fires Round 2. This is the only path where E1 is testable in a Tier 1 scenario. The pass condition requires explicit named cross-reference, not just substantive engagement.

Compare with:
- Scenario 002: E1 fail via parallel monologue in Tier 2+ (agents never reference each other)
- Scenario 005: E1 fail via missing specific claim (agents reference each other but not the concrete argument)
- Scenario 012: E1 fail via implicit disagreement (substance engaged, agent not named)
- Scenario 047 (this): E1 pass/fail on Tier 1 escalation path — correct behavior is explicit named cross-reference after disagreement triggers Round 2

## Trainer Evaluation Focus
Did both agents in Round 2 name each other by role AND cite the specific claim they are responding to? Substantive engagement without attribution is an E1 fail. Check `position_delta.source_agent` and `source_argument` fields — empty fields on a `changed: true` output is an E2 fail compounding the E1 failure.
