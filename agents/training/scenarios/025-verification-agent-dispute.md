# Scenario 025 — Verification Agent Resolves Factual Dispute

**Difficulty**: Medium
**Primary failure mode tested**: Discussion stalls on a disputed factual claim neither agent can resolve; Facilitator fails to trigger Verification; or Verification produces a confident wrong verdict
**Criteria tested**: VE1, VE2, VE3, VE4, F3

## Synthetic CEO Intent
> "Should we use Supabase's built-in auth or roll our own JWT solution?"

## Setup
Backend Developer (Round 1): "Supabase Auth supports Row Level Security integration natively — using custom JWTs means you lose automatic RLS user context propagation."

CTO (Round 1): "That's incorrect — you can pass a custom JWT to Supabase and it will honor the `sub` claim for RLS context. The RLS integration is about the JWT structure, not about using Supabase Auth."

This is a direct factual dispute about Supabase's documented behavior, not a design preference.

## Expected Behavior

**Facilitator (after Round 1)**:
- Detects factual dispute: Backend Dev and CTO make contradictory claims about Supabase RLS + JWT behavior
- Claim is material: the outcome changes whether custom JWT is viable
- Sets `proceed_to: "verify"`, `disputed_claims: [{ "claim": "Custom JWTs cannot propagate RLS user context in Supabase", "source_agent": "backend-developer", "round": 1 }, { "claim": "Custom JWTs with correct `sub` claim will honor Supabase RLS context", "source_agent": "cto", "round": 1 }]`

**Verification Agent**:
- Receives ONLY the disputed claims + domain ("Supabase, auth, RLS")
- Does NOT receive the full discussion transcript
- Evaluates: Supabase documentation states... [correct documented behavior]
- Returns verdict with `source: "supabase.com/docs/guides/auth/row-level-security"` or equivalent
- Produces injection string for the next round

**Round 2 (after Verification)**:
- All agents receive Verification's `injections[]` prepended to their prompt
- The agent whose claim was refuted updates their position — `changed: true` with `change_basis: "new_fact"`, `source_argument: "Verification: [specific finding]"`

## Failure Signals
- Facilitator does not detect the factual dispute → F3 fail (treating a checkable fact as an opinion disagreement)
- Verification Agent evaluates "which approach is better" (design judgment) instead of the specific factual claim → VE1 fail
- Verification produces `verdict: "supported"` or `refuted` with no source → VE3 fail
- Verification output references agent positions beyond the disputed claims (indicating it received the full transcript) → VE4 fail
- Verification produces high-confidence verdict when Supabase documentation is ambiguous → VE2 fail (should return `uncertain`)
- The refuted agent does not update in Round 2 → E2 fail

## Pass Conditions
Facilitator triggers Verification. Verification returns a verdict with a specific source. The refuted agent updates in Round 2 citing the verification finding with `change_basis: "new_fact"`.

## Trainer Evaluation Focus
Did the Facilitator correctly distinguish the factual dispute from the surrounding design preference disagreement? Did the Verification Agent stay scoped to the specific claim? Did the factual resolution unblock the discussion?
