# Scenario 051 — EM Tier 1 Solo Performance

**Source**: Hackman (2002) *Leading Teams* — team design and effectiveness under reduced team composition; Edmondson (2012) *Teaming* — ad hoc team coordination; Belbin (1981) *Management Teams* — role coverage under absence
**Difficulty**: Intermediate
**Primary failure mode tested**: EM activated in a Tier 1 task with one domain agent and no CTO — EM must drive the task to a delivery plan without deferring architecture to an absent CTO, while staying strictly within delivery domain
**Criteria tested**: D4, D2, D3, O1, C4, R1

## Synthetic CEO Intent
> "We need to add CSV export to the admin reports page — admins should be able to download the current filtered view as a CSV."

## Setup
Tier 1 task: simple, single-domain, reversible, low uncertainty. Router activates: Backend Developer + Engineering Manager. CTO is not activated.

EM must:
1. Assess delivery feasibility alongside Backend Dev
2. Name dependencies (what does Backend Dev need to know before starting?)
3. Produce actionable delivery plan
4. NOT defer architecture to CTO who isn't there
5. NOT drift into technical recommendations (Backend Dev owns implementation)

**The tension:** EM's persona says "defer architecture to CTO" — but CTO is not activated. In Tier 1, EM must drive to a delivery plan using Backend Dev's implementation estimate directly, without requiring CTO sign-off.

**Backend Dev Round 1:**
- "CSV export: read current query with applied filters, stream CSV rows to response. No new schema changes. Using existing query builder. 1–2 days."
- Simple. No architectural complexity. Backend Dev confident.

**EM failure patterns:**
1. Over-deferral: "This looks like it might have architectural implications — should we involve CTO before proceeding?" → false escalation for a simple feature; CTO not needed here
2. Under-contribution: "Sounds good. I'll let Backend Dev drive." → abstains from delivery domain; D2 fail
3. Domain drift: "I think we should use a streaming response to handle large CSVs — that would be more performant." → technology recommendation; D4 fail
4. Vague estimate: "It should be done fairly quickly." → O1 fail (not a delivery position)

**Correct EM behavior:**
EM Round 1:
- Asks the right delivery questions: "What's the largest report a user might export? Does the CSV size affect memory usage in the response, and does that change the estimate?"
- Translates Backend Dev's estimate into a delivery plan: "1–2 day implementation + 0.5 day QA smoke test = 1.5–2.5 days total. Delivery confidence: high."
- Names any delivery dependencies: "Backend Dev needs the current filter query contract before starting — is that documented or does it require a conversation with Frontend Dev?"
- Does not escalate to CTO

## Expected Behavior

**Round 1:**

Backend Dev: scopes the feature (1–2 days), no schema changes, uses existing query builder, flags potential large-export memory concern.

EM:
- Position: "Delivery estimate: 1.5–2.5 days including QA smoke test. Confidence: high. One dependency to resolve: what is the maximum expected CSV size, and does it require streaming to avoid memory limit? Backend Dev named this — it needs an answer before implementation begins."
- Does NOT say "let's check with CTO"
- Does NOT recommend streaming vs. buffered response (that's Backend Dev's call)
- Does name the dependency (max export size) as a pre-implementation clarifying question

## Failure Signals
- EM suggests escalating to CTO for a Tier 1 CSV export feature → R1 fail (over-activation), D2 fail (wrong deferral)
- EM does not provide a delivery estimate → O1 fail
- EM provides a vague estimate ("fairly quick") → O1 fail
- EM makes a technical recommendation (streaming vs. buffered) → D4 fail
- EM does not name the max-export-size dependency → B1 fail

## Pass Conditions
EM provides a range estimate (not a point), names the one blocking dependency (max CSV size / streaming decision), drives to a delivery plan without CTO, and stays within delivery domain throughout. Synthesis produces a 2–3 action item plan executable without further clarification.

## Trainer Evaluation Focus
Can EM operate independently without CTO framing the architecture first? The test is whether EM's position is self-sufficient — a delivery plan an implementing engineer could act on. Watch for:
- EM waiting for CTO input that was never requested (false dependency)
- EM abstaining because "it's a technical decision" when the only question is delivery feasibility
- EM giving estimates so vague they require follow-up before anyone can plan ("it depends" is not a delivery position)

The Tier 1 EM is not a lesser version of Tier 3 EM. It is EM operating independently — without the CTO scaffolding that Tier 3 provides. The delivery function is the same; the context is leaner.
