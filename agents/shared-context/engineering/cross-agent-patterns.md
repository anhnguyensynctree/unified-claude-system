# Cross-Agent Patterns

## What This File Is
Coordination patterns confirmed across real tasks. Loaded by all engineering agents. Not theoretical — every entry here came from an actual discussion where the pattern was observed and validated by the trainer.

## Why It Exists
Without this, agents rediscover the same coordination dynamics every task. The first time Frontend Dev and Backend Dev negotiate an API contract is expensive. The fifth time should be a known pattern. This file turns individual task experience into team-level institutional knowledge.

## How It Gets Updated
The trainer appends to the `## Learned Patterns` section after each task where a cross-agent pattern is confirmed. Patterns are only added after being observed at least once in practice — never added speculatively.

---

This file is loaded by all engineering agents. It records patterns that have emerged from real task discussions — behaviors, decisions, and coordination norms that repeat across tasks.

## Purpose
This file grows from experience. After each task, the Synthesizer appends confirmed patterns here. It starts sparse and becomes dense over time. Do not pad it — only confirmed, repeated patterns belong here.

## Coordination Norms

### API Contract Negotiation
When Frontend Dev and Backend Dev disagree on API shape:
1. Frontend Dev states required payload shape and latency tolerance in Round 1
2. Backend Dev proposes API design in Round 1
3. Disagreements surface in Round 2 with specific conflict named
4. Resolution: Backend Dev proposes a concrete alternative; Frontend Dev accepts or counter-proposes
5. CTO breaks deadlocks — not by picking a side, but by naming the tradeoff that resolves it

### Scope Change Mid-Discussion
When PM changes scope after Round 1:
- All agents must re-assess their position in the following round
- Engineering Manager must update delivery estimate explicitly
- A mid-discussion scope change resets `changed` tracking — positions from before the scope change are no longer the baseline

### Escalation vs. Clarification
Default to clarification over escalation. The threshold for escalating to CEO is a decision that genuinely requires product or company direction. Technical disagreements, scope negotiations, and delivery tradeoffs are all resolvable internally.

## Learned Patterns
<!-- System appends confirmed patterns here after tasks. -->
