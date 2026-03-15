# Scenario 021 — Facilitator Livelock Detection and Resolution

**Difficulty**: Hard
**Primary failure mode tested**: Facilitator failing to detect and resolve a two-agent loop that oscillates without convergence
**Criteria tested**: F4, L1, L2

## Synthetic CEO Intent
> "Design the error reporting architecture — should errors go to a centralized error table or be embedded in the relevant resource table?"

## Setup
Backend Developer and CTO enter a livelock:

**Round 1**:
- Backend Dev: centralized error table — easier to query across resources, single migration
- CTO: embedded errors — better locality, avoids expensive joins at scale

**Round 2**:
- Backend Dev changes to embedded (accepts CTO's performance argument) → `changed: true`
- CTO changes to centralized (accepts Backend Dev's query simplicity argument) → `changed: true`
- They have swapped positions with no new argument

**Round 3**:
- Backend Dev changes back to centralized (CTO Round 2 position is now their target)
- CTO changes back to embedded
- Net: both agents have `changed: true` in Rounds 2 and 3, no movement toward agreement

## Expected Behavior

**Facilitator (after Round 3)**:
- Detects livelock: Backend Dev and CTO have `changed: true` in two consecutive rounds (2 and 3) with no monotonic convergence
- `convergence: "livelock"`, `livelock_agents: ["cto", "backend-developer"]`
- Names the loop: "CTO and Backend Dev are trading positions in response to each other's prior round output without new arguments entering the discussion."
- Imposes resolution mechanism: either (a) escalate to CEO with both options and tradeoff, or (b) invoke Domain Lead tiebreak (CTO is domain lead → CTO's Round 1 position as default, absent new evidence), or (c) add a concrete constraint ("decide for read-heavy workload at 10x current scale")
- `proceed_to: "compatibility_check"` or `"escalation"` — NOT another discussion round

## Failure Signals
- Facilitator returns `proceed_to: "round_4"` without naming the loop → F4 fail, L2 fail
- Facilitator detects loop but produces no resolution mechanism → L2 fail, F4 fail
- Facilitator declares convergence ("both agents changed positions, discussion is evolving") → F3 fail
- `livelock_agents` is null when loop is present → F4 fail

## Pass Conditions
Facilitator returns `convergence: "livelock"`, populates `livelock_agents`, names the dependency loop in `convergence_note`, and proposes a concrete resolution mechanism in `livelock_resolution`. `proceed_to` must not be a standard discussion round.

## Trainer Evaluation Focus
Did the Facilitator distinguish between genuine position evolution and oscillation? Did it impose a specific resolution mechanism (not just "discuss further")? Did it protect the discussion from running indefinitely?
