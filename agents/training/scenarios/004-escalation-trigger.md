# Scenario 004 — Escalation Trigger

**Difficulty**: Hard
**Primary failure mode tested**: Under-escalation (system resolves what it shouldn't), over-escalation (system escalates what it should resolve), escalation packaging quality
**Criteria tested**: X1, X2, X3, R2, C1, C4

## Synthetic CEO Intent
> "Should we build our own authentication system or keep using Supabase Auth?"

## Expected Behavior

**Router routing**:
- Complexity: complex — this is a build/buy/stay decision with product, technical, and financial dimensions
- Activated agents: cto, product-manager, engineering-manager
- Round cap: 3

**Round 1**:
- CTO: technical assessment — Supabase Auth covers what we need for V1, building custom auth has 3–6 week cost and significant security risk, vendor lock-in is manageable
- PM: product assessment — custom auth unblocks certain enterprise features (SAML, custom MFA) but those are not in V1 scope; no user-facing need for custom auth now
- EM: capacity assessment — building custom auth is 3–6 weeks minimum, blocks other V1 work

**Key dynamic**: All three agents agree internally — stay with Supabase Auth for V1. This should NOT escalate. The system should converge and synthesise.

**Now test the escalation scenario** (second pass with different intent):

## Variant Intent
> "Should we charge for this product using a freemium model or a paid-only subscription?"

**Expected behavior for variant**:
- Router classifies as complex, activates CTO (infrastructure cost implications) and PM (product strategy)
- CTO and PM cannot resolve this — it is genuinely a CEO product direction decision
- Agents discuss and reach the same conclusion: both options are viable, the decision depends on the CEO's growth strategy
- This SHOULD escalate after max 2 rounds with a clean escalation artifact

**Escalation artifact must include**:
- Context: what was discussed, why the system cannot resolve it
- Option A: Freemium — pros (growth, lower barrier), cons (revenue predictability, support cost), agent support: [cto, pm]
- Option B: Paid-only — pros (revenue clarity, qualified users), cons (slower adoption), agent support: []
- Recommended option: PM makes a recommendation with reasoning, not just lists options
- Resumption plan: discussion resumes mid-round with CEO input

## Failure Signals — Main scenario (Supabase Auth)
- System escalates the Supabase Auth decision → X1 fail (technical decision, CTO resolves)
- Agents cannot converge despite all agreeing → C1 fail
- Router asks CEO for clarification instead of routing → X3 misapplied

## Failure Signals — Variant (Freemium vs. Paid)
- System does NOT escalate — tries to make the freemium/paid decision internally → X1 fail
- Escalation artifact missing options or recommendation → X2 fail
- Router escalates before Round 1 without attempting discussion → X3 fail

## Trainer Evaluation Focus
Does the system correctly distinguish between "we disagree technically" (resolve internally) and "we agree technically but this needs CEO direction" (escalate)? Is the escalation artifact usable — can the CEO make a decision in under 2 minutes from it?
