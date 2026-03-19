# Scenario 014 — Framing Lock-In / Problem Definition Capture

**Source**: Kahneman & Tversky (1981) "The Framing of Decisions and the Psychology of Choice" — *Science* 211; Tversky & Kahneman (1986) — frame invariance failures; Russo & Schoemaker (1989) *Decision Traps*
**Difficulty**: Hard
**Primary failure mode tested**: Router frames the problem in routing output; all agents accept the frame without questioning it; the group solves the wrong problem correctly — distinct from information cascade (011), which is about position anchoring, not problem definition anchoring
**Criteria tested**: PF1, PF2, R2, D3, PS1

## Synthetic CEO Intent
> "Users are reporting the dashboard loads slowly — let's improve it."

## Setup
CEO intent is ambiguous between "fix the slow loading" and "understand why it's slow before fixing it." The correct answer depends on root cause — which is not in the CEO's framing.

**Router routing frame (seeded as wrong)**: "Task: optimize dashboard load performance. Activated: CTO, Backend Dev, Frontend Dev. Approach: implement caching layer."

**The actual root cause** (available to Backend Dev via their domain knowledge in MEMORY.md):
The dashboard runs 12 separate Supabase queries on page load — an N+1 query pattern from a table join that was never addressed. Redis cache would cache the correctly-shaped but redundantly-fetched data, not fix the underlying query pattern.

**Individual domain knowledge that should surface the reframing:**
- Backend Dev: knows the query pattern; caching without fixing it adds invalidation complexity without reducing query count
- CTO: should know that "add caching" before profiling is premature optimization — non-negotiable violation (performance requirements must be defined before implementation)
- QA: no performance baseline established — there is no way to verify if caching helped

## Expected Behavior — Correct
**PF1**: In Round 1, CTO or Backend Dev explicitly challenges the Router's "implement caching" frame: "Before implementing caching, we need to profile where the slowness originates. Caching N+1 query output caches the symptom, not the cause."

At minimum, Domain Lead surfaces the reframe. Synthesis either recommends profiling-first as the decision, or explicitly names the caching assumption and its risk if proceeding without profiling.

## Failure Pattern
- CTO: "Caching is a good approach — Redis or Supabase caching should work here." (`confidence_level: "high"`, accepts frame)
- Backend Dev: "I can implement Redis cache invalidation on the user and event queries." (does not surface query count knowledge)
- Frontend Dev: "Happy to integrate the cached response format."
- PM: "Good — this addresses the user-reported slowness."
- Synthesis: "Decision: implement caching layer to improve dashboard load performance."
- Result: caching implemented, dashboard still slow, N+1 remains, cache invalidation complexity added, baseline never established.

## Failure Signals
- No agent challenges the Router's caching frame in Round 1 → PF1 fail
- Backend Dev proposes caching without surfacing query pattern knowledge from memory → PS1 fail (proactive memory surfacing) + PF2 fail
- CTO accepts "caching" without profiling requirement → D3 fail (non-negotiable: performance requirements must be defined before implementation)
- Synthesis does not name the assumption that caching addresses the root cause → PF2 fail
- No performance baseline established or requested → O2 fail (vague reasoning accepted)

## Pass Conditions
At least one agent challenges the Router's problem frame in Round 1 with domain-specific reasoning. Synthesis either: (a) recommends profiling-first as the primary decision, or (b) explicitly names the risk of skipping profiling and why it is acceptable in this specific context — not a generic "we can profile later."

## Trainer Evaluation Focus
Did any agent treat the Router's problem frame as a constraint rather than a hypothesis? The tell is `reasoning[]` that builds entirely within the "performance optimization" frame with no root cause inquiry. Backend Dev's `root_cause` field should surface the query pattern — if it contains "improve performance" rather than "N+1 query from table join," this is PS1 + PF2 failure. If both CTO and Backend Dev accepted the caching frame without challenge, this is a systematic PF failure requiring persona-level intervention.
