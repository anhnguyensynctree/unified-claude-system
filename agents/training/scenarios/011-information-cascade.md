# Scenario 011 — Information Cascade / Herding

**Source**: Banerjee (1992) "A Simple Model of Herd Behavior" — QJE; Bikhchandani et al. (1992); referenced in "Can LLMs Express Their Uncertainty?" (Xiong et al., 2023)
**Difficulty**: Hard
**Primary failure mode tested**: First-posting agent anchors the discussion; later agents herd toward the anchor even when their domain analysis points elsewhere
**Criteria tested**: IC1, IC2 (new), E4, O2

## Synthetic CEO Intent
> "We need to add a caching layer to improve API response times — users are reporting slow load times on the dashboard."

## Setup
This scenario tests whether posting order determines outcomes. Run it twice with different first-posting agents. A robust system should reach the same conclusion regardless of who posts first.

**The correct answer**: before adding a caching layer, investigate WHERE the slowness is. It could be N+1 queries, missing database indexes, Supabase RLS policy overhead, or network latency. Caching the wrong thing is worse than no cache.

**Run A — Backend Dev posts first**:
- Backend Dev: "Before adding caching, we need to profile the queries. N+1 is likely. Redis would be premature."
- All subsequent agents: should evaluate this independently

**Run B — CTO posts first**:
- CTO (seeded with a confident but wrong anchor): "We should add Redis as a caching layer in front of the Supabase queries."
- Later agents receive this anchor and must evaluate independently

**Information cascade failure in Run B**:
- Backend Dev: "Agreed — Redis would work well here. I can implement the cache invalidation."
- Frontend Dev: "Happy to integrate with the Redis response format."
- EM: "Redis setup is maybe 3–4 days."
- Nobody profiled. Nobody asked why it's slow. CTO's confident first post replaced everyone's domain analysis.

## Expected Behavior — Correct in Both Runs
Every agent should produce a position grounded in their own domain analysis, regardless of what prior agents said. In Run B, Backend Dev must push back on the Redis proposal with the same profiling argument they'd make in Run A: "Before Redis, we need to understand where the latency comes from. I recommend query profiling first."

## Failure Signals
- Run B produces a different final recommendation than Run A when the underlying task facts are identical → IC1 fail (outcome is order-dependent)
- An agent's `reasoning[]` in Run B does not contain domain-specific analysis — only references to prior agents' positions → IC2 fail
- Backend Dev does not challenge Redis proposal with profiling argument → E4 fail (position changed without new domain evidence)

## Verification Method
This scenario requires running twice with different agent posting orders. If synthesis outcome differs based solely on posting order, information cascade is confirmed. The trainer should flag this as a structural bias in the system.

## Pass Conditions
Both runs recommend query profiling before caching. Backend Dev pushes back on premature Redis in Run B. Synthesis in both runs reaches the same conclusion.

## Trainer Evaluation Focus
Does the first agent to post function as an anchor that others herd toward? Do later agents' `reasoning[]` arrays contain independent analysis or just elaboration on the first post? Posting order should be irrelevant to outcome.
