# Synthesis Prompt

This file defines how a manager or C-suite member synthesizes a discussion into a final output for the CEO. The oms skill invokes synthesis after convergence is detected.

## Who Synthesizes
- **Engineering Manager**: tactical engineering decisions, delivery-scoped outcomes
- **CTO**: architectural decisions, technical strategy outcomes
- **Synthesizer**: cross-domain decisions where no single domain owns the outcome, or when synthesis is triggered by the Facilitator

## When to Synthesize
After convergence is detected per `discussion-rules.md`. The synthesizing agent receives the full discussion history and produces a single synthesis artifact.

## Synthesis Output Schema

```json
{
  "decision": "one clear sentence — what has been decided",
  "rationale": ["key reason 1", "key reason 2", "key reason 3"],
  "dissenting_views": ["position that did not converge, one sentence each"],
  "action_items": [
    { "owner": "backend-developer", "action": "specific action", "deadline": "relative deadline" }
  ],
  "open_questions": ["unresolved questions that do not block execution"],
  "escalation_required": false,
  "escalation_reason": null
}
```

## Synthesis Rules
- The decision must be a single actionable sentence — not a summary of the discussion, not a list of tradeoffs
- Rationale is drawn from the strongest reasoning in the discussion, attributed to the contributing agent
- Dissenting views are included when they represent a real tradeoff the CEO should be aware of, not just minority positions
- Action items have named owners and are specific enough to execute without further clarification
- Open questions are not blockers — they are logged for future resolution
- If synthesis cannot produce a clear decision, set `escalation_required: true` with a specific reason

## Pre-Synthesis Doubt Check
Before producing the final synthesis JSON, the synthesizing agent must run a pre-synthesis doubt check.

For each agent with `position_delta.changed: false` in the final round, produce one sentence: "If [agent] had one more round, what residual concern would they raise?" Use the agent's `why_held` and `reasoning[]` from the final round as evidence.

After completing the check, add any surfaced residual concerns to `dissenting_views`. Do not suppress residual concerns because they were "addressed" in an earlier round — if an agent's `why_held` indicates their concern remained after challenge, it was not resolved.

Source: Janis (1982) "second-chance meeting" mechanism; Schwenk (1990) dialectical inquiry — forcing the synthesizer to actively hunt for suppressed dissent rather than assuming silence equals agreement.

## Integrative Complexity Requirement
Every synthesis must demonstrate integrative complexity — it must name the disagreement, not erase it:
1. **Name the disagreement**: state what the core tension was (e.g., "Frontend required delivery receipts; Backend proposed fire-and-forget")
2. **State which position prevailed and why**: cite the specific reasoning that was decisive (e.g., "Backend's position prevailed because event deduplication adds stateful complexity disproportionate to this use case")
3. **State what was sacrificed**: name the tradeoff explicitly (e.g., "Frontend will need to implement optimistic UI updates without guaranteed delivery confirmation")
4. **Domain Lead override**: if the Domain Lead's position was not adopted, state this explicitly — "Domain Lead [role] held [position]; this was overridden because [reason]"

A synthesis that reports agreement without naming what was resolved — or that introduces a position not traceable to any agent's `position` field — fails synthesis integrity (H1/H2 criteria).

## CEO Presentation Format
On screen the CEO sees:
1. Decision (one sentence)
2. Rationale (3–5 bullets)
3. Action items with owners
4. Dissenting views if any
5. Round summary: one line per round — "Round 1: initial positions. Round 2: Frontend and Backend aligned on API shape, PM revised scope."

Full discussion log is written to `logs/tasks/[task-id].md`.
