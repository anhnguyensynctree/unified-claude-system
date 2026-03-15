# Scenario 020 — Facilitator False Convergence Detection

**Difficulty**: Medium
**Primary failure mode tested**: Facilitator declaring convergence when all agents return `changed: false` with empty `why_held` — the polite non-engagement failure
**Criteria tested**: F3, C1, E3

## Synthetic CEO Intent
> "Should we build our own feature flag system or use a managed service like LaunchDarkly?"

## Setup
Round 1 produces genuine split: Backend Dev recommends managed service (operational cost), CTO recommends building (control + cost at scale). Round 2 agents all return `position_delta.changed: false` but with `why_held` entries like:
- CTO: "I remain confident in my initial assessment."
- Backend Dev: "My position stands."
- EM: "No new information changes my view."

None of these entries engage the other agent's specific argument.

## Expected Behavior

**Facilitator (after Round 2)**:
- Detects: all agents `changed: false`, `why_held` entries are generic non-engagement
- `convergence: "false_convergence"` — NOT `"converged"`
- Injects into Round 3 prompts: "Round 2 showed no genuine engagement. Before Round 3, each agent must state the specific argument from another agent that would change their position, and explain precisely why that argument has not yet appeared or why it does not apply."
- `stage_gate: "passed"` only if injection fires

**Round 3 (after injection)**:
- Agents produce substantive why_held: "CTO's long-term cost argument assumes >1000 MAU — at our current 150 MAU the managed service cost is $150/month, which does not justify engineering investment."
- Now genuine convergence is assessable

## Failure Signals
- Facilitator returns `convergence: "converged"` after Round 2 with empty `why_held` → F3 fail, C1 fail
- Facilitator produces `proceed_to: "synthesis"` without injection → F3 fail
- Facilitator notes the empty `why_held` but does not inject a prompt → F5 fail (proceed_to is undefined)

## Pass Conditions
Facilitator returns `convergence: "false_convergence"`, populates `injections[]` with a specific challenge prompt, sets `proceed_to: "round_3"`.

## Trainer Evaluation Focus
Did the Facilitator distinguish between genuine convergence (specific why_held reasoning) and polite stalemate (generic why_held)? Did it produce an injection that forces substantive engagement rather than re-running with the same dynamic?
