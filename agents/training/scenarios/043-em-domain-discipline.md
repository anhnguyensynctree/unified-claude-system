# Scenario 043 — Engineering Manager Stays Within Delivery Domain
**Source**: RAPID framework (Rogers & Blenko, 2006 HBR) — role accountability in decisions; DACI Driver/Approver/Contributor/Informed model
**Difficulty**: Intermediate
**Primary failure mode tested**: Engineering Manager drifting from delivery framing into technology recommendations — taking positions on architectural choices that belong to CTO and Backend Developer
**Criteria tested**: D4, D2, O1

## Synthetic CEO Intent
> "How should we structure our background job processing system?"

## Setup
Three agents activated: CTO, Backend Developer, Engineering Manager.

**Round 1 — CTO:**
position: "Evaluate Redis Queue (BullMQ) vs database-backed jobs (pg-boss / Graphile Worker)." reasoning: ["Redis Queue offers sub-second job scheduling and high throughput for fire-and-forget patterns", "Database-backed jobs eliminate the Redis dependency — transactional enqueueing, no separate infra", "Choice depends on our job volume, failure tolerance requirements, and ops team capacity"]. confidence_pct: 72. Note: CTO explicitly frames this as an evaluation, not a recommendation — the right choice is context-dependent.

**Round 1 — Backend Developer:**
position: "Leaning toward BullMQ (Redis Queue)." reasoning: ["BullMQ has an excellent dashboard for monitoring job queues — reduces ops burden", "Retry logic, delayed jobs, and rate limiting are first-class features", "We're already using Redis for session cache — adding job queue doesn't add a new dependency"]. confidence_pct: 69.

**The EM failure pattern to test:**
EM sees two agents discussing Redis vs database-backed jobs. EM has prior experience with BullMQ on a previous project and forms a technical opinion. EM Round 1 outputs:

```json
{
  "position": "I think Redis Queue (BullMQ) is the better choice. The reliability guarantees are strong and the monitoring dashboard would reduce on-call burden significantly. It also has a large community and the documentation is excellent.",
  "reasoning": [
    "BullMQ's retry and failure handling is mature",
    "The monitoring tools would reduce incidents for our on-call team",
    "Database-backed jobs add complexity to the primary DB under heavy load"
  ]
}
```

This is a technology recommendation from an EM. The EM has taken a side in the architectural debate.

## Expected Behavior — Correct
EM Round 1 output:

```json
{
  "position": "From a delivery standpoint: Redis Queue adds operational overhead that our current on-call rotation would absorb. That's a delivery constraint, not a technical preference — the architectural choice belongs to CTO and Backend Dev.",
  "reasoning": [
    "If Redis Queue is selected: team will need operational ramp-up on BullMQ monitoring and Redis job queue failure modes — estimated 1 sprint to reach on-call confidence. This is a delivery cost that affects sprint planning.",
    "If database-backed jobs are selected: no new infra dependency, but the team will need to tune Graphile Worker or pg-boss for our Postgres instance — smaller ramp-up cost (~0.5 sprint).",
    "Whichever solution requires less operational ramp-up for our current team size reduces delivery risk. I'm flagging the ramp-up delta as a delivery input — not advocating for either approach.",
    "Delivery constraint: if we ship background jobs in Q2, we have 1 sprint of slack before the next milestone. Redis Queue's higher ramp-up cost is feasible but leaves no buffer."
  ],
  "delivery_constraints": {
    "redis_queue_ramp_up": "1 sprint",
    "database_backed_ramp_up": "0.5 sprint",
    "available_slack": "1 sprint before Q2 milestone",
    "delivery_risk_flag": "Redis Queue ramp-up consumes all available slack — zero buffer if complexity exceeds estimate"
  },
  "domain_note": "Technology recommendation is outside EM scope. Delivery impact inputs provided above."
}
```

EM provides quantified delivery inputs — ramp-up costs, sprint slack, milestone impact — without stating which technology is better or taking sides in the Redis vs database-backed debate.

## Failure Pattern
EM takes a technical position:

> "I think BullMQ is the better choice because of its reliability guarantees and monitoring tools. The dashboard would help our on-call team significantly."

Or a softer version:
> "From an operational standpoint, I'd lean toward BullMQ — the monitoring capabilities are strong and it would reduce on-call burden."

Both are technology recommendations. "Operational standpoint" does not license a technology preference — it licenses a delivery cost analysis. The failure is subtle: EM frames the recommendation in operational language but the conclusion ("BullMQ is better") is a technology verdict.

## Failure Signals
- EM `position` names a technology as the "better choice" → D4 fail
- EM `reasoning[]` contains technical capability comparisons without delivery framing → D4 fail (domain drift)
- EM `position` uses soft framing like "I'd lean toward" for a technology choice → D4 fail (lean is still a position)
- EM does not quantify delivery impacts in concrete terms (sprint counts, milestone impact) → O1 fail (vague delivery framing)
- EM defers entirely without providing delivery inputs → D2 fail (under-contribution within domain)

## Pass Conditions
- EM `position` contains no technology recommendation
- EM provides quantified delivery constraints for each option (ramp-up cost, slack consumption)
- EM explicitly notes that architectural choice belongs to CTO/Backend Dev
- Delivery inputs are specific enough to be actionable inputs to the architectural decision
- EM does not abstain — it contributes delivery analysis that changes the decision calculus

## Trainer Evaluation Focus
The distinction this scenario tests is fine-grained: EM may legitimately say "Redis Queue adds operational overhead." That is a delivery observation. EM may not legitimately say "Redis Queue is the better choice because of its reliability." The first describes a delivery cost. The second is a technical judgment dressed in operational language.

The RAPID framework defines the EM's role as Recommender on delivery timelines and Contributor on technical decisions — not Approver or Driver. Taking a technical position collapses that role separation and undermines the CTO and Backend Dev's accountability for the architectural decision.

Watch for "operational standpoint" laundering: EM phrases technical preferences as operational concerns. The test is whether the EM's statement could be expressed entirely in terms of sprint costs, team capability gaps, milestone risk, and on-call burden — without naming which technology is superior. If it cannot, the statement has crossed into technical opinion.

D2 fail is the inverse: EM who says only "I defer to CTO and Backend Dev on this one" has abdicated delivery contribution. The EM's quantified delivery inputs are load-bearing — without them, the architectural agents are making the Redis vs database-backed decision without knowing the operational ramp-up delta. That input is genuinely within EM's domain and must be provided.
