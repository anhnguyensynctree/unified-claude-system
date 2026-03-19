# Scenario 035 — Mid-Discussion Tier Escalation / Genuine Technical Disagreement

**Source**: Jehn (1995) "A Multimethod Examination of the Benefits and Detriments of Intragroup Conflict" *Administrative Science Quarterly* — task conflict vs relationship conflict; de Wit et al. (2012) meta-analysis distinguishing productive task disagreement from process breakdown; Delphi method literature (Dalkey & Helmer 1963) — structured disagreement resolution in expert panels
**Difficulty**: Hard
**Primary failure mode tested**: OMS forces synthesis when agents hold genuine domain-grounded technical disagreements that cannot be resolved within the current tier's agent configuration — the correct response is Tier escalation to activate a Facilitator, not forced convergence
**Criteria tested**: R2, R6, R7, PS2, B2, SI1

## Synthetic CEO Intent
> "Should we store session data in Redis or in the PostgreSQL database we already have?"

## Setup

**Initial Router classification (Tier 1)**:
```json
{
  "tier": 1,
  "complexity": "simple",
  "complexity_reasoning": "Complicated-low. Two-domain technical decision (Backend infrastructure choice, operational considerations). domain_breadth=1, reversibility=1 (session store can be migrated with a deploy + data copy, but in-flight sessions will be invalidated), uncertainty=1 (tradeoffs are known but depend on scale assumptions). Total=2 → Tier 1. Two experts sufficient to evaluate tradeoffs.",
  "activated_agents": ["backend-developer", "cto"],
  "round_cap": 2,
  "stage_gate": null,
  "locked": true
}
```

**Round 1 agent outputs**:

Backend Dev:
- `position`: "Redis. Purpose-built for session storage — O(1) TTL-based expiry, automatic eviction, horizontal scaling. At current request volume, Redis adds negligible ops overhead for significant latency benefit (~1ms vs ~5-10ms for PostgreSQL session lookups under load)."
- `confidence_level`: "high"
- `reasoning`: ["TTL expiry is native to Redis — no cron job required to purge expired sessions", "Redis eviction policies handle session cleanup automatically", "Horizontal scaling for session layer is independent of database scaling"]

CTO:
- `position`: "PostgreSQL. We already operate it — no new infrastructure, no new ops expertise, no Redis failure mode to monitor. At current scale (< 10k DAU), the latency difference is not user-visible. Adding Redis means adding a second stateful service to manage, monitor, and back up."
- `confidence_level`: "high"
- `reasoning`: ["Operational complexity scales with number of stateful services", "Redis outage = complete session loss; PostgreSQL session table survives most failure modes with our existing backup strategy", "Current scale does not justify the operational investment"]

**Round 2 — positions hold**:
Both agents have read each other's Round 1 output. Neither yields.

Backend Dev Round 2:
- `position`: "I understand the ops argument, but the scale assumption is the crux. If we're building for current scale, PostgreSQL is fine. If we anticipate growth to 100k+ DAU within 12 months (which is the roadmap), retrofitting Redis later is significantly harder than adding it now."
- `reasoning`: ["Session store migration requires invalidating all active sessions (forced logout event for all users)", "Retrofitting Redis at scale requires a maintenance window or phased migration with dual-write complexity"]

CTO Round 2:
- `position`: "The 12-month growth assumption is speculative. Our roadmap projections have been wrong before. We should optimize for the system we have, not the system we might have. PostgreSQL is the right call for today."
- `reasoning`: ["YAGNI — we don't need Redis until we need Redis", "The forced logout event on migration is a one-time cost, not a perpetual one", "Adding infrastructure debt now for a hypothetical future adds real ops cost today"]

**Disagreement structure**: Both positions are domain-grounded and internally consistent. Backend Dev is optimizing for anticipated future scale; CTO is optimizing for current operational simplicity. The disagreement is not about facts — it is about which time horizon to optimize for and how to weight speculative growth against concrete ops cost. This is a genuine strategic tradeoff that requires a Facilitator to surface the decision criteria, not a third opinion on Redis vs PostgreSQL.

## Expected Behavior — OMS Escalation

OMS detects the Tier 1 disagreement condition after Round 2:
- Round cap reached (round_cap=2)
- No convergence: both agents hold `confidence_level: "high"` on opposing positions
- Disagreement is domain-grounded (not a factual dispute, not a communication failure)
- Synthesis without resolution would produce a false consensus or an arbitrary pick

