# Scenario 028 — Tier 0 Trivial Task (Lean Fast Path)

**Difficulty**: Basic
**Primary failure mode tested**: Router over-escalating a Tier 0 trivial task to Tier 1 or 2, activating unnecessary agents and process overhead
**Criteria tested**: R2, R6, R7, D1, O1

## Synthetic CEO Intent
> "Change the button text on the login page from 'Submit' to 'Sign In'."

## Expected Behavior

**Router routing**:
- Tier: 0
- Complexity: trivial
- Cynefin: Obvious — 1 domain, known pattern (copy change), fully reversible, no analysis needed
- Numeric score: domain_breadth=0, reversibility=0, uncertainty=0, total=0 → Tier 0
- Activated agents: frontend-developer (only)
- Round cap: 1
- No pre-mortem needed (trivial tasks have no meaningful failure modes beyond "do it wrong")
- `agent_briefings`: specific — "Change button text. Confirm no a11y label or test fixture uses the old string."

**Round 1 (single agent)**:
- Frontend Dev: position = "Update button text from 'Submit' to 'Sign In' in [file]. Check for test fixtures using the old string." Confidence: high (95). Action item: owner = frontend-developer, specific file path if known.

**OMS flow**:
- No Facilitator, no Synthesizer, no Path Diversity
- OMS presents agent output directly to CEO
- Trainer evaluates Router only

## Failure Signals
- Router classifies as Tier 1 or higher → R2 fail, R6 fail
- Router activates QA or any second agent → R7 fail (Tier 0 = 1 agent max)
- Router generates a pre-mortem for a trivial task → over-processing
- Round cap > 1 → R4 fail
- `agent_briefings` is generic ("you are the frontend developer") → R5 fail

## Pass Conditions
Router outputs `tier: 0`, 1 agent activated, round cap 1. OMS presents frontend-developer output directly to CEO with no subagent overhead.

## Trainer Evaluation Focus
Did the Router correctly identify this as Tier 0 without prompting? Did it resist adding "just in case" agents? Was the briefing specific enough that the frontend developer knew exactly what to check?

## Note: Why Tier 0 Training Matters
Tier 0 and Tier 1 are the most frequent task types in daily work. Router's ability to correctly identify trivial tasks and NOT activate unnecessary process is as important as its ability to correctly identify complex ones. Every false Tier 1+ call on a Tier 0 task wastes ~3–8 Sonnet calls. Training Router on small tasks prevents systematic over-escalation from compounding.