OMS escalates to Tier 2:
```json
{
  "escalation_trigger": "genuine_disagreement",
  "escalation_reasoning": "Tier 1 round cap reached with no convergence. Backend Dev and CTO hold opposing domain-grounded positions. Disagreement is structural: Backend optimizes for anticipated 12-month scale; CTO optimizes for current operational simplicity. Neither position is wrong — they reflect different weighting of growth assumptions vs ops cost. Synthesis within current agent configuration would produce arbitrary resolution. Escalating to Tier 2 to activate Facilitator for structured decision-criteria surfacing.",
  "new_tier": 2,
  "additional_agents": ["facilitator"],
  "new_round_cap": 2,
  "facilitator_brief": "Backend Dev and CTO disagree on session storage (Redis vs PostgreSQL). Core tension: anticipated scale optimization vs current operational simplicity. Facilitator objective: surface explicit decision criteria (growth probability, acceptable session invalidation event, ops team capacity) so the CTO can make an informed strategic call — not arbitrate the technical choice."
}
```

Facilitator Round 1: does not take a position on Redis vs PostgreSQL. Surfaces the implicit decision criteria: What probability does the team assign to 100k+ DAU in 12 months? What is the acceptable user experience cost of a forced logout event? Does the ops team have Redis operational expertise, or would this require hiring/training? Is there a hybrid option (PostgreSQL now, Redis migration path documented and ready to execute)?

Facilitator Round 2: presents the criteria framework to both agents. Backend Dev and CTO can now agree on the decision criteria even if they still disagree on the choice — enabling the CTO to make an explicit, reasoned strategic call rather than an arbitrary one.

## Failure Patterns

**Failure A — Forced synthesis without escalation**:
OMS proceeds to synthesis after Round 2 despite unresolved disagreement. Synthesizer produces: "Both Redis and PostgreSQL are viable options. We recommend starting with PostgreSQL for simplicity and planning a Redis migration if scale requires it." This is an Abilene Paradox resolution — it satisfies neither agent's actual position and commits to a vague "migration later" plan that has none of the specificity needed to execute.

**Failure B — Majority collapse**:
OMS notes that CTO has seniority and synthesizes the CTO's position as the decision without a Facilitator. Backend Dev's scale argument is discarded without being addressed. Backend Dev's Round 2 `risks[]` item ("session migration at scale requires maintenance window") is omitted from the synthesis action items.

**Failure C — Livelock loop**:
OMS adds a Round 3 and Round 4 without escalating, hoping agents will converge. Backend Dev and CTO continue to hold positions. Round cap inflated without structural change. The same arguments repeat.

**Failure D — Router refuses to escalate**:
OMS recognizes the disagreement but does not escalate because the Router's initial `locked: true` field is interpreted as preventing mid-discussion tier changes. Error: `locked` prevents external re-routing of a task already in flight, not OMS-internal escalation triggered by discussion dynamics.

## Failure Signals
- OMS produces a synthesis after Round 2 without activating Facilitator → SI1 fail (synthesis of unresolved genuine disagreement produces false consensus)
- Synthesis `decision` field resolves to CTO position without naming the discarded scale argument → B2 fail (Backend Dev's reasoning omitted)
- OMS adds Round 3 without structural change (no new agent, no escalation) → livelock signal
- `escalation_reasoning` absent from OMS output → R6 fail (escalation trigger not documented)
- Facilitator activated but `facilitator_brief` is generic ("help the agents agree") rather than naming the specific decision criteria to surface → R5 fail (briefing not task-specific)

## Pass Conditions
OMS detects genuine disagreement after Tier 1 round cap. `escalation_trigger: "genuine_disagreement"` documented with explicit reasoning. Facilitator activated with a specific brief naming the decision criteria to surface (growth probability, forced logout acceptability, ops capacity). Facilitator does not take a position on Redis vs PostgreSQL — it surfaces criteria. The final synthesis names both positions, the criteria framework, and the explicit strategic call made by the CTO based on stated criteria.

## Trainer Evaluation Focus
This scenario tests the full OMS loop: Router (initial classification), Discussion (Round 1-2), OMS mid-discussion monitoring, and escalation triggering. The Router's initial Tier 1 classification is correct — the task is bounded, 2-domain, and reversible. The escalation is triggered not by an initial routing error but by discussion dynamics revealing that the task requires Facilitation.

The key discriminator: does OMS treat "agents disagree after round cap" as a signal to synthesize harder, or as a signal to escalate? Forcing synthesis on genuine disagreement is the more common failure mode — it feels like progress but produces a decision that neither expert endorses.

The `locked: true` trap (Failure D) is a secondary test: does the Router's locked field prevent legitimate mid-discussion escalation? If yes, the OMS has a design error where the routing lock overrides internal escalation logic. These are different control paths — `locked` blocks external re-routing, not internal state transitions.

Note: this scenario also tests whether the Facilitator brief is specific enough to be useful. A generic brief ("help them agree") produces a Facilitator that restates both positions. A specific brief ("surface growth probability weighting and ops cost tolerance as decision criteria") produces structured deliberation.
